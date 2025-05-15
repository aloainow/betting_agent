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
    
def get_odds_data(selected_markets):
    """
    Exibe campos de input para as odds dos mercados selecionados e retorna os valores inseridos.
    
    Args:
        selected_markets (dict): Dicionário com os mercados selecionados
        
    Returns:
        dict: Dicionário com as odds configuradas para cada mercado
    """
    logger.info(f"Exibindo inputs para odds dos mercados: {[k for k, v in selected_markets.items() if v]}")
    
    odds_data = {}
    
    # Verificar se algum mercado foi selecionado
    if not any(selected_markets.values()):
        st.warning("Selecione pelo menos um mercado para configurar odds.")
        return None
    
    # Money Line (1X2)
    if selected_markets.get("money_line"):
        st.subheader("Money Line (1X2)")
        col1, col2, col3 = st.columns(3)
        with col1:
            home_win = st.number_input("Casa (1)", min_value=1.01, max_value=50.0, value=2.0, step=0.05, format="%.2f", key="ml_home")
        with col2:
            draw = st.number_input("Empate (X)", min_value=1.01, max_value=50.0, value=3.2, step=0.05, format="%.2f", key="ml_draw")
        with col3:
            away_win = st.number_input("Fora (2)", min_value=1.01, max_value=50.0, value=3.5, step=0.05, format="%.2f", key="ml_away")
        
        odds_data["money_line"] = {
            "home": home_win,
            "draw": draw,
            "away": away_win
        }
    
    # Total de Gols (Over/Under)
    if selected_markets.get("over_under"):
        st.subheader("Total de Gols")
        col1, col2 = st.columns(2)
        with col1:
            over_odds = st.number_input("Over 2.5", min_value=1.01, max_value=10.0, value=1.85, step=0.05, format="%.2f", key="ou_over")
        with col2:
            under_odds = st.number_input("Under 2.5", min_value=1.01, max_value=10.0, value=1.95, step=0.05, format="%.2f", key="ou_under")
        
        odds_data["over_under"] = {
            "over": over_odds,
            "under": under_odds
        }
    
    # Chance Dupla
    if selected_markets.get("chance_dupla"):
        st.subheader("Chance Dupla")
        col1, col2, col3 = st.columns(3)
        with col1:
            home_draw = st.number_input("Casa ou Empate (1X)", min_value=1.01, max_value=10.0, value=1.3, step=0.05, format="%.2f", key="cd_home_draw")
        with col2:
            home_away = st.number_input("Casa ou Fora (12)", min_value=1.01, max_value=10.0, value=1.25, step=0.05, format="%.2f", key="cd_home_away")
        with col3:
            draw_away = st.number_input("Empate ou Fora (X2)", min_value=1.01, max_value=10.0, value=1.6, step=0.05, format="%.2f", key="cd_draw_away")
        
        odds_data["chance_dupla"] = {
            "home_draw": home_draw,
            "home_away": home_away,
            "draw_away": draw_away
        }
    
    # Ambos Marcam
    if selected_markets.get("ambos_marcam"):
        st.subheader("Ambos Marcam")
        col1, col2 = st.columns(2)
        with col1:
            btts_yes = st.number_input("Sim", min_value=1.01, max_value=10.0, value=1.8, step=0.05, format="%.2f", key="btts_yes")
        with col2:
            btts_no = st.number_input("Não", min_value=1.01, max_value=10.0, value=2.0, step=0.05, format="%.2f", key="btts_no")
        
        odds_data["ambos_marcam"] = {
            "yes": btts_yes,
            "no": btts_no
        }
    
    # Total de Escanteios
    if selected_markets.get("escanteios"):
        st.subheader("Total de Escanteios")
        col1, col2 = st.columns(2)
        with col1:
            corners_over = st.number_input("Over 9.5", min_value=1.01, max_value=10.0, value=1.85, step=0.05, format="%.2f", key="corners_over")
        with col2:
            corners_under = st.number_input("Under 9.5", min_value=1.01, max_value=10.0, value=1.95, step=0.05, format="%.2f", key="corners_under")
        
        odds_data["escanteios"] = {
            "over": corners_over,
            "under": corners_under
        }
    
    # Total de Cartões
    if selected_markets.get("cartoes"):
        st.subheader("Total de Cartões")
        col1, col2 = st.columns(2)
        with col1:
            cards_over = st.number_input("Over 3.5", min_value=1.01, max_value=10.0, value=1.85, step=0.05, format="%.2f", key="cards_over")
        with col2:
            cards_under = st.number_input("Under 3.5", min_value=1.01, max_value=10.0, value=1.95, step=0.05, format="%.2f", key="cards_under")
        
        odds_data["cartoes"] = {
            "over": cards_over,
            "under": cards_under
        }
    
    # Verificar se temos dados de odds
    if not odds_data:
        st.warning("Nenhum mercado selecionado para configurar odds.")
        return None
    
    return odds_data

