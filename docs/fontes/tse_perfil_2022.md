# Perfil do eleitorado por município (gênero, idade, escolaridade), 2022

`tse_perfil_2022` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (Dados Abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2022.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2022.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/eleitorado-2022](https://dadosabertos.tse.jus.br/dataset/eleitorado-2022) |
| Cópia neste projeto (release) | [https://github.com/berndof/eleicao-2026/releases/download/dados-brutos-2026-10-04/perfil_eleitorado_2022.zip](https://github.com/berndof/eleicao-2026/releases/download/dados-brutos-2026-10-04/perfil_eleitorado_2022.zip) |
| Arquivo local | data/raw/perfil_eleitorado_2022.zip |
| Coletado em (UTC) | 2026-10-05T02:24:29Z |
| Tamanho (bytes) | 76699889 |
| Licença | CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026) |
| Granularidade | município × gênero × faixa etária × escolaridade |
| Período | eleitorado de 2022 |
| Camada da análise | 1 (dados brutos) → 3 (features) |
| SHA-256 | `4bccad7e39ec13ea22a0ce4612d6147b4f06ee2c672cd5978112943951fb87e8` |

## Onde é usada

data/interim/perfil_2022_mun.csv; features de escolaridade, idade e gênero do M1

## Limitações

Perfil de quem pode votar, não de quem votou.

## Como conferir

```bash
sha256sum data/raw/perfil_eleitorado_2022.zip
```
