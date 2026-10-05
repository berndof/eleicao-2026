with open("src/eleicao2026/viz/figuras_dados.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "f\"Cada bolinha = 1 município (tamanho = total de votos)" in l:
        lines[i] = '    b.text(0.03, 0.96, f"Cada bolinha = 1 município (tamanho = total de votos)\\nCorrelação r = {rr:.2f}\\n"\\\n'
        lines[i+1] = ""
        lines[i+2] = ""
        break

for i, l in enumerate(lines):
    if '"Linha tracejada cinza:' in l:
        lines[i] = '    b.text(78, 83, "Linha tracejada cinza:\\nse a votação de 2026\\nfosse idêntica à de 2022", color="#666666", fontsize=9, ha="right", va="bottom", bbox=cx_box)\n'
        lines[i+1] = ""
        lines[i+2] = ""
        break

with open("src/eleicao2026/viz/figuras_dados.py", "w", encoding="utf-8") as f:
    f.writelines(lines)
