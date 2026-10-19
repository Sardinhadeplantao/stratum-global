"""Agendador: o banco (Supabase) dispara o robô a cada 15 minutos (decisão 0004).

O agendamento do GitHub Actions atrasa horas no plano gratuito. O Supabase tem relógio próprio (pg_cron) e faz
chamadas web (pg_net). A cada 15 minutos, ele pede ao GitHub para rodar o robô (workflow_dispatch no main).

O token do GitHub fica no cofre do Supabase (Vault), colado pelo dono com o nome `stratum_disparo`.
O robô nunca lê nem grava o token. O comando agendado o busca no cofre na hora da chamada, então ele não aparece
no texto do agendamento, no código ou no log. A validade vem do cabeçalho da resposta do GitHub.

Só roda no main, com banco permanente. Uma falha aqui nunca derruba a rodada.
"""
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

NOME_SEGREDO = "stratum_disparo"
NOME_TAREFA = "stratum-robo"
HORARIO = "2,17,32,47 * * * *"          # a cada 15 minutos, fora da hora cheia
WORKFLOW = "robo.yml"
REF = "main"
DIAS_AVISO = 14                          # avisa quando o token vence em até 14 dias
SEM_CHAMADA_HA = timedelta(minutes=45)   # 3 chamadas perdidas seguidas: falhando

FALHAS = ("erro", "token_invalido", "falhando")
_REPOSITORIO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

# Texto para o resumo do Telegram e para a tela Método (o site usa o mesmo significado)
TEXTOS = {
    "ok": "funcionando: o Supabase dispara o robô a cada 15 minutos",
    "aguardando": "configurado; a primeira chamada sai em até 15 minutos",
    "vence_logo": "funcionando, mas o token vence em {dias} dias: gere outro e troque no cofre do Supabase",
    "falhando": "o Supabase não está conseguindo disparar o robô (última resposta do GitHub: {resposta})",
    "token_invalido": "o GitHub recusou o token: gere outro e troque no cofre do Supabase",
    "erro": "não foi possível configurar no Supabase ({erro})",
    "sem_token": "não configurado: falta o token no cofre do Supabase; o GitHub decide o horário e pode atrasar horas",
    "sem_banco": "precisa do banco permanente",
}


@dataclass
class Estado:
    situacao: str                        # ok | aguardando | vence_logo | falhando | token_invalido | erro | sem_token | sem_banco
    erro: str | None = None              # só o tipo da exceção (a mensagem pode conter dados da conexão)
    ultima_chamada: datetime | None = None
    resposta: int | None = None          # código HTTP que o GitHub devolveu na última chamada
    token_vence_em: datetime | None = None
    dias_para_vencer: int | None = None

    def texto(self) -> str:
        return TEXTOS[self.situacao].format(dias=self.dias_para_vencer, resposta=self.resposta or "nenhuma",
                                            erro=self.erro)

    def para_status(self) -> dict:
        def iso(d):
            return d.isoformat(timespec="seconds") + "Z" if d else None
        return {"situacao": self.situacao, "texto": self.texto(), "erro": self.erro,
                "ultima_chamada": iso(self.ultima_chamada), "resposta": self.resposta,
                "token_vence_em": iso(self.token_vence_em), "dias_para_vencer": self.dias_para_vencer}


def comando(repositorio: str) -> str:
    """O SQL que o pg_cron roda a cada 15 minutos. Não contém o token: ele é lido do cofre na hora."""
    if not _REPOSITORIO.match(repositorio):
        raise ValueError("nome de repositório inválido")
    url = f"https://api.github.com/repos/{repositorio}/actions/workflows/{WORKFLOW}/dispatches"
    return f"""select net.http_post(
  url := '{url}',
  headers := jsonb_build_object(
    'Authorization', 'Bearer ' || (select decrypted_secret from vault.decrypted_secrets where name = '{NOME_SEGREDO}'),
    'Accept', 'application/vnd.github+json',
    'X-GitHub-Api-Version', '2022-11-28',
    'User-Agent', 'stratum-global-agendador',
    'Content-Type', 'application/json'),
  body := jsonb_build_object('ref', '{REF}'),
  timeout_milliseconds := 15000)"""


def token_no_cofre(engine) -> bool:
    """O dono já colou o token no cofre? Olha só o nome, nunca o conteúdo."""
    with engine.connect() as c:
        return bool(c.execute(text("select exists(select 1 from vault.secrets where name = :n)"),
                              {"n": NOME_SEGREDO}).scalar())


