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
BASE_URL = "https://api.football-data-api.com"
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

# Updated section for utils/footystats_api.py

# Mapeamento atualizado de IDs das principais ligas
LEAGUE_IDS = {
    # Top 5 European Leagues
    "Premier League": 2,
    "La Liga": 3,
    "Serie A": 4,
    "Bundesliga": 5,
    "Ligue 1": 6,
    
    # European Competitions
    "Champions League": 7,
    "Europa League": 8,
    "Conference League": 9,
    
    # Other Popular Leagues
    "Brasileirão": 98,  # Brazilian Serie A
    "Liga Portugal": 10,
    "Eredivisie": 11,   # Dutch League
    "Belgian Pro League": 12,
    "Scottish Premiership": 13,
    "Super Lig": 14,    # Turkish League
    "Swiss Super League": 15,
    "Championship": 16, # English 2nd tier
    "Serie B": 17,      # Italian 2nd tier
    "La Liga 2": 18,    # Spanish 2nd tier
    "Bundesliga 2": 19, # German 2nd tier
    "Ligue 2": 20,      # French 2nd tier
    "MLS": 21,          # US Major League Soccer
    "Liga MX": 22,      # Mexican League
    "J1 League": 23,    # Japanese League
    "K League 1": 24,   # Korean League
    "A-League": 25,     # Australian League
    "Campeonato Argentino": 26, # Argentine League
    "Primeira Liga": 27, # Brazilian 1st tier (alternative name)
    
    # Add any other leagues you need with appropriate IDs
}

