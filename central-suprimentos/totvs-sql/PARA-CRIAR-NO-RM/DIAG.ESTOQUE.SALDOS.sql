/* =========================================================
   DIAG.ESTOQUE.SALDOS — só para conferir (não é usada pela Central)
   ---------------------------------------------------------
   A CUBO.SUP.ESTOQUE rodou sem linhas na coligada 35. Esta consulta mostra,
   para a coligada do parâmetro, quantas linhas de saldo existem e em qual
   das colunas SALDOFISICO1…10 há valor. A coluna com mais itens "com saldo"
   é a que a empresa usa como saldo atual.

   Parâmetro: :CODCOLIGADA_N
   Resultado em 2 blocos:
     ORIGEM = TPRDLOC     → saldo por local de estoque (o que a Central usa)
     ORIGEM = TPRODUTODEF → saldo geral do produto na coligada (sem local)
   Se TODAS as contagens vierem 0, o estoque não é controlado no RM nesta
   coligada: use o saldo pela Central (Configurações › Almoxarifado).
   ========================================================= */

SELECT
    'TPRDLOC'                                                        AS ORIGEM,
    COUNT(*)                                                         AS LINHAS,
    COUNT(DISTINCT PL.CODLOC)                                        AS LOCAIS,
    SUM(CASE WHEN COALESCE(PL.SALDOFISICO1 ,0) <> 0 THEN 1 ELSE 0 END) AS COM_SALDO_1,
    SUM(CASE WHEN COALESCE(PL.SALDOFISICO2 ,0) <> 0 THEN 1 ELSE 0 END) AS COM_SALDO_2,
    SUM(CASE WHEN COALESCE(PL.SALDOFISICO3 ,0) <> 0 THEN 1 ELSE 0 END) AS COM_SALDO_3,
    SUM(CASE WHEN COALESCE(PL.SALDOFISICO4 ,0) <> 0 THEN 1 ELSE 0 END) AS COM_SALDO_4,
    SUM(CASE WHEN COALESCE(PL.SALDOFISICO5 ,0) <> 0 THEN 1 ELSE 0 END) AS COM_SALDO_5,
    SUM(CASE WHEN COALESCE(PL.SALDOFISICO6 ,0) <> 0 THEN 1 ELSE 0 END) AS COM_SALDO_6,
    SUM(CASE WHEN COALESCE(PL.SALDOFISICO7 ,0) <> 0 THEN 1 ELSE 0 END) AS COM_SALDO_7,
    SUM(CASE WHEN COALESCE(PL.SALDOFISICO8 ,0) <> 0 THEN 1 ELSE 0 END) AS COM_SALDO_8,
    SUM(CASE WHEN COALESCE(PL.SALDOFISICO9 ,0) <> 0 THEN 1 ELSE 0 END) AS COM_SALDO_9,
    SUM(CASE WHEN COALESCE(PL.SALDOFISICO10,0) <> 0 THEN 1 ELSE 0 END) AS COM_SALDO_10
FROM TPRDLOC PL (NOLOCK)
WHERE PL.CODCOLIGADA = :CODCOLIGADA_N

UNION ALL

SELECT
    'TPRODUTODEF',
    COUNT(*),
    0,
    SUM(CASE WHEN COALESCE(PD.SALDOGERALFISICO,0) <> 0 THEN 1 ELSE 0 END),
    0, 0, 0, 0, 0, 0, 0, 0, 0
FROM TPRODUTODEF PD (NOLOCK)
WHERE PD.CODCOLIGADA = :CODCOLIGADA_N;
