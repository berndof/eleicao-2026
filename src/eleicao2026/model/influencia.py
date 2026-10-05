#!/usr/bin/env python3
"""Quanto cada dado de entrada (pesquisa, eleição histórica) move a previsão do 2º turno?

Método "deixa um de fora" (leave-one-out): recalcula o componente que usa aquele dado SEM ele e
mede a diferença. É determinístico (sem sorteio) e usa as mesmas funções do ensemble.

  M2  (pesquisas)   usa: pesquisas de 2º turno (última de cada instituto, peso por recência)
                    e pesquisas de 1º turno (último de cada instituto -> viés medido na urna).
                    Forma fechada (normal) validada contra as simulações do próprio M2.
  M1  (estrutural)  usa: pesquisas de transferência (Quaest, Datafolha) -> fração de cada eliminado
                    que vai a Flávio. Efeito medido no cenário determinístico do M1.
  M3  (histórico)   usa: as 6 eleições de 2002-2022 (regressão sem intercepto).

Saídas (data/processed/):
  influencia_2turno.csv   cada pesquisa de 2º turno: por que entra/não entra, peso, efeito
  influencia_1turno.csv   cada pesquisa de 1º turno: erro medido, efeito no viés e no M2
  influencia_transf.csv   cada candidato eliminado: votos, origem da fração, sensibilidade do M1
  influencia_historico.csv  cada eleição: efeito no M3
  influencia.json         resumo e cenários
Somente biblioteca padrão.

Uso: python -m eleicao2026.model.influencia
"""
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import date

from eleicao2026 import config as C
from eleicao2026.config import LULA, FLAV
from eleicao2026.model import ensemble as E
from eleicao2026.model import segundo_turno as S
from eleicao2026.model.linalg import expit, logit

W_ENS = E.W


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def t4_cdf(t):
    u = t / math.sqrt(1 + t * t / 4)
    return 0.5 + 0.375 * u * (1 - u * u / 12)


def _std(x):
    m = sum(x) / len(x)
    return math.sqrt(sum((a - m) ** 2 for a in x) / (len(x) - 1))


# ----------------------------------------------------------------------------- seleção das pesquisas
def polls_1t(L1, F1):
    """Todas as pesquisas de 1º turno do arquivo, marcadas como entra / antes do corte / substituída."""
    rows = list(csv.DictReader(open(C.INTERIM / "pesquisas_1turno.csv")))
    out = []
    for i, r in enumerate(rows):
        d = date.fromisoformat(r["data_fim"])
        tot = sum(float(r[k] or 0) for k in ("lula", "flavio", "caiado", "zema", "santos", "cury", "outros"))
        l, f = float(r["lula"]) / tot, float(r["flavio"]) / tot
        out.append(dict(i=i, pollster=r["pollster"], data=r["data"], data_fim=d, l=l, f=f,
                        err=(l - f) - (L1 - F1), status="entra"))
        if d < E.CORTE_1T:
            out[-1]["status"] = "antes_do_corte"
    last = {}
    for o in out:
        if o["status"] == "entra":
            if o["pollster"] not in last or o["data_fim"] >= out[last[o["pollster"]]]["data_fim"]:
                last[o["pollster"]] = o["i"]
    for o in out:
        if o["status"] == "entra" and last[o["pollster"]] != o["i"]:
            o["status"] = "substituida"
    return out


def polls_2t():
    rows = list(csv.DictReader(open(C.INTERIM / "pesquisas_2turno.csv")))
    out = []
    for i, r in enumerate(rows):
        d = date.fromisoformat(r["data_fim"])
        l, f = float(r["lula"]), float(r["flavio"])
        out.append(dict(i=i, pollster=r["pollster"], data=r["data"], data_fim=d, l=l, f=f, v=l / (l + f),
                        status="antes_do_corte" if d < E.CORTE_2T else "entra"))
    last = {}
    for o in out:
        if o["status"] == "entra":
            if o["pollster"] not in last or o["data_fim"] >= out[last[o["pollster"]]]["data_fim"]:
                last[o["pollster"]] = o["i"]
    for o in out:
        if o["status"] == "entra" and last[o["pollster"]] != o["i"]:
            o["status"] = "substituida"
    return out


