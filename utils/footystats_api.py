# utils/footystats_api.py - Updated with proper headers and authentication

import os
import json
import time
import logging
import requests
from datetime import datetime

# Configuração de logging
logger = logging.getLogger("valueHunter.footystats_api")

# Configuração da API
BASE_URL = "https://footystats.org/api"
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

# Mapeamento de IDs das principais ligas
LEAGUE_IDS = {
    "Premier League": 1,     # England Premier League
    "La Liga": 3,            # Spain La Liga
    "Serie A": 4,            # Italy Serie A
    "Bundesliga": 5,         # Germany Bundesliga
    "Ligue 1": 7,            # France Ligue 1
    "Champions League": 8,   # UEFA Champions League
    "Europa League": 9,      # UEFA Europa League
    "Brasileirão": 26,       # Brazil Serie A
    "Liga Portugal": 13,     # Portugal Primeira Liga
    "Eredivisie": 10,        # Netherlands Eredivisie
    "Belgian Pro League": 14, # Belgium First Division
    "Scottish Premiership": 27, # Scotland Premiership
    "Super Lig": 19,         # Turkey Super Lig
    "Championship": 2,       # England Championship
    "MLS": 23,               # USA MLS
}

# Mapeamento de temporadas por liga
LEAGUE_SEASONS = {
    # European leagues
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
    
    # Montar URL completa
    url = f"{BASE_URL}{endpoint}"
    
    # Garantir que params é um dicionário
    if params is None:
        params = {}
    
    # Adicionar API key aos parâmetros
    params["key"] = API_KEY
    
    # Configurar headers de acordo com a documentação do FootyStats
    headers = {
        "Accept": "application/json",
        "User-Agent": "ValueHunter/1.0",
        "Referer": "https://footystats.org/",
        "Origin": "https://footystats.org"
    }
    
    try:
        # Log detalhado da requisição (omitindo a API key por segurança)
        param_log = {k: v for k, v in params.items() if k != "key"}
        logger.info(f"API Request: {url} - Params: {param_log}")
        
        # Fazer a requisição com timeout e retentativas
        for attempt in range(3):  # Try up to 3 times
            try:
                response = requests.get(url, params=params, headers=headers, timeout=15)
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
        
        # Informações detalhadas da resposta para diagnóstico
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
            logger.error(f"Resposta: {response.text[:500]}")
            
            # Informações detalhadas para ajudar no diagnóstico
            if response.status_code == 403:
                logger.error("Erro 403 Forbidden - Possíveis causas:")
                logger.error("1. Autenticação incorreta")
                logger.error("2. Restrição de IP")
                logger.error("3. Headers incorretos")
                logger.error("4. Endpoint restrito para seu plano")
                
            return None
            
    except Exception as e:
        logger.error(f"Erro ao acessar a API: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def fetch_league_teams(league_id, season=None):
    """
    Buscar times de uma liga específica
    
    Args:
        league_id (int): ID da liga
        season (int, optional): Temporada
        
    Returns:
        list: Lista de times ou lista vazia em caso de erro
    """
    # Usar temporada atual se não for especificada
    if season is None:
        season = CURRENT_SEASON
    
    # Parâmetros de acordo com a documentação
    params = {
        "key": API_KEY,
        "comp_id": league_id,
        "season_id": season
    }
    
    # Endpoint correto conforme documentação
    endpoint = "/league-teams"
    
    logger.info(f"Buscando times para liga ID {league_id}, temporada {season}")
    
    # Fazer requisição sem usar api_request para ter mais controle
    url = f"{BASE_URL}{endpoint}"
    
    # Headers específicos
    headers = {
        "Accept": "application/json",
        "User-Agent": "ValueHunter/1.0",
        "Referer": "https://footystats.org/",
        "Origin": "https://footystats.org"
    }
    
    try:
        # Log detalhado
        logger.info(f"Requisição direta: {url} com params comp_id={league_id}, season_id={season}")
        
        # Requisição direta
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        logger.info(f"Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "data" in data and len(data["data"]) > 0:
                logger.info(f"Encontrados {len(data['data'])} times para liga ID {league_id}")
                return data["data"]
            else:
                logger.warning(f"API retornou array vazio para liga ID {league_id}")
                if "message" in data:
                    logger.warning(f"Mensagem da API: {data['message']}")
                return []
        else:
            logger.error(f"Erro ao buscar times: {response.status_code}")
            logger.error(f"Resposta: {response.text[:500]}")
            return []
    
    except Exception as e:
        logger.error(f"Exceção ao buscar times: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def get_team_names_by_league(league_name):
    """
    Obter apenas os nomes dos times de uma liga
    
    Args:
        league_name (str): Nome da liga
        
    Returns:
        list: Lista de nomes dos times
    """
    # Verificar se a liga existe no mapeamento
    if league_name not in LEAGUE_IDS:
        logger.error(f"Liga não encontrada no mapeamento: {league_name}")
        return []
    
    league_id = LEAGUE_IDS[league_name]
    season = LEAGUE_SEASONS.get(league_name, CURRENT_SEASON)
    
    # Verificar cache
    cache_key = f"teams_{league_name}_{season}"
    cached_names = get_from_cache(cache_key)
    if cached_names:
        return cached_names
    
    # Buscar times da API
    teams_data = fetch_league_teams(league_id, season)
    
    if teams_data and len(teams_data) > 0:
        # Extrair apenas os nomes dos times
        team_names = []
        for team in teams_data:
            name = team.get("name", "Unknown")
            if name and name != "Unknown":
                team_names.append(name)
        
        if team_names:
            # Salvar nomes no cache
            save_to_cache(team_names, cache_key)
            return team_names
    
    # Se não encontrou times, tentar endpoint alternativo
    logger.warning("Tentando endpoint alternativo para obter times...")
    
    # Tentar endpoint teams
    try:
        params = {
            "key": API_KEY,
            "comp_id": league_id
        }
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "ValueHunter/1.0",
            "Referer": "https://footystats.org/",
            "Origin": "https://footystats.org"
        }
        
        url = f"{BASE_URL}/teams"
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                teams = []
                for team in data["data"]:
                    name = team.get("name", "Unknown")
                    if name and name != "Unknown":
                        teams.append(name)
                
                if teams:
                    # Salvar no cache
                    save_to_cache(teams, cache_key)
                    return teams
    except Exception as e:
        logger.error(f"Erro ao usar endpoint alternativo: {str(e)}")
    
    return []

def test_auth_methods():
    """
    Testa diferentes métodos de autenticação para diagnosticar problemas
    
    Returns:
        dict: Resultados dos testes
    """
    results = {}
    
    # Teste 1: Chave na URL como parâmetro query
    try:
        url = f"{BASE_URL}/leagues?key={API_KEY}"
        response = requests.get(url, timeout=10)
        results["query_param"] = {
            "status": response.status_code,
            "success": response.status_code == 200
        }
    except Exception as e:
        results["query_param"] = {"error": str(e)}
    
    # Teste 2: Chave como header de autorização
    try:
        url = f"{BASE_URL}/leagues"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(url, headers=headers, timeout=10)
        results["auth_header"] = {
            "status": response.status_code,
            "success": response.status_code == 200
        }
    except Exception as e:
        results["auth_header"] = {"error": str(e)}
    
    # Teste 3: Chave como parâmetro + user agent
    try:
        url = f"{BASE_URL}/leagues"
        params = {"key": API_KEY}
        headers = {"User-Agent": "ValueHunter/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        results["user_agent"] = {
            "status": response.status_code,
            "success": response.status_code == 200
        }
    except Exception as e:
        results["user_agent"] = {"error": str(e)}
    
    # Teste 4: Completo com todos os headers
    try:
        url = f"{BASE_URL}/leagues"
        params = {"key": API_KEY}
        headers = {
            "Accept": "application/json",
            "User-Agent": "ValueHunter/1.0",
            "Referer": "https://footystats.org/",
            "Origin": "https://footystats.org"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        results["full_headers"] = {
            "status": response.status_code,
            "success": response.status_code == 200
        }
    except Exception as e:
        results["full_headers"] = {"error": str(e)}
    
    return results

def test_api_connection():
    """
    Testa a conexão com a API e exibe detalhes de diagnóstico
    
    Returns:
        bool: True se a conexão foi bem sucedida, False caso contrário
    """
    try:
        logger.info("Testando conexão com a API FootyStats...")
        
        # Testar diferentes métodos de autenticação
        auth_results = test_auth_methods()
        
        # Verificar se algum método funcionou
        working_methods = [method for method, result in auth_results.items() 
                         if result.get("success", False)]
        
        if working_methods:
            logger.info(f"✓ Conexão com API FootyStats bem sucedida")
            logger.info(f"✓ Métodos de autenticação que funcionaram: {working_methods}")
            return True
        else:
            logger.error("✗ Nenhum método de autenticação funcionou")
            for method, result in auth_results.items():
                status = result.get("status", "Erro")
                logger.error(f"  - {method}: Status {status}")
            
            logger.error("Verifique:")
            logger.error("1. Se sua API key está correta")
            logger.error("2. Se sua assinatura está ativa")
            logger.error("3. Se você tem permissão para acessar a API")
            logger.error("4. Se há restrições de IP")
            
            return False
    except Exception as e:
        logger.error(f"✗ Erro ao testar conexão com API: {str(e)}")
        return False

def get_available_leagues():
    """
    Obter lista de ligas disponíveis
    
    Returns:
        dict: Dicionário com nomes das ligas como chaves e IDs como valores
    """
    # Tentar obter da API
    data = api_request("/leagues", {"key": API_KEY})
    
    if data and isinstance(data, dict) and "data" in data:
        leagues = {}
        for league in data["data"]:
            league_name = league.get("name", "Unknown")
            league_id = league.get("id")
            if league_id:
                leagues[league_name] = league_id
                
        if leagues:
            logger.info(f"Obtidas {len(leagues)} ligas da API")
            return leagues
    
    # Se falhar, usar o mapeamento estático
    logger.warning("Usando mapeamento estático de ligas")
    return LEAGUE_IDS
