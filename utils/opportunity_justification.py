"""
Módulo para geração de justificativas para oportunidades identificadas na análise.
"""
import logging
import re
import traceback

# Configuração de logging
logger = logging.getLogger("valueHunter.opportunity_justification")

def generate_opportunity_justification(opportunity_name, real_prob, stats_data, home_team, away_team):
    """
    Gera uma justificativa personalizada para uma oportunidade identificada
    baseada nos dados estatísticos disponíveis.
    
    Args:
        opportunity_name (str): Nome da oportunidade (ex: "Flamengo", "Over 2.5 Gols")
        real_prob (float): Probabilidade real calculada
        stats_data (dict): Dados estatísticos completos
        home_team (str): Nome do time da casa
        away_team (str): Nome do time visitante
        
    Returns:
        str: Justificativa formatada
    """
    try:
        # Inicializar justificativa
        justification = ""
        
        # Verificar a presença dos dados essenciais
        if not stats_data or not isinstance(stats_data, dict):
            return ""
            
        if "home_team" not in stats_data or "away_team" not in stats_data:
            return ""
            
        # Extrair dados relevantes
        home_stats = stats_data.get("home_team", {})
        away_stats = stats_data.get("away_team", {})
        h2h_stats = stats_data.get("h2h", {})
        
        # 1. Money Line (Vitória de um time)
        if opportunity_name == home_team:
            # Justificativa para vitória do time da casa
            home_wins = home_stats.get("wins", 0)
            home_played = home_stats.get("played", 1)
            home_win_percent = (home_wins / home_played) * 100 if home_played > 0 else 0
            
            # Gols marcados e sofridos
            home_goals_scored = home_stats.get("goals_scored", 0)
            home_goals_conceded = home_stats.get("goals_conceded", 0)
            home_avg_goals = home_stats.get("avg_goals_scored", 0)
            
            # Forma recente (últimos 5 jogos)
            home_form_str = home_stats.get("formRun_overall", "")
            home_form_points = 0
            
            if isinstance(home_form_str, str) and len(home_form_str) >= 5:
                recent_form = home_form_str[-5:]
                for result in recent_form:
                    if result.upper() == 'W':
                        home_form_points += 3
                    elif result.upper() == 'D':
                        home_form_points += 1
            
            # Desempenho em casa
            home_home_wins = home_stats.get("home_wins", 0)
            home_home_played = home_stats.get("home_played", 1)
            home_home_percent = (home_home_wins / home_home_played) * 100 if home_home_played > 0 else 0
            
            # Montar justificativa
            justification_parts = []
            
            if home_avg_goals > 1.5:
                justification_parts.append(f"força ofensiva superior ({home_avg_goals:.1f} gols/jogo)")
            
            if home_form_points >= 9:
                justification_parts.append(f"forma recente positiva ({home_form_points}/15 pts)")
            
            if home_home_percent >= 60:
                justification_parts.append(f"{home_home_percent:.1f}% de aproveitamento em casa")
            
            # H2H dominância
            h2h_home_wins = h2h_stats.get("home_wins", 0)
            h2h_matches = h2h_stats.get("matches", 0)
            if h2h_matches > 0 and h2h_home_wins / h2h_matches > 0.5:
                justification_parts.append(f"vantagem histórica contra {away_team} ({h2h_home_wins}/{h2h_matches} vitórias)")
            
            if justification_parts:
                justification = "Justificativa: " + ", ".join(justification_parts) + "."
            
        elif opportunity_name == away_team:
            # Justificativa para vitória do time visitante
            away_wins = away_stats.get("wins", 0)
            away_played = away_stats.get("played", 1)
            away_win_percent = (away_wins / away_played) * 100 if away_played > 0 else 0
            
            # Gols marcados e sofridos
            away_goals_scored = away_stats.get("goals_scored", 0)
            away_goals_conceded = away_stats.get("goals_conceded", 0)
            away_avg_goals = away_stats.get("avg_goals_scored", 0)
            
            # Forma recente (últimos 5 jogos)
            away_form_str = away_stats.get("formRun_overall", "")
            away_form_points = 0
            
            if isinstance(away_form_str, str) and len(away_form_str) >= 5:
                recent_form = away_form_str[-5:]
                for result in recent_form:
                    if result.upper() == 'W':
                        away_form_points += 3
                    elif result.upper() == 'D':
                        away_form_points += 1
            
            # Desempenho fora de casa
            away_away_wins = away_stats.get("away_wins", 0)
            away_away_played = away_stats.get("away_played", 1)
            away_away_percent = (away_away_wins / away_away_played) * 100 if away_away_played > 0 else 0
            
            # Montar justificativa
            justification_parts = []
            
            if away_avg_goals > 1.5:
                justification_parts.append(f"ataque produtivo ({away_avg_goals:.1f} gols/jogo)")
            
            if away_form_points >= 9:
                justification_parts.append(f"boa sequência recente ({away_form_points}/15 pts)")
            
            if away_away_percent >= 50:
                justification_parts.append(f"bom aproveitamento como visitante ({away_away_percent:.1f}%)")
            
            # H2H dominância
            h2h_away_wins = h2h_stats.get("away_wins", 0)
            h2h_matches = h2h_stats.get("matches", 0)
            if h2h_matches > 0 and h2h_away_wins / h2h_matches > 0.5:
                justification_parts.append(f"vantagem histórica contra {home_team} ({h2h_away_wins}/{h2h_matches} vitórias)")
            
            if justification_parts:
                justification = "Justificativa: " + ", ".join(justification_parts) + "."
        
        # 2. Empate
        elif "Empate" in opportunity_name:
            # Buscar estatísticas de empates
            home_draws = home_stats.get("draws", 0)
            home_played = home_stats.get("played", 1)
            home_draw_percent = (home_draws / home_played) * 100 if home_played > 0 else 0
            
            away_draws = away_stats.get("draws", 0)
            away_played = away_stats.get("played", 1)
            away_draw_percent = (away_draws / away_played) * 100 if away_played > 0 else 0
            
            h2h_draws = h2h_stats.get("draws", 0)
            h2h_matches = h2h_stats.get("matches", 0)
            h2h_draw_percent = (h2h_draws / h2h_matches) * 100 if h2h_matches > 0 else 0
            
            # Montar justificativa
            justification_parts = []
            
            if h2h_matches >= 3 and h2h_draw_percent >= 30:
                justification_parts.append(f"histórico de empates entre os times ({h2h_draws}/{h2h_matches} jogos)")
            
            if home_draw_percent >= 25 and away_draw_percent >= 25:
                justification_parts.append(f"ambos empatam com frequência ({home_draw_percent:.1f}% e {away_draw_percent:.1f}%)")
            
            avg_goals_diff = abs(home_stats.get("avg_goals_scored", 0) - away_stats.get("avg_goals_scored", 0))
            if avg_goals_diff < 0.5:
                justification_parts.append("equilíbrio ofensivo entre as equipes")
            
            if justification_parts:
                justification = "Justificativa: " + ", ".join(justification_parts) + "."
        
        # 3. Over/Under Gols
        elif "Over" in opportunity_name and "Gols" in opportunity_name:
            # Extrair valor do over (ex: Over 2.5 Gols -> 2.5)
            over_value = 2.5  # Valor padrão
            match = re.search(r"Over (\d+\.?\d*)", opportunity_name)
            if match:
                over_value = float(match.group(1))
            
            # Calcular médias de gols
            home_avg_scored = home_stats.get("avg_goals_scored", 0)
            home_avg_conceded = home_stats.get("avg_goals_conceded", 0)
            away_avg_scored = away_stats.get("avg_goals_scored", 0)
            away_avg_conceded = away_stats.get("avg_goals_conceded", 0)
            
            combined_avg = home_avg_scored + away_avg_scored
            
            # Percentuais de jogos over
            over_key = f"over_{str(over_value).replace('.', '_')}"
            home_over_percent = home_stats.get(over_key, 0)
            if isinstance(home_over_percent, (int, float)) and home_over_percent > 1:
                home_over_percent = home_over_percent  # Já está em percentual
            else:
                # Tentar extrair de campos específicos para linhas comuns
                if over_value == 2.5:
                    home_over_percent = home_stats.get("over_2_5", 0) * 100
                elif over_value == 1.5:
                    home_over_percent = home_stats.get("over_1_5", 0) * 100
            
            away_over_percent = away_stats.get(over_key, 0)
            if isinstance(away_over_percent, (int, float)) and away_over_percent > 1:
                away_over_percent = away_over_percent  # Já está em percentual
            else:
                # Tentar extrair de campos específicos para linhas comuns
                if over_value == 2.5:
                    away_over_percent = away_stats.get("over_2_5", 0) * 100
                elif over_value == 1.5:
                    away_over_percent = away_stats.get("over_1_5", 0) * 100
            
            # Montar justificativa
            justification_parts = []
            
            if combined_avg > over_value:
                justification_parts.append(f"média combinada de {combined_avg:.1f} gols por jogo")
            
            if home_over_percent >= 50 and away_over_percent >= 40:
                justification_parts.append(f"{home_over_percent:.0f}% dos jogos do {home_team} e {away_over_percent:.0f}% do {away_team} terminam com Over {over_value}")
            
            if home_avg_scored > 1.5 and away_avg_scored > 1.0:
                justification_parts.append(f"ambas equipes têm bom ataque ({home_avg_scored:.1f} e {away_avg_scored:.1f} gols/jogo)")
            
            if justification_parts:
                justification = "Justificativa: " + ", ".join(justification_parts) + "."
                
        elif "Under" in opportunity_name and "Gols" in opportunity_name:
            # Extrair valor do under (ex: Under 2.5 Gols -> 2.5)
            under_value = 2.5  # Valor padrão
            match = re.search(r"Under (\d+\.?\d*)", opportunity_name)
            if match:
                under_value = float(match.group(1))
            
            # Calcular médias de gols
            home_avg_scored = home_stats.get("avg_goals_scored", 0)
            home_avg_conceded = home_stats.get("avg_goals_conceded", 0)
            away_avg_scored = away_stats.get("avg_goals_scored", 0)
            away_avg_conceded = away_stats.get("avg_goals_conceded", 0)
            
            combined_avg = home_avg_scored + away_avg_scored
            
            # Dados defensivos
            home_clean_sheets = home_stats.get("clean_sheets", 0)
            home_played = home_stats.get("played", 1)
            home_clean_sheet_percent = (home_clean_sheets / home_played) * 100 if home_played > 0 else 0
            
            away_clean_sheets = away_stats.get("clean_sheets", 0)
            away_played = away_stats.get("played", 1)
            away_clean_sheet_percent = (away_clean_sheets / away_played) * 100 if away_played > 0 else 0
            
            # Percentuais de jogos under
            under_key = f"under_{str(under_value).replace('.', '_')}"
            home_under_percent = 100 - home_stats.get(f"over_{str(under_value).replace('.', '_')}", 0)
            away_under_percent = 100 - away_stats.get(f"over_{str(under_value).replace('.', '_')}", 0)
            
            # Montar justificativa
            justification_parts = []
            
            if combined_avg < under_value:
                justification_parts.append(f"média combinada de apenas {combined_avg:.1f} gols por jogo")
            
            if home_clean_sheet_percent >= 30 or away_clean_sheet_percent >= 30:
                justification_parts.append(f"defesas sólidas ({home_clean_sheet_percent:.0f}% e {away_clean_sheet_percent:.0f}% de clean sheets)")
            
            if home_under_percent >= 50 and away_under_percent >= 50:
                justification_parts.append(f"tendência de jogos com poucos gols para ambos times")
            
            if home_avg_scored < 1.2 or away_avg_scored < 1.2:
                low_scoring_team = home_team if home_avg_scored < away_avg_scored else away_team
                justification_parts.append(f"baixa produtividade ofensiva do {low_scoring_team}")
            
            if justification_parts:
                justification = "Justificativa: " + ", ".join(justification_parts) + "."
        
        # 4. Ambos Marcam (BTTS)
        elif "Ambos Marcam" in opportunity_name or "BTTS" in opportunity_name:
            if "Sim" in opportunity_name:
                # Estatísticas de ambos marcam
                home_btts = home_stats.get("btts", 0)
                home_btts_percent = home_btts * 100 if isinstance(home_btts, float) and home_btts <= 1 else home_btts
                
                away_btts = away_stats.get("btts", 0)
                away_btts_percent = away_btts * 100 if isinstance(away_btts, float) and away_btts <= 1 else away_btts
                
                # Estatísticas ofensivas e defensivas
                home_avg_scored = home_stats.get("avg_goals_scored", 0)
                away_avg_scored = away_stats.get("avg_goals_scored", 0)
                
                home_games_scored = home_stats.get("played", 0) - home_stats.get("failed_to_score", 0)
                home_played = home_stats.get("played", 1)
                home_scored_percent = (home_games_scored / home_played) * 100 if home_played > 0 else 0
                
                away_games_scored = away_stats.get("played", 0) - away_stats.get("failed_to_score", 0)
                away_played = away_stats.get("played", 1)
                away_scored_percent = (away_games_scored / away_played) * 100 if away_played > 0 else 0
                
                # Montar justificativa
                justification_parts = []
                
                if home_btts_percent >= 50 and away_btts_percent >= 50:
                    justification_parts.append(f"alta incidência de BTTS para ambas equipes ({home_btts_percent:.0f}% e {away_btts_percent:.0f}%)")
                
                if home_scored_percent >= 70 and away_scored_percent >= 70:
                    justification_parts.append(f"ambas marcam com frequência ({home_scored_percent:.0f}% e {away_scored_percent:.0f}% dos jogos)")
                
                if home_avg_scored > 1.0 and away_avg_scored > 1.0:
                    justification_parts.append(f"bom potencial ofensivo dos dois times ({home_avg_scored:.1f} e {away_avg_scored:.1f} gols/jogo)")
                
                if justification_parts:
                    justification = "Justificativa: " + ", ".join(justification_parts) + "."
            
            elif "Não" in opportunity_name:
                # Estatísticas de clean sheets e failed to score
                home_clean_sheets = home_stats.get("clean_sheets", 0)
                home_played = home_stats.get("played", 1)
                home_clean_sheet_percent = (home_clean_sheets / home_played) * 100 if home_played > 0 else 0
                
                away_clean_sheets = away_stats.get("clean_sheets", 0)
                away_played = away_stats.get("played", 1)
                away_clean_sheet_percent = (away_clean_sheets / away_played) * 100 if away_played > 0 else 0
                
                home_failed_to_score = home_stats.get("failed_to_score", 0)
                home_failed_percent = (home_failed_to_score / home_played) * 100 if home_played > 0 else 0
                
                away_failed_to_score = away_stats.get("failed_to_score", 0)
                away_failed_percent = (away_failed_to_score / away_played) * 100 if away_played > 0 else 0
                
                # Estatísticas de BTTS=No
                home_btts = home_stats.get("btts", 0)
                home_btts_no_percent = 100 - (home_btts * 100 if isinstance(home_btts, float) and home_btts <= 1 else home_btts)
                
                away_btts = away_stats.get("btts", 0)
                away_btts_no_percent = 100 - (away_btts * 100 if isinstance(away_btts, float) and away_btts <= 1 else away_btts)
                
                # Montar justificativa
                justification_parts = []
                
                if home_btts_no_percent >= 50 or away_btts_no_percent >= 50:
                    higher_team = home_team if home_btts_no_percent > away_btts_no_percent else away_team
                    higher_percent = max(home_btts_no_percent, away_btts_no_percent)
                    justification_parts.append(f"tendência de jogos sem ambos marcarem para o {higher_team} ({higher_percent:.0f}%)")
                
                if home_clean_sheet_percent >= 30 or away_clean_sheet_percent >= 30:
                    better_defense = home_team if home_clean_sheet_percent > away_clean_sheet_percent else away_team
                    better_percent = max(home_clean_sheet_percent, away_clean_sheet_percent)
                    justification_parts.append(f"defesa sólida do {better_defense} ({better_percent:.0f}% de clean sheets)")
                
                if home_failed_percent >= 30 or away_failed_percent >= 30:
                    worse_attack = home_team if home_failed_percent > away_failed_percent else away_team
                    worse_percent = max(home_failed_percent, away_failed_percent)
                    justification_parts.append(f"dificuldades ofensivas do {worse_attack} ({worse_percent:.0f}% sem marcar)")
                
                if justification_parts:
                    justification = "Justificativa: " + ", ".join(justification_parts) + "."
        
        # 5. Chance Dupla
        elif "ou" in opportunity_name or "Chance Dupla" in opportunity_name:
            # Chance Dupla - identificar qual é
            is_home_draw = home_team in opportunity_name and "Empate" in opportunity_name  # 1X
            is_home_away = home_team in opportunity_name and away_team in opportunity_name  # 12
            is_draw_away = "Empate" in opportunity_name and away_team in opportunity_name  # X2
            
            justification_parts = []
            
            if is_home_draw:  # 1X
                home_wins = home_stats.get("wins", 0)
                home_draws = home_stats.get("draws", 0)
                home_played = home_stats.get("played", 1)
                home_not_lose_percent = ((home_wins + home_draws) / home_played) * 100 if home_played > 0 else 0
                
                # H2H
                h2h_home_wins = h2h_stats.get("home_wins", 0)
                h2h_draws = h2h_stats.get("draws", 0)
                h2h_matches = h2h_stats.get("matches", 0)
                h2h_home_not_lose = ((h2h_home_wins + h2h_draws) / h2h_matches) * 100 if h2h_matches > 0 else 0
                
                if home_not_lose_percent >= 60:
                    justification_parts.append(f"{home_team} raramente perde ({home_not_lose_percent:.0f}% sem derrota)")
                
                if h2h_matches >= 3 and h2h_home_not_lose >= 60:
                    justification_parts.append(f"histórico favorável no confronto direto ({h2h_home_not_lose:.0f}% sem derrota)")
                
                home_home_wins = home_stats.get("home_wins", 0)
                home_home_draws = home_stats.get("home_draws", 0)
                home_home_played = home_stats.get("home_played", 1)
                
                if home_home_played > 0:
                    home_home_not_lose = ((home_home_wins + home_home_draws) / home_home_played) * 100
                    if home_home_not_lose >= 70:
                        justification_parts.append(f"força como mandante ({home_home_not_lose:.0f}% sem perder em casa)")
            
            elif is_home_away:  # 12
                home_wins = home_stats.get("wins", 0)
                away_wins = away_stats.get("wins", 0)
                home_played = home_stats.get("played", 1)
                away_played = away_stats.get("played", 1)
                
                home_win_percent = (home_wins / home_played) * 100 if home_played > 0 else 0
                away_win_percent = (away_wins / away_played) * 100 if away_played > 0 else 0
                
                combined_win_percent = (home_win_percent + away_win_percent) / 2
                
                # H2H
                h2h_home_wins = h2h_stats.get("home_wins", 0)
                h2h_away_wins = h2h_stats.get("away_wins", 0)
                h2h_matches = h2h_stats.get("matches", 0)
                h2h_no_draw_percent = ((h2h_home_wins + h2h_away_wins) / h2h_matches) * 100 if h2h_matches > 0 else 0
                
                if combined_win_percent >= 60:
                    justification_parts.append(f"ambas equipes têm bom aproveitamento ({home_win_percent:.0f}% e {away_win_percent:.0f}%)")
                
                if h2h_matches >= 3 and h2h_no_draw_percent >= 70:
                    justification_parts.append(f"histórico de decisão sem empates ({h2h_no_draw_percent:.0f}%)")
                
                home_draws = home_stats.get("draws", 0)
                away_draws = away_stats.get("draws", 0)
                
                home_draw_percent = (home_draws / home_played) * 100 if home_played > 0 else 0
                away_draw_percent = (away_draws / away_played) * 100 if away_played > 0 else 0
                
                if home_draw_percent < 20 or away_draw_percent < 20:
                    justification_parts.append("baixa incidência de empates")
            
            elif is_draw_away:  # X2
                away_wins = away_stats.get("wins", 0)
                away_draws = away_stats.get("draws", 0)
                away_played = away_stats.get("played", 1)
                away_not_lose_percent = ((away_wins + away_draws) / away_played) * 100 if away_played > 0 else 0
                
                # H2H
                h2h_away_wins = h2h_stats.get("away_wins", 0)
                h2h_draws = h2h_stats.get("draws", 0)
                h2h_matches = h2h_stats.get("matches", 0)
                h2h_away_not_lose = ((h2h_away_wins + h2h_draws) / h2h_matches) * 100 if h2h_matches > 0 else 0
                
                if away_not_lose_percent >= 50:
                    justification_parts.append(f"{away_team} é resiliente ({away_not_lose_percent:.0f}% sem derrota)")
                
                if h2h_matches >= 3 and h2h_away_not_lose >= 50:
                    justification_parts.append(f"bom histórico no confronto direto ({h2h_away_not_lose:.0f}% sem derrota)")
                
                away_away_wins = away_stats.get("away_wins", 0)
                away_away_draws = away_stats.get("away_draws", 0)
                away_away_played = away_stats.get("away_played", 1)
                
                if away_away_played > 0:
                    away_away_not_lose = ((away_away_wins + away_away_draws) / away_away_played) * 100
                    if away_away_not_lose >= 50:
                        justification_parts.append(f"bom desempenho como visitante ({away_away_not_lose:.0f}% sem perder fora)")
            
            if justification_parts:
                justification = "Justificativa: " + ", ".join(justification_parts) + "."
        
        # 6. Escanteios
        elif "Escanteios" in opportunity_name:
            # Tentar extrair estatísticas de escanteios
            if "home_corners" in home_stats and "away_corners" in away_stats:
                home_corners_scored = home_stats.get("home_corners", 0)
                away_corners_scored = away_stats.get("away_corners", 0)
                
                home_played = home_stats.get("played", 1)
                away_played = away_stats.get("played", 1)
                
                home_corners_avg = home_corners_scored / home_played if home_played > 0 else 0
                away_corners_avg = away_corners_scored / away_played if away_played > 0 else 0
                
                combined_corners_avg = home_corners_avg + away_corners_avg
                
                # Extrair valor da linha
                corners_value = 9.5  # Valor padrão
                if "Over" in opportunity_name:
                    match = re.search(r"Over (\d+\.?\d*)", opportunity_name)
                    if match:
                        corners_value = float(match.group(1))
                    
                    # Justificativa para Over Escanteios
                    justification_parts = []
                    
                    if combined_corners_avg > corners_value:
                        justification_parts.append(f"média combinada de {combined_corners_avg:.1f} escanteios por jogo")
                    
                    if home_corners_avg > 5.5:
                        justification_parts.append(f"{home_team} produz muitos escanteios ({home_corners_avg:.1f} por jogo)")
                    
                    if away_corners_avg > 4.5:
                        justification_parts.append(f"{away_team} também gera bom volume ({away_corners_avg:.1f} por jogo)")
                    
                    if justification_parts:
                        justification = "Justificativa: " + ", ".join(justification_parts) + "."
                
                elif "Under" in opportunity_name:
                    match = re.search(r"Under (\d+\.?\d*)", opportunity_name)
                    if match:
                        corners_value = float(match.group(1))            
        # 7. Cartões
        elif "Cartões" in opportunity_name:
            # Tentar extrair estatísticas de cartões
            home_cards = home_stats.get("yellow_cards", 0) + home_stats.get("red_cards", 0)
            away_cards = away_stats.get("yellow_cards", 0) + away_stats.get("red_cards", 0)
            
            home_played = home_stats.get("played", 1)
            away_played = away_stats.get("played", 1)
            
            home_cards_avg = home_cards / home_played if home_played > 0 else 0
            away_cards_avg = away_cards / away_played if away_played > 0 else 0
            
            combined_cards_avg = home_cards_avg + away_cards_avg
            
            # Extrair valor da linha
            cards_value = 3.5  # Valor padrão
            if "Over" in opportunity_name:
                match = re.search(r"Over (\d+\.?\d*)", opportunity_name)
                if match:
                    cards_value = float(match.group(1))
                
                # Justificativa para Over Cartões
                justification_parts = []
                
                if combined_cards_avg > cards_value:
                    justification_parts.append(f"média combinada de {combined_cards_avg:.1f} cartões por jogo")
                
                if home_cards_avg > 2.0:
                    justification_parts.append(f"{home_team} recebe muitos cartões ({home_cards_avg:.1f} por jogo)")
                
                if away_cards_avg > 2.0:
                    justification_parts.append(f"{away_team} também é indisciplinado ({away_cards_avg:.1f} por jogo)")
                
                # Verificar intensidade do confronto pelo H2H
                h2h_matches = h2h_stats.get("matches", 0)
                h2h_cards = h2h_stats.get("total_cards", 0)
                if h2h_matches > 0 and h2h_cards > 0:
                    h2h_cards_avg = h2h_cards / h2h_matches
                    if h2h_cards_avg > 4.0:
                        justification_parts.append(f"histórico de confrontos intensos ({h2h_cards_avg:.1f} cartões/jogo)")
                
                if justification_parts:
                    justification = "Justificativa: " + ", ".join(justification_parts) + "."
            
            elif "Under" in opportunity_name:
                match = re.search(r"Under (\d+\.?\d*)", opportunity_name)
                if match:
                    cards_value = float(match.group(1))
                
                # Justificativa para Under Cartões
                justification_parts = []
                
                if combined_cards_avg < cards_value:
                    justification_parts.append(f"média combinada de apenas {combined_cards_avg:.1f} cartões por jogo")
                
                if home_cards_avg < 1.5 and away_cards_avg < 1.5:
                    justification_parts.append("ambas equipes são disciplinadas")
                elif home_cards_avg < 1.5 or away_cards_avg < 1.5:
                    disciplined_team = home_team if home_cards_avg < away_cards_avg else away_team
                    disciplined_avg = min(home_cards_avg, away_cards_avg)
                    justification_parts.append(f"{disciplined_team} é disciplinado ({disciplined_avg:.1f} cartões/jogo)")
                
                # Verificar intensidade do confronto pelo H2H
                h2h_matches = h2h_stats.get("matches", 0)
                h2h_cards = h2h_stats.get("total_cards", 0)
                if h2h_matches > 0 and h2h_cards > 0:
                    h2h_cards_avg = h2h_cards / h2h_matches
                    if h2h_cards_avg < 3.0:
                        justification_parts.append(f"histórico de confrontos calmos ({h2h_cards_avg:.1f} cartões/jogo)")
                
                if justification_parts:
                    justification = "Justificativa: " + ", ".join(justification_parts) + "."
        
        return justification
        
    except Exception as e:
        logger.error(f"Erro ao gerar justificativa: {str(e)}")
        logger.error(traceback.format_exc())
        return ""


