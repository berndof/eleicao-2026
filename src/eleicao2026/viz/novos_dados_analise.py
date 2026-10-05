#!/usr/bin/env python3
"""Gera figuras analíticas avançadas baseadas nos novos dados coletados:
  20_religiao_censo_e_voto.png
  21_renda_urbanizacao_e_voto.png
  22_prefeitos_2024_e_presidencial.png
  23_polymarket_trajetoria.png
  24_auditoria_pesquisas_custos_financiadores.png
  25_rejeicao_datafolha_2026.png

Salva em figures/pt/ e figures/en/.
Uso: python -m eleicao2026.viz.novos_dados_analise
"""
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from eleicao2026 import config as C

COR_LULA = "#c0392b"
COR_FLAVIO = "#2980b9"
COR_NEUTRO = "#7f8c8d"


def carregar_dados_municipais():
    mun_data = {}
    with open(C.INTERIM / "mun_2026.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["uf"] == "zz":
                continue
            vv = float(r["vv"]) if float(r.get("vv", 0)) > 0 else 1
            lula = float(r.get("v_LULA", 0)) / vv * 100
            flavio = float(r.get("v_FLAVIO BOLSONARO", 0)) / vv * 100
            mun_data[(r["uf"], r["cd"])] = {"vv": vv, "lula_pct": lula, "flavio_pct": flavio, "nome": r["nome"]}

    censo_data = {}
    with open(C.EXTERNAL / "censo2022_mun.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            chave = (r["uf"], r["cd_tse"])
            if chave in mun_data:
                try:
                    censo_data[chave] = {
                        "evang": float(r["pct_evangelica_10mais"]) if r.get("pct_evangelica_10mais") else None,
                        "catol": float(r["pct_catolica_10mais"]) if r.get("pct_catolica_10mais") else None,
                        "renda": float(r["renda_media_percapita_2022"]) if r.get("renda_media_percapita_2022") else None,
                        "urb": float(r["pct_urbana_2022"]) if r.get("pct_urbana_2022") else None,
                        "preta_parda": float(r["pct_preta_parda_2022"]) if r.get("pct_preta_parda_2022") else None,
                        "pop": float(r["populacao_2022"]) if r.get("populacao_2022") else None,
                        **mun_data[chave]
                    }
                except Exception:
                    pass

    pref_data = {}
    with open(C.EXTERNAL / "prefeitos_2024_mun.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pref_data[(r["uf"], r["cd_tse"])] = r["sg_partido"]

    return censo_data, pref_data


def fig20_religiao(dados, out_dir, lang="pt"):
    """Figura 20: Religião no Censo 2022 vs Votação Presidencial 2026."""
    xs = [d["evang"] for d in dados.values() if d["evang"] is not None]
    ys_lula = [d["lula_pct"] for d in dados.values() if d["evang"] is not None]
    ys_flavio = [d["flavio_pct"] for d in dados.values() if d["evang"] is not None]
    pesos = [d["vv"] for d in dados.values() if d["evang"] is not None]

    w_norm = np.array(pesos) / sum(pesos)
    r_l = np.corrcoef(xs, ys_lula)[0, 1]
    r_f = np.corrcoef(xs, ys_flavio)[0, 1]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)

    # Lula
    sc1 = ax1.scatter(xs, ys_lula, s=np.array(pesos)/25000 + 3, alpha=0.25, color=COR_LULA, edgecolors="none")
    m_l, b_l = np.polyfit(xs, ys_lula, 1, w=np.sqrt(w_norm))
    x_lin = np.linspace(min(xs), max(xs), 100)
    ax1.plot(x_lin, m_l * x_lin + b_l, color="darkred", lw=2.5, label=f"Tendência (r = {r_l:+.2f})")
    ax1.set_xlabel("% População Evangélica (10+ anos, Censo 2022)" if lang=="pt" else "% Evangelical (Census 2022)", fontsize=11)
    ax1.set_ylabel("% Votos Válidos Lula (1º Turno 2026)" if lang=="pt" else "% Valid Votes Lula (1st Round 2026)", fontsize=11)
    ax1.set_title("Votação de Lula x População Evangélica" if lang=="pt" else "Lula Vote Share vs Evangelical Share", fontsize=12, fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper right")

    # Flávio
    sc2 = ax2.scatter(xs, ys_flavio, s=np.array(pesos)/25000 + 3, alpha=0.25, color=COR_FLAVIO, edgecolors="none")
    m_f, b_f = np.polyfit(xs, ys_flavio, 1, w=np.sqrt(w_norm))
    ax2.plot(x_lin, m_f * x_lin + b_f, color="navy", lw=2.5, label=f"Tendência (r = {r_f:+.2f})")
    ax2.set_xlabel("% População Evangélica (10+ anos, Censo 2022)" if lang=="pt" else "% Evangelical (Census 2022)", fontsize=11)
    ax2.set_ylabel("% Votos Válidos Flávio (1º Turno 2026)" if lang=="pt" else "% Valid Votes Flávio (1st Round 2026)", fontsize=11)
    ax2.set_title("Votação de Flávio Bolsonaro x População Evangélica" if lang=="pt" else "Flávio Vote Share vs Evangelical Share", fontsize=12, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper left")

    plt.suptitle("Censo 2022 e Urna 2026: Religião e Comportamento Eleitoral por Município" if lang=="pt"
                 else "Census 2022 & 2026 Election: Religion and Voting Patterns by Municipality",
                 fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(out_dir / "20_religiao_censo_e_voto.png", dpi=180)
    plt.close()


def fig21_renda_urb(dados, out_dir, lang="pt"):
    """Figura 21: Renda Domiciliar e Raça vs Voto em 2026."""
    rendas = [d["renda"] for d in dados.values() if d["renda"] is not None]
    racas = [d["preta_parda"] for d in dados.values() if d["preta_parda"] is not None]
    ys_lula = [d["lula_pct"] for d in dados.values() if d["renda"] is not None]
    pesos = [d["vv"] for d in dados.values() if d["renda"] is not None]

    r_renda = np.corrcoef(rendas, ys_lula)[0, 1]
    r_raca = np.corrcoef(racas, [d["lula_pct"] for d in dados.values() if d["preta_parda"] is not None])[0, 1]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # Renda vs Lula
    ax1.scatter(rendas, ys_lula, s=np.array(pesos)/25000 + 3, alpha=0.25, color="#8e44ad", edgecolors="none")
    m1, b1 = np.polyfit(rendas, ys_lula, 1)
    xr = np.linspace(min(rendas), max(rendas), 100)
    ax1.plot(xr, m1 * xr + b1, color="indigo", lw=2.5, label=f"Tendência (r = {r_renda:+.2f})")
    ax1.set_xlabel("Rendimento Médio Domiciliar Per Capita (R$, Censo 2022)" if lang=="pt" else "Mean Household Per Capita Income (BRL)", fontsize=11)
    ax1.set_ylabel("% Votos Lula (1º Turno 2026)" if lang=="pt" else "% Lula Votes (1st Round 2026)", fontsize=11)
    ax1.set_title("Renda Per Capita x Voto em Lula" if lang=="pt" else "Income per Capita vs Lula Vote Share", fontsize=12, fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Raça (% Preta/Parda) vs Lula
    ys_lula_raca = [d["lula_pct"] for d in dados.values() if d["preta_parda"] is not None]
    ax2.scatter(racas, ys_lula_raca, s=np.array(pesos)/25000 + 3, alpha=0.25, color="#d35400", edgecolors="none")
    m2, b2 = np.polyfit(racas, ys_lula_raca, 1)
    xrc = np.linspace(min(racas), max(racas), 100)
    ax2.plot(xrc, m2 * xrc + b2, color="#ba4a00", lw=2.5, label=f"Tendência (r = {r_raca:+.2f})")
    ax2.set_xlabel("% População Autodeclarada Preta ou Parda (Censo 2022)" if lang=="pt" else "% Black / Pardo Population (Census 2022)", fontsize=11)
    ax2.set_ylabel("% Votos Lula (1º Turno 2026)" if lang=="pt" else "% Lula Votes (1st Round 2026)", fontsize=11)
    ax2.set_title("Composição Racial x Voto em Lula" if lang=="pt" else "Racial Composition vs Lula Vote Share", fontsize=12, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.suptitle("Censo 2022: Renda e Composição Étnico-Racial vs Voto em Lula" if lang=="pt"
                 else "Census 2022: Income & Race vs Lula Vote Share", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(out_dir / "21_renda_urbanizacao_e_voto.png", dpi=180)
    plt.close()


def fig22_prefeitos(dados, pref_data, out_dir, lang="pt"):
    """Figura 22: Prefeitos eleitos em 2024 vs Votação Presidencial 2026."""
    partidos = defaultdict(lambda: {"vv": 0, "lula": 0, "flavio": 0, "mun": 0})
    for k, d in dados.items():
        if k in pref_data:
            p = pref_data[k]
            partidos[p]["vv"] += d["vv"]
            partidos[p]["lula"] += d["vv"] * (d["lula_pct"] / 100)
            partidos[p]["flavio"] += d["vv"] * (d["flavio_pct"] / 100)
            partidos[p]["mun"] += 1

    # Top 10 partidos por eleitorado
    top = sorted(partidos.items(), key=lambda x: x[1]["vv"], reverse=True)[:10]
    nomes = [p for p, _ in top]
    lula_pct = [d["lula"] / d["vv"] * 100 for _, d in top]
    flavio_pct = [d["flavio"] / d["vv"] * 100 for _, d in top]
    votos_tot = [d["vv"] / 1e6 for _, d in top]

    y_pos = np.arange(len(nomes))

    fig, ax = plt.subplots(figsize=(10, 6))
    h = 0.38
    rects1 = ax.barh(y_pos + h/2, lula_pct, h, label="Lula (1ºT 2026)", color=COR_LULA, alpha=0.9)
    rects2 = ax.barh(y_pos - h/2, flavio_pct, h, label="Flávio Bolsonaro (1ºT 2026)", color=COR_FLAVIO, alpha=0.9)

    ax.set_yticks(y_pos)
    labels_partidos = [f"{p} ({top[i][1]['mun']} cidades, {votos_tot[i]:.1f}M votos)" for i, p in enumerate(nomes)]
    ax.set_yticklabels(labels_partidos, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("% Votos Válidos no Município" if lang=="pt" else "% Valid Votes in Municipality", fontsize=11)
    ax.set_title("Votação Presidencial 2026 por Partido do Prefeito Eleito em 2024" if lang=="pt"
                 else "2026 Presidential Vote by Party of Mayor Elected in 2024", fontsize=13, fontweight="bold")
    ax.axvline(50, color="gray", linestyle="--", alpha=0.7)
    ax.grid(True, axis="x", alpha=0.3)
    ax.legend(loc="lower right")

    for i in range(len(nomes)):
        ax.text(lula_pct[i] + 0.8, y_pos[i] + h/2, f"{lula_pct[i]:.1f}%", va="center", fontsize=9, color="darkred", fontweight="bold")
        ax.text(flavio_pct[i] + 0.8, y_pos[i] - h/2, f"{flavio_pct[i]:.1f}%", va="center", fontsize=9, color="navy", fontweight="bold")

    plt.tight_layout()
    plt.savefig(out_dir / "22_prefeitos_2024_e_presidencial.png", dpi=180)
    plt.close()


def fig23_polymarket(out_dir, lang="pt"):
    """Figura 23: Trajetória das odds de probabilidade no Polymarket (Lula vs Flávio)."""
    p_lula = C.RAW / "polymarket" / "historico_clob_lula.json"
    p_flavio = C.RAW / "polymarket" / "historico_clob_flavio.json"
    if not p_lula.exists() or not p_flavio.exists():
        return

    hist_l = json.loads(p_lula.read_text(encoding="utf-8")).get("history", [])
    hist_f = json.loads(p_flavio.read_text(encoding="utf-8")).get("history", [])

    dts_l = [datetime.fromtimestamp(pt["t"], timezone.utc) for pt in hist_l]
    vals_l = [pt["p"] * 100 for pt in hist_l]

    dts_f = [datetime.fromtimestamp(pt["t"], timezone.utc) for pt in hist_f]
    vals_f = [pt["p"] * 100 for pt in hist_f]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(dts_l, vals_l, color=COR_LULA, lw=2.5, label="Lula (YES Token)")
    ax.plot(dts_f, vals_f, color=COR_FLAVIO, lw=2.5, label="Flávio Bolsonaro (YES Token)")

    ax.set_ylabel("Probabilidade Implícita de Vitória (%)" if lang=="pt" else "Implied Probability of Victory (%)", fontsize=11)
    ax.set_title("Evolução das Cotações de Vitória no Polymarket (Nov/2025 – Out/2026)" if lang=="pt"
                 else "Polymarket Presidential Odds Trajectory (Nov 2025 – Oct 2026)", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-2, 102)
    ax.axhline(50, color="gray", linestyle="--", alpha=0.6)

    # Anotações de fatos marcantes
    ax.annotate("1º Turno (04/10):\nFlávio lidera apuração",
                xy=(dts_f[-1], vals_f[-1]), xytext=(dts_f[-1] - np.timedelta64(45, 'D'), vals_f[-1] - 15),
                arrowprops=dict(facecolor='black', arrowstyle='->'),
                fontsize=9, fontweight="bold", backgroundcolor="#ffffff")

    ax.legend(loc="center left")
    plt.tight_layout()
    plt.savefig(out_dir / "23_polymarket_trajetoria.png", dpi=180)
    plt.close()


def fig24_auditoria_pesquisas(out_dir, lang="pt"):
    """Figura 24: Custo declarado e principais financiadores das pesquisas no TSE."""
    p_audit = C.PROCESSED / "auditoria_pesquisas.csv"
    if not p_audit.exists():
        return

    with open(p_audit, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Agrupa por instituto
    inst_custos = defaultdict(list)
    inst_amostras = defaultdict(list)
    for r in rows:
        try:
            c = float(r["custo_declarado_rs"])
            a = float(r["amostra_planejada_tse"])
            if c > 0 and a > 0:
                inst_custos[r["instituto"]].append(c)
                inst_amostras[r["instituto"]].append(a)
        except Exception:
            pass

    institutos = sorted(inst_custos.keys(), key=lambda k: np.median(inst_custos[k]), reverse=True)
    med_custo = [np.median(inst_custos[k])/1000 for k in institutos]
    med_amostra = [np.median(inst_amostras[k]) for k in institutos]

    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    x = np.arange(len(institutos))
    w = 0.4

    b1 = ax1.bar(x - w/2, med_custo, w, label="Custo Mediano Declarado (mil R$)", color="#27ae60", alpha=0.9)
    ax1.set_ylabel("Custo Declarado (mil R$)" if lang=="pt" else "Declared Cost (thousand BRL)", fontsize=11, color="darkgreen")
    ax1.set_xticks(x)
    ax1.set_xticklabels(institutos, rotation=35, ha="right", fontsize=10)
    ax1.grid(True, axis="y", alpha=0.3)

    ax2 = ax1.twinx()
    b2 = ax2.bar(x + w/2, med_amostra, w, label="Amostra Mediana", color="#e67e22", alpha=0.9)
    ax2.set_ylabel("Tamanho da Amostra (entrevistados)" if lang=="pt" else "Sample Size", fontsize=11, color="darkorange")

    plt.title("Auditoria TSE: Custo Declarado e Amostra por Instituto de Pesquisa" if lang=="pt"
              else "TSE Audit: Declared Cost and Sample Size by Polling Firm", fontsize=13, fontweight="bold")

    # Legenda combinada
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper right")

    plt.tight_layout()
    plt.savefig(out_dir / "24_auditoria_pesquisas_custos_financiadores.png", dpi=180)
    plt.close()


def fig25_rejeicao(out_dir, lang="pt"):
    """Figura 25: A Batalha de Rejeição em 2026 segundo o Datafolha."""
    p_rej = C.EXTERNAL / "datafolha_aprovacao_rejeicao.csv"
    if not p_rej.exists():
        return

    pontos = []
    with open(p_rej, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["serie"] == "rejeicao":
                dt = datetime.fromisoformat(r["data_divulgacao"])
                pontos.append({
                    "dt": dt,
                    "lula": float(r["valor_lula"]),
                    "flavio": float(r["valor_flavio"])
                })

    pontos.sort(key=lambda x: x["dt"])
    dts = [p["dt"] for p in pontos]
    lula_rej = [p["lula"] for p in pontos]
    flavio_rej = [p["flavio"] for p in pontos]

    fig, ax = plt.subplots(figsize=(9.5, 5))
    ax.plot(dts, lula_rej, marker="o", color=COR_LULA, lw=2.5, label="Rejeição a Lula ('não votaria de jeito nenhum')")
    ax.plot(dts, flavio_rej, marker="s", color=COR_FLAVIO, lw=2.5, label="Rejeição a Flávio Bolsonaro")

    ax.set_ylabel("Taxa de Rejeição (%)" if lang=="pt" else "Rejection Rate (%)", fontsize=11)
    ax.set_title("Evolução da Rejeição dos Candidatos Presidenciais (Datafolha 2026)" if lang=="pt"
                 else "Candidate Rejection Trajectory (Datafolha 2026)", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(35, 55)

    for i in range(len(pontos)):
        ax.text(dts[i], lula_rej[i] + 0.6, f"{lula_rej[i]:.0f}%", ha="center", fontsize=9, color="darkred", fontweight="bold")
        ax.text(dts[i], flavio_rej[i] - 1.0, f"{flavio_rej[i]:.0f}%", ha="center", fontsize=9, color="navy", fontweight="bold")

    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(out_dir / "25_rejeicao_datafolha_2026.png", dpi=180)
    plt.close()


def main():
    print("Carregando dados municipais...")
    dados, pref_data = carregar_dados_municipais()

    for lang in ("pt", "en"):
        out_dir = C.FIGURES / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Gerando gráficos em {out_dir} ({lang})...")
        fig20_religiao(dados, out_dir, lang=lang)
        fig21_renda_urb(dados, out_dir, lang=lang)
        fig22_prefeitos(dados, pref_data, out_dir, lang=lang)
        fig23_polymarket(out_dir, lang=lang)
        fig24_auditoria_pesquisas(out_dir, lang=lang)
        fig25_rejeicao(out_dir, lang=lang)

    print("Todas as 6 novas figuras geradas com sucesso!")


if __name__ == "__main__":
    main()
