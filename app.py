# Sistema de Monitoramento de Preços com Interface Streamlit
# -----------------------------------------------------------------------------
# Autor: Mauro Vinícius Vargas Custódio "H4kuna"
# Data: 04/06/2025
# Descrição:
#   Este sistema realiza o monitoramento automático de preços de produtos em
#   diferentes sites, utilizando scraping com BeautifulSoup e Selenium.
#   Os dados são armazenados em JSON, logs são mantidos em arquivo texto,
#   e a interface gráfica é feita com Streamlit, incluindo abas para dashboard,
#   produtos, logs e configuração.
# -----------------------------------------------------------------------------

import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os
import streamlit as st
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
import time
import threading

# -----------------------------------------------------------------------------
# Configuração de Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    filename='log_precos.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# -----------------------------------------------------------------------------
# Constantes e Arquivos de Dados
# -----------------------------------------------------------------------------
DATA_FILE = 'precos.json'

# -----------------------------------------------------------------------------
# Carregamento do Banco de Dados de Preços
# -----------------------------------------------------------------------------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        historico_precos = json.load(f)
else:
    historico_precos = {}

def salvar_dados():
    """
    Salva o histórico de preços no arquivo JSON.
    """
    with open(DATA_FILE, 'w') as f:
        json.dump(historico_precos, f, indent=2)

