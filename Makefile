PY ?= .venv/bin/python

.PHONY: help setup data collect model backtest figures all test clean-figures

help:
	@echo "make setup     - cria .venv e instala o pacote"
	@echo "make data      - baixa históricos/perfil do TSE (~1,1 GB) e gera tabelas por município (lento, 1x)"
	@echo "make collect   - atualiza apuração do TSE e pesquisas (rápido; repetir a cada atualização)"
	@echo "make model     - projeção do 1º turno + ensemble do 2º turno"
	@echo "make backtest  - compara a projeção feita com 85% apurado com o resultado final"
	@echo "make figures   - gera todas as figuras (PT e EN) em figures/"
	@echo "make all       - collect + model + backtest + figures"
	@echo "make test      - testes"

setup:
	uv venv --python 3.13 .venv
	uv pip install --python $(PY) -e ".[dev]"

data:
	$(PY) -m eleicao2026.collect.tse_historico all

collect:
	$(PY) -m eleicao2026.collect.tse_apuracao
	$(PY) -m eleicao2026.collect.pesquisas

model:
	$(PY) -m eleicao2026.model.primeiro_turno
	$(PY) -m eleicao2026.model.ensemble

backtest:
	$(PY) -m eleicao2026.model.backtest

figures:
	$(PY) -m eleicao2026.viz.figures

tables:
	$(PY) -m eleicao2026.report

all: collect model backtest figures tables

test:
	$(PY) -m pytest -q
