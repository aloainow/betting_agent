# Solução mínima para resolver o problema de strings triplas
# Substitua TODO o arquivo app.py por este código

import os
import logging
import sys
import streamlit as st
import time
from datetime import datetime
import base64

# Configuração básica da página
st.set_page_config(
    page_title="ValueHunter",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("valueHunter")

# Ocultar elementos de navegação com CSS simples
st.markdown(
    "<style>"
    "[data-testid='stSidebarNavItems'] {display: none !important;}"
    "header[data-testid='stHeader'], footer, #MainMenu {display: none !important;}"
    "</style>",
    unsafe_allow_html=True
)

# Importar módulos de utilidade
try:
    from utils.core import (
        DATA_DIR, init_session_state, show_valuehunter_logo, 
        init_stripe, check_payment_success, handle_stripe_errors
    )
    from utils.data import UserManager
    from pages.dashboard import show_main_dashboard
    from pages.landing import show_landing_page
    from pages.auth import show_login, show_register, show_verification
    from pages.packages import show_packages_page
except Exception as e:
    st.error(f"Erro ao importar módulos: {str(e)}")
    logger.error(f"Erro ao importar módulos: {str(e)}")

# Funções de navegação
def go_to_login():
    st.session_state.page = "login"
    st.session_state.show_register = False
    st.experimental_rerun()

def go_to_register():
    st.session_state.page = "register"
    st.session_state.show_register = True
    st.experimental_rerun()

def go_to_landing():
    st.session_state.page = "landing"
    st.experimental_rerun()

# Inicialização básica
try:
    # Criar diretório de dados
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Inicializar estado da sessão
    init_session_state()
    
    # Inicializar Stripe
    init_stripe()
    
    # Verificar pagamentos
    check_payment_success()
    handle_stripe_errors()
except Exception as e:
    st.error(f"Erro de inicialização: {str(e)}")
    logger.error(f"Erro de inicialização: {str(e)}")

# Roteamento básico
try:
    if "page" in st.session_state:
        page = st.session_state.page
        
        if page == "landing":
            show_landing_page()
        elif page == "login":
            show_login()
        elif page == "register":
            show_register()
        elif page == "verification":
            show_verification()
        elif page == "main":
            if st.session_state.authenticated:
                show_main_dashboard()
            else:
                go_to_login()
        elif page == "packages":
            if st.session_state.authenticated:
                show_packages_page()
            else:
                go_to_login()
        else:
            # Página desconhecida, voltar para landing
            go_to_landing()
    else:
        # Estado não inicializado
        st.session_state.page = "landing"
        st.experimental_rerun()
except Exception as e:
    st.error(f"Erro no roteamento: {str(e)}")
    logger.error(f"Erro no roteamento: {str(e)}")
    
    # Mostrar informações de debug em caso de erro
    st.write("Informações de depuração:")
    st.write(f"Python: {sys.version}")
    st.write(f"Diretório: {os.getcwd()}")
    try:
        st.write(f"Arquivos: {os.listdir('.')}")
    except:
        st.write("Não foi possível listar arquivos")
