# utils/league_ids.py
"""
Mapeamento manual das ligas para seus IDs de temporada específicos.
"""

# Mapeamento das ligas e seus IDs de temporada exatos
SEASON_IDS = {
    # Ligas Sul-Americanas
    "Primera División (Argentina)": 14125,
    "Argentina Primera División": 14125,
    
    "Serie A (Brazil)": 14231,
    "Brazil Serie A": 14231,
    "Brasileirão": 14231,  # Nome alternativo comum
    
    "Serie B (Brazil)": 14305,
    "Brazil Serie B": 14305,
    "Brasileirão Série B": 14305,  # Nome alternativo comum
    
    "Copa do Brasil": 14210,
    "Brazil Copa do Brasil": 14210,
    
    "Primera División (Uruguay)": 14128,
    "Uruguay Primera División": 14128,
    
    "Copa Libertadores": 13974,
    "South America Copa Libertadores": 13974,
    
    "Copa Sudamericana": 13965,
    "South America Copa Sudamericana": 13965,
    
    # Ligas Europeias - Top 5
    "Premier League": 12325,
    "Premier League (England)": 12325,
    "England Premier League": 12325,
    
    "La Liga": 12316,
    "La Liga (Spain)": 12316,
    "Spain La Liga": 12316,
    
    "Segunda División": 12467,
    "Segunda División (Spain)": 12467,
    "Spain Segunda División": 12467,
    
    "Bundesliga": 12529,
    "Bundesliga (Germany)": 12529,
    "Germany Bundesliga": 12529,
    
    "2. Bundesliga": 12528,
    "2. Bundesliga (Germany)": 12528,
    "Germany 2. Bundesliga": 12528,
    
    "Serie A (Italy)": 12530,
    "Italy Serie A": 12530,
    
    "Serie B (Italy)": 12621,
    "Italy Serie B": 12621,
    
    "Ligue 1": 12337,
    "Ligue 1 (France)": 12337,
    "France Ligue 1": 12337,
    
    "Ligue 2": 12338,
    "Ligue 2 (France)": 12338,
    "France Ligue 2": 12338,
    
    # Outras Ligas Europeias
    "Bundesliga (Austria)": 12472,
    "Austria Bundesliga": 12472,
    
    "Pro League": 12137,
    "Pro League (Belgium)": 12137,
    "Belgium Pro League": 12137,
    
    "Eredivisie": 12322,
    "Eredivisie (Netherlands)": 12322,
    "Netherlands Eredivisie": 12322,
    
    "Liga NOS": 12931,
    "Liga NOS (Portugal)": 12931,
    "Portugal Liga NOS": 12931,
    "Primeira Liga": 12931,  # Nome alternativo comum
    
    # Competições Europeias
    "Champions League": 12321,
    "Champions League (Europe)": 12321,
    "UEFA Champions League": 12321,
    
    "Europa League": 12327,
    "Europa League (Europe)": 12327,
    "UEFA Europa League": 12327,
    
    # Outras Ligas
    "Liga MX": 12136,
    "Liga MX (Mexico)": 12136,
    "Mexico Liga MX": 12136,
    
    # Outras competições inglesas
    "FA Cup": 13698,
    "FA Cup (England)": 13698,
    "England FA Cup": 13698,
    
    "EFL League One": 12446,
    "EFL League One (England)": 12446,
    "England EFL League One": 12446
}

def get_season_id(league_name):
    """
    Obtém o ID da temporada para uma liga específica.
    
    Args:
        league_name (str): Nome da liga
        
    Returns:
        int: ID da temporada ou None se não encontrado
    """
    # Verificar correspondência exata
    if league_name in SEASON_IDS:
        return SEASON_IDS[league_name]
    
    # Verificar correspondência ignorando maiúsculas/minúsculas
    league_name_lower = league_name.lower()
    for known_league, season_id in SEASON_IDS.items():
        if known_league.lower() == league_name_lower:
            return season_id
    
    # Verificar correspondência parcial (se o nome da liga está contido em alguma chave)
    for known_league, season_id in SEASON_IDS.items():
        if league_name_lower in known_league.lower() or known_league.lower() in league_name_lower:
            return season_id
    
    # Nenhuma correspondência encontrada
    return None
