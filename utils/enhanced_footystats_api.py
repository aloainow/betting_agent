import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta

# Configuração de logging
logger = logging.getLogger("valueHunter.enhanced_api")

# Referência à variável global do diretório de dados
try:
    from utils.core import DATA_DIR
except ImportError:
    DATA_DIR = os.environ.get("DATA_DIR", "data")
    if "RENDER" in os.environ:
        DATA_DIR = "/mnt/value-hunter-data"

# API Configuration
API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"
BASE_URL = "https://api.football-data-api.com"

# Cache settings
CACHE_DIR = os.path.join(DATA_DIR, "api_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_DURATION = 6 * 60 * 60  # 6 hours in seconds

# Create a cache file path
def get_cache_path(endpoint, params):
    """Create a cache file path based on endpoint and parameters"""
    param_str = "_".join([f"{k}_{v}" for k, v in sorted(params.items()) if k != "key"])
    filename = f"{endpoint}_{param_str}.json"
    # Make sure filename is valid and not too long
    filename = "".join(c for c in filename if c.isalnum() or c in "_-.")[:100]
    return os.path.join(CACHE_DIR, filename)

# Cache functions
def save_to_cache(data, endpoint, params):
    """Save data to cache"""
    cache_path = get_cache_path(endpoint, params)
    try:
        cache_data = {
            "timestamp": time.time(),
            "data": data
        }
        with open(cache_path, "w") as f:
            json.dump(cache_data, f)
        logger.info(f"Saved to cache: {cache_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to cache: {str(e)}")
        return False

def get_from_cache(endpoint, params, max_age=CACHE_DURATION):
    """Get data from cache if not expired"""
    cache_path = get_cache_path(endpoint, params)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid
            if time.time() - cache_data["timestamp"] < max_age:
                logger.info(f"Using cached data: {cache_path}")
                return cache_data["data"]
        except Exception as e:
            logger.error(f"Error reading cache: {str(e)}")
    
    return None

# Base API request function
def api_request(endpoint, params, use_cache=True):
    """Make an API request with caching"""
    # Check cache first
    if use_cache:
        cached_data = get_from_cache(endpoint, params)
        if cached_data:
            return cached_data
    
    # Ensure API key is in params
    if "key" not in params:
        params["key"] = API_KEY
    
    # Make request
    url = f"{BASE_URL}/{endpoint}"
    try:
        logger.info(f"API Request: {url} - Params: {params}")
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if use_cache:
                    save_to_cache(data, endpoint, params)
                return data
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response.text[:200]}...")
                return None
        else:
            logger.error(f"API error: {response.status_code} - {response.text[:200]}...")
            return None
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        return None

# Functions to get team_id and match_id information

def get_teams_with_ids(season_id, use_cache=True):
    """
    Get all teams in a league season with their IDs
    
    Args:
        season_id (int): The season/league ID
        use_cache (bool): Whether to use cached data
        
    Returns:
        list: List of team data including IDs
    """
    params = {
        "season_id": season_id,
        "include": "stats"
    }
    
    response = api_request("league-teams", params, use_cache)
    
    if response and "data" in response and isinstance(response["data"], list):
        teams = response["data"]
        logger.info(f"Found {len(teams)} teams for season_id {season_id}")
        return teams
    
    logger.error(f"Failed to get teams for season_id {season_id}")
    return []

def get_team_id_by_name(team_name, season_id=None, all_teams=None):
    """
    Find a team's ID by name
    
    Args:
        team_name (str): The team name to search for
        season_id (int, optional): Season ID to search in (if not providing all_teams)
        all_teams (list, optional): Pre-fetched list of teams
        
    Returns:
        int: Team ID or None if not found
    """
    # If all_teams not provided, fetch them
    teams = all_teams or (get_teams_with_ids(season_id) if season_id else [])
    
    if not teams:
        logger.error("No teams available to search")
        return None
    
    # Normalize team name for comparison
    team_name_lower = team_name.lower()
    
    # First try exact match
    for team in teams:
        if team.get("name", "").lower() == team_name_lower:
            logger.info(f"Exact match found for {team_name}: ID {team.get('id')}")
            return team.get("id")
    
    # Then try partial match
    for team in teams:
        if team_name_lower in team.get("name", "").lower() or team.get("name", "").lower() in team_name_lower:
            logger.info(f"Partial match found for {team_name}: {team.get('name')} (ID {team.get('id')})")
            return team.get("id")
    
    logger.error(f"No team ID found for {team_name}")
    return None

