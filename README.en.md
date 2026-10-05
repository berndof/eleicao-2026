# Brazil 2026 presidential election — first-round projection and runoff forecast

[![license: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE) [![text: CC BY 4.0](https://img.shields.io/badge/text-CC%20BY%204.0-lightgrey.svg)](LICENSE) ![python](https://img.shields.io/badge/python-3.11%2B-blue)

[🇧🇷 Português](README.md) · 🇬🇧 English

A statistical model built on public data (TSE, polls, IBGE) that **(1)** projects the final first-round result while the count is incomplete and **(2)** forecasts the **Flávio Bolsonaro vs. Lula** runoff (25 Oct 2026) by combining three independent methods. The repo contains the full pipeline, the data, 30,000 simulations and an article.

> ⚠️ A modelling exercise — **not** an opinion poll nor a voting recommendation. The model's intervals are probably too narrow (see the backtest and limitations).

## 📄 Read the article

* **[docs/article.en.md](docs/article.en.md)** — full text with charts
* [docs/artigo.pt.md](docs/artigo.pt.md) — Portuguese version
* **[docs/layers.en.md](docs/layers.en.md)** — **anatomy of the analysis, layer by layer**: what each step does and how every piece of data is used, with real numbers
* **[docs/polls.en.md](docs/polls.en.md)** — which polls enter, where, and how much each weighs
* [docs/tables.en.md](docs/tables.en.md) (generated tables) · [docs/metodologia.md](docs/metodologia.md) and [docs/dados.md](docs/dados.md) (Portuguese)
* **Raw data:** [release `dados-brutos-2026-10-04`](https://github.com/berndof/eleicao-2026/releases/tag/dados-brutos-2026-10-04) (TSE, 1.1 GB + the original count JSON) — `make fetch-raw`

## Key results (data as of 4 Oct 2026, 11pm)

| | |
|---|---|
| First round (99.99% counted) | **Flávio 47.03% vs. Lula 45.16%** of valid votes |
| Backtest of the projection made at 85% counted | **0.2 pp error per candidate** (the partial count was off by 1.4–1.6); correct winner in **28/28** units; but the 90% interval for the national margin missed by 0.08 pp |
| First-round polls | erred on average **+3.8 pp on the margin in Lula's favor** (12 pollsters) |
| Runoff — probability that Lula wins | **18%** for the ensemble, but **0.3% to 41%** depending on the method (M1 structural / M2 adjusted polls / M3 historical) |
| Lula's share of runoff valid votes | mean **48.1%** (90% CI: 45.1% – 52.6%) |

![Ensemble distribution](figures/en/09_distribuicao_ensemble.png)

![Backtest](figures/en/02_backtest_nacional.png)

## Layout

```
eleicao-2026/
├── docs/                 article (PT/EN), methodology, data dictionary, generated tables
├── figures/{pt,en}/      19 figures per language (make figures)
├── data/
│   ├── raw/              raw TSE data (~1.1 GB; in the GitHub release, not in git)
│   ├── external/         IBGE map, polls wikitext, history, transfer polls
│   ├── interim/          per-municipality tables
│   ├── processed/        final outputs: results, projection, backtest, simulations (versioned)
│   └── snapshots/        frozen ~8pm data (85% counted), basis of the backtest
├── src/eleicao2026/
│   ├── collect/          tse_apuracao, tse_historico, pesquisas
│   ├── model/            primeiro_turno, segundo_turno (M1), ensemble (M1+M2+M3), backtest,
│   │                     influencia (per-poll leave-one-out), explicar (worked examples)
│   ├── viz/figures.py    charts and maps
│   └── report.py         Markdown tables
├── tests/                unit tests
├── Makefile              make setup | data | collect | model | backtest | figures | all
└── pyproject.toml
```

Module and column names are in Portuguese (the data are Brazilian); see [docs/dados.md](docs/dados.md).

## Reproduce

Requires Python ≥ 3.11 (and [`uv`](https://docs.astral.sh/uv/) for `make setup`; `pip` works too).

```bash
git clone https://github.com/berndof/eleicao-2026 && cd eleicao-2026
make setup      # creates .venv and installs the package
make fetch-raw  # downloads the raw data (~1.1 GB) from the release and checks SHA-256 (or skip and use make data, straight from TSE)
make data       # once: builds the per-municipality tables from the raw data
make all        # fetches count + polls, runs models, backtest, figures and tables
make test
```

* The models' core uses **only the standard library**; `matplotlib`/`numpy` are only for figures.
* Fixed seed: `python -m eleicao2026.model.primeiro_turno --cur data/snapshots/20261004_2005_apuracao85/mun_2026.csv --tag snap85` exactly reproduces the projection published at ~8pm.
* The TSE fetch takes ~2 min (5,757 municipalities); the ensemble ~1 min.

## Refreshing with the latest count/polls

```bash
make collect model backtest figures tables
```

## Methodological honesty

* Ensemble weights (50/30/20) and the poll-bias persistence factor (0.4) are **declared assumptions**; there is a sensitivity analysis.
* Transfer polls (Quaest/Datafolha by each eliminated candidate's voters) come from search summaries (medium-low confidence).
* The forecast is frozen at tag `previsao-2t-2026-10-04-v2` (`-v2` fixes an error in the original version, described in the [erratum](docs/layers.en.md#erratum)); a post-mortem will be published after the runoff.

## License and citation

Code: [MIT](LICENSE). Text and figures: CC BY 4.0. Data: original producers (TSE, IBGE, pollsters; Wikipedia under CC BY-SA). See [CITATION.cff](CITATION.cff).
