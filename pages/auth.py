# pages/auth.py - Funções de Autenticação
import streamlit as st
import time
import logging
from utils.core import show_valuehunter_logo, go_to_landing, go_to_login, go_to_register, apply_responsive_styles, apply_custom_styles, apply_dark_theme
from utils.email_verification import send_verification_email, generate_verification_code

# Configuração de logging
logger = logging.getLogger("valueHunter.auth")

# Modificação na função show_login() em pages/auth.py

def show_login():
    """Exibe a tela de login prevenindo duplicação e garantindo redirecionamento correto"""

    # Aplicar tema escuro
    apply_dark_theme()
    # Exibir o logo do ValueHunter (apenas uma vez)
    show_valuehunter_logo()
    
    # Título e descrição da página
    st.title("Login")
    st.markdown("Entre com suas credenciais para acessar o sistema.")
    
    # Criar duas colunas para centralizar o formulário
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Formulário de login
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Senha", type="password", key="login_password")
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Entrar", key="login_btn"):
                if not email or not password:
                    st.error("Por favor, preencha todos os campos.")
                else:
                    # Verificar credenciais com manejo de erro
                    try:
                        if st.session_state.user_manager.verify_login(email, password):
                            # Login bem-sucedido
                            st.session_state.authenticated = True
                            st.session_state.email = email
                            
                            # Log para debug
                            print(f"Login bem-sucedido para {email}, redirecionando para dashboard")
                            
                            # Redirecionar para dashboard
                            st.session_state.page = "main"
                            
                            # Usar experimental_rerun de forma mais segura
                            st.experimental_rerun()
                        else:
                            st.error("Email ou senha incorretos.")
                    except Exception as e:
                        st.error(f"Erro ao fazer login: {str(e)}")
                        print(f"Erro no login: {str(e)}")
        
        with col_btn2:
            if st.button("Registrar", key="register_from_login"):
                st.session_state.page = "register"
                st.experimental_rerun()
        
        # Links para recuperação de senha
        st.markdown("---")
        if st.button("Esqueceu sua senha?", key="forgot_password"):
            st.session_state.page = "password_recovery"
            st.experimental_rerun()


