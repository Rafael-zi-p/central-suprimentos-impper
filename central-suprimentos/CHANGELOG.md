# Histórico de versões

## v3: servidor da empresa (07/10/2026)

**Infraestrutura**
- **Servidor Flask** no padrão da Plataforma de Automações:
  - login Microsoft Entra (`identity.flask`), sessão no Redis;
  - PostgreSQL com schema `suprimentos`;
  - Dockerfile para o Coolify.
- **Sem serviço externo**: a tela fala só com o próprio servidor.
- **Permissões conferidas no servidor**, com as mesmas regras do banco anterior, e auditoria gravada pelo servidor.
- **TOTVS pelo usuário de serviço**: ninguém digita senha do RM. Atualização automática no servidor, com agenda definida pelo administrador (rápida de SC e OC de 15 em 15 minutos, diária e completa semanal), com data "desde" única, definida pelo administrador.
- **Restrição por obra no servidor**: quem tem obras limitadas no perfil só recebe essas obras (proxy do RM, arquivos da atualização e `sc_itens`).
- **LGPD**: inventário de dados pessoais, retenção, pedido de titular e encerramento do ambiente de testes, com modelo de declaração (`docs/02-LGPD.md`).
- **Chat** pelo próprio servidor: mensagem privada só chega a quem deve.

**Regras de negócio e correções desde a v2.0**
- **SLA da obra:** conta da criação da SC até a data de necessidade. O prazo de entrega não é medido.
- **Aprovação da OC:** F = aprovada, A = pendente, C com OC ativa = rejeitada; aviso para quem criou e atalhos na aba OC.
- **Contratações (Pré-Compras):** fluxo da abertura pela obra até contrato assinado e OC, sem ZEEV: aprovação do GGO, triagem do Orçamento (início do SLA), negociação com mapa de aprovação, contrato (Engenharia, Jurídico e assinatura) e SC/OC em paralelo; papéis e prazos por tipo configuráveis; anexos por etapa. O mapa de aprovação é o quadro de contrato do Quadro de Cotação (vencedor e valor voltam sozinhos).
- **Atualização do TOTVS de 15 em 15 minutos:** agenda definida pelo administrador (rápida de SC e OC, diária com Verbas e Insumos, completa semanal), uma única tarefa agendada no servidor, e a tela recebe os dados novos sozinha, sem interromper quem está editando.
- **Data de entrega da OC fora do app:** é só trava do TOTVS; sai do PDF, do e-mail, do detalhe da OC, do Excel e do assistente. A necessidade da SC (obra) continua valendo.
- **Quadro de Cotação:** ao digitar a descrição do item, sugere insumos da Base de Insumos e preenche a unidade.
- **Visão Geral (09/10/2026):**
  - cada gráfico num quadro próprio (a volumetria e o prazo obra × comprador eram quadros com vários gráficos juntos);
  - cada quadro tem versão padrão, barras, colunas e pizza (e linhas nos quadros mês a mês), com a escolha do que medir;
  - filtro de obras e compradores no painel e também em cada quadro;
  - largura e altura de cada quadro ajustáveis (arrastando o canto ou pelo menu do quadro); os gráficos usam a largura real e não ficam mais espremidos;
  - "Meu dia" com um resumo do dia e o que fazer primeiro.
- **Ordem das abas por pessoa (10/10/2026):** em Configurações › Ordem das abas cada um organiza o menu (arrastar ou setas); fica no perfil e vale em qualquer computador.
- **Acesso pelo ImpperFlows (10/10/2026):**
  - rota `/entrar` para o botão do ImpperFlows: quem já está logado entra direto; quem não está vai direto ao login Microsoft, sem a página "Sign In" e sem escolher conta;
  - `?aba=<aba>` abre a Central direto numa aba, se a pessoa tiver acesso;
  - link **Voltar ao ImpperFlows** no menu (`PORTAL_URL`, `PORTAL_NOME`);
  - passo a passo em `docs/07`.
