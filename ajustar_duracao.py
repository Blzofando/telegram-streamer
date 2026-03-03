import os
import json
import re
import glob

def find_durations_files():
    # Encontra todos arquivos que começam com "duracoes_" e terminam com ".json"
    files = glob.glob("duracoes_*.json")
    return files

def main():
    print("=" * 50)
    print("🛠️ AJUSTAR DURAÇÕES (Para Formato: prefixo-FXXX: segundos)")
    print("=" * 50)

    # 1. Carregar o mapeamento para cruzar os dados
    if not os.path.exists('mapeamento_aulas.json'):
        print("❌ 'mapeamento_aulas.json' não encontrado na pasta atual.")
        return

    with open('mapeamento_aulas.json', 'r', encoding='utf-8') as f:
        mapeamento = json.load(f)

    # Criar um índice do mapeamento pelo message_id
    # Ex: mapping_by_msg_id[20] = "pbi-F001"
    mapping_by_msg_id = {}
    for key, val in mapeamento.items():
        if "message_id" in val:
            mapping_by_msg_id[str(val["message_id"])] = key

    # 2. Listar arquivos
    arquivos = find_durations_files()
    if not arquivos:
        print("❌ Nenhum arquivo 'duracoes_*.json' encontrado.")
        return

    print("\nArquivos encontrados:")
    for i, file in enumerate(arquivos):
        print(f"[{i + 1}] {file}")

    print("[0] Sair")

    # 3. Pedir escolha do usuário
    opcao = input("\nEscolha o número do arquivo para ajustar: ").strip()
    
    if opcao == '0':
        return
        
    try:
        idx = int(opcao) - 1
        if idx < 0 or idx >= len(arquivos):
            print("❌ Opção inválida.")
            return
        arquivo_escolhido = arquivos[idx]
    except ValueError:
        print("❌ Digite um número válido.")
        return

    # 4. Ler o arquivo selecionado
    with open(arquivo_escolhido, 'r', encoding='utf-8') as f:
        duracoes_originais = json.load(f)

    # 5. Criar novo dicionário
    novo_dict = {}
    nao_encontrados = 0

    for msg_id_str, data in duracoes_originais.items():
        # A nova modelagem busca cruzar o message_id do json de duracao com o mapeamento
        # Caso exista no mapeamento, ele usa o código ex: pbi-F001
        
        # O caption no json de duracao contém o código, ex: #F001
        # E o arquivo extrair_duracoes salvou com a chave sendo o message_id do telegram
        
        if msg_id_str in mapping_by_msg_id:
            codigo = mapping_by_msg_id[msg_id_str]
        else:
            # Fallback buscando pelo caption caso o message_id do canal das durações
            # não seja o exato message_id do mapeamento
            caption = data.get("caption", "")
            match = re.search(r'#F(\d+)', caption)
            if match:
                num = match.group(1)
                # Tentar achar a chave no mapeamento que termine com F + num
                codigo = None
                for key in mapeamento.keys():
                    if key.endswith(f"-F{num}") or key.endswith(f"F{num}"):
                        codigo = key
                        break
                if not codigo:
                    # Se mesmo assim não achou, cria uma baseada no nome do aqruivo
                    # Ex: duracoes_css.json -> css-F001
                    prefixo = arquivo_escolhido.replace("duracoes_", "").replace(".json", "")
                    codigo = f"{prefixo}-F{num}"
            else:
                nao_encontrados += 1
                continue

        # Transforma os segundos guardando apenas como int
        segundos = int(float(data.get("duracao_segundos", 0)))
        novo_dict[codigo] = segundos

    # 6. Salvar no mesmo arquivo (ou num novo pra evitar perder os dados por acidente)
    novo_arquivo = arquivo_escolhido.replace(".json", "_ajustado.json")
    
    with open(novo_arquivo, 'w', encoding='utf-8') as f:
        json.dump(novo_dict, f, ensure_ascii=False, indent=2)

    print("-" * 50)
    print(f"✅ Ajuste concluído!")
    print(f"Processados: {len(novo_dict)}")
    if nao_encontrados > 0:
        print(f"⚠️ Não foi possível identificar o código para {nao_encontrados} vídeos.")
    print(f"💾 Salvo em: {novo_arquivo}")
    print("Se o arquivo estiver correto, você pode apagar o original e renomear este.")
    print("-" * 50)

if __name__ == "__main__":
    main()
