# 06 — Almoxarifado: como começar a gestão de estoque

Hoje o estoque das obras não é controlado no RM: na coligada 35, a consulta de saldo (`CUBO.SUP.ESTOQUE`) não tem nenhuma linha e o saldo geral dos produtos está zerado (conferido em 10/10/2026). A gestão começa pela **Central**, com o saldo calculado por ela. O RM entra depois, quando a TI ligar a gravação (`docs/05`).

## Antes de começar (uma vez)

| # | O quê | Quem | Onde |
|---|---|---|---|
| 1 | Dar a permissão **Almoxarifado** aos almoxarifes (e as obras de cada um) | Administrador | Configurações › Usuários & Permissões |
| 2 | Conferir os **destinos da saída** (tarefa do orçamento, empreiteira, equipe, canteiro, perda…) e o que é obrigatório | Suprimentos | Configurações › Almoxarifado |
| 3 | Definir **quem aprova os ajustes** de inventário | Suprimentos | Configurações › Almoxarifado |
| 4 | Deixar o saldo pela **Central** (padrão) | Suprimentos | Configurações › Almoxarifado |

## Começar em cada obra

1. Na aba **Almoxarifado**, escolha a obra e clique em **Começar o controle nesta obra**.
2. **Data de início:** a partir dela, os recebimentos das OCs entram no estoque. Os de antes não contam, porque esse material já foi usado.
3. **Saldo inicial**, uma de duas formas:
   - **Contar o que tem hoje** (recomendado). A lista já vem com o que chegou pelas OCs nos últimos 90 dias, e dá para incluir qualquer item da Base de Insumos. Conte, digite as quantidades e clique em **Finalizar e começar o controle**.
   - **Começar do zero**: o estoque começa vazio e só conta o que chegar daqui em diante.
4. A partir daí a obra já tem saldo, extrato por item e alertas.

Dica: comece por uma obra-piloto por duas a quatro semanas, ajuste os destinos e os obrigatórios, e depois leve para as outras.

## Rotina do almoxarife

| Quando | O quê | Na aba |
|---|---|---|
| Ao receber material | **Conferir** o recebimento da OC (quantidade que chegou, divergência). É a quantidade conferida que entra no saldo. | Recebimentos |
| Sempre que sair material | **Registrar saída**: itens, destino, tarefa, quem retirou | botão Registrar saída |
| Material que volta da obra | **Devolução** | botão Devolução |
| Envio para outra obra | **Transferir** (sai daqui e entra lá) | botão Transferir |
| Toda semana | Ver os itens **abaixo do mínimo** e definir mínimo e local dos principais | Estoque › item |
| Todo mês | **Inventário** (todos os itens ou os de maior giro); a diferença vira ajuste para aprovar | Inventário |

## Para quem acompanha

- **Saídas por destino e por tarefa:** Saídas, com filtro de período e destino, e **Baixar planilha**.
- **Divergências de recebimento:** Recebimentos (o conferido diferente do recebido fica em vermelho).
- **Ajustes de inventário:** Inventário › ajustes aguardando aprovação.

## Depois: o RM

Para o RM passar a ser o dono do estoque:
1. A TI cadastra os **locais de estoque** de cada obra no RM.
2. Implanta o **saldo inicial no RM**. Um inventário feito na Central serve de base.
3. Liga a **Gravação no RM** das saídas, transferências, devoluções e ajustes (`docs/05`), com os tipos de movimento em Configurações › Almoxarifado.
4. Em Configurações › Almoxarifado, o saldo passa a ser **RM**. A Central mostra o saldo do RM menos as baixas que ainda não foram gravadas lá.
