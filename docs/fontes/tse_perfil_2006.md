# Perfil do eleitorado por município (gênero, idade, escolaridade), 2006

`tse_perfil_2006` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (Dados Abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2006.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2006.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/eleitorado-2006](https://dadosabertos.tse.jus.br/dataset/eleitorado-2006) |
| Cópia neste projeto (release) | — |
| Arquivo local | data/raw/perfil_eleitorado_2006.zip |
| Coletado em (UTC) | 2026-10-05T04:08:50Z |
| Tamanho (bytes) | 2268213 |
| Licença | CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026) |
| Granularidade | município × gênero × faixa etária × escolaridade |
| Período | eleitorado de 2006 |
| Camada da análise | 1 (dados brutos) → 3 (features) |
| SHA-256 | `7e08ce10070b073594a14550dfecd79b8108c887234cb17afb52f4193fa58e91` |

## Onde é usada

data/interim/perfil_2006_mun.csv; tabela municipal em preparação, ainda NÃO entra nos modelos publicados

## Limitações

Em 2002 e 2006 a faixa etária vem como código -3 (não informada): 'jovem' e 'idoso' não devem ser usados nesses anos.

## Como conferir

```bash
sha256sum data/raw/perfil_eleitorado_2006.zip
```
