# Plano

O caminho do usuário: **aconteceu → é verdade? → importa? → quem é afetado? → o que vem por aí?**
Cada fase entrega algo usável e termina num "pronto quando" verificável.

## Fase 0. Fundação ✅ (código pronto; falta a configuração em `docs/configurar.md`)

- [x] Robô no GitHub Actions a cada 15 minutos, com testes antes de cada rodada
- [x] Banco com migrações automáticas; banco temporário quando o Supabase não está configurado
- [x] Primeiras fontes (oficiais e imprensa de vários blocos), sem duplicatas, com registro de cada coleta
- [x] Site com o globo (países do Natural Earth, cinza = sem medição), painel do país e tela Método
- [x] Resumo no Telegram às 7:30, 12:00 e 19:00 de Brasília (decisão 0005)
- [x] Agendador pelo Supabase: o robô roda a cada 15 minutos, sem depender do horário do GitHub (decisão 0004)
- [ ] Supabase, Telegram e GitHub Pages ligados pelo dono (passo a passo em `docs/configurar.md`)

**Pronto quando:** o site está no ar, a tela Método diz "Banco: Permanente" e a mensagem de teste chega no Telegram.

## Fase 1. Monitor (4 a 6 semanas)

Já entregue: nome Stratum Global, página inicial no formato do esboço (globo, últimas atualizações, indicadores,
cartões) e a regra de citação de países (dicionário com nomes, gentílicos, capitais e siglas; versão atual em `docs/decisoes/0003-regra-paises-0.2.md`).

Falta:

- Lista de fontes completa: oficiais (diários oficiais, sanções, chancelarias, ONU, UE), imprensa de vários blocos
  com o controle de cada veículo (privado, público, estatal) documentado com fonte, GDELT para volume.
- Caminho do documento até o evento: idioma, tradução (Argos/Opus-MT), quase-duplicatas (MinHash),
  nomes com código (GLiNER + Wikidata), lugar (GeoNames), agrupamento em eventos.
- Grau de confirmação (pista, relatado, corroborado, oficial, contestado) e importância calculados por regra.
- Globo com eventos, lista de eventos, página do evento e do país, alertas por regra no Telegram, briefing extrativo.

**Pronto quando:** você acompanha o mundo por uma semana só pelo Stratum Global.

## Fase 2. Mercados (3 a 4 semanas)

- Séries por lista: moedas (BCE, FRED), juros de 10 anos, bolsa por país, commodities (Banco Mundial, EIA), cripto.
- A régua única (percentil contra o próprio histórico) e a reação medida a cada evento.
- Tela Mercados: o que se mexeu fora do normal e os eventos no mesmo período ("coincidência no tempo, não causa").

**Pronto quando:** todo evento importante mostra se algum ativo ligado se mexeu fora do normal.

## Fase 3. IA como redatora (2 a 3 semanas)

- Tarefa agendada do Claude: briefing da manhã com citação de cada fonte; zelador semanal que propõe consertos.
- API gratuita (Groq, com Gemini de reserva) para títulos e resumos dos eventos importantes.
- Conjunto de ~100 documentos anotados para medir se a IA melhora sem inventar fonte.

**Pronto quando:** o briefing é melhor que o extrativo no conjunto anotado e toda citação confere.

## Fase 4. Medição física (4 a 6 semanas)

PortWatch (navios nos estreitos), comércio (UN Comtrade, BACI), sanções e conflito (UCDP, ACLED) como séries,
calendário geopolítico, picos de cobertura, comparação entre imprensas de blocos diferentes.

**Pronto quando:** eventos aparecem ligados a fluxos físicos, além do mercado.

## Fase 5. Grafo, hipóteses e arquivo (4 a 6 semanas)

Ligações país–commodity–ativo com fonte e peso, simulação de choque, hipóteses com placar,
perguntas sobre o arquivo com citação, rever o passado como o sistema o via.

**Pronto quando:** o teste retroativo não usa dado do futuro.

## Para quando abrir ao público

Login, aviso legal, licenças de dados (mercado não oficial, ACLED e OpenSanctions são só para uso não comercial),
briefing por API própria em vez do plano pessoal do Claude.
