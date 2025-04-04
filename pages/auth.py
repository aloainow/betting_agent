# pages/auth.py - Funções de Autenticação
import streamlit as st
import time
import logging
from utils.core import show_valuehunter_logo, go_to_landing, go_to_login, go_to_register
from utils.core import show_valuehunter_logo, go_to_landing, go_to_login, go_to_register, apply_responsive_styles, apply_custom_styles


# Configuração de logging
logger = logging.getLogger("valueHunter.auth")

def show_login():
    """Display login form"""
    try:
        # Aplicar estilos personalizados
        apply_custom_styles()
        # Aplicar estilos responsivos
        apply_responsive_styles()
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
        # Aplicar estilos personalizados
        apply_custom_styles()
        # Aplicar estilos responsivos
        apply_responsive_styles()
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
