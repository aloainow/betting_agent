import os
import sys
import logging
import streamlit as st
import time
from datetime import datetime, timedelta
import json
import base64
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("valueHunter")

# Importar módulos do projeto
from utils.core import (
    init_session_state, 
    go_to_login, 
    go_to_register, 
    go_to_landing,
    show_valuehunter_logo,
    insert_favicon,
    hide_streamlit_menu,
    hide_app_admin_items,
    apply_global_css,
    configure_sidebar_visibility
)

# Inicializar estado da sessão
init_session_state()

# Verificar se o usuário está autenticado
def check_authentication():
    """Verifica se o usuário está autenticado e redireciona se necessário"""
    if not st.session_state.authenticated and st.session_state.page not in ["landing", "login", "register", "password_reset"]:
        st.session_state.page = "login"
        st.experimental_rerun()

# Função para mostrar a barra lateral
def show_sidebar():
    """Exibe a barra lateral com opções de navegação"""
    with st.sidebar:
        # Logo no topo da barra lateral
        show_valuehunter_logo()
        
        st.markdown("---")
        
        # Mostrar informações do usuário se autenticado
        if st.session_state.authenticated and st.session_state.email:
            # Obter dados do usuário
            user_data = st.session_state.user_manager.get_user_data(st.session_state.email)
            if user_data:
                credits = user_data.get("credits", 0)
                st.markdown(f"### Olá, {st.session_state.email.split('@')[0]}!")
                st.markdown(f"**Créditos Restantes:** {credits}")
                
                # Barra de progresso para créditos
                progress = min(credits / 100, 1.0)  # Máximo de 100 créditos para a barra
                st.progress(progress)
                
                st.markdown("---")
            
            # Botões de navegação
            if st.button("Ver Pacotes de Créditos", key="sidebar_credits"):
                st.session_state.page = "packages"
                st.experimental_rerun()
                
            if st.button("Dashboard", key="sidebar_dashboard"):
                st.session_state.page = "dashboard"
                st.experimental_rerun()
                
            if st.button("Sair", key="sidebar_logout"):
                st.session_state.authenticated = False
                st.session_state.email = None
                st.session_state.page = "landing"
                st.experimental_rerun()
        else:
            # Opções para usuários não autenticados
            if st.button("Início", key="sidebar_home"):
                st.session_state.page = "landing"
                st.experimental_rerun()
                
            if st.button("Entrar", key="sidebar_login"):
                st.session_state.page = "login"
                st.experimental_rerun()
                
            if st.button("Registrar", key="sidebar_register"):
                st.session_state.page = "register"
                st.experimental_rerun()

# Função para aplicar tema escuro
def apply_dark_theme():
    """Aplica o tema escuro à aplicação"""
    st.markdown("""
    <style>
    /* Tema escuro para toda a aplicação */
    body {
        color: white;
        background-color: #121212;
    }
    
    /* Cores para elementos específicos */
    .stApp {
        background-color: #121212;
    }
    
    /* Estilo para botões */
    div.stButton > button {
        background-color: #fd7014;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        font-weight: 500;
    }
    
    div.stButton > button:hover {
        background-color: #ff8c3a;
    }
    
    /* Estilo para texto */
    h1, h2, h3, h4, h5, h6, p, li {
        color: white;
    }
    
    /* Estilo para links */
    a {
        color: #fd7014;
    }
    
    a:hover {
        color: #ff8c3a;
    }
    
    /* Estilo para inputs */
    input, textarea, select {
        background-color: #2d2d2d;
        color: white;
        border: 1px solid #3F3F45;
    }
    
    /* Estilo para widgets */
    .stSlider, .stCheckbox, .stRadio, .stSelectbox, .stTextInput, .stTextArea {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 0.3rem;
    }
    
    /* Remover elementos de UI do Streamlit */
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    /* Estilo para a barra lateral */
    [data-testid="stSidebar"] {
        background-color: #1e1e1e;
        border-right: 1px solid #3F3F45;
    }
    
    /* Estilo para o logo */
    .logo-container {
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Função para mostrar a página de landing
def show_landing_page():
    """Exibe a página inicial (landing page)"""
    from pages.landing import show_landing
    show_landing()

# Função para mostrar a página de login
def show_login():
    """Exibe a página de login"""
    from pages.auth import show_login_page
    show_login_page()

# Função para mostrar a página de registro
def show_register():
    """Exibe a página de registro"""
    from pages.auth import show_register_page
    show_register_page()

# Função para mostrar a página de redefinição de senha
def show_password_reset():
    """Exibe a página de redefinição de senha"""
    from pages.auth import show_password_reset_page
    show_password_reset_page()

# Função para mostrar a página de pacotes de créditos
def show_packages():
    """Exibe a página de pacotes de créditos"""
    from pages.packages import show_packages_page
    show_packages_page()

# Função principal
def main():
    """Função principal da aplicação"""
    # Inserir favicon
    insert_favicon()
    
    # Verificar autenticação
    check_authentication()
    
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
                from pages.dashboard import show_main_dashboard
                show_main_dashboard()
        elif st.session_state.page == "packages":
            show_packages()
        else:
            # Página não encontrada, redirecionar para landing
            st.session_state.page = "landing"
            st.experimental_rerun()
    
    except Exception as e:
        st.error(f"Erro na aplicação: {str(e)}")
        logger.error(f"Erro na aplicação: {str(e)}", exc_info=True)

# Ativar modo de debug com query parameter
if "debug" in st.query_params:
    st.session_state.debug_mode = True

# Executar a aplicação
if __name__ == "__main__":
    main()
