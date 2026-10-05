import re

with open("src/eleicao2026/viz/figuras_dados.py", "r", encoding="utf-8") as f:
    s = f.read()

# Modify d03b to add more labels
d03b_caps = """    capitais = ["SÃO PAULO", "RIO DE JANEIRO", "SALVADOR", "FORTALEZA", "BELO HORIZONTE", "MANAUS", "CURITIBA", "PORTO ALEGRE", "FLORIANÓPOLIS", "VITÓRIA"]
    outliers = ["FARTURA DO PIAUÍ", "CARNAUBEIRA DA PENHA", "NOVA PÁDUA", "SÃO CAETANO DO SUL"]
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
        if r["nome"] in capitais or r["nome"] in outliers:
            caps_x.append(px)
            caps_y.append(py)
            caps_n.append(r["nome"].title())"""
s = re.sub(r'    capitais = \["SÃO PAULO".*?            caps_n\.append\(r\["nome"\]\.title\(\)\)', d03b_caps, s, flags=re.DOTALL)

# Modify d04 to add labels to the scatter plot
d04_scatter = """    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5.6), gridspec_kw=dict(width_ratios=[1.6, 1]))
    a.scatter(dt, F, color=COR["flavio"], alpha=0.65, s=28, label="Flávio (pesquisas)")
    a.scatter(dt, L, color=COR["lula"], alpha=0.65, s=28, label="Lula (pesquisas)")
    
    # Add institute names as tiny text labels
    for x, y_l, y_f, n in zip(dt, L, F, nomes):
        a.annotate(n, (x, y_l), xytext=(4, 0), textcoords="offset points", fontsize=6, color="#555555", va="center")
        a.annotate(n, (x, y_f), xytext=(4, 0), textcoords="offset points", fontsize=6, color="#555555", va="center")
"""
s = re.sub(r'    fig, \(a, b\) = plt\.subplots\(1, 2, figsize=\(13, 5\.6\), gridspec_kw=dict\(width_ratios=\[1\.6, 1\]\)\)\n    a\.scatter\(dt, F, color=COR\["flavio"\], alpha=0\.65, s=28, label="Flávio \(pesquisas\)"\)\n    a\.scatter\(dt, L, color=COR\["lula"\], alpha=0\.65, s=28, label="Lula \(pesquisas\)"\)\n', d04_scatter, s)


with open("src/eleicao2026/viz/figuras_dados.py", "w", encoding="utf-8") as f:
    f.write(s)
