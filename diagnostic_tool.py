import requests
import sys
import json
import os
import time

# API Configuration
API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"
BASE_URL = "https://api.football-data-api.com"

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def get_league_id(league_name):
    """Obter o ID da liga a partir do nome"""
    print(f"{Colors.BLUE}Buscando ID para liga: {league_name}{Colors.ENDC}")
    
    # Iniciar com uma requisição para listar todas as ligas disponíveis
    try:
        response = requests.get(f"{BASE_URL}/league-list", params={"key": API_KEY}, timeout=15)
        
        if response.status_code != 200:
            print(f"{Colors.RED}Erro ao buscar lista de ligas: {response.status_code}{Colors.ENDC}")
            return None
        
        data = response.json()
        
        if "data" not in data or not isinstance(data["data"], list):
            print(f"{Colors.RED}Formato de resposta inválido{Colors.ENDC}")
            return None
        
        # Procurar a liga pelo nome (correspondência parcial)
        league_id = None
        league_name_lower = league_name.lower()
        
        # Primeiro tentar correspondência exata
        for league in data["data"]:
            league_full_name = f"{league.get('name', '')} ({league.get('country', '')})"
            if league_full_name.lower() == league_name_lower:
                league_id = league.get("id")
                print(f"{Colors.GREEN}Correspondência exata! Liga: {league_full_name}, ID: {league_id}{Colors.ENDC}")
                print(f"{Colors.BLUE}Informações da temporada: {league.get('season', 'N/A')}{Colors.ENDC}")
                return league_id
        
        # Se não encontrou correspondência exata, tentar correspondência parcial
        matches = []
        for league in data["data"]:
            league_api_name = league.get("name", "").lower()
            if league_name_lower in league_api_name or league_api_name in league_name_lower:
                matches.append((league.get("id"), f"{league.get('name', '')} ({league.get('country', '')})"))
        
        if matches:
            print(f"{Colors.YELLOW}Encontradas {len(matches)} ligas parcialmente correspondentes:{Colors.ENDC}")
            for idx, (lid, lname) in enumerate(matches, 1):
                print(f"{idx}. {lname} (ID: {lid})")
            
            if len(matches) == 1:
                return matches[0][0]
                
            # Se houver múltiplas correspondências, perguntar qual usar
            choice = input(f"{Colors.BOLD}Digite o número da liga correta (ou Enter para usar a primeira): {Colors.ENDC}")
            if choice.strip() and choice.isdigit() and 1 <= int(choice) <= len(matches):
                return matches[int(choice)-1][0]
            elif not choice.strip():
                return matches[0][0]
        
        print(f"{Colors.RED}Nenhuma correspondência encontrada para: {league_name}{Colors.ENDC}")
        print(f"{Colors.YELLOW}Ligas disponíveis incluem:{Colors.ENDC}")
        for i, league in enumerate(data["data"][:10], 1):
            league_full_name = f"{league.get('name', '')} ({league.get('country', '')})"
            print(f"{i}. {league_full_name}")
        return None
    
    except Exception as e:
        print(f"{Colors.RED}Erro ao buscar ID da liga: {str(e)}{Colors.ENDC}")
        return None

def list_teams_for_league(league_id):
    """Listar todos os times disponíveis em uma liga"""
    print(f"{Colors.BLUE}Buscando times para liga ID: {league_id}{Colors.ENDC}")
    
    try:
        # Buscar times da liga
        response = requests.get(
            f"{BASE_URL}/league-teams", 
            params={"key": API_KEY, "season_id": league_id, "include": "stats"},
            timeout=15
        )
        
        if response.status_code != 200:
            print(f"{Colors.RED}Erro ao buscar times: {response.status_code}{Colors.ENDC}")
            
            # Tentar extrair mensagem de erro
            try:
                error_data = response.json()
                if "message" in error_data:
                    print(f"{Colors.RED}Mensagem da API: {error_data['message']}{Colors.ENDC}")
            except:
                pass
                
            return []
        
        data = response.json()
        
        if "data" not in data or not isinstance(data["data"], list):
            print(f"{Colors.RED}Formato de resposta inválido{Colors.ENDC}")
            return []
        
        teams = data["data"]
        
        if not teams:
            print(f"{Colors.YELLOW}Nenhum time encontrado para esta liga!{Colors.ENDC}")
            return []
        
        print(f"{Colors.GREEN}Encontrados {len(teams)} times!{Colors.ENDC}")
        
        # Organizar times alfabeticamente
        team_names = []
        for team in teams:
            team_id = team.get("id")
            team_name = team.get("name", "Unknown")
            if team_id and team_name != "Unknown":
                team_names.append((team_id, team_name))
        
        team_names.sort(key=lambda x: x[1])
        
        return team_names
    
    except Exception as e:
        print(f"{Colors.RED}Erro ao buscar times: {str(e)}{Colors.ENDC}")
        return []

