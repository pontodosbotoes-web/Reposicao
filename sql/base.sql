WITH ProdutosBase AS
(
    SELECT
        p.IdProduto, p.CODPRODUTO, p.CodProdutoFabr, p.NOMEPRODUTO, p.UNID,
        p.CODFABR, f.NOMEFABR, g.NomeGrupo
    FROM Produtos p WITH (NOLOCK)
    LEFT JOIN Fabricantes f WITH (NOLOCK) ON f.CODFABR = p.CODFABR
    LEFT JOIN Grupos g      WITH (NOLOCK) ON g.IdGrupo  = p.IdGrupo
    WHERE
        LEFT(g.CodGrupo, 2) NOT IN ('09','10')
        AND (:fabricante = ''
             OR CAST(p.CODFABR AS VARCHAR(100)) LIKE '%' + :fabricante + '%'
             OR f.NOMEFABR LIKE '%' + :fabricante + '%')
        AND (:departamento = '' OR LEFT(g.CodGrupo, 2) LIKE '%' + :departamento + '%')
        AND (:grupo = ''        OR LEFT(g.CodGrupo, 5) LIKE '%' + :grupo + '%')
        AND (:subgrupo = ''     OR g.CodGrupo LIKE '%' + :subgrupo + '%'
                                OR g.NomeGrupo LIKE '%' + :subgrupo + '%')
        AND (:produto = ''
             OR CAST(p.CODPRODUTO AS VARCHAR(100)) LIKE '%' + :produto + '%'
             OR CAST(p.CodProdutoFabr AS VARCHAR(100)) LIKE '%' + :produto + '%'
             OR p.NOMEPRODUTO LIKE '%' + :produto + '%'
             OR EXISTS (
                 SELECT 1 FROM CodigoBarras cb WITH (NOLOCK)
                 WHERE cb.IdProduto = p.IdProduto
                   AND (
                       CAST(cb.CodigoBarras AS VARCHAR(100)) LIKE '%' + :produto + '%'
                       OR CAST(cb.GTIN AS VARCHAR(100)) LIKE '%' + :produto + '%'
                   )
             ))
),

UltimaCompra AS
(
    SELECT i.IdProduto,
        MAX(CAST(m.DtFinalizacao AS DATE)) AS DataUltimaCompra
    FROM ItensMov i WITH (NOLOCK)
    INNER JOIN Movimento m WITH (NOLOCK) ON m.IdMov = i.IdMov
    INNER JOIN ProdutosBase pb ON pb.IdProduto = i.IdProduto
    WHERE m.TipoMov = '1.1'
      AND m.CodCliFor NOT IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
      AND m.DtFinalizacao < DATEADD(DAY, 1, :data_referencia)
      AND m.CodFilial IN (1,2,3,4,5)
    GROUP BY i.IdProduto
),

Mov AS
(
    SELECT
        i.IdProduto,
        m.CodFilial,
        SUM(CASE WHEN m.TipoMov = '1.1'
                  AND m.CodCliFor NOT IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
                 THEN (i.Qtd - ISNULL(i.QtdCancel,0)) / NULLIF(i.FatorConvUnid,0) ELSE 0 END) AS QtdComprada,
        SUM(CASE WHEN m.CodCliFor IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
                  AND m.TipoMov IN ('1.1','1.2')
                 THEN (i.Qtd - ISNULL(i.QtdCancel,0)) / NULLIF(i.FatorConvUnid,0) ELSE 0 END) AS QtdRecebida,
        SUM(CASE WHEN m.CodCliFor IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
                  AND m.TipoMov IN ('2.2','2.4','2.9')
                  AND (m.TipoMov = '2.2' OR (m.TipoMov IN ('2.4','2.9') AND m.NfeStatus = 'U'))
                 THEN (i.Qtd - ISNULL(i.QtdCancel,0)) / NULLIF(i.FatorConvUnid,0) ELSE 0 END) AS QtdEnviada,
        SUM(CASE WHEN m.TipoMov = '2.4' AND m.NfeStatus = 'U'
                  AND m.CodCliFor NOT IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
                 THEN (i.Qtd - ISNULL(i.QtdCancel,0)) / NULLIF(i.FatorConvUnid,0) ELSE 0 END) AS QtdVendida,
        COUNT(DISTINCT CASE WHEN m.TipoMov = '2.4' AND m.NfeStatus = 'U'
                             AND m.CodCliFor NOT IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
                            THEN CAST(m.DtFinalizacao AS DATE) END) AS DiasAtivo
    FROM ItensMov i WITH (NOLOCK)
    INNER JOIN Movimento m WITH (NOLOCK) ON m.IdMov = i.IdMov
    INNER JOIN ProdutosBase pb ON pb.IdProduto = i.IdProduto
    WHERE m.DtFinalizacao >= DATEADD(DAY, -:max_lookback, :data_referencia)
      AND m.DtFinalizacao <  DATEADD(DAY, 1, :data_referencia)
      AND m.CodFilial IN (1,2,3,4,5)
      AND m.TipoMov IN ('1.1','1.2','2.2','2.4','2.9')
    GROUP BY i.IdProduto, m.CodFilial
),

