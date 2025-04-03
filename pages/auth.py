# pages/auth.py - Solução Completa em Streamlit
import streamlit as st
import time
import logging
from utils.core import show_valuehunter_logo, go_to_landing, go_to_login, go_to_register

# Configuração de logging
logger = logging.getLogger("valueHunter.auth")

def show_login():
    """Display login form using native Streamlit components"""
    try:
        # Configurar página
        st.set_page_config(
            page_title="ValueHunter - Login",
            page_icon="💼",
            layout="centered",
            initial_sidebar_state="collapsed"
        )
        
        # Esconder a barra lateral e outros elementos do Streamlit
        hide_elements = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none !important;}
        
        /* Ajustar o container principal */
        .block-container {
            max-width: 800px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Fundo com gradiente */
        .stApp {
            background: linear-gradient(135deg, #1a1a1a 0%, #1a1a1a 50%, #fd7014 50%, #fd7014 100%);
        }
        
        /* Estilizar elementos importantes */
        div[data-testid="stVerticalBlock"] > div {
            background-color: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            max-width: 450px;
            margin: 0 auto;
        }
        
        h1 {
            color: #333;
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #fd7014;
            width: fit-content;
        }
        
        /* Botões estilizados */
        .stButton button {
            background-color: #fd7014;
            color: white;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            border: none;
            width: 100%;
        }
        
        .stButton button:hover {
            background-color: #e06000;
        }
        
        .secondary-button button {
            background-color: #252525;
            color: white;
        }
        
        .secondary-button button:hover {
            background-color: #333;
        }
        
        /* Estilizar inputs */
        .stTextInput input, .stPasswordInput input {
            border-radius: 6px;
            border: 1px solid #ccc;
            padding: 0.5rem;
        }
        
        /* Centralizar texto */
        .center-text {
            text-align: center;
        }
        
        /* Esqueceu senha link */
        .forgot-password {
            text-align: center;
            margin-top: 1rem;
        }
        
        .forgot-password a {
            color: #fd7014;
            text-decoration: none;
            font-weight: 500;
        }
        
        /* Logo estilizado */
        .value-hunter-logo {
            text-align: center;
            margin-bottom: 2rem;
            font-size: 1.8rem;
            font-weight: bold;
        }
        
        .value-hunter-logo .value {
            color: #333;
        }
        
        .value-hunter-logo .hunter {
            color: #fd7014;
        }
        
        /* Separador com margem */
        hr.custom-divider {
            margin: 2rem 0;
            border-top: 1px solid #eee;
            border-bottom: none;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(hide_elements, unsafe_allow_html=True)
        
        # Logo
        st.markdown('<div class="value-hunter-logo"><span class="value">Value</span><span class="hunter">Hunter</span></div>', unsafe_allow_html=True)
        
        # Título
        st.markdown('<h1>Faça o seu login</h1>', unsafe_allow_html=True)
        
        # Formulário - usando componentes nativos
        with st.form("login_form"):
            email = st.text_input("Seu e-mail")
            password = st.text_input("Sua senha", type="password")
            remember = st.checkbox("Lembrar-me")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button("ENTRAR", use_container_width=True)
        
        # Esqueceu senha link
        st.markdown('<div class="forgot-password"><a href="#">Esqueceu sua senha?</a></div>', unsafe_allow_html=True)
        
        # Separador
        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
        
        # Não tem conta
        st.markdown('<div class="center-text">Não tem uma conta?</div>', unsafe_allow_html=True)
        
        # Botão Registre-se
        st.markdown('<div class="secondary-button">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("REGISTRE-SE AQUI", use_container_width=True):
                st.session_state.page = "register"
                st.experimental_rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Processar submissão do formulário
        if submitted:
            if not email or not password:
                st.error("Por favor, preencha todos os campos.")
                return
                
            try:
                if st.session_state.user_manager.authenticate(email, password):
                    st.session_state.authenticated = True
                    st.session_state.email = email
                    st.success("Login realizado com sucesso!")
                    st.session_state.page = "main"
                    time.sleep(1)
                    st.experimental_rerun()
                else:
                    st.error("Credenciais inválidas.")
            except Exception as e:
                logger.error(f"Erro durante autenticação: {str(e)}")
                st.error("Erro ao processar login. Por favor, tente novamente.")
    except Exception as e:
        logger.error(f"Erro ao exibir página de login: {str(e)}")
        st.error("Erro ao carregar a página de login. Por favor, tente novamente.")
        st.error(f"Detalhes: {str(e)}")

def show_register():
    """Display registration form using native Streamlit components"""
    try:
        # Configurar página
        st.set_page_config(
            page_title="ValueHunter - Registro",
            page_icon="💼",
            layout="centered",
            initial_sidebar_state="collapsed"
        )
        
        # Esconder a barra lateral e outros elementos do Streamlit
        hide_elements = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none !important;}
        
        /* Ajustar o container principal */
        .block-container {
            max-width: 800px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Fundo com gradiente */
        .stApp {
            background: linear-gradient(135deg, #1a1a1a 0%, #1a1a1a 50%, #fd7014 50%, #fd7014 100%);
        }
        
        /* Estilizar elementos importantes */
        div[data-testid="stVerticalBlock"] > div {
            background-color: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            max-width: 450px;
            margin: 0 auto;
        }
        
        h1 {
            color: #333;
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #fd7014;
            width: fit-content;
        }
        
        /* Botões estilizados */
        .stButton button {
            background-color: #fd7014;
            color: white;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            border: none;
            width: 100%;
        }
        
        .stButton button:hover {
            background-color: #e06000;
        }
        
        .secondary-button button {
            background-color: #252525;
            color: white;
        }
        
        .secondary-button button:hover {
            background-color: #333;
        }
        
        /* Estilizar inputs */
        .stTextInput input, .stPasswordInput input {
            border-radius: 6px;
            border: 1px solid #ccc;
            padding: 0.5rem;
        }
        
        /* Centralizar texto */
        .center-text {
            text-align: center;
        }
        
        /* Logo estilizado */
        .value-hunter-logo {
            text-align: center;
            margin-bottom: 2rem;
            font-size: 1.8rem;
            font-weight: bold;
        }
        
        .value-hunter-logo .value {
            color: #333;
        }
        
        .value-hunter-logo .hunter {
            color: #fd7014;
        }
        
        /* Separador com margem */
        hr.custom-divider {
            margin: 2rem 0;
            border-top: 1px solid #eee;
            border-bottom: none;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(hide_elements, unsafe_allow_html=True)
        
        # Logo
        st.markdown('<div class="value-hunter-logo"><span class="value">Value</span><span class="hunter">Hunter</span></div>', unsafe_allow_html=True)
        
        # Título
        st.markdown('<h1>Criar uma conta</h1>', unsafe_allow_html=True)
        
        # Formulário - usando componentes nativos
        with st.form("register_form"):
            name = st.text_input("Nome completo")
            email = st.text_input("Seu e-mail")
            password = st.text_input("Sua senha", type="password")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button("REGISTRAR", use_container_width=True)
        
        # Separador
        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
        
        # Já tem conta
        st.markdown('<div class="center-text">Já tem uma conta?</div>', unsafe_allow_html=True)
        
        # Botão Login
        st.markdown('<div class="secondary-button">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("FAÇA LOGIN", use_container_width=True):
                st.session_state.page = "login"
                st.experimental_rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Processar submissão do formulário
        if submitted:
            if not name or not email or not password:
                st.error("Por favor, preencha todos os campos.")
                return
                
            try:
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
            except Exception as e:
                logger.error(f"Erro durante registro: {str(e)}")
                st.error("Erro ao processar registro. Por favor, tente novamente.")
    except Exception as e:
        logger.error(f"Erro ao exibir página de registro: {str(e)}")
        st.error("Erro ao carregar a página de registro. Por favor, tente novamente.")
        st.error(f"Detalhes: {str(e)}")
