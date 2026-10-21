"""Sonda o PortWatch (FMI e Universidade de Oxford): navios por dia em cada estreito, candidato a série (fase 4,
adiantado a pedido do dono). Roda no GitHub Actions (workflow sondar.yml), porque a máquina do Claude não alcança o
ArcGIS. Mostra os campos, os nomes dos estreitos, o atraso do dado, o tamanho do histórico e os termos de uso.
Nada é gravado; o trecho bruto impresso vira a amostra real em tests/fixtures.

Uso:  python scripts/sondar_navios.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stratum import config  # noqa: E402
from stratum.connectors import rss  # noqa: E402

SERVICO = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer"
NOSSOS = ["Hormuz", "Mandeb", "Suez", "Malacca", "Bosporus", "Dardanelles", "Oresund", "Danish", "Belt", "Panama",
          "Good Hope", "Gibraltar"]


def pedir(sessao, ua, url, params=None):
    r = sessao.get(url, params=params, headers={"User-Agent": ua}, timeout=60)
    print(f"  HTTP {r.status_code} · {len(r.content)} bytes · {r.url[:200]}")
    r.raise_for_status()
    return r.json()


def main() -> int:
    sessao, ua = rss.nova_sessao(), config.ler().user_agent
    print("== Camada (campos e limite por pedido)")
    camada = pedir(sessao, ua, f"{SERVICO}/0", {"f": "json"})
    print(f"  nome: {camada.get('name')} · maxRecordCount: {camada.get('maxRecordCount')} · "
          f"editado: {camada.get('editingInfo', {}).get('dataLastEditDate')}")
    for c in camada.get("fields", []):
        print(f"  campo {c['name']} ({c['type']}): {c.get('alias')}")
    print("== Termos (itemInfo)")
    try:
        info = pedir(sessao, ua, f"{SERVICO}/info/itemInfo", {"f": "pjson"})
        for k in ("title", "snippet", "licenseInfo", "accessInformation", "description"):
            print(f"  {k}: {str(info.get(k))[:1500]}")
    except Exception as exc:  # noqa: BLE001 - sonda: mostra e segue
        print(f"  falhou: {type(exc).__name__}: {exc}")
    print("== Estreitos")
    nomes = pedir(sessao, ua, f"{SERVICO}/0/query", {"where": "1=1", "outFields": "portid,portname",
                                                     "returnDistinctValues": "true", "returnGeometry": "false", "f": "json"})
    estreitos = sorted({(f["attributes"]["portid"], f["attributes"]["portname"]) for f in nomes.get("features", [])},
                       key=lambda x: int("".join(ch for ch in x[0] if ch.isdigit()) or 0))
    for pid, nome in estreitos:
        print(f"  {pid}: {nome}{'   <- ponto nosso' if any(n.lower() in nome.lower() for n in NOSSOS) else ''}")
    print("== Histórico e atraso por estreito nosso")
    for pid, nome in estreitos:
        if not any(n.lower() in nome.lower() for n in NOSSOS):
            continue
        est = pedir(sessao, ua, f"{SERVICO}/0/query", {
            "where": f"portid='{pid}'", "returnGeometry": "false", "f": "json",
            "outStatistics": json.dumps([{"statisticType": "count", "onStatisticField": "date", "outStatisticFieldName": "n"},
                                         {"statisticType": "min", "onStatisticField": "date", "outStatisticFieldName": "primeiro"},
                                         {"statisticType": "max", "onStatisticField": "date", "outStatisticFieldName": "ultimo"}])})
        print(f"  {pid} {nome}: {est.get('features', [{}])[0].get('attributes') if est.get('features') else est}")
    hormuz = next((pid for pid, nome in estreitos if "hormuz" in nome.lower()), None)
    if hormuz:
        print(f"== Últimos 21 dias de {hormuz}, bruto (amostra para tests/fixtures)")
        bruto = pedir(sessao, ua, f"{SERVICO}/0/query", {
            "where": f"portid='{hormuz}'", "outFields": "*", "orderByFields": "date DESC", "resultRecordCount": "21",
            "returnGeometry": "false", "f": "json"})
        print(json.dumps(bruto, ensure_ascii=False)[:12000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