ProdutoFilial AS
(
    SELECT pb.*, f.CodFilial,
        CASE f.CodFilial
            WHEN 1 THEN 'ALECRIM' WHEN 2 THEN 'VIA DIRETA' WHEN 3 THEN 'ZONA SUL'
            WHEN 4 THEN 'ZONA NORTE' WHEN 5 THEN 'ATACADO' END AS Filial
    FROM ProdutosBase pb
    CROSS JOIN (SELECT 1 AS CodFilial UNION ALL SELECT 2 UNION ALL SELECT 3
                UNION ALL SELECT 4 UNION ALL SELECT 5) f
    WHERE :filial = ''
       OR EXISTS (SELECT 1 FROM STRING_SPLIT(:filial, ',') s
                  WHERE LTRIM(RTRIM(s.value)) = CAST(f.CodFilial AS VARCHAR(100))
                     OR CAST(TRY_CAST(LTRIM(RTRIM(s.value)) AS INT) AS VARCHAR(100)) = CAST(f.CodFilial AS VARCHAR(100)))
)

SELECT
    pf.IdProduto,
    pf.CODPRODUTO      AS CodigoProduto,
    pf.CodProdutoFabr  AS ReferenciaFabricante,
    pf.NOMEPRODUTO     AS Produto,
    pf.UNID            AS Embalagem,
    pf.NOMEFABR        AS Fabricante,
    pf.NomeGrupo,
    pf.CodFilial       AS CodigoFilial,
    pf.Filial,

    uc.DataUltimaCompra,
    DATEDIFF(DAY, uc.DataUltimaCompra, :data_referencia) + 1 AS DiasDesdeCompra,

    CAST(CASE WHEN ISNULL(mv.DiasAtivo,0) = 0 THEN 0
              ELSE ISNULL(mv.QtdVendida,0) / NULLIF(mv.DiasAtivo,0) END
         AS DECIMAL(18,4)) AS VelocidadeAtiva,

    CAST(ISNULL(mv.QtdVendida,0) / NULLIF(:max_lookback, 0)
         AS DECIMAL(18,4)) AS VelocidadePeriodo,

    ISNULL(mv.DiasAtivo, 0) AS DiasAtivo,
    :max_lookback - ISNULL(mv.DiasAtivo, 0) AS DiasInativo,

    CAST(ISNULL(mv.QtdComprada,0)  AS DECIMAL(18,2)) AS QtdComprada,
    CAST(ISNULL(mv.QtdRecebida,0)  AS DECIMAL(18,2)) AS QtdRecebida,
    CAST(ISNULL(mv.QtdEnviada,0)   AS DECIMAL(18,2)) AS QtdEnviada,
    CAST(ISNULL(mv.QtdVendida,0)   AS DECIMAL(18,2)) AS QtdVendida,

    CAST(
        ISNULL(mv.QtdComprada,0) + ISNULL(mv.QtdRecebida,0)
        - ISNULL(mv.QtdEnviada,0) - ISNULL(mv.QtdVendida,0)
        AS DECIMAL(18,2)
    ) AS SaldoProvavel

FROM ProdutoFilial pf
LEFT JOIN UltimaCompra uc ON uc.IdProduto = pf.IdProduto
LEFT JOIN Mov mv ON mv.IdProduto = pf.IdProduto AND mv.CodFilial = pf.CodFilial
WHERE mv.IdProduto IS NOT NULL

ORDER BY pf.NOMEPRODUTO, pf.CodFilial
OPTION (MAXDOP 1);