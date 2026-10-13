# 05 — Gravar no RM: o caminho até a OC sair pela Central

Objetivo: a Central deixar de só **ler** o RM e passar a **alimentar** o RM, com uma base única de dados. O ponto de chegada é o comprador **emitir a OC pela própria Central**, com a OC nascendo no RM, vinculada à SC e passando pela aprovação normal do RM.

Este documento diz o que a TI precisa preparar no RM, o que muda no servidor da Central e em que ordem fazer. Os nomes de DataServers e processos citados são os usuais do RM; **a TI confirma os nomes exatos na versão do RM da empresa** antes de começar.

## 1. Como é hoje

- A Central **só lê** o RM. A tela pede ao servidor, e o servidor chama a API do RM (`RealizaConsulta`, as consultas `CUBO.SUP.*`) com o usuário de serviço (`rm_user`/`rm_senha`).
- O endereço `/totvs/*` do servidor aceita **só leitura** (GET), só das consultas liberadas em `TOTVS_CONSULTAS_PERMITIDAS`, e respeita as obras de cada perfil (`servidor/app/rotas_app.py`, `obras.py`).
- O que é só da Central (responsável pela SC, marcações, cotações, Pré-Compras, avaliações) fica no PostgreSQL da Central e **não volta ao RM**.

## 2. Regras que não mudam

1. **Nunca gravar direto nas tabelas do RM** (INSERT/UPDATE no SQL Server). O RM tem numeração, alçadas de aprovação, integridade entre tabelas e campos calculados que só rodam quando o registro é salvo pelo próprio RM. Gravação direta corrompe movimentos e tira o suporte da TOTVS.
2. **Toda gravação passa pela API do RM**: DataServers (salvam um registro como se fosse a tela do RM) e processos (executam uma rotina do RM, como gerar a OC a partir da SC).
3. **Toda gravação sai do servidor**, nunca do navegador. O navegador não tem nem verá a senha do usuário que grava.
4. **O RM é a fonte da verdade.** Depois de gravar, a próxima leitura traz o dado de volta e a Central passa a mostrar a versão do RM.
5. **Tudo começa na homologação** do RM. Produção só depois do aceite de cada etapa (seção 7).

## 3. O que a TI precisa preparar no RM

| # | Item | Para quê | Quem |
|---|---|---|---|
| 1 | **Ambiente de homologação** do RM com cópia recente da base | testar gravações sem risco | TI / TOTVS |
| 2 | **Serviços de gravação da API habilitados** no host do RM: `wsDataServer` (SaveRecord/ReadRecord) e `wsProcess` (execução de processos), ou os equivalentes REST da versão instalada | é por eles que a Central grava | TI |
| 3 | **Usuário de serviço só para gravação** (separado do `rm_user` de leitura), com perfil restrito: só os DataServers/processos combinados, só as coligadas em uso | limitar o estrago se a senha vazar | TI |
| 4 | **Campos complementares do movimento** (SC e OC) para o que não tem campo nativo: comprador responsável, marcação (regularização, urgência, caixinha, permuta), nº do quadro de cotação, ID da Central | levar ao RM o que hoje só existe na Central | TI |
| 5 | **Definição da cotação**: global × por item (conversa já aberta pelo Gabriel) e se o RM guarda a cotação no módulo de cotação ou só o vencedor na OC | decide a etapa 2 | TI + Suprimentos |
| 6 | **Tipo de movimento e regras da OC** que a Central vai gerar: quais tipos (1.1.10 a 1.1.22), série, filial, local de estoque, condições de pagamento aceitas, campos obrigatórios | montar a OC certa | TI + Suprimentos |
| 7 | **Aprovação da OC** continua no RM (alçadas). Confirmar que a OC criada pela API entra na mesma fila de aprovação | ninguém pula a alçada | TI |
| 8 | **Nomes exatos** dos DataServers e processos na versão instalada (ex.: movimentos `MovMovimentoTBCData`; geração da OC a partir da SC pelo processo de faturamento/recebimento de movimento) | o servidor chama por nome | TI / TOTVS |

## 4. O que já está pronto na Central (10/10/2026)

A parte da Central está feita e testada com um RM falso (`servidor/testes/testar_gravacao.py`, 24 de 24). **Vem desligada.** Falta só o que depende do RM (seção 3).

