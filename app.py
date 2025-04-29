import os
import os
import logging
import sys
import streamlit as st
import time
from datetime import datetime
import base64

# Remova completamente a função inject_favicon() e use esta abordagem simplificada:

# === 1. CONFIGURAR FAVICON & PAGE CONFIG ===
st.set_page_config(
    page_title="ValueHunter - Análise de Apostas Esportivas",
    page_icon="📊",  # Usando um emoji como favicon temporário
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Função auxiliar para converter arquivo em base64 com tratamento de erro
def _get_base64(path: str) -> str:
    """Converte qualquer arquivo binário em string base64 com segurança."""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.error(f"Erro ao carregar arquivo {path}: {str(e)}")
        return ""

# Verifica se o arquivo existe antes de tentar carregar
logo_path = os.path.join(os.getcwd(), "3F3F45.png")
_LOGO_B64 = ""  # Inicializa vazio por padrão

if os.path.exists(logo_path):
    _LOGO_B64 = _get_base64(logo_path)
    logger.info(f"Logo carregado com sucesso: {logo_path}")
else:
    logger.error(f"Arquivo de logo não encontrado: {logo_path}")

# Tenta injetar o favicon de maneira simples - sem função separada
try:
    favicon_path = os.path.join(os.getcwd(), "favicon_svg.svg")
    if os.path.exists(favicon_path):
        favicon_b64 = _get_base64(favicon_path)
        if favicon_b64:
            st.markdown(
                f'<link rel="icon" href="data:image/svg+xml;base64,{favicon_b64}">',
                unsafe_allow_html=True
            )
            logger.info("Favicon SVG injetado com sucesso")
except Exception as e:
    logger.error(f"Erro ao injetar favicon: {str(e)}")
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

# === 3. LOADING SCREEN CSS ===
loading_css = """
<style>
/* Ocultar tudo do Streamlit durante o loading */
body.loading header,
body.loading footer,
body.loading #MainMenu,
body.loading [data-testid="stSidebar"],
body.loading [data-testid="stToolbar"],
body.loading [data-testid="stDecoration"],
body.loading div.css-1d391kg,
body.loading div.css-12oz5g7,
body.loading .stDeployButton {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
}

/* Container de loading */
.vh-loading-container {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    background-color: #1a1a1a;
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    z-index: 10000;
    transition: opacity 0.6s ease, visibility 0.6s ease;
}

/* Logo dentro do loading */
.vh-logo-container {
    background-color: #fd7014;
    padding: 15px 30px;
    border-radius: 10px;
    display: flex; align-items: center; gap: 15px;
    margin-bottom: 40px;
    box-shadow: 0 4px 15px rgba(253,112,20,0.3);
}
.vh-logo-container img {
    width: 40px; height: 40px;
}
.vh-logo-text {
    font-size: 2.5rem;
    font-weight: bold;
    color: #FFFFFF;
}
/* Spinner */
.vh-loader {
    width: 60px; height: 60px;
    border: 5px solid rgba(253,112,20,0.2);
    border-radius: 50%;
    border-top: 5px solid #fd7014;
    animation: vh-spin 1s linear infinite;
    margin-bottom: 30px;
}
@keyframes vh-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
/* Texto pulsante */
.vh-loading-text {
    color: white; font-size: 18px; font-family: Arial, sans-serif;
    animation: vh-pulse 1.5s infinite;
}
@keyframes vh-pulse {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}
/* Barra de progresso */
.vh-loading-progress {
    width: 200px; height: 4px;
    background-color: rgba(255,255,255,0.1);
    border-radius: 2px; margin-top: 20px;
    position: relative; overflow: hidden;
}
.vh-progress-bar {
    position: absolute; left: 0; top: 0;
    height: 100%; width: 0%;
    background-color: #fd7014; border-radius: 2px;
    transition: width 0.5s ease;
}
</style>
"""
st.markdown(loading_css, unsafe_allow_html=True)

# === 4. LOADING SCREEN HTML + JS ===
loading_screen = f"""
<div class="vh-loading-container" id="vh-loading-screen">
  <div class="vh-logo-container">
    <img src="data:image/png;base64,{_LOGO_B64}" />
    <span class="vh-logo-text">VALUEHUNTER</span>
  </div>
  <div class="vh-loader"></div>
  <div class="vh-loading-text" id="vh-loading-text">Inicializando aplicação...</div>
  <div class="vh-loading-progress">
    <div class="vh-progress-bar" id="vh-progress-bar"></div>
  </div>
</div>

<script>
// Ativa modo 'loading' no body
document.body.classList.add('loading');

const texts = [
  "Inicializando aplicação...",
  "Carregando interface...",
  "Conectando aos serviços...",
  "Preparando análise de apostas...",
  "Quase pronto..."
];
let val=0, idx=0;
const bar = document.getElementById('vh-progress-bar');
const txt = document.getElementById('vh-loading-text');

function update() {{
  if(val<30) {{
    val+=Math.random()*5+3;
  }}
  else if(val<70) {{
    val+=Math.random()*3+1;
  }}
  else if(val<90) {{
    val+=Math.random()*1+0.3;
  }}
  bar.style.width = Math.min(val,95) + '%';
  if(Math.floor(val/20)>idx && idx<texts.length-1){{
    idx++; txt.textContent = texts[idx];
  }}
  if(val<95) setTimeout(update,300+Math.random()*500);
}}
update();

function checkReady(){{
  if(document.querySelector('.stApp') && document.querySelector('.main .block-container')){{
    val=100; bar.style.width='100%'; txt.textContent="Carregamento concluído!";
    setTimeout(()=>{{
      const lg = document.getElementById('vh-loading-screen');
      lg.style.opacity='0'; lg.style.visibility='hidden';
      document.body.classList.remove('loading');
      setTimeout(()=> lg.remove(),700);
    }},1000);
    return true;
  }}
  return false;
}}
const iv = setInterval(()=>{{
  if(checkReady()) clearInterval(iv);
}},200);
setTimeout(()=>{{
  clearInterval(iv);
  const lg = document.getElementById('vh-loading-screen');
  if(lg){{ lg.style.opacity='0'; lg.style.visibility='hidden'; document.body.classList.remove('loading');
    setTimeout(()=>lg.remove(),700);
  }}
}},12000);
</script>
"""
# Renderiza o loading screen
st.components.v1.html(loading_screen, height=0)

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


# Adicionar a tela de carregamento personalizada
loading_html = """
<!-- Código HTML para a tela de carregamento do ValueHunter -->
<style>
/* Ocultar TUDO do Streamlit durante o carregamento */
body.loading header, 
body.loading footer, 
body.loading #MainMenu, 
body.loading [data-testid="stSidebar"], 
body.loading [data-testid="stToolbar"], 
body.loading [data-testid="stDecoration"], 
body.loading div.css-1d391kg, 
body.loading div.css-12oz5g7, 
body.loading .stDeployButton {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
}

.vh-loading-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: #1a1a1a;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 10000;
    transition: opacity 0.6s ease, visibility 0.6s ease;
}

.vh-logo-container {
    background-color: #fd7014;
    padding: 15px 30px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 40px;
    box-shadow: 0 4px 15px rgba(253, 112, 20, 0.3);
}

/* SVG Logo Style */
.vh-logo-svg {
    width: 40px;
    height: 40px;
}

.vh-logo-text {
    font-size: 2.5rem;
    font-weight: bold;
    color: #FFFFFF;
}

/* Spinner de carregamento */
.vh-loader {
    width: 60px;
    height: 60px;
    border: 5px solid rgba(253, 112, 20, 0.2);
    border-radius: 50%;
    border-top: 5px solid #fd7014;
    animation: vh-spin 1s linear infinite;
    margin-bottom: 30px;
}

@keyframes vh-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.vh-loading-text {
    color: white;
    font-size: 18px;
    font-family: Arial, sans-serif;
    animation: vh-pulse 1.5s infinite;
}

@keyframes vh-pulse {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}

.vh-loading-progress {
    width: 200px;
    height: 4px;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    margin-top: 20px;
    overflow: hidden;
    position: relative;
}

.vh-progress-bar {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    width: 0%;
    background-color: #fd7014;
    border-radius: 2px;
    transition: width 0.5s ease;
}
</style>
"""

loading_html = f"""
<div class="vh-loading-container" id="vh-loading-screen">
  <div class="vh-logo-container">
    <!-- Logo na tela de carregamento -->
    {f'<img src="data:image/png;base64,{_LOGO_B64}" style="width:40px; height:40px;" />' if _LOGO_B64 else '<div style="width:40px; height:40px; background-color:#3F3F45; color:white; display:flex; align-items:center; justify-content:center; font-weight:bold; border-radius:5px;">V</div>'}
    <span class="vh-logo-text">VALUEHUNTER</span>
  </div>

  <div class="vh-loader"></div>
  <div class="vh-loading-text" id="vh-loading-text">
    Inicializando aplicação...
  </div>
  <div class="vh-loading-progress">
    <div class="vh-progress-bar" id="vh-progress-bar"></div>
  </div>
</div>
"""


<script>
// Adicionar a classe 'loading' ao body para esconder elementos do Streamlit
document.body.classList.add('loading');

// Textos para mostrar durante o carregamento
const loadingTexts = [
    "Inicializando aplicação...",
    "Carregando interface...",
    "Conectando aos serviços...",
    "Preparando análise de apostas...",
    "Quase pronto..."
];

// Atualizar a barra de progresso e o texto
let progressValue = 0;
let textIndex = 0;
const progressBar = document.getElementById('vh-progress-bar');
const loadingText = document.getElementById('vh-loading-text');

// Função para atualizar o progresso de maneira realista
function updateProgress() {{
    // Se o progresso é pequeno, avanços maiores
    if (progressValue < 30) {{
        progressValue += Math.random() * 5 + 3;
    }} 
    // Progresso médio, avanços médios
    else if (progressValue < 70) {{
        progressValue += Math.random() * 3 + 1;
    }} 
    // Progresso alto, avanços lentos
    else if (progressValue < 90) {{
        progressValue += Math.random() * 1 + 0.3;
    }}
    // Não chegar a 100% até estar realmente pronto
    
    // Atualizar barra de progresso
    progressBar.style.width = Math.min(progressValue, 95) + '%';
    
    // Atualizar texto periodicamente
    if (Math.floor(progressValue / 20) > textIndex && textIndex < loadingTexts.length - 1) {{
        textIndex++;
        loadingText.textContent = loadingTexts[textIndex];
    }}
    
    // Continuar atualizando se não chegou a 100%
    if (progressValue < 95) {{
        setTimeout(updateProgress, 300 + Math.random() * 500);
    }}
}}

// Iniciar o progresso
updateProgress();

// Função para verificar se o app do Streamlit foi carregado
function checkAppReady() {{
    // Verificar elementos que indicam que o app está pronto
    if (document.querySelector('.stApp') && 
        document.querySelector('.main .block-container')) {{
        // Completar o progresso
        progressValue = 100;
        progressBar.style.width = '100%';
        loadingText.textContent = "Carregamento concluído!";
        
        // Esperar um momento e então fazer o fade out
        setTimeout(() => {{
            const loadingScreen = document.getElementById('vh-loading-screen');
            if (loadingScreen) {{
                loadingScreen.style.opacity = '0';
                loadingScreen.style.visibility = 'hidden';
                
                // Remover a classe 'loading' do body
                document.body.classList.remove('loading');
                
                // Depois da transição, remover completamente
                setTimeout(() => {{
                    loadingScreen.remove();
                    
                    // Ocultar novamente os elementos de navegação, para garantir
                    document.querySelectorAll('[data-testid="stSidebarNavItems"], .st-emotion-cache-16idsys, .st-emotion-cache-1cypcdb, header[data-testid="stHeader"], footer, #MainMenu').forEach(el => {{
                        if (el) el.style.display = 'none';
                    }});
                }}, 700);
            }}
        }}, 1000);
        
        return true;
    }}
    return false;
}}

// Verificar periodicamente se o app está pronto
const readyInterval = setInterval(() => {{
    if (checkAppReady()) {{
        clearInterval(readyInterval);
    }}
}}, 200);

// Escape hatch - remover o loading depois de 10 segundos de qualquer forma
setTimeout(() => {{
    clearInterval(readyInterval);
    const loadingScreen = document.getElementById('vh-loading-screen');
    if (loadingScreen) {{
        loadingScreen.style.opacity = '0';
        loadingScreen.style.visibility = 'hidden';
        document.body.classList.remove('loading');
        
        setTimeout(() => {{
            loadingScreen.remove();
        }}, 700);
    }}
}}, 12000);
</script>
"""
st.components.v1.html(loading_html, height=0)

# Aplicar CSS imediatamente após o set_page_config para ocultar a navegação

st.markdown("""
<style>
/* Ocultar completamente o menu de navegação lateral */
[data-testid="stSidebarNavItems"] {
    display: none !important;
}
section[data-testid="stSidebarUserContent"] {
    margin-top: 0 !important;
}
/* Seletores adicionais para ocultar a navegação, incluindo versões mais recentes */
div[class*="st-emotion-cache-16idsys"], 
div[class*="st-emotion-cache-1cypcdb"],
div[class*="st-emotion-cache-vk3wp9"],
div[class*="st-emotion-cache-ue6h4q"],
div[class*="st-emotion-cache-jnd7a1"] {
    display: none !important;
}
/* Ocultar o menu principal e o botão de navegação */
header[data-testid="stHeader"],
button[kind="header"],
#MainMenu,
footer {
    display: none !important;
}
/* Garantir que a barra lateral em si permanece visível */
[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

# Importar e disponibilizar funções e classes principais
from utils.core import (
    go_to_login, go_to_register, go_to_landing,
    get_base_url, redirect_to_stripe, update_purchase_button
)
from pages.dashboard import show_main_dashboard
from pages.landing import show_landing_page
from pages.auth import show_login, show_register, show_verification, show_password_recovery, show_password_reset_code, show_password_reset
from pages.packages import show_packages_page

# Adicionar script JavaScript para ocultar a navegação dinamicamente
# Substitua o script JavaScript que está ocultando os itens de navegação por este:

# Substitua o script JavaScript com os comentários corrigidos:

# Substitua todo o bloco js_ocultacao por esta versão mais segura:

js_ocultacao = """
<script>
    /* Função para remover elementos do menu de navegação */
    function hideNavItems() {
        /* Encontrar e ocultar elementos de navegação */
        const navItems = document.querySelectorAll('[data-testid="stSidebarNavItems"]');
        navItems.forEach(item => {
            item.style.display = 'none';
        });
        
        /* Procurar por outros seletores possíveis */
        const otherClasses = [
            'st-emotion-cache-16idsys', 
            'st-emotion-cache-1cypcdb',
            'st-emotion-cache-vk3wp9',
            'st-emotion-cache-ue6h4q',
            'st-emotion-cache-jnd7a1',
            'st-emotion-cache-pbk8do'
        ];
        
        otherClasses.forEach(className => {
            document.querySelectorAll('div[class*="' + className + '"]').forEach(el => {
                if (el) el.style.display = 'none';
            });
        });
        
        /* Ocultar outros elementos */
        document.querySelectorAll('header[data-testid="stHeader"], footer, #MainMenu').forEach(el => {
            if (el) el.style.display = 'none';
        });
    }
    
    /* Executar imediatamente */
    hideNavItems();
    
    /* Executar novamente após o carregamento completo da página */
    window.addEventListener('load', hideNavItems);
    
    /* Executar periodicamente por alguns segundos */
    let attempts = 0;
    const interval = setInterval(function() {
        hideNavItems();
        attempts++;
        if (attempts >= 10) clearInterval(interval);
    }, 500);
</script>
"""
st.components.v1.html(js_ocultacao, height=0)

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

# Inicialização de configurações globais
def initialize_app_state():
    """Inicializa o estado do aplicativo com valores padrão"""
    from utils.data import UserManager
    
    if 'initialized' not in st.session_state:
        # Estado de navegação
        if 'page' not in st.session_state:
            st.session_state.page = 'landing'  # Página inicial padrão
        
        # Estado de autenticação - manter valores existentes se já definidos
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'email' not in st.session_state:
            st.session_state.email = None
        
        # Variáveis para controle de sessão
        if "last_activity" not in st.session_state:
            st.session_state.last_activity = datetime.now()
        elif (datetime.now() - st.session_state.last_activity).total_seconds() > 3600:  # 1 hora
            st.session_state.authenticated = False
            st.session_state.email = None
            st.warning("Sua sessão expirou. Por favor, faça login novamente.")
        
        # Variáveis para a página de landing
        if "show_register" not in st.session_state:
            st.session_state.show_register = False
        
        # Variáveis para o checkout integrado
        if "show_checkout" not in st.session_state:
            st.session_state.show_checkout = False
        
        if "checkout_credits" not in st.session_state:
            st.session_state.checkout_credits = 0
            
        if "checkout_amount" not in st.session_state:
            st.session_state.checkout_amount = 0
            
        if "last_stripe_session_id" not in st.session_state:
            st.session_state.last_stripe_session_id = None
        
        # Stripe test mode flag
        if "stripe_test_mode" not in st.session_state:
            st.session_state.stripe_test_mode = True
        
        # Variáveis para recuperação de senha
        if "recovery_email" not in st.session_state:
            st.session_state.recovery_email = None
        
        if "code_verified" not in st.session_state:
            st.session_state.code_verified = False
        
        # Modo de depuração
        if "debug_mode" not in st.session_state:
            st.session_state.debug_mode = False
        
        # Estado da sidebar
        if 'sidebar_expanded' not in st.session_state:
            st.session_state.sidebar_expanded = True
            
        # Registrar que inicializamos
        st.session_state.initialized = True
        
        # UserManager deve ser o último a ser inicializado
        if "user_manager" not in st.session_state:
            st.session_state.user_manager = UserManager()
        
        logger.info("Estado do aplicativo inicializado com valores padrão")
    
    # Atualizar timestamp de última atividade
    st.session_state.last_activity = datetime.now()

# Função para gerenciar a navegação entre páginas
def handle_navigation():
    """Gerencia transições entre páginas e atualiza dados quando necessário"""
    # Verificar se é necessário recarregar dados do usuário ao navegar
    current_page = st.session_state.page
    previous_page = st.session_state.get('previous_page')
    
    if (current_page != previous_page and 
        st.session_state.authenticated and st.session_state.email):
        
        # Recarregar dados ao mudar entre páginas principais
        try:
            # Recarregar a classe UserManager para garantir dados atualizados
            from utils.data import UserManager
            st.session_state.user_manager = UserManager()
            # Limpar qualquer cache que possa existir para estatísticas
            if hasattr(st.session_state, 'user_stats_cache'):
                del st.session_state.user_stats_cache
            # Log da atualização
            logger.info(f"Dados de usuário recarregados na transição de {previous_page} para {current_page}")
        except Exception as e:
            logger.error(f"Erro ao atualizar dados do usuário: {str(e)}")
    
    # Atualizar página anterior para a próxima navegação
    st.session_state.previous_page = current_page

# Roteamento central de páginas
# Modifique a função route_pages() no app.py para remover a chamada ao configure_sidebar_toggle
def route_pages():
    """Função central de roteamento para todas as páginas do aplicativo"""
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
            
        # Aplicar CSS global
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
                # NÃO CHAMAR configure_sidebar_toggle() - foi removido
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

# Função principal
def main():
    """Função principal que controla o fluxo do aplicativo"""
    try:
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
        initialize_app_state()
        
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
        
        # Processar navegação entre páginas
        handle_navigation()
        
        # Roteamento de páginas
        route_pages()
        
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
