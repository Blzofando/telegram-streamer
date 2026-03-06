import re
import json

text = """= 1. Introducao Assista antes de comecar

== 1. Como assistir as aulas
#F01

== 2. Como tirar suas duvidas
#F02

== 3. Como baixar os arquivos e a apostila
#F03

== 4. Como emitir o certificado
#F04

== 5. Como funciona a garantia
#F05

== 6. Suporte Hashtag
#F06

== 7. Grupo do Facebook do HTML e CSS Impressionador
#F07

= 2. Boas vindas e configuracoes iniciais

== 1. O que e Desenvolvimento Web
#F08

== 2. O que voce vai aprender
#F09

== 3. 2 dicas para todo programador
#F10

== 4. Baixando e configurando nosso editor de codigos
#F11

= 3. Introducao ao HTML

== 1. O que e o HTML
#F12

== 2. Estrutura de um documento HTML
#F13

== 3. Elementos de texto
#F14

== 4. Enfase Importancia e Formatacao de Textos
#F15

== 5. Listas ordenadas e nao ordenadas
#F16

== 6. Hiperlinks
#F17

== 7. Imagens e seus atributos no HTML
#F18

== 8. Ferramentas do Programador
#F19

== 9. Desafio 1 Apresentando o Desafio
#F20

== 10. Desafio 1 Construindo o Desafio do Zero
#F21

== 11. Desafio 2 Home da Hashtag Treinamentos
#F22

== 12. Desafio 2 Criando o Cabecalho
#F23

== 13. Desafio 2 Criando a Secao Hero
#F24

== 14. Desafio 2 Criando a Secao Conteudos Gratuitos
#F25

== 15. Desafio 2 Criando a Secao Diferenciais
#F26

== 16. Desafio 2 Criando a Secao O que falam
#F27

== 17. Desafio 2 Criando a Secao Na midia
#F28

== 18. Desafio 2 Criando a Secao Blog da Hashtag
#F29

== 19. Desafio 2 Criando a Secao Como ajudar
#F30

== 20. Desafio 2 Criando a Secao Minicurso
#F31

== 21. Desafio 2 Criando o Rodape
#F32

= 4. Introducao ao CSS

== 1. O que e CSS
#F33

== 2. As tres formas de escrever CSS
#F34

== 3. Seletores no CSS
#F35

== 4. Combinando seletores
#F36

== 5. Estilizando textos
#F37

== 6. Trabalhando com cores
#F38

== 7. Estilizando hiperlinks
#F39

== 8. Desafio 1 Formatando uma pagina em HTML
#F40

== 9. Desafio 1 Resolvendo o Desafio
#F41

== 10. Desafio 2 Formatando a Home da Hashtag
#F42

== 11. Desafio 2 Formatando o Cabecalho
#F43

== 12. Desafio 2 Formatando a Secao Hero
#F44

== 13. Desafio 2 Formatando a Secao Conteudos Gratuitos
#F45

== 14. Desafio 2 Formatando a Secao Diferenciais
#F46

== 15. Desafio 2 Formatando a Secao O que falam
#F47

== 16. Desafio 2 Formatando a Secao Na midia
#F48

== 17. Desafio 2 Formatando a Secao Blog da Hashtag
#F49

== 18. Desafio 2 Formatando a Secao Como ajudar
#F50

== 19. Desafio 2 Formatando a Secao Minicurso
#F51

== 20. Desafio 2 Formatando o Rodape
#F52

= 5. Aprofundando no HTML

== 1. Apresentacao do Modulo
#F53

== 2. Citacoes Abreviacoes e Detalhes de contato
#F54

== 3. Codigos e Datas
#F55

== 4. Entrando mais a fundo na estrutura dos documentos
#F56

== 5. Formularios
#F57

== 6. Input Pattern Regex
#F58

== 7. Tabelas
#F59

== 8. iFrames
#F60

== 9. Dialog
#F61

== 10. Desafio 1 Apresentando o Desafio
#F62

== 11. Desafio 1 Construindo juntos
#F63

== 12. Desafio 2 Explicando as novidades
#F64

== 13. Desafio 2 Completando o Cabecalho
#F65

== 14. Desafio 2 Completando a Secao Hero
#F66

== 15. Desafio 2 Completando a Secao Conteudos Gratuitos
#F67

== 16. Desafio 2 Completando a Secao Diferenciais
#F68

== 17. Desafio 2 Completando a Secao O que falam e Na midia
#F69

== 18. Desafio 2 Completando a Secao Blog da Hashtag
#F70

== 19. Desafio 2 Completando a Secao Como ajudar
#F71

== 20. Desafio 2 Completando a Secao Minicurso
#F72

== 21. Desafio 2 Completando o Rodape
#F73

= 6. Aprofundando no CSS

== 1. Apresentacao do Modulo
#F74

== 2. Especificidade no CSS
#F75

== 3. Trabalhando com espacamentos
#F76

== 4. Dimensoes e unidades no CSS
#F77

== 5. Pseudoclasses
#F78

== 6. Pseudoelementos
#F79

== 7. Seletor universal e heranca de estilos
#F80

== 8. Box Model no CSS
#F81

== 9. Sombras
#F82

== 10. Novas unidades no CSS svh lvh dvh
#F83

== 11. Elementos arredondados
#F84

== 12. Tipos de visualizacao
#F85

== 13. Tipos de posicionamento
#F86

== 14. Background Color e Image
#F87

== 15. Desafio 1 Evoluindo a pagina de Exercicio
#F88

== 16. Desafio 1 Gabarito
#F89

== 17. Desafio 2 Aprofundando no Desafio 2
#F90

== 18. Desafio 2 Aprofundando o Cabecalho
#F91

== 19. Desafio 2 Aprofundando a Secao Hero
#F92

== 20. Desafio 2 Aprofundando a Secao Conteudos Gratuitos
#F93

== 21. Desafio 2 Aprofundando a Secao Diferenciais
#F94

== 22. Desafio 2 Aprofundando a Secao O que falam
#F95

== 23. Desafio 2 Aprofundando a Secao Na midia
#F96

== 24. Desafio 2 Aprofundando a Blog da Hashtag
#F97

== 25. Desafio 2 Aprofundando a Secao Como ajudar
#F98

== 26. Desafio 2 Aprofundando a Secao Minicurso
#F99

== 27. Desafio 2 Aprofundando o Rodape
#F100

== 28. Exercicios Extras CSS Diner
#F101

= 7. Flexbox no CSS

== 1. Apresentacao do Modulo
#F102

== 2. O que e e como usar o Flexbox
#F103

== 3. Espacamento entre os elementos
#F104

== 4. Mudar a direcao do Flexbox
#F105

== 5. Tamanho dos elementos
#F106

== 6. Alinhamento e Posicionamento dos elementos
#F107

== 7. Desafio 1 Construindo Layouts com Flexbox
#F108

== 8. Desafio 1 Gabarito
#F109

== 9. Desafio 2 Flexbox na Home da Hashtag
#F110

== 10. Desafio 2 Flexbox no Cabecalho
#F111

== 11. Desafio 2 Flexbox na Secao Hero
#F112

== 12. Desafio 2 Flexbox na Secao Conteudos Gratuitos
#F113

== 13. Desafio 2 Flexbox na Secao Diferenciais
#F114

== 14. Desafio 2 Flexbox na Secao O que falam
#F115

== 15. Desafio 2 Flexbox na Secao Na midia
#F116

== 16. Desafio 2 Flexbox na Blog da Hashtag
#F117

== 17. Desafio 2 Flexbox na Secao Como ajudar
#F118

== 18. Desafio 2 Flexbox na Secao Minicurso
#F119

== 19. Desafio 2 Flexbox no Rodape
#F120

== 20. Exercicios Extras Flexbox Froggy
#F121

= 8. Componentes Personalizados no HTML

== 1. Apresentacao do Modulo
#F122

== 2. Paginacao Apresentando o Desafio
#F123

== 3. Paginacao Resolucao 12
#F124

== 4. Paginacao Resolucao 22 CSS Nesting
#F125

== 5. Acordeao Apresentando o Desafio
#F126

== 6. Acordeao Resolucao
#F127

== 7. Popup Apresentando o Desafio
#F128

== 8. Popup Resolucao
#F129

== 9. Carrossel Apresentando o Desafio
#F130

== 10. Carrossel Resolucao 12
#F131

== 11. Carrossel Resolucao 22
#F132

== 12. Desafio 2 Criando o Popup da Home da Hashtag
#F133

== 13. Desafio 2 Gabarito
#F134

= 9. Grid no CSS

== 1. Apresentacao do Modulo
#F135

== 2. Como usar o Grid
#F136

== 3. Definindo as linhas da Grade
#F137

== 4. Definindo as colunas da Grade
#F138

== 5. Propriedade Grid
#F139

== 6. Posicionando os elementos
#F140

== 7. Espacamento entre os elementos
#F141

== 8. Areas dentro da Grade
#F142

== 9. Alinhamento dos elementos
#F143

== 10. Propriedade placeitems
#F144

== 11. Autofit e Autofill para criar Grids Responsivas
#F145

== 12. Grid vs Flexbox
#F146

== 13. Desafio 1 Construindo um layout com Grid
#F147

== 14. Desafio 1 Gabarito
#F148

== 15. Desafio 2 Usando Grid na Secao Blog
#F149

== 16. Desafio 2 Gabarito
#F150

== 17. Exercicios Extras Grid Garden
#F151

= 10. Checkpoint

== 1. O que vem pela frente
#F152

== 2. Feedback ate aqui
#F153

= 11. Animacoes e Efeitos no CSS

== 1. Apresentacao do Modulo
#F154

== 2. Transicoes 12
#F155

== 3. Transicoes 22
#F156

== 4. Efeitos 2D
#F157

== 5. Efeitos 3D
#F158

== 6. Keyframes
#F159

== 7. Animation e suas propriedades
#F160

== 8. @media prefersreducedmotion
#F161

== 9. Desafio 1 Criando um Elementos Animado
#F162

== 10. Desafio 1 Gabarito
#F163

== 11. Desafio 2 Transicoes na Home da Hashtag
#F164

== 12. Desafio 2 Gabarito
#F165

= 13. Float no CSS

== 1. Apresentacao do Modulo
#F166

== 2. Como usar as propriedades float e clear
#F167

== 3. Desafio Construindo um layout com float
#F168

== 4. Desafio Gabarito
#F169

= 14. Metodologia BEM

== 1. Apresentacao do Modulo
#F170

== 2. Como funciona a Metodologia
#F171

== 3. Exemplos da Metotologia
#F172

== 4. Vantagens Desvantagens e Conclusao
#F173

== 5. Cuidados e Observacoes
#F174

== 6. Exemplo pratico
#F175

== 7. Desafio Apresentacao
#F176

== 8. Desafio Gabarito
#F177

= 15. Extensao SASS

== 1. Apresentacao do Modulo
#F178

== 2. O que e SASS
#F179

== 3. O que e NodeJS e o que e NPM
#F180

== 4. Instalando o NodeJS NPM e SASS
#F181

== 5. Criando e compilando nosso primeiro codigo
#F182

== 6. Variaveis
#F183

== 7. Nesting x Native Nesting
#F184

== 8. Functions
#F185

== 9. Mixins e Includes
#F186

== 10. Extends
#F187

== 11. Content e If
#F188

== 12. Build Compile Prefix and Compress
#F189

== 13. @for
#F190

== 14. Padrao 71
#F191

= 18. Framework Bootstrap

== 1. Apresentacao do Modulo
#F192

== 2. Instalacao via CDN
#F193

== 3. Instalando via Package Manager npm
#F194

== 4. Usando componentes prontos
#F195

== 5. Como encontrar elementos e classes
#F196

== 6. Containers e Breakpoints
#F197

== 7. Grid System
#F198

== 8. CSS Grid e Flexbox
#F199

= 19. Projeto de Landing Page Bootstrap

== 1. Apresentacao do Desafio
#F200

== 2. Configuracoes Iniciais Secao Hero
#F201

== 3. Secao Disclaimer Dark Mode
#F202

== 4. Secao Features
#F203

== 5. Secao Para Quem
#F204

== 6. Secao Quem
#F205

== 7. Rodape
#F206

== 8. Modal
#F207

== 9. Responsividade
#F208

== 10. Consideracoes Finais sobre o Bootstrap
#F209

= 21. Framework Tailwind CSS

== 1. Apresentacao do Modulo e do Tailwind
#F210

== 2. Instalacao via CDN
#F211

== 3. Instalacao via Package Manager npm
#F212

== 4. Layout da pagina com Flex e Grid
#F213

== 5. Cores Fontes e Tamanhos Tailwind Fold
#F214

== 6. Borderradius Textdecoration e Ajustes na primeira dobra.mp4
#F216

== 7. Liststyle Posicionamento absoluto e Finalizando o Desktop.mp4
#F218

== 8. Responsividade
#F219

= 23. Plantao de Duvidas de HTML CSS e JavaScript

== 1. Plantao de Duvidas de HTML CSS e JavaScript
#F220

== Materiais do Curso
#M01
"""

