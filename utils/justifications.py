# utils/justifications.py
import logging
import re

def generate_justifications_for_opportunities(opportunities, home_team, away_team, original_probabilities, implied_probabilities):
    """
    Gera justificativas detalhadas para as oportunidades identificadas.
    
    Args:
        opportunities (list): Lista de oportunidades identificadas
        home_team (str): Nome do time da casa
        away_team (str): Nome do time visitante
        original_probabilities (dict): Probabilidades reais calculadas
        implied_probabilities (dict): Probabilidades implícitas nas odds
    
    Returns:
        list: Lista de justificativas formatadas
    """
    justifications = []
    
    for opportunity in opportunities:
        # Identificar o mercado e extrar informações da oportunidade
        market_type, bet_type, real_prob, implied_prob = extract_opportunity_info(opportunity, home_team, away_team)
        
        # Gerar justificativa específica para o mercado
        if market_type and bet_type and real_prob and implied_prob:
            justification = generate_detailed_justification(
                market_type, bet_type, home_team, away_team, 
                real_prob, implied_prob, 
                original_probabilities
            )
            
            if justification:
                justifications.append(justification)
    
    return justifications

def format_justifications_section(justifications):
    """
    Formata a seção de justificativas com um cabeçalho apropriado.
    """
    if not justifications:
        return ""
    
    header = "# Justificativas Detalhadas para Oportunidades:\n"
    return header + "\n".join(justifications)

def extract_opportunity_info(opportunity, home_team, away_team):
    """
    Extrai informações da oportunidade identificada.
    
    Args:
        opportunity (str): Texto da oportunidade
        home_team (str): Nome do time da casa
        away_team (str): Nome do time visitante
        
    Returns:
        tuple: (market_type, bet_type, real_prob, implied_prob)
    """
    try:
        # Extrair probabilidades usando regex
        real_prob_match = re.search(r"Real (\d+\.\d+)%", opportunity)
        implied_prob_match = re.search(r"Implícita (\d+\.\d+)%", opportunity)
        
        if not (real_prob_match and implied_prob_match):
            return None, None, None, None
            
        real_prob = float(real_prob_match.group(1))
        implied_prob = float(implied_prob_match.group(1))
        
        # Extrair o nome do mercado (parte entre ** **)
        market_name_match = re.search(r"\*\*(.*?)\*\*", opportunity)
        if not market_name_match:
            return None, None, real_prob, implied_prob
            
        market_name = market_name_match.group(1)
        
        # Identificar o tipo de mercado e o tipo de aposta
        market_type = "unknown"
        bet_type = "unknown"
        
        # Moneyline (1X2)
        if market_name == home_team:
            market_type = "moneyline"
            bet_type = "home_win"
        elif market_name == away_team:
            market_type = "moneyline"
            bet_type = "away_win"
        elif market_name == "Empate":
            market_type = "moneyline"
            bet_type = "draw"
        # Chance Dupla
        elif "ou" in market_name:
            market_type = "double_chance"
            if home_team in market_name and away_team in market_name:
                bet_type = "home_or_away"
            elif home_team in market_name:
                bet_type = "home_or_draw"
            elif away_team in market_name:
                bet_type = "away_or_draw"
        # Ambos Marcam
        elif "Ambos Marcam" in market_name:
            market_type = "btts"
            bet_type = "yes" if "Sim" in market_name else "no"
        # Over/Under Gols
        elif "Gols" in market_name:
            market_type = "goals"
            threshold_match = re.search(r"([Oo]ver|[Uu]nder)\s+(\d+\.?\d*)", market_name)
            if threshold_match:
                direction = threshold_match.group(1).lower()
                threshold = threshold_match.group(2).replace(".", "_")
                bet_type = f"{direction}_{threshold}"
        # Escanteios
        elif "Escanteios" in market_name:
            market_type = "corners"
            threshold_match = re.search(r"([Oo]ver|[Uu]nder)\s+(\d+\.?\d*)", market_name)
            if threshold_match:
                direction = threshold_match.group(1).lower()
                threshold = threshold_match.group(2).replace(".", "_")
                bet_type = f"{direction}_{threshold}"
        # Cartões
        elif "Cartões" in market_name:
            market_type = "cards"
            threshold_match = re.search(r"([Oo]ver|[Uu]nder)\s+(\d+\.?\d*)", market_name)
            if threshold_match:
                direction = threshold_match.group(1).lower()
                threshold = threshold_match.group(2).replace(".", "_")
                bet_type = f"{direction}_{threshold}"
        
        return market_type, bet_type, real_prob, implied_prob
        
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro ao extrair informações da oportunidade: {str(e)}")
        return None, None, None, None