- **Assistente sem IA mais inteligente e objetivo (10/10/2026):**
  - entende a pergunta por pontuação de assunto e aceita erro de digitação ("regularisação", "fornecedro", "estque");
  - responde primeiro o número ou o nome, depois no máximo 5 linhas e um atalho para a tela certa; mostra o que entendeu (obra, período, insumo);
  - lembra da pergunta anterior: "e no mês passado?", "e na obra X?", "por fornecedor", "último preço";
  - assuntos novos: estoque e itens abaixo do mínimo, saídas do almoxarifado, OCs aprovadas a enviar ao fornecedor, OCs aguardando aprovação, pedidos de cadastro, pré-compras em validação, saldo da verba e dados do fornecedor (CNPJ, IE, contatos);
  - "quanto compramos" compara com o período anterior.
- **Almoxarifado (10/10/2026):** aba nova para o almoxarife da obra:
  - estoque por item (saldo, mínimo, local no almoxarifado e extrato), com alerta abaixo do mínimo;
  - saída (baixa) com destino (tarefa do orçamento, empreiteira, equipe, canteiro, perda), quem retirou e vários itens; entrada avulsa, devolução e transferência entre obras;
  - conferência dos recebimentos das OCs (quantidade conferida e divergência);
  - inventário com ajuste e aprovação; planilha dos movimentos;
  - saldo pela Central ou pelo RM (`CUBO.SUP.ESTOQUE`), movimentos do RM (`CUBO.SUP.ALMOMOV`) e gravação no RM das saídas, transferências, devoluções e ajustes (desligada até a homologação);
  - parâmetros em Configurações › Almoxarifado e permissão própria;
  - **começo do controle por obra**: data de início e saldo inicial por contagem (ou do zero); recebimentos de antes do início não contam (`docs/06`).
- **Gravação no RM parametrizada (10/10/2026):** tudo o que pode ir para o RM fica configurado em **Configurações › Gravação no RM**: cadastro de fornecedor, cadastro de insumo, informações do fornecedor, comprador responsável e observação do item da SC, marcações da SC e da OC, cotação e emissão da OC. Para cada uma: liga/desliga, DataServer ou processo, contexto, modelo do registro com marcadores, envio automático e simulação. O servidor grava (`app/rm_gravacao.py`, tabela `rm_envios`), com usuário só de gravação, lista fechada, permissão `rm_gravar`, sem gravar duas vezes e com auditoria. Vem **desligado**.
- **Fornecedor com vários contatos (10/10/2026):** o pedido de cadastro e a ficha aceitam outros contatos (nome, função, telefone, e-mail).
- **Fornecedores (10/10/2026):** a aba virou cadastro e consulta, além da avaliação:
  - lista do cadastro do RM com compras e nota das obras nos últimos 12 meses, e ficha de cada fornecedor com informações da equipe (o que vende, observações);
  - consulta pelo CNPJ traz da Receita razão social, endereço, situação, regime e **inscrição estadual**; CPF é validado (pessoa física não tem consulta pública);
  - **pedido de cadastro** no RM com os dados já preenchidos, anexos, aviso a quem cadastra, pedido de informação, conclusão com o código do RM e "Copiar dados para o RM".
- **PDF e e-mail da OC (09/10/2026):** logo em preto e maior; "Abrir no app Outlook" salva o e-mail formatado (.eml), que abre no Outlook do computador, e "E-mail padrão / Outlook web" abre pelo programa padrão; o navegador não imprime mais o cabeçalho que repetia o número da OC e a obra.
- **Pré-Compras:**
  - tickets e pacotes com quem criou e para quem foi direcionado;
  - categorias definidas pelo administrador;
  - ligação com cotação, SC e OC.
- **Ordens de Compra:**
  - PDF para o fornecedor com o tipo de cada item (produto ou serviço);
  - observação do TOTVS só sai no PDF e no assunto do e-mail se o comprador marcar (padrão: não sai), e pode ser copiada para editar;
  - marcações pela observação (regularização, caixinha, permuta);
  - aviso de número repetido em outro movimento.
- **Visão Geral:**
  - volumetria por comprador;
  - quadro de prazo obra × comprador;
  - gráficos repetidos removidos.
- **Análise completa do código:** cerca de 70 correções de cálculo, segurança e desempenho (detalhes no histórico do projeto).

## v2.0: referência (04/10/2026)

Versão entregue como referência funcional, para testes.
