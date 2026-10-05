#!/usr/bin/env python3
"""Coleta e extrai as pesquisas eleitorais (1º e 2º turno, Lula × Flávio) da Wikipédia (EN).

Fonte: "Opinion polling for the 2026 Brazilian presidential election" (wikitext bruto). Cada linha da
página cita o veículo original (g1, Folha, etc.). Saídas em data/interim/:
  pesquisas_1turno.csv, pesquisas_2turno.csv   (com `data_fim` em ISO 8601)

Uso: python -m eleicao2026.collect.pesquisas [--no-download]
Somente biblioteca padrão.
"""
import argparse
import csv
import re
import sys
from datetime import date
from urllib.request import Request, urlopen

from eleicao2026 import config as C

URL = ("https://en.wikipedia.org/w/index.php?title=Opinion_polling_for_the_2026_Brazilian_presidential_election"
       "&action=raw")
WIKITEXT = C.EXTERNAL / "wikipedia_pesquisas_2026.wikitext"
MES = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10,
       "Nov": 11, "Dec": 12}


def baixar():
    C.EXTERNAL.mkdir(parents=True, exist_ok=True)
    with urlopen(Request(URL, headers=C.UA), timeout=60) as r:
        WIKITEXT.write_bytes(r.read())
    print(f"wikitext salvo em {WIKITEXT} ({WIKITEXT.stat().st_size/1e3:.0f} kB)", file=sys.stderr)


def section(txt, start, end):
    i = txt.index(start)
    j = txt.index(end, i)
    return txt[i:j]


def clean(c):
    c = c.strip()
    c = re.sub(r"<ref.*?(</ref>|/>)", "", c, flags=re.S)
    if "|" in c and not c.startswith("{{"):
        c = c.split("|")[-1]
    c = c.replace("''", "").replace("{{n/a}}", "").replace("{{small|", "").replace("}}", "").strip()
    return c


def num(c):
    c = clean(c).replace(",", ".")
    m = re.match(r"^-?\d+(\.\d+)?", c)
    return float(m.group(0)) if m else None


def data_fim(s, ano=2026):
    """'27–29 Sep' -> 2026-09-29;  '30 Sep–3 Oct' -> 2026-10-03;  '3 Oct' -> 2026-10-03."""
    m = re.findall(r"(\d+)\s*([A-Za-z]{3})?", s.replace("–", "-").replace("—", "-"))
    if not m:
        return None
    dia = int(m[-1][0])
    mes = m[-1][1] or next((x[1] for x in reversed(m) if x[1]), "Oct")
    return date(ano, MES.get(mes, 10), dia).isoformat()


def rows_of(block):
    out = []
    for chunk in block.split("\n|-")[1:]:
        cells = []
        for line in chunk.split("\n"):
            if line.startswith("|") and not line.startswith("|}") and not line.startswith("|-"):
                cells.append(line[1:])
            elif line.startswith("!"):
                cells = []
                break
        if cells:
            out.append(cells)
    return out


def extrair():
    txt = WIKITEXT.read_text(encoding="utf-8")
    C.INTERIM.mkdir(parents=True, exist_ok=True)

    # 2º turno (campanha): [pollster, periodo, Lula, Flavio, Caiado, Zema, Santos, Cury, branco, ...]
    r2 = section(txt, "==Second round==", "==See also==")
    r2 = section(r2, "==== Aug–Oct (Campaign period) ====", "==== Apr–Aug ====")
    out2, cur_p, cur_d = [], None, None
    for cells in rows_of(r2):
        if "rowspan" in cells[0] or cells[0].startswith("''") or len(cells) >= 12:
            if len(cells) >= 12:
                cur_p, cur_d = clean(cells[0]).strip(), clean(cells[1])
                vals = cells[2:]
            else:
                vals = cells  # linha de continuação com rowspan: já começa nos números
        else:
            vals = cells
        if len(vals) < 8:
            continue
        L, Fl, Cai, Zem, San, Cur = (num(vals[i]) for i in range(6))
        blank = num(vals[6])
        # só confrontos diretos Lula x Flávio
        if L is not None and Fl is not None and not any(x is not None for x in (Cai, Zem, San, Cur)):
            out2.append(dict(pollster=cur_p, data=cur_d, data_fim=data_fim(cur_d), lula=L, flavio=Fl,
                             branco_nao_sabe=blank))
    with open(C.INTERIM / "pesquisas_2turno.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out2[0].keys()))
        w.writeheader()
        w.writerows(out2)
    print(f"2º turno (Lula x Flávio): {len(out2)} pesquisas na campanha")

    # 1º turno (campanha)
    r1 = section(txt, "==== Aug–Oct (Campaign period) ====", "==== Apr–Aug ====")
    out1, cur_p, cur_d = [], None, None
    for cells in rows_of(r1):
        if len(cells) >= 12:
            cur_p, cur_d = clean(cells[0]).strip(), clean(cells[1])
            vals = cells[2:]
        else:
            vals = cells
        if len(vals) < 8:
            continue
        v = [num(x) for x in vals[:9]]
        # A linha "Results" da Wikipédia é o RESULTADO da urna (não é pesquisa): fica de fora, senão
        # entraria como um instituto de erro ~0 e diluiria o viés das pesquisas.
        if cur_p == "Results":
            continue
        if v[0] is not None and v[1] is not None:
            out1.append(dict(pollster=cur_p, data=cur_d, data_fim=data_fim(cur_d), lula=v[0], flavio=v[1],
                             caiado=v[2], zema=v[3], santos=v[4], cury=v[5], outros=v[6],
                             branco_nao_sabe=v[7]))
    with open(C.INTERIM / "pesquisas_1turno.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out1[0].keys()))
        w.writeheader()
        w.writerows(out1)
    print(f"1º turno: {len(out1)} pesquisas na campanha")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-download", action="store_true", help="usa o wikitext já salvo em data/external/")
    a = ap.parse_args()
    if not a.no_download:
        baixar()
    extrair()


if __name__ == "__main__":
    main()
