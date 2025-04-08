# pages/auth.py - Funções de Autenticação
import streamlit as st
import time
import logging
from utils.core import show_valuehunter_logo, go_to_landing, go_to_login, go_to_register
from utils.core import show_valuehunter_logo, go_to_landing, go_to_login, go_to_register, apply_responsive_styles, apply_custom_styles
from utils.email_verification import send_verification_email, generate_verification_code

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
                
                if not email or not password:
                    st.error("Por favor, preencha todos os campos.")
                    return
                
                # Gerar código de verificação
                verification_code = generate_verification_code()
                
                # Todo usuário novo começa automaticamente no pacote Free
                # Tentativa adaptativa - primeiro tentar com o parâmetro nome e verificação
                try:
                    success, message = st.session_state.user_manager.register_user(
                        email, password, name, "free", 
                        verified=False, verification_code=verification_code
                    )
                except TypeError:
                    # Se der erro, tentar uma versão com menos parâmetros
                    try:
                        success, message = st.session_state.user_manager.register_user(
                            email, password, name, "free"
                        )
                        # Adicionar campos de verificação depois
                        if success and hasattr(st.session_state.user_manager, "users") and email in st.session_state.user_manager.users:
                            st.session_state.user_manager.users[email]["verified"] = False
                            st.session_state.user_manager.users[email]["verification_code"] = verification_code
                            st.session_state.user_manager._save_users()
                    except TypeError:
                        # Usar a versão antiga como fallback final
                        success, message = st.session_state.user_manager.register_user(email, password, "free")
                        # E atualizar o nome e verificação depois, se for bem-sucedido
                        if success and hasattr(st.session_state.user_manager, "users") and email in st.session_state.user_manager.users:
                            st.session_state.user_manager.users[email]["name"] = name
                            st.session_state.user_manager.users[email]["verified"] = False
                            st.session_state.user_manager.users[email]["verification_code"] = verification_code
                            st.session_state.user_manager._save_users()
                
                if success:
                    # Enviar email de verificação
                    if send_verification_email(email, verification_code):
                        st.success("Conta criada com sucesso!")
                        st.info("Verificamos sua conta por email para garantir a segurança. Por favor, verifique sua caixa de entrada.")
                        
                        # Armazenar email na sessão para a página de verificação
                        st.session_state.pending_verification_email = email
                        
                        # Redirecionar para a página de verificação
                        st.session_state.page = "verification"
                        time.sleep(2)
                        st.experimental_rerun()
                    else:
                        st.warning("Conta criada, mas houve um problema ao enviar o email de verificação.")
                        st.info("Você não receberá seus créditos gratuitos até verificar seu email. Por favor, entre em contato com o suporte.")
                        
                        # Mesmo assim, redirecionar para login após alguns segundos
                        st.session_state.page = "login"
                        time.sleep(3)
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
def show_verification():
    """Display verification code entry form"""
    try:
        # Aplicar estilos
        apply_custom_styles()
        apply_responsive_styles()
        
        # Esconder a barra lateral
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        
        st.title("Verificação de Email")
        st.info("Um código de verificação foi enviado para o seu email. Por favor, insira-o abaixo para ativar sua conta.")
        
        with st.form("verification_form"):
            verification_code = st.text_input("Código de Verificação", max_chars=6)
            submitted = st.form_submit_button("Verificar")
            
            if submitted:
                if not verification_code:
                    st.error("Por favor, insira o código de verificação.")
                    return
                
                # Verificar se o email está na sessão
                if 'pending_verification_email' not in st.session_state:
                    st.error("Sessão expirada. Por favor, registre-se novamente.")
                    time.sleep(2)
                    go_to_register()
                    return
                
                email = st.session_state.pending_verification_email
                
                # Verificar o código
                if st.session_state.user_manager.verify_email(email, verification_code):
                    st.success("Email verificado com sucesso! Sua conta agora está ativa.")
                    
                    # Limpar dados de verificação pendente
                    if 'pending_verification_email' in st.session_state:
                        del st.session_state.pending_verification_email
                    
                    # Redirecionar para login
                    st.session_state.page = "login"
                    time.sleep(2)
                    st.experimental_rerun()
                else:
                    st.error("Código de verificação inválido. Por favor, tente novamente.")
        
        # Botão para reenviar código
        if st.button("Reenviar código de verificação"):
            if 'pending_verification_email' in st.session_state:
                email = st.session_state.pending_verification_email
                new_code = generate_verification_code()
                
                if st.session_state.user_manager.update_verification_code(email, new_code):
                    if send_verification_email(email, new_code):
                        st.success("Um novo código de verificação foi enviado para o seu email.")
                    else:
                        st.error("Erro ao enviar novo código de verificação. Por favor, tente novamente.")
                else:
                    st.error("Erro ao gerar novo código. Por favor, entre em contato com o suporte.")
            else:
                st.error("Sessão expirada. Por favor, registre-se novamente.")
                time.sleep(2)
                go_to_register()
    
    except Exception as e:
        logger.error(f"Erro ao exibir página de verificação: {str(e)}")
        st.error("Erro ao carregar a página de verificação. Por favor, tente novamente.")
        st.error(f"Detalhes: {str(e)}")