**Na tela — Configurações › Gravação no RM (administrador):** uma linha por operação que pode ir para o RM:

| Operação | Onde aparece na Central | Envio |
|---|---|---|
| Cadastro de fornecedor | Fornecedores › Pedidos de cadastro › **Gravar no RM** | botão, com resumo para confirmar |
| Cadastro de insumo | Base de Insumos › Solicitações de cadastro › **Gravar no RM** | botão, com resumo para confirmar |
| Informações do fornecedor (o que vende, observações, contatos) | ficha do fornecedor › Salvar | automático, se ligado |
| Comprador responsável pelo item da SC | SC, Mesa e Reunião do CUBO, ao definir o responsável | automático, se ligado |
| Observação do item da SC | detalhe do item, ao salvar | automático, se ligado |
| Marcações da SC e da OC (regularização, urgência) | detalhe da SC/OC, ao marcar | automático, se ligado |
| Almoxarifado: saída (baixa/requisição), transferência, devolução, entrada avulsa e ajuste de inventário | aba Almoxarifado, ao registrar (o ajuste, depois de aprovado) | automático, se ligado; o tipo de movimento de cada um vem de Configurações › Almoxarifado (`{tipoMov}`) |
| Cotação (quadro e vencedor) | Quadro de Cotação | depende da decisão do item 5 |
| Emitir a OC a partir da SC | Quadro de Cotação / Mesa | processo do RM (item 8) |

Para cada operação o administrador define: **ligada**, **automática** (quando cabe), **tipo** (DataServer com `SaveRecord` ou processo com `ExecuteWithXmlParams`), **nome no RM**, **contexto** (padrão `CODCOLIGADA={coligada};CODSISTEMA=T;CODUSUARIO={usuario_rm}`) e o **modelo do registro** em XML, com marcadores `{campo}` (a tela lista os campos de cada operação). O botão **Simular** mostra exatamente o que o servidor enviaria, sem enviar. Cadastro de fornecedor e de insumo vêm com um modelo de **exemplo** (FinCFO / TPRODUTO), para a TI conferir os campos na versão instalada. As demais a TI escreve conforme os campos complementares que criar.

**No servidor (`servidor/app/rm_gravacao.py`):**
- `POST /api/rm/envio` monta o registro com a configuração salva, escapa os valores, chama o RM com o **usuário de gravação** e guarda a resposta; `GET /api/rm/envios` mostra a fila (a pessoa vê os envios dela; o administrador, todos; o XML enviado não volta para a tela); `GET /api/rm/gravacao/estado` mostra se está ligado.
- Só grava com **todas** estas condições: `RM_GRAVACAO_ATIVA=1`, usuário de gravação configurado, nome do DataServer/processo em `RM_GRAVACAO_PERMITIDOS`, operação ligada na tela, modelo sem marcador desconhecido, pessoa com a permissão **`rm_gravar`** (Usuários & Permissões) ou administrador.
- **Não grava duas vezes** a mesma operação para o mesmo registro (a segunda chamada devolve a primeira).
- Toda gravação fica na tabela **`rm_envios`** (criada pelo `banco/01-estrutura.sql`) e na **auditoria**.
- A resposta do RM é lida assim: no DataServer, a chave do registro salvo (ex.: `0;F0123`) é sucesso e qualquer outro texto é a mensagem de erro do RM; no processo, `1` é sucesso. Quando o fornecedor ou o insumo é gravado, a Central conclui o pedido com o código devolvido e avisa quem pediu.

**Variáveis** (ENTREGA-COMPLETA §5): `RM_GRAVACAO_ATIVA`, `rm_grav_user` / `rm_grav_senha`, `RM_GRAVACAO_PERMITIDOS`, `RM_GRAVACAO_TIMEOUT`, `RM_WS_DATASERVER`, `RM_WS_PROCESS`.

**Ainda não feito (depois da homologação):** nova tentativa automática quando o RM está fora (hoje fica como "erro" na fila e o pedido continua aberto) e a conferência das obras do perfil em cada gravação (hoje vale a permissão `rm_gravar`).

## 5. Etapas, da mais simples à OC

### Etapa 1 — Dados da Central nos campos complementares da SC

Primeiro teste de ponta a ponta, com risco baixo: grava num movimento que já existe, sem criar nada.

- Grava na SC (campos complementares): **comprador responsável** e **marcações**.
- Pronto quando: definir o responsável na Central aparece no RM na SC certa, e a próxima leitura confirma.

