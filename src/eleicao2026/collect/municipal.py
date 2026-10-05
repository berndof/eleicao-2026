#!/usr/bin/env python3
"""Coleta e harmonização de indicadores municipais socioeconômicos e eleitorais.

Gera:
  data/external/municipios_chaves.csv   tabela de ligação entre códigos TSE, IBGE e SIAFI
  data/external/censo2022_mun.csv       indicadores do Censo 2022 por município (religião, raça, renda, urbanização)
  data/external/censo2022_dicionario.csv dicionário das variáveis do Censo 2022
  data/external/prefeitos_2024_mun.csv  partido do prefeito eleito em 2024 por município (TSE)

Uso:
  python -m eleicao2026.collect.municipal [--chaves] [--censo] [--prefeitos]
"""
import argparse
import csv
import gzip
import io
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from eleicao2026 import config as C
from eleicao2026.collect.util_eco import salvar_bruto, escrever_entrada, agora_utc

URL_CROSSWALK = "https://storage.googleapis.com/basedosdados-public/one-click-download/br_bd_diretorios_brasil/municipio/municipio.csv.gz"
URL_TSE_2024 = f"{C.TSE_CDN}/votacao_candidato_munzona/votacao_candidato_munzona_2024.zip"


def gerar_chaves():
    """Baixa o diretório de municípios (Base dos Dados) e gera data/external/municipios_chaves.csv."""
    C.EXTERNAL.mkdir(parents=True, exist_ok=True)
    saida = C.EXTERNAL / "municipios_chaves.csv"
    req = Request(URL_CROSSWALK, headers=C.UA)
    coletado_em = agora_utc()
    with urlopen(req, timeout=60) as r:
        raw_bytes = r.read()

    salvar_bruto("base_dos_dados_municipios", "municipio.csv.gz", raw_bytes, URL_CROSSWALK, coletado_em)

    linhas_out = []
    with gzip.open(io.BytesIO(raw_bytes), "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cd_tse = r["id_municipio_tse"].zfill(5) if r["id_municipio_tse"] else ""
            linhas_out.append({
                "cd_tse": cd_tse,
                "uf": r["sigla_uf"].lower(),
                "id_ibge7": r["id_municipio"],
                "id_ibge6": r["id_municipio_6"],
                "siafi": r["id_municipio_rf"].zfill(4) if r["id_municipio_rf"] else "",
                "nome": r["nome"],
                "capital": r["capital_uf"],
                "regiao": r["nome_regiao"]
            })

    # Adiciona o 5.571º município: Boa Esperança do Norte (MT), instalado em 2024/2025
    linhas_out.append({
        "cd_tse": "73709",
        "uf": "mt",
        "id_ibge7": "5101837",
        "id_ibge6": "510183",
        "siafi": "",
        "nome": "Boa Esperança do Norte",
        "capital": "0",
        "regiao": "Centro-Oeste"
    })

    linhas_out.sort(key=lambda x: (x["uf"], x["cd_tse"]))

    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas_out[0].keys()))
        w.writeheader()
        w.writerows(linhas_out)

    print(f"Gerado {saida} com {len(linhas_out)} municípios.")

    # Grava entrada de catálogo
    escrever_entrada({
        "id": "base_dos_dados_municipios",
        "nome": "Diretório de Municípios Brasileiros (TSE, IBGE, SIAFI)",
        "publicador": "Base dos Dados",
        "url_origem": URL_CROSSWALK,
        "url_landing": "https://basedosdados.org/dataset/br-bd-diretorios-brasil",
        "coletado_em": coletado_em,
        "sha256": "",
        "tamanho_bytes": len(raw_bytes),
        "licenca": "MIT / Open Data",
        "granularidade": "município (5.571 municípios)",
        "periodo": "versão atualizada com instalação de Boa Esperança do Norte (2024/2026)",
        "confianca": "alta",
        "status": "verificada",
        "usado_em": "data/external/municipios_chaves.csv; cruzamento entre códigos TSE e IBGE",
        "limitacoes": "Exterior (ZZ) não possui código IBGE correspondente."
    })
    return linhas_out