def add_justifications_to_analysis(analysis_text, stats_data, home_team, away_team):
    """
    Adiciona justificativas a cada oportunidade identificada na análise
    
    Args:
        analysis_text (str): Texto da análise
        stats_data (dict): Dados estatísticos completos
        home_team (str): Nome do time da casa
        away_team (str): Nome do time visitante
        
    Returns:
        str: Texto da análise com justificativas
    """
    import re
    
    # Se não temos dados estatísticos, retornar o texto original
    if not stats_data or "home_team" not in stats_data or "away_team" not in stats_data:
        return analysis_text
    
    # Procurar a seção de Oportunidades Identificadas
    opportunities_section = None
    opportunities_start_idx = -1
    sections = analysis_text.split("# ")
    
    for i, section in enumerate(sections):
        if section.startswith("Oportunidades Identificadas"):
            opportunities_section = section
            opportunities_start_idx = i
            break
    
    # Se não encontrou a seção, retornar o texto original
    if opportunities_section is None or opportunities_start_idx == -1:
        return analysis_text
    
    # Extrair oportunidades individuais
    opportunities = []
    
    # Padrão para capturar oportunidades (sem justificativa atual)
    pattern = r"- \*\*(.*?)\*\*: Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(Valor de (\d+\.\d+)%\)(?!\s*\*Justificativa:)"
    
    matches = re.findall(pattern, opportunities_section)
    
    # Se não encontrou oportunidades, tentar outro padrão
    if not matches:
        # Padrão alternativo com indentação diferente
        pattern = r"\*\*(.*?)\*\*: Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(Valor de (\d+\.\d+)%\)(?!\s*\*Justificativa:)"
        matches = re.findall(pattern, opportunities_section)
    
    # Se ainda não encontrou, retornar o texto original
    if not matches:
        return analysis_text
    
    # Processar cada oportunidade encontrada
    updated_section = opportunities_section
    for match in matches:
        opportunity_name, real_prob_str, implicit_prob_str, margin_str = match
        
        try:
            # Converter para números
            real_prob = float(real_prob_str)
            
            # Gerar justificativa
            justification = generate_opportunity_justification(
                opportunity_name.strip(),
                real_prob,
                stats_data,
                home_team,
                away_team
            )
            
            if justification:
                # Texto original da oportunidade (para substituição)
                original_text = f"**{opportunity_name}**: Real {real_prob_str}% vs Implícita {implicit_prob_str}% (Valor de {margin_str}%)"
                
                # Novo texto com justificativa
                new_text = f"**{opportunity_name}**: Real {real_prob_str}% vs Implícita {implicit_prob_str}% (Valor de {margin_str}%) *{justification}*"
                
                # Substituir apenas a ocorrência exata
                updated_section = updated_section.replace(original_text, new_text)
        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao processar oportunidade '{opportunity_name}': {str(e)}")
            continue
    
    # Reconstruir o texto completo da análise
    sections[opportunities_start_idx] = updated_section
    updated_analysis = "# ".join(sections)
    
    return updated_analysis
