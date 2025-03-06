# utils/api_football.py - Integração com a API-Football
import requests
import os
import json
import time
import logging
import streamlit as st
from datetime import datetime

# Configuração de logging
logger = logging.getLogger("valueHunter.api_football")

# Configuração da API
BASE_URL = "https://v3.football.api-sports.io"
API_KEY = "5682997853dece33394e79e4746d5f7e"  # Atenção: em produção, use secrets

# Obter a temporada atual (atual ano ou ano anterior se estamos no início do ano)
def get_current_season():
    current_year = datetime.now().year
    current_month = datetime.now().month
    # Se estamos nos primeiros meses do ano, a temporada anterior ainda pode estar ativa
    if current_month < 7:  # antes de julho, consideramos a temporada do ano anterior
        return current_year - 1
    else:
        return current_year

# Temporada atual por padrão
CURRENT_SEASON = get_current_season()

# Mapeamento de IDs das principais ligas
LEAGUE_IDS = {
    "Premier League": 39,
    "La Liga": 140,
    "Serie A": 135,
    "Bundesliga": 78,
    "Ligue 1": 61,
    "Champions League": 2
}

# Mapeamento de temporadas específicas para cada liga (atualizar conforme necessário)
LEAGUE_SEASONS = {
    # A maioria das ligas europeias já começou a temporada 2024-2025
    "Premier League": 2024,
    "La Liga": 2024,
    "Serie A": 2024,
    "Bundesliga": 2024,
    "Ligue 1": 2024,
    # Champions League tem uma estrutura de temporada diferente
    "Champions League": 2024
}

