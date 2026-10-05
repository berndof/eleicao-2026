#!/usr/bin/env python3
"""Gera a página "Quais pesquisas entram, onde e com que peso" (PT e EN) a partir de data/processed/influencia*.

Saída: docs/pesquisas.pt.md e docs/polls.en.md  (arquivos gerados — não editar à mão)
Uso: python -m eleicao2026.report_influencia   (rodar depois de eleicao2026.model.influencia)
"""
import csv
import json

from eleicao2026 import config as C

CAND = {"RONALDO CAIADO": "Ronaldo Caiado", "ESCRITOR AUGUSTO CURY": "Augusto Cury", "RENAN SANTOS": "Renan Santos",
        "ZEMA": "Romeu Zema", "SAMARA": "Samara", "CLARIANA BARAO": "Clariana Barão", "HERTZ DIAS": "Hertz Dias",
        "EDMILSON COSTA": "Edmilson Costa", "VETERINÁRIO WILSON GRASSI": "Wilson Grassi",
        "RUI COSTA PIMENTA": "Rui Costa Pimenta"}
SCEN_EN = {
    "M2 base (média das pesquisas corrigida pelo viés do 1º turno × 0,4)": "M2 base (poll average corrected by 0.4 × first-round bias)",
    "Sem correção do 1º turno (só a média das pesquisas de 2º turno)": "No first-round correction (runoff polls only)",
    "Correção total do viés do 1º turno (fator 1,0)": "Full first-round bias correction (factor 1.0)",
    "Média simples (sem peso por recência)": "Plain average (no recency weighting)",
    "Sem os 3 institutos que mais erraram no 1º turno (Indexa, MDA, Nexus)": "Without the 3 worst first-round pollsters (Indexa, MDA, Nexus)",
    "Só Quaest (sem Datafolha)": "Quaest only (no Datafolha)", "Só Datafolha (sem Quaest)": "Datafolha only (no Quaest)",
    "Sem nenhuma pesquisa de transferência (todos por suposição)": "No transfer poll at all (all assumed)",
}


def csvr(name):
    return list(csv.DictReader(open(C.PROCESSED / name)))


