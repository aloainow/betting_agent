# utils/footystats_api.py - Implementação corrigida para ligas FootyStats
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

# Mapeamento de IDs das principais ligas COM PAÍSES - será preenchido dinamicamente
LEAGUE_IDS = {}

# Mapeamento de temporadas - inicializado como vazio, será preenchido com dados da API
LEAGUE_SEASONS = {}

# Mapeamento reverso para compatibilidade
SIMPLE_LEAGUE_NAMES = {}

# Cache para minimizar requisições
CACHE_DURATION = 6 * 60 * 60  # 6 horas em segundos (reduzido de 24h para evitar problemas de cache)
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

def diagnose_api_in_detail():
    """
    Função de diagnóstico detalhado que testa várias combinações de parâmetros
    para identificar qual funciona com a API do FootyStats.
    """
    import requests
    import json
    
    print("=== DIAGNÓSTICO DETALHADO DA API FOOTYSTATS ===")
    print(f"API Key (últimos 8 caracteres): ...{API_KEY[-8:]}")
    print(f"Base URL: {BASE_URL}")
    
    # 1. Teste básico - verificar se a API está acessível
    print("\n1. TESTANDO ACESSO BÁSICO À API")
    try:
        response = requests.get(f"{BASE_URL}/league-list", params={"key": API_KEY})
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API acessível")
            data = response.json()
            if "data" in data and isinstance(data["data"], list):
                print(f"✅ Encontradas {len(data['data'])} ligas no total")
            else:
                print("❌ Formato de resposta inválido")
        else:
            print(f"❌ API retornou erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao acessar API: {str(e)}")
    
    # 2. Testar parâmetros diferentes com ligas conhecidas
    print("\n2. TESTANDO PARÂMETROS DIFERENTES COM LIGAS CONHECIDAS")
    
    # Ligas conhecidas para teste
    test_leagues = {
        "La Liga": 1869,
        "Premier League": 1625,
        "Serie A": 1870,
        "Bundesliga": 1871
    }
    
    # Parâmetros para testar
    param_combinations = [
        {"season_id": None, "include": "stats"},
        {"season_id": None},
        {"league_id": None, "include": "stats"},
        {"league_id": None}
    ]
    
    successful_combinations = []
    
    for league_name, league_id in test_leagues.items():
        print(f"\nTestando com {league_name} (ID: {league_id}):")
        
        for params_template in param_combinations:
            # Copiar o template e preencher o ID
            params = params_template.copy()
            
            # Substituir None pelo ID real
            for key in params:
                if params[key] is None:
                    params[key] = league_id
            
            # Adicionar chave API
            params["key"] = API_KEY
            
            # Construir descrição dos parâmetros (sem a API key)
            param_desc = ", ".join([f"{k}={v}" for k, v in params.items() if k != "key"])
            print(f"  Testando: {param_desc}")
            
            try:
                response = requests.get(f"{BASE_URL}/league-teams", params=params, timeout=15)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data and isinstance(data["data"], list):
                        teams = data["data"]
                        if teams:
                            print(f"  ✅ Sucesso: {len(teams)} times encontrados")
                            
                            # Mostrar alguns times
                            team_sample = [team["name"] for team in teams[:3] if "name" in team]
                            if team_sample:
                                print(f"  Exemplos: {', '.join(team_sample)}")
                            
                            # Registrar combinação bem-sucedida
                            successful_combinations.append({
                                "league": league_name,
                                "params": param_desc,
                                "teams_count": len(teams)
                            })
                        else:
                            print("  ⚠️ Resposta vazia (nenhum time)")
                    else:
                        error_msg = data.get("message", "Formato inválido") if isinstance(data, dict) else "Resposta não é um objeto"
                        print(f"  ❌ Erro: {error_msg}")
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", f"Código HTTP {response.status_code}")
                    except:
                        error_msg = f"Código HTTP {response.status_code}"
                    print(f"  ❌ Erro: {error_msg}")
            except Exception as e:
                print(f"  ❌ Erro de requisição: {str(e)}")
    
    # 3. Resumo e recomendações
    print("\n3. RESUMO E RECOMENDAÇÕES")
    
    if successful_combinations:
        print(f"\n✅ {len(successful_combinations)} combinações bem-sucedidas:")
        
        # Contar sucessos por combinação de parâmetros
        param_success = {}
        for combo in successful_combinations:
            params = combo["params"]
            if params not in param_success:
                param_success[params] = 0
            param_success[params] += 1
        
        # Mostrar contagens
        for params, count in sorted(param_success.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {params}: funcionou em {count} ligas")
        
        # Encontrar a melhor combinação
        best_params = max(param_success.items(), key=lambda x: x[1])
        print(f"\n✨ RECOMENDAÇÃO: Use os parâmetros {best_params[0]} (funcionou em {best_params[1]} ligas)")
    else:
        print("\n❌ Nenhuma combinação funcionou!")
        print("\nRecomendações:")
        print("1. Verifique se sua API key está correta")
        print("2. Verifique se você tem uma assinatura ativa no FootyStats")
        print("3. Verifique se você selecionou ligas específicas no seu dashboard FootyStats")
    
    return successful_combinations

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

# Adicione esta função ao arquivo utils/footystats_api.py

def get_league_id_mapping(force_refresh=False):
    """
    Obtém um mapeamento completo de nomes de ligas para seus IDs
    
    Args:
        force_refresh (bool): Se True, ignora o cache
    
    Returns:
        dict: Mapeamento de nomes de liga para IDs
    """
    # Verificar cache
    cache_key = "league_id_mapping"
    if not force_refresh:
        cached_data = get_from_cache(cache_key)
        if cached_data:
            logger.info(f"Usando mapeamento de IDs em cache: {len(cached_data)} ligas")
            return cached_data
    
    # Buscar dados da API
    params = {"key": API_KEY}
    data = api_request("league-list", params, use_cache=not force_refresh)
    
    if data and "data" in data and isinstance(data["data"], list):
        # Criar mapeamento
        mapping = {}
        for league in data["data"]:
            if "id" in league and "name" in league and "country" in league:
                league_id = league["id"]
                name = league["name"]
                country = league["country"]
                
                # Criar o nome completo da liga
                formatted_name = f"{name} ({country})"
                
                # Adicionar ao mapeamento
                mapping[formatted_name] = league_id
                
                # Adicionar também versão sem país
                mapping[name] = league_id
                
                # Para ligas mais conhecidas, adicionar nomes alternativos 
                if "Premier League" in name and "England" in country:
                    mapping["Premier League"] = league_id
                elif "La Liga" in name and "Spain" in country:
                    mapping["La Liga"] = league_id
                elif "Serie A" in name and "Italy" in country:
                    mapping["Serie A"] = league_id
                elif "Bundesliga" in name and "Germany" in country and not "2." in name:
                    mapping["Bundesliga"] = league_id
                elif "Ligue 1" in name and "France" in country:
                    mapping["Ligue 1"] = league_id
                elif "Champions League" in name and "Europe" in country:
                    mapping["Champions League"] = league_id
                elif "Brasileirão" in name or ("Série A" in name and "Brazil" in country):
                    mapping["Brasileirão"] = league_id
        
        # Salvar no cache
        save_to_cache(mapping, cache_key)
        logger.info(f"Mapeamento de IDs criado: {len(mapping)} entradas")
        return mapping
    
    # Fallback para o mapeamento existente em LEAGUE_IDS
    logger.warning("Usando mapeamento estático de IDs - a API não retornou dados válidos")
    return LEAGUE_IDS.copy()

def test_api_connection():
    """
    Enhanced test to directly check your API key and available leagues.
    Returns ONLY leagues that are actually in your subscription.
    
    Returns:
        dict: Test result with detailed information
    """
    try:
        logger.info("Testing FootyStats API connection...")
        result = {
            "success": False,
            "details": [],
            "available_leagues": [],
            "error": None
        }
        
        # First test: Check if the API key is valid
        logger.info("Testing API key validation...")
        
        try:
            # Make a basic request to check API access
            response = requests.get(
                f"{BASE_URL}/league-list", 
                params={"key": API_KEY},
                timeout=10
            )
            
            if response.status_code == 200:
                result["details"].append("✓ API key is valid")
                
                # Parse the league list
                try:
                    data = response.json()
                    all_leagues = data.get("data", [])
                    result["details"].append(f"✓ API returned information about {len(all_leagues)} total leagues")
                    
                    # Now, for each league, test if you have ACTUAL access by trying to get teams
                    logger.info("Testing which leagues you have actual access to...")
                    
                    # To avoid making too many API calls, we'll test the first few leagues,
                    # then use a more efficient approach for the rest
                    available_leagues = []
                    
                    # Method 1: Test specific common leagues that people often subscribe to
                    common_leagues = [
                        "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1",
                        "Champions League", "Brasileirão", "MLS", "Primeira Liga", "Eredivisie"
                    ]
                    
                    # For each common league, find its ID and test access
                    for league_name in common_leagues:
                        for league in all_leagues:
                            if league_name.lower() in league.get("name", "").lower():
                                league_id = league.get("id")
                                if league_id:
                                    # Test if you can access this league's teams
                                    team_response = requests.get(
                                        f"{BASE_URL}/league-teams",
                                        params={"key": API_KEY, "league_id": league_id},
                                        timeout=10
                                    )
                                    
                                    if team_response.status_code == 200:
                                        try:
                                            team_data = team_response.json()
                                            if "data" in team_data and len(team_data["data"]) > 0:
                                                # This league is accessible!
                                                country = league.get("country", "")
                                                full_name = f"{league.get('name')} ({country})" if country else league.get('name', "")
                                                available_leagues.append(full_name)
                                                logger.info(f"Found accessible league: {full_name}")
                                        except:
                                            pass
                    
                    # Method 2: For the remaining leagues, use the response message to determine access
                    if len(available_leagues) < 5:  # If we found very few leagues, try harder
                        logger.info("Found few leagues, testing more comprehensively...")
                        for league in all_leagues:
                            league_id = league.get("id")
                            if league_id:
                                country = league.get("country", "")
                                full_name = f"{league.get('name')} ({country})" if country else league.get('name', "")
                                
                                # Skip leagues we already tested
                                if full_name in available_leagues:
                                    continue
                                
                                # Test if you can access this league's teams
                                team_response = requests.get(
                                    f"{BASE_URL}/league-teams", 
                                    params={"key": API_KEY, "league_id": league_id},
                                    timeout=10
                                )
                                
                                if team_response.status_code == 200:
                                    try:
                                        team_data = team_response.json()
                                        if "data" in team_data and len(team_data["data"]) > 0:
                                            # This league is accessible!
                                            available_leagues.append(full_name)
                                            logger.info(f"Found accessible league: {full_name}")
                                            
                                            # Limit how many leagues we test to avoid overloading the API
                                            if len(available_leagues) >= 30:
                                                logger.info("Found enough leagues, stopping search...")
                                                break
                                    except:
                                        pass
                    
                    # Update result
                    result["available_leagues"] = available_leagues
                    result["success"] = len(available_leagues) > 0
                    result["details"].append(f"✓ Found {len(available_leagues)} leagues in your subscription")
                    
                    if len(available_leagues) == 0:
                        result["error"] = "No leagues found in your subscription. Please select leagues in your FootyStats account."
                        result["details"].append("✗ No leagues are selected in your FootyStats account")
                    
                except Exception as e:
                    result["details"].append(f"✗ Error parsing API response: {str(e)}")
                    result["error"] = f"API returned invalid data: {str(e)}"
            else:
                result["details"].append(f"✗ API returned error code {response.status_code}")
                if response.status_code == 401:
                    result["error"] = "Invalid API key"
                else:
                    result["error"] = f"API error: {response.status_code}"
                    try:
                        error_json = response.json()
                        if "message" in error_json:
                            result["error"] = error_json["message"]
                    except:
                        pass
                    
        except requests.exceptions.RequestException as e:
            result["details"].append(f"✗ Connection error: {str(e)}")
            result["error"] = f"Connection error: {str(e)}"
        
        logger.info(f"API test complete: success={result['success']}, leagues={len(result['available_leagues'])}")
        return result
        
    except Exception as e:
        logger.error(f"Critical error in API test: {str(e)}")
        return {
            "success": False,
            "details": [f"✗ Critical error: {str(e)}"],
            "available_leagues": [],
            "error": str(e)
        }
def clear_all_cache():
    """Limpar todo o cache da API"""
    try:
        if not os.path.exists(CACHE_DIR):
            return 0
            
        count = 0
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(CACHE_DIR, filename)
                try:
                    os.remove(file_path)
                    count += 1
                except OSError as e:
                    logger.error(f"Erro ao remover arquivo de cache {file_path}: {e}")
                    
        logger.info(f"Cache limpo: {count} arquivos removidos")
        return count
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
        return 0

def clear_league_cache(league_name):
    """Limpar cache específico para uma liga"""
    try:
        if not os.path.exists(CACHE_DIR):
            return 0
            
        count = 0
        safe_name = league_name.replace(' ', '_').replace('(', '').replace(')', '').lower()
        
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.json') and safe_name in filename.lower():
                file_path = os.path.join(CACHE_DIR, filename)
                try:
                    os.remove(file_path)
                    count += 1
                except OSError as e:
                    logger.error(f"Erro ao remover arquivo de cache {file_path}: {e}")
                    
        logger.info(f"Cache limpo para {league_name}: {count} arquivos removidos")
        return count
    except Exception as e:
        logger.error(f"Erro ao limpar cache para {league_name}: {str(e)}")
        return 0

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

# Adicione este código ao seu arquivo utils/footystats_api.py:

# Lista de ligas selecionadas pelo usuário
USER_SELECTED_LEAGUES = [
    # Ligas da América do Sul
    "Primera División (Argentina)",
    "Serie A (Brazil)",
    "Brasileirão (Brazil)",  # Nome alternativo para Serie A
    "Serie B (Brazil)",
    "Copa do Brasil (Brazil)",
    "Primera División (Uruguay)",
    "Copa Libertadores (South America)",
    "Copa Sudamericana (South America)",
    
    # Ligas Europeias - Top 5
    "Premier League (England)", 
    "La Liga (Spain)",
    "Segunda División (Spain)",
    "Bundesliga (Germany)",
    "2. Bundesliga (Germany)",
    "Serie A (Italy)",
    "Serie B (Italy)",
    "Ligue 1 (France)",
    "Ligue 2 (France)",
    
    # Outras Ligas Europeias
    "Bundesliga (Austria)",
    "Pro League (Belgium)",
    "Eredivisie (Netherlands)",
    "Liga NOS (Portugal)",
    "Primeira Liga (Portugal)",  # Nome alternativo para Liga NOS
    
    # Competições Europeias
    "Champions League (Europe)",
    "Europa League (Europe)",
    
    # Outras Ligas
    "Liga MX (Mexico)",
    
    # Outras competições inglesas
    "FA Cup (England)",
    "EFL League One (England)"
]

# Mapeamento de nomes alternativos para nomes padrão da API
LEAGUE_NAME_MAPPING = {
    "Brasileirão": "Serie A (Brazil)",
    "Primeira Liga": "Liga NOS (Portugal)",
    "Premier League": "Premier League (England)",
    "La Liga": "La Liga (Spain)",
    "Bundesliga": "Bundesliga (Germany)",
    "Serie A": "Serie A (Italy)",
    "Ligue 1": "Ligue 1 (France)",
    "Champions League": "Champions League (Europe)",
    "Europa League": "Europa League (Europe)",
    "Eredivisie": "Eredivisie (Netherlands)",
    "Liga MX": "Liga MX (Mexico)"
}

# Se você já tem essa função, não precisa adicionar novamente
def get_user_selected_leagues_direct():
    """
    Retorna diretamente as ligas selecionadas pelo usuário,
    sem precisar testar via API.
    
    Returns:
        list: Lista de nomes de ligas selecionadas pelo usuário
    """
    # Remove duplicatas e ordena
    unique_leagues = set(USER_SELECTED_LEAGUES)
    return sorted(list(unique_leagues))

# Se você já tem essa função, não precisa adicionar novamente
def normalize_league_name_for_api(league_name):
    """
    Normaliza o nome da liga para corresponder ao formato esperado pela API.
    
    Args:
        league_name (str): Nome da liga do dropdown
        
    Returns:
        str: Nome da liga no formato da API
    """
    # Verificar se há um mapeamento direto
    if league_name in LEAGUE_NAME_MAPPING:
        return LEAGUE_NAME_MAPPING[league_name]
        
    # Verificar alguns casos especiais
    if "Brasileirão" in league_name:
        return "Serie A (Brazil)"
    if "Primeira Liga" in league_name or "Liga NOS" in league_name:
        return "Primeira Liga (Portugal)"
        
    return league_name

def retrieve_available_leagues(force_refresh=False):
    """
    Buscar todas as ligas disponíveis para o usuário na API
    
    Args:
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        dict: Mapeamento de nomes de liga para IDs
    """
    # Verificar cache, a menos que force_refresh seja True
    cache_key = "available_leagues"
    if not force_refresh:
        cached_data = get_from_cache(cache_key)
        if cached_data:
            return cached_data
    
    # Se não houver cache, buscar da API
    # Endpoint correto para listar ligas disponíveis para o usuário
    leagues_data = api_request("league-list", use_cache=not force_refresh)
    
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
        else:
            logger.warning("API retornou lista de ligas vazia - verifique sua assinatura")
    
    # Se falhar, tentar com o endpoint alternativo
    logger.info("Tentando endpoint alternativo para listar ligas")
    alt_leagues_data = api_request("competitions", use_cache=not force_refresh)
    
    if alt_leagues_data and "data" in alt_leagues_data:
        leagues = {}
        
        for league in alt_leagues_data["data"]:
            league_id = league.get("id")
            name = league.get("name", "Unknown")
            country = league.get("country", "Unknown")
            
            full_name = f"{name} ({country})"
            
            if league_id:
                leagues[full_name] = league_id
                SIMPLE_LEAGUE_NAMES[full_name] = name
                LEAGUE_IDS[full_name] = league_id
        
        if leagues:
            save_to_cache(leagues, cache_key)
            logger.info(f"Recuperadas {len(leagues)} ligas do endpoint alternativo")
            return leagues
    
    # Se ainda falhar, usar mapeamento com ligas mais comuns
    logger.warning("Usando mapeamento padrão de ligas - API não retornou dados")
    
    # Mapeamento básico com ligas mais comuns
    fallback_leagues = {
        "Premier League (England)": 1625,
        "La Liga (Spain)": 1869,
        "Serie A (Italy)": 1870,
        "Bundesliga (Germany)": 1871,
        "Ligue 1 (France)": 1872,
        "Champions League (Europe)": 1873
    }
    
    # Atualizar mapeamentos globais
    for full_name, league_id in fallback_leagues.items():
        simple_name = full_name.split(" (")[0]
        SIMPLE_LEAGUE_NAMES[full_name] = simple_name
        LEAGUE_IDS[full_name] = league_id
    
    return fallback_leagues

def get_selected_leagues(force_refresh=False):
    """
    Get only leagues that are actually selected in the user's FootyStats account.
    Uses caching to avoid expensive API calls.
    
    Args:
        force_refresh (bool): If True, ignores the cache
        
    Returns:
        list: List of leagues selected in the user's account
    """
    # Check cache first (unless force_refresh is True)
    cache_key = "selected_leagues"
    if not force_refresh:
        cached_data = get_from_cache(cache_key)
        if cached_data:
            logger.info(f"Using cached selected leagues: {len(cached_data)} leagues")
            return cached_data
    
    # Get all leagues from API
    params = {"key": API_KEY}
    all_leagues_data = api_request("league-list", params, use_cache=not force_refresh)
    
    if not all_leagues_data or "data" not in all_leagues_data:
        logger.error("Failed to fetch leagues from API")
        return []
    
    # Parse all leagues
    all_leagues = []
    for league in all_leagues_data["data"]:
        league_id = league.get("id")
        name = league.get("name", "")
        country = league.get("country", "")
        if name and league_id:
            formatted_name = f"{name} ({country})" if country else name
            all_leagues.append((formatted_name, league_id))
    
    # Test each league to see if it's selected
    selected_leagues = []
    for league_name, league_id in all_leagues:
        # Try to fetch teams for this league
        teams_data = fetch_league_teams(league_id)
        
        # If we got teams, the league is selected
        if isinstance(teams_data, list) and len(teams_data) > 0:
            selected_leagues.append(league_name)
            logger.info(f"League '{league_name}' is selected in your account")
    
    # Cache the results
    if selected_leagues:
        save_to_cache(selected_leagues, cache_key, cache_duration=24*60*60)  # Cache for 24 hours
        logger.info(f"Identified {len(selected_leagues)} selected leagues")
    
    return selected_leagues


def fetch_league_teams(league_id):
    """
    Buscar times de uma liga específica.
    Sem fallbacks ou dados de exemplo.
    
    Args:
        league_id (int): ID da liga/temporada
        
    Returns:
        list: Lista de times ou lista vazia em caso de erro
    """
    # Parâmetros conforme documentação atualizada
    params = {
        "key": API_KEY,
        "season_id": league_id,  # Mudado de league_id para season_id
        "include": "stats"  # Adicionado conforme documentação
    }
    
    # Endpoint correto conforme documentação
    endpoint = "league-teams"
    
    logger.info(f"Buscando times para temporada/liga ID {league_id}")
    
    # Fazer a requisição
    data = api_request(endpoint, params)
    
    if data and isinstance(data, dict) and "data" in data:
        teams = data["data"]
        logger.info(f"Encontrados {len(teams)} times para temporada/liga ID {league_id}")
        return teams
    
    # Se não encontramos times, verificar o erro
    if data and isinstance(data, dict) and "message" in data:
        error_msg = data.get("message", "")
        logger.warning(f"Erro ao buscar times: {error_msg}")
        
    logger.warning(f"Nenhum time encontrado para temporada/liga ID {league_id}")
    return []
def load_dashboard_leagues():
    """
    Carrega as ligas para o dropdown do dashboard,
    usando diretamente a lista de ligas selecionadas.
    
    Returns:
        list: Lista de nomes de ligas para o dropdown
    """
    leagues = get_user_selected_leagues_direct()
    
    # Ordenar alfabeticamente
    leagues.sort()
    
    return leagues

def find_league_id_by_name(league_name):
    """
    Enhanced version that finds the league ID even with naming variations
    
    Args:
        league_name (str): Name of the league (with or without country)
        
    Returns:
        int: League ID or None if not found
    """
    # Get league mapping
    league_mapping = get_league_id_mapping()
    
    # Case 1: Exact match
    if league_name in league_mapping:
        logger.info(f"Exact match found for '{league_name}': {league_mapping[league_name]}")
        return league_mapping[league_name]
    
    # Case 2: Get available leagues from test_api_connection
    api_test = test_api_connection()
    if api_test["success"] and "available_leagues" in api_test and api_test["available_leagues"]:
        # For each available league in user account
        for available_league in api_test["available_leagues"]:
            # Remove country prefix if it exists (e.g., "Spain La Liga" -> "La Liga")
            available_name = available_league
            available_country = ""
            if "(" in available_league:
                available_parts = available_league.split("(")
                available_name = available_parts[0].strip()
                available_country = "(" + available_parts[1] if len(available_parts) > 1 else ""
            
            # Same for input league name
            input_name = league_name
            input_country = ""
            if "(" in league_name:
                input_parts = league_name.split("(")
                input_name = input_parts[0].strip()
                input_country = "(" + input_parts[1] if len(input_parts) > 1 else ""
            
            # Try to match base names
            if (input_name.lower() in available_name.lower() or 
                available_name.lower() in input_name.lower()):
                
                # Countries match or don't exist in one of them
                if not input_country or not available_country or input_country.lower() == available_country.lower():
                    logger.info(f"Found matching league: '{available_league}' for '{league_name}'")
                    
                    # Get ID from mapping
                    for map_name, map_id in league_mapping.items():
                        if available_league.lower() == map_name.lower():
                            logger.info(f"Found ID {map_id} for '{available_league}'")
                            return map_id
                    
                    # If not found in mapping, try using league name directly for lookup
                    league_list_data = api_request("league-list", {"key": API_KEY})
                    if league_list_data and "data" in league_list_data:
                        for league in league_list_data["data"]:
                            league_api_name = league.get("name", "")
                            league_api_country = league.get("country", "")
                            full_api_name = f"{league_api_name} ({league_api_country})"
                            
                            if (full_api_name.lower() == available_league.lower() or
                                league_api_name.lower() == available_name.lower()):
                                league_id = league.get("id")
                                if league_id:
                                    logger.info(f"Found ID {league_id} for '{available_league}' via API lookup")
                                    return league_id
    
    # Case 3: Check for similar names in league mapping
    for map_name, map_id in league_mapping.items():
        # Strip country parts
        map_base = map_name.split("(")[0].strip().lower()
        input_base = league_name.split("(")[0].strip().lower()
        
        # Check for similarity
        if map_base in input_base or input_base in map_base:
            similarity = len(set(map_base.split()) & set(input_base.split())) / max(len(map_base.split()), len(input_base.split()))
            if similarity > 0.5:  # At least 50% word overlap
                logger.info(f"Found similar league: '{map_name}' for '{league_name}' (similarity: {similarity:.2f})")
                return map_id
    
    logger.error(f"No league ID found for '{league_name}'")
    return None

def get_team_names_by_league(league_name, force_refresh=False):
    """
    Obter nomes dos times de uma liga usando o endpoint correto do FootyStats
    
    Args:
        league_name (str): Nome da liga
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        list: Lista de nomes dos times
    """
    logger.info(f"Buscando times para liga: {league_name}")
    
    # Verificar cache, a menos que force_refresh seja True
    cache_key = f"teams_{league_name.replace(' ', '_').replace('(', '').replace(')', '')}"
    if not force_refresh:
        cached_names = get_from_cache(cache_key)
        if cached_names:
            logger.info(f"Usando times em cache para '{league_name}': {len(cached_names)} times")
            return cached_names
    
    # Obter ID da liga/temporada
    league_id = find_league_id_by_name(league_name)
    
    if not league_id:
        logger.error(f"Não foi possível encontrar ID para a liga: {league_name}")
        return []
    
    # Parâmetros exatos conforme a documentação do FootyStats
    # Note que usamos season_id em vez de league_id conforme a documentação
    params = {
        "key": API_KEY,
        "season_id": league_id,  # Mudou de league_id para season_id
        "include": "stats"  # Adicionando o parâmetro include=stats conforme a documentação
    }
    
    # Fazer a requisição diretamente
    url = f"{BASE_URL}/league-teams"
    
    try:
        logger.info(f"Fazendo requisição para {url} com season_id={league_id} (conforme documentação)")
        response = requests.get(url, params=params, timeout=15)
        
        # Log da resposta
        logger.info(f"Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Log do conteúdo para debug
                logger.info(f"Tipo de resposta: {type(data)}")
                if isinstance(data, dict):
                    logger.info(f"Chaves na resposta: {list(data.keys())}")
                
                # Verificar se temos dados válidos
                if "data" in data and isinstance(data["data"], list):
                    teams_data = data["data"]
                    logger.info(f"Encontrados {len(teams_data)} times no JSON")
                    
                    # Extrair apenas os nomes dos times
                    team_names = []
                    for team in teams_data:
                        if isinstance(team, dict) and "name" in team:
                            team_names.append(team["name"])
                    
                    if team_names:
                        logger.info(f"Nomes de times extraídos: {len(team_names)}")
                        logger.info(f"Primeiros 5 times: {team_names[:5]}")
                        
                        # Salvar no cache
                        save_to_cache(team_names, cache_key)
                        return team_names
                    else:
                        logger.warning("Nenhum nome de time extraído dos dados")
                else:
                    logger.warning(f"Formato de resposta inesperado. Chaves: {list(data.keys()) if isinstance(data, dict) else 'Não é um dicionário'}")
                    
                    # Verificar se há mensagem de erro na resposta
                    if isinstance(data, dict) and "message" in data:
                        logger.error(f"Mensagem de erro da API: {data['message']}")
            except ValueError as json_error:
                logger.error(f"Erro ao processar JSON: {str(json_error)}")
                logger.error(f"Primeiros 500 caracteres da resposta: {response.text[:500]}")
        else:
            logger.error(f"Código de status HTTP inesperado: {response.status_code}")
            try:
                error_data = response.json()
                if "message" in error_data:
                    logger.error(f"Mensagem de erro: {error_data['message']}")
            except:
                logger.error(f"Corpo da resposta: {response.text[:500]}")
    
    except requests.exceptions.RequestException as req_error:
        logger.error(f"Erro na requisição HTTP: {str(req_error)}")
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Se chegamos aqui, algo deu errado
    return []
def diagnose_api_connection():
    """
    Teste detalhado da conexão com a API para diagnóstico
    
    Returns:
        dict: Resultado do diagnóstico
    """
    results = {
        "success": False,
        "api_key_valid": False,
        "can_list_leagues": False,
        "leagues_found": 0,
        "errors": [],
        "sample_leagues": []
    }
    
    try:
        # Teste 1: Verificar se a API key é válida
        response = requests.get(
            f"{BASE_URL}/league-list", 
            params={"key": API_KEY},
            timeout=10
        )
        
        results["status_code"] = response.status_code
        
        if response.status_code == 200:
            results["api_key_valid"] = True
            
            # Teste 2: Verificar se conseguimos listar ligas
            try:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    results["can_list_leagues"] = True
                    results["leagues_found"] = len(data["data"])
                    
                    # Pegar amostra de ligas para referência
                    sample = []
                    for league in data["data"][:5]:  # Primeiras 5 ligas
                        if "name" in league and "country" in league:
                            sample.append(f"{league['name']} ({league['country']})")
                    
                    results["sample_leagues"] = sample
                    
                    # Se encontramos ligas, teste foi bem-sucedido
                    if results["leagues_found"] > 0:
                        results["success"] = True
                else:
                    results["errors"].append("API retornou formato inesperado")
            except ValueError:
                results["errors"].append("API retornou JSON inválido")
        else:
            results["errors"].append(f"API retornou código de erro: {response.status_code}")
            
            # Tentar extrair mensagem de erro
            try:
                error_data = response.json()
                if "message" in error_data:
                    results["errors"].append(f"Mensagem de erro: {error_data['message']}")
            except:
                results["errors"].append(f"Corpo da resposta: {response.text[:100]}...")
        
    except requests.exceptions.RequestException as e:
        results["errors"].append(f"Erro de conexão: {str(e)}")
    except Exception as e:
        results["errors"].append(f"Erro inesperado: {str(e)}")
    
    return results

def get_available_leagues(force_refresh=False):
    """
    Obter lista de ligas disponíveis para o usuário
    
    Args:
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        dict: Dicionário com nomes das ligas disponíveis
    """
    # Buscar ligas da API (com possível refresh forçado)
    leagues = retrieve_available_leagues(force_refresh)
    
    # Retornar nomes para compatibilidade
    result = {}
    for league_name in leagues.keys():
        # Usar nome simples como valor se disponível
        simple_name = SIMPLE_LEAGUE_NAMES.get(league_name, league_name)
        result[simple_name] = simple_name
    
    return result

def diagnose_league_access(league_name):
    """
    Diagnostica problemas de acesso a uma liga específica
    
    Args:
        league_name (str): Nome da liga
        
    Returns:
        dict: Resultado do diagnóstico
    """
    result = {
        "success": False,
        "league_name": league_name,
        "error": None,
        "details": [],
        "recommendations": []
    }
    
    # Passo 1: Verificar se a liga está no mapeamento
    league_id = find_league_id_by_name(league_name)
    if not league_id:
        result["error"] = f"Liga '{league_name}' não encontrada no mapeamento"
        result["details"].append("✗ Esta liga não foi encontrada na lista de ligas disponíveis")
        result["recommendations"].append("Verifique se o nome da liga está correto")
        result["recommendations"].append("Acesse sua conta FootyStats e selecione esta liga")
        
        # Listar algumas ligas disponíveis como sugestão
        available = list(LEAGUE_IDS.keys())
        if available:
            sample = available[:5]
            result["details"].append(f"✓ Ligas disponíveis incluem: {', '.join(sample)}")
        return result
    
    # Passo 2: Testar acesso à liga
    params = {"key": API_KEY, "league_id": league_id}
    data = api_request("league-teams", params, use_cache=False)
    
    if not data:
        result["error"] = f"Não foi possível acessar dados da liga (ID {league_id})"
        result["details"].append("✗ Falha ao conectar com a API FootyStats")
        result["recommendations"].append("Verifique sua conexão com a internet")
        result["recommendations"].append("Verifique se sua chave de API é válida")
        return result
    
    # Passo 3: Analisar resposta
    if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
        # Sucesso - encontramos times!
        teams = data["data"]
        result["success"] = True
        result["details"].append(f"✓ Liga acessível com sucesso (ID {league_id})")
        result["details"].append(f"✓ {len(teams)} times encontrados")
        
        # Listar alguns times como exemplo
        if teams:
            team_names = [team.get("name", "Unknown") for team in teams[:5] if "name" in team]
            if team_names:
                result["details"].append(f"✓ Times incluem: {', '.join(team_names)}")
        
        return result
    
    # Passo 4: Analisar erro específico
    if "message" in data:
        error_msg = data["message"]
        result["error"] = error_msg
        
        if "League is not chosen by the user" in error_msg:
            result["details"].append(f"✗ Liga '{league_name}' não está selecionada na sua conta FootyStats")
            result["recommendations"].append("Acesse sua conta FootyStats e selecione explicitamente esta liga")
            result["recommendations"].append("Após selecionar a liga, aguarde até 30 minutos para o cache ser atualizado")
            result["recommendations"].append("Use o botão 'Limpar Cache' e tente novamente")
        elif "not available to this user" in error_msg:
            result["details"].append(f"✗ Liga '{league_name}' não está disponível no seu plano atual")
            result["recommendations"].append("Verifique se seu plano FootyStats inclui esta liga")
            result["recommendations"].append("Considere fazer upgrade do seu plano FootyStats")
        else:
            result["details"].append(f"✗ Erro ao acessar a liga: {error_msg}")
            result["recommendations"].append("Entre em contato com o suporte do FootyStats")
    else:
        result["error"] = "Resposta da API não contém times nem mensagem de erro"
        result["details"].append("✗ Resposta da API está vazia ou em formato inesperado")
        result["recommendations"].append("Tente novamente mais tarde")
        result["recommendations"].append("Verifique se sua conta FootyStats está ativa")
    
    return result

# Inicialização - buscar ligas disponíveis
try:
    # Tenta buscar ligas disponíveis ao importar o módulo (com cache)
    retrieve_available_leagues()
except Exception as e:
    logger.warning(f"Erro ao inicializar ligas: {str(e)}")
