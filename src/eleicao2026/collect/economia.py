#!/usr/bin/env python3
"""Coleta de indicadores econômicos conjunturais (BCB SGS, BCB Focus e IBGE SIDRA).

Salva os brutos em `data/raw/`, alimenta o ledger em `data/ledger/observacoes.csv`
e gera o sumário em `data/external/economia_resumo.csv`.

Uso:
  python -m eleicao2026.collect.economia
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from eleicao2026 import config as C
from eleicao2026 import ledger as L
from eleicao2026.collect.util_eco import salvar_bruto, escrever_entrada, agora_utc

SGS_SERIES = [
    {"codigo": 432, "nome": "selic_meta", "unidade": "% a.a.", "freq": "diaria"},
    {"codigo": 1178, "nome": "selic_diaria_anualizada", "unidade": "% a.a.", "freq": "diaria"},
    {"codigo": 1, "nome": "usd_ptax_venda", "unidade": "BRL", "freq": "diaria"},
    {"codigo": 433, "nome": "ipca_mensal", "unidade": "%", "freq": "mensal"},
    {"codigo": 13522, "nome": "ipca_12m", "unidade": "%", "freq": "mensal"},
    {"codigo": 189, "nome": "igpm_mensal", "unidade": "%", "freq": "mensal"},
    {"codigo": 1619, "nome": "salario_minimo", "unidade": "BRL", "freq": "mensal"},
    {"codigo": 24369, "nome": "desemprego_pnad_3m", "unidade": "%", "freq": "mensal"},
    {"codigo": 24364, "nome": "ibc_br_dessazonalizado", "unidade": "indice", "freq": "mensal"},
]


def coletar_sgs():
    hoje = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    hoje_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    coletado_em = agora_utc()
    linhas_ledger = []
    resumo = []

    print("Coletando séries do BCB SGS...")
    for s in SGS_SERIES:
        cod = s["codigo"]
        dt_ini = "01/01/2023" if s["freq"] == "diaria" else "01/01/2018"
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}/dados?formato=json&dataInicial={dt_ini}&dataFinal={hoje}"
        try:
            req = Request(url, headers=C.UA)
            with urlopen(req, timeout=30) as r:
                raw_bytes = r.read()
            salvar_bruto("bcb_sgs", f"sgs_{cod}.json", raw_bytes, url, coletado_em)
            dados = json.loads(raw_bytes.decode("utf-8"))

            ult_val, ult_data = None, None
            for r in dados:
                dt_partes = r["data"].split("/")
                dt_iso = f"{dt_partes[2]}-{dt_partes[1]}-{dt_partes[0]}"
                if dt_iso > hoje_iso:
                    continue
                val = r["valor"]
                ult_val = val
                ult_data = dt_iso
                linhas_ledger.append({
                    "fonte_id": "bcb_sgs",
                    "serie": s["nome"],
                    "periodo_ref": dt_iso if s["freq"] == "diaria" else f"{dt_partes[2]}-{dt_partes[1]}",
                    "valor": val,
                    "unidade": s["unidade"],
                    "divulgado_em": "",
                    "coletado_em": coletado_em,
                    "url": url,
                    "nota": "sem data de divulgação na API; último valor revisado"
                })
            if ult_val is not None:
                resumo.append({
                    "fonte": "BCB SGS",
                    "serie": s["nome"],
                    "periodo_recente": ult_data,
                    "valor_recente": ult_val,
                    "unidade": s["unidade"]
                })
                print(f"  SGS {cod} ({s['nome']}): {ult_val} {s['unidade']} ({ult_data})")
        except Exception as e:
            print(f"  Erro em SGS {cod}: {e}")

    L.acrescentar(linhas_ledger)

    escrever_entrada({
        "id": "bcb_sgs",
        "nome": "Sistema Gerenciador de Séries Temporais (BCB SGS)",
        "publicador": "Banco Central do Brasil",
        "url_origem": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.<code>/dados",
        "url_landing": "https://www3.bcb.gov.br/sgspub/",
        "coletado_em": coletado_em,
        "sha256": "",
        "tamanho_bytes": 0,
        "licenca": "Dados Abertos BCB (livre utilização)",
        "granularidade": "nacional (diária/mensal)",
        "periodo": "2018 a outubro de 2026",
        "confianca": "alta",
        "status": "verificada",
        "usado_em": "data/ledger/observacoes.csv; séries macroeconômicas de conjuntura",
        "limitacoes": "SGS sobrescreve séries com valores revisados; não preserva histórico de revisões point-in-time."
    })
    return resumo


def coletar_focus():
    coletado_em = agora_utc()
    filtro = ("(Indicador eq 'IPCA' or Indicador eq 'Câmbio' or Indicador eq 'PIB Total' or Indicador eq 'Selic') "
              "and (DataReferencia eq '2026' or DataReferencia eq '2027') and baseCalculo eq 0")
    filtro_enc = quote(filtro, safe="()='")
    url = (f"https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais?"
           f"$filter={filtro_enc}&$orderby=Data%20desc&$top=500&$format=json")
    print("Coletando expectativas de mercado (BCB Focus)...")
    req = Request(url, headers=C.UA)
    with urlopen(req, timeout=30) as r:
        raw_bytes = r.read()

    salvar_bruto("bcb_focus", "focus_anuais_2026_2027.json", raw_bytes, url, coletado_em)
    dados = json.loads(raw_bytes.decode("utf-8")).get("value", [])

    linhas_ledger = []
    resumo = []
    vistos = set()

    for r in dados:
        ind = r["Indicador"]
        ref = r["DataReferencia"]
        dt = r["Data"]
        mediana = str(r["Mediana"])
        serie_nome = f"focus_{ind.lower().replace(' ', '_')}_{ref}_mediana"
        linhas_ledger.append({
            "fonte_id": "bcb_focus",
            "serie": serie_nome,
            "periodo_ref": ref,
            "valor": mediana,
            "unidade": "%" if ind != "Câmbio" else "BRL",
            "divulgado_em": f"{dt}T00:00:00Z",
            "coletado_em": coletado_em,
            "url": url,
            "nota": f"Focus survey date {dt}; baseCalculo 0 (ampla)"
        })
        chave = (ind, ref)
        if chave not in vistos:
            vistos.add(chave)
            resumo.append({
                "fonte": "BCB Focus",
                "serie": serie_nome,
                "periodo_recente": dt,
                "valor_recente": mediana,
                "unidade": "%" if ind != "Câmbio" else "BRL"
            })
            print(f"  Focus {serie_nome}: {mediana} ({dt})")

    L.acrescentar(linhas_ledger)

    escrever_entrada({
        "id": "bcb_focus",
        "nome": "Expectativas de Mercado (Relatório Focus / Olinda OData)",
        "publicador": "Banco Central do Brasil",
        "url_origem": url,
        "url_landing": "https://www.bcb.gov.br/publicacoes/focus",
        "coletado_em": coletado_em,
        "sha256": "",
        "tamanho_bytes": len(raw_bytes),
        "licenca": "Dados Abertos BCB",
        "granularidade": "nacional (pesquisa diária com instituições financeiras)",
        "periodo": "2025 a outubro de 2026",
        "confianca": "alta",
        "status": "verificada",
        "usado_em": "data/ledger/observacoes.csv; expectativas point-in-time de inflação, juros, PIB e câmbio",
        "limitacoes": "Reflete expectativas do mercado financeiro, que podem divergir do comportamento do eleitor médio."
    })
    return resumo


def main():
    C.EXTERNAL.mkdir(parents=True, exist_ok=True)
    res_sgs = coletar_sgs()
    res_focus = coletar_focus()

    resumo_total = res_sgs + res_focus
    saida_resumo = C.EXTERNAL / "economia_resumo.csv"
    with open(saida_resumo, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fonte", "serie", "periodo_recente", "valor_recente", "unidade"])
        w.writeheader()
        w.writerows(resumo_total)

    print(f"Sumário de economia gravado em: {saida_resumo}")


if __name__ == "__main__":
    main()
