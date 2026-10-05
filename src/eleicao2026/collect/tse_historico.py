#!/usr/bin/env python3
"""Baixa e prepara os dados históricos e de perfil do eleitorado a partir dos Dados Abertos do TSE.

Insumos (baixados para data/raw/, ~1,1 GB, não versionados):
  votacao_candidato_munzona_2022.zip   votos por candidato/município/zona (Presidente 2022, 1º e 2º turno)
  perfil_eleitorado_2022.zip / _2026.zip   perfil do eleitorado (gênero, idade, escolaridade) por município

Saídas (data/interim/, CSV por município):
  pres_2022_mun.csv, pres_2022_t2_mun.csv, perfil_2022_mun.csv, perfil_2026_mun.csv

Uso: python -m eleicao2026.collect.tse_historico download | votos2022 | perfil 2022 | perfil 2026 | all
Somente biblioteca padrão.
"""
import csv
import io
import sys
import zipfile
from collections import defaultdict
from urllib.request import Request, urlopen

from eleicao2026 import config as C

ARQUIVOS = {
    "votacao_candidato_munzona_2022.zip": f"{C.TSE_CDN}/votacao_candidato_munzona/votacao_candidato_munzona_2022.zip",
    "perfil_eleitorado_2022.zip": f"{C.TSE_CDN}/perfil_eleitorado/perfil_eleitorado_2022.zip",
    "perfil_eleitorado_2026.zip": f"{C.TSE_CDN}/perfil_eleitorado/perfil_eleitorado_2026.zip",
}


def download():
    C.RAW.mkdir(parents=True, exist_ok=True)
    for nome, url in ARQUIVOS.items():
        dst = C.RAW / nome
        if dst.exists() and dst.stat().st_size > 0:
            print(f"já existe: {dst.name}", file=sys.stderr)
            continue
        print(f"baixando {url}", file=sys.stderr)
        with urlopen(Request(url, headers=C.UA), timeout=120) as r, open(dst, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)


def rows(zf, name):
    with zf.open(name) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding="latin1"), delimiter=";")


def votos2022():
    """Votos de Presidente 2022 por município: pres_2022_mun.csv (1º turno) e pres_2022_t2_mun.csv (2º)."""
    out = {1: defaultdict(lambda: defaultdict(int)), 2: defaultdict(lambda: defaultdict(int))}
    zf = zipfile.ZipFile(C.RAW / "votacao_candidato_munzona_2022.zip")
    for n in zf.namelist():
        # Presidente (cargo 1) está somente no arquivo _BR (detalhado por UF/município)
        if not n.endswith("_2022_BR.csv"):
            continue
        for r in rows(zf, n):
            if r["CD_CARGO"] != "1":
                continue
            k = (r["SG_UF"].lower(), r["CD_MUNICIPIO"].zfill(5), r["NM_MUNICIPIO"])
            out[int(r["NR_TURNO"])][k][r["NM_URNA_CANDIDATO"]] += int(r["QT_VOTOS_NOMINAIS"])
        print(n, len(out[1]), len(out[2]), file=sys.stderr)
    C.INTERIM.mkdir(parents=True, exist_ok=True)
    for turno, fname in ((1, "pres_2022_mun.csv"), (2, "pres_2022_t2_mun.csv")):
        o = out[turno]
        cands = sorted({c for v in o.values() for c in v})
        with open(C.INTERIM / fname, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["uf", "cd", "nome"] + cands)
            for k, v in sorted(o.items()):
                w.writerow(list(k) + [v.get(c, 0) for c in cands])


def _perfil_arquivo(args):
    ano, n = args
    zf = zipfile.ZipFile(C.RAW / f"perfil_eleitorado_{ano}.zip")
    agg = defaultdict(lambda: defaultdict(int))
    for r in rows(zf, n):
        q = int(r["QT_ELEITORES"])
        k = (r["SG_UF"].lower(), r["CD_MUNICIPIO"].zfill(5))
        a = agg[k]
        a["tot"] += q
        if r["CD_GENERO"] == "4":
            a["fem"] += q
        esc = r["DS_GRAU_ESCOLARIDADE"].upper()
        if "SUPERIOR COMPLETO" in esc:
            a["sup"] += q
        elif esc in ("ANALFABETO", "LÊ E ESCREVE", "LE E ESCREVE") or "ANALFAB" in esc:
            a["analf"] += q
        elif "FUNDAMENTAL INCOMPLETO" in esc:
            a["fund_inc"] += q
        try:
            fx = int(r["CD_FAIXA_ETARIA"])
        except ValueError:
            fx = -1
        if 1600 <= fx <= 2400:
            a["jovem"] += q
        if fx >= 6000 and fx != 9999:
            a["idoso"] += q
    print(n, len(agg), file=sys.stderr)
    return {k: dict(v) for k, v in agg.items()}


def perfil(ano):
    """Processa um arquivo (UF) por núcleo."""
    from multiprocessing import Pool
    zf = zipfile.ZipFile(C.RAW / f"perfil_eleitorado_{ano}.zip")
    # _BRASIL.csv é o agregado nacional (duplica todos os arquivos por UF) -> ignorar
    names = [n for n in zf.namelist() if n.endswith(".csv") and not n.endswith("_BRASIL.csv")]
    sizes = {i.filename: i.file_size for i in zf.infolist()}
    names.sort(key=lambda n: -sizes[n])  # maiores primeiro, para balancear a carga
    agg = defaultdict(lambda: defaultdict(int))
    with Pool() as pool:
        for part in pool.imap_unordered(_perfil_arquivo, [(ano, n) for n in names]):
            for k, v in part.items():
                for c, x in v.items():
                    agg[k][c] += x
    cols = ["tot", "fem", "sup", "analf", "fund_inc", "jovem", "idoso"]
    C.INTERIM.mkdir(parents=True, exist_ok=True)
    with open(C.INTERIM / f"perfil_{ano}_mun.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uf", "cd"] + cols)
        for (uf, cd), a in sorted(agg.items()):
            w.writerow([uf, cd] + [a.get(c, 0) for c in cols])


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("download", "all"):
        download()
    if cmd in ("votos2022", "all"):
        votos2022()
    if cmd == "perfil":
        perfil(sys.argv[2])
    if cmd == "all":
        perfil("2022")
        perfil("2026")


if __name__ == "__main__":
    main()
