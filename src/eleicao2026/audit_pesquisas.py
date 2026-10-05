#!/usr/bin/env python3
"""Auditoria das pesquisas da Wikipédia contra o registro oficial do TSE (PesqEle).

Cruza cada uma das 112 pesquisas eleitorais (56 de 1º turno e 56 de 2º turno) usadas pelo projeto
com a base oficial do TSE de pesquisas registradas (`registro_pesquisas_presidente_2026.csv`).

Identifica:
  * Protocolo TSE oficial (ex.: BR017082026);
  * Quem contratou (empresas de mídia, partidos) e quem pagou;
  * Custo declarado da pesquisa;
  * Comparação entre amostra planejada (TSE) e amostra realizada (relatório/Wikipédia);
  * Margem de erro oficial x declarada;
  * Status da auditoria: casado_exato, casado_amostra_realizada, casado_data, sem_registro.

Gera:
  data/processed/auditoria_pesquisas.csv

Uso: python -m eleicao2026.audit_pesquisas
"""
import csv
import re
from datetime import datetime
from pathlib import Path

from eleicao2026 import config as C
from eleicao2026.collect.pesquisas import WIKITEXT, clean, data_fim, rows_of, section

ALIASES = {
    "AtlasIntel": "ATLASINTEL TECNOLOGIA DE DADOS LTDA",
    "Datafolha": "DATAFOLHA INSTITUTO DE PESQUISAS LTDA.",
    "Futura": "100% CIDADES PARTICIPACOES LTDA",
    "Ideia": "BOAS IDEIAS INTELIGENCIA EM PESQUISA E ESTRATEGIA DIGITAL LTDA",
    "Indexa": "INSTITUTO INDEXA PESQUISAS LTDA",
    "MDA": "MDA-PESQUISA DE OPINIAO PUBLICA E CONSULT. ESTATIST. LTDA - EPP",
    "Nexus": "NEXUS PESQUISA E INTELIGENCIA DE DADOS LTDA",
    "Palver": "PALVER CONSULTORIA E DESENVOLVIMENTO TECNOLOGICO LTDA.",
    "PoderData": "PODERDATA PESQUISA, JORNALISMO E COMUNICACAO LTDA",
    "Quaest": "QUAEST PESQUISAS, CONSULTORIA E PROJETOS LTDA.",
    "Real Time": "REAL TIME MIDIA LTDA",
    "Vox Brasil": "INSTITUTO VOX BRASIL OPINIAO E PESQUISAS LTDA",
}

SAIDA = C.PROCESSED / "auditoria_pesquisas.csv"


def extrair_metas_wikitext():
    """Extrai amostra, margem e link de cada linha do wikitext para 1T e 2T."""
    txt = WIKITEXT.read_text(encoding="utf-8")
    metas_1, metas_2 = {}, {}

    # 1º turno
    r1 = section(txt, "==== Aug–Oct (Campaign period) ====", "==== Apr–Aug ====")
    for cells in rows_of(r1):
        if len(cells) >= 12:
            p = clean(cells[0]).strip()
            d = clean(cells[1]).strip()
            df = data_fim(d)
            if p and p != "Results" and df:
                m = clean(cells[10]).strip()
                s = clean(cells[11]).strip().replace(",", "")
                link = cells[13] if len(cells) > 13 else ""
                m_url = re.search(r"url=(https?://[^\s\|\}]+)", link)
                url = m_url.group(1) if m_url else ""
                metas_1[(p, df)] = {"amostra": s, "margem": m, "url": url, "data_str": d}

    # 2º turno: no 2T não há coluna 'Others', então margem é idx 9, amostra é idx 10, link é idx 12
    r2 = section(txt, "==Second round==", "==See also==")
    r2 = section(r2, "==== Aug–Oct (Campaign period) ====", "==== Apr–Aug ====")
    for cells in rows_of(r2):
        if len(cells) >= 11:
            p = clean(cells[0]).strip()
            d = clean(cells[1]).strip()
            df = data_fim(d)
            if p and p != "Results" and df:
                m = clean(cells[9]).strip() if len(cells) > 9 else ""
                s = clean(cells[10]).strip().replace(",", "") if len(cells) > 10 else ""
                link = cells[12] if len(cells) > 12 else ""
                m_url = re.search(r"url=(https?://[^\s\|\}]+)", link)
                url = m_url.group(1) if m_url else ""
                metas_2[(p, df)] = {"amostra": s, "margem": m, "url": url, "data_str": d}

    return metas_1, metas_2


