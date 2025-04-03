# pages/auth.py - Layout completamente corrigido
import streamlit as st
import time
import logging
from utils.core import show_valuehunter_logo, go_to_landing, go_to_login, go_to_register

# Configuração de logging
logger = logging.getLogger("valueHunter.auth")

def apply_fixed_login_style():
    """Aplica um estilo completamente corrigido para a tela de login"""
    st.markdown("""
    <style>
    /* Reset completo de estilos */
    div.block-container {
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Esconder completamente elementos do Streamlit */
    div.stApp > header {
        display: none !important;
    }
    
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Fundo com diagrama corrigido */
    .vh-login-page {
        width: 100vw;
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        background: linear-gradient(135deg, #1a1a1a 0%, #1a1a1a 50%, #fd7014 50%, #fd7014 100%);
        padding: 0;
        margin: 0;
        overflow: hidden;
        box-sizing: border-box;
    }
    
    /* Card de login centralizado e com tamanho fixo */
    .vh-login-card {
        width: 100%;
        max-width: 420px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.15);
        padding: 40px 30px;
        box-sizing: border-box;
    }
    
    /* Título e decoração */
    .vh-login-title {
        font-size: 24px;
        font-weight: 600;
        color: #333;
        margin-bottom: 30px;
        position: relative;
        padding-bottom: 10px;
    }
    
    .vh-login-title:after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 50px;
        height: 3px;
        background-color: #fd7014;
    }
    
    /* Campos de formulário */
    .vh-form-field {
        margin-bottom: 25px;
    }
    
    .vh-form-label {
        display: block;
        font-size: 14px;
        font-weight: 500;
        color: #555;
        margin-bottom: 8px;
    }
    
    .vh-form-input {
        width: 100%;
        padding: 12px 15px;
        border: 1px solid #ddd;
        border-radius: 6px;
        background-color: #f7f7f7;
        font-size: 16px;
        box-sizing: border-box;
    }
    
    /* Checkbox personalizado */
    .vh-checkbox {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .vh-checkbox input[type="checkbox"] {
        margin-right: 8px;
    }
    
    .vh-checkbox label {
        font-size: 14px;
        color: #555;
    }
    
    /* Botão de login */
    .vh-button {
        background-color: #fd7014;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 12px 20px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        transition: background-color 0.2s;
    }
    
    .vh-button:hover {
        background-color: #e06000;
    }
    
    /* Links e texto de apoio */
    .vh-text-center {
        text-align: center;
    }
    
    .vh-link {
        color: #fd7014;
        text-decoration: none;
        font-weight: 500;
    }
    
    .vh-link:hover {
        text-decoration: underline;
    }
    
    .vh-mt-20 {
        margin-top: 20px;
    }
    
    .vh-mt-30 {
        margin-top: 30px;
    }
    
    .vh-divider {
        border-top: 1px solid #eee;
        margin: 25px 0;
    }
    
    /* Botão secundário */
    .vh-button-secondary {
        background-color: #252525;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 12px 20px;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        width: 100%;
        transition: background-color 0.2s;
    }
    
    .vh-button-secondary:hover {
        background-color: #333;
    }
    
    /* Logo */
    .vh-logo {
        font-size: 24px;
        font-weight: bold;
        color: #252525;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .vh-logo span {
        color: #fd7014;
    }
    
    /* Esconder elementos do Streamlit */
    div[data-testid="stForm"] > div:first-child {
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
        background: transparent !important;
    }
    
    /* Ajustes responsivos */
    @media (max-width: 480px) {
        .vh-login-card {
            max-width: 90%;
            padding: 30px 20px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def show_login():
    """Display properly formatted login form"""
    try:
        # Esconder a barra lateral do Streamlit
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Aplicar estilo corrigido
        apply_fixed_login_style()
        
        # Estrutura HTML customizada
        st.markdown("""
        <div class="vh-login-page">
            <div class="vh-login-card">
                <div class="vh-logo">Value<span>Hunter</span></div>
                <h1 class="vh-login-title">Faça o seu login</h1>
                
                <!-- Aqui o Streamlit vai inserir o formulário -->
        """, unsafe_allow_html=True)
        
        # O formulário é inserido aqui (vai se integrar com o HTML)
        with st.form("login_form", clear_on_submit=False):
            st.markdown('<div class="vh-form-field">', unsafe_allow_html=True)
            st.markdown('<label class="vh-form-label">Seu e-mail</label>', unsafe_allow_html=True)
            email = st.text_input("", key="email_input", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="vh-form-field">', unsafe_allow_html=True)
            st.markdown('<label class="vh-form-label">Sua senha</label>', unsafe_allow_html=True)
            password = st.text_input("", type="password", key="password_input", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="vh-checkbox">', unsafe_allow_html=True)
            remember = st.checkbox("Lembrar-me", value=False, key="remember_checkbox", label_visibility="collapsed")
            st.markdown('<label for="remember_checkbox">Lembrar-me</label>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            submitted = st.form_submit_button("ENTRAR", type="primary")
        
        # Continuar o layout HTML após o formulário
        st.markdown("""
                <button class="vh-button" type="button" onclick="document.querySelector('button[data-testid=\\"baseButton-primary\\"]').click();">ENTRAR</button>
                
                <div class="vh-text-center vh-mt-20">
                    <a href="#" class="vh-link">Esqueceu sua senha?</a>
                </div>
                
                <div class="vh-divider"></div>
                
                <div class="vh-text-center">
                    <p>Não tem uma conta?</p>
                    <a href="?page=register" class="vh-button-secondary vh-mt-20" style="display: inline-block; text-decoration: none;">REGISTRE-SE AQUI</a>
                </div>
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
    """Display properly formatted registration form"""
    try:
        # Esconder a barra lateral do Streamlit
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Aplicar estilo corrigido
        apply_fixed_login_style()
        
        # Estrutura HTML customizada
        st.markdown("""
        <div class="vh-login-page">
            <div class="vh-login-card">
                <div class="vh-logo">Value<span>Hunter</span></div>
                <h1 class="vh-login-title">Criar uma conta</h1>
                
                <!-- Aqui o Streamlit vai inserir o formulário -->
        """, unsafe_allow_html=True)
        
        # O formulário é inserido aqui (vai se integrar com o HTML)
        with st.form("register_form", clear_on_submit=False):
            st.markdown('<div class="vh-form-field">', unsafe_allow_html=True)
            st.markdown('<label class="vh-form-label">Nome completo</label>', unsafe_allow_html=True)
            name = st.text_input("", key="name_input", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="vh-form-field">', unsafe_allow_html=True)
            st.markdown('<label class="vh-form-label">Seu e-mail</label>', unsafe_allow_html=True)
            email = st.text_input("", key="email_input", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="vh-form-field">', unsafe_allow_html=True)
            st.markdown('<label class="vh-form-label">Sua senha</label>', unsafe_allow_html=True)
            password = st.text_input("", type="password", key="password_input", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            submitted = st.form_submit_button("REGISTRAR", type="primary")
        
        # Continuar o layout HTML após o formulário
        st.markdown("""
                <button class="vh-button" type="button" onclick="document.querySelector('button[data-testid=\\"baseButton-primary\\"]').click();">REGISTRAR</button>
                
                <div class="vh-divider"></div>
                
                <div class="vh-text-center">
                    <p>Já tem uma conta?</p>
                    <a href="?page=login" class="vh-button-secondary vh-mt-20" style="display: inline-block; text-decoration: none;">FAÇA LOGIN</a>
                </div>
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
