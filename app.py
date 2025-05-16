import os
import sys
import logging
import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import re
import hashlib
from datetime import datetime, timedelta
from functools import wraps

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("valueHunter.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("valueHunter.app")

# Configuração do diretório de dados
DATA_DIR = os.environ.get("DATA_DIR", "data")
if "RENDER" in os.environ:
    DATA_DIR = "/mnt/value-hunter-data"

# Garantir que o diretório de dados existe
os.makedirs(DATA_DIR, exist_ok=True)

# Importar módulos do projeto
try:
    from utils.core import UserManager, DATA_DIR
except ImportError:
    # Se falhar, criar uma referência local
    from utils.data import UserManager

# Importar páginas
from pages.landing import show_landing_page
from pages.dashboard import show_main_dashboard
from pages.auth import show_login, show_register, show_password_reset

# Configurações da página
st.set_page_config(
    page_title="ValueHunter",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.valueHunter.com/help',
        'Report a bug': 'https://www.valueHunter.com/bug',
        'About': "# ValueHunter\nSua ferramenta de análise de apostas esportivas."
    }
)

# Inicializar estado da sessão
if 'page' not in st.session_state:
    st.session_state.page = "landing"

if 'user' not in st.session_state:
    st.session_state.user = None

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

if 'use_sample_data' not in st.session_state:
    st.session_state.use_sample_data = True

# Inicializar user_manager no session_state
if 'user_manager' not in st.session_state:
    st.session_state.user_manager = UserManager()

# Função para aplicar tema escuro
def apply_dark_theme():
    """Aplica tema escuro consistente em toda a aplicação"""
    st.markdown("""
    <style>
    /* Tema escuro */
    body {
        color: #f0f0f0;
        background-color: #121212;
    }
    
    .stApp {
        background-color: #121212;
    }
    
    .stSidebar {
        background-color: #1e1e1e;
    }
    
    .stButton>button {
        background-color: #3F3F45;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton>button:hover {
        background-color: #4f4f55;
    }
    
    .stTextInput>div>div>input {
        background-color: #2d2d2d;
        color: white;
        border: 1px solid #3F3F45;
    }
    
    .stSelectbox>div>div>select {
        background-color: #2d2d2d;
        color: white;
        border: 1px solid #3F3F45;
    }
    
    .stDataFrame {
        background-color: #2d2d2d;
        color: white;
    }
    
    /* Cores de destaque */
    .highlight {
        color: #FF5733;
        font-weight: bold;
    }
    
    .success {
        color: #4CAF50;
    }
    
    .warning {
        color: #FFC107;
    }
    
    .error {
        color: #F44336;
    }
    
    /* Estilo de cartões */
    .card {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #3F3F45;
    }
    
    /* Estilo de tabelas */
    table {
        width: 100%;
        border-collapse: collapse;
    }
    
    th {
        background-color: #3F3F45;
        color: white;
        text-align: left;
        padding: 8px;
    }
    
    td {
        border-bottom: 1px solid #3F3F45;
        padding: 8px;
    }
    
    tr:hover {
        background-color: #2d2d2d;
    }
    </style>
    """, unsafe_allow_html=True)

