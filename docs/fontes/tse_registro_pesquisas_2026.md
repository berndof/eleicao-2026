# Registro de pesquisas eleitorais 2026 (TSE) - Presidente, com contratante e pagante

`tse_registro_pesquisas_2026` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | Tribunal Superior Eleitoral (dados abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/pesquisa_eleitoral/pesquisa_eleitoral_2026.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/pesquisa_eleitoral/pesquisa_eleitoral_2026.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/pesquisas-eleitorais-2026](https://dadosabertos.tse.jus.br/dataset/pesquisas-eleitorais-2026) |
| Cópia neste projeto (release) | — |
| Arquivo local | — |
| Coletado em (UTC) | 2026-10-05T04:41:58Z |
| Tamanho (bytes) | 5889349 |
| Licença | Creative Commons Attribution (campo license_id='cc-by' do CKAN, lido em https://dadosabertos.tse.jus.br/api/3/action/package_show?id=pesquisas-eleitorais-2026) |
| Granularidade | uma linha por protocolo de registro de pesquisa; sem resultados (só metadados do registro) |
| Período | registros com fim de campo de 2026-01-11 a 2026-10-08 |
| Camada da análise | — |
| SHA-256 | `c6a987776ee23733b14ec4abe55bb8371b3fa22a30b4d472447c0dafce41e4fb` |

## Onde é usada

auditoria de proveniencia das pesquisas (data/processed/auditoria_pesquisas.csv); nao entra no modelo

## Limitações

Registro, nao resultado: nao traz percentuais. Arquivos regenerados diariamente (ver Last-Modified no manifesto). Varios registros 'Presidente' sao de universos estaduais. Margem de erro extraida por regex do texto livre (ausente em parte dos registros). Contratante/pagante pessoa fisica reduzido a categoria. Outros ZIPs do dataset (notas fiscais, questionarios, bairro/municipio, PDF) nao foram coletados.
