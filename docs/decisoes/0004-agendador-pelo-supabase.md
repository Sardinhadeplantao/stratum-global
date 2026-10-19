# 0004. Agendador pelo Supabase

Data: 2026-10-19

## Contexto

O robô deveria rodar a cada 15 minutos, mas o agendamento do GitHub Actions é "quando der". Entre 16 e 19 de
outubro ele rodou só 20 vezes, com intervalos de 2 a 5 horas, em vez de umas 280 vezes. O GitHub avisa que, em
horários de carga, rodadas agendadas atrasam ou são descartadas. Relatos de 2026 dizem que repositórios novos e
gratuitos são os mais afetados. O site mostrava notícias de 5 horas antes, e o aviso de dados parados acendeu.

Alternativas consideradas:

- **Deixar como está**: o "pronto quando" da fase 1 é acompanhar o mundo só pelo Stratum Global, e isso não dá com
  dados de horas atrás.
- **Robô dormindo dentro do GitHub** (uma rodada longa que repete a coleta): ocupa uma máquina do GitHub o dia
  inteiro. Os termos do GitHub Actions proíbem usá-lo como servidor genérico.
- **Serviço de agendamento externo** (cron-job.org e parecidos): mais uma conta, e a chave ficaria num serviço a mais.
- **Mover o robô para outro servidor**: os gratuitos com agendamento pedem cartão de crédito ou rodam só uma vez por dia.

## Decisão

- O banco no Supabase, que já existe e é gratuito, tem relógio próprio (`pg_cron`) e faz chamadas web (`pg_net`).
  A cada 15 minutos (minutos 2, 17, 32 e 47), ele pede ao GitHub para rodar o robô (`workflow_dispatch` no `main`).
- A chave usada nessa chamada é um token do GitHub que só pode mexer em Actions deste repositório.
  - O dono cola o token direto no cofre do Supabase (Vault), que é criptografado, com o nome `stratum_disparo`.
  - O robô nunca vê, copia nem grava o token. Uma versão anterior desta decisão fazia o robô copiar o token dos
    Secrets do GitHub para o cofre; a trava de segurança da sessão barrou, e a cópia não é necessária.
  - O comando agendado lê o token do cofre na hora da chamada, então o token não fica no texto do agendamento,
    no código nem no log.
  - Esta é a única exceção à regra 12 ("segredos só nos Secrets do GitHub"). O cofre do banco que já guarda os
    dados é o lugar mais restrito disponível fora do GitHub.
- O robô configura o resto sozinho a cada rodada no `main`: liga as extensões e cria ou atualiza o agendamento.
  - Só agenda se o token já estiver no cofre.
  - Renomear o repositório não exige mexer no Supabase.
  - A validade do token vem da própria resposta do GitHub a cada chamada (cabeçalho com a data de vencimento).
- O agendamento do GitHub continua como reserva. Se o Supabase falhar, o robô ainda roda de vez em quando.
  Uma rodada por vez: o GitHub enfileira as chamadas que chegam durante uma rodada.
- O robô publica o estado do agendador no status.json e na tela Método:
  - quando foi a última chamada e o que o GitHub respondeu;
  - quando o token vence.
- Problemas do agendador (falha, token recusado, token a 14 dias de vencer) entram no resumo do Telegram
  (decisão 0005); não há mensagem fora dos horários do resumo.

## Consequências

- O site passa a ter dados de no máximo uns 20 minutos, enquanto o Supabase estiver de pé.
- O token vence em até um ano. O dono gera outro e o troca no cofre do Supabase; o aviso chega antes.
- Se o Supabase pausar o projeto gratuito por falta de uso, o agendador para junto. Com o robô gravando a cada
  15 minutos, isso não deve acontecer. Se acontecer, o aviso de dados parados aparece no site.
- Custo zero: o Actions é gratuito em repositório público, e `pg_cron` e `pg_net` fazem parte do plano gratuito
  do Supabase.