# Função para mostrar barra lateral
def show_sidebar():
    """Exibe a barra lateral com opções de navegação e configuração"""
    with st.sidebar:
        st.title("ValueHunter")
        
        # Informações do usuário
        if st.session_state.logged_in and st.session_state.user:
            st.subheader(f"Olá, {st.session_state.user.get('name', 'usuário')}!")
            
            # Estatísticas de uso
            user_manager = UserManager()
            stats = user_manager.get_usage_stats(st.session_state.user['email'])
            
            st.write(f"Estatísticas de Uso")
            
            # Créditos
            credits_col1, credits_col2 = st.columns(2)
            with credits_col1:
                st.write("Créditos Restantes:")
            with credits_col2:
                st.write(f"{stats.get('credits_remaining', 0)}")
            
            # Tier
            tier_col1, tier_col2 = st.columns(2)
            with tier_col1:
                st.write("Plano:")
            with tier_col2:
                tier_name = stats.get('tier', 'free')
                if tier_name == 'free':
                    tier_display = "Gratuito"
                elif tier_name == 'standard':
                    tier_display = "Standard"
                elif tier_name == 'pro':
                    tier_display = "Pro"
                else:
                    tier_display = tier_name.capitalize()
                st.write(f"{tier_display}")
            
            # Análises realizadas
            analyses_col1, analyses_col2 = st.columns(2)
            with analyses_col1:
                st.write("Análises realizadas:")
            with analyses_col2:
                st.write(f"{stats.get('analyses_count', 0)}")
            
            # Renovação de créditos (apenas para tier gratuito)
            if tier_name == 'free':
                if stats.get('free_credits_reset', False):
                    st.success("Créditos renovados!")
                elif 'next_free_credits_time' in stats:
                    st.info(f"Próxima renovação em: {stats['next_free_credits_time']}")
            
            # Aviso de downgrade (apenas para tiers pagos sem créditos)
            if tier_name in ['standard', 'pro'] and stats.get('credits_remaining', 0) == 0:
                days_until_downgrade = stats.get('days_until_downgrade')
                if days_until_downgrade is not None and days_until_downgrade > 0:
                    st.warning(f"Seu plano será rebaixado em {days_until_downgrade} dias se não adquirir mais créditos.")
            
            # Botões de navegação
            if st.button("Dashboard"):
                st.session_state.page = "dashboard"
                st.experimental_rerun()
            
            if st.button("Ver Pacotes de Créditos"):
                st.session_state.page = "credits"
                st.experimental_rerun()
            
            if st.button("Sair"):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.page = "landing"
                st.experimental_rerun()
        else:
            # Opções para usuários não logados
            if st.button("Início"):
                st.session_state.page = "landing"
                st.experimental_rerun()
            
            if st.button("Entrar"):
                st.session_state.page = "login"
                st.experimental_rerun()
            
            if st.button("Registrar"):
                st.session_state.page = "register"
                st.experimental_rerun()
        
        # Modo de debug (apenas visível se ativado)
        if st.session_state.debug_mode:
            st.sidebar.subheader("Modo de Debug")
            
            # Estado da sessão
            if st.sidebar.checkbox("Mostrar estado da sessão"):
                st.sidebar.json(st.session_state)
            
            # Variáveis de ambiente
            if st.sidebar.checkbox("Mostrar variáveis de ambiente"):
                env_vars = {k: v for k, v in os.environ.items() if not k.startswith('AWS_') and not k.startswith('RENDER_')}
                st.sidebar.json(env_vars)
            
            # Diretório de dados
            if st.sidebar.checkbox("Mostrar diretório de dados"):
                st.sidebar.text(f"DATA_DIR: {DATA_DIR}")
                if os.path.exists(DATA_DIR):
                    files = os.listdir(DATA_DIR)
                    st.sidebar.text(f"Arquivos: {len(files)}")
                    for f in files[:10]:  # Mostrar apenas os primeiros 10
                        st.sidebar.text(f"- {f}")
                    if len(files) > 10:
                        st.sidebar.text(f"... e mais {len(files) - 10} arquivos")
                else:
                    st.sidebar.warning(f"Diretório não existe: {DATA_DIR}")
            
            # Logs
            if st.sidebar.checkbox("Mostrar logs recentes"):
                st.sidebar.subheader("Logs Recentes")
                try:
                    log_file = "valueHunter.log"
                    if os.path.exists(log_file):
                        with open(log_file, "r") as f:
                            logs = f.readlines()[-20:]  # Últimas 20 linhas
                        for log in logs:
                            st.sidebar.text(log.strip())
                    else:
                        st.sidebar.warning("Arquivo de log não encontrado")
                except Exception as e:
                    st.sidebar.error(f"Erro ao ler logs: {str(e)}")
            
            # Ativar dados de exemplo
            st.session_state.use_sample_data = st.sidebar.checkbox(
                "Usar dados de exemplo", 
                value=st.session_state.get("use_sample_data", True)
            )
            
            # Permitir forçar reload do cache
            if st.sidebar.button("Limpar cache"):
                import glob
                cache_files = glob.glob(os.path.join(DATA_DIR, "cache_*.html"))
                for f in cache_files:
                    try:
                        os.remove(f)
                        st.sidebar.success(f"Removido: {os.path.basename(f)}")
                    except Exception as e:
                        st.sidebar.error(f"Erro ao remover {f}: {str(e)}")
        else:
            st.session_state.debug_mode = False

