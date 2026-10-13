# Central de Suprimentos: entrega v3 para a TI

| | |
|---|---|
| **O quê** | App de gestão de suprimentos (SC → Mesa → Cotação → OC → recebimento, prazos SLA, avaliação de fornecedores, Curva 25, orçado × comprado) |
| **Onde roda** | No servidor da empresa: Flask + PostgreSQL + Redis + Microsoft Entra, publicado pelo Coolify (padrão da Plataforma de Automações) |
| **Dependências externas** | Só o TOTVS RM (pelo servidor, com usuário de serviço) e o login Microsoft da empresa |
| **Titular** | Grupo Impper (Termo de Entrega e Cessão de Direitos, a ser assinado) |
| **Desenvolvido por** | Rafael Luís de Souza ([CREDITOS.md](CREDITOS.md)) |
| **Data** | 07/10/2026 |

## Comece por aqui

1. **[ENTREGA-COMPLETA.md](ENTREGA-COMPLETA.md)**: arquitetura, instalação passo a passo, variáveis, agendamentos, segurança e homologação.
2. **[docs/01-regras-de-negocio.md](docs/01-regras-de-negocio.md)**: as regras que o app calcula.
3. **[docs/03-abas-o-que-cada-uma-precisa.md](docs/03-abas-o-que-cada-uma-precisa.md)**: aba por aba, de onde vêm os dados, o que configurar e como conferir.
4. **[docs/05-gravacao-no-rm.md](docs/05-gravacao-no-rm.md)**: próximo passo, a Central gravar no RM (até emitir a OC pela Central): o que a TI prepara e em que ordem.
5. **[docs/06-almoxarifado-como-comecar.md](docs/06-almoxarifado-como-comecar.md)**: como cada obra começa a gestão de estoque na Central (data de início, saldo inicial, rotina).
6. **[docs/07-acesso-pelo-impperflows.md](docs/07-acesso-pelo-impperflows.md)**: passo a passo do botão da Central dentro do ImpperFlows (endereço `/entrar`, grupo do Entra, atalhos por aba, testes).

**Quer ver funcionando antes de publicar?** Siga o [RODAR-NO-PC.md](RODAR-NO-PC.md): sobe tudo no próprio PC com Docker (localhost).

## Instalação em 6 passos (detalhes no ENTREGA-COMPLETA)

1. Banco: rodar `banco/00-usuario-do-app.sql` e depois `banco/01-estrutura.sql`.
2. Entra: registrar o app com a URL de retorno `https://<endereço>/getAToken`.
3. RM: criar o usuário de serviço só de leitura e liberar as consultas `CUBO.SUP.*`.
4. Coolify: novo recurso a partir da pasta `servidor/` (Dockerfile), com as variáveis do `servidor/.env.exemplo`.
5. Agendar `python -m app.totvs_job auto` a cada 5 minutos (`*/5 * * * *`). O ritmo (rápida de 15 em 15 minutos, diária e completa) é definido pelo administrador na tela.
6. Entrar com um e-mail de `ADMIN_EMAILS`, definir "Buscar desde" e rodar a primeira atualização completa.

**O app começa limpo:** nada do ambiente de testes é importado. A configuração inicial é feita na tela (ENTREGA-COMPLETA §4.6 e §4.8). LGPD em `docs/02-LGPD.md`.
