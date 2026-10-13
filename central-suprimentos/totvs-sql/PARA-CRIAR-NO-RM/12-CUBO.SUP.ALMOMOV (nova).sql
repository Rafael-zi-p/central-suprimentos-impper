/* =========================================================
   CUBO.SUP.ALMOMOV — movimentos de estoque lançados no RM na obra
   ---------------------------------------------------------
   Uso na Central: aba Almoxarifado › Movimentos › "Movimentos de estoque
   no RM" (entradas por nota, requisições/saídas, transferências, ajustes).
   A Central classifica cada tipo de movimento (CODTMV) pelo papel definido
   em Configurações › Almoxarifado (entrada, saída, transferência, ajuste);
   tipo sem papel não aparece. Por isso este SQL traz todos os movimentos
   com local de estoque, menos SC e OC (1.1.xx), que já vêm de outras
   consultas.

   Código no RM: CUBO.SUP.ALMOMOV (criada e testada em 10/10/2026).
   Parâmetros: :CODCOLIGADA_N, :DATAINI_D, :DATAFIM_D
   Uma linha por item de movimento.

   CONFERIR ANTES DE CRIAR:
     1. Se os tipos de movimento de estoque da empresa não ficam fora de
        1.1.xx, ajuste o filtro do CODTMV (no fim do WHERE).
     2. CODLOCDESTINO só existe em movimentos de transferência; se a coluna
        não existir na versão do RM, apague a linha.
     3. Movimentos cancelados (STATUS = 'C') ficam de fora.

   Tabelas e colunas já usadas nas consultas validadas (CUBO.SUP.OC e
   CUBO.SUP.OCDOC): TMOV, TITMMOV, TPRODUTO, TMOVHISTORICO, GCCUSTO.

   Colunas que a Central espera (remapeáveis em Configurações › Consultas
   TOTVS › Movimentos do almoxarifado):
     CODCOLIGADA, NUMERO_MOV, CODTMV, NOME_TMV, DATA_MOV, STATUS,
     CODIGO_INSUMO, NOME_INSUMO, UNIDADE, QUANTIDADE, CODLOC,
     LOCAL_ESTOQUE, CODLOC_DESTINO, CENTRO_CUSTO, USUARIO, HISTORICO
   ========================================================= */

SELECT
    M.CODCOLIGADA,
    M.NUMEROMOV                                   AS NUMERO_MOV,
    M.CODTMV,
    TMV.NOME                                      AS NOME_TMV,
    CAST(M.DATAEMISSAO AS DATE)                   AS DATA_MOV,
    M.STATUS,
    I.NSEQITMMOV                                  AS ITEM_MOV,
    PROD.CODIGOPRD                                AS CODIGO_INSUMO,
    PROD.NOMEFANTASIA                             AS NOME_INSUMO,
    I.CODUND                                      AS UNIDADE,
    I.QUANTIDADE                                  AS QUANTIDADE,
    I.PRECOUNITARIO                               AS PRECO_UNITARIO,
    COALESCE(I.CODLOC, M.CODLOC)                  AS CODLOC,
    LOC.NOME                                      AS LOCAL_ESTOQUE,
    M.CODLOCDESTINO                               AS CODLOC_DESTINO,   -- conferir (item 2)
    CC.NOME                                       AS CENTRO_CUSTO,
    M.USUARIOCRIACAO                              AS USUARIO,
    CAST(HIS.HISTORICOCURTO AS VARCHAR(1000))     AS HISTORICO

FROM TMOV M (NOLOCK)

INNER JOIN TITMMOV I (NOLOCK)
    ON  I.CODCOLIGADA = M.CODCOLIGADA
    AND I.IDMOV       = M.IDMOV

LEFT JOIN TPRODUTO PROD (NOLOCK)
    ON  PROD.IDPRD = I.IDPRD

LEFT JOIN TTMV TMV (NOLOCK)
    ON  TMV.CODCOLIGADA = M.CODCOLIGADA
    AND TMV.CODTMV      = M.CODTMV

LEFT JOIN TLOC LOC (NOLOCK)
    ON  LOC.CODCOLIGADA = M.CODCOLIGADA
    AND LOC.CODFILIAL   = M.CODFILIAL
    AND LOC.CODLOC      = COALESCE(I.CODLOC, M.CODLOC)

LEFT JOIN GCCUSTO CC (NOLOCK)
    ON  CC.CODCOLIGADA = M.CODCOLIGADA
    AND CC.CODCCUSTO   = COALESCE(I.CODCCUSTO, M.CODCCUSTO)

LEFT JOIN TMOVHISTORICO HIS (NOLOCK)
    ON  HIS.CODCOLIGADA = M.CODCOLIGADA
    AND HIS.IDMOV       = M.IDMOV

WHERE
    M.CODCOLIGADA = :CODCOLIGADA_N
    AND M.DATAEMISSAO >= :DATAINI_D
    AND M.DATAEMISSAO <  DATEADD(DAY, 1, :DATAFIM_D)
    AND M.STATUS <> 'C'
    AND COALESCE(I.CODLOC, M.CODLOC) IS NOT NULL
    AND M.CODTMV NOT LIKE '1.1.%'                  -- SC e OC ficam nas outras consultas (item 1)

ORDER BY
    M.DATAEMISSAO,
    M.NUMEROMOV,
    I.NSEQITMMOV;