def show_password_recovery():
    """Display password recovery form"""
    try:
        # Aplicar estilos personalizados
        apply_custom_styles()
        # Aplicar estilos responsivos
        apply_responsive_styles()
        # Esconder a barra lateral do Streamlit
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        
        st.title("Recuperação de Senha")
        
        # Botão para voltar ao login
        if st.button("← Voltar para o login"):
            st.session_state.page = "login"
            st.experimental_rerun()
            
        st.markdown("### Insira seu email para recuperar sua senha")
        st.info("Um email com instruções para redefinir sua senha será enviado para você.")
        
        with st.form("recovery_form"):
            email = st.text_input("Email")
            submitted = st.form_submit_button("Enviar")
            
            if submitted:
                if not email:
                    st.error("Por favor, insira seu email.")
                    return
                    
                # Verificar se o email existe
                if not hasattr(st.session_state.user_manager, "users") or email not in st.session_state.user_manager.users:
                    st.error("Email não encontrado. Por favor, verifique e tente novamente.")
                    return
                
                # Gerar código de recuperação
                from utils.email_verification import generate_verification_code, send_password_recovery_email
                
                recovery_code = generate_verification_code()
                
                # Atualizar o código no perfil do usuário
                st.session_state.user_manager.users[email]["recovery_code"] = recovery_code
                st.session_state.user_manager._save_users()
                
                # Registrar evento nos logs
                logger.info(f"Código de recuperação gerado para {email}: {recovery_code}")
                
                try:
                    # Tentativa de enviar email usando a função específica para recuperação
                    if send_password_recovery_email(email, recovery_code):
                        # Sucesso - redirecionar para a tela de código
                        st.session_state.recovery_email = email
                        st.session_state.page = "password_reset_code"
                        st.success("Email enviado com sucesso! Verifique sua caixa de entrada.")
                        time.sleep(2)
                        st.experimental_rerun()
                    else:
                        # Se falhar o envio, mostrar o código na tela (apenas para desenvolvimento/teste)
                        if "debug_mode" in st.session_state and st.session_state.debug_mode:
                            st.warning(f"Não foi possível enviar o email. Código de recuperação (APENAS PARA TESTE): {recovery_code}")
                            # Redirecionar mesmo assim
                            st.session_state.recovery_email = email
                            st.session_state.page = "password_reset_code"
                            time.sleep(3)
                            st.experimental_rerun()
                        else:
                            st.error("Não foi possível enviar o email. Por favor, tente novamente mais tarde.")
                except Exception as e:
                    logger.error(f"Erro ao enviar email de recuperação: {str(e)}")
                    
                    # Mostrar código na tela em modo de depuração
                    if "debug_mode" in st.session_state and st.session_state.debug_mode:
                        st.warning(f"Erro no envio: {str(e)}")
                        st.info(f"Código de recuperação (APENAS PARA TESTE): {recovery_code}")
                        
                        # Ainda permitir prosseguir em modo debug
                        st.session_state.recovery_email = email
                        if st.button("Continuar mesmo assim"):
                            st.session_state.page = "password_reset_code"
                            st.experimental_rerun()
                    else:
                        st.error("Erro ao enviar email. Por favor, tente novamente mais tarde.")
                    
    except Exception as e:
        logger.error(f"Erro ao exibir página de recuperação de senha: {str(e)}")
        st.error("Erro ao carregar a página de recuperação. Por favor, tente novamente.")
        
        # Mostrar detalhes em modo debug
        if "debug_mode" in st.session_state and st.session_state.debug_mode:
            st.error(f"Detalhes: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

def show_password_reset_code():
    """Display password reset code verification page"""
    try:
        # Aplicar estilos personalizados
        apply_custom_styles()
        # Aplicar estilos responsivos
        apply_responsive_styles()
        # Esconder a barra lateral do Streamlit
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        
        st.title("Verificação do Código")
        
        # Verificar se o email está na sessão
        if 'recovery_email' not in st.session_state:
            st.error("Sessão expirada. Por favor, solicite a recuperação novamente.")
            st.session_state.page = "password_recovery"
            time.sleep(2)
            st.experimental_rerun()
            return
            
        email = st.session_state.recovery_email
        st.markdown(f"### Um código foi enviado para {email}")
        st.info("Insira o código que você recebeu no seu email para prosseguir com a redefinição de senha.")
        
        with st.form("reset_code_form"):
            reset_code = st.text_input("Código de Verificação", max_chars=6)
            submitted = st.form_submit_button("Verificar")
            
            if submitted:
                if not reset_code:
                    st.error("Por favor, insira o código de verificação.")
                    return
                
                # Verificar o código
                if (hasattr(st.session_state.user_manager, "users") and 
                    email in st.session_state.user_manager.users and 
                    st.session_state.user_manager.users[email].get("recovery_code") == reset_code):
                    
                    # Código correto - redirecionar para redefinição de senha
                    st.session_state.code_verified = True
                    st.session_state.page = "password_reset"
                    st.success("Código verificado com sucesso!")
                    time.sleep(1)
                    st.experimental_rerun()
                else:
                    st.error("Código inválido. Por favor, tente novamente.")
    
    except Exception as e:
        logger.error(f"Erro ao exibir página de verificação de código: {str(e)}")
        st.error("Erro ao carregar a página de verificação. Por favor, tente novamente.")
        st.error(f"Detalhes: {str(e)}")

def show_password_reset():
    """Display password reset page"""
    try:
        # Aplicar estilos personalizados
        apply_custom_styles()
        # Aplicar estilos responsivos
        apply_responsive_styles()
        # Esconder a barra lateral do Streamlit
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        
        st.title("Redefinir Senha")
        
        # Verificar se o código foi verificado
        if 'code_verified' not in st.session_state or not st.session_state.code_verified:
            st.error("Acesso não autorizado. Por favor, siga o processo de recuperação de senha.")
            st.session_state.page = "password_recovery"
            time.sleep(2)
            st.experimental_rerun()
            return
            
        # Verificar se o email está na sessão
        if 'recovery_email' not in st.session_state:
            st.error("Sessão expirada. Por favor, solicite a recuperação novamente.")
            st.session_state.page = "password_recovery"
            time.sleep(2)
            st.experimental_rerun()
            return
            
        email = st.session_state.recovery_email
        
        st.markdown(f"### Defina uma nova senha para sua conta")
        
        with st.form("new_password_form"):
            new_password = st.text_input("Nova Senha", type="password")
            confirm_password = st.text_input("Confirmar Senha", type="password")
            submitted = st.form_submit_button("Alterar Senha")
            
            if submitted:
                if not new_password or not confirm_password:
                    st.error("Por favor, preencha todos os campos.")
                    return
                    
                if new_password != confirm_password:
                    st.error("As senhas não coincidem. Por favor, tente novamente.")
                    return
                    
                if len(new_password) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                    return
                
                # Atualizar a senha no perfil do usuário
                if hasattr(st.session_state.user_manager, "users") and email in st.session_state.user_manager.users:
                    # Hash da nova senha
                    hashed_password = st.session_state.user_manager._hash_password(new_password)
                    
                    # Atualizar a senha
                    st.session_state.user_manager.users[email]["password"] = hashed_password
                    
                    # Remover código de recuperação
                    if "recovery_code" in st.session_state.user_manager.users[email]:
                        del st.session_state.user_manager.users[email]["recovery_code"]
                    
                    # Salvar alterações
                    st.session_state.user_manager._save_users()
                    
                    # Limpar variáveis de sessão
                    if 'recovery_email' in st.session_state:
                        del st.session_state.recovery_email
                    if 'code_verified' in st.session_state:
                        del st.session_state.code_verified
                    
                    # Redirecionar para login
                    st.success("Senha alterada com sucesso! Agora você pode fazer login com sua nova senha.")
                    st.session_state.page = "login"
                    time.sleep(2)
                    st.experimental_rerun()
                else:
                    st.error("Usuário não encontrado. Por favor, solicite a recuperação novamente.")
                    st.session_state.page = "password_recovery"
                    time.sleep(2)
                    st.experimental_rerun()
                    
    except Exception as e:
        logger.error(f"Erro ao exibir página de redefinição de senha: {str(e)}")
        st.error("Erro ao carregar a página de redefinição. Por favor, tente novamente.")
        st.error(f"Detalhes: {str(e)}")
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
