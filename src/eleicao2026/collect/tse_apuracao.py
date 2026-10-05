#!/usr/bin/env python3
"""Coleta a apuração (Presidente, 1º turno 2026) do TSE por município.

Gera:
  data/interim/mun_2026.csv        uma linha por município (seções, eleitorado, votos válidos e votos por candidato)
  data/processed/apuracao_meta.json  carimbo de tempo e % apurado (nacional) no momento da coleta

Uso: python -m eleicao2026.collect.tse_apuracao [--out data/interim/mun_2026.csv]
"""
import argparse
import csv
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen

from eleicao2026 import config as C


def get(url, tries=4):
    for i in range(tries):
        try:
            with urlopen(Request(url, headers=C.UA), timeout=30) as r:
                return json.loads(r.read().decode("utf-8-sig"))
        except Exception:
            time.sleep(1 + i)
    return None


def num(x):
    return int(x) if x not in (None, "") else 0


def parse(d):
    c = d["carg"][0]
    votes = {}
    for a in c.get("agr", []):
        for p in a["par"]:
            for k in p["cand"]:
                votes[k["nmu"]] = num(k["vap"])
    s, e, v = d["s"], d["e"], d["v"]
    return dict(
        ts=num(s["ts"]), st=num(s["st"]),
        te=num(e["te"]), est=num(e["est"]),
        vv=num(v["vv"]), tv=num(v["tv"]), vb=num(v["vb"]), vn=num(v["tvn"]),
        hg=d["hg"], votes=votes,
    )


def job(args):
    uf, cd, nome, ibge = args
    d = get(f"{C.TSE_BASE}/dados/{uf}/{uf}{cd}-c0001-e00{C.TSE_ELE}-u.json")
    if d is None:
        return None
    r = parse(d)
    r.update(uf=uf, cd=cd, nome=nome, ibge=ibge)
    return r


def nacional():
    """Totais nacionais (cabeçalho do arquivo br): usado só como metadado e conferência."""
    d = get(f"{C.TSE_BASE}/dados/br/br-c0001-e00{C.TSE_ELE}-u.json")
    r = parse(d)
    r.update(dg=d["dg"], tf=d["tf"], pct_secoes=d["s"]["pstn"], pct_eleitorado=d["e"]["pestn"],
             comparecimento=d["e"]["pcn"], abstencao=d["e"]["pan"])
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(C.INTERIM / "mun_2026.csv"))
    args = ap.parse_args()
    C.INTERIM.mkdir(parents=True, exist_ok=True)
    C.PROCESSED.mkdir(parents=True, exist_ok=True)

    nac = nacional()
    cfg = get(f"{C.TSE_BASE}/config/mun-e00{C.TSE_ELE}-cm.json")
    tasks = [(a["cd"], m["cd"], m["nm"], m.get("cdi", "")) for a in cfg["abr"] for m in a["mu"]]
    print(f"{len(tasks)} municípios", file=sys.stderr)
    with ThreadPoolExecutor(24) as ex:
        res = [r for r in ex.map(job, tasks) if r]
    print(f"{len(res)} coletados", file=sys.stderr)

    names = sorted({n for r in res for n in r["votes"]})
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uf", "cd", "nome", "ibge", "ts", "st", "te", "est", "vv", "tv", "vb", "vn", "hg"]
                   + ["v_" + n for n in names])
        for r in res:
            w.writerow([r["uf"], r["cd"], r["nome"], r["ibge"], r["ts"], r["st"], r["te"], r["est"],
                        r["vv"], r["tv"], r["vb"], r["vn"], r["hg"]]
                       + [r["votes"].get(n, 0) for n in names])

    meta = dict(
        coletado_em=time.strftime("%Y-%m-%dT%H:%M:%S%z"), tse_dg=nac["dg"], tse_hg=nac["hg"],
        totalizacao_final=nac["tf"] == "s", pct_secoes_apuradas=nac["pct_secoes"],
        pct_eleitorado_apurado=nac["pct_eleitorado"], comparecimento_pct=nac["comparecimento"],
        abstencao_pct=nac["abstencao"], votos_validos=nac["vv"], votos_brancos=nac["vb"],
        votos_nulos=nac["vn"], votos_candidatos=nac["votes"], municipios=len(res),
        soma_municipios_validos=sum(r["vv"] for r in res),
    )
    (C.PROCESSED / "apuracao_meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print(json.dumps({k: meta[k] for k in ("tse_hg", "pct_secoes_apuradas", "votos_validos",
                                            "soma_municipios_validos")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