def diagnostic_for_match(league_id, home_team_id, away_team_id):
    """Executar diagnóstico completo para um jogo específico"""
    print(f"{Colors.BLUE}Diagnóstico para jogo entre times {home_team_id} e {away_team_id}{Colors.ENDC}")
    
    # Etapa 1: Verificar se conseguimos obter o match_id para o confronto
    try:
        print(f"{Colors.BLUE}Buscando match_id para o confronto...{Colors.ENDC}")
        response = requests.get(
            f"{BASE_URL}/league-matches",
            params={"key": API_KEY, "season_id": league_id},
            timeout=15
        )
        
        if response.status_code != 200:
            print(f"{Colors.RED}Erro ao buscar partidas: {response.status_code}{Colors.ENDC}")
            return
        
        data = response.json()
        
        if "data" not in data or not isinstance(data["data"], list):
            print(f"{Colors.RED}Formato de resposta inválido{Colors.ENDC}")
            return
        
        matches = data["data"]
        
        # Procurar jogo com estes times
        match_id = None
        for match in matches:
            if "homeID" in match and "awayID" in match:
                if match["homeID"] == home_team_id and match["awayID"] == away_team_id:
                    match_id = match.get("id")
                    print(f"{Colors.GREEN}Match ID encontrado: {match_id}{Colors.ENDC}")
                    print(f"Status do jogo: {match.get('status', 'N/A')}")
                    print(f"Data do jogo: {match.get('date', 'N/A')}")
                    break
        
        if not match_id:
            print(f"{Colors.YELLOW}Nenhum match_id encontrado para confronto direto entre os times.{Colors.ENDC}")
            print(f"{Colors.YELLOW}Isso pode ocorrer se os times não se enfrentarem na temporada atual.{Colors.ENDC}")
        else:
            # Etapa 2: Obter detalhes do jogo
            print(f"{Colors.BLUE}Buscando detalhes do jogo...{Colors.ENDC}")
            match_response = requests.get(
                f"{BASE_URL}/match",
                params={"key": API_KEY, "match_id": match_id},
                timeout=15
            )
            
            if match_response.status_code != 200:
                print(f"{Colors.RED}Erro ao buscar detalhes do jogo: {match_response.status_code}{Colors.ENDC}")
                return
            
            match_data = match_response.json()
            
            if "data" not in match_data:
                print(f"{Colors.RED}Formato de resposta inválido para detalhes do jogo{Colors.ENDC}")
                return
            
            # Verificar se há dados de H2H
            if "h2h" in match_data["data"]:
                h2h = match_data["data"]["h2h"]
                print(f"{Colors.GREEN}Dados H2H encontrados!{Colors.ENDC}")
                print(f"Jogos totais: {h2h.get('total_matches', 0)}")
                print(f"Vitórias casa: {h2h.get('home_wins', 0)}")
                print(f"Vitórias visitante: {h2h.get('away_wins', 0)}")
                print(f"Empates: {h2h.get('draws', 0)}")
            else:
                print(f"{Colors.YELLOW}Dados H2H não disponíveis para este jogo.{Colors.ENDC}")
    
    except Exception as e:
        print(f"{Colors.RED}Erro durante diagnóstico: {str(e)}{Colors.ENDC}")

