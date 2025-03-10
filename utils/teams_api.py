# utils/teams_api.py - Funções otimizadas para acessar times das temporadas atuais
import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta

# Configuração de logging
logger = logging.getLogger("valueHunter.teams_api")

# Referência à variável global do diretório de dados
from utils.core import DATA_DIR

def get_teams_for_current_season(league_name, force_refresh=False):
    """
    Obtém os times de uma liga APENAS da temporada atual (2024-2025 ou 2025).
    
    Args:
        league_name (str): Nome da liga selecionada no dropdown
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        list: Lista de nomes dos times da temporada atual
    """
    # Criar diretório de cache se não existir
    cache_dir = os.path.join(DATA_DIR, "teams_cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # API Configuration
    API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"
    BASE_URL = "https://api.football-data-api.com"
    
    # Gerar nome de arquivo para cache com indicação de temporada
    safe_league = league_name.replace(' ', '_').replace('/', '_').replace('\\', '_').replace('(', '').replace(')', '')
    cache_file = os.path.join(cache_dir, f"{safe_league}_current_season.json")
    
    # Verificar cache, a menos que force_refresh seja True
    if not force_refresh and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # Verificar se o cache não é muito antigo (1 dia)
            if "timestamp" in cache_data:
                cache_time = datetime.fromtimestamp(cache_data["timestamp"])
                if datetime.now() - cache_time < timedelta(days=1):
                    logger.info(f"Usando times em cache para '{league_name}' (temporada atual)")
                    return cache_data.get("teams", [])
                else:
                    logger.info(f"Cache expirado para '{league_name}', buscando novamente")
            else:
                logger.info(f"Cache sem timestamp para '{league_name}', buscando novamente")
        except Exception as e:
            logger.error(f"Erro ao ler cache: {str(e)}")
    
    try:
        # PASSO 1: Buscar a lista completa de ligas/temporadas disponíveis
        logger.info(f"Buscando temporada atual para {league_name}...")
        
        response = requests.get(
            f"{BASE_URL}/league-list", 
            params={"key": API_KEY},
            timeout=15
        )
        
        if response.status_code != 200:
            logger.error(f"Erro ao buscar lista de ligas: {response.status_code}")
            return []
        
        data = response.json()
        
        if "data" not in data or not isinstance(data["data"], list):
            logger.error(f"Formato de resposta inválido: {data}")
            return []
        
        # PASSO 2: Filtrar para encontrar a liga na temporada ATUAL
        current_season_id = None
        current_season_info = None
        matching_leagues = []
        
        # Converter nome da liga para lowercase para comparação
        league_name_lower = league_name.lower()
        # Remover parte do país se existir
        if "(" in league_name_lower:
            league_name_base = league_name_lower.split("(")[0].strip()
        else:
            league_name_base = league_name_lower
        
        for league in data["data"]:
            # Obter dados básicos da liga
            api_league_name = league.get("name", "").lower()
            api_league_id = league.get("id")
            api_country = league.get("country", "").lower()
            
            # Verificar correspondência do nome (com ou sem país)
            name_match = (
                league_name_lower == f"{api_league_name} ({api_country})" or
                league_name_base == api_league_name or
                league_name_lower in api_league_name or
                api_league_name in league_name_base
            )
            
            if name_match:
                # Obter informações da temporada
                season_data = None
                season_year = None
                
                # Verificar diferentes formatos de temporada
                if "season" in league:
                    season_data = league["season"]
                    
                    # Pode ser uma string simples "2024-2025" ou um objeto complexo
                    if isinstance(season_data, str):
                        season_year = season_data
                    elif isinstance(season_data, dict) and "year" in season_data:
                        season_year = season_data["year"]
                
                # Verificar se é temporada atual (2024-2025 ou 2025)
                is_current = False
                if season_year:
                    # Para ligas europeias (2024-2025)
                    if isinstance(season_year, str) and ("-" in season_year or "/" in season_year):
                        delimiter = "-" if "-" in season_year else "/"
                        first_year = season_year.split(delimiter)[0].strip()
                        is_current = first_year == "2024"
                    # Para ligas sul-americanas (2025)
                    elif str(season_year) == "2025":
                        is_current = True
                
                # Adicionar à lista de ligas correspondentes
                matching_leagues.append({
                    "id": api_league_id,
                    "name": league.get("name"),
                    "country": league.get("country"),
                    "season_year": season_year,
                    "is_current": is_current
                })
                
                # Se for temporada atual, já salvamos o ID
                if is_current:
                    current_season_id = api_league_id
                    current_season_info = f"{league.get('name')} ({league.get('country')}): {season_year}"
                    logger.info(f"Encontrada temporada atual: {current_season_info}")
        
        # Se não encontramos a temporada atual, usar a primeira correspondência
        if not current_season_id and matching_leagues:
            current_season_id = matching_leagues[0]["id"]
            current_season_info = f"{matching_leagues[0]['name']} ({matching_leagues[0]['country']}): {matching_leagues[0]['season_year']}"
            logger.warning(f"Temporada atual não encontrada. Usando: {current_season_info}")
        
        # Se não encontrou nenhuma correspondência
        if not current_season_id:
            logger.error(f"Nenhuma temporada encontrada para {league_name}")
            return []
        
        # PASSO 3: Buscar os times da temporada identificada
        logger.info(f"Buscando times com season_id: {current_season_id}")
        
        teams_response = requests.get(
            f"{BASE_URL}/league-teams", 
            params={
                "key": API_KEY,
                "season_id": current_season_id,
                "include": "stats"
            },
            timeout=15
        )
        
        if teams_response.status_code != 200:
            logger.error(f"Erro ao buscar times: {teams_response.status_code}")
            return []
        
        teams_data = teams_response.json()
        
        if "data" not in teams_data or not isinstance(teams_data["data"], list):
            logger.error(f"Formato inválido na resposta de times: {teams_data}")
            return []
        
        # Extrair nomes dos times
        team_names = []
        for team in teams_data["data"]:
            if "name" in team:
                team_names.append(team["name"])
        
        # Salvar no cache
        if team_names:
            try:
                cache_data = {
                    "teams": team_names,
                    "timestamp": time.time(),
                    "season_info": current_season_info
                }
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f)
                
                logger.info(f"Salvos {len(team_names)} times no cache para {league_name}")
            except Exception as e:
                logger.error(f"Erro ao salvar cache: {str(e)}")
        
        logger.info(f"Retornando {len(team_names)} times para {league_name}")
        return team_names
    
    except Exception as e:
        import traceback
        logger.error(f"Erro ao buscar times para {league_name}: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def diagnose_league_season_structure(league_name=None):
    """
    Função de diagnóstico que mostra a estrutura exata do JSON da API
    para ajudar a entender o formato dos dados de temporada.
    
    Args:
        league_name (str, optional): Nome da liga para filtrar a análise
        
    Returns:
        dict: Informações de diagnóstico
    """
    API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"
    BASE_URL = "https://api.football-data-api.com"
    
    try:
        # Obter lista completa de ligas
        response = requests.get(
            f"{BASE_URL}/league-list", 
            params={"key": API_KEY},
            timeout=15
        )
        
        if response.status_code != 200:
            return {"error": f"Erro na requisição: {response.status_code}"}
        
        data = response.json()
        
        if "data" not in data or not isinstance(data["data"], list):
            return {"error": "Formato de resposta inválido"}
        
        leagues = data["data"]
        
        # Filtrar por liga específica se solicitado
        if league_name:
            league_name_lower = league_name.lower()
            filtered_leagues = []
            
            for league in leagues:
                league_api_name = league.get("name", "").lower()
                league_api_country = league.get("country", "").lower()
                
                if (league_name_lower in league_api_name or 
                    league_api_name in league_name_lower or
                    league_name_lower == f"{league_api_name} ({league_api_country})"):
                    filtered_leagues.append(league)
            
            leagues = filtered_leagues
        
        # Limitar a análise às primeiras 10 ligas para não sobrecarregar
        leagues = leagues[:10]
        
        # Analisar estrutura de temporada
        season_formats = []
        for league in leagues:
            if "season" in league:
                league_info = {
                    "name": league.get("name"),
                    "country": league.get("country"),
                    "id": league.get("id"),
                    "season_type": type(league["season"]).__name__,
                    "season_raw": league["season"]
                }
                
                # Extrair ano da temporada
                season_year = None
                if isinstance(league["season"], dict) and "year" in league["season"]:
                    season_year = league["season"]["year"]
                elif isinstance(league["season"], str):
                    season_year = league["season"]
                
                league_info["season_year"] = season_year
                season_formats.append(league_info)
        
        return {
            "total_leagues": len(data["data"]),
            "analyzed_leagues": len(season_formats),
            "season_structures": season_formats
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Erro no diagnóstico: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e), "traceback": traceback.format_exc()}
