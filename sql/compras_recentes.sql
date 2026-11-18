SELECT
    m.NumMov AS NumeroNF, 
    CAST(m.DtFinalizacao AS DATE) AS DataCompra,
    cf.NomeCliFor AS NomeFornecedor,
    CASE m.CodFilial 
        WHEN 1 THEN 'ALECRIM' 
        WHEN 2 THEN 'VIA DIRETA' 
        WHEN 3 THEN 'ZONA SUL' 
        WHEN 4 THEN 'ZONA NORTE' 
        WHEN 5 THEN 'ATACADO' 
        ELSE 'OUTRA' 
    END AS Filial,
    i.IdProduto,
    p.CODPRODUTO AS CodigoProduto,
    p.NOMEPRODUTO AS Produto,
    f.NOMEFABR AS Fabricante,
    CASE 
        WHEN ISNULL(p.ProdutoPesavel, 'N') = 'S' 
            THEN (i.Qtd - ISNULL(i.QtdCancel,0)) / NULLIF(i.FatorConvUnid,0)
        ELSE 
            CEILING((i.Qtd - ISNULL(i.QtdCancel,0)) / NULLIF(i.FatorConvUnid,0))
    END AS QtdComprada
FROM Movimento m WITH (NOLOCK)
INNER JOIN ItensMov i WITH (NOLOCK) ON m.IdMov = i.IdMov
INNER JOIN Produtos p WITH (NOLOCK) ON i.IdProduto = p.IdProduto
LEFT JOIN Fabricantes f WITH (NOLOCK) ON p.CODFABR = f.CODFABR
INNER JOIN Cli_For cf WITH (NOLOCK) ON m.CodCliFor = cf.CodCliFor
WHERE m.TipoMov = '1.1'
  AND m.CodLocal = '01'
  AND cf.CodCliFor LIKE 'F%'
  AND m.CodCliFor NOT IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
  AND m.DtFinalizacao >= DATEADD(DAY, -:dias_compra, GETDATE())
ORDER BY m.DtFinalizacao DESC, m.NumMov DESC;