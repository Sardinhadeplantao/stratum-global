"""Configuração lida do ambiente. Nenhuma chave fica no código, em log ou em arquivo do repositório."""
import os
from dataclasses import dataclass
from urllib.parse import quote

USER_AGENT_PADRAO = "stratum-global/0.1 (+https://github.com/Sardinhadeplantao/stratum-global)"


@dataclass(frozen=True)
class Config:
    database_url: str | None      # Supabase em produção. Sem ela, o robô usa um banco temporário
    telegram_token: str | None
    telegram_chat: str | None
    user_agent: str
    repositorio: str | None = None     # dono/nome, que o GitHub Actions informa sozinho
    ultima_copia: str | None = None    # data da última cópia do banco no GitHub ("" = nenhuma; None = não conferida)

    @property
    def banco_permanente(self) -> bool:
        return self.database_url is not None

    @property
    def telegram_configurado(self) -> bool:
        return bool(self.telegram_token and self.telegram_chat)


def _env(nome: str) -> str | None:
    return (os.environ.get(nome) or "").strip() or None


def endereco_do_banco() -> str | None:
    """DATABASE_URL completo; ou, mais simples para o dono, só a senha (SUPABASE_SENHA, um segredo) junto com o
    servidor e o usuário do Supabase (SUPABASE_HOST e SUPABASE_USUARIO, que não são segredo e ficam no workflow)."""
    if url := _env("DATABASE_URL"):
        return url
    senha, host, usuario = _env("SUPABASE_SENHA"), _env("SUPABASE_HOST"), _env("SUPABASE_USUARIO")
    if not (senha and host and usuario):
        return None
    # quote: senha com @, # ou / quebraria o endereço
    return f"postgresql://{quote(usuario, safe='.')}:{quote(senha, safe='')}@{host}:5432/postgres"


def ler() -> Config:
    return Config(
        database_url=endereco_do_banco(),
        telegram_token=_env("TELEGRAM_BOT_TOKEN"),
        telegram_chat=_env("TELEGRAM_CHAT_ID"),
        user_agent=_env("STRATUM_USER_AGENT") or USER_AGENT_PADRAO,
        repositorio=_env("GITHUB_REPOSITORY"),
        ultima_copia=os.environ.get("STRATUM_ULTIMA_COPIA"),  # vazio tem significado: não usa _env
    )
