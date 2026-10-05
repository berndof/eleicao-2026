#!/usr/bin/env python3
"""Coleta a apuração (Presidente, 1º turno 2026) do TSE por município.

Gera:
  data/interim/mun_2026.csv        uma linha por município (seções, eleitorado, votos válidos e votos por candidato)
  data/processed/apuracao_meta.json  carimbo de tempo e % apurado (nacional) no momento da coleta

Uso: python -m eleicao2026.collect.tse_apuracao [--out data/interim/mun_2026.csv]
                                                [--meta data/processed/apuracao_meta.json]
                                                [--save-raw data/raw/tse_apuracao_AAAAMMDD.tar.gz]
Com --save-raw, as respostas JSON originais do TSE (uma por município + nacional) são arquivadas
tal como recebidas, para que a transformação em CSV seja auditável.
"""
import argparse
import csv
import io
import json
import sys
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

from eleicao2026 import config as C


RAW_LOG = None  # lista (nome, bytes) preenchida quando --save-raw está ativo


def get(url, tries=4):
    for i in range(tries):
        try:
            with urlopen(Request(url, headers=C.UA), timeout=30) as r:
                body = r.read()
                if RAW_LOG is not None:
                    RAW_LOG.append((url.split("/ele2026/")[-1], body))
                return json.loads(body.decode("utf-8-sig"))
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
    ap.add_argument("--meta", default=str(C.PROCESSED / "apuracao_meta.json"))
    ap.add_argument("--save-raw", help="arquiva as respostas JSON originais do TSE neste .tar.gz")
    args = ap.parse_args()
    global RAW_LOG
    if args.save_raw:
        RAW_LOG = []
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
    Path(args.meta).parent.mkdir(parents=True, exist_ok=True)
    Path(args.meta).write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    if args.save_raw:
        Path(args.save_raw).parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(args.save_raw, "w:gz") as tf:
            for nome, body in RAW_LOG:
                ti = tarfile.TarInfo(nome)
                ti.size = len(body)
                ti.mtime = time.time()
                tf.addfile(ti, io.BytesIO(body))
        print(f"{len(RAW_LOG)} respostas brutas arquivadas em {args.save_raw}", file=sys.stderr)
    print(json.dumps({k: meta[k] for k in ("tse_hg", "pct_secoes_apuradas", "votos_validos",
                                            "soma_municipios_validos")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
