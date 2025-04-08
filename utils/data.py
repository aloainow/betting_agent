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
    
    def register_user(self, email: str, password: str, name: str = None, tier: str = "free", verified: bool = False, verification_code: str = None) -> tuple:
        """Register a new user with verification support"""
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
            
            # Se não foi fornecido código de verificação, gerar um
            if verification_code is None:
                from utils.email_verification import generate_verification_code
                verification_code = generate_verification_code()
                    
            self.users[email] = {
                "password": self._hash_password(password),
                "name": name,  # Adicionando o nome
                "tier": tier,
                "verified": verified,  # Novo campo para verificação
                "verification_code": verification_code,  # Código de verificação
                "usage": {
                    "daily": [],
                    "total": []  # Track total usage
                },
                "purchased_credits": 0,  # Track additional purchased credits
                "free_credits_exhausted_at": None,  # Timestamp when free credits run out
                "paid_credits_exhausted_at": None,  # Timestamp when paid credits run out
                "created_at": datetime.now().isoformat()
            }
            
            # Se o usuário não está verificado, não dar créditos ainda
            if not verified:
                self.users[email]["credits_remaining"] = 0
            
            save_success = self._save_users()
            if not save_success:
                logger.warning(f"Falha ao salvar dados durante registro do usuário: {email}")
                
            logger.info(f"Usuário registrado com sucesso: {email}, tier: {tier}, verificado: {verified}")
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
    
    def verify_email_code(self, email, user_provided_code):
        """
        Verifica se o código fornecido pelo usuário corresponde ao código armazenado
        
        Args:
            email (str): Email do usuário
            user_provided_code (str): Código fornecido pelo usuário
            
        Returns:
            bool: True se o código for válido, False caso contrário
        """
        try:
            if email not in self.users:
                logger.warning(f"Tentativa de verificar código para usuário inexistente: {email}")
                return False
                
            user = self.users[email]
            stored_code = user.get('verification_code')
            
            # Verificar se os códigos correspondem
            if stored_code and user_provided_code == stored_code:
                # Atualizar status do usuário para verificado
                self.users[email]['verified'] = True
                
                # Adicionar créditos gratuitos se ainda não foram adicionados
                if self.users[email].get('credits_remaining', 0) == 0:
                    # Conceder 5 créditos gratuitos para usuários verificados
                    logger.info(f"Concedendo 5 créditos gratuitos para usuário verificado: {email}")
                
                # Salvar alterações
                self._save_users()
                logger.info(f"Email verificado com sucesso: {email}")
                return True
                
            logger.warning(f"Código de verificação inválido para {email}")
            return False
        except Exception as e:
            import traceback
            logger.error(f"Erro ao verificar código para {email}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def update_verification_code(self, email, new_code):
        """
        Atualiza o código de verificação para um usuário
        
        Args:
            email (str): Email do usuário
            new_code (str): Novo código de verificação
            
        Returns:
            bool: True se o código foi atualizado, False caso contrário
        """
        try:
            if email not in self.users:
                logger.warning(f"Tentativa de atualizar código para usuário inexistente: {email}")
                return False
                
            # Atualizar código
            self.users[email]['verification_code'] = new_code
            
            # Salvar alterações
            self._save_users()
            logger.info(f"Código de verificação atualizado para {email}")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar código para {email}: {str(e)}")
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
            
            # Se o usuário não está verificado, mostrar 0 créditos
            if not user.get('verified', True):
                logger.info(f"Usuário não verificado: {email}")
                return {
                    "name": user.get("name", email.split('@')[0].capitalize()),
                    "tier": user.get("tier", "free"),
                    "tier_display": self._format_tier_name(user.get("tier", "free")),
                    "credits_used": 0,
                    "credits_total": 0,
                    "credits_remaining": 0,
                    "market_limit": float('inf'),
                    "verified": False
                }
            
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
                "next_free_credits_time": next_free_credits_time,
                "verified": user.get('verified', True)
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
                "market_limit": float('inf'),
                "verified": False
            }
    
    def record_usage(self, email, num_markets, analysis_data=None):
        """Record usage of credits"""
        if email not in self.users:
            logger.warning(f"Tentativa de registrar uso para usuário inexistente: {email}")
            return False
            
        # Verificar se o usuário está verificado
        if not self.users[email].get('verified', True):
            logger.warning(f"Tentativa de registrar uso para usuário não verificado: {email}")
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

   
    # Mensagem de erro simples e clara
    logger.error(f"Não foi possível carregar os dados do campeonato {league_name} após múltiplas tentativas")
    return None
    # Adicione esta função em utils/ai.py ou utils/data.py

