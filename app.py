import os
import sys
import logging
import streamlit as st
import time
from datetime import datetime
from utils.core import (
    DATA_DIR, init_session_state, show_valuehunter_logo, 
    configure_sidebar_visibility, apply_global_css, init_stripe,
    check_payment_success, handle_stripe_errors, apply_custom_styles,
    remove_loading_screen, apply_responsive_styles, hide_sidebar_completely,
    remove_top_whitespace, apply_dark_theme
)

# -----------------------------------------------------
# 1. CONFIGURAR FAVICON E TÍTULO DA PÁGINA
# Deve ser a primeira chamada Streamlit do script
# -----------------------------------------------------
st.set_page_config(
    page_title="ValueHunter",
    page_icon="favicon_svg.svg",
    layout="wide"
)

# -----------------------------------------------------
# SOLUÇÃO ULTRA-AGRESSIVA PARA REMOVER ESPAÇO EM BRANCO
# -----------------------------------------------------
st.markdown("""
<style>
/* Solução definitiva - qualquer elemento que possa causar espaço */
.main .block-container,
.css-18e3th9,
.css-1d391kg,
.st-ae, 
.st-af, 
.st-ag, 
.st-ah, 
.st-ai, 
.st-aj, 
.st-ak, 
.st-al,
.css-hxt7ib,
.e1fqkh3o4,
.css-1544g2n.e1fqkh3o4,
.withScreencast,
.main,
.main-content,
.stApp,
[data-testid="stAppViewContainer"] > section,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
section[data-testid*="stBlock"],
div[data-testid*="stBlock"],
[data-testid="stVerticalBlock"],
.element-container:first-child,
.stMarkdown:first-child,
.main section:first-child,
.main .block-container > div:first-child {
    padding-top: 0 !important;
    margin-top: 0 !important;
    gap: 0 !important;
    border-top: 0 !important;
    border-top-width: 0 !important;
}

/* Esconder cabeçalho e outros elementos que ocupam espaço */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
div[data-testid="stTopBanner"] {
    position: absolute !important;
    display: none !important;
    height: 0 !important;
    max-height: 0 !important;
    min-height: 0 !important;
    opacity: 0 !important;
    visibility: hidden !important;
    width: 0 !important;
    z-index: -9999 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Reduzir espaço entre componentes */
.element-container {
    margin-bottom: 10px !important;
}

/* Ajustar toda a hierarquia de elementos a partir da raiz */
html, body, #root, .stApp {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Remover espaço em layouts específicos */
.row-widget.stSelectbox,
.row-widget,
div[data-layout="wide"],
div[data-layout] {
    margin-top: 0 !important;
    padding-top: 0 !important;
    gap: 0 !important;
}

/* Remover espaço da .stAlert utilizada para mensagens na tela */
.stAlert {
    margin-top: 5px !important;
    margin-bottom: 5px !important;
}
</style>
""", unsafe_allow_html=True)

