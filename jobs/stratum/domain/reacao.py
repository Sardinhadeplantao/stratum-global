"""Reação do mercado a cada evento (decisão 0017): o que os ativos ligados a um evento fizeram no dia dele e no pregão
seguinte, medido pela régua de sempre (regra 6), com a taxa-base ao lado.

Regra pura: sem banco, rede ou IA. Mede coincidência no tempo, não causa: "saiu do normal no dia" não quer dizer que
foi por causa do evento. Preço é contexto (regra 8): a reação não ordena eventos nem dispara aviso.
"""
from bisect import bisect_left
from datetime import date, timedelta

from stratum.domain import regua

REGRA = "reacao-0.1"
DIAS = 2  # o dia do evento e o pregão seguinte: com fechamento diário não dá para saber se a notícia veio antes ou
          # depois do fechamento de cada mercado
GRUPOS_DO_PAIS = ("moedas", "bolsas", "juros")  # nesta ordem, para cada país citado
MOEDA_DE_MERCADO = "yahoo_cambio"               # a moeda contra o dólar (nos EUA, o DXY); a do BCE só confere


def ligados(paises: list[dict], pontos: list[dict], series: list[dict]) -> list[tuple[str, dict]]:
    """Os ativos ligados a um evento, sem repetir: primeiro os mercados de cada ponto crítico citado, depois a moeda,
    a bolsa e o juro de cada país citado. `paises`: [{iso, nome}]; `pontos`: os de domain/pontos.py; `series`: o
    catálogo (fontes.SERIES). Devolve (id da série, por que está ligada)."""
    ativas = {s["id"]: s for s in series if s.get("ativa", True) and s.get("frequencia", "diaria") == "diaria"}
    saida: dict[str, dict] = {}
    for p in pontos:
        for sid in p["mercados"]:
            if sid in ativas:
                saida.setdefault(sid, {"tipo": "ponto", "id": p["id"], "nome": p["nome"]})
    for pais in paises:
        do_pais = [s for s in ativas.values() if s.get("pais") == pais["iso"]
                   and (s["grupo"] != "moedas" or s.get("fonte") == MOEDA_DE_MERCADO)]
        for s in sorted(do_pais, key=lambda s: GRUPOS_DO_PAIS.index(s["grupo"]) if s["grupo"] in GRUPOS_DO_PAIS else 9):
            if s["grupo"] in GRUPOS_DO_PAIS:
                saida.setdefault(s["id"], {"tipo": "pais", "id": pais["iso"], "nome": pais["nome"]})
    return list(saida.items())


def _r(x: float | None, casas: int) -> float | None:
    return None if x is None else round(x, casas)


