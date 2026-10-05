# Votação por candidato × zona × município, todos os cargos, 2002

`tse_votos_2002` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (Dados Abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2002.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2002.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/resultados-2002](https://dadosabertos.tse.jus.br/dataset/resultados-2002) |
| Cópia neste projeto (release) | — |
| Arquivo local | data/raw/votacao_candidato_munzona_2002.zip |
| Coletado em (UTC) | 2026-10-05T04:08:54Z |
| Tamanho (bytes) | 120264128 |
| Licença | CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026) |
| Granularidade | zona eleitoral × município × candidato |
| Período | eleição de 2002 |
| Camada da análise | 1 (dados brutos) → 2 (tabelas municipais) |
| SHA-256 | `c1b7eabc9415ad853e10b11958c3e22ad6f248afbc6acb6a0cab38f4b25635ee` |

## Onde é usada

data/interim/pres_2002_mun.csv e pres_2002_t2_mun.csv (filtro Presidente); tabela municipal em preparação; ainda NÃO entra nos modelos publicados (o M3 usa só o histórico nacional digitado, historico_2turnos)

## Limitações

Contém todos os cargos; só Presidente é usado. Votos nominais, sem brancos e nulos. Formato de colunas varia entre anos (2014 tem menos colunas).

## Como conferir

```bash
sha256sum data/raw/votacao_candidato_munzona_2002.zip
```
