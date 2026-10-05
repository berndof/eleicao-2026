# Perfil do eleitorado por município (gênero, idade, escolaridade), 2002

`tse_perfil_2002` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (Dados Abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2002.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2002.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/eleitorado-2002](https://dadosabertos.tse.jus.br/dataset/eleitorado-2002) |
| Cópia neste projeto (release) | — |
| Arquivo local | data/raw/perfil_eleitorado_2002.zip |
| Coletado em (UTC) | 2026-10-05T04:08:54Z |
| Tamanho (bytes) | 2244531 |
| Licença | CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026) |
| Granularidade | município × gênero × faixa etária × escolaridade |
| Período | eleitorado de 2002 |
| Camada da análise | 1 (dados brutos) → 3 (features) |
| SHA-256 | `45737185ef698107a3e54419ec12614bef7867df30055707cec8fb8aef1453b7` |

## Onde é usada

data/interim/perfil_2002_mun.csv; tabela municipal em preparação, ainda NÃO entra nos modelos publicados

## Limitações

Em 2002 e 2006 a faixa etária vem como código -3 (não informada): 'jovem' e 'idoso' não devem ser usados nesses anos.

## Como conferir

```bash
sha256sum data/raw/perfil_eleitorado_2002.zip
```
