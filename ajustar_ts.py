import json
import re

filepath = 'd:/Applications/telegram-streamer/mapeamento_aulas.json'

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Module grouping
modules = {}
module_order = []

for key, value in data.items():
    if not key.startswith('css-'):
        continue
    
    titulo_completo = value.get('titulo_completo', '')
    if '\n\n' in titulo_completo:
        parts = titulo_completo.split('\n\n')
        aula_part = parts[0].strip()
        modulo_part = parts[1].strip()
        
        # aula_part is like "#F001 1. Como assistir as aulas"
        first_space = aula_part.find(' ')
        if first_space != -1 and aula_part.startswith('#'):
            aula_title = aula_part[first_space+1:].strip()
        else:
            aula_title = aula_part
            
        module_title = modulo_part
    else:
        # Fallback para os nao formatados
        module_title = "Outros"
        aula_title = titulo_completo

    if module_title not in modules:
        modules[module_title] = []
        module_order.append(module_title)
        
    modules[module_title].append({
        "id": key,
        "title": aula_title
    })

# REVERSE THE MODULE ORDER SO "1. Introdução" IS Module-1
module_order.reverse()

moduleIds_str = ", ".join([f'"css-Module-{i+1}"' for i in range(len(module_order))])

ts_content = f"""import {{ Course }} from '../../types';

export const CssExtCourse: Course = {{
    id: "css-course",
    slug: "css",
    title: "Html & Css Extremo",
    description: "Descrição automática gerada pelo script.",
    thumbnail: "/images/css-thumb.jpg",
    categories: [
        {{ 
            name: "Todos os Módulos", 
            moduleIds: [{moduleIds_str}] 
        }}
    ],
    modules: [
"""

def extract_number(id_str):
    match = re.search(r'\d+', id_str)
    return int(match.group()) if match else 999999

for i, mod_title in enumerate(module_order):
    ts_content += f"""        {{
            id: "css-Module-{i+1}",
            title: "{mod_title}",
            lessons: [
"""
    lessons = modules[mod_title]
    lessons.sort(key=lambda x: extract_number(x['id']))
    
    for j, lesson in enumerate(lessons):
        comma = "," if j < len(lessons)-1 else ""
        ts_content += f"""                {{ id: "{lesson['id']}", title: "{lesson['title']}" }}{comma}
"""
    
    comma = "," if i < len(module_order)-1 else ""
    ts_content += f"""            ]
        }}{comma}
"""

ts_content += """    ]
};
"""

target_ts = 'd:/Applications/telegram-streamer/course_css.ts'
with open(target_ts, 'w', encoding='utf-8') as f:
    f.write(ts_content)

print(f"course_css.ts gerado com {len(module_order)} módulos na ordem reversa.")
