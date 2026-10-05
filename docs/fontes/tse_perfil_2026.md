# Perfil do eleitorado por município (gênero, idade, escolaridade), 2026

`tse_perfil_2026` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (Dados Abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2026.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2026.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/eleitorado-2026](https://dadosabertos.tse.jus.br/dataset/eleitorado-2026) |
| Cópia neste projeto (release) | [https://github.com/berndof/eleicao-2026/releases/download/dados-brutos-2026-10-04/perfil_eleitorado_2026.zip](https://github.com/berndof/eleicao-2026/releases/download/dados-brutos-2026-10-04/perfil_eleitorado_2026.zip) |
| Arquivo local | data/raw/perfil_eleitorado_2026.zip |
| Coletado em (UTC) | 2026-10-05T02:24:29Z |
| Tamanho (bytes) | 408490728 |
| Licença | CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026) |
| Granularidade | município × gênero × faixa etária × escolaridade |
| Período | eleitorado de 2026 |
| Camada da análise | 1 (dados brutos) → 3 (features) |
| SHA-256 | `0952e9d9577be19380b444bfcc6a9a99397005e8dc839de9d5ec49914d75648b` |

## Onde é usada

data/interim/perfil_2026_mun.csv; features de escolaridade, idade e gênero do M1

## Limitações

Perfil de quem pode votar, não de quem votou.

## Como conferir

```bash
sha256sum data/raw/perfil_eleitorado_2026.zip
```