def auditar():
    reg_path = C.EXTERNAL / "registro_pesquisas_presidente_2026.csv"
    if not reg_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {reg_path}")

    with open(reg_path, encoding="utf-8") as f:
        registro = list(csv.DictReader(f))

    reg_by_emp = {}
    for r in registro:
        reg_by_emp.setdefault(r["empresa"], []).append(r)

    metas_1, metas_2 = extrair_metas_wikitext()

    saida_linhas = []
    total_casados = 0

    for t, f_csv, metas in [(1, C.INTERIM / "pesquisas_1turno.csv", metas_1),
                            (2, C.INTERIM / "pesquisas_2turno.csv", metas_2)]:
        with open(f_csv, encoding="utf-8") as f:
            polls = list(csv.DictReader(f))

        for idx, p in enumerate(polls, start=1):
            p_name = p["pollster"]
            df = p["data_fim"]
            meta = metas.get((p_name, df), {})
            amostra_wiki = meta.get("amostra", "")
            margem_wiki = meta.get("margem", "")
            url_wiki = meta.get("url", "")
            emp_tse = ALIASES.get(p_name, "")
            cands = reg_by_emp.get(emp_tse, [])

            match = None
            status = "sem_registro"
            obs = ""

            # 1. Casamento exato em data_fim e amostra
            if amostra_wiki:
                for c in cands:
                    if c["data_fim"] == df and c["amostra"] == amostra_wiki:
                        match = c
                        status = "casado_exato"
                        break

            # 2. Casamento exato na data_fim com amostra realizada próxima (diferença <= 3%)
            # Muito comum em pesquisas nacionais (ex.: registro prevê 5000, campo realiza 4945 ou 5018)
            if not match and amostra_wiki:
                try:
                    w_num = float(amostra_wiki)
                    for c in cands:
                        if c["data_fim"] == df:
                            c_num = float(c["amostra"])
                            if abs(w_num - c_num) / c_num <= 0.03:
                                match = c
                                status = "casado_amostra_realizada"
                                obs = f"Amostra TSE={c['amostra']} vs Wiki={amostra_wiki}"
                                break
                except ValueError:
                    pass

            # 3. Casamento com diferença de até 2 dias e mesma amostra (ou quase mesma)
            if not match and amostra_wiki:
                try:
                    w_num = float(amostra_wiki)
                    d1 = datetime.fromisoformat(df)
                    for c in cands:
                        d2 = datetime.fromisoformat(c["data_fim"])
                        if abs((d1 - d2).days) <= 2:
                            c_num = float(c["amostra"])
                            if c["amostra"] == amostra_wiki:
                                match = c
                                status = "casado_data_proxima"
                                obs = f"Data TSE={c['data_fim']} vs Wiki={df}"
                                break
                            elif abs(w_num - c_num) / c_num <= 0.03:
                                match = c
                                status = "casado_amostra_realizada"
                                obs = f"Data TSE={c['data_fim']} vs Wiki={df}; n TSE={c['amostra']} vs Wiki={amostra_wiki}"
                                break
                except ValueError:
                    pass

            # 4. Se só há uma pesquisa nacional registrada daquele instituto na data ou no intervalo
            if not match:
                same_date = [c for c in cands if c["data_fim"] == df]
                if len(same_date) == 1:
                    match = same_date[0]
                    status = "casado_data"
                    obs = f"Único registro na data: n TSE={match['amostra']} vs Wiki={amostra_wiki}"

            if match:
                total_casados += 1
                saida_linhas.append({
                    "turno": t,
                    "idx": idx,
                    "instituto": p_name,
                    "data_wiki": p["data"],
                    "data_fim_wiki": df,
                    "amostra_wiki": amostra_wiki,
                    "margem_wiki": margem_wiki,
                    "status_auditoria": status,
                    "protocolo_tse": match["protocolo"],
                    "empresa_tse": match["empresa"],
                    "data_fim_tse": match["data_fim"],
                    "data_divulgacao_tse": match["data_divulgacao"],
                    "amostra_planejada_tse": match["amostra"],
                    "diferenca_amostra": (int(amostra_wiki) - int(match["amostra"])) if (amostra_wiki.isdigit() and match["amostra"].isdigit()) else "",
                    "margem_tse_pp": match["margem_erro_pp"],
                    "custo_declarado_rs": match["custo"],
                    "contratantes": match["contratantes"],
                    "pagantes": match["pagantes"],
                    "url_referencia": url_wiki,
                    "observacoes": obs
                })
            else:
                saida_linhas.append({
                    "turno": t,
                    "idx": idx,
                    "instituto": p_name,
                    "data_wiki": p["data"],
                    "data_fim_wiki": df,
                    "amostra_wiki": amostra_wiki,
                    "margem_wiki": margem_wiki,
                    "status_auditoria": "sem_registro",
                    "protocolo_tse": "",
                    "empresa_tse": emp_tse,
                    "data_fim_tse": "",
                    "data_divulgacao_tse": "",
                    "amostra_planejada_tse": "",
                    "diferenca_amostra": "",
                    "margem_tse_pp": "",
                    "custo_declarado_rs": "",
                    "contratantes": "",
                    "pagantes": "",
                    "url_referencia": url_wiki,
                    "observacoes": "Registro oficial não localizado nos critérios definidos"
                })

    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        campos = list(saida_linhas[0].keys())
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(saida_linhas)

    print(f"Auditoria concluída: {total_casados}/112 pesquisas ({total_casados/112*100:.1f}%) casadas com registros do TSE.")
    print(f"Arquivo gerado em: {SAIDA}")
    return saida_linhas


def main():
    auditar()


if __name__ == "__main__":
    main()
