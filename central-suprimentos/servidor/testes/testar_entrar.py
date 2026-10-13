"""Teste da rota /entrar (botão "Central de Suprimentos" no ImpperFlows).

Roda sozinho, sem banco e sem o servidor no ar, com a biblioteca de login real
(identity.flask) e um cliente fictício: confere que quem não está logado vai
direto para o login Microsoft (sem a página intermediária e sem "escolher conta")
e que o parâmetro ?aba= é limpo.

    cd servidor && python testes/testar_entrar.py
"""
import re
import tempfile
from urllib.parse import parse_qs, urlsplit

from flask import Flask, redirect, request
from identity.flask import Auth

REDIRECT = "https://central.exemplo/getAToken"
app = Flask(__name__)
app.config.update(SECRET_KEY="teste", SESSION_TYPE="filesystem", SESSION_FILE_DIR=tempfile.mkdtemp())
auth = Auth(app, authority="https://login.microsoftonline.com/common",
            client_id="00000000-0000-0000-0000-000000000001", client_credential="ficticio", redirect_uri=REDIRECT)


@app.get("/entrar")
def entrar():
    # mesma lógica de app/__init__.py › entrar()
    aba = re.sub(r"[^a-z0-9_-]", "", (request.args.get("aba") or "").lower())[:30]
    destino = "/?aba=" + aba if aba else "/"
    web = getattr(auth, "_auth", None)
    if web is None or web.get_user():
        return redirect(destino)
    r = web.log_in(scopes=["User.Read"], redirect_uri=REDIRECT, next_link=destino)
    if "error" in r or not r.get("auth_uri"):
        return redirect(destino)
    return redirect(r["auth_uri"])


OK, FALHA = [], []


def chk(nome, cond, extra=""):
    (OK if cond else FALHA).append(nome + ("" if cond else "  -> " + str(extra)[:200]))


c = app.test_client()
for q, aba in (("/entrar?aba=sc", "sc"), ("/entrar?aba=<script>almox", "scriptalmox"), ("/entrar", "")):
    resp = c.get(q)
    loc = resp.headers.get("Location", "")
    p = parse_qs(urlsplit(loc).query)
    chk(q + " → login Microsoft", resp.status_code == 302 and loc.startswith("https://login.microsoftonline.com/"), loc[:80])
    chk(q + " sem 'escolher conta'", "prompt" not in p, p.get("prompt"))
    chk(q + " volta para o REDIRECT_URI", p.get("redirect_uri") == [REDIRECT], p.get("redirect_uri"))
    with c.session_transaction() as s:
        fluxo = s.get("_auth_flow") or {}
    destino = [v for k, v in fluxo.items() if "next" in str(k).lower()]
    chk(q + " guarda o destino certo", destino == [("/?aba=" + aba) if aba else "/"], destino)

print("PASSOU %d" % len(OK))
for x in OK:
    print("  ok  ", x)
print("FALHOU %d" % len(FALHA))
for x in FALHA:
    print("  XX  ", x)
raise SystemExit(1 if FALHA else 0)
