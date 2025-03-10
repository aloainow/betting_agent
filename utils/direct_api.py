# utils/direct_api.py
"""
Funções otimizadas para buscar times diretamente usando os season_ids exatos.
"""
import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta

# Configuração de logging
logger = logging.getLogger("valueHunter.direct_api")

# Referência à variável global do diretório de dados
from utils.core import DATA_DIR

# Import do mapeamento de IDs
from utils.league_ids import get_season_id

# Configuração da API
API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"
BASE_URL = "https://api.football-data-api.com"

def get_teams_direct(league_name, force_refresh=False):
    """
    Busca times diretamente usando o season_id específico para a liga.
    
    Args:
        league_name (str): Nome da liga
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        list: Lista com os nomes dos times
    """
    # Obter o season_id para a liga
    season_id = get_season_id(league_name)
    
    if not season_id:
        logger.error(f"Não foi possível encontrar season_id para liga: {league_name}")
        return []
    
    # Verificar cache
    cache_dir = os.path.join(DATA_DIR, "teams_cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Nome do arquivo de cache usando o nome da liga e season_id para garantir unicidade
    safe_league = league_name.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
    cache_file = os.path.join(cache_dir, f"{safe_league}_{season_id}.json")
    
    # Verificar cache, a menos que force_refresh seja True
    if not force_refresh and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verificar se o cache não é muito antigo (1 dia)
            if "timestamp" in cache_data:
                cache_time = datetime.fromtimestamp(cache_data["timestamp"])
                if datetime.now() - cache_time < timedelta(days=1):
                    logger.info(f"Usando times em cache para '{league_name}' (ID: {season_id})")
                    return cache_data.get("teams", [])
                else:
                    logger.info(f"Cache expirado para '{league_name}', buscando novamente")
            else:
                logger.info(f"Cache sem timestamp para '{league_name}', buscando novamente")
        except Exception as e:
            logger.error(f"Erro ao ler cache: {str(e)}")
    
    # Buscar times diretamente da API
    logger.info(f"Buscando times para liga '{league_name}' com season_id: {season_id}")
    
    try:
        # Realizar a requisição
        response = requests.get(
            f"{BASE_URL}/league-teams", 
            params={
                "key": API_KEY,
                "season_id": season_id,
                "include": "stats"
            },
            timeout=15
        )
        
        # Verificar resposta
        if response.status_code != 200:
            logger.error(f"Erro ao buscar times: status {response.status_code}")
            try:
                error_data = response.json()
                if "message" in error_data:
                    logger.error(f"Mensagem da API: {error_data['message']}")
            except:
                pass
            return []
        
        # Processar a resposta
        data = response.json()
        
        if "data" not in data or not isinstance(data["data"], list):
            logger.error("Formato de resposta inválido")
            return []
        
        # Extrair nomes dos times
        teams = data["data"]
        team_names = []
        
        for team in teams:
            if "name" in team:
                team_names.append(team["name"])
        
        # Salvar no cache
        if team_names:
            try:
                cache_data = {
                    "teams": team_names,
                    "timestamp": time.time(),
                    "season_id": season_id,
                    "league": league_name
                }
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f)
                
                logger.info(f"Salvos {len(team_names)} times no cache para {league_name}")
            except Exception as e:
                logger.error(f"Erro ao salvar cache: {str(e)}")
        
        logger.info(f"Encontrados {len(team_names)} times para '{league_name}'")
        return team_names
        
    except Exception as e:
        import traceback
        logger.error(f"Erro ao buscar times para {league_name}: {str(e)}")
        logger.error(traceback.format_exc())
        return []
