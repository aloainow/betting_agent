import requests
import json
import os

# API Configuration
API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"
BASE_URL = "https://api.football-data-api.com"

# Ligas e times para teste
TEST_CASES = [
    {"league": "Premier League", "season_id": 12325, "home": "Arsenal FC", "away": "Chelsea FC"},
    {"league": "La Liga", "season_id": 12316, "home": "Barcelona", "away": "Real Madrid"}
]

def test_api_endpoints():
    """Teste múltiplos endpoints para identificar como os dados estão estruturados"""
    for test_case in TEST_CASES:
        league = test_case["league"]
        season_id = test_case["season_id"]
        home_team = test_case["home"]
        away_team = test_case["away"]
        
        print(f"\n=== Testando {home_team} vs {away_team} ({league}) ===\n")
        
        # 1. Testar league-teams endpoint
        print("1. Testando endpoint league-teams...")
        response = requests.get(
            f"{BASE_URL}/league-teams", 
            params={"key": API_KEY, "season_id": season_id, "include": "stats"},
            timeout=15
        )
        
        if response.status_code == 200:
            teams_data = response.json()
            if "data" in teams_data and isinstance(teams_data["data"], list):
                print(f"Sucesso! Encontrados {len(teams_data['data'])} times.")
                
                # Procurar os times específicos
                home_team_data = None
                away_team_data = None
                
                for team in teams_data["data"]:
                    if "name" in team and team["name"] == home_team:
                        home_team_data = team
                    elif "name" in team and team["name"] == away_team:
                        away_team_data = team
                
                # Salvar os dados brutos dos times específicos
                os.makedirs("debug", exist_ok=True)
                
                if home_team_data:
                    print(f"Time da casa encontrado: {home_team}")
                    with open(f"debug/{home_team.replace(' ', '_')}_raw.json", "w") as f:
                        json.dump(home_team_data, f, indent=2)
                    
                    # Mostrar estrutura de campos principais
                    print(f"Campos principais: {list(home_team_data.keys())}")
                    
                    # Verificar se existe stats e sua estrutura
                    if "stats" in home_team_data:
                        stats_type = type(home_team_data["stats"]).__name__
                        print(f"Campo stats é do tipo: {stats_type}")
                        
                        if stats_type == "dict":
                            print(f"Campos em stats: {list(home_team_data['stats'].keys())}")
                            
                            # Verificar campos específicos
                            fields_to_check = ["xG", "xg", "expected_goals", "yellow_cards", "red_cards"]
                            for field in fields_to_check:
                                if field in home_team_data["stats"]:
                                    print(f"✅ Campo {field} encontrado em stats: {home_team_data['stats'][field]}")
                                else:
                                    print(f"❌ Campo {field} NÃO encontrado em stats")
                            
                            # Verificar possíveis campos de forma alternativos
                            form_fields = ["form", "recent_form", "current_form"]
                            for field in form_fields:
                                if field in home_team_data["stats"]:
                                    print(f"✅ Campo de forma {field} encontrado: {home_team_data['stats'][field]}")
                
                else:
                    print(f"❌ Time da casa não encontrado: {home_team}")
                
                if away_team_data:
                    print(f"Time visitante encontrado: {away_team}")
                    with open(f"debug/{away_team.replace(' ', '_')}_raw.json", "w") as f:
                        json.dump(away_team_data, f, indent=2)
                else:
                    print(f"❌ Time visitante não encontrado: {away_team}")
                
        else:
            print(f"❌ Erro ao acessar league-teams: {response.status_code}")
        
        # 2. Testar endpoint de forma diretamente
        print("\n2. Testando endpoint lastx para dados de forma...")
        
        # Precisamos dos IDs dos times para este endpoint
        home_id = home_team_data.get("id") if home_team_data else None
        away_id = away_team_data.get("id") if away_team_data else None
        
        if home_id:
            form_response = requests.get(
                f"{BASE_URL}/lastx",
                params={"key": API_KEY, "team_id": home_id, "num": 5},
                timeout=15
            )
            
            if form_response.status_code == 200:
                form_data = form_response.json()
                print(f"✅ Dados de forma obtidos para {home_team}")
                with open(f"debug/{home_team.replace(' ', '_')}_form.json", "w") as f:
                    json.dump(form_data, f, indent=2)
                    
                # Verificar estrutura da resposta
                if "data" in form_data and isinstance(form_data["data"], list):
                    print(f"Encontrados {len(form_data['data'])} jogos recentes")
                    if form_data["data"]:
                        print(f"Estrutura de um jogo recente: {list(form_data['data'][0].keys())}")
            else:
                print(f"❌ Erro ao obter forma: {form_response.status_code}")
        
        # 3. Testar endpoint H2H
        print("\n3. Testando endpoint match para dados H2H...")
        if home_id and away_id:
            # Primeiro precisamos encontrar o match_id
            matches_response = requests.get(
                f"{BASE_URL}/league-matches",
                params={"key": API_KEY, "season_id": season_id},
                timeout=15
            )
            
            if matches_response.status_code == 200:
                matches_data = matches_response.json()
                if "data" in matches_data and isinstance(matches_data["data"], list):
                    print(f"Encontrados {len(matches_data['data'])} jogos na liga")
                    
                    # Procurar jogo entre os times
                    match_id = None
                    for match in matches_data["data"]:
                        if "homeID" in match and "awayID" in match:
                            if match["homeID"] == home_id and match["awayID"] == away_id:
                                match_id = match.get("id")
                                break
                    
                    if match_id:
                        print(f"✅ Match ID encontrado: {match_id}")
                        
                        # Obter detalhes do jogo
                        match_response = requests.get(
                            f"{BASE_URL}/match",
                            params={"key": API_KEY, "match_id": match_id},
                            timeout=15
                        )
                        
                        if match_response.status_code == 200:
                            match_details = match_response.json()
                            print("✅ Detalhes do jogo obtidos")
                            with open(f"debug/{home_team.replace(' ', '_')}_vs_{away_team.replace(' ', '_')}_match.json", "w") as f:
                                json.dump(match_details, f, indent=2)
                                
                            # Verificar se há dados H2H
                            if "data" in match_details and "h2h" in match_details["data"]:
                                print("✅ Dados H2H encontrados")
                                print(f"Campos H2H: {list(match_details['data']['h2h'].keys())}")
                            else:
                                print("❌ Dados H2H não encontrados na resposta")
                        else:
                            print(f"❌ Erro ao obter detalhes do jogo: {match_response.status_code}")
                    else:
                        print("❌ Match ID não encontrado")
            else:
                print(f"❌ Erro ao obter jogos da liga: {matches_response.status_code}")
        
        print("\n=== Diagnóstico concluído ===")
        print(f"Arquivos de diagnóstico salvos na pasta 'debug'")

if __name__ == "__main__":
    test_api_endpoints()
