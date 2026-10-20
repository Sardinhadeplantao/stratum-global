"""Casos de referência propostos (grau-0.1 e agrupamento online). Rodar: venv/bin/python -m pytest -q grau/"""
from datetime import datetime, timedelta

import online
import regra_grau as R
from fichas import AGENCIAS, FICHAS

FICHAS_TESTE = FICHAS | {"rede_x": dict(nivel=5, controlador_tipo="privado", controlador="grupo:x",
                                        atos_proprios="nenhum")}
T0 = datetime(2026, 10, 19, 12, 0)


def doc(i, fonte, titulo, resumo=None, horas=0.0):
    t = T0 + timedelta(hours=horas)
    return dict(id=i, fonte=fonte, titulo=titulo, resumo=resumo or titulo, conhecido_em=t, quando=t)


def g(*docs):
    return R.grau(list(docs), FICHAS_TESTE, AGENCIAS)


# ---------- grau ----------

def test_g1_duas_manchetes_da_tass_sobre_o_mesmo_fato_sao_relatado():
    r = g(doc(114, "tass", "Russian forces to sweep liberated Dobropolye for scattered enemy groups — Donetsk leader"),
          doc(108, "tass", "More than 100 Ukrainian troops eliminated in Dobropolye mines — commander"))
    assert r["grau"] == "relatado" and r["vozes"] == ["estado:RUS"]


def test_g2_dw_e_france24_que_creditam_a_afp_sao_relatado():
    r = g(doc(1, "dw_mundo", "Quake kills dozens in Peru", "At least 30 people died, officials told AFP."),
          doc(2, "france24", "Strong earthquake hits Peru", "Rescuers search rubble (AFP)."))
    assert r["grau"] == "relatado" and r["vozes"] == ["agencia:afp"] and len(r["publicadores"]) == 2


def test_g3_federal_register_da_ofac_e_oficial_mesmo_sozinho():
    r = g(doc(1, "fr_ofac", "Notice of OFAC Sanctions Actions"))
    assert r["grau"] == "oficial" and r["oficiais"] == [1]


def test_g4_onu_news_noticiando_bombardeio_continua_relatado():
    r = g(doc(1, "onu_noticias", "Airstrike on market kills dozens in Sudan's El Fasher, UN says"))
    assert r["grau"] == "relatado" and r["vozes"] == ["org:ONU"]


def test_g5_onu_news_sobre_ato_do_proprio_orgao_e_oficial():
    assert g(doc(1, "onu_noticias", "Security Council extends UNIFIL mandate for a final year"))["grau"] == "oficial"
    assert g(doc(2, "onu_noticias", "WFP cuts aid to 500,000 people in Gaza as funds run dry"))["grau"] == "oficial"


def test_g6_fala_do_orgao_nao_e_ato():
    assert g(doc(1, "onu_noticias", "UN chief condemns attack on hospital in Gaza"))["grau"] == "relatado"
    assert g(doc(2, "onu_noticias", "Security Council members warn of famine in Sudan"))["grau"] == "relatado"


def test_g7_dois_controladores_diferentes_corroboram():  # evento A4.E1 do dev
    r = g(doc(5, "aljazeera", "Australian MP Helen Haines critically injured in ‘deliberate’ car ramming"),
          doc(54, "dw_mundo", "Australian MP seriously hurt in suspected car attack"))
    assert r["grau"] == "corroborado" and r["vozes"] == ["estado:DEU", "estado:QAT"]


def test_g8_tass_citando_afp_mais_tass_nao_corrobora():
    r = g(doc(148, "tass", "Nearly 2,400 people detained during unrest in France — agency",
              "According to the Interior Ministry, cited by AFP, 997 law enforcement officers were hurt"),
          doc(167, "tass", "Over 2,000 protesters detained during riots in France — interior minister"))
    assert r["vozes"] == ["agencia:afp", "estado:RUS"] and r["publicadores"] == ["estado:RUS"]
    assert r["grau"] == "relatado"  # 2 vozes, mas um só controlador publicou


def test_g9_bbc_mais_tass_citando_afp_corrobora():
    r = g(doc(43, "bbc_mundo", "Watch: Shops looted and restaurants gutted in Paris riots"),
          doc(148, "tass", "Nearly 2,400 people detained during unrest in France — agency", "cited by AFP"))
    assert r["grau"] == "corroborado"


def test_g10_quase_duplicata_de_veiculos_diferentes_conta_uma_vez():
    texto = "Gunmen killed at least 12 villagers in an overnight raid in Zamfara state, police said on Sunday."
    r = g(doc(1, "the_hindu", "Gunmen kill 12 villagers in Nigeria's Zamfara", texto),
          doc(2, "aljazeera", "Gunmen kill 12 villagers in Nigeria's Zamfara state", texto, horas=1))
    assert r["grau"] == "relatado" and r["grupos_de_texto"] == 1 and r["vozes"] == ["grupo:the_hindu"]


def test_g11_rede_social_sozinha_e_pista_e_nao_soma():
    assert g(doc(1, "rede_x", "Explosions reported near port"))["grau"] == "pista"
    r = g(doc(1, "rede_x", "Explosions reported near port"), doc(2, "tass", "Explosions sound in port city"))
    assert r["grau"] == "relatado" and r["vozes"] == ["estado:RUS"]


def test_g12_ap_sozinho_nao_e_credito():  # "AP" no The Hindu costuma ser Andhra Pradesh
    assert R.credito_agencia("AP Chief Minister inaugurates port") is None
    assert R.credito_agencia("the minister told The Associated Press") == "ap"
    assert R.credito_agencia("(Reuters) - Ships diverted") == "reuters"
    assert R.credito_agencia("disse à Agence France-Presse") == "afp"