def extract_team_stats(stats_df, team_name):
    """
    Extrai estatísticas abrangentes de um time específico.
    Retorna um dicionário organizado com todas as estatísticas relevantes.
    """
    from utils.data import get_stat
    import pandas as pd
    import logging
    
    logger = logging.getLogger("valueHunter.stats")
    
    # Verifica se o time existe no DataFrame
    if team_name not in stats_df['Squad'].values:
        logger.error(f"Time {team_name} não encontrado no DataFrame")
        return {}
    
    # Obter linha de estatísticas do time
    team_stats = stats_df[stats_df['Squad'] == team_name].iloc[0]
    
    # Função auxiliar para obter estatística com tratamento
    def get_numeric_stat(stat_name, default=0):
        value = get_stat(team_stats, stat_name, default)
        if value == 'N/A':
            return default
            
        # Converter para número se for string
        if isinstance(value, str):
            value = value.replace(',', '.')
            try:
                return float(value)
            except:
                return default
        return value
    
    # Função para calcular estatísticas por jogo
    def per_game(stat, games):
        if games <= 0:
            return 0
        return round(stat / games, 2)
    
    # Jogos disputados (valor base importante)
    matches_played = get_numeric_stat('MP', 1)  # Default 1 para evitar divisão por zero
    
    # Estatísticas coletadas
    stats = {
        # Básicas
        "matches_played": matches_played,
        "points": get_numeric_stat("Pts"),
        "points_per_game": per_game(get_numeric_stat("Pts"), matches_played),
        
        # Ofensivas
        "goals_scored": get_numeric_stat("Gls"),
        "goals_per_game": per_game(get_numeric_stat("Gls"), matches_played),
        "expected_goals": get_numeric_stat("xG"),
        "expected_goals_per_game": per_game(get_numeric_stat("xG"), matches_played),
        "shots": get_numeric_stat("Sh"),
        "shots_on_target": get_numeric_stat("SoT"),
        "shots_on_target_percentage": get_numeric_stat("SoT%", 0),
        
        # Defensivas
        "goals_against": get_numeric_stat("GA"),
        "goals_against_per_game": per_game(get_numeric_stat("GA"), matches_played),
        "expected_goals_against": get_numeric_stat("xGA"),
        "expected_goals_against_per_game": per_game(get_numeric_stat("xGA"), matches_played),
        "clean_sheets": get_numeric_stat("CS"),
        "clean_sheets_percentage": round(get_numeric_stat("CS") * 100 / matches_played, 1) if matches_played > 0 else 0,
        
        # Posse e Passes
        "possession": get_numeric_stat("Poss"),
        "passes_completed": get_numeric_stat("Cmp"),
        "passes_attempted": get_numeric_stat("Att"),
        "pass_completion": get_numeric_stat("Cmp%"),
        
        # Outros
        "yellow_cards": get_numeric_stat("CrdY"),
        "red_cards": get_numeric_stat("CrdR"),
        "fouls": get_numeric_stat("Fls"),
        "corners": get_numeric_stat("CK"),
        
        # Eficiência e análise
        "goal_efficiency": round((get_numeric_stat("Gls") / get_numeric_stat("xG", 0.01)) * 100, 1) if get_numeric_stat("xG", 0) > 0 else 100,
        "defensive_efficiency": round((get_numeric_stat("GA") / get_numeric_stat("xGA", 0.01)) * 100, 1) if get_numeric_stat("xGA", 0) > 0 else 100,
        "goal_difference": get_numeric_stat("Gls") - get_numeric_stat("GA"),
        "expected_goal_difference": round(get_numeric_stat("xG") - get_numeric_stat("xGA"), 2),
    }
    
    # Corrigir valores extremos ou inesperados
    for key, value in stats.items():
        if value is None or pd.isna(value):
            stats[key] = 0
        elif key.endswith("percentage") and value > 100:
            stats[key] = 100
    
    return stats

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

