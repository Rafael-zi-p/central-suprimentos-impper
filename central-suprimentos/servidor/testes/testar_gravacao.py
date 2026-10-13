"""Testes da gravação no RM (app/rm_gravacao.py) com um RM falso (sem rede).

Usa o banco de teste (as tabelas dados_compartilhados, rm_envios e auditoria precisam existir)
e simula o usuário logado. Apaga, no fim, só o que ele mesmo criou.

Rodar na pasta servidor/, com as variáveis do banco de teste:
    python testes/testar_gravacao.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("RM_GRAVACAO_ATIVA", "1")
os.environ.setdefault("rm_grav_user", "gravacao.rm")
os.environ.setdefault("RM_GRAVACAO_SENHA", "senha-gravacao")
os.environ.setdefault("RM_GRAVACAO_PERMITIDOS", "FinCFODataBR,ProcTeste")
os.environ.setdefault("TOTVS_BASE_URL", "http://rm-falso:8051")

from flask import Flask                                   # noqa: E402
from sqlalchemy import delete, insert, select             # noqa: E402

from app import config, rm_gravacao as RG, usuario as US  # noqa: E402
from app.db import engine, tabela                         # noqa: E402

OK, FALHA = [], []


def chk(nome, cond, extra=""):
    (OK if cond else FALHA).append(nome + ("" if cond else "  -> " + str(extra)[:400]))


# ── usuário simulado ──
ATUAL = {"u": None}
ADM = {"id": "00000000-0000-0000-0000-00000000a001", "email": "admin.teste@empresa.com.br", "nome": "Admin Teste", "permitido": True,
       "perfil": {"id": "p-adm", "nome": "Admin Teste", "ativo": True, "is_admin": True, "permissoes": []}}
COMUM = {"id": "00000000-0000-0000-0000-00000000c002", "email": "comum.teste@empresa.com.br", "nome": "Comum", "permitido": True,
         "perfil": {"id": "p-com", "nome": "Comum", "ativo": True, "is_admin": False, "permissoes": ["sc"]}}
GRAVA = {"id": "00000000-0000-0000-0000-00000000d003", "email": "grava.teste@empresa.com.br", "nome": "Grava", "permitido": True,
         "perfil": {"id": "p-grv", "nome": "Grava", "ativo": True, "is_admin": False, "permissoes": ["sc", "rm_gravar"]}}
US.usuario_atual = lambda: ATUAL["u"]
RG.usuario_atual = lambda: ATUAL["u"]

# ── RM falso: responde conforme o DataServer e guarda o que recebeu ──
CHAMADAS = []
RESPOSTA = {"txt": "0;F0123"}


class _Resp:
    def __init__(self, txt, code=200):
        self.status_code, self.text = code, txt


def _post(url, data=None, headers=None, auth=None, timeout=None, verify=None):
    CHAMADAS.append({"url": url, "corpo": data.decode("utf-8"), "acao": (headers or {}).get("SOAPAction"), "auth": auth})
    if "IwsProcess" in url:
        return _Resp("<s:Envelope><s:Body><ExecuteWithXmlParamsResponse><ExecuteWithXmlParamsResult>1</ExecuteWithXmlParamsResult></ExecuteWithXmlParamsResponse></s:Body></s:Envelope>")
    return _Resp("<s:Envelope><s:Body><SaveRecordResponse><SaveRecordResult>%s</SaveRecordResult></SaveRecordResponse></s:Body></s:Envelope>" % RESPOSTA["txt"])


RG.requests.post = _post

app = Flask("teste")
app.register_blueprint(RG.bp_rm)
cli = app.test_client()
T = tabela("dados_compartilhados")


def cfg(ops):
    with engine.begin() as cx:
        cx.execute(delete(T).where(T.c.tipo == "param_rm_gravacao"))
        cx.execute(insert(T).values(tipo="param_rm_gravacao", dados={"ops": ops}))


def enviar(op, chave, dados, simular=False):
    r = cli.post("/api/rm/envio", json={"operacao": op, "chave": chave, "dados": dados, "simular": simular})
    return r.status_code, r.get_json()


MODELO = "<FinCFO><FCFO><CODCOLIGADA>{coligada}</CODCOLIGADA><NOME>{razao}</NOME><CGCCFO>{docFmt}</CGCCFO><INSCRESTADUAL>{ie}</INSCRESTADUAL></FCFO></FinCFO>"
FORN = {"coligada": "0", "razao": "A & B <Materiais> LTDA", "docFmt": "11.222.333/0001-81", "ie": "123456789"}
try:
    ATUAL["u"] = None
    chk("sem login = 401", cli.post("/api/rm/envio", json={}).status_code == 401)
    ATUAL["u"] = COMUM
    st, j = enviar("forn_cadastro", "teste-1", FORN)
    chk("sem a permissão rm_gravar = 403", st == 403, (st, j))
    ATUAL["u"] = ADM
    cfg({})
    st, j = enviar("forn_cadastro", "teste-1", FORN)
    chk("operação não configurada = 400", st == 400, (st, j))
    cfg({"forn_cadastro": {"ativo": False, "tipo": "dataserver", "destino": "FinCFODataBR", "contexto": "CODCOLIGADA={coligada};CODSISTEMA=T;CODUSUARIO={usuario_rm}", "modelo": MODELO}})
    st, j = enviar("forn_cadastro", "teste-1", FORN, simular=True)
    chk("simular monta o XML", st == 200 and j.get("simulado") and "<NOME>A &amp; B &lt;Materiais&gt; LTDA</NOME>" in j.get("xml", ""), (st, j))
    chk("simular monta o contexto com o usuário de gravação", st == 200 and j.get("contexto") == "CODCOLIGADA=0;CODSISTEMA=T;CODUSUARIO=gravacao.rm", j)
    chk("simular não chama o RM", not CHAMADAS)
    st, j = enviar("forn_cadastro", "teste-1", FORN)
    chk("operação desligada = 400", st == 400 and "desligada" in j.get("erro", ""), (st, j))
    cfg({"forn_cadastro": {"ativo": True, "tipo": "dataserver", "destino": "FinCFODataBR", "contexto": "CODCOLIGADA={coligada};CODSISTEMA=T;CODUSUARIO={usuario_rm}", "modelo": MODELO},
         "fora_lista": {"ativo": True, "tipo": "dataserver", "destino": "OutroDataBR", "modelo": "<X>{a}</X>"},
         "com_falta": {"ativo": True, "tipo": "dataserver", "destino": "FinCFODataBR", "modelo": "<X>{nao_existe}</X>"},
         "processo": {"ativo": True, "tipo": "processo", "destino": "ProcTeste", "modelo": "<Params><SC>{numeroSC}</SC></Params>"}})
    config.RM_GRAVACAO_ATIVA = False
    st, j = enviar("forn_cadastro", "teste-1", FORN)
    chk("gravação desligada no servidor = 503", st == 503, (st, j))
    config.RM_GRAVACAO_ATIVA = True
    st, j = enviar("fora_lista", "teste-2", {"a": "1"})
    chk("DataServer fora de RM_GRAVACAO_PERMITIDOS = 403", st == 403, (st, j))
    st, j = enviar("com_falta", "teste-3", {"a": "1", "coligada": "35"})
    chk("marcador sem valor = 400", st == 400 and "nao_existe" in j.get("erro", ""), (st, j))
    chk("nada foi enviado ao RM até aqui", not CHAMADAS, CHAMADAS)
    st, j = enviar("forn_cadastro", "teste-1", FORN)
    chk("grava e devolve a chave do RM", st == 200 and j.get("chave_rm") == "0;F0123", (st, j))
    c = CHAMADAS[-1] if CHAMADAS else {}
    chk("chamada SaveRecord no wsDataServer", c.get("url", "").endswith("/wsDataServer/IwsDataServer") and c.get("acao") == "http://www.totvs.com/IwsDataServer/SaveRecord", c)
    chk("envelope com DataServer, XML e contexto", "<tot:DataServerName>FinCFODataBR</tot:DataServerName>" in c.get("corpo", "") and "<![CDATA[<FinCFO>" in c.get("corpo", "") and "CODUSUARIO=gravacao.rm" in c.get("corpo", ""), c)
    chk("usa o usuário de gravação (não o de leitura)", c.get("auth") == ("gravacao.rm", "senha-gravacao"), c.get("auth"))
    n = len(CHAMADAS)
    st, j = enviar("forn_cadastro", "teste-1", FORN)
    chk("mesma chave não grava de novo", st == 200 and j.get("repetido") and len(CHAMADAS) == n, (st, j, len(CHAMADAS)))
    RESPOSTA["txt"] = "Campo obrigatório CODETD não informado. Verifique o cadastro de estados e tente novamente."
    st, j = enviar("forn_cadastro", "teste-4", FORN)
    chk("erro do RM = 502 com a mensagem do RM", st == 502 and "CODETD" in j.get("erro", ""), (st, j))
    st, j = enviar("processo", "teste-5", {"numeroSC": "4101", "coligada": "35"})
    chk("processo ExecuteWithXmlParams", st == 200 and CHAMADAS[-1]["acao"] == "http://www.totvs.com/IwsProcess/ExecuteWithXmlParams", (st, j))
    ATUAL["u"] = GRAVA
    RESPOSTA["txt"] = "0;F0999"
    st, j = enviar("forn_cadastro", "teste-6", FORN)
    chk("pessoa com rm_gravar grava", st == 200 and j.get("chave_rm") == "0;F0999", (st, j))
    st, j = enviar("forn_cadastro", "teste-6", FORN, simular=True)
    chk("só o administrador simula", st == 403, (st, j))
    r = cli.get("/api/rm/envios")
    L = (r.get_json() or {}).get("envios", [])
    chk("fila da pessoa: só os envios dela, sem o XML", r.status_code == 200 and L and all(x["quem_email"] == GRAVA["email"] for x in L) and all("xml" not in x for x in L), L[:2])
    ATUAL["u"] = ADM
    L = (cli.get("/api/rm/envios").get_json() or {}).get("envios", [])
    chk("fila do administrador: todos", len([x for x in L if str(x["chave"]).startswith("teste-")]) >= 4, len(L))
    with engine.connect() as cx:
        A = tabela("auditoria")
        n = cx.execute(select(A.c.id).where(A.c.tabela == "rm_envios", A.c.registro.like("%|teste-%"))).fetchall()
    chk("auditoria de cada gravação", len(n) >= 4, len(n))
    chk("estado do servidor", cli.get("/api/rm/gravacao/estado").get_json().get("ativa") is True)
finally:
    with engine.begin() as cx:
        cx.execute(delete(T).where(T.c.tipo == "param_rm_gravacao"))
        cx.execute(delete(RG.ENVIOS).where(RG.ENVIOS.c.chave.like("teste-%")))
        A = tabela("auditoria")
        cx.execute(delete(A).where(A.c.tabela == "rm_envios", A.c.registro.like("%|teste-%")))

print("PASSOU %d" % len(OK))
for x in OK:
    print("  ok  ", x)
print("FALHOU %d" % len(FALHA))
for x in FALHA:
    print("  XX  ", x)
sys.exit(1 if FALHA else 0)