class Medidor:
    """Mede a reação de vários eventos sobre as mesmas séries, sem refazer a conta de um ativo no mesmo dia.

    `series`: por id, {"pts": [(data, valor)] em ordem de data, "medida", e opcionais "frequencia", "trocas" (dias de
    troca de contrato) e "ultimo" ({"data", "situacao", "parcial"}: a leitura do último dia no painel de mercados,
    para a reação dizer o mesmo que o painel naquele dia)."""

    def __init__(self, series: dict[str, dict]):
        self.series = series
        self._ativos: dict = {}
        self._historicos: dict = {}
        self._taxas: dict = {}

    def ativo(self, sid: str, dia: date) -> dict | None:
        """A reação de uma série a um evento do dia `dia`: a base, os dias da reação e a variação desde o evento."""
        if (sid, dia) not in self._ativos:
            self._ativos[(sid, dia)] = self._medir(sid, dia)
        return self._ativos[(sid, dia)]

    def _medir(self, sid: str, dia: date) -> dict | None:
        s = self.series.get(sid)
        if not s or not s["pts"]:  # série sem nenhum dado: não entra (não é "sem pregão")
            return None
        pts, medida = s["pts"], s["medida"]
        frequencia, trocas, ultimo = s.get("frequencia", "diaria"), s.get("trocas") or frozenset(), s.get("ultimo") or {}
        i = bisect_left([d for d, _ in pts], dia)
        base = pts[i - 1] if i > 0 else None
        dias = []
        for j in range(i, min(i + DIAS, len(pts))):
            d = pts[j][0]
            lido = regua.ler(pts[:j + 1], medida, frequencia, trocas, mudancas=False)
            situacao, extremo = lido.situacao, lido.extremo
            e_o_ultimo = j == len(pts) - 1 and ultimo.get("data") == d
            if e_o_ultimo and ultimo.get("situacao") in ("nao_confere", "parada"):
                situacao, extremo = ultimo["situacao"], None  # o mesmo que o painel diz deste dia
            dias.append({"data": d.isoformat(), "variacao": _r(lido.medida, 2), "percentil": _r(lido.percentil, 1),
                         "extremo": extremo if situacao == "ok" else None, "situacao": situacao,
                         "parcial": bool(e_o_ultimo and ultimo.get("parcial"))})
        desde = None
        # Troca de contrato futuro entre a base e o último valor: os preços são de contratos diferentes e a conta
        # mediria o salto da troca, não o mercado
        troca = bool(base and i < len(pts) and any(base[0] < d <= pts[-1][0] for d in trocas))
        if base and i < len(pts) and not troca:
            medidas = regua.MEDIDAS[medida]([base, pts[-1]])
            desde = _r(medidas[0][1], 2) if medidas else None
        return {"base": {"data": base[0].isoformat(), "valor": base[1]} if base else None, "dias": dias,
                "extremo": next((x["extremo"] for x in dias if x["extremo"]), None),
                "desde": desde, "troca_de_contrato": troca, "ate": pts[-1][0].isoformat() if i < len(pts) else None,
                # o último valor é o do dia em andamento: o "desde o evento" ainda muda
                "parcial": bool(i < len(pts) and ultimo.get("parcial") and ultimo.get("data") == pts[-1][0])}

    def _historico(self, sid: str) -> tuple[list[date], dict[date, bool], date | None]:
        """Para a taxa-base: as datas da série, se cada dia saiu do normal e o primeiro dia com régua."""
        if sid not in self._historicos:
            s = self.series[sid]
            trocas = s.get("trocas") or frozenset()
            medidas = [m for m in regua.MEDIDAS[s["medida"]](s["pts"]) if m[0] not in trocas]
            ps = regua.percentis(medidas, regua.MINIMO[s.get("frequencia", "diaria")])
            fora = {d: p <= regua.EXTREMO or p >= 100 - regua.EXTREMO for (d, _), p in zip(medidas, ps) if p is not None}
            self._historicos[sid] = ([d for d, _ in s["pts"]], fora, min(fora, default=None))
        return self._historicos[sid]

    def taxa_base(self, sids: list[str], dia: date) -> dict | None:
        """Em quantos % dos períodos de DIAS pregões dos 5 anos antes do evento pelo menos um destes ativos saiu do
        normal. Um período começa em cada dia do calendário e vale quando todos os ativos têm a régua nele e ele
        termina antes do dia do evento. Dia de troca de contrato conta como normal (não mede o mercado)."""
        chave = (tuple(sorted(sids)), dia)
        if chave in self._taxas:
            return self._taxas[chave]
        historicos = [self._historico(s) for s in sids if s in self.series]
        resultado = None
        if historicos and all(h[2] for h in historicos):
            validos = vezes = 0
            d = max([regua.anos_antes(dia, regua.JANELA_ANOS)] + [h[2] for h in historicos])
            while d < dia:
                algum, ok = False, True
                for datas, fora, _ in historicos:
                    k = bisect_left(datas, d)
                    janela = datas[k:k + DIAS]
                    if len(janela) < DIAS or janela[-1] >= dia:
                        ok = False
                        break
                    algum = algum or any(fora.get(x, False) for x in janela)
                if ok:
                    validos += 1
                    vezes += algum
                d += timedelta(days=1)
            if validos >= regua.MINIMO["diaria"]:
                resultado = {"pct": round(vezes / validos * 100), "periodos": validos, "dias": DIAS,
                             "anos": regua.JANELA_ANOS}
        self._taxas[chave] = resultado
        return resultado

    def evento(self, dia: date, ligacoes: list[tuple[str, dict]]) -> dict:
        """A reação de um evento do dia `dia` (UTC) nos ativos ligados. Situação: fora_do_normal | normal | aguardando
        (nenhum pregão desde o evento) | sem_ativo (nenhum ativo acompanhado ligado)."""
        ativos = []
        for sid, por in ligacoes:
            r = self.ativo(sid, dia)
            if r is not None:
                ativos.append({"id": sid, "por": por} | r)
        fora = sum(1 for a in ativos if a["extremo"])
        situacao = ("sem_ativo" if not ativos else "aguardando" if not any(a["dias"] for a in ativos)
                    else "fora_do_normal" if fora else "normal")
        ativos.sort(key=lambda a: not a["extremo"])  # os que saíram do normal primeiro; o resto na ordem da ligação
        return {"regra": REGRA, "dia": dia.isoformat(), "situacao": situacao, "fora": fora, "ativos": ativos,
                "taxa_base": self.taxa_base([a["id"] for a in ativos], dia) if ativos else None}
