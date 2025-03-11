import requests
import json
import time
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("valueHunter.diagnostic")

# API Configuration
API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"
BASE_URL = "https://api.football-data-api.com"

def run_api_diagnostic(league_name=None, home_team=None, away_team=None):
    """
    Run a comprehensive diagnostic on the FootyStats API connection
    
    Args:
        league_name (str, optional): League to test
        home_team (str, optional): Home team to test
        away_team (str, optional): Away team to test
        
    Returns:
        dict: Diagnostic results
    """
    results = {
        "api_status": None,
        "subscription_status": None,
        "league_status": None,
        "teams_found": [],
        "errors": [],
        "recommendations": []
    }
    
    # Step 1: Basic API test
    logger.info("Testing basic API connection...")
    try:
        response = requests.get(f"{BASE_URL}/league-list", params={"key": API_KEY}, timeout=10)
        results["api_status"] = {
            "status_code": response.status_code,
            "successful": response.status_code == 200
        }
        
        if response.status_code == 200:
            logger.info("✓ API connection successful")
            
            # Parse the data
            data = response.json()
            
            if "data" in data and isinstance(data["data"], list):
                available_leagues = data["data"]
                results["available_leagues"] = len(available_leagues)
                results["subscription_status"] = "active" if available_leagues else "issues"
                
                # Get some sample leagues
                sample_leagues = []
                for league in available_leagues[:5]:
                    if "name" in league and "country" in league:
                        sample_leagues.append(f"{league['name']} ({league['country']})")
                
                results["sample_leagues"] = sample_leagues
                
                # If a specific league was provided, check if it's available
                if league_name:
                    logger.info(f"Looking for league: {league_name}")
                    league_name_lower = league_name.lower()
                    league_found = False
                    season_id = None
                    
                    # First check exact matches
                    for league in available_leagues:
                        league_api_name = f"{league.get('name', '')} ({league.get('country', '')})"
                        if league_api_name.lower() == league_name_lower:
                            league_found = True
                            season_id = league.get('id')
                            season_info = league.get('season', {})
                            results["league_status"] = {
                                "found": True,
                                "id": season_id,
                                "name": league_api_name,
                                "season": season_info
                            }
                            break
                    
                    # If not found, check partial matches
                    if not league_found:
                        for league in available_leagues:
                            league_api_name = league.get('name', '').lower()
                            country = league.get('country', '').lower()
                            
                            # Check if league_name contains the API league name or vice versa
                            if (league_api_name in league_name_lower or 
                                league_name_lower in league_api_name):
                                league_found = True
                                season_id = league.get('id')
                                season_info = league.get('season', {})
                                results["league_status"] = {
                                    "found": True,
                                    "id": season_id,
                                    "name": f"{league.get('name', '')} ({league.get('country', '')})",
                                    "season": season_info,
                                    "match_type": "partial"
                                }
                                break
                    
                    if not league_found:
                        results["league_status"] = {
                            "found": False,
                            "error": f"League '{league_name}' not found in your subscription"
                        }
                        results["errors"].append(f"League '{league_name}' not found in your subscription")
                        results["recommendations"].append("Check if this league is selected in your FootyStats account")
                        results["recommendations"].append("Try using one of the sample leagues shown in the diagnostic")
                    else:
                        # If league was found and teams were provided, check if teams exist
                        if home_team or away_team:
                            if season_id:
                                logger.info(f"Testing teams in league ID {season_id}")
                                team_response = requests.get(
                                    f"{BASE_URL}/league-teams", 
                                    params={"key": API_KEY, "season_id": season_id, "include": "stats"},
                                    timeout=15
                                )
                                
                                if team_response.status_code == 200:
                                    team_data = team_response.json()
                                    
                                    if "data" in team_data and isinstance(team_data["data"], list):
                                        teams = team_data["data"]
                                        team_names = [team.get("name", "") for team in teams if "name" in team]
                                        
                                        results["teams_found"] = team_names
                                        
                                        # Check if home_team exists
                                        if home_team:
                                            home_team_lower = home_team.lower()
                                            home_team_found = False
                                            
                                            for team_name in team_names:
                                                if (team_name.lower() == home_team_lower or
                                                    team_name.lower() in home_team_lower or
                                                    home_team_lower in team_name.lower()):
                                                    home_team_found = True
                                                    break
                                            
                                            if not home_team_found:
                                                results["errors"].append(f"Home team '{home_team}' not found in league")
                                                results["recommendations"].append(f"Check team name spelling or try another team")
                                                
                                                # Show similar teams
                                                similar_teams = []
                                                for team_name in team_names:
                                                    if any(word in team_name.lower() for word in home_team_lower.split()):
                                                        similar_teams.append(team_name)
                                                
                                                if similar_teams:
                                                    results["recommendations"].append(f"Similar teams: {', '.join(similar_teams[:5])}")
                                        
                                        # Check if away_team exists
                                        if away_team:
                                            away_team_lower = away_team.lower()
                                            away_team_found = False
                                            
                                            for team_name in team_names:
                                                if (team_name.lower() == away_team_lower or
                                                    team_name.lower() in away_team_lower or
                                                    away_team_lower in team_name.lower()):
                                                    away_team_found = True
                                                    break
                                            
                                            if not away_team_found:
                                                results["errors"].append(f"Away team '{away_team}' not found in league")
                                                results["recommendations"].append(f"Check team name spelling or try another team")
                                                
                                                # Show similar teams
                                                similar_teams = []
                                                for team_name in team_names:
                                                    if any(word in team_name.lower() for word in away_team_lower.split()):
                                                        similar_teams.append(team_name)
                                                
                                                if similar_teams:
                                                    results["recommendations"].append(f"Similar teams: {', '.join(similar_teams[:5])}")
                                    else:
                                        results["errors"].append("Invalid team data format from API")
                                        results["recommendations"].append("Contact support if this issue persists")
                                else:
                                    results["errors"].append(f"Failed to get teams: Status {team_response.status_code}")
                                    results["recommendations"].append("Check your FootyStats subscription status")
                            else:
                                results["errors"].append("Season ID not found")
                                results["recommendations"].append("Check if this league has current season data")
            else:
                results["errors"].append("Invalid API response format")
                results["recommendations"].append("Check if API key is valid and has the correct permissions")
        else:
            logger.error(f"✗ API connection failed: Status {response.status_code}")
            results["errors"].append(f"API connection failed: Status {response.status_code}")
            
            # Try to parse error message
            try:
                error_data = response.json()
                if "message" in error_data:
                    results["errors"].append(f"API error: {error_data['message']}")
            except:
                results["errors"].append(f"Response: {response.text[:200]}")
            
            results["recommendations"].append("Check if API key is valid")
            results["recommendations"].append("Check your internet connection")
            results["recommendations"].append("Check if FootyStats API is operational")
    
    except Exception as e:
        logger.error(f"Error during API test: {str(e)}")
        results["errors"].append(f"Exception: {str(e)}")
        results["recommendations"].append("Check your internet connection")
        results["recommendations"].append("Contact FootyStats support if issues persist")
    
    # Final recommendations
    if not results["errors"]:
        results["recommendations"].append("Your API connection is working correctly!")
    elif "League not found" in str(results["errors"]):
        results["recommendations"].append("Make sure the league is selected in your FootyStats account")
        results["recommendations"].append("Note that it may take up to 24 hours for newly selected leagues to become available")
    elif "team not found" in str(results["errors"]).lower():
        results["recommendations"].append("Make sure you're selecting teams from the current season")
        results["recommendations"].append("Clear the app cache and try again")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnose FootyStats API connection')
    parser.add_argument('--league', help='League to test')
    parser.add_argument('--home', help='Home team to test')
    parser.add_argument('--away', help='Away team to test')
    
    args = parser.parse_args()
    
    results = run_api_diagnostic(args.league, args.home, args.away)
    
    print("\n==== FootyStats API Diagnostic Results ====\n")
    
    if results["api_status"]["successful"]:
        print("✅ API Connection: Successful")
        print(f"📊 Available Leagues: {results['available_leagues']}")
        
        if "sample_leagues" in results:
            print("\n🏆 Sample Leagues:")
            for i, league in enumerate(results["sample_leagues"], 1):
                print(f"  {i}. {league}")
        
        if "league_status" in results and results["league_status"]:
            if results["league_status"]["found"]:
                print(f"\n✅ League '{results['league_status']['name']}' found")
                print(f"   ID: {results['league_status']['id']}")
                print(f"   Season: {results['league_status']['season']}")
            else:
                print(f"\n❌ League not found: {results['league_status']['error']}")
        
        if "teams_found" in results and results["teams_found"]:
            print(f"\n⚽ Found {len(results['teams_found'])} teams in the league")
            print("  Sample teams:")
            for i, team in enumerate(results["teams_found"][:10], 1):
                print(f"  {i}. {team}")
    else:
        print("❌ API Connection Failed")
        print(f"   Status Code: {results['api_status']['status_code']}")
    
    if results["errors"]:
        print("\n❌ Errors:")
        for i, error in enumerate(results["errors"], 1):
            print(f"  {i}. {error}")
    
    print("\n💡 Recommendations:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"  {i}. {rec}")
    
    print("\n===================================")