# ----------------------------------------------------------------------------- M2 em forma fechada
def m2_dist(errs, rows2, L1, F1, carry=E.CARRY_CENTRAL):
    """Média, desvio e P(Lula > 50%) do alvo nacional do M2, a partir dos insumos selecionados."""
    b1, sd_b = sum(errs) / len(errs), _std(errs)
    ref = max(r["data_fim"] for r in rows2)
    ws = [0.5 ** ((ref - r["data_fim"]).days / E.MEIA_VIDA_DIAS) for r in rows2]
    avg = sum(w * r["v"] for w, r in zip(ws, rows2)) / sum(ws)
    sd_poll = _std([r["v"] for r in rows2])
    bias = b1 / (L1 + F1)
    mean = avg - carry * bias / 2
    sd_m2 = math.sqrt(0.018 ** 2 + 0.015 ** 2 + (sd_poll / math.sqrt(len(rows2))) ** 2)
    var = sd_m2 ** 2 + (E.CARRY_DP * bias / 2) ** 2 + (carry * (sd_b / math.sqrt(len(errs))) / (L1 + F1) / 2) ** 2
    sd = math.sqrt(var)
    return dict(avg=avg, b1=b1, mean=mean, sd=sd, p=1 - phi((0.5 - mean) / sd), ws=ws, bias=bias)


# ----------------------------------------------------------------------------- M1 determinístico
def split_from(sources, elim):
    """Fração do voto válido de cada eliminado que vai a Flávio, usando só as `sources` pedidas."""
    quaest, datafolha, agg = E.load_transfer()
    f_agg = agg[0] / (agg[0] + agg[1])
    split, src = {}, {}
    for c in elim:
        parts, notes = [], []
        if c in ("RENAN SANTOS", "RONALDO CAIADO", "ESCRITOR AUGUSTO CURY", "ZEMA"):
            if "quaest" in sources and c in quaest:
                f, l, _ = quaest[c]
                parts.append(f / (f + l))
                notes.append(f"Quaest {f:.0f}/{l:.0f}")
            if "datafolha" in sources:
                if c in datafolha:
                    f, l = datafolha[c]
                    parts.append(f / (f + l))
                    notes.append(f"Datafolha {f:.0f}/{l:.0f}")
                else:
                    parts.append(f_agg)
                    notes.append(f"Datafolha agregado {agg[0]:.0f}/{agg[1]:.0f}")
        if parts:
            split[c], src[c] = sum(parts) / len(parts), " + ".join(notes)
        else:
            split[c] = E.MINOR_LEFT if c in E.LEFT else E.MINOR_RIGHT
            src[c] = "suposição: " + ("esquerda minoritária" if c in E.LEFT else "direita/menor")
    return split, src


