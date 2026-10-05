"""Núcleo do modelo estrutural de 2º turno (M1): calibração em 2022 + transferência de votos.

Estrutura:
 1. CALIBRAÇÃO (2022, regressão por município e macrorregião, grupos L / B / Outros):
    votos de Lula e Bolsonaro no 2º turno (fração dos válidos do 1º turno) contra a composição do
    1º turno. Mede: retenção de Lula e Bolsonaro, quanto dos eleitores dos eliminados chega a votar
    no 2º turno (rho) e a inclinação regional deles (logit Lula/Bolsonaro).
    Grupos pequenos (Tebet × D'Ávila × Soraya...) NÃO são separáveis por regressão agregada
    (estimativas absurdas, ex.: -160%), por isso os eliminados entram em bloco.
 2. TRANSFERÊNCIA 2026: fração dos votos válidos de cada eliminado que iria a Flávio × Lula.
 3. runoff(): converte votos do 1º turno projetado (por UF) em votos de 2º turno.
Somente biblioteca padrão.
"""
import csv
import math
from collections import defaultdict
from pathlib import Path

from eleicao2026 import config as C
from eleicao2026.config import LULA, FLAV, REG, UF2REG
from eleicao2026.model.linalg import expit, logit, wls

TAU_NAT = 0.015  # SUPOSIÇÃO: choque nacional na margem do 2º turno (1,5 pp)
ASYM_BASE = 0.5  # peso da assimetria de mobilização de 2022 (0 = bases mantêm 100%; 1 = como em 2022)
GROUPS = ["L", "B", "O"]


# ------------------------------------------------------------ calibração 2022
def load22():
    t1, t2 = {}, {}
    for fn, dst in (("pres_2022_mun.csv", t1), ("pres_2022_t2_mun.csv", t2)):
        for r in csv.DictReader(open(C.INTERIM / fn)):
            dst[(r["uf"], r["cd"])] = {c: int(v) for c, v in r.items() if c not in ("uf", "cd", "nome")}
    rows = []
    for k, v1 in t1.items():
        v2 = t2.get(k)
        V1 = sum(v1.values())
        if not v2 or V1 <= 0:
            continue
        x = [v1.get("LULA", 0) / V1, v1.get(C.BOLSONARO_2022, 0) / V1, 0.0]
        x[2] = 1 - x[0] - x[1]
        L2, B2 = v2.get("LULA", 0), v2.get(C.BOLSONARO_2022, 0)
        rows.append(dict(k=k, reg=UF2REG[k[0]], V1=V1, x=x, yl=L2 / V1, yb=B2 / V1, L2=L2, B2=B2))
    return rows


def fit(rows, regional, min_reg=40):
    def _fit(sub):
        X = [r["x"] for r in sub]
        w = [r["V1"] for r in sub]
        return (wls(X, [r["yl"] for r in sub], w), wls(X, [r["yb"] for r in sub], w))
    out = {None: _fit(rows)}
    if regional:
        by = defaultdict(list)
        for r in rows:
            by[r["reg"]].append(r)
        for reg, sub in by.items():
            if len(sub) >= min_reg:
                out[reg] = _fit(sub)
    return out


def coef(alfa, reg):
    return alfa.get(reg) or alfa[None]


def cv_eval(rows, regional, rnd):
    folds = [rnd.randrange(5) for _ in rows]
    res = []
    for fo in range(5):
        tr = [r for r, f in zip(rows, folds) if f != fo]
        al = fit(tr, regional)
        for r, f in zip(rows, folds):
            if f != fo:
                continue
            a = coef(al, r["reg"])
            l = sum(xi * ai for xi, ai in zip(r["x"], a[0]))
            b = sum(xi * ai for xi, ai in zip(r["x"], a[1]))
            pred = l / (l + b) if l + b > 0 else 0.5
            act = r["L2"] / (r["L2"] + r["B2"])
            res.append((r, pred - act))
    sw = sum(r["V1"] for r, _ in res)
    return math.sqrt(sum(r["V1"] * e * e for r, e in res) / sw), res


# --------------------------------------------------------------- 2026
def load26(cur_csv=None, proj_mun_csv=None):
    cur = {}
    for r in csv.DictReader(open(Path(cur_csv or C.INTERIM / "mun_2026.csv"))):
        cur[(r["uf"], r["cd"])] = {c[2:]: int(v) for c, v in r.items() if c.startswith("v_")}
    pm = {}
    for r in csv.DictReader(open(Path(proj_mun_csv or C.INTERIM / "projecao_mun.csv"))):
        pm[(r["uf"], r["cd"])] = dict(vv=int(r["vv_apurado"]), M=float(r["faltantes"]),
                                      ml=float(r["share_lula_falt"]), mf=float(r["share_flavio_falt"]))
    return cur, pm


def first_round(cur, pm):
    """Votos projetados do 1º turno por UF: Lula, Flávio e cada eliminado."""
    tot_oth = defaultdict(int)
    for v in cur.values():
        for c, n in v.items():
            if c not in (LULA, FLAV):
                tot_oth[c] += n
    sum_oth = sum(tot_oth.values())
    N = defaultdict(lambda: defaultdict(float))
    muni = []
    for k, p in pm.items():
        v = cur[k]
        V = p["vv"] + p["M"]
        Lp = v.get(LULA, 0) + p["M"] * p["ml"]
        Fp = v.get(FLAV, 0) + p["M"] * p["mf"]
        orest = max(V - Lp - Fp, 0.0)
        o_cur = sum(n for c, n in v.items() if c not in (LULA, FLAV))
        N[k[0]][LULA] += Lp
        N[k[0]][FLAV] += Fp
        for c in tot_oth:
            sh = v.get(c, 0) / o_cur if o_cur > 0 else tot_oth[c] / sum_oth
            N[k[0]][c] += orest * sh
        muni.append((k[0], V))
    return N, muni


def runoff(N, alfa, split, rho, delta, vote_rate=None, asym=None):
    """Votos de 2º turno por UF.
    split[c]: fração do voto válido do eliminado c que vai a Flávio (nacional);
    rho: fração dos eliminados que vota no 2º turno; delta[reg]: inclinação regional (logit);
    asym: peso da assimetria de mobilização de 2022 nas bases de Lula/Flávio;
    vote_rate[c]: se dado, substitui rho para o candidato c."""
    out = {}
    for uf, Nuf in N.items():
        reg = UF2REG[uf]
        a = coef(alfa, reg)
        L1, F1 = Nuf.get(LULA, 0.0), Nuf.get(FLAV, 0.0)
        w = ASYM_BASE if asym is None else asym
        # bases de Lula/Flávio: mistura entre "mantêm 100%" e a retenção/mobilização observada em 2022
        l = L1 * (w * a[0][0] + (1 - w)) + F1 * (w * a[0][1])
        b = L1 * (w * a[1][0]) + F1 * (w * a[1][1] + (1 - w))
        for c, n in Nuf.items():
            if c in (LULA, FLAV):
                continue
            s = expit(logit(split[c]) + delta.get(reg, 0.0))
            r = (vote_rate or {}).get(c, rho)
            b += n * r * s
            l += n * r * (1 - s)
        out[uf] = (l, b)
    return out


def total(res):
    return sum(v[0] for v in res.values()), sum(v[1] for v in res.values())
