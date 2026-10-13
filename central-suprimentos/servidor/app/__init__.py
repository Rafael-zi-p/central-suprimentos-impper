"""Central de Suprimentos — servidor Flask no padrão da Plataforma de Automações Impper.

Login Microsoft Entra (identity.flask) + sessão Redis + PostgreSQL. A tela é o
mesmo app de sempre (static/index.html), que conversa só com este servidor.
"""
from flask import Flask, redirect, request
from flask_session import Session
from identity.flask import Auth
from werkzeug.middleware.proxy_fix import ProxyFix

from . import config


def create_app():
    app = Flask(__name__, static_folder=None)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    app.config.from_object(config)
    Session(app)

    faltando = [k for k in ("AUTHORITY", "CLIENT_ID", "CLIENT_SECRET", "REDIRECT_URI") if not getattr(config, k)]
    if faltando:
        raise RuntimeError("Login Microsoft não configurado. Defina: " + ", ".join(faltando))
    auth = Auth(app, authority=config.AUTHORITY, client_id=config.CLIENT_ID,
                client_credential=config.CLIENT_SECRET, redirect_uri=config.REDIRECT_URI)
    app.extensions["pz_auth"] = auth

    from .ia import bp_ia
    from .rm_gravacao import bp_rm
    from .rotas_app import bp as bp_app, pagina_inicial
    from .rotas_db import bp as bp_db

    @app.get("/")
    @auth.login_required(scopes=["User.Read"])
    def inicio(*, context):
        return pagina_inicial()

    @app.get("/entrar")
    def entrar():
        """Endereço do botão "Central de Suprimentos" no portal da empresa (ex.: ImpperFlows).

        Quem já está logado vai direto para a tela; quem não está vai direto para o
        login Microsoft (sem a página intermediária e sem pedir a escolha da conta,
        então quem já entrou no portal com a conta da empresa não digita nada).
        ?aba=<id> abre a tela naquela aba, se a pessoa tiver acesso.
        """
        import re
        aba = re.sub(r"[^a-z0-9_-]", "", (request.args.get("aba") or "").lower())[:30]
        destino = "/?aba=" + aba if aba else "/"
        web = getattr(auth, "_auth", None)          # identity.web.Auth (no modo do PC não existe)
        if web is None or web.get_user():
            return redirect(destino)
        r = web.log_in(scopes=["User.Read"], redirect_uri=config.REDIRECT_URI, next_link=destino)
        if "error" in r or not r.get("auth_uri"):
            return redirect(destino)                # cai no login padrão
        return redirect(r["auth_uri"])

    @app.get("/logout")
    def sair():
        return auth.logout(request.host_url)

    @app.get("/saude")
    def saude():
        # usado pelo Coolify para saber se o app está de pé (não expõe nada)
        from sqlalchemy import text
        from .db import engine
        with engine.connect() as cx:
            cx.execute(text("select 1"))
        return {"ok": True}

    app.register_blueprint(bp_db)
    app.register_blueprint(bp_ia)
    app.register_blueprint(bp_rm)
    app.register_blueprint(bp_app)   # por último: tem a rota de arquivos estáticos

    @app.after_request
    def cabecalhos(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if resp.mimetype == "text/html":
            resp.headers.setdefault("Content-Security-Policy",
                # cdnjs/jsdelivr: leitor de PDF, OCR e Excel formatado (carregados só quando usados)
                "default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' blob: https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "worker-src 'self' blob: https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob:; "
                "connect-src 'self' https://brasilapi.com.br https://publica.cnpj.ws https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://tessdata.projectnaptha.com; "
                # frame-src: o botão "Abrir no app Outlook" usa um quadro escondido com mailto:
                "frame-src 'self' mailto: ms-outlook:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'")
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    return app