### Etapa 2 — Cotação

Depende do item 5 da seção 3.

- **Se o RM guardar a cotação:** a Central envia o quadro (fornecedores, preços por item, condições, vencedor) para o módulo de cotação do RM.
- **Se o RM guardar só o vencedor:** a Central guarda o quadro e envia ao RM o nº do quadro e o vencedor, que vão para a OC na etapa 3.
- Pronto quando: a cotação (ou o vencedor) aparece no RM igual ao quadro da Central.

### Etapa 3 — Emitir a OC pela Central

- **Como:** a Central pede ao RM para **gerar a OC a partir da SC**, pelo mesmo processo que o comprador usa na tela do RM. Assim:
  - o **vínculo SC → OC** fica igual ao de hoje (a consulta `CUBO.SUP.OC` já lê esse vínculo);
  - o saldo da SC baixa;
  - a OC entra na **aprovação normal** do RM.
- **O que a Central envia:**
  - coligada, filial e tipo de movimento da OC;
  - fornecedor (código no RM), condição e forma de pagamento, frete;
  - itens (produto, quantidade, unidade, preço) e de qual item de SC cada um vem;
  - centro de custo e tarefa da verba;
  - observação, comprador e nº do quadro de cotação.
- **O que a Central recebe:** nº da OC gerada no RM. A OC aparece na aba Ordens de Compra como "aguardando aprovação". Depois de aprovada, segue o envio ao fornecedor que já existe (PDF e e-mail).
- Pronto quando: a OC criada pela Central é idêntica, no RM, a uma OC feita na tela do RM para a mesma SC (itens, valores, vínculo, aprovação).

### Etapa 4 — Produção

- Ligar em produção uma etapa por vez, primeiro para um ou dois compradores.
- Acompanhar a fila de envio por algumas semanas antes de liberar a todos.

## 6. Segurança

- **Permissão própria** `rm_gravar` no perfil, separada de ver as abas. Só quem pode emitir OC no RM recebe.
- O servidor confere, em toda gravação:
  - perfil ativo, permissão e obra liberada para a pessoa;
  - DataServer/processo na lista permitida;
  - valores dentro do esperado (quantidade, preço, fornecedor existente).
- **Senha só no servidor**: o usuário de gravação fica nas variáveis de ambiente do Coolify, como o de leitura hoje.
- **Sem gravação pelo navegador**: o endereço `/totvs/*` continua só leitura.

## 7. Testes e aceite (em homologação)

Para cada etapa:
1. **Caminho feliz:** gravar, conferir no RM pela tela e pela consulta.
2. **Recusa do RM:** campo obrigatório faltando, fornecedor bloqueado, SC sem saldo. A Central tem que mostrar o motivo do RM e não marcar como enviado.
3. **Repetição:** clicar duas vezes e simular queda de rede no meio. Tem que existir **um** registro no RM.
4. **Permissão:** pessoa sem `rm_gravar` é recusada pelo servidor (a conferência por obra entra depois da homologação).
5. **Auditoria:** a gravação aparece com quem, quando e o que foi enviado.

Só passa para produção com os cinco testes aprovados pela TI e por Suprimentos.

## 8. Perguntas para a TI e a TOTVS (para a primeira reunião)

1. Qual a versão do RM e quais serviços de gravação estão disponíveis (SOAP `wsDataServer`/`wsProcess` ou REST)? Estão habilitados no host?
2. Existe homologação? Com que frequência ela é atualizada com a produção?
3. Quem cria o usuário de gravação e os campos complementares?
4. Cotação: global ou por item? O RM guarda o quadro ou só o vencedor?
5. Qual processo do RM gera a OC a partir da SC na versão de vocês, e quais parâmetros ele pede?
6. Tipos de movimento, séries e campos obrigatórios da OC por coligada.
7. A OC criada pela API cai na mesma alçada de aprovação?

## 9. Divisão do trabalho

| Parte | Quem |
|---|---|
| Itens da seção 3 (ambiente, usuário, campos, definições) | TI, com apoio da TOTVS se precisar |
| Módulo de gravação, fila, rotas, permissões e telas (seção 4) | desenvolvimento da Central |
| Testes da seção 7 | TI + Suprimentos |
| Liberação em produção | TI, depois do aceite |