def _get_sidra(url):
    req = Request(url, headers=C.UA)
    with urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def coletar_censo2022():
    """Consulta o SIDRA/IBGE para variáveis municipais do Censo 2022."""
    chaves_file = C.EXTERNAL / "municipios_chaves.csv"
    if not chaves_file.exists():
        gerar_chaves()

    # Mapeamento ibge7 -> (cd_tse, uf, nome)
    ibge_to_tse = {}
    with open(chaves_file, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["id_ibge7"]:
                ibge_to_tse[r["id_ibge7"]] = (r["cd_tse"], r["uf"], r["nome"])

    dados_mun = {ibge: {"cd_tse": info[0], "uf": info[1], "nome": info[2], "id_ibge7": ibge}
                 for ibge, info in ibge_to_tse.items()}

    print("1/5 Coletando População (SIDRA 4714)...")
    url_pop = "https://apisidra.ibge.gov.br/values/t/4714/n6/all/v/93/p/2022?formato=json"
    pop_raw = _get_sidra(url_pop)
    for r in pop_raw[1:]:
        ibge = r.get("D1C")
        if ibge in dados_mun:
            dados_mun[ibge]["populacao_2022"] = r.get("V", "")

    print("2/5 Coletando Religião (SIDRA 9537)...")
    # c133: 95263 Católica, 95277 Evangélicas, 2836 Sem religião
    url_rel = "https://apisidra.ibge.gov.br/values/t/9537/n6/all/v/1000140/p/2022/c133/95263,95277,2836/c2/6794/c58/95253?formato=json"
    rel_raw = _get_sidra(url_rel)
    for r in rel_raw[1:]:
        ibge = r.get("D1C")
        if ibge in dados_mun:
            cat = r.get("D4C")
            val = r.get("V", "")
            if cat == "95263":
                dados_mun[ibge]["pct_catolica_10mais"] = val
            elif cat == "95277":
                dados_mun[ibge]["pct_evangelica_10mais"] = val
            elif cat == "2836":
                dados_mun[ibge]["pct_sem_religiao_10mais"] = val

    print("3/5 Coletando Situação Domicílio Urbana/Rural (SIDRA 9923)...")
    url_urb = "https://apisidra.ibge.gov.br/values/t/9923/n6/all/v/93/p/2022/c1/1,2?formato=json"
    urb_raw = _get_sidra(url_urb)
    temp_urb = {}
    for r in urb_raw[1:]:
        ibge = r.get("D1C")
        if ibge in dados_mun:
            sit = r.get("D4C")  # 1=Urbana, 2=Rural
            val = float(r.get("V", 0)) if r.get("V", "").replace(".", "").isdigit() else 0
            temp_urb.setdefault(ibge, {})[sit] = val

    for ibge, sits in temp_urb.items():
        u = sits.get("1", 0)
        ru = sits.get("2", 0)
        tot = u + ru
        dados_mun[ibge]["pop_urbana_2022"] = int(u)
        dados_mun[ibge]["pop_rural_2022"] = int(ru)
        dados_mun[ibge]["pct_urbana_2022"] = f"{(u / tot * 100):.2f}" if tot > 0 else ""

    print("4/5 Coletando Cor ou Raça (SIDRA 9605)...")
    url_raca = "https://apisidra.ibge.gov.br/values/t/9605/n6/all/v/93/p/2022/c86/2776,2777,2779?formato=json"
    raca_raw = _get_sidra(url_raca)
    temp_raca = {}
    for r in raca_raw[1:]:
        ibge = r.get("D1C")
        if ibge in dados_mun:
            cor = r.get("D4C")  # 2776=Branca, 2777=Preta, 2779=Parda
            val = float(r.get("V", 0)) if r.get("V", "").replace(".", "").isdigit() else 0
            temp_raca.setdefault(ibge, {})[cor] = val

    for ibge, cores in temp_raca.items():
        pop_tot = float(dados_mun[ibge].get("populacao_2022", 0) or 0)
        b = cores.get("2776", 0)
        p = cores.get("2777", 0)
        pa = cores.get("2779", 0)
        dados_mun[ibge]["pop_branca_2022"] = int(b)
        dados_mun[ibge]["pop_preta_2022"] = int(p)
        dados_mun[ibge]["pop_parda_2022"] = int(pa)
        if pop_tot > 0:
            dados_mun[ibge]["pct_branca_2022"] = f"{(b / pop_tot * 100):.2f}"
            dados_mun[ibge]["pct_preta_parda_2022"] = f"{((p + pa) / pop_tot * 100):.2f}"

    print("5/5 Coletando Renda Domiciliar Per Capita (SIDRA 10295)...")
    url_renda = "https://apisidra.ibge.gov.br/values/t/10295/n6/all/v/13431,13534/p/2022/c2/6794/c86/95251/c58/95253?formato=json"
    renda_raw = _get_sidra(url_renda)
    for r in renda_raw[1:]:
        ibge = r.get("D1C")
        if ibge in dados_mun:
            var = r.get("D2C")
            val = r.get("V", "")
            if var == "13431":
                dados_mun[ibge]["renda_media_percapita_2022"] = val
            elif var == "13534":
                dados_mun[ibge]["renda_mediana_percapita_2022"] = val

    linhas_censo = list(dados_mun.values())
    linhas_censo.sort(key=lambda x: (x["uf"], x["cd_tse"]))

    saida_censo = C.EXTERNAL / "censo2022_mun.csv"
    with open(saida_censo, "w", newline="", encoding="utf-8") as f:
        campos = ["cd_tse", "uf", "nome", "id_ibge7", "populacao_2022",
                  "pct_catolica_10mais", "pct_evangelica_10mais", "pct_sem_religiao_10mais",
                  "pop_urbana_2022", "pop_rural_2022", "pct_urbana_2022",
                  "pop_branca_2022", "pop_preta_2022", "pop_parda_2022", "pct_branca_2022", "pct_preta_parda_2022",
                  "renda_media_percapita_2022", "renda_mediana_percapita_2022"]
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas_censo)

    print(f"Salvo {saida_censo} com {len(linhas_censo)} municípios.")

    # Dicionário do Censo 2022
    dicionario = [
        {"coluna": "populacao_2022", "tabela_sidra": "4714", "variavel": "93", "definicao": "População residente total (Censo 2022)", "denominador": "total pessoas"},
        {"coluna": "pct_catolica_10mais", "tabela_sidra": "9537", "variavel": "1000140 (c133=95263)", "definicao": "Percentual de pessoas com 10 anos ou mais católicas", "denominador": "população com 10 anos ou mais"},
        {"coluna": "pct_evangelica_10mais", "tabela_sidra": "9537", "variavel": "1000140 (c133=95277)", "definicao": "Percentual de pessoas com 10 anos ou mais evangélicas", "denominador": "população com 10 anos ou mais"},
        {"coluna": "pct_sem_religiao_10mais", "tabela_sidra": "9537", "variavel": "1000140 (c133=2836)", "definicao": "Percentual de pessoas com 10 anos ou mais sem religião", "denominador": "população com 10 anos ou mais"},
        {"coluna": "pct_urbana_2022", "tabela_sidra": "9923", "variavel": "93 (c1=1)", "definicao": "Percentual da população residente em área urbana", "denominador": "população residente total"},
        {"coluna": "pct_branca_2022", "tabela_sidra": "9605", "variavel": "93 (c86=2776)", "definicao": "Percentual de pessoas autodeclaradas brancas", "denominador": "população residente total"},
        {"coluna": "pct_preta_parda_2022", "tabela_sidra": "9605", "variavel": "93 (c86=2777+2779)", "definicao": "Percentual de pessoas autodeclaradas pretas ou pardas", "denominador": "população residente total"},
        {"coluna": "renda_media_percapita_2022", "tabela_sidra": "10295", "variavel": "13431", "definicao": "Rendimento nominal médio mensal domiciliar per capita (R$)", "denominador": "moradores em domicílios ocupados"},
        {"coluna": "renda_mediana_percapita_2022", "tabela_sidra": "10295", "variavel": "13534", "definicao": "Rendimento nominal mediano mensal domiciliar per capita (R$)", "denominador": "moradores em domicílios ocupados"}
    ]
    saida_dic = C.EXTERNAL / "censo2022_dicionario.csv"
    with open(saida_dic, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["coluna", "tabela_sidra", "variavel", "definicao", "denominador"])
        w.writeheader()
        w.writerows(dicionario)

    escrever_entrada({
        "id": "ibge_censo_2022_municipios",
        "nome": "Indicadores Municipais do Censo Demográfico 2022 (SIDRA/IBGE)",
        "publicador": "IBGE",
        "url_origem": "https://apisidra.ibge.gov.br",
        "url_landing": "https://sidra.ibge.gov.br",
        "coletado_em": agora_utc(),
        "sha256": "",
        "tamanho_bytes": saida_censo.stat().st_size,
        "licenca": "IBGE Dados Abertos (CC-BY compatível)",
        "granularidade": "município (5.570 municípios)",
        "periodo": "ano censitário 2022 (religião divulgada em 06/06/2025)",
        "confianca": "alta",
        "status": "verificada",
        "usado_em": "data/external/censo2022_mun.csv; análise de perfil sociodemográfico e resíduos do modelo",
        "limitacoes": "Censo reflete população residente, não eleitorado. Falácia ecológica: correlação municipal não implica causalidade individual."
    })


