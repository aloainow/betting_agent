# utils/footystats_api.py - Integração com a API FootyStats
import os
import json
import time
import logging
import requests
from datetime import datetime

# Configuração de logging
logger = logging.getLogger("valueHunter.footystats_api")

# Configuração da API
BASE_URL = "https://api.footystats.org"
API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"  # Substitua pela sua chave da FootyStats

# Obter a temporada atual
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

# Mapeamento de IDs das principais ligas (ajuste conforme os IDs da FootyStats)
LEAGUE_IDS = {
    "Premier League": 2,
    "La Liga": 3,
    "Serie A": 4,
    "Bundesliga": 5,
    "Ligue 1": 6,
    "Champions League": 7
}

# Mapeamento de temporadas específicas para cada liga
LEAGUE_SEASONS = {
    "Premier League": 2024,
    "La Liga": 2024,
    "Serie A": 2024,
    "Bundesliga": 2024,
    "Ligue 1": 2024,
    "Champions League": 2024
}

# Cache para minimizar requisições
CACHE_DURATION = 24 * 60 * 60  # 24 horas em segundos
CACHE_DIR = os.path.join("data", "api_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_auth_params():
    """Obter parâmetros de autenticação para as requisições à API"""
    return {
        "key": API_KEY
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
    
    # Adicionar chave de API aos parâmetros
    auth_params = get_auth_params()
    if params:
        params.update(auth_params)
    else:
        params = auth_params
    
    try:
        response = requests.get(url, params=params)
        
        # Log da requisição para diagnóstico
        logger.info(f"API Request: {url} - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar se a API retornou erro
            if "error" in data:
                logger.error(f"Erro da API: {data['error']}")
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
    Obter a temporada para uma liga específica
    
    Args:
        league_name (str): Nome da liga
        
    Returns:
        int: Temporada (ano) para a liga
    """
    # Verificar se temos uma temporada específica definida para esta liga
    if league_name in LEAGUE_SEASONS:
        return LEAGUE_SEASONS[league_name]
    
    # Fallback para a temporada atual
    return CURRENT_SEASON

def get_available_leagues():
    """
    Obter lista de ligas disponíveis
    
    Returns:
        dict: Dicionário com nomes das ligas como chaves e IDs como valores
    """
    try:
        # Fazer requisição para obter todas as ligas
        data = api_request("/competitions")
        
        if data and "data" in data:
            available_leagues = {}
            
            for league in data["data"]:
                # Mapear apenas as ligas principais que já conhecemos
                league_name = league.get("name")
                league_id = league.get("id")
                
                if league_name in LEAGUE_IDS:
                    available_leagues[league_name] = league_id
                    logger.info(f"Liga {league_name} disponível (ID: {league_id})")
            
            if available_leagues:
                return available_leagues
    except Exception as e:
        logger.error(f"Erro ao verificar ligas disponíveis: {str(e)}")
    
    # Se não conseguir obter ligas da API, retornar as principais que conhecemos
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
        "competition_id": league_id,
        "season": season
    }
    
    # Log da temporada sendo usada
    logger.info(f"Buscando times para {league_name} (temporada {season})")
    
    # Fazer requisição à API
    data = api_request("/league-teams", params)
    
    if data and "data" in data:
        # Formatar a resposta para retornar apenas o necessário
        teams = []
        for team in data["data"]:
            teams.append({
                "id": team["id"],
                "name": team["name"],
                "logo": team.get("image_path", "")
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
        "team_id": team_id,
        "competition_id": league_id,
        "season": season
    }
    
    # Fazer requisição à API
    data = api_request("/team-statistics", params)
    
    if data and "data" in data:
        return data["data"]
    
    return None

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

def get_fixture_statistics(home_team_name, away_team_name, league_name):
    """
    Obter estatísticas para uma partida entre dois times
    
    Args:
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
        league_name (str): Nome da liga
        
    Returns:
        dict: Estatísticas de ambos os times formatadas para análise
    """
    # Obter IDs dos times
    home_team_id = get_team_id_by_name(home_team_name, league_name)
    away_team_id = get_team_id_by_name(away_team_name, league_name)
    
    if not home_team_id or not away_team_id:
        teams_not_found = []
        if not home_team_id:
            teams_not_found.append(home_team_name)
        if not away_team_id:
            teams_not_found.append(away_team_name)
        
        logger.error(f"Times não encontrados: {', '.join(teams_not_found)}")
        return None
    
    # Obter estatísticas de cada time
    home_team_stats = get_team_statistics(home_team_id, league_name)
    away_team_stats = get_team_statistics(away_team_id, league_name)
    
    if not home_team_stats or not away_team_stats:
        missing_stats = []
        if not home_team_stats:
            missing_stats.append(home_team_name)
        if not away_team_stats:
            missing_stats.append(away_team_name)
            
        logger.error(f"Estatísticas não disponíveis para: {', '.join(missing_stats)}")
        return None
    
    # Formatar estatísticas para análise
    season = LEAGUE_SEASONS.get(league_name, CURRENT_SEASON)
    return {
        "home_team": {
            "name": home_team_name,
            "id": home_team_id,
            "stats": home_team_stats
        },
        "away_team": {
            "name": away_team_name,
            "id": away_team_id,
            "stats": away_team_stats
        },
        "league": {
            "name": league_name,
            "id": LEAGUE_IDS.get(league_name)
        },
        "season": season
    }

def convert_api_stats_to_df_format(fixture_stats):
    """
    Converter estatísticas da API FootyStats para o formato de DataFrame esperado
    
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
        
        # Extrair estatísticas básicas dos times
        home_stats = home_team["stats"]
        away_stats = away_team["stats"]
        
        # Mapeamento de campos da FootyStats para o formato esperado pelo ValueHunter
        # Nota: Estes campos precisam ser ajustados com base na documentação real da FootyStats
        home_row = {
            "Squad": home_team["name"],
            "MP": safe_get(home_stats, "matches_played", default=0),
            "W": safe_get(home_stats, "wins", default=0),
            "D": safe_get(home_stats, "draws", default=0),
            "L": safe_get(home_stats, "losses", default=0),
            "Pts": safe_get(home_stats, "points", default=0),
            "Gls": safe_get(home_stats, "goals_scored", default=0),
            "GA": safe_get(home_stats, "goals_conceded", default=0),
            "xG": safe_get(home_stats, "expected_goals", default=None),
            "xGA": safe_get(home_stats, "expected_goals_against", default=None),
            "Poss": safe_get(home_stats, "possession_percent", default=50),
            "CS": safe_get(home_stats, "clean_sheets", default=0)
        }
        
        away_row = {
            "Squad": away_team["name"],
            "MP": safe_get(away_stats, "matches_played", default=0),
            "W": safe_get(away_stats, "wins", default=0),
            "D": safe_get(away_stats, "draws", default=0),
            "L": safe_get(away_stats, "losses", default=0),
            "Pts": safe_get(away_stats, "points", default=0),
            "Gls": safe_get(away_stats, "goals_scored", default=0),
            "GA": safe_get(away_stats, "goals_conceded", default=0),
            "xG": safe_get(away_stats, "expected_goals", default=None),
            "xGA": safe_get(away_stats, "expected_goals_against", default=None),
            "Poss": safe_get(away_stats, "possession_percent", default=50),
            "CS": safe_get(away_stats, "clean_sheets", default=0)
        }

        # Fallback para dados de xG se não estiverem disponíveis
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
