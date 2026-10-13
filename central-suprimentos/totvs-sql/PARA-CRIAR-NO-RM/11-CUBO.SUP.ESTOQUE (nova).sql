/* =========================================================
   CUBO.SUP.ESTOQUE — saldo do almoxarifado por item e local de estoque
   ---------------------------------------------------------
   Uso na Central: aba Almoxarifado, quando "Saldo do estoque" está como RM
   (Configurações › Almoxarifado). A Central mostra este saldo menos as
   saídas que o almoxarife lançou na Central e que ainda não foram para o RM.

   Parâmetro: :CODCOLIGADA_N  (a obra/coligada)
   Uma linha por item × local de estoque, só com saldo diferente de zero.

   Versão 2 (10/10/2026): a unidade vem da definição do produto na
   coligada (TPRODUTODEF.CODUNDCONTROLE) — na TPRODUTO essa coluna não
   existe ("Invalid column name 'CODUNDCONTROLE'"). O custo médio saiu
   (era opcional).

   CONFERIR SE DER ERRO:
     1. A coluna de saldo físico. No RM existem várias (SALDOFISICO1,
        SALDOFISICO2…); a que vale como "saldo atual" é a definida nos
        parâmetros do Estoque da empresa. Este SQL usa SALDOFISICO2.
        Para ver as colunas da tabela, rode a DIAG.ESTOQUE.COLUNAS
        (arquivo ao lado).
     2. Se a unidade ainda der erro, apague a linha do UNIDADE e o
        LEFT JOIN TPRODUTODEF: a Central completa a unidade pela Base
        de Insumos.

   Colunas que a Central espera (podem ser remapeadas em
   Configurações › Consultas TOTVS › Estoque do almoxarifado):
     CODCOLIGADA, CODFILIAL, CODLOC, LOCAL_ESTOQUE, CODIGO_INSUMO,
     NOME_INSUMO, UNIDADE, SALDO
   ========================================================= */

SELECT
    PL.CODCOLIGADA,
    PL.CODFILIAL,
    PL.CODLOC,
    LOC.NOME                          AS LOCAL_ESTOQUE,
    PROD.CODIGOPRD                    AS CODIGO_INSUMO,
    PROD.NOMEFANTASIA                 AS NOME_INSUMO,
    PD.CODUNDCONTROLE                 AS UNIDADE,        -- item 2 acima
    PL.SALDOFISICO2                   AS SALDO           -- item 1 acima

FROM TPRDLOC PL (NOLOCK)

INNER JOIN TPRODUTO PROD (NOLOCK)
    ON  PROD.IDPRD = PL.IDPRD

LEFT JOIN TPRODUTODEF PD (NOLOCK)
    ON  PD.CODCOLIGADA = PL.CODCOLIGADA
    AND PD.IDPRD       = PL.IDPRD

LEFT JOIN TLOC LOC (NOLOCK)
    ON  LOC.CODCOLIGADA = PL.CODCOLIGADA
    AND LOC.CODFILIAL   = PL.CODFILIAL
    AND LOC.CODLOC      = PL.CODLOC

WHERE
    PL.CODCOLIGADA = :CODCOLIGADA_N
    AND COALESCE(PL.SALDOFISICO2, 0) <> 0

ORDER BY
    LOC.NOME,
    PROD.NOMEFANTASIA;
