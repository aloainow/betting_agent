# app.py - Aplicativo principal ValueHunter com navegação aprimorada
import streamlit as st
import logging
import os
import time
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("valueHunter.app")

# Importações dos módulos do projeto
from utils.core import (
    show_valuehunter_logo, update_purchase_button, check_payment_success, 
    apply_custom_styles, go_to_login, configure_sidebar_toggle, DATA_DIR
)
from utils.data import UserManager
from pages.dashboard import show_main_dashboard, get_league_selection, show_usage_stats
from pages.packages import show_packages_page
from pages.login import show_login_page
from pages.landing import show_landing_page

# Cria diretórios necessários
os.makedirs(DATA_DIR, exist_ok=True)

# Inicialização de configurações globais
def initialize_app_state():
    """Inicializa o estado do aplicativo com valores padrão"""
    if 'initialized' not in st.session_state:
        # Estado de navegação
        st.session_state.current_page = 'landing'
        st.session_state.previous_page = None
        
        # Estado de autenticação
        st.session_state.authenticated = False
        st.session_state.email = None
        
        # Configurações e personalizações
        st.session_state.debug_mode = False
        st.session_state.stripe_test_mode = True  # Modo de teste ativado por padrão
        
        # Estado da sidebar
        st.session_state.sidebar_expanded = True
        
        # Marcar como inicializado
        st.session_state.initialized = True
        
        logger.info("Estado do aplicativo inicializado com valores padrão")

# Função para gerenciar a navegação entre páginas
def handle_navigation():
    """Gerencia transições entre páginas e atualiza dados quando necessário"""
    # Verificar se é necessário recarregar dados do usuário ao navegar
    if (st.session_state.current_page != st.session_state.previous_page and 
        st.session_state.authenticated and st.session_state.email):
        
        # Recarregar dados ao mudar entre páginas principais
        try:
            # Recarregar a classe UserManager para garantir dados atualizados
            st.session_state.user_manager = UserManager()
            # Limpar qualquer cache que possa existir para estatísticas
            if hasattr(st.session_state, 'user_stats_cache'):
                del st.session_state.user_stats_cache
            # Log da atualização
            logger.info(f"Dados de usuário recarregados na transição de {st.session_state.previous_page} para {st.session_state.current_page}")
        except Exception as e:
            logger.error(f"Erro ao atualizar dados do usuário: {str(e)}")

# Renderiza botões de navegação na sidebar
def render_sidebar_navigation():
    """Renderiza os botões de navegação na sidebar e retorna True se algum botão foi clicado"""
    # Adiciona separador para melhor UI
    st.sidebar.markdown("---")
    
    nav_clicked = False
    
    # Botão para ir para a página de pacotes
    if st.sidebar.button("🚀 Ver Pacotes de Créditos", key="nav_packages_btn", use_container_width=True):
        st.session_state.previous_page = st.session_state.current_page
        st.session_state.current_page = 'packages'
        nav_clicked = True
    
    # Botão de logout
    if st.sidebar.button("Logout", key="nav_logout_btn", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.email = None
        st.session_state.previous_page = st.session_state.current_page
        st.session_state.current_page = 'landing'
        nav_clicked = True
    
    # Se estamos em modo debug, adicionar opções de depuração
    if st.session_state.debug_mode:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Debug Options")
        
        # Botão para limpar todo o cache
        if st.sidebar.button("🧹 Clear All Cache", key="clear_all_cache_btn"):
            from utils.footystats_api import clear_all_cache
            num_cleared = clear_all_cache()
            st.sidebar.success(f"Cleared {num_cleared} cache files")
            nav_clicked = True
    
    return nav_clicked

# Função principal do aplicativo
def main():
    """Função principal que controla o fluxo do aplicativo"""
    # Inicializar estado do aplicativo
    initialize_app_state()
    
    # Verificar parâmetros de URL para navegação
    query_params = st.experimental_get_query_params()
    if "page" in query_params:
        requested_page = query_params["page"][0]
        if requested_page != st.session_state.current_page:
            st.session_state.previous_page = st.session_state.current_page
            st.session_state.current_page = requested_page
            # Remover parâmetro para evitar navegação duplicada
            del st.query_params["page"]
    
    # Processar páginas acessíveis sem autenticação
    if st.session_state.current_page == 'landing':
        show_landing_page()
        return
    
    if st.session_state.current_page == 'login':
        show_login_page()
        return
    
    # Verificar autenticação para páginas protegidas
    if not st.session_state.authenticated or not st.session_state.email:
        logger.warning("Tentativa de acesso a página protegida sem autenticação")
        st.session_state.current_page = 'login'
        show_login_page()
        return
    
    # Aplicar estilos personalizados para páginas autenticadas
    apply_custom_styles()
    
    # Configurar sidebar (se visível na página atual)
    if st.session_state.current_page != 'packages':  # Ocultar na página de pacotes
        # Configurar toggle da sidebar
        configure_sidebar_toggle()
        
        # Mostrar conteúdo da sidebar
        with st.sidebar:
            st.title("ValueHunter")
            st.markdown("---")
            
            # Mostrar estatísticas de uso
            show_usage_stats()
            
            # Mostrar seleções específicas da página principal
            if st.session_state.current_page == 'main':
                # Escolha da liga
                selected_league = get_league_selection(key_suffix="_main_dashboard")
                if selected_league:
                    # Nota sobre carregamento
                    st.info("Os times são carregados automaticamente ao selecionar uma liga.")
                
                # Separador
                st.markdown("---")
            
            # Verificar botões de navegação (deve ser o último elemento da sidebar)
            if render_sidebar_navigation():
                # Se algum botão foi clicado, processar navegação
                handle_navigation()
                st.experimental_rerun()
    
    # Renderizar a página correta baseado no estado atual
    if st.session_state.current_page == 'main':
        show_main_dashboard()
    elif st.session_state.current_page == 'packages':
        show_packages_page()
    else:
        # Página não encontrada, redirecionar para dashboard
        logger.warning(f"Página não reconhecida: {st.session_state.current_page}, redirecionando para dashboard")
        st.session_state.current_page = 'main'
        st.experimental_rerun()

# Verificar suporte para versão específica do Streamlit
def check_streamlit_version():
    """Verifica se a versão do Streamlit é compatível"""
    try:
        import streamlit as st
        version = st.__version__
        major, minor, patch = map(int, version.split('.'))
        
        if major < 1 or (major == 1 and minor < 10):
            st.warning(f"Versão atual do Streamlit: {version}. Recomendamos a versão 1.10.0 ou superior para melhor experiência.")
            logger.warning(f"Versão do Streamlit possivelmente incompatível: {version}")
    except:
        logger.warning("Não foi possível verificar a versão do Streamlit")

# Execução principal
if __name__ == "__main__":
    # Verificar versão
    check_streamlit_version()
    
    # Iniciar aplicativo
    try:
        main()
    except Exception as e:
        logger.error(f"Erro fatal na execução do aplicativo: {str(e)}")
        
        # Exibir mensagem amigável para o usuário
        st.error("Ocorreu um erro inesperado. Por favor, recarregue a página e tente novamente.")
        
        # Em modo de depuração, mostrar detalhes adicionais
        if hasattr(st.session_state, 'debug_mode') and st.session_state.debug_mode:
            import traceback
            st.code(traceback.format_exc())
