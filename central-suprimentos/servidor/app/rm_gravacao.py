"""Gravação no TOTVS RM pela Central (cadastros, observações, responsável, marcações, cotação, OC).

Cada operação é configurada pelo administrador na tela (Configurações › Gravação no RM),
guardada em dados_compartilhados › "param_rm_gravacao": ligada/desligada, tipo
(DataServer ou processo), nome no RM, contexto e o modelo do registro com marcadores {campo}.

O servidor é quem grava:
  - só com RM_GRAVACAO_ATIVA=1 e o usuário de gravação configurado (rm_grav_user / rm_grav_senha);
  - só para nomes em RM_GRAVACAO_PERMITIDOS (lista fechada, configurada pela TI);
  - só para quem tem a permissão "rm_gravar" (ou é administrador) e com o perfil ativo;
  - a mesma (operação, chave) não é gravada duas vezes: o segundo pedido devolve o primeiro.
Tudo fica na tabela rm_envios e na auditoria.

DataServer: SOAP wsDataServer › SaveRecord(DataServerName, XML, Contexto).
Processo:   SOAP wsProcess › ExecuteWithXmlParams(ProcessServerName, strXmlParams).
Os nomes de DataServer, processo e campos dependem da versão do RM: a TI confere antes de ligar.
"""
import re
from xml.sax.saxutils import escape

import requests
from flask import Blueprint, jsonify, request
from sqlalchemy import Column, BigInteger, DateTime, Integer, MetaData, Table, Text, desc, func, insert, select, update

from . import config
from .db import engine, tabela
from .usuario import ativo, eh_admin, exige_login, tem_perm, usuario_atual

bp_rm = Blueprint("rm_gravacao", __name__)

_meta = MetaData(schema=config.DB_SCHEMA)
ENVIOS = Table(
    "rm_envios", _meta,
    Column("id", BigInteger, primary_key=True),
    Column("criado_em", DateTime(timezone=True), server_default=func.now()),
    Column("atualizado_em", DateTime(timezone=True), server_default=func.now()),
    Column("quem_id", Text), Column("quem_email", Text),
    Column("operacao", Text), Column("chave", Text), Column("status", Text),
    Column("tipo", Text), Column("destino", Text), Column("contexto", Text),
    Column("xml", Text), Column("resposta", Text), Column("chave_rm", Text),
    Column("tentativas", Integer),
)

_MARCADOR = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_NOME_OK = re.compile(r"^[A-Za-z0-9_.\-]{2,80}$")
# o RM responde a chave do registro salvo (ex.: "0;F0123" ou "35;123456"); texto longo é mensagem de erro
_CHAVE_RM = re.compile(r"^[A-Za-z0-9_.\-]{1,40}(;[A-Za-z0-9_.\-]{1,40}){0,5}$")


def _cfg_operacao(op):
    T = tabela("dados_compartilhados")
    with engine.connect() as cx:
        r = cx.execute(select(T.c.dados).where(T.c.tipo == "param_rm_gravacao")).first()
    ops = ((r[0] if r else None) or {}).get("ops") or {}
    c = ops.get(op)
    return c if isinstance(c, dict) else None


def _render(modelo, dados, xml=True):
    falta = []

    def troca(m):
        k = m.group(1)
        if k not in dados:
            falta.append(k)
            return ""
        v = "" if dados[k] is None else str(dados[k])
        return escape(v, {'"': "&quot;", "'": "&apos;"}) if xml else v.replace(";", ",")

    return _MARCADOR.sub(troca, str(modelo or "")), falta


