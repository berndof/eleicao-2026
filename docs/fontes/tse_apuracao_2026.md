# Apuração do 1º turno de 2026 (respostas JSON originais do portal de resultados)

`tse_apuracao_2026` · status: **verificada** · confiança: **alta**

| Campo | Valor |
|---|---|
| Publicador | TSE (portal de resultados) |
| Origem | [https://resultados.tse.jus.br/oficial/ele2026/6257](https://resultados.tse.jus.br/oficial/ele2026/6257) |
| Página da fonte | [https://resultados.tse.jus.br](https://resultados.tse.jus.br) |
| Cópia neste projeto (release) | [https://github.com/berndof/eleicao-2026/releases/download/dados-brutos-2026-10-04/tse_apuracao_20261005.tar.gz](https://github.com/berndof/eleicao-2026/releases/download/dados-brutos-2026-10-04/tse_apuracao_20261005.tar.gz) |
| Arquivo local | data/raw/tse_apuracao_20261005.tar.gz |
| Coletado em (UTC) | 2026-10-05T03:25:17Z |
| Tamanho (bytes) | 2695366 |
| Licença | nao_verificada (portal de resultados; os Dados Abertos do TSE são CC-BY) |
| Granularidade | município (5.757 respostas, mais a nacional e a configuração) |
| Período | coleta de 05/10/2026 00:11, 99,997% das seções |
| Camada da análise | 1 (dados brutos) → 2 (tabelas municipais) |
| SHA-256 | `221bd59ab75b656ca234712c0d8f616d4a5a5003f38fe10ef837ce56e942ef75` |

## Onde é usada

data/interim/mun_2026.csv (coleta anterior, de 23h25 de 04/10, 99,991%); esta coleta está em data/snapshots/20261005_apuracao_final/. Base do M1 e do backtest

## Limitações

Os modelos publicados usam a coleta de 04/10, não esta; a diferença é de ~0,006% do eleitorado.

## Como conferir

```bash
sha256sum data/raw/tse_apuracao_20261005.tar.gz
```
