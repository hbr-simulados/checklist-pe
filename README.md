# 🚨 Dashboard de Simulado de Emergência - Monitoramento dos Pontos de Encontro

[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://yourapp-url.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

Dashboard interativo para gestão de simulações de Planos de Ação de Emergência (PAE) com visualização geoespacial em tempo real.

![image](https://github.com/user-attachments/assets/0c71bd18-5e4b-438e-b69c-6d50637e5a9c)


## ✨ Funcionalidades Principais
- **Mapa Interativo:** Visualização de pontos de encontro com ícones coloridos por efetividade
- **Métricas em Tempo Real:**
  - Total de participantes vs. esperados
  - Efetividade geral e por ponto específico
- **Múltiplas Fontes de Dados:**
  - Entrada manual de coordenadas
  - Upload de arquivos Excel/Shapefile
- **Personalização Corporativa:**
  - Logotipos customizáveis
  - Cores institucionais
  - Títulos dinâmicos

## 🛠️ Pré-requisitos
- Python 3.9+
- Gerenciador de pacotes `pip`
- Conta no [Streamlit Cloud](https://streamlit.io/cloud) para deploy

## 🚀 Instalação Local
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/pae-dashboard.git

# Acesse o diretório
cd pae-dashboard

# Crie e ative ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
