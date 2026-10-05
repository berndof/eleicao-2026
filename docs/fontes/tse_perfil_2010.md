# Perfil do eleitorado por município (gênero, idade, escolaridade), 2010

`tse_perfil_2010` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (Dados Abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2010.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2010.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/eleitorado-2010](https://dadosabertos.tse.jus.br/dataset/eleitorado-2010) |
| Cópia neste projeto (release) | — |
| Arquivo local | data/raw/perfil_eleitorado_2010.zip |
| Coletado em (UTC) | 2026-10-05T04:08:45Z |
| Tamanho (bytes) | 35907120 |
| Licença | CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026) |
| Granularidade | município × gênero × faixa etária × escolaridade |
| Período | eleitorado de 2010 |
| Camada da análise | 1 (dados brutos) → 3 (features) |
| SHA-256 | `76360758f6285a94004c730d85ccd673c86d0c5a0d85e43f5574cc2e67f691c4` |

## Onde é usada

data/interim/perfil_2010_mun.csv; tabela municipal em preparação, ainda NÃO entra nos modelos publicados

## Limitações

Perfil de quem pode votar, não de quem votou.

## Como conferir

```bash
sha256sum data/raw/perfil_eleitorado_2010.zip
```
