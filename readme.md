📹 Telegram Video Streamer API

Este é o backend responsável por fazer o streaming de vídeos diretamente de canais do Telegram para o seu site de cursos. Ele mapeia as aulas (ex: #F001) e cria um link de vídeo transmitido em tempo real, suportando múltiplos canais/cursos.

🚀 Instalação Inicial (Primeiro Acesso)

Se acabou de baixar o projeto ou formatou o computador, siga estes passos para configurar o ambiente.

1. Configurar o Ambiente Python

Abra o terminal na pasta do projeto e execute:

# 1. Crie o ambiente virtual
python -m venv venv

# 2. Ative o ambiente (Windows)
.\venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt
pip install python-dotenv


2. Configurar Credenciais (.env)

Crie um arquivo chamado .env na raiz do projeto (onde está o main.py) e adicione as suas chaves do Telegram (obtenha em my.telegram.org):

API_ID=seu_numero_api_id
API_HASH=sua_hash_aqui


3. Gerar Sessão do Telegram

Para permitir que o sistema baixe os vídeos, precisa gerar uma sessão de login.

Rode o script:

python gerar_string.py


Siga as instruções no terminal (telefone e código de verificação).

Copie o código gigante que será gerado.

Adicione esse código ao seu arquivo .env:

TELEGRAM_SESSION_STRING=cole_o_codigo_gigante_aqui


4. Testar Localmente

Para iniciar o servidor no seu computador:

uvicorn main:app --reload


O servidor ficará disponível em: http://127.0.0.1:8000

➕ Como Adicionar Novos Cursos/Canais

Sempre que quiser adicionar um novo curso (ex: JavaScript, Excel), siga este fluxo:

Passo 1: Descobrir o ID do Canal

Certifique-se de que a sua conta do Telegram entrou no canal desejado.

Rode o script de listagem:

python listar_canais.py


Copie o ID numérico do canal (ex: -100123456789).

Passo 2: Configurar o Mapeamento

Abra o arquivo gerar_mapeamento.py e edite o dicionário CANAIS_CURSOS:

CANAIS_CURSOS = {
    "pbi": -1001573455897,      # Power BI
    "html": -1002417234174,     # HTML e CSS
    "js": -1009999999999,       # <--- Novo curso adicionado
}


O nome que colocar na chave (ex: "js") será o prefixo da URL (ex: js-F01).

Passo 3: Atualizar o JSON

Execute o script para varrer os canais e salvar os links dos vídeos:

python gerar_mapeamento.py


Aguarde a mensagem de sucesso. Isso atualizará o arquivo mapeamento_aulas.json.

Passo 4: Atualizar no Servidor (Deploy)

Se o site já estiver online, envie as alterações:

fly deploy


☁️ Deploy no Fly.io

Comandos Principais

Login: fly auth login

Subir atualização: fly deploy

Ver logs: fly logs

Ver status: fly status

Configuração de Segredos (Primeiro Deploy)

O servidor online não lê o arquivo .env. Deve enviar as senhas para o cofre do Fly.io via terminal:

fly secrets set API_ID=seu_id API_HASH=sua_hash TELEGRAM_SESSION_STRING=sua_string_da_sessao


⚠️ Segurança e Git

NUNCA faça commit do arquivo .env ou dos arquivos *.session.

O arquivo .gitignore já está configurado para ignorá-los.

Se clonar este repositório noutra máquina, precisará recriar o .env localmente.