def run_diagnostic():
    """Executar diagnóstico completo com interação do usuário"""
    print(f"{Colors.BOLD}{Colors.BLUE}=== DIAGNÓSTICO DA API FOOTYSTATS ==={Colors.ENDC}")
    
    # Etapa 1: Verificar conexão com a API
    print(f"{Colors.BOLD}Verificando conexão com a API...{Colors.ENDC}")
    try:
        response = requests.get(f"{BASE_URL}/league-list", params={"key": API_KEY}, timeout=10)
        
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ Conexão com API bem-sucedida!{Colors.ENDC}")
            
            data = response.json()
            if "data" in data and isinstance(data["data"], list):
                print(f"{Colors.GREEN}✓ {len(data['data'])} ligas disponíveis na sua assinatura{Colors.ENDC}")
            else:
                print(f"{Colors.RED}✗ Formato de resposta inválido{Colors.ENDC}")
        else:
            print(f"{Colors.RED}✗ Erro na conexão com API: Status {response.status_code}{Colors.ENDC}")
            print(f"{Colors.RED}Detalhes: {response.text[:200]}{Colors.ENDC}")
            return
    except Exception as e:
        print(f"{Colors.RED}✗ Erro ao conectar com API: {str(e)}{Colors.ENDC}")
        return
    
    # Etapa 2: Obter nome da liga
    league_name = input(f"{Colors.BOLD}Digite o nome da liga (ex: Champions League): {Colors.ENDC}")
    if not league_name.strip():
        print(f"{Colors.RED}Nome da liga não fornecido. Abortando.{Colors.ENDC}")
        return
    
    # Etapa 3: Obter ID da liga
    league_id = get_league_id(league_name)
    if not league_id:
        return
    
    # Etapa 4: Listar times
    teams = list_teams_for_league(league_id)
    
    if not teams:
        return
    
    print(f"{Colors.GREEN}==== Times disponíveis na liga ===={Colors.ENDC}")
    
    # Mostrar times organizados em colunas
    COLUMNS = 3
    teams_per_column = max(1, (len(teams) + COLUMNS - 1) // COLUMNS)
    
    for i in range(0, teams_per_column):
        row = []
        for j in range(COLUMNS):
            idx = i + j * teams_per_column
            if idx < len(teams):
                team_id, team_name = teams[idx]
                row.append(f"{team_name:<30} (ID: {team_id})")
            else:
                row.append("")
        print(" | ".join(row))
    
    print(f"{Colors.YELLOW}Total: {len(teams)} times{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}===================================={Colors.ENDC}")
    
    # Etapa 5: Diagnóstico para um jogo específico (opcional)
    if len(teams) >= 2:
        do_match = input(f"{Colors.BOLD}Deseja testar a análise para um jogo específico? (s/n): {Colors.ENDC}")
        if do_match.lower() == 's':
            print(f"{Colors.BLUE}Escolhendo times para testar estatísticas...{Colors.ENDC}")
            
            # Para home team
            print(f"{Colors.YELLOW}Times disponíveis para casa:{Colors.ENDC}")
            for i, (team_id, team_name) in enumerate(teams[:10], 1):
                print(f"{i}. {team_name}")
            
            home_choice = input(f"{Colors.BOLD}Digite o número do time da casa: {Colors.ENDC}")
            if not home_choice.strip() or not home_choice.isdigit() or int(home_choice) < 1 or int(home_choice) > len(teams):
                print(f"{Colors.RED}Escolha inválida. Abortando.{Colors.ENDC}")
                return
            
            home_team_id, home_team_name = teams[int(home_choice) - 1]
            
            # Para away team
            print(f"{Colors.YELLOW}Times disponíveis para visitante:{Colors.ENDC}")
            for i, (team_id, team_name) in enumerate(teams[:10], 1):
                if team_id != home_team_id:  # Não mostrar o mesmo time
                    print(f"{i}. {team_name}")
            
            away_choice = input(f"{Colors.BOLD}Digite o número do time visitante: {Colors.ENDC}")
            if not away_choice.strip() or not away_choice.isdigit() or int(away_choice) < 1 or int(away_choice) > len(teams):
                print(f"{Colors.RED}Escolha inválida. Abortando.{Colors.ENDC}")
                return
            
            away_team_id, away_team_name = teams[int(away_choice) - 1]
            
            # Executar diagnóstico específico para o jogo
            print(f"{Colors.BLUE}Testando estatísticas para {home_team_name} vs {away_team_name}{Colors.ENDC}")
            diagnostic_for_match(league_id, home_team_id, away_team_id)
    
    # Etapa 6: Salvar listagem de times em arquivo (opcional)
    save_file = input(f"{Colors.BOLD}Deseja salvar a lista de times em um arquivo? (s/n): {Colors.ENDC}")
    if save_file.lower() == 's':
        filename = f"times_{league_name.replace(' ', '_')}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Times da liga: {league_name} (ID: {league_id})\n")
                f.write("=" * 50 + "\n\n")
                for team_id, team_name in teams:
                    f.write(f"{team_name} (ID: {team_id})\n")
            print(f"{Colors.GREEN}Lista de times salva em: {filename}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}Erro ao salvar arquivo: {str(e)}{Colors.ENDC}")

if __name__ == "__main__":
    run_diagnostic()
