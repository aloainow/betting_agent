# pages/auth.py - Funções de Autenticação
import streamlit as st
import time
import logging
from utils.core import show_valuehunter_logo, go_to_landing, go_to_login, go_to_register, apply_responsive_styles
from utils.email_verification import send_verification_email, generate_verification_code

# Configuração de logging
logger = logging.getLogger("valueHunter.auth")

# Modificação na função show_login() em pages/auth.py

def show_login():
    """Exibe a tela de login prevenindo duplicação e garantindo redirecionamento correto"""
    
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
                            st.session_state.logged_in = True
                            st.session_state.email = email
                            
                            # Obter dados do usuário
                            user_data = st.session_state.user_manager.get_user_data(email)
                            if user_data:
                                st.session_state.user = user_data
                            
                            # Log para debug
                            print(f"Login bem-sucedido para {email}, redirecionando para dashboard")
                            
                            # Redirecionar para dashboard - CORRIGIDO: usar "dashboard" em vez de "main"
                            st.session_state.page = "dashboard"
                            
                            # Forçar rerun para garantir redirecionamento
                            st.success("Login bem-sucedido! Redirecionando para o dashboard...")
                            time.sleep(1)
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
            password = st.text_input("Senha", type="password")
            confirm_password = st.text_input("Confirmar Senha", type="password")
            
            submitted = st.form_submit_button("Registrar")
            
            if submitted:
                if not name or not email or not password or not confirm_password:
                    st.error("Por favor, preencha todos os campos.")
                    return
                    
                if password != confirm_password:
                    st.error("As senhas não coincidem. Por favor, tente novamente.")
                    return
                    
                if len(password) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                    return
                    
                # Verificar se o email já está registrado
                if hasattr(st.session_state.user_manager, "users") and email in st.session_state.user_manager.users:
                    st.error("Este email já está registrado. Por favor, use outro email ou faça login.")
                    return
                
                # Registrar o usuário
                try:
                    # Gerar código de verificação
                    verification_code = generate_verification_code()
                    
                    # Registrar usuário com código de verificação
                    st.session_state.user_manager.register_user(email, password, name, verification_code)
                    
                    # Enviar email de verificação
                    if send_verification_email(email, verification_code):
                        # Sucesso - redirecionar para a tela de verificação
                        st.session_state.verification_email = email
                        st.session_state.page = "verify_email"
                        st.success("Registro realizado com sucesso! Verifique seu email para ativar sua conta.")
                        time.sleep(2)
                        st.experimental_rerun()
                    else:
                        # Se falhar o envio, mostrar o código na tela (apenas para desenvolvimento/teste)
                        if "debug_mode" in st.session_state and st.session_state.debug_mode:
                            st.warning(f"Não foi possível enviar o email. Código de verificação (APENAS PARA TESTE): {verification_code}")
                            # Redirecionar mesmo assim
                            st.session_state.verification_email = email
                            st.session_state.page = "verify_email"
                            time.sleep(3)
                            st.experimental_rerun()
                        else:
                            st.error("Não foi possível enviar o email de verificação. Por favor, tente novamente mais tarde.")
                except Exception as e:
                    logger.error(f"Erro ao registrar usuário: {str(e)}")
                    st.error(f"Erro ao registrar usuário: {str(e)}")
                    
                    # Mostrar código na tela em modo de depuração
                    if "debug_mode" in st.session_state and st.session_state.debug_mode:
                        st.warning(f"Erro no registro: {str(e)}")
                        st.info(f"Código de verificação (APENAS PARA TESTE): {verification_code}")
                        
                        # Ainda permitir prosseguir em modo debug
                        st.session_state.verification_email = email
                        if st.button("Continuar mesmo assim"):
                            st.session_state.page = "verify_email"
                            st.experimental_rerun()
        
        # Link para login
        st.markdown("---")
        st.markdown("Já tem uma conta?")
        if st.button("Fazer Login"):
            go_to_login()
            
    except Exception as e:
        logger.error(f"Erro ao exibir página de registro: {str(e)}")
        st.error("Erro ao carregar a página de registro. Por favor, tente novamente.")
        
        # Mostrar detalhes em modo debug
        if "debug_mode" in st.session_state and st.session_state.debug_mode:
            st.error(f"Detalhes: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

def show_verify_email():
    """Display email verification page"""
    try:
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
        
        st.title("Verificação de Email")
        
        # Verificar se o email está na sessão
        if 'verification_email' not in st.session_state:
            st.error("Sessão expirada. Por favor, registre-se novamente.")
            st.session_state.page = "register"
            time.sleep(2)
            st.experimental_rerun()
            return
            
        email = st.session_state.verification_email
        st.markdown(f"### Um código foi enviado para {email}")
        st.info("Insira o código que você recebeu no seu email para ativar sua conta.")
        
        with st.form("verification_form"):
            verification_code = st.text_input("Código de Verificação", max_chars=6)
            submitted = st.form_submit_button("Verificar")
            
            if submitted:
                if not verification_code:
                    st.error("Por favor, insira o código de verificação.")
                    return
                
                # Verificar o código
                if (hasattr(st.session_state.user_manager, "users") and 
                    email in st.session_state.user_manager.users and 
                    st.session_state.user_manager.users[email].get("verification_code") == verification_code):
                    
                    # Código correto - ativar a conta
                    st.session_state.user_manager.users[email]["verified"] = True
                    
                    # Remover código de verificação
                    if "verification_code" in st.session_state.user_manager.users[email]:
                        del st.session_state.user_manager.users[email]["verification_code"]
                    
                    # Salvar alterações
                    st.session_state.user_manager._save_users()
                    
                    # Limpar variáveis de sessão
                    if 'verification_email' in st.session_state:
                        del st.session_state.verification_email
                    
                    # Redirecionar para login
                    st.success("Email verificado com sucesso! Agora você pode fazer login.")
                    st.session_state.page = "login"
                    time.sleep(2)
                    st.experimental_rerun()
                else:
                    st.error("Código inválido. Por favor, tente novamente.")
        
        # Opção para reenviar o código
        st.markdown("---")
        if st.button("Reenviar código"):
            # Gerar novo código de verificação
            new_verification_code = generate_verification_code()
            
            # Atualizar o código no perfil do usuário
            if hasattr(st.session_state.user_manager, "users") and email in st.session_state.user_manager.users:
                st.session_state.user_manager.users[email]["verification_code"] = new_verification_code
                st.session_state.user_manager._save_users()
                
                # Enviar email com o novo código
                if send_verification_email(email, new_verification_code):
                    st.success("Novo código enviado com sucesso! Verifique seu email.")
                else:
                    # Se falhar o envio, mostrar o código na tela (apenas para desenvolvimento/teste)
                    if "debug_mode" in st.session_state and st.session_state.debug_mode:
                        st.warning(f"Não foi possível enviar o email. Novo código de verificação (APENAS PARA TESTE): {new_verification_code}")
                    else:
                        st.error("Não foi possível enviar o email. Por favor, tente novamente mais tarde.")
            else:
                st.error("Usuário não encontrado. Por favor, registre-se novamente.")
                st.session_state.page = "register"
                time.sleep(2)
                st.experimental_rerun()
    
    except Exception as e:
        logger.error(f"Erro ao exibir página de verificação de email: {str(e)}")
        st.error("Erro ao carregar a página de verificação. Por favor, tente novamente.")
        st.error(f"Detalhes: {str(e)}")
