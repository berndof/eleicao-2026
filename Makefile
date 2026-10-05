PY ?= .venv/bin/python

.PHONY: help setup data fetch-raw collect model influence explain backtest figures all test clean-figures

help:
	@echo "make setup     - cria .venv e instala o pacote"
	@echo "make data      - baixa históricos/perfil do TSE (~1,1 GB) e gera tabelas por município (lento, 1x)"
	@echo "make fetch-raw  - baixa os dados brutos da release do GitHub e confere o SHA-256"
	@echo "make collect   - atualiza apuração do TSE e pesquisas (rápido; repetir a cada atualização)"
	@echo "make model     - projeção do 1º turno + ensemble do 2º turno"
	@echo "make influence  - influência de cada pesquisa (leave-one-out) + página docs/pesquisas.pt.md"
	@echo "make explain   - exemplos numéricos passo a passo (município, UF, decomposição do M1)"
	@echo "make backtest  - compara a projeção feita com 85% apurado com o resultado final"
	@echo "make figures   - gera todas as figuras (PT e EN) em figures/"
	@echo "make all       - collect + model + backtest + figures"
	@echo "make test      - testes"

setup:
	uv venv --python 3.13 .venv
	uv pip install --python $(PY) -e ".[dev]"

data:
	$(PY) -m eleicao2026.collect.tse_historico all

RAW_URL = https://github.com/berndof/eleicao-2026/releases/download/dados-brutos-2026-10-04
RAW_FILES = votacao_candidato_munzona_2022.zip perfil_eleitorado_2022.zip perfil_eleitorado_2026.zip tse_apuracao_20261005.tar.gz

fetch-raw:
	mkdir -p data/raw
	for f in $(RAW_FILES) SHA256SUMS.txt; do [ -s data/raw/$$f ] || curl -L --fail -o data/raw/$$f $(RAW_URL)/$$f; done
	cd data/raw && sha256sum -c --ignore-missing SHA256SUMS.txt

collect:
	$(PY) -m eleicao2026.collect.tse_apuracao
	$(PY) -m eleicao2026.collect.pesquisas

model:
	$(PY) -m eleicao2026.model.primeiro_turno
	$(PY) -m eleicao2026.model.ensemble

influence:
	$(PY) -m eleicao2026.model.influencia
	$(PY) -m eleicao2026.report_influencia

explain:
	$(PY) -m eleicao2026.model.explicar

backtest:
	$(PY) -m eleicao2026.model.backtest

figures:
	$(PY) -m eleicao2026.viz.figures

tables:
	$(PY) -m eleicao2026.report

all: collect model influence explain backtest figures tables

test:
	$(PY) -m pytest -q