# Mapeamento de temporadas específicas para cada liga
# European leagues use 2024 for 2024-2025 season
# Other leagues may still be in their 2023 season
LEAGUE_SEASONS = {
    # European leagues that have started 2024-2025 season
    "Premier League": 2024,
    "La Liga": 2024,
    "Serie A": 2024,
    "Bundesliga": 2024,
    "Ligue 1": 2024,
    "Champions League": 2024,
    "Europa League": 2024,
    "Conference League": 2024,
    "Liga Portugal": 2024,
    "Eredivisie": 2024,
    "Belgian Pro League": 2024,
    "Scottish Premiership": 2024,
    "Super Lig": 2024,
    "Swiss Super League": 2024,
    "Championship": 2024,
    "Serie B": 2024,
    "La Liga 2": 2024,
    "Bundesliga 2": 2024,
    "Ligue 2": 2024,
    
    # Leagues that might still be in 2023 season or using calendar year
    "Brasileirão": 2024,  # Brazilian league runs calendar year
    "MLS": 2023,         # Runs from spring to fall
    "Liga MX": 2024,
    "J1 League": 2024,    # Calendar year season
    "K League 1": 2024,   # Calendar year season
    "A-League": 2023,     # Southern hemisphere (may be between seasons)
    "Campeonato Argentino": 2024,
    "Primeira Liga": 2024,
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

def test_api_connection():
    """
    Testa a conexão com a API e exibe detalhes de diagnóstico
    
    Returns:
        bool: True se a conexão foi bem sucedida, False caso contrário
    """
    try:
        logger.info("Testando conexão com a API FootyStats...")
        
        # Teste simples para verificar se a API está acessível
        test_endpoint = "/competitions"
        
        # Adicionar chave de API aos parâmetros
        auth_params = get_auth_params()
        
        response = requests.get(f"{BASE_URL}{test_endpoint}", params=auth_params, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data and "data" in data and len(data["data"]) > 0:
                    logger.info("✓ Conexão com API FootyStats bem sucedida")
                    logger.info(f"✓ {len(data['data'])} competições disponíveis")
                    return True
                else:
                    logger.error("✗ API retornou resposta vazia ou inválida")
            except json.JSONDecodeError:
                logger.error("✗ API retornou resposta que não é um JSON válido")
        else:
            logger.error(f"✗ API retornou código de status {response.status_code}")
            if response.status_code == 401:
                logger.error("✗ Erro de autenticação: verifique sua API key")
            elif response.status_code == 429:
                logger.error("✗ Limite de requisições atingido")
                
        return False
        
    except Exception as e:
        logger.error(f"✗ Erro ao testar conexão com API: {str(e)}")
        return False

# Enhanced api_request function for utils/footystats_api.py

def api_request(endpoint, params=None, use_cache=True, cache_duration=CACHE_DURATION):
    """
    Fazer requisição à API com tratamento de erros e cache aprimorado
    
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
        # Log detalhado da requisição
        param_log = {k: v for k, v in params.items() if k != "key"}  # Omit the key for security
        logger.info(f"API Request: {url} - Params: {param_log}")
        
        # Fazer a requisição com timeout e retentativas
        for attempt in range(3):  # Try up to 3 times
            try:
                response = requests.get(url, params=params, timeout=10)
                break
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout na tentativa {attempt+1}/3 para {endpoint}")
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(1)  # Wait before retry
            except requests.exceptions.ConnectionError:
                logger.warning(f"Erro de conexão na tentativa {attempt+1}/3 para {endpoint}")
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(1)  # Wait before retry
        
        # Log da resposta para diagnóstico
        logger.info(f"API Response: {url} - Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Resposta não é um JSON válido: {response.text[:100]}...")
                return None
            
            # Verificar se a API retornou erro explícito
            if isinstance(data, dict) and "error" in data:
                logger.error(f"Erro da API: {data.get('error')}")
                return None
                
            # Verificar se a resposta está vazia ou é None
            if data is None or (isinstance(data, dict) and not data):
                logger.warning(f"API retornou dados vazios para {endpoint}")
                return None
                
            # Verificar se a resposta tem a estrutura esperada
            if isinstance(data, dict) and "data" in data:
                if not data["data"]:  # data field is empty
                    logger.warning(f"API retornou campo data vazio para {endpoint}")
                
            # Salvar no cache se estiver habilitado
            if use_cache:
                save_to_cache(data, endpoint, params)
                
            return data
            
        elif response.status_code == 429:
            # Limite de requisições atingido
            logger.warning("Limite de requisições à API atingido. Aguardando antes de tentar novamente.")
            time.sleep(5)  # Wait for rate limit to reset
            return {"error": "rate_limit", "message": "Limite de requisições atingido"}
            
        elif response.status_code == 401:
            logger.error("Erro de autenticação (401): API key inválida ou expirada")
            return {"error": "auth_error", "message": "API key inválida ou expirada"}
            
        elif response.status_code == 404:
            logger.error(f"Endpoint não encontrado (404): {endpoint}")
            return {"error": "not_found", "message": f"Endpoint {endpoint} não encontrado"}
            
        else:
            logger.error(f"Erro na requisição: {response.status_code}")
            logger.error(f"Resposta: {response.text[:200]}...")  # Log first 200 chars
            return None
            
    except Exception as e:
        logger.error(f"Erro ao acessar a API: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# Add this function to check API configuration
def test_api_connection():
    """
    Testa a conexão com a API e exibe detalhes de diagnóstico
    
    Returns:
        bool: True se a conexão foi bem sucedida, False caso contrário
    """
    try:
        logger.info("Testando conexão com a API FootyStats...")
        
        # Teste simples para verificar se a API está acessível
        test_endpoint = "/competitions"
        
        response = requests.get(f"{BASE_URL}{test_endpoint}", params=get_auth_params(), timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data and "data" in data and len(data["data"]) > 0:
                    logger.info("✓ Conexão com API FootyStats bem sucedida")
                    logger.info(f"✓ {len(data['data'])} competições disponíveis")
                    return True
                else:
                    logger.error("✗ API retornou resposta vazia ou inválida")
            except json.JSONDecodeError:
                logger.error("✗ API retornou resposta que não é um JSON válido")
        else:
            logger.error(f"✗ API retornou código de status {response.status_code}")
            if response.status_code == 401:
                logger.error("✗ Erro de autenticação: verifique sua API key")
            elif response.status_code == 429:
                logger.error("✗ Limite de requisições atingido")
                
        return False
        
    except Exception as e:
        logger.error(f"✗ Erro ao testar conexão com API: {str(e)}")
        return False
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
    # ===== ENDPOINTS PARA ESTATÍSTICAS DE LIGAS =====

def get_league_standings(league_name):
    """
    Obter classificação da liga
    
    Args:
        league_name (str): Nome da liga
        
    Returns:
        list: Lista de times com suas posições e estatísticas na liga
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
    
    # Fazer requisição à API
    data = api_request("/league-table", params)
    
    if data and "data" in data:
        return data["data"]
    
    logger.warning(f"Não foi possível obter classificação para {league_name}")
    return []

def get_league_stats(league_name):
    """
    Obter estatísticas gerais da liga
    
    Args:
        league_name (str): Nome da liga
        
    Returns:
        dict: Estatísticas gerais da liga
    """
    # Obter o ID da liga
    league_id = LEAGUE_IDS.get(league_name)
    if not league_id:
        logger.error(f"Liga não encontrada: {league_name}")
        return {}
    
    # Obter a temporada adequada para esta liga
    season = LEAGUE_SEASONS.get(league_name, CURRENT_SEASON)
    
    # Parâmetros da requisição
    params = {
        "competition_id": league_id,
        "season": season
    }
    
    # Fazer requisição à API
    data = api_request("/league-stats", params)
    
    if data and "data" in data:
        return data["data"]
    
    logger.warning(f"Não foi possível obter estatísticas para {league_name}")
    return {}

# ===== ENDPOINTS PARA ESTATÍSTICAS DE TIMES =====

def get_team_form(team_id, league_name, last_n=5):
    """
    Obter o retrospecto recente de um time
    
    Args:
        team_id (int): ID do time
        league_name (str): Nome da liga
        last_n (int): Número de jogos recentes para analisar
        
    Returns:
        list: Lista dos últimos jogos com resultados
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
        "team_id": team_id,
        "competition_id": league_id,
        "season": season,
        "last": last_n
    }
    
    # Fazer requisição à API
    data = api_request("/team-form", params)
    
    if data and "data" in data:
        return data["data"]
    
    logger.warning(f"Não foi possível obter retrospecto para o time {team_id}")
    return []

def get_team_players(team_id, league_name):
    """
    Obter lista de jogadores de um time
    
    Args:
        team_id (int): ID do time
        league_name (str): Nome da liga
        
    Returns:
        list: Lista de jogadores com estatísticas
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
        "team_id": team_id,
        "competition_id": league_id,
        "season": season
    }
    
    # Fazer requisição à API
    data = api_request("/team-players", params)
    
    if data and "data" in data:
        return data["data"]
    
    logger.warning(f"Não foi possível obter jogadores para o time {team_id}")
    return []

def get_team_matches(team_id, league_name, include_upcoming=True):
    """
    Obter partidas de um time
    
    Args:
        team_id (int): ID do time
        league_name (str): Nome da liga
        include_upcoming (bool): Incluir partidas futuras
        
    Returns:
        list: Lista de partidas
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
        "team_id": team_id,
        "competition_id": league_id,
        "season": season,
        "upcoming": "true" if include_upcoming else "false"
    }
    
    # Fazer requisição à API
    data = api_request("/team-matches", params)
    
    if data and "data" in data:
        return data["data"]
    
    logger.warning(f"Não foi possível obter partidas para o time {team_id}")
    return []

# ===== ENDPOINTS PARA ANÁLISES HEAD-TO-HEAD =====

def get_head_to_head(team1_id, team2_id):
    """
    Obter estatísticas de confrontos diretos entre dois times
    
    Args:
        team1_id (int): ID do primeiro time
        team2_id (int): ID do segundo time
        
    Returns:
        dict: Estatísticas de confrontos diretos
    """
    # Parâmetros da requisição
    params = {
        "team1_id": team1_id,
        "team2_id": team2_id
    }
    
    # Fazer requisição à API
    data = api_request("/head2head", params)
    
    if data and "data" in data:
        return data["data"]
    
    logger.warning(f"Não foi possível obter head-to-head entre {team1_id} e {team2_id}")
    return {}

# ===== ENDPOINTS PARA ANÁLISES AVANÇADAS =====

def get_team_advanced_stats(team_id, league_name):
    """
    Obter estatísticas avançadas de um time
    
    Args:
        team_id (int): ID do time
        league_name (str): Nome da liga
        
    Returns:
        dict: Estatísticas avançadas
    """
    # Obter o ID da liga
    league_id = LEAGUE_IDS.get(league_name)
    if not league_id:
        logger.error(f"Liga não encontrada: {league_name}")
        return {}
    
    # Obter a temporada adequada para esta liga
    season = LEAGUE_SEASONS.get(league_name, CURRENT_SEASON)
    
    # Parâmetros da requisição
    params = {
        "team_id": team_id,
        "competition_id": league_id,
        "season": season
    }
    
    # Fazer requisição à API
    data = api_request("/team-advanced-stats", params)
    
    if data and "data" in data:
        return data["data"]
    
    logger.warning(f"Não foi possível obter estatísticas avançadas para o time {team_id}")
    return {}

def get_odds_analysis(team1_id, team2_id, league_name):
    """
    Obter análise de probabilidades para uma partida
    
    Args:
        team1_id (int): ID do time da casa
        team2_id (int): ID do time visitante
        league_name (str): Nome da liga
        
    Returns:
        dict: Análise de probabilidades
    """
    # Obter o ID da liga
    league_id = LEAGUE_IDS.get(league_name)
    if not league_id:
        logger.error(f"Liga não encontrada: {league_name}")
        return {}
    
    # Obter a temporada adequada para esta liga
    season = LEAGUE_SEASONS.get(league_name, CURRENT_SEASON)
    
    # Parâmetros da requisição
    params = {
        "home_team_id": team1_id,
        "away_team_id": team2_id,
        "competition_id": league_id,
        "season": season
    }
    
    # Fazer requisição à API
    data = api_request("/match-odds", params)
    
    if data and "data" in data:
        return data["data"]
    
    logger.warning(f"Não foi possível obter análise de odds para {team1_id} vs {team2_id}")
    return {}

# ===== FUNÇÕES DE CONVERSÃO PARA INTEGRAÇÃO COM O VALUEHUNTER =====

def extract_betting_markets(fixture_stats):
    """
    Extrair mercados de apostas das estatísticas de uma partida
    
    Args:
        fixture_stats (dict): Estatísticas obtidas da API
        
    Returns:
        dict: Mercados de apostas formatados para o ValueHunter
    """
    try:
        if not fixture_stats:
            return None
        
        # Tentar extrair odd analysis ou fazer uma chamada direta
        home_team_id = fixture_stats["home_team"]["id"]
        away_team_id = fixture_stats["away_team"]["id"]
        league_name = fixture_stats["league"]["name"]
        
        # Obter análise de odds para esta partida
        odds_data = get_odds_analysis(home_team_id, away_team_id, league_name)
        
        if not odds_data:
            return {}
        
        # Mapeamento para o formato esperado pelo ValueHunter
        betting_markets = {
            "money_line": {
                "home": odds_data.get("home_win_odds", 0),
                "draw": odds_data.get("draw_odds", 0),
                "away": odds_data.get("away_win_odds", 0)
            },
            "over_under": {
                "over": odds_data.get("over_2_5_odds", 0),
                "under": odds_data.get("under_2_5_odds", 0),
                "line": 2.5
            },
            "btts": {
                "yes": odds_data.get("btts_yes_odds", 0),
                "no": odds_data.get("btts_no_odds", 0)
            }
        }
        
        return betting_markets
    except Exception as e:
        logger.error(f"Erro ao extrair mercados de apostas: {str(e)}")
        return {}

def get_complete_fixture_analysis(home_team_name, away_team_name, league_name):
    """
    Função abrangente que combina diversas análises para uma partida
    
    Args:
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
        league_name (str): Nome da liga
        
    Returns:
        dict: Análise completa da partida
    """
    try:
        # Obter IDs dos times
        home_team_id = get_team_id_by_name(home_team_name, league_name)
        away_team_id = get_team_id_by_name(away_team_name, league_name)
        
        if not home_team_id or not away_team_id:
            logger.error(f"Não foi possível encontrar IDs para {home_team_name} ou {away_team_name}")
            return None
        
        # 1. Estatísticas básicas dos times
        fixture_stats = get_fixture_statistics(home_team_name, away_team_name, league_name)
        if not fixture_stats:
            return None
        
        # 2. Retrospecto recente
        home_form = get_team_form(home_team_id, league_name)
        away_form = get_team_form(away_team_id, league_name)
        
        # 3. Head to head
        h2h_data = get_head_to_head(home_team_id, away_team_id)
        
        # 4. Estatísticas avançadas
        home_advanced = get_team_advanced_stats(home_team_id, league_name)
        away_advanced = get_team_advanced_stats(away_team_id, league_name)
        
        # 5. Odds e probabilidades
        betting_markets = extract_betting_markets(fixture_stats)
        
        # Combinar tudo em uma análise completa
        complete_analysis = {
            "basic_stats": fixture_stats,
            "team_form": {
                "home": home_form,
                "away": away_form
            },
            "head_to_head": h2h_data,
            "advanced_stats": {
                "home": home_advanced,
                "away": away_advanced
            },
            "betting_markets": betting_markets
        }
        
        return complete_analysis
    except Exception as e:
        logger.error(f"Erro ao gerar análise completa: {str(e)}")
        return None    
# Add this to the end of utils/footystats_api.py to help with testing

def test_specific_league_request(league_name):
    """
    Test a specific league request to check if it works
    
    Args:
        league_name (str): The name of the league to test
        
    Returns:
        dict: The API response or error details
    """
    if league_name not in LEAGUE_IDS:
        return {"error": "league_not_found", "message": f"League '{league_name}' not found in LEAGUE_IDS mapping"}
    
    league_id = LEAGUE_IDS[league_name]
    season = LEAGUE_SEASONS.get(league_name, CURRENT_SEASON)
    
    # Build request parameters
    params = {
        "key": API_KEY,
        "competition_id": league_id,
        "season": season
    }
    
    # Make the request directly (bypassing the api_request function)
    url = f"{BASE_URL}/league-teams"
    
    try:
        logger.info(f"Testing direct request for {league_name} (id: {league_id}, season: {season})")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data and isinstance(data, dict):
                    # Check for API error messages
                    if "error" in data:
                        return {
                            "success": False,
                            "error": data.get("error"),
                            "message": data.get("message", "Unknown API error")
                        }
                    
                    # Check if 'data' field exists and has content
                    if "data" in data:
                        if data["data"] and len(data["data"]) > 0:
                            return {
                                "success": True,
                                "teams_count": len(data["data"]),
                                "sample_teams": [team.get("name", "Unknown") for team in data["data"][:5]],
                                "response": data
                            }
                        else:
                            return {
                                "success": False,
                                "error": "empty_data",
                                "message": "API returned empty data array"
                            }
                    else:
                        return {
                            "success": False,
                            "error": "missing_data_field",
                            "message": "API response doesn't contain 'data' field",
                            "response": data
                        }
                else:
                    return {
                        "success": False,
                        "error": "invalid_response",
                        "message": "API response is not a valid dictionary",
                        "response": data
                    }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": "json_decode_error",
                    "message": f"Failed to parse API response as JSON: {str(e)}",
                    "response_text": response.text[:500]  # First 500 chars
                }
        else:
            return {
                "success": False,
                "error": f"http_{response.status_code}",
                "message": f"API returned status code {response.status_code}",
                "response_text": response.text[:500]  # First 500 chars
            }
    except Exception as e:
        return {
            "success": False,
            "error": "request_exception",
            "message": f"Exception during API request: {str(e)}"
        }
