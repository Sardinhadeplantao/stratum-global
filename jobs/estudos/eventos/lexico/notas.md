# Agrupamento em eventos: abordagem léxica (fase 1, segunda tentativa)

Tudo aqui foi medido só no conjunto `dev_19out` (236 manchetes, 108 pares, 33 eventos com 2 ou mais manchetes).
O conjunto de teste não foi aberto.

## Resultado em uma frase

A melhor configuração léxica junta pouco e quase sempre certo: no dev, precisão de 0,96 a 0,97 e cobertura de
0,22 a 0,29, com 10 dos 33 eventos com par juntado. **A meta da fase 1 não é alcançável só com palavras**:
a cobertura fica em menos da metade dos 0,60 pedidos, e os eventos com par juntado ficam em 10 (a meta pede 17).
Serve como primeira camada de alta precisão (quase-duplicatas e o mesmo fato contado com as mesmas palavras),
não como solução sozinha.

| Ordem de chegada | Precisão | Cobertura | B-cubed F | Pares juntados / certos | Eventos com par |
|---|---|---|---|---|---|
| ids crescentes | 0,966 | 0,259 | 0,892 | 29 / 28 | 10 de 33 |
| ids decrescentes | 0,969 | 0,287 | 0,896 | 32 / 31 | 10 de 33 |
| embaralhada (semente 1) | 0,960 | 0,222 | 0,889 | 25 / 24 | 10 de 33 |
| **pior / média** | **0,960 / 0,965** | **0,222 / 0,256** | 0,889 / 0,892 | | |

Linha de base "não juntar nada": B-cubed F 0,857.

Cobertura por tipo de par (o gabarito tem 27 pares da mesma fonte, 81 de fontes diferentes e 14 entre idiomas):
mesma fonte 0,07 a 0,15; fontes diferentes 0,27 a 0,36; **entre idiomas 0** (nenhum par Folha x inglês).

