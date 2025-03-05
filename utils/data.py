# utils/data.py - Manipulação de Dados
import os
import json
import hashlib
import time
import re
import logging
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import streamlit as st  # Adicione esta importação
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

# Configuração de logging
logger = logging.getLogger("valueHunter.data")

# Referência à variável global do diretório de dados
from utils.core import DATA_DIR
# Temos que verificar se já existe uma referência a DATA_DIR
try:
    # Primeiro, tentar importar diretamente
    from utils.core import DATA_DIR
except (ImportError, ModuleNotFoundError):
    # Se falhar, usa uma variável local
    DATA_DIR = os.environ.get("DATA_DIR", "data")
    if "RENDER" in os.environ:
        DATA_DIR = "/mnt/value-hunter-data"

# Garantir que o diretório de dados existe
os.makedirs(DATA_DIR, exist_ok=True)

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
        
        # Limpar qualquer cache que possa existir para estatísticas
        try:
            import streamlit as st
            if hasattr(st.session_state, 'user_stats_cache'):
                del st.session_state.user_stats_cache
        except Exception as e:
            logger.warning(f"Erro ao limpar cache de estatísticas: {str(e)}")
            
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

# Funções para análise e carregamento de dados

def rate_limit(seconds):
    """Decorador para limitar taxa de requisições"""
    def decorator(func):
        last_called = [0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < seconds:
                time.sleep(seconds - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

@rate_limit(1)  # 1 requisição por segundo
def fetch_fbref_data(url, force_reload=False):
    """
    Busca dados do FBref com melhor tratamento de erros e opção de forçar reload.
    Versão que estava funcionando, com melhorias sutis.
    """
    import random
    import time
    
    logger.info(f"Buscando dados do FBref: {url}, force_reload={force_reload}")
    
    # Pequena lista de User-Agents para alternar (não muitos para evitar detecção)
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    
    # Manter os cabeçalhos simples - não exagerar
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }
    
    # Tenta usar cache para diferentes ligas
    cache_key = url.split('/')[-1]
    cache_file = os.path.join(DATA_DIR, f"cache_{cache_key.replace('-', '_')}.html")
    
    # Verificar se existe cache - sem mostrar mensagem
    if not force_reload:
        try:
            if os.path.exists(cache_file):
                file_age_seconds = time.time() - os.path.getmtime(cache_file)
                with open(cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Se o cache tiver conteúdo não vazio e não for muito antigo (24 horas)
                    if content and len(content) > 1000 and file_age_seconds < 86400:
                        logger.info(f"Usando cache para {url} (idade: {file_age_seconds/3600:.1f} horas)")
                        return content
        except Exception as e:
            logger.warning(f"Erro ao ler do cache: {str(e)}")
    
    # Implementar retry com backoff exponencial
    max_retries = 3
    retry_delay = 5  # segundos iniciais de espera
    
    # Adicionar um delay aleatório antes da requisição para parecer mais humano
    time.sleep(1 + random.random() * 2)
    
    for attempt in range(max_retries):
        try:
            with st.spinner(f"Carregando dados do campeonato (tentativa {attempt+1}/{max_retries})..."):
                # Variar levemente o user agent entre tentativas
                if attempt > 0:
                    headers['User-Agent'] = random.choice(user_agents)
                
                # Aumentar o timeout nas tentativas subsequentes
                timeout = 30 + (attempt * 10)
                
                # Fazer a requisição
                response = requests.get(url, headers=headers, timeout=timeout)
                
                if response.status_code == 200:
                    # Verificar se a resposta tem conteúdo válido
                    if len(response.text) < 1000 or '<table' not in response.text:
                        logger.warning(f"Resposta sem tabelas ou muito pequena ({len(response.text)} bytes): {url}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 1.5
                            continue
                    
                    # Salvar em cache para uso futuro
                    try:
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        logger.info(f"Cache salvo para {url}")
                    except Exception as e:
                        logger.warning(f"Erro ao salvar cache: {str(e)}")
                        
                    return response.text
                elif response.status_code == 429:
                    # Não mostrar mensagens de warning sobre rate limiting para o usuário
                    logger.warning(f"Rate limit atingido. Tentativa {attempt+1}/{max_retries}. Aguardando {retry_delay}s.")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Backoff exponencial
                else:
                    logger.warning(f"Erro HTTP {response.status_code}. Tentativa {attempt+1}/{max_retries}. Aguardando {retry_delay}s.")
                    
                    # Se for um erro 403/404, tentar URL alternativa se possível
                    if response.status_code in [403, 404] and '/Stats' in url:
                        alt_url = url.replace('/Stats', '')
                        logger.info(f"Tentando URL alternativa: {alt_url}")
                        try:
                            alt_response = requests.get(alt_url, headers=headers, timeout=timeout)
                            if alt_response.status_code == 200 and len(alt_response.text) > 1000:
                                return alt_response.text
                        except:
                            pass
                    
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    
        except requests.Timeout:
            logger.warning(f"Timeout na requisição. Tentativa {attempt+1}/{max_retries}. Aguardando {retry_delay}s.")
            time.sleep(retry_delay)
            retry_delay *= 1.5
        except requests.RequestException as e:
            logger.warning(f"Erro na requisição: {str(e)}. Tentativa {attempt+1}/{max_retries}. Aguardando {retry_delay}s.")
            time.sleep(retry_delay)
            retry_delay *= 1.5
        except Exception as e:
            logger.warning(f"Erro não esperado: {str(e)}. Tentativa {attempt+1}/{max_retries}. Aguardando {retry_delay}s.")
            time.sleep(retry_delay)
            retry_delay *= 1.5
    
    # Se falhou com o cache normal, tentar buscar um fallback de cache
    try:
        fallback_files = [f for f in os.listdir(DATA_DIR) if f.startswith("cache_") and f.endswith(".html")]
        if fallback_files:
            # Usar o cache mais recente de qualquer liga
            fallback_file = os.path.join(DATA_DIR, sorted(fallback_files, 
                            key=lambda x: os.path.getmtime(os.path.join(DATA_DIR, x)), 
                            reverse=True)[0])
            
            logger.warning(f"Usando cache de fallback: {fallback_file}")
            with open(fallback_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content and len(content) > 1000:
                    return content
    except Exception as e:
        logger.error(f"Erro ao tentar usar cache de fallback: {str(e)}")
    
    # Mensagem de erro simples e clara
    logger.error("Não foi possível carregar os dados do campeonato após múltiplas tentativas")
    return None
def parse_team_stats(html_content):
    """Função robusta para processar dados de times de futebol de HTML"""
    try:
        import pandas as pd
        import numpy as np
        from bs4 import BeautifulSoup
        import streamlit as st
        import os
        import re
        import time
        
        logger.info("Iniciando processamento de HTML avançado")
        
        # Verificar se o conteúdo HTML é válido
        if not html_content or len(html_content) < 1000:
            logger.error(f"Conteúdo HTML inválido: {len(html_content) if html_content else 0} caracteres")
            st.error("O HTML recebido está incompleto ou inválido")
            
            # Salvar HTML para diagnóstico
            try:
                debug_path = os.path.join(DATA_DIR, f"debug_html_{int(time.time())}.txt")
                with open(debug_path, 'w', encoding='utf-8') as f:
                    f.write(html_content if html_content else "HTML vazio")
                logger.info(f"HTML inválido salvo para diagnóstico em: {debug_path}")
            except Exception as save_error:
                logger.error(f"Erro ao salvar HTML para diagnóstico: {str(save_error)}")
            
            return None
        
        # 0. Salvar uma cópia do HTML para diagnóstico
        try:
            debug_path = os.path.join(DATA_DIR, f"debug_html_{int(time.time())}.txt")
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(html_content[:20000])  # Salvar apenas parte inicial para economizar espaço
            logger.info(f"HTML salvo para diagnóstico em: {debug_path}")
        except Exception as save_error:
            logger.warning(f"Não foi possível salvar HTML para diagnóstico: {str(save_error)}")
            
        # 1. Método de parsing com BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1.1 Procurar todas as tabelas
        all_tables = soup.find_all('table')
        logger.info(f"Total de tabelas encontradas: {len(all_tables)}")
        
        if len(all_tables) == 0:
            logger.error("Nenhuma tabela encontrada no HTML")
            st.error("Não foi possível encontrar tabelas na página. O site pode ter mudado de estrutura.")
            return None
            
        # 1.2 Lista de possiveis IDs/classes de tabelas de estatísticas
        table_ids = [
            'stats_squads_standard_for',
            'stats_squads_standard_stats',
            'stats_squads_standard',
            'stats_squads',
            'stats_standard'
        ]
        
        # 1.3 Procurar por tabelas com IDs específicos
        stats_table = None
        for table_id in table_ids:
            table = soup.find('table', {'id': table_id})
            if table:
                stats_table = table
                logger.info(f"Tabela encontrada com ID: {table_id}")
                break
                
        # 1.4 Se não encontrou por ID, procurar por conteúdo
        if not stats_table:
            logger.info("Procurando tabelas por conteúdo...")
            for table in all_tables:
                # Verificar se tem thead/tbody
                has_thead = table.find('thead') is not None
                has_tbody = table.find('tbody') is not None
                
                # Verificar se tem cabeçalhos
                headers = table.find_all('th')
                header_text = " ".join([h.get_text(strip=True).lower() for h in headers])
                
                logger.info(f"Tabela: thead={has_thead}, tbody={has_tbody}, headers={len(headers)}")
                logger.info(f"Header text sample: {header_text[:100]}")
                
                # Verificar marcadores específicos de tabelas de estatísticas
                if (has_thead and has_tbody and len(headers) > 3 and 
                    any(kw in header_text for kw in ['squad', 'team', 'equipe', 'mp', 'matches', 'jogos', 'gls', 'goals'])):
                    stats_table = table
                    logger.info("Tabela de estatísticas encontrada pelo conteúdo dos cabeçalhos")
                    break
                    
        # 1.5 Se ainda não encontrou, usar a maior tabela
        if not stats_table and all_tables:
            tables_with_rows = []
            for i, table in enumerate(all_tables):
                rows = table.find_all('tr')
                if len(rows) > 5:  # Uma tabela de estatísticas deve ter pelo menos alguns times
                    tables_with_rows.append((i, len(rows), table))
            
            if tables_with_rows:
                # Ordenar por número de linhas (maior primeiro)
                tables_with_rows.sort(key=lambda x: x[1], reverse=True)
                stats_table = tables_with_rows[0][2]
                logger.info(f"Usando a maior tabela (índice {tables_with_rows[0][0]}) com {tables_with_rows[0][1]} linhas")
                
        # 2. Diagnóstico da tabela encontrada
        if not stats_table:
            logger.error("Não foi possível identificar uma tabela de estatísticas válida")
            st.error("A estrutura da página não contém uma tabela de estatísticas reconhecível")
            return None
            
        # 2.1 Analisar estrutura da tabela
        rows = stats_table.find_all('tr')
        logger.info(f"A tabela selecionada tem {len(rows)} linhas")
        
        # 2.2 Verificar cabeçalhos
        header_row = None
        for i, row in enumerate(rows[:5]):  # Verificar apenas as primeiras linhas
            headers = row.find_all('th')
            if len(headers) > 3:  # Precisa ter alguns cabeçalhos
                header_row = i
                header_texts = [h.get_text(strip=True) for h in headers]
                logger.info(f"Linha de cabeçalho encontrada (índice {i}): {header_texts}")
                break
                
        if header_row is None:
            logger.error("Não foi possível identificar uma linha de cabeçalho válida")
            
        # 3. MÉTODO A: Pandas read_html
        df = None
        try:
            logger.info("Tentando extrair com pandas read_html")
            # Nota: pandas.read_html pode falhar se o HTML for muito complexo
            tables = pd.read_html(str(stats_table))
            
            if tables and len(tables) > 0:
                df = tables[0]
                
                # Verificar se o DataFrame tem dados
                if len(df) > 0 and len(df.columns) > 3:
                    logger.info(f"Extração bem-sucedida com pandas: {df.shape}")
                    
                    # Verificar se há uma coluna com nomes de equipes
                    has_teams = False
                    for col in df.columns:
                        col_values = df[col].astype(str)
                        if any(len(val) > 3 for val in col_values):  # Nomes de times geralmente têm mais de 3 caracteres
                            has_teams = True
                            logger.info(f"Possível coluna de equipes: {col}")
                            break
                    
                    if not has_teams:
                        logger.warning("O DataFrame não parece conter nomes de equipes")
                        df = None
                else:
                    logger.warning(f"DataFrame extraído com pandas parece vazio ou inválido: {df.shape}")
                    df = None
            else:
                logger.warning("pandas.read_html não retornou nenhuma tabela")
                df = None
                
        except Exception as e:
            logger.error(f"Erro ao extrair com pandas.read_html: {str(e)}")
            df = None
            
        # 4. MÉTODO B: Extração manual com BeautifulSoup
        if df is None:
            try:
                logger.info("Tentando extração manual com BeautifulSoup")
                
                # 4.1 Identificar cabeçalhos
                header_cells = []
                
                # Primeiro, procurar na linha <thead>
                thead = stats_table.find('thead')
                if thead:
                    header_rows = thead.find_all('tr')
                    if header_rows:
                        # Pegar a última linha do thead, que geralmente tem os cabeçalhos detalhados
                        header_cells = header_rows[-1].find_all(['th', 'td'])
                        
                # Se não encontrou no thead, procurar nas primeiras linhas
                if not header_cells:
                    for row in rows[:3]:  # Verificar apenas as primeiras linhas
                        cells = row.find_all(['th', 'td'])
                        if len(cells) > 3:  # Precisa ter alguns cabeçalhos
                            header_cells = cells
                            break
                
                if not header_cells:
                    logger.error("Não foi possível encontrar cabeçalhos para extração manual")
                    return None
                    
                # 4.2 Extrair textos dos cabeçalhos
                headers = []
                for i, cell in enumerate(header_cells):
                    header_text = cell.get_text(strip=True)
                    if not header_text:
                        header_text = f"Column_{i}"  # Nome de coluna genérico
                    headers.append(header_text)
                    
                logger.info(f"Cabeçalhos extraídos manualmente: {headers}")
                
                # 4.3 Identificar tbody ou linhas de dados
                data_rows = []
                tbody = stats_table.find('tbody')
                if tbody:
                    data_rows = tbody.find_all('tr')
                else:
                    # Se não tem tbody, pular a linha de cabeçalho e usar o resto
                    if header_row is not None:
                        data_rows = rows[header_row+1:]
                    else:
                        # Tentar adivinhar - pular a primeira linha
                        data_rows = rows[1:]
                
                # 4.4 Extrair dados de cada linha
                data = []
                for row in data_rows:
                    cells = row.find_all(['td', 'th'])
                    row_data = []
                    for cell in cells:
                        row_data.append(cell.get_text(strip=True))
                    
                    # Verificar se a linha tem dados válidos e o mesmo número de colunas que os cabeçalhos
                    if row_data and len(row_data) == len(headers):
                        data.append(row_data)
                    elif row_data:
                        logger.warning(f"Linha ignorada - número de colunas não corresponde: {len(row_data)} vs {len(headers)}")
                
                # 4.5 Criar DataFrame com os dados extraídos manualmente
                if data and headers:
                    df = pd.DataFrame(data, columns=headers)
                    logger.info(f"DataFrame criado manualmente: {df.shape}")
                else:
                    logger.error("Extração manual não produziu dados válidos")
                    return None
                    
            except Exception as e:
                logger.error(f"Erro na extração manual: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                return None
                
        # 5. Validação final do DataFrame
        if df is None or df.empty:
            logger.error("Falha em todos os métodos de extração")
            st.error("Não foi possível extrair dados válidos.")
            return None
            
        # 5.1 Identificar coluna com nomes de times
        squad_col = None
        for col in df.columns:
            col_name = str(col).lower()
            # Verificar se o nome da coluna sugere que contém nomes de times
            if any(team_kw in col_name for team_kw in ['squad', 'team', 'equipe', 'time', 'clube', 'nombre']):
                squad_col = col
                logger.info(f"Coluna de times identificada pelo nome: {col}")
                break
                
        # 5.2 Se não encontrou pelo nome, procurar pela natureza dos dados
        if squad_col is None:
            for col in df.columns:
                # Verificar valores na coluna
                col_values = df[col].astype(str)
                # Times geralmente têm nomes com mais de 3 caracteres e são textos, não números
                if (col_values.str.len() > 3).mean() > 0.8 and not pd.to_numeric(col_values, errors='coerce').notna().any():
                    squad_col = col
                    logger.info(f"Coluna de times identificada pela natureza dos dados: {col}")
                    break
                    
        # 5.3 Se ainda não encontrou, usar a primeira coluna
        if squad_col is None and len(df.columns) > 0:
            squad_col = df.columns[0]
            logger.warning(f"Usando primeira coluna como coluna de times: {squad_col}")
            
        # 5.4 Renomear coluna de times para padronizar
        if squad_col is not None:
            df = df.rename(columns={squad_col: 'Squad'})
            logger.info(f"Coluna {squad_col} renomeada para 'Squad'")
        else:
            logger.error("Não foi possível identificar uma coluna de times")
            st.error("Estrutura de dados inválida: coluna de times não encontrada")
            return None
            
        # 5.5 Limpar dados
        # Remover linhas vazias e duplicadas
        df = df.dropna(subset=['Squad'])
        df = df.drop_duplicates(subset=['Squad'])
        
        # Remover qualquer linha onde Squad é um valor genérico, não um time
        generic_values = ['team', 'squad', 'equipe', 'time', 'total', 'média', 'average']
        df = df[~df['Squad'].str.lower().isin(generic_values)]
        
        # 5.6 Tentar converter colunas numéricas
        numeric_cols = []
        for col in df.columns:
            if col != 'Squad':
                try:
                    # Limpar texto e converter para número
                    df[col] = pd.to_numeric(
                        df[col].astype(str)
                           .str.replace(',', '.')  # Decimal europeu
                           .str.replace('%', '')   # Percentuais
                           .str.extract('([-+]?\d*\.?\d+)', expand=False),  # Extrair números
                        errors='coerce'
                    )
                    numeric_cols.append(col)
                except:
                    pass
                    
        logger.info(f"Colunas convertidas para numéricas: {numeric_cols}")
        
        # 5.7 Verificar se temos dados suficientes
        if len(df) < 3:
            logger.error(f"DataFrame final tem muito poucos times: {len(df)}")
            st.warning(f"Foram encontrados apenas {len(df)} times. Os dados podem estar incompletos.")
            
        # 5.8 Verificar e mapear colunas importantes
        important_cols = {
            'MP': ['mp', 'matches', 'jogos', 'p', 'pj', 'partidas'],
            'Gls': ['gls', 'goals', 'gols', 'g', 'gf'],
            'xG': ['xg', 'expected_goals', 'gols_esperados'],
            'Poss': ['poss', 'possession', 'posse']
        }
        
        for target, possible_names in important_cols.items():
            if target not in df.columns:
                for col in df.columns:
                    if str(col).lower() in possible_names:
                        df = df.rename(columns={col: target})
                        logger.info(f"Coluna {col} mapeada para {target}")
                        break
                        
        # Log final
        logger.info(f"DataFrame final: {df.shape}, colunas: {df.columns.tolist()}")
        logger.info(f"Primeiros times: {df['Squad'].head(3).tolist()}")
        
        return df
        
    except Exception as e:
        logger.error(f"Erro global no processamento de dados: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        st.error("Erro ao processar dados de estatísticas dos times.")
        return None

def get_stat(stats, col, default='N/A'):
    """
    Função auxiliar melhorada para extrair estatísticas com tratamento de erro e fallback
    """
    try:
        # Primeiro tenta o nome exato da coluna
        if col in stats and pd.notna(stats[col]) and stats[col] != '':
            return stats[col]
        
        # Mapeamento de nomes alternativos de colunas
        col_map = {
            'MP': ['MP', 'PJ', 'Matches', 'Jogos', 'Games'],
            'Gls': ['Gls', 'G', 'Gols', 'Goals', 'GF'],
            'xG': ['xG', 'ExpG', 'Expected_Goals'],
            'Poss': ['Poss', 'Posse', 'Possession', '%Posse']
        }
        
        # Se a coluna original foi encontrada no mapa, tenta os alternativos
        if col in col_map:
            for alt_col in col_map[col]:
                if alt_col in stats and pd.notna(stats[alt_col]) and stats[alt_col] != '':
                    return stats[alt_col]
                    
        # Verificar variações de case (maiúsculas/minúsculas)
        for stats_col in stats.index:
            if stats_col.lower() == col.lower() and pd.notna(stats[stats_col]) and stats[stats_col] != '':
                return stats[stats_col]
                
        return default
    except Exception as e:
        logger.warning(f"Erro ao obter estatística '{col}': {str(e)}")
        return default

def get_odds_data(selected_markets):
    """Função para coletar e formatar os dados das odds"""
    import streamlit as st
    
    try:
        odds_data = {}
        odds_text = []
        has_valid_odds = False

        # Money Line
        if selected_markets.get("money_line", False):
            st.markdown("### Money Line")
            col1, col2, col3 = st.columns(3)
            with col1:
                odds_data["home"] = st.number_input("Casa (@)", min_value=1.01, step=0.01, value=1.50, format="%.2f", key="ml_home")
            with col2:
                odds_data["draw"] = st.number_input("Empate (@)", min_value=1.01, step=0.01, value=4.00, format="%.2f", key="ml_draw")
            with col3:
                odds_data["away"] = st.number_input("Fora (@)", min_value=1.01, step=0.01, value=6.50, format="%.2f", key="ml_away")

            if all(odds_data.get(k, 0) > 1.01 for k in ["home", "draw", "away"]):
                has_valid_odds = True
                odds_text.append(
                    f"""Money Line:
- Casa: @{odds_data['home']:.2f} (Implícita: {(100/odds_data['home']):.1f}%)
- Empate: @{odds_data['draw']:.2f} (Implícita: {(100/odds_data['draw']):.1f}%)
- Fora: @{odds_data['away']:.2f} (Implícita: {(100/odds_data['away']):.1f}%)""")

        # Over/Under
        if selected_markets.get("over_under", False):
            st.markdown("### Over/Under")
            col1, col2, col3 = st.columns(3)
            with col1:
                odds_data["goals_line"] = st.number_input("Linha", min_value=0.5, value=2.5, step=0.5, format="%.1f", key="goals_line")
            with col2:
                odds_data["over"] = st.number_input(f"Over {odds_data.get('goals_line', 2.5)} (@)", min_value=1.01, step=0.01, value=1.85, format="%.2f", key="ou_over")
            with col3:
                odds_data["under"] = st.number_input(f"Under {odds_data.get('goals_line', 2.5)} (@)", min_value=1.01, step=0.01, value=1.95, format="%.2f", key="ou_under")

            if all(odds_data.get(k, 0) > 1.01 for k in ["over", "under"]):
                has_valid_odds = True
                odds_text.append(f"""Over/Under {odds_data['goals_line']}:
    - Over: @{odds_data['over']:.2f} (Implícita: {(100/odds_data['over']):.1f}%)
    - Under: @{odds_data['under']:.2f} (Implícita: {(100/odds_data['under']):.1f}%)""")

        # Chance Dupla
        if selected_markets.get("chance_dupla", False):
            st.markdown("### Chance Dupla")
            col1, col2, col3 = st.columns(3)
            with col1:
                odds_data["1x"] = st.number_input("1X (@)", min_value=1.01, step=0.01, value=1.20, format="%.2f", key="cd_1x")
            with col2:
                odds_data["12"] = st.number_input("12 (@)", min_value=1.01, step=0.01, value=1.30, format="%.2f", key="cd_12")
            with col3:
                odds_data["x2"] = st.number_input("X2 (@)", min_value=1.01, step=0.01, value=1.40, format="%.2f", key="cd_x2")

            if all(odds_data.get(k, 0) > 1.01 for k in ["1x", "12", "x2"]):
                has_valid_odds = True
                odds_text.append(f"""Chance Dupla:
    - 1X: @{odds_data['1x']:.2f} (Implícita: {(100/odds_data['1x']):.1f}%)
    - 12: @{odds_data['12']:.2f} (Implícita: {(100/odds_data['12']):.1f}%)
    - X2: @{odds_data['x2']:.2f} (Implícita: {(100/odds_data['x2']):.1f}%)""")

        # Ambos Marcam
        if selected_markets.get("ambos_marcam", False):
            st.markdown("### Ambos Marcam")
            col1, col2 = st.columns(2)
            with col1:
                odds_data["btts_yes"] = st.number_input("Sim (@)", min_value=1.01, step=0.01, value=1.75, format="%.2f", key="btts_yes")
            with col2:
                odds_data["btts_no"] = st.number_input("Não (@)", min_value=1.01, step=0.01, value=2.05, format="%.2f", key="btts_no")

            if all(odds_data.get(k, 0) > 1.01 for k in ["btts_yes", "btts_no"]):
                has_valid_odds = True
                odds_text.append(f"""Ambos Marcam:
    - Sim: @{odds_data['btts_yes']:.2f} (Implícita: {(100/odds_data['btts_yes']):.1f}%)
    - Não: @{odds_data['btts_no']:.2f} (Implícita: {(100/odds_data['btts_no']):.1f}%)""")

        # Total de Escanteios
        if selected_markets.get("escanteios", False):
            st.markdown("### Total de Escanteios")
            col1, col2, col3 = st.columns(3)
            with col1:
                odds_data["corners_line"] = st.number_input("Linha Escanteios", min_value=0.5, value=9.5, step=0.5, format="%.1f", key="corners_line")
            with col2:
                odds_data["corners_over"] = st.number_input("Over Escanteios (@)", min_value=1.01, step=0.01, value=1.85, format="%.2f", key="corners_over")
            with col3:
                odds_data["corners_under"] = st.number_input("Under Escanteios (@)", min_value=1.01, step=0.01, value=1.95, format="%.2f", key="corners_under")

            if all(odds_data.get(k, 0) > 1.01 for k in ["corners_over", "corners_under"]):
                has_valid_odds = True
                odds_text.append(f"""Total de Escanteios {odds_data['corners_line']}:
    - Over: @{odds_data['corners_over']:.2f} (Implícita: {(100/odds_data['corners_over']):.1f}%)
    - Under: @{odds_data['corners_under']:.2f} (Implícita: {(100/odds_data['corners_under']):.1f}%)""")

        # Total de Cartões
        if selected_markets.get("cartoes", False):
            st.markdown("### Total de Cartões")
            col1, col2, col3 = st.columns(3)
            with col1:
                odds_data["cards_line"] = st.number_input("Linha Cartões", min_value=0.5, value=3.5, step=0.5, format="%.1f", key="cards_line")
            with col2:
                odds_data["cards_over"] = st.number_input("Over Cartões (@)", min_value=1.01, step=0.01, value=1.85, format="%.2f", key="cards_over")
            with col3:
                odds_data["cards_under"] = st.number_input("Under Cartões (@)", min_value=1.01, step=0.01, value=1.95, format="%.2f", key="cards_under")

            if all(odds_data.get(k, 0) > 1.01 for k in ["cards_over", "cards_under"]):
                has_valid_odds = True
                odds_text.append(f"""Total de Cartões {odds_data['cards_line']}:
    - Over: @{odds_data['cards_over']:.2f} (Implícita: {(100/odds_data['cards_over']):.1f}%)
    - Under: @{odds_data['cards_under']:.2f} (Implícita: {(100/odds_data['cards_under']):.1f}%)""")

        if not has_valid_odds:
            return None
            
        return "\n\n".join(odds_text)
    except Exception as e:
        logger.error(f"Erro ao obter dados de odds: {str(e)}")
        return None

def format_prompt(stats_df, home_team, away_team, odds_data, selected_markets):
    """Formata o prompt para o GPT-4 com os dados coletados"""
    try:
        # Extrair dados dos times
        home_stats = stats_df[stats_df['Squad'] == home_team].iloc[0]
        away_stats = stats_df[stats_df['Squad'] == away_team].iloc[0]
        
        # Calcular probabilidades reais baseadas em xG e outros dados
        def calculate_real_prob(home_xg, away_xg, home_games, away_games):
            try:
                if pd.isna(home_xg) or pd.isna(away_xg):
                    return None
                
                home_xg_per_game = home_xg / home_games if home_games > 0 else 0
                away_xg_per_game = away_xg / away_games if away_games > 0 else 0
                
                # Ajuste baseado em home advantage
                home_advantage = 1.1
                adjusted_home_xg = home_xg_per_game * home_advantage
                
                total_xg = adjusted_home_xg + away_xg_per_game
                if total_xg == 0:
                    return None
                    
                home_prob = (adjusted_home_xg / total_xg) * 100
                away_prob = (away_xg_per_game / total_xg) * 100
                draw_prob = 100 - (home_prob + away_prob)
                
                return {
                    'home': home_prob,
                    'draw': draw_prob,
                    'away': away_prob
                }
            except:
                return None

        # Formatar estatísticas dos times
        home_team_stats = f"""
  * Jogos Disputados: {get_stat(home_stats, 'MP')}
  * Gols Marcados: {get_stat(home_stats, 'Gls')}
  * Expected Goals (xG): {get_stat(home_stats, 'xG')}
  * Posse de Bola: {get_stat(home_stats, 'Poss')}%"""

        away_team_stats = f"""
  * Jogos Disputados: {get_stat(away_stats, 'MP')}
  * Gols Marcados: {get_stat(away_stats, 'Gls')}
  * Expected Goals (xG): {get_stat(away_stats, 'xG')}
  * Posse de Bola: {get_stat(away_stats, 'Poss')}%"""

        # Calcular probabilidades reais
        real_probs = calculate_real_prob(
            float(get_stat(home_stats, 'xG', 0)),
            float(get_stat(away_stats, 'xG', 0)),
            float(get_stat(home_stats, 'MP', 1)),
            float(get_stat(away_stats, 'MP', 1))
        )

        # Montar o prompt completo
        full_prompt = f"""Role: Agente Analista de Probabilidades Esportivas

KNOWLEDGE BASE INTERNO:
- Estatísticas Home Team ({home_team}):{home_team_stats}

- Estatísticas Away Team ({away_team}):{away_team_stats}

PROBABILIDADES CALCULADAS:
"""
        
        if real_probs:
            full_prompt += f"""- Vitória {home_team}: {real_probs['home']:.1f}% (Real)
- Empate: {real_probs['draw']:.1f}% (Real)
- Vitória {away_team}: {real_probs['away']:.1f}% (Real)
"""
        else:
            full_prompt += "Dados insuficientes para cálculo de probabilidades reais\n"

        # Adicionar informações sobre quais mercados foram selecionados
        selected_market_names = []
        full_prompt += "\nMERCADOS SELECIONADOS PARA ANÁLISE:\n"
        for market, selected in selected_markets.items():
            if selected:
                market_names = {
                    "money_line": "Money Line (1X2)",
                    "over_under": "Over/Under Gols",
                    "chance_dupla": "Chance Dupla",
                    "ambos_marcam": "Ambos Marcam",
                    "escanteios": "Total de Escanteios",
                    "cartoes": "Total de Cartões"
                }
                market_name = market_names.get(market, market)
                selected_market_names.append(market_name)
                full_prompt += f"- {market_name}\n"

        # Instrução muito clara sobre o formato de saída
        full_prompt += f"""
INSTRUÇÕES ESPECIAIS: VOCÊ DEVE CALCULAR PROBABILIDADES REAIS PARA TODOS OS MERCADOS LISTADOS ACIMA, não apenas para o Money Line. Use os dados disponíveis e sua expertise para estimar probabilidades reais para CADA mercado selecionado.

[SAÍDA OBRIGATÓRIA]

# Análise da Partida
## {home_team} x {away_team}

# Análise de Mercados Disponíveis:
{odds_data}

# Probabilidades Calculadas (REAL vs IMPLÍCITA):
[IMPORTANTE - Para cada um dos mercados abaixo, você DEVE mostrar a probabilidade REAL calculada, bem como a probabilidade IMPLÍCITA nas odds:]
{chr(10).join([f"- {name}" for name in selected_market_names])}

# Oportunidades Identificadas (Edges >3%):
[Listagem detalhada de cada mercado selecionado, indicando explicitamente se há edge ou não para cada opção.]

# Nível de Confiança Geral: [Baixo/Médio/Alto]
[Breve explicação da sua confiança na análise]
"""
        return full_prompt

    except Exception as e:
        logger.error(f"Erro ao formatar prompt: {str(e)}")
        return None
