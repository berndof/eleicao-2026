# Perfil do eleitorado por município (gênero, idade, escolaridade), 2018

`tse_perfil_2018` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (Dados Abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2018.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2018.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/eleitorado-2018](https://dadosabertos.tse.jus.br/dataset/eleitorado-2018) |
| Cópia neste projeto (release) | — |
| Arquivo local | data/raw/perfil_eleitorado_2018.zip |
| Coletado em (UTC) | 2026-10-05T04:08:17Z |
| Tamanho (bytes) | 34851376 |
| Licença | CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026) |
| Granularidade | município × gênero × faixa etária × escolaridade |
| Período | eleitorado de 2018 |
| Camada da análise | 1 (dados brutos) → 3 (features) |
| SHA-256 | `d94cc9871ffbdbee3184c98b52c256560dffb5e19f62e27c91648a6fdfe4d803` |

## Onde é usada

data/interim/perfil_2018_mun.csv; tabela municipal em preparação, ainda NÃO entra nos modelos publicados

## Limitações

Perfil de quem pode votar, não de quem votou.

## Como conferir

```bash
sha256sum data/raw/perfil_eleitorado_2018.zip
```
