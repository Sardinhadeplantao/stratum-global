"""Aplica a regra grau-0.1 aos eventos do gabarito dev (os grupos do gabarito no lugar do agrupamento).

Uso: venv/bin/python grau/aplicar_dev.py   (só o conjunto dev; o de teste não é aberto)
"""
import collections
import json
import random
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path[:0] = [str(AQUI), str(AQUI.parent)]
from avaliar import carregar          # noqa: E402
import regra_grau as R                # noqa: E402
from fichas import AGENCIAS, FICHAS   # noqa: E402


def main():
    docs, gold = carregar("dev_19out")
    por_id = {d["id"]: d for d in docs}
    eventos = collections.defaultdict(list)
    for i, e in gold["evento"].items():
        eventos[e].append(i)

    ordens = {"crescente": sorted(por_id), "decrescente": sorted(por_id, reverse=True)}
    embaralhada = sorted(por_id)
    random.Random(1).shuffle(embaralhada)
    ordens["embaralhada"] = embaralhada

    resultados = {}
    for nome, ordem in ordens.items():
        posicao = {i: k for k, i in enumerate(ordem)}
        graus = {}
        for e, ids in eventos.items():
            ds = [dict(por_id[i], conhecido_em=f"{posicao[i]:06d}") for i in ids]
            graus[e] = R.grau(ds, FICHAS, AGENCIAS)
        resultados[nome] = graus

    base = resultados["crescente"]
    iguais = all({e: r["grau"] for e, r in resultados[o].items()} == {e: r["grau"] for e, r in base.items()}
                 for o in ordens)
    contagem = collections.Counter(r["grau"] for r in base.values())
    print(f"Eventos: {len(base)}  (manchetes: {len(docs)})")
    print("Por grau:", {g: contagem.get(g, 0) for g in R.ORDEM})
    print("Mesmo resultado nas 3 ordens de chegada:", iguais)

    tamanho = collections.Counter()
    for e, r in base.items():
        n = len(eventos[e])
        tamanho[(r["grau"], "1 manchete" if n == 1 else "2 ou mais")] += 1
    print("Grau x tamanho:", dict(sorted(tamanho.items())))

    so_tass = sum(1 for e, ids in eventos.items() if all(por_id[i]["fonte"] == "tass" for i in ids))
    print("Eventos só da TASS:", so_tass)
    multi_mesmo = [e for e, r in base.items() if len(eventos[e]) > 1 and r["grau"] == "relatado"]
    print("Eventos com 2+ manchetes que ficaram relatado (um controlador só):", len(multi_mesmo),
          sorted({por_id[i]["fonte"] for e in multi_mesmo for i in eventos[e]}))

    creditos = [(i, R.credito_agencia(d["titulo"] + "\n" + (d["resumo"] or "")), d["fonte"]) for i, d in por_id.items()]
    creditos = [c for c in creditos if c[1]]
    print("Manchetes com crédito de agência:", creditos)
    mudou = []
    for e, r in base.items():
        sem = R.grau([dict(por_id[i], titulo=por_id[i]["titulo"].replace("AFP", "x"),
                           resumo=(por_id[i]["resumo"] or "").replace("AFP", "x")) for i in eventos[e]],
                     FICHAS, AGENCIAS)
        if sem["grau"] != r["grau"]:
            mudou.append(e)
    print("Eventos cujo grau muda por causa do crédito de agência:", mudou)
    print("Eventos oficiais:", [e for e, r in base.items() if r["grau"] == "oficial"])
    print("Quase-duplicatas encontradas (grupos de texto < manchetes contáveis):",
          [e for e, r in base.items() if r["grupos_de_texto"] < r["documentos"]])

    print("\nCorroborados:")
    for e, r in sorted(base.items(), key=lambda kv: (-len(kv[1]["vozes"]), kv[0])):
        if r["grau"] == "corroborado":
            print(f"  {e}: {len(eventos[e])} manchetes, {len(r['vozes'])} vozes {r['vozes']}")

    tipo_evento = {gold["evento"][i]: gold["tipo"][i] for i in por_id}
    por_tipo = collections.Counter((tipo_evento[e], r["grau"]) for e, r in base.items())
    print("\nTipo do evento (gabarito) x grau:", dict(sorted(por_tipo.items())))
    print("Manchetes por fonte:", dict(collections.Counter(d["fonte"] for d in docs).most_common()))

    # Sensibilidade às duas escolhas que o dono pode rever (AFP como Estado francês; Al Jazeera, mesma chave)
    agencias_afp_fra = AGENCIAS | {"afp": dict(AGENCIAS["afp"], controlador="estado:FRA")}
    mudam = [e for e, ids in eventos.items()
             if R.grau([por_id[i] for i in ids], FICHAS, agencias_afp_fra)["grau"] != base[e]["grau"]]
    print("Eventos que mudam de grau com a AFP = estado:FRA:", mudam)

    saida = {e: dict(r, ids=sorted(eventos[e])) for e, r in base.items()}
    (AQUI / "graus_dev.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
