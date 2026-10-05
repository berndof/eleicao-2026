# Votação por candidato × zona × município, todos os cargos, 2022

`tse_votos_2022` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (Dados Abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2022.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2022.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/resultados-2022](https://dadosabertos.tse.jus.br/dataset/resultados-2022) |
| Cópia neste projeto (release) | [https://github.com/berndof/eleicao-2026/releases/download/dados-brutos-2026-10-04/votacao_candidato_munzona_2022.zip](https://github.com/berndof/eleicao-2026/releases/download/dados-brutos-2026-10-04/votacao_candidato_munzona_2022.zip) |
| Arquivo local | data/raw/votacao_candidato_munzona_2022.zip |
| Coletado em (UTC) | 2026-10-05T02:24:29Z |
| Tamanho (bytes) | 641972446 |
| Licença | CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026) |
| Granularidade | zona eleitoral × município × candidato |
| Período | eleição de 2022 |
| Camada da análise | 1 (dados brutos) → 2 (tabelas municipais) |
| SHA-256 | `b5bd20d7e2aee66c142ff38cebaaf7f31b84bc6aaaee1ae09ae4b66778c96b7d` |

## Onde é usada

data/interim/pres_2022_mun.csv e pres_2022_t2_mun.csv (filtro Presidente); base do M1 (swing 2022→2026)

## Limitações

Contém todos os cargos; só Presidente é usado. Votos nominais, sem brancos e nulos. Formato de colunas varia entre anos (2014 tem menos colunas).

## Como conferir

```bash
sha256sum data/raw/votacao_candidato_munzona_2022.zip
```
