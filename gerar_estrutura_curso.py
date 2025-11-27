import asyncio
import os
import re
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterVideo

# Carrega variáveis de ambiente
load_dotenv()

# Configurações iniciais
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_NAME = 'streamer_session'

def limpar_texto(texto):
    """Remove caracteres estranhos e espaços extras"""
    return texto.strip().replace('"', "'")

async def main():
    print(f"{'='*60}")
    print("🚀 GERADOR DE ESTRUTURA DE CURSO (.TS)")
    print(f"{'='*60}")

    # --- PERGUNTAS AO USUÁRIO ---
    channel_id_input = input("1. Digite o ID do Canal (ex: -100123456): ").strip()
    prefixo = input("2. Digite o Prefixo para os IDs (ex: lic, html): ").strip().lower()
    var_name = input("3. Nome da variável no código (ex: htmlCssCourse): ").strip()
    titulo_curso = input("4. Título do Curso (ex: Curso de Excel): ").strip()
    
    try:
        channel_id = int(channel_id_input)
    except ValueError:
        print("❌ ID do canal inválido! Deve ser um número.")
        return

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()

    print(f"\n🔍 Conectando ao canal {channel_id}...")
    
    try:
        entity = await client.get_entity(channel_id)
    except Exception as e:
        print(f"❌ Erro ao encontrar canal: {e}")
        await client.disconnect()
        return

    # Estrutura para armazenar: { "Nome do Módulo": [ {id, titulo} ] }
    modulos_dict = {}
    total_videos = 0

    print("📥 Lendo mensagens e organizando aulas...")

    # Itera sobre as mensagens (vídeos)
    async for msg in client.iter_messages(entity, limit=2000, filter=InputMessagesFilterVideo):
        if msg.message:
            # Procura pelo padrão #Fxxx
            match = re.search(r'#F(\d+)', msg.message)
            
            if match:
                numero_aula = match.group(1) # Ex: 001 ou 01
                
                # Formata o ID da aula: prefixo-Fnúmero (ex: lic-F001)
                # Removemos zeros à esquerda se quiser ficar igual ao seu exemplo (F01) ou mantemos (F001)
                # O código abaixo mantém o número original achado na hashtag
                id_aula = f"{prefixo}-F{numero_aula}"
                
                # Separa Título e Módulo
                # Geralmente o formato é: #F001 Título da Aula\n\nNome do Módulo
                linhas = msg.message.strip().split('\n')
                
                # A primeira linha costuma ser o título (removendo a hashtag)
                titulo_bruto = linhas[0]
                titulo_aula = re.sub(r'#F\d+\s*', '', titulo_bruto).strip()
                
                # Tenta achar o módulo (geralmente está na última linha ou após quebra dupla)
                nome_modulo = "Módulo Geral"
                if len(linhas) > 1:
                    # Pega a última linha não vazia como nome do módulo
                    for linha in reversed(linhas):
                        if linha.strip():
                            nome_modulo = linha.strip()
                            break
                
                # Adiciona ao dicionário
                if nome_modulo not in modulos_dict:
                    modulos_dict[nome_modulo] = []
                
                modulos_dict[nome_modulo].append({
                    "id": id_aula,
                    "title": limpar_texto(titulo_aula),
                    "raw_num": int(numero_aula) # Para ordenar depois
                })
                
                total_videos += 1
                print(f"   ✅ Capturado: {id_aula}")

    await client.disconnect()

    if total_videos == 0:
        print("\n⚠️ Nenhum vídeo com código #F encontrado!")
        return

    # --- GERAÇÃO DO ARQUIVO .TS ---
    print(f"\n📝 Gerando código TypeScript...")

    # Ordenar módulos (alfabeticamente ou você pode numerar no telegram tipo "01-Modulo")
    nomes_modulos_ordenados = sorted(modulos_dict.keys())
    
    # Monta a string dos Modules
    modules_str = ""
    category_module_ids = [] # Para colocar na categoria "Todos"

    for i, nome_modulo in enumerate(nomes_modulos_ordenados):
        aulas = modulos_dict[nome_modulo]
        # Ordena as aulas pelo número #F
        aulas.sort(key=lambda x: x['raw_num'])
        
        # ID do módulo: prefixo-Module-Contador
        mod_id = f"{prefixo}-Module-{i+1}"
        category_module_ids.append(f'"{mod_id}"')
        
        modules_str += "        {\n"
        modules_str += f'            id: "{mod_id}",\n'
        modules_str += f'            title: "{nome_modulo}",\n'
        modules_str += "            lessons: [\n"
        
        for aula in aulas:
            modules_str += f'                {{ id: "{aula["id"]}", title: "{aula["title"]}" }},\n'
        
        # Remove a última vírgula e fecha array
        modules_str = modules_str.rstrip(",\n") + "\n"
        modules_str += "            ],\n"
        modules_str += "        },\n"

    # Monta o arquivo final
    ts_content = f"""import {{ Course }} from '../../types';

export const {var_name}: Course = {{
    id: "{prefixo}-course",
    slug: "{prefixo}",
    title: "{titulo_curso}",
    description: "Descrição automática gerada pelo script.",
    thumbnail: "/images/{prefixo}-thumb.jpg",
    categories: [
        {{ 
            name: "Todos os Módulos", 
            moduleIds: [{', '.join(category_module_ids)}] 
        }}
    ],
    modules: [
{modules_str.rstrip(",\n")}
    ],
}};
"""

    # Salva no arquivo
    nome_arquivo = f"course_{prefixo}.ts"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(ts_content)

    print(f"\n{'='*60}")
    print(f"🎉 Arquivo gerado com sucesso: {nome_arquivo}")
    print(f"📂 Copie o conteúdo deste arquivo para o seu projeto frontend.")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())