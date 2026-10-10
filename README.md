
# 🔍 Raio-X do Candidato

> Transformando dados públicos do TSE em linguagem que **qualquer eleitor** entende.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## 🎯 O Problema

Os dados de candidatos brasileiros estão **disponíveis publicamente** (TSE, Portal da Transparência, Receita Federal), mas:

- ❌ São **inacessíveis** para quem não é especialista
- ❌ Usam **linguagem técnica** ("circular_donation", "CEIS/CNEP")
- ❌ Estão em **planilhas enormes** sem contexto

## 💡 A Solução

Um site que transforma esses dados em:

- 📊 **Nota de 0 a 100** com semáforo colorido
- 📖 **Resumo em 3 frases** que qualquer pessoa entende
- 🏠 **Analogias do dia a dia** ("Isso equivale a 26 casas populares")
- 📸 **Card para compartilhar** no WhatsApp e Instagram
- 🔍 **Filtros** por estado, partido, cargo e ano

## 🎬 Como funciona

1. Digite o nome do político
2. Veja a nota e o resumo em linguagem simples
3. Compartilhe nos Stories ou no WhatsApp

## 🛠️ Tecnologias

| Camada | Tecnologia |
| :--- | :--- |
| **Backend** | Python 3.12, FastAPI, SQLite |
| **Frontend** | HTML, TailwindCSS, JavaScript |
| **Dados** | TSE, Portal da Transparência, Receita Federal |
| **Base de Dados** | EloSys (11,4 GB, 36 tabelas) |

## 🚀 Como rodar localmente

### Pré-requisitos
- Python 3.12+
- `uv` (gerenciador de pacotes)

### Passo a passo

```bash
# 1. Clonar o repositório
git clone https://github.com/matheussouzarte23/raiox-candidato.git
cd raiox-candidato

# 2. Baixar o banco de dados (11,4 GB)
# Link: https://archive.org/details/elosys
# Extrair para dados/elosys.db

# 3. Instalar dependências do backend
cd backend
uv sync

# 4. Rodar o backend
uv run python main.py

# 5. Em outro terminal, abrir o frontend
cd ../frontend
python -m http.server 5500
