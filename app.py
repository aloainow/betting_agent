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
    remove_loading_screen, apply_responsive_styles, hide_sidebar_completely, apply_dark_theme
)

# -----------------------------------------------------
# 1. CONFIGURAR FAVICON E TÍTULO DA PÁGINA
# Deve ser a primeira chamada Streamlit do script
# -----------------------------------------------------
st.set_page_config(
    page_title="ValueHunter",
    page_icon="favicon_svg.svg",   # Corrigido para usar o arquivo .svg
    layout="wide"
)

# AGORA injetamos o CSS para remover espaçamento DEPOIS da configuração da página
st.markdown("""
<style>
/* SOLUÇÃO ULTRA AGRESSIVA PARA ESPAÇO EM BRANCO - aplicada globalmente */
/* Reset de todos os espaçamentos em todos os elementos */
body, html, .stApp, .main, .main .block-container, div[data-testid="stAppViewContainer"], div[data-testid="stVerticalBlock"] {
    margin-top: 0 !important;
    padding-top: 0 !important;
    gap: 0 !important;
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}

/* Remover completamente o cabeçalho do Streamlit */
header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    visibility: hidden !important;
    position: absolute !important;
    z-index: -9999 !important;
    opacity: 0 !important;
    width: 0 !important;
}

/* Remover todos os elementos decorativos e espaços extras */
[data-testid="stDecoration"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
[data-testid="stSidebarNavItems"],
div[data-testid~="injected"] {
    display: none !important;
    height: 0 !important;
    width: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    visibility: hidden !important;
    position: absolute !important;
    z-index: -9999 !important;
}

/* Corrigir a altura do contêiner principal */
.main .block-container {
    max-width: 100% !important;
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* Forçar primeiro elemento a começar no topo absoluto */
.main .block-container > div:first-child,
.element-container:first-child,
.stMarkdown:first-child,
section.main > div:first-child,
div[data-testid="stVerticalBlock"] > div:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Zerar margens e paddings de todos primeiros filhos */
*:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Reset para layout de gaps e grids */
div[data-layout] {
    gap: 0 !important;
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Reduzir ainda mais o espaço entre elementos */
.stMarkdown, .stText, .stTitle, .element-container {
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* Remover espaço entre colunas e linhas */
div[data-layout="grid"] {
    gap: 0.5rem !important;
}

/* Ajustar espaçamento de widgets */
.stButton, .stSelectbox, .stTextInput, .stNumberInput {
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* Forçar remoção de espaço no topo da página */
.stApp > header + div > div:first-child,
.main > div:first-child,
.main .block-container > div:first-child,
.stApp [data-testid="stAppViewBlockContainer"] > div:first-child,
[data-testid="collapsedControl"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
section.main > div:first-child,
div[data-testid="stVerticalBlock"] > div:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
    min-height: 0 !important;
}

/* Remover decorações no topo */
.stApp::before,
.stApp::after {
    display: none !important;
}

/* Resetar layout e gaps */
.stApp [data-testid="stAppViewContainer"],
.stApp [data-testid="stAppViewContainer"] > section {
    gap: 0 !important;
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Remover espaço em todos os elementos */
div, p, h1, h2, h3, h4, h5, h6, ul, ol, li, span, a, button, input, select, textarea {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# Favicon SVG (binóculo laranja)
favicon_svg = """
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" rx="20" fill="#fd7014"/>
  <g fill="white" transform="translate(20, 30) scale(1.5)">
    <ellipse cx="12" cy="20" rx="7" ry="8"/>
    <ellipse cx="28" cy="20" rx="7" ry="8"/>
    <path d="M12 15C10 15 9 17 9 20C9 23 10 25 12 25C14 25 15 23 15 20C15 17 14 15 12 15ZM28 15C26 15 25 17 25 20C25 23 26 25 28 25C30 25 31 23 31 20C31 17 30 15 28 15Z" stroke="#fd7014" stroke-width="1.5"/>
    <path d="M20 17V23M17 20H23" stroke="#fd7014" stroke-width="1.5"/>
  </g>
</svg>
"""

# Converter SVG para base64
import base64
favicon_b64 = base64.b64encode(favicon_svg.encode('utf-8')).decode()

# Inserir múltiplas versões do favicon para garantir compatibilidade em diferentes navegadores
# Favicon baseado no logo ValueHunter
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

# Importar módulos de utilidade - colocado antes da configuração do Streamlit
from utils.core import (
    DATA_DIR, init_session_state, show_valuehunter_logo, 
    configure_sidebar_visibility, apply_global_css, init_stripe,
    check_payment_success, handle_stripe_errors, apply_custom_styles,
    remove_loading_screen, apply_responsive_styles, hide_sidebar_completely
)
from utils.data import UserManager

# -----------------------------------------------------
# 3. EXIBIR LOGO
# -----------------------------------------------------

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

# Função para remover todos os espaçamentos
def remove_all_spacing():
    """Remove completamente todos os espaços em branco no início da página em toda a aplicação"""
    
    
    st.markdown("""
    <style>
    /* Reset completo de todos os espaçamentos iniciais */
    .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remover completamente o header do Streamlit */
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        position: absolute !important;
    }
    
    /* Remover espaçamento de todos os elementos no topo */
    .stApp > header + div > div:first-child,
    .main > div:first-child,
    .main .block-container > div:first-child,
    .stApp [data-testid="stAppViewBlockContainer"] > div:first-child,
    [data-testid="collapsedControl"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    section.main > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
        min-height: 0 !important;
    }
    
    /* Definir margens zero para o primeiro elemento de diferentes tipos no início da página */
    .stMarkdown:first-child, 
    .stText:first-child,
    .stTitle:first-child,
    .element-container:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remover decorações no topo */
    .stApp::before,
    .stApp::after {
        display: none !important;
    }
    
    /* Resetar layout e gaps */
    .stApp [data-testid="stAppViewContainer"],
    .stApp [data-testid="stAppViewContainer"] > section {
        gap: 0 !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
                
        # CORREÇÃO DEFINITIVA DO ESPAÇO EM BRANCO - Aplicar imediatamente
        st.markdown("""
        <style>
        /* SOLUÇÃO ULTRA AGRESSIVA PARA ESPAÇO EM BRANCO - aplicada globalmente */
        /* Reset de todos os espaçamentos em todos os elementos */
        body, html, .stApp, .main, .main .block-container, div[data-testid="stAppViewContainer"], div[data-testid="stVerticalBlock"] {
            margin-top: 0 !important;
            padding-top: 0 !important;
            gap: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Remover completamente o cabeçalho */
        header[data-testid="stHeader"] {
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
            visibility: hidden !important;
            position: absolute !important;
            z-index: -9999 !important;
            width: 0 !important;
        }
        
        /* Forçar primeiro elemento a começar no topo absoluto */
        .main .block-container > div:first-child,
        .element-container:first-child,
        .stMarkdown:first-child,
        section.main > div:first-child,
        div[data-testid="stVerticalBlock"] > div:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* Corrigir altura do container principal */
        .main .block-container {
            max-width: 100% !important; 
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        /* Remover espaço em todos os elementos */
        div, p, h1, h2, h3, h4, h5, h6, ul, ol, li, span, a, button, input, select, textarea {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* SOLUÇÃO EXTREMA - Remover todos os espaços em branco */
        * {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Forçar todos os containers a começarem no topo absoluto */
        .stApp {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* Remover espaço entre elementos */
        .element-container {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Remover espaço em todos os widgets do Streamlit */
        .stButton, .stCheckbox, .stRadio, .stSelectbox, .stSlider, .stText, .stTextInput, .stTextArea {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Remover espaço em todos os containers */
        .stContainer, .stColumn, .stColumns, .stExpander, .stTabs, .stTab {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Remover espaço em todos os elementos de texto */
        .stMarkdown, .stTitle, .stHeader, .stSubheader, .stText, .stCaption {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Remover espaço em todos os elementos de formulário */
        .stForm, .stFormSubmit, .stFileUploader {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Remover espaço em todos os elementos de visualização */
        .stPlot, .stDataFrame, .stTable, .stJson, .stImage, .stAudio, .stVideo {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Remover espaço em todos os elementos de layout */
        .stSidebar, .stMain, .stContent, .stContainer {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Remover espaço em todos os elementos de navegação */
        .stTabs, .stTab, .stTabContent {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Adicionar um JavaScript que reforça a remoção de espaços
        st.components.v1.html("""
        <script>
        // Função que remove ativamente espaços em branco
        function removeSpaces() {
            // Forçar reset de todos os elementos que possam causar espaço
            document.querySelectorAll('*').forEach(el => {
                el.style.marginTop = '0';
                el.style.paddingTop = '0';
                el.style.marginBottom = '0';
                el.style.paddingBottom = '0';
            });
            
            // Remover especificamente o cabeçalho
            const header = document.querySelector('header[data-testid="stHeader"]');
            if (header) {
                header.style.display = 'none';
                header.style.height = '0';
                header.style.minHeight = '0';
                header.style.maxHeight = '0';
                header.style.visibility = 'hidden';
            }
            
            // Forçar o primeiro elemento a começar no topo absoluto
            const firstElements = document.querySelectorAll('.main .block-container > div:first-child, .element-container:first-child, .stMarkdown:first-child, section.main > div:first-child, div[data-testid="stVerticalBlock"] > div:first-child');
            firstElements.forEach(el => {
                el.style.marginTop = '0';
                el.style.paddingTop = '0';
            });
            
            // Remover espaço em todos os containers
            const containers = document.querySelectorAll('.stApp, .main, .main .block-container, div[data-testid="stAppViewContainer"], div[data-testid="stVerticalBlock"]');
            containers.forEach(el => {
                el.style.marginTop = '0';
                el.style.paddingTop = '0';
                el.style.gap = '0';
            });
            
            // Remover cabeçalho por completo
            const headerElement = document.querySelector('header[data-testid="stHeader"]');
            if (headerElement) headerElement.style.display = 'none';
            
            // Remover espaço entre widgets
            const widgets = document.querySelectorAll('.stButton, .stCheckbox, .stRadio, .stSelectbox, .stSlider, .stText, .stTextInput, .stTextArea');
            widgets.forEach(el => {
                el.style.marginTop = '0';
                el.style.paddingTop = '0';
                el.style.marginBottom = '0';
                el.style.paddingBottom = '0';
            });
        }
        
        // Executar a função imediatamente
        removeSpaces();
        
        // Executar novamente após o carregamento completo
        window.addEventListener('load', removeSpaces);
        
        // Executar periodicamente para garantir que novos elementos também sejam afetados
        setInterval(removeSpaces, 100);
        </script>
        """, unsafe_allow_html=True)
        
        // Executar imediatamente
        removeSpaces();
        
        // Executar novamente após carregamento
        window.addEventListener('load', removeSpaces);
        
        // Executar a cada 100ms por um curto período para garantir
        let attempts = 0;
        const interval = setInterval(() => {
            removeSpaces();
            attempts++;
            if (attempts > 20) clearInterval(interval);
        }, 100);
        </script>
        """, height=0)
        
        
        # NOVO: Diagnóstico de arquivos
        print("\nDiagnóstico de arquivos:")
        print(f"Diretório atual: {os.getcwd()}")
        print(f"Arquivos na raiz: {os.listdir('.')}")
        print(f"Arquivos em utils: {os.listdir('./utils') if os.path.exists('./utils') else 'Diretório não existe'}")
        print(f"Arquivos em pages: {os.listdir('./pages') if os.path.exists('./pages') else 'Diretório não existe'}")
        
        # Inicializar estado da sessão
        init_session_state()
        
        # Configurar visibilidade da barra lateral
        configure_sidebar_visibility()
        
        # Aplicar estilos globais
        apply_global_css()
        
        # Aplicar estilos personalizados
        apply_custom_styles()
        
        # Aplicar estilos responsivos
        apply_responsive_styles()
        
        # Remover tela de carregamento
        remove_loading_screen()
        
        # Inicializar Stripe
        init_stripe()
        
        # Verificar se há um código de pagamento na URL
        check_payment_success()
        
        # Ativar modo de debug se necessário
        enable_debug_mode()
        
        # Determinar qual página mostrar com base no estado da sessão
        if st.session_state.get("page") == "login":
            show_login()
        elif st.session_state.get("page") == "register":
            show_register()
        elif st.session_state.get("page") == "verification":
            show_verification()
        elif st.session_state.get("page") == "password_recovery":
            show_password_recovery()
        elif st.session_state.get("page") == "password_reset_code":
            show_password_reset_code()
        elif st.session_state.get("page") == "password_reset":
            show_password_reset()
        elif st.session_state.get("page") == "dashboard":
            show_main_dashboard()
        elif st.session_state.get("page") == "packages":
            show_packages_page()
        else:
            # Página inicial (landing)
            show_landing_page()
            
    except Exception as e:
        st.error(f"Erro na aplicação: {str(e)}")
        logger.error(f"Erro na aplicação: {str(e)}")
        
        # Mostrar detalhes do erro em modo de debug
        if st.session_state.get("debug_mode", False):
            import traceback
            st.code(traceback.format_exc())

# Executar a função principal
if __name__ == "__main__":
    main()