def show_verification():
    """Display verification code entry form"""
    try:
        # Aplicar estilos personalizados
        apply_custom_styles()
        # Aplicar estilos responsivos
        apply_responsive_styles()
        # Esconder a barra lateral do Streamlit na página de verificação
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        
        st.title("Verificação de Email")
        st.info("Um código de verificação foi enviado para o seu email. Por favor, insira-o abaixo para ativar sua conta.")
        
        with st.form("verification_form"):
            verification_code = st.text_input("Código de Verificação", max_chars=6)
            submitted = st.form_submit_button("Verificar")
            
            if submitted:
                if not verification_code:
                    st.error("Por favor, insira o código de verificação.")
                    return
                
                # Verificar se o email está na sessão
                if 'pending_verification_email' not in st.session_state:
                    st.error("Sessão expirada. Por favor, registre-se novamente.")
                    time.sleep(2)
                    go_to_register()
                    return
                
                email = st.session_state.pending_verification_email
                
                # Verificar o código
                try:
                    if st.session_state.user_manager.verify_email_code(email, verification_code):
                        st.success("Email verificado com sucesso! Sua conta agora está ativa.")
                        
                        # Limpar dados de verificação pendente
                        if 'pending_verification_email' in st.session_state:
                            del st.session_state.pending_verification_email
                        
                        # Redirecionar para login
                        st.session_state.page = "login"
                        time.sleep(2)
                        st.experimental_rerun()
                    else:
                        st.error("Código de verificação inválido. Por favor, tente novamente.")
                except Exception as e:
                    st.error(f"Erro ao verificar código: {str(e)}")
        
        # Botão para reenviar código
        if st.button("Reenviar código de verificação"):
            if 'pending_verification_email' in st.session_state:
                email = st.session_state.pending_verification_email
                from utils.email_verification import generate_verification_code, send_verification_email
                
                new_code = generate_verification_code()
                
                if st.session_state.user_manager.update_verification_code(email, new_code):
                    if send_verification_email(email, new_code):
                        st.success("Um novo código de verificação foi enviado para o seu email.")
                    else:
                        st.error("Erro ao enviar novo código de verificação. Por favor, tente novamente.")
                else:
                    st.error("Erro ao gerar novo código. Por favor, entre em contato com o suporte.")
            else:
                st.error("Sessão expirada. Por favor, registre-se novamente.")
                time.sleep(2)
                go_to_register()
    
    except Exception as e:
        logger.error(f"Erro ao exibir página de verificação: {str(e)}")
        st.error("Erro ao carregar a página de verificação. Por favor, tente novamente.")
        st.error(f"Detalhes: {str(e)}")
