import logging

# Configuração de logging
logger = logging.getLogger("valueHunter.prompt_adapter")

def transform_to_highly_optimized_data(api_data, home_team_name, away_team_name, selected_markets=None):
    """
    Transform API data into a properly structured format with all essential fields.
    
    Args:
        api_data (dict): Original API data from FootyStats
        home_team_name (str): Name of home team
        away_team_name (str): Name of away team
        selected_markets (dict, optional): Dictionary of selected markets to filter data
        
    Returns:
        dict: Highly optimized data structure with minimal footprint
    """
    import logging
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    try:
        # Initialize with the correct structure - FIXO: usado match_info e home_team/away_team
        optimized_data = {
            "match_info": {  # Changed from "match" to "match_info"
                "home_team": home_team_name,  # Changed from "home" to "home_team"
                "away_team": away_team_name,  # Changed from "away" to "away_team"
                "league": "",
                "league_id": None
            },
            "home_team": {},  # Changed from "home" to "home_team"
            "away_team": {},  # Changed from "away" to "away_team"
            "h2h": {}
        }
        
        # Check if we have valid API data
        if not api_data or not isinstance(api_data, dict):
            logger.error("Invalid API data provided")
            return optimized_data
        
        # Debug: Log API data structure
        logger.info(f"API data keys: {list(api_data.keys())}")
        if "basic_stats" in api_data:
            logger.info(f"basic_stats keys: {list(api_data['basic_stats'].keys())}")
        
        # Fill in league info
        if "basic_stats" in api_data and "league_id" in api_data["basic_stats"]:
            optimized_data["match_info"]["league_id"] = api_data["basic_stats"]["league_id"]
        
        # ENSURE ALL ESSENTIAL STATS ARE INCLUDED - don't rely on selected markets
        essential_stats = {
            # Basic stats
            "played", "wins", "draws", "losses", 
            "goals_scored", "goals_conceded", 
            "clean_sheets_pct", "btts_pct", "over_2_5_pct",
            
            # Home/Away specific
            "home_played", "home_wins", "home_draws", "home_losses",
            "home_goals_scored", "home_goals_conceded",
            "away_played", "away_wins", "away_draws", "away_losses",
            "away_goals_scored", "away_goals_conceded",
            
            # Advanced
            "xg", "xga", "ppda", "possession",
            
            # Cards
            "cards_total", "cards_per_game", "yellow_cards", "red_cards",
            "over_3_5_cards_pct", "home_cards_per_game", "away_cards_per_game",
            
            # Corners
            "corners_total", "corners_per_game", "corners_for", "corners_against",
            "over_9_5_corners_pct", "home_corners_per_game", "away_corners_per_game"
        }
        
        # Extract home team stats - use all essential stats
        home_stats = extract_expanded_team_stats(api_data, "home", essential_stats)
        optimized_data["home_team"] = home_stats
        
        # Extract away team stats - use all essential stats
        away_stats = extract_expanded_team_stats(api_data, "away", essential_stats)
        optimized_data["away_team"] = away_stats
        
        # Extract complete h2h data
        optimized_data["h2h"] = extract_expanded_h2h(api_data)
        
        # Add form data
        optimized_data["home_team"]["form"] = extract_form_string(api_data, "home")
        optimized_data["away_team"]["form"] = extract_form_string(api_data, "away")
        
        # Add fallbacks for critical fields
        ensure_critical_fields(optimized_data, home_team_name, away_team_name)
        
        # Debug log - Verificar campos extraídos
        logger.info(f"Home stats extracted: {list(home_stats.keys())}")
        logger.info(f"Away stats extracted: {list(away_stats.keys())}")
        logger.info(f"H2H stats extracted: {list(optimized_data['h2h'].keys())}")
        
        logger.info(f"Created complete data structure for {home_team_name} vs {away_team_name}")
        return optimized_data
        
    except Exception as e:
        logger.error(f"Error creating optimized data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "match_info": {"home_team": home_team_name, "away_team": away_team_name},
            "home_team": {}, 
            "away_team": {},
            "h2h": {}
        }