def get_league_matches(season_id, use_cache=True):
    """
    Get all matches in a league season
    
    Args:
        season_id (int): The season/league ID
        use_cache (bool): Whether to use cached data
        
    Returns:
        list: List of matches with IDs
    """
    params = {
        "season_id": season_id
    }
    
    response = api_request("league-matches", params, use_cache)
    
    if response and "data" in response and isinstance(response["data"], list):
        matches = response["data"]
        logger.info(f"Found {len(matches)} matches for season_id {season_id}")
        return matches
    
    logger.error(f"Failed to get matches for season_id {season_id}")
    return []

def find_match_id(home_team, away_team, season_id=None, all_matches=None):
    """
    Find a match ID between two teams
    
    Args:
        home_team (str): Home team name
        away_team (str): Away team name
        season_id (int, optional): Season ID to search in (if not providing all_matches)
        all_matches (list, optional): Pre-fetched list of matches
        
    Returns:
        int: Match ID or None if not found
    """
    # If all_matches not provided, fetch them
    matches = all_matches or (get_league_matches(season_id) if season_id else [])
    
    if not matches:
        logger.error("No matches available to search")
        return None
    
    # Normalize team names for comparison
    home_team_lower = home_team.lower()
    away_team_lower = away_team.lower()
    
    # Look for match with these teams
    for match in matches:
        # Get team names from match data
        match_home = match.get("home_name", "").lower()
        match_away = match.get("away_name", "").lower()
        
        # Check if this is the match we're looking for
        home_match = home_team_lower == match_home or home_team_lower in match_home or match_home in home_team_lower
        away_match = away_team_lower == match_away or away_team_lower in match_away or match_away in away_team_lower
        
        if home_match and away_match:
            logger.info(f"Match found: {match.get('home_name')} vs {match.get('away_name')} (ID {match.get('id')})")
            return match.get("id")
    
    # Try with reversed teams (sometimes home/away can be switched)
    for match in matches:
        match_home = match.get("home_name", "").lower()
        match_away = match.get("away_name", "").lower()
        
        home_match = away_team_lower == match_home or away_team_lower in match_home or match_home in away_team_lower
        away_match = home_team_lower == match_away or home_team_lower in match_away or match_away in home_team_lower
        
        if home_match and away_match:
            logger.info(f"Match found (reversed): {match.get('home_name')} vs {match.get('away_name')} (ID {match.get('id')})")
            return match.get("id")
    
    logger.error(f"No match ID found for {home_team} vs {away_team}")
    return None

# Enhanced API functions to get statistics

def get_team_stats(team_id, use_cache=True):
    """
    Get detailed statistics for a team
    
    Args:
        team_id (int): The team ID
        use_cache (bool): Whether to use cached data
        
    Returns:
        dict: Team statistics
    """
    params = {
        "team_id": team_id,
        "include": "stats"
    }
    
    response = api_request("team", params, use_cache)
    
    if response and "data" in response:
        team_data = response["data"]
        logger.info(f"Got stats for team ID {team_id}")
        return team_data
    
    logger.error(f"Failed to get stats for team ID {team_id}")
    return None

