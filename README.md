# Stratum Global

Monitor de geopolítica e mercados globais: o que está acontecendo no mundo, com fonte e grau de confirmação,
ligado ao que se mede nos mercados.

**Site:** https://sardinhadeplantao.github.io/stratum-global/ (depois que o repositório for renomeado para
`stratum-global`; até lá, https://sardinhadeplantao.github.io/apex-trading-streamlit/)

## Como funciona

```
A cada 15 min (Supabase dispara)       Toda manhã (fase 3)
Robô (GitHub Actions)                  Redator (tarefa agendada do Claude)
  lê as fontes → grava o que é novo      lê os eventos do dia
  → banco (Supabase)                     → escreve o briefing com links
  → atualiza o site → resumo no Telegram (7:30, 12h, 19h)
                  ↓
        Site com o globo (GitHub Pages)
```

Custo: zero, dentro dos planos gratuitos do GitHub, Supabase e Telegram.

## Onde está cada coisa

- `jobs/`: robô em Python (coleta, banco, citações de países, status). Testes em `jobs/tests`.
- `web/`: site (Next.js estático + MapLibre).
- `docs/plano.md`: as fases e o que conta como pronto.
- `docs/configurar.md`: passo a passo para ligar banco, Telegram e site.
- `docs/decisoes/`: decisões de projeto, com data e motivo.
- `CLAUDE.md`: regras que toda sessão de IA segue ao mexer no projeto.

Fronteiras: Natural Earth (domínio público). Termos e nomes de países: derivados de
[mledoze/countries](https://github.com/mledoze/countries). O arquivo `jobs/stratum/dados/nomes_paises.json` é
disponibilizado sob a [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1.0/).

*Informação de contexto baseada em fontes públicas. Não é recomendação de investimento.*