def configurar(engine, repositorio: str) -> None:
    """Liga as extensões e cria ou atualiza a tarefa. Rodar de novo não duplica nada."""
    with engine.begin() as c:
        c.execute(text("create extension if not exists pg_cron with schema pg_catalog"))
        c.execute(text("create extension if not exists pg_net with schema extensions"))
        # Com o mesmo nome, o pg_cron atualiza a tarefa em vez de criar outra
        c.execute(text("select cron.schedule(:nome, :horario, :comando)"),
                  {"nome": NOME_TAREFA, "horario": HORARIO, "comando": comando(repositorio)})


def _utc(d: datetime | None) -> datetime | None:
    return d.astimezone(timezone.utc).replace(tzinfo=None) if d is not None and d.tzinfo is not None else d


def ultima_chamada(engine) -> dict:
    """A última resposta do GitHub (o pg_net guarda 6 horas) e a última execução da tarefa no pg_cron."""
    with engine.connect() as c:
        resposta = c.execute(text("select created, status_code, headers from net._http_response "
                                  "order by created desc limit 1")).first()
        execucao = c.execute(text("select d.start_time, d.status from cron.job_run_details d "
                                  "join cron.job j on j.jobid = d.jobid where j.jobname = :n "
                                  "order by d.start_time desc limit 1"), {"n": NOME_TAREFA}).first()
    cabecalhos = {str(k).lower(): v for k, v in ((resposta[2] or {}) if resposta else {}).items()}
    return {
        "chamada": _utc(resposta[0]) if resposta else None,
        "resposta": resposta[1] if resposta else None,
        "vence_em": ler_vencimento(cabecalhos.get("github-authentication-token-expiration")),
        "execucao": _utc(execucao[0]) if execucao else None,
        "execucao_ok": (execucao[1] != "failed") if execucao else True,
    }


def ler_vencimento(valor: str | None) -> datetime | None:
    """'2027-10-19 08:00:00 UTC' ou '2027-10-19 08:00:00 -0300' -> datetime em UTC, sem fuso."""
    if not valor:
        return None
    valor = str(valor).strip().replace(" UTC", " +0000")
    try:
        d = datetime.strptime(valor, "%Y-%m-%d %H:%M:%S %z")
    except ValueError:
        return None
    return d.astimezone(timezone.utc).replace(tzinfo=None)


def avaliar(agora: datetime, chamada: datetime | None = None, resposta: int | None = None,
            vence_em: datetime | None = None, execucao: datetime | None = None, execucao_ok: bool = True) -> Estado:
    """Regra da situação do agendador, já configurado. Testada em tests/test_agendador.py.
    chamada/resposta/vence_em: a última resposta do GitHub; execucao: a última vez que o pg_cron rodou a tarefa."""
    dias = None if vence_em is None else max((vence_em - agora).days, 0)
    base = dict(ultima_chamada=chamada, resposta=resposta, token_vence_em=vence_em, dias_para_vencer=dias)
    if resposta in (401, 403):
        return Estado("token_invalido", **base)
    if not execucao_ok:
        return Estado("falhando", **base)  # o próprio comando agendado deu erro no banco
    if resposta is not None and not 200 <= resposta < 300:
        return Estado("falhando", **base)
    if chamada is not None and agora - chamada > SEM_CHAMADA_HA:
        return Estado("falhando", **base)
    if chamada is None and execucao is not None and agora - execucao > timedelta(minutes=5):
        return Estado("falhando", **base)  # a tarefa roda, mas a chamada não sai (pg_net)
    if dias is not None and dias <= DIAS_AVISO:
        return Estado("vence_logo", **base)
    if chamada is None:
        return Estado("aguardando", **base)
    return Estado("ok", **base)


def cuidar(engine, banco_permanente: bool, repositorio: str | None, agora: datetime) -> Estado:
    """Uma passada por rodada: configura, confere e devolve a situação. Nunca levanta exceção."""
    if not banco_permanente or engine.dialect.name != "postgresql" or not repositorio:
        return Estado("sem_banco")
    try:
        if not token_no_cofre(engine):
            return Estado("sem_token")
        configurar(engine, repositorio)
        return avaliar(agora, **ultima_chamada(engine))
    except Exception as exc:  # a mensagem pode conter dados da conexão: só o tipo
        return Estado("erro", erro=type(exc).__name__)
