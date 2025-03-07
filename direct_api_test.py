# test_correct_api.py - Test the correctly configured FootyStats API
import requests
import json

# Correct configuration from the documentation
API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"
BASE_URL = "https://api.football-data-api.com"

def test_with_example():
    """Test using the example key to verify endpoint functionality"""
    print("\nTesting with example key...")
    try:
        response = requests.get(f"{BASE_URL}/league-tables?key=example&league_id=1625", timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("✓ Success with example key!")
            data = response.json()
            if "data" in data:
                print(f"✓ Valid response structure")
            else:
                print("✗ Unexpected response structure")
        else:
            print(f"✗ Failed with status code {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

def test_with_real_key():
    """Test using your actual API key"""
    print("\nTesting with your API key...")
    try:
        response = requests.get(f"{BASE_URL}/league-teams?key={API_KEY}", timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("✓ Success with your API key!")
            data = response.json()
            if "data" in data:
                print(f"✓ Found {len(data.get('data', []))} teams")
                if len(data.get('data', [])) > 0:
                    first_team = data['data'][0]
                    print(f"Example team: {first_team.get('name', 'Unknown')}")
            else:
                print("✗ Unexpected response structure")
        else:
            print(f"✗ Failed with status code {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

def test_league_teams():
    """Test getting teams for a specific league"""
    print("\nTesting league teams API...")
    try:
        # Using example key and Premier League ID
        response = requests.get(f"{BASE_URL}/league-teams?key=example&league_id=1625", timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("✓ Success getting league teams!")
            data = response.json()
            if "data" in data and len(data['data']) > 0:
                print(f"✓ Found {len(data['data'])} teams")
                team_names = [team.get('name', 'Unknown') for team in data['data'][:5]]
                print(f"Sample teams: {', '.join(team_names)}")
            else:
                print("✗ No teams found in response")
        else:
            print(f"✗ Failed with status code {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

if __name__ == "__main__":
    print("FootyStats API Test")
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
    
    # Run tests
    test_with_example()
    test_with_real_key()
    test_league_teams()
    
    print("\nTests complete. If any test succeeded, the API is working correctly.")
