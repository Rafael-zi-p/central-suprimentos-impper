# 07 — Botão da Central de Suprimentos dentro do ImpperFlows

A TI vai colocar um botão de acesso à Central no ImpperFlows (Plataforma de Automações). Este documento é o passo a passo. A Central já está preparada (10/10/2026): tem um endereço de entrada próprio para o botão (`/entrar`), abre direto numa aba (`?aba=`) e mostra um link de volta ao ImpperFlows.

## Como fica para quem usa

1. A pessoa está no ImpperFlows (já entrou com a conta Microsoft da empresa).
2. Clica em **Central de Suprimentos** no menu.
3. A Central abre numa aba nova do navegador, **sem pedir senha nem a escolha de conta**: o servidor da Central manda direto para o login Microsoft, que reconhece a conta já aberta e devolve a pessoa logada.
4. No menu da Central aparece **Voltar ao ImpperFlows**.

São dois apps separados, cada um com a sua sessão: o ImpperFlows não passa dados nem token para a Central. O "login único" vem da conta Microsoft do navegador.

## Decisões (já recomendadas)

| Ponto | Recomendação | Por quê |
|---|---|---|
| Abrir como? | **Link em aba nova** (`target="_blank"`) | A Central é um app de trabalho de dia inteiro; as duas telas ficam abertas lado a lado |
| Dentro de um quadro (iframe)? | **Não** | A Central bloqueia ser exibida dentro de outro site (`frame-ancestors 'none'` e `X-Frame-Options: DENY`). O login Microsoft também não abre dentro de quadro, e o cookie de sessão da Central (`SameSite=Lax`) não funcionaria lá dentro |
| Registro no Entra | **Registro próprio da Central** (separado do ImpperFlows) | Segredo e permissões independentes; trocar o segredo de um não derruba o outro. Mesmo locatário (tenant), então o login único funciona igual |
| Quem vê o botão | **O mesmo grupo do Entra** que pode entrar na Central | Quem vê o botão consegue entrar; quem não está no grupo não vê o botão e a Central recusa |
| Endereço | Subdomínio próprio, ex.: `https://suprimentos.grupoimpper.com.br` | Cookies e sessões separados do ImpperFlows |

## Passo a passo

### 1. Publicar a Central (se ainda não estiver)

Siga o [ENTREGA-COMPLETA.md](../ENTREGA-COMPLETA.md). Anote o endereço final, por exemplo `https://suprimentos.grupoimpper.com.br`.

### 2. Grupo do Entra para a Central

1. Crie (ou escolha) o grupo **Central de Suprimentos — Usuários** e coloque as pessoas que usam a Central: compradores, coordenação, obras, almoxarifes.
2. Na Central (variáveis do Coolify): `GRUPOS_ACESSO=<id do grupo>`. Pode ter mais de um, separados por vírgula.
3. O que cada pessoa vê **dentro** da Central (abas e obras) continua sendo definido em Configurações › Usuários & Permissões.

### 3. Variáveis novas na Central

No Coolify (recurso da Central), além das que já existem:

| Variável | Exemplo | Para quê |
|---|---|---|
| `PORTAL_URL` | `https://<endereço do ImpperFlows>/` | Mostra **Voltar ao ImpperFlows** no menu. Precisa começar com `https://`; vazio = sem link |
| `PORTAL_NOME` | `ImpperFlows` | Texto do link (padrão: ImpperFlows) |

Reinicie a Central depois de salvar.

### 4. Botão no ImpperFlows

**4.1 Variáveis no ImpperFlows** (Coolify do ImpperFlows):

| Variável | Exemplo |
|---|---|
| `CENTRAL_SUPRIMENTOS_URL` | `https://suprimentos.grupoimpper.com.br` |
| `CENTRAL_SUPRIMENTOS_GRUPO` | id do mesmo grupo do passo 2 (vazio = todos veem o botão) |

**4.2 Disponibilizar para os templates.** Em `api/app/routes.py`, na função `inject_info_user` (o `@app.context_processor` que já existe), acrescente as duas chaves:

```python
@app.context_processor
def inject_info_user():
    return {
        "info_user": getattr(g, 'info_user', None),
        "notificacoes": getattr(g, 'notificacoes', []),
        "central_url": (os.getenv("CENTRAL_SUPRIMENTOS_URL") or "").rstrip("/"),
        "central_grupo": os.getenv("CENTRAL_SUPRIMENTOS_GRUPO") or "",
    }
```

