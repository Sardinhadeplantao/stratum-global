# Stratum Global

Monitor de geopolítica e mercados globais. O usuário quer saber o que está acontecendo no mundo, se é verdade e se importa.
O dono do projeto não é programador: explique em português simples, decida pelo que é melhor e diga o porquê.
O plano está em `docs/plano.md`; as decisões, em `docs/decisoes/`.
O repositório ainda se chama `apex-trading-streamlit` e será renomeado para `stratum-global` pelo dono.
O endereço do site acompanha o nome do repositório sozinho (o robô usa o nome atual).

## Como funciona

- **Robô** (`jobs/`, Python): roda no GitHub Actions a cada 15 minutos (`.github/workflows/robo.yml`).
  Lê as fontes, grava o que é novo no banco e gera `web/public/dados/status.json`.
- **Banco**: PostgreSQL no Supabase (plano gratuito), pelo segredo `SUPABASE_SENHA` (servidor e usuário ficam no workflow)
  ou por um `DATABASE_URL` completo. Session pooler, porque o GitHub Actions não tem IPv6.
  Sem isso, o robô usa um SQLite temporário e diz isso na tela Método.
- **Site** (`web/`, Next.js estático + MapLibre): publicado no GitHub Pages. Só mostra o que o robô gravou.
- **Agendador**: o Supabase (pg_cron + pg_net) dispara o robô a cada 15 minutos; o GitHub atrasa horas
  (`agendador.py`, decisão 0004). O token fica no cofre do Supabase, colado pelo dono; o robô nunca o lê.
- **Avisos**: Telegram (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`), só um resumo às 7:30, 12:00 e 19:00 de Brasília
  (`resumo.py`, decisão 0005). Problemas entram no resumo; não há mensagem fora desses horários.
- **Cópia**: toda semana, `.github/workflows/copia.yml` copia as tabelas do projeto e testa a restauração
  (`copia.py`, decisão 0007). Fica como artefato do GitHub, público; tabela com dado pessoal não entra sem decisão.
- **IA**: nenhuma é obrigatória. Planejado: tarefa agendada do Claude para o briefing (fase 3) e API gratuita
  (Groq/Gemini) como ajudante opcional. LLM local foi descartada (`docs/decisoes/0001-arquitetura.md`).

## Regras que nenhuma mudança pode quebrar

1. **Duas datas em tudo**: quando aconteceu (`publicado_em`, `ocorreu_em`) e quando o sistema soube (`conhecido_em`, UTC).
2. **Nada é apagado nem reescrito.** O robô só insere. Correção vira registro novo. `downgrade` de migração não existe.
3. **Documento repetido não entra duas vezes**: identidade pelo hash da URL canônica (`domain/documento.py`).
4. **Notícia entra com grau de confirmação.** Rede social é pista, nunca fato, e nunca entra em conta.
5. **Escopo por lista com critério escrito.** Toda fonte em `fontes.py` tem `criterio`. Nada entra por parecer importante.
6. **Uma régua para todas as séries** (fase 2): percentil contra o próprio histórico, mesmos parâmetros, publicados na tela Método.
7. **Regra decide; IA só lê, resume e traduz.** Confirmação, importância, mudança e julgamento saem de regra testada.
   O sistema precisa funcionar com a IA desligada.
8. **Preço é contexto**: nunca ordena eventos nem dispara aviso sozinho.
9. **O site não calcula.** Cor só para estado medido; cinza = sem dado. Contagens, níveis de cor e proporções
   vêm prontos no status.json.
10. **Mostrar o que não se mede** (tela Método).
11. **Custo zero**: biblioteca gratuita antes de LLM; nada pago obrigatório.
12. **Segredos só nos Secrets do GitHub**, com uma exceção: o token `stratum_disparo`, que o dono cola no cofre (Vault)
    do Supabase (decisão 0004); o código nunca o lê, grava ou imprime.
    Nunca em código, log, mensagem de erro, conversa ou captura de tela; segredo que aparecer num desses lugares
    é trocado no mesmo dia.
    Erro de banco imprime só o tipo da exceção (a mensagem pode conter dados da conexão).
13. **Só a branch `main` grava no banco de produção e manda avisos.** Branches rodam com banco temporário.

## Estrutura

```
jobs/stratum/
  domain/        regras puras (sem banco, rede ou IA)
  connectors/    um conector por tipo de fonte; devolvem itens, não gravam
  fontes.py      a lista de fontes (única)
  db.py          esquema; mudou? crie migração nova em migracoes/versions/
  robo.py        uma rodada: coletar, gravar, registrar, avisar
  export.py      status.json para o site
  avisos.py      Telegram (envio)
  resumo.py      resumo das 7:30, 12:00 e 19:00
  agendador.py   Supabase dispara o robô a cada 15 minutos
  copia.py       cópia semanal do banco e restauração
  domain/paises.py      regra de citação de países (dicionário, sem IA)
  dados/nomes_paises.json  termos de cada país, gerado por scripts/preparar_nomes_paises.py
jobs/tests/      test_referencia.py = casos de referência (não altere para passar)
jobs/tests/gabarito/  manchetes agrupadas em eventos (fase 1); o conjunto de teste não serve para ajustar regra
jobs/scripts/    ferramentas avulsas: preparar_paises.py (mapa), preparar_nomes_paises.py (dicionário),
                 sondar_fontes.py (testa fonte candidata no GitHub Actions, workflow sondar.yml)
web/             site; dados do robô em public/dados/ (gerados, fora do git)
```

## Como trabalhar

- Uma tarefa por sessão, com um "pronto quando" claro (veja `docs/plano.md`).
- **Economia, pedido do dono**: o limite de uso é dele. Cada coisa se faz uma vez, direto, sem várias cópias do
  Claude em paralelo (workflows, agentes) nem leituras repetidas. Exceção só quando o dono pedir, ou uma revisão
  curta, de um agente, quando o código mexe no banco ou em senhas.
- Escreva ou ajuste o caso de referência antes do código. Se um caso de referência precisar mudar,
  a regra mudou: registre em `docs/decisoes/` antes.
- Decisão de projeto nova = arquivo curto em `docs/decisoes/` com data, contexto, decisão e consequência.
- Ideia fora da fase atual vai para `docs/ideias.md`.

## Comandos

```
cd jobs && pip install -r requirements.txt && python -m pytest        # testes do robô
cd jobs && python -m stratum.robo --exportar ../web/public/dados/status.json   # uma rodada (banco temporário sem senha do banco)
cd web && npm ci && npm test && npm run dev                           # site local em http://localhost:3000
```
