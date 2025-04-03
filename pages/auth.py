# pages/auth.py - Solução Simplificada
import streamlit as st
import time
import logging
from utils.core import show_valuehunter_logo, go_to_landing, go_to_login, go_to_register

# Configuração de logging
logger = logging.getLogger("valueHunter.auth")

def apply_streamlit_friendly_styles():
    """Aplica estilos que funcionam de forma confiável com o Streamlit"""
    st.markdown("""
    <style>
    /* Esconder barra lateral */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Estilo de fundo com gradiente */
    .stApp {
        background: linear-gradient(135deg, #1a1a1a 0%, #1a1a1a 50%, #fd7014 50%, #fd7014 100%);
    }
    
    /* Estilo para o card */
    .login-card {
        background: white;
        border-radius: 12px;
        padding: 40px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        max-width: 420px;
        margin: 0 auto;
    }
    
    /* Logo estilizado */
    .vh-logo {
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    .vh-logo-value {
        color: #252525;
    }
    
    .vh-logo-hunter {
        color: #fd7014;
    }
    
    /* Título com linha abaixo */
    .login-title {
        color: #333;
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 30px;
        position: relative;
        padding-bottom: 12px;
        border-bottom: 3px solid #fd7014;
        width: fit-content;
    }
    
    /* Estilo para o botão de login/registro */
    div[data-testid="stButton"] button {
        background-color: #fd7014;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: background-color 0.3s;
        width: 100%;
    }
    
    div[data-testid="stButton"] button:hover {
        background-color: #e06000;
    }
    
    /* Estilo para o botão secundário */
    .secondary-button button {
        background-color: #252525 !important;
    }
    
    .secondary-button button:hover {
        background-color: #333 !important;
    }
    
    /* Estilos para texto centralizado e separadores */
    .centered-text {
        text-align: center;
    }
    
    hr.divider {
        margin: 25px 0;
        border-top: 1px solid #eee;
        border-bottom: none;
    }
    
    /* Estilos para links */
    a.orange-link {
        color: #fd7014;
        text-decoration: none;
        font-weight: 500;
    }
    
    a.orange-link:hover {
        text-decoration: underline;
    }
    
    /* Melhorar aparência do formulário */
    div[data-baseweb="input"] {
        margin-bottom: 15px;
    }
    
    div[data-baseweb="input"] input {
        background-color: #f7f7f7;
        border-radius: 6px;
    }
    
    div[data-testid="stCheckbox"] {
        margin-bottom: 20px;
    }
    
    /* Melhorar espaçamento */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

def show_login():
    """Display login form with simpler styling approach"""
    try:
        # Aplicar os estilos
        apply_streamlit_friendly_styles()
        
        # Criar o container com a classe de estilo
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # Logo
        st.markdown('<div class="vh-logo"><span class="vh-logo-value">Value</span><span class="vh-logo-hunter">Hunter</span></div>', unsafe_allow_html=True)
        
        # Título
        st.markdown('<h1 class="login-title">Faça o seu login</h1>', unsafe_allow_html=True)
        
        # Formulário
        with st.form("login_form"):
            email = st.text_input("Seu e-mail")
            password = st.text_input("Sua senha", type="password")
            remember = st.checkbox("Lembrar-me")
            
            # Botão de submissão
            submitted = st.form_submit_button("ENTRAR", use_container_width=True)
        
        # Link para senha esquecida
        st.markdown('<div class="centered-text"><a href="#" class="orange-link">Esqueceu sua senha?</a></div>', unsafe_allow_html=True)
        
        # Separador
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        
        # Opção de registro
        st.markdown('<div class="centered-text">Não tem uma conta?</div>', unsafe_allow_html=True)
        
        # Botão para registro - usando o padrão do Streamlit
        st.markdown('<div class="secondary-button">', unsafe_allow_html=True)
        if st.button("REGISTRE-SE AQUI", use_container_width=True):
            go_to_register()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Fechar div do card
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
    """Display registration form with simpler styling approach"""
    try:
        # Aplicar os estilos
        apply_streamlit_friendly_styles()
        
        # Criar o container com a classe de estilo
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # Logo
        st.markdown('<div class="vh-logo"><span class="vh-logo-value">Value</span><span class="vh-logo-hunter">Hunter</span></div>', unsafe_allow_html=True)
        
        # Título
        st.markdown('<h1 class="login-title">Criar uma conta</h1>', unsafe_allow_html=True)
        
        # Formulário
        with st.form("register_form"):
            name = st.text_input("Nome completo")
            email = st.text_input("Seu e-mail")
            password = st.text_input("Sua senha", type="password")
            
            # Botão de submissão
            submitted = st.form_submit_button("REGISTRAR", use_container_width=True)
        
        # Separador
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        
        # Opção de login
        st.markdown('<div class="centered-text">Já tem uma conta?</div>', unsafe_allow_html=True)
        
        # Botão para login - usando o padrão do Streamlit
        st.markdown('<div class="secondary-button">', unsafe_allow_html=True)
        if st.button("FAÇA LOGIN", use_container_width=True):
            go_to_login()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Fechar div do card
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