# Função principal
def main():
    """Função principal que controla o fluxo do aplicativo"""
    try:
        # Aplicar tema escuro consistente
        apply_dark_theme()
                
        # CORREÇÃO ULTRA ESPECÍFICA PARA RETÂNGULO BRANCO E ESPAÇAMENTO
        st.markdown("""
        <style>
        /* SOLUÇÃO ULTRA ESPECÍFICA PARA RETÂNGULO BRANCO E FUNDO ESCURO */
        /* Forçar fundo escuro em todos os elementos principais */
        body, html, .stApp, .main, .main .block-container, 
        .stApp > header, .stApp > div:first-child,
        .stApp > div > div, .stApp > div > div > div,
        .stApp > div > div > div > div, .stApp > div > div > div > div > div,
        .stApp > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div,
        .stApp > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div > div {
            background-color: #121212 !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
            gap: 0 !important;
        }
        
        /* Remover completamente o cabeçalho */
        header[data-testid="stHeader"],
        [data-testid="stHeader"] {
            display: none !important;
            height: 0 !important;
            visibility: hidden !important;
            opacity: 0 !important;
            position: absolute !important;
            top: -9999px !important;
            left: -9999px !important;
        }
        
        /* Remover TODOS os elementos que podem causar o retângulo branco */
        div[data-testid="stDecoration"], 
        div[data-testid="stToolbar"], 
        div[data-testid="stStatusWidget"],
        iframe.stDeployButton,
        .stDeployButton,
        [data-testid="stDecoration"],
        [data-testid="stToolbar"],
        [data-testid="stStatusWidget"],
        .stStatusWidget,
        .stToolbar,
        .stDecoration,
        .stHeader,
        .stApp > header,
        .stApp > div:first-child > div:first-child,
        .stApp > div:first-child > div:first-child > div:first-child,
        .stApp > div:first-child > div:first-child > div:first-child > div:first-child,
        .stApp > div:first-child > div:first-child > div:first-child > div:first-child > div:first-child {
            display: none !important;
            height: 0 !important;
            max-height: 0 !important;
            min-height: 0 !important;
            visibility: hidden !important;
            opacity: 0 !important;
            position: absolute !important;
            top: -9999px !important;
            left: -9999px !important;
            z-index: -9999 !important;
            pointer-events: none !important;
            margin: 0 !important;
            padding: 0 !important;
            border: none !important;
            outline: none !important;
        }
        
        /* Forçar primeiro elemento a começar no topo absoluto */
        .main .block-container > div:first-child,
        .main > div:first-child,
        .stApp > div:first-child,
        .stApp > div > div:first-child,
        .stApp > div > div > div:first-child,
        .stApp > div > div > div > div:first-child,
        .stApp > div > div > div > div > div:first-child,
        .stApp > div > div > div > div > div > div:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
            top: 0 !important;
        }
        
        /* Corrigir altura do container principal */
        .main .block-container,
        .main > div,
        .stApp > div,
        .stApp > div > div,
        .stApp > div > div > div {
            max-width: 100% !important; 
            padding-top: 0 !important;
            margin-top: 0 !important;
            background-color: #121212 !important;
        }
        
        /* Configurar fundo escuro para elementos principais */
        .stApp {
            background-color: #121212 !important;
        }
        
        /* Estilizar botões corretamente */
        .stButton>button {
            background-color: #FF5733 !important;
            color: white !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 0.5rem 1rem !important;
            font-weight: 500 !important;
        }
        
        .stButton>button:hover {
            background-color: #FF7F50 !important;
        }
        
        /* Garantir que o texto dentro dos botões não tenha fundo preto */
        .stButton>button span,
        .stButton>button p,
        .stButton>button div,
        .stButton button *,
        button span,
        button p,
        button div,
        button * {
            background-color: transparent !important;
            color: white !important;
            background: transparent !important;
        }
        
        /* Estilizar campos de entrada */
        input, select, textarea, .stSelectbox>div>div>select, .stTextInput>div>div>input {
            background-color: #2d2d2d !important;
            color: white !important;
            border: 1px solid #3F3F45 !important;
        }
        
        /* Configurar cores de texto */
        p, h1, h2, h3, h4, h5, h6, span, label {
            color: #f0f0f0 !important;
        }
        
        /* Esconder a barra lateral nas páginas de login e registro */
        .login-page [data-testid="stSidebar"],
        .register-page [data-testid="stSidebar"],
        [data-testid="stSidebar"] {
            display: none !important;
            width: 0 !important;
            height: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            visibility: hidden !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Adicionar um JavaScript que reforça a remoção de espaços e retângulo branco
        st.components.v1.html("""
        <script>
        // Função para remover elementos indesejados e aplicar estilos
        function fixLayout() {
            // Remover retângulo branco e outros elementos indesejados
            const elementsToRemove = [
                'header[data-testid="stHeader"]',
                'div[data-testid="stDecoration"]',
                'div[data-testid="stToolbar"]',
                'div[data-testid="stStatusWidget"]',
                'iframe.stDeployButton',
                '.stDeployButton',
                '.stDecoration',
                '.stToolbar',
                '.stStatusWidget',
                '.stHeader'
            ];
            
            elementsToRemove.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    if (el) {
                        el.style.display = 'none';
                        el.style.height = '0';
                        el.style.visibility = 'hidden';
                        el.style.opacity = '0';
                        el.style.position = 'absolute';
                        el.style.top = '-9999px';
                        el.style.left = '-9999px';
                    }
                });
            });
            
            // Aplicar fundo escuro a todos os elementos
            document.body.style.backgroundColor = '#121212';
            document.documentElement.style.backgroundColor = '#121212';
            
            // Encontrar e remover qualquer elemento branco no topo
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.backgroundColor === 'rgb(255, 255, 255)' || 
                    style.backgroundColor === '#ffffff' || 
                    style.backgroundColor === 'white') {
                    el.style.backgroundColor = '#121212';
                }
                
                // Remover margens e paddings do topo
                el.style.marginTop = '0';
                el.style.paddingTop = '0';
            });
            
            // Corrigir texto nos botões
            const buttonTexts = document.querySelectorAll('button *, .stButton button *');
            buttonTexts.forEach(el => {
                el.style.backgroundColor = 'transparent';
                el.style.background = 'transparent';
            });
        }
        
        // Executar imediatamente
        fixLayout();
        
        // Executar após carregamento completo
        window.addEventListener('load', fixLayout);
        
        // Executar periodicamente para garantir
        setInterval(fixLayout, 100);
        </script>
        """)
        // Função que remove ativamente espaços em branco
        function removeSpaces() {
            // Forçar reset de todos os elementos que possam causar espaço
            document.querySelectorAll('*').forEach(el => {
                el.style.marginTop = '0';
                el.style.paddingTop = '0';
                el.style.marginBottom = '0';
                el.style.paddingBottom = '0';
            });
            
            // Remover especificamente o cabeçalho
            const headerElement = document.querySelector('header[data-testid="stHeader"]');
            if (headerElement) headerElement.style.display = 'none';
            
            // Remover espaço entre widgets
            const widgets = document.querySelectorAll('.stButton, .stCheckbox, .stRadio, .stSelectbox, .stSlider, .stText, .stTextInput, .stTextArea');
            widgets.forEach(el => {
                el.style.marginTop = '0';
                el.style.paddingTop = '0';
                el.style.marginBottom = '0';
                el.style.paddingBottom = '0';
            });
        }
        
        // Executar a função imediatamente
        removeSpaces();
        
        // Executar novamente após o carregamento completo
        window.addEventListener('load', removeSpaces);
        
        // Executar periodicamente para garantir que novos elementos também sejam afetados
        setInterval(removeSpaces, 100);
        </script>
        """)
        
        # Mostrar barra lateral
        show_sidebar()
        
        # Roteamento de páginas
        if st.session_state.page == "landing":
            # Adicionar classe para esconder a barra lateral na landing page
            st.markdown('<div class="login-page">', unsafe_allow_html=True)
            show_landing_page()
            st.markdown('</div>', unsafe_allow_html=True)
        elif st.session_state.page == "login":
            # Esconder a barra lateral na página de login
            st.markdown('<div class="login-page">', unsafe_allow_html=True)
            # Esconder a barra lateral explicitamente
            st.markdown("""
            <style>
            [data-testid="stSidebar"] {
                display: none !important;
                width: 0px !important;
                height: 0px !important;
                min-width: 0px !important;
                max-width: 0px !important;
                visibility: hidden !important;
                position: absolute !important;
                z-index: -9999 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            show_login()
            st.markdown('</div>', unsafe_allow_html=True)
        elif st.session_state.page == "register":
            # Esconder a barra lateral na página de registro
            st.markdown('<div class="register-page">', unsafe_allow_html=True)
            show_register()
            st.markdown('</div>', unsafe_allow_html=True)
        elif st.session_state.page == "password_reset":
            show_password_reset()
        elif st.session_state.page == "dashboard":
            if st.session_state.logged_in:
                show_main_dashboard()
            else:
                st.warning("Você precisa estar logado para acessar o dashboard.")
                st.session_state.page = "login"
                st.experimental_rerun()
        elif st.session_state.page == "credits":
            if st.session_state.logged_in:
                # Implementar página de créditos
                st.title("Pacotes de Créditos")
                st.write("Escolha um pacote de créditos para continuar suas análises.")
                
                # Exibir pacotes disponíveis
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.subheader("Pacote Standard")
                    st.write("30 créditos")
                    st.write("R$ 29,90")
                    if st.button("Comprar Standard"):
                        st.session_state.selected_package = "standard"
                        st.session_state.page = "checkout"
                        st.experimental_rerun()
                
                with col2:
                    st.subheader("Pacote Pro")
                    st.write("60 créditos")
                    st.write("R$ 49,90")
                    if st.button("Comprar Pro"):
                        st.session_state.selected_package = "pro"
                        st.session_state.page = "checkout"
                        st.experimental_rerun()
                
                with col3:
                    st.subheader("Pacote Premium")
                    st.write("100 créditos")
                    st.write("R$ 79,90")
                    if st.button("Comprar Premium"):
                        st.session_state.selected_package = "premium"
                        st.session_state.page = "checkout"
                        st.experimental_rerun()
            else:
                st.warning("Você precisa estar logado para comprar créditos.")
                st.session_state.page = "login"
                st.experimental_rerun()
        elif st.session_state.page == "checkout":
            if st.session_state.logged_in:
                # Implementar página de checkout
                st.title("Checkout")
                st.write(f"Você selecionou o pacote {st.session_state.get('selected_package', 'Standard')}.")
                
                # Formulário de pagamento
                st.subheader("Informações de Pagamento")
                st.write("Esta é uma demonstração. Nenhum pagamento real será processado.")
                
                # Simular processamento de pagamento
                if st.button("Finalizar Compra"):
                    # Adicionar créditos ao usuário
                    user_manager = UserManager()
                    
                    if st.session_state.selected_package == "standard":
                        credits = 30
                        tier = "standard"
                    elif st.session_state.selected_package == "pro":
                        credits = 60
                        tier = "pro"
                    elif st.session_state.selected_package == "premium":
                        credits = 100
                        tier = "pro"
                    else:
                        credits = 30
                        tier = "standard"
                    
                    success = user_manager.add_credits(
                        st.session_state.user['email'],
                        credits,
                        tier
                    )
                    
                    if success:
                        st.success(f"{credits} créditos adicionados com sucesso!")
                        st.session_state.page = "dashboard"
                        st.experimental_rerun()
                    else:
                        st.error("Erro ao adicionar créditos. Tente novamente.")
            else:
                st.warning("Você precisa estar logado para finalizar a compra.")
                st.session_state.page = "login"
                st.experimental_rerun()
        else:
            # Página não encontrada, redirecionar para landing
            st.session_state.page = "landing"
            st.experimental_rerun()
    
    except Exception as e:
        st.error(f"Erro na aplicação: {str(e)}")
        logger.exception("Erro não tratado na aplicação")
        
        # Mostrar detalhes do erro apenas no modo de debug
        if st.session_state.debug_mode:
            st.exception(e)

# Ativar modo de debug com query parameter
if "debug" in st.query_params:
    st.session_state.debug_mode = True

# Executar aplicação
if __name__ == "__main__":
    main()
