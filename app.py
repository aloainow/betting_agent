# Standard library imports
import os
import json
import hashlib
import time
import re
import traceback
import logging
import sys
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode, quote

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("valueHunter")

# Log de diagnóstico no início
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
try:
    logger.info(f"Directory contents: {os.listdir('.')}")
except Exception as e:
    logger.error(f"Erro ao listar diretório: {str(e)}")

DATA_DIR = "data"
if "RENDER" in os.environ:
    # Em produção no Render, use um caminho padrão para montagem de disco
    DATA_DIR = "/mnt/value-hunter-data"  # Caminho padrão para discos persistentes
    
# Criar diretório de dados se não existir
os.makedirs(DATA_DIR, exist_ok=True)
logger.info(f"Diretório de dados configurado: {DATA_DIR}")
logger.info(f"Conteúdo do diretório de dados: {os.listdir(DATA_DIR) if os.path.exists(DATA_DIR) else 'Diretório não existe'}")

# Configuração do Streamlit DEVE ser o primeiro comando Streamlit
import streamlit as st
st.set_page_config(
    page_title="ValueHunter - Análise de Apostas Esportivas",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Resto dos imports
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

# Imports com tratamento de erro
try:
    from openai import OpenAI, OpenAIError
    logger.info("OpenAI importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar OpenAI: {str(e)}")
    class DummyOpenAI:
        def __init__(self, **kwargs):
            pass
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    class FakeResponse:
                        class FakeChoice:
                            class FakeMessage:
                                content = "Serviço de IA temporariamente indisponível."
                            message = FakeMessage()
                        choices = [FakeChoice()]
                    return FakeResponse()
        
    OpenAI = DummyOpenAI
    class OpenAIError(Exception):
        pass

try:
    import stripe
    logger.info("Stripe importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar Stripe: {str(e)}")
    # Dummy stripe para caso de falha no import
    class DummyStripe:
        api_key = None
        class checkout:
            class Session:
                @staticmethod
                def create(**kwargs):
                    return type('obj', (object,), {'id': 'dummy_session', 'url': '#'})
                @staticmethod
                def retrieve(session_id):
                    return type('obj', (object,), {'payment_status': 'unpaid', 'metadata': {'credits': '0', 'email': ''}})
        class error:
            class InvalidRequestError(Exception):
                pass
    stripe = DummyStripe
def configure_sidebar_visibility():
    """
    Configura a visibilidade da barra lateral:
    1. NÃO ocultamos a barra lateral globalmente
    2. Oculta apenas itens específicos (app e admin)
    """
    st.markdown("""
    <style>
        /* PRIMEIRO: Garantir que a barra lateral esteja visível nas páginas que precisam dela */
        /* Deixamos a visibilidade ser controlada por cada página individualmente */
        
        /* SEGUNDO: Ocultar apenas os itens específicos no menu */
        [data-testid="stSidebarNavItems"] a:has(p:contains("app")),
        [data-testid="stSidebarNavItems"] a:has(p:contains("admin")) {
            display: none !important;
        }
        
        /* Versão alternativa para Streamlit mais recente */
        .st-emotion-cache-16idsys a:has(p:contains("app")),
        .st-emotion-cache-16idsys a:has(p:contains("admin")) {
            display: none !important;
        }
        
        /* Verificar mais um seletor alternativo */
        div[data-testid="stSidebarNavContainer"] li:has(a[href*="app"]),
        div[data-testid="stSidebarNavContainer"] li:has(a[href*="admin"]) {
            display: none !important;
        }
        
        /* Também oculta os textos diretos contendo app/admin */
        [data-testid="stSidebarNavItems"] p:contains("app"),
        [data-testid="stSidebarNavItems"] p:contains("admin"),
        .st-emotion-cache-16idsys p:contains("app"),
        .st-emotion-cache-16idsys p:contains("admin") {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
def remove_admin_app_options():
    """Remove as opções 'app' e 'admin' do menu lateral"""
    st.markdown("""
    <style>
        /* Remove opções específicas do menu lateral */
        [data-testid="stSidebarNavItems"] .css-16idsys p:contains("app"),
        [data-testid="stSidebarNavItems"] .css-16idsys p:contains("admin") {
            display: none !important;
        }
        
        /* Para versões mais recentes do Streamlit, usar também o seletor a seguir */
        .st-emotion-cache-16idsys p:contains("app"),
        .st-emotion-cache-16idsys p:contains("admin") {
            display: none !important;
        }
        
        /* Também oculta os links para essas páginas */
        a[href*="app"], a[href*="admin"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Definição das URLs do FBref
FBREF_URLS = {
    "Premier League": {
        "stats": "https://fbref.com/en/comps/9/Premier-League-Stats",
        "fixtures": "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    },
    "La Liga": {
        "stats": "https://fbref.com/en/comps/12/La-Liga-Stats",
        "fixtures": "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"
    },
    "Serie A": {
        "stats": "https://fbref.com/en/comps/11/Serie-A-Stats",
        "fixtures": "https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures"
    },
    "Bundesliga": {
        "stats": "https://fbref.com/en/comps/20/Bundesliga-Stats",
        "fixtures": "https://fbref.com/en/comps/20/schedule/Bundesliga-Scores-and-Fixtures"
    },
    "Ligue 1": {
        "stats": "https://fbref.com/en/comps/13/Ligue-1-Stats",
        "fixtures": "https://fbref.com/en/comps/13/schedule/Ligue-1-Scores-and-Fixtures"
    },
    "Champions League": {
        "stats": "https://fbref.com/en/comps/8/Champions-League-Stats",
        "fixtures": "https://fbref.com/en/comps/8/schedule/Champions-League-Scores-and-Fixtures"
    }
}


@dataclass
class UserTier:
    name: str
    total_credits: int  # Total credits in package
    market_limit: int   # Limit of markets per analysis


# Função init_session_state deve vir ANTES da classe UserManager
def init_session_state():
    """Initialize session state variables"""
    if "page" not in st.session_state:
        st.session_state.page = "landing"  # Nova variável para controlar a página atual
        
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "email" not in st.session_state:
        st.session_state.email = None
    
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = datetime.now()
    elif (datetime.now() - st.session_state.last_activity).total_seconds() > 3600:  # 1 hora
        st.session_state.authenticated = False
        st.session_state.email = None
        st.warning("Sua sessão expirou. Por favor, faça login novamente.")
    
    # Variáveis para a página de landing
    if "show_register" not in st.session_state:
        st.session_state.show_register = False
    
    # Variáveis para o checkout integrado
    if "show_checkout" not in st.session_state:
        st.session_state.show_checkout = False
    
    if "checkout_credits" not in st.session_state:
        st.session_state.checkout_credits = 0
        
    if "checkout_amount" not in st.session_state:
        st.session_state.checkout_amount = 0
        
    if "last_stripe_session_id" not in st.session_state:
        st.session_state.last_stripe_session_id = None
    
    # Stripe test mode flag
    if "stripe_test_mode" not in st.session_state:
        st.session_state.stripe_test_mode = True
    
    # UserManager deve ser o último a ser inicializado
    if "user_manager" not in st.session_state:
        st.session_state.user_manager = UserManager()
    
    # Atualizar timestamp de última atividade
    st.session_state.last_activity = datetime.now()


def get_stripe_success_url(credits, email):
    """URL de sucesso que força refresh dos dados"""
    base_url = get_base_url()
    
    success_params = urlencode({
        'success_page': 'true',
        'credits': credits,
        'email': email,
        'session_id': '{CHECKOUT_SESSION_ID}',
        'payment_processed': 'true'  # Novo parâmetro para forçar refresh
    })
    
    full_url = f"{base_url}/?{success_params}"
    logger.info(f"URL de sucesso do Stripe configurada: {full_url}")
    return full_url


def get_stripe_cancel_url():
    """URL de cancelamento simplificada"""
    base_url = get_base_url()
    cancel_params = urlencode({'cancel_page': 'true'})
    full_url = f"{base_url}/?{cancel_params}"
    return full_url


def handle_success_page():
    """
    Função aprimorada que garante a adição de créditos,
    mesmo em caso de erros.
    """
    try:
        # Obter parâmetros da URL
        credits_param = st.query_params.get('credits', '0')
        email_param = st.query_params.get('email', '')
        session_id = st.query_params.get('session_id', '')
        
        # Converter créditos para número
        try:
            credits_value = int(credits_param)
        except:
            credits_value = 0
            
        # Log detalhado
        logger.info(f"Processando página de sucesso: email={email_param}, credits={credits_value}, session_id={session_id}")
        
        # Inicializar Stripe (garantir que temos acesso à API)
        try:
            init_stripe()
        except Exception as e:
            logger.error(f"Erro ao inicializar Stripe: {str(e)}")
        
        # Verificar pagamento de forma robusta
        is_valid, verified_credits, verified_email = verify_stripe_payment(session_id)
        
        # Log detalhado após verificação
        logger.info(f"Resultado da verificação: valid={is_valid}, credits={verified_credits}, email={verified_email}")
        
        # Variáveis para a mensagem
        final_credits = verified_credits if verified_credits > 0 else credits_value
        final_email = verified_email if verified_email else email_param
        
        # IMPORTANTE: Adicionar créditos SEMPRE, garantindo que não falhe
        credits_added = False
        
        # Primeira tentativa: usar email verificado
        if final_email and final_credits > 0:
            try:
                logger.info(f"Tentando adicionar {final_credits} créditos para {final_email}")
                
                # Verificar se o usuário existe
                if hasattr(st.session_state, 'user_manager') and final_email in st.session_state.user_manager.users:
                    # Adicionar diretamente na estrutura de dados para garantir
                    if "purchased_credits" not in st.session_state.user_manager.users[final_email]:
                        st.session_state.user_manager.users[final_email]["purchased_credits"] = 0
                    
                    st.session_state.user_manager.users[final_email]["purchased_credits"] += final_credits
                    
                    # Limpar timestamp de esgotamento se existir
                    if "paid_credits_exhausted_at" in st.session_state.user_manager.users[final_email]:
                        st.session_state.user_manager.users[final_email]["paid_credits_exhausted_at"] = None
                    
                    # Salvar alterações
                    st.session_state.user_manager._save_users()
                    
                    # Registrar sucesso
                    logger.info(f"Créditos adicionados diretamente: {final_credits} para {final_email}")
                    credits_added = True
                else:
                    # Tentar usar a função padrão
                    if st.session_state.user_manager.add_credits(final_email, final_credits):
                        logger.info(f"Créditos adicionados via função: {final_credits} para {final_email}")
                        credits_added = True
                    else:
                        logger.warning(f"Falha ao adicionar créditos via função: {final_credits} para {final_email}")
            except Exception as add_error:
                logger.error(f"Erro ao adicionar créditos para {final_email}: {str(add_error)}")
        
        # Log final
        if credits_added:
            logger.info(f"SUCESSO: {final_credits} créditos adicionados para {final_email}")
        else:
            logger.warning(f"FALHA: Não foi possível adicionar créditos para {final_email}")
        
        # HTML ultra-simples, apenas a mensagem
        success_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pagamento Aprovado</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #3F3F45;
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    padding: 20px;
                    box-sizing: border-box;
                }}
                .message-box {{
                    background-color: #4CAF50;
                    border-radius: 10px;
                    padding: 30px;
                    text-align: center;
                    max-width: 500px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }}
                .logo {{
                    background-color: #fd7014;
                    padding: 10px 20px;
                    border-radius: 8px;
                    display: inline-flex;
                    align-items: center;
                    margin-bottom: 20px;
                }}
                .logo-v {{
                    color: #3F3F45;
                    font-size: 2rem;
                    font-weight: bold;
                }}
                .logo-text {{
                    font-size: 1.7rem;
                    font-weight: bold;
                    color: white;
                }}
                h1 {{
                    font-size: 1.8rem;
                    margin: 15px 0;
                }}
                p {{
                    font-size: 1.2rem;
                    margin: 10px 0;
                }}
                .credits {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: #FFEB3B;
                    margin: 15px 0;
                }}
                .status {{
                    font-size: 1rem;
                    color: rgba(255,255,255,0.8);
                    margin-top: 20px;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            <div class="message-box">
                <div class="logo">
                    <span class="logo-v">V</span>
                    <span class="logo-text">ValueHunter</span>
                </div>
                <h1>✅ Pagamento Aprovado</h1>
                <p>Seu pagamento foi processado com sucesso.</p>
                <div class="credits">{final_credits} créditos</div>
                <p>foram adicionados à sua conta.</p>
                <p><strong>Feche esta janela para continuar.</strong></p>
                <div class="status">{f"ID: {session_id[:8]}..." if session_id else "Processado com sucesso"}</div>
            </div>
        </body>
        </html>
        """
        
        # Renderizar APENAS o HTML
        st.components.v1.html(success_html, height=400, scrolling=False)
        
        # Impedir a execução de qualquer outro código
        st.stop()
        
        return True
        
    except Exception as e:
        logger.error(f"Erro crítico na página de sucesso: {str(e)}")
        
        # Mensagem de erro ultra-simples
        error_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Processando Pagamento</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #3F3F45;
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    padding: 20px;
                    box-sizing: border-box;
                }
                .message-box {
                    background-color: #2196F3;
                    border-radius: 10px;
                    padding: 30px;
                    text-align: center;
                    max-width: 500px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                .logo {
                    background-color: #fd7014;
                    padding: 10px 20px;
                    border-radius: 8px;
                    display: inline-flex;
                    align-items: center;
                    margin-bottom: 20px;
                }
                .logo-v {
                    color: #3F3F45;
                    font-size: 2rem;
                    font-weight: bold;
                }
                .logo-text {
                    font-size: 1.7rem;
                    font-weight: bold;
                    color: white;
                }
                h1 {
                    font-size: 1.8rem;
                    margin: 15px 0;
                }
                p {
                    font-size: 1.2rem;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <div class="message-box">
                <div class="logo">
                    <span class="logo-v">V</span>
                    <span class="logo-text">ValueHunter</span>
                </div>
                <h1>Processando Pagamento</h1>
                <p>Estamos verificando seu pagamento.</p>
                <p><strong>Feche esta janela para continuar.</strong></p>
            </div>
        </body>
        </html>
        """
        
        st.components.v1.html(error_html, height=400, scrolling=False)
        st.stop()
        return False

def handle_cancel_page():
    """
    Mostra APENAS uma mensagem estática de cancelamento, sem timer.
    """
    try:
        # HTML ultra-simples
        cancel_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pagamento Não Aprovado</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #3F3F45;
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    padding: 20px;
                    box-sizing: border-box;
                }
                .message-box {
                    background-color: #FF9800;
                    border-radius: 10px;
                    padding: 30px;
                    text-align: center;
                    max-width: 500px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                .logo {
                    background-color: #fd7014;
                    padding: 10px 20px;
                    border-radius: 8px;
                    display: inline-flex;
                    align-items: center;
                    margin-bottom: 20px;
                }
                .logo-v {
                    color: #3F3F45;
                    font-size: 2rem;
                    font-weight: bold;
                }
                .logo-text {
                    font-size: 1.7rem;
                    font-weight: bold;
                    color: white;
                }
                h1 {
                    font-size: 1.8rem;
                    margin: 15px 0;
                }
                p {
                    font-size: 1.2rem;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <div class="message-box">
                <div class="logo">
                    <span class="logo-v">V</span>
                    <span class="logo-text">ValueHunter</span>
                </div>
                <h1>⚠️ Pagamento Não Aprovado</h1>
                <p>O pagamento não foi concluído.</p>
                <p><strong>Feche esta janela e tente novamente.</strong></p>
            </div>
        </body>
        </html>
        """
        
        # Renderizar APENAS o HTML
        st.components.v1.html(cancel_html, height=400, scrolling=False)
        
        # Parar a execução
        st.stop()
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao exibir página de cancelamento: {str(e)}")
        return False

def apply_global_css():
    """Aplica estilos CSS globais para toda a aplicação"""
    st.markdown("""
    <style>
        /* Removemos a regra que ocultava a barra lateral em todas as páginas */
        /* Estilo para TODOS os botões - LARANJA COM TEXTO BRANCO */
        div.stButton > button, button.css-1rs6os.edgvbvh3 {
            background-color: #fd7014 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 4px;
            font-weight: bold;
            transition: background-color 0.3s ease;
        }
        
        div.stButton > button:hover, button.css-1rs6os.edgvbvh3:hover {
            background-color: #27272a !important; /* Cinza escuro no hover */
            color: white !important;
        }
        
        /* Logo consistente */
        .logo-container {
            background-color: #fd7014;
            padding: 12px 25px !important;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
            width: fit-content;
            margin-bottom: 20px;
        }
        
        .logo-v {
            color: #3F3F45;
            font-size: 3rem !important;
            font-weight: bold;
        }
        
        .logo-text {
            font-size: 2.5rem !important;
            font-weight: bold;
            color: #FFFFFF;
        }
        
        body {
            background-color: #3F3F45;
            color: #FFFFFF;
        }
        .landing-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .hero {
            margin: 2rem 0;
            text-align: left;
        }
        .hero h1 {
            font-size: 2.8rem;
            color: #fd7014;
            margin-bottom: 1rem;
        }
        .hero p {
            font-size: 1.25rem;
            color: #FFFFFF;
            max-width: 90%;
            margin-left: 0;
        }
        .about-content {
            max-width: 90%;
            margin-left: 0;
            line-height: 1.6;
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
        .about-content h2 {
            color: #fd7014;
            margin-bottom: 0.8rem;
            text-align: left;
        }
        .footer {
            margin-top: 2rem;
            text-align: center;
            color: #b0b0b0;
        }
        .btn-container {
            display: flex;
            justify-content: flex-start;
            gap: 20px;
            margin-top: 1.5rem;
        }
        p, li {
            color: #FFFFFF !important;
        }
        
        .main .block-container {
            max-width: 95% !important; 
            padding: 1rem !important;
        }
        
        .analysis-result {
            width: 100% !important;
            max-width: 100% !important; 
            padding: 2rem !important;
            background-color: #575760;
            border-radius: 8px;
            border: 1px solid #6b6b74;
            margin: 1rem 0;
        }
        
        /* Estilo para os cartões de crédito */
        .credit-card {
            background-color: #3F3F45;
            border: 1px solid #575760;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            color: white;
            text-align: center;
        }
        .credit-title {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .credit-price {
            font-size: 42px;
            font-weight: bold;
            margin-bottom: 15px;
            color: white;
        }
        .credit-desc {
            font-size: 16px;
            color: #b0b0b0;
            margin-bottom: 15px;
        }
    </style>
    """, unsafe_allow_html=True)


# Função para exibir a logo do ValueHunter de forma consistente
def show_valuehunter_logo():
    """Exibe a logo do ValueHunter de forma consistente"""
    st.markdown(
        '<div class="logo-container"><span class="logo-v">V</span><span class="logo-text">ValueHunter</span></div>', 
        unsafe_allow_html=True
    )


def go_to_login():
    """Navigate to login page"""
    st.session_state.page = "login"
    st.session_state.show_register = False
    st.experimental_rerun()


def go_to_register():
    """Navigate to register page"""
    st.session_state.page = "register"
    st.session_state.show_register = True
    st.experimental_rerun()


def go_to_landing():
    """Navigate to landing page"""
    st.session_state.page = "landing"
    st.experimental_rerun()


def init_stripe():
    """Initialize Stripe with the API key."""
    # Melhor controle de erros e logging para inicialização do Stripe
    try:
        # Se estamos no Render, usar variáveis de ambiente diretamente
        if "RENDER" in os.environ:
            api_key = os.environ.get("STRIPE_SECRET_KEY", "")
            logger.info("Usando API key do Stripe de variáveis de ambiente no Render")
        else:
            # Tente usar secrets (para desenvolvimento local ou Streamlit Cloud)
            try:
                api_key = st.secrets.get("STRIPE_SECRET_KEY", "")
                logger.info("Usando API key do Stripe de st.secrets")
            except Exception as e:
                logger.warning(f"Erro ao tentar carregar API key do Stripe de st.secrets: {str(e)}")
                api_key = os.environ.get("STRIPE_SECRET_KEY", "")
                logger.info("Usando API key do Stripe de variáveis de ambiente locais")
        
        # Atualizar API key do Stripe
        stripe.api_key = api_key
        
        if not stripe.api_key:
            logger.error("Stripe API key não encontrada em nenhuma configuração")
            st.error("Stripe API key not found")
        else:
            logger.info(f"Stripe API key configurada com sucesso. Modo de teste: {stripe.api_key.startswith('sk_test_')}")
        
        # Para teste, isso avisa os usuários que estão no modo de teste
        st.session_state.stripe_test_mode = stripe.api_key.startswith("sk_test_")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar Stripe: {str(e)}")
        st.error(f"Erro ao inicializar Stripe. Por favor, tente novamente mais tarde.")


def get_base_url():
    """Get the base URL for the application, with special handling for Render."""
    # Check if running on Render
    if "RENDER" in os.environ:
        url = os.environ.get("RENDER_EXTERNAL_URL", "https://value-hunter.onrender.com")
        logger.info(f"Base URL no Render: {url}")
        return url
    # Check if running on Streamlit Cloud
    elif os.environ.get("IS_STREAMLIT_CLOUD"):
        url = os.environ.get("STREAMLIT_URL", "https://valuehunter.streamlit.app")
        logger.info(f"Base URL no Streamlit Cloud: {url}")
        return url
    # Local development
    else:
        try:
            url = st.get_option("server.baseUrlPath") or "http://localhost:8501"
            logger.info(f"Base URL local: {url}")
            return url
        except:
            logger.info("Usando URL local padrão: http://localhost:8501")
            return "http://localhost:8501"


def redirect_to_stripe(checkout_url):
    """Abre um popup para o checkout do Stripe"""
    # JavaScript para abrir o Stripe em um popup
    js_popup = f"""
    <script>
        // Abrir popup do Stripe centralizado
        var windowWidth = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
        var windowHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
        
        var popupWidth = 600;
        var popupHeight = 700;
        
        var left = (windowWidth - popupWidth) / 2;
        var top = (windowHeight - popupHeight) / 2;
        
        // Abrir popup centralizado com nome único para evitar múltiplas janelas
        var stripePopup = window.open(
            '{checkout_url}', 
            'stripe_checkout',
            `width=${{popupWidth}},height=${{popupHeight}},left=${{left}},top=${{top}},location=yes,toolbar=yes,scrollbars=yes`
        );
        
        // Verificar se o popup foi bloqueado
        if (!stripePopup || stripePopup.closed || typeof stripePopup.closed == 'undefined') {{
            // Popup foi bloqueado
            document.getElementById('popup-blocked').style.display = 'block';
        }} else {{
            // Popup foi aberto com sucesso
            document.getElementById('popup-success').style.display = 'block';
        }}
    </script>
    
    <div id="popup-blocked" style="display:none; padding: 15px; background-color: #ffcccc; border-radius: 5px; margin: 15px 0;">
        <h3>⚠️ Popup bloqueado!</h3>
        <p>Seu navegador bloqueou o popup de pagamento. Por favor:</p>
        <ol>
            <li>Clique no ícone de bloqueio de popup na barra de endereço</li>
            <li>Selecione "Sempre permitir popups de [seu site]"</li>
            <li>Clique no botão abaixo para tentar novamente</li>
        </ol>
        <a href="{checkout_url}" target="_blank" style="display: inline-block; padding: 10px 15px; background-color: #fd7014; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
            Abrir página de pagamento
        </a>
    </div>
    
    <div id="popup-success" style="display:none; padding: 15px; background-color: #e6ffe6; border-radius: 5px; margin: 15px 0;">
        <h3>✅ Janela de pagamento aberta!</h3>
        <p>Uma nova janela foi aberta para você concluir seu pagamento.</p>
        <p>Após completar o pagamento, a janela será fechada automaticamente e seus créditos serão adicionados.</p>
        <p>Para ver seus créditos, clique no botão "Voltar para análises" após concluir o pagamento.</p>
    </div>
    """
    
    # Exibir o JavaScript
    st.components.v1.html(js_popup, height=350)


def create_stripe_checkout_session(email, credits, amount):
    """Cria uma sessão de checkout do Stripe com manejo simplificado"""
    try:
        # Initialize Stripe
        init_stripe()
        
        # Convert amount to cents
        amount_cents = int(float(amount) * 100)
        
        # Create product description
        product_description = f"{credits} Créditos para ValueHunter"
        
        # Create success URL
        success_url = get_stripe_success_url(credits, email)
        cancel_url = get_stripe_cancel_url()
        
        logger.info(f"Criando sessão de checkout para {email}: {credits} créditos, R${amount}")
        logger.info(f"Success URL: {success_url}")
        logger.info(f"Cancel URL: {cancel_url}")
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': f'ValueHunter - {credits} Créditos',
                        'description': product_description,
                    },
                    'unit_amount': amount_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            customer_email=email,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'email': email,
                'credits': str(credits)
            }
        )
        
        # Armazenar o ID da sessão
        st.session_state.last_stripe_session_id = checkout_session.id
        logger.info(f"Sessão de checkout do Stripe criada com sucesso: {checkout_session.id}")
        
        return checkout_session
    except Exception as e:
        logger.error(f"Erro ao criar sessão de pagamento: {str(e)}")
        st.error(f"Erro ao criar sessão de pagamento: {str(e)}")
        return None


def verify_stripe_payment(session_id):
    """
    Versão aprimorada e mais tolerante da verificação de pagamento.
    Em ambiente de teste, SEMPRE considera o pagamento válido.
    """
    try:
        logger.info(f"Verificando sessão de pagamento: {session_id}")
        
        # IMPORTANTE: Em ambiente de teste, considerar QUALQUER pagamento válido
        if st.session_state.stripe_test_mode:
            try:
                # Tentar obter dados reais, mas não falhar se não conseguir
                if session_id and session_id.startswith('cs_'):
                    try:
                        session = stripe.checkout.Session.retrieve(session_id)
                        credits = int(session.metadata.get('credits', 0))
                        email = session.metadata.get('email', '')
                        logger.info(f"TESTE: Sessão válida para {email}: {credits} créditos")
                        return True, credits, email
                    except:
                        # Se falhar, pegar dados da URL (fallback)
                        credits = st.query_params.get('credits', 0)
                        email = st.query_params.get('email', '')
                        credits = int(credits) if isinstance(credits, str) else credits
                        logger.info(f"TESTE FALLBACK: Usando dados da URL: {email}, {credits} créditos")
                        return True, credits, email
            except Exception as e:
                # Sempre retornar verdadeiro em ambiente de teste, com valores de fallback
                logger.warning(f"Erro em ambiente de teste, usando fallback: {str(e)}")
                credits = st.query_params.get('credits', 30)  # Valor padrão se tudo falhar
                email = st.query_params.get('email', '')
                credits = int(credits) if isinstance(credits, str) else credits
                return True, credits, email

        # Em ambiente de produção, verificar o status do pagamento
        if session_id and session_id.startswith('cs_'):
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                
                # Extrair informações mesmo que o pagamento não esteja completo
                credits = int(session.metadata.get('credits', 0))
                email = session.metadata.get('email', '')
                
                # Verificar status de pagamento
                if session.payment_status == 'paid':
                    logger.info(f"PRODUÇÃO: Pagamento verificado com sucesso: {session_id}")
                    return True, credits, email
                else:
                    logger.warning(f"PRODUÇÃO: Pagamento não concluído: {session_id}, status: {session.payment_status}")
                    # Retornar os dados, mas indicando que o pagamento não está confirmado
                    return False, credits, email
            except Exception as e:
                logger.error(f"Erro ao verificar sessão do Stripe: {str(e)}")
                # Em caso de erro, tentar obter informações da URL
                credits = st.query_params.get('credits', 0) 
                email = st.query_params.get('email', '')
                credits = int(credits) if isinstance(credits, str) else credits
                return False, credits, email
        
        # Se não há ID de sessão ou não começa com cs_
        logger.warning(f"ID de sessão inválido: {session_id}")
        credits = st.query_params.get('credits', 0)
        email = st.query_params.get('email', '')
        credits = int(credits) if isinstance(credits, str) else credits
        return False, credits, email
        
    except Exception as e:
        logger.error(f"Erro crítico ao verificar pagamento: {str(e)}")
        # Último recurso - tentar obter da URL
        credits = st.query_params.get('credits', 0)
        email = st.query_params.get('email', '')
        credits = int(credits) if isinstance(credits, str) else credits
        return False, credits, email



def update_purchase_button(credits, amount):
    """Função comum para processar a compra de créditos"""
    logger.info(f"Botão de {credits} créditos clicado")
    
    # Criar checkout e redirecionar
    checkout_session = create_stripe_checkout_session(
        st.session_state.email, 
        credits, 
        amount
    )
    
    if checkout_session:
        logger.info(f"Checkout session criada: {checkout_session.id}")
        redirect_to_stripe(checkout_session.url)
        return True
        
    return False


def check_payment_success():
    """
    Verifica se estamos em uma página especial de sucesso/cancelamento
    ou se estamos verificando parâmetros na página principal.
    """
    # Verificar se estamos na página de sucesso do popup
    if 'success_page' in st.query_params and st.query_params.success_page == 'true':
        return handle_success_page()
        
    # Verificar se estamos na página de cancelamento do popup
    if 'cancel_page' in st.query_params and st.query_params.cancel_page == 'true':
        return handle_cancel_page()
        
    return False


def show_landing_page():
    """Display landing page with about content and login/register buttons"""
    try:
        # Esconder a barra lateral do Streamlit apenas na página inicial
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Logo e botões de navegação
        col1, col2 = st.columns([5, 1])
        with col1:
            show_valuehunter_logo()
        with col2:
            c1, c2 = st.columns([1, 1], gap="small")
            with c1:
                if st.button("Sign In", key="landing_signin_btn"):
                    go_to_login()
            with c2:
                if st.button("Sign Up", key="landing_signup_btn"):
                    go_to_register()
                
        # Conteúdo principal
        st.markdown("""
            <div class="hero">
                <h1>Maximize o Valor em Apostas Esportivas</h1>
                <p style="color: #FFFFFF;">Identifique oportunidades de valor com precisão matemática e análise de dados avançada.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Seção Sobre - SEM O RETÂNGULO CINZA
        st.markdown('<h2 style="color: #fd7014; margin-bottom: 0.8rem; text-align: left;">Sobre o ValueHunter</h2>', unsafe_allow_html=True)
        
        # Conteúdo da seção sobre
        with st.container():
            st.markdown('<p style="color: #FFFFFF;">O ValueHunter se fundamenta em um princípio crucial: "Ganhar não é sobre escolher o vencedor e sim conseguir o preço certo e depois deixar a variância fazer o trabalho dela."</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">Percebemos que o sucesso nas apostas esportivas não depende de prever corretamente cada resultado individual. Em vez disso, o ValueHunter busca identificar sistematicamente quando existe uma discrepância favorável entre o valor real, calculado pela nossa Engine e o valor implícito, oferecido pelas casas de apostas.</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">ValueHunter opera na interseção entre análise de dados e apostas esportivas. O ValueHunter trabalha para:</p>', unsafe_allow_html=True)
            
            st.markdown("""
            <ol style="color: #FFFFFF;">
                <li>Calcular probabilidades reais de eventos esportivos baseadas em modelos matemáticos e análise de dados</li>
                <li>Comparar essas probabilidades com as odds implícitas oferecidas pelas casas de apostas</li>
                <li>Identificar oportunidades onde existe uma vantagem estatística significativa</li>
            </ol>
            """, unsafe_allow_html=True)
            
            st.markdown('<p style="color: #FFFFFF;">Quando a probabilidade real calculada pelo ValueHunter é maior que a probabilidade implícita nas odds da casa, ele encontra uma "oportunidade" - uma aposta com valor positivo esperado a longo prazo.</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">Esta abordagem reconhece que, embora cada evento individual seja incerto, a matemática da expectativa estatística garante que, com disciplina e paciência suficientes, apostar consistentemente em situações com valor positivo me levará a lucros no longo prazo, desde que o agente de IA esteja calibrado adequadamente.</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">Em resumo, meu agente não tenta "vencer o jogo" prevendo resultados individuais, mas sim "vencer o mercado" identificando inconsistências nas avaliações de probabilidade, permitindo que a variância natural do esporte trabalhe a meu favor através de uma vantagem matemática consistente.</p>', unsafe_allow_html=True)
        
        # Botão centralizado
        st.markdown('<div class="btn-container"></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("FAÇA SEU TESTE GRÁTIS", use_container_width=True, key="landing_free_test_btn"):
                go_to_register()
                
        # Footer
        st.markdown("""
            <div class="footer">
                <p style="color: #b0b0b0;">© 2025 ValueHunter. Todos os direitos reservados.</p>
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao exibir página inicial: {str(e)}")
        st.error("Erro ao carregar a página. Por favor, tente novamente.")
        st.write(f"Detalhes do erro: {str(e)}")
    

def show_login():
    """Display login form"""
    try:
        # Esconder a barra lateral do Streamlit na página de login
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        
        # Botão para voltar à página inicial
        if st.button("← Voltar para a página inicial"):
            go_to_landing()
        
        # Login form
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if not email or not password:
                    st.error("Por favor, preencha todos os campos.")
                    return
                    
                try:
                    if st.session_state.user_manager.authenticate(email, password):
                        st.session_state.authenticated = True
                        st.session_state.email = email
                        st.success("Login realizado com sucesso!")
                        st.session_state.page = "main"  # Ir para a página principal
                        time.sleep(1)
                        st.experimental_rerun()
                    else:
                        st.error("Credenciais inválidas.")
                except Exception as e:
                    logger.error(f"Erro durante autenticação: {str(e)}")
                    st.error("Erro ao processar login. Por favor, tente novamente.")
        
        # Registration link
        st.markdown("---")
        st.markdown("<div style='text-align: center;'>Não tem uma conta?</div>", unsafe_allow_html=True)
        if st.button("Registre-se aqui", use_container_width=True):
            go_to_register()
    except Exception as e:
        logger.error(f"Erro ao exibir página de login: {str(e)}")
        st.error("Erro ao carregar a página de login. Por favor, tente novamente.")
        st.error(f"Detalhes: {str(e)}")  # Adicionar detalhes do erro para diagnóstico    

def show_register():
    """Display registration form"""
    try:
        # Esconder a barra lateral do Streamlit na página de registro
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        
        # Botão para voltar à página inicial
        if st.button("← Voltar para a página inicial"):
            go_to_landing()
        
        with st.form("register_form"):
            name = st.text_input("Nome")  # Novo campo
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Register")
            
            if submitted:
                # Verificar se nome foi preenchido
                if not name:
                    st.error("Por favor, informe seu nome.")
                    return
                    
                # Todo usuário novo começa automaticamente no pacote Free
                # Precisamos alterar a chamada ao register_user para incluir o nome
                # Verificar a assinatura atual do método no UserManager
                try:
                    # Tentativa adaptativa - primeiro tentar com o parâmetro nome
                    success, message = st.session_state.user_manager.register_user(email, password, name, "free")
                except TypeError:
                    # Se der erro, provavelmente a função antiga ainda não tem o parâmetro nome
                    # Vamos usar a versão antiga
                    success, message = st.session_state.user_manager.register_user(email, password, "free")
                    # E atualizar o nome depois, se for bem-sucedido
                    if success and hasattr(st.session_state.user_manager, "users") and email in st.session_state.user_manager.users:
                        st.session_state.user_manager.users[email]["name"] = name
                        st.session_state.user_manager._save_users()
                
                if success:
                    st.success(message)
                    st.info("Você foi registrado no pacote Free com 5 créditos. Você pode fazer upgrade a qualquer momento.")
                    st.session_state.page = "login"
                    st.session_state.show_register = False
                    time.sleep(2)
                    st.experimental_rerun()
                else:
                    st.error(message)
        
        st.markdown("---")
        st.markdown("<div style='text-align: center;'>Já tem uma conta?</div>", unsafe_allow_html=True)
        if st.button("Fazer login", use_container_width=True):
            go_to_login()
    except Exception as e:
        logger.error(f"Erro ao exibir página de registro: {str(e)}")
        st.error("Erro ao carregar a página de registro. Por favor, tente novamente.")
        st.error(f"Detalhes: {str(e)}")  # Adicionar detalhes do erro para diagnóstico

def show_packages_page():
    """Display credit purchase page with improved session handling"""
    try:
        # Esconder a barra lateral na página de pacotes
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        
        # Se estamos em uma página especial, mostrar apenas o conteúdo dela
        if check_payment_success():
            return
        
        # IMPORTANTE: Forçar refresh dos dados do usuário para garantir que os créditos estão atualizados
        if st.session_state.authenticated and st.session_state.email:
            try:
                # Recarregar explicitamente os dados do usuário do disco
                st.session_state.user_manager = UserManager()
                # Limpar qualquer cache que possa existir para estatísticas
                if hasattr(st.session_state, 'user_stats_cache'):
                    del st.session_state.user_stats_cache
                # Log da atualização
                logger.info(f"Dados do usuário recarregados na página de pacotes para: {st.session_state.email}")
            except Exception as e:
                logger.error(f"Erro ao atualizar dados do usuário na página de pacotes: {str(e)}")
        
        st.title("Comprar Mais Créditos")
        st.markdown("Adquira mais créditos quando precisar, sem necessidade de mudar de pacote.")
        
        # Mostrar créditos atuais para o usuário ver
        if st.session_state.authenticated and st.session_state.email:
            stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
            st.info(f"💰 Você atualmente tem **{stats['credits_remaining']} créditos** disponíveis em sua conta.")
        
        # Layout da página de compra
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="credit-card">
                <div class="credit-title">30 Créditos</div>
                <div class="credit-price">R$ 19,99</div>
                <div class="credit-desc">Pacote Standard</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar 30 Créditos", use_container_width=True, key="buy_30c"):
                update_purchase_button(30, 19.99)
        
        with col2:
            st.markdown("""
            <div class="credit-card">
                <div class="credit-title">60 Créditos</div>
                <div class="credit-price">R$ 29,99</div>
                <div class="credit-desc">Pacote Pro</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar 60 Créditos", use_container_width=True, key="buy_60c"):
                update_purchase_button(60, 29.99)
        
        # Add payment instructions
        st.markdown("""
        ### Como funciona o processo de pagamento:
        
        1. Ao clicar em "Comprar Créditos", uma nova janela será aberta para pagamento
        2. Complete seu pagamento na página do Stripe
        3. Após o pagamento, você verá uma mensagem de confirmação
        4. Seus créditos serão adicionados à sua conta imediatamente
        5. Clique em "Voltar para análises" para continuar usando o aplicativo
        
        **Nota:** Todo o processo é seguro e seus dados de pagamento são protegidos pelo Stripe
        """)
        
        # Test mode notice
        if st.session_state.stripe_test_mode:
            st.warning("""
            ⚠️ **Modo de teste ativado**
            
            Use o cartão 4242 4242 4242 4242 com qualquer data futura e CVC para simular um pagamento bem-sucedido.
            """)
        
        # Botão para voltar
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Voltar para análises", key="back_to_analysis", use_container_width=True):
            # IMPORTANTE: Forçar refresh dos dados ao voltar para análises
            try:
                # Recarregar a classe UserManager para garantir dados atualizados
                st.session_state.user_manager = UserManager()
                # Limpar qualquer cache de estatísticas
                if hasattr(st.session_state, 'user_stats_cache'):
                    del st.session_state.user_stats_cache
                logger.info(f"Dados recarregados ao voltar para análises: {st.session_state.email}")
            except Exception as e:
                logger.error(f"Erro ao recarregar dados ao voltar: {str(e)}")
                
            # Mudar a página
            st.session_state.page = "main"
            st.experimental_rerun()
    except Exception as e:
        logger.error(f"Erro ao exibir página de pacotes: {str(e)}")
        st.error("Erro ao carregar a página de pacotes. Por favor, tente novamente.")


def show_usage_stats():
    """Display usage statistics with forced refresh"""
    try:
        # IMPORTANTE: Verificar se precisamos atualizar os dados
        if not hasattr(st.session_state, 'user_stats_cache'):
            # Primeira vez carregando ou após um refresh forçado
            stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
            # Armazenar em um cache temporário na sessão
            st.session_state.user_stats_cache = stats
            logger.info(f"Estatísticas recarregadas para {st.session_state.email}")
        else:
            # Usar cache se disponível
            stats = st.session_state.user_stats_cache
        
        # Obter nome do usuário - com fallback seguro
        user_name = "Usuário"
        try:
            # Tentar obter o nome do usuário diretamente da estrutura de dados
            if hasattr(st.session_state.user_manager, "users") and st.session_state.email in st.session_state.user_manager.users:
                user_data = st.session_state.user_manager.users[st.session_state.email]
                if "name" in user_data:
                    user_name = user_data["name"]
            # Ou dos stats, se disponível
            elif "name" in stats:
                user_name = stats["name"]
        except Exception:
            pass  # Manter o fallback em caso de erro
        
        # Saudação com nome do usuário
        st.sidebar.markdown(f"### Olá, {user_name}!")
        
        st.sidebar.markdown("### Estatísticas de Uso")
        st.sidebar.markdown(f"**Créditos Restantes:** {stats['credits_remaining']}")
        
        # Add progress bar for credits
        if stats['credits_total'] > 0:
            progress = stats['credits_used'] / stats['credits_total']
            st.sidebar.progress(min(progress, 1.0))
        
        # Free tier renewal info (if applicable)
        if stats['tier'] == 'free' and stats.get('next_free_credits_time'):
            st.sidebar.info(f"⏱️ Renovação em: {stats['next_free_credits_time']}")
        elif stats['tier'] == 'free' and stats.get('free_credits_reset'):
            st.sidebar.success("✅ Créditos renovados!")
        
        # Warning for paid tiers about to be downgraded
        if stats.get('days_until_downgrade'):
            st.sidebar.warning(f"⚠️ Sem créditos há {7-stats['days_until_downgrade']} dias. Você será rebaixado para o pacote Free em {stats['days_until_downgrade']} dias se não comprar mais créditos.")
    except Exception as e:
        logger.error(f"Erro ao exibir estatísticas de uso: {str(e)}")
        st.sidebar.error("Erro ao carregar estatísticas")
def check_analysis_limits(selected_markets):
    """Check if user can perform analysis with selected markets"""
    try:
        num_markets = sum(1 for v in selected_markets.values() if v)
        stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
        
        # Check if user has enough credits
        remaining_credits = stats['credits_remaining']
        
        if num_markets > remaining_credits:
            # Special handling for Free tier
            if stats['tier'] == 'free':
                st.error(f"❌ Você esgotou seus 5 créditos gratuitos.")
                
                if stats.get('next_free_credits_time'):
                    st.info(f"⏱️ Seus créditos serão renovados em {stats['next_free_credits_time']}")
                
                st.warning("💡 Deseja continuar analisando sem esperar? Faça upgrade para um pacote pago.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Standard - 30 Créditos", key="upgrade_standard", use_container_width=True):
                        update_purchase_button(30, 19.99)
                        return False
                with col2:
                    if st.button("Pro - 60 Créditos", key="upgrade_pro", use_container_width=True):
                        update_purchase_button(60, 29.99)
                        return False
                
                return False
            else:
                # Paid tiers - offer to buy more credits
                st.warning(f"⚠️ Você tem apenas {remaining_credits} créditos restantes. Esta análise requer {num_markets} créditos.")
                
                # Show days until downgrade if applicable
                if stats.get('days_until_downgrade'):
                    st.warning(f"⚠️ Atenção: Você será rebaixado para o pacote Free em {stats['days_until_downgrade']} dias se não comprar mais créditos.")
                
                # Show purchase options
                st.info("Compre mais créditos para continuar.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("30 Créditos - R$19,99", use_container_width=True):
                        update_purchase_button(30, 19.99)
                        return False
                            
                with col2:
                    if st.button("60 Créditos - R$29,99", use_container_width=True):
                        update_purchase_button(60, 29.99)
                        return False
                
                return False
                
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar limites de análise: {str(e)}")
        st.error("Erro ao verificar limites de análise. Por favor, tente novamente.")
        return False


def show_main_dashboard():
    """Show the main dashboard with improved error handling and debug info"""
    try:
        # Garantir que a barra lateral esteja visível na página principal (dashboard)
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Iniciar com log de diagnóstico
        logger.info("Iniciando renderização do dashboard principal")
        
        # Show usage stats in sidebar
        show_usage_stats()
        
        # Sidebar layout
        st.sidebar.title("Análise de Apostas")
        
        if st.sidebar.button("Logout", key="sidebar_logout_btn"):
            st.session_state.authenticated = False
            st.session_state.email = None
            st.session_state.page = "landing"
            st.experimental_rerun()
            
        st.sidebar.markdown("---")
        
        if st.sidebar.button("🚀 Ver Pacotes de Créditos", key="sidebar_packages_button", use_container_width=True):
            st.session_state.page = "packages"
            st.experimental_rerun()
        
        # Log de progresso
        logger.info("Sidebar renderizada com sucesso")
        
        # Conteúdo principal com tratamento de erro em cada etapa
        try:
            # Logo exibida consistentemente
            show_valuehunter_logo()
            
            # Título principal
            st.title("Seleção de Times")
                
            # Sidebar Configurações
            try:
                st.sidebar.title("Configurações")
                
                # Lista de ligas disponíveis com fallback seguro
                available_leagues = list(FBREF_URLS.keys())
                if not available_leagues:
                    st.error("Erro: Nenhuma liga disponível.")
                    logger.error("FBREF_URLS está vazia")
                    return
                
                selected_league = st.sidebar.selectbox(
                    "Escolha o campeonato:",
                    available_leagues
                )
                logger.info(f"Liga selecionada: {selected_league}")
                
                # Container para status
                status_container = st.sidebar.empty()
            except Exception as sidebar_error:
                logger.error(f"Erro na configuração da sidebar: {str(sidebar_error)}")
                st.error("Erro ao carregar configurações da sidebar.")
                traceback.print_exc()
                return
                
            # Bloco try separado para carregar dados
            try:
                # Mostrar spinner enquanto carrega
                with st.spinner("Carregando dados do campeonato..."):
                    # Tentar carregar dados da liga selecionada
                    if selected_league not in FBREF_URLS:
                        st.error(f"Liga não encontrada: {selected_league}")
                        logger.error(f"Liga {selected_league} não encontrada em FBREF_URLS")
                        return
                        
                    # Obter URL das estatísticas
                    stats_url = FBREF_URLS[selected_league].get("stats")
                    if not stats_url:
                        st.error(f"URL de estatísticas não encontrada para {selected_league}")
                        logger.error(f"URL de estatísticas ausente para {selected_league}")
                        return
                        
                    # Buscar dados - com tratamento de erro explícito
                    stats_html = fetch_fbref_data(stats_url)
                    if not stats_html:
                        st.error(f"Não foi possível carregar os dados do campeonato {selected_league}")
                        logger.error(f"fetch_fbref_data retornou None para {stats_url}")
                        return
                    
                    # Parsear estatísticas dos times
                    team_stats_df = parse_team_stats(stats_html)
                    if team_stats_df is None:
                        st.error("Erro ao processar dados de estatísticas dos times")
                        logger.error("parse_team_stats retornou None")
                        return
                        
                    if 'Squad' not in team_stats_df.columns:
                        st.error("Dados incompletos: coluna 'Squad' não encontrada")
                        logger.error(f"Colunas disponíveis: {team_stats_df.columns.tolist()}")
                        return
                    
                    # Extrair lista de times
                    teams = team_stats_df['Squad'].dropna().unique().tolist()
                    if not teams:
                        st.error("Não foi possível encontrar os times do campeonato")
                        logger.error("Lista de times vazia após dropna() e unique()")
                        return
                        
                    # Mostrar mensagem de sucesso
                    status_container.success("Dados carregados com sucesso!")
                    logger.info(f"Dados carregados: {len(teams)} times encontrados")
                    
            except Exception as load_error:
                logger.error(f"Erro ao carregar dados: {str(load_error)}")
                st.error(f"Erro ao carregar dados: {str(load_error)}")
                traceback.print_exc()
                return
                
            # Bloco try separado para selecionar times
            try:
                # Seleção de times
                col1, col2 = st.columns(2)
                with col1:
                    home_team = st.selectbox("Time da Casa:", teams, key='home_team')
                with col2:
                    away_teams = [team for team in teams if team != home_team]
                    away_team = st.selectbox("Time Visitante:", away_teams, key='away_team')
                    
                logger.info(f"Times selecionados: {home_team} vs {away_team}")
                
                # Obter estatísticas do usuário
                user_stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
                
            except Exception as teams_error:
                logger.error(f"Erro ao selecionar times: {str(teams_error)}")
                st.error(f"Erro ao exibir seleção de times: {str(teams_error)}")
                traceback.print_exc()
                return
                
            # Bloco try separado para seleção de mercados
            try:
                # Seleção de mercados
                with st.expander("Mercados Disponíveis", expanded=True):
                    st.markdown("### Seleção de Mercados")
                    st.info(f"Você tem {user_stats['credits_remaining']} créditos disponíveis. Cada mercado selecionado consumirá 1 crédito.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_markets = {
                            "money_line": st.checkbox("Money Line (1X2)", value=True, key='ml'),
                            "over_under": st.checkbox("Over/Under", key='ou'),
                            "chance_dupla": st.checkbox("Chance Dupla", key='cd')
                        }
                    with col2:
                        selected_markets.update({
                            "ambos_marcam": st.checkbox("Ambos Marcam", key='btts'),
                            "escanteios": st.checkbox("Total de Escanteios", key='corners'),
                            "cartoes": st.checkbox("Total de Cartões", key='cards')
                        })

                    num_selected_markets = sum(1 for v in selected_markets.values() if v)
                    if num_selected_markets == 0:
                        st.warning("Por favor, selecione pelo menos um mercado para análise.")
                    else:
                        st.write(f"Total de créditos que serão consumidos: {num_selected_markets}")
                        
                logger.info(f"Mercados selecionados: {[k for k, v in selected_markets.items() if v]}")
                
            except Exception as markets_error:
                logger.error(f"Erro na seleção de mercados: {str(markets_error)}")
                st.error(f"Erro ao exibir mercados disponíveis: {str(markets_error)}")
                traceback.print_exc()
                return
            
            # Bloco try separado para odds
            try:
                # Odds
                odds_data = None
                if any(selected_markets.values()):
                    with st.expander("Configuração de Odds", expanded=True):
                        odds_data = get_odds_data(selected_markets)
                        
                logger.info(f"Odds configuradas: {odds_data is not None}")
                
            except Exception as odds_error:
                logger.error(f"Erro na configuração de odds: {str(odds_error)}")
                st.error(f"Erro ao configurar odds: {str(odds_error)}")
                traceback.print_exc()
                return
            
            # Botão de análise centralizado
            try:
                col1, col2, col3 = st.columns([1,1,1])
                with col2:
                    analyze_button = st.button("Analisar Partida", type="primary")
                    
                    if analyze_button:
                        if not any(selected_markets.values()):
                            st.error("Por favor, selecione pelo menos um mercado para análise.")
                            return
                            
                        if not odds_data:
                            st.error("Por favor, configure as odds para os mercados selecionados.")
                            return
                        
                        # Verificar limites de análise
                        if not check_analysis_limits(selected_markets):
                            return
                            
                        # Criar um placeholder para o status
                        status = st.empty()
                        
                        # Executar análise com tratamento de erro para cada etapa
                        try:
                            # Etapa 1: Carregar dados
                            status.info("Carregando dados dos times...")
                            if not stats_html or team_stats_df is None:
                                status.error("Falha ao carregar dados")
                                return
                                
                            # Etapa 2: Formatar prompt
                            status.info("Preparando análise...")
                            prompt = format_prompt(team_stats_df, home_team, away_team, odds_data, selected_markets)
                            if not prompt:
                                status.error("Falha ao preparar análise")
                                return
                                
                            # Etapa 3: Análise GPT
                            status.info("Realizando análise com IA...")
                            analysis = analyze_with_gpt(prompt)
                            if not analysis:
                                status.error("Falha na análise com IA")
                                return
                            
                            # Etapa 4: Mostrar resultado
                            if analysis:
                                # Limpar status
                                status.empty()
                                
                                # Exibir a análise em uma div com largura total
                                st.markdown(f'<div class="analysis-result">{analysis}</div>', unsafe_allow_html=True)
                                
                                # Registrar uso após análise bem-sucedida
                                num_markets = sum(1 for v in selected_markets.values() if v)
                                
                                # AQUI É ONDE ADICIONAMOS O NOVO CÓDIGO:
                                # Registro de uso com dados detalhados
                                analysis_data = {
                                    "league": selected_league,
                                    "home_team": home_team,
                                    "away_team": away_team,
                                    "markets_used": [k for k, v in selected_markets.items() if v]
                                }
                                success = st.session_state.user_manager.record_usage(
                                    st.session_state.email, 
                                    num_markets,
                                    analysis_data
                                )
                                
                                if success:
                                    # Mostrar mensagem de sucesso com créditos restantes
                                    updated_stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
                                    credits_after = updated_stats['credits_remaining']
                                    st.success(f"{num_markets} créditos foram consumidos. Agora você tem {credits_after} créditos.")
                                else:
                                    st.error("Não foi possível registrar o uso dos créditos. Por favor, tente novamente.")
                                    
                        except Exception as analysis_error:
                            logger.error(f"Erro durante a análise: {str(analysis_error)}")
                            status.error(f"Erro durante a análise: {str(analysis_error)}")
                            traceback.print_exc()
                            
            except Exception as button_error:
                logger.error(f"Erro no botão de análise: {str(button_error)}")
                st.error(f"Erro no botão de análise: {str(button_error)}")
                traceback.print_exc()
                
        except Exception as content_error:
            logger.error(f"Erro fatal no conteúdo principal: {str(content_error)}")
            st.error("Erro ao carregar o conteúdo principal. Detalhes no log.")
            st.error(f"Detalhes: {str(content_error)}")
            traceback.print_exc()
            
    except Exception as e:
        logger.error(f"Erro crítico ao exibir painel principal: {str(e)}")
        st.error("Erro ao carregar o painel principal. Por favor, tente novamente.")
        st.error(f"Erro: {str(e)}")
        traceback.print_exc()
        
        # Exibir informações de depuração em ambiente de teste
        if st.session_state.stripe_test_mode:
            st.warning("### Informações de Depuração (apenas em modo de teste)")
            st.write("Sessão atual:", dict([(k, v) for k, v in st.session_state.items() if k not in ['user_manager']]))
            
            # Verificar se FBREF_URLS está definido corretamente
            st.write("FBREF_URLS disponíveis:", FBREF_URLS is not None)
            st.write("Número de ligas configuradas:", len(FBREF_URLS) if FBREF_URLS else 0)

@st.cache_data
def get_admin_password():
    """Retorna a senha do administrador de forma cacheada"""
    return "sua_senha_segura_aqui"  # Altere para uma senha forte


def show_admin_page():
    """Exibe página de administrador com download e estatísticas"""
    # Header com a logo
    show_valuehunter_logo()
    st.title("Painel Administrativo")
    
    # Verificação de senha
    password = st.text_input("Senha de Administrador", type="password")
    
    if password == get_admin_password():
        st.success("Acesso autorizado!")
        
        # Seção 1: Download de dados
        st.header("Gerenciamento de Dados")
        if st.button("Baixar Dados de Usuários"):
            try:
                # Ler o arquivo de dados
                file_path = os.path.join(DATA_DIR, "user_data.json")
                with open(file_path, "r", encoding="utf-8") as f:
                    data = f.read()
                
                # Oferecer para download
                st.download_button(
                    "Baixar JSON", 
                    data, 
                    "user_data.json", 
                    "application/json"
                )
                
                # Mostrar informações do arquivo
                file_size = os.path.getsize(file_path) / 1024  # KB
                st.info(f"Tamanho do arquivo: {file_size:.2f} KB")
                
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {str(e)}")
        
        # Seção 2: Estatísticas do Sistema
        st.header("Estatísticas do Sistema")
        
        # Verificar número de usuários
        if hasattr(st.session_state, 'user_manager') and hasattr(st.session_state.user_manager, 'users'):
            users = st.session_state.user_manager.users
            num_users = len(users)
            
            # Estatísticas básicas
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total de Usuários", num_users)
            
            # Distribuição por tipo de pacote
            tier_counts = {}
            for user_email, user_data in users.items():
                tier = user_data.get('tier', 'desconhecido')
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            with col2:
                # Mostrar distribuição em texto
                tiers_text = ", ".join([f"{count} {tier}" for tier, count in tier_counts.items()])
                st.metric("Distribuição de Pacotes", tiers_text)
            
            # Lista de usuários (expandable)
            with st.expander("Lista de Usuários"):
                for email, user_data in users.items():
                    tier = user_data.get('tier', 'desconhecido')
                    name = user_data.get('name', email.split('@')[0])
                    credits = user_data.get('purchased_credits', 0)
                    
                    # Formatar como uma linha com emoji
                    tier_emoji = "🆓" if tier == "free" else "💎"
                    st.write(f"{tier_emoji} **{name}** ({email}) - Pacote: {tier.capitalize()}, Créditos: {credits}")
        else:
            st.warning("Dados de usuários não disponíveis")
        
        # Seção 3: Informações de Armazenamento
        st.header("Informações de Armazenamento")
        
        # Mostrar diretório
        st.write(f"📁 Diretório de dados: `{DATA_DIR}`")
        
        # Listar arquivos
        if os.path.exists(DATA_DIR):
            files = os.listdir(DATA_DIR)
            st.write(f"Arquivos encontrados: {len(files)}")
            
            # Tabela de arquivos
            file_data = []
            for file in files:
                file_path = os.path.join(DATA_DIR, file)
                file_size = os.path.getsize(file_path) / 1024  # KB
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_data.append({
                    "Nome": file,
                    "Tamanho (KB)": f"{file_size:.2f}",
                    "Modificado": modified_time.strftime("%Y-%m-%d %H:%M")
                })
            
            # Exibir como dataframe
            if file_data:
                st.dataframe(file_data)
        else:
            st.warning("Diretório de dados não encontrado!")
        
        # Botão para voltar
        st.markdown("---")
        if st.button("← Voltar ao Dashboard", use_container_width=True):
            st.session_state.page = "main"
            st.experimental_rerun()
    else:
        st.error("Senha incorreta")
        
        # Sessão 4: Estatísticas de Análise
        st.header("Estatísticas de Análise")
        
        if hasattr(st.session_state, 'user_manager') and hasattr(st.session_state.user_manager, 'users'):
            users = st.session_state.user_manager.users
            
            # Coletar dados de análise
            all_analyses = []
            for email, user_data in users.items():
                if "usage" in user_data and "total" in user_data["usage"]:
                    for usage in user_data["usage"]["total"]:
                        if "league" in usage:  # Verificar se contém dados detalhados
                            # Adicionar email do usuário aos dados
                            analysis = usage.copy()
                            analysis["email"] = email
                            all_analyses.append(analysis)
            
            if all_analyses:
                st.write(f"Total de análises detalhadas registradas: {len(all_analyses)}")
                
                # Estatísticas por liga
                leagues = {}
                for analysis in all_analyses:
                    league = analysis.get("league", "Desconhecido")
                    if league in leagues:
                        leagues[league] += 1
                    else:
                        leagues[league] = 1
                
                # Times mais analisados
                teams = {}
                for analysis in all_analyses:
                    home = analysis.get("home_team", "")
                    away = analysis.get("away_team", "")
                    
                    for team in [home, away]:
                        if team:
                            if team in teams:
                                teams[team] += 1
                            else:
                                teams[team] = 1
                
                # Mercados mais utilizados
                markets = {}
                for analysis in all_analyses:
                    for market in analysis.get("markets_used", []):
                        if market in markets:
                            markets[market] += 1
                        else:
                            markets[market] = 1
                
                # Exibir estatísticas em tabs
                tab1, tab2, tab3 = st.tabs(["Ligas", "Times", "Mercados"])
                
                with tab1:
                    st.subheader("Ligas Mais Analisadas")
                    if leagues:
                        # Ordenar por uso
                        sorted_leagues = dict(sorted(leagues.items(), 
                                               key=lambda x: x[1], reverse=True))
                        
                        # Criar gráfico ou lista
                        for league, count in sorted_leagues.items():
                            st.metric(league, count)
                    else:
                        st.info("Nenhuma análise de liga registrada ainda.")
                
                with tab2:
                    st.subheader("Times Mais Analisados")
                    if teams:
                        # Mostrar top 10 times
                        top_teams = dict(sorted(teams.items(), 
                                        key=lambda x: x[1], reverse=True)[:10])
                        
                        # Exibir como barras horizontais ou métricas
                        for team, count in top_teams.items():
                            st.metric(team, count)
                    else:
                        st.info("Nenhuma análise de time registrada ainda.")
                
                with tab3:
                    st.subheader("Mercados Mais Utilizados")
                    if markets:
                        market_names = {
                            "money_line": "Money Line (1X2)",
                            "over_under": "Over/Under Gols",
                            "chance_dupla": "Chance Dupla",
                            "ambos_marcam": "Ambos Marcam",
                            "escanteios": "Total de Escanteios",
                            "cartoes": "Total de Cartões"
                        }
                        
                        # Ordenar por uso
                        sorted_markets = dict(sorted(markets.items(), 
                                             key=lambda x: x[1], reverse=True))
                        
                        # Exibir métricas
                        for market_key, count in sorted_markets.items():
                            market_name = market_names.get(market_key, market_key)
                            st.metric(market_name, count)
                    else:
                        st.info("Nenhuma análise de mercado registrada ainda.")
                
                # Análises recentes
                with st.expander("Análises Recentes"):
                    # Ordenar por timestamp (mais recentes primeiro)
                    recent = sorted(all_analyses, 
                                   key=lambda x: x.get("timestamp", ""), 
                                   reverse=True)[:20]
                    
                    for idx, analysis in enumerate(recent):
                        # Formatar como cartão
                        timestamp = datetime.fromisoformat(analysis.get("timestamp", "")).strftime("%d/%m/%Y %H:%M")
                        league = analysis.get("league", "Liga desconhecida")
                        home = analysis.get("home_team", "Time casa")
                        away = analysis.get("away_team", "Time visitante")
                        markets_used = ", ".join(analysis.get("markets_used", []))
                        
                        st.markdown(f"""
                        **Análise #{idx+1}** - {timestamp}
                        - **Liga:** {league}
                        - **Partida:** {home} x {away}
                        - **Mercados:** {markets_used}
                        - **Usuário:** {analysis.get("email")}
                        ---
                        """)
            else:
                st.info("Ainda não há dados detalhados de análise disponíveis. As novas análises serão registradas com detalhes.")
        else:
            st.warning("Dados de usuários não disponíveis")    

# Atualização para função route_pages()
def route_pages():
    """Roteamento de páginas com suporte à página admin"""
    # Verificar parâmetro especial para acessar a página admin
    if 'admin' in st.query_params and st.query_params.admin == 'true':
        show_admin_page()
        return
        
    # Resto do código de roteamento existente...
    if st.session_state.page == "landing":
        show_landing_page()
    elif st.session_state.page == "login":
        show_login()
    elif st.session_state.page == "register":
        show_register()
    elif st.session_state.page == "main":
        if not st.session_state.authenticated:
            st.warning("Sua sessão expirou. Por favor, faça login novamente.")
            go_to_login()
            return
        show_main_dashboard()
    elif st.session_state.page == "packages":
        if not st.session_state.authenticated:
            st.warning("Você precisa fazer login para acessar os pacotes.")
            go_to_login()
            return
        show_packages_page()
    elif st.session_state.page == "admin":  # Nova opção
        show_admin_page()
    else:
        st.session_state.page = "landing"
        st.experimental_rerun()
class UserManager:
    def __init__(self, storage_path: str = None):
        # Caminho para armazenamento em disco persistente no Render
        if storage_path is None:
            self.storage_path = os.path.join(DATA_DIR, "user_data.json")
        else:
            self.storage_path = storage_path
            
        logger.info(f"Inicializando UserManager com arquivo de dados em: {self.storage_path}")
        
        # Garantir que o diretório existe
        os_dir = os.path.dirname(self.storage_path)
        if not os.path.exists(os_dir):
            try:
                os.makedirs(os_dir, exist_ok=True)
                logger.info(f"Diretório criado: {os_dir}")
            except Exception as e:
                logger.error(f"Erro ao criar diretório para dados de usuário: {str(e)}")
        
        self.users = self._load_users()
        
        # Define user tiers/packages
        self.tiers = {
            "free": UserTier("free", 5, float('inf')),     # 5 credits, multiple markets
            "standard": UserTier("standard", 30, float('inf')),  # 30 credits, multiple markets
            "pro": UserTier("pro", 60, float('inf'))       # 60 credits, multiple markets
        }        
    
    def _load_users(self) -> Dict:
        """Load users from JSON file with better error handling"""
        try:
            # Verificar se o arquivo existe
            if os.path.exists(self.storage_path):
                try:
                    with open(self.storage_path, 'r') as f:
                        data = json.load(f)
                        logger.info(f"Dados de usuários carregados com sucesso: {len(data)} usuários")
                        return data
                except json.JSONDecodeError as e:
                    logger.error(f"Arquivo de usuários corrompido: {str(e)}")
                    # Fazer backup do arquivo corrompido
                    if os.path.exists(self.storage_path):
                        backup_path = f"{self.storage_path}.bak.{int(time.time())}"
                        try:
                            with open(self.storage_path, 'r') as src, open(backup_path, 'w') as dst:
                                dst.write(src.read())
                            logger.info(f"Backup do arquivo corrompido criado: {backup_path}")
                        except Exception as be:
                            logger.error(f"Erro ao criar backup do arquivo corrompido: {str(be)}")
                except Exception as e:
                    logger.error(f"Erro desconhecido ao ler arquivo de usuários: {str(e)}")
            
            # Se chegamos aqui, não temos dados válidos
            logger.info("Criando nova estrutura de dados de usuários")
            return {}
        except Exception as e:
            logger.error(f"Erro não tratado em _load_users: {str(e)}")
            return {}
    
    def _save_users(self):
        """Save users to JSON file with error handling and atomic writes"""
        try:
            # Criar diretório se não existir
            directory = os.path.dirname(self.storage_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Usar escrita atômica com arquivo temporário
            temp_path = f"{self.storage_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(self.users, f, indent=2)
            
            # Renomear o arquivo temporário para o arquivo final (operação atômica)
            os.replace(temp_path, self.storage_path)
            
            logger.info(f"Dados de usuários salvos com sucesso: {len(self.users)} usuários")
            return True
                
        except Exception as e:
            logger.error(f"Erro ao salvar dados de usuários: {str(e)}")
            
            # Tentar salvar em local alternativo
            try:
                alt_path = os.path.join(DATA_DIR, "users_backup.json")
                with open(alt_path, 'w') as f:
                    json.dump(self.users, f, indent=2)
                logger.info(f"Dados de usuários salvos no local alternativo: {alt_path}")
                self.storage_path = alt_path  # Atualizar caminho para próximos salvamentos
                return True
            except Exception as alt_e:
                logger.error(f"Erro ao salvar no local alternativo: {str(alt_e)}")
                
        return False
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))
    
    def _format_tier_name(self, tier: str) -> str:
        """Format tier name for display (capitalize)"""
        tier_display = {
            "free": "Free",
            "standard": "Standard", 
            "pro": "Pro"
        }
        return tier_display.get(tier, tier.capitalize())
    
    def register_user(self, email: str, password: str, name: str = None, tier: str = "free") -> tuple:
        """Register a new user with optional name parameter"""
        try:
            if not self._validate_email(email):
                return False, "Email inválido"
            if email in self.users:
                return False, "Email já registrado"
            if len(password) < 6:
                return False, "Senha deve ter no mínimo 6 caracteres"
            if tier not in self.tiers:
                return False, "Tipo de usuário inválido"
                    
            # Se nome não for fornecido, usar parte do email como nome
            if not name:
                name = email.split('@')[0].capitalize()
                    
            self.users[email] = {
                "password": self._hash_password(password),
                "name": name,  # Adicionando o nome
                "tier": tier,
                "usage": {
                    "daily": [],
                    "total": []  # Track total usage
                },
                "purchased_credits": 0,  # Track additional purchased credits
                "free_credits_exhausted_at": None,  # Timestamp when free credits run out
                "paid_credits_exhausted_at": None,  # Timestamp when paid credits run out
                "created_at": datetime.now().isoformat()
            }
            
            save_success = self._save_users()
            if not save_success:
                logger.warning(f"Falha ao salvar dados durante registro do usuário: {email}")
                
            logger.info(f"Usuário registrado com sucesso: {email}, tier: {tier}")
            return True, "Registro realizado com sucesso"
        except Exception as e:
            logger.error(f"Erro ao registrar usuário {email}: {str(e)}")
            return False, f"Erro interno ao registrar usuário: {str(e)}"
    
    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate a user"""
        try:
            if email not in self.users:
                logger.info(f"Tentativa de login com email não registrado: {email}")
                return False
                
            # Check if the password matches
            if self.users[email]["password"] != self._hash_password(password):
                logger.info(f"Tentativa de login com senha incorreta: {email}")
                return False
                
            # Autenticação bem-sucedida
            logger.info(f"Login bem-sucedido: {email}")
            return True
        except Exception as e:
            logger.error(f"Erro durante a autenticação para {email}: {str(e)}")
            return False
    
    def add_credits(self, email: str, amount: int) -> bool:
        """Add more credits to a user account"""
        try:
            if email not in self.users:
                logger.warning(f"Tentativa de adicionar créditos para usuário inexistente: {email}")
                return False
                
            if "purchased_credits" not in self.users[email]:
                self.users[email]["purchased_credits"] = 0
                
            self.users[email]["purchased_credits"] += amount
            
            # Clear paid credits exhausted timestamp when adding credits
            if self.users[email].get("paid_credits_exhausted_at"):
                self.users[email]["paid_credits_exhausted_at"] = None
                
            save_success = self._save_users()
            if not save_success:
                logger.warning(f"Falha ao salvar dados após adicionar créditos para: {email}")
                
            logger.info(f"Créditos adicionados com sucesso: {amount} para {email}")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar créditos para {email}: {str(e)}")
            return False
    
    def get_usage_stats(self, email: str) -> Dict:
        """Get usage statistics for a user"""
        try:
            if email not in self.users:
                logger.warning(f"Tentativa de obter estatísticas para usuário inexistente: {email}")
                return {
                    "name": "Usuário",
                    "tier": "free",
                    "tier_display": "Free",
                    "credits_used": 0,
                    "credits_total": 5,
                    "credits_remaining": 5,
                    "market_limit": float('inf')
                }
                    
            user = self.users[email]
            
            # Calculate total credits used
            total_credits_used = sum(
                u["markets"] for u in user.get("usage", {}).get("total", [])
            )
            
            # Get credits based on user tier
            tier_name = user.get("tier", "free")
            if tier_name not in self.tiers:
                tier_name = "free"
                
            tier = self.tiers[tier_name]
            base_credits = tier.total_credits
            
            # Add any purchased credits
            purchased_credits = user.get("purchased_credits", 0)
            
            # Get user name (with fallback)
            user_name = user.get("name", email.split('@')[0].capitalize())
            
            # Free tier special handling
            free_credits_reset = False
            next_free_credits_time = None
            
            if user["tier"] == "free" and user.get("free_credits_exhausted_at"):
                try:
                    # Convert stored time to datetime
                    exhausted_time = datetime.fromisoformat(user["free_credits_exhausted_at"])
                    current_time = datetime.now()
                    
                    # Check if 24 hours have passed
                    if (current_time - exhausted_time).total_seconds() >= 86400:  # 24 hours in seconds
                        # Reset credits - IMPORTANTE: sempre será 5 créditos, não acumula
                        user["free_credits_exhausted_at"] = None
                        
                        # Clear usage history for free users after reset
                        user["usage"]["total"] = []
                        free_credits_reset = True
                        self._save_users()
                        
                        # Após resetar, não há créditos usados
                        total_credits_used = 0
                        logger.info(f"Créditos gratuitos renovados para: {email}")
                    else:
                        # Calculate time remaining
                        time_until_reset = exhausted_time + timedelta(days=1) - current_time
                        hours = int(time_until_reset.total_seconds() // 3600)
                        minutes = int((time_until_reset.total_seconds() % 3600) // 60)
                        next_free_credits_time = f"{hours}h {minutes}min"
                except Exception as e:
                    logger.error(f"Erro ao calcular tempo para renovação de créditos: {str(e)}")
            
            # Calculate remaining credits
            remaining_credits = max(0, base_credits + purchased_credits - total_credits_used)
            
            # Check if user is out of credits and set exhausted timestamp
            if remaining_credits == 0 and not user.get("free_credits_exhausted_at") and user["tier"] == "free":
                user["free_credits_exhausted_at"] = datetime.now().isoformat()
                self._save_users()
                logger.info(f"Créditos gratuitos esgotados para: {email}")
            
            return {
                "name": user_name,
                "tier": tier_name,
                "tier_display": self._format_tier_name(tier_name),
                "credits_used": total_credits_used,
                "credits_total": base_credits + purchased_credits,
                "credits_remaining": remaining_credits,
                "market_limit": tier.market_limit,
                "free_credits_reset": free_credits_reset,
                "next_free_credits_time": next_free_credits_time
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas para {email}: {str(e)}")
            # Retornar estatísticas padrão com nome genérico
            return {
                "name": "Usuário",
                "tier": "free",
                "tier_display": "Free",
                "credits_used": 0,
                "credits_total": 5,
                "credits_remaining": 5,
                "market_limit": float('inf')
            }
    
    def record_usage(self, email, num_markets, analysis_data=None):
        """Record usage of credits"""
        if email not in self.users:
            logger.warning(f"Tentativa de registrar uso para usuário inexistente: {email}")
            return False

        today = datetime.now().date().isoformat()
        
        # Criar registro de uso com dados detalhados
        usage = {
            "date": today,
            "markets": num_markets,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Adicionar dados de análise se fornecidos
        if analysis_data:
            usage.update({
                "league": analysis_data.get("league"),
                "home_team": analysis_data.get("home_team"),
                "away_team": analysis_data.get("away_team"),
                "markets_used": analysis_data.get("markets_used", [])
            })
        
        # Garantir que a estrutura de uso existe para o usuário
        if "usage" not in self.users[email]:
            self.users[email]["usage"] = {"daily": [], "total": []}
        
        # Adicionar o registro ao rastreamento diário e total
        self.users[email]["usage"]["daily"].append(usage)
        self.users[email]["usage"]["total"].append(usage)
        
        # Salvar alterações
        save_success = self._save_users()
        if not save_success:
            logger.warning(f"Falha ao salvar dados após registrar uso para: {email}")
            return False
            
        # Verificar créditos restantes após a atualização
        stats_after = self.get_usage_stats(email)
        credits_after = stats_after.get('credits_remaining', 0)
        
        # Se o usuário for do tier Free e esgotou os créditos, marcar o esgotamento
        if self.users[email]["tier"] == "free":
            if credits_after == 0 and not self.users[email].get("free_credits_exhausted_at"):
                self.users[email]["free_credits_exhausted_at"] = datetime.now().isoformat()
                self._save_users()
                logger.info(f"Marcando esgotamento de créditos gratuitos para: {email}")
        
        # Para usuários dos tiers Standard ou Pro
        elif self.users[email]["tier"] in ["standard", "pro"]:
            if credits_after == 0 and not self.users[email].get("paid_credits_exhausted_at"):
                self.users[email]["paid_credits_exhausted_at"] = datetime.now().isoformat()
                self._save_users()
                logger.info(f"Marcando esgotamento de créditos pagos para: {email}")
        
        logger.info(f"Uso registrado com sucesso: {num_markets} créditos para {email}")
        return True
    
    def _upgrade_to_standard(self, email: str) -> bool:
        """Upgrade a user to Standard package (for admin use)"""
        if email not in self.users:
            return False
            
        self.users[email]["tier"] = "standard"
        # Reset usage and timestamps for upgrade
        self.users[email]["free_credits_exhausted_at"] = None
        self.users[email]["paid_credits_exhausted_at"] = None
        self.users[email]["usage"]["total"] = []
        self.users[email]["purchased_credits"] = 0
        self._save_users()
        return True
        
    def _upgrade_to_pro(self, email: str) -> bool:
        """Upgrade a user to Pro package (for admin use)"""
        if email not in self.users:
            return False
            
        self.users[email]["tier"] = "pro"
        # Reset usage and timestamps for upgrade
        self.users[email]["free_credits_exhausted_at"] = None
        self.users[email]["paid_credits_exhausted_at"] = None
        self.users[email]["usage"]["total"] = []
        self.users[email]["purchased_credits"] = 0
        self._save_users()
        return True
def show_login():
    """Display login form"""
    try:
        # Esconder a barra lateral do Streamlit
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        st.title("Login")
        
        # Botão para voltar à página inicial
        if st.button("← Voltar para a página inicial"):
            go_to_landing()
        
        # Login form
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if not email or not password:
                    st.error("Por favor, preencha todos os campos.")
                    return
                    
                try:
                    if st.session_state.user_manager.authenticate(email, password):
                        st.session_state.authenticated = True
                        st.session_state.email = email
                        st.success("Login realizado com sucesso!")
                        st.session_state.page = "main"  # Ir para a página principal
                        time.sleep(1)
                        st.experimental_rerun()
                    else:
                        st.error("Credenciais inválidas.")
                except Exception as e:
                    logger.error(f"Erro durante autenticação: {str(e)}")
                    st.error("Erro ao processar login. Por favor, tente novamente.")
        
        # Registration link
        st.markdown("---")
        st.markdown("<div style='text-align: center;'>Não tem uma conta?</div>", unsafe_allow_html=True)
        if st.button("Registre-se aqui", use_container_width=True):
            go_to_register()
    except Exception as e:
        logger.error(f"Erro ao exibir página de login: {str(e)}")
        st.error("Erro ao carregar a página de login. Por favor, tente novamente.")
        st.error(f"Detalhes: {str(e)}")  # Adicionar detalhes do erro para diagnóstico    

def show_register():
    """Display simplified registration form"""
    try:
        # Esconder a barra lateral do Streamlit
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        st.title("Register")
        
        # Botão para voltar à página inicial
        if st.button("← Voltar para a página inicial"):
            go_to_landing()
        
        with st.form("register_form"):
            name = st.text_input("Nome")  # Novo campo
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Register")
            
            if submitted:
                # Verificar se nome foi preenchido
                if not name:
                    st.error("Por favor, informe seu nome.")
                    return
                    
                # Todo usuário novo começa automaticamente no pacote Free
                # Precisamos alterar a chamada ao register_user para incluir o nome
                # Verificar a assinatura atual do método no UserManager
                try:
                    # Tentativa adaptativa - primeiro tentar com o parâmetro nome
                    success, message = st.session_state.user_manager.register_user(email, password, name, "free")
                except TypeError:
                    # Se der erro, provavelmente a função antiga ainda não tem o parâmetro nome
                    # Vamos usar a versão antiga
                    success, message = st.session_state.user_manager.register_user(email, password, "free")
                    # E atualizar o nome depois, se for bem-sucedido
                    if success and hasattr(st.session_state.user_manager, "users") and email in st.session_state.user_manager.users:
                        st.session_state.user_manager.users[email]["name"] = name
                        st.session_state.user_manager._save_users()
                
                if success:
                    st.success(message)
                    st.info("Você foi registrado no pacote Free com 5 créditos. Você pode fazer upgrade a qualquer momento.")
                    st.session_state.page = "login"
                    st.session_state.show_register = False
                    time.sleep(2)
                    st.experimental_rerun()
                else:
                    st.error(message)
        
        st.markdown("---")
        st.markdown("<div style='text-align: center;'>Já tem uma conta?</div>", unsafe_allow_html=True)
        if st.button("Fazer login", use_container_width=True):
            go_to_login()
    except Exception as e:
        logger.error(f"Erro ao exibir página de registro: {str(e)}")
        st.error("Erro ao carregar a página de registro. Por favor, tente novamente.")
        st.error(f"Detalhes: {str(e)}")  # Adicionar detalhes do erro para diagnóstico
def get_odds_data(selected_markets):
    """Função para coletar e formatar os dados das odds"""
    try:
        odds_data = {}
        odds_text = []
        has_valid_odds = False

        # Money Line
        if selected_markets.get("money_line", False):
            st.markdown("### Money Line")
            col1, col2, col3 = st.columns(3)
            with col1:
                odds_data["home"] = st.number_input("Casa (@)", min_value=1.01, step=0.01, value=1.50, format="%.2f", key="ml_home")
            with col2:
                odds_data["draw"] = st.number_input("Empate (@)", min_value=1.01, step=0.01, value=4.00, format="%.2f", key="ml_draw")
            with col3:
                odds_data["away"] = st.number_input("Fora (@)", min_value=1.01, step=0.01, value=6.50, format="%.2f", key="ml_away")

            if all(odds_data.get(k, 0) > 1.01 for k in ["home", "draw", "away"]):
                has_valid_odds = True
                odds_text.append(
                    f"""Money Line:
- Casa: @{odds_data['home']:.2f} (Implícita: {(100/odds_data['home']):.1f}%)
- Empate: @{odds_data['draw']:.2f} (Implícita: {(100/odds_data['draw']):.1f}%)
- Fora: @{odds_data['away']:.2f} (Implícita: {(100/odds_data['away']):.1f}%)""")

        # Over/Under
        if selected_markets.get("over_under", False):
            st.markdown("### Over/Under")
            col1, col2, col3 = st.columns(3)
            with col1:
                odds_data["goals_line"] = st.number_input("Linha", min_value=0.5, value=2.5, step=0.5, format="%.1f", key="goals_line")
            with col2:
                odds_data["over"] = st.number_input(f"Over {odds_data.get('goals_line', 2.5)} (@)", min_value=1.01, step=0.01, value=1.85, format="%.2f", key="ou_over")
            with col3:
                odds_data["under"] = st.number_input(f"Under {odds_data.get('goals_line', 2.5)} (@)", min_value=1.01, step=0.01, value=1.95, format="%.2f", key="ou_under")

            if all(odds_data.get(k, 0) > 1.01 for k in ["over", "under"]):
                has_valid_odds = True
                odds_text.append(f"""Over/Under {odds_data['goals_line']}:
    - Over: @{odds_data['over']:.2f} (Implícita: {(100/odds_data['over']):.1f}%)
    - Under: @{odds_data['under']:.2f} (Implícita: {(100/odds_data['under']):.1f}%)""")

        # Chance Dupla
        if selected_markets.get("chance_dupla", False):
            st.markdown("### Chance Dupla")
            col1, col2, col3 = st.columns(3)
            with col1:
                odds_data["1x"] = st.number_input("1X (@)", min_value=1.01, step=0.01, value=1.20, format="%.2f", key="cd_1x")
            with col2:
                odds_data["12"] = st.number_input("12 (@)", min_value=1.01, step=0.01, value=1.30, format="%.2f", key="cd_12")
            with col3:
                odds_data["x2"] = st.number_input("X2 (@)", min_value=1.01, step=0.01, value=1.40, format="%.2f", key="cd_x2")

            if all(odds_data.get(k, 0) > 1.01 for k in ["1x", "12", "x2"]):
                has_valid_odds = True
                odds_text.append(f"""Chance Dupla:
    - 1X: @{odds_data['1x']:.2f} (Implícita: {(100/odds_data['1x']):.1f}%)
    - 12: @{odds_data['12']:.2f} (Implícita: {(100/odds_data['12']):.1f}%)
    - X2: @{odds_data['x2']:.2f} (Implícita: {(100/odds_data['x2']):.1f}%)""")

        # Ambos Marcam
        if selected_markets.get("ambos_marcam", False):
            st.markdown("### Ambos Marcam")
            col1, col2 = st.columns(2)
            with col1:
                odds_data["btts_yes"] = st.number_input("Sim (@)", min_value=1.01, step=0.01, value=1.75, format="%.2f", key="btts_yes")
            with col2:
                odds_data["btts_no"] = st.number_input("Não (@)", min_value=1.01, step=0.01, value=2.05, format="%.2f", key="btts_no")

            if all(odds_data.get(k, 0) > 1.01 for k in ["btts_yes", "btts_no"]):
                has_valid_odds = True
                odds_text.append(f"""Ambos Marcam:
    - Sim: @{odds_data['btts_yes']:.2f} (Implícita: {(100/odds_data['btts_yes']):.1f}%)
    - Não: @{odds_data['btts_no']:.2f} (Implícita: {(100/odds_data['btts_no']):.1f}%)""")

        # Total de Escanteios
        if selected_markets.get("escanteios", False):
            st.markdown("### Total de Escanteios")
            col1, col2, col3 = st.columns(3)
            with col1:
                odds_data["corners_line"] = st.number_input("Linha Escanteios", min_value=0.5, value=9.5, step=0.5, format="%.1f", key="corners_line")
            with col2:
                odds_data["corners_over"] = st.number_input("Over Escanteios (@)", min_value=1.01, step=0.01, value=1.85, format="%.2f", key="corners_over")
            with col3:
                odds_data["corners_under"] = st.number_input("Under Escanteios (@)", min_value=1.01, step=0.01, value=1.95, format="%.2f", key="corners_under")

            if all(odds_data.get(k, 0) > 1.01 for k in ["corners_over", "corners_under"]):
                has_valid_odds = True
                odds_text.append(f"""Total de Escanteios {odds_data['corners_line']}:
    - Over: @{odds_data['corners_over']:.2f} (Implícita: {(100/odds_data['corners_over']):.1f}%)
    - Under: @{odds_data['corners_under']:.2f} (Implícita: {(100/odds_data['corners_under']):.1f}%)""")

        # Total de Cartões
        if selected_markets.get("cartoes", False):
            st.markdown("### Total de Cartões")
            col1, col2, col3 = st.columns(3)
            with col1:
                odds_data["cards_line"] = st.number_input("Linha Cartões", min_value=0.5, value=3.5, step=0.5, format="%.1f", key="cards_line")
            with col2:
                odds_data["cards_over"] = st.number_input("Over Cartões (@)", min_value=1.01, step=0.01, value=1.85, format="%.2f", key="cards_over")
            with col3:
                odds_data["cards_under"] = st.number_input("Under Cartões (@)", min_value=1.01, step=0.01, value=1.95, format="%.2f", key="cards_under")

            if all(odds_data.get(k, 0) > 1.01 for k in ["cards_over", "cards_under"]):
                has_valid_odds = True
                odds_text.append(f"""Total de Cartões {odds_data['cards_line']}:
    - Over: @{odds_data['cards_over']:.2f} (Implícita: {(100/odds_data['cards_over']):.1f}%)
    - Under: @{odds_data['cards_under']:.2f} (Implícita: {(100/odds_data['cards_under']):.1f}%)""")

        if not has_valid_odds:
            return None
            
        return "\n\n".join(odds_text)
    except Exception as e:
        logger.error(f"Erro ao obter dados de odds: {str(e)}")
        return None

def get_fbref_urls():
    """Retorna o dicionário de URLs do FBref"""
    return FBREF_URLS


@st.cache_resource
def get_openai_client():
    # Melhor tratamento de erros para obtenção da API key
    try:
        # Se estamos no Render, usar variáveis de ambiente diretamente
        if "RENDER" in os.environ:
            api_key = os.environ.get("OPENAI_API_KEY", "")
            logger.info("Usando API key da OpenAI de variáveis de ambiente no Render")
        else:
            # Tente usar secrets (para desenvolvimento local ou Streamlit Cloud)
            try:
                api_key = st.secrets.get("OPENAI_API_KEY", "")
                logger.info("Usando API key da OpenAI de st.secrets")
            except Exception as e:
                logger.warning(f"Erro ao tentar carregar API key da OpenAI de st.secrets: {str(e)}")
                api_key = os.environ.get("OPENAI_API_KEY", "")
                logger.info("Usando API key da OpenAI de variáveis de ambiente locais")
        
        if not api_key:
            logger.error("OpenAI API key não encontrada em nenhuma configuração")
            return None
            
        try:
            client = OpenAI(api_key=api_key)
            logger.info("Cliente OpenAI inicializado com sucesso")
            return client
        except Exception as e:
            logger.error(f"Erro ao criar cliente OpenAI: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Erro não tratado em get_openai_client: {str(e)}")
        return None


def analyze_with_gpt(prompt):
    try:
        client = get_openai_client()
        if not client:
            st.error("Cliente OpenAI não inicializado")
            return None
            
        with st.spinner("Analisando dados e calculando probabilidades..."):
            logger.info("Enviando prompt para análise com GPT")
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um Agente Analista de Probabilidades Esportivas especializado."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                timeout=60  # Timeout de 60 segundos
            )
            logger.info("Resposta recebida do GPT com sucesso")
            return response.choices[0].message.content
    except OpenAIError as e:
        logger.error(f"Erro na API OpenAI: {str(e)}")
        st.error(f"Erro na API OpenAI: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        st.error(f"Erro inesperado: {str(e)}")
        return None


def parse_team_stats(html_content):
    """Processa os dados do time com tratamento melhorado para extrair estatísticas"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Procurar todas as tabelas que podem conter as estatísticas
        stats_table = None
        
        # Lista de IDs de tabelas conhecidos
        table_ids = [
            'stats_squads_standard_for',
            'stats_squads_standard_stats',
            'stats_squads_standard_overall',
            'stats_squads_keeper_for'
        ]
        
        # Tentar encontrar a tabela por ID
        for table_id in table_ids:
            stats_table = soup.find('table', {'id': table_id})
            if stats_table:
                logger.info(f"Tabela encontrada com ID: {table_id}")
                break
        
        # Se não encontrou por ID, procurar por conteúdo
        if not stats_table:
            all_tables = soup.find_all('table')
            for table in all_tables:
                headers = table.find_all('th')
                if headers:
                    header_text = [h.get_text(strip=True).lower() for h in headers]
                    if any(keyword in ' '.join(header_text) for keyword in ['squad', 'team', 'goals']):
                        stats_table = table
                        logger.info(f"Tabela encontrada por conteúdo (keywords)")
                        break
        
        if not stats_table:
            logger.error("Nenhuma tabela de estatísticas encontrada no HTML")
            return None
        
        # Ler a tabela com pandas
        df = pd.read_html(str(stats_table))[0]
        
        # Tratar colunas multi-índice e duplicadas
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[-1] if isinstance(col, tuple) else col for col in df.columns]
        
        # Remover colunas duplicadas mantendo a primeira ocorrência
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Limpar nomes das colunas
        df.columns = [str(col).strip() for col in df.columns]
        
        # Função para encontrar a coluna correta
        def find_column(possible_names, df_columns):
            for name in possible_names:
                # Procura exata
                if name in df_columns:
                    return name
                # Procura case-insensitive
                matches = [col for col in df_columns if str(col).strip().lower() == name.lower()]
                if matches:
                    return matches[0]
                # Procura por substring
                matches = [col for col in df_columns if name.lower() in str(col).strip().lower()]
                if matches:
                    return matches[0]
            return None

        # Mapear colunas importantes
        column_mapping = {
            'Squad': ['Squad', 'Team', 'Equipe'],
            'MP': ['MP', 'Matches', 'Jogos'],
            'Gls': ['Gls', 'Goals', 'Gols', 'G'],
            'G90': ['G90', 'Goals90', 'Gols90'],
            'xG': ['xG', 'Expected Goals'],
            'xG90': ['xG90', 'ExpectedGoals90'],
            'Poss': ['Poss', 'Possession', 'PosseBola']
        }
        
        # Encontrar e renomear colunas usando find_column
        new_columns = {}
        for new_name, possible_names in column_mapping.items():
            found_col = find_column(possible_names, df.columns)
            if found_col:
                new_columns[found_col] = new_name
        
        # Aplicar o mapeamento de colunas
        df = df.rename(columns=new_columns)
        
        # Garantir coluna Squad
        if 'Squad' not in df.columns and len(df.columns) > 0:
            df = df.rename(columns={df.columns[0]: 'Squad'})
        
        # Limpar dados
        df['Squad'] = df['Squad'].astype(str).str.strip()
        df = df.dropna(subset=['Squad'])
        df = df.drop_duplicates(subset=['Squad'])
        
        # Converter colunas numéricas com segurança
        numeric_columns = ['MP', 'Gls', 'G90', 'xG', 'xG90', 'Poss']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    # Primeiro, garantir que a coluna é uma série e não um DataFrame
                    if isinstance(df[col], pd.DataFrame):
                        df[col] = df[col].iloc[:, 0]
                    
                    # Limpar e converter para número
                    df[col] = pd.to_numeric(
                        df[col].astype(str)
                           .str.replace(',', '.')
                           .str.extract('([-+]?\d*\.?\d+)', expand=False),
                        errors='coerce'
                    )
                except Exception:
                    df[col] = np.nan
        
        # Preencher valores ausentes
        df = df.fillna('N/A')
        
        logger.info(f"Dados dos times processados com sucesso. Total de times: {len(df)}")
        return df
    
    except Exception as e:
        logger.error(f"Erro ao processar dados: {str(e)}")
        return None


def rate_limit(seconds):
    def decorator(func):
        last_called = [0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < seconds:
                time.sleep(seconds - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator


@rate_limit(1)  # 1 requisição por segundo
def fetch_fbref_data(url, force_reload=False):
    """
    Busca dados do FBref com melhor tratamento de erros e opção de forçar reload.
    """
    import random
    import time
    
    logger.info(f"Buscando dados do FBref: {url}, force_reload={force_reload}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }
    
    # Tenta usar cache para diferentes ligas
    cache_key = url.split('/')[-1]
    cache_file = os.path.join(DATA_DIR, f"cache_{cache_key.replace('-', '_')}.html")
    
    # Verificar se existe cache - sem mostrar mensagem
    if not force_reload:
        try:
            if os.path.exists(cache_file):
                file_age_seconds = time.time() - os.path.getmtime(cache_file)
                with open(cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Se o cache tiver conteúdo não vazio e não for muito antigo
                    if content and len(content) > 1000 and file_age_seconds < 86400:  # 24 horas
                        logger.info(f"Usando cache para {url} (idade: {file_age_seconds/3600:.1f} horas)")
                        return content
        except Exception as e:
            logger.warning(f"Erro ao ler do cache: {str(e)}")
    
    # Implementar retry com backoff exponencial
    max_retries = 3
    retry_delay = 5  # segundos iniciais de espera
    
    # Adicionar um delay aleatório antes da requisição para parecer mais humano
    time.sleep(1 + random.random() * 2)
    
    for attempt in range(max_retries):
        try:
            with st.spinner(f"Carregando dados do campeonato (tentativa {attempt+1}/{max_retries})..."):
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    # Verificar se a resposta tem conteúdo válido
                    if len(response.text) < 1000:
                        logger.warning(f"Resposta muito pequena ({len(response.text)} bytes): {url}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 1.5
                            continue
                    
                    # Salvar em cache para uso futuro
                    try:
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        logger.info(f"Cache salvo para {url}")
                    except Exception as e:
                        logger.warning(f"Erro ao salvar cache: {str(e)}")
                        
                    return response.text
                elif response.status_code == 429:
                    # Não mostrar mensagens de warning sobre rate limiting para o usuário
                    logger.warning(f"Rate limit atingido. Tentativa {attempt+1}/{max_retries}. Aguardando {retry_delay}s.")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Backoff exponencial
                else:
                    logger.warning(f"Erro HTTP {response.status_code}. Tentativa {attempt+1}/{max_retries}. Aguardando {retry_delay}s.")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    
        except requests.Timeout:
            logger.warning(f"Timeout na requisição. Tentativa {attempt+1}/{max_retries}. Aguardando {retry_delay}s.")
            time.sleep(retry_delay)
            retry_delay *= 1.5
        except requests.RequestException as e:
            logger.warning(f"Erro na requisição: {str(e)}. Tentativa {attempt+1}/{max_retries}. Aguardando {retry_delay}s.")
            time.sleep(retry_delay)
            retry_delay *= 1.5
        except Exception as e:
            logger.warning(f"Erro não esperado: {str(e)}. Tentativa {attempt+1}/{max_retries}. Aguardando {retry_delay}s.")
            time.sleep(retry_delay)
            retry_delay *= 1.5
    
    # Se falhou com o cache normal, tentar buscar um fallback de cache
    try:
        fallback_files = [f for f in os.listdir(DATA_DIR) if f.startswith("cache_") and f.endswith(".html")]
        if fallback_files:
            # Usar o cache mais recente de qualquer liga
            fallback_file = os.path.join(DATA_DIR, sorted(fallback_files, 
                            key=lambda x: os.path.getmtime(os.path.join(DATA_DIR, x)), 
                            reverse=True)[0])
            
            logger.warning(f"Usando cache de fallback: {fallback_file}")
            with open(fallback_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content and len(content) > 1000:
                    return content
    except Exception as e:
        logger.error(f"Erro ao tentar usar cache de fallback: {str(e)}")
    
    # Mensagem de erro simples e clara
    logger.error("Não foi possível carregar os dados do campeonato após múltiplas tentativas")
    return None    
def get_stat(stats, col, default='N/A'):
    """
    Função auxiliar para extrair estatísticas com tratamento de erro
    """
    try:
        value = stats[col]
        if pd.notna(value) and value != '':
            return value
        return default
    except:
        return default


def format_prompt(stats_df, home_team, away_team, odds_data, selected_markets):
    """Formata o prompt para o GPT-4 com os dados coletados"""
    try:
        # Extrair dados dos times
        home_stats = stats_df[stats_df['Squad'] == home_team].iloc[0]
        away_stats = stats_df[stats_df['Squad'] == away_team].iloc[0]
        
        # Calcular probabilidades reais baseadas em xG e outros dados
        def calculate_real_prob(home_xg, away_xg, home_games, away_games):
            try:
                if pd.isna(home_xg) or pd.isna(away_xg):
                    return None
                
                home_xg_per_game = home_xg / home_games if home_games > 0 else 0
                away_xg_per_game = away_xg / away_games if away_games > 0 else 0
                
                # Ajuste baseado em home advantage
                home_advantage = 1.1
                adjusted_home_xg = home_xg_per_game * home_advantage
                
                total_xg = adjusted_home_xg + away_xg_per_game
                if total_xg == 0:
                    return None
                    
                home_prob = (adjusted_home_xg / total_xg) * 100
                away_prob = (away_xg_per_game / total_xg) * 100
                draw_prob = 100 - (home_prob + away_prob)
                
                return {
                    'home': home_prob,
                    'draw': draw_prob,
                    'away': away_prob
                }
            except:
                return None

        # Formatar estatísticas dos times
        home_team_stats = f"""
  * Jogos Disputados: {get_stat(home_stats, 'MP')}
  * Gols Marcados: {get_stat(home_stats, 'Gls')}
  * Expected Goals (xG): {get_stat(home_stats, 'xG')}
  * Posse de Bola: {get_stat(home_stats, 'Poss')}%"""

        away_team_stats = f"""
  * Jogos Disputados: {get_stat(away_stats, 'MP')}
  * Gols Marcados: {get_stat(away_stats, 'Gls')}
  * Expected Goals (xG): {get_stat(away_stats, 'xG')}
  * Posse de Bola: {get_stat(away_stats, 'Poss')}%"""

        # Calcular probabilidades reais
        real_probs = calculate_real_prob(
            float(get_stat(home_stats, 'xG', 0)),
            float(get_stat(away_stats, 'xG', 0)),
            float(get_stat(home_stats, 'MP', 1)),
            float(get_stat(away_stats, 'MP', 1))
        )

        # Montar o prompt completo
        full_prompt = f"""Role: Agente Analista de Probabilidades Esportivas

KNOWLEDGE BASE INTERNO:
- Estatísticas Home Team ({home_team}):{home_team_stats}

- Estatísticas Away Team ({away_team}):{away_team_stats}

PROBABILIDADES CALCULADAS:
"""
        
        if real_probs:
            full_prompt += f"""- Vitória {home_team}: {real_probs['home']:.1f}% (Real)
- Empate: {real_probs['draw']:.1f}% (Real)
- Vitória {away_team}: {real_probs['away']:.1f}% (Real)
"""
        else:
            full_prompt += "Dados insuficientes para cálculo de probabilidades reais\n"

        # Adicionar informações sobre quais mercados foram selecionados
        selected_market_names = []
        full_prompt += "\nMERCADOS SELECIONADOS PARA ANÁLISE:\n"
        for market, selected in selected_markets.items():
            if selected:
                market_names = {
                    "money_line": "Money Line (1X2)",
                    "over_under": "Over/Under Gols",
                    "chance_dupla": "Chance Dupla",
                    "ambos_marcam": "Ambos Marcam",
                    "escanteios": "Total de Escanteios",
                    "cartoes": "Total de Cartões"
                }
                market_name = market_names.get(market, market)
                selected_market_names.append(market_name)
                full_prompt += f"- {market_name}\n"

        # Instrução muito clara sobre o formato de saída
        full_prompt += f"""
INSTRUÇÕES ESPECIAIS: VOCÊ DEVE CALCULAR PROBABILIDADES REAIS PARA TODOS OS MERCADOS LISTADOS ACIMA, não apenas para o Money Line. Use os dados disponíveis e sua expertise para estimar probabilidades reais para CADA mercado selecionado.

[SAÍDA OBRIGATÓRIA]

# Análise da Partida
## {home_team} x {away_team}

# Análise de Mercados Disponíveis:
{odds_data}

# Probabilidades Calculadas (REAL vs IMPLÍCITA):
[IMPORTANTE - Para cada um dos mercados abaixo, você DEVE mostrar a probabilidade REAL calculada, bem como a probabilidade IMPLÍCITA nas odds:]
{chr(10).join([f"- {name}" for name in selected_market_names])}

# Oportunidades Identificadas (Edges >3%):
[Listagem detalhada de cada mercado selecionado, indicando explicitamente se há edge ou não para cada opção.]

# Nível de Confiança Geral: [Baixo/Médio/Alto]
[Breve explicação da sua confiança na análise]
"""
        return full_prompt

    except Exception as e:
        logger.error(f"Erro ao formatar prompt: {str(e)}")
        return None


def apply_custom_css():
    apply_global_css()


def main():
    try:
        # Verificar se precisamos fechar a janela atual
        if 'close_window' in st.query_params and st.query_params.close_window == 'true':
            st.components.v1.html("""
                <script>
                    window.opener && window.opener.postMessage('payment_complete', '*');
                    window.close();
                </script>
            """, height=0)
            st.success("Pagamento concluído! Você pode fechar esta janela.")
            return
            
        # Initialize session state
        init_session_state()

        # Configurar visibilidade da barra lateral - ADICIONE ESTA LINHA
        configure_sidebar_visibility()
        
        # Apply global CSS
        apply_global_css()
        
        # Initialize Stripe
        init_stripe()
        
        # Check for payment from popup
        popup_payment = False
        if 'check_payment' in st.query_params and st.query_params.check_payment == 'true':
            popup_payment = True
        
        # Handle page routing
        if popup_payment and st.session_state.authenticated:
            check_payment_success()
            
        # Regular payment callback check
        payment_result = check_payment_success()
        
        # Stripe error handling
        handle_stripe_errors()
        
        # Roteamento de páginas
        route_pages()
        
    except Exception as e:
        logger.error(f"Erro geral na aplicação: {str(e)}")
        traceback.print_exc()

def handle_stripe_errors():
    if 'error' in st.query_params:
        st.error("Erro no processamento do pagamento...")
        st.query_params.clear()


def route_pages():
    if st.session_state.page == "landing":
        show_landing_page()
    elif st.session_state.page == "login":
        show_login()
    elif st.session_state.page == "register":
        show_register()
    elif st.session_state.page == "main":
        if not st.session_state.authenticated:
            st.warning("Sua sessão expirou. Por favor, faça login novamente.")
            go_to_login()
            return
        show_main_dashboard()
    elif st.session_state.page == "packages":
        if not st.session_state.authenticated:
            st.warning("Você precisa fazer login para acessar os pacotes.")
            go_to_login()
            return
        show_packages_page()
    else:
        st.session_state.page = "landing"
        st.experimental_rerun()


# Executar a aplicação
if __name__ == "__main__":
    try:
        logger.info("Iniciando aplicação ValueHunter")
        main()
    except Exception as e:
        logger.critical(f"Erro fatal na aplicação: {str(e)}")
        st.error("Ocorreu um erro inesperado. Por favor, recarregue a página e tente novamente.")
        st.error(f"Detalhes do erro: {str(e)}")