def extract_expanded_team_stats(api_data, team_type, essential_stats):
    """
    Extract comprehensive team statistics with fallbacks for missing data.
    
    Args:
        api_data (dict): Original API data
        team_type (str): "home" or "away"
        essential_stats (set): Set of essential stat names to include
        
    Returns:
        dict: Complete stats dictionary with all essential fields
    """
    stats = {}
    
    # Initialize with default values for all essential stats
    for stat in essential_stats:
        stats[stat] = 0
    
    # Fill in form placeholder
    stats["form"] = "?????"
    stats["recent_matches"] = []
    
    # If no valid data, return defaults
    if not api_data or "basic_stats" not in api_data:
        return stats
    
    # Try to extract real data
    team_key = f"{team_type}_team"
    if team_key in api_data["basic_stats"]:
        team_data = api_data["basic_stats"][team_key]
        
        # Debug log
        logger.info(f"{team_type}_team keys: {list(team_data.keys() if isinstance(team_data, dict) else [])}")
        
        # Try different possible locations and formats for stats
        if "stats" in team_data:
            raw_stats = None
            if isinstance(team_data["stats"], dict):
                if "stats" in team_data["stats"]:
                    raw_stats = team_data["stats"]["stats"]
                else:
                    raw_stats = team_data["stats"]
            
            if raw_stats:
                # Debug log
                logger.info(f"{team_type} raw_stats keys: {list(raw_stats.keys() if isinstance(raw_stats, dict) else [])}")
                
                # Map API fields to our essential stats with multiple possible keys
                field_mapping = {
                    "played": ["matches_played", "seasonMatchesPlayed_overall", "MP"],
                    "wins": ["wins", "seasonWinsNum_overall", "W"],
                    "draws": ["draws", "seasonDrawsNum_overall", "D"],
                    "losses": ["losses", "seasonLossesNum_overall", "L"],
                    "goals_scored": ["goals_scored", "seasonGoals_overall", "Gls", "goals"],
                    "goals_conceded": ["goals_conceded", "seasonConceded_overall", "GA"],
                    "xg": ["xG", "xg", "xg_for_overall", "expected_goals"],
                    "xga": ["xGA", "xga", "xg_against_avg_overall"],
                    "possession": ["possession", "possessionAVG_overall", "Poss"],
                    "clean_sheets_pct": ["clean_sheet_percentage", "seasonCSPercentage_overall"],
                    "btts_pct": ["btts_percentage", "seasonBTTSPercentage_overall"],
                    "over_2_5_pct": ["over_2_5_percentage", "seasonOver25Percentage_overall"],
                    "home_played": ["matches_played_home", "seasonMatchesPlayed_home"],
                    "home_wins": ["home_wins", "seasonWinsNum_home"],
                    "home_draws": ["home_draws", "seasonDrawsNum_home"],
                    "home_losses": ["home_losses", "seasonLossesNum_home"],
                    "home_goals_scored": ["goals_scored_home", "seasonGoals_home"],
                    "home_goals_conceded": ["goals_conceded_home", "seasonConceded_home"],
                    "away_played": ["matches_played_away", "seasonMatchesPlayed_away"],
                    "away_wins": ["away_wins", "seasonWinsNum_away"],
                    "away_draws": ["away_draws", "seasonDrawsNum_away"],
                    "away_losses": ["away_losses", "seasonLossesNum_away"],
                    "away_goals_scored": ["goals_scored_away", "seasonGoals_away"],
                    "away_goals_conceded": ["goals_conceded_away", "seasonConceded_away"],
                    "cards_total": ["cards_total", "seasonCrdYNum_overall", "CrdY"],
                    "yellow_cards": ["yellow_cards", "seasonCrdYNum_overall", "CrdY"],
                    "red_cards": ["red_cards", "seasonCrdRNum_overall", "CrdR"],
                    "over_3_5_cards_pct": ["over_3_5_cards_percentage"],
                    "corners_total": ["corners_total"],
                    "corners_for": ["corners_for", "seasonCornersFor_overall", "CK"],
                    "corners_against": ["corners_against", "seasonCornersAgainst_overall"],
                    "over_9_5_corners_pct": ["over_9_5_corners_percentage"],
                }
                
                # Extract fields using mapping
                for stat_name, api_keys in field_mapping.items():
                    for key in api_keys:
                        if key in raw_stats:
                            value = raw_stats[key]
                            # Validate and convert value
                            if value is not None and value != 'N/A':
                                try:
                                    stats[stat_name] = float(value)
                                    break  # Found valid value, stop looking
                                except (ValueError, TypeError):
                                    pass  # Continue to next key if value can't be converted
        
        # Try to get PPDA from advanced_stats if available
        if "advanced_stats" in api_data and team_type in api_data["advanced_stats"]:
            adv_stats = api_data["advanced_stats"][team_type]
            ppda_keys = ["ppda", "passes_per_defensive_action"]
            for key in ppda_keys:
                if key in adv_stats and adv_stats[key] is not None:
                    try:
                        stats["ppda"] = float(adv_stats[key])
                        break
                    except (ValueError, TypeError):
                        pass
        
        # Calculate derived statistics
        # Example: if we have enough games played, calculate per-game stats
        if stats["played"] > 0:
            if stats["cards_total"] > 0:
                stats["cards_per_game"] = round(stats["cards_total"] / stats["played"], 2)
            if stats["corners_for"] > 0 or stats["corners_against"] > 0:
                stats["corners_total"] = stats["corners_for"] + stats["corners_against"]
                stats["corners_per_game"] = round(stats["corners_total"] / stats["played"], 2)
    
    return stats

