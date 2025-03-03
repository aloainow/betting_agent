# Standard library imports
import os
import json
import hashlib
import time
import re
import traceback
import logging
import sys
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode, quote

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("valueHunter")

# Log de diagnóstico no início
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
try:
    logger.info(f"Directory contents: {os.listdir('.')}")
except Exception as e:
    logger.error(f"Erro ao listar diretório: {str(e)}")

DATA_DIR = "data"
if "RENDER" in os.environ:
    # Em produção no Render, use um caminho padrão para montagem de disco
    DATA_DIR = "/mnt/value-hunter-data"  # Caminho padrão para discos persistentes
    
# Criar diretório de dados se não existir
os.makedirs(DATA_DIR, exist_ok=True)
logger.info(f"Diretório de dados configurado: {DATA_DIR}")
logger.info(f"Conteúdo do diretório de dados: {os.listdir(DATA_DIR) if os.path.exists(DATA_DIR) else 'Diretório não existe'}")

# Configuração do Streamlit DEVE ser o primeiro comando Streamlit
import streamlit as st
st.set_page_config(
    page_title="ValueHunter - Análise de Apostas Esportivas",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"  # Manter expandido para exibir corretamente
)

# Resto dos imports
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

# Imports com tratamento de erro
try:
    from openai import OpenAI, OpenAIError
    logger.info("OpenAI importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar OpenAI: {str(e)}")
    class DummyOpenAI:
        def __init__(self, **kwargs):
            pass
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    class FakeResponse:
                        class FakeChoice:
                            class FakeMessage:
                                content = "Serviço de IA temporariamente indisponível."
                            message = FakeMessage()
                        choices = [FakeChoice()]
                    return FakeResponse()
        
    OpenAI = DummyOpenAI
    class OpenAIError(Exception):
        pass

try:
    import stripe
    logger.info("Stripe importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar Stripe: {str(e)}")
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