def generate_detailed_justification(market_type, bet_type, home_team, away_team, real_prob, implied_prob, original_probabilities):
    """
    Gera justificativa detalhada específica para cada tipo de mercado.
    
    Args:
        market_type (str): Tipo de mercado (moneyline, goals, btts, etc.)
        bet_type (str): Tipo de aposta (home_win, over_2_5, etc.)
        home_team (str): Nome do time da casa
        away_team (str): Nome do time visitante
        real_prob (float): Probabilidade real calculada
        implied_prob (float): Probabilidade implícita na odd
        original_probabilities (dict): Probabilidades originais calculadas
        
    Returns:
        str: Justificativa formatada
    """
    try:
        # Extrair análise dados
        analysis_data = original_probabilities.get("analysis_data", {})
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # Formatar título com base no mercado
        title = ""
        
        # 1. MONEYLINE (1X2)
        if market_type == "moneyline":
            if bet_type == "home_win":
                title = f"### Justificativa para {home_team} (Vitória Casa)"
                content = generate_moneyline_home_justification(
                    home_team, away_team, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
            elif bet_type == "away_win":
                title = f"### Justificativa para {away_team} (Vitória Fora)"
                content = generate_moneyline_away_justification(
                    home_team, away_team, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
            elif bet_type == "draw":
                title = "### Justificativa para Empate"
                content = generate_draw_justification(
                    home_team, away_team, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
        
        # 2. DUPLA CHANCE
        elif market_type == "double_chance":
            if bet_type == "home_or_draw":
                title = f"### Justificativa para {home_team} ou Empate (Dupla Chance)"
                content = generate_home_draw_justification(
                    home_team, away_team, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
            elif bet_type == "away_or_draw":
                title = f"### Justificativa para {away_team} ou Empate (Dupla Chance)"
                content = generate_away_draw_justification(
                    home_team, away_team, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
            elif bet_type == "home_or_away":
                title = f"### Justificativa para {home_team} ou {away_team} (Dupla Chance)"
                content = generate_home_away_justification(
                    home_team, away_team, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
        
        # 3. AMBOS MARCAM (BTTS)
        elif market_type == "btts":
            if bet_type == "yes":
                title = "### Justificativa para Ambos Marcam - Sim"
                content = generate_btts_yes_justification(
                    home_team, away_team, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
            else:  # no
                title = "### Justificativa para Ambos Marcam - Não"
                content = generate_btts_no_justification(
                    home_team, away_team, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
        
        # 4. TOTAL DE GOLS
        elif market_type == "goals":
            # Extrair threshold do bet_type (por exemplo, over_2_5 -> 2.5)
            parts = bet_type.split("_")
            direction = parts[0]  # over ou under
            threshold = float(parts[1] + "." + parts[2]) if len(parts) > 2 else float(parts[1])
            
            if direction == "over":
                title = f"### Justificativa para Over {threshold} Gols"
                content = generate_over_goals_justification(
                    home_team, away_team, threshold, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
            else:  # under
                title = f"### Justificativa para Under {threshold} Gols"
                content = generate_under_goals_justification(
                    home_team, away_team, threshold, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
        
        # 5. ESCANTEIOS
        elif market_type == "corners":
            # Extrair threshold do bet_type
            parts = bet_type.split("_")
            direction = parts[0]  # over ou under
            threshold = float(parts[1] + "." + parts[2]) if len(parts) > 2 else float(parts[1])
            
            if direction == "over":
                title = f"### Justificativa para Over {threshold} Escanteios"
                content = generate_over_corners_justification(
                    home_team, away_team, threshold, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
            else:  # under
                title = f"### Justificativa para Under {threshold} Escanteios"
                content = generate_under_corners_justification(
                    home_team, away_team, threshold, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
        
        # 6. CARTÕES
        elif market_type == "cards":
            # Extrair threshold do bet_type
            parts = bet_type.split("_")
            direction = parts[0]  # over ou under
            threshold = float(parts[1] + "." + parts[2]) if len(parts) > 2 else float(parts[1])
            
            if direction == "over":
                title = f"### Justificativa para Over {threshold} Cartões"
                content = generate_over_cards_justification(
                    home_team, away_team, threshold, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
            else:  # under
                title = f"### Justificativa para Under {threshold} Cartões"
                content = generate_under_cards_justification(
                    home_team, away_team, threshold, real_prob, implied_prob, 
                    original_probabilities, analysis_data
                )
        
        # Caso não tenha identificado o tipo de mercado
        else:
            title = f"### Justificativa para {bet_type.capitalize()}"
            content = f"Valor identificado: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%."
        
        # Retornar justificativa formatada
        if title and content:
            return f"{title}\n\n{content}\n"
        return ""
        
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro ao gerar justificativa detalhada: {str(e)}")
        return ""

#
# FUNÇÕES ESPECÍFICAS PARA CADA TIPO DE JUSTIFICATIVA
#

def generate_moneyline_home_justification(home_team, away_team, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para vitória do time da casa"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # Forma e consistência
        home_form_points = analysis_data.get("home_form_points", 0) * 15
        home_consistency = analysis_data.get("home_consistency", 0)
        
        # Desempenho em casa
        home_wins = home_team_data.get("home_wins", 0)
        home_draws = home_team_data.get("home_draws", 0)
        home_losses = home_team_data.get("home_losses", 0)
        win_pct = home_team_data.get("win_pct", 0)
        
        # Gols marcados/sofridos em casa
        home_goals_scored = home_team_data.get("home_goals_scored", 0)
        home_goals_conceded = home_team_data.get("home_goals_conceded", 0)
        home_played = home_team_data.get("home_played", 1)
        
        if home_played > 0:
            home_goals_avg = home_goals_scored / home_played
            home_conceded_avg = home_goals_conceded / home_played
        else:
            home_goals_avg = 0
            home_conceded_avg = 0
        
        # Dados H2H
        home_h2h_wins = h2h_data.get("home_wins", 0)
        total_h2h = h2h_data.get("total_matches", 0)
        h2h_win_pct = (home_h2h_wins / total_h2h * 100) if total_h2h > 0 else 0
        
        # Construir justificativa
        justification = f"- **Forma como mandante**: {home_form_points:.0f}/15 pontos, consistência de {home_consistency:.1f}%\n"
        
        if home_wins + home_draws + home_losses > 0:
            justification += f"- **Desempenho como mandante**: {home_wins}V {home_draws}E {home_losses}D ({win_pct:.0f}% vitórias)\n"
        
        justification += f"- **Ofensividade em casa**: Marca {home_goals_avg:.2f} e sofre {home_conceded_avg:.2f} gols por jogo\n"
        
        if total_h2h > 0:
            justification += f"- **Histórico H2H**: Venceu {home_h2h_wins} de {total_h2h} confrontos ({h2h_win_pct:.0f}%)\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa home: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_moneyline_away_justification(home_team, away_team, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para vitória do time visitante"""
    try:
        # Extrair dados relevantes
        away_team_data = original_probabilities.get("away_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # Forma e consistência
        away_form_points = analysis_data.get("away_form_points", 0) * 15
        away_consistency = analysis_data.get("away_consistency", 0)
        
        # Desempenho fora
        away_wins = away_team_data.get("away_wins", 0)
        away_draws = away_team_data.get("away_draws", 0)
        away_losses = away_team_data.get("away_losses", 0)
        win_pct = away_team_data.get("win_pct", 0)
        
        # Gols marcados/sofridos fora
        away_goals_scored = away_team_data.get("away_goals_scored", 0)
        away_goals_conceded = away_team_data.get("away_goals_conceded", 0)
        away_played = away_team_data.get("away_played", 1)
        
        if away_played > 0:
            away_goals_avg = away_goals_scored / away_played
            away_conceded_avg = away_goals_conceded / away_played
        else:
            away_goals_avg = 0
            away_conceded_avg = 0
        
        # Dados H2H
        away_h2h_wins = h2h_data.get("away_wins", 0)
        total_h2h = h2h_data.get("total_matches", 0)
        h2h_win_pct = (away_h2h_wins / total_h2h * 100) if total_h2h > 0 else 0
        
        # Construir justificativa
        justification = f"- **Forma como visitante**: {away_form_points:.0f}/15 pontos, consistência de {away_consistency:.1f}%\n"
        
        if away_wins + away_draws + away_losses > 0:
            justification += f"- **Desempenho como visitante**: {away_wins}V {away_draws}E {away_losses}D ({win_pct:.0f}% vitórias)\n"
        
        justification += f"- **Ofensividade fora**: Marca {away_goals_avg:.2f} e sofre {away_conceded_avg:.2f} gols por jogo\n"
        
        if total_h2h > 0:
            justification += f"- **Histórico H2H**: Venceu {away_h2h_wins} de {total_h2h} confrontos ({h2h_win_pct:.0f}%)\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa away: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_draw_justification(home_team, away_team, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para empate"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # Forma e consistência
        home_form_points = analysis_data.get("home_form_points", 0) * 15
        away_form_points = analysis_data.get("away_form_points", 0) * 15
        
        # Percentuais de empate
        home_draw_pct = home_team_data.get("draw_pct", 0)
        away_draw_pct = away_team_data.get("draw_pct", 0)
        
        # Dados H2H
        draws_h2h = h2h_data.get("draws", 0)
        total_h2h = h2h_data.get("total_matches", 0)
        h2h_draw_pct = (draws_h2h / total_h2h * 100) if total_h2h > 0 else 0
        
        # Força relativa
        home_total_score = analysis_data.get("home_total_score", 0)
        away_total_score = analysis_data.get("away_total_score", 0)
        force_diff = abs(home_total_score - away_total_score)
        
        # Construir justificativa
        justification = f"- **Forma dos times**: Casa com {home_form_points:.0f}/15 pts, Fora com {away_form_points:.0f}/15 pts\n"
        justification += f"- **Tendência de empates**: Casa {home_draw_pct:.0f}%, Fora {away_draw_pct:.0f}%\n"
        
        if force_diff < 0.15:
            justification += "- **Equilíbrio de forças**: Times com pontuações totais próximas\n"
        
        if total_h2h > 0:
            justification += f"- **Histórico H2H**: {draws_h2h} empates em {total_h2h} confrontos ({h2h_draw_pct:.0f}%)\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa draw: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_home_draw_justification(home_team, away_team, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para Casa ou Empate"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # Forma e consistência
        home_form_points = analysis_data.get("home_form_points", 0) * 15
        home_consistency = analysis_data.get("home_consistency", 0)
        
        # Desempenho em casa
        home_wins = home_team_data.get("home_wins", 0)
        home_draws = home_team_data.get("home_draws", 0)
        home_losses = home_team_data.get("home_losses", 0)
        
        # Dados H2H
        home_h2h_wins = h2h_data.get("home_wins", 0)
        draws_h2h = h2h_data.get("draws", 0)
        total_h2h = h2h_data.get("total_matches", 0)
        
        # Percentual de não-derrota em H2H
        h2h_no_loss_pct = ((home_h2h_wins + draws_h2h) / total_h2h * 100) if total_h2h > 0 else 0
        
        # Construir justificativa
        justification = f"- **Forma como mandante**: {home_form_points:.0f}/15 pontos, consistência de {home_consistency:.1f}%\n"
        
        if home_wins + home_draws + home_losses > 0:
            no_loss_pct = ((home_wins + home_draws) / (home_wins + home_draws + home_losses)) * 100
            justification += f"- **Desempenho como mandante**: {home_wins}V {home_draws}E {home_losses}D ({no_loss_pct:.0f}% jogos sem perder)\n"
        
        if total_h2h > 0:
            justification += f"- **Histórico H2H**: {home_h2h_wins + draws_h2h} jogos sem perder em {total_h2h} confrontos ({h2h_no_loss_pct:.0f}%)\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa home_draw: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_away_draw_justification(home_team, away_team, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para Fora ou Empate"""
    try:
        # Extrair dados relevantes
        away_team_data = original_probabilities.get("away_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # Forma e consistência
        away_form_points = analysis_data.get("away_form_points", 0) * 15
        away_consistency = analysis_data.get("away_consistency", 0)
        
        # Desempenho fora
        away_wins = away_team_data.get("away_wins", 0)
        away_draws = away_team_data.get("away_draws", 0)
        away_losses = away_team_data.get("away_losses", 0)
        
        # Dados H2H
        away_h2h_wins = h2h_data.get("away_wins", 0)
        draws_h2h = h2h_data.get("draws", 0)
        total_h2h = h2h_data.get("total_matches", 0)
        
        # Percentual de não-derrota em H2H
        h2h_no_loss_pct = ((away_h2h_wins + draws_h2h) / total_h2h * 100) if total_h2h > 0 else 0
        
        # Construir justificativa
        justification = f"- **Forma como visitante**: {away_form_points:.0f}/15 pontos, consistência de {away_consistency:.1f}%\n"
        
        if away_wins + away_draws + away_losses > 0:
            no_loss_pct = ((away_wins + away_draws) / (away_wins + away_draws + away_losses)) * 100
            justification += f"- **Desempenho como visitante**: {away_wins}V {away_draws}E {away_losses}D ({no_loss_pct:.0f}% jogos sem perder)\n"
        
        if total_h2h > 0:
            justification += f"- **Histórico H2H**: {away_h2h_wins + draws_h2h} jogos sem perder em {total_h2h} confrontos ({h2h_no_loss_pct:.0f}%)\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa away_draw: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_home_away_justification(home_team, away_team, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para Casa ou Fora"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # Dados H2H
        home_h2h_wins = h2h_data.get("home_wins", 0)
        away_h2h_wins = h2h_data.get("away_wins", 0)
        draws_h2h = h2h_data.get("draws", 0)
        total_h2h = h2h_data.get("total_matches", 0)
        
        # Percentual de vitórias (não empates) em H2H
        h2h_win_pct = ((home_h2h_wins + away_h2h_wins) / total_h2h * 100) if total_h2h > 0 else 0
        
        # Construir justificativa
        justification = "- **Baixa probabilidade de empate**: "
        
        if "draw_pct" in home_team_data and "draw_pct" in away_team_data:
            home_draw_pct = home_team_data.get("draw_pct", 0)
            away_draw_pct = away_team_data.get("draw_pct", 0)
            justification += f"Casa tem {home_draw_pct:.0f}% e fora tem {away_draw_pct:.0f}% de empates na temporada\n"
        else:
            justification += "Ambas equipes têm baixa tendência a empates\n"
            
        if total_h2h > 0:
            justification += f"- **Histórico H2H**: {home_h2h_wins + away_h2h_wins} vitórias em {total_h2h} confrontos ({h2h_win_pct:.0f}%)\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa home_away: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_btts_yes_justification(home_team, away_team, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para Ambos Marcam - Sim"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # xG e médias de gols
        home_xg = home_team_data.get("xg_for_avg_overall", 0)
        home_xg_home = home_team_data.get("xg_for_avg_home", home_xg)
        away_xg = away_team_data.get("xg_for_avg_overall", 0)
        away_xg_away = away_team_data.get("xg_for_avg_away", away_xg)
        
        # Médias de gols
        home_goals_scored = home_team_data.get("home_goals_scored", 0)
        home_played = home_team_data.get("home_played", 1)
        away_goals_scored = away_team_data.get("away_goals_scored", 0)
        away_played = away_team_data.get("away_played", 1)
        
        home_goals_home = home_goals_scored / max(1, home_played)
        away_goals_away = away_goals_scored / max(1, away_played)
        
        # Percentuais de BTTS
        home_btts_pct = home_team_data.get("btts_pct", 0)
        away_btts_pct = away_team_data.get("btts_pct", 0)
        h2h_btts_pct = h2h_data.get("btts_pct", 0)
        
        # Total esperado de gols
        total_expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 0)
        
        # Construir justificativa
        justification = f"- **xG**: Casa {home_xg_home:.2f} (mandante), Fora {away_xg_away:.2f} (visitante)\n"
        justification += f"- **Média de gols**: Casa {home_goals_home:.2f} (mandante), Fora {away_goals_away:.2f} (visitante)\n"
        justification += f"- **Histórico BTTS**: Casa {home_btts_pct:.0f}%, Fora {away_btts_pct:.0f}%"
        
        if h2h_btts_pct > 0:
            justification += f", H2H {h2h_btts_pct:.0f}%\n"
        else:
            justification += "\n"
            
        justification += f"- **Previsão de gols**: {total_expected_goals:.2f} gols totais na partida\n"
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa btts_yes: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_btts_no_justification(home_team, away_team, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para Ambos Marcam - Não"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # Clean sheets
        home_cs_pct = home_team_data.get("clean_sheets_pct", 0)
        away_cs_pct = away_team_data.get("clean_sheets_pct", 0)
        
        # xG e médias de gols
        home_xg = home_team_data.get("xg_for_avg_overall", 0)
        home_xg_home = home_team_data.get("xg_for_avg_home", home_xg)
        away_xg = away_team_data.get("xg_for_avg_overall", 0)
        away_xg_away = away_team_data.get("xg_for_avg_away", away_xg)
        
        # Médias de gols
        home_goals_conceded = home_team_data.get("home_goals_conceded", 0)
        home_played = home_team_data.get("home_played", 1)
        away_goals_conceded = away_team_data.get("away_goals_conceded", 0)
        away_played = away_team_data.get("away_played", 1)
        
        home_conceded_home = home_goals_conceded / max(1, home_played)
        away_conceded_away = away_goals_conceded / max(1, away_played)
        
        # Percentuais de BTTS
        home_btts_pct = home_team_data.get("btts_pct", 0)
        away_btts_pct = away_team_data.get("btts_pct", 0)
        h2h_btts_pct = h2h_data.get("btts_pct", 0)
        
        # Total esperado de gols
        total_expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 0)
        
        # Construir justificativa
        justification = f"- **Clean Sheets**: Casa {home_cs_pct:.0f}%, Fora {away_cs_pct:.0f}%\n"
        justification += f"- **xG**: Casa {home_xg_home:.2f} (mandante), Fora {away_xg_away:.2f} (visitante)\n"
        justification += f"- **Média de gols sofridos**: Casa {home_conceded_home:.2f} (mandante), Fora {away_conceded_away:.2f} (visitante)\n"
        justification += f"- **Histórico BTTS-Não**: Casa {100-home_btts_pct:.0f}%, Fora {100-away_btts_pct:.0f}%"
        
        if h2h_btts_pct > 0:
            justification += f", H2H {100-h2h_btts_pct:.0f}%\n"
        else:
            justification += "\n"
            
        justification += f"- **Previsão de gols**: {total_expected_goals:.2f} gols totais na partida\n"
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa btts_no: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_over_goals_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para Over X.5 Gols"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # xG e médias de gols
        home_xg = home_team_data.get("xg_for_avg_overall", 0)
        home_xg_home = home_team_data.get("xg_for_avg_home", home_xg)
        away_xg = away_team_data.get("xg_for_avg_overall", 0)
        away_xg_away = away_team_data.get("xg_for_avg_away", away_xg)
        
        # Médias de gols
        home_goals_scored = home_team_data.get("home_goals_scored", 0)
        home_goals_conceded = home_team_data.get("home_goals_conceded", 0)
        home_played = home_team_data.get("home_played", 1)
        
        away_goals_scored = away_team_data.get("away_goals_scored", 0)
        away_goals_conceded = away_team_data.get("away_goals_conceded", 0)
        away_played = away_team_data.get("away_played", 1)
        
        home_goals_home = home_goals_scored / max(1, home_played)
        home_conceded_home = home_goals_conceded / max(1, home_played)
        away_goals_away = away_goals_scored / max(1, away_played)
        away_conceded_away = away_goals_conceded / max(1, away_played)
        
        # Percentuais de Over
        threshold_key = str(threshold).replace(".", "_")
        home_over_key = f"over_{threshold_key}_percentage"
        away_over_key = f"over_{threshold_key}_percentage"
        h2h_over_key = f"over_{threshold_key}_percentage"
        
        home_over_pct = home_team_data.get(home_over_key, 0)
        away_over_pct = away_team_data.get(away_over_key, 0)
        h2h_over_pct = h2h_data.get(h2h_over_key, 0)
        
        # Total esperado de gols
        total_expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 0)
        
        # Verificar se o total esperado é maior/menor que o threshold
        if total_expected_goals > threshold:
            comparison = "acima"
        else:
            comparison = "próximo"
        
        # Construir justificativa
        justification = f"- **xG**: Casa {home_xg_home:.2f} (mandante), Fora {away_xg_away:.2f} (visitante)\n"
        justification += f"- **Média de gols (mandante)**: Casa marca {home_goals_home:.2f} e sofre {home_conceded_home:.2f}\n"
        justification += f"- **Média de gols (visitante)**: Fora marca {away_goals_away:.2f} e sofre {away_conceded_away:.2f}\n"
        
        if home_over_pct > 0 or away_over_pct > 0:
            justification += f"- **Histórico Over {threshold}**: Casa {home_over_pct:.0f}%, Fora {away_over_pct:.0f}%"
            
            if h2h_over_pct > 0:
                justification += f", H2H {h2h_over_pct:.0f}%\n"
            else:
                justification += "\n"
        
        justification += f"- **Previsão de gols**: {total_expected_goals:.2f} gols totais, {comparison} do threshold {threshold}\n"
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa over_goals: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_under_goals_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para Under X.5 Gols"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # xG e médias de gols
        home_xg = home_team_data.get("xg_for_avg_overall", 0)
        home_xg_home = home_team_data.get("xg_for_avg_home", home_xg)
        away_xg = away_team_data.get("xg_for_avg_overall", 0)
        away_xg_away = away_team_data.get("xg_for_avg_away", away_xg)
        
        # Médias de gols
        home_goals_scored = home_team_data.get("home_goals_scored", 0)
        home_goals_conceded = home_team_data.get("home_goals_conceded", 0)
        home_played = home_team_data.get("home_played", 1)
        
        away_goals_scored = away_team_data.get("away_goals_scored", 0)
        away_goals_conceded = away_team_data.get("away_goals_conceded", 0)
        away_played = away_team_data.get("away_played", 1)
        
        home_goals_home = home_goals_scored / max(1, home_played)
        home_conceded_home = home_goals_conceded / max(1, home_played)
        away_goals_away = away_goals_scored / max(1, away_played)
        away_conceded_away = away_goals_conceded / max(1, away_played)
        
        # Percentuais de Under
        threshold_key = str(threshold).replace(".", "_")
        home_under_key = f"under_{threshold_key}_percentage"
        away_under_key = f"under_{threshold_key}_percentage"
        h2h_under_key = f"under_{threshold_key}_percentage"
        
        # Se não existir direto, calcular como 100% - over%
        if home_under_key not in home_team_data:
            home_over_key = f"over_{threshold_key}_percentage"
            home_under_pct = 100 - home_team_data.get(home_over_key, 0)
        else:
            home_under_pct = home_team_data.get(home_under_key, 0)
            
        if away_under_key not in away_team_data:
            away_over_key = f"over_{threshold_key}_percentage"
            away_under_pct = 100 - away_team_data.get(away_over_key, 0)
        else:
            away_under_pct = away_team_data.get(away_under_key, 0)
            
        if h2h_under_key not in h2h_data:
            h2h_over_key = f"over_{threshold_key}_percentage"
            h2h_under_pct = 100 - h2h_data.get(h2h_over_key, 0)
        else:
            h2h_under_pct = h2h_data.get(h2h_under_key, 0)
        
        # Total esperado de gols
        total_expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 0)
        
        # Verificar se o total esperado é maior/menor que o threshold
        if total_expected_goals < threshold:
            comparison = "abaixo"
        else:
            comparison = "próximo"
        
        # Construir justificativa
        justification = f"- **xG**: Casa {home_xg_home:.2f} (mandante), Fora {away_xg_away:.2f} (visitante)\n"
        justification += f"- **Média de gols (mandante)**: Casa marca {home_goals_home:.2f} e sofre {home_conceded_home:.2f}\n"
        justification += f"- **Média de gols (visitante)**: Fora marca {away_goals_away:.2f} e sofre {away_conceded_away:.2f}\n"
        
        if home_under_pct > 0 or away_under_pct > 0:
            justification += f"- **Histórico Under {threshold}**: Casa {home_under_pct:.0f}%, Fora {away_under_pct:.0f}%"
            
            if h2h_under_pct > 0:
                justification += f", H2H {h2h_under_pct:.0f}%\n"
            else:
                justification += "\n"
        
        justification += f"- **Previsão de gols**: {total_expected_goals:.2f} gols totais, {comparison} do threshold {threshold}\n"
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa under_goals: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_over_corners_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para Over X.5 Escanteios"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # Médias de escanteios
        home_corners_avg = home_team_data.get("corners_per_game", 0)
        home_corners_home = home_team_data.get("home_corners_per_game", home_corners_avg)
        away_corners_avg = away_team_data.get("corners_per_game", 0)
        away_corners_away = away_team_data.get("away_corners_per_game", away_corners_avg)
        
        # Escanteios contra
        home_corners_against = home_team_data.get("cornersAgainstAVG_home", 0) or home_team_data.get("cornersAgainstAVG_overall", 0)
        away_corners_against = away_team_data.get("cornersAgainstAVG_away", 0) or away_team_data.get("cornersAgainstAVG_overall", 0)
        
        # Posse de bola
        home_possession = home_team_data.get("possession", 50)
        away_possession = away_team_data.get("possession", 50)
        
        # Percentuais de Over
        threshold_key = str(threshold).replace(".", "_")
        home_over_key = f"over_{threshold_key}_corners_percentage"
        away_over_key = f"over_{threshold_key}_corners_percentage"
        
        home_over_pct = home_team_data.get(home_over_key, 0)
        away_over_pct = away_team_data.get(away_over_key, 0)
        
        # Total esperado de escanteios
        total_expected_corners = original_probabilities.get("corners", {}).get("expected_corners", 0)
        
        # Verificar se o total esperado é maior/menor que o threshold
        if total_expected_corners > threshold:
            comparison = "acima"
        else:
            comparison = "próximo"
        
        # Construir justificativa
        justification = f"- **Escanteios (mandante)**: Casa {home_corners_home:.1f} a favor vs {home_corners_against:.1f} contra\n"
        justification += f"- **Escanteios (visitante)**: Fora {away_corners_away:.1f} a favor vs {away_corners_against:.1f} contra\n"
        
        if home_possession > 0 and away_possession > 0:
            justification += f"- **Posse de bola**: Casa {home_possession:.0f}% vs Fora {away_possession:.0f}%\n"
        
        if home_over_pct > 0 or away_over_pct > 0:
            justification += f"- **Histórico Over {threshold}**: Casa {home_over_pct:.0f}%, Fora {away_over_pct:.0f}%\n"
        
        justification += f"- **Previsão de escanteios**: {total_expected_corners:.1f} totais, {comparison} do threshold {threshold}\n"
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa over_corners: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_under_corners_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para Under X.5 Escanteios"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        h2h_data = original_probabilities.get("h2h", {})
        
        # Médias de escanteios
        home_corners_avg = home_team_data.get("corners_per_game", 0)
        home_corners_home = home_team_data.get("home_corners_per_game", home_corners_avg)
        away_corners_avg = away_team_data.get("corners_per_game", 0)
        away_corners_away = away_team_data.get("away_corners_per_game", away_corners_avg)
        
        # Escanteios contra
        home_corners_against = home_team_data.get("cornersAgainstAVG_home", 0) or home_team_data.get("cornersAgainstAVG_overall", 0)
        away_corners_against = away_team_data.get("cornersAgainstAVG_away", 0) or away_team_data.get("cornersAgainstAVG_overall", 0)
        
        # Posse de bola
        home_possession = home_team_data.get("possession", 50)
        away_possession = away_team_data.get("possession", 50)
        
        # Percentuais de Under
        threshold_key = str(threshold).replace(".", "_")
        home_under_key = f"under_{threshold_key}_corners_percentage"
        away_under_key = f"under_{threshold_key}_corners_percentage"
        
        # Se não existir direto, calcular como 100% - over%
        if home_under_key not in home_team_data:
            home_over_key = f"over_{threshold_key}_corners_percentage"
            home_under_pct = 100 - home_team_data.get(home_over_key, 0)
        else:
            home_under_pct = home_team_data.get(home_under_key, 0)
            
        if away_under_key not in away_team_data:
            away_over_key = f"over_{threshold_key}_corners_percentage"
            away_under_pct = 100 - away_team_data.get(away_over_key, 0)
        else:
            away_under_pct = away_team_data.get(away_under_key, 0)
        
        # Total esperado de escanteios
        total_expected_corners = original_probabilities.get("corners", {}).get("expected_corners", 0)
        
        # Verificar se o total esperado é maior/menor que o threshold
        if total_expected_corners < threshold:
            comparison = "abaixo"
        else:
            comparison = "próximo"
        
        # Construir justificativa
        justification = f"- **Escanteios (mandante)**: Casa {home_corners_home:.1f} a favor vs {home_corners_against:.1f} contra\n"
        justification += f"- **Escanteios (visitante)**: Fora {away_corners_away:.1f} a favor vs {away_corners_against:.1f} contra\n"
        
        if home_possession > 0 and away_possession > 0:
            justification += f"- **Posse de bola**: Casa {home_possession:.0f}% vs Fora {away_possession:.0f}%\n"
        
        if home_under_pct > 0 or away_under_pct > 0:
            justification += f"- **Histórico Under {threshold}**: Casa {home_under_pct:.0f}%, Fora {away_under_pct:.0f}%\n"
        
        justification += f"- **Previsão de escanteios**: {total_expected_corners:.1f} totais, {comparison} do threshold {threshold}\n"
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa under_corners: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_over_cards_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para Over X.5 Cartões"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        match_info = original_probabilities.get("match_info", {})
        
        # Médias de cartões
        home_cards_avg = home_team_data.get("cards_per_game", 0)
        home_cards_home = home_team_data.get("home_cards_per_game", home_cards_avg)
        away_cards_avg = away_team_data.get("cards_per_game", 0)
        away_cards_away = away_team_data.get("away_cards_per_game", away_cards_avg)
        
        # Cartões provocados (contra)
        home_cards_against = home_team_data.get("cards_against", 0) / max(1, home_team_data.get("played", 1))
        away_cards_against = away_team_data.get("cards_against", 0) / max(1, away_team_data.get("played", 1))
        
        # Árbitro
        referee = match_info.get("referee", "")
        referee_avg_cards = match_info.get("referee_avg_cards", 0)
        
        # Percentuais de Over
        threshold_key = str(threshold).replace(".", "_")
        home_over_key = f"over_{threshold_key}_cards_percentage"
        away_over_key = f"over_{threshold_key}_cards_percentage"
        
        home_over_pct = home_team_data.get(home_over_key, 0)
        away_over_pct = away_team_data.get(away_over_key, 0)
        
        # Total esperado de cartões
        total_expected_cards = original_probabilities.get("cards", {}).get("expected_cards", 0)
        
        # Verificar se o total esperado é maior/menor que o threshold
        if total_expected_cards > threshold:
            comparison = "acima"
        else:
            comparison = "próximo"
        
        # Construir justificativa
        justification = f"- **Cartões (mandante)**: Casa {home_cards_home:.1f} recebidos / {home_cards_against:.1f} provocados\n"
        justification += f"- **Cartões (visitante)**: Fora {away_cards_away:.1f} recebidos / {away_cards_against:.1f} provocados\n"
        
        if referee and referee_avg_cards > 0:
            justification += f"- **Árbitro**: {referee} com média de {referee_avg_cards:.1f} cartões por jogo\n"
        
        if home_over_pct > 0 or away_over_pct > 0:
            justification += f"- **Histórico Over {threshold}**: Casa {home_over_pct:.0f}%, Fora {away_over_pct:.0f}%\n"
        
        # Dados sobre intensidade do jogo
        home_total_score = analysis_data.get("home_total_score", 0)
        away_total_score = analysis_data.get("away_total_score", 0)
        force_diff = abs(home_total_score - away_total_score)
        
        if force_diff < 0.15:
            justification += "- **Intensidade**: Jogo equilibrado tende a ter mais cartões\n"
        
        justification += f"- **Previsão de cartões**: {total_expected_cards:.1f} totais, {comparison} do threshold {threshold}\n"
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa over_cards: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_under_cards_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    """Justificativa para Under X.5 Cartões"""
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        match_info = original_probabilities.get("match_info", {})
        
        # Médias de cartões
        home_cards_avg = home_team_data.get("cards_per_game", 0)
        home_cards_home = home_team_data.get("home_cards_per_game", home_cards_avg)
        away_cards_avg = away_team_data.get("cards_per_game", 0)
        away_cards_away = away_team_data.get("away_cards_per_game", away_cards_avg)
        
        # Cartões provocados (contra)
        home_cards_against = home_team_data.get("cards_against", 0) / max(1, home_team_data.get("played", 1))
        away_cards_against = away_team_data.get("cards_against", 0) / max(1, away_team_data.get("played", 1))
        
        # Árbitro
        referee = match_info.get("referee", "")
        referee_avg_cards = match_info.get("referee_avg_cards", 0)
        
        # Percentuais de Under
        threshold_key = str(threshold).replace(".", "_")
        home_under_key = f"under_{threshold_key}_cards_percentage"
        away_under_key = f"under_{threshold_key}_cards_percentage"
        
        # Se não existir direto, calcular como 100% - over%
        if home_under_key not in home_team_data:
            home_over_key = f"over_{threshold_key}_cards_percentage"
            home_under_pct = 100 - home_team_data.get(home_over_key, 0)
        else:
            home_under_pct = home_team_data.get(home_under_key, 0)
            
        if away_under_key not in away_team_data:
            away_over_key = f"over_{threshold_key}_cards_percentage"
            away_under_pct = 100 - away_team_data.get(away_over_key, 0)
        else:
            away_under_pct = away_team_data.get(away_under_key, 0)
        
        # Total esperado de cartões
        total_expected_cards = original_probabilities.get("cards", {}).get("expected_cards", 0)
        
        # Verificar se o total esperado é maior/menor que o threshold
        if total_expected_cards < threshold:
            comparison = "abaixo"
        else:
            comparison = "próximo"
        
        # Construir justificativa
        justification = f"- **Cartões (mandante)**: Casa {home_cards_home:.1f} recebidos / {home_cards_against:.1f} provocados\n"
        justification += f"- **Cartões (visitante)**: Fora {away_cards_away:.1f} recebidos / {away_cards_against:.1f} provocados\n"
        
        if referee and referee_avg_cards > 0:
            justification += f"- **Árbitro**: {referee} com média de {referee_avg_cards:.1f} cartões por jogo\n"
        
        if home_under_pct > 0 or away_under_pct > 0:
            justification += f"- **Histórico Under {threshold}**: Casa {home_under_pct:.0f}%, Fora {away_under_pct:.0f}%\n"
        
        # Dados sobre intensidade do jogo
        home_total_score = analysis_data.get("home_total_score", 0)
        away_total_score = analysis_data.get("away_total_score", 0)
        force_diff = abs(home_total_score - away_total_score)
        
        if force_diff > 0.25:
            justification += "- **Intensidade**: Diferença de qualidade pode resultar em jogo menos disputado\n"
        
        justification += f"- **Previsão de cartões**: {total_expected_cards:.1f} totais, {comparison} do threshold {threshold}\n"
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa under_cards: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_condensed_justification(team_name, home_team, away_team, real_prob, implied_prob, analysis_data, original_probabilities, expected_goals=None):
    """
    Gera uma justificativa condensada específica para cada tipo de mercado,
    usando os nomes dos times e mostrando forma apenas para mercados relevantes.
    """
    import re
    
    # Identificar o tipo de mercado e o threshold (se aplicável)
    market_type = ""
    threshold = None
    threshold_direction = None
    
    # Padrão para identificar threshold (linha)
    threshold_pattern = r'([Oo]ver|[Uu]nder)\s+(\d+\.?\d*)'
    threshold_match = re.search(threshold_pattern, team_name)
    
    if threshold_match:
        threshold_direction = threshold_match.group(1).lower()  # "over" ou "under"
        threshold = float(threshold_match.group(2))
    
    # Extrair dados básicos apenas se formos usá-los
    home_form_points = analysis_data.get("home_form_points", 0) * 15
    away_form_points = analysis_data.get("away_form_points", 0) * 15
    
    # Extrair dados específicos de cada time
    home_team_data = original_probabilities.get("home_team", {})
    away_team_data = original_probabilities.get("away_team", {})
    
    # Determinar o tipo de mercado
    if team_name == home_team or team_name == away_team or team_name == "Empate":
        market_type = "moneyline"
    elif "ou" in team_name:
        market_type = "double_chance"
    elif "Ambos Marcam" in team_name:
        market_type = "btts"
    elif "Gols" in team_name:
        market_type = "goals"
    elif "Escanteios" in team_name:
        market_type = "corners"
    elif "Cartões" in team_name:
        market_type = "cards"
    else:
        market_type = "unknown"
    
    # Construir justificativa com base no tipo de mercado
    justification = ""
    
    # 1. MONEYLINE (1X2) - INCLUI FORMA
    if market_type == "moneyline":
        if team_name == home_team:
            # Vitória do time da casa
            home_consistency = analysis_data.get("home_consistency", 0)
            home_wins = home_team_data.get("home_wins", 0)
            home_draws = home_team_data.get("home_draws", 0)
            home_losses = home_team_data.get("home_losses", 0)
            
            justification = f"{home_team} em casa: {home_form_points:.0f}/15 pts, {home_consistency:.0f}% consistência. "
            
            if home_wins + home_draws + home_losses > 0:
                win_pct = (home_wins / (home_wins + home_draws + home_losses)) * 100
                justification += f"Venceu {win_pct:.0f}% dos jogos como mandante. "
            
            justification += f"Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
            
        elif team_name == away_team:
            # Vitória do time visitante
            away_consistency = analysis_data.get("away_consistency", 0)
            away_wins = away_team_data.get("away_wins", 0)
            away_draws = away_team_data.get("away_draws", 0)
            away_losses = away_team_data.get("away_losses", 0)
            
            justification = f"{away_team} fora: {away_form_points:.0f}/15 pts, {away_consistency:.0f}% consistência. "
            
            if away_wins + away_draws + away_losses > 0:
                win_pct = (away_wins / (away_wins + away_draws + away_losses)) * 100
                justification += f"Venceu {win_pct:.0f}% dos jogos como visitante. "
            
            justification += f"Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
            
        elif team_name == "Empate":
            # Empate
            home_draw_pct = home_team_data.get("draw_pct", 0)
            away_draw_pct = away_team_data.get("draw_pct", 0)
            
            justification = f"{home_team} vs {away_team}. "
            
            if home_draw_pct > 0 and away_draw_pct > 0:
                justification += f"Tendência de empates: {home_team} {home_draw_pct:.0f}%, {away_team} {away_draw_pct:.0f}%. "
            
            justification += f"Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
    
    # 2. DUPLA CHANCE - INCLUI FORMA
    elif market_type == "double_chance":
        if home_team in team_name and "Empate" in team_name:
            # Casa ou Empate
            home_consistency = analysis_data.get("home_consistency", 0)
            
            justification = f"{home_team} em casa: {home_form_points:.0f}/15 pts, {home_consistency:.0f}% consistência. "
            justification += f"Probabilidade de {real_prob:.1f}% de não perder vs {implied_prob:.1f}% das odds."
            
        elif away_team in team_name and "Empate" in team_name:
            # Fora ou Empate
            away_consistency = analysis_data.get("away_consistency", 0)
            
            justification = f"{away_team} fora: {away_form_points:.0f}/15 pts, {away_consistency:.0f}% consistência. "
            justification += f"Probabilidade de {real_prob:.1f}% de não perder vs {implied_prob:.1f}% das odds."
            
        elif home_team in team_name and away_team in team_name:
            # Casa ou Fora
            justification = f"Baixa probabilidade de empate entre {home_team} e {away_team}. "
            justification += f"Probabilidade de {real_prob:.1f}% vs {implied_prob:.1f}% das odds."
    
    # 3. AMBOS MARCAM (BTTS) - SEM FORMA
    elif market_type == "btts":
        # Extrair estatísticas de BTTS
        home_btts_pct = home_team_data.get("btts_pct", 0)
        away_btts_pct = away_team_data.get("btts_pct", 0)
        home_cs_pct = home_team_data.get("clean_sheets_pct", 0)
        away_cs_pct = away_team_data.get("clean_sheets_pct", 0)
        
        # Total esperado de gols
        total_expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 0)
        
        if "Sim" in team_name:
            justification = f"{home_team} vs {away_team}. BTTS: {home_team} {home_btts_pct:.0f}%, {away_team} {away_btts_pct:.0f}%. "
            justification += f"Previsão {total_expected_goals:.2f} gols. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
        else:  # Não
            justification = f"{home_team} vs {away_team}. Clean Sheets: {home_team} {home_cs_pct:.0f}%, {away_team} {away_cs_pct:.0f}%. "
            justification += f"Previsão {total_expected_goals:.2f} gols. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
    
    # 4. TOTAL DE GOLS - SEM FORMA
    elif market_type == "goals" and threshold is not None:
        # Extrair médias de gols
        home_goals_scored = home_team_data.get("home_goals_scored", 0)
        home_played = home_team_data.get("home_played", 1)
        away_goals_scored = away_team_data.get("away_goals_scored", 0)
        away_played = away_team_data.get("away_played", 1)
        
        home_goals_home = home_goals_scored / max(1, home_played)
        away_goals_away = away_goals_scored / max(1, away_played)
        
        # Total esperado de gols
        total_expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 0)
        
        # Verificar se o total esperado é maior/menor que o threshold
        if threshold_direction == "over":
            if total_expected_goals > threshold:
                comparison = "acima"
            else:
                comparison = "próximo"
                
            justification = f"{home_team} marca {home_goals_home:.2f} e {away_team} marca {away_goals_away:.2f} gols em média. "
            justification += f"Previsão {total_expected_goals:.2f} gols, {comparison} de {threshold}. "
            justification += f"Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
        else:  # under
            if total_expected_goals < threshold:
                comparison = "abaixo"
            else:
                comparison = "próximo"
                
            justification = f"{home_team} marca {home_goals_home:.2f} e {away_team} marca {away_goals_away:.2f} gols em média. "
            justification += f"Previsão {total_expected_goals:.2f} gols, {comparison} de {threshold}. "
            justification += f"Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
    
    # 5. ESCANTEIOS - SEM FORMA
    elif market_type == "corners" and threshold is not None:
        # Extrair médias de escanteios
        home_corners_home = home_team_data.get("home_corners_per_game", 0)
        away_corners_away = away_team_data.get("away_corners_per_game", 0)
        
        # Total esperado de escanteios
        total_expected_corners = original_probabilities.get("corners", {}).get("expected_corners", 0)
        
        # Verificar se o total esperado é maior/menor que o threshold
        if threshold_direction == "over":
            if total_expected_corners > threshold:
                comparison = "acima"
            else:
                comparison = "próximo"
                
            justification = f"{home_team} ({home_corners_home:.1f}) vs {away_team} ({away_corners_away:.1f}) escanteios em média. "
            justification += f"Previsão {total_expected_corners:.1f} escanteios, {comparison} de {threshold}. "
            justification += f"Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
        else:  # under
            if total_expected_corners < threshold:
                comparison = "abaixo"
            else:
                comparison = "próximo"
                
            justification = f"{home_team} ({home_corners_home:.1f}) vs {away_team} ({away_corners_away:.1f}) escanteios em média. "
            justification += f"Previsão {total_expected_corners:.1f} escanteios, {comparison} de {threshold}. "
            justification += f"Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
    
    # 6. CARTÕES - SEM FORMA
    elif market_type == "cards" and threshold is not None:
        # Extrair médias de cartões
        home_cards_home = home_team_data.get("home_cards_per_game", 0)
        away_cards_away = away_team_data.get("away_cards_per_game", 0)
        
        # Total esperado de cartões
        total_expected_cards = original_probabilities.get("cards", {}).get("expected_cards", 0)
        
        # Árbitro (se disponível)
        referee = original_probabilities.get("match_info", {}).get("referee", "")
        referee_avg_cards = original_probabilities.get("match_info", {}).get("referee_avg_cards", 0)
        
        # Verificar se o total esperado é maior/menor que o threshold
        if threshold_direction == "over":
            if total_expected_cards > threshold:
                comparison = "acima"
            else:
                comparison = "próximo"
                
            justification = f"{home_team} ({home_cards_home:.1f}) vs {away_team} ({away_cards_away:.1f}) cartões em média. "
            
            if referee and referee_avg_cards > 0:
                justification += f"Árbitro: média de {referee_avg_cards:.1f} cartões/jogo. "
                
            justification += f"Previsão {total_expected_cards:.1f} cartões, {comparison} de {threshold}. "
            justification += f"Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
        else:  # under
            if total_expected_cards < threshold:
                comparison = "abaixo"
            else:
                comparison = "próximo"
                
            justification = f"{home_team} ({home_cards_home:.1f}) vs {away_team} ({away_cards_away:.1f}) cartões em média. "
            
            if referee and referee_avg_cards > 0:
                justification += f"Árbitro: média de {referee_avg_cards:.1f} cartões/jogo. "
                
            justification += f"Previsão {total_expected_cards:.1f} cartões, {comparison} de {threshold}. "
            justification += f"Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
    
    # Caso não identifique o mercado, retorna justificativa genérica
    else:
        justification = f"{home_team} vs {away_team}. "
        justification += f"Valor de {real_prob-implied_prob:.1f}% entre probabilidade real ({real_prob:.1f}%) e odds ({implied_prob:.1f}%)."
    
    return justification
