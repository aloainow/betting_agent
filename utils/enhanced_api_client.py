import requests
import logging
import time
import json
import os
from datetime import datetime

# Configuração de logging
logger = logging.getLogger("valueHunter.api_client")

# Configuração da API
API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"
BASE_URL = "https://api.football-data-api.com"

# Diretório para armazenar cache
from utils.core import DATA_DIR
CACHE_DIR = os.path.join(DATA_DIR, "api_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def api_request(endpoint, params, use_cache=True, cache_duration=3600):
    """
    Função robusta para fazer requisições à API com cache e tratamento de erros
    
    Args:
        endpoint (str): Endpoint da API (ex: 'league-teams')
        params (dict): Parâmetros da requisição
        use_cache (bool): Se deve usar cache
        cache_duration (int): Duração do cache em segundos
        
    Returns:
        dict: Dados da resposta ou None se ocorrer erro
    """
    # Garantir que key está nos parâmetros
    if "key" not in params:
        params["key"] = API_KEY
    
    # Criar nome do arquivo de cache
    cache_key = f"{endpoint}_"
    for k, v in sorted(params.items()):
        if k != "key":  # Não incluir a key no nome do arquivo
            cache_key += f"{k}_{v}_"
    cache_key = cache_key.rstrip("_")
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    # Verificar cache
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            # Verificar se o cache ainda é válido
            if time.time() - cache_data["timestamp"] < cache_duration:
                logger.info(f"Usando dados em cache para {endpoint}")
                return cache_data["data"]
        except Exception as e:
            logger.error(f"Erro ao ler cache: {str(e)}")
    
    # Se não há cache válido, fazer requisição à API
    url = f"{BASE_URL}/{endpoint}"
    logger.info(f"Fazendo requisição para {url} com parâmetros: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        # Verificar resposta
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Salvar no cache
                if use_cache:
                    try:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump({
                                "timestamp": time.time(),
                                "data": data
                            }, f)
                    except Exception as e:
                        logger.error(f"Erro ao salvar cache: {str(e)}")
                
                return data
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON da resposta: {response.text[:200]}")
                return None
        else:
            logger.error(f"Erro na requisição: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"Erro ao fazer requisição: {str(e)}")
        return None

def get_teams_for_league(season_id, force_refresh=False):
    """
    Obtém todos os times de uma liga com suas estatísticas básicas
    
    Args:
        season_id (int): ID da temporada/liga
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        list: Lista de times com suas estatísticas ou lista vazia em caso de erro
    """
    params = {
        "season_id": season_id,
        "include": "stats"
    }
    
    response = api_request("league-teams", params, use_cache=not force_refresh)
    
    if response and "data" in response and isinstance(response["data"], list):
        teams = response["data"]
        logger.info(f"Encontrados {len(teams)} times para season_id {season_id}")
        return teams
    
    logger.error(f"Falha ao obter times para season_id {season_id}")
    return []

def get_league_table(season_id, force_refresh=False):
    """
    Obtém a tabela de classificação de uma liga
    
    Args:
        season_id (int): ID da temporada/liga
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        dict: Dados da tabela de classificação ou None em caso de erro
    """
    params = {
        "season_id": season_id
    }
    
    response = api_request("league-tables", params, use_cache=not force_refresh)
    
    if response and "data" in response:
        league_table = response["data"]
        logger.info(f"Tabela de classificação obtida para season_id {season_id}")
        return league_table
    
    logger.error(f"Falha ao obter tabela de classificação para season_id {season_id}")
    return None

def get_team_last_matches(team_id, num_matches=5, force_refresh=False):
    """
    Obtém os últimos X jogos de um time
    
    Args:
        team_id (int): ID do time
        num_matches (int): Número de jogos (5, 6 ou 10)
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        dict: Dados dos últimos jogos ou None em caso de erro
    """
    # Validar num_matches (API só suporta 5, 6 ou 10)
    if num_matches not in [5, 6, 10]:
        num_matches = 5
    
    params = {
        "team_id": team_id,
        "num": num_matches
    }
    
    response = api_request("lastx", params, use_cache=not force_refresh)
    
    if response and "data" in response:
        last_matches = response["data"]
        logger.info(f"Últimos {num_matches} jogos obtidos para team_id {team_id}")
        return last_matches
    
    logger.error(f"Falha ao obter últimos jogos para team_id {team_id}")
    return None

def find_match_id(home_team_id, away_team_id, season_id, force_refresh=False):
    """
    Encontra o ID de um jogo entre dois times em uma liga
    
    Args:
        home_team_id (int): ID do time da casa
        away_team_id (int): ID do time visitante
        season_id (int): ID da temporada/liga
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        int: ID do jogo ou None se não encontrado
    """
    params = {
        "season_id": season_id
    }
    
    response = api_request("league-matches", params, use_cache=not force_refresh)
    
    if response and "data" in response and isinstance(response["data"], list):
        matches = response["data"]
        logger.info(f"Encontrados {len(matches)} jogos para season_id {season_id}")
        
        # Procurar jogo com estes times
        for match in matches:
            if "homeID" in match and "awayID" in match:
                if match["homeID"] == home_team_id and match["awayID"] == away_team_id:
                    # Verificar se o jogo ainda não aconteceu (status não é "complete")
                    if "status" in match and match["status"] != "complete":
                        logger.info(f"Encontrado jogo futuro: ID {match.get('id')}")
                        return match.get("id")
        
        # Se não encontrou jogo futuro, verificar jogos passados
        for match in matches:
            if "homeID" in match and "awayID" in match:
                if match["homeID"] == home_team_id and match["awayID"] == away_team_id:
                    logger.info(f"Encontrado jogo passado: ID {match.get('id')}")
                    return match.get("id")
        
        logger.warning(f"Nenhum jogo encontrado entre times {home_team_id} e {away_team_id}")
    else:
        logger.error(f"Falha ao buscar jogos para season_id {season_id}")
    
    return None

def get_match_details(match_id, force_refresh=False):
    """
    Obtém detalhes de um jogo específico
    
    Args:
        match_id (int): ID do jogo
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        dict: Detalhes do jogo ou None em caso de erro
    """
    params = {
        "match_id": match_id
    }
    
    response = api_request("match", params, use_cache=not force_refresh)
    
    if response and "data" in response:
        match_details = response["data"]
        logger.info(f"Detalhes obtidos para match_id {match_id}")
        return match_details
    
    logger.error(f"Falha ao obter detalhes para match_id {match_id}")
    return None

def get_complete_match_analysis(home_team, away_team, season_id, force_refresh=False):
    """
    Função principal que obtém todos os dados necessários para análise de um jogo
    
    Args:
        home_team (str): Nome do time da casa
        away_team (str): Nome do time visitante
        season_id (int): ID da temporada/liga
        force_refresh (bool): Se True, ignora o cache
        
    Returns:
        dict: Análise completa com todas as estatísticas ou None em caso de erro
    """
    logger.info(f"Iniciando análise completa para {home_team} vs {away_team} na liga {season_id}")
    
    try:
        # Passo 1: Obter todos os times da liga com estatísticas básicas
        teams = get_teams_for_league(season_id, force_refresh)
        if not teams:
            logger.error(f"Não foi possível obter times para a liga {season_id}")
            return None
        
        # Encontrar os times específicos
        home_team_data = None
        away_team_data = None
        
        for team in teams:
            if "name" in team and team["name"] == home_team:
                home_team_data = team
            if "name" in team and team["name"] == away_team:
                away_team_data = team
        
        if not home_team_data:
            logger.error(f"Time da casa '{home_team}' não encontrado na liga {season_id}")
            return None
        
        if not away_team_data:
            logger.error(f"Time visitante '{away_team}' não encontrado na liga {season_id}")
            return None
        
        home_team_id = home_team_data["id"]
        away_team_id = away_team_data["id"]
        
        logger.info(f"Times encontrados: {home_team} (ID: {home_team_id}) vs {away_team} (ID: {away_team_id})")
        
        # Passo 2: Obter tabela de classificação
        league_table = get_league_table(season_id, force_refresh)
        
        # Passo 3: Obter últimos jogos de ambos os times
        home_last_matches = get_team_last_matches(home_team_id, 5, force_refresh)
        away_last_matches = get_team_last_matches(away_team_id, 5, force_refresh)
        
        # Passo 4: Encontrar match_id e obter detalhes do confronto direto
        match_id = find_match_id(home_team_id, away_team_id, season_id, force_refresh)
        match_details = None
        if match_id:
            match_details = get_match_details(match_id, force_refresh)
        
        # Compilar todos os dados
        complete_analysis = {
            "basic_stats": {
                "league_id": season_id,
                "home_team": {"name": home_team, "stats": home_team_data},
                "away_team": {"name": away_team, "stats": away_team_data},
                "referee": match_details.get("referee", "Não informado") if match_details else "Não informado"
            },
            "league_table": league_table,
            "team_form": {
                "home": home_last_matches,
                "away": away_last_matches
            },
            "head_to_head": match_details.get("h2h", {}) if match_details else {},
            "match_details": match_details,
            "advanced_stats": {
                "home": extract_advanced_stats(home_team_data),
                "away": extract_advanced_stats(away_team_data)
            }
        }
        
        logger.info(f"Análise completa concluída para {home_team} vs {away_team}")
        return complete_analysis
    
    except Exception as e:
        logger.error(f"Erro durante análise completa: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def extract_advanced_stats(team_data):
    """
    Extrai estatísticas avançadas dos dados do time
    
    Args:
        team_data (dict): Dados do time
        
    Returns:
        dict: Estatísticas avançadas
    """
    advanced_stats = {}
    
    if not team_data or not isinstance(team_data, dict):
        return advanced_stats
    
    # Estatísticas avançadas potencialmente úteis
    metrics = [
        "ppda", "deep_completions", "shot_quality", "xg_per_shot",
        "build_up_disruption", "possessionAVG_overall", "winPercentage_overall",
        "drawPercentage_overall", "losePercentage_overall", "seasonCSPercentage_overall",
        "seasonFTSPercentage_overall", "seasonBTTSPercentage_overall"
    ]
    
    # Extrair do objeto "stats" se existir
    if "stats" in team_data and isinstance(team_data["stats"], dict):
        for metric in metrics:
            if metric in team_data["stats"]:
                advanced_stats[metric] = team_data["stats"][metric]
    
    # Extrair diretamente do team_data
    for metric in metrics:
        if metric in team_data and metric not in advanced_stats:
            advanced_stats[metric] = team_data[metric]
    
    return advanced_stats

def convert_to_dataframe_format(complete_analysis):
    """
    Converte a análise completa para o formato de DataFrame esperado pela função format_prompt
    
    Args:
        complete_analysis (dict): Análise completa obtida por get_complete_match_analysis
        
    Returns:
        pandas.DataFrame: DataFrame com as estatísticas no formato esperado
    """
    import pandas as pd
    
    # Verificar se a análise é válida
    if not complete_analysis or not isinstance(complete_analysis, dict):
        logger.error("Análise inválida para conversão")
        return None
    
    try:
        # Extrair dados básicos
        home_team = complete_analysis["basic_stats"]["home_team"]["name"]
        away_team = complete_analysis["basic_stats"]["away_team"]["name"]
        
        # Extrair estatísticas
        home_stats = complete_analysis["basic_stats"]["home_team"]["stats"]
        away_stats = complete_analysis["basic_stats"]["away_team"]["stats"]
        
        # Criar DataFrame
        df = pd.DataFrame({
            'Squad': [home_team, away_team]
        })
        
        # Definir mapeamento de campos
        field_mapping = {
            'MP': ('seasonMatchesPlayed_overall', 'matches_played'),
            'W': ('seasonWinsNum_overall', 'wins'),
            'D': ('seasonDrawsNum_overall', 'draws'),
            'L': ('seasonLossesNum_overall', 'losses'),
            'Gls': ('seasonGoals_overall', 'goals_scored'),
            'GA': ('seasonConceded_overall', 'goals_conceded'),
            'xG': ('xg_for_overall', 'xg'),
            'xGA': ('xg_against_avg_overall', 'xga'),
            'Poss': ('possessionAVG_overall', 'possession'),
            'Sh': ('shotsAVG_overall', 'shots'),
            'SoT': ('shotsOnTargetAVG_overall', 'shots_on_target'),
            'CrdY': ('cards_for_avg_overall', 'yellow_cards'),
            'CrdR': ('seasonCrdRNum_overall', 'red_cards'),
            'CK': ('cornersAVG_overall', 'corners')
        }
        
        # Preencher DataFrame com estatísticas
        for df_col, api_fields in field_mapping.items():
            home_val = None
            away_val = None
            
            # Tentar encontrar valores usando múltiplos campos
            for field in api_fields:
                # Para home team
                if home_val is None:
                    if isinstance(home_stats, dict) and field in home_stats:
                        home_val = home_stats[field]
                    elif "stats" in home_stats and isinstance(home_stats["stats"], dict) and field in home_stats["stats"]:
                        home_val = home_stats["stats"][field]
                
                # Para away team
                if away_val is None:
                    if isinstance(away_stats, dict) and field in away_stats:
                        away_val = away_stats[field]
                    elif "stats" in away_stats and isinstance(away_stats["stats"], dict) and field in away_stats["stats"]:
                        away_val = away_stats["stats"][field]
            
            # Usar valores default se não encontrados
            if home_val is None:
                home_val = 0
            if away_val is None:
                away_val = 0
            
            # Adicionar ao DataFrame
            df[df_col] = [home_val, away_val]
        
        logger.info(f"DataFrame criado com sucesso. Shape: {df.shape}")
        return df
    
    except Exception as e:
        logger.error(f"Erro ao converter para DataFrame: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
