# utils/footystats_api.py - Implementação corrigida para ligas FootyStats
import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta

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
    Obter nomes dos times de uma liga usando o fluxo correto do FootyStats:
    1. Buscar lista de ligas para encontrar o season_id correto
    2. Usar o season_id para buscar os times
    
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
    
    # Passo 1: Buscar a lista de ligas para encontrar o season_id
    try:
        logger.info("Buscando lista de ligas para encontrar season_id...")
        league_list_response = requests.get(
            f"{BASE_URL}/league-list", 
            params={"key": API_KEY},
            timeout=15
        )
        
        if league_list_response.status_code != 200:
            logger.error(f"Erro ao buscar lista de ligas: {league_list_response.status_code}")
            return []
        
        league_data = league_list_response.json()
        
        if "data" not in league_data or not isinstance(league_data["data"], list):
            logger.error("Formato de resposta inválido na lista de ligas")
            return []
        
        # Procurar a liga por nome
        season_id = None
        for league in league_data["data"]:
            league_full_name = f"{league.get('name', '')} ({league.get('country', '')})"
            
            # Comparar nomes ignorando case
            if league_name.lower() == league_full_name.lower() or league_name.lower() == league.get('name', '').lower():
                season_id = league.get('id')
                logger.info(f"Liga encontrada! Nome: {league_full_name}, season_id: {season_id}")
                break
        
        # Se não encontrou correspondência exata, tentar correspondência parcial
        if not season_id:
            logger.info("Tentando correspondência parcial...")
            for league in league_data["data"]:
                league_api_name = league.get('name', '').lower()
                league_name_lower = league_name.lower()
                
                # Remover partes entre parênteses para comparação
                if '(' in league_name_lower:
                    league_name_base = league_name_lower.split('(')[0].strip()
                else:
                    league_name_base = league_name_lower
                
                if league_name_base in league_api_name or league_api_name in league_name_base:
                    season_id = league.get('id')
                    league_full_name = f"{league.get('name', '')} ({league.get('country', '')})"
                    logger.info(f"Correspondência parcial! Nome: {league_full_name}, season_id: {season_id}")
                    break
        
        if not season_id:
            logger.error(f"Não foi possível encontrar season_id para: {league_name}")
            return []
        
        # Passo 2: Buscar os times usando o season_id encontrado
        logger.info(f"Buscando times com season_id: {season_id}")
        params = {
            "key": API_KEY,
            "season_id": season_id,
            "include": "stats"
        }
        
        teams_response = requests.get(f"{BASE_URL}/league-teams", params=params, timeout=15)
        
        if teams_response.status_code != 200:
            logger.error(f"Erro ao buscar times: {teams_response.status_code}")
            return []
        
        teams_data = teams_response.json()
        
        if "data" not in teams_data or not isinstance(teams_data["data"], list):
            logger.error("Formato de resposta inválido na lista de times")
            return []
        
        # Extrair nomes dos times
        team_names = []
        for team in teams_data["data"]:
            if isinstance(team, dict) and "name" in team:
                team_names.append(team["name"])
        
        if not team_names:
            logger.warning("Nenhum time encontrado para a liga")
            return []
        
        # Salvar no cache
        save_to_cache(team_names, cache_key)
        logger.info(f"Encontrados {len(team_names)} times para {league_name}")
        
        return team_names
        
    except Exception as e:
        logger.error(f"Erro ao buscar times: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []
    
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

# Funções para correção de Team IDs e Match IDs

def calculate_name_similarity(name1, name2):
    """
    Calcula a similaridade entre dois nomes de times
    
    Args:
        name1 (str): Primeiro nome
        name2 (str): Segundo nome
        
    Returns:
        float: Valor de similaridade entre 0 e 1
    """
    # Caso 1: Correspondência exata
    if name1 == name2:
        return 1.0
    
    # Caso 2: Um contém o outro completamente
    if name1 in name2 or name2 in name1:
        shorter = min(len(name1), len(name2))
        longer = max(len(name1), len(name2))
        return shorter / longer  # Uma medida da "contenção"
    
    # Caso 3: Similaridade baseada em palavras comuns
    words1 = set(name1.split())
    words2 = set(name2.split())
    
    # Se não há palavras, retornar 0
    if not words1 or not words2:
        return 0
    
    # Calcular a similaridade Jaccard: tamanho da interseção / tamanho da união
    common_words = words1.intersection(words2)
    all_words = words1.union(words2)
    
    if not all_words:
        return 0
        
    return len(common_words) / len(all_words)

def get_fixture_statistics(home_team, away_team, selected_league, use_cache=True):
    """
    Enhanced function to get comprehensive statistics for a fixture between two teams
    with improved error handling and team name matching.
    
    Args:
        home_team (str): Home team name
        away_team (str): Away team name
        selected_league (str): League name
        use_cache (bool): Whether to use cached data
        
    Returns:
        dict: Comprehensive fixture statistics or None if error
    """
    try:
        logger.info(f"Getting fixture statistics for {home_team} vs {away_team} in {selected_league}")
        
        # Step 1: Find the league/season ID with improved error handling
        from utils.footystats_api import find_league_id_by_name
        season_id = find_league_id_by_name(selected_league)
        
        # If not found, try to use the LEAGUE_SEASON_IDS mapping directly
        if not season_id:
            from utils.footystats_api import LEAGUE_SEASON_IDS
            if selected_league in LEAGUE_SEASON_IDS:
                season_id = LEAGUE_SEASON_IDS[selected_league]
                logger.info(f"Found season ID {season_id} from direct mapping for {selected_league}")
            else:
                # Try partial matching for league names
                selected_league_lower = selected_league.lower()
                for league_name, league_id in LEAGUE_SEASON_IDS.items():
                    if (league_name.lower() in selected_league_lower or 
                        selected_league_lower in league_name.lower()):
                        season_id = league_id
                        logger.info(f"Found season ID {season_id} via partial match for {selected_league}")
                        break
                        
        if not season_id:
            logger.error(f"League ID not found for {selected_league}")
            return None
        
        logger.info(f"Using season ID {season_id} for {selected_league}")
        
        # Clear team cache if needed
        if not use_cache:
            from utils.footystats_api import clear_league_cache
            clear_league_cache(selected_league)
            logger.info(f"Cleared cache for {selected_league}")
            
        # Step 2: Get teams with retry mechanism and more flexible name matching
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Get all teams in the league with appropriate parameters
                api_url = f"https://api.football-data-api.com/league-teams"
                params = {
                    "key": "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1",
                    "season_id": season_id,
                    "include": "stats"
                }
                
                response = requests.get(api_url, params=params, timeout=15)
                
                if response.status_code != 200:
                    logger.error(f"API error: {response.status_code} - {response.text[:200]}")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(1)
                    continue
                    
                teams_data = response.json()
                
                if "data" not in teams_data or not isinstance(teams_data["data"], list):
                    logger.error(f"Invalid response format: {teams_data.keys()}")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(1)
                    continue
                    
                teams = teams_data["data"]
                if not teams:
                    logger.error(f"No teams returned for league {selected_league}")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(1)
                    continue
                    
                logger.info(f"Found {len(teams)} teams for league {selected_league}")
                
                # Step 3: Find team IDs with better team name matching
                def calculate_name_similarity(name1, name2):
                    """Calculate similarity between two team names"""
                    name1 = name1.lower().strip()
                    name2 = name2.lower().strip()
                    
                    # Exact match
                    if name1 == name2:
                        return 1.0
                    
                    # One contains the other
                    if name1 in name2 or name2 in name1:
                        shorter = min(len(name1), len(name2))
                        longer = max(len(name1), len(name2))
                        return shorter / longer
                    
                    # Word overlap similarity
                    words1 = set(name1.split())
                    words2 = set(name2.split())
                    
                    if not words1 or not words2:
                        return 0
                    
                    common = words1.intersection(words2)
                    union = words1.union(words2)
                    return len(common) / len(union)
                
                # Find home team
                home_team_matches = []
                for team in teams:
                    team_name = team.get("name", "")
                    similarity = calculate_name_similarity(home_team, team_name)
                    if similarity > 0.5:  # At least 50% similar
                        home_team_matches.append((team, similarity))
                
                # Find away team
                away_team_matches = []
                for team in teams:
                    team_name = team.get("name", "")
                    similarity = calculate_name_similarity(away_team, team_name)
                    if similarity > 0.5:  # At least 50% similar
                        away_team_matches.append((team, similarity))
                
                # Sort by similarity (highest first)
                home_team_matches.sort(key=lambda x: x[1], reverse=True)
                away_team_matches.sort(key=lambda x: x[1], reverse=True)
                
                # Check if we found matches
                if not home_team_matches:
                    logger.error(f"No match found for home team: {home_team}")
                    if attempt == max_retries - 1:
                        # Show available teams for debugging
                        sample_teams = [team.get("name", "") for team in teams[:10]]
                        logger.info(f"Available teams include: {', '.join(sample_teams)}")
                        return None
                    time.sleep(1)
                    continue
                
                if not away_team_matches:
                    logger.error(f"No match found for away team: {away_team}")
                    if attempt == max_retries - 1:
                        # Show available teams for debugging
                        sample_teams = [team.get("name", "") for team in teams[:10]]
                        logger.info(f"Available teams include: {', '.join(sample_teams)}")
                        return None
                    time.sleep(1)
                    continue
                
                # Get the best matches
                home_team_data, home_similarity = home_team_matches[0]
                away_team_data, away_similarity = away_team_matches[0]
                
                logger.info(f"Home team match: {home_team} -> {home_team_data.get('name')} (similarity: {home_similarity:.2f})")
                logger.info(f"Away team match: {away_team} -> {away_team_data.get('name')} (similarity: {away_similarity:.2f})")
                
                # Step 4: Extract statistics
                home_team_stats = extract_team_stats(home_team_data)
                away_team_stats = extract_team_stats(away_team_data)
                
                # Step 5: Compile fixture statistics
                fixture_stats = {
                    "league": {
                        "id": season_id,
                        "name": selected_league
                    },
                    "teams": {
                        "home": {
                            "id": home_team_data.get("id"),
                            "name": home_team_data.get("name")
                        },
                        "away": {
                            "id": away_team_data.get("id"),
                            "name": away_team_data.get("name")
                        }
                    },
                    "basic_stats": {
                        "home_team": {"name": home_team_data.get("name"), "stats": home_team_stats},
                        "away_team": {"name": away_team_data.get("name"), "stats": away_team_stats},
                        "referee": "Não informado"
                    },
                    "advanced_stats": {
                        "home": extract_advanced_stats(home_team_data),
                        "away": extract_advanced_stats(away_team_data)
                    },
                    "team_form": {
                        "home": extract_team_form(home_team_data),
                        "away": extract_team_form(away_team_data)
                    },
                    "head_to_head": {}
                }
                
                logger.info(f"Successfully compiled fixture statistics for {home_team} vs {away_team}")
                return fixture_stats
                
            except Exception as retry_error:
                logger.error(f"Error during attempt {attempt+1}: {str(retry_error)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
                
        return None
            
    except Exception as e:
        logger.error(f"Error getting fixture statistics: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def extract_team_stats(team_data):
    """Extract statistics from team data with improved robustness"""
    stats = {}
    
    if not team_data or not isinstance(team_data, dict):
        return stats
    
    # Extract basic stats
    basic_stats = [
        "matches_played", "wins", "draws", "losses", 
        "goals_scored", "goals_conceded", "clean_sheets",
        "xg", "xga", "possession", "shots", "shots_on_target"
    ]
    
    # Direct extraction from team_data
    for key in basic_stats:
        if key in team_data:
            stats[key] = team_data[key]
    
    # Extract from nested "stats" object if available
    if "stats" in team_data and isinstance(team_data["stats"], dict):
        for key, value in team_data["stats"].items():
            stats[key] = value
    
    # Handle different API formats with fallbacks
    if "overall" in team_data and isinstance(team_data["overall"], dict):
        for key, value in team_data["overall"].items():
            if key not in stats:
                stats[key] = value
    
    # Calculate derived statistics if enough data is available
    if "wins" in stats and "matches_played" in stats and stats["matches_played"] > 0:
        stats["win_percentage"] = (stats["wins"] / stats["matches_played"]) * 100
        
    if "draws" in stats and "matches_played" in stats and stats["matches_played"] > 0:
        stats["draw_percentage"] = (stats["draws"] / stats["matches_played"]) * 100
    
    if "goals_scored" in stats and "matches_played" in stats and stats["matches_played"] > 0:
        stats["goals_per_game"] = stats["goals_scored"] / stats["matches_played"]
    
    return stats

def extract_advanced_stats(team_data):
    """Extract advanced statistics from team data"""
    stats = {}
    
    if not team_data or not isinstance(team_data, dict):
        return stats
    
    # Look for advanced stats
    advanced_keys = [
        "ppda", "deep_completions", "shot_quality", "xg_per_shot",
        "build_up_disruption", "passes_per_defensive_action"
    ]
    
    for key in advanced_keys:
        if key in team_data:
            stats[key] = team_data[key]
    
    # Check for nested structures
    for nested_key in ["advanced_stats", "detailed_stats"]:
        if nested_key in team_data and isinstance(team_data[nested_key], dict):
            for key, value in team_data[nested_key].items():
                stats[key] = value
    
    return stats

def extract_team_form(team_data):
    """Extract recent form data"""
    form = []
    
    if not team_data or not isinstance(team_data, dict):
        return [{"result": "?"} for _ in range(5)]  # Return 5 placeholders
    
    # Check for form data
    if "form" in team_data and isinstance(team_data["form"], list):
        return team_data["form"][:5]  # Return at most 5 results
    
    # Handle string format like "WDLWD"
    if "recent_form" in team_data:
        recent = team_data["recent_form"]
        if isinstance(recent, str):
            for char in recent[:5]:
                if char in ["W", "D", "L"]:
                    form.append({"result": char})
    
    # Fill with placeholders if needed
    while len(form) < 5:
        form.append({"result": "?"})
    
    return form
def get_head_to_head_stats(home_team, away_team, league_name):
    """Get head-to-head statistics between two teams"""
    # This would normally come from an API call, but we'll create a placeholder
    h2h = {
        "total_matches": 0,
        "home_wins": 0,
        "away_wins": 0,
        "draws": 0,
        "average_goals": 0,
        "over_2_5_percentage": 0,
        "btts_percentage": 0,
        "average_corners": 0,
        "average_cards": 0
    }
    
    return h2h

def extract_stat_value(team_data, stat_key, default=0):
    """Extract a statistic value from team data with proper fallbacks"""
    # Check for stats dictionary
    if "stats" in team_data and isinstance(team_data["stats"], dict):
        if stat_key in team_data["stats"]:
            return team_data["stats"][stat_key]
    
    # Check for direct key in team_data
    if stat_key in team_data:
        return team_data[stat_key]
    
    # Return default value if not found
    return default

def convert_api_stats_to_df_format(fixture_stats):
    """
    Convert fixture statistics from API to DataFrame format
    
    Args:
        fixture_stats (dict): Statistics from get_fixture_statistics()
        
    Returns:
        pandas.DataFrame: DataFrame with team statistics
    """
    import pandas as pd
    
    try:
        # Check if fixture_stats is valid
        if not fixture_stats or not isinstance(fixture_stats, dict):
            logger.error("Dados de estatísticas inválidos")
            return None
            
        # Extract basic information
        home_team_data = fixture_stats.get("home_team", {})
        away_team_data = fixture_stats.get("away_team", {})
        
        if not home_team_data or not away_team_data:
            logger.error("Dados de times inválidos")
            return None
            
        home_team = home_team_data.get("name", "Home")
        away_team = away_team_data.get("name", "Away")
        
        # Create DataFrame with team names
        df = pd.DataFrame({"Squad": [home_team, away_team]})
        
        # Common stats to extract
        stats_mapping = {
            "MP": "matches_played",
            "W": "wins", 
            "D": "draws",
            "L": "losses",
            "Gls": "goals_scored",
            "GA": "goals_conceded",
            "xG": "xg",
            "xGA": "xga",
            "Poss": "possession",
            "Sh": "shots",
            "SoT": "shots_on_target",
            "CrdY": "yellow_cards",
            "CrdR": "red_cards",
            "CK": "corners",
            "Fls": "fouls"
        }
        
        # Extract stats for both teams
        for df_col, api_key in stats_mapping.items():
            # Extract values, defaulting to 0 if not found
            home_val = extract_stat_value(home_team_data, api_key)
            away_val = extract_stat_value(away_team_data, api_key)
            
            # Add to DataFrame
            df[df_col] = [home_val, away_val]
        
        logger.info(f"DataFrame criado com sucesso: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"Erro ao converter estatísticas para DataFrame: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# Funções para buscar utilizando Match IDs

def get_team_detailed_stats(team_id):
    """
    Obtém estatísticas detalhadas de um time específico
    
    Args:
        team_id (int): ID do time
        
    Returns:
        dict: Estatísticas detalhadas do time ou None em caso de erro
    """
    logger.info(f"Buscando estatísticas detalhadas para time ID {team_id}")
    
    try:
        api_url = f"{BASE_URL}/team"
        params = {
            "key": API_KEY,
            "team_id": team_id,
            "include": "stats"
        }
        
        response = requests.get(api_url, params=params, timeout=15)
        if response.status_code != 200:
            logger.error(f"Erro ao buscar estatísticas: status {response.status_code}")
            return None
        
        data = response.json()
        if "data" not in data:
            logger.error("Formato de resposta inválido")
            return None
            
        logger.info(f"Estatísticas detalhadas obtidas com sucesso para time ID {team_id}")
        return data["data"]
    
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas detalhadas: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def get_team_last_matches(team_id, num_matches=5):
    """
    Obtém dados das últimas X partidas de um time
    
    Args:
        team_id (int): ID do time
        num_matches (int): Número de partidas (5, 6 ou 10)
        
    Returns:
        dict: Dados das últimas partidas ou None em caso de erro
    """
    logger.info(f"Buscando últimas {num_matches} partidas para time ID {team_id}")
    
    # Validar num_matches (API só suporta 5, 6 ou 10)
    if num_matches not in [5, 6, 10]:
        num_matches = 5
    
    try:
        api_url = f"{BASE_URL}/lastx"
        params = {
            "key": API_KEY,
            "team_id": team_id,
            "num": num_matches
        }
        
        response = requests.get(api_url, params=params, timeout=15)
        if response.status_code != 200:
            logger.error(f"Erro ao buscar últimas partidas: status {response.status_code}")
            return None
        
        data = response.json()
        if "data" not in data:
            logger.error("Formato de resposta inválido")
            return None
            
        logger.info(f"Últimas {num_matches} partidas obtidas com sucesso para time ID {team_id}")
        return data["data"]
    
    except Exception as e:
        logger.error(f"Erro ao buscar últimas partidas: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def get_match_id_for_teams(home_team_id, away_team_id, league_id):
    """
    Tenta encontrar um match_id para partida entre dois times em uma liga
    
    Args:
        home_team_id (int): ID do time da casa
        away_team_id (int): ID do time visitante
        league_id (int): ID da liga
        
    Returns:
        int: match_id se encontrado, ou None em caso contrário
    """
    logger.info(f"Buscando match_id para times {home_team_id} vs {away_team_id} na liga {league_id}")
    
    try:
        api_url = f"{BASE_URL}/league-matches"
        params = {
            "key": API_KEY,
            "season_id": league_id
        }
        
        response = requests.get(api_url, params=params, timeout=15)
        if response.status_code != 200:
            logger.error(f"Erro ao buscar partidas: status {response.status_code}")
            return None
        
        data = response.json()
        if "data" not in data or not isinstance(data["data"], list):
            logger.error("Formato de resposta inválido")
            return None
        
        matches = data["data"]
        logger.info(f"Encontradas {len(matches)} partidas na liga {league_id}")
        
        # Procurar partida com estes times - usando os campos corretos
        for match in matches:
            if "homeID" in match and "awayID" in match:
                if match["homeID"] == home_team_id and match["awayID"] == away_team_id:
                    logger.info(f"Match ID encontrado: {match.get('id')}")
                    return match.get('id')
        
        logger.warning(f"Nenhum match_id encontrado para times {home_team_id} vs {away_team_id}")
        return None
    
    except Exception as e:
        logger.error(f"Erro ao buscar match_id: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def get_all_matches_for_team(team_id, league_id):
    """
    Obtém todas as partidas de um time em uma liga/temporada
    
    Args:
        team_id (int): ID do time
        league_id (int): ID da liga
        
    Returns:
        list: Lista de partidas do time ou lista vazia em caso de erro
    """
    logger.info(f"Buscando todas as partidas do time {team_id} na liga {league_id}")
    
    try:
        api_url = f"{BASE_URL}/league-matches"
        params = {
            "key": API_KEY,
            "season_id": league_id
        }
        
        response = requests.get(api_url, params=params, timeout=15)
        if response.status_code != 200:
            logger.error(f"Erro ao buscar partidas: status {response.status_code}")
            return []
        
        data = response.json()
        if "data" not in data or not isinstance(data["data"], list):
            logger.error("Formato de resposta inválido")
            return []
        
        matches = data["data"]
        logger.info(f"Processando {len(matches)} partidas na liga {league_id}")
        
        # Filtrar partidas em que o time participou (como mandante ou visitante)
        team_matches = []
        for match in matches:
            if "homeID" in match and "awayID" in match:
                if match["homeID"] == team_id or match["awayID"] == team_id:
                    team_matches.append(match)
        
        logger.info(f"Encontradas {len(team_matches)} partidas para o time {team_id}")
        return team_matches
    
    except Exception as e:
        logger.error(f"Erro ao buscar partidas do time: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def get_match_details(match_id):
    """
    Obtém detalhes completos de uma partida usando o match_id
    
    Args:
        match_id (int): ID da partida
        
    Returns:
        dict: Detalhes da partida ou None em caso de erro
    """
    logger.info(f"Buscando detalhes para partida ID {match_id}")
    
    try:
        api_url = f"{BASE_URL}/match"
        params = {
            "key": API_KEY,
            "match_id": match_id
        }
        
        # Verificar cache
        cache_key = f"match_{match_id}"
        cached_data = get_from_cache(cache_key)
        if cached_data:
            logger.info(f"Usando dados em cache para partida ID {match_id}")
            return cached_data
        
        # Se não há cache, buscar da API
        response = requests.get(api_url, params=params, timeout=15)
        if response.status_code != 200:
            logger.error(f"Erro ao buscar detalhes da partida: status {response.status_code}")
            return None
        
        data = response.json()
        if "data" not in data:
            logger.error("Formato de resposta inválido")
            return None
            
        # Salvar no cache
        save_to_cache(data["data"], cache_key)
        
        logger.info(f"Detalhes obtidos com sucesso para partida ID {match_id}")
        return data["data"]
    
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes da partida: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def get_upcoming_matches(league_id):
    """
    Obtém partidas futuras de uma liga/temporada
    
    Args:
        league_id (int): ID da liga
        
    Returns:
        list: Lista de partidas futuras ou lista vazia em caso de erro
    """
    logger.info(f"Buscando partidas futuras na liga {league_id}")
    
    try:
        api_url = f"{BASE_URL}/league-matches"
        params = {
            "key": API_KEY,
            "season_id": league_id
        }
        
        response = requests.get(api_url, params=params, timeout=15)
        if response.status_code != 200:
            logger.error(f"Erro ao buscar partidas: status {response.status_code}")
            return []
        
        data = response.json()
        if "data" not in data or not isinstance(data["data"], list):
            logger.error("Formato de resposta inválido")
            return []
        
        matches = data["data"]
        
        # Filtrar partidas futuras (status não é "complete")
        upcoming_matches = []
        for match in matches:
            if "status" in match and match["status"] != "complete":
                upcoming_matches.append(match)
        
        logger.info(f"Encontradas {len(upcoming_matches)} partidas futuras na liga {league_id}")
        return upcoming_matches
    
    except Exception as e:
        logger.error(f"Erro ao buscar partidas futuras: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def get_round_matches(league_id, round_id):
    """
    Obtém todas as partidas de uma rodada específica
    
    Args:
        league_id (int): ID da liga
        round_id (int): ID da rodada
        
    Returns:
        list: Lista de partidas da rodada ou lista vazia em caso de erro
    """
    logger.info(f"Buscando partidas da rodada {round_id} na liga {league_id}")
    
    try:
        api_url = f"{BASE_URL}/league-matches"
        params = {
            "key": API_KEY,
            "season_id": league_id
        }
        
        response = requests.get(api_url, params=params, timeout=15)
        if response.status_code != 200:
            logger.error(f"Erro ao buscar partidas: status {response.status_code}")
            return []
        
        data = response.json()
        if "data" not in data or not isinstance(data["data"], list):
            logger.error("Formato de resposta inválido")
            return []
        
        matches = data["data"]
        
        # Filtrar partidas da rodada específica
        round_matches = []
        for match in matches:
            if "roundID" in match and match["roundID"] == round_id:
                round_matches.append(match)
        
        logger.info(f"Encontradas {len(round_matches)} partidas na rodada {round_id}")
        return round_matches
    
    except Exception as e:
        logger.error(f"Erro ao buscar partidas da rodada: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

# Função avançada que combina várias fontes de dados
def get_complete_match_analysis(home_team, away_team, selected_league):
    """
    Realiza uma análise completa de uma partida usando todas as APIs disponíveis
    
    Args:
        home_team (str): Nome do time da casa
        away_team (str): Nome do time visitante
        selected_league (str): Nome da liga
        
    Returns:
        dict: Análise completa com estatísticas, histórico e predicções
    """
    logger.info(f"Iniciando análise completa de {home_team} vs {away_team} na liga {selected_league}")
    
    try:
        # Passo 1: Obter informações básicas e team_ids
        fixture_stats = get_fixture_statistics(home_team, away_team, selected_league)
        if not fixture_stats:
            logger.error("Falha ao obter estatísticas básicas")
            return None
            
        home_team_id = fixture_stats["home_team"]["id"]
        away_team_id = fixture_stats["away_team"]["id"]
        league_id = fixture_stats["league"]["id"]
        
        # Passo 2: Buscar o match_id
        match_id = get_match_id_for_teams(home_team_id, away_team_id, league_id)
        
        # Passo 3: Buscar detalhes do jogo se houver match_id
        match_details = None
        if match_id:
            match_details = get_match_details(match_id)
        
        # Passo 4: Buscar todos os jogos recentes de ambos os times
        home_matches = get_all_matches_for_team(home_team_id, league_id)
        away_matches = get_all_matches_for_team(away_team_id, league_id)
        
        # Passo 5: Buscar estatísticas detalhadas de cada time
        home_detailed = get_team_detailed_stats(home_team_id)
        away_detailed = get_team_detailed_stats(away_team_id)
        
        # Passo 6: Compilar toda a informação
        complete_analysis = {
            "match": {
                "id": match_id,
                "teams": {
                    "home": {
                        "id": home_team_id,
                        "name": fixture_stats["home_team"]["name"],
                        "detailed_stats": home_detailed,
                        "all_matches": home_matches
                    },
                    "away": {
                        "id": away_team_id,
                        "name": fixture_stats["away_team"]["name"],
                        "detailed_stats": away_detailed,
                        "all_matches": away_matches
                    }
                },
                "details": match_details,
                "basic_stats": fixture_stats
            },
            "league": {
                "id": league_id,
                "name": selected_league
            },
            "meta": {
                "analysis_time": datetime.now().isoformat(),
                "api_version": "v1.0"
            }
        }
        
        logger.info(f"Análise completa concluída com sucesso para {home_team} vs {away_team}")
        return complete_analysis
        
    except Exception as e:
        logger.error(f"Erro durante análise completa: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def fetch_stats_data(selected_league, home_team=None, away_team=None):
    """
    Busca estatísticas das equipes com abordagem sequencial completa
    
    Args:
        selected_league (str): Nome da liga
        home_team (str, optional): Nome do time da casa
        away_team (str, optional): Nome do time visitante
        
    Returns:
        tuple: (DataFrame com estatísticas, dados brutos) ou (None, None) em caso de erro
    """
    try:
        with st.spinner("Buscando estatísticas atualizadas..."):
            # Verificar se temos times específicos para buscar
            if home_team and away_team:
                # Abordagem integrada usando a nova API client
                try:
                    from utils.enhanced_api_client import get_complete_match_analysis, convert_to_dataframe_format
                    from utils.league_ids import get_season_id  # Para obter o season_id correto
                    from utils.footystats_api import LEAGUE_SEASONS, CURRENT_SEASON
                    
                    # Obter season_id para a liga selecionada
                    season_id = get_season_id(selected_league)
                    if not season_id:
                        st.error(f"Não foi possível encontrar ID para liga: {selected_league}")
                        return None, None
                    
                    # Mostrar qual temporada estamos usando para feedback ao usuário
                    season = LEAGUE_SEASONS.get(selected_league, CURRENT_SEASON)
                    st.info(f"Buscando estatísticas da temporada {season} para {selected_league}")
                    
                    # Etapa principal - buscar análise completa
                    complete_analysis = get_complete_match_analysis(home_team, away_team, season_id)
                    
                    if complete_analysis:
                        # Converter para o formato de DataFrame esperado pelo restante da aplicação
                        team_stats_df = convert_to_dataframe_format(complete_analysis)
                        
                        if team_stats_df is not None:
                            st.success(f"Estatísticas carregadas com sucesso para {home_team} vs {away_team}")
                            return team_stats_df, complete_analysis
                        else:
                            st.error("Erro ao processar estatísticas para formato DataFrame")
                            return None, None
                    else:
                        st.error("Estatísticas não disponíveis para estes times")
                        st.info("Isso pode ocorrer se os times não fizerem parte da mesma liga ou temporada.")
                        
                        # Mostrar informações adicionais para diagnóstico
                        st.warning("Verificando times disponíveis nesta liga...")
                        from utils.enhanced_api_client import get_teams_for_league
                        teams = get_teams_for_league(season_id)
                        
                        if teams:
                            team_names = [team.get("name", "Unknown") for team in teams[:10]]
                            st.info(f"Times disponíveis incluem: {', '.join(team_names)}")
                            st.info("Use os nomes exatos dos times acima para a análise.")
                        else:
                            st.warning(f"Não foi possível encontrar times para a liga {selected_league}")
                        
                        return None, None
                
                except Exception as api_error:
                    st.error(f"Erro ao obter estatísticas da API: {str(api_error)}")
                    logger.error(f"Erro na API de estatísticas: {str(api_error)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return None, None
            else:
                st.error("É necessário selecionar dois times para análise.")
                return None, None
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {str(e)}")
        st.error(f"Erro ao buscar estatísticas: {str(e)}")
        return None, None