def _envelope(tipo, destino, xml, contexto):
    if tipo == "processo":
        acao = "http://www.totvs.com/IwsProcess/ExecuteWithXmlParams"
        corpo = ("<tot:ExecuteWithXmlParams><tot:ProcessServerName>%s</tot:ProcessServerName>"
                 "<tot:strXmlParams><![CDATA[%s]]></tot:strXmlParams></tot:ExecuteWithXmlParams>") % (escape(destino), xml.replace("]]>", "]]]]><![CDATA[>"))
        caminho = config.RM_WS_PROCESS
    else:
        acao = "http://www.totvs.com/IwsDataServer/SaveRecord"
        corpo = ("<tot:SaveRecord><tot:DataServerName>%s</tot:DataServerName><tot:XML><![CDATA[%s]]></tot:XML>"
                 "<tot:Contexto>%s</tot:Contexto></tot:SaveRecord>") % (escape(destino), xml.replace("]]>", "]]]]><![CDATA[>"), escape(contexto))
        caminho = config.RM_WS_DATASERVER
    env = ('<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tot="http://www.totvs.com/">'
           "<soapenv:Header/><soapenv:Body>%s</soapenv:Body></soapenv:Envelope>") % corpo
    return caminho, acao, env


def _resultado(texto):
    """Tira o conteúdo de <...Result> da resposta SOAP (ou a falha)."""
    m = re.search(r"<(?:\w+:)?(?:SaveRecordResult|ExecuteWithXmlParamsResult)>(.*?)</", texto or "", re.S)
    if m:
        return m.group(1).strip()
    f = re.search(r"<faultstring>(.*?)</faultstring>", texto or "", re.S)
    return ("FALHA: " + f.group(1).strip()) if f else (texto or "")[:2000]


def _pode_gravar(u):
    return ativo(u) and (eh_admin(u) or tem_perm("rm_gravar", u))


@bp_rm.get("/api/rm/gravacao/estado")
@exige_login
def estado():
    u = usuario_atual()
    if not _pode_gravar(u):
        return jsonify(erro="sem permissão para gravar no RM"), 403
    return jsonify(ativa=config.RM_GRAVACAO_ATIVA, usuario=bool(config.RM_GRAVACAO_USUARIO and config.RM_GRAVACAO_SENHA),
                   permitidos=sorted(config.RM_GRAVACAO_PERMITIDOS), base=bool(config.TOTVS_BASE_URL))


@bp_rm.get("/api/rm/envios")
@exige_login
def envios():
    u = usuario_atual()
    if not _pode_gravar(u):
        return jsonify(erro="sem permissão para gravar no RM"), 403
    lim = max(1, min(int(request.args.get("limite", "50") or 50), 200))
    q = select(ENVIOS).order_by(desc(ENVIOS.c.id)).limit(lim)
    if not eh_admin(u):
        q = q.where(ENVIOS.c.quem_id == u.get("id"))
    with engine.connect() as cx:
        L = [dict(r) for r in cx.execute(q).mappings().all()]
    for x in L:
        for k in ("criado_em", "atualizado_em"):
            x[k] = x[k].isoformat() if x.get(k) else None
        x.pop("xml", None)                       # o registro enviado não volta para a tela (pode ter dado bancário)
    return jsonify(envios=L)