def test_g13_negacao_nao_vira_contestado_na_versao_01():  # evento A8.E3 do dev
    r = g(doc(11, "aljazeera", "Rubio says there was no US pause in intelligence sharing with Ukraine"),
          doc(115, "tass", "Rubio says software problem behind recent air defense failure in Ukraine"),
          doc(190, "the_hindu", "Rubio says no pause in U.S. intel sharing with Ukraine"))
    assert r["grau"] == "corroborado"  # todos confirmam que Rubio negou; a negação é o próprio evento


def test_g14_mesmo_estado_conta_uma_voz_mesmo_com_veiculos_diferentes():
    fichas = FICHAS_TESTE | {"rfi": dict(FICHAS["france24"])}
    r = R.grau([doc(1, "france24", "Strike shuts Paris metro"), doc(2, "rfi", "Paris metro halted by strike")],
               fichas, AGENCIAS)
    assert r["grau"] == "relatado"


# ---------- caminho online ----------

def _mesmo_por_rotulo(d, docs_evento):
    return d.get("rotulo") is not None and any(x.get("rotulo") == d["rotulo"] for x in docs_evento)


def _d(i, fonte, rotulo, horas):
    x = doc(i, fonte, f"manchete {i}", horas=horas)
    x["rotulo"] = rotulo
    return x


def test_o1_mudanca_de_grau_cria_registro_novo_e_o_antigo_continua():
    b = online.Banco()
    online.processar(b, [_d(1, "tass", "A", 0)], _mesmo_por_rotulo, FICHAS_TESTE, AGENCIAS, T0)
    antes = [dict(x) for x in b.evento_grau]
    online.processar(b, [_d(2, "bbc_mundo", "A", 1)], _mesmo_por_rotulo, FICHAS_TESTE, AGENCIAS, T0 + timedelta(hours=1))
    assert b.evento_grau[:1] == antes                          # o registro antigo não mudou
    assert [x["grau"] for x in b.evento_grau] == ["relatado", "corroborado"]
    assert b.evento_grau[1]["documento_id"] == 2               # quem provocou a mudança
    assert online.mudancas_desde(b, T0) == [dict(evento_id=1, de="relatado", para="corroborado", documento_id=2)]


def test_o2_documento_que_nao_muda_o_grau_nao_cria_registro():
    b = online.Banco()
    online.processar(b, [_d(1, "tass", "A", 0), _d(2, "tass", "A", 1)], _mesmo_por_rotulo, FICHAS_TESTE, AGENCIAS, T0)
    assert len(b.evento_grau) == 1 and len(b.documento_evento) == 2


def test_o3_manchete_nova_nao_muda_evento_fora_da_janela():
    b = online.Banco()
    online.processar(b, [_d(1, "tass", "A", 0)], _mesmo_por_rotulo, FICHAS_TESTE, AGENCIAS, T0)
    online.processar(b, [_d(2, "bbc_mundo", "A", 49)], _mesmo_por_rotulo, FICHAS_TESTE, AGENCIAS, T0 + timedelta(hours=49))
    assert len(b.evento) == 2                                  # abriu evento novo
    assert b.docs_do_evento(1) == [b.documentos[1]] and b.grau_atual(1) == "relatado"


def test_o4_rodar_de_novo_nao_duplica_nada():
    b = online.Banco()
    lote = [_d(1, "tass", "A", 0), _d(2, "bbc_mundo", "A", 1)]
    online.processar(b, lote, _mesmo_por_rotulo, FICHAS_TESTE, AGENCIAS, T0)
    tamanhos = (len(b.evento), len(b.documento_evento), len(b.evento_grau))
    online.processar(b, lote, _mesmo_por_rotulo, FICHAS_TESTE, AGENCIAS, T0 + timedelta(minutes=15))
    assert (len(b.evento), len(b.documento_evento), len(b.evento_grau)) == tamanhos


def test_o5_manchete_nunca_muda_de_evento_nem_eventos_se_fundem():
    b = online.Banco()
    # 1 e 2 chegam antes e abrem eventos separados; 3 "liga" os dois, mas entra só no primeiro
    ponte = lambda d, docs: d["id"] == 3 or _mesmo_por_rotulo(d, docs)
    online.processar(b, [_d(1, "tass", "A", 0), _d(2, "bbc_mundo", "B", 0.5)], _mesmo_por_rotulo,
                     FICHAS_TESTE, AGENCIAS, T0)
    online.processar(b, [_d(3, "france24", "C", 1)], ponte, FICHAS_TESTE, AGENCIAS, T0 + timedelta(hours=1))
    assert [(l["documento_id"], l["evento_id"]) for l in b.documento_evento] == [(1, 1), (2, 2), (3, 1)]


def test_o6_manchete_atrasada_compara_pela_data_do_fato_nao_pela_chegada():
    b = online.Banco()
    online.processar(b, [_d(1, "tass", "A", 0)], _mesmo_por_rotulo, FICHAS_TESTE, AGENCIAS, T0)
    atrasada = _d(2, "bbc_mundo", "A", 1)
    atrasada["conhecido_em"] = T0 + timedelta(days=3)        # a fonte voltou 3 dias depois, com a notícia de T0+1h
    online.processar(b, [atrasada], _mesmo_por_rotulo, FICHAS_TESTE, AGENCIAS, T0 + timedelta(days=3))
    assert len(b.evento) == 1 and b.grau_atual(1) == "corroborado"
    assert b.evento_grau[-1]["calculado_em"] == T0 + timedelta(days=3)   # a mudança tem a data em que o sistema soube
