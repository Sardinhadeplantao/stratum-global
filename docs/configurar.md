# Configurar (passo a passo, sem programar)

Faça na ordem. Cada passo leva poucos minutos. Senhas e chaves vão **só** nos Secrets do GitHub (a única exceção é
a chave do passo 6, que vai no cofre do Supabase): nunca cole em conversa (nem com o Claude), em arquivo ou em print.

## 1. Ligar o site

1. No repositório, abra **Settings → Pages**.
2. Em **Build and deployment**, clique na caixa **Source** (mostra "Deploy from a branch") e escolha **GitHub Actions**.
   Salva sozinho; não há botão.

Pronto: em até 15 minutos o robô publica o site em `https://sardinhadeplantao.github.io/<nome-do-repositório>/`.

## 1b. Renomear o repositório para Stratum Global

1. No repositório, abra **Settings → General**.
2. Em **Repository name**, troque `apex-trading-streamlit` por `stratum-global` e clique em **Rename**.

O site passa para https://sardinhadeplantao.github.io/stratum-global/ na rodada seguinte. Nada no código precisa mudar.
Nas próximas sessões do Claude, escolha o repositório `stratum-global`.

## 2. Criar o banco (Supabase, gratuito)

1. Entre em https://supabase.com e crie uma conta (dá para usar a do GitHub).
2. **New project**: nome `stratum-global`; crie uma senha forte para o banco e guarde num gerenciador de senhas;
   região: uma do leste dos EUA (fica perto de onde o robô roda); plano **Free**.
3. Se precisar trocar a senha: **Project Settings → Database → Reset database password**.
   Prefira uma senha só com letras e números.

O robô já sabe o servidor e o usuário deste projeto (estão em `.github/workflows/robo.yml`, porque não são segredo).
Só a senha vai para o GitHub, no passo 4. Se um dia o projeto do Supabase mudar, peça ao Claude para atualizar
`SUPABASE_HOST` e `SUPABASE_USUARIO` no workflow (em **Connect → Direct → Session pooler**, eles aparecem como host e user).

## 3. Criar o bot do Telegram

1. No Telegram, abra **@BotFather**, envie `/newbot`, escolha um nome e um usuário terminado em `bot`.
   Ele responde com um **token** (uma sequência longa de letras e números).
2. Abra o seu bot novo e mande "oi". Bots só podem escrever para quem falou com eles antes.
3. Abra **@userinfobot** e envie `/start`. Ele responde com o seu **Id** (um número).

## 4. Guardar as chaves no GitHub

No repositório: **Settings → Secrets and variables → Actions → New repository secret**. Crie três:

| Nome | Valor |
|---|---|
| `SUPABASE_SENHA` | só a senha do banco (passo 2) |
| `TELEGRAM_BOT_TOKEN` | o token do passo 3.1 |
| `TELEGRAM_CHAT_ID` | o número do passo 3.3 |

## 5. Testar o Telegram

1. No repositório: **Actions → Robô (coleta e site) → Run workflow**.
2. Marque **Mandar uma mensagem de teste no Telegram** e clique em **Run workflow**.
3. Em uns 5 minutos:
   - chega no Telegram: "Stratum Global: o robô está conectado ao seu Telegram.";
   - a tela **Método** do site mostra "Banco: Permanente" e as fontes que funcionaram.

Se algo não funcionar, a tela Método diz o que falhou. Numa sessão do Claude, peça:
"veja a última execução do robô do Stratum Global e me diga o que falhou".

## 6. Ligar o agendador (o robô roda a cada 15 minutos e o resumo sai na hora)

O agendamento do GitHub atrasa horas. Com este passo, o Supabase dispara o robô a cada 15 minutos (decisão 0004).
O código do robô nunca lê esta chave: você a cola direto no cofre do Supabase, e o próprio Supabase a usa.
Quem tem a senha do banco consegue ler a chave no cofre. Se um dia a senha do banco vazar, troque a senha e
revogue também esta chave (GitHub → Settings → Developer settings → Fine-grained tokens → **Revoke**).

**Criar a chave no GitHub:**

1. Clique na sua foto (canto superior direito) → **Settings**.
2. No fim do menu da esquerda, abra **Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
3. Preencha:
   - **Token name:** `stratum-agendador`
   - **Expiration:** escolha **Custom** e uma data daqui a 1 ano. Não escolha *No expiration*.
     O resumo do Telegram avisa 14 dias antes de vencer.
   - **Repository access:** **Only select repositories** → `stratum-global`.
   - **Permissions → Repository permissions → Actions:** **Read and write**. Só essa.
4. Clique em **Generate token** e copie o código, que começa com `github_pat_`.

**Guardar no cofre do Supabase:**

1. No painel do projeto, use a busca do topo (**Search… Ctrl K**) e digite **Vault**. Abra a página do cofre;
   se ela pedir para ativar, ative.
2. Clique para adicionar um segredo novo (**Add new secret**):
   - **Name:** `stratum_disparo`, exatamente assim;
   - **Secret:** o código copiado;
   - **Description:** opcional.
3. Salve. Na rodada seguinte, o robô liga o agendamento sozinho, e a tela **Método** passa a mostrar "Agendador: funcionando".

Para trocar a chave quando ela vencer, gere outra e edite o segredo `stratum_disparo` no cofre.

## 7. Resumos no Telegram

O Telegram recebe só três mensagens por dia, às 7:30, ao meio-dia e às 19:00 (Brasília), com o que aconteceu
desde o resumo anterior. Problemas do robô aparecem no resumo seguinte, nunca em mensagens fora desses horários.
