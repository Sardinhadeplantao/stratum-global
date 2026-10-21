"""Sonda as fontes de séries (decisão 0011) do jeito que o robô lê, e mostra o começo do arquivo bruto.

Roda no GitHub Actions (workflow sondar.yml), porque a máquina do Claude não alcança o BCE nem o FRED. O trecho
bruto impresso vira a amostra real guardada em tests/fixtures (regra de fonte nova). Nada é gravado.

Uso:  python scripts/sondar_series.py
"""
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stratum import config, fontes  # noqa: E402
from stratum.connectors import rss, series as conectores  # noqa: E402


def main() -> None:
    sessao, ua = rss.nova_sessao(), config.ler().user_agent
    desde = date.today() - timedelta(days=10)
    for f in fontes.ativas():
        if f["conector"] not in conectores.CONECTORES:
            continue
        da_fonte = [s for s in fontes.SERIES if s["fonte"] == f["id"] and s.get("ativa", True)]
        amostra = da_fonte[:2] if f["conector"] == "bce" else da_fonte[:1]
        url = {"bce": lambda: conectores.url_bce(f, [s["codigo"] for s in amostra], desde),
               "fred": lambda: conectores.url_fred(f, amostra[0]["codigo"], desde),
               "yahoo": lambda: conectores.url_yahoo(f, amostra[0]["codigo"], desde, int(time.time()) + 86400)}[f["conector"]]()
        try:
            bruto = conectores._baixar(sessao, url, ua)
            print(f"::group::Bruto de {f['id']} [{url}]\n" + "\n".join(bruto.splitlines()[:12])[:6000] + "\n::endgroup::")
            obs = conectores.CONECTORES[f["conector"]](f, da_fonte, sessao, ua, desde)
        except Exception as exc:  # noqa: BLE001 - a sonda só relata
            print(f"FALHOU {f['id']}: {type(exc).__name__}: {str(exc)[:160]}  [{url}]")
            if f["conector"] == "yahoo":  # diagnóstico: a recusa é pelo nome do robô (User-Agent)?
                r = sessao.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
                print(f"  com User-Agent de navegador: HTTP {r.status_code}, {len(r.content)} bytes")
            continue
        por_codigo: dict[str, list] = {}
        for o in obs:
            por_codigo.setdefault(o.codigo, []).append(o)
        faltam = [s["codigo"] for s in da_fonte if s["codigo"] not in por_codigo]
        print(f"OK {f['id']}: {len(obs)} observações de {len(por_codigo)} séries"
              + (f"; sem dado: {', '.join(faltam)}" if faltam else ""))
        for codigo, lista in sorted(por_codigo.items()):
            print(f"  {codigo}: {lista[-1].data} = {lista[-1].valor}")


if __name__ == "__main__":
    main()
