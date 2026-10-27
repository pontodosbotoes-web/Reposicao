-- ============================================================
-- TRANSFERÊNCIAS RECEBIDAS RECENTEMENTE
-- Entradas por transferência nos últimos N dias
-- Parâmetros:
--   :data_referencia   (date)
--   :dias_reposicao    (int) — janela de "Reposição Recente"
-- ============================================================
SELECT
    i.IdProduto,
    m.CodFilial AS CodFilial,
    SUM((i.Qtd - ISNULL(i.QtdCancel,0)) / NULLIF(i.FatorConvUnid,0)) AS QtdRecebidaRecente,
    MAX(CAST(m.DtFinalizacao AS DATE)) AS DataRecebimento
FROM ItensMov i WITH (NOLOCK)
INNER JOIN Movimento m WITH (NOLOCK) ON m.IdMov = i.IdMov
WHERE m.TipoMov IN ('1.1','1.2')
  AND m.CodCliFor IN ('C08327','F00074','C08328','F10077','C22206',
                      'F15703','C16205','F14688','C30965','F16834')
  AND m.DtFinalizacao >= DATEADD(DAY, -:dias_reposicao, :data_referencia)
  AND m.DtFinalizacao <  DATEADD(DAY, 1, :data_referencia)
  AND m.CodFilial IN (1,2,3,4,5)
  AND m.CodLocal = '1'
GROUP BY i.IdProduto, m.CodFilial;