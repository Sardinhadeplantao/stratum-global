"""Sonda da tradução (decisão 0010): baixa o modelo como o robô faz, traduz manchetes reais e mostra tempo e resultado.

Roda no GitHub Actions (workflow sondar.yml). Não grava nada.
Uso:  python scripts/sondar_traducao.py
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stratum import traducao  # noqa: E402

GABARITO = Path(__file__).resolve().parents[1] / "tests" / "gabarito" / "dev_19out.jsonl"


def main() -> None:
    t = time.time()
    raiz = traducao.baixar_modelo()
    print(f"Modelo {traducao.MODELO} pronto em {time.time() - t:.1f}s")
    t = time.time()
    tradutor = traducao.Tradutor(raiz)
    print(f"Carregado em {time.time() - t:.1f}s")
    titulos = [json.loads(l)["titulo"] for l in open(GABARITO, encoding="utf-8")]
    titulos = [x for x in titulos if x.isascii()][:200]
    t = time.time()
    saida = tradutor(titulos)
    print(f"{len(titulos)} títulos em {time.time() - t:.1f}s")
    for original, pt in list(zip(titulos, saida))[::20]:
        print(f"  {original}\n    → {pt}")


if __name__ == "__main__":
    main()