def mk(lang):
    pt = lang == "pt"

    def n(x, d=1, sign=False):
        s = f"{float(x):{'+' if sign else ''}.{d}f}"
        return s.replace(".", ",") if pt else s

    def tab(head, rows, align=None):
        al = align or ["---"] * len(head)
        return "\n".join(["| " + " | ".join(head) + " |", "|" + "|".join(al) + "|"] + ["| " + " | ".join(r) + " |" for r in rows])

    inf = json.loads((C.PROCESSED / "influencia.json").read_text())
    p2, p1 = csvr("influencia_2turno.csv"), csvr("influencia_1turno.csv")
    tr, hist = csvr("influencia_transf.csv"), csvr("influencia_historico.csv")
    transf_raw = list(csv.DictReader(open(C.EXTERNAL / "transferencia_pesquisas.csv")))
    res = json.loads((C.PROCESSED / "resumo_2turno.json").read_text())
    R = {"entra": "entra" if pt else "enters", "antes_do_corte": "anterior ao corte" if pt else "before cutoff",
         "substituida": "substituída por mais recente" if pt else "superseded by a newer poll"}
    out = []
    w = out.append
    L = lambda a, b: a if pt else b  # noqa: E731

    w(L("# Quais pesquisas entram, onde entram e quanto pesam", "# Which polls enter, where, and how much they weigh"))
    w("")
    w(L("> Arquivo **gerado** por `python -m eleicao2026.report_influencia` a partir de `data/processed/influencia*.csv`. "
        "A explicação conceitual de cada camada está em [camadas.pt.md](camadas.pt.md).",
        "> **Generated** file (`python -m eleicao2026.report_influencia`, from `data/processed/influencia*.csv`). "
        "The conceptual explanation of each layer is in [layers.en.md](layers.en.md)."))
    w("")
    w(L("## 1. Mapa: cada tipo de dado alimenta exatamente um componente", "## 1. Map: each type of data feeds exactly one component"))
    w("")
    w(tab([L("Dado", "Data"), L("Alimenta", "Feeds"), L("Como entra", "How it enters"), L("Onde está", "Where")],
          [[L("Pesquisas de 2º turno (Lula × Flávio)", "Runoff polls (Lula vs. Flávio)"), "M2",
            L("última de cada instituto desde 20/09; peso `0,5^(dias/7)`", "latest per pollster since 20 Sep; weight `0.5^(days/7)`"),
            "`data/interim/pesquisas_2turno.csv`"],
           [L("Pesquisas de 1º turno", "First-round polls"), "M2",
            L("erro contra a urna (último de cada instituto desde 26/09) → viés médio → correção × 0,4",
              "error vs. the ballot box (latest per pollster since 26 Sep) → mean bias → correction × 0.4"),
            "`data/interim/pesquisas_1turno.csv`"],
           [L("Pesquisas de transferência (Quaest, Datafolha)", "Transfer polls (Quaest, Datafolha)"), "M1",
            L("fração do voto de cada eliminado que vai a Flávio; % que declara voto", "share of each eliminated candidate's vote that goes to Flávio; % who state a vote"),
            "`data/external/transferencia_pesquisas.csv`"],
           [L("Resultado do 2º turno de 2022 por município", "2022 runoff result by municipality"), "M1",
            L("calibra retenção, mobilização, comparecimento e inclinação regional", "calibrates retention, mobilization, turnout and regional tilt"),
            "`data/interim/pres_2022*_mun.csv`"],
           [L("2º turno de 2002–2022", "2002–2022 runoffs"), "M3",
            L("regressão `2T = 50 + β·(1T − 50)`", "regression `R2 = 50 + β·(R1 − 50)`"), "`data/external/historico_2turnos.csv`"],
           [L("Pesquisas anteriores ao corte ou superadas", "Polls before the cutoff or superseded"), L("nenhum", "none"),
            L("só aparecem no gráfico 06", "only shown in figure 06"), L("(mesmos arquivos)", "(same files)")]]))
    w("")
    w(L("Nenhuma pesquisa de 2º turno toca o M1, e nenhuma pesquisa de transferência toca o M2: os três métodos usam **dados disjuntos**. "
        "É por isso que concordam ou discordam de forma informativa.",
        "No runoff poll touches M1, and no transfer poll touches M2: the three methods use **disjoint data**. "
        "That is why their agreement or disagreement is informative."))
    w("")
    w(L("## 2. Pesquisas de 2º turno → M2", "## 2. Runoff polls → M2"))
    w("")
    ent2 = [r for r in p2 if r["status"] == "entra"]
    w(L(f"Das {inf['n_2t_total']} pesquisas do arquivo, **{inf['n_2t_entram']} entram**. "
        f"Média ponderada: **Lula {n(100*inf['m2_fechada']['avg_pesquisas'])}%** dos válidos entre os dois. "
        "Os efeitos abaixo são de **tirar aquela pesquisa** e refazer o M2 (forma fechada, validada contra as simulações: "
        f"{n(100*inf['m2_fechada']['media'],2)}% × {n(100*inf['m2_simulado']['media'],2)}% de média; "
        f"P = {n(100*inf['m2_fechada']['p'])}% × {n(100*inf['m2_simulado']['p'])}%).",
        f"Of the {inf['n_2t_total']} polls in the file, **{inf['n_2t_entram']} enter**. "
        f"Weighted average: **Lula {n(100*inf['m2_fechada']['avg_pesquisas'])}%** of the two-candidate vote. "
        "The effects below are from **dropping that poll** and recomputing M2 (closed form, validated against the simulations: "
        f"mean {n(100*inf['m2_fechada']['media'],2)}% vs. {n(100*inf['m2_simulado']['media'],2)}%; "
        f"P = {n(100*inf['m2_fechada']['p'])}% vs. {n(100*inf['m2_simulado']['p'])}%)."))
    w("")
    w(tab([L("Instituto", "Pollster"), L("Período", "Period"), "Lula", L("Flávio", "Flávio"), L("Lula/(L+F)", "Lula/(L+F)"),
           L("Peso na média (%)", "Weight (%)"), L("Δ M2 se removida (pp)", "Δ M2 if dropped (pp)"),
           L("Δ P(Lula) ensemble (pp)", "Δ ensemble P(Lula) (pp)")],
          [[r["pollster"], r["data"].replace("–", "–"), n(r["lula"]), n(r["flavio"]), n(100 * float(r["lula_valido"])),
            n(100 * float(r["peso_normalizado"])), n(r["d_m2_pp"], 2, True), n(r["d_ens_p_pp"], 2, True)] for r in ent2],
          ["---", "---", "--:", "--:", "--:", "--:", "--:", "--:"]))
    w("")
    w(f"![{L('Peso das pesquisas', 'Poll weights')}](../figures/{lang}/16_peso_pesquisas_2turno.png)")
    w("")
    w(L("Cor das barras: vermelho = Lula acima de 50% dos válidos naquela pesquisa; azul = abaixo.",
        "Bar colors: red = Lula above 50% of valid votes in that poll; blue = below."))
    w("")
    exc = [r for r in p2 if r["status"] != "entra"]
    w(f"<details><summary>{L('Pesquisas de 2º turno que não entram', 'Runoff polls that do not enter')} ({len(exc)})</summary>")
    w("")
    w(tab([L("Instituto", "Pollster"), L("Período", "Period"), "Lula", L("Flávio", "Flávio"), L("Motivo", "Reason")],
          [[r["pollster"], r["data"], n(r["lula"]), n(r["flavio"]), R[r["status"]]] for r in exc], ["---", "---", "--:", "--:", "---"]))
    w("")
    w("</details>")
    w("")
    w(L("## 3. Pesquisas de 1º turno → viés → M2", "## 3. First-round polls → bias → M2"))
    w("")
    ent1 = [r for r in p1 if r["status"] == "entra"]
    w(L(f"Das {inf['n_1t_total']} pesquisas do arquivo (a linha \"Results\" da Wikipédia, que é a **urna**, não é pesquisa e foi excluída), "
        f"**{inf['n_1t_entram']} entram**: a última de cada instituto desde 26/09. Cada uma vira um número, o **erro na margem Lula − Flávio** "
        f"(pesquisa − urna, usando só os candidatos, sem brancos). Média: **{n(100*inf['m2_fechada']['vies_1t'],2,True)} pp**.",
        f"Of the {inf['n_1t_total']} polls in the file (the Wikipedia \"Results\" row is the **ballot box**, not a poll, and is excluded), "
        f"**{inf['n_1t_entram']} enter**: each pollster's latest since 26 Sep. Each becomes one number, the **error in the Lula − Flávio margin** "
        f"(poll − ballot box, candidates only, no blanks). Mean: **{n(100*inf['m2_fechada']['vies_1t'],2,True)} pp**."))
    w("")
    w(tab([L("Instituto", "Pollster"), L("Período", "Period"), L("Lula (norm.)", "Lula (norm.)"), L("Flávio (norm.)", "Flávio (norm.)"),
           L("Erro na margem (pp)", "Margin error (pp)"), L("Δ viés médio se removida (pp)", "Δ mean bias if dropped (pp)"),
           L("Δ P(Lula) ensemble (pp)", "Δ ensemble P(Lula) (pp)")],
          [[r["pollster"], r["data"], n(100 * float(r["lula"])), n(100 * float(r["flavio"])), n(r["err_margem_pp"], 1, True),
            n(r["d_b1_pp"], 2, True), n(r["d_ens_p_pp"], 2, True)] for r in ent1], ["---", "---", "--:", "--:", "--:", "--:", "--:"]))
    w("")
    w(f"![{L('Efeito de remover cada pesquisa', 'Effect of dropping each poll')}](../figures/{lang}/17_efeito_remover_pesquisa.png)")
    w("")
    exc1 = [r for r in p1 if r["status"] != "entra"]
    w(f"<details><summary>{L('Pesquisas de 1º turno que não entram', 'First-round polls that do not enter')} ({len(exc1)})</summary>")
    w("")
    w(tab([L("Instituto", "Pollster"), L("Período", "Period"), "Lula", "Flávio", L("Motivo", "Reason")],
          [[r["pollster"], r["data"], n(100 * float(r["lula"])), n(100 * float(r["flavio"])), R[r["status"]]] for r in exc1],
          ["---", "---", "--:", "--:", "---"]))
    w("")
    w("</details>")
    w("")
    w(L("## 4. O que mais pesa: as hipóteses, não uma pesquisa", "## 4. What weighs most: the assumptions, not any one poll"))
    w("")
    w(tab([L("Cenário do M2", "M2 scenario"), L("Lula no M2 (%)", "Lula in M2 (%)"), "P(Lula) M2 (%)",
           L("Δ P(Lula) ensemble (pp)", "Δ ensemble P(Lula) (pp)")],
          [[(SCEN_EN.get(s["rotulo"], s["rotulo"]) if not pt else s["rotulo"]), n(100 * s["m2_media"], 2), n(100 * s["m2_p"]),
            n(s["ens_p_delta_pp"], 1, True)] for s in inf["cenarios_m2"]], ["---", "--:", "--:", "--:"]))
    w("")
    w(f"![{L('Cenários de insumo', 'Input scenarios')}](../figures/{lang}/18_cenarios_de_insumo.png)")
    w("")
    w(L("O fator 0,4 (quanto do viés do 1º turno persiste no 2º) é uma **suposição**, e é a maior alavanca entre os dados de pesquisa: "
        "de 0 a 1, a probabilidade de Lula no ensemble vai de ~22% a ~13%.",
        "The 0.4 factor (how much first-round bias persists into the runoff) is an **assumption**, and it is the largest lever among poll data: "
        "from 0 to 1, Lula's ensemble probability goes from ~22% to ~13%."))
    w("")
    w(L("## 5. Pesquisas de transferência → M1", "## 5. Transfer polls → M1"))
    w("")
    w(L("Cada pesquisa pergunta aos eleitores de um candidato eliminado em quem votariam no 2º turno. Dois institutos, poucos números "
        "(todos de resumos de busca; confiança média-baixa):",
        "Each poll asks the voters of an eliminated candidate whom they would pick in the runoff. Two pollsters, few numbers "
        "(all from search summaries; medium-low confidence):"))
    w("")
    w(tab([L("Instituto", "Pollster"), L("Eleitores de", "Voters of"), L("→ Flávio", "→ Flávio"), L("→ Lula", "→ Lula"),
           L("Branco/nulo/NS", "Blank/null/DK"), L("Obs.", "Notes")],
          [[r["instituto"], CAND.get(r["eleitor_de"], r["eleitor_de"].title()), r["flavio"], r["lula"], r["branco_nulo_indeciso"] or "—",
            r["observacao"]] for r in transf_raw], ["---", "---", "--:", "--:", "--:", "---"]))
    w("")
    w(L("Como viram um número do modelo: para cada candidato, média simples de `Flávio/(Flávio+Lula)` do Quaest e do Datafolha "
        "(se o Datafolha não tem número individual, usa-se o agregado 43/30); candidatos sem pesquisa recebem uma **suposição** (direita menor 65%, esquerda minoritária 30%).",
        "How they become a model input: for each candidate, the simple mean of `Flávio/(Flávio+Lula)` from Quaest and Datafolha "
        "(if Datafolha has no individual number, the 43/30 aggregate is used); candidates without a poll get an **assumption** (minor right 65%, minor left 30%)."))
    w("")
    w(tab([L("Eleitores de", "Voters of"), L("Votos válidos 1T (mi)", "Valid R1 votes (M)"), L("% do total", "% of total"),
           L("→ Flávio (usado)", "→ Flávio (used)"), L("Origem", "Source"), L("Δ Lula no M1 se +10 pp p/ Flávio (pp)", "Δ Lula in M1 if +10 pp to Flávio (pp)")],
          [[CAND.get(r["candidato"], r["candidato"]), n(float(r["votos_validos_1t"]) / 1e6, 2), n(r["pct_dos_validos"], 2),
            n(100 * float(r["para_flavio"]), 1) + "%", r["origem"].replace("suposição: direita/menor", L("suposição: direita menor", "assumption: minor right"))
            .replace("suposição: esquerda minoritária", L("suposição: esquerda minoritária", "assumption: minor left")),
            n(r["delta_m1_por_10pp"], 2, True)] for r in tr], ["---", "--:", "--:", "--:", "---", "--:"]))
    w("")
    w(L("Três candidatos (Cury, Renan, Caiado) concentram quase todo o efeito. Efeito de usar só um instituto, ou nenhum:",
        "Three candidates (Cury, Renan, Caiado) concentrate almost all of the effect. Effect of using only one pollster, or none:"))
    w("")
    w(tab([L("Cenário", "Scenario"), L("Lula no M1 (%)", "Lula in M1 (%)"), L("Δ no M1 (pp)", "Δ in M1 (pp)"), L("Δ no ensemble, média (pp)", "Δ in ensemble mean (pp)")],
          [[(SCEN_EN.get(s["rotulo"], s["rotulo"]) if not pt else s["rotulo"]), n(100 * s["m1_lula"], 2), n(s["delta_pp"], 2, True), n(s["ens_delta_pp"], 2, True)]
           for s in inf["cenarios_transf"]], ["---", "--:", "--:", "--:"]))
    w("")
    w(L("Repare que **sem nenhuma** pesquisa de transferência o M1 mal muda (Quaest e Datafolha, em média, caem perto das suposições); "
        "a incerteza relevante é o que cada instituto diz **individualmente** (Quaest sozinho: Lula −0,3 pp; Datafolha sozinho: +0,3 pp).",
        "Note that **with no** transfer poll at all M1 barely changes (Quaest and Datafolha, on average, land close to the assumptions); "
        "the relevant uncertainty is what each pollster says **individually** (Quaest alone: Lula −0.3 pp; Datafolha alone: +0.3 pp)."))
    w("")
    w(L("## 6. Eleições históricas → M3", "## 6. Historical elections → M3"))
    w("")
    w(tab([L("Ano", "Year"), L("Líder 1T", "R1 leader"), L("% líder 1T", "Leader % R1"), L("% 2º 1T", "Runner-up % R1"),
           L("% líder 2T", "Leader % R2"), L("β sem essa eleição", "β without it"), L("Δ Lula no M3 (pp)", "Δ Lula in M3 (pp)"),
           L("Δ P(Lula) ensemble (pp)", "Δ ensemble P(Lula) (pp)")],
          [[r["ano"], f"{r['lider']} × {r['segundo']}", n(r["pct_lider_1t"], 2), n(r["pct_segundo_1t"], 2), n(r["pct_lider_2t"], 2),
            n(r["beta_sem"], 2), n(r["d_m3_pp"], 2, True), n(r["d_ens_p_pp"], 2, True)] for r in hist],
          ["---", "---", "--:", "--:", "--:", "--:", "--:", "--:"]))
    w("")
    w(L("O centro do M3 quase não depende de nenhum ano; o que muda é a **dispersão** (2006 infla o erro-padrão: sem ele, a probabilidade do ensemble cai ~2,6 pp).",
        "M3's center barely depends on any single year; what changes is the **spread** (2006 inflates the standard error: without it, the ensemble probability drops ~2.6 pp)."))
    w("")
    w(L("## 7. Como ler (e como não ler) estes números", "## 7. How to read (and not read) these numbers"))
    w("")
    w(L("* **Remover uma pesquisa não é medir causalidade.** É uma análise de sensibilidade: quanto o resultado depende daquele dado, dado o resto.\n"
        "* **As pesquisas não são independentes** (mesmo período, metodologias parecidas, erros correlacionados, como mostrou o 1º turno). Por isso o erro-padrão da média é otimista.\n"
        "* **Δ do ensemble** = peso do componente × Δ do componente (o ensemble é uma mistura linear de probabilidades).\n"
        "* Os efeitos em P(Lula) usam a forma fechada normal do M2 (e t-4 do M3); a conferência contra as simulações está no topo da seção 2.",
        "* **Dropping a poll is not causal measurement.** It is a sensitivity analysis: how much the result depends on that datum, given the rest.\n"
        "* **Polls are not independent** (same period, similar methodologies, correlated errors, as the first round showed). The standard error of the mean is therefore optimistic.\n"
        "* **Ensemble Δ** = component weight × component Δ (the ensemble is a linear mixture of probabilities).\n"
        "* P(Lula) effects use the closed-form normal M2 (and t-4 M3); the check against the simulations is at the top of section 2."))
    w("")
    return "\n".join(out) + "\n"


def main():
    (C.DOCS / "pesquisas.pt.md").write_text(mk("pt"))
    (C.DOCS / "polls.en.md").write_text(mk("en"))
    print("docs/pesquisas.pt.md, docs/polls.en.md")


if __name__ == "__main__":
    main()