# Substituir completamente a função  em utils/data.py

def get_odds_data(selected_markets):
    """
    Captura as odds configuradas pelo usuário na interface.
    
    Args:
        selected_markets (dict): Mercados selecionados pelo usuário
        
    Returns:
        str: String formatada com as odds capturadas
    """
    import streamlit as st
    import logging
    
    logger = logging.getLogger("valueHunter.data")
    logger.info(f"Capturando odds para mercados: {selected_markets}")
    
    # Inicializar dicionário de configuração de odds na sessão se não existir
    if 'odds_config' not in st.session_state:
        st.session_state.odds_config = {}
    
    odds_text = []
    
    # Money Line (1X2)
    if selected_markets.get("money_line", False):
        odds_text.append("Money Line (1X2):")
        
        # Valores padrão ou recuperados da sessão
        default_casa = st.session_state.odds_config.get('ml_casa_odd', 1.35)
        default_empate = st.session_state.odds_config.get('ml_empate_odd', 5.25)
        default_fora = st.session_state.odds_config.get('ml_fora_odd', 7.50)
        
        # Adicionar campos de input para usuário
        st.subheader("Money Line (1X2)")
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                casa_odd = st.number_input("Casa (@)", value=float(default_casa), 
                                          min_value=1.01, max_value=100.0, step=0.05, 
                                          key='ml_casa_odd_input')
                st.session_state.odds_config['ml_casa_odd'] = casa_odd
            with col2:
                empate_odd = st.number_input("Empate (@)", value=float(default_empate), 
                                            min_value=1.01, max_value=100.0, step=0.05, 
                                            key='ml_empate_odd_input')
                st.session_state.odds_config['ml_empate_odd'] = empate_odd
            with col3:
                fora_odd = st.number_input("Fora (@)", value=float(default_fora), 
                                          min_value=1.01, max_value=100.0, step=0.05, 
                                          key='ml_fora_odd_input')
                st.session_state.odds_config['ml_fora_odd'] = fora_odd
        
        odds_text.append(f"• Casa: @{casa_odd:.2f}")
        odds_text.append(f"• Empate: @{empate_odd:.2f}")
        odds_text.append(f"• Fora: @{fora_odd:.2f}")
    
    # Chance Dupla
    if selected_markets.get("chance_dupla", False):
        odds_text.append("\nChance Dupla:")
        
        # Valores padrão ou recuperados da sessão
        default_1x = st.session_state.odds_config.get('cd_1x_odd', 1.10)
        default_12 = st.session_state.odds_config.get('cd_12_odd', 1.16)
        default_x2 = st.session_state.odds_config.get('cd_x2_odd', 3.00)
        
        st.subheader("Chance Dupla")
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                cd_1x_odd = st.number_input("1X (@)", value=float(default_1x), 
                                           min_value=1.01, max_value=100.0, step=0.05, 
                                           key='cd_1x_odd_input')
                st.session_state.odds_config['cd_1x_odd'] = cd_1x_odd
            with col2:
                cd_12_odd = st.number_input("12 (@)", value=float(default_12), 
                                           min_value=1.01, max_value=100.0, step=0.05, 
                                           key='cd_12_odd_input')
                st.session_state.odds_config['cd_12_odd'] = cd_12_odd
            with col3:
                cd_x2_odd = st.number_input("X2 (@)", value=float(default_x2), 
                                           min_value=1.01, max_value=100.0, step=0.05, 
                                           key='cd_x2_odd_input')
                st.session_state.odds_config['cd_x2_odd'] = cd_x2_odd
        
        odds_text.append(f"• 1X: @{cd_1x_odd:.2f}")
        odds_text.append(f"• 12: @{cd_12_odd:.2f}")
        odds_text.append(f"• X2: @{cd_x2_odd:.2f}")
    
    # Ambos Marcam
    if selected_markets.get("ambos_marcam", False):
        odds_text.append("\nAmbos Marcam (BTTS):")
        
        # Valores padrão ou recuperados da sessão
        default_sim = st.session_state.odds_config.get('btts_sim_odd', 2.00)
        default_nao = st.session_state.odds_config.get('btts_nao_odd', 1.80)
        
        st.subheader("Ambos Marcam (BTTS)")
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                btts_sim_odd = st.number_input("Sim (@)", value=float(default_sim), 
                                              min_value=1.01, max_value=100.0, step=0.05, 
                                              key='btts_sim_odd_input')
                st.session_state.odds_config['btts_sim_odd'] = btts_sim_odd
            with col2:
                btts_nao_odd = st.number_input("Não (@)", value=float(default_nao), 
                                              min_value=1.01, max_value=100.0, step=0.05, 
                                              key='btts_nao_odd_input')
                st.session_state.odds_config['btts_nao_odd'] = btts_nao_odd
        
        odds_text.append(f"• Sim (BTTS): @{btts_sim_odd:.2f}")
        odds_text.append(f"• Não (BTTS): @{btts_nao_odd:.2f}")
    
    # Gols (Over/Under)
    if selected_markets.get("over_under", False):
        odds_text.append("\nTotal de Gols:")
        
        # Valores padrão ou recuperados da sessão
        default_linha = st.session_state.odds_config.get('gols_linha', 2.5)
        default_over = st.session_state.odds_config.get('gols_over_odd', 1.90)
        default_under = st.session_state.odds_config.get('gols_under_odd', 1.90)
        
        st.subheader("Total de Gols")
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                linha_options = [0.5, 1.5, 2.5, 3.5, 4.5]
                linha_index = linha_options.index(default_linha) if default_linha in linha_options else 2
                gols_linha = st.selectbox("Linha", linha_options, index=linha_index, key='gols_linha_input')
                st.session_state.odds_config['gols_linha'] = gols_linha
            with col2:
                gols_over_odd = st.number_input(f"Over {gols_linha} (@)", value=float(default_over), 
                                               min_value=1.01, max_value=100.0, step=0.05, 
                                               key='gols_over_odd_input')
                st.session_state.odds_config['gols_over_odd'] = gols_over_odd
            with col3:
                gols_under_odd = st.number_input(f"Under {gols_linha} (@)", value=float(default_under), 
                                                min_value=1.01, max_value=100.0, step=0.05, 
                                                key='gols_under_odd_input')
                st.session_state.odds_config['gols_under_odd'] = gols_under_odd
        
        odds_text.append(f"• Over {gols_linha} Gols: @{gols_over_odd:.2f}")
        odds_text.append(f"• Under {gols_linha} Gols: @{gols_under_odd:.2f}")
    
    # Escanteios
    if selected_markets.get("escanteios", False):
        odds_text.append("\nTotal de Escanteios:")
        
        # Valores padrão ou recuperados da sessão
        default_linha = st.session_state.odds_config.get('corners_linha', 9.5)
        default_over = st.session_state.odds_config.get('corners_over_odd', 1.85)
        default_under = st.session_state.odds_config.get('corners_under_odd', 1.85)
        
        st.subheader("Total de Escanteios")
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                linha_options = [7.5, 8.5, 9.5, 10.5, 11.5]
                linha_index = linha_options.index(default_linha) if default_linha in linha_options else 2
                corners_linha = st.selectbox("Linha", linha_options, index=linha_index, key='corners_linha_input')
                st.session_state.odds_config['corners_linha'] = corners_linha
            with col2:
                corners_over_odd = st.number_input(f"Over {corners_linha} (@)", value=float(default_over), 
                                                  min_value=1.01, max_value=100.0, step=0.05, 
                                                  key='corners_over_odd_input')
                st.session_state.odds_config['corners_over_odd'] = corners_over_odd
            with col3:
                corners_under_odd = st.number_input(f"Under {corners_linha} (@)", value=float(default_under), 
                                                   min_value=1.01, max_value=100.0, step=0.05, 
                                                   key='corners_under_odd_input')
                st.session_state.odds_config['corners_under_odd'] = corners_under_odd
        
        odds_text.append(f"• Over {corners_linha} Escanteios: @{corners_over_odd:.2f}")
        odds_text.append(f"• Under {corners_linha} Escanteios: @{corners_under_odd:.2f}")
    
    # Cartões
    if selected_markets.get("cartoes", False):
        odds_text.append("\nTotal de Cartões:")
        
        # Valores padrão ou recuperados da sessão
        default_linha = st.session_state.odds_config.get('cards_linha', 3.5)
        default_over = st.session_state.odds_config.get('cards_over_odd', 1.85)
        default_under = st.session_state.odds_config.get('cards_under_odd', 1.85)
        
        st.subheader("Total de Cartões")
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                linha_options = [2.5, 3.5, 4.5, 5.5, 6.5]
                linha_index = linha_options.index(default_linha) if default_linha in linha_options else 1
                cards_linha = st.selectbox("Linha", linha_options, index=linha_index, key='cards_linha_input')
                st.session_state.odds_config['cards_linha'] = cards_linha
            with col2:
                cards_over_odd = st.number_input(f"Over {cards_linha} (@)", value=float(default_over), 
                                               min_value=1.01, max_value=100.0, step=0.05, 
                                               key='cards_over_odd_input')
                st.session_state.odds_config['cards_over_odd'] = cards_over_odd
            with col3:
                cards_under_odd = st.number_input(f"Under {cards_linha} (@)", value=float(default_under), 
                                                min_value=1.01, max_value=100.0, step=0.05, 
                                                key='cards_under_odd_input')
                st.session_state.odds_config['cards_under_odd'] = cards_under_odd
        
        odds_text.append(f"• Over {cards_linha} Cartões: @{cards_over_odd:.2f}")
        odds_text.append(f"• Under {cards_linha} Cartões: @{cards_under_odd:.2f}")
    
    # Juntar tudo em uma string formatada
    odds_data = "\n".join(odds_text)
    
    # Log das odds capturadas
    logger.info(f"Odds configuradas pelo usuário: {odds_data}")
    
    return odds_data
