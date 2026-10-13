/* =========================================================
   DIAG.ESTOQUE.COLUNAS — só para conferir (não é usada pela Central)
   ---------------------------------------------------------
   Lista as colunas das tabelas usadas na CUBO.SUP.ESTOQUE, para achar o
   nome certo do saldo físico e da unidade se a consulta der erro de
   coluna. Sem parâmetros. Pode apagar depois de conferir.
   ========================================================= */

SELECT
    C.TABLE_NAME   AS TABELA,
    C.COLUMN_NAME  AS COLUNA,
    C.DATA_TYPE    AS TIPO
FROM INFORMATION_SCHEMA.COLUMNS C
WHERE C.TABLE_NAME IN ('TPRDLOC', 'TPRODUTODEF', 'TLOC')
  AND (C.COLUMN_NAME LIKE '%SALDO%' OR C.COLUMN_NAME LIKE '%UND%' OR C.COLUMN_NAME IN ('CODCOLIGADA', 'CODFILIAL', 'CODLOC', 'IDPRD', 'NOME'))
ORDER BY C.TABLE_NAME, C.COLUMN_NAME;
