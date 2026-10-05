#!/usr/bin/env python3
"""Coleta de mercados preditivos (Polymarket e verificação Kalshi).

Salva o evento e históricos em `data/raw/polymarket/`, grava os preços no ledger
(`data/ledger/observacoes.csv`) e exporta os mercados por UF para calibração
em `data/external/polymarket_mercados_uf.csv`.

Uso:
  python -m eleicao2026.collect.mercado
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from eleicao2026 import config as C
from eleicao2026 import ledger as L
from eleicao2026.collect.util_eco import salvar_bruto, escrever_entrada, agora_utc


def _get_json(url, timeout=30):
    req = Request(url, headers=C.UA)
    with urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def coletar_polymarket():
    coletado_em = agora_utc()
    print("1/3 Coletando evento principal Polymarket (45915)...")
    url_event = "https://gamma-api.polymarket.com/events/45915"
    req = Request(url_event, headers=C.UA)
    with urlopen(req, timeout=30) as r:
        raw_event = r.read()

    salvar_bruto("polymarket", "evento_45915_brasil.json", raw_event, url_event, coletado_em)
    event_data = json.loads(raw_event.decode("utf-8"))

    # Tokens de Lula e Flávio
    token_lula, token_flavio = None, None
    for m in event_data.get("markets", []):
        title = m.get("groupItemTitle", "").upper()
        tokens = json.loads(m.get("clobTokenIds", "[]")) if isinstance(m.get("clobTokenIds"), str) else m.get("clobTokenIds", [])
        if "LULA" in title and tokens:
            token_lula = tokens[0]  # YES token
        elif "FLÁVIO" in title or "FLAVIO" in title:
            if tokens:
                token_flavio = tokens[0]  # YES token

    linhas_ledger = []
    print("2/3 Coletando histórico diário CLOB (Lula e Flávio)...")
    for cand, token in [("lula", token_lula), ("flavio", token_flavio)]:
        if not token:
            continue
        url_hist = f"https://clob.polymarket.com/prices-history?market={token}&interval=max&fidelity=1440"
        try:
            req = Request(url_hist, headers=C.UA)
            with urlopen(req, timeout=30) as r:
                raw_hist = r.read()
            salvar_bruto("polymarket", f"historico_clob_{cand}.json", raw_hist, url_hist, coletado_em)
            hist = json.loads(raw_hist.decode("utf-8")).get("history", [])
            for pt in hist:
                ts = pt.get("t")
                dt_iso = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")
                dt_full = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                linhas_ledger.append({
                    "fonte_id": "polymarket",
                    "serie": f"polymarket_presidencia_{cand}_yes",
                    "periodo_ref": dt_iso,
                    "valor": str(pt.get("p")),
                    "unidade": "probabilidade (0-1)",
                    "divulgado_em": dt_full,
                    "coletado_em": coletado_em,
                    "url": url_hist,
                    "nota": "preço diário token YES (probabilidade implícita do mercado)"
                })
            print(f"  {cand}: {len(hist)} pontos diários coletados.")
        except Exception as e:
            print(f"  Erro ao buscar histórico CLOB de {cand}: {e}")

    L.acrescentar(linhas_ledger)

    print("3/3 Buscando mercados estaduais de 1º turno no Polymarket...")
    url_search = "https://gamma-api.polymarket.com/public-search?q=brazil%20presidential&limit_per_type=50"
    search_data = _get_json(url_search)

    mercados_uf = []
    for ev in search_data.get("events", []):
        title = ev.get("title", "")
        if "First Round: 1st Place in" in title or "1st Place in" in title:
            # Estado no título
            partes = title.split("1st Place in")
            uf_nome = partes[-1].strip() if len(partes) > 1 else ""
            for m in ev.get("markets", []):
                outcomes = json.loads(m.get("outcomes", "[]")) if isinstance(m.get("outcomes"), str) else m.get("outcomes", [])
                prices = json.loads(m.get("outcomePrices", "[]")) if isinstance(m.get("outcomePrices"), str) else m.get("outcomePrices", [])
                mercados_uf.append({
                    "event_id": ev.get("id"),
                    "titulo": title,
                    "estado": uf_nome,
                    "question": m.get("question"),
                    "outcomes": "; ".join(outcomes),
                    "outcome_prices": "; ".join(prices),
                    "closed": m.get("closed"),
                    "resolved": m.get("resolvedBy") is not None or m.get("closed") is True
                })

    saida_uf = C.EXTERNAL / "polymarket_mercados_uf.csv"
    if mercados_uf:
        with open(saida_uf, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(mercados_uf[0].keys()))
            w.writeheader()
            w.writerows(mercados_uf)
        print(f"Salvo {saida_uf} com {len(mercados_uf)} mercados estaduais.")

    escrever_entrada({
        "id": "polymarket_eleicao_2026",
        "nome": "Mercados Preditivos da Eleição Presidencial Brasileira (Polymarket)",
        "publicador": "Polymarket",
        "url_origem": "https://gamma-api.polymarket.com/events/45915",
        "url_landing": "https://polymarket.com/event/brazil-presidential-election",
        "coletado_em": coletado_em,
        "sha256": "",
        "tamanho_bytes": len(raw_event),
        "licenca": "Polymarket API Terms (dados públicos de trading)",
        "granularidade": "nacional e por estado (preços diários)",
        "periodo": "novembro de 2025 a outubro de 2026",
        "confianca": "media",
        "status": "verificada",
        "usado_em": "data/external/polymarket_mercados_uf.csv e data/ledger/observacoes.csv; apenas calibração e contexto externo (NÃO entra no modelo de projeção)",
        "limitacoes": "Preço de mercado preditivo reflete sentimento e liquidez de traders globais, não uma pesquisa eleitoral probabilística. Não deve ser usado como insumo para evitar circularidade."
    })


def verificar_kalshi():
    coletado_em = agora_utc()
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBRPRES-26"
    print("Verificando endpoint Kalshi...")
    status_msg = ""
    try:
        req = Request(url, headers=C.UA)
        with urlopen(req, timeout=5) as r:
            status_msg = f"HTTP {r.status}"
            st = "verificada"
    except Exception as e:
        status_msg = f"Falha de conexão / DNS ({type(e).__name__}: {e})"
        st = "nao_verificada"
        print(f"  Kalshi não acessível: {status_msg}")

    escrever_entrada({
        "id": "kalshi_eleicao_2026",
        "nome": "Mercados Regulados de Predição (Kalshi / KXBRPRES-26)",
        "publicador": "Kalshi",
        "url_origem": url,
        "url_landing": "https://kalshi.com",
        "coletado_em": coletado_em,
        "sha256": "",
        "tamanho_bytes": 0,
        "licenca": "Kalshi API Terms",
        "granularidade": "nacional",
        "periodo": "2026",
        "confianca": "baixa",
        "status": st,
        "usado_em": "catalogado, nao usado no modelo",
        "limitacoes": f"Tentativa de conexão falhou no ambiente de coleta: {status_msg}. Nenhuma observação coletada."
    })


def main():
    C.EXTERNAL.mkdir(parents=True, exist_ok=True)
    coletar_polymarket()
    verificar_kalshi()


if __name__ == "__main__":
    main()
