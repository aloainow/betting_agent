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

# Mapeamento de IDs das principais ligas
LEAGUE_IDS = {
    "Premier League": 39,
    "La Liga": 140,
    "Serie A": 135,
    "Bundesliga": 78,
    "Ligue 1": 61,
    "Champions League": 2
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

def get_available_leagues(season=2023):
    """
    Obter lista de ligas disponíveis
    
    Returns:
        dict: Dicionário com nomes das ligas como chaves e IDs como valores
    """
    # Verificar se temos a lista predefinida de ligas
    if LEAGUE_IDS:
        # Verificar disponibilidade das ligas na temporada atual
        params = {"season": season}
        data = api_request("/leagues", params)
        
        if data and "response" in data:
            # Filtrar apenas as ligas que conhecemos e que estão disponíveis
            available_leagues = {}
            
            for league_item in data["response"]:
                league = league_item["league"]
                league_id = league["id"]
                
                # Verificar se esta liga está em nosso mapeamento
                for name, id_value in LEAGUE_IDS.items():
                    if id_value == league_id:
                        available_leagues[name] = league_id
                        break
            
            if available_leagues:
                return available_leagues
    
    # Se não conseguir dados da API ou se não encontrar ligas, usar o mapeamento padrão
    return LEAGUE_IDS

def get_teams_by_league(league_name, season=2023):
    """
    Obter lista de times para uma liga específica
    
    Args:
        league_name (str): Nome da liga
        season (int): Temporada (ano)
        
    Returns:
        list: Lista de dicionários com informações dos times
    """
    # Obter o ID da liga
    league_id = LEAGUE_IDS.get(league_name)
    if not league_id:
        logger.error(f"Liga não encontrada: {league_name}")
        return []
    
    # Parâmetros da requisição
    params = {
        "league": league_id,
        "season": season
    }
    
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
    
    return []

def get_team_names_by_league(league_name, season=2023):
    """
    Obter apenas os nomes dos times de uma liga (formato simplificado)
    
    Args:
        league_name (str): Nome da liga
        season (int): Temporada (ano)
        
    Returns:
        list: Lista de nomes dos times
    """
    teams = get_teams_by_league(league_name, season)
    return [team["name"] for team in teams]

def get_team_statistics(team_id, league_name, season=2023):
    """
    Obter estatísticas detalhadas de um time
    
    Args:
        team_id (int): ID do time
        league_name (str): Nome da liga
        season (int): Temporada (ano)
        
    Returns:
        dict: Estatísticas do time ou None se ocorrer erro
    """
    # Obter o ID da liga
    league_id = LEAGUE_IDS.get(league_name)
    if not league_id:
        logger.error(f"Liga não encontrada: {league_name}")
        return None
    
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
    
    return None

def get_team_id_by_name(team_name, league_name, season=2023):
    """
    Encontrar o ID de um time pelo nome
    
    Args:
        team_name (str): Nome do time
        league_name (str): Nome da liga
        season (int): Temporada (ano)
        
    Returns:
        int: ID do time ou None se não encontrado
    """
    # Buscar todos os times da liga
    teams = get_teams_by_league(league_name, season)
    
    # Procurar pelo nome exato primeiro
    for team in teams:
        if team["name"].lower() == team_name.lower():
            return team["id"]
    
    # Se não encontrar pelo nome exato, tentar nome parcial
    for team in teams:
        if team_name.lower() in team["name"].lower() or team["name"].lower() in team_name.lower():
            return team["id"]
    
    return None

def get_fixture_statistics(team1_name, team2_name, league_name, season=2023):
    """
    Obter estatísticas para uma partida entre dois times
    
    Args:
        team1_name (str): Nome do primeiro time
        team2_name (str): Nome do segundo time
        league_name (str): Nome da liga
        season (int): Temporada (ano)
        
    Returns:
        dict: Estatísticas de ambos os times formatadas para análise
    """
    # Obter IDs dos times
    team1_id = get_team_id_by_name(team1_name, league_name, season)
    team2_id = get_team_id_by_name(team2_name, league_name, season)
    
    if not team1_id or not team2_id:
        teams_not_found = []
        if not team1_id:
            teams_not_found.append(team1_name)
        if not team2_id:
            teams_not_found.append(team2_name)
        
        logger.error(f"Times não encontrados: {', '.join(teams_not_found)}")
        return None
    
    # Obter estatísticas de cada time
    team1_stats = get_team_statistics(team1_id, league_name, season)
    team2_stats = get_team_statistics(team2_id, league_name, season)
    
    if not team1_stats or not team2_stats:
        return None
    
    # Formatar estatísticas para análise
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
        
        # Criando as linhas para o DataFrame
        home_row = {
            "Squad": home_team["name"],
            "MP": home_team["stats"]["fixtures"]["played"]["total"],
            "W": home_team["stats"]["fixtures"]["wins"]["total"],
            "D": home_team["stats"]["fixtures"]["draws"]["total"],
            "L": home_team["stats"]["fixtures"]["loses"]["total"],
            "Pts": None,  # Calcular abaixo
            "Gls": home_team["stats"]["goals"]["for"]["total"]["total"],
            "GA": home_team["stats"]["goals"]["against"]["total"]["total"],
            "xG": home_team["stats"].get("goals", {}).get("for", {}).get("expected", {}).get("total", None),
            "xGA": home_team["stats"].get("goals", {}).get("against", {}).get("expected", {}).get("total", None),
            "Poss": home_team["stats"]["lineups"][0]["formation"].get("played", 0) if home_team["stats"]["lineups"] else None,
            "CS": home_team["stats"]["clean_sheet"]["total"]
        }
        
        away_row = {
            "Squad": away_team["name"],
            "MP": away_team["stats"]["fixtures"]["played"]["total"],
            "W": away_team["stats"]["fixtures"]["wins"]["total"],
            "D": away_team["stats"]["fixtures"]["draws"]["total"],
            "L": away_team["stats"]["fixtures"]["loses"]["total"],
            "Pts": None,  # Calcular abaixo
            "Gls": away_team["stats"]["goals"]["for"]["total"]["total"],
            "GA": away_team["stats"]["goals"]["against"]["total"]["total"],
            "xG": away_team["stats"].get("goals", {}).get("for", {}).get("expected", {}).get("total", None),
            "xGA": away_team["stats"].get("goals", {}).get("against", {}).get("expected", {}).get("total", None),
            "Poss": away_team["stats"]["lineups"][0]["formation"].get("played", 0) if away_team["stats"]["lineups"] else None,
            "CS": away_team["stats"]["clean_sheet"]["total"]
        }
        
        # Calcular pontos
        home_row["Pts"] = (home_row["W"] * 3) + home_row["D"]
        away_row["Pts"] = (away_row["W"] * 3) + away_row["D"]
        
        # Criar DataFrame
        df = pd.DataFrame([home_row, away_row])
        
        return df
    
    except Exception as e:
        logger.error(f"Erro ao converter estatísticas: {str(e)}")
        return None

# Função principal para uso no dashboard
def get_league_and_teams_data():
    """
    Função principal para obter dados de ligas e times para o dashboard
    
    Returns:
        tuple: (ligas disponíveis, mapeamento de times por liga)
    """
    # Obter ligas disponíveis
    leagues = get_available_leagues()
    
    # Criar mapeamento de times por liga
    teams_by_league = {}
    for league_name in leagues.keys():
        teams_by_league[league_name] = get_team_names_by_league(league_name)
    
    return leagues.keys(), teams_by_league