# Cache para minimizar requisições
CACHE_DURATION = 24 * 60 * 60  # 24 horas em segundos
CACHE_DIR = os.path.join("data", "api_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_headers():
    """Obter headers para as requisições à API"""
    return {
        "x-apisports-key": API_KEY
    }

def get_cache_file(endpoint, params=None):
    """Gerar nome de arquivo para cache baseado no endpoint e parâmetros"""
    cache_key = endpoint.replace("/", "_")
    if params:
        param_str = "_".join([f"{k}_{v}" for k, v in sorted(params.items())])
        cache_key += "_" + param_str
    
    # Limitar o tamanho e garantir que o nome do arquivo seja válido
    cache_key = "".join(c for c in cache_key if c.isalnum() or c in "_-")[:100]
    return os.path.join(CACHE_DIR, f"{cache_key}.json")

def save_to_cache(data, endpoint, params=None):
    """Salvar dados no cache"""
    try:
        cache_file = get_cache_file(endpoint, params)
        cache_data = {
            "timestamp": time.time(),
            "data": data
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)
        logger.info(f"Dados salvos no cache: {cache_file}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar cache: {str(e)}")
        return False

def get_from_cache(endpoint, params=None, max_age=CACHE_DURATION):
    """Obter dados do cache se existirem e forem recentes"""
    try:
        cache_file = get_cache_file(endpoint, params)
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
            
            # Verificar se os dados estão atualizados
            if time.time() - cache_data["timestamp"] < max_age:
                logger.info(f"Dados obtidos do cache: {cache_file}")
                return cache_data["data"]
        
        return None
    except Exception as e:
        logger.error(f"Erro ao ler cache: {str(e)}")
        return None

def api_request(endpoint, params=None, use_cache=True, cache_duration=CACHE_DURATION):
    """
    Fazer requisição à API com tratamento de erros e cache
    
    Args:
        endpoint (str): Endpoint da API (ex: "/leagues")
        params (dict): Parâmetros da requisição
        use_cache (bool): Se deve usar o cache
        cache_duration (int): Duração do cache em segundos
        
    Returns:
        dict: Dados da resposta ou None se ocorrer erro
    """
    # Verificar cache se estiver habilitado
    if use_cache:
        cached_data = get_from_cache(endpoint, params, cache_duration)
        if cached_data:
            return cached_data
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, headers=get_headers(), params=params)
        
        # Log da requisição para diagnóstico
        logger.info(f"API Request: {url} - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar se a API retornou erro
            if "errors" in data and data["errors"]:
                errors = data["errors"]
                logger.error(f"Erro da API: {errors}")
                return None
                
            # Salvar no cache se estiver habilitado
            if use_cache:
                save_to_cache(data, endpoint, params)
                
            return data
            
        elif response.status_code == 429:
            # Limite de requisições atingido
            logger.warning("Limite de requisições à API atingido")
            return {"error": "rate_limit", "message": "Limite de requisições atingido"}
            
        else:
            logger.error(f"Erro na requisição: {response.status_code}")
            logger.error(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao acessar a API: {str(e)}")
        return None

def get_league_season(league_name):
    """
    Obter a temporada definida para uma liga específica
    
    Args:
        league_name (str): Nome da liga
        
    Returns:
        int: Temporada (ano) definida para a liga
    """
    # Simplesmente retornar a temporada definida ou a atual
    if league_name in LEAGUE_SEASONS:
        return LEAGUE_SEASONS[league_name]
    
    # Retornar a temporada atual como fallback
    return CURRENT_SEASON
def get_available_leagues():
    """
    Obter lista de ligas disponíveis com suas temporadas atuais
    
    Returns:
        dict: Dicionário com nomes das ligas como chaves e IDs como valores
    """
    try:
        # Atualizar as temporadas para cada liga
        for league_name in LEAGUE_IDS.keys():
            if league_name not in LEAGUE_SEASONS:
                LEAGUE_SEASONS[league_name] = get_league_season(league_name)
        
        # Verificar disponibilidade das ligas nas temporadas atualizadas
        available_leagues = {}
        
        for league_name, league_id in LEAGUE_IDS.items():
            season = LEAGUE_SEASONS.get(league_name, CURRENT_SEASON)
            params = {"league": league_id, "season": season}
            
            # Verificar se há times para esta liga e temporada
            teams_data = api_request("/teams", params, use_cache=True)
            
            if teams_data and "response" in teams_data and len(teams_data["response"]) > 0:
                available_leagues[league_name] = league_id
                logger.info(f"Liga {league_name} disponível com {len(teams_data['response'])} times (temporada {season})")
        
        if available_leagues:
            return available_leagues
    except Exception as e:
        logger.error(f"Erro ao verificar ligas disponíveis: {str(e)}")
    
    # Se não conseguir validar quais ligas estão disponíveis, retornar todas
    return LEAGUE_IDS

def get_teams_by_league(league_name):
    """
    Obter lista de times para uma liga específica
    
    Args:
        league_name (str): Nome da liga
        
    Returns:
        list: Lista de dicionários com informações dos times
    """
    # Obter o ID da liga
    league_id = LEAGUE_IDS.get(league_name)
    if not league_id:
        logger.error(f"Liga não encontrada: {league_name}")
        return []
    
    # Obter a temporada adequada para esta liga
    season = LEAGUE_SEASONS.get(league_name, CURRENT_SEASON)
    
    # Parâmetros da requisição
    params = {
        "league": league_id,
        "season": season
    }
    
    # Log da temporada sendo usada
    logger.info(f"Buscando times para {league_name} (temporada {season})")
    
    # Fazer requisição à API
    data = api_request("/teams", params)
    
    if data and "response" in data:
        # Formatar a resposta para retornar apenas o necessário
        teams = []
        for team_item in data["response"]:
            team = team_item["team"]
            teams.append({
                "id": team["id"],
                "name": team["name"],
                "logo": team.get("logo", "")
            })
        
        return teams

# Se não encontrar dados para a temporada atual, retorne lista vazia
logger.warning(f"Nenhum dado encontrado para {league_name} na temporada {season}")
return []

def get_team_names_by_league(league_name):
    """
    Obter apenas os nomes dos times de uma liga (formato simplificado)
    
    Args:
        league_name (str): Nome da liga
        
    Returns:
        list: Lista de nomes dos times
    """
    teams = get_teams_by_league(league_name)
    return [team["name"] for team in teams]

def get_team_statistics(team_id, league_name):
    """
    Obter estatísticas detalhadas de um time
    
    Args:
        team_id (int): ID do time
        league_name (str): Nome da liga
        
    Returns:
        dict: Estatísticas do time ou None se ocorrer erro
    """
    # Obter o ID da liga
    league_id = LEAGUE_IDS.get(league_name)
    if not league_id:
        logger.error(f"Liga não encontrada: {league_name}")
        return None
    
    # Obter a temporada adequada para esta liga
    season = LEAGUE_SEASONS.get(league_name, CURRENT_SEASON)
    
    # Parâmetros da requisição
    params = {
        "team": team_id,
        "league": league_id,
        "season": season
    }
    
    # Fazer requisição à API
    data = api_request("/teams/statistics", params)
    
    if data and "response" in data:
        return data["response"]

def get_team_id_by_name(team_name, league_name):
    """
    Encontrar o ID de um time pelo nome
    
    Args:
        team_name (str): Nome do time
        league_name (str): Nome da liga
        
    Returns:
        int: ID do time ou None se não encontrado
    """
    # Buscar todos os times da liga
    teams = get_teams_by_league(league_name)
    
    # Log para diagnóstico
    logger.info(f"Buscando ID para '{team_name}' em {league_name} ({len(teams)} times disponíveis)")
    
    # Procurar pelo nome exato primeiro
    for team in teams:
        if team["name"].lower() == team_name.lower():
            logger.info(f"Time encontrado com correspondência exata: {team['name']} (ID: {team['id']})")
            return team["id"]
    
    # Se não encontrar pelo nome exato, tentar nome parcial
    for team in teams:
        if team_name.lower() in team["name"].lower() or team["name"].lower() in team_name.lower():
            logger.info(f"Time encontrado com correspondência parcial: {team['name']} (ID: {team['id']})")
            return team["id"]
    
    logger.warning(f"Não foi possível encontrar o time '{team_name}' na liga {league_name}")
    return None

def get_fixture_statistics(team1_name, team2_name, league_name):
    """
    Obter estatísticas para uma partida entre dois times
    
    Args:
        team1_name (str): Nome do primeiro time
        team2_name (str): Nome do segundo time
        league_name (str): Nome da liga
        
    Returns:
        dict: Estatísticas de ambos os times formatadas para análise
    """
    # Obter IDs dos times
    team1_id = get_team_id_by_name(team1_name, league_name)
    team2_id = get_team_id_by_name(team2_name, league_name)
    
    if not team1_id or not team2_id:
        teams_not_found = []
        if not team1_id:
            teams_not_found.append(team1_name)
        if not team2_id:
            teams_not_found.append(team2_name)
        
        logger.error(f"Times não encontrados: {', '.join(teams_not_found)}")
        return None
    
    # Obter estatísticas de cada time
    team1_stats = get_team_statistics(team1_id, league_name)
    team2_stats = get_team_statistics(team2_id, league_name)
    
    if not team1_stats or not team2_stats:
        missing_stats = []
        if not team1_stats:
            missing_stats.append(team1_name)
        if not team2_stats:
            missing_stats.append(team2_name)
            
        logger.error(f"Estatísticas não disponíveis para: {', '.join(missing_stats)}")
        return None
    
    # Formatar estatísticas para análise
    season = LEAGUE_SEASONS.get(league_name, CURRENT_SEASON)
    return {
        "home_team": {
            "name": team1_name,
            "id": team1_id,
            "stats": team1_stats
        },
        "away_team": {
            "name": team2_name,
            "id": team2_id,
            "stats": team2_stats
        },
        "league": {
            "name": league_name,
            "id": LEAGUE_IDS.get(league_name)
        },
        "season": season
    }

# Funções para converter dados da API para o formato esperado pelo ValueHunter
def convert_api_stats_to_df_format(fixture_stats):
    """
    Converter estatísticas da API para o formato de DataFrame esperado pelas funções existentes
    
    Args:
        fixture_stats (dict): Estatísticas obtidas da API
        
    Returns:
        pandas.DataFrame: DataFrame com estatísticas no formato esperado
    """
    import pandas as pd
    
    try:
        if not fixture_stats:
            return None
        
        home_team = fixture_stats["home_team"]
        away_team = fixture_stats["away_team"]
        
        # Verificar se temos dados completos para ambos os times
        if not home_team.get("stats") or not away_team.get("stats"):
            logger.error("Dados de estatísticas incompletos")
            return None
        
        # Extrair estatísticas com verificação de existência para evitar erros
        def safe_get(obj, *keys, default=None):
            current = obj
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            return current
        
        # Criando as linhas para o DataFrame
        home_row = {
            "Squad": home_team["name"],
            "MP": safe_get(home_team, "stats", "fixtures", "played", "total", default=0),
            "W": safe_get(home_team, "stats", "fixtures", "wins", "total", default=0),
            "D": safe_get(home_team, "stats", "fixtures", "draws", "total", default=0),
            "L": safe_get(home_team, "stats", "fixtures", "loses", "total", default=0),
            "Pts": None,  # Calcular abaixo
            "Gls": safe_get(home_team, "stats", "goals", "for", "total", "total", default=0),
            "GA": safe_get(home_team, "stats", "goals", "against", "total", "total", default=0),
            "xG": safe_get(home_team, "stats", "goals", "for", "expected", "total", default=None),
            "xGA": safe_get(home_team, "stats", "goals", "against", "expected", "total", default=None),
            "Poss": safe_get(home_team, "stats", "possession", default=50),
            "CS": safe_get(home_team, "stats", "clean_sheet", "total", default=0)
        }
        
        away_row = {
            "Squad": away_team["name"],
            "MP": safe_get(away_team, "stats", "fixtures", "played", "total", default=0),
            "W": safe_get(away_team, "stats", "fixtures", "wins", "total", default=0),
            "D": safe_get(away_team, "stats", "fixtures", "draws", "total", default=0),
            "L": safe_get(away_team, "stats", "fixtures", "loses", "total", default=0),
            "Pts": None,  # Calcular abaixo
            "Gls": safe_get(away_team, "stats", "goals", "for", "total", "total", default=0),
            "GA": safe_get(away_team, "stats", "goals", "against", "total", "total", default=0),
            "xG": safe_get(away_team, "stats", "goals", "for", "expected", "total", default=None),
            "xGA": safe_get(away_team, "stats", "goals", "against", "expected", "total", default=None),
            "Poss": safe_get(away_team, "stats", "possession", default=50),
            "CS": safe_get(away_team, "stats", "clean_sheet", "total", default=0)
        }
        
        # Calcular pontos
        home_row["Pts"] = (home_row["W"] * 3) + home_row["D"]
        away_row["Pts"] = (away_row["W"] * 3) + away_row["D"]

        # Backup para dados de xG se não estiverem disponíveis
        if home_row["xG"] is None:
            home_row["xG"] = round(home_row["Gls"] * 0.9, 1)  # Estimativa baseada em gols
        if home_row["xGA"] is None:
            home_row["xGA"] = round(home_row["GA"] * 0.9, 1)  # Estimativa baseada em gols sofridos
        
        if away_row["xG"] is None:
            away_row["xG"] = round(away_row["Gls"] * 0.9, 1)  # Estimativa baseada em gols
        if away_row["xGA"] is None:
            away_row["xGA"] = round(away_row["GA"] * 0.9, 1)  # Estimativa baseada em gols sofridos
        
        # Criar DataFrame
        df = pd.DataFrame([home_row, away_row])
        
        return df
    
    except Exception as e:
        logger.error(f"Erro ao converter estatísticas: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
