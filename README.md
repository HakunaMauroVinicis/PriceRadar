# Monitoramento de Preços com Streamlit

Este projeto é um sistema completo para monitoramento automático de preços de produtos em diferentes sites, com interface gráfica em Streamlit. Ele realiza scraping usando BeautifulSoup e Selenium, armazena o histórico de preços em JSON, mantém logs detalhados e permite visualização e previsão de preços.

## Funcionalidades

- **Cadastro de Produtos:** Adicione produtos informando nome, URL, tag HTML e classe CSS do preço.
- **Extração Automática de Preços:** O sistema busca o preço atual do produto na web, inclusive em páginas protegidas por JavaScript ou anti-bot (usando Selenium como fallback).
- **Histórico e Gráficos:** Visualize o histórico de preços de cada produto em tabelas e gráficos.
- **Previsão de Preço:** Previsão simples baseada em média móvel dos últimos 3 preços.
- **Atualização Automática:** Thread em background atualiza todos os produtos periodicamente, com frequência configurável.
- **Logs Detalhados:** Visualize logs de erros, avisos e operações diretamente na interface.
- **Interface Amigável:** Navegação por abas (Dashboard, Produtos, Logs, Configuração) via Streamlit.

## Como Usar

1. **Pré-requisitos**
   - Python 3.8+
   - Google Chrome instalado (para Selenium)
   - Instale as dependências:
     ```bash
     pip install streamlit selenium beautifulsoup4 pandas matplotlib
     ```

2. **Configuração do WebDriver**
   - Baixe o [ChromeDriver](https://chromedriver.chromium.org/downloads) compatível com sua versão do Chrome e coloque-o no PATH do sistema ou na mesma pasta do projeto.

3. **Executando o Projeto**
   ```bash
   streamlit run app.py