Robustez: em 30 ordens aleatórias extras (sementes 2 a 31), a precisão mínima foi 0,944 (mediana 0,963)
e a cobertura entre 0,157 e 0,343 (mediana 0,241). A cobertura depende muito da ordem de chegada (veja "Por que
não chega lá").

## Como funciona (configuração escolhida)

Arquivo `agrupar.py`, `CONFIG` com todos os parâmetros. Só biblioteca padrão do Python.

1. **Palavras do título.** Minúsculas, sem acento, sem palavras vazias em inglês e português, sem verbos de fala
   ("says", "diz", "told"), sem dias, meses e palavras de formato ("live", "watch", "video"). Números escritos
   viram algarismos ("four" vira "4"; "2.400" e "2,400" viram "2400").
2. **Radical simples: as 5 primeiras letras** de cada palavra. "protests" e "protestos" viram "prote"; "França"
   e "France" viram "franc"; "Zelensky" e "Zelenskyy" viram "zelen". Uma regra só para as duas línguas.
3. **Países** que a regra de países já marcou entram como termos ("@FRA"), com peso 0,5.
4. **Peso de cada palavra pelo IDF da janela**: palavra que aparece em muitas manchetes do dia (França, Rubio,
   protestos) pesa pouco; palavra rara (endossa, incêndio, petroleiro) pesa muito. Fórmula `ln((N+1)/(df+1)) + 1`,
   com df contado no texto inteiro (título + resumo + países) de cada manchete da janela.
5. **Online, com centro do grupo.** As manchetes chegam uma a uma. Cada grupo guarda a soma dos vetores dos seus
   membros (o "centro"). A manchete nova vai para o grupo de centro mais parecido (cosseno), se passar:
   - **0,46** para formar par com uma manchete que está sozinha;
   - **0,38** para entrar num grupo que já tem 2 ou mais.
6. **Trava de países**: se a manchete nova e algum membro do grupo têm países marcados e nenhum em comum,
   não entra.
7. Se nenhum grupo passa, abre grupo novo. Nada é movido depois e grupos não se fundem (regra 2).

O resumo do RSS **não** entra no vetor (só ajuda a contar a raridade das palavras).

## Por que estes parâmetros

| Parâmetro | Valor | Motivo (medido no dev, pior ordem, melhor ponto com precisão >= 0,93) |
|---|---|---|
| corte | 5 letras | 4 letras: cobertura 0,213; 6 letras: 0,231; palavra inteira: 0,139; snowball: 0,185. O corte em 5 casa plural, verbo e cognatos pt/en sem biblioteca. |
| peso_resumo | 0 | Com o resumo, a precisão cai: peso 0,15 dá 0,231 de cobertura no melhor ponto; peso 0,3, só 0,185. O trecho do RSS costuma contar o evento vizinho ("a polícia perdeu o controle" no resumo da renúncia recusada). |
| peso_pais | 0,5 | Sem países: 0,25 (com limiares piores para a precisão: 0,917 nos limiares finais); peso 1,0: 0,269 mas com precisão 0,935 (sem folga). 0,5 fica no meio, com 0,96. |
| idf | janela | O IDF de um corpus fixo (wordfreq) nunca chegou a precisão 0,90: ele dá peso alto a "Macron", "Rubio", "França", que são o assunto do dia, não o evento. |
| limiar_par | 0,46 | Abaixo de 0,46 entram os "eventos irmãos" (Papa, ministro iraniano, sanções, colonos): em 0,44 a precisão mínima cai para 0,81 nas 30 ordens extras. |
| limiar_grupo | 0,38 | 0,36 dá 0,259 nas 3 ordens oficiais, mas cai a 0,885 de precisão em algumas das 30 ordens extras; 0,38 fica com mínimo de 0,944 e a mesma mediana de cobertura (0,241). Sem limiar separado (um limiar só, 0,46), a cobertura cai para 0,194. |
| trava_pais | sim | Sem a trava, a precisão nos limiares finais cai para 0,875. |

Por que dois limiares: juntar duas manchetes soltas cria um evento novo com só duas testemunhas, então pede prova
mais forte; entrar num grupo de 2 ou mais compara com o centro, que já resume o que as manchetes têm em comum.

## O que tentei e o resultado de cada variante

Melhor ponto da grade de limiares com precisão (pior das 3 ordens) >= 0,93; cobertura "pior / média".
Linhas marcadas com (F) usam o pipeline final e mudam só o item da linha. Linhas marcadas com (L) foram medidas no
laboratório numa etapa anterior (ligação "máximo" ou "centro" com um limiar só, às vezes com o resumo); servem para
comparar a ideia, não para comparar casas decimais com a escolhida.

| Variante | Cobertura no melhor ponto | Observação |
|---|---|---|
| (L) Primeira tentativa (interrompida; em `tentativa1/`): título + resumo 0,25, ligação pela média | 0,130 / 0,136 | Conferida e substituída. |
| (L) Só ranquear pares (sem grupos), melhor representação | no máximo 0,17 a 0,19 dos pares | Teto de qualquer regra que olhe um par de cada vez. |
| (F) **Ligação "centro" com dois limiares (escolhida)** | **0,222 / 0,256** | Com 0,46 / 0,36 chega a 0,259 / 0,272, mas é frágil (veja robustez). |
| (F) Ligação "máximo" (membro mais parecido) | 0,213 / 0,241 | |
| (F) Ligação "média" dos membros | 0,213 / 0,225 | |
| (F) Ligação "líder" (só o primeiro do grupo) | 0,194 / 0,213 | |
| (F) Um limiar só (centro) | 0,194 / 0,207 | |
| (F) + trava "nome próprio em comum" (maiúscula no meio da frase e nunca minúscula na janela) | 0,213 / 0,247 | Perde 1 par e não evita nenhum erro neste ponto; ficou de fora. |
| (F) + trava "entre idiomas, 2 nomes ou números em comum" | 0,222 / 0,256 | Não muda nada neste ponto; ficou de fora. |
| (F) + trava "palavra minúscula do título em comum" (verbo ou substantivo do fato) | 0,213 / 0,247 | Evita o erro do ministro iraniano mais abaixo, mas perde pares bons. |
| (L) Regra "na dúvida entre dois grupos parecidos, não junta" (margem 0,02 a 0,1) | igual ou pior | |
| (F) Resumo com peso 0,15 / 0,3 | 0,231 / 0,185 | Nos limiares finais, a precisão cai para 0,85 / 0,76. |
| (L) Só os nomes do resumo, peso 0,3 / 0,6 | 0,185 / 0,130 | |
| (F) Sem países como termo / países com peso 1,0 | 0,250 / 0,269 | Mas nos limiares finais a precisão cai para 0,917 / 0,776: sem folga. |
| (F) Corte em 4 / 6 letras / palavra inteira | 0,213 / 0,231 / 0,139 | |
| (L) Radical do snowball (inglês e português) | 0,185 / 0,204 | Pior que o corte em 5 e é uma dependência a mais. |
| (F) Sem trava de países | 0,222 / 0,238 (com limiar 0,52) | Nos limiares finais, precisão 0,875. |
| (L) IDF elevado a 1,5 / ao quadrado | 0,185 / nenhum ponto | Ganha um pouco só com precisão 0,90. |
| (F) IDF de corpus fixo (wordfreq, inglês e português) | nenhum ponto com precisão >= 0,90 | Precisão 0,30 nos limiares finais. |
| (F) IDF incremental (só o que já chegou; janela começa vazia) | 0,231 / 0,259, precisão 0,941 | Pior caso de produção; quase igual à janela inteira. |
| (L) Pares de palavras vizinhas (bigramas) no título, peso 0,5 / 1,0 | 0,194 / 0,028 | |
| (L) Contenção (quanto do título de um está no texto do outro) | 0,15 a 0,19 | |
| (L) Pedaços de 3, 4 e 5 letras ("shingles") com IDF | 0,185 / 0,148 / 0,139 | Piores que palavras cortadas. MinHash não foi preciso: com até 5.000 manchetes a conta exata é rápida e não aproxima nada. |

Os scripts do laboratório estão em `laboratorio/` (lab.py, lab2.py, lab3.py e os s_*.py). `variantes.py`,
`exp_idf.py`, `robustez.py` e `tempo.py` refazem as tabelas com o `agrupar.py` final.

## IDF em produção

- **Escolha: IDF da janela** (as manchetes dos últimos 2 dias que o robô já tem no banco, mais as novas da rodada),
  recalculado a cada rodada. É o que o `agrupar()` faz com as manchetes que recebe.
- No dev (um dia só), "janela" quer dizer o dia inteiro, inclusive manchetes que chegariam depois. Para medir o
  efeito disso, rodei também o **IDF incremental** (cada manchete só enxerga as que já chegaram, como no primeiro
  dia em produção, com a janela vazia): precisão pior 0,941 e cobertura 0,231 / 0,259, contra 0,960 e 0,222 / 0,256
  da janela inteira. Ou seja, o resultado quase não depende disso.
- **Corpus fixo de referência (wordfreq) não serve**: ele não sabe o que é assunto do dia. Precisão 0,30.

## Erros de junção

Na configuração escolhida há **um** só par errado, o mesmo nas 3 ordens:

1. `[46 cgtn_mundo] Montenegrin PM meets Chinese FM` x `[49 cgtn_mundo] Montenegrin president meets Chinese FM`
   (cosseno 0,91). Dois encontros diferentes do mesmo chanceler chinês; só "PM" x "president" muda.

Para mostrar os próximos erros, afrouxei os limiares para 0,40 / 0,32 (precisão cai para 0,76). Os 10 piores,
contados em quantas das 3 ordens aparecem:

| Ordens | Cos | Manchete A | Manchete B | Por que parece igual |
|---|---|---|---|---|
| 3/3 | 0,91 | Montenegrin PM meets Chinese FM | Montenegrin president meets Chinese FM | evento irmão |
| 3/3 | 0,45 | Pope greeted by crowds in first major appearance since lung cancer surgery | Vatican says Pope Leo to be released from the hospital on October 17, four days after lung cancer surgery | fundo comum ("lung cancer surgery") |
| 3/3 | 0,45 | Trump-Zelensky rift will not affect special military operation, expert says | A rift in the U.S.-Israel special relationship | duas palavras genéricas ("rift", "special") |
| 3/3 | 0,45 | Iran's new Defence Minister Akhlaghi threatens 'enormous damage' if U.S. attacks | Iran's Parliament approves Mehrdad Akhlaqi as Minister of Defence | mesma pessoa, atos diferentes |
| 3/3 | 0,43 | Trump says he can tighten sanctions on Russia 'any time' he wants | Zelenskyy says Trump could lift more Russia sanctions | "tighten" x "lift": o sentido muda, as palavras não |
| 2/3 | 0,45 | Israel Police arrest eight suspects over settler attacks on diplomats, U.S. photojournalist in West Bank | Masked settlers attack European diplomats in occupied West Bank | o ataque x a prisão pelo ataque |
| 2/3 | 0,41 | France's Macron declines minister's resignation after violent protests | Nada justifica violência em protestos, diz Macron após dia de caos na França | entre idiomas só casam nomes e cognatos |
| 2/3 | 0,18 | Nada justifica violência em protestos, diz Macron após dia de caos na França | French President Macron refuses Interior Minister Laurent Nunez's resignation after protests | arrastado pelo par acima |
| 1/3 | 0,37 | France's Macron declines minister's resignation after violent protests | France's National Rally leader calls for Macron's resignation amid riots | "Macron" + "resignation" |
| 1/3 | 0,35 | The kingmakers who could determine Israel's election | Trump endorses Netanyahu in Israeli election | "Israel" + "election" |

O padrão: **eventos irmãos** (mesmo assunto, mesmas pessoas, fato diferente) usam tantas palavras iguais quanto
duas manchetes do mesmo fato. Palavras não separam "aprova" de "ameaça", nem "aperta" de "alivia".

## Perdas (pares do gabarito que ficaram separados)

Na configuração escolhida, 72 dos 108 pares ficam separados nas 3 ordens. Onde estão:

| Evento | Pares perdidos | Exemplo de manchetes |
|---|---|---|
| A1.E1 (tumultos na França: presos, saques) | 21 de 21 | "Nearly 2,400 people detained during unrest in France", "France protests: Police arrest 1,800 after violent clashes and looting mar protests", "Watch: Shops looted and restaurants gutted in Paris riots", "França tem 1 morto, mais de mil policiais feridos e 2.400 presos após protestos" |
| A8.E4 (Rubio: pausa das sanções contra a Rússia) | 6 de 6 | "Trump removes sanctions on Russian diesel fuel for sake of US' profit — Rubio", "60-day pause on Russia sanctions to analyse global impact: Rubio", "Rubio diz que Trump vai avaliar decisão sobre sanções contra a Rússia" |
| A8.E1 (ataque russo a Kiev) | 6 de 6 | "Data center in Kiev completely destroyed by Russian strike", "Explosions sound in Ukrainian capital", "Russia pounds Kyiv as Rubio urges..." |
| A10.E1, A1.E5, A1.E6, A4.E1, A8.E5, A15.E1 | 3 cada | Lavrov no Irã; Macron recusa a renúncia; Macron condena a violência; deputada australiana atropelada; declarações de Rubio sobre a Ucrânia; indicações do governo russo |

As 10 perdas que mais perto chegaram de entrar (cosseno título x título, separadas nas 3 ordens):

| Cos | Manchete A | Manchete B |
|---|---|---|
| 0,46 | Australian MP seriously hurt in suspected car attack | Australian lawmaker 'critically' hurt in attack, officials say |
| 0,44 | France's Macron declines minister's resignation after violent protests | French President Macron refuses Interior Minister Laurent Nunez's resignation after protests |
| 0,42 | Personal attacks fire up debate before Brazil's run-off vote | Brazil's Lula, Bolsonaro clash in bitter debate ahead of election run-off |
| 0,42 | Five nominees: what is known about proposed reshuffles in Russian government | Russian PM submits five government nominations to State Duma for approval |
| 0,42 | Lavrov arrives in Iran to discuss regional de-escalation with Araghchi | Lavrov to outline Russia's de-escalation efforts during visit to Iran |
| 0,40 | Australian MP Helen Haines critically injured in 'deliberate' car ramming | Australian MP seriously hurt in suspected car attack |
| 0,40 | Tanker hits mine in southern part of Strait of Hormuz — IRGC | Oil tanker on fire after hitting mine in Hormuz: Iran's Guards |
| 0,38 | Deadly fire at Canada military base moved a kilometre 'in 30 to 60 seconds' | Major fire breaks out in Alberta after deadly incident at military base |
| 0,37 | Data center in Kiev completely destroyed by Russian strike, cannot be restored | Storage sites for cruise missiles, data center in Kiev hit in massive Russian attack |
| 0,37 | Watch: Shops looted and restaurants gutted in Paris riots | French shops demolished after weekend riots across the country |

Estes pares ficam entre 0,37 e 0,46, a mesma faixa dos erros da tabela anterior (0,35 a 0,45). Não há um limiar
que pegue uns sem pegar os outros.

## Por que não chega lá

1. **Eventos irmãos parecem iguais** (tabela de erros). Com 25 a 30 pares certos, cada par errado custa 3 a 4
   pontos de precisão; três ou quatro irmãos já levam a precisão para perto ou abaixo de 0,90.
2. **O mesmo fato com palavras diferentes**: "detained", "arrest", "presos", "looted", "demolished"; "Kiev" e
   "Kyiv"; "Explosions sound in Ukrainian capital" não tem nenhuma palavra em comum com o resto do evento. O maior
   evento do dev (21 pares, um quinto da cobertura) fica inteiro de fora, porque a França tem vários outros eventos
   do mesmo assunto com as mesmas palavras.
3. **Português x inglês**: só nomes, números e cognatos casam ("franc", "prote", "macro", "netan", "2400"). O par
   Folha x inglês com cosseno mais alto (0,41) é um erro (Macron condena a violência x Macron recusa a renúncia);
   os pares certos ficam entre 0,19 e 0,32. Resultado: 0 de 14 pares entre idiomas. A tradução prevista no plano
   (Argos/Opus-MT) é o caminho para isso.
4. **Online, sem refazer**: quando a primeira manchete de um evento chega e o par não passa no limiar, ela fica
   sozinha para sempre (não há fusão). Por isso a cobertura varia de 0,157 a 0,343 só mudando a ordem.

## Tempo e dependências

- Só biblioteca padrão do Python (nada a instalar). Os pacotes testados e descartados foram snowballstemmer 3.1.1
  (BSD-3, ~2 MB) e wordfreq 3.1.1 (código Apache-2.0, dados CC BY-SA 4.0, ~58 MB).
- Tempo (`tempo.py`, uma CPU): dev nas 3 ordens, 0,1 s; janela sintética de 2.000 manchetes (pior caso, quase
  todas sozinhas), 0,6 s; 5.000 manchetes, 3,5 s; 2.000 com IDF incremental, 2,1 s. Memória: menos de 50 MB.
  Cabe com folga nos 14 minutos do GitHub Actions.
- Determinístico: mesma entrada e mesma ordem dão o mesmo resultado (empate vai para o grupo mais antigo).

## Recomendação

Usar a regra léxica como **primeira camada**, para juntar o que é claramente o mesmo fato (precisão de pelo menos 0,94
em todas as 33 ordens medidas). A meta da fase 1 precisa de outra fonte de sinal por cima: tradução para o português
ou para o inglês antes de comparar (pares entre idiomas) e algo que entenda sentido (sinônimos e paráfrases:
"detained" = "arrest" = "presos"). Pelas regras 7 e 11, isso tem de ser gratuito e decidido por regra testada.