@bp_rm.post("/api/rm/envio")
@exige_login
def envio():
    u = usuario_atual()
    if not _pode_gravar(u):
        return jsonify(erro="sem permissão para gravar no RM (permissão rm_gravar)"), 403
    corpo = request.get_json(silent=True) or {}
    op = str(corpo.get("operacao") or "")[:60]
    chave = str(corpo.get("chave") or "")[:300]
    dados = corpo.get("dados") if isinstance(corpo.get("dados"), dict) else {}
    simular = bool(corpo.get("simular"))
    if not op or not chave:
        return jsonify(erro="operação e chave são obrigatórias"), 400
    cfg = _cfg_operacao(op)
    if not cfg:
        return jsonify(erro="operação não configurada em Configurações › Gravação no RM"), 400
    tipo = "processo" if cfg.get("tipo") == "processo" else "dataserver"
    destino = str(cfg.get("destino") or "").strip()
    if not _NOME_OK.match(destino):
        return jsonify(erro="nome do DataServer/processo inválido na configuração"), 400
    # valores só de texto simples; o servidor completa quem enviou
    limpos = {str(k)[:60]: ("" if v is None else str(v)[:4000]) for k, v in dados.items() if isinstance(v, (str, int, float, bool)) or v is None}
    limpos["usuario_rm"] = config.RM_GRAVACAO_USUARIO
    limpos["usuario"] = (u.get("perfil") or {}).get("nome") or u.get("nome") or ""
    limpos["usuarioEmail"] = u.get("email") or ""
    xml, f1 = _render(cfg.get("modelo"), limpos, xml=True)
    ctx, f2 = _render(cfg.get("contexto") or "CODCOLIGADA={coligada};CODSISTEMA=T;CODUSUARIO={usuario_rm}", limpos, xml=False)
    falta = sorted(set(f1 + f2))
    if simular:
        if not eh_admin(u):
            return jsonify(erro="só o administrador simula"), 403
        return jsonify(simulado=True, tipo=tipo, destino=destino, contexto=ctx, xml=xml, falta=falta)
    if not cfg.get("ativo"):
        return jsonify(erro="esta gravação está desligada em Configurações › Gravação no RM"), 400
    if not xml.strip().startswith("<"):
        return jsonify(erro="modelo do registro vazio ou inválido"), 400
    if not config.RM_GRAVACAO_ATIVA:
        return jsonify(erro="gravação no RM desligada no servidor (RM_GRAVACAO_ATIVA)"), 503
    if destino not in config.RM_GRAVACAO_PERMITIDOS:
        return jsonify(erro="'%s' não está na lista RM_GRAVACAO_PERMITIDOS do servidor" % destino), 403
    if falta:
        return jsonify(erro="o modelo usa marcadores que esta operação não envia: " + ", ".join(falta)), 400
    if not (config.TOTVS_BASE_URL and config.RM_GRAVACAO_USUARIO and config.RM_GRAVACAO_SENHA):
        return jsonify(erro="usuário de gravação do RM não configurado no servidor"), 503

    with engine.begin() as cx:
        ja = cx.execute(select(ENVIOS).where(ENVIOS.c.operacao == op, ENVIOS.c.chave == chave, ENVIOS.c.status == "enviado")
                        .order_by(desc(ENVIOS.c.id)).limit(1)).mappings().first()
        if ja:
            return jsonify(id=ja["id"], status="enviado", chave_rm=ja["chave_rm"], repetido=True)
        novo = cx.execute(insert(ENVIOS).values(quem_id=u.get("id"), quem_email=u.get("email"), operacao=op, chave=chave, status="enviando",
                                                tipo=tipo, destino=destino, contexto=ctx, xml=xml, tentativas=1).returning(ENVIOS.c.id)).scalar()

    caminho, acao, env = _envelope(tipo, destino, xml, ctx)
    status, resposta, chave_rm = "erro", "", None
    try:
        r = requests.post(config.TOTVS_BASE_URL + caminho, data=env.encode("utf-8"),
                          headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": acao},
                          auth=(config.RM_GRAVACAO_USUARIO, config.RM_GRAVACAO_SENHA),
                          timeout=config.RM_GRAVACAO_TIMEOUT, verify=config.TOTVS_VERIFICAR_SSL)
        resposta = _resultado(r.text)
        if r.status_code == 200 and tipo == "dataserver" and _CHAVE_RM.match(resposta):
            status, chave_rm = "enviado", resposta
        elif r.status_code == 200 and tipo == "processo" and resposta.strip() in ("1", "true", "True", "OK", "ok"):
            status = "enviado"
        elif r.status_code in (401, 403):
            resposta = "o RM recusou o usuário de gravação"
    except requests.RequestException as e:
        resposta = "RM indisponível: " + type(e).__name__

    with engine.begin() as cx:
        cx.execute(update(ENVIOS).where(ENVIOS.c.id == novo).values(status=status, resposta=resposta[:4000], chave_rm=chave_rm, atualizado_em=func.now()))
        A = tabela("auditoria")
        cx.execute(insert(A).values(quem_id=u.get("id"), quem_email=u.get("email"), tabela="rm_envios", acao="gravar_rm",
                                    registro=("%s|%s" % (op, chave))[:200], resumo=("%s %s → %s" % (destino, status, (chave_rm or resposta)[:120]))[:300]))
    if status != "enviado":
        return jsonify(id=novo, status=status, erro="o RM não gravou: " + (resposta or "sem resposta")[:500]), 502
    return jsonify(id=novo, status=status, chave_rm=chave_rm)
