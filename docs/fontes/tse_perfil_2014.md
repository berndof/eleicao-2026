# Perfil do eleitorado por município (gênero, idade, escolaridade), 2014

`tse_perfil_2014` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (Dados Abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2014.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2014.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/eleitorado-2014](https://dadosabertos.tse.jus.br/dataset/eleitorado-2014) |
| Cópia neste projeto (release) | — |
| Arquivo local | data/raw/perfil_eleitorado_2014.zip |
| Coletado em (UTC) | 2026-10-05T04:08:40Z |
| Tamanho (bytes) | 32269026 |
| Licença | CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026) |
| Granularidade | município × gênero × faixa etária × escolaridade |
| Período | eleitorado de 2014 |
| Camada da análise | 1 (dados brutos) → 3 (features) |
| SHA-256 | `a4276a1aeaae888a6a1df17ee2cd44f52b82778460cf39f40f9f5c2126e34f11` |

## Onde é usada

data/interim/perfil_2014_mun.csv; tabela municipal em preparação, ainda NÃO entra nos modelos publicados

## Limitações

Perfil de quem pode votar, não de quem votou.

## Como conferir

```bash
sha256sum data/raw/perfil_eleitorado_2014.zip
```
