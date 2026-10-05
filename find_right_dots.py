import csv

def load_csv(f):
    with open(f, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file))

mun = load_csv("data/interim/mun_2026.csv")
perf = {r["cd"]: r for r in load_csv("data/interim/perfil_2026_mun.csv")}

dados = []
for r in mun:
    p = perf.get(r["cd"])
    vv = int(r["vv"])
    if not p or vv < 200 or int(p["tot"]) == 0 or r["uf"] == "zz":
        continue
    px = 100 * int(p["sup"]) / int(p["tot"])
    py = 100 * int(r["v_LULA"]) / vv
    dados.append((px, py, r["nome"].title(), r["uf"]))

dados.sort(key=lambda x: x[0], reverse=True)
print("Highest education (x-axis):")
for d in dados[:10]:
    print(d)

print("\nHighest Lula (y-axis):")
dados.sort(key=lambda x: x[1], reverse=True)
for d in dados[:10]:
    print(d)
