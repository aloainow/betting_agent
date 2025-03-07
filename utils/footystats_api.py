# Complete overhaul of key functions in utils/footystats_api.py

import os
import json
import time
import logging
import requests
from datetime import datetime

# Configuração de logging
logger = logging.getLogger("valueHunter.footystats_api")

# Configuração da API - URL BASE CORRIGIDA
BASE_URL = "https://api.football-data-api.com"
API_KEY = "b1742f67bda1c097be51c61409f1897a334d1889c291fedd5bcc0b3e070aa6c1"  # Substitua pela sua chave da FootyStats

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

# Mapeamento de IDs das principais ligas (corrigidos conforme documentação da API)
LEAGUE_IDS = {
    # Top 5 European Leagues - Using correct IDs
    "Premier League": 2012,    # England Premier League
    "La Liga": 2014,           # Spain La Liga
    "Serie A": 2019,           # Italy Serie A
    "Bundesliga": 2002,        # Germany Bundesliga
    "Ligue 1": 2015,           # France Ligue 1
    
    # European Competitions
    "Champions League": 2001,  # UEFA Champions League
    "Europa League": 2146,     # UEFA Europa League
    
    # Other Popular Leagues - Verify these IDs in your FootyStats account
    "Brasileirão": 2013,       # Brazil Serie A
    "Liga Portugal": 2017,     # Portugal Primeira Liga
    "Eredivisie": 2003,        # Netherlands Eredivisie
    "Belgian Pro League": 2009, # Belgium First Division
    "Scottish Premiership": 2084, # Scotland Premiership
    "Super Lig": 2070,         # Turkey Super Lig
    "Championship": 2016,      # England Championship
    "MLS": 2087,               # USA MLS
}

# Mapeamento de temporadas por liga
LEAGUE_SEASONS = {
    # European leagues 2023-2024 season (may need to be updated)
    "Premier League": 2023,
    "La Liga": 2023,
    "Serie A": 2023,
    "Bundesliga": 2023,
    "Ligue 1": 2023,
    "Champions League": 2023,
    "Europa League": 2023,
    
    # Other leagues
    "Brasileirão": 2023,
    "Liga Portugal": 2023,
    "Eredivisie": 2023,
    "Belgian Pro League": 2023,
    "Scottish Premiership": 2023,
    "Super Lig": 2023,
    "Championship": 2023,
    "MLS": 2023,
}