# JavaScript ultra-agressivo para remover espaçamento
js_fix_spacing = """
<script>
    // Função para remover qualquer espaço no topo
    function forceNoTopSpace() {
        // 1. Esconder completamente o cabeçalho
        const headers = document.querySelectorAll('[data-testid="stHeader"], header');
        headers.forEach(el => {
            el.style.display = 'none';
            el.style.height = '0';
            el.style.margin = '0';
            el.style.padding = '0';
            el.style.visibility = 'hidden';
            el.style.position = 'absolute';
            el.style.zIndex = '-9999';
        });
        
        // 2. Remover espaço do contêiner principal
        const mainContainers = document.querySelectorAll('.main .block-container, .css-18e3th9, [data-testid="stAppViewContainer"] > section');
        mainContainers.forEach(el => {
            el.style.paddingTop = '0';
            el.style.marginTop = '0';
            el.style.gap = '0';
        });
        
        // 3. Remover espaço do primeiro elemento em cada seção
        const firstElements = document.querySelectorAll('.main .block-container > div:first-child, .element-container:first-child, .stMarkdown:first-child');
        firstElements.forEach(el => {
            el.style.marginTop = '0';
            el.style.paddingTop = '0';
        });
        
        // 4. Forçar remoção de qualquer margem ou padding no topo de todos elementos principais
        const allMainElements = document.querySelectorAll('section.main, .main, .stApp, section[data-testid="stAppViewContainer"]');
        allMainElements.forEach(el => {
            el.style.paddingTop = '0';
            el.style.marginTop = '0';
        });
        
        // 5. Remover qualquer decoração ou barra de ferramentas
        const decorations = document.querySelectorAll('[data-testid="stDecoration"], [data-testid="stToolbar"], [data-testid="stStatusWidget"]');
        decorations.forEach(el => {
            el.style.display = 'none';
            el.style.height = '0';
            el.style.margin = '0';
            el.style.padding = '0';
        });
        
        // 6. Remover espaço do título específico "VALUE HUNTER Seleção de Times"
        const titles = document.querySelectorAll('h1, h2, h3, .stTitle');
        titles.forEach(el => {
            el.style.marginTop = '0';
            el.style.paddingTop = '0';
        });
    }
    
    // Executar a função em vários momentos
    forceNoTopSpace();
    document.addEventListener('DOMContentLoaded', forceNoTopSpace);
    window.addEventListener('load', forceNoTopSpace);
    
    // Executar periodicamente para garantir que novos elementos também não tenham espaço
    setInterval(forceNoTopSpace, 200);
    
    // Executar depois de carregamentos parciais
    setTimeout(forceNoTopSpace, 100);
    setTimeout(forceNoTopSpace, 500);
    setTimeout(forceNoTopSpace, 1000);
    setTimeout(forceNoTopSpace, 2000);
</script>
"""
st.components.v1.html(js_fix_spacing, height=0)

# Adicione este código no app.py logo após o JS anterior
additional_spacing_fix = """
<style>
/* Solução extremamente específica para qualquer espaço residual */
/* Alvo: Cabeçalho especifico e elementos na página de seleção de times */

/* Reduzir espaçamento ao mínimo absoluto */
.main .block-container,
section[data-testid="stAppViewContainer"] {
    padding-top: 0 !important;
    margin-top: 0 !important;
    min-height: 0 !important;
}

/* Ajustes específicos para o título "VALUE HUNTER" */
h1, h2, h3, h1 *, h2 *, h3 * {
    margin-top: 0 !important;
    padding-top: 0 !important;
    line-height: 1.2 !important;
}

/* Remover espaço de qualquer alerta ou mensagem (como a mensagem de versão mobile) */
.stAlert,
[data-baseweb="notification"],
div[role="alert"],
.info-box,
.css-1aumxhk {
    margin-top: 0 !important;
    padding-top: 3px !important;
    padding-bottom: 3px !important;
}

/* Ajuste para qualquer elemento de notificação na parte superior */
[data-testid="stAppViewContainer"] > section > div:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Compactar espaços entre elementos */
.element-container {
    margin-bottom: 5px !important;
}

/* Fixar elementos específicos da dashboard */
div:has(> .stTitle),
div:has(> h1),
div:has(> h2) {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Remover qualquer margem das primeiras 5 divs */
.main .block-container > div:nth-child(-n+5) {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
</style>

<script>
// Script ultra-específico para a página de seleção de times
document.addEventListener('DOMContentLoaded', function() {
    // Função para ajustar espaçamento de forma extremamente agressiva
    function ultraFix() {
        // Encontrar qualquer título com "VALUE HUNTER" ou "Seleção de Times"
        const titleElements = Array.from(document.querySelectorAll('h1, h2, h3, div'));
        const targetElements = titleElements.filter(el => 
            el.textContent && (
                el.textContent.includes('VALUE') || 
                el.textContent.includes('HUNTER') || 
                el.textContent.includes('Seleção de Times')
            )
        );
        
        // Remover todo espaço acima destes elementos específicos
        targetElements.forEach(el => {
            // Obter todos os elementos pais
            let parent = el.parentElement;
            while (parent && parent.tagName !== 'BODY') {
                parent.style.marginTop = '0';
                parent.style.paddingTop = '0';
                parent = parent.parentElement;
            }
            
            // Ajustar o elemento específico
            el.style.marginTop = '0';
            el.style.paddingTop = '0';
        });
        
        // Remover margens de mensagens de info (versão mobile, liga selecionada)
        const infoMessages = Array.from(document.querySelectorAll('div, p, span')).filter(el => 
            el.textContent && (
                el.textContent.includes('Versão Mobile') || 
                el.textContent.includes('Liga selecionada') ||
                el.textContent.includes('times carregados')
            )
        );
        
        infoMessages.forEach(el => {
            let parent = el;
            // Subir até 5 níveis para ajustar pais
            for (let i = 0; i < 5; i++) {
                if (!parent) break;
                parent.style.marginTop = '0';
                parent.style.paddingTop = '0';
                parent = parent.parentElement;
            }
        });
        
        // Forçar ajuste direto para a main
        const mains = document.querySelectorAll('.main, main');
        mains.forEach(m => {
            m.style.paddingTop = '0';
            m.style.marginTop = '0';
        });
    }
    
    // Executar várias vezes para garantir
    ultraFix();
    setTimeout(ultraFix, 100);
    setTimeout(ultraFix, 500);
    setTimeout(ultraFix, 1000);
    
    // Adicionar listener de mutação para detectar mudanças no DOM
    const observer = new MutationObserver(ultraFix);
    observer.observe(document.body, { 
        childList: true, 
        subtree: true,
        attributes: true
    });
});
</script>
"""
st.components.v1.html(additional_spacing_fix, height=0)

