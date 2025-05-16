# utils/core.py - Funções Principais
import os
import json
import time
import logging
import streamlit as st
from datetime import datetime, timedelta
from urllib.parse import urlencode
import base64


# Importando dependências
try:
    import stripe
except ImportError:
    # Dummy stripe para caso de falha no import
    class DummyStripe:
        api_key = None
        class checkout:
            class Session:
                @staticmethod
                def create(**kwargs):
                    return type('obj', (object,), {'id': 'dummy_session', 'url': '#'})
                @staticmethod
                def retrieve(session_id):
                    return type('obj', (object,), {'payment_status': 'unpaid', 'metadata': {'credits': '0', 'email': ''}})
        class error:
            class InvalidRequestError(Exception):
                pass
    stripe = DummyStripe
# Configuração de logging
logger = logging.getLogger("valueHunter.core")
# Configurações globais
DATA_DIR = "data"
if "RENDER" in os.environ:
    # Em produção no Render, use um caminho padrão para montagem de disco
    DATA_DIR = "/mnt/value-hunter-data"  # Caminho padrão para discos persistentes

# Ocultar mensagens de erro relacionadas a secrets.toml
def hide_streamlit_errors():
    st.markdown("""
    <style>
    /* Ocultar mensagens de erro sobre secrets */
    [data-testid="stException"],
    div[data-stale="false"][data-testid="stStatusWidget"],
    div.stException,
    .element-container div.stAlert[kind="error"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Chamar a função para ocultar erros quando o módulo é importado
try:
    hide_streamlit_errors()
except:
    pass  # Ignorar erros se o contexto Streamlit não estiver disponível

# Funções de CSS e UI
def configure_sidebar_visibility():
    """
    Configura a visibilidade da barra lateral:
    1. Mantém a barra lateral visível
    2. Oculta apenas os itens de navegação
    """
    st.markdown("""
    <style>
        /* Garantir que a barra lateral esteja visível */
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
        }
        
        /* Ocultar completamente o menu de navegação lateral */
        [data-testid="stSidebarNavItems"],
        .st-emotion-cache-16idsys, 
        .st-emotion-cache-1cypcdb,
        .st-emotion-cache-vk3wp9,
        .st-emotion-cache-ue6h4q,
        .st-emotion-cache-jnd7a1 {
            display: none !important;
        }

        /* Remover margens superiores desnecessárias */
        section[data-testid="stSidebarUserContent"] {
            margin-top: 0 !important;
        }
        
        /* Ocultar outros elementos de navegação */
        header[data-testid="stHeader"],
        button[kind="header"],
        #MainMenu,
        footer,
        [data-testid="collapsedControl"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
def hide_streamlit_menu():
    """Oculta o menu de navegação do Streamlit e outros elementos da interface padrão"""
    return """
    <style>
        /* Ocultar completamente o menu de navegação lateral */
        [data-testid="stSidebarNavItems"],
        div.stSidebarNavItems, 
        button.stSidebarButton,
        .st-emotion-cache-16idsys, 
        .st-emotion-cache-1cypcdb,
        .st-emotion-cache-vk3wp9,
        .st-emotion-cache-ue6h4q,
        .st-emotion-cache-jnd7a1,
        ul.st-emotion-cache-pbk8do {
            display: none !important;
        }
        
        /* Remover margens superiores desnecessárias */
        section[data-testid="stSidebarUserContent"] {
            margin-top: 0 !important;
        }
        
        /* Ocultar cabeçalho, rodapé e menu principal */
        header[data-testid="stHeader"],
        button[kind="header"],
        #MainMenu,
        footer,
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        
        /* Garantir que a barra lateral esteja visível e funcionando */
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
            transform: none !important;
        }
        
        /* Remover espaço extra no topo que normalmente é ocupado pelo menu */
        .main .block-container {
            padding-top: 1rem !important;
        }
    </style>
    """
def hide_app_admin_items():
    """
    Função para ocultar completamente os itens 'app' e 'admin' 
    em qualquer parte da interface do Streamlit
    """
    st.markdown("""
    <style>
        /* Seletores específicos para o modal/dropdown */
        div[role="dialog"] p:contains("app"),
        div[role="dialog"] p:contains("admin"),
        div[aria-modal="true"] p:contains("app"),
        div[aria-modal="true"] p:contains("admin"),
        
        /* Seletores para navegação lateral */
        [data-testid="stSidebarNavItems"] a:has(p:contains("app")),
        [data-testid="stSidebarNavItems"] a:has(p:contains("admin")),
        
        /* Seletores gerais para qualquer texto */
        p:contains("app"),
        p:contains("admin") {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def hide_app_admin_from_modal():
    """
    Função específica para ocultar os itens 'app' e 'admin' no modal/dropdown de navegação
    """
    st.markdown("""
    <style>
        /* Seletores ultra-específicos para o modal/dropdown da captura de tela */
        div[role="dialog"] div > p:contains("app"),
        div[role="dialog"] div > p:contains("admin") {
            display: none !important;
        }
        
        /* Seletor alternativo para o mesmo elemento */
        div[aria-modal="true"] p:contains("app"),
        div[aria-modal="true"] p:contains("admin") {
            display: none !important;
        }
        
        /* Seletor com correspondência de texto exato para maior precisão */
        p:text-is("app"),
        p:text-is("admin") {
            display: none !important;
        }
        
        /* Seletor direto para elementos de página na navegação */
        div.st-bd p:contains("app"),
        div.st-bd p:contains("admin") {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def apply_global_css():
    """Aplica apenas estilos CSS essenciais"""
    css = (
        "<style>"
        "div.stButton > button {background-color: #fd7014 !important; color: white !important;}"
        "div.stButton > button:hover {background-color: #333 !important;}"
        "p, li {color: white !important;}"
        "[data-testid='stSidebarNavItems'] {display: none !important;}"
        "header[data-testid='stHeader'], footer, #MainMenu {display: none !important;}"
        "</style>"
    )
    
    st.markdown(css, unsafe_allow_html=True)
# Função para exibir a logo do ValueHunter de forma consistente
def _get_base64(path: str) -> str:
    """Converte qualquer arquivo binário em string base64."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

import os, base64, streamlit as st

# Função corrigida para mostrar a logodef (container=None, size="medium"):
def show_valuehunter_logo():
    """Display ValueHunter logo with improved layout"""
    st.markdown("""
    <div class="logo-container">
        <div style="display: flex; align-items: center;">
            <span style="color: #fd7014; font-size: 1.8rem; font-weight: bold; margin-right: 4px;">VALUE</span>
            <span style="color: white; font-size: 1.8rem; font-weight: bold;">HUNTER</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
# Coluna 4 permanece vazia para espaçamento
def insert_favicon():
    """
    Insere o favicon SVG diretamente no HTML
    """
    # Código SVG inline para o favicon (binóculos)
    favicon_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
      <rect width="64" height="64" fill="none"/>
      <circle cx="20" cy="32" r="14" fill="#fd7014" stroke="#ffffff" stroke-width="2"/>
      <circle cx="44" cy="32" r="14" fill="#fd7014" stroke="#ffffff" stroke-width="2"/>
      <rect x="20" y="28" width="24" height="8" fill="#fd7014" stroke="#ffffff" stroke-width="1"/>
      <circle cx="20" cy="32" r="7" fill="#1e1e1e" stroke="#ffffff" stroke-width="1"/>
      <circle cx="44" cy="32" r="7" fill="#1e1e1e" stroke="#ffffff" stroke-width="1"/>
    </svg>
    """
    
    # Converter para base64
    import base64
    favicon_b64 = base64.b64encode(favicon_svg.encode()).decode()
    
    # Inserir como tag link com tipo MIME correto para SVG
    favicon_html = (
        "<link rel='icon' type='image/svg+xml' "
        f"href='data:image/svg+xml;base64,{favicon_b64}'>"
    )
    
    # Inserir também como ícone alternativo para garantir compatibilidade
    st.markdown(favicon_html, unsafe_allow_html=True)
    
    # Adicionar também uma versão para Apple
    apple_touch_icon = (
        "<link rel='apple-touch-icon' "
        f"href='data:image/svg+xml;base64,{favicon_b64}'>"
    )
    st.markdown(apple_touch_icon, unsafe_allow_html=True)
    
    # Log de sucesso
    logger.info("Favicon SVG personalizado inserido com sucesso")

# Funções de navegação
def go_to_login():
    """Navigate to login page"""
    # Apenas atualiza a página sem limpar as variáveis relacionadas ao logo
    st.session_state.page = "login"
    st.session_state.show_register = False
    
    # Resetar flags específicas de formulários
    if "login_form_rendered" in st.session_state:
        st.session_state.login_form_rendered = False
        
    st.experimental_rerun()

def go_to_register():
    """Navigate to register page"""
    st.session_state.page = "register"
    st.session_state.show_register = True
    st.experimental_rerun()

def go_to_landing():
    """Navigate to landing page"""
    st.session_state.page = "landing"
    st.experimental_rerun()

# Função init_session_state
def init_session_state():
    """Initialize session state variables"""
    from utils.data import UserManager
    
    if "page" not in st.session_state:
        st.session_state.page = "landing"  # Nova variável para controlar a página atual
        
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "email" not in st.session_state:
        st.session_state.email = None
    
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
    
    # UserManager deve ser o último a ser inicializado
    if "user_manager" not in st.session_state:
        st.session_state.user_manager = UserManager()
    
    # Atualizar timestamp de última atividade
    st.session_state.last_activity = datetime.now()

# Funções de Stripe
def init_stripe():
    """Initialize Stripe with the API key."""
    # Melhor controle de erros e logging para inicialização do Stripe
    try:
        # Se estamos no Render, usar variáveis de ambiente diretamente
        if "RENDER" in os.environ:
            api_key = os.environ.get("STRIPE_SECRET_KEY", "")
            logger.info("Usando API key do Stripe de variáveis de ambiente no Render")
        else:
            # Tente usar secrets (para desenvolvimento local ou Streamlit Cloud)
            try:
                api_key = st.secrets.get("STRIPE_SECRET_KEY", "")
                logger.info("Usando API key do Stripe de st.secrets")
            except Exception as e:
                logger.warning(f"Erro ao tentar carregar API key do Stripe de st.secrets: {str(e)}")
                api_key = os.environ.get("STRIPE_SECRET_KEY", "")
                logger.info("Usando API key do Stripe de variáveis de ambiente locais")
        
        # Atualizar API key do Stripe
        stripe.api_key = api_key
        
        if not stripe.api_key:
            logger.error("Stripe API key não encontrada em nenhuma configuração")
            st.error("Stripe API key not found")
        else:
            logger.info(f"Stripe API key configurada com sucesso. Modo de teste: {stripe.api_key.startswith('sk_test_')}")
        
        # Para teste, isso avisa os usuários que estão no modo de teste
        st.session_state.stripe_test_mode = stripe.api_key.startswith("sk_test_")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar Stripe: {str(e)}")
        st.error(f"Erro ao inicializar Stripe. Por favor, tente novamente mais tarde.")

def get_base_url():
    """Get the base URL for the application, with special handling for Render."""
    # Check if running on Render
    if "RENDER" in os.environ:
        url = os.environ.get("RENDER_EXTERNAL_URL", "https://value-hunter.onrender.com")
        logger.info(f"Base URL no Render: {url}")
        return url
    # Check if running on Streamlit Cloud
    elif os.environ.get("IS_STREAMLIT_CLOUD"):
        url = os.environ.get("STREAMLIT_URL", "https://valuehunter.streamlit.app")
        logger.info(f"Base URL no Streamlit Cloud: {url}")
        return url
    # Local development
    else:
        try:
            url = st.get_option("server.baseUrlPath") or "http://localhost:8501"
            logger.info(f"Base URL local: {url}")
            return url
        except:
            logger.info("Usando URL local padrão: http://localhost:8501")
            return "http://localhost:8501"

def get_stripe_success_url(credits, email):
    """URL de sucesso que força refresh dos dados"""
    base_url = get_base_url()
    
    success_params = urlencode({
        'success_page': 'true',
        'credits': credits,
        'email': email,
        'session_id': '{CHECKOUT_SESSION_ID}',
        'payment_processed': 'true'  # Novo parâmetro para forçar refresh
    })
    
    full_url = f"{base_url}/?{success_params}"
    logger.info(f"URL de sucesso do Stripe configurada: {full_url}")
    return full_url

def get_stripe_cancel_url():
    """URL de cancelamento simplificada"""
    base_url = get_base_url()
    cancel_params = urlencode({'cancel_page': 'true'})
    full_url = f"{base_url}/?{cancel_params}"
    return full_url

class UserManager:
    """Gerencia usuários e autenticação"""
    
    def __init__(self):
        """Inicializa o gerenciador de usuários"""
        self.users_file = os.path.join(DATA_DIR, "users.json")
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Garante que o arquivo de usuários existe"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, "w") as f:
                json.dump([], f)
    
    def register_user(self, email, password, name=""):
        """Registra um novo usuário"""
        users = self._load_users()
        
        # Verificar se o email já existe
        if any(user["email"] == email for user in users):
            return False, "Email já cadastrado"
        
        # Criar novo usuário
        new_user = {
            "email": email,
            "password": self._hash_password(password),
            "name": name,
            "created_at": datetime.now().isoformat(),
            "credits": 10,  # Créditos iniciais
            "is_admin": False
        }
        
        users.append(new_user)
        self._save_users(users)
        return True, "Usuário registrado com sucesso"
    
    def verify_login(self, email, password):
        """Verifica as credenciais de login"""
        users = self._load_users()
        
        for user in users:
            if user["email"] == email and self._verify_password(password, user["password"]):
                return True
        
        return False
    
    def get_user_data(self, email):
        """Retorna os dados do usuário pelo email"""
        users = self._load_users()
        
        for user in users:
            if user["email"] == email:
                # Criar uma cópia sem a senha
                user_data = user.copy()
                if "password" in user_data:
                    del user_data["password"]
                return user_data
        
        return None
    
    def update_user(self, email, data):
        """Atualiza os dados de um usuário"""
        users = self._load_users()
        
        for i, user in enumerate(users):
            if user["email"] == email:
                # Atualizar apenas os campos permitidos
                for key in data:
                    if key != "email" and key != "password":  # Não permitir alterar email ou senha aqui
                        users[i][key] = data[key]
                
                self._save_users(users)
                return True
        
        return False
    
    def change_password(self, email, current_password, new_password):
        """Altera a senha de um usuário"""
        if not self.verify_login(email, current_password):
            return False, "Senha atual incorreta"
        
        users = self._load_users()
        
        for i, user in enumerate(users):
            if user["email"] == email:
                users[i]["password"] = self._hash_password(new_password)
                self._save_users(users)
                return True, "Senha alterada com sucesso"
        
        return False, "Usuário não encontrado"
    
    def add_credits(self, email, credits):
        """Adiciona créditos a um usuário"""
        users = self._load_users()
        
        for i, user in enumerate(users):
            if user["email"] == email:
                users[i]["credits"] = user.get("credits", 0) + credits
                self._save_users(users)
                return True, f"{credits} créditos adicionados com sucesso"
        
        return False, "Usuário não encontrado"
    
    def get_credits(self, email):
        """Retorna o número de créditos de um usuário"""
        users = self._load_users()
        
        for user in users:
            if user["email"] == email:
                return user.get("credits", 0)
        
        return 0
    
    def use_credits(self, email, credits=1):
        """Usa créditos de um usuário"""
        users = self._load_users()
        
        for i, user in enumerate(users):
            if user["email"] == email:
                current_credits = user.get("credits", 0)
                if current_credits < credits:
                    return False, "Créditos insuficientes"
                
                users[i]["credits"] = current_credits - credits
                self._save_users(users)
                return True, f"{credits} créditos utilizados"
        
        return False, "Usuário não encontrado"
    
    def _load_users(self):
        """Carrega os usuários do arquivo"""
        try:
            with open(self.users_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_users(self, users):
        """Salva os usuários no arquivo"""
        with open(self.users_file, "w") as f:
            json.dump(users, f, indent=2)
    
    def _hash_password(self, password):
        """Cria um hash da senha"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password, hashed_password):
        """Verifica se a senha corresponde ao hash"""
        return self._hash_password(password) == hashed_password
        return self._hash_password(password) == hashed_password
