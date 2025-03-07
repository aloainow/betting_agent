# utils/footystats_api.py - Complete fixed implementation with country info

import os
import json
import time
import logging
import requests
from datetime import datetime

# Configuração de logging
logger = logging.getLogger("valueHunter.footystats_api")

# Configuração da API - URL CORRETA CONFORME DOCUMENTAÇÃO
BASE_URL = "https://api.football-data-api.com"
API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"

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

# Mapeamento de IDs das principais ligas COM PAÍSES
# Formato: "Nome da Liga (País)": ID
# Nota: Os IDs são exemplos e serão substituídos pelos IDs reais obtidos da API
LEAGUE_IDS = {
    "Premier League (England)": 1625,
    "La Liga (Spain)": 1869,
    "Serie A (Italy)": 1870,
    "Bundesliga (Germany)": 1871,
    "Ligue 1 (France)": 1872,
    "Champions League (Europe)": 1873,
    "Brasileirão (Brazil)": 1874,
    "Eredivisie (Netherlands)": 1875,
    "Liga Portugal (Portugal)": 1876
}

# Mapeamento de temporadas - inicializado como vazio, será preenchido com dados da API
LEAGUE_SEASONS = {}

# Mapeamento reverso para compatibilidade
SIMPLE_LEAGUE_NAMES = {
    "Premier League (England)": "Premier League",
    "La Liga (Spain)": "La Liga",
    "Serie A (Italy)": "Serie A",
    "Bundesliga (Germany)": "Bundesliga",
    "Ligue 1 (France)": "Ligue 1",
    "Champions League (Europe)": "Champions League",
    "Brasileirão (Brazil)": "Brasileirão",
    "Eredivisie (Netherlands)": "Eredivisie",
    "Liga Portugal (Portugal)": "Liga Portugal"
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

def api_request(endpoint, params=None, use_cache=True, cache_duration=CACHE_DURATION):
    """
    Fazer requisição à API com tratamento de erros e cache
    
    Args:
        endpoint (str): Endpoint da API (ex: "leagues")
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
    
    # Montar URL completa - IMPORTANTE: não incluir barra antes do endpoint
    url = f"{BASE_URL}/{endpoint}"
    
    # Garantir que params é um dicionário
    if params is None:
        params = {}
    
    # Adicionar API key aos parâmetros se não estiver presente
    if "key" not in params:
        params["key"] = API_KEY
    
    try:
        # Log detalhado da requisição (omitindo a API key por segurança)
        param_log = {k: v for k, v in params.items() if k != "key"}
        logger.info(f"API Request: {url} - Params: {param_log}")
        
        # Fazer a requisição com timeout e retentativas
        for attempt in range(3):  # Try up to 3 times
            try:
                response = requests.get(url, params=params, timeout=15)
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
                
            # Salvar no cache se estiver habilitado
            if use_cache:
                save_to_cache(data, endpoint, params)
                
            return data
        else:
            logger.error(f"Erro na requisição: {response.status_code}")
            logger.error(f"Resposta: {response.text[:200]}...")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao acessar a API: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def retrieve_available_leagues():
    """
    Buscar todas as ligas disponíveis para o usuário na API
    
    Returns:
        dict: Mapeamento de nomes de liga para IDs
    """
    # Verificar cache
    cache_key = "available_leagues"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Se não houver cache, buscar da API
    leagues_data = api_request("competitions")
    
    if leagues_data and "data" in leagues_data:
        leagues = {}
        
        for league in leagues_data["data"]:
            # Extrair informações da liga
            league_id = league.get("id")
            name = league.get("name", "Unknown")
            country = league.get("country", "Unknown")
            
            # Criar nome completo com país
            full_name = f"{name} ({country})"
            
            # Adicionar ao mapeamento
            if league_id:
                leagues[full_name] = league_id
                
                # Adicionar também ao mapeamento simples
                SIMPLE_LEAGUE_NAMES[full_name] = name
                
                # Atualizar o mapeamento de IDs
                LEAGUE_IDS[full_name] = league_id
                
                # Guardar também informações de temporada se disponíveis
                if "season" in league:
                    LEAGUE_SEASONS[full_name] = league["season"]
        
        # Salvar no cache
        if leagues:
            save_to_cache(leagues, cache_key)
            logger.info(f"Recuperadas {len(leagues)} ligas da API")
            return leagues
    
    # Se falhar, retornar mapeamento estático
    logger.warning("Usando mapeamento estático de ligas")
    return LEAGUE_IDS

def fetch_league_teams(league_id):
    """
    Buscar times de uma liga específica
    
    Args:
        league_id (int): ID da liga
        
    Returns:
        list: Lista de times ou lista vazia em caso de erro
    """
    # Parâmetros conforme documentação
    params = {
        "key": API_KEY,
        "league_id": league_id
    }
    
    # Endpoint correto conforme documentação
    endpoint = "league-teams"
    
    logger.info(f"Buscando times para liga ID {league_id}")
    
    # Fazer a requisição
    data = api_request(endpoint, params)
    
    if data and isinstance(data, dict) and "data" in data:
        teams = data["data"]
        logger.info(f"Encontrados {len(teams)} times para liga ID {league_id}")
        return teams
    
    logger.warning(f"Nenhum time encontrado para liga ID {league_id}")
    return []

def find_league_id_by_name(league_name):
    """
    Encontrar o ID de uma liga a partir do nome
    
    Args:
        league_name (str): Nome da liga (com ou sem país)
        
    Returns:
        int: ID da liga ou None se não encontrado
    """
    # Inicializar dicionários de ligas se ainda não tiver sido feito
    if not LEAGUE_IDS or len(LEAGUE_IDS) < 5:
        retrieve_available_leagues()
    
    # Caso 1: Nome exato com país
    if league_name in LEAGUE_IDS:
        return LEAGUE_IDS[league_name]
    
    # Caso 2: Nome sem país
    for full_name, league_id in LEAGUE_IDS.items():
        # Verificar se o nome da liga está contido no nome completo
        if league_name in full_name or SIMPLE_LEAGUE_NAMES.get(full_name) == league_name:
            return league_id
    
    # Caso 3: Correspondência parcial
    for full_name, league_id in LEAGUE_IDS.items():
        simple_name = SIMPLE_LEAGUE_NAMES.get(full_name, "")
        if (league_name.lower() in full_name.lower() or 
            (simple_name and league_name.lower() in simple_name.lower())):
            return league_id
    
    return None

def get_team_names_by_league(league_name):
    """
    Obter nomes dos times de uma liga
    
    Args:
        league_name (str): Nome da liga
        
    Returns:
        list: Lista de nomes dos times
    """
    # Verificar cache
    cache_key = f"teams_{league_name}"
    cached_names = get_from_cache(cache_key)
    if cached_names:
        return cached_names
    
    # Buscar ID da liga
    league_id = find_league_id_by_name(league_name)
    
    if not league_id:
        logger.error(f"Não foi possível encontrar ID para a liga: {league_name}")
        return []
    
    # Buscar times da API
    teams_data = fetch_league_teams(league_id)
    
    if teams_data and len(teams_data) > 0:
        # Extrair apenas os nomes dos times
        team_names = []
        for team in teams_data:
            name = team.get("name")
            if name:
                team_names.append(name)
        
        if team_names:
            # Salvar nomes no cache
            save_to_cache(team_names, cache_key)
            return team_names
    
    # Se não encontrou times para esta liga,
    # tentar usando a chave de exemplo para Premier League
    if league_name in ["Premier League", "Premier League (England)"]:
        logger.info("Tentando buscar times de exemplo da Premier League")
        
        # Verificar cache
        cache_key = "teams_premier_league_example"
        cached_names = get_from_cache(cache_key)
        if cached_names:
            return cached_names
        
        # Usar chave de exemplo conforme documentação
        params = {
            "key": "example",
            "league_id": 1625  # Premier League 2018/2019
        }
        
        # Fazer a requisição
        endpoint = "league-teams"
        data = api_request(endpoint, params)
        
        if data and isinstance(data, dict) and "data" in data:
            teams = data["data"]
            logger.info(f"Encontrados {len(teams)} times de exemplo da Premier League")
            
            # Extrair apenas os nomes dos times
            team_names = []
            for team in teams:
                name = team.get("name")
                if name:
                    team_names.append(name)
            
            if team_names:
                # Salvar nomes no cache
                save_to_cache(team_names, cache_key)
                return team_names
    
    return []

def test_api_connection():
    """
    Testa a conexão com a API
    
    Returns:
        bool: True se a conexão foi bem sucedida, False caso contrário
    """
    try:
        logger.info("Testando conexão com a API FootyStats...")
        
        # Teste 1: Usando chave de exemplo
        endpoint = "league-teams"
        params = {"key": "example", "league_id": 1625}
        
        logger.info("Teste 1: Usando chave de exemplo")
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data and "data" in data and len(data["data"]) > 0:
                    logger.info("✓ Teste 1 bem sucedido com chave de exemplo")
                    logger.info(f"✓ {len(data['data'])} times encontrados")
                else:
                    logger.warning("✗ Teste 1: API retornou resposta vazia ou inválida")
            except json.JSONDecodeError:
                logger.warning("✗ Teste 1: API retornou resposta que não é um JSON válido")
        else:
            logger.warning(f"✗ Teste 1: API retornou código de status {response.status_code}")
            logger.warning(f"Response: {response.text[:200]}")
        
        # Teste 2: Usando sua chave real
        logger.info("Teste 2: Usando sua chave real")
        params = {"key": API_KEY}
        
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data and "data" in data and len(data["data"]) > 0:
                    logger.info("✓ Teste 2 bem sucedido com sua chave real")
                    logger.info(f"✓ {len(data['data'])} times encontrados")
                    return True
                else:
                    logger.warning("✗ Teste 2: API retornou resposta vazia ou inválida")
            except json.JSONDecodeError:
                logger.warning("✗ Teste 2: API retornou resposta que não é um JSON válido")
        else:
            logger.warning(f"✗ Teste 2: API retornou código de status {response.status_code}")
                
        return False
        
    except Exception as e:
        logger.error(f"✗ Erro ao testar conexão com API: {str(e)}")
        return False

def get_available_leagues():
    """
    Obter lista de ligas disponíveis
    
    Returns:
        dict: Dicionário com nomes das ligas
    """
    # Buscar ligas da API
    leagues = retrieve_available_leagues()
    
    # Retornar nomes para compatibilidade
    result = {}
    for league_name in leagues.keys():
        # Usar nome simples como valor se disponível
        simple_name = SIMPLE_LEAGUE_NAMES.get(league_name, league_name)
        result[simple_name] = simple_name
    
    return result

# Inicialização - buscar ligas disponíveis
try:
    # Tenta buscar ligas disponíveis ao importar o módulo
    retrieve_available_leagues()
except Exception as e:
    logger.warning(f"Erro ao inicializar ligas: {str(e)}")