# Favicon SVG (binóculo laranja)
favicon_svg = """
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" rx="10" fill="#fd7014"/>
  <g fill="white" transform="translate(20, 40)">
    <circle cx="15" cy="10" r="12"/>
    <circle cx="45" cy="10" r="12"/>
  </g>
</svg>
"""

# Converter SVG para base64
import base64
favicon_b64 = base64.b64encode(favicon_svg.encode('utf-8')).decode()

# Inserir múltiplos favicons para garantir compatibilidade
favicon_html = f"""
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{favicon_b64}">
<link rel="shortcut icon" href="data:image/svg+xml;base64,{favicon_b64}">
<link rel="apple-touch-icon" href="data:image/svg+xml;base64,{favicon_b64}">
"""
st.markdown(favicon_html, unsafe_allow_html=True)

# Adicionar JavaScript para forçar a atualização do favicon
js_force_favicon = f"""
<script>
// Função para aplicar o favicon
function updateFavicon() {{
  var link = document.querySelector("link[rel*='icon']") || document.createElement('link');
  link.type = 'image/svg+xml';
  link.rel = 'shortcut icon';
  link.href = 'data:image/svg+xml;base64,{favicon_b64}';
  document.getElementsByTagName('head')[0].appendChild(link);
}}

// Aplicar imediatamente
updateFavicon();

// Aplicar novamente após o carregamento completo
window.addEventListener('load', updateFavicon);

// Aplicar várias vezes para garantir
setTimeout(updateFavicon, 500);
setTimeout(updateFavicon, 1500);
</script>
"""

st.components.v1.html(js_force_favicon, height=0)

# -----------------------------------------------------
# 2. CONFIGURAÇÃO DE LOGGING
# -----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("valueHunter")

# Log de diagnóstico
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
try:
    logger.info(f"Directory contents: {os.listdir('.')}")
except Exception as e:
    logger.error(f"Erro ao listar diretório: {e}")

# Importar módulos de utilidade
from utils.core import (
    DATA_DIR, init_session_state, show_valuehunter_logo, 
    configure_sidebar_visibility, apply_global_css, init_stripe,
    check_payment_success, handle_stripe_errors, apply_custom_styles,
    remove_loading_screen, apply_responsive_styles, hide_sidebar_completely
)
from utils.data import UserManager

# -----------------------------------------------------
# 3. ESTILOS BÁSICOS DA APLICAÇÃO
# -----------------------------------------------------

# Aplicar CSS para ocultar elementos de navegação
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

# -----------------------------------------------------
# 4. FUNÇÃO DEFINITIVA PARA REMOVER ESPAÇAMENTO
# -----------------------------------------------------

def remove_all_top_space():
    """
    Função unificada para remover espaços no topo.
    Use no início de cada página para garantir que não haja espaço.
    """
    # Esta injeção de CSS será feita apenas uma vez, não precisa repetir
    # em todas as chamadas da função, pois já aplicamos o CSS principal no início
    pass

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
        # Aplicar tema escuro consistente
        apply_dark_theme()
        
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
