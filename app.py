import os
import logging
import sys
import streamlit as st
import time
from datetime import datetime
import base64
from utils.core import show_valuehunter_logo

show_valuehunter_logo()

# === NOVO: Verificação de caminhos do Render ===
RENDER_PROJECT_DIR = "/opt/render/project/src"
if "RENDER" in os.environ and os.path.exists(RENDER_PROJECT_DIR):
    # Logo e favicon estão na raiz do projeto no Render
    logo_path_render = os.path.join(RENDER_PROJECT_DIR, "3F3F45.png")
    favicon_path_render = os.path.join(RENDER_PROJECT_DIR, "favicon_svg.svg")
    
    print(f"Caminhos no Render:")
    print(f"Logo: {logo_path_render} (existe: {os.path.exists(logo_path_render)})")
    print(f"Favicon: {favicon_path_render} (existe: {os.path.exists(favicon_path_render)})")

# Verificação avançada de arquivos em múltiplos diretórios
def check_files_in_directories():
    """Verifica se os arquivos existem em diferentes diretórios possíveis"""
    # Diretórios a verificar
    directories = [
        os.getcwd(),                               # Diretório atual
        os.path.join(os.getcwd(), "static"),       # Pasta static
        "/opt/render/project/src",                 # Raiz do Render
        "/app",                                    # Outra pasta comum
        os.path.dirname(os.path.abspath(__file__)) # Diretório do script
    ]
    
    # Arquivos a procurar
    files = ["3F3F45.png", "favicon_svg.svg", "logo.png"]
    
    results = {}
    
    # Verificar cada diretório
    for directory in directories:
        if os.path.exists(directory):
            print(f"Verificando diretório: {directory}")
            try:
                dir_files = os.listdir(directory)
                print(f"Arquivos em {directory}: {dir_files}")
                
                # Verificar cada arquivo
                for file in files:
                    file_path = os.path.join(directory, file)
                    exists = os.path.exists(file_path)
                    results[f"{directory}/{file}"] = exists
                    
                    if exists:
                        print(f"ENCONTRADO: {file} em {directory}")
            except Exception as e:
                print(f"Erro ao listar {directory}: {str(e)}")
        else:
            print(f"Diretório não existe: {directory}")
    
    return results

# Chamar a função no início do aplicativo
file_check_results = check_files_in_directories()

# Descobrir caminhos corretos para o logo e favicon
logo_path = None
favicon_path = None

for path, exists in file_check_results.items():
    if exists and ("3F3F45.png" in path or "logo.png" in path):
        logo_path = path
        print(f"Usando logo encontrado em: {logo_path}")
    if exists and "favicon_svg.svg" in path:
        favicon_path = path
        print(f"Usando favicon encontrado em: {favicon_path}")

# === 1. CONFIGURAR FAVICON & PAGE CONFIG ===
# Definir o conteúdo SVG do favicon inline
favicon_svg = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" rx="20" fill="#fd7014"/>
  <path d="M35 25C25.5 25 20 35 20 45C20 55 25.5 65 35 65C44.5 65 50 55 50 45C50 35 44.5 25 35 25Z" fill="white"/>
  <path d="M65 25C74.5 25 80 35 80 45C80 55 74.5 65 65 65C55.5 65 50 55 50 45C50 35 55.5 25 65 25Z" fill="white"/>
  <path d="M50 40V50M43 45L57 45M35 35C31.7 35 30 39 30 45C30 51 31.7 55 35 55C38.3 55 40 51 40 45C40 39 38.3 35 35 35ZM65 35C61.7 35 60 39 60 45C60 51 61.7 55 65 55C68.3 55 70 51 70 45C70 39 68.3 35 65 35Z" stroke="#3F3F45" stroke-width="3"/>