# Cache para minimizar requisições
CACHE_DURATION = 24 * 60 * 60  # 24 horas em segundos
CACHE_DIR = os.path.join("data", "api_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_file(endpoint, params=None):
    """Gerar nome de arquivo para cache baseado no endpoint e parâmetros"""
    cache_key = endpoint.replace("/", "_")
    if params:
        param_str = "_".join([f"{k}_{v}" for k, v in sorted(params.items()) if k != "key"])
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

def fetch_competitions():
    """
    Buscar todas as competições disponíveis na API
    
    Returns:
        dict: Lista de competições disponíveis ou None em caso de erro
    """
    url = f"{BASE_URL}/competitions"
    params = {"key": API_KEY}
    
    try:
        logger.info("Buscando lista de competições disponíveis")
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                logger.info(f"Encontradas {len(data['data'])} competições disponíveis")
                return data
            else:
                logger.warning("API retornou lista vazia de competições")
                return None
        else:
            logger.error(f"Erro ao buscar competições: {response.status_code}")
            logger.error(f"Resposta: {response.text[:200]}...")
            return None
    except Exception as e:
        logger.error(f"Exceção ao buscar competições: {str(e)}")
        return None

def fetch_teams_by_league_id(league_id, season=None):
    """
    Buscar times por ID de liga
    
    Args:
        league_id (int): ID da liga
        season (int, optional): Temporada
        
    Returns:
        list: Lista de times ou lista vazia em caso de erro
    """
    url = f"{BASE_URL}/teams"  # Endpoint correto conforme documentação
    
    # Usar temporada atual se não for especificada
    if season is None:
        season = CURRENT_SEASON
    
    params = {
        "key": API_KEY,
        "comp_id": league_id,  # Parâmetro correto conforme documentação
    }
    
    # Log detalhado
    logger.info(f"Buscando times para liga ID {league_id}, temporada {season}")
    logger.info(f"URL: {url}, Parâmetros: comp_id={league_id}")
    
    try:
        response = requests.get(url, params=params, timeout=15)
        logger.info(f"Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                logger.info(f"Encontrados {len(data['data'])} times")
                return data["data"]
            else:
                logger.warning(f"Nenhum time encontrado para liga ID {league_id}")
                logger.warning(f"Resposta: {json.dumps(data)[:200]}...")
                return []
        else:
            logger.error(f"Erro {response.status_code} ao buscar times")
            logger.error(f"Resposta: {response.text[:200]}...")
            return []
    except Exception as e:
        logger.error(f"Exceção ao buscar times: {str(e)}")
        return []

def get_team_names_by_league(league_name):
    """
    Obter apenas os nomes dos times de uma liga (formato simplificado)
    
    Args:
        league_name (str): Nome da liga
        
    Returns:
        list: Lista de nomes dos times
    """
    # Primeiro, verificar se a liga existe no mapeamento
    league_id = LEAGUE_IDS.get(league_name)
    if not league_id:
        logger.error(f"Liga não encontrada: {league_name}")
        return []
    
    # Verificar cache
    cache_key = f"teams_{league_name}_{CURRENT_SEASON}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Se não está em cache, buscar da API
    teams_data = fetch_teams_by_league_id(league_id, CURRENT_SEASON)
    
    if teams_data and len(teams_data) > 0:
        # Extrair apenas os nomes dos times
        team_names = [team.get("name", "Unknown") for team in teams_data]
        
        # Salvar no cache
        save_to_cache(team_names, cache_key)
        
        return team_names
    
    return []

def test_api_connection():
    """
    Testa a conexão com a API e exibe detalhes de diagnóstico
    
    Returns:
        bool: True se a conexão foi bem sucedida, False caso contrário
    """
    try:
        logger.info("Testando conexão com a API FootyStats...")
        
        # Teste simples para verificar se a API está acessível
        response = requests.get(f"{BASE_URL}/competitions", params={"key": API_KEY}, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data and "data" in data and len(data["data"]) > 0:
                    logger.info("✓ Conexão com API FootyStats bem sucedida")
                    logger.info(f"✓ {len(data['data'])} competições disponíveis")
                    
                    # Mostrar algumas competições disponíveis
                    for comp in data["data"][:5]:
                        logger.info(f"  - {comp.get('name', 'Unknown')} (ID: {comp.get('id', 'Unknown')})")
                    
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

def fetch_available_leagues():
    """
    Buscar ligas disponíveis na API
    
    Returns:
        dict: Mapeamento de nomes para IDs das ligas disponíveis
    """
    data = None
    # Try to fetch from API
    try:
        response = requests.get(f"{BASE_URL}/competitions", params={"key": API_KEY}, timeout=15)
        if response.status_code == 200:
            data = response.json()
    except Exception as e:
        logger.error(f"Erro ao buscar ligas disponíveis: {str(e)}")
        
    # Process the data if available
    if data and "data" in data and len(data["data"]) > 0:
        available_leagues = {}
        for league in data["data"]:
            name = league.get("name", "Unknown")
            league_id = league.get("id")
            if name and league_id:
                available_leagues[name] = league_id
                logger.info(f"Liga disponível: {name} (ID: {league_id})")
        
        # Update the global mapping with what we found
        if available_leagues:
            for name, id in available_leagues.items():
                # Only add if there's a match with our predefined leagues
                for key in LEAGUE_IDS.keys():
                    if key.lower() in name.lower() or name.lower() in key.lower():
                        logger.info(f"Atualizando ID para {key}: {id} (foi {LEAGUE_IDS[key]})")
                        LEAGUE_IDS[key] = id
                        break
        
        return available_leagues
    
    # Fall back to our predefined mapping
    return {k: v for k, v in LEAGUE_IDS.items()}

def get_available_leagues():
    """
    Obter ligas disponíveis (com fallback para mapeamento estático)
    
    Returns:
        dict: Mapeamento de nomes para IDs das ligas disponíveis
    """
    leagues = fetch_available_leagues()
    if leagues and len(leagues) > 0:
        return leagues
    
    # If API fails, fall back to our predefined mapping
    return {k: v for k, v in LEAGUE_IDS.items()}
