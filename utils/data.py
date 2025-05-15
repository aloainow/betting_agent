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

# Funções que estavam faltando e causando o erro
def get_configured_odds():
    """
    Retorna as odds configuradas para a partida atual.
    Esta é uma função stub adicionada para corrigir o erro de importação.
    """
    logger.info("Função get_configured_odds chamada (stub)")
    return "Odds não disponíveis"

def get_match_odds(match_id):
    """
    Retorna as odds para uma partida específica.
    Esta é uma função stub adicionada para corrigir o erro de importação.
    """
    logger.info(f"Função get_match_odds chamada para match_id={match_id} (stub)")
    return "Odds não disponíveis"

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

    def verify_login(self, email, password):
        """
        Verifica as credenciais de login do usuário
        
        Args:
            email (str): Email do usuário
            password (str): Senha do usuário
            
        Returns:
            bool: True se as credenciais forem válidas, False caso contrário
        """
        # Verificar se o email existe
        if email not in self.users:
            return False
        
        # Verificar a senha
        user_data = self.users[email]
        stored_password = user_data.get('password', '')
        
        # Hash da senha fornecida
        hashed_password = self._hash_password(password)
        
        # Comparar as senhas
        if stored_password == hashed_password:
            return True
        
        return False
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
            tier_credits = tier.total_credits
            
            # Add purchased credits
            purchased_credits = user.get("purchased_credits", 0)
            total_credits = tier_credits + purchased_credits
            
            # Calculate remaining credits
            credits_remaining = max(0, total_credits - total_credits_used)
            
            # Get market limit
            market_limit = tier.market_limit
            
            # Format tier name for display
            tier_display = self._format_tier_name(tier_name)
            
            # Get user name
            name = user.get("name", email.split('@')[0].capitalize())
            
            return {
                "name": name,
                "tier": tier_name,
                "tier_display": tier_display,
                "credits_used": total_credits_used,
                "credits_total": total_credits,
                "credits_remaining": credits_remaining,
                "market_limit": market_limit,
                "verified": True
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas para {email}: {str(e)}")
            return {
                "name": "Erro",
                "tier": "free",
                "tier_display": "Free",
                "credits_used": 0,
                "credits_total": 5,
                "credits_remaining": 5,
                "market_limit": float('inf')
            }
    
    def register_usage(self, email: str, num_markets: int = 1) -> bool:
        """Register usage of credits"""
        try:
            if email not in self.users:
                logger.warning(f"Tentativa de registrar uso para usuário inexistente: {email}")
                return False
                
            # Verificar se o usuário está verificado
            if not self.users[email].get('verified', False):
                logger.warning(f"Tentativa de registrar uso para usuário não verificado: {email}")
                return False
                
            # Verificar se o usuário tem créditos suficientes
            stats = self.get_usage_stats(email)
            credits_remaining = stats.get('credits_remaining', 0)
            
            if credits_remaining < num_markets:
                logger.warning(f"Usuário {email} não tem créditos suficientes: {credits_remaining} < {num_markets}")
                return False
                
            # Registrar uso
            now = datetime.now()
            usage_entry = {
                "timestamp": now.isoformat(),
                "markets": num_markets
            }
            
            # Adicionar ao uso total
            if "usage" not in self.users[email]:
                self.users[email]["usage"] = {"daily": [], "total": []}
                
            if "total" not in self.users[email]["usage"]:
                self.users[email]["usage"]["total"] = []
                
            self.users[email]["usage"]["total"].append(usage_entry)
            
            # Adicionar ao uso diário
            today = now.strftime("%Y-%m-%d")
            
            if "daily" not in self.users[email]["usage"]:
                self.users[email]["usage"]["daily"] = []
                
            # Verificar se já existe uma entrada para hoje
            today_entry = None
            for entry in self.users[email]["usage"]["daily"]:
                entry_date = entry.get("date")
                if entry_date == today:
                    today_entry = entry
                    break
                    
            if today_entry:
                today_entry["markets"] += num_markets
            else:
                self.users[email]["usage"]["daily"].append({
                    "date": today,
                    "markets": num_markets
                })
                
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
        except Exception as e:
            logger.error(f"Erro ao registrar uso para {email}: {str(e)}")
            return False
    
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
                    logger.error("Não foi possível identificar células de cabeçalho")
                    return None
                    
                # 4.2 Extrair nomes de colunas
                column_names = []
                for cell in header_cells:
                    # Tentar obter o texto do cabeçalho
                    header_text = cell.get_text(strip=True)
                    if not header_text:
                        # Se não tem texto, usar um nome genérico
                        header_text = f"Col{len(column_names)}"
                    column_names.append(header_text)
                
                logger.info(f"Nomes de colunas extraídos: {column_names}")
                
                # 4.3 Extrair dados das linhas
                data_rows = []
                
                # Se tem tbody, usar as linhas de lá
                tbody = stats_table.find('tbody')
                if tbody:
                    data_tr_elements = tbody.find_all('tr')
                else:
                    # Se não tem tbody, pular a linha de cabeçalho
                    if header_row is not None:
                        data_tr_elements = rows[header_row+1:]
                    else:
                        # Se não identificou cabeçalho, usar todas as linhas exceto a primeira
                        data_tr_elements = rows[1:]
                
                # Processar cada linha de dados
                for tr in data_tr_elements:
                    cells = tr.find_all(['td', 'th'])
                    
                    # Verificar se a linha tem células suficientes
                    if len(cells) < 3:  # Muito poucas células, provavelmente não é uma linha de dados
                        continue
                        
                    # Extrair valores das células
                    row_data = []
                    for cell in cells:
                        # Obter texto da célula
                        cell_text = cell.get_text(strip=True)
                        row_data.append(cell_text)
                    
                    # Adicionar à lista de linhas
                    if len(row_data) > 0:
                        data_rows.append(row_data)
                
                # 4.4 Criar DataFrame
                if data_rows:
                    # Ajustar tamanho das linhas para corresponder aos cabeçalhos
                    num_cols = len(column_names)
                    adjusted_rows = []
                    for row in data_rows:
                        if len(row) > num_cols:
                            # Truncar linhas muito longas
                            adjusted_rows.append(row[:num_cols])
                        elif len(row) < num_cols:
                            # Preencher linhas muito curtas
                            adjusted_rows.append(row + [''] * (num_cols - len(row)))
                        else:
                            adjusted_rows.append(row)
                    
                    # Criar DataFrame
                    df = pd.DataFrame(adjusted_rows, columns=column_names)
                    logger.info(f"DataFrame criado manualmente: {df.shape}")
                else:
                    logger.error("Nenhuma linha de dados extraída")
                    return None
                    
            except Exception as e:
                logger.error(f"Erro na extração manual: {str(e)}")
                return None
                
        # 5. Pós-processamento do DataFrame
        if df is not None:
            try:
                # 5.1 Identificar coluna de equipes
                team_column = None
                for col in df.columns:
                    # Verificar se o nome da coluna indica equipes
                    if col.lower() in ['squad', 'team', 'equipe', 'time', 'clube']:
                        team_column = col
                        break
                
                # Se não encontrou pelo nome, procurar pela primeira coluna com strings longas
                if not team_column:
                    for col in df.columns:
                        col_values = df[col].astype(str)
                        if any(len(val) > 3 for val in col_values):
                            team_column = col
                            logger.info(f"Coluna de equipes identificada por conteúdo: {col}")
                            break
                
                if not team_column:
                    # Usar a primeira coluna como fallback
                    team_column = df.columns[0]
                    logger.warning(f"Usando primeira coluna como coluna de equipes: {team_column}")
                
                # 5.2 Renomear coluna de equipes para padrão
                df = df.rename(columns={team_column: 'Squad'})
                
                # 5.3 Limpar e converter dados
                # Remover linhas sem nome de equipe
                df = df[df['Squad'].notna() & (df['Squad'] != '')]
                
                # Converter colunas numéricas
                for col in df.columns:
                    if col != 'Squad':
                        try:
                            # Substituir vírgulas por pontos
                            df[col] = df[col].astype(str).str.replace(',', '.')
                            # Converter para numérico
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        except:
                            pass
                
                logger.info(f"DataFrame final: {df.shape}")
                return df
                
            except Exception as e:
                logger.error(f"Erro no pós-processamento do DataFrame: {str(e)}")
                return df  # Retornar o DataFrame mesmo com erro no pós-processamento
        
        return None
        
    except Exception as e:
        logger.error(f"Erro geral no parse_team_stats: {str(e)}")
        return None

def get_stat(team_stats, stat_name, default=0):
    """
    Obtém uma estatística específica de um time com tratamento de erros.
    
    Args:
        team_stats: Linha do DataFrame com estatísticas do time
        stat_name: Nome da estatística desejada
        default: Valor padrão caso a estatística não exista
        
    Returns:
        Valor da estatística ou valor padrão
    """
    try:
        # Verificar se a estatística existe
        if stat_name in team_stats:
            value = team_stats[stat_name]
            
            # Verificar se é NaN
            if pd.isna(value):
                return default
                
            # Verificar se é string e converter para número se possível
            if isinstance(value, str):
                try:
                    # Substituir vírgula por ponto para conversão
                    value = value.replace(',', '.')
                    return float(value)
                except:
                    return value
                    
            return value
        else:
            return default
    except Exception as e:
        logger.error(f"Erro ao obter estatística {stat_name}: {str(e)}")
        return default
