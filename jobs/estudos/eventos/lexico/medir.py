"""Mede o agrupar() léxico no conjunto dev_19out, nas 3 ordens de chegada, e grava resultado.json.

Uso:
    python medir.py            # resumo
    python medir.py --erros    # também lista as junções erradas e as perdas, com as manchetes

Só usa o dev. O conjunto de teste não é aberto aqui.
"""
import itertools
import json
import math
import random
import sys
import time
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))   # avaliar.py (medida comum)
sys.path.insert(0, str(AQUI))

from avaliar import carregar, medir  # noqa: E402
import agrupar as A  # noqa: E402


def ordens(docs):
    ids = sorted(d["id"] for d in docs)
    emb = ids[:]
    random.Random(1).shuffle(emb)
    return {"crescente": ids, "decrescente": ids[::-1], "embaralhada": emb}


def main():
    docs, gold = carregar("dev_19out")
    por_id = {d["id"]: d for d in docs}
    resultado, grupos_por_ordem = {}, {}
    t0 = time.perf_counter()
    for nome, ordem in ordens(docs).items():
        grupos = A.agrupar(docs, ordem)
        grupos_por_ordem[nome] = grupos
        resultado[nome] = medir(grupos, gold, docs)
    tempo = time.perf_counter() - t0
    erros = {n: (r.pop("erros_juntou"), r.pop("erros_separou")) for n, r in resultado.items()}
    (AQUI / "resultado.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")

    chaves = ["precisao_pares", "cobertura_pares", "bcubed_f", "pares_juntados", "pares_certos",
              "eventos_com_par_juntado", "cobertura_mesma_fonte", "cobertura_fontes_diferentes",
              "cobertura_entre_idiomas", "meta_atingida"]
    print(f"CONFIG: {json.dumps(A.CONFIG, ensure_ascii=False)}")
    print(f"{'':32s}" + "".join(f"{n:>13s}" for n in resultado))
    for k in chaves:
        print(f"{k:32s}" + "".join(f"{str(r[k]):>13s}" for r in resultado.values()))
    for k in ("precisao_pares", "cobertura_pares", "bcubed_f"):
        v = [r[k] for r in resultado.values()]
        print(f"{k}: pior {min(v):.3f}  média {sum(v) / len(v):.3f}")
    print(f"eventos com 2+ manchetes: {resultado['crescente']['eventos_multiplos']}; "
          f"tempo das 3 ordens: {tempo:.2f} s")

    if "--erros" in sys.argv:
        listar_erros(docs, gold, por_id, grupos_por_ordem)


def _cos_par(docs):
    """Cosseno título x título com o IDF da janela (o mesmo vetor do agrupar), só para o relatório."""
    pesos, textos = {}, {}
    for d in docs:
        pesos[d["id"]], textos[d["id"]] = A.pesos_doc(d, A.CONFIG)
    idf = A.idf_janela(textos)
    v = {i: A.vetor(p, idf) for i, p in pesos.items()}
    return lambda a, b: sum(x * v[b].get(t, 0.0) for t, x in v[a].items())


def listar_erros(docs, gold, por_id, grupos_por_ordem):
    cos = _cos_par(docs)
    ev = gold["evento"]

    def pares(grupos):
        return {tuple(sorted(p)) for g in grupos for p in itertools.combinations(g, 2)}

    juntou = Counter()
    for g in grupos_por_ordem.values():
        for p in pares(g):
            if ev[p[0]] != ev[p[1]]:
                juntou[p] += 1
    ouro = {tuple(sorted(p)) for e in set(ev.values())
            for p in itertools.combinations([i for i in ev if ev[i] == e], 2)}
    perdeu = Counter()
    for g in grupos_por_ordem.values():
        pp = pares(g)
        for p in ouro - pp:
            perdeu[p] += 1

    def m(i):
        d = por_id[i]
        return f"[{i} {d['fonte']}] {d['titulo']}"

    print("\n== JUNÇÕES ERRADAS (em quantas ordens; cosseno título x título)")
    for p, n in sorted(juntou.items(), key=lambda x: (-x[1], -cos(*x[0])))[:10]:
        print(f"  {n}/3  cos {cos(*p):.2f}  {ev[p[0]]} x {ev[p[1]]}\n      {m(p[0])}\n      {m(p[1])}")
    sempre = [p for p, n in perdeu.items() if n == 3]
    print(f"\n== PERDAS: {len(sempre)} pares do gabarito separados nas 3 ordens; por evento:")
    por_ev = Counter(ev[p[0]] for p in sempre)
    for e, n in por_ev.most_common():
        print(f"  {e}: {n} pares perdidos")
    print("\n== AS 10 PERDAS MAIS PERTO DE ENTRAR (maior cosseno, separadas nas 3 ordens)")
    for p in sorted(sempre, key=lambda p: -cos(*p))[:10]:
        print(f"  cos {cos(*p):.2f}  {ev[p[0]]}\n      {m(p[0])}\n      {m(p[1])}")


if __name__ == "__main__":
    main()