**4.3 Item no menu.** Em `api/app/templates/index.html`, dentro de `<ul class="imp-nav">` (por exemplo logo depois de "Relatórios"):

```html
{% if central_url and info_user and (not central_grupo or central_grupo in info_user.groups) %}
<li>
    <a class="imp-nav__link" href="{{ central_url }}/entrar" target="_blank" rel="noopener">
    <span class="imp-nav__icon" aria-hidden="true">▦</span>
    <span class="imp-nav__label">Central de Suprimentos</span>
    </a>
</li>
{% endif %}
```

O link aponta para **`/entrar`**, não para a raiz `/`. A raiz também funciona, mas mostra antes a página "Sign In" da biblioteca de login e a tela "escolha uma conta" da Microsoft; `/entrar` pula as duas.

**4.4 (Opcional) Atalhos direto para uma aba.** `…/entrar?aba=<aba>` abre a Central naquela aba. Por exemplo, um cartão na página inicial do ImpperFlows ou um link dentro do fluxo de Abertura de OC:

| `aba=` | Abre |
|---|---|
| `geral` | Visão Geral |
| `sc` | Solicitações de Compra |
| `mesa` | Mesa de Compras |
| `cotacao` | Quadro de Cotação |
| `oc` | Ordens de Compra |
| `regz` | Regularizações |
| `precompras` | Pré-Compras e contratações |
| `notas` | Anotações e tarefas |
| `insumos` | Base de Insumos |
| `verbas` | Verbas |
| `sla` | Prazos SLA |
| `forn` | Fornecedores (cadastro e avaliação) |
| `almox` | Almoxarifado |
| `cronograma` | Curva 25 |

Se a pessoa não tiver acesso à aba pedida, a Central abre normalmente e avisa: "Você não tem acesso à aba …".

### 5. Testar (homologação)

| # | Teste | Esperado |
|---|---|---|
| 1 | Pessoa do grupo, logada no ImpperFlows, clica no botão | A Central abre em aba nova, já logada, sem digitar nada |
| 2 | Primeiro acesso de alguém à Central | Pode aparecer **uma vez** a tela de consentimento da Microsoft (ler o perfil), dependendo da política do Entra. Para evitar, o administrador do Entra dá o consentimento em nome da organização |
| 3 | Pessoa fora do grupo | Não vê o botão; se digitar o endereço, a Central recusa ("Esta conta não tem acesso") |
| 4 | Link com `?aba=almox` | Abre direto no Almoxarifado; o endereço fica limpo depois |
| 5 | `?aba=` de uma aba sem permissão | Abre na primeira aba permitida, com o aviso |
| 6 | **Voltar ao ImpperFlows** no menu da Central | Abre o ImpperFlows (sempre na mesma aba do navegador, sem acumular abas) |
| 7 | Sair da Central | Encerra a sessão da Central e a sessão Microsoft do navegador. A sessão do ImpperFlows, que é dele, continua até expirar (30 min) ou até a pessoa sair de lá também |
| 8 | Teste automático da rota | `cd servidor && python testes/testar_entrar.py` → `FALHOU 0` |

### 6. Cuidados

- **Cookies e Redis:** os dois apps podem usar o mesmo Redis. A Central grava com o prefixo `suprimentos:` e usa o cookie `suprimentos_sessao`, então não conflita com a sessão do ImpperFlows.
- **Nada de token na URL:** o botão é só um link. Não passe e-mail, token ou id de usuário no endereço; a Central descobre quem é pela conta Microsoft.
- **Cadastros que existem nos dois:** o ImpperFlows já tem os fluxos de cadastro de fornecedor e de material; a Central tem pedido de cadastro com consulta de CNPJ e aviso de duplicado. Decidir com Processos qual fica valendo, para não ter dois caminhos para a mesma coisa. Se a escolha for o ImpperFlows, o botão "Solicitar cadastro" da Central pode passar a abrir o fluxo de lá: é um ajuste pequeno na Central, sob pedido.
- **Antes de pôr o botão no ar**, vale corrigir no ImpperFlows os pontos de segurança apontados no relatório de análise do ImpperFlows entregue à TI, principalmente os itens 1 a 4: o botão traz mais gente para dentro do ImpperFlows.