def run(log=print):
    cal = E.calibrate(lambda *_: None)
    alfa, rho0, delta = cal["alfa"], cal["rho0"], cal["delta"]
    cur, pm = S.load26()
    N, _ = S.first_round(cur, pm)
    V1 = sum(sum(v.values()) for v in N.values())
    L1 = sum(v.get(LULA, 0) for v in N.values()) / V1
    F1 = sum(v.get(FLAV, 0) for v in N.values()) / V1
    elim = sorted({c for u in N.values() for c in u if c not in (LULA, FLAV)})
    elim_votes = {c: sum(N[u].get(c, 0.0) for u in N) for c in elim}
    res = json.loads((C.PROCESSED / "resumo_2turno.json").read_text())

    # ------------------------------------------------ 1º turno + 2º turno -> M2
    p1, p2 = polls_1t(L1, F1), polls_2t()
    in1 = [o for o in p1 if o["status"] == "entra"]
    in2 = [o for o in p2 if o["status"] == "entra"]
    base = m2_dist([o["err"] for o in in1], in2, L1, F1)
    ps = E.poll_stats(L1, F1)
    assert abs(base["avg"] - ps["avg"]) < 1e-12 and abs(base["b1"] - ps["b1"]) < 1e-12, "seleção difere do ensemble"
    m2sim = res["componentes"]["M2"]
    log(f"M2 forma fechada: média {100*base['mean']:.2f}% P={100*base['p']:.1f}%  |  simulado: "
        f"{100*m2sim['media']:.2f}% P={100*m2sim['p_lula']:.1f}%")

    def eff(dist):
        return dict(d_m2_pp=100 * (dist["mean"] - base["mean"]), d_m2_p_pp=100 * (dist["p"] - base["p"]),
                    d_ens_mean_pp=100 * W_ENS["M2"] * (dist["mean"] - base["mean"]),
                    d_ens_p_pp=100 * W_ENS["M2"] * (dist["p"] - base["p"]))

    rows2 = []
    wsum = sum(base["ws"])
    wmap = {o["i"]: w for o, w in zip(in2, base["ws"])}
    for o in p2:
        r = dict(tipo="2T", pollster=o["pollster"], data=o["data"], data_fim=o["data_fim"].isoformat(),
                 lula=o["l"], flavio=o["f"], lula_valido=o["v"], status=o["status"])
        if o["status"] == "entra":
            w = wmap[o["i"]]
            sub = [x for x in in2 if x["i"] != o["i"]]
            r.update(peso_recencia=w, peso_normalizado=w / wsum,
                     contribuicao_media_pp=100 * w / wsum * o["v"], **eff(m2_dist([x["err"] for x in in1], sub, L1, F1)))
        rows2.append(r)
    rows1 = []
    for o in p1:
        r = dict(tipo="1T", pollster=o["pollster"], data=o["data"], data_fim=o["data_fim"].isoformat(),
                 lula=o["l"], flavio=o["f"], err_margem_pp=100 * o["err"], status=o["status"])
        if o["status"] == "entra":
            sub = [x["err"] for x in in1 if x["i"] != o["i"]]
            d = m2_dist(sub, in2, L1, F1)
            r.update(d_b1_pp=100 * (d["b1"] - base["b1"]), **eff(d))
        rows1.append(r)

    # cenários agregados do M2
    errs = [o["err"] for o in in1]
    scen = []

    def sc(label, d):
        scen.append(dict(rotulo=label, m2_media=d["mean"], m2_p=d["p"], ens_p_delta_pp=100 * W_ENS["M2"] * (d["p"] - base["p"])))
    sc("M2 base (média das pesquisas corrigida pelo viés do 1º turno × 0,4)", base)
    sc("Sem correção do 1º turno (só a média das pesquisas de 2º turno)", m2_dist(errs, in2, L1, F1, carry=0.0))
    sc("Correção total do viés do 1º turno (fator 1,0)", m2_dist(errs, in2, L1, F1, carry=1.0))
    sc("Média simples (sem peso por recência)",
       m2_dist(errs, [dict(x, data_fim=max(y["data_fim"] for y in in2)) for x in in2], L1, F1))
    sc("Sem os 3 institutos que mais erraram no 1º turno (Indexa, MDA, Nexus)",
       m2_dist([o["err"] for o in in1 if o["pollster"] not in ("Indexa", "MDA", "Nexus")],
               [x for x in in2 if x["pollster"] not in ("Indexa", "MDA", "Nexus")], L1, F1))

    # ------------------------------------------------ transferência -> M1
    full = {"quaest", "datafolha"}

    def m1_lula(split):
        l, b = S.total(S.runoff(N, alfa, split, rho0, delta))
        return l / (l + b)
    split0, src0 = split_from(full, elim)
    m1_0 = m1_lula(split0)
    det = res["m1_deterministico"]["lula_pct"]
    assert abs(m1_0 - det) < 1e-9, f"M1 determinístico difere: {m1_0} vs {det}"
    tr_scen = []
    for lab, srcs in (("Só Quaest (sem Datafolha)", {"quaest"}), ("Só Datafolha (sem Quaest)", {"datafolha"}),
                      ("Sem nenhuma pesquisa de transferência (todos por suposição)", set())):
        s_, _ = split_from(srcs, elim)
        v = m1_lula(s_)
        tr_scen.append(dict(rotulo=lab, m1_lula=v, delta_pp=100 * (v - m1_0), ens_delta_pp=100 * W_ENS["M1"] * (v - m1_0)))
    trows = []
    for c in sorted(elim, key=lambda c: -elim_votes[c]):
        s2 = dict(split0)
        s2[c] = expit(logit(split0[c]) + 0.4)   # ~ +10 pp
        up = m1_lula(s2) - m1_0
        s3 = dict(split0)
        s3[c] = split0[c] + 0.10
        s3[c] = min(s3[c], 0.999)
        up10 = m1_lula(s3) - m1_0
        trows.append(dict(candidato=c, votos_validos_1t=elim_votes[c], pct_dos_validos=100 * elim_votes[c] / V1,
                          para_flavio=split0[c], origem=src0[c], delta_m1_por_10pp=100 * up10,
                          delta_ens_por_10pp=100 * W_ENS["M1"] * up10))

    # ------------------------------------------------ histórico -> M3
    hist = E.load_hist()
    beta, sd_h, _, lead, m3f = E.hist_model(hist, F1, L1)
    m3_mean = 1 - m3f
    # P(Lula > 50%) = P(e < 0,5 - m); e ~ t com 4 g.l. e escala sd_h/sqrt(2) (como na simulação)
    m3_p = 1 - t4_cdf((0.5 - m3_mean) / (sd_h / math.sqrt(2)))
    m3sim = res["componentes"]["M3"]
    log(f"M3 forma fechada: média {100*m3_mean:.2f}% P={100*m3_p:.1f}%  |  simulado: {100*m3sim['media']:.2f}% P={100*m3sim['p_lula']:.1f}%")
    hrows = []
    for ano in sorted(hist):
        sub = {a: v for a, v in hist.items() if a != ano}
        b, sd, _, ld, f = E.hist_model(sub, F1, L1)
        m = 1 - f
        p = 1 - t4_cdf((0.5 - m) / (sd / math.sqrt(2)))
        nm, s1, s2_, r2, seg = hist[ano]
        hrows.append(dict(ano=ano, lider=nm, segundo=seg, pct_lider_1t=s1, pct_segundo_1t=s2_, pct_lider_2t=r2,
                          x=s1 / (s1 + s2_), beta_sem=b, m3_media_sem=m, d_m3_pp=100 * (m - m3_mean),
                          d_ens_p_pp=100 * W_ENS["M3"] * (p - m3_p), d_ens_mean_pp=100 * W_ENS["M3"] * (m - m3_mean)))

    # ------------------------------------------------ escrita
    def write(name, rows):
        keys = []
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(C.PROCESSED / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in rows:
                w.writerow({k: (f"{v:.5f}" if isinstance(v, float) else v) for k, v in r.items()})
    write("influencia_2turno.csv", rows2)
    write("influencia_1turno.csv", rows1)
    write("influencia_transf.csv", trows)
    write("influencia_historico.csv", hrows)
    out = dict(m2_fechada=dict(media=base["mean"], dp=base["sd"], p=base["p"], avg_pesquisas=base["avg"], vies_1t=base["b1"]),
               m2_simulado=dict(media=m2sim["media"], p=m2sim["p_lula"]),
               m3_fechada=dict(media=m3_mean, p=m3_p), m3_simulado=dict(media=m3sim["media"], p=m3sim["p_lula"]),
               m1_det=m1_0, cenarios_m2=scen, cenarios_transf=tr_scen,
               n_1t_total=len(p1), n_1t_entram=len(in1), n_2t_total=len(p2), n_2t_entram=len(in2),
               pesos=W_ENS)
    (C.PROCESSED / "influencia.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    log(f"1T: {len(in1)}/{len(p1)} entram | 2T: {len(in2)}/{len(p2)} entram")
    return out


def main():
    run(lambda s: print(s, file=sys.stderr))


if __name__ == "__main__":
    main()