</svg>"""

# Converter SVG para base64
import base64
favicon_b64 = base64.b64encode(favicon_svg.encode('utf-8')).decode()

# Configurar a página
st.set_page_config(
    page_title="ValueHunter - Análise de Apostas Esportivas",
    page_icon="📊",  # Mantém o emoji como fallback para navegadores que não suportam SVG
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Inserir o favicon SVG logo após a configuração da página
favicon_html = f"""
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{favicon_b64}">
<link rel="shortcut icon" type="image/svg+xml" href="data:image/svg+xml;base64,{favicon_b64}">
"""
st.markdown(favicon_html, unsafe_allow_html=True)
print("Favicon SVG inserido diretamente no HTML!")

# Tentar inserir o favicon SVG
try:
    if favicon_path and os.path.exists(favicon_path):
        with open(favicon_path, "rb") as f:
            favicon_data = f.read()
        favicon_b64 = base64.b64encode(favicon_data).decode()
        favicon_html = f"<link rel='icon' type='image/svg+xml' href='data:image/svg+xml;base64,{favicon_b64}'>"
        st.markdown(favicon_html, unsafe_allow_html=True)
        print("Favicon inserido com sucesso")
    else:
        # NOVO: Tente usar o caminho específico do Render
        if "RENDER" in os.environ and os.path.exists(favicon_path_render):
            with open(favicon_path_render, "rb") as f:
                favicon_data = f.read()
            favicon_b64 = base64.b64encode(favicon_data).decode()
            favicon_html = f"<link rel='icon' type='image/svg+xml' href='data:image/svg+xml;base64,{favicon_b64}'>"
            st.markdown(favicon_html, unsafe_allow_html=True)
            print("Favicon inserido com sucesso via caminho Render")
        else:
            print("Nenhum caminho para o favicon encontrado")
except Exception as e:
    print(f"Erro ao inserir favicon: {str(e)}")

# Função auxiliar para converter arquivo em base64
def _get_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Erro ao carregar {path}: {str(e)}")
        return ""

# Carregar logo
_LOGO_B64 = ""
if logo_path and os.path.exists(logo_path):
    _LOGO_B64 = _get_base64(logo_path)
    print(f"Logo carregado com sucesso: {logo_path}")
else:
    # NOVO: Tente usar o caminho específico do Render
    if "RENDER" in os.environ and os.path.exists(logo_path_render):
        _LOGO_B64 = _get_base64(logo_path_render)
        print(f"Logo carregado com sucesso via caminho Render: {logo_path_render}")
    else:
        print(f"Arquivo de logo não encontrado ou caminho inválido")

# === 2. SETUP DE LOGS ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("valueHunter")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
try:
    logger.info(f"Directory contents: {os.listdir('.')}")
except Exception as e:
    logger.error(f"Erro ao listar diretório: {str(e)}")

# Aplicar CSS para ocultar elementos de navegação - sem strings triplas
css = (
    "<style>"
    "[data-testid='stSidebarNavItems'] {display: none !important;}"
    "section[data-testid='stSidebarUserContent'] {margin-top: 0 !important;}"
    "div[class*='st-emotion-cache-16idsys'], "
    "div[class*='st-emotion-cache-1cypcdb'], "
    "div[class*='st-emotion-cache-vk3wp9'], "
    "div[class*='st-emotion-cache-ue6h4q'], "
    "div[class*='st-emotion-cache-jnd7a1'] {display: none !important;}"
    "header[data-testid='stHeader'], button[kind='header'], #MainMenu, footer "
    "{display: none !important;}"
    "[data-testid='stSidebar'] {display: block !important; visibility: visible !important; opacity: 1 !important;}"
    "div.stButton > button, button.css-1rs6os.edgvbvh3 {"
    "background-color: #fd7014 !important;"
    "color: #FFFFFF !important;"
    "border: none !important;"
    "border-radius: 4px;"
    "font-weight: bold;"
    "transition: background-color 0.3s ease;"
    "}"
    "div.stButton > button:hover, button.css-1rs6os.edgvbvh3:hover {"
    "background-color: #27272a !important;"
    "color: white !important;"
    "}"
    "</style>"
)
st.markdown(css, unsafe_allow_html=True)

# Tela de carregamento simplificada
loading_css = (
    "<style>"
    "#loading-spinner {position: fixed; top: 0; left: 0; width: 100%; height: 100%;"
    "background-color: #1a1a1a; display: flex; justify-content: center;"
    "align-items: center; z-index: 9999; transition: opacity 0.5s;}"
    ".spinner {width: 50px; height: 50px; border: 5px solid #fd7014;"
    "border-top: 5px solid transparent; border-radius: 50%;"
    "animation: spin 1s linear infinite;}"
    "@keyframes spin {0% {transform: rotate(0deg);} 100% {transform: rotate(360deg);}}"
    "</style>"
    "<div id='loading-spinner'><div class='spinner'></div></div>"
    "<script>"
    "setTimeout(function() {"
    "document.getElementById('loading-spinner').style.opacity = '0';"
    "setTimeout(function() {"
    "document.getElementById('loading-spinner').style.display = 'none';"
    "}, 500);"
    "}, 2000);"
    "</script>"
)
st.components.v1.html(loading_css, height=0)

# Importar módulos de utilidade - colocado antes da configuração do Streamlit
from utils.core import (
    DATA_DIR, init_session_state, show_valuehunter_logo, 
    configure_sidebar_visibility, apply_global_css, init_stripe,
    check_payment_success, handle_stripe_errors, apply_custom_styles,
    remove_loading_screen, apply_responsive_styles, hide_sidebar_completely
)
from utils.data import UserManager

# Criar diretório de dados se não existir
os.makedirs(DATA_DIR, exist_ok=True)
logger.info(f"Diretório de dados configurado: {DATA_DIR}")
logger.info(f"Conteúdo do diretório de dados: {os.listdir(DATA_DIR) if os.path.exists(DATA_DIR) else 'Diretório não existe'}")

# Importar funções e classes principais
from utils.core import (
    go_to_login, go_to_register, go_to_landing,
    get_base_url, redirect_to_stripe, update_purchase_button
)
from pages.dashboard import show_main_dashboard
from pages.landing import show_landing_page
from pages.auth import show_login, show_register, show_verification, show_password_recovery, show_password_reset_code, show_password_reset
from pages.packages import show_packages_page

# Função para modo de debug
def enable_debug_mode():
    """Ativa o modo de debug para ajudar na resolução de problemas"""
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False
        
    # Verificar se o modo de debug deve ser ativado
    if st.sidebar.checkbox("Modo de Debug", value=st.session_state.debug_mode):
        st.session_state.debug_mode = True
        st.session_state.use_sample_data = True
        
        st.sidebar.success("Modo de debug ativado")
        
        # Exibir informações de debug
        if st.sidebar.checkbox("Mostrar informações do sistema"):
            st.sidebar.subheader("Informações do Sistema")
            st.sidebar.info(f"Python: {sys.version}")
            st.sidebar.info(f"Diretório: {os.getcwd()}")
            st.sidebar.info(f"DATA_DIR: {DATA_DIR}")
            
        # Exibir logs recentes
        if st.sidebar.checkbox("Mostrar logs recentes"):
            st.sidebar.subheader("Logs Recentes")
            try:
                log_file = "valueHunter.log"
                if os.path.exists(log_file):
                    with open(log_file, "r") as f:
                        logs = f.readlines()[-20:]  # Últimas 20 linhas
                    for log in logs:
                        st.sidebar.text(log.strip())
                else:
                    st.sidebar.warning("Arquivo de log não encontrado")
            except Exception as e:
                st.sidebar.error(f"Erro ao ler logs: {str(e)}")
        
        # Ativar dados de exemplo
        st.session_state.use_sample_data = st.sidebar.checkbox(
            "Usar dados de exemplo", 
            value=st.session_state.get("use_sample_data", True)
        )
        
        # Permitir forçar reload do cache
        if st.sidebar.button("Limpar cache"):
            import glob
            cache_files = glob.glob(os.path.join(DATA_DIR, "cache_*.html"))
            for f in cache_files:
                try:
                    os.remove(f)
                    st.sidebar.success(f"Removido: {os.path.basename(f)}")
                except Exception as e:
                    st.sidebar.error(f"Erro ao remover {f}: {str(e)}")
    else:
        st.session_state.debug_mode = False

# Função principal
def main():
    """Função principal que controla o fluxo do aplicativo"""
    try:
        # NOVO: Diagnóstico de arquivos
        print("\n===== DIAGNÓSTICO DE ARQUIVOS =====")
        print(f"Diretório atual: {os.getcwd()}")
        try:
            print(f"Arquivos no diretório atual: {os.listdir(os.getcwd())}")
        except Exception as e:
            print(f"Erro ao listar diretório: {str(e)}")

        print(f"3F3F45.png existe? {os.path.exists(os.path.join(os.getcwd(), '3F3F45.png'))}")
        print(f"favicon_svg.svg existe? {os.path.exists(os.path.join(os.getcwd(), 'favicon_svg.svg'))}")

        # Verificar caso-sensitivo
        print("\nVerificação de maiúsculas/minúsculas:")
        try:
            for arquivo in os.listdir(os.getcwd()):
                if arquivo.lower() in ['3f3f45.png', 'favicon_svg.svg']:
                    print(f"Encontrado: {arquivo} (nome exato no disco)")
        except Exception as e:
            print(f"Erro na verificação caso-sensitiva: {str(e)}")
        print("===================================\n")
        
        # Verificar se precisamos fechar a janela atual
        if 'close_window' in st.query_params and st.query_params.close_window == 'true':
            st.components.v1.html("""
                <script>
                    window.opener && window.opener.postMessage('payment_complete', '*');
                    window.close();
                </script>
            """, height=0)
            st.success("Pagamento concluído! Você pode fechar esta janela.")
            return
            
        # Initialize session state com valores padrão
        init_session_state()
        
        # Ativar modo de debug se necessário
        enable_debug_mode()
        
        # Initialize Stripe
        init_stripe()
        
        # Check for payment from popup
        popup_payment = False
        if 'check_payment' in st.query_params and st.query_params.check_payment == 'true':
            popup_payment = True
        
        # Handle page routing
        if popup_payment and st.session_state.authenticated:
            check_payment_success()
            
        # Regular payment callback check
        payment_result = check_payment_success()
        
        # Stripe error handling
        handle_stripe_errors()
        
        # Roteamento para páginas
        if "page" in st.session_state:
            page = st.session_state.page
            
            # Configurar CSS e visibilidade da barra lateral com base na página
            if page in ["landing", "login", "register", "verification", 
                       "password_recovery", "password_reset_code", "password_reset"]:
                # Páginas de autenticação - ocultar totalmente a barra lateral
                st.markdown("""
                <style>
                [data-testid="stSidebar"] {
                    display: none !important;
                }
                </style>
                """, unsafe_allow_html=True)
            else:
                # Outras páginas - configurar barra lateral normalmente
                configure_sidebar_visibility()
                
            # Aplicar CSS global - versão simplificada
            apply_global_css()
            
            # Roteamento para a página correta
            if page == "landing":
                show_landing_page()
            elif page == "login":
                show_login()
            elif page == "register":
                show_register()
            elif page == "verification":
                show_verification()
            elif page == "password_recovery":
                show_password_recovery()
            elif page == "password_reset_code":
                show_password_reset_code()
            elif page == "password_reset":
                show_password_reset()
            elif page == "main":
                if st.session_state.authenticated:
                    # Aplicar estilo responsivo
                    apply_custom_styles()
                    show_main_dashboard()
                else:
                    go_to_login()
            elif page == "admin":
                # Verificar se é admin antes de mostrar (implementação futura)
                if st.session_state.authenticated:
                    try:
                        from pages._admin import show_admin_panel
                        show_admin_panel()
                    except Exception as e:
                        logger.error(f"Erro ao carregar painel admin: {str(e)}")
                        st.error("Erro ao carregar painel administrativo")
                else:
                    go_to_login()
            elif page == "packages":
                if st.session_state.authenticated:
                    show_packages_page()
                else:
                    go_to_login()
            else:
                # Página desconhecida, voltar para a landing
                st.session_state.page = "landing"
                st.experimental_rerun()
        else:
            # Estado da sessão não inicializado, voltar para a landing
            st.session_state.page = "landing"
            st.experimental_rerun()
        
        # Remover a tela de carregamento quando tudo estiver pronto
        remove_loading_screen()
        
    except Exception as e:
        logger.error(f"Erro geral na aplicação: {str(e)}")
        import traceback
        traceback.print_exc()
        st.error("Ocorreu um erro inesperado. Por favor, recarregue a página e tente novamente.")
        
        if "debug_mode" in st.session_state and st.session_state.debug_mode:
            with st.expander("Detalhes do erro", expanded=True):
                st.code(traceback.format_exc())

# Executar a aplicação
if __name__ == "__main__":
    try:
        logger.info("Iniciando aplicação ValueHunter")
        main()
    except Exception as e:
        logger.critical(f"Erro fatal na aplicação: {str(e)}")
        st.error("Ocorreu um erro inesperado. Por favor, recarregue a página e tente novamente.")
