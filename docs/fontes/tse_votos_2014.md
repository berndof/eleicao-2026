# Votação por candidato × zona × município, todos os cargos, 2014

`tse_votos_2014` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (Dados Abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2014.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2014.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/resultados-2014](https://dadosabertos.tse.jus.br/dataset/resultados-2014) |
| Cópia neste projeto (release) | — |
| Arquivo local | data/raw/votacao_candidato_munzona_2014.zip |
| Coletado em (UTC) | 2026-10-05T04:08:38Z |
| Tamanho (bytes) | 494100168 |
| Licença | CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026) |
| Granularidade | zona eleitoral × município × candidato |
| Período | eleição de 2014 |
| Camada da análise | 1 (dados brutos) → 2 (tabelas municipais) |
| SHA-256 | `f41bceb427820c068b2b14b87befa69d8c333638644eea0e8337534f9b349fd3` |

## Onde é usada

data/interim/pres_2014_mun.csv e pres_2014_t2_mun.csv (filtro Presidente); tabela municipal em preparação; ainda NÃO entra nos modelos publicados (o M3 usa só o histórico nacional digitado, historico_2turnos)

## Limitações

Contém todos os cargos; só Presidente é usado. Votos nominais, sem brancos e nulos. Formato de colunas varia entre anos (2014 tem menos colunas).

## Como conferir

```bash
sha256sum data/raw/votacao_candidato_munzona_2014.zip
```
