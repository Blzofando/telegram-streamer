import json

filepath = 'd:/Applications/telegram-streamer/mapeamento_aulas.json'

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

count = 0
for key, value in data.items():
    titulo = value.get('titulo_completo', '')
    
    # Verifica se o título atual bate com o padrão que precisa ser ajustado
    if '\n=' in titulo or 'ext' in titulo.lower() or 'Indexado por' in titulo:
        linhas = titulo.split('\n')
        linhas = [l.strip() for l in linhas if l.strip()] # Remove linhas vazias
        
        if len(linhas) >= 3 and linhas[0].startswith('#') and linhas[-1].startswith('='):
            # Extrair o ID, ex: "#F001"
            codigo_id = linhas[0].split(' ')[0]
            
            # Extrair Módulo
            modulo = linhas[1]
            
            # Extrair Aula, removendo '=' e o final '- Indexado...'
            aula = linhas[-1].lstrip('=')
            idx = aula.find(' - Indexado por')
            if idx != -1:
                aula = aula[:idx]
            
            aula = aula.strip()
            
            # Formatar para o novo padrao
            novo_titulo = f"{codigo_id} {aula}\n\n{modulo}"
            
            if value['titulo_completo'] != novo_titulo:
                value['titulo_completo'] = novo_titulo
                count += 1

with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Registros atualizados: {count}")
