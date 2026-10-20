"""Estudo: agrupar notícias em eventos por vetores de frase de um modelo multilíngue gratuito (sentence-transformers).

Roda no GitHub Actions (workflow estudo.yml), onde o modelo pode ser baixado. Mede só no conjunto de desenvolvimento.
O modelo não decide nada sozinho: a regra é um limiar de semelhança, versionado como qualquer outra (regra 7).

Agrupamento online, como em produção: cada manchete entra no grupo da manchete já chegada mais parecida, se a
semelhança passar do limiar; senão abre um grupo novo. Nada é movido depois. Três ordens de chegada.
Variante "trava": não junta duas manchetes que citam países no título sem nenhum em comum (como em entidades/).
"""
import random
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))          # avaliar.py
sys.path.insert(0, str(AQUI.parents[2]))      # a pasta jobs/ (stratum)

from avaliar import carregar, medir  # noqa: E402
from stratum.domain import paises  # noqa: E402

MODELOS = [
    ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", ""),
    ("intfloat/multilingual-e5-small", "query: "),
    ("sentence-transformers/paraphrase-multilingual-mpnet-base-v2", ""),
]
LIMIARES = [round(0.50 + 0.025 * k, 3) for k in range(19)]   # 0,50 a 0,95
META_PRECISAO = 0.93                                          # margem sobre os 0,90 da meta, para o teste


def ordens(ids):
    embaralhada = list(ids)
    random.Random(1).shuffle(embaralhada)
    return {"crescente": sorted(ids), "decrescente": sorted(ids, reverse=True), "embaralhada": embaralhada}


def agrupar(sim, ids, ordem, limiar, permitido=None):
    pos = {i: k for k, i in enumerate(ids)}
    grupo_de, grupos, vistos = {}, [], []
    for i in ordem:
        a = pos[i]
        melhor, nota = None, -1.0
        for j in vistos:
            b = pos[j]
            if permitido is not None and not permitido[a, b]:
                continue
            if sim[a, b] > nota:
                melhor, nota = j, sim[a, b]
        if melhor is not None and nota >= limiar:
            grupo_de[i] = grupo_de[melhor]
            grupos[grupo_de[i]].append(i)
        else:
            grupo_de[i] = len(grupos)
            grupos.append([i])
        vistos.append(i)
    return grupos


def main():
    from sentence_transformers import SentenceTransformer

    docs, gold = carregar("dev_19out")
    ids = [d["id"] for d in docs]
    d = paises.carregar()
    no_titulo = [set(paises.citados(x["titulo"], d)) for x in docs]
    n = len(docs)
    trava = np.ones((n, n), dtype=bool)
    for a in range(n):
        for b in range(n):
            if no_titulo[a] and no_titulo[b] and not (no_titulo[a] & no_titulo[b]):
                trava[a, b] = False
    textos = {
        "titulo": [x["titulo"] for x in docs],
        "titulo+resumo": [x["titulo"] + ". " + (x["resumo"] or "")[:300] for x in docs],
    }
    ords = ordens(ids)
    melhores = []
    for nome, prefixo in MODELOS:
        t0 = time.time()
        modelo = SentenceTransformer(nome, device="cpu")
        carga = time.time() - t0
        for qual, lista in textos.items():
            t0 = time.time()
            v = modelo.encode([prefixo + t for t in lista], normalize_embeddings=True, batch_size=64)
            cod = time.time() - t0
            sim = v @ v.T
            print(f"\n## {nome} | {qual} | carregar {carga:.1f}s, {n} manchetes em {cod:.1f}s")
            print("variante | limiar | pior precisão | pior cobertura | eventos com par (pior) | meta")
            for variante, perm in (("pura", None), ("trava", trava)):
                escolha = None
                for t in LIMIARES:
                    rs = [medir(agrupar(sim, ids, o, t, perm), gold, docs) for o in ords.values()]
                    p = min(r["precisao_pares"] for r in rs)
                    c = min(r["cobertura_pares"] for r in rs)
                    e = min(r["eventos_com_par_juntado"] for r in rs)
                    ok = all(r["meta_atingida"] for r in rs)
                    print(f"{variante} | {t:.3f} | {p:.3f} | {c:.3f} | {e} de {rs[0]['eventos_multiplos']} | "
                          f"{'sim' if ok else 'não'}")
                    if p >= META_PRECISAO and (escolha is None or c > escolha[3]):
                        escolha = (nome, qual, variante, c, t, p, e, rs[0])
                if escolha:
                    melhores.append(escolha)
    print("\n# Melhor de cada combinação com precisão >= 0,93 na pior ordem")
    for nome, qual, variante, c, t, p, e, r in sorted(melhores, key=lambda x: -x[3]):
        print(f"{nome} | {qual} | {variante} | limiar {t} | precisão {p:.3f} | cobertura {c:.3f} | eventos {e} | "
              f"mesma fonte {r['cobertura_mesma_fonte']} | fontes diferentes {r['cobertura_fontes_diferentes']} | "
              f"entre idiomas {r['cobertura_entre_idiomas']}")


if __name__ == "__main__":
    main()