def format_prompt(team_stats, selected_markets, odds_data):
    """
    Formata um prompt para análise de partida com base nas odds e mercados selecionados.
    
    Args:
        team_stats (dict): Estatísticas dos times
        selected_markets (dict): Mercados selecionados
        odds_data (dict): Odds configuradas
        
    Returns:
        str: Prompt formatado para análise
    """
    logger.info("Formatando prompt para análise de partida")
    
    # Verificar se temos dados necessários
    if not team_stats or not selected_markets or not odds_data:
        return "Dados insuficientes para análise."
    
    # Extrair informações básicas
    home_team = team_stats.get("match_info", {}).get("home_team", "Time da Casa")
    away_team = team_stats.get("match_info", {}).get("away_team", "Time Visitante")
    league = team_stats.get("match_info", {}).get("league", "Liga não especificada")
    
    # Construir o prompt
    prompt = f"Análise da partida {home_team} vs {away_team} na {league}.\n\n"
    prompt += "Mercados e odds selecionados:\n"
    
    # Adicionar informações de cada mercado
    if selected_markets.get("money_line") and "money_line" in odds_data:
        prompt += f"- Money Line (1X2): Casa {odds_data['money_line']['home']}, Empate {odds_data['money_line']['draw']}, Fora {odds_data['money_line']['away']}\n"
    
    if selected_markets.get("over_under") and "over_under" in odds_data:
        prompt += f"- Total de Gols: Over 2.5 {odds_data['over_under']['over']}, Under 2.5 {odds_data['over_under']['under']}\n"
    
    if selected_markets.get("chance_dupla") and "chance_dupla" in odds_data:
        prompt += f"- Chance Dupla: 1X {odds_data['chance_dupla']['home_draw']}, 12 {odds_data['chance_dupla']['home_away']}, X2 {odds_data['chance_dupla']['draw_away']}\n"
    
    if selected_markets.get("ambos_marcam") and "ambos_marcam" in odds_data:
        prompt += f"- Ambos Marcam: Sim {odds_data['ambos_marcam']['yes']}, Não {odds_data['ambos_marcam']['no']}\n"
    
    if selected_markets.get("escanteios") and "escanteios" in odds_data:
        prompt += f"- Total de Escanteios: Over 9.5 {odds_data['escanteios']['over']}, Under 9.5 {odds_data['escanteios']['under']}\n"
    
    if selected_markets.get("cartoes") and "cartoes" in odds_data:
        prompt += f"- Total de Cartões: Over 3.5 {odds_data['cartoes']['over']}, Under 3.5 {odds_data['cartoes']['under']}\n"
    
    # Adicionar instruções para análise
    prompt += "\nPor favor, analise estes mercados considerando as estatísticas das equipes e identifique oportunidades de valor."
    
    return prompt

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
            except Exception as alt_e:
                logger.error(f"Erro ao salvar dados de usuários no local alternativo: {str(alt_e)}")
            
            return False
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, email: str, password: str, name: str = None) -> bool:
        """
        Register a new user
        
        Args:
            email (str): User email
            password (str): User password
            name (str, optional): User name. Defaults to None.
            
        Returns:
            bool: True if registration was successful, False otherwise
        """
        # Verificar se o email já existe
        if email in self.users:
            logger.warning(f"Tentativa de registro com email já existente: {email}")
            return False
        
        # Hash da senha
        hashed_password = self._hash_password(password)
        
        # Criar novo usuário
        self.users[email] = {
            'password': hashed_password,
            'name': name or email.split('@')[0],  # Usar parte do email como nome se não fornecido
            'created_at': time.time(),
            'tier': 'free',  # Todos os usuários começam no tier gratuito
            'credits_used': 0,
            'credits_remaining': 5,  # 5 créditos gratuitos iniciais
            'credits_total': 5,
            'last_free_credits_reset': time.time(),  # Timestamp da última renovação de créditos gratuitos
            'last_analysis': None,  # Timestamp da última análise
            'analyses_count': 0,  # Contador de análises realizadas
            'verified': False,  # Usuário não verificado inicialmente
            'verification_code': None,  # Código de verificação
            'verification_sent_at': None,  # Timestamp do envio do código de verificação
            'password_reset_code': None,  # Código de redefinição de senha
            'password_reset_sent_at': None,  # Timestamp do envio do código de redefinição de senha
            'last_login': None,  # Timestamp do último login
            'last_credit_purchase': None,  # Timestamp da última compra de créditos
            'purchases': []  # Histórico de compras
        }
        
        # Salvar usuários
        success = self._save_users()
        
        if success:
            logger.info(f"Novo usuário registrado: {email}")
        else:
            logger.error(f"Erro ao salvar dados após registro de novo usuário: {email}")
        
        return success
    
    def get_usage_stats(self, email: str) -> Dict:
        """
        Get usage statistics for a user
        
        Args:
            email (str): User email
            
        Returns:
            Dict: User statistics
        """
        if email not in self.users:
            logger.warning(f"Tentativa de obter estatísticas para usuário inexistente: {email}")
            return {}
        
        user_data = self.users[email]
        
        # Verificar se é hora de renovar créditos gratuitos (a cada 24 horas)
        if user_data.get('tier') == 'free':
            last_reset = user_data.get('last_free_credits_reset', 0)
            now = time.time()
            
            # Se passaram mais de 24 horas desde a última renovação
            if now - last_reset > 24 * 60 * 60:
                # Renovar créditos gratuitos
                user_data['credits_remaining'] = 5
                user_data['credits_total'] = 5
                user_data['last_free_credits_reset'] = now
                user_data['free_credits_reset'] = True  # Flag para indicar que os créditos foram renovados
                
                # Salvar usuários
                self._save_users()
                
                logger.info(f"Créditos gratuitos renovados para {email}")
            else:
                # Calcular tempo restante para próxima renovação
                time_to_next_reset = 24 * 60 * 60 - (now - last_reset)
                hours = int(time_to_next_reset / 3600)
                minutes = int((time_to_next_reset % 3600) / 60)
                
                user_data['next_free_credits_time'] = f"{hours}h {minutes}min"
                user_data['free_credits_reset'] = False
        
        # Verificar se o usuário pago está sem créditos há mais de 7 dias
        if user_data.get('tier') in ['standard', 'pro'] and user_data.get('credits_remaining', 0) == 0:
            last_analysis = user_data.get('last_analysis', 0)
            now = time.time()
            
            # Se passaram mais de 7 dias desde a última análise
            if last_analysis > 0 and now - last_analysis > 7 * 24 * 60 * 60:
                # Calcular dias restantes até o downgrade
                days_since_last_analysis = (now - last_analysis) / (24 * 60 * 60)
                days_until_downgrade = max(0, 7 - int(days_since_last_analysis))
                
                user_data['days_until_downgrade'] = days_until_downgrade
                
                # Se passaram mais de 7 dias, fazer downgrade para free
                if days_until_downgrade == 0:
                    user_data['tier'] = 'free'
                    user_data['credits_remaining'] = 5
                    user_data['credits_total'] = 5
                    user_data['last_free_credits_reset'] = now
                    
                    # Salvar usuários
                    self._save_users()
                    
                    logger.info(f"Usuário {email} rebaixado para tier gratuito por inatividade")
        
        return user_data
    
    def use_credits(self, email: str, num_credits: int) -> bool:
        """
        Use credits for a user
        
        Args:
            email (str): User email
            num_credits (int): Number of credits to use
            
        Returns:
            bool: True if credits were used successfully, False otherwise
        """
        if email not in self.users:
            logger.warning(f"Tentativa de usar créditos para usuário inexistente: {email}")
            return False
        
        user_data = self.users[email]
        
        # Verificar se o usuário tem créditos suficientes
        if user_data.get('credits_remaining', 0) < num_credits:
            logger.warning(f"Usuário {email} não tem créditos suficientes: {user_data.get('credits_remaining', 0)} < {num_credits}")
            return False
        
        # Usar créditos
        user_data['credits_remaining'] -= num_credits
        user_data['credits_used'] += num_credits
        user_data['last_analysis'] = time.time()
        user_data['analyses_count'] = user_data.get('analyses_count', 0) + 1
        
        # Salvar usuários
        success = self._save_users()
        
        if success:
            logger.info(f"Usuário {email} usou {num_credits} créditos. Restantes: {user_data['credits_remaining']}")
        else:
            logger.error(f"Erro ao salvar dados após uso de créditos para {email}")
            # Reverter uso de créditos
            user_data['credits_remaining'] += num_credits
            user_data['credits_used'] -= num_credits
        
        return success
    
    def add_credits(self, email: str, num_credits: int, tier: str = None) -> bool:
        """
        Add credits to a user
        
        Args:
            email (str): User email
            num_credits (int): Number of credits to add
            tier (str, optional): New tier for the user. Defaults to None.
            
        Returns:
            bool: True if credits were added successfully, False otherwise
        """
        if email not in self.users:
            logger.warning(f"Tentativa de adicionar créditos para usuário inexistente: {email}")
            return False
        
        user_data = self.users[email]
        
        # Adicionar créditos
        user_data['credits_remaining'] = user_data.get('credits_remaining', 0) + num_credits
        user_data['credits_total'] = user_data.get('credits_total', 0) + num_credits
        user_data['last_credit_purchase'] = time.time()
        
        # Atualizar tier se fornecido
        if tier and tier in self.tiers:
            user_data['tier'] = tier
        
        # Adicionar compra ao histórico
        purchase = {
            'timestamp': time.time(),
            'credits': num_credits,
            'tier': tier or user_data.get('tier', 'free')
        }
        
        if 'purchases' not in user_data:
            user_data['purchases'] = []
        
        user_data['purchases'].append(purchase)
        
        # Salvar usuários
        success = self._save_users()
        
        if success:
            logger.info(f"Adicionados {num_credits} créditos para {email}. Novo total: {user_data['credits_remaining']}")
        else:
            logger.error(f"Erro ao salvar dados após adição de créditos para {email}")
            # Reverter adição de créditos
            user_data['credits_remaining'] -= num_credits
            user_data['credits_total'] -= num_credits
            user_data['purchases'].pop()  # Remover última compra
        
        return success
    
    def set_verification_code(self, email: str, code: str) -> bool:
        """
        Set verification code for a user
        
        Args:
            email (str): User email
            code (str): Verification code
            
        Returns:
            bool: True if code was set successfully, False otherwise
        """
        if email not in self.users:
            logger.warning(f"Tentativa de definir código de verificação para usuário inexistente: {email}")
            return False
        
        user_data = self.users[email]
        
        # Definir código de verificação
        user_data['verification_code'] = code
        user_data['verification_sent_at'] = time.time()
        
        # Salvar usuários
        success = self._save_users()
        
        if success:
            logger.info(f"Código de verificação definido para {email}")
        else:
            logger.error(f"Erro ao salvar dados após definição de código de verificação para {email}")
        
        return success
    
    def verify_user(self, email: str, code: str) -> bool:
        """
        Verify a user with a verification code
        
        Args:
            email (str): User email
            code (str): Verification code
            
        Returns:
            bool: True if verification was successful, False otherwise
        """
        if email not in self.users:
            logger.warning(f"Tentativa de verificar usuário inexistente: {email}")
            return False
        
        user_data = self.users[email]
        
        # Verificar se o código é válido
        if user_data.get('verification_code') != code:
            logger.warning(f"Código de verificação inválido para {email}")
            return False
        
        # Verificar se o código não expirou (24 horas)
        sent_at = user_data.get('verification_sent_at', 0)
        if time.time() - sent_at > 24 * 60 * 60:
            logger.warning(f"Código de verificação expirado para {email}")
            return False
        
        # Verificar usuário
        user_data['verified'] = True
        user_data['verification_code'] = None
        user_data['verification_sent_at'] = None
        
        # Salvar usuários
        success = self._save_users()
        
        if success:
            logger.info(f"Usuário {email} verificado com sucesso")
        else:
            logger.error(f"Erro ao salvar dados após verificação de {email}")
            # Reverter verificação
            user_data['verified'] = False
        
        return success
    
    def set_password_reset_code(self, email: str, code: str) -> bool:
        """
        Set password reset code for a user
        
        Args:
            email (str): User email
            code (str): Password reset code
            
        Returns:
            bool: True if code was set successfully, False otherwise
        """
        if email not in self.users:
            logger.warning(f"Tentativa de definir código de redefinição de senha para usuário inexistente: {email}")
            return False
        
        user_data = self.users[email]
        
        # Definir código de redefinição de senha
        user_data['password_reset_code'] = code
        user_data['password_reset_sent_at'] = time.time()
        
        # Salvar usuários
        success = self._save_users()
        
        if success:
            logger.info(f"Código de redefinição de senha definido para {email}")
        else:
            logger.error(f"Erro ao salvar dados após definição de código de redefinição de senha para {email}")
        
        return success
    
    def reset_password(self, email: str, code: str, new_password: str) -> bool:
        """
        Reset password for a user
        
        Args:
            email (str): User email
            code (str): Password reset code
            new_password (str): New password
            
        Returns:
            bool: True if password was reset successfully, False otherwise
        """
        if email not in self.users:
            logger.warning(f"Tentativa de redefinir senha para usuário inexistente: {email}")
            return False
        
        user_data = self.users[email]
        
        # Verificar se o código é válido
        if user_data.get('password_reset_code') != code:
            logger.warning(f"Código de redefinição de senha inválido para {email}")
            return False
        
        # Verificar se o código não expirou (1 hora)
        sent_at = user_data.get('password_reset_sent_at', 0)
        if time.time() - sent_at > 60 * 60:
            logger.warning(f"Código de redefinição de senha expirado para {email}")
            return False
        
        # Hash da nova senha
        hashed_password = self._hash_password(new_password)
        
        # Atualizar senha
        user_data['password'] = hashed_password
        user_data['password_reset_code'] = None
        user_data['password_reset_sent_at'] = None
        
        # Salvar usuários
        success = self._save_users()
        
        if success:
            logger.info(f"Senha redefinida com sucesso para {email}")
        else:
            logger.error(f"Erro ao salvar dados após redefinição de senha para {email}")
        
        return success
    
    def update_last_login(self, email: str) -> bool:
        """
        Update last login timestamp for a user
        
        Args:
            email (str): User email
            
        Returns:
            bool: True if timestamp was updated successfully, False otherwise
        """
        if email not in self.users:
            logger.warning(f"Tentativa de atualizar último login para usuário inexistente: {email}")
            return False
        
        user_data = self.users[email]
        
        # Atualizar timestamp de último login
        user_data['last_login'] = time.time()
        
        # Salvar usuários
        success = self._save_users()
        
        if success:
            logger.info(f"Timestamp de último login atualizado para {email}")
        else:
            logger.error(f"Erro ao salvar dados após atualização de timestamp de último login para {email}")
        
        return success
    
    def get_user_tier(self, email: str) -> Optional[UserTier]:
        """
        Get user tier
        
        Args:
            email (str): User email
            
        Returns:
            Optional[UserTier]: User tier or None if user does not exist
        """
        if email not in self.users:
            logger.warning(f"Tentativa de obter tier para usuário inexistente: {email}")
            return None
        
        user_data = self.users[email]
        tier_name = user_data.get('tier', 'free')
        
        return self.tiers.get(tier_name)
    
    def get_user_name(self, email: str) -> Optional[str]:
        """
        Get user name
        
        Args:
            email (str): User email
            
        Returns:
            Optional[str]: User name or None if user does not exist
        """
        if email not in self.users:
            logger.warning(f"Tentativa de obter nome para usuário inexistente: {email}")
            return None
        
        user_data = self.users[email]
        return user_data.get('name', email.split('@')[0])
    
    def update_user_name(self, email: str, name: str) -> bool:
        """
        Update user name
        
        Args:
            email (str): User email
            name (str): New name
            
        Returns:
            bool: True if name was updated successfully, False otherwise
        """
        if email not in self.users:
            logger.warning(f"Tentativa de atualizar nome para usuário inexistente: {email}")
            return False
        
        user_data = self.users[email]
        
        # Atualizar nome
        user_data['name'] = name
        
        # Salvar usuários
        success = self._save_users()
        
        if success:
            logger.info(f"Nome atualizado para {email}: {name}")
        else:
            logger.error(f"Erro ao salvar dados após atualização de nome para {email}")
        
        return success
    
    def delete_user(self, email: str) -> bool:
        """
        Delete a user
        
        Args:
            email (str): User email
            
        Returns:
            bool: True if user was deleted successfully, False otherwise
        """
        if email not in self.users:
            logger.warning(f"Tentativa de excluir usuário inexistente: {email}")
            return False
        
        # Excluir usuário
        del self.users[email]
        
        # Salvar usuários
        success = self._save_users()
        
        if success:
            logger.info(f"Usuário {email} excluído com sucesso")
        else:
            logger.error(f"Erro ao salvar dados após exclusão de {email}")
        
        return success
    
    def get_all_users(self) -> Dict:
        """
        Get all users
        
        Returns:
            Dict: All users
        """
        return self.users
    
    def get_user_count(self) -> int:
        """
        Get user count
        
        Returns:
            int: Number of users
        """
        return len(self.users)
    
    def get_active_users(self, days: int = 7) -> Dict:
        """
        Get active users
        
        Args:
            days (int, optional): Number of days to consider. Defaults to 7.
            
        Returns:
            Dict: Active users
        """
        active_users = {}
        now = time.time()
        
        for email, user_data in self.users.items():
            last_login = user_data.get('last_login', 0)
            
            # Se o usuário fez login nos últimos X dias
            if now - last_login < days * 24 * 60 * 60:
                active_users[email] = user_data
        
        return active_users
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user by email
        
        Args:
            email (str): User email
            
        Returns:
            Optional[Dict]: User data or None if user does not exist
        """
        return self.users.get(email)
    
    def user_exists(self, email: str) -> bool:
        """
        Check if user exists
        
        Args:
            email (str): User email
            
        Returns:
            bool: True if user exists, False otherwise
        """
        return email in self.users
    
    def is_user_verified(self, email: str) -> bool:
        """
        Check if user is verified
        
        Args:
            email (str): User email
            
        Returns:
            bool: True if user is verified, False otherwise
        """
        if email not in self.users:
            return False
        
        user_data = self.users[email]
        return user_data.get('verified', False)
    
    def has_enough_credits(self, email: str, num_credits: int) -> bool:
        """
        Check if user has enough credits
        
        Args:
            email (str): User email
            num_credits (int): Number of credits to check
            
        Returns:
            bool: True if user has enough credits, False otherwise
        """
        if email not in self.users:
            return False
        
        user_data = self.users[email]
        return user_data.get('credits_remaining', 0) >= num_credits
    
    def get_user_credits(self, email: str) -> int:
        """
        Get user credits
        
        Args:
            email (str): User email
            
        Returns:
            int: Number of credits
        """
        if email not in self.users:
            return 0
        
        user_data = self.users[email]
        return user_data.get('credits_remaining', 0)
    
    def get_user_total_credits(self, email: str) -> int:
        """
        Get user total credits
        
        Args:
            email (str): User email
            
        Returns:
            int: Total number of credits
        """
        if email not in self.users:
            return 0
        
        user_data = self.users[email]
        return user_data.get('credits_total', 0)
    
    def get_user_used_credits(self, email: str) -> int:
        """
        Get user used credits
        
        Args:
            email (str): User email
            
        Returns:
            int: Number of used credits
        """
        if email not in self.users:
            return 0
        
        user_data = self.users[email]
        return user_data.get('credits_used', 0)
    
    def get_user_analyses_count(self, email: str) -> int:
        """
        Get user analyses count
        
        Args:
            email (str): User email
            
        Returns:
            int: Number of analyses
        """
        if email not in self.users:
            return 0
        
        user_data = self.users[email]
        return user_data.get('analyses_count', 0)
    
    def get_user_last_analysis(self, email: str) -> Optional[float]:
        """
        Get user last analysis timestamp
        
        Args:
            email (str): User email
            
        Returns:
            Optional[float]: Last analysis timestamp or None if user does not exist
        """
        if email not in self.users:
            return None
        
        user_data = self.users[email]
        return user_data.get('last_analysis')
    
    def get_user_last_login(self, email: str) -> Optional[float]:
        """
        Get user last login timestamp
        
        Args:
            email (str): User email
            
        Returns:
            Optional[float]: Last login timestamp or None if user does not exist
        """
        if email not in self.users:
            return None
        
        user_data = self.users[email]
        return user_data.get('last_login')
    
    def get_user_last_credit_purchase(self, email: str) -> Optional[float]:
        """
        Get user last credit purchase timestamp
        
        Args:
            email (str): User email
            
        Returns:
            Optional[float]: Last credit purchase timestamp or None if user does not exist
        """
        if email not in self.users:
            return None
        
        user_data = self.users[email]
        return user_data.get('last_credit_purchase')
    
    def get_user_purchases(self, email: str) -> List[Dict]:
        """
        Get user purchases
        
        Args:
            email (str): User email
            
        Returns:
            List[Dict]: List of purchases
        """
        if email not in self.users:
            return []
        
        user_data = self.users[email]
        return user_data.get('purchases', [])
    
    def get_user_creation_date(self, email: str) -> Optional[float]:
        """
        Get user creation date
        
        Args:
            email (str): User email
            
        Returns:
            Optional[float]: Creation date timestamp or None if user does not exist
        """
        if email not in self.users:
            return None
        
        user_data = self.users[email]
        return user_data.get('created_at')
    
    def get_user_age_days(self, email: str) -> Optional[int]:
        """
        Get user age in days
        
        Args:
            email (str): User email
            
        Returns:
            Optional[int]: User age in days or None if user does not exist
        """
        if email not in self.users:
            return None
        
        user_data = self.users[email]
        created_at = user_data.get('created_at')
        
        if created_at is None:
            return None
        
        now = time.time()
        return int((now - created_at) / (24 * 60 * 60))
    
    def get_user_tier_name(self, email: str) -> Optional[str]:
        """
        Get user tier name
        
        Args:
            email (str): User email
            
        Returns:
            Optional[str]: Tier name or None if user does not exist
        """
        if email not in self.users:
            return None
        
        user_data = self.users[email]
        return user_data.get('tier', 'free')
    
    def get_user_tier_limit(self, email: str) -> Optional[int]:
        """
        Get user tier market limit
        
        Args:
            email (str): User email
            
        Returns:
            Optional[int]: Market limit or None if user does not exist
        """
        if email not in self.users:
            return None
        
        user_data = self.users[email]
        tier_name = user_data.get('tier', 'free')
        tier = self.tiers.get(tier_name)
        
        if tier is None:
            return None
        
        return tier.market_limit
    
    def get_user_tier_total_credits(self, email: str) -> Optional[int]:
        """
        Get user tier total credits
        
        Args:
            email (str): User email
            
        Returns:
            Optional[int]: Total credits or None if user does not exist
        """
        if email not in self.users:
            return None
        
        user_data = self.users[email]
        tier_name = user_data.get('tier', 'free')
        tier = self.tiers.get(tier_name)
        
        if tier is None:
            return None
        
        return tier.total_credits
    
    def is_user_free_tier(self, email: str) -> bool:
        """
        Check if user is on free tier
        
        Args:
            email (str): User email
            
        Returns:
            bool: True if user is on free tier, False otherwise
        """
        if email not in self.users:
            return False
        
        user_data = self.users[email]
        return user_data.get('tier', 'free') == 'free'
    
    def is_user_paid_tier(self, email: str) -> bool:
        """
        Check if user is on paid tier
        
        Args:
            email (str): User email
            
        Returns:
            bool: True if user is on paid tier, False otherwise
        """
        if email not in self.users:
            return False
        
        user_data = self.users[email]
        return user_data.get('tier', 'free') != 'free'
    
    def get_free_tier_reset_time(self, email: str) -> Optional[str]:
        """
        Get free tier reset time
        
        Args:
            email (str): User email
            
        Returns:
            Optional[str]: Reset time string or None if user does not exist or is not on free tier
        """
        if email not in self.users:
            return None
        
        user_data = self.users[email]
        
        if user_data.get('tier', 'free') != 'free':
            return None
        
        return user_data.get('next_free_credits_time')
    
    def was_free_tier_reset(self, email: str) -> bool:
        """
        Check if free tier was reset
        
        Args:
            email (str): User email
            
        Returns:
            bool: True if free tier was reset, False otherwise
        """
        if email not in self.users:
            return False
        
        user_data = self.users[email]
        
        if user_data.get('tier', 'free') != 'free':
            return False
        
        return user_data.get('free_credits_reset', False)
    
    def get_days_until_downgrade(self, email: str) -> Optional[int]:
        """
        Get days until downgrade
        
        Args:
            email (str): User email
            
        Returns:
            Optional[int]: Days until downgrade or None if user does not exist or is not on paid tier
        """
        if email not in self.users:
            return None
        
        user_data = self.users[email]
        
        if user_data.get('tier', 'free') == 'free':
            return None
        
        return user_data.get('days_until_downgrade')
    
    def is_user_about_to_downgrade(self, email: str) -> bool:
        """
        Check if user is about to downgrade
        
        Args:
            email (str): User email
            
        Returns:
            bool: True if user is about to downgrade, False otherwise
        """
        if email not in self.users:
            return False
        
        user_data = self.users[email]
        
        if user_data.get('tier', 'free') == 'free':
            return False
        
        days_until_downgrade = user_data.get('days_until_downgrade')
        
        if days_until_downgrade is None:
            return False
        
        return days_until_downgrade <= 3  # Considerar "prestes a ser rebaixado" se faltarem 3 dias ou menos

def parse_team_stats(html_content):
    """
    Extrai estatísticas de times a partir de conteúdo HTML.
    
    Args:
        html_content (str): Conteúdo HTML com tabela de estatísticas
        
    Returns:
        pandas.DataFrame: DataFrame com estatísticas ou None em caso de erro
    """
    try:
        import pandas as pd
        from bs4 import BeautifulSoup
        import re
        
        # 1. Verificar se temos conteúdo
        if not html_content or len(html_content) < 100:
            logger.error("Conteúdo HTML vazio ou muito pequeno")
            return None
        
        # 2. Tentar extrair tabelas com pandas
        df = None
        try:
            # Tentar extrair todas as tabelas
            tables = pd.read_html(html_content)
            
            if tables and len(tables) > 0:
                # Usar a primeira tabela que parece ter estatísticas de times
                for table in tables:
                    # Verificar se a tabela tem pelo menos 3 colunas e 5 linhas
                    if table.shape[0] >= 5 and table.shape[1] >= 3:
                        df = table
                        logger.info(f"Tabela extraída com pandas: {df.shape}")
                        break
        except Exception as e:
            logger.warning(f"Erro ao extrair tabelas com pandas: {str(e)}")
            # Continuar com BeautifulSoup
        
        # 3. Se pandas falhou, tentar com BeautifulSoup
        if df is None:
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Procurar tabelas
                tables = soup.find_all('table')
                
                if not tables:
                    logger.warning("Nenhuma tabela encontrada no HTML")
                    return None
                
                # Usar a primeira tabela que parece ter estatísticas
                target_table = None
                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) >= 5:  # Pelo menos 5 linhas (cabeçalho + 4 times)
                        target_table = table
                        break
                
                if not target_table:
                    logger.warning("Nenhuma tabela adequada encontrada")
                    return None
                
                # Extrair cabeçalho
                headers = []
                header_row = target_table.find('thead')
                if header_row:
                    header_cells = header_row.find_all(['th', 'td'])
                    headers = [cell.get_text(strip=True) for cell in header_cells]
                else:
                    # Tentar primeira linha como cabeçalho
                    first_row = target_table.find('tr')
                    if first_row:
                        header_cells = first_row.find_all(['th', 'td'])
                        headers = [cell.get_text(strip=True) for cell in header_cells]
                
                if not headers:
                    logger.warning("Não foi possível extrair cabeçalho da tabela")
                    # Criar cabeçalho genérico
                    first_row = target_table.find('tr')
                    if first_row:
                        num_cols = len(first_row.find_all(['th', 'td']))
                        headers = ['Column' + str(i) for i in range(num_cols)]
                    else:
                        headers = ['Column0', 'Column1', 'Column2']
                
                # Extrair linhas de dados
                rows = []
                data_rows = target_table.find_all('tr')
                
                # Pular primeira linha se for cabeçalho
                start_idx = 1 if header_row or (len(data_rows) > 0 and data_rows[0].find('th')) else 0
                
                for row in data_rows[start_idx:]:
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        row_data = [cell.get_text(strip=True) for cell in cells]
                        rows.append(row_data)
                
                if not rows:
                    logger.warning("Não foi possível extrair linhas de dados da tabela")
                    return None
                
                # Criar DataFrame
                df = pd.DataFrame(rows, columns=headers[:len(rows[0])])
                logger.info(f"Tabela extraída com BeautifulSoup: {df.shape}")
                
            except Exception as e:
                logger.error(f"Erro ao extrair tabela com BeautifulSoup: {str(e)}")
                return None
        
        # 4. Extração manual como último recurso
        if df is None:
            try:
                # Procurar padrões de tabela no HTML
                # Exemplo: <tr>...</tr> com <td>...</td> ou <th>...</th>
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extrair todas as linhas
                tr_tags = soup.find_all('tr')
                
                if not tr_tags:
                    logger.error("Nenhuma linha de tabela encontrada")
                    return None
                
                # Extrair dados de cada linha
                rows = []
                for tr in tr_tags:
                    cells = tr.find_all(['td', 'th'])
                    if cells:
                        row_data = [cell.get_text(strip=True) for cell in cells]
                        rows.append(row_data)
                
                if not rows:
                    logger.error("Nenhuma célula de dados encontrada")
                    return None
                
                # Determinar número de colunas (usar o máximo)
                num_cols = max(len(row) for row in rows)
                
                # Criar nomes de colunas genéricos
                column_names = ['Column' + str(i) for i in range(num_cols)]
                
                # Ajustar linhas para ter o mesmo número de colunas
                adjusted_rows = []
                for row in rows:
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
