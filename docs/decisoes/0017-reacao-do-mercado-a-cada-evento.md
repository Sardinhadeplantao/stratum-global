# 0017. Reação do mercado a cada evento

Data: 2026-10-21

## Contexto

Falta o último item da fase 2: "todo evento importante mostra se algum ativo ligado se mexeu fora do normal". O dono
quer ver o que bolsas, petróleo e moedas fizeram logo depois de cada acontecimento.

Os mercados já têm a régua única (decisão 0011) e o dia em andamento (decisão 0016). Faltava dizer o que é o evento,
quais ativos estão ligados a ele, quais dias contam e como separar reação de coincidência.

Com fechamento diário não dá para saber se a notícia saiu antes ou depois do fechamento de cada bolsa: a notícia das
23h de sexta chega depois do fechamento de sexta. E, com vários ativos, quase sempre algum sai do normal por acaso: com
6 ativos e 2 dias, isso acontece na maior parte dos períodos.

## Decisão (`reacao-0.1`)

1. **Evento**: cada história que aparece no site (decisão 0009) e cada ponto crítico em pauta ou crítico (decisão
   0014). O começo é a primeira notícia da história; no ponto, a primeira notícia das últimas 24 horas que o cita. O
   dia do evento é a data desse começo, em UTC.
2. **Ativos ligados**, por lista com critério escrito (regra 5):
   - de cada ponto crítico citado nos títulos: os mercados do ponto (`domain/pontos.py`);
   - de cada país citado nos títulos: a moeda contra o dólar (o DXY, nos EUA), a bolsa e o juro de 10 anos, quando o
     país tem essas séries. O euro contra a moeda (BCE) fica de fora: ele confere a cotação e repetiria a mesma moeda.
3. **Dias da reação**: o dia do evento e o pregão seguinte de cada ativo (2 pregões). **Base**: o último fechamento
   antes do dia do evento.
4. **Medida**: a régua de sempre (regra 6). A variação de cada dia é comparada com os 5 anos da própria série; fora do
   normal é o percentil até 5 ou a partir de 95. Dia de troca de contrato não conta. O dia em andamento entra marcado
   como parcial e muda até fechar.
5. **Desde o evento**: a variação do último valor contra a base, em coluna à parte.
6. **Taxa-base**: em quantos por cento dos períodos de 2 pregões dos 5 anos anteriores pelo menos um dos mesmos ativos
   saiu do normal. É ela que diz se "um ativo fora do normal" é raro ou corriqueiro para esse conjunto.
7. **Situação do evento**:
   - fora do normal: algum ativo saiu do normal nos dias da reação;
   - normal: houve pregão e nenhum saiu;
   - aguardando: ainda não houve pregão desde o evento;
   - sem ativo: nenhum ativo acompanhado está ligado ao evento.

## Consequências

- O site mostra, em cada história e em cada ponto, os ativos ligados, a variação desde o evento e a taxa-base.
- Mede coincidência no tempo, não causa: "saiu do normal no dia" não quer dizer que foi por causa do evento. O site
  diz isso ao lado.
- Preço é contexto (regra 8): a reação não muda a ordem das histórias nem dos pontos e não gera aviso.
- Movimento dentro do dia não é medido: as séries são diárias.
- País sem série acompanhada fica sem ativo ligado. Mais países e ativos entram pela lista de séries (`fontes.py`).
- Mudar o número de dias, a base ou a ligação de ativos pede decisão nova e versão nova da regra.
