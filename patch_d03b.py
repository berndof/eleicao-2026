import re

with open("src/eleicao2026/viz/figuras_dados.py", "r", encoding="utf-8") as f:
    s = f.read()

# Replace the capitais/outliers list in d03b
d03b_new_labels = """    capitais = ["SÃO PAULO", "RIO DE JANEIRO", "SALVADOR", "FORTALEZA", "BELO HORIZONTE", "MANAUS", "CURITIBA", "PORTO ALEGRE", "FLORIANÓPOLIS", "VITÓRIA"]
    outliers = ["FARTURA DO PIAUÍ", "NOVA PÁDUA", "SÃO CAETANO DO SUL", "ÁGUAS DE SÃO PEDRO", "BALNEÁRIO CAMBORIÚ", "NITERÓI", "SINGAPURA", "MONTREAL", "VANCOUVER"]
    caps_x, caps_y, caps_n = [], [], []
    xs, ys, ws, cs = [], [], [], []
    for r in rows(C.INTERIM / "mun_2026.csv"):
        p = perf.get((r["uf"], r["cd"]))
        vv = int(r["vv"])
        if not p or vv < 200 or int(p["tot"]) == 0:
            continue
        px = 100 * int(p["sup"]) / int(p["tot"])
        py = 100 * int(r["v_LULA"]) / vv
        xs.append(px)
        ys.append(py)
        ws.append(vv)
        cs.append(COR_REG.get(UF2REG.get(r["uf"].lower()), "#444444"))
        
        nm = r["nome"]
        if nm in capitais or nm in outliers:
            caps_x.append(px)
            caps_y.append(py)
            label = nm.title()
            if r["uf"] == "zz":
                label = f"{label} (Ext.)"
            caps_n.append(label)"""

s = re.sub(r'    capitais = \["SÃO PAULO".*?            caps_n\.append\(r\["nome"\]\.title\(\)\)', d03b_new_labels, s, flags=re.DOTALL)

with open("src/eleicao2026/viz/figuras_dados.py", "w", encoding="utf-8") as f:
    f.write(s)
