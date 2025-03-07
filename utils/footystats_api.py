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
    Testa a conexão com a API e diagnóstica problemas.
    Não usa chave de exemplo para testes.
    
    Returns:
        dict: Resultado do teste com informações detalhadas
    """
    try:
        logger.info("Testando conexão com a API FootyStats...")
        result = {
            "success": False,
            "details": [],
            "available_leagues": [],
            "error": None
        }
        
        # Tentar obter ligas disponíveis com sua chave real
        logger.info("Verificando ligas disponíveis para sua chave")
        try:
            params = {"key": API_KEY}
            response = requests.get(f"{BASE_URL}/league-list", params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data and "data" in data and len(data["data"]) > 0:
                        leagues = data["data"]
                        result["success"] = True
                        result["details"].append(f"✓ Sua conta tem acesso a {len(leagues)} ligas")
                        
                        # Armazenar nomes das ligas disponíveis
                        available_leagues = []
                        for league in leagues:
                            name = league.get("name", "")
                            country = league.get("country", "")
                            if name:
                                formatted_name = f"{name} ({country})" if country else name
                                available_leagues.append(formatted_name)
                                
                        result["available_leagues"] = available_leagues
                        if available_leagues:
                            result["details"].append(f"✓ Ligas disponíveis: {', '.join(available_leagues[:5])}{'...' if len(available_leagues) > 5 else ''}")
                        
                        # Verificar se Brasileirão está na lista
                        has_brasileirao = any("brasileir" in league.lower() or 
                                             ("serie a" in league.lower() and "brazil" in league.lower()) 
                                             for league in available_leagues)
                        if has_brasileirao:
                            result["details"].append("✓ Brasileirão está disponível na sua conta")
                        else:
                            result["details"].append("✗ Brasileirão NÃO está disponível na sua conta")
                            
                    else:
                        result["details"].append("✗ Nenhuma liga disponível para sua conta")
                        result["error"] = "Sua conta não tem acesso a nenhuma liga. Verifique sua assinatura."
                except json.JSONDecodeError:
                    result["details"].append("✗ API retornou resposta inválida ao verificar ligas")
            else:
                result["details"].append(f"✗ API retornou código {response.status_code} ao verificar ligas")
                if response.status_code == 401:
                    result["error"] = "Chave de API inválida ou expirada"
                else:
                    result["error"] = f"Erro ao acessar API: código {response.status_code}"
        except Exception as e:
            result["details"].append(f"✗ Erro ao verificar ligas: {str(e)}")
            result["error"] = f"Erro de conexão: {str(e)}"
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Erro ao testar conexão com API: {str(e)}")
        return {
            "success": False,
            "details": [f"✗ Erro global no teste: {str(e)}"],
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

def fetch_league_teams(league_id):
    """
    Buscar times de uma liga específica.
    Sem fallbacks ou dados de exemplo.
    
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
    
    # Se não encontramos times, verificar o erro
    if data and isinstance(data, dict) and "message" in data:
        error_msg = data.get("message", "")
        logger.warning(f"Erro ao buscar times: {error_msg}")
        
        # Verificar por mensagem específica de liga não selecionada
        if "League is not chosen by the user" in error_msg:
            logger.error(f"A liga (ID {league_id}) não está selecionada na sua conta FootyStats")
            
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
    # Obter mapeamento atualizado de ligas
    league_mapping = get_league_id_mapping()
    
    # Caso 1: Nome exato
    if league_name in league_mapping:
        logger.info(f"ID encontrado para '{league_name}': {league_mapping[league_name]}")
        return league_mapping[league_name]
    
    # Caso 2: Correspondência parcial
    for name, league_id in league_mapping.items():
        if league_name.lower() in name.lower() or name.lower() in league_name.lower():
            logger.info(f"ID encontrado para '{league_name}' via correspondência parcial com '{name}': {league_id}")
            return league_id
    
    # Caso 3: Buscar na lista de ligas disponíveis
    try:
        api_test = test_api_connection()
        if api_test["success"] and api_test["available_leagues"]:
            for league in api_test["available_leagues"]:
                if league_name.lower() in league.lower() or league.lower() in league_name.lower():
                    # Tentar encontrar o ID para esta liga
                    for name, league_id in league_mapping.items():
                        if league.lower() in name.lower() or name.lower() in league.lower():
                            logger.info(f"ID encontrado para '{league_name}' via liga similar '{league}': {league_id}")
                            return league_id
    except Exception as e:
        logger.error(f"Erro ao buscar liga similar: {str(e)}")
    
    # Não encontrado
    logger.error(f"ID não encontrado para liga: '{league_name}'")
    return None

def get_team_names_by_league(league_name, force_refresh=False):
    """
    Obter nomes dos times de uma liga
    
    Args:
        league_name (str): Nome da liga
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        list: Lista de nomes dos times
    """
    logger.info(f"Buscando times para liga: {league_name}")
    
    # Verificar cache, a menos que force_refresh seja True
    cache_key = f"teams_{league_name}"
    if not force_refresh:
        cached_names = get_from_cache(cache_key)
        if cached_names:
            logger.info(f"Usando times em cache para '{league_name}': {len(cached_names)} times")
            return cached_names
    
    # Buscar ID da liga com o mapeamento atualizado
    league_id = find_league_id_by_name(league_name)
    
    if not league_id:
        # Verificar se existe uma liga similar no teste da API
        try:
            api_test = test_api_connection()
            if api_test["success"] and api_test["available_leagues"]:
                similar_leagues = []
                for league in api_test["available_leagues"]:
                    # Comparar os nomes das ligas ignorando case
                    league_base_name = league_name.split(" (")[0].lower() if " (" in league_name else league_name.lower()
                    api_league_base_name = league.split(" (")[0].lower() if " (" in league else league.lower()
                    
                    # Verificar se há sobreposição entre os nomes
                    if league_base_name in api_league_base_name or api_league_base_name in league_base_name:
                        similar_leagues.append(league)
                        # Tentar usar o primeiro similar que encontrar
                        new_id = find_league_id_by_name(league)
                        if new_id:
                            logger.info(f"Usando ID de liga similar '{league}': {new_id}")
                            league_id = new_id
                            break
                
                if similar_leagues:
                    logger.info(f"Ligas similares encontradas: {similar_leagues}")
        except Exception as e:
            logger.error(f"Erro ao buscar ligas similares: {str(e)}")
    
    if not league_id:
        logger.error(f"Não foi possível encontrar ID para a liga: {league_name}")
        return []
    
    # Buscar times da API
    logger.info(f"Buscando times para liga ID {league_id}")
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
            logger.info(f"Times obtidos para '{league_name}': {len(team_names)} times")
            return team_names
    
    # Se chegamos aqui, não encontramos times
    logger.warning(f"Nenhum time encontrado para liga '{league_name}' (ID: {league_id})")
    return []


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