# Definição das URLs do FBref
FBREF_URLS = {
    "Premier League": {
        "stats": "https://fbref.com/en/comps/9/Premier-League-Stats",
        "fixtures": "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    },
    "La Liga": {
        "stats": "https://fbref.com/en/comps/12/La-Liga-Stats",
        "fixtures": "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"
    },
    "Serie A": {
        "stats": "https://fbref.com/en/comps/11/Serie-A-Stats",
        "fixtures": "https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures"
    },
    "Bundesliga": {
        "stats": "https://fbref.com/en/comps/20/Bundesliga-Stats",
        "fixtures": "https://fbref.com/en/comps/20/schedule/Bundesliga-Scores-and-Fixtures"
    },
    "Ligue 1": {
        "stats": "https://fbref.com/en/comps/13/Ligue-1-Stats",
        "fixtures": "https://fbref.com/en/comps/13/schedule/Ligue-1-Scores-and-Fixtures"
    },
    "Champions League": {
        "stats": "https://fbref.com/en/comps/8/Champions-League-Stats",
        "fixtures": "https://fbref.com/en/comps/8/schedule/Champions-League-Scores-and-Fixtures"
    }
}


@dataclass
class UserTier:
    name: str
    total_credits: int  # Total credits in package
    market_limit: int   # Limit of markets per analysis


# Funções para manipular o menu lateral
def force_sidebar_visible():
    """Força a exibição da barra lateral usando JavaScript"""
    js_code = """
    <script>
        // Função para garantir que a barra lateral esteja visível
        function showSidebar() {
            // Vários métodos para tentar mostrar a barra lateral
            var sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.style.display = "flex";
                sidebar.style.visibility = "visible";
                sidebar.style.opacity = "1";
                sidebar.style.width = "auto";
                sidebar.style.height = "auto";
                sidebar.style.maxHeight = "100vh";
                sidebar.style.transform = "none";
                sidebar.style.position = "relative";
            }
            
            // Oculta apenas itens específicos do menu
            var menuItems = document.querySelectorAll('[data-testid="stSidebarNavItems"] a, .st-emotion-cache-16idsys a');
            menuItems.forEach(function(item) {
                var text = item.innerText.toLowerCase();
                if (text.includes('app') || text.includes('admin')) {
                    item.style.display = 'none';
                }
            });
        }
        
        // Executar quando a página carregar
        document.addEventListener('DOMContentLoaded', showSidebar);
        
        // Executar novamente após um curto atraso para garantir
        setTimeout(showSidebar, 500);
        setTimeout(showSidebar, 1000);
    </script>
    """
    st.components.v1.html(js_code, height=0)

def show_sidebar_css():
    """Força a exibição da barra lateral via CSS"""
    st.markdown("""
    <style>
        /* Forçar exibição da barra lateral */
        [data-testid="stSidebar"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
        }
        
        /* Ocultar apenas itens específicos */
        [data-testid="stSidebarNavItems"] a:has(p:contains("app")),
        [data-testid="stSidebarNavItems"] a:has(p:contains("admin")),
        .st-emotion-cache-16idsys a:has(p:contains("app")),
        .st-emotion-cache-16idsys a:has(p:contains("admin")),
        div[data-testid="stSidebarNavContainer"] li:has(a[href*="app"]),
        div[data-testid="stSidebarNavContainer"] li:has(a[href*="admin"]),
        [data-testid="stSidebarNavItems"] p:contains("app"),
        [data-testid="stSidebarNavItems"] p:contains("admin"),
        .st-emotion-cache-16idsys p:contains("app"),
        .st-emotion-cache-16idsys p:contains("admin") {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)


# Função init_session_state deve vir ANTES da classe UserManager
def init_session_state():
    """Initialize session state variables"""
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


# CLASSE CORRIGIDA: UserManager completamente reescrita
class UserManager:
    def __init__(self, storage_path: str = None):
        # Caminho para armazenamento em disco persistente no Render
        if storage_path is None:
            self.storage_path = os.path.join(DATA_DIR, "user_data.json")
        else:
            self.storage_path = storage_path
            
        logger.info(f"Inicializando UserManager com arquivo de dados em: {self.storage_path}")
        
        # Garantir que o diretório existe
        os_dir = os.path.dirname(self.storage_path)
        if not os.path.exists(os_dir):
            try:
                os.makedirs(os_dir, exist_ok=True)
                logger.info(f"Diretório criado: {os_dir}")
            except Exception as e:
                logger.error(f"Erro ao criar diretório para dados de usuário: {str(e)}")
        
        self.users = self._load_users()
        
        # Define user tiers/packages
        self.tiers = {
            "free": UserTier("free", 5, float('inf')),     # 5 credits, multiple markets
            "standard": UserTier("standard", 30, float('inf')),  # 30 credits, multiple markets
            "pro": UserTier("pro", 60, float('inf'))       # 60 credits, multiple markets
        }        
    
    def _load_users(self) -> Dict:
        """Load users from JSON file with better error handling"""
        try:
            # Verificar se o arquivo existe
            if os.path.exists(self.storage_path):
                try:
                    with open(self.storage_path, 'r') as f:
                        data = json.load(f)
                        logger.info(f"Dados de usuários carregados com sucesso: {len(data)} usuários")
                        return data
                except json.JSONDecodeError as e:
                    logger.error(f"Arquivo de usuários corrompido: {str(e)}")
                    # Fazer backup do arquivo corrompido
                    if os.path.exists(self.storage_path):
                        backup_path = f"{self.storage_path}.bak.{int(time.time())}"
                        try:
                            with open(self.storage_path, 'r') as src, open(backup_path, 'w') as dst:
                                dst.write(src.read())
                            logger.info(f"Backup do arquivo corrompido criado: {backup_path}")
                        except Exception as be:
                            logger.error(f"Erro ao criar backup do arquivo corrompido: {str(be)}")
                except Exception as e:
                    logger.error(f"Erro desconhecido ao ler arquivo de usuários: {str(e)}")
            
            # Se chegamos aqui, não temos dados válidos
            logger.info("Criando nova estrutura de dados de usuários")
            return {}
        except Exception as e:
            logger.error(f"Erro não tratado em _load_users: {str(e)}")
            return {}
    
    def _save_users(self):
        """Save users to JSON file with error handling and atomic writes"""
        try:
            # Criar diretório se não existir
            directory = os.path.dirname(self.storage_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Usar escrita atômica com arquivo temporário
            temp_path = f"{self.storage_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(self.users, f, indent=2)
            
            # Renomear o arquivo temporário para o arquivo final (operação atômica)
            os.replace(temp_path, self.storage_path)
            
            logger.info(f"Dados de usuários salvos com sucesso: {len(self.users)} usuários")
            return True
                
        except Exception as e:
            logger.error(f"Erro ao salvar dados de usuários: {str(e)}")
            
            # Tentar salvar em local alternativo
            try:
                alt_path = os.path.join(DATA_DIR, "users_backup.json")
                with open(alt_path, 'w') as f:
                    json.dump(self.users, f, indent=2)
                logger.info(f"Dados de usuários salvos no local alternativo: {alt_path}")
                self.storage_path = alt_path  # Atualizar caminho para próximos salvamentos
                return True
            except Exception as alt_e:
                logger.error(f"Erro ao salvar no local alternativo: {str(alt_e)}")
                
        return False
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))
    
    def _format_tier_name(self, tier: str) -> str:
        """Format tier name for display (capitalize)"""
        tier_display = {
            "free": "Free",
            "standard": "Standard", 
            "pro": "Pro"
        }
        return tier_display.get(tier, tier.capitalize())
    
    def register_user(self, email: str, password: str, name: str = None, tier: str = "free") -> tuple:
        """Register a new user with optional name parameter"""
        try:
            if not self._validate_email(email):
                return False, "Email inválido"
            if email in self.users:
                return False, "Email já registrado"
            if len(password) < 6:
                return False, "Senha deve ter no mínimo 6 caracteres"
            if tier not in self.tiers:
                return False, "Tipo de usuário inválido"
                    
            # Se nome não for fornecido, usar parte do email como nome
            if not name:
                name = email.split('@')[0].capitalize()
                    
            self.users[email] = {
                "password": self._hash_password(password),
                "name": name,  # Adicionando o nome
                "tier": tier,
                "usage": {
                    "daily": [],
                    "total": []  # Track total usage
                },
                "purchased_credits": 0,  # Track additional purchased credits
                "free_credits_exhausted_at": None,  # Timestamp when free credits run out
                "paid_credits_exhausted_at": None,  # Timestamp when paid credits run out
                "created_at": datetime.now().isoformat()
            }
            
            save_success = self._save_users()
            if not save_success:
                logger.warning(f"Falha ao salvar dados durante registro do usuário: {email}")
                
            logger.info(f"Usuário registrado com sucesso: {email}, tier: {tier}")
            return True, "Registro realizado com sucesso"
        except Exception as e:
            logger.error(f"Erro ao registrar usuário {email}: {str(e)}")
            return False, f"Erro interno ao registrar usuário: {str(e)}"
    
    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate a user"""
        try:
            if email not in self.users:
                logger.info(f"Tentativa de login com email não registrado: {email}")
                return False
                
            # Check if the password matches
            if self.users[email]["password"] != self._hash_password(password):
                logger.info(f"Tentativa de login com senha incorreta: {email}")
                return False
                
            # Autenticação bem-sucedida
            logger.info(f"Login bem-sucedido: {email}")
            return True
        except Exception as e:
            logger.error(f"Erro durante a autenticação para {email}: {str(e)}")
            return False
    
    def add_credits(self, email: str, amount: int) -> bool:
        """Add more credits to a user account"""
        try:
            if email not in self.users:
                logger.warning(f"Tentativa de adicionar créditos para usuário inexistente: {email}")
                return False
                
            if "purchased_credits" not in self.users[email]:
                self.users[email]["purchased_credits"] = 0
                
            self.users[email]["purchased_credits"] += amount
            
            # Clear paid credits exhausted timestamp when adding credits
            if self.users[email].get("paid_credits_exhausted_at"):
                self.users[email]["paid_credits_exhausted_at"] = None
                
            save_success = self._save_users()
            if not save_success:
                logger.warning(f"Falha ao salvar dados após adicionar créditos para: {email}")
                
            logger.info(f"Créditos adicionados com sucesso: {amount} para {email}")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar créditos para {email}: {str(e)}")
            return False
    
    def get_usage_stats(self, email: str) -> Dict:
        """Get usage statistics for a user"""
        try:
            if email not in self.users:
                logger.warning(f"Tentativa de obter estatísticas para usuário inexistente: {email}")
                return {
                    "name": "Usuário",
                    "tier": "free",
                    "tier_display": "Free",
                    "credits_used": 0,
                    "credits_total": 5,
                    "credits_remaining": 5,
                    "market_limit": float('inf')
                }
                    
            user = self.users[email]
            
            # Calculate total credits used
            total_credits_used = sum(
                u["markets"] for u in user.get("usage", {}).get("total", [])
            )
            
            # Get credits based on user tier
            tier_name = user.get("tier", "free")
            if tier_name not in self.tiers:
                tier_name = "free"
                
            tier = self.tiers[tier_name]
            base_credits = tier.total_credits
            
            # Add any purchased credits
            purchased_credits = user.get("purchased_credits", 0)
            
            # Get user name (with fallback)
            user_name = user.get("name", email.split('@')[0].capitalize())
            
            # Free tier special handling
            free_credits_reset = False
            next_free_credits_time = None
            
            if user["tier"] == "free" and user.get("free_credits_exhausted_at"):
                try:
                    # Convert stored time to datetime
                    exhausted_time = datetime.fromisoformat(user["free_credits_exhausted_at"])
                    current_time = datetime.now()
                    
                    # Check if 24 hours have passed
                    if (current_time - exhausted_time).total_seconds() >= 86400:  # 24 hours in seconds
                        # Reset credits - IMPORTANTE: sempre será 5 créditos, não acumula
                        user["free_credits_exhausted_at"] = None
                        
                        # Clear usage history for free users after reset
                        user["usage"]["total"] = []
                        free_credits_reset = True
                        self._save_users()
                        
                        # Após resetar, não há créditos usados
                        total_credits_used = 0
                        logger.info(f"Créditos gratuitos renovados para: {email}")
                    else:
                        # Calculate time remaining
                        time_until_reset = exhausted_time + timedelta(days=1) - current_time
                        hours = int(time_until_reset.total_seconds() // 3600)
                        minutes = int((time_until_reset.total_seconds() % 3600) // 60)
                        next_free_credits_time = f"{hours}h {minutes}min"
                except Exception as e:
                    logger.error(f"Erro ao calcular tempo para renovação de créditos: {str(e)}")
            
            # Calculate remaining credits
            remaining_credits = max(0, base_credits + purchased_credits - total_credits_used)
            
            # Check if user is out of credits and set exhausted timestamp
            if remaining_credits == 0 and not user.get("free_credits_exhausted_at") and user["tier"] == "free":
                user["free_credits_exhausted_at"] = datetime.now().isoformat()
                self._save_users()
                logger.info(f"Créditos gratuitos esgotados para: {email}")
            
            return {
                "name": user_name,
                "tier": tier_name,
                "tier_display": self._format_tier_name(tier_name),
                "credits_used": total_credits_used,
                "credits_total": base_credits + purchased_credits,
                "credits_remaining": remaining_credits,
                "market_limit": tier.market_limit,
                "free_credits_reset": free_credits_reset,
                "next_free_credits_time": next_free_credits_time
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas para {email}: {str(e)}")
            # Retornar estatísticas padrão com nome genérico
            return {
                "name": "Usuário",
                "tier": "free",
                "tier_display": "Free",
                "credits_used": 0,
                "credits_total": 5,
                "credits_remaining": 5,
                "market_limit": float('inf')
            }
    
    def record_usage(self, email, num_markets, analysis_data=None):
        """Record usage of credits"""
        if email not in self.users:
            logger.warning(f"Tentativa de registrar uso para usuário inexistente: {email}")
            return False

        today = datetime.now().date().isoformat()
        
        # Criar registro de uso com dados detalhados
        usage = {
            "date": today,
            "markets": num_markets,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Adicionar dados de análise se fornecidos
        if analysis_data:
            usage.update({
                "league": analysis_data.get("league"),
                "home_team": analysis_data.get("home_team"),
                "away_team": analysis_data.get("away_team"),
                "markets_used": analysis_data.get("markets_used", [])
            })
        
        # Garantir que a estrutura de uso existe para o usuário
        if "usage" not in self.users[email]:
            self.users[email]["usage"] = {"daily": [], "total": []}
        
        # Adicionar o registro ao rastreamento diário e total
        self.users[email]["usage"]["daily"].append(usage)
        self.users[email]["usage"]["total"].append(usage)
        
        # Salvar alterações
        save_success = self._save_users()
        if not save_success:
            logger.warning(f"Falha ao salvar dados após registrar uso para: {email}")
            return False
            
        # Verificar créditos restantes após a atualização
        stats_after = self.get_usage_stats(email)
        credits_after = stats_after.get('credits_remaining', 0)
        
        # Se o usuário for do tier Free e esgotou os créditos, marcar o esgotamento
        if self.users[email]["tier"] == "free":
            if credits_after == 0 and not self.users[email].get("free_credits_exhausted_at"):
                self.users[email]["free_credits_exhausted_at"] = datetime.now().isoformat()
                self._save_users()
                logger.info(f"Marcando esgotamento de créditos gratuitos para: {email}")
        
        # Para usuários dos tiers Standard ou Pro
        elif self.users[email]["tier"] in ["standard", "pro"]:
            if credits_after == 0 and not self.users[email].get("paid_credits_exhausted_at"):
                self.users[email]["paid_credits_exhausted_at"] = datetime.now().isoformat()
                self._save_users()
                logger.info(f"Marcando esgotamento de créditos pagos para: {email}")
        
        logger.info(f"Uso registrado com sucesso: {num_markets} créditos para {email}")
        return True
    
    def _upgrade_to_standard(self, email: str) -> bool:
        """Upgrade a user to Standard package (for admin use)"""
        if email not in self.users:
            return False
            
        self.users[email]["tier"] = "standard"
        # Reset usage and timestamps for upgrade
        self.users[email]["free_credits_exhausted_at"] = None
        self.users[email]["paid_credits_exhausted_at"] = None
        self.users[email]["usage"]["total"] = []
        self.users[email]["purchased_credits"] = 0
        self._save_users()
        return True        
        
    def _upgrade_to_pro(self, email: str) -> bool:
        """Upgrade a user to Pro package (for admin use)"""
        if email not in self.users:
            return False
            
        self.users[email]["tier"] = "pro"
        # Reset usage and timestamps for upgrade
        self.users[email]["free_credits_exhausted_at"] = None
        self.users[email]["paid_credits_exhausted_at"] = None
        self.users[email]["usage"]["total"] = []
        self.users[email]["purchased_credits"] = 0
        self._save_users()
        return True
    def apply_global_css():
    """Aplica estilos CSS globais para toda a aplicação"""
    st.markdown("""
    <style>
        /* Estilo para TODOS os botões - LARANJA COM TEXTO BRANCO */
        div.stButton > button, button.css-1rs6os.edgvbvh3 {
            background-color: #fd7014 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 4px;
            font-weight: bold;
            transition: background-color 0.3s ease;
        }
        
        div.stButton > button:hover, button.css-1rs6os.edgvbvh3:hover {
            background-color: #27272a !important; /* Cinza escuro no hover */
            color: white !important;
        }
        
        /* Logo consistente */
        .logo-container {
            background-color: #fd7014;
            padding: 12px 25px !important;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
            width: fit-content;
            margin-bottom: 20px;
        }
        
        .logo-v {
            color: #3F3F45;
            font-size: 3rem !important;
            font-weight: bold;
        }
        
        .logo-text {
            font-size: 2.5rem !important;
            font-weight: bold;
            color: #FFFFFF;
        }
        
        body {
            background-color: #3F3F45;
            color: #FFFFFF;
        }
        .landing-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .hero {
            margin: 2rem 0;
            text-align: left;
        }
        .hero h1 {
            font-size: 2.8rem;
            color: #fd7014;
            margin-bottom: 1rem;
        }
        .hero p {
            font-size: 1.25rem;
            color: #FFFFFF;
            max-width: 90%;
            margin-left: 0;
        }
        .about-content {
            max-width: 90%;
            margin-left: 0;
            line-height: 1.6;
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
        .about-content h2 {
            color: #fd7014;
            margin-bottom: 0.8rem;
            text-align: left;
        }
        .footer {
            margin-top: 2rem;
            text-align: center;
            color: #b0b0b0;
        }
        .btn-container {
            display: flex;
            justify-content: flex-start;
            gap: 20px;
            margin-top: 1.5rem;
        }
        p, li {
            color: #FFFFFF !important;
        }
        
        .main .block-container {
            max-width: 95% !important; 
            padding: 1rem !important;
        }
        
        .analysis-result {
            width: 100% !important;
            max-width: 100% !important; 
            padding: 2rem !important;
            background-color: #575760;
            border-radius: 8px;
            border: 1px solid #6b6b74;
            margin: 1rem 0;
        }
        
        /* Estilo para os cartões de crédito */
        .credit-card {
            background-color: #3F3F45;
            border: 1px solid #575760;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            color: white;
            text-align: center;
        }
        .credit-title {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .credit-price {
            font-size: 42px;
            font-weight: bold;
            margin-bottom: 15px;
            color: white;
        }
        .credit-desc {
            font-size: 16px;
            color: #b0b0b0;
            margin-bottom: 15px;
        }
    </style>
    """, unsafe_allow_html=True)


# Função para exibir a logo do ValueHunter de forma consistente
def show_valuehunter_logo():
    """Exibe a logo do ValueHunter de forma consistente"""
    st.markdown(
        '<div class="logo-container"><span class="logo-v">V</span><span class="logo-text">ValueHunter</span></div>', 
        unsafe_allow_html=True
    )


def go_to_login():
    """Navigate to login page"""
    st.session_state.page = "login"
    st.session_state.show_register = False
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


# Funções de página corrigidas para mostrar o menu lateral adequadamente

def show_landing_page():
    """Display landing page with about content and login/register buttons"""
    try:
        # Logo e botões de navegação
        col1, col2 = st.columns([5, 1])
        with col1:
            show_valuehunter_logo()
        with col2:
            c1, c2 = st.columns([1, 1], gap="small")
            with c1:
                if st.button("Sign In", key="landing_signin_btn"):
                    go_to_login()
            with c2:
                if st.button("Sign Up", key="landing_signup_btn"):
                    go_to_register()
                
        # Conteúdo principal
        st.markdown("""
            <div class="hero">
                <h1>Maximize o Valor em Apostas Esportivas</h1>
                <p style="color: #FFFFFF;">Identifique oportunidades de valor com precisão matemática e análise de dados avançada.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Seção Sobre - SEM O RETÂNGULO CINZA
        st.markdown('<h2 style="color: #fd7014; margin-bottom: 0.8rem; text-align: left;">Sobre o ValueHunter</h2>', unsafe_allow_html=True)
        
        # Conteúdo da seção sobre
        with st.container():
            st.markdown('<p style="color: #FFFFFF;">O ValueHunter se fundamenta em um princípio crucial: "Ganhar não é sobre escolher o vencedor e sim conseguir o preço certo e depois deixar a variância fazer o trabalho dela."</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">Percebemos que o sucesso nas apostas esportivas não depende de prever corretamente cada resultado individual. Em vez disso, o ValueHunter busca identificar sistematicamente quando existe uma discrepância favorável entre o valor real, calculado pela nossa Engine e o valor implícito, oferecido pelas casas de apostas.</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">ValueHunter opera na interseção entre análise de dados e apostas esportivas. O ValueHunter trabalha para:</p>', unsafe_allow_html=True)
            
            st.markdown("""
            <ol style="color: #FFFFFF;">
                <li>Calcular probabilidades reais de eventos esportivos baseadas em modelos matemáticos e análise de dados</li>
                <li>Comparar essas probabilidades com as odds implícitas oferecidas pelas casas de apostas</li>
                <li>Identificar oportunidades onde existe uma vantagem estatística significativa</li>
            </ol>
            """, unsafe_allow_html=True)
            
            st.markdown('<p style="color: #FFFFFF;">Quando a probabilidade real calculada pelo ValueHunter é maior que a probabilidade implícita nas odds da casa, ele encontra uma "oportunidade" - uma aposta com valor positivo esperado a longo prazo.</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">Esta abordagem reconhece que, embora cada evento individual seja incerto, a matemática da expectativa estatística garante que, com disciplina e paciência suficientes, apostar consistentemente em situações com valor positivo me levará a lucros no longo prazo, desde que o agente de IA esteja calibrado adequadamente.</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">Em resumo, meu agente não tenta "vencer o jogo" prevendo resultados individuais, mas sim "vencer o mercado" identificando inconsistências nas avaliações de probabilidade, permitindo que a variância natural do esporte trabalhe a meu favor através de uma vantagem matemática consistente.</p>', unsafe_allow_html=True)
        
        # Botão centralizado
        st.markdown('<div class="btn-container"></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("FAÇA SEU TESTE GRÁTIS", use_container_width=True, key="landing_free_test_btn"):
                go_to_register()
                
        # Footer
        st.markdown("""
            <div class="footer">
                <p style="color: #b0b0b0;">© 2025 ValueHunter. Todos os direitos reservados.</p>
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao exibir página inicial: {str(e)}")
        st.error("Erro ao carregar a página. Por favor, tente novamente.")
        st.write(f"Detalhes do erro: {str(e)}")
    

def show_login():
    """Display login form"""
    try:
        # Header com a logo
        show_valuehunter_logo()
        st.title("Login")
        
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
        # Header com a logo
        show_valuehunter_logo()
        st.title("Register")
        
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


def show_main_dashboard():
    """Show the main dashboard with improved error handling and debug info"""
    try:
        # Forçar exibição do menu lateral na página logada
        force_sidebar_visible()
        show_sidebar_css()
        
        # Iniciar com log de diagnóstico
        logger.info("Iniciando renderização do dashboard principal")
        
        # Show usage stats in sidebar
        show_usage_stats()
        
        # Sidebar layout
        st.sidebar.title("Análise de Apostas")
        
        if st.sidebar.button("Logout", key="sidebar_logout_btn"):
            st.session_state.authenticated = False
            st.session_state.email = None
            st.session_state.page = "landing"
            st.experimental_rerun()
            
        st.sidebar.markdown("---")
        
        if st.sidebar.button("🚀 Ver Pacotes de Créditos", key="sidebar_packages_button", use_container_width=True):
            st.session_state.page = "packages"
            st.experimental_rerun()
        
        # Log de progresso
        logger.info("Sidebar renderizada com sucesso")
        
        # Conteúdo principal com tratamento de erro em cada etapa
        try:
            # Logo exibida consistentemente
            show_valuehunter_logo()
            
            # Título principal
            st.title("Seleção de Times")
                
            # Sidebar Configurações
            try:
                st.sidebar.title("Configurações")
                
                # Lista de ligas disponíveis com fallback seguro
                available_leagues = list(FBREF_URLS.keys())
                if not available_leagues:
                    st.error("Erro: Nenhuma liga disponível.")
                    logger.error("FBREF_URLS está vazia")
                    return
                
                selected_league = st.sidebar.selectbox(
                    "Escolha o campeonato:",
                    available_leagues
                )
                logger.info(f"Liga selecionada: {selected_league}")
                
                # Container para status
                status_container = st.sidebar.empty()
            except Exception as sidebar_error:
                logger.error(f"Erro na configuração da sidebar: {str(sidebar_error)}")
                st.error("Erro ao carregar configurações da sidebar.")
                traceback.print_exc()
                return
                
            # Bloco try separado para carregar dados
            try:
                # Mostrar spinner enquanto carrega
                with st.spinner("Carregando dados do campeonato..."):
                    # Tentar carregar dados da liga selecionada
                    if selected_league not in FBREF_URLS:
                        st.error(f"Liga não encontrada: {selected_league}")
                        logger.error(f"Liga {selected_league} não encontrada em FBREF_URLS")
                        return
                        
                    # Obter URL das estatísticas
                    stats_url = FBREF_URLS[selected_league].get("stats")
                    if not stats_url:
                        st.error(f"URL de estatísticas não encontrada para {selected_league}")
                        logger.error(f"URL de estatísticas ausente para {selected_league}")
                        return
                        
                    # Buscar dados - com tratamento de erro explícito
                    stats_html = fetch_fbref_data(stats_url)
                    if not stats_html:
                        st.error(f"Não foi possível carregar os dados do campeonato {selected_league}")
                        logger.error(f"fetch_fbref_data retornou None para {stats_url}")
                        return
                    
                    # Parsear estatísticas dos times
                    team_stats_df = parse_team_stats(stats_html)
                    if team_stats_df is None:
                        st.error("Erro ao processar dados de estatísticas dos times")
                        logger.error("parse_team_stats retornou None")
                        return
                        
                    if 'Squad' not in team_stats_df.columns:
                        st.error("Dados incompletos: coluna 'Squad' não encontrada")
                        logger.error(f"Colunas disponíveis: {team_stats_df.columns.tolist()}")
                        return
                    
                    # Extrair lista de times
                    teams = team_stats_df['Squad'].dropna().unique().tolist()
                    if not teams:
                        st.error("Não foi possível encontrar os times do campeonato")
                        logger.error("Lista de times vazia após dropna() e unique()")
                        return
                        
                    # Mostrar mensagem de sucesso
                    status_container.success("Dados carregados com sucesso!")
                    logger.info(f"Dados carregados: {len(teams)} times encontrados")
                    
            except Exception as load_error:
                logger.error(f"Erro ao carregar dados: {str(load_error)}")
                st.error(f"Erro ao carregar dados: {str(load_error)}")
                traceback.print_exc()
                return
                
            # Bloco try separado para selecionar times
            try:
                # Seleção de times
                col1, col2 = st.columns(2)
                with col1:
                    home_team = st.selectbox("Time da Casa:", teams, key='home_team')
                with col2:
                    away_teams = [team for team in teams if team != home_team]
                    away_team = st.selectbox("Time Visitante:", away_teams, key='away_team')
                    
                logger.info(f"Times selecionados: {home_team} vs {away_team}")
                
                # Obter estatísticas do usuário
                user_stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
                
            except Exception as teams_error:
                logger.error(f"Erro ao selecionar times: {str(teams_error)}")
                st.error(f"Erro ao exibir seleção de times: {str(teams_error)}")
                traceback.print_exc()
                return
                
            # Bloco try separado para seleção de mercados
            try:
                # Seleção de mercados
                with st.expander("Mercados Disponíveis", expanded=True):
                    st.markdown("### Seleção de Mercados")
                    st.info(f"Você tem {user_stats['credits_remaining']} créditos disponíveis. Cada mercado selecionado consumirá 1 crédito.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_markets = {
                            "money_line": st.checkbox("Money Line (1X2)", value=True, key='ml'),
                            "over_under": st.checkbox("Over/Under", key='ou'),
                            "chance_dupla": st.checkbox("Chance Dupla", key='cd')
                        }
                    with col2:
                        selected_markets.update({
                            "ambos_marcam": st.checkbox("Ambos Marcam", key='btts'),
                            "escanteios": st.checkbox("Total de Escanteios", key='corners'),
                            "cartoes": st.checkbox("Total de Cartões", key='cards')
                        })

                    num_selected_markets = sum(1 for v in selected_markets.values() if v)
                    if num_selected_markets == 0:
                        st.warning("Por favor, selecione pelo menos um mercado para análise.")
                    else:
                        st.write(f"Total de créditos que serão consumidos: {num_selected_markets}")
                        
                logger.info(f"Mercados selecionados: {[k for k, v in selected_markets.items() if v]}")
                
            except Exception as markets_error:
                logger.error(f"Erro na seleção de mercados: {str(markets_error)}")
                st.error(f"Erro ao exibir mercados disponíveis: {str(markets_error)}")
                traceback.print_exc()
                return
            
            # Bloco try separado para odds
            try:
                # Odds
                odds_data = None
                if any(selected_markets.values()):
                    with st.expander("Configuração de Odds", expanded=True):
                        odds_data = get_odds_data(selected_markets)
                        
                logger.info(f"Odds configuradas: {odds_data is not None}")
                
            except Exception as odds_error:
                logger.error(f"Erro na configuração de odds: {str(odds_error)}")
                st.error(f"Erro ao configurar odds: {str(odds_error)}")
                traceback.print_exc()
                return
            
            # Botão de análise centralizado
            try:
                col1, col2, col3 = st.columns([1,1,1])
                with col2:
                    analyze_button = st.button("Analisar Partida", type="primary")
                    
                    if analyze_button:
                        if not any(selected_markets.values()):
                            st.error("Por favor, selecione pelo menos um mercado para análise.")
                            return
                            
                        if not odds_data:
                            st.error("Por favor, configure as odds para os mercados selecionados.")
                            return
                        
                        # Verificar limites de análise
                        if not check_analysis_limits(selected_markets):
                            return
                            
                        # Criar um placeholder para o status
                        status = st.empty()
                        
                        # Executar análise com tratamento de erro para cada etapa
                        try:
                            # Etapa 1: Carregar dados
                            status.info("Carregando dados dos times...")
                            if not stats_html or team_stats_df is None:
                                status.error("Falha ao carregar dados")
                                return
                                
                            # Etapa 2: Formatar prompt
                            status.info("Preparando análise...")
                            prompt = format_prompt(team_stats_df, home_team, away_team, odds_data, selected_markets)
                            if not prompt:
                                status.error("Falha ao preparar análise")
                                return
                                
                            # Etapa 3: Análise GPT
                            status.info("Realizando análise com IA...")
                            analysis = analyze_with_gpt(prompt)
                            if not analysis:
                                status.error("Falha na análise com IA")
                                return
                            
                            # Etapa 4: Mostrar resultado
                            if analysis:
                                # Limpar status
                                status.empty()
                                
                                # Exibir a análise em uma div com largura total
                                st.markdown(f'<div class="analysis-result">{analysis}</div>', unsafe_allow_html=True)
                                
                                # Registrar uso após análise bem-sucedida
                                num_markets = sum(1 for v in selected_markets.values() if v)
                                
                                # AQUI É ONDE ADICIONAMOS O NOVO CÓDIGO:
                                # Registro de uso com dados detalhados
                                analysis_data = {
                                    "league": selected_league,
                                    "home_team": home_team,
                                    "away_team": away_team,
                                    "markets_used": [k for k, v in selected_markets.items() if v]
                                }
                                success = st.session_state.user_manager.record_usage(
                                    st.session_state.email, 
                                    num_markets,
                                    analysis_data
                                )
                                
                                if success:
                                    # Mostrar mensagem de sucesso com créditos restantes
                                    updated_stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
                                    credits_after = updated_stats['credits_remaining']
                                    st.success(f"{num_markets} créditos foram consumidos. Agora você tem {credits_after} créditos.")
                                else:
                                    st.error("Não foi possível registrar o uso dos créditos. Por favor, tente novamente.")
                                    
                        except Exception as analysis_error:
                            logger.error(f"Erro durante a análise: {str(analysis_error)}")
                            status.error(f"Erro durante a análise: {str(analysis_error)}")
                            traceback.print_exc()
                            
            except Exception as button_error:
                logger.error(f"Erro no botão de análise: {str(button_error)}")
                st.error(f"Erro no botão de análise: {str(button_error)}")
                traceback.print_exc()
                
        except Exception as content_error:
            logger.error(f"Erro fatal no conteúdo principal: {str(content_error)}")
            st.error("Erro ao carregar o conteúdo principal. Detalhes no log.")
            st.error(f"Detalhes: {str(content_error)}")
            traceback.print_exc()
            
    except Exception as e:
        logger.error(f"Erro crítico ao exibir painel principal: {str(e)}")
        st.error("Erro ao carregar o painel principal. Por favor, tente novamente.")
        st.error(f"Erro: {str(e)}")
        traceback.print_exc()


def show_packages_page():
    """Display credit purchase page with improved session handling"""
    try:
        # Forçar exibição do menu lateral
        force_sidebar_visible()
        show_sidebar_css()
        
        # Header com a logo
        show_valuehunter_logo()
        
        # Se estamos em uma página especial, mostrar apenas o conteúdo dela
        if check_payment_success():
            return
        
        # IMPORTANTE: Forçar refresh dos dados do usuário para garantir que os créditos estão atualizados
        if st.session_state.authenticated and st.session_state.email:
            try:
                # Recarregar explicitamente os dados do usuário do disco
                st.session_state.user_manager = UserManager()
                # Limpar qualquer cache que possa existir para estatísticas
                if hasattr(st.session_state, 'user_stats_cache'):
                    del st.session_state.user_stats_cache
                # Log da atualização
                logger.info(f"Dados do usuário recarregados na página de pacotes para: {st.session_state.email}")
            except Exception as e:
                logger.error(f"Erro ao atualizar dados do usuário na página de pacotes: {str(e)}")
        
        st.title("Comprar Mais Créditos")
        st.markdown("Adquira mais créditos quando precisar, sem necessidade de mudar de pacote.")
        
        # Mostrar créditos atuais para o usuário ver
        if st.session_state.authenticated and st.session_state.email:
            stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
            st.info(f"💰 Você atualmente tem **{stats['credits_remaining']} créditos** disponíveis em sua conta.")
        
        # Layout da página de compra
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="credit-card">
                <div class="credit-title">30 Créditos</div>
                <div class="credit-price">R$ 19,99</div>
                <div class="credit-desc">Pacote Standard</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar 30 Créditos", use_container_width=True, key="buy_30c"):
                update_purchase_button(30, 19.99)
        
        with col2:
            st.markdown("""
            <div class="credit-card">
                <div class="credit-title">60 Créditos</div>
                <div class="credit-price">R$ 29,99</div>
                <div class="credit-desc">Pacote Pro</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar 60 Créditos", use_container_width=True, key="buy_60c"):
                update_purchase_button(60, 29.99)
        
        # Add payment instructions
        st.markdown("""
        ### Como funciona o processo de pagamento:
        
        1. Ao clicar em "Comprar Créditos", uma nova janela será aberta para pagamento
        2. Complete seu pagamento na página do Stripe
        3. Após o pagamento, você verá uma mensagem de confirmação
        4. Seus créditos serão adicionados à sua conta imediatamente
        5. Clique em "Voltar para análises" para continuar usando o aplicativo
        
        **Nota:** Todo o processo é seguro e seus dados de pagamento são protegidos pelo Stripe
        """)
        
        # Test mode notice
        if st.session_state.stripe_test_mode:
            st.warning("""
            ⚠️ **Modo de teste ativado**
            
            Use o cartão 4242 4242 4242 4242 com qualquer data futura e CVC para simular um pagamento bem-sucedido.
            """)
        
        # Botão para voltar
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Voltar para análises", key="back_to_analysis", use_container_width=True):
            # IMPORTANTE: Forçar refresh dos dados ao voltar para análises
            try:
                # Recarregar a classe UserManager para garantir dados atualizados
                st.session_state.user_manager = UserManager()
                # Limpar qualquer cache de estatísticas
                if hasattr(st.session_state, 'user_stats_cache'):
                    del st.session_state.user_stats_cache
                logger.info(f"Dados recarregados ao voltar para análises: {st.session_state.email}")
            except Exception as e:
                logger.error(f"Erro ao recarregar dados ao voltar: {str(e)}")
                
            # Mudar a página
            st.session_state.page = "main"
            st.experimental_rerun()
    except Exception as e:
        logger.error(f"Erro ao exibir página de pacotes: {str(e)}")
        st.error("Erro ao carregar a página de pacotes. Por favor, tente novamente.")


# Função principal (main)
def main():
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
            
        # Initialize session state
        init_session_state()
        
        # Forçar visibilidade do menu lateral em todas as páginas
        force_sidebar_visible()
        show_sidebar_css()
        
        # Apply global CSS
        apply_global_css()
        
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
        
        # Roteamento de páginas
        route_pages()
        
    except Exception as e:
        logger.error(f"Erro geral na aplicação: {str(e)}")
        traceback.print_exc()


# Atualização para função route_pages() com suporte para admin
def route_pages():
    """Roteamento de páginas com suporte à página admin"""
    # Verificar parâmetro especial para acessar a página admin
    if 'admin' in st.query_params and st.query_params.admin == 'true':
        show_admin_page()
        return
        
    # Resto do código de roteamento existente...
    if st.session_state.page == "landing":
        show_landing_page()
    elif st.session_state.page == "login":
        show_login()
    elif st.session_state.page == "register":
        show_register()
    elif st.session_state.page == "main":
        if not st.session_state.authenticated:
            st.warning("Sua sessão expirou. Por favor, faça login novamente.")
            go_to_login()
            return
        show_main_dashboard()
    elif st.session_state.page == "packages":
        if not st.session_state.authenticated:
            st.warning("Você precisa fazer login para acessar os pacotes.")
            go_to_login()
            return
        show_packages_page()
    elif st.session_state.page == "admin":  # Nova opção
        show_admin_page()
    else:
        st.session_state.page = "landing"
        st.experimental_rerun()


# Executar a aplicação
if __name__ == "__main__":
    try:
        logger.info("Iniciando aplicação ValueHunter")
        main()
    except Exception as e:
        logger.critical(f"Erro fatal na aplicação: {str(e)}")
        st.error("Ocorreu um erro inesperado. Por favor, recarregue a página e tente novamente.")
        st.error(f"Detalhes do erro: {str(e)}")