lines = text.split('\n')
modules = []
current_module = None
current_lesson_title = None
module_count = 0

for line in lines:
    line = line.strip()
    if line.startswith('= ') and not line.startswith('== '):
        module_count += 1
        title = line[2:]
        current_module = {
            "id": f"html-Module-{module_count}",
            "title": title,
            "lessons": []
        }
        modules.append(current_module)
    elif line.startswith('== '):
        current_lesson_title = line[3:]
    elif line.startswith('#'):
        video_id = line[1:]
        if current_module and current_lesson_title:
            current_module["lessons"].append({
                "id": f"html-{video_id}",
                "title": current_lesson_title
            })
            current_lesson_title = None

course_str = "    modules: [\n"
for mod in modules:
    course_str += "        {\n"
    course_str += f'            id: "{mod["id"]}",\n'
    course_str += f'            title: "{mod["title"]}",\n'
    course_str += "            lessons: [\n"
    for i, lesson in enumerate(mod["lessons"]):
        comma = "," if i < len(mod["lessons"]) - 1 else ""
        course_str += f'                {{ id: "{lesson["id"]}", title: "{lesson["title"]}" }}{comma}\n'
    course_str += "            ]\n"
    if mod == modules[-1]:
        course_str += "        }\n"
    else:
        course_str += "        },\n"
course_str += "    ]\n"

with open('output_modules.txt', 'w', encoding='utf-8') as f:
    f.write(course_str)
