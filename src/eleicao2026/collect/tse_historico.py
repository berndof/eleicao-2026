#!/usr/bin/env python3
"""Baixa e prepara os dados históricos e de perfil do eleitorado a partir dos Dados Abertos do TSE.

Insumos (baixados para data/raw/, ~1,1 GB para 2022/2026 e ~1,4 GB para 2002-2018, não versionados):
  votacao_candidato_munzona_AAAA.zip   votos por candidato/município/zona (Presidente, 1º e 2º turno)
  perfil_eleitorado_AAAA.zip           perfil do eleitorado (gênero, idade, escolaridade) por município

Saídas (data/interim/, CSV por município):
  pres_AAAA_mun.csv, pres_AAAA_t2_mun.csv, perfil_AAAA_mun.csv
  pres_candidatos.csv   uma linha por candidato × turno × ano (total nacional, % dos válidos, partido)

Uso: python -m eleicao2026.collect.tse_historico download | votos2022 | perfil 2022 | perfil 2026 | all
     python -m eleicao2026.collect.tse_historico anteriores   (baixa e processa 2002-2018)
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
# Eleições presidenciais anteriores a 2022 (as mesmas de data/external/historico_2turnos.csv)
ANOS_ANTERIORES = (2002, 2006, 2010, 2014, 2018)


def arquivos_anos(anos):
    out = {}
    for a in anos:
        for tipo in ("votacao_candidato_munzona", "perfil_eleitorado"):
            out[f"{tipo}_{a}.zip"] = f"{C.TSE_CDN}/{tipo}/{tipo}_{a}.zip"
    return out


def download(arquivos=None):
    C.RAW.mkdir(parents=True, exist_ok=True)
    for nome, url in (arquivos or ARQUIVOS).items():
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


def _linhas_presidente(zf, name):
    """Lê só as linhas de Presidente de um CSV enorme (o do Brasil tem até 4 GB).
    Filtra por texto antes de interpretar o CSV, o que é muito mais rápido que ler tudo."""
    with zf.open(name) as f:
        txt = io.TextIOWrapper(f, encoding="latin1")
        cab = next(txt)
        yield cab
        for linha in txt:
            if "Presidente" in linha:
                yield linha


def votos(ano):
    """Votos de Presidente por município: pres_AAAA_mun.csv (1º turno) e pres_AAAA_t2_mun.csv (2º).
    Também atualiza pres_candidatos.csv (total nacional de cada candidato, % dos válidos, partido)."""
    out = {1: defaultdict(lambda: defaultdict(int)), 2: defaultdict(lambda: defaultdict(int))}
    nac = {}  # (turno, nome de urna) -> [nome completo, partido, situação, votos]
    zf = zipfile.ZipFile(C.RAW / f"votacao_candidato_munzona_{ano}.zip")
    # O arquivo agregado do Brasil traz Presidente por UF/município. Em 2022 há dois (_BR e _BRASIL, com o
    # mesmo conteúdo) e nos anos anteriores só _BRASIL: lê-se apenas UM, senão os votos sairiam em dobro.
    agregados = [n for n in zf.namelist() if n.endswith(("_BR.csv", "_BRASIL.csv"))]
    agregados = sorted(agregados, key=lambda n: not n.endswith("_BR.csv"))[:1]
    for n in agregados:
        leitor = csv.DictReader(_linhas_presidente(zf, n), delimiter=";")
        for r in leitor:
            if r["CD_CARGO"] != "1":
                continue
            turno, urna, q = int(r["NR_TURNO"]), r["NM_URNA_CANDIDATO"], int(r["QT_VOTOS_NOMINAIS"])
            k = (r["SG_UF"].lower(), r["CD_MUNICIPIO"].zfill(5), r["NM_MUNICIPIO"])
            out[turno][k][urna] += q
            c = nac.setdefault((turno, urna), [r["NM_CANDIDATO"], r["SG_PARTIDO"], r["DS_SIT_TOT_TURNO"], 0])
            c[3] += q
        print(ano, n, len(out[1]), len(out[2]), file=sys.stderr)
    C.INTERIM.mkdir(parents=True, exist_ok=True)
    for turno, fname in ((1, f"pres_{ano}_mun.csv"), (2, f"pres_{ano}_t2_mun.csv")):
        o = out[turno]
        if not o:
            continue
        cands = sorted({c for v in o.values() for c in v})
        with open(C.INTERIM / fname, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["uf", "cd", "nome"] + cands)
            for k, v in sorted(o.items()):
                w.writerow(list(k) + [v.get(c, 0) for c in cands])
    _atualiza_candidatos(ano, nac)


def _atualiza_candidatos(ano, nac):
    """Regrava as linhas de `ano` em pres_candidatos.csv, preservando os outros anos."""
    dst = C.INTERIM / "pres_candidatos.csv"
    campos = ["ano", "turno", "candidato", "nome", "partido", "situacao", "votos", "pct_validos"]
    linhas = []
    if dst.exists():
        linhas = [r for r in csv.DictReader(open(dst)) if int(r["ano"]) != ano]
    total = defaultdict(int)
    for (turno, _), c in nac.items():
        total[turno] += c[3]
    for (turno, urna), c in sorted(nac.items(), key=lambda x: (x[0][0], -x[1][3])):
        linhas.append(dict(ano=ano, turno=turno, candidato=urna, nome=c[0], partido=c[1], situacao=c[2],
                           votos=c[3], pct_validos=f"{100 * c[3] / total[turno]:.2f}"))
    linhas.sort(key=lambda r: (int(r["ano"]), int(r["turno"]), -int(r["votos"])))
    with open(dst, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)


def votos2022():
    """Votos de Presidente 2022 por município (atalho para votos(2022))."""
    votos(2022)


def _perfil_arquivo(args):
    ano, n = args
    zf = zipfile.ZipFile(C.RAW / f"perfil_eleitorado_{ano}.zip")
    agg = defaultdict(lambda: defaultdict(int))
    for r in rows(zf, n):
        # nos arquivos anteriores a 2022 a coluna se chama QT_ELEITORES_PERFIL
        q = int(r["QT_ELEITORES"] if "QT_ELEITORES" in r else r["QT_ELEITORES_PERFIL"])
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
    if cmd == "votos":
        votos(int(sys.argv[2]))
    if cmd == "perfil":
        perfil(sys.argv[2])
    if cmd == "all":
        perfil("2022")
        perfil("2026")
    if cmd == "anteriores":
        download(arquivos_anos(ANOS_ANTERIORES))
        for ano in ANOS_ANTERIORES:
            votos(ano)
            perfil(str(ano))


if __name__ == "__main__":
    main()