def coletar_prefeitos_2024():
    """Baixa a votação municipal de 2024 e extrai o partido do prefeito eleito por município."""
    coletado_em = agora_utc()
    print("Baixando votação de 2024 do TSE (48 MB)...")
    req = Request(URL_TSE_2024, headers=C.UA)
    with urlopen(req, timeout=90) as r:
        raw_bytes = r.read()

    salvar_bruto("tse_votacao_2024", "votacao_candidato_munzona_2024.zip", raw_bytes, URL_TSE_2024, coletado_em)
    zf = zipfile.ZipFile(io.BytesIO(raw_bytes))

    prefeitos = {}
    for name in zf.namelist():
        if not name.endswith(".csv"):
            continue
        with zf.open(name) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="latin-1", errors="replace"), delimiter=";")
            for r in reader:
                if r.get("DS_CARGO") == "Prefeito":
                    sit = r.get("DS_SIT_TOT_TURNO", "")
                    if sit.startswith("ELEITO"):
                        uf = r["SG_UF"].lower()
                        cd = r["CD_MUNICIPIO"].zfill(5)
                        turno = int(r.get("NR_TURNO", 1))
                        chave = (uf, cd)
                        # Se já existir turno 1 e este for turno 2, substitui pelo 2º turno
                        if chave not in prefeitos or turno > prefeitos[chave]["nr_turno"]:
                            prefeitos[chave] = {
                                "cd_tse": cd,
                                "uf": uf,
                                "sg_partido": r.get("SG_PARTIDO", ""),
                                "sg_federacao": r.get("SG_FEDERACAO", ""),
                                "nr_turno": turno,
                                "situacao": sit
                            }

    linhas_pref = list(prefeitos.values())
    linhas_pref.sort(key=lambda x: (x["uf"], x["cd_tse"]))

    saida_pref = C.EXTERNAL / "prefeitos_2024_mun.csv"
    with open(saida_pref, "w", newline="", encoding="utf-8") as f:
        campos = ["cd_tse", "uf", "sg_partido", "sg_federacao", "nr_turno", "situacao"]
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas_pref)

    print(f"Salvo {saida_pref} com {len(linhas_pref)} prefeitos eleitos.")

    escrever_entrada({
        "id": "tse_prefeitos_2024",
        "nome": "Prefeitos Eleitos nas Eleições Municipais de 2024",
        "publicador": "TSE (Dados Abertos)",
        "url_origem": URL_TSE_2024,
        "url_landing": "https://dadosabertos.tse.jus.br/dataset/resultados-2024",
        "coletado_em": coletado_em,
        "sha256": "",
        "tamanho_bytes": len(raw_bytes),
        "licenca": "CC-BY",
        "granularidade": "município (5.568 municípios com prefeitos eleitos)",
        "periodo": "eleições municipais de 2024 (1º e 2º turnos)",
        "confianca": "alta",
        "status": "verificada",
        "usado_em": "data/external/prefeitos_2024_mun.csv; indicador de força partidária local e alinhamento político",
        "limitacoes": "Prefeito eleito não garante transferência automática de votos na eleição presidencial."
    })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chaves", action="store_true", help="Gera data/external/municipios_chaves.csv")
    ap.add_argument("--censo", action="store_true", help="Coleta Censo 2022 do SIDRA")
    ap.add_argument("--prefeitos", action="store_true", help="Coleta prefeitos 2024 do TSE")
    a = ap.parse_args()
    tudo = not (a.chaves or a.censo or a.prefeitos)
    if a.chaves or tudo:
        gerar_chaves()
    if a.censo or tudo:
        coletar_censo2022()
    if a.prefeitos or tudo:
        coletar_prefeitos_2024()


if __name__ == "__main__":
    main()