def validate_match_data(match_data):
    """
    Valida se os dados de uma partida estão completos o suficiente para análise.
    
    Args:
        match_data (dict): Dados da partida a serem validados
        
    Returns:
        tuple: (bool, str) - (dados válidos, mensagem de erro)
    """
    if not match_data or not isinstance(match_data, dict):
        return False, "Dados de partida ausentes ou inválidos."
    
    # Verificar estrutura básica
    if not all(key in match_data for key in ["match_info", "home_team", "away_team"]):
        return False, "Estrutura de dados incompleta."
    
    # Verificar times
    home_team = match_data.get("home_team", {})
    away_team = match_data.get("away_team", {})
    
    # Verificar se dados básicos estão presentes
    if not home_team or not away_team:
        return False, "Dados de times ausentes."
    
    # Verificar se há dados estatísticos mínimos
    min_stats = ["played", "wins", "draws", "losses", "goals_scored", "goals_conceded"]
    
    home_has_stats = all(stat in home_team for stat in min_stats)
    away_has_stats = all(stat in away_team for stat in min_stats)
    
    if not home_has_stats or not away_has_stats:
        return False, "Estatísticas básicas faltando para os times."
    
    # Verificar se os dados não são todos zeros
    home_all_zeros = all(home_team.get(stat, 0) == 0 for stat in min_stats)
    away_all_zeros = all(away_team.get(stat, 0) == 0 for stat in min_stats)
    
    if home_all_zeros and away_all_zeros:
        return False, "Todos os dados estatísticos são zero."
    
    # Verificar dados de jogos recentes
    if "recent_matches" in home_team:
        # Se existe recent_matches mas só tem times da Premier League e os times atuais são de outra liga, provavelmente é fallback
        home_opponents = [match.get("opponent", "") for match in home_team.get("recent_matches", [])]
        premier_league_teams = ["Liverpool", "Chelsea", "Arsenal", "Tottenham", "Man Utd"]
        
        if home_opponents and all(opponent in premier_league_teams for opponent in home_opponents):
            if match_data["match_info"].get("league") and "Premier League" not in match_data["match_info"].get("league"):
                return False, "Dados de partidas recentes incompatíveis com a liga."
    
    return True, "Dados válidos."

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
