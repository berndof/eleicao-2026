# Votação por candidato × zona × município, todos os cargos, 2010

`tse_votos_2010` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (Dados Abertos) |
| Origem | [https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2010.zip](https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2010.zip) |
| Página da fonte | [https://dadosabertos.tse.jus.br/dataset/resultados-2010](https://dadosabertos.tse.jus.br/dataset/resultados-2010) |
| Cópia neste projeto (release) | — |
| Arquivo local | data/raw/votacao_candidato_munzona_2010.zip |
| Coletado em (UTC) | 2026-10-05T04:08:44Z |
| Tamanho (bytes) | 132565895 |
| Licença | CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026) |
| Granularidade | zona eleitoral × município × candidato |
| Período | eleição de 2010 |
| Camada da análise | 1 (dados brutos) → 2 (tabelas municipais) |
| SHA-256 | `fc7052974632351a3dc81e8ec17312889687eae0b2d56508259f91deecadd563` |

## Onde é usada

data/interim/pres_2010_mun.csv e pres_2010_t2_mun.csv (filtro Presidente); tabela municipal em preparação; ainda NÃO entra nos modelos publicados (o M3 usa só o histórico nacional digitado, historico_2turnos)

## Limitações

Contém todos os cargos; só Presidente é usado. Votos nominais, sem brancos e nulos. Formato de colunas varia entre anos (2014 tem menos colunas).

## Como conferir

```bash
sha256sum data/raw/votacao_candidato_munzona_2010.zip
```