def get_team_last_matches(team_id, num_matches=5, use_cache=True):
    """
    Get statistics for a team's last X matches
    
    Args:
        team_id (int): The team ID
        num_matches (int): Number of last matches (5, 6, or 10)
        use_cache (bool): Whether to use cached data
        
    Returns:
        dict: Last X matches statistics
    """
    # Validate num_matches (API only supports 5, 6, or 10)
    if num_matches not in [5, 6, 10]:
        num_matches = 5
    
    params = {
        "team_id": team_id,
        "num": num_matches
    }
    
    response = api_request("lastx", params, use_cache)
    
    if response and "data" in response:
        last_matches = response["data"]
        logger.info(f"Got last {num_matches} matches for team ID {team_id}")
        return last_matches
    
    logger.error(f"Failed to get last {num_matches} matches for team ID {team_id}")
    return None

def get_match_details(match_id, use_cache=True):
    """
    Get detailed statistics for a match
    
    Args:
        match_id (int): The match ID
        use_cache (bool): Whether to use cached data
        
    Returns:
        dict: Match statistics including H2H and odds
    """
    params = {
        "match_id": match_id
    }
    
    response = api_request("match", params, use_cache)
    
    if response and "data" in response:
        match_data = response["data"]
        logger.info(f"Got details for match ID {match_id}")
        return match_data
    
    logger.error(f"Failed to get details for match ID {match_id}")
    return None

def get_league_table(season_id, use_cache=True):
    """
    Get league table for a season
    
    Args:
        season_id (int): The season/league ID
        use_cache (bool): Whether to use cached data
        
    Returns:
        dict: League table data
    """
    params = {
        "season_id": season_id
    }
    
    response = api_request("league-tables", params, use_cache)
    
    if response and "data" in response:
        table_data = response["data"]
        logger.info(f"Got league table for season ID {season_id}")
        return table_data
    
    logger.error(f"Failed to get league table for season ID {season_id}")
    return None

def get_btts_stats(use_cache=True):
    """
    Get Both Teams To Score (BTTS) statistics
    
    Returns:
        dict: BTTS statistics
    """
    response = api_request("stats-data-btts", {}, use_cache)
    
    if response and "data" in response:
        btts_data = response["data"]
        logger.info("Got BTTS stats")
        return btts_data
    
    logger.error("Failed to get BTTS stats")
    return None

def get_over25_stats(use_cache=True):
    """
    Get Over 2.5 Goals statistics
    
    Returns:
        dict: Over 2.5 goals statistics
    """
    response = api_request("stats-data-over25", {}, use_cache)
    
    if response and "data" in response:
        over25_data = response["data"]
        logger.info("Got Over 2.5 goals stats")
        return over25_data
    
    logger.error("Failed to get Over 2.5 goals stats")
    return None

