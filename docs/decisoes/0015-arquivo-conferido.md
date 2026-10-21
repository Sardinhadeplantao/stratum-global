# 0015. Arquivo conferido: o que é antigo sai do banco só depois de guardado e conferido

Data: 2026-10-21

## Contexto

O banco gratuito do Supabase tem 500 MB. Em 21/10 estava com 45,6 MB (cópia da semana): 31 MB de cotações (11 anos
de 61 séries, baixados uma vez), 2,5 MB de notícias com traduções e histórias e 0,45 MB do registro de leituras. No
ritmo medido de 20 para 21/10, crescem por ano cerca de 220 MB as notícias (com traduções e ligações às histórias),
120 MB o registro de leituras (uma linha por fonte a cada rodada de 15 minutos) e 45 MB as cotações. O plano gratuito
encheria em pouco mais de um ano.

O dono perguntou se não seria melhor ler das fontes públicas em vez de guardar. Vale para o que a fonte guarda
(cotações têm histórico na fonte), mas não para notícias: o feed mostra só as últimas dezenas, que somem em horas.
Sem guardar, não há contagem de vozes, histórias nem "o que aconteceu ontem".

A regra 2 dizia "nada é apagado". O dono escolheu, entre manter a regra (e pagar ou montar outro banco em 1,5 a 2 anos),
decidir depois, ou o arquivo conferido, o arquivo conferido (21/10).

## Decisão

1. **O que fica no banco**: as notícias dos últimos 12 meses (com as traduções e as ligações às histórias delas) e
   o registro de leituras dos últimos 30 dias. Cotações, contratos futuros, terremotos, rodadas, fontes, séries e
   resumos ficam para sempre (são pequenos ou são a base da régua).
2. **Para onde vai o resto**: um "release" do GitHub por arquivamento (`arquivo-AAAA-MM-DD-HHMM`), público como o
   repositório, permanente e gratuito (os artefatos do GitHub, usados pela cópia semanal, somem em 90 dias). Cada
   tabela vira um arquivo de uma linha JSON por registro, comprimido, com o manifesto (corte, linhas e a impressão
   digital SHA-256 de cada arquivo).
3. **Só sai depois de conferido** (`jobs/stratum/arquivo.py`, workflow `arquivo.yml`, uma vez por mês, só na main):
   separar o que passou do prazo; publicar no GitHub; baixar de volta do GitHub; conferir a impressão digital;
   restaurar num banco vazio e comparar cada linha com o banco; só então tirar, numa transação que se desfaz inteira
   se a contagem não bater. Qualquer diferença: nada sai, e o arquivo fica no GitHub para conferir.
4. **Notícia repetida continua sem entrar duas vezes** (regra 3): o banco guarda, para cada notícia arquivada, uma
   impressão curta (os primeiros 60 bits do hash, 8 bytes). O robô não grava notícia cuja impressão está lá.
5. **Os números continuam inteiros**: cada arquivamento fica registrado no banco (tabela `arquivo`: etiqueta, tabela,
   corte, linhas, impressão digital, e as notícias por fonte). As contagens de notícias do site somam o banco e o
   arquivo, e a tela Método diz até quando as notícias estão no arquivo, com o link.
6. **A regra 2 passa a ser**: nada é reescrito, e nada se perde. O robô só insere; correção vira registro novo. Só o
   arquivo conferido tira do banco, e só o que já está guardado e conferido no GitHub.
7. Notícia com uma ligação de história a outra que ainda fica no banco também fica (a ligação não pode apontar para
   o vazio). É raro: as histórias juntam notícias de poucos dias.

## Consequências

- Pela conta de 21/10, o banco gratuito dura uns 5 anos; o limite passa a ser o crescimento das cotações, que pode
  ganhar sua própria decisão depois (por exemplo, guardar só o fechamento de cada dia).
- O histórico completo = os releases de arquivo + a cópia semanal. `python -m stratum.arquivo --restaurar PASTA`
  devolve um arquivo a um banco (para pesquisa ou recuperação), sem repetir o que já está lá.
- O workflow do arquivo precisa poder criar releases (`contents: write`), só ele.
- O primeiro arquivamento com efeito será o do registro de leituras, a partir de meados de novembro de 2026; as
  notícias, a partir de outubro de 2027. Antes disso, o ensaio numa branch (banco temporário com dado real e prazo
  zero) confere o caminho inteiro.
