"""Mede agrupar.py no conjunto dev_19out nas 3 ordens de chegada e grava resultado.json.

Uso:  python medir.py              resumo na tela e resultado.json
      python medir.py --detalhes   também os erros de junção e as perdas (para as notas)
      python medir.py --tempo      também o tempo com ~2.800 manchetes (dev repetido 12 vezes)

Só usa o conjunto dev_19out (o de teste é guardado).
"""
import itertools
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))      # avaliar.py (medida comum)
sys.path.insert(0, str(AQUI))

from avaliar import carregar, medir  # noqa: E402
import agrupar as ag  # noqa: E402


def ordens(ids):
    emb = sorted(ids)
    random.Random(1).shuffle(emb)
    return {"crescente": sorted(ids), "decrescente": sorted(ids, reverse=True), "embaralhada": emb}


def notas_finais(docs, ordem, cfg=None):
    """Assinaturas e frequências como estavam no fim da ordem dada (para explicar erros e perdas)."""
    cfg = dict(ag.CONFIG, **(cfg or {}))
    por_id = {d["id"]: d for d in docs}
    vocab, sigs, df = set(), {}, Counter()
    for i in ordem:
        vocab |= ag.minusculas(por_id[i])
        sigs[i] = ag.assinatura(por_id[i], vocab, cfg)
        df.update(sigs[i].keys())
    return sigs, df, len(ordem)


def main():
    docs, gold = carregar("dev_19out")
    ids = [d["id"] for d in docs]
    por_id = {d["id"]: d for d in docs}
    resultado = {"conjunto": "dev_19out", "config": ag.CONFIG, "ordens": {}}
    grupos_por_ordem = {}
    for nome, ordem in ordens(ids).items():
        t = time.perf_counter()
        grupos = ag.agrupar(docs, ordem)
        seg = time.perf_counter() - t
        r = medir(grupos, gold, docs)
        grupos_por_ordem[nome] = grupos
        r = {k: v for k, v in r.items() if not k.startswith("erros_")}
        r["segundos"] = round(seg, 3)
        resultado["ordens"][nome] = r
    rs = resultado["ordens"].values()
    pior = min(rs, key=lambda r: (r["precisao_pares"], r["cobertura_pares"]))
    resultado["pior_ordem"] = {k: min(r[k] for r in rs) for k in
                               ("precisao_pares", "cobertura_pares", "bcubed_f", "eventos_com_par_juntado")}
    resultado["media"] = {k: round(sum(r[k] for r in rs) / 3, 3) for k in
                          ("precisao_pares", "cobertura_pares", "bcubed_f", "cobertura_mesma_fonte",
                           "cobertura_fontes_diferentes", "cobertura_entre_idiomas")}
    (AQUI / "resultado.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")

    print("Assinatura de entidades, dev_19out (236 manchetes, 108 pares no gabarito)")
    print(f"{'ordem':12s} {'precisão':>9s} {'cobertura':>10s} {'pares':>6s} {'certos':>7s} {'B3 F':>6s} "
          f"{'ev.c/par':>9s} {'mesma f.':>9s} {'f. dif.':>8s} {'idiomas':>8s} {'tempo':>7s}")
    for nome, r in resultado["ordens"].items():
        print(f"{nome:12s} {r['precisao_pares']:9.3f} {r['cobertura_pares']:10.3f} {r['pares_juntados']:6d} "
              f"{r['pares_certos']:7d} {r['bcubed_f']:6.3f} {r['eventos_com_par_juntado']:5d}/{r['eventos_multiplos']}"
              f" {r['cobertura_mesma_fonte']:9.3f} {r['cobertura_fontes_diferentes']:8.3f} "
              f"{r['cobertura_entre_idiomas']:8.3f} {r['segundos']:6.2f}s")
    print("pior ordem:", resultado["pior_ordem"])
    print("média:     ", resultado["media"])
    print("meta da fase 1 (no teste: precisão >= 0,90, cobertura >= 0,60, metade dos eventos com par):",
          "atingida no dev em todas as ordens" if all(r["meta_atingida"] for r in rs) else "NÃO atingida no dev")

    if "--detalhes" in sys.argv:
        detalhes(docs, gold, grupos_por_ordem, por_id)
    if "--tempo" in sys.argv:
        tempo(docs)


def detalhes(docs, gold, grupos_por_ordem, por_id):
    ev = gold["evento"]
    erros, perdas = Counter(), Counter()
    for nome, grupos in grupos_por_ordem.items():
        gid = {i: k for k, g in enumerate(grupos) for i in g}
        for a, b in itertools.combinations(sorted(ev), 2):
            junto, certo = gid[a] == gid[b], ev[a] == ev[b]
            if junto and not certo:
                erros[(a, b)] += 1
            if certo and not junto:
                perdas[(a, b)] += 1
    sigs, df, n = notas_finais(docs, sorted(ev))
    cfg = ag.CONFIG

    def linha(a, b):
        s = ag.nota(sigs[a], sigs[b], df, n, cfg)
        comuns = sorted(sigs[a].keys() & sigs[b].keys())
        return (f"  nota {s:.2f}  {a} [{ev[a]}] {por_id[a]['titulo'][:80]}\n"
                f"              {b} [{ev[b]}] {por_id[b]['titulo'][:80]}\n"
                f"              em comum: {' '.join(comuns)[:150]}")

    print("\nERROS DE JUNÇÃO (pares juntados que o gabarito separa), com o número de ordens em que aparecem:")
    for (a, b), k in sorted(erros.items(), key=lambda x: (-x[1], x[0])):
        print(f" [{k}/3]", linha(a, b))
    # os próximos erros: pares errados de nota mais alta abaixo do limiar (o que entraria se o limiar baixasse)
    cand = []
    for a, b in itertools.combinations(sorted(ev), 2):
        if ev[a] != ev[b] and (a, b) not in erros:
            s = ag.nota(sigs[a], sigs[b], df, n, cfg)
            if s > 0:
                cand.append((s, a, b))
    cand.sort(reverse=True)
    print("\nPRÓXIMOS ERROS (pares errados de nota mais alta que ficaram abaixo do limiar):")
    for s, a, b in cand[:12]:
        print(linha(a, b))
    print("\nPERDAS (pares do gabarito não juntados), as de nota mais alta, perdidas nas 3 ordens:")
    pl = [(ag.nota(sigs[a], sigs[b], df, n, cfg), a, b) for (a, b), k in perdas.items() if k == 3]
    pl.sort(reverse=True)
    for s, a, b in pl[:12]:
        print(linha(a, b))
    por_ev = Counter(ev[a] for (a, b), k in perdas.items() if k == 3)
    print("\nPares perdidos (nas 3 ordens) por evento:", por_ev.most_common())


def tempo(docs):
    copias = []
    for k in range(12):
        for d in docs:
            copias.append(dict(d, id=d["id"] + 1000 * k))
    t = time.perf_counter()
    ag.agrupar(copias)
    print(f"\nTempo com {len(copias)} manchetes (dev repetido 12 vezes, pior caso: cópias idênticas): "
          f"{time.perf_counter() - t:.1f} s")


if __name__ == "__main__":
    main()