# -----------------------------------------------------------------------------
# Funções de Extração de Preço
# -----------------------------------------------------------------------------
def extrair_preco_com_selenium(url, tag, class_name):
    """
    Extrai o preço de uma página utilizando Selenium, útil para páginas com proteção anti-bot ou JavaScript dinâmico.

    Args:
        url (str): URL do produto.
        tag (str): Tag HTML do elemento do preço.
        class_name (str): Classe CSS do elemento do preço.

    Returns:
        float or None: Preço extraído ou None em caso de erro.
    """
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)
        driver.get(url)
        time.sleep(15)  # Aguarda carregamento dinâmico

        elementos = driver.find_elements(By.CLASS_NAME, class_name)
        for el in elementos:
            if el.tag_name.lower() == tag.lower():
                preco_str = el.text.strip().replace('R$', '').replace(',', '.').strip()
                preco = float(preco_str)
                return preco

    except (WebDriverException, TimeoutException, NoSuchElementException) as e:
        logging.error(f"[Selenium] Erro: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
    return None

def extrair_preco(url, tag, class_name):
    """
    Extrai o preço de uma página utilizando BeautifulSoup. Caso falhe, utiliza Selenium como fallback.

    Args:
        url (str): URL do produto.
        tag (str): Tag HTML do elemento do preço.
        class_name (str): Classe CSS do elemento do preço.

    Returns:
        float or None: Preço extraído ou None em caso de erro.
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        preco_elemento = soup.find(tag, {'class': class_name})
        if preco_elemento:
            preco_str = preco_elemento.text.strip().replace('R$', '').replace(',', '.').strip()
            preco = float(preco_str)
            return preco
        else:
            return extrair_preco_com_selenium(url, tag, class_name)
    except Exception as e:
        return extrair_preco_com_selenium(url, tag, class_name)

# -----------------------------------------------------------------------------
# Funções de Manipulação de Produtos e Preços
# -----------------------------------------------------------------------------
def adicionar_produto(nome, url, preco_atual, tag, class_name):
    """
    Adiciona um novo produto ao histórico de preços.

    Args:
        nome (str): Nome do produto.
        url (str): URL do produto.
        preco_atual (float): Preço atual do produto.
        tag (str): Tag HTML do elemento do preço.
        class_name (str): Classe CSS do elemento do preço.
    """
    if nome not in historico_precos:
        historico_precos[nome] = {
            'url': url,
            'tag': tag,
            'class': class_name,
            'precos': [
                {'timestamp': datetime.now().isoformat(), 'preco': preco_atual}
            ]
        }
        salvar_dados()

def inserir_preco_manual(nome, preco):
    """
    Insere manualmente um novo preço para um produto.

    Args:
        nome (str): Nome do produto.
        preco (float): Preço a ser inserido.
    """
    historico_precos[nome]['precos'].append({
        'timestamp': datetime.now().isoformat(),
        'preco': preco
    })
    salvar_dados()

def atualizar_preco_automatico(nome):
    """
    Atualiza automaticamente o preço de um produto, extraindo o valor da web.

    Args:
        nome (str): Nome do produto.
    """
    dados = historico_precos[nome]
    preco = extrair_preco(dados['url'], dados['tag'], dados['class'])
    if preco:
        inserir_preco_manual(nome, preco)

# -----------------------------------------------------------------------------
# Funções de Visualização e Previsão
# -----------------------------------------------------------------------------
def gerar_grafico(nome_produto):
    """
    Gera um gráfico de histórico de preços para um produto.

    Args:
        nome_produto (str): Nome do produto.

    Returns:
        matplotlib.figure.Figure or None: Figura do gráfico ou None se não houver dados.
    """
    dados = historico_precos[nome_produto]['precos']
    if not dados:
        return None
    df = pd.DataFrame(dados)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.plot(df.index, df['preco'], marker='o')
    ax.set_title(f'{nome_produto}')
    ax.set_xlabel('Data')
    ax.set_ylabel('R$')
    ax.grid(True)
    plt.xticks(rotation=30)
    return fig

def prever_preco(nome_produto):
    """
    Realiza uma previsão simples do preço utilizando média móvel de 3 períodos.

    Args:
        nome_produto (str): Nome do produto.

    Returns:
        float or None: Preço previsto ou None se não houver dados suficientes.
    """
    dados = historico_precos[nome_produto]['precos']
    if len(dados) < 3:
        return None
    df = pd.DataFrame(dados)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    df['preco_ma'] = df['preco'].rolling(window=3).mean()
    return df['preco_ma'].iloc[-1]

# -----------------------------------------------------------------------------
# Atualização Automática Periódica dos Produtos
# -----------------------------------------------------------------------------
ultima_execucao = 0

CONFIG_FILE = 'config.json'
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        configuracoes = json.load(f)
        horas = configuracoes.get("frequencia_horas", 6)
else:
    horas = 6

intervalo_em_segundos = horas * 3600

def atualizar_todos_os_produtos_periodicamente():
    """
    Thread responsável por atualizar automaticamente todos os produtos cadastrados
    em intervalos regulares definidos pelo usuário.
    """
    global ultima_execucao
    while True:
        agora = time.time()
        if agora - ultima_execucao > intervalo_em_segundos:
            logging.info("Iniciando atualização automática de todos os produtos.")
            for nome in historico_precos:
                try:
                    atualizar_preco_automatico(nome)
                except Exception as e:
                    logging.error(f"Erro ao atualizar {nome}: {e}")
            ultima_execucao = agora
        time.sleep(60)

# Inicia a thread de atualização automática
threading.Thread(target=atualizar_todos_os_produtos_periodicamente, daemon=True).start()

# -----------------------------------------------------------------------------
# Interface Gráfica com Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide")
st.sidebar.title("Menu")
abas = st.sidebar.radio("Navegação", ["Dashboard", "Produtos", "Logs", "Configuração"])

# ---------------------- Aba Dashboard ----------------------
if abas == "Dashboard":
    st.title("📊 Monitoramento de Preços")

    # Formulário para adicionar novo produto
    with st.form("form_adicionar"):
        nome = st.text_input("Nome do Produto")
        url = st.text_input("URL do Produto")
        preco_atual = st.number_input("Preço Atual", min_value=0.0, format="%.2f")
        tag = st.text_input("Tag HTML", value="span")
        class_name = st.text_input("Classe CSS")
        submitted = st.form_submit_button("Adicionar")
        if submitted and nome and url and preco_atual:
            adicionar_produto(nome, url, preco_atual, tag, class_name)
            st.success(f"Produto '{nome}' adicionado.")

    # Exibição de informações e histórico do produto selecionado
    if historico_precos:
        produto_selecionado = st.selectbox("Produto:", list(historico_precos.keys()))
        if produto_selecionado:
            dados = historico_precos[produto_selecionado]
            st.write(f"**URL:** {dados['url']}")
            st.write(f"**Tag:** {dados['tag']} | Classe: {dados['class']}")

            preco_manual = st.number_input("Novo Preço", min_value=0.0, format="%.2f")
            if st.button("Registrar Preço Manual"):
                inserir_preco_manual(produto_selecionado, preco_manual)

            if st.button("🔄 Atualizar Automaticamente"):
                atualizar_preco_automatico(produto_selecionado)
                st.success("Atualizado!")

            st.subheader("Histórico de Preços")
            fig = gerar_grafico(produto_selecionado)
            if fig:
                st.pyplot(fig)

            previsao = prever_preco(produto_selecionado)
            if previsao:
                st.info(f"Previsão (média móvel): R$ {previsao:.2f}")

            df = pd.DataFrame(dados['precos'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            st.dataframe(df.sort_values(by='timestamp', ascending=False).head(10))

# ---------------------- Aba Produtos ----------------------
elif abas == "Produtos":
    st.title("📦 Produtos Cadastrados")
    if historico_precos:
        for nome, dados in historico_precos.items():
            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown(f"### {nome}")
                st.write(f"URL: {dados['url']}")
                st.write(f"Tag: {dados['tag']} | Classe: {dados['class']}")
                previsao = prever_preco(nome)
                if previsao:
                    st.success(f"Previsão: R$ {previsao:.2f}")
                df = pd.DataFrame(dados['precos'])
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    st.dataframe(df.sort_values(by='timestamp', ascending=False).head(5))
            with col2:
                fig = gerar_grafico(nome)
                if fig:
                    st.pyplot(fig)
    else:
        st.info("Nenhum produto cadastrado.")

# ---------------------- Aba Logs ----------------------
elif abas == "Logs":
    st.title("📁 Logs do Sistema")
    try:
        with open("log_precos.txt", "r") as log_file:
            conteudo = log_file.readlines()

        if conteudo:
            with st.expander("▶ Ver Logs Detalhados", expanded=True):
                for linha in reversed(conteudo[-100:]):
                    if "ERROR" in linha:
                        st.error(linha.strip())
                    elif "WARNING" in linha:
                        st.warning(linha.strip())
                    elif "INFO" in linha:
                        st.info(linha.strip())
                    else:
                        st.write(linha.strip())
        else:
            st.info("O log está vazio.")

    except FileNotFoundError:
        st.warning("Arquivo de log não encontrado.")

# ---------------------- Aba Configuração ----------------------
elif abas == "Configuração":
    st.title("⚙️ Configuração de Atualização Automática")

    CONFIG_FILE = 'config.json'
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            configuracoes = json.load(f)
    else:
        configuracoes = {"frequencia_horas": 6}

    horas = st.slider("Frequência de Atualização (em horas):", min_value=1, max_value=24, value=configuracoes.get("frequencia_horas", 6))

    if st.button("Salvar Configuração"):
        configuracoes["frequencia_horas"] = horas
        with open(CONFIG_FILE, 'w') as f:
            json.dump(configuracoes, f, indent=2)
        st.success(f"A atualização automática ocorrerá a cada {horas} hora(s).")

    intervalo_em_segundos = horas * 3600