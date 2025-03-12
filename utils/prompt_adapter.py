import logging

# Configuração de logging
logger = logging.getLogger("valueHunter.prompt_adapter")

# Add this to utils/prompt_adapter.py

def transform_to_optimized_data(api_data, home_team_name, away_team_name, selected_markets=None):
    """
    Transform API data into a more optimized, flattened structure
    
    Args:
        api_data (dict): Original API data from FootyStats
        home_team_name (str): Name of home team
        away_team_name (str): Name of away team
        selected_markets (dict, optional): Dictionary of selected markets to filter data
        
    Returns:
        dict: Optimized data structure
    """
    import logging
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    try:
        # Initialize the optimized structure
        optimized_data = {
            "match_info": {
                "home_team": home_team_name,
                "away_team": away_team_name,
                "league": "",
                "league_id": None
            },
            "home_team": {
                # Basic stats
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_scored": 0,
                "goals_conceded": 0,
                "clean_sheets_pct": 0,
                "btts_pct": 0,
                "over_2_5_pct": 0,
                # Home specific
                "home_played": 0,
                "home_wins": 0,
                "home_draws": 0,
                "home_losses": 0,
                "home_goals_scored": 0,
                "home_goals_conceded": 0,
                # Advanced
                "xg": 0,
                "xga": 0,
                "ppda": 0,
                "possession": 0,
                # Card stats
                "cards_total": 0,
                "cards_per_game": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "over_3_5_cards_pct": 0,
                "home_cards_per_game": 0,
                "away_cards_per_game": 0,
                # Corner stats
                "corners_total": 0,
                "corners_per_game": 0,
                "corners_for": 0,
                "corners_against": 0,
                "over_9_5_corners_pct": 0,
                "home_corners_per_game": 0,
                "away_corners_per_game": 0,
                # Form (simplified)
                "form": "",
                "recent_matches": []
            },
            "away_team": {
                # Copy of the same structure for away team
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_scored": 0,
                "goals_conceded": 0,
                "clean_sheets_pct": 0,
                "btts_pct": 0,
                "over_2_5_pct": 0,
                # Away specific
                "away_played": 0,
                "away_wins": 0,
                "away_draws": 0,
                "away_losses": 0,
                "away_goals_scored": 0,
                "away_goals_conceded": 0,
                # Advanced
                "xg": 0,
                "xga": 0,
                "ppda": 0,
                "possession": 0,
                # Card stats
                "cards_total": 0,
                "cards_per_game": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "over_3_5_cards_pct": 0,
                "home_cards_per_game": 0,
                "away_cards_per_game": 0,
                # Corner stats
                "corners_total": 0,
                "corners_per_game": 0,
                "corners_for": 0,
                "corners_against": 0,
                "over_9_5_corners_pct": 0,
                "home_corners_per_game": 0,
                "away_corners_per_game": 0,
                # Form (simplified)
                "form": "",
                "recent_matches": []
            },
            "h2h": {
                "total_matches": 0,
                "home_wins": 0,
                "away_wins": 0,
                "draws": 0,
                "over_2_5_pct": 0,
                "btts_pct": 0,
                "avg_cards": 0,
                "avg_corners": 0,
                "recent_matches": []
            }
        }
        
        # Check if we have valid API data
        if not api_data or not isinstance(api_data, dict):
            logger.error("Invalid API data provided")
            return optimized_data
        
        # Fill in league info
        if "basic_stats" in api_data and "league_id" in api_data["basic_stats"]:
            optimized_data["match_info"]["league_id"] = api_data["basic_stats"]["league_id"]
            
        # Extract home team stats
        home_team_data = {}
        if "basic_stats" in api_data and "home_team" in api_data["basic_stats"]:
            # Get raw data from API
            home_raw = api_data["basic_stats"]["home_team"]
            
            # Extract stats from nested structure
            if "stats" in home_raw:
                if isinstance(home_raw["stats"], dict):
                    # If stats is a direct object
                    home_team_data = home_raw["stats"]
                elif "stats" in home_raw["stats"] and isinstance(home_raw["stats"]["stats"], dict):
                    # If stats is nested deeper
                    home_team_data = home_raw["stats"]["stats"]
            
            # Basic stats
            optimized_data["home_team"]["played"] = get_value(home_team_data, ["matches_played", "seasonMatchesPlayed_overall", "MP"])
            optimized_data["home_team"]["wins"] = get_value(home_team_data, ["wins", "seasonWinsNum_overall", "W"])
            optimized_data["home_team"]["draws"] = get_value(home_team_data, ["draws", "seasonDrawsNum_overall", "D"])
            optimized_data["home_team"]["losses"] = get_value(home_team_data, ["losses", "seasonLossesNum_overall", "L"])
            optimized_data["home_team"]["goals_scored"] = get_value(home_team_data, ["goals_scored", "seasonGoals_overall", "Gls"])
            optimized_data["home_team"]["goals_conceded"] = get_value(home_team_data, ["goals_conceded", "seasonConceded_overall", "GA"])
            
            # Goal trends
            optimized_data["home_team"]["clean_sheets_pct"] = get_value(home_team_data, ["clean_sheet_percentage", "seasonCSPercentage_overall"])
            optimized_data["home_team"]["btts_pct"] = get_value(home_team_data, ["btts_percentage", "seasonBTTSPercentage_overall"])
            optimized_data["home_team"]["over_2_5_pct"] = get_value(home_team_data, ["over_2_5_percentage", "seasonOver25Percentage_overall"])
            
            # Home specific
            optimized_data["home_team"]["home_played"] = get_value(home_team_data, ["matches_played_home", "seasonMatchesPlayed_home"])
            optimized_data["home_team"]["home_wins"] = get_value(home_team_data, ["home_wins", "seasonWinsNum_home"])
            optimized_data["home_team"]["home_draws"] = get_value(home_team_data, ["home_draws", "seasonDrawsNum_home"])
            optimized_data["home_team"]["home_losses"] = get_value(home_team_data, ["home_losses", "seasonLossesNum_home"])
            optimized_data["home_team"]["home_goals_scored"] = get_value(home_team_data, ["goals_scored_home", "seasonGoals_home"])
            optimized_data["home_team"]["home_goals_conceded"] = get_value(home_team_data, ["goals_conceded_home", "seasonConceded_home"])
            
            # Advanced stats
            optimized_data["home_team"]["xg"] = get_value(home_team_data, ["xG", "xg", "xg_for_overall"])
            optimized_data["home_team"]["xga"] = get_value(home_team_data, ["xGA", "xga", "xg_against_avg_overall"])
            optimized_data["home_team"]["possession"] = get_value(home_team_data, ["possession", "possessionAVG_overall", "Poss"])
            
            # Card stats
            optimized_data["home_team"]["cards_total"] = get_value(home_team_data, ["cards_total", "seasonCrdYNum_overall", "CrdY"]) + get_value(home_team_data, ["seasonCrdRNum_overall", "CrdR"], 0)
            optimized_data["home_team"]["yellow_cards"] = get_value(home_team_data, ["yellow_cards", "seasonCrdYNum_overall", "CrdY"])
            optimized_data["home_team"]["red_cards"] = get_value(home_team_data, ["red_cards", "seasonCrdRNum_overall", "CrdR"])
            optimized_data["home_team"]["over_3_5_cards_pct"] = get_value(home_team_data, ["over_3_5_cards_percentage"])
            
            # If matches played exists, calculate per-game averages
            matches_played = optimized_data["home_team"]["played"]
            if matches_played > 0:
                optimized_data["home_team"]["cards_per_game"] = optimized_data["home_team"]["cards_total"] / matches_played
                
            # Corner stats
            optimized_data["home_team"]["corners_for"] = get_value(home_team_data, ["corners_for", "seasonCornersFor_overall", "CK"])
            optimized_data["home_team"]["corners_against"] = get_value(home_team_data, ["corners_against", "seasonCornersAgainst_overall"])
            optimized_data["home_team"]["corners_total"] = optimized_data["home_team"]["corners_for"] + optimized_data["home_team"]["corners_against"]
            optimized_data["home_team"]["over_9_5_corners_pct"] = get_value(home_team_data, ["over_9_5_corners_percentage"])
            
            # Calculate per-game averages for corners if matches played
            if matches_played > 0:
                optimized_data["home_team"]["corners_per_game"] = optimized_data["home_team"]["corners_total"] / matches_played
            
            # Get PPDA from advanced stats if available
            if "advanced_stats" in api_data and "home" in api_data["advanced_stats"]:
                optimized_data["home_team"]["ppda"] = get_value(api_data["advanced_stats"]["home"], ["ppda", "passes_per_defensive_action"])
        
        # Extract away team stats (similar structure)
        away_team_data = {}
        if "basic_stats" in api_data and "away_team" in api_data["basic_stats"]:
            # Get raw data from API
            away_raw = api_data["basic_stats"]["away_team"]
            
            # Extract stats from nested structure
            if "stats" in away_raw:
                if isinstance(away_raw["stats"], dict):
                    # If stats is a direct object
                    away_team_data = away_raw["stats"]
                elif "stats" in away_raw["stats"] and isinstance(away_raw["stats"]["stats"], dict):
                    # If stats is nested deeper
                    away_team_data = away_raw["stats"]["stats"]
            
            # Basic stats
            optimized_data["away_team"]["played"] = get_value(away_team_data, ["matches_played", "seasonMatchesPlayed_overall", "MP"])
            optimized_data["away_team"]["wins"] = get_value(away_team_data, ["wins", "seasonWinsNum_overall", "W"])
            optimized_data["away_team"]["draws"] = get_value(away_team_data, ["draws", "seasonDrawsNum_overall", "D"])
            optimized_data["away_team"]["losses"] = get_value(away_team_data, ["losses", "seasonLossesNum_overall", "L"])
            optimized_data["away_team"]["goals_scored"] = get_value(away_team_data, ["goals_scored", "seasonGoals_overall", "Gls"])
            optimized_data["away_team"]["goals_conceded"] = get_value(away_team_data, ["goals_conceded", "seasonConceded_overall", "GA"])
            
            # Goal trends
            optimized_data["away_team"]["clean_sheets_pct"] = get_value(away_team_data, ["clean_sheet_percentage", "seasonCSPercentage_overall"])
            optimized_data["away_team"]["btts_pct"] = get_value(away_team_data, ["btts_percentage", "seasonBTTSPercentage_overall"])
            optimized_data["away_team"]["over_2_5_pct"] = get_value(away_team_data, ["over_2_5_percentage", "seasonOver25Percentage_overall"])
            
            # Away specific
            optimized_data["away_team"]["away_played"] = get_value(away_team_data, ["matches_played_away", "seasonMatchesPlayed_away"])
            optimized_data["away_team"]["away_wins"] = get_value(away_team_data, ["away_wins", "seasonWinsNum_away"])
            optimized_data["away_team"]["away_draws"] = get_value(away_team_data, ["away_draws", "seasonDrawsNum_away"])
            optimized_data["away_team"]["away_losses"] = get_value(away_team_data, ["away_losses", "seasonLossesNum_away"])
            optimized_data["away_team"]["away_goals_scored"] = get_value(away_team_data, ["goals_scored_away", "seasonGoals_away"])
            optimized_data["away_team"]["away_goals_conceded"] = get_value(away_team_data, ["goals_conceded_away", "seasonConceded_away"])
            
            # Advanced stats
            optimized_data["away_team"]["xg"] = get_value(away_team_data, ["xG", "xg", "xg_for_overall"])
            optimized_data["away_team"]["xga"] = get_value(away_team_data, ["xGA", "xga", "xg_against_avg_overall"])
            optimized_data["away_team"]["possession"] = get_value(away_team_data, ["possession", "possessionAVG_overall", "Poss"])
            
            # Card stats
            optimized_data["away_team"]["cards_total"] = get_value(away_team_data, ["cards_total", "seasonCrdYNum_overall", "CrdY"]) + get_value(away_team_data, ["seasonCrdRNum_overall", "CrdR"], 0)
            optimized_data["away_team"]["yellow_cards"] = get_value(away_team_data, ["yellow_cards", "seasonCrdYNum_overall", "CrdY"])
            optimized_data["away_team"]["red_cards"] = get_value(away_team_data, ["red_cards", "seasonCrdRNum_overall", "CrdR"])
            optimized_data["away_team"]["over_3_5_cards_pct"] = get_value(away_team_data, ["over_3_5_cards_percentage"])
            
            # If matches played exists, calculate per-game averages
            matches_played = optimized_data["away_team"]["played"]
            if matches_played > 0:
                optimized_data["away_team"]["cards_per_game"] = optimized_data["away_team"]["cards_total"] / matches_played
                
            # Corner stats
            optimized_data["away_team"]["corners_for"] = get_value(away_team_data, ["corners_for", "seasonCornersFor_overall", "CK"])
            optimized_data["away_team"]["corners_against"] = get_value(away_team_data, ["corners_against", "seasonCornersAgainst_overall"])
            optimized_data["away_team"]["corners_total"] = optimized_data["away_team"]["corners_for"] + optimized_data["away_team"]["corners_against"]
            optimized_data["away_team"]["over_9_5_corners_pct"] = get_value(away_team_data, ["over_9_5_corners_percentage"])
            
            # Calculate per-game averages for corners if matches played
            if matches_played > 0:
                optimized_data["away_team"]["corners_per_game"] = optimized_data["away_team"]["corners_total"] / matches_played
            
            # Get PPDA from advanced stats if available
            if "advanced_stats" in api_data and "away" in api_data["advanced_stats"]:
                optimized_data["away_team"]["ppda"] = get_value(api_data["advanced_stats"]["away"], ["ppda", "passes_per_defensive_action"])
        
        # Extract head-to-head data
        if "head_to_head" in api_data:
            h2h_data = api_data["head_to_head"]
            
            optimized_data["h2h"]["total_matches"] = get_value(h2h_data, ["total_matches"])
            optimized_data["h2h"]["home_wins"] = get_value(h2h_data, ["home_wins"])
            optimized_data["h2h"]["away_wins"] = get_value(h2h_data, ["away_wins"])
            optimized_data["h2h"]["draws"] = get_value(h2h_data, ["draws"])
            optimized_data["h2h"]["over_2_5_pct"] = get_value(h2h_data, ["over_2_5_percentage"])
            optimized_data["h2h"]["btts_pct"] = get_value(h2h_data, ["btts_percentage"])
            optimized_data["h2h"]["avg_cards"] = get_value(h2h_data, ["average_cards"])
            optimized_data["h2h"]["avg_corners"] = get_value(h2h_data, ["average_corners"])
        
        # Extract form data
        if "team_form" in api_data:
            # Home team form
            if "home" in api_data["team_form"] and isinstance(api_data["team_form"]["home"], list):
                form_list = []
                form_string = ""
                
                for match in api_data["team_form"]["home"][:5]:
                    result = match.get("result", "?")
                    form_list.append(result)
                    form_string += result
                
                optimized_data["home_team"]["form"] = form_string
                optimized_data["home_team"]["recent_matches"] = api_data["team_form"]["home"][:5]
            
            # Away team form
            if "away" in api_data["team_form"] and isinstance(api_data["team_form"]["away"], list):
                form_list = []
                form_string = ""
                
                for match in api_data["team_form"]["away"][:5]:
                    result = match.get("result", "?")
                    form_list.append(result)
                    form_string += result
                
                optimized_data["away_team"]["form"] = form_string
                optimized_data["away_team"]["recent_matches"] = api_data["team_form"]["away"][:5]
        
        # Filter the data if markets are specified
        if selected_markets and isinstance(selected_markets, dict):
            return filter_optimized_data(optimized_data, selected_markets)
        
        return optimized_data
        
    except Exception as e:
        logger.error(f"Error transforming data to optimized format: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return optimized_data  # Return the default structure


def get_value(data_dict, possible_keys, default=0):
    """
    Helper function to get a value from a dictionary using multiple possible keys
    
    Args:
        data_dict (dict): Dictionary to extract from
        possible_keys (list): List of possible keys to try
        default: Default value if not found
        
    Returns:
        Value from dictionary or default
    """
    if not data_dict or not isinstance(data_dict, dict):
        return default
    
    for key in possible_keys:
        if key in data_dict:
            # Handle 'N/A' and other non-numeric values
            value = data_dict[key]
            if value == 'N/A' or value is None:
                return default
            
            # Try to convert to float
            try:
                return float(value)
            except (ValueError, TypeError):
                pass
    
    return default


def filter_optimized_data(optimized_data, selected_markets):
    """
    Filter optimized data based on selected markets
    
    Args:
        optimized_data (dict): Optimized data structure
        selected_markets (dict): Dictionary of selected markets
        
    Returns:
        dict: Filtered optimized data
    """
    # Create a copy to avoid modifying the original
    filtered_data = {
        "match_info": optimized_data["match_info"].copy(),
        "home_team": {},
        "away_team": {},
        "h2h": {}
    }
    
    # Basic stats are always needed
    basic_fields = [
        "played", "wins", "draws", "losses", 
        "goals_scored", "goals_conceded", 
        "form", "recent_matches"
    ]
    
    # Define field groups for each market
    market_fields = {
        "money_line": [
            "home_played", "home_wins", "home_draws", "home_losses",
            "home_goals_scored", "home_goals_conceded",
            "away_played", "away_wins", "away_draws", "away_losses",
            "away_goals_scored", "away_goals_conceded",
            "xg", "xga", "possession", "ppda"
        ],
        "chance_dupla": [
            "home_played", "home_wins", "home_draws", "home_losses",
            "home_goals_scored", "home_goals_conceded",
            "away_played", "away_wins", "away_draws", "away_losses",
            "away_goals_scored", "away_goals_conceded",
            "xg", "xga", "possession", "ppda"
        ],
        "over_under": [
            "clean_sheets_pct", "over_2_5_pct", "xg", "xga"
        ],
        "ambos_marcam": [
            "clean_sheets_pct", "btts_pct", "xg", "xga"
        ],
        "escanteios": [
            "corners_total", "corners_per_game", "corners_for", "corners_against",
            "over_9_5_corners_pct", "home_corners_per_game", "away_corners_per_game"
        ],
        "cartoes": [
            "cards_total", "cards_per_game", "yellow_cards", "red_cards",
            "over_3_5_cards_pct", "home_cards_per_game", "away_cards_per_game"
        ]
    }
    
    # H2H fields for each market
    h2h_market_fields = {
        "money_line": ["total_matches", "home_wins", "away_wins", "draws"],
        "chance_dupla": ["total_matches", "home_wins", "away_wins", "draws"],
        "over_under": ["over_2_5_pct"],
        "ambos_marcam": ["btts_pct"],
        "escanteios": ["avg_corners"],
        "cartoes": ["avg_cards"]
    }
    
    # Add basic fields for both teams
    for team in ["home_team", "away_team"]:
        filtered_data[team] = {field: optimized_data[team][field] for field in basic_fields if field in optimized_data[team]}
    
    # Add market-specific fields based on selections
    for market, selected in selected_markets.items():
        if selected and market in market_fields:
            for team in ["home_team", "away_team"]:
                for field in market_fields[market]:
                    if field in optimized_data[team]:
                        filtered_data[team][field] = optimized_data[team][field]
            
            # Add H2H fields for this market
            if market in h2h_market_fields:
                for field in h2h_market_fields[market]:
                    if field in optimized_data["h2h"]:
                        if "h2h" not in filtered_data:
                            filtered_data["h2h"] = {}
                        filtered_data["h2h"][field] = optimized_data["h2h"][field]
    
    return filtered_data

def adapt_api_data_for_prompt(complete_analysis):
    """
    Adapta os dados coletados da API para o formato esperado pelo format_enhanced_prompt
    
    Args:
        complete_analysis (dict): Dados coletados pelo enhanced_api_client
        
    Returns:
        dict: Dados formatados para o format_enhanced_prompt
    """
    try:
        # Verificar se os dados são válidos
        if not complete_analysis or not isinstance(complete_analysis, dict):
            logger.error("Dados de análise inválidos")
            return None
        
        # Inicializar a estrutura adaptada
        adapted_data = {
            "basic_stats": {
                "home_team": {"name": "", "stats": {}},
                "away_team": {"name": "", "stats": {}},
                "referee": "Não informado"
            },
            "team_form": {
                "home": [],
                "away": []
            },
            "head_to_head": {},
            "advanced_stats": {
                "home": {},
                "away": {}
            }
        }
        
        # 1. Adaptar estatísticas básicas
        if "basic_stats" in complete_analysis:
            # Copiar estrutura básica
            adapted_data["basic_stats"] = complete_analysis["basic_stats"]
            
            # Garantir que a estrutura esteja correta
            if "home_team" in complete_analysis["basic_stats"]:
                home_team = complete_analysis["basic_stats"]["home_team"]
                if "stats" in home_team:
                    # Se "stats" for um objeto, extrair estatísticas do objeto completo
                    if isinstance(home_team["stats"], dict):
                        # Verificar se há um subobjeto "stats" dentro do objeto "stats"
                        if "stats" in home_team["stats"] and isinstance(home_team["stats"]["stats"], dict):
                            adapted_data["basic_stats"]["home_team"]["stats"] = home_team["stats"]["stats"]
                        else:
                            adapted_data["basic_stats"]["home_team"]["stats"] = extract_stats(home_team["stats"])
            
            if "away_team" in complete_analysis["basic_stats"]:
                away_team = complete_analysis["basic_stats"]["away_team"]
                if "stats" in away_team:
                    # Se "stats" for um objeto, extrair estatísticas do objeto completo
                    if isinstance(away_team["stats"], dict):
                        # Verificar se há um subobjeto "stats" dentro do objeto "stats"
                        if "stats" in away_team["stats"] and isinstance(away_team["stats"]["stats"], dict):
                            adapted_data["basic_stats"]["away_team"]["stats"] = away_team["stats"]["stats"]
                        else:
                            adapted_data["basic_stats"]["away_team"]["stats"] = extract_stats(away_team["stats"])
        
        # 2. Adaptar form recente
        if "team_form" in complete_analysis:
            # Verificar se temos dados de form
            if "home" in complete_analysis["team_form"] and isinstance(complete_analysis["team_form"]["home"], dict):
                # Se estiver no formato da API lastx
                if "data" in complete_analysis["team_form"]["home"] and isinstance(complete_analysis["team_form"]["home"]["data"], list):
                    adapted_data["team_form"]["home"] = adapt_last_matches(complete_analysis["team_form"]["home"]["data"])
                else:
                    adapted_data["team_form"]["home"] = []
            elif "home" in complete_analysis["team_form"] and isinstance(complete_analysis["team_form"]["home"], list):
                # Se já estiver em lista
                adapted_data["team_form"]["home"] = complete_analysis["team_form"]["home"]
            
            if "away" in complete_analysis["team_form"] and isinstance(complete_analysis["team_form"]["away"], dict):
                # Se estiver no formato da API lastx
                if "data" in complete_analysis["team_form"]["away"] and isinstance(complete_analysis["team_form"]["away"]["data"], list):
                    adapted_data["team_form"]["away"] = adapt_last_matches(complete_analysis["team_form"]["away"]["data"])
                else:
                    adapted_data["team_form"]["away"] = []
            elif "away" in complete_analysis["team_form"] and isinstance(complete_analysis["team_form"]["away"], list):
                # Se já estiver em lista
                adapted_data["team_form"]["away"] = complete_analysis["team_form"]["away"]
        
        # 3. Adaptar Head-to-Head
        if "head_to_head" in complete_analysis:
            adapted_data["head_to_head"] = complete_analysis["head_to_head"]
        elif "match_details" in complete_analysis and complete_analysis["match_details"]:
            # Se temos detalhes da partida, verificar se há H2H
            if "h2h" in complete_analysis["match_details"]:
                adapted_data["head_to_head"] = complete_analysis["match_details"]["h2h"]
        
        # 4. Adaptar Advanced Stats
        if "advanced_stats" in complete_analysis:
            adapted_data["advanced_stats"] = complete_analysis["advanced_stats"]
        
        logger.info("Dados adaptados com sucesso para formato do prompt")
        return adapted_data
    
    except Exception as e:
        logger.error(f"Erro ao adaptar dados para prompt: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def extract_stats(stats_obj):
    """
    Extrai estatísticas relevantes de um objeto de estatísticas
    
    Args:
        stats_obj (dict): Objeto com estatísticas do time
        
    Returns:
        dict: Estatísticas extraídas no formato esperado
    """
    stats = {}
    
    # Mapeamento de campos da API para o formato esperado
    field_mapping = {
        'matches_played': ['seasonMatchesPlayed_overall', 'matches_played', 'MP'],
        'wins': ['seasonWinsNum_overall', 'wins', 'W'],
        'draws': ['seasonDrawsNum_overall', 'draws', 'D'],
        'losses': ['seasonLossesNum_overall', 'losses', 'L'],
        'goals_scored': ['seasonGoals_overall', 'goals_scored', 'Gls'],
        'goals_conceded': ['seasonConceded_overall', 'goals_conceded', 'GA'],
        'xG': ['xg_for_overall', 'xg', 'xG'],
        'xGA': ['xg_against_avg_overall', 'xga', 'xGA'],
        'possession': ['possessionAVG_overall', 'possession', 'Poss'],
        'win_percentage': ['winPercentage_overall'],
        'draw_percentage': ['drawPercentage_overall'],
        'clean_sheets': ['seasonCS_overall'],
        'clean_sheet_percentage': ['seasonCSPercentage_overall'],
        'btts_percentage': ['seasonBTTSPercentage_overall'],
        'over_2_5_percentage': ['seasonOver25Percentage_overall'],
        'home_wins': ['seasonWinsNum_home'],
        'home_draws': ['seasonDrawsNum_home'],
        'home_losses': ['seasonLossesNum_home'],
        'away_wins': ['seasonWinsNum_away'],
        'away_draws': ['seasonDrawsNum_away'],
        'away_losses': ['seasonLossesNum_away']
    }
    
    # Extrair campos usando o mapeamento
    for target_field, source_fields in field_mapping.items():
        for source_field in source_fields:
            if source_field in stats_obj:
                stats[target_field] = stats_obj[source_field]
                break
    
    return stats

def adapt_last_matches(matches_data):
    """
    Adapta os dados dos últimos jogos para o formato esperado
    
    Args:
        matches_data (list): Lista de jogos da API
        
    Returns:
        list: Lista formatada para o prompt
    """
    if not matches_data or not isinstance(matches_data, list):
        return []
    
    # Limitando aos últimos 5 jogos
    matches = matches_data[:5]
    
    # Converter para o formato esperado
    formatted_matches = []
    for match in matches:
        result = "?"
        
        # Determinar resultado (W/D/L)
        if "result" in match:
            result = match["result"]
        elif "homeID" in match and "awayID" in match and "homeGoals" in match and "awayGoals" in match and "teamID" in match:
            # Se for o time da casa
            if match["homeID"] == match["teamID"]:
                if match["homeGoals"] > match["awayGoals"]:
                    result = "W"
                elif match["homeGoals"] < match["awayGoals"]:
                    result = "L"
                else:
                    result = "D"
            # Se for o time visitante
            elif match["awayID"] == match["teamID"]:
                if match["homeGoals"] < match["awayGoals"]:
                    result = "W"
                elif match["homeGoals"] > match["awayGoals"]:
                    result = "L"
                else:
                    result = "D"
        
        formatted_matches.append({"result": result})
    
    # Preencher com placeholders se necessário
    while len(formatted_matches) < 5:
        formatted_matches.append({"result": "?"})
    
    return formatted_matches
