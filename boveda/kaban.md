Aja como um programador especialista em Python com foco em interfaces gráficas locais. Gere diretamente o código completo de um aplicativo local de Kanban com as seguintes características:

# 🧩 Título: Criação de aplicativo Kanban local com PyQt5

## 🎯 Objetivo
Criar um aplicativo **Kanban local**, simples e funcional, usando **Python com PyQt5**. O programa será usado para organizar ideias de artigos científicos. Deve ser totalmente offline, **sem dependências de nuvem**.

---

## ✅ Funcionalidades obrigatórias

### 0. Interface por falta com colunas Kanban (quadros)
- As colunas representam estados como:  
  - **"Ideias"**
  - **"Em elaboração"**
  - **"Submetidos"**
  - **"Aprovados"**, etc.
- As colunas são chamadas de **quadros** e tem uma cor verde claro diferente do fundo.

### 1. Toolbar com botões para:
- Adicionar um novo quadro (coluna).
- Remover um quadro selecionado.
- Botao para salvar o json
- Botão cargar json
todos Os botoes usam icones do sistema
### 2 Quadros
- Cada quadro tem um botao para anhadir nova nota
- Cada quadro tem um botão de eliminar quadro
- o titulo do quadro deve estar no topo e deve ser editavel
todos Os botoes usam icones do sistema
### 3. Notas em cada quadro:
- Cada nota possui:
  - Um **título**
  - Um **conteúdo editável** (parágrafo) este parte deve ser exansivel e comprimivel pois pode ser longo.
- O conteúdo deve aceitar **Markdown** (renderizado ou, no mínimo, salvo como texto markdown).
- As notas devem poder ser **movidas entre quadros via drag and drop**. obviamente ao mover uma nota se elimina de onde saiu.
- Agrega um botao para remover nota

todos Os botoes usam icones do sistema

### 4. Persistência local (opcional no primeiro protótipo):
- Todas as notas e quadros devem ser salvos em um **único arquivo JSON local** para manter os dados entre execuções.

---

## 🛠️ Tecnologias

- **PyQt5**
- `QWidget`, `QVBoxLayout`, `QHBoxLayout`, `QTextEdit`, `QListWidget`, `QToolBar`, etc.
- Se possível, usar `QMarkdownTextEdit` (ou substituto baseado em `QTextEdit`) para suporte a Markdown.

---

## 🧪 Estilo desejado

- Interface **clara, funcional e minimalista**, compacta sobretudo, os boteoes devem ter tooltip.
- **Drag and drop** entre colunas funcionando.
- Boa separação visual entre colunas (usando cores ou bordas simples).
- Não é necessário tema escuro ou recursos avançados.

---

Por favor, gere o código completo do aplicativo inicial com essas funcionalidades.
