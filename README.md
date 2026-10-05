# Eleição presidencial 2026 — projeção do 1º turno e previsão do 2º

[![license: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE) [![text: CC BY 4.0](https://img.shields.io/badge/text-CC%20BY%204.0-lightgrey.svg)](LICENSE) ![python](https://img.shields.io/badge/python-3.11%2B-blue)

🇧🇷 Português · [🇬🇧 English](README.en.md)

Modelo estatístico com dados públicos (TSE, pesquisas, IBGE) que **(1)** projeta o resultado final do 1º turno enquanto a apuração está incompleta e **(2)** prevê o 2º turno entre **Flávio Bolsonaro** e **Lula** (25/10/2026) combinando três métodos independentes. O repositório traz o pipeline completo, os dados, as 30.000 simulações e um artigo.

> ⚠️ Exercício de modelagem, **não** é pesquisa eleitoral nem recomendação de voto. Os intervalos do modelo são provavelmente estreitos demais (veja o backtest e as limitações).

## 📄 Leia o artigo

* **[docs/artigo.pt.md](docs/artigo.pt.md)** — texto completo, com gráficos
* [docs/article.en.md](docs/article.en.md) — English version
* **[docs/camadas.pt.md](docs/camadas.pt.md)** — **anatomia da análise, camada por camada**: o que cada etapa faz e como usamos cada pedacinho de dado, com números reais
* **[docs/pesquisas.pt.md](docs/pesquisas.pt.md)** — quais pesquisas entram, onde, e quanto cada uma pesa
* [docs/metodologia.md](docs/metodologia.md) · [docs/dados.md](docs/dados.md) · [docs/tabelas.pt.md](docs/tabelas.pt.md)
* **Dados brutos:** [release `dados-brutos-2026-10-04`](https://github.com/berndof/eleicao-2026/releases/tag/dados-brutos-2026-10-04) (TSE, 1,1 GB + JSON da apuração) — `make fetch-raw`

## Principais resultados (dados de 04/10/2026, 23h)

| | |
|---|---|
| 1º turno (99,99% apurado) | **Flávio 47,03% × Lula 45,16%** dos votos válidos |
| Backtest da projeção feita com 85% apurado | erro de **0,2 p.p. por candidato** (o parcial errava 1,4–1,6); vencedor certo em **28/28** UFs; mas o IC de 90% da margem nacional errou por 0,08 p.p. |
| Pesquisas de 1º turno | erraram em média **+3,8 p.p. na margem a favor de Lula** (12 institutos) |
| 2º turno — probabilidade de Lula vencer | **18%** no ensemble, mas de **0,3% a 41%** conforme o método (M1 estrutural / M2 pesquisas corrigidas / M3 histórico) |
| Lula nos válidos do 2º turno | média **48,1%** (IC 90%: 45,1% – 52,6%) |

![Distribuição do ensemble](figures/pt/09_distribuicao_ensemble.png)

![Backtest](figures/pt/02_backtest_nacional.png)

## Estrutura

```
eleicao-2026/
├── docs/                 artigo e camadas (PT/EN), pesquisas, metodologia, dicionário de dados, tabelas
├── figures/{pt,en}/      19 figuras por idioma (geradas por make figures)
├── data/
│   ├── raw/              brutos do TSE (~1,1 GB; na release do GitHub, não no git)
│   ├── external/         malha IBGE, wikitext das pesquisas, histórico, pesquisas de transferência
│   ├── interim/          tabelas por município
│   ├── processed/        saídas finais: resultado, projeção, backtest, simulações (versionadas)
│   └── snapshots/        fotografia dos dados de ~20h (85% apurado), base do backtest
├── src/eleicao2026/
│   ├── collect/          tse_apuracao, tse_historico, pesquisas
│   ├── model/            primeiro_turno, segundo_turno (M1), ensemble (M1+M2+M3), backtest,
│   │                     influencia (leave-one-out por pesquisa), explicar (exemplos passo a passo)
│   ├── viz/figures.py    gráficos e mapas
│   └── report.py         tabelas em Markdown
├── tests/                testes unitários
├── Makefile              make setup | data | collect | model | backtest | figures | all
└── pyproject.toml
```

## Como reproduzir

Requer Python ≥ 3.11 (e [`uv`](https://docs.astral.sh/uv/) para o `make setup`; dá para usar `pip`).

```bash
git clone https://github.com/berndof/eleicao-2026 && cd eleicao-2026
make setup      # cria .venv e instala o pacote
make fetch-raw  # baixa os dados brutos (~1,1 GB) da release e confere o SHA-256 (ou pule e use make data, direto do TSE)
make data       # 1x: gera as tabelas por município a partir dos brutos
make all        # coleta apuração + pesquisas, roda modelos, backtest, figuras e tabelas
make test
```

* O núcleo dos modelos usa **só a biblioteca padrão**; `matplotlib`/`numpy` são só para as figuras.
* Semente fixa: rodar `python -m eleicao2026.model.primeiro_turno --cur data/snapshots/20261004_2005_apuracao85/mun_2026.csv --tag snap85` reproduz exatamente a projeção publicada às ~20h.
* A coleta do TSE leva ~2 min (5.757 municípios); o ensemble, ~1 min.

## Atualizando com a apuração/pesquisas mais recentes

```bash
make collect model backtest figures tables
```

## Honestidade metodológica

* Pesos do ensemble (50/30/20) e fator de persistência do viés das pesquisas (0,4) são **suposições declaradas**; há análise de sensibilidade.
* As pesquisas de transferência (Quaest/Datafolha por eleitorado de cada eliminado) foram obtidas de resumos de busca (confiança média-baixa).
* A previsão está congelada na tag `previsao-2t-2026-10-04-v2` (a `-v2` corrige um erro da versão original, descrito na [errata](docs/camadas.pt.md#errata)); após o 2º turno será publicado um pós-mortem.

## Licença e citação

Código: [MIT](LICENSE). Texto e figuras: CC BY 4.0. Dados: dos produtores originais (TSE, IBGE, institutos; Wikipédia sob CC BY-SA). Veja [CITATION.cff](CITATION.cff).
