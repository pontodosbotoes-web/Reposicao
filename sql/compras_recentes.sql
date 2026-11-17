SELECT
    m.Numero AS NumeroNF,
    CAST(m.DtFinalizacao AS DATE) AS DataCompra,
    m.DesCliFor AS NomeFornecedor,
    i.IdProduto,
    p.CODPRODUTO AS CodigoProduto,
    p.NOMEPRODUTO AS Produto,
    f.NOMEFABR AS Fabricante,
    (i.Qtd - ISNULL(i.QtdCancel,0)) * ISNULL(NULLIF(i.FatorConvUnid,0), 1) AS QtdComprada
FROM Movimento m WITH (NOLOCK)
INNER JOIN ItensMov i WITH (NOLOCK) ON m.IdMov = i.IdMov
INNER JOIN Produtos p WITH (NOLOCK) ON i.IdProduto = p.IdProduto
LEFT JOIN Fabricantes f WITH (NOLOCK) ON p.CODFABR = f.CODFABR
WHERE m.TipoMov = '1.1'
  AND m.CodLocal = '01'
  AND m.CodCliFor NOT IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
  AND m.DtFinalizacao >= DATEADD(DAY, -30, GETDATE())
ORDER BY m.DtFinalizacao DESC, m.Numero DESC;