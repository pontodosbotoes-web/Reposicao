-- ============================================================
-- TRANSFERÊNCIAS EM TRÂNSITO
-- Saídas dos últimos N dias que ainda não foram recebidas
-- Parâmetros:
--   :data_referencia (date)
--   :dias_transito   (int) — geralmente = lead time
-- ============================================================
SELECT
    i.IdProduto,
    CASE m.CodCliFor
        WHEN 'C08327' THEN 1
        WHEN 'F00074' THEN 1
        WHEN 'C08328' THEN 2
        WHEN 'F10077' THEN 2
        WHEN 'C22206' THEN 3
        WHEN 'F15703' THEN 3
        WHEN 'C16205' THEN 4
        WHEN 'F14688' THEN 4
        WHEN 'C30965' THEN 5
        WHEN 'F16834' THEN 5
    END AS CodFilialDestino,
    SUM((i.Qtd - ISNULL(i.QtdCancel,0)) / NULLIF(i.FatorConvUnid,0)) AS QtdEmTransito,
    MAX(CAST(m.DtFinalizacao AS DATE)) AS DataEnvio
FROM ItensMov i WITH (NOLOCK)
INNER JOIN Movimento m WITH (NOLOCK) ON m.IdMov = i.IdMov
WHERE m.TipoMov IN ('2.2','2.4','2.9')
  AND m.CodCliFor IN ('C08327','F00074','C08328','F10077','C22206',
                      'F15703','C16205','F14688','C30965','F16834')
  AND m.DtFinalizacao >= DATEADD(DAY, -:dias_transito, :data_referencia)
  AND m.DtFinalizacao <  DATEADD(DAY, 1, :data_referencia)
  AND m.CodFilial IN (1,2,3,4,5)
GROUP BY i.IdProduto, m.CodCliFor;