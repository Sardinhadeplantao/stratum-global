"""Pontos críticos do mapa (decisão 0014): estreitos e canais por onde passa o petróleo do mundo.

Regra pura, sem IA: dá para conferir palavra por palavra.
- Lista: os pontos de passagem da análise do EIA (agência de energia dos EUA), com o volume de petróleo de cada um.
- Uma notícia cita o ponto quando o título ou o resumo traz um dos nomes dele, como palavra inteira, com as maiúsculas
  do nome ("Suezmax" não é Suez).
- Estado em 24 horas: em pauta (uma notícia ou mais); crítico (palavra de ação numa delas e duas vozes independentes,
  isto é, donos diferentes); sem pauta (nenhuma). Mede a atenção das fontes, não a gravidade.
"""
import re

REGRA = "pontos-0.1"
EIA = "https://www.eia.gov/international/content/analysis/special_topics/World_Oil_Transit_Chokepoints/"
EIA_STEO = "https://www.eia.gov/outlooks/steo/report/energysecurity/article.php"
VOZES_PARA_CRITICO = 2


def _fato(texto: str, periodo: str, url: str = EIA) -> dict:
    return {"texto": texto, "periodo": periodo, "fonte": "EIA (agência de energia dos EUA)", "url": url}


# lon, lat: o centro do ponto no mapa. mercados: ids das séries ligadas (fontes.SERIES). portwatch: o estreito no
# PortWatch do FMI, para os navios por dia (decisão 0018); portwatch_nota: o que a conta do PortWatch não cobre
PONTOS: list[dict] = [
    dict(id="ormuz", nome="Estreito de Ormuz", lon=56.4, lat=26.5, margens=["IRN", "OMN", "ARE"], portwatch="chokepoint6",
         termos=["Strait of Hormuz", "Hormuz", "Estreito de Ormuz", "Ormuz"],
         mercados=["commodity_bz", "commodity_cl", "commodity_ttf"],
         fatos=[_fato("20,9 milhões de barris de petróleo por dia, cerca de um quarto do petróleo vendido por mar e "
                      "20% do consumo mundial", "1º semestre de 2025"),
                _fato("O fluxo caiu para 14,9 milhões de barris por dia no 1º trimestre de 2026 e 4,9 no 2º; o EIA avisa "
                      "que os sinais dos navios na região ficaram pouco confiáveis desde o fim de fevereiro de 2026",
                      "2026", EIA_STEO)]),
    dict(id="bab_el_mandeb", nome="Bab el-Mandeb e Mar Vermelho", lon=43.4, lat=12.6, margens=["YEM", "DJI", "ERI"],
         portwatch="chokepoint4",
         termos=["Bab el-Mandeb", "Bab al-Mandab", "Bab-el-Mandeb", "Bab el Mandeb", "Red Sea", "Mar Vermelho"],
         mercados=["commodity_bz", "commodity_ttf"],
         fatos=[_fato("4,2 milhões de barris de petróleo por dia; o fluxo caiu muito depois dos ataques houthis a navios, "
                      "a partir do fim de 2023", "1º semestre de 2025"),
                _fato("Subiu para 8,1 milhões de barris por dia", "2º trimestre de 2026", EIA_STEO)]),
    dict(id="suez", nome="Canal de Suez e oleoduto SUMED", lon=32.35, lat=30.4, margens=["EGY"], portwatch="chokepoint1",
         portwatch_nota="Só os navios do canal; o petróleo do oleoduto SUMED não aparece nesta conta.",
         termos=["Suez Canal", "Suez", "SUMED", "Canal de Suez"],
         mercados=["commodity_bz", "commodity_ttf"],
         fatos=[_fato("4,9 milhões de barris de petróleo por dia (eram 8,8 em 2023)", "1º semestre de 2025")]),
    dict(id="malaca", nome="Estreito de Malaca", lon=100.9, lat=2.9, margens=["MYS", "IDN", "SGP"], portwatch="chokepoint5",
         termos=["Strait of Malacca", "Malacca Strait", "Malacca", "Singapore Strait", "Estreito de Malaca"],
         mercados=["commodity_bz", "bolsa_000001ss"],
         fatos=[_fato("23,2 milhões de barris de petróleo por dia, cerca de 29% do petróleo vendido por mar: o maior "
                      "ponto de passagem do mundo", "1º semestre de 2025"),
                _fato("16,6 milhões de barris por dia", "2º trimestre de 2026", EIA_STEO)]),
    dict(id="estreitos_turcos", nome="Estreitos turcos (Bósforo e Dardanelos)", lon=29.05, lat=41.1, margens=["TUR"],
         portwatch="chokepoint3", portwatch_nota="Só o Bósforo: o PortWatch não conta os Dardanelos à parte.",
         termos=["Bosporus", "Bosphorus", "Dardanelles", "Turkish Straits", "Bósforo", "Dardanelos", "Estreitos turcos"],
         mercados=["commodity_bz", "commodity_zw", "yahoo_try"],
         fatos=[_fato("3,7 milhões de barris de petróleo e derivados por dia, cerca de 5% do comércio marítimo",
                      "1º semestre de 2025")]),
    dict(id="estreitos_dinamarqueses", nome="Estreitos dinamarqueses", lon=11.0, lat=55.7, margens=["DNK", "SWE"],
         portwatch="chokepoint10", portwatch_nota="Só o Øresund: o Grande Belt, rota dos navios de maior calado, não é "
                                                  "coberto pelo PortWatch.",
         termos=["Danish Straits", "Great Belt", "Øresund", "Oresund", "Estreitos dinamarqueses"],
         mercados=["commodity_bz"], fatos=[]),
    dict(id="panama", nome="Canal do Panamá", lon=-79.7, lat=9.1, margens=["PAN"], portwatch="chokepoint2",
         termos=["Panama Canal", "Canal do Panamá", "Canal de Panamá"],
         mercados=["commodity_cl", "commodity_zs", "commodity_zc"],
         fatos=[_fato("Mais de 2,3 milhões de barris de petróleo por dia (ano fiscal de outubro a setembro)",
                      "ano fiscal de 2025")]),
    dict(id="cabo_boa_esperanca", nome="Cabo da Boa Esperança", lon=18.5, lat=-34.4, margens=["ZAF"], portwatch="chokepoint7",
         termos=["Cape of Good Hope", "Cabo da Boa Esperança"], mercados=["commodity_bz"], fatos=[]),
]

