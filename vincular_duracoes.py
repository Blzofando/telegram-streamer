
import json
import os

def main():
    print("="*60)
    print("🔗 VINCULADOR DE DURAÇÕES (Mapeamento -> Duração)")
    print("="*60)

    # 1. Solicita nome do arquivo de durações
    arquivo_duracoes = input("\nDigite o nome do arquivo de durações (ex: duracoes_lic.json): ").strip()
    
    if not os.path.exists(arquivo_duracoes):
        print(f"❌ Arquivo '{arquivo_duracoes}' não encontrado!")
        return

    # 2. Solicita o prefixo
    prefixo = input("Digite o prefixo do curso (ex: lic, pbi): ").strip()

    # 3. Carrega os arquivos
    print(f"\n📂 Carregando '{arquivo_duracoes}'...")
    with open(arquivo_duracoes, 'r', encoding='utf-8') as f:
        dados_duracoes = json.load(f)

    print(f"📂 Carregando 'mapeamento_aulas.json'...")
    if not os.path.exists('mapeamento_aulas.json'):
        print("❌ 'mapeamento_aulas.json' não encontrado!")
        return
        
    with open('mapeamento_aulas.json', 'r', encoding='utf-8') as f:
        mapeamento = json.load(f)

    # 4. Processamento
    print("\n🔄 Cruzando dados...")
    
    resultado_final = {}
    encontrados = 0
    nao_encontrados = 0
    
    # Itera sobre o mapeamento procurando aulas com o prefixo
    for codigo_aula, info in mapeamento.items():
        # Verifica se começa com o prefixo (ex: "lic-F...")
        # Adicionamos "-" para garantir que é o prefixo correto (evita pegar "lic" em "licao")
        if codigo_aula.startswith(f"{prefixo}-"):
            
            message_id = info.get('message_id')
            
            if message_id is not None:
                # O JSON de durações tem chaves como STRING, mas message_id no mapeamento é INT
                chave_busca = str(message_id)
                
                if chave_busca in dados_duracoes:
                    # Pega a duração (suporta tanto o formato novo dict quanto direto int se fosse o caso)
                    item = dados_duracoes[chave_busca]
                    duracao = 0
                    
                    if isinstance(item, dict):
                        duracao = item.get('duracao_segundos', 0)
                    elif isinstance(item, (int, float)):
                        duracao = item
                        
                    if duracao > 0:
                        resultado_final[codigo_aula] = duracao
                        encontrados += 1
                        # print(f"   ✅ {codigo_aula} -> {duracao}s")
                    else:
                        print(f"   ⚠️ {codigo_aula}: Duração zerada no arquivo de entrada.")
                else:
                    nao_encontrados += 1
                    # print(f"   ❌ {codigo_aula} (Msg ID {message_id}): Não encontrado no arquivo de durações.")
            else:
                print(f"   ⚠️ {codigo_aula}: Sem message_id no mapeamento.")

    # 5. Salvar Resultado
    print("-" * 60)
    print("RESUMO DO PROCESSAMENTO:")
    print(f"Aulas do prefixo '{prefixo}' encontradas no mapeamento: {encontrados + nao_encontrados}")
    print(f"✅ Durações vinculadas com sucesso: {encontrados}")
    print(f"❌ Aulas sem duração correspondente: {nao_encontrados}")

    if resultado_final:
        nome_saida = f"duracoes_finais_{prefixo}.json"
        
        # Ordena pelo código da aula (decrescente ou crescente, o user pediu exemplo decrescente mas json não garante ordem, vamos ordenar por chave)
        # O exemplo do user parecia decrescente (F434, F433...), vamos tentar respeitar isso
        resultado_ordenado = dict(sorted(resultado_final.items(), key=lambda item: item[0], reverse=True))
        
        with open(nome_saida, 'w', encoding='utf-8') as f:
            json.dump(resultado_ordenado, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 Arquivo final gerado: {nome_saida}")
    else:
        print("\n⚠️ Nenhum vínculo criado. Verifique se o prefixo e os IDs batem.")

if __name__ == "__main__":
    main()
