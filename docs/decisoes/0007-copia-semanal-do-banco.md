# 0007. Cópia semanal do banco

Data: 2026-10-19

## Contexto

O banco fica no Supabase gratuito, que não faz cópia de segurança. Pela regra 2, nada é apagado: o banco é o
arquivo inteiro do projeto. Se o projeto do Supabase se perder, perde-se tudo, inclusive o histórico que a fase 5
precisa para o teste retroativo. A análise dos PDFs do sistema antigo pôs a cópia antes do resto da fase 1
(decisão 0006).

## Decisão

- **Uma vez por semana**, no domingo às 6:41 de Brasília, o workflow `copia.yml` roda `python -m stratum.copia`:
  - copia cada tabela do projeto para um arquivo comprimido, com uma linha por registro;
  - grava um manifesto com o número de linhas, a versão do esquema e o tamanho do banco e de cada tabela;
  - restaura a cópia num banco vazio, copia de novo e compara linha por linha. Se não voltar idêntica, o workflow
    falha.
- **Só as tabelas do projeto** (`db.md`). O cofre do Supabase (onde está o token do agendador), o pg_cron e o pg_net
  ficam de fora.
- **Onde fica**: como artefato do próprio GitHub, por 90 dias (o máximo num repositório público). Como o banco só
  recebe inserções, a cópia mais nova sempre tem tudo; as anteriores são reserva.
- **É pública, como o repositório.** Hoje as tabelas guardam manchetes públicas, o registro das coletas e o texto dos
  resumos já enviados, sem dado pessoal ou de conexão. Tabela nova com dado pessoal (por exemplo, a nota do dono da
  fase 5) precisa de decisão própria antes de entrar na cópia.
- **Só a `main`** roda a cópia, porque só ela conhece a senha do banco (regra 13).
- **Quem confere**: a cada rodada na `main`, o workflow do robô lê a data da cópia mais recente no GitHub. A tela
  Método mostra a data. Se a cópia tiver mais de 8 dias, ou se nunca houve uma, isso entra no resumo do Telegram
  (decisão 0005). O robô também mantém o agendamento da cópia ligado, como já faz com o dele (o GitHub desliga
  agendamentos depois de 60 dias sem atividade no repositório).
- **Restaurar** roda no próprio GitHub, para a senha nunca sair dos Secrets: o mesmo workflow, rodado à mão com o
  número da rodada da cópia (passo a passo em `docs/configurar.md`, item 8). Ele desliga o robô, restaura e religa.
  - Só aceita banco vazio; nunca sobrescreve nada. Por isso o robô é desligado antes de trocar o banco.
  - O banco novo sobe só até a versão do esquema da cópia, recebe os registros e depois sobe até a versão do código.
    Assim, uma cópia de antes de uma migração continua restaurável.
  - Cópia de uma versão do esquema que o código não conhece é recusada, assim como coluna desconhecida ou arquivo
    com menos linhas que o manifesto: nada se perde em silêncio, e nada fica pela metade.

## Consequências

- O manifesto de cada semana mede o tamanho do banco e de cada tabela; comparando as semanas, sai o crescimento.
  São os números que a decisão de retenção da fase 1 precisa.
- Se o GitHub sumir junto com o Supabase, a cópia some também. O risco foi aceito: os dois são de empresas
  diferentes, e o dono pode baixar uma cópia quando quiser (Actions → Cópia do banco → copia-banco).
- Custo zero: o Actions é gratuito em repositório público, e a cópia comprimida é pequena perto do limite de
  armazenamento de artefatos.