# Palavras de ação (em minúsculas, como início de palavra): o que transforma "citado" em "crítico" com duas vozes
ACOES = [
    "attack", "strike", "struck", "missile", "drone", "mine", "mined", "seize", "seizure", "hijack", "blockade",
    "blocked", "closure", "explosion", "exploded", "fire", "ablaze", "sink", "sank", "sunk", "torpedo", "warship",
    "ataque", "atac", "míssil", "mísseis", "mina", "minas", "apreens", "apreend", "sequestr", "bloquei", "fechament",
    "explos", "incêndio", "incendi", "afund",
]
_ACAO = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(a) for a in sorted(ACOES, key=len, reverse=True)) + r")\w*",
                   re.IGNORECASE)
_PADROES = {p["id"]: re.compile(r"(?<!\w)(?:" + "|".join(re.escape(t) for t in sorted(p["termos"], key=len, reverse=True))
                                + r")(?!\w)") for p in PONTOS}


def citados(texto: str | None) -> set[str]:
    """Ids dos pontos que o texto cita."""
    if not texto:
        return set()
    return {pid for pid, padrao in _PADROES.items() if padrao.search(texto)}


def tem_acao(texto: str | None) -> bool:
    return bool(texto and _ACAO.search(texto))


def estados(noticias: list[dict]) -> dict[str, dict]:
    """Estado de cada ponto a partir das notícias da janela (sem rede social; quem chama já tirou).
    Cada notícia: titulo, resumo e controlador (o dono; duas notícias do mesmo dono são uma voz)."""
    saida = {p["id"]: {"noticias": 0, "vozes": set(), "com_acao": 0} for p in PONTOS}
    for n in noticias:
        texto = f"{n.get('titulo') or ''}\n{n.get('resumo') or ''}"
        for pid in citados(texto):
            s = saida[pid]
            s["noticias"] += 1
            s["vozes"].add(n.get("controlador"))
            s["com_acao"] += tem_acao(texto)
    resultado = {}
    for pid, s in saida.items():
        vozes = len(s["vozes"])
        estado = ("sem_pauta" if s["noticias"] == 0
                  else "critico" if s["com_acao"] and vozes >= VOZES_PARA_CRITICO else "em_pauta")
        resultado[pid] = {"estado": estado, "noticias": s["noticias"], "vozes": vozes, "com_acao": s["com_acao"]}
    return resultado
