"""Agendador pelo Supabase (decisão 0004): o comando não carrega o token e a situação sai de regra testada."""
from datetime import datetime, timedelta

import pytest

from stratum import agendador

AGORA = datetime(2026, 10, 19, 12, 0)


def test_comando_le_o_token_do_cofre_e_nao_o_contem():
    sql = agendador.comando("Sardinhadeplantao/stratum-global")
    assert "https://api.github.com/repos/Sardinhadeplantao/stratum-global/actions/workflows/robo.yml/dispatches" in sql
    assert "vault.decrypted_secrets where name = 'stratum_disparo'" in sql
    assert "jsonb_build_object('ref', 'main')" in sql and "User-Agent" in sql


@pytest.mark.parametrize("ruim", ["dono/repo'; drop table x; --", "sem-barra", "a/b/c", ""])
def test_comando_recusa_nome_de_repositorio_estranho(ruim):
    with pytest.raises(ValueError):
        agendador.comando(ruim)


def test_le_o_vencimento_do_cabecalho_do_github():
    assert agendador.ler_vencimento("2027-10-19 08:00:00 UTC") == datetime(2027, 10, 19, 8, 0)
    assert agendador.ler_vencimento("2027-10-19 08:00:00 -0300") == datetime(2027, 10, 19, 11, 0)
    assert agendador.ler_vencimento(None) is None and agendador.ler_vencimento("lixo") is None


@pytest.mark.parametrize("args,esperado", [
    (dict(), "aguardando"),
    (dict(chamada=AGORA - timedelta(minutes=10), resposta=204), "ok"),
    (dict(chamada=AGORA - timedelta(minutes=10), resposta=401), "token_invalido"),
    (dict(chamada=AGORA - timedelta(minutes=10), resposta=500), "falhando"),
    (dict(chamada=AGORA - timedelta(minutes=50), resposta=204), "falhando"),            # parou de chamar
    (dict(execucao=AGORA - timedelta(minutes=10)), "falhando"),                         # roda, mas não chama
    (dict(execucao=AGORA - timedelta(minutes=2)), "aguardando"),
    (dict(chamada=AGORA - timedelta(minutes=5), resposta=204, execucao_ok=False), "falhando"),
    (dict(chamada=AGORA - timedelta(minutes=5), resposta=204, vence_em=AGORA + timedelta(days=10)), "vence_logo"),
    (dict(chamada=AGORA - timedelta(minutes=5), resposta=204, vence_em=AGORA + timedelta(days=200)), "ok"),
])
def test_situacao_por_regra(args, esperado):
    assert agendador.avaliar(AGORA, **args).situacao == esperado


def test_sem_banco_permanente_nao_mexe_em_nada(engine):
    assert agendador.cuidar(engine, False, "Dono/repo", AGORA).situacao == "sem_banco"
    assert agendador.cuidar(engine, True, "Dono/repo", AGORA).situacao == "sem_banco"  # SQLite não tem pg_cron


def test_texto_para_o_resumo_e_o_site():
    e = agendador.avaliar(AGORA, chamada=AGORA, resposta=204, vence_em=AGORA + timedelta(days=9))
    assert e.texto() == "funcionando, mas o token vence em 9 dias: gere outro e troque no cofre do Supabase"
    status = e.para_status()
    assert status["situacao"] == "vence_logo" and status["dias_para_vencer"] == 9 and status["token_vence_em"].endswith("Z")