def extract_expanded_h2h(api_data):
    """
    Extract comprehensive head-to-head data.
    
    Args:
        api_data (dict): Original API data
        
    Returns:
        dict: Complete H2H data
    """
    h2h = {
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
    
    if not api_data:
        return h2h
    
    # Check for H2H data in different locations
    h2h_data = None
    
    # Direct h2h property
    if "head_to_head" in api_data:
        h2h_data = api_data["head_to_head"]
    # Inside match_details
    elif "match_details" in api_data and api_data["match_details"]:
        if "h2h" in api_data["match_details"]:
            h2h_data = api_data["match_details"]["h2h"]
    
    # If we found H2H data, extract it
    if h2h_data and isinstance(h2h_data, dict):
        # Map API fields to our fields
        field_mapping = {
            "total_matches": ["total_matches", "matches"],
            "home_wins": ["home_wins"],
            "away_wins": ["away_wins"],
            "draws": ["draws"],
            "over_2_5_pct": ["over_2_5_percentage"],
            "btts_pct": ["btts_percentage"],
            "avg_cards": ["average_cards"],
            "avg_corners": ["average_corners"]
        }
        
        # Extract each field
        for h2h_field, api_keys in field_mapping.items():
            for key in api_keys:
                if key in h2h_data and h2h_data[key] is not None:
                    try:
                        h2h[h2h_field] = float(h2h_data[key])
                        break
                    except (ValueError, TypeError):
                        pass
        
        # Extract recent matches if available
        if "matches" in h2h_data and isinstance(h2h_data["matches"], list):
            h2h["recent_matches"] = h2h_data["matches"][:5]  # Take only the 5 most recent
    
    return h2h

def extract_form_string(api_data, team_type):
    """
    Extract recent form as a simple string like "WWDLD" instead of an array.
    
    Args:
        api_data (dict): Original API data
        team_type (str): "home" or "away"
        
    Returns:
        str: Form string like "WWDLD"
    """
    form = ""
    
    if "team_form" not in api_data or team_type not in api_data["team_form"]:
        return "?????"
        
    team_form = api_data["team_form"][team_type]
    
    if isinstance(team_form, list) and len(team_form) > 0:
        # Extract up to 5 recent results
        for i in range(min(5, len(team_form))):
            if isinstance(team_form[i], dict) and "result" in team_form[i]:
                form += team_form[i]["result"]
            else:
                form += "?"
    elif isinstance(team_form, dict) and "data" in team_form and isinstance(team_form["data"], list):
        # Handle API lastx format
        data = team_form["data"]
        for i in range(min(5, len(data))):
            match = data[i]
            result = "?"
            
            # Try to determine result based on goals
            if "homeGoals" in match and "awayGoals" in match and "teamID" in match:
                if ("homeID" in match and match["homeID"] == match["teamID"]):
                    # Home team
                    if match["homeGoals"] > match["awayGoals"]:
                        result = "W"
                    elif match["homeGoals"] < match["awayGoals"]:
                        result = "L"
                    else:
                        result = "D"
                elif ("awayID" in match and match["awayID"] == match["teamID"]):
                    # Away team
                    if match["homeGoals"] < match["awayGoals"]:
                        result = "W"
                    elif match["homeGoals"] > match["awayGoals"]:
                        result = "L"
                    else:
                        result = "D"
            
            form += result
    
    # Ensure we return exactly 5 characters
    while len(form) < 5:
        form += "?"
        
    return form

def ensure_critical_fields(optimized_data, home_team_name, away_team_name):
    """
    Ensure critical fields have reasonable values even if not found in the data.
    
    Args:
        optimized_data (dict): Data structure to check and update
        home_team_name (str): Name of home team
        away_team_name (str): Name of away team
    """
    # Home team critical fields
    if "home_team" in optimized_data:
        home = optimized_data["home_team"]
        # Expected goals - use reasonable defaults if missing
        if home.get("xg", 0) == 0:
            home["xg"] = 1.5  # League average xG
        if home.get("xga", 0) == 0:
            home["xga"] = 1.5
            
        # Possession - default to balanced if missing
        if home.get("possession", 0) == 0:
            home["possession"] = 50
            
        # Goals - estimate from games played if missing
        played = max(home.get("played", 10), 1)  # Avoid division by zero
        if home.get("goals_scored", 0) == 0:
            home["goals_scored"] = int(played * 1.5)  # Average 1.5 goals per game
        if home.get("goals_conceded", 0) == 0:
            home["goals_conceded"] = int(played * 1.5)
            
        # btts and over_2_5 percentages
        if home.get("btts_pct", 0) == 0:
            home["btts_pct"] = 50  # Default to 50%
        if home.get("over_2_5_pct", 0) == 0:
            home["over_2_5_pct"] = 50  # Default to 50%
            
        # Clean sheets percentage
        if home.get("clean_sheets_pct", 0) == 0:
            home["clean_sheets_pct"] = 30  # Default to 30%
    
    # Away team critical fields
    if "away_team" in optimized_data:
        away = optimized_data["away_team"]
        # Expected goals - use reasonable defaults if missing
        if away.get("xg", 0) == 0:
            away["xg"] = 1.2  # Slightly lower for away teams
        if away.get("xga", 0) == 0:
            away["xga"] = 1.8  # Slightly higher for away teams
            
        # Possession - default to balanced if missing
        if away.get("possession", 0) == 0:
            away["possession"] = 50
            
        # Goals - estimate from games played if missing
        played = max(away.get("played", 10), 1)  # Avoid division by zero
        if away.get("goals_scored", 0) == 0:
            away["goals_scored"] = int(played * 1.2)  # Average 1.2 goals per game for away teams
        if away.get("goals_conceded", 0) == 0:
            away["goals_conceded"] = int(played * 1.8)
            
        # btts and over_2_5 percentages
        if away.get("btts_pct", 0) == 0:
            away["btts_pct"] = 50  # Default to 50%
        if away.get("over_2_5_pct", 0) == 0:
            away["over_2_5_pct"] = 50  # Default to 50%
            
        # Clean sheets percentage
        if away.get("clean_sheets_pct", 0) == 0:
            away["clean_sheets_pct"] = 25  # Default to 25% (slightly lower for away teams)
    
    # H2H critical fields
    if "h2h" in optimized_data:
        h2h = optimized_data["h2h"]
        # Ensure basic fields exist
        if h2h.get("total_matches", 0) == 0:
            h2h["total_matches"] = 0
            h2h["home_wins"] = 0
            h2h["away_wins"] = 0
            h2h["draws"] = 0
            
        # Ensure percentage fields exist
        if h2h.get("over_2_5_pct", 0) == 0:
            h2h["over_2_5_pct"] = 50
        if h2h.get("btts_pct", 0) == 0:
            h2h["btts_pct"] = 50
            
        # Ensure average fields exist
        if h2h.get("avg_cards", 0) == 0:
            h2h["avg_cards"] = 4.0  # Average cards per game
        if h2h.get("avg_corners", 0) == 0:
            h2h["avg_corners"] = 10.0  # Average corners per game

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
        # Initialize the optimized structure - USING THE EXPECTED FORMAT
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
            
            # Now extract all stats from the data
            extract_all_stats(optimized_data["home_team"], home_team_data, "home")
            
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
            
            # Now extract all stats from the data
            extract_all_stats(optimized_data["away_team"], away_team_data, "away")
            
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
        
        # Ensure all critical fields have reasonable values
        ensure_critical_fields(optimized_data, home_team_name, away_team_name)
        
        logger.info(f"Data structure optimized successfully for {home_team_name} vs {away_team_name}")
        return optimized_data
        
    except Exception as e:
        logger.error(f"Error transforming data to optimized format: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return optimized_data  # Return the default structure

def extract_all_stats(target_dict, data_dict, team_type):
    """
    Extract all stats from data dictionary to target dictionary
    
    Args:
        target_dict (dict): Target dictionary to populate
        data_dict (dict): Source data dictionary
        team_type (str): "home" or "away"
    """
    # Basic stats
    target_dict["played"] = get_value(data_dict, ["matches_played", "seasonMatchesPlayed_overall", "MP"])
    target_dict["wins"] = get_value(data_dict, ["wins", "seasonWinsNum_overall", "W"])
    target_dict["draws"] = get_value(data_dict, ["draws", "seasonDrawsNum_overall", "D"])
    target_dict["losses"] = get_value(data_dict, ["losses", "seasonLossesNum_overall", "L"])
    target_dict["goals_scored"] = get_value(data_dict, ["goals_scored", "seasonGoals_overall", "Gls"])
    target_dict["goals_conceded"] = get_value(data_dict, ["goals_conceded", "seasonConceded_overall", "GA"])
    
    # Goal trends
    target_dict["clean_sheets_pct"] = get_value(data_dict, ["clean_sheet_percentage", "seasonCSPercentage_overall"])
    target_dict["btts_pct"] = get_value(data_dict, ["btts_percentage", "seasonBTTSPercentage_overall"])
    target_dict["over_2_5_pct"] = get_value(data_dict, ["over_2_5_percentage", "seasonOver25Percentage_overall"])
    
    # Home/Away specific
    prefix = team_type  # "home" or "away"
    target_dict[f"{prefix}_played"] = get_value(data_dict, [f"matches_played_{prefix}", f"seasonMatchesPlayed_{prefix}"])
    target_dict[f"{prefix}_wins"] = get_value(data_dict, [f"{prefix}_wins", f"seasonWinsNum_{prefix}"])
    target_dict[f"{prefix}_draws"] = get_value(data_dict, [f"{prefix}_draws", f"seasonDrawsNum_{prefix}"])
    target_dict[f"{prefix}_losses"] = get_value(data_dict, [f"{prefix}_losses", f"seasonLossesNum_{prefix}"])
    target_dict[f"{prefix}_goals_scored"] = get_value(data_dict, [f"goals_scored_{prefix}", f"seasonGoals_{prefix}"])
    target_dict[f"{prefix}_goals_conceded"] = get_value(data_dict, [f"goals_conceded_{prefix}", f"seasonConceded_{prefix}"])
    
    # Advanced stats
    target_dict["xg"] = get_value(data_dict, ["xG", "xg", "xg_for_overall"])
    target_dict["xga"] = get_value(data_dict, ["xGA", "xga", "xg_against_avg_overall"])
    target_dict["possession"] = get_value(data_dict, ["possession", "possessionAVG_overall", "Poss"])
    
    # Card stats
    target_dict["cards_total"] = get_value(data_dict, ["cards_total", "seasonCrdYNum_overall", "CrdY"]) + get_value(data_dict, ["seasonCrdRNum_overall", "CrdR"], 0)
    target_dict["yellow_cards"] = get_value(data_dict, ["yellow_cards", "seasonCrdYNum_overall", "CrdY"])
    target_dict["red_cards"] = get_value(data_dict, ["red_cards", "seasonCrdRNum_overall", "CrdR"])
    target_dict["over_3_5_cards_pct"] = get_value(data_dict, ["over_3_5_cards_percentage"])
    
    # If matches played exists, calculate per-game averages
    matches_played = target_dict["played"]
    if matches_played > 0:
        target_dict["cards_per_game"] = round(target_dict["cards_total"] / matches_played, 2)
        
    # Corner stats
    target_dict["corners_for"] = get_value(data_dict, ["corners_for", "seasonCornersFor_overall", "CK"])
    target_dict["corners_against"] = get_value(data_dict, ["corners_against", "seasonCornersAgainst_overall"])
    target_dict["corners_total"] = target_dict["corners_for"] + target_dict["corners_against"]
    target_dict["over_9_5_corners_pct"] = get_value(data_dict, ["over_9_5_corners_percentage"])
    
    # Calculate per-game averages for corners if matches played
    if matches_played > 0:
        target_dict["corners_per_game"] = round(target_dict["corners_total"] / matches_played, 2)

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

def get_nested_value(data_dict, possible_keys, default=0):
    """
    Get a value from a nested dictionary using multiple possible keys
    
    Args:
        data_dict (dict): Dictionary to search
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

def round_stat(value, precision=0):
    """
    Round a statistical value to reduce data size
    
    Args:
        value: The value to round
        precision (int): Decimal precision
        
    Returns:
        int or float: Rounded value
    """
    if value is None:
        return 0
        
    try:
        if precision == 0:
            return int(round(float(value), 0))
        else:
            return round(float(value), precision)
    except (ValueError, TypeError):
        return 0

def adapt_api_data_for_prompt(complete_analysis):
    """
    Adapta os dados coletados da API para o formato esperado pelo format_enhanced_prompt
    
    Args:
        complete_analysis (dict): Dados coletados pelo enhanced_api_client
        
    Returns:
        dict: Dados formatados para o format_enhanced_prompt
    """
    try:
        # Use a função transform_to_optimized_data para garantir a estrutura correta
        return transform_to_optimized_data(
            complete_analysis, 
            complete_analysis.get("basic_stats", {}).get("home_team", {}).get("name", "Home Team"),
            complete_analysis.get("basic_stats", {}).get("away_team", {}).get("name", "Away Team")
        )
    except Exception as e:
        logger.error(f"Erro ao adaptar dados para prompt: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
