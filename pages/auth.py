# pages/auth.py - Redesign da Tela de Login
import streamlit as st
import time
import logging
from utils.core import show_valuehunter_logo, go_to_landing, go_to_login, go_to_register

# Configuração de logging
logger = logging.getLogger("valueHunter.auth")

def apply_modern_login_style():
    """Aplica um estilo moderno e limpo para a tela de login"""
    st.markdown("""
    <style>
    /* Estilo geral da página */
    .main .block-container {
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Fundo com gradiente */
    .login-background {
        background: linear-gradient(135deg, #1a1a1a 0%, #1a1a1a 50%, #fd7014 50%, #fd7014 100%);
        width: 100%;
        min-height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    /* Container do card de login */
    .login-container {
        width: 90%;
        max-width: 400px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        padding: 40px 30px;
        position: relative;
    }
    
    /* Estilo para o título de login */
    .login-title {
        color: #333;
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 25px;
        position: relative;
    }
    
    /* Linha laranja abaixo do título */
    .login-title:after {
        content: '';
        position: absolute;
        left: 0;
        bottom: -8px;
        height: 3px;
        width: 50px;
        background-color: #fd7014;
    }
    
    /* Estilo para labels */
    .login-label {
        color: #555;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 8px;
        display: block;
    }
    
    /* Estilo para campos de input */
    .login-input {
        width: 100%;
        padding: 12px 15px;
        border: 1px solid #ddd;
        border-radius: 8px;
        background-color: #f5f5f5;
        margin-bottom: 20px;
        font-size: 14px;
    }
    
    /* Botão principal */
    .login-button {
        width: 100%;
        padding: 12px;
        background-color: #fd7014;
        color: white;
        border: none;
        border-radius: 30px;
        font-weight: 600;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s;
        text-align: center;
        display: block;
        margin-top: 10px;
    }
    
    .login-button:hover {
        background-color: #e06000;
    }
    
    /* Link para esqueceu senha e registro */
    .login-link {
        text-align: center;
        margin-top: 20px;
        font-size: 14px;
        color: #666;
    }
    
    .login-link a {
        color: #0096c7;
        text-decoration: none;
    }
    
    /* Botão secundário para registro */
    .register-button {
        width: 100%;
        padding: 12px;
        background-color: #252525;
        color: white;
        border: none;
        border-radius: 30px;
        font-weight: 500;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s;
        text-align: center;
        display: block;
        margin-top: 10px;
    }
    
    .register-button:hover {
        background-color: #333;
    }
    
    /* Esconder elementos de controle do Streamlit */
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    /* Ajustes para formulários do Streamlit */
    div[data-testid="stForm"] {
        background: transparent !important;
        padding: 0 !important;
        border: none !important;
    }
    
    div[data-baseweb="input"] {
        background-color: #f5f5f5 !important;
        border-radius: 8px !important;
        margin-bottom: 15px !important;
    }
    
    div[data-testid="stTextInput"] label {
        font-size: 14px !important;
        color: #555 !important;
        font-weight: 500 !important;
    }
    
    /* Esconder o botão padrão do Streamlit e substitui-lo por CSS */
    div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
        display: none;
    }
    
    /* Ajustes responsivos */
    @media (max-width: 767px) {
        .login-container {
            width: 95%;
            padding: 30px 20px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def show_login():
    """Display modern login form"""
    try:
        # Esconder a barra lateral do Streamlit
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Aplicar o estilo moderno de login
        apply_modern_login_style()
        
        # Criar página de login com HTML personalizado
        st.markdown("""
        <div class="login-background">
            <div class="login-container">
                <h2 class="login-title">Faça o seu login</h2>
                <!-- O formulário será inserido aqui pelo Streamlit -->
        """, unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Seu e-mail")
            password = st.text_input("Sua senha", type="password")
            
            # Checkbox para lembrar
            st.checkbox("Lembrar-me")
            
            # Botão invisível do formulário (CSS vai escondê-lo)
            submitted = st.form_submit_button("ENTRAR")
        
        # Botão personalizado fora do formulário (para acionar o formulário via JS)
        st.markdown("""
        <button class="login-button" onclick="document.querySelector('div[data-testid=\\"stForm\\"] button[kind=\\"primaryFormSubmit\\"]').click();">
            ENTRAR
        </button>
        
        <div class="login-link">
            Esqueceu sua senha? <a href="#">Clique aqui!</a>
        </div>
        
        <div class="login-link" style="margin-top: 25px;">
            Não tem uma conta?
        </div>
        """, unsafe_allow_html=True)
        
        # Botão de registro
        st.markdown("""
        <button class="register-button" onclick="window.location.href='?page=register';">
            REGISTRE-SE AQUI
        </button>
        """, unsafe_allow_html=True)
        
        # Fechar divs do container
        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)
        
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
    """Display registration form with matching style"""
    try:
        # Esconder a barra lateral do Streamlit
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Aplicar o estilo moderno de login (reutilizamos o mesmo estilo)
        apply_modern_login_style()
        
        # Criar página de registro com HTML personalizado
        st.markdown("""
        <div class="login-background">
            <div class="login-container">
                <h2 class="login-title">Criar uma conta</h2>
                <!-- O formulário será inserido aqui pelo Streamlit -->
        """, unsafe_allow_html=True)
        
        # Formulário de registro
        with st.form("register_form", clear_on_submit=False):
            name = st.text_input("Nome completo")
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            
            # Botão invisível do formulário
            submitted = st.form_submit_button("REGISTRAR")
        
        # Botão personalizado de registro
        st.markdown("""
        <button class="login-button" onclick="document.querySelector('div[data-testid=\\"stForm\\"] button[kind=\\"primaryFormSubmit\\"]').click();">
            REGISTRAR
        </button>
        
        <div class="login-link" style="margin-top: 25px;">
            Já tem uma conta?
        </div>
        """, unsafe_allow_html=True)
        
        # Botão de login
        st.markdown("""
        <button class="register-button" onclick="window.location.href='?page=login';">
            FAÇA LOGIN
        </button>
        """, unsafe_allow_html=True)
        
        # Fechar divs do container
        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)
        
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