# Main function to get fixture statistics
def get_fixture_statistics(home_team, away_team, selected_league, use_cache=True):
    """
    Get comprehensive statistics for a fixture between two teams
    
    Args:
        home_team (str): Home team name
        away_team (str): Away team name
        selected_league (str): League name
        use_cache (bool): Whether to use cached data
        
    Returns:
        dict: Comprehensive fixture statistics
    """
    try:
        logger.info(f"Getting fixture statistics for {home_team} vs {away_team} in {selected_league}")
        
        # Step 1: Find the league/season ID
        from utils.footystats_api import find_league_id_by_name
        season_id = find_league_id_by_name(selected_league)
        
        if not season_id:
            logger.error(f"League ID not found for {selected_league}")
            return None
        
        logger.info(f"Found season ID {season_id} for {selected_league}")
        
        # Step 2: Get all teams in the league
        teams = get_teams_with_ids(season_id, use_cache)
        
        if not teams:
            logger.error(f"No teams found for league {selected_league}")
            return None
        
        # Step 3: Find team IDs
        home_team_id = get_team_id_by_name(home_team, all_teams=teams)
        away_team_id = get_team_id_by_name(away_team, all_teams=teams)
        
        if not home_team_id:
            logger.error(f"Team ID not found for {home_team}")
            return None
            
        if not away_team_id:
            logger.error(f"Team ID not found for {away_team}")
            return None
        
        logger.info(f"Found team IDs: {home_team} ({home_team_id}) vs {away_team} ({away_team_id})")
        
        # Step 4: Get team statistics
        home_team_stats = get_team_stats(home_team_id, use_cache)
        away_team_stats = get_team_stats(away_team_id, use_cache)
        
        if not home_team_stats or not away_team_stats:
            logger.error("Failed to get team statistics")
            return None
        
        # Step 5: Get team form (last 5 matches)
        home_team_form = get_team_last_matches(home_team_id, 5, use_cache)
        away_team_form = get_team_last_matches(away_team_id, 5, use_cache)
        
        # Step 6: Try to find a match between these teams
        matches = get_league_matches(season_id, use_cache)
        match_id = find_match_id(home_team, away_team, all_matches=matches)
        
        # Step 7: Get match details if available
        match_details = get_match_details(match_id, use_cache) if match_id else None
        
        # Step 8: Get league table
        league_table = get_league_table(season_id, use_cache)
        
        # Step 9: Compile all statistics
        fixture_stats = {
            "league": {
                "id": season_id,
                "name": selected_league,
                "table": league_table
            },
            "teams": {
                "home": {
                    "id": home_team_id,
                    "name": home_team
                },
                "away": {
                    "id": away_team_id,
                    "name": away_team
                }
            },
            "match": {
                "id": match_id,
                "details": match_details
            },
            "basic_stats": {
                "home_team": {"name": home_team, "stats": home_team_stats},
                "away_team": {"name": away_team, "stats": away_team_stats},
                "referee": match_details.get("referee", "Não informado") if match_details else "Não informado"
            },
            "advanced_stats": {
                "home": extract_advanced_stats(home_team_stats),
                "away": extract_advanced_stats(away_team_stats)
            },
            "team_form": {
                "home": home_team_form,
                "away": away_team_form
            },
            "head_to_head": extract_h2h_stats(match_details) if match_details else {}
        }
        
        logger.info(f"Successfully compiled fixture statistics for {home_team} vs {away_team}")
        return fixture_stats
        
    except Exception as e:
        logger.error(f"Error getting fixture statistics: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def extract_advanced_stats(team_data):
    """Extract advanced stats from team data"""
    stats = {}
    
    if not team_data:
        return stats
    
    # Extract advanced statistics if available
    if "stats" in team_data and isinstance(team_data["stats"], dict):
        advanced_stats = team_data["stats"]
        
        # Common advanced metrics
        stats["ppda"] = advanced_stats.get("ppda", "N/A")
        stats["deep_completions"] = advanced_stats.get("deep_completions", "N/A")
        stats["shot_quality"] = advanced_stats.get("shot_quality", "N/A")
        stats["xg_per_shot"] = advanced_stats.get("xg_per_shot", "N/A")
        stats["build_up_disruption"] = advanced_stats.get("build_up_disruption", "N/A")
        
        # Add any other advanced metrics
        for key, value in advanced_stats.items():
            if key not in stats:
                stats[key] = value
    
    return stats

def extract_h2h_stats(match_data):
    """Extract head-to-head stats from match data"""
    h2h = {}
    
    if not match_data:
        return h2h
    
    # Extract H2H data if available
    if "h2h" in match_data and isinstance(match_data["h2h"], dict):
        h2h_data = match_data["h2h"]
        
        # Basic H2H statistics
        h2h["total_matches"] = h2h_data.get("total_matches", 0)
        h2h["home_wins"] = h2h_data.get("home_wins", 0)
        h2h["away_wins"] = h2h_data.get("away_wins", 0)
        h2h["draws"] = h2h_data.get("draws", 0)
        
        # Goals statistics
        h2h["average_goals"] = h2h_data.get("average_goals", 0)
        h2h["over_2_5_percentage"] = h2h_data.get("over_2_5_percentage", 0)
        h2h["btts_percentage"] = h2h_data.get("btts_percentage", 0)
        
        # Other statistics
        h2h["average_corners"] = h2h_data.get("average_corners", 0)
        h2h["average_cards"] = h2h_data.get("average_cards", 0)
        
        # Previous matches
        h2h["previous_matches"] = h2h_data.get("previous_matches", [])
    
    return h2h

def convert_api_stats_to_df_format(fixture_stats):
    """
    Convert comprehensive fixture statistics to DataFrame format
    
    Args:
        fixture_stats (dict): Fixture statistics from get_fixture_statistics()
        
    Returns:
        pandas.DataFrame: DataFrame with team statistics
    """
    import pandas as pd
    
    try:
        if not fixture_stats or not isinstance(fixture_stats, dict):
            logger.error("Invalid fixture statistics")
            return None
        
        # Extract basic information
        home_team = fixture_stats["teams"]["home"]["name"]
        away_team = fixture_stats["teams"]["away"]["name"]
        
        # Get stats objects
        home_stats = fixture_stats["basic_stats"]["home_team"]["stats"]
        away_stats = fixture_stats["basic_stats"]["away_team"]["stats"]
        
        # Create DataFrame with required columns
        # Extract actual statistics from the stats objects
        home_matches = home_stats.get("stats", {}).get("matches_played", 0)
        home_wins = home_stats.get("stats", {}).get("total_wins", 0)
        home_draws = home_stats.get("stats", {}).get("total_draws", 0)
        home_losses = home_stats.get("stats", {}).get("total_losses", 0)
        home_goals_scored = home_stats.get("stats", {}).get("goals_scored", 0)
        home_goals_against = home_stats.get("stats", {}).get("goals_against", 0)
        home_xg = home_stats.get("stats", {}).get("xg", 0)
        home_xga = home_stats.get("stats", {}).get("xga", 0)
        home_possession = home_stats.get("stats", {}).get("possession", 50)
        
        away_matches = away_stats.get("stats", {}).get("matches_played", 0)
        away_wins = away_stats.get("stats", {}).get("total_wins", 0)
        away_draws = away_stats.get("stats", {}).get("total_draws", 0)
        away_losses = away_stats.get("stats", {}).get("total_losses", 0)
        away_goals_scored = away_stats.get("stats", {}).get("goals_scored", 0)
        away_goals_against = away_stats.get("stats", {}).get("goals_against", 0)
        away_xg = away_stats.get("stats", {}).get("xg", 0)
        away_xga = away_stats.get("stats", {}).get("xga", 0)
        away_possession = away_stats.get("stats", {}).get("possession", 50)
        
        # Create DataFrame
        df = pd.DataFrame({
            'Squad': [home_team, away_team],
            'MP': [home_matches, away_matches],
            'W': [home_wins, away_wins],
            'D': [home_draws, away_draws],
            'L': [home_losses, away_losses],
            'Gls': [home_goals_scored, away_goals_scored],
            'GA': [home_goals_against, away_goals_against],
            'xG': [home_xg, away_xg],
            'xGA': [home_xga, away_xga],
            'Poss': [home_possession, away_possession]
        })
        
        # Add additional columns if available
        additional_columns = {
            'Sh': ('shots', 0),
            'SoT': ('shots_on_target', 0),
            'SoT%': ('shots_on_target_percentage', 0),
            'G/Sh': ('goals_per_shot', 0),
            'Cmp': ('passes_completed', 0),
            'Att': ('passes_attempted', 0),
            'Cmp%': ('pass_completion', 0),
            'PrgP': ('progressive_passes', 0),
            'CrdY': ('yellow_cards', 0),
            'CrdR': ('red_cards', 0),
            'Fls': ('fouls', 0),
            'CK': ('corners', 0)
        }
        
        for col, (stat_name, default) in additional_columns.items():
            home_val = home_stats.get("stats", {}).get(stat_name, default)
            away_val = away_stats.get("stats", {}).get(stat_name, default)
            df[col] = [home_val, away_val]
        
        logger.info(f"Successfully created DataFrame with shape {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"Error converting to DataFrame: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
