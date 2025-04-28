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
                content = (
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
        
        # Forma e consistência - CORRIGIDO
        form_details = analysis_data.get("form_details", {})
        home_specific = form_details.get("home_specific", {})
        home_overall = form_details.get("home_overall", {})
        
        # Obter pontos de forma das fontes corretas
        home_form_points = 0
        if home_specific and "points" in home_specific:
            home_form_points = home_specific.get("points", 0)
        elif home_overall and "points" in home_overall:
            home_form_points = home_overall.get("points", 0)
        
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
        justification = f"- **Forma como mandante**: {home_form_points}/15 pontos, consistência de {home_consistency:.1f}%\n"
        
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
        
        # Forma e consistência - CORRIGIDO
        form_details = analysis_data.get("form_details", {})
        away_specific = form_details.get("away_specific", {})
        away_overall = form_details.get("away_overall", {})
        
        # Obter pontos de forma das fontes corretas
        away_form_points = 0
        if away_specific and "points" in away_specific:
            away_form_points = away_specific.get("points", 0)
        elif away_overall and "points" in away_overall:
            away_form_points = away_overall.get("points", 0)
        
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
        justification = f"- **Forma como visitante**: {away_form_points}/15 pontos, consistência de {away_consistency:.1f}%\n"
        
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
        
        # Forma e consistência - CORRIGIDO
        form_details = analysis_data.get("form_details", {})
        
        # Obter pontos de forma para casa
        home_specific = form_details.get("home_specific", {})
        home_overall = form_details.get("home_overall", {})
        home_form_points = 0
        if home_specific and "points" in home_specific:
            home_form_points = home_specific.get("points", 0)
        elif home_overall and "points" in home_overall:
            home_form_points = home_overall.get("points", 0)
            
        # Obter pontos de forma para fora
        away_specific = form_details.get("away_specific", {})
        away_overall = form_details.get("away_overall", {})
        away_form_points = 0
        if away_specific and "points" in away_specific:
            away_form_points = away_specific.get("points", 0)
        elif away_overall and "points" in away_overall:
            away_form_points = away_overall.get("points", 0)
        
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
        justification = f"- **Forma dos times**: Casa com {home_form_points}/15 pts, Fora com {away_form_points}/15 pts\n"
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
        
        # Forma e consistência - CORRIGIDO
        form_details = analysis_data.get("form_details", {})
        home_specific = form_details.get("home_specific", {})
        home_overall = form_details.get("home_overall", {})
        
        # Obter pontos de forma das fontes corretas
        home_form_points = 0
        if home_specific and "points" in home_specific:
            home_form_points = home_specific.get("points", 0)
        elif home_overall and "points" in home_overall:
            home_form_points = home_overall.get("points", 0)
        
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
        justification = f"- **Forma como mandante**: {home_form_points}/15 pontos, consistência de {home_consistency:.1f}%\n"
        
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
        
        # Forma e consistência - CORRIGIDO
        form_details = analysis_data.get("form_details", {})
        away_specific = form_details.get("away_specific", {})
        away_overall = form_details.get("away_overall", {})
        
        # Obter pontos de forma das fontes corretas
        away_form_points = 0
        if away_specific and "points" in away_specific:
            away_form_points = away_specific.get("points", 0)
        elif away_overall and "points" in away_overall:
            away_form_points = away_overall.get("points", 0)
        
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
        justification = f"- **Forma como visitante**: {away_form_points}/15 pontos, consistência de {away_consistency:.1f}%\n"
        
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
        
        # Estatísticas de gols
        home_goals_per_game = home_team_data.get("goals_per_game", 0)
        away_goals_per_game = away_team_data.get("goals_per_game", 0)
        home_conceded_per_game = home_team_data.get("conceded_per_game", 0)
        away_conceded_per_game = away_team_data.get("conceded_per_game", 0)
        
        # Percentuais de BTTS
        home_btts_pct = home_team_data.get("btts_pct", 0)
        away_btts_pct = away_team_data.get("btts_pct", 0)
        
        # Dados H2H
        h2h_btts_pct = h2h_data.get("btts_percentage", 0)
        total_h2h = h2h_data.get("total_matches", 0)
        
        # Construir justificativa
        justification = f"- **Média de gols**: {home_team} marca {home_goals_per_game:.2f} e sofre {home_conceded_per_game:.2f} por jogo\n"
        justification += f"- **Média de gols**: {away_team} marca {away_goals_per_game:.2f} e sofre {away_conceded_per_game:.2f} por jogo\n"
        
        justification += f"- **Tendência BTTS**: {home_team} tem {home_btts_pct:.0f}% de jogos com ambos marcam\n"
        justification += f"- **Tendência BTTS**: {away_team} tem {away_btts_pct:.0f}% de jogos com ambos marcam\n"
        
        if total_h2h > 0:
            justification += f"- **Histórico H2H**: {h2h_btts_pct:.0f}% dos confrontos terminaram com ambos marcando\n"
        
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
        
        # Estatísticas de clean sheets
        home_cs_pct = home_team_data.get("clean_sheet_pct", 0)
        away_cs_pct = away_team_data.get("clean_sheet_pct", 0)
        home_failed_to_score_pct = home_team_data.get("failed_to_score_pct", 0)
        away_failed_to_score_pct = away_team_data.get("failed_to_score_pct", 0)
        
        # Percentuais de BTTS
        home_btts_pct = home_team_data.get("btts_pct", 0)
        away_btts_pct = away_team_data.get("btts_pct", 0)
        
        # Dados H2H
        h2h_btts_pct = h2h_data.get("btts_percentage", 0)
        total_h2h = h2h_data.get("total_matches", 0)
        
        # Construir justificativa
        justification = f"- **Clean sheets**: {home_team} mantém o zero em {home_cs_pct:.0f}% dos jogos\n"
        justification += f"- **Clean sheets**: {away_team} mantém o zero em {away_cs_pct:.0f}% dos jogos\n"
        
        justification += f"- **Falha em marcar**: {home_team} não marca em {home_failed_to_score_pct:.0f}% dos jogos\n"
        justification += f"- **Falha em marcar**: {away_team} não marca em {away_failed_to_score_pct:.0f}% dos jogos\n"
        
        if total_h2h > 0:
            no_btts_pct = 100 - h2h_btts_pct
            justification += f"- **Histórico H2H**: {no_btts_pct:.0f}% dos confrontos terminaram sem ambos marcarem\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logging.getLogger("valueHunter.ai").error(f"Erro em justificativa btts_no: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_over_goals_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        ou_data = original_probabilities.get("over_under", {})
        
        # Estatísticas de gols - Garantir que temos os valores
        home_goals_per_game = home_team_data.get("goals_per_game", 0)
        away_goals_per_game = away_team_data.get("goals_per_game", 0)
        home_conceded_per_game = home_team_data.get("conceded_per_game", 0)
        away_conceded_per_game = away_team_data.get("conceded_per_game", 0)
        
        # Logging para debug
        logger.info(f"GOLS - Casa marca: {home_goals_per_game}, sofre: {home_conceded_per_game}")
        logger.info(f"GOLS - Fora marca: {away_goals_per_game}, sofre: {away_conceded_per_game}")
        
        # Expected goals
        expected_goals = ou_data.get("expected_goals", home_goals_per_game + away_goals_per_game)
        
        # Construir justificativa
        justification = f"- **Média de gols**: {home_team} marca {home_goals_per_game:.2f} e sofre {home_conceded_per_game:.2f} por jogo\n"
        justification += f"- **Média de gols**: {away_team} marca {away_goals_per_game:.2f} e sofre {away_conceded_per_game:.2f} por jogo\n"
        
        justification += f"- **Expected goals**: Previsão de {expected_goals:.2f} gols nesta partida, acima do limite de {threshold}\n"
        
        # Adicionar percentuais de over se disponíveis
        if "over_2_5_pct" in home_team_data:
            justification += f"- **Tendência Over**: {home_team} tem {home_team_data.get('over_2_5_pct', 0):.0f}% de jogos acima de 2.5 gols\n"
        
        if "over_2_5_pct" in away_team_data:
            justification += f"- **Tendência Over**: {away_team} tem {away_team_data.get('over_2_5_pct', 0):.0f}% de jogos acima de 2.5 gols\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logger.error(f"Erro em justificativa over_goals: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_under_goals_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        ou_data = original_probabilities.get("over_under", {})
        
        # Estatísticas de gols - Garantir que temos os valores
        home_goals_per_game = home_team_data.get("goals_per_game", 0)
        away_goals_per_game = away_team_data.get("goals_per_game", 0)
        home_conceded_per_game = home_team_data.get("conceded_per_game", 0)
        away_conceded_per_game = away_team_data.get("conceded_per_game", 0)
        
        # Logging para debug
        logger.info(f"GOLS - Casa marca: {home_goals_per_game}, sofre: {home_conceded_per_game}")
        logger.info(f"GOLS - Fora marca: {away_goals_per_game}, sofre: {away_conceded_per_game}")
        
        # Expected goals
        expected_goals = ou_data.get("expected_goals", home_goals_per_game + away_goals_per_game)
        
        # Construir justificativa
        justification = f"- **Média de gols**: {home_team} marca {home_goals_per_game:.2f} e sofre {home_conceded_per_game:.2f} por jogo\n"
        justification += f"- **Média de gols**: {away_team} marca {away_goals_per_game:.2f} e sofre {away_conceded_per_game:.2f} por jogo\n"
        
        justification += f"- **Expected goals**: Previsão de {expected_goals:.2f} gols nesta partida, abaixo do limite de {threshold}\n"
        
        # Dados sobre clean sheets se disponíveis
        if "clean_sheets_pct" in home_team_data:
            justification += f"- **Clean sheets**: {home_team} mantém o zero em {home_team_data.get('clean_sheets_pct', 0):.0f}% dos jogos\n"
        
        if "clean_sheets_pct" in away_team_data:
            justification += f"- **Clean sheets**: {away_team} mantém o zero em {away_team_data.get('clean_sheets_pct', 0):.0f}% dos jogos\n"
        
        # Adicionar percentuais de under se disponíveis
        under_key = f"under_{str(threshold).replace('.', '_')}_pct"
        over_key = f"over_{str(threshold).replace('.', '_')}_pct"
        
        # Tenta encontrar estatísticas de under, senão calcula a partir de over
        if under_key in home_team_data:
            justification += f"- **Tendência Under {threshold}**: {home_team} tem {home_team_data.get(under_key, 0):.0f}% de jogos abaixo de {threshold} gols\n"
        elif over_key in home_team_data or "over_2_5_pct" in home_team_data:
            # Se não tem o threshold específico, usa over 2.5 como base
            over_pct = home_team_data.get(over_key, home_team_data.get("over_2_5_pct", 0))
            under_pct = 100 - over_pct
            justification += f"- **Tendência Under**: {home_team} tem {under_pct:.0f}% de jogos com poucos gols\n"
        
        if under_key in away_team_data:
            justification += f"- **Tendência Under {threshold}**: {away_team} tem {away_team_data.get(under_key, 0):.0f}% de jogos abaixo de {threshold} gols\n"
        elif over_key in away_team_data or "over_2_5_pct" in away_team_data:
            # Se não tem o threshold específico, usa over 2.5 como base
            over_pct = away_team_data.get(over_key, away_team_data.get("over_2_5_pct", 0))
            under_pct = 100 - over_pct
            justification += f"- **Tendência Under**: {away_team} tem {under_pct:.0f}% de jogos com poucos gols\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logger.error(f"Erro em justificativa under_goals: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_over_corners_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        corners_data = original_probabilities.get("corners", {})
        
        # Estatísticas de escanteios - Use múltiplas opções para encontrar os valores
        home_corners_per_game = home_team_data.get("cornersAVG_overall", 0) or home_team_data.get("corners_per_game", 0)
        away_corners_per_game = away_team_data.get("cornersAVG_overall", 0) or away_team_data.get("corners_per_game", 0)
        
        # Logging para debug
        logger.info(f"ESCANTEIOS - Casa: {home_corners_per_game}, Fora: {away_corners_per_game}")
        
        # Expected corners - usar o valor calculado
        expected_corners = corners_data.get("expected_corners", home_corners_per_game + away_corners_per_game)
        
        # Construir justificativa
        justification = f"- **Média de escanteios**: {home_team} ({home_corners_per_game:.2f}) vs {away_team} ({away_corners_per_game:.2f}) escanteios em média. Previsão {expected_corners:.1f} escanteios, acima de {threshold}.\n"
        
        # Adicionar informações de tendência se disponíveis
        if "over_9_5_corners_pct" in home_team_data:
            justification += f"- **Tendência Over {threshold}**: {home_team} tem {home_team_data.get('over_9_5_corners_pct', 0):.0f}% de jogos acima de {threshold} escanteios\n"
        
        if "over_9_5_corners_pct" in away_team_data:
            justification += f"- **Tendência Over {threshold}**: {away_team} tem {away_team_data.get('over_9_5_corners_pct', 0):.0f}% de jogos acima de {threshold} escanteios\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logger.error(f"Erro em justificativa over_corners: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_under_corners_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        corners_data = original_probabilities.get("corners", {})
        
        # Estatísticas de escanteios - Use múltiplas opções para encontrar os valores
        home_corners_per_game = home_team_data.get("cornersAVG_overall", 0) or home_team_data.get("corners_per_game", 0)
        away_corners_per_game = away_team_data.get("cornersAVG_overall", 0) or away_team_data.get("corners_per_game", 0)
        
        # Logging para debug
        logger.info(f"ESCANTEIOS - Casa: {home_corners_per_game}, Fora: {away_corners_per_game}")
        
        # Expected corners - usar o valor calculado
        expected_corners = corners_data.get("expected_corners", home_corners_per_game + away_corners_per_game)
        
        # Construir justificativa
        justification = f"- **Média de escanteios**: {home_team} ({home_corners_per_game:.2f}) vs {away_team} ({away_corners_per_game:.2f}) escanteios em média. Previsão {expected_corners:.1f} escanteios, abaixo de {threshold}.\n"
        
        # Adicionar informações de tendência se disponíveis
        under_key = f"under_{str(threshold).replace('.', '_')}_corners_pct"
        over_key = f"over_{str(threshold).replace('.', '_')}_corners_pct"
        
        # Tenta encontrar estatísticas de under, senão calcula a partir de over
        if under_key in home_team_data:
            justification += f"- **Tendência Under {threshold}**: {home_team} tem {home_team_data.get(under_key, 0):.0f}% de jogos abaixo de {threshold} escanteios\n"
        elif over_key in home_team_data:
            under_pct = 100 - home_team_data.get(over_key, 0)
            justification += f"- **Tendência Under {threshold}**: {home_team} tem {under_pct:.0f}% de jogos abaixo de {threshold} escanteios\n"
        
        if under_key in away_team_data:
            justification += f"- **Tendência Under {threshold}**: {away_team} tem {away_team_data.get(under_key, 0):.0f}% de jogos abaixo de {threshold} escanteios\n"
        elif over_key in away_team_data:
            under_pct = 100 - away_team_data.get(over_key, 0)
            justification += f"- **Tendência Under {threshold}**: {away_team} tem {under_pct:.0f}% de jogos abaixo de {threshold} escanteios\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logger.error(f"Erro em justificativa under_corners: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_over_cards_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        cards_data = original_probabilities.get("cards", {})
        
        # Estatísticas de cartões
        home_cards_per_game = home_team_data.get("cards_per_game", 0)
        away_cards_per_game = away_team_data.get("cards_per_game", 0)
        
        # Logging para debug
        logger.info(f"CARTÕES - Casa: {home_cards_per_game}, Fora: {away_cards_per_game}")
        
        # Expected cards
        expected_cards = cards_data.get("expected_cards", home_cards_per_game + away_cards_per_game)
        
        # Construir justificativa
        justification = f"- **Média de cartões**: {home_team} ({home_cards_per_game:.2f}) vs {away_team} ({away_cards_per_game:.2f}) cartões em média. Previsão {expected_cards:.1f} cartões, acima de {threshold}.\n"
        
        # Adicionar informações sobre cartões em casa/fora se disponíveis
        if "home_cards_per_game" in home_team_data and home_team_data["home_cards_per_game"] > 0:
            justification += f"- **Cartões em casa**: {home_team} recebe {home_team_data['home_cards_per_game']:.2f} cartões por jogo como mandante\n"
        
        if "away_cards_per_game" in away_team_data and away_team_data["away_cards_per_game"] > 0:
            justification += f"- **Cartões fora**: {away_team} recebe {away_team_data['away_cards_per_game']:.2f} cartões por jogo como visitante\n"
        
        # Adicionar informações de tendência se disponíveis
        over_key = f"over_{str(threshold).replace('.', '_')}_cards_pct"
        if over_key in home_team_data:
            justification += f"- **Tendência Over {threshold}**: {home_team} tem {home_team_data.get(over_key, 0):.0f}% de jogos acima de {threshold} cartões\n"
        elif "over_3_5_cards_pct" in home_team_data:
            justification += f"- **Tendência Over 3.5**: {home_team} tem {home_team_data.get('over_3_5_cards_pct', 0):.0f}% de jogos acima de 3.5 cartões\n"
        
        if over_key in away_team_data:
            justification += f"- **Tendência Over {threshold}**: {away_team} tem {away_team_data.get(over_key, 0):.0f}% de jogos acima de {threshold} cartões\n"
        elif "over_3_5_cards_pct" in away_team_data:
            justification += f"- **Tendência Over 3.5**: {away_team} tem {away_team_data.get('over_3_5_cards_pct', 0):.0f}% de jogos acima de 3.5 cartões\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logger.error(f"Erro em justificativa over_cards: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_under_cards_justification(home_team, away_team, threshold, real_prob, implied_prob, original_probabilities, analysis_data):
    try:
        # Extrair dados relevantes
        home_team_data = original_probabilities.get("home_team", {})
        away_team_data = original_probabilities.get("away_team", {})
        cards_data = original_probabilities.get("cards", {})
        
        # Estatísticas de cartões
        home_cards_per_game = home_team_data.get("cards_per_game", 0)
        away_cards_per_game = away_team_data.get("cards_per_game", 0)
        
        # Logging para debug
        logger.info(f"CARTÕES - Casa: {home_cards_per_game}, Fora: {away_cards_per_game}")
        
        # Expected cards
        expected_cards = cards_data.get("expected_cards", home_cards_per_game + away_cards_per_game)
        
        # Construir justificativa
        justification = f"- **Média de cartões**: {home_team} ({home_cards_per_game:.2f}) vs {away_team} ({away_cards_per_game:.2f}) cartões em média. Previsão {expected_cards:.1f} cartões, abaixo de {threshold}.\n"
        
        # Adicionar informações sobre cartões em casa/fora se disponíveis
        if "home_cards_per_game" in home_team_data and home_team_data["home_cards_per_game"] > 0:
            justification += f"- **Cartões em casa**: {home_team} recebe {home_team_data['home_cards_per_game']:.2f} cartões por jogo como mandante\n"
        
        if "away_cards_per_game" in away_team_data and away_team_data["away_cards_per_game"] > 0:
            justification += f"- **Cartões fora**: {away_team} recebe {away_team_data['away_cards_per_game']:.2f} cartões por jogo como visitante\n"
        
        # Adicionar informações de tendência se disponíveis
        under_key = f"under_{str(threshold).replace('.', '_')}_cards_pct"
        over_key = f"over_{str(threshold).replace('.', '_')}_cards_pct"
        
        # Tenta encontrar estatísticas de under, senão calcula a partir de over
        if under_key in home_team_data:
            justification += f"- **Tendência Under {threshold}**: {home_team} tem {home_team_data.get(under_key, 0):.0f}% de jogos abaixo de {threshold} cartões\n"
        elif over_key in home_team_data or "over_3_5_cards_pct" in home_team_data:
            # Se não tem o threshold específico, usa over 3.5 como base
            over_pct = home_team_data.get(over_key, home_team_data.get("over_3_5_cards_pct", 0))
            under_pct = 100 - over_pct
            justification += f"- **Tendência Under cartões**: {home_team} tem {under_pct:.0f}% de jogos com poucos cartões\n"
        
        if under_key in away_team_data:
            justification += f"- **Tendência Under {threshold}**: {away_team} tem {away_team_data.get(under_key, 0):.0f}% de jogos abaixo de {threshold} cartões\n"
        elif over_key in away_team_data or "over_3_5_cards_pct" in away_team_data:
            # Se não tem o threshold específico, usa over 3.5 como base
            over_pct = away_team_data.get(over_key, away_team_data.get("over_3_5_cards_pct", 0))
            under_pct = 100 - over_pct
            justification += f"- **Tendência Under cartões**: {away_team} tem {under_pct:.0f}% de jogos com poucos cartões\n"
        
        justification += f"- **Valor identificado**: Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, representando uma vantagem de {real_prob-implied_prob:.1f}%"
        
        return justification
    except Exception as e:
        logger.error(f"Erro em justificativa under_cards: {str(e)}")
        return f"Probabilidade real {real_prob:.1f}% vs implícita {implied_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."

def generate_condensed_justification(team_name, home_team, away_team, real_prob, implied_prob, analysis_data, original_probabilities, expected_goals=None):
    """
    Gera uma justificativa condensada para uso em oportunidades.
    """
    try:
        # Identificar o tipo de mercado
        if team_name == home_team:
            # Mercado de vitória do time da casa
            home_form_points = analysis_data.get("home_form_points", 0) * 15
            consistency = analysis_data.get("home_consistency", 0)
            return f"{home_team} em casa: {home_form_points:.0f}/15 pts, {consistency:.0f}% consistência.\nOdds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
            
        elif team_name == away_team:
            # Mercado de vitória do time visitante
            away_form_points = analysis_data.get("away_form_points", 0) * 15
            consistency = analysis_data.get("away_consistency", 0)
            return f"{away_team} fora: {away_form_points:.0f}/15 pts, {consistency:.0f}% consistência.\nOdds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
            
        elif team_name == "Empate":
            # Mercado de empate
            return f"Equilíbrio entre as equipes favorece o empate.\nOdds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
            
        elif "Over" in team_name and "Gols" in team_name:
            # Mercado de Over gols
            threshold = re.search(r"Over (\d+\.?\d*)", team_name).group(1)
            if expected_goals:
                return f"Previsão de {expected_goals:.1f} gols, acima de {threshold}. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
            else:
                # Tentar obter expected_goals de over_under
                expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 0)
                if expected_goals > 0:
                    return f"Previsão de {expected_goals:.1f} gols, acima de {threshold}. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
                else:
                    return f"Tendência ofensiva favorece mais de {threshold} gols. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
                
        elif "Under" in team_name and "Gols" in team_name:
            # Mercado de Under gols
            threshold = re.search(r"Under (\d+\.?\d*)", team_name).group(1)
            if expected_goals:
                return f"Previsão de {expected_goals:.1f} gols, abaixo de {threshold}. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
            else:
                # Tentar obter expected_goals de over_under
                expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 0)
                if expected_goals > 0:
                    return f"Previsão de {expected_goals:.1f} gols, abaixo de {threshold}. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
                else:
                    return f"Tendência defensiva favorece menos de {threshold} gols. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
                
        elif "Ambos Marcam - Sim" in team_name:
            # Mercado de BTTS Sim
            return f"Ambas equipes têm boa capacidade ofensiva. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
            
        elif "Ambos Marcam - Não" in team_name:
            # Mercado de BTTS Não
            return f"Pelo menos uma equipe deve manter o zero. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
            
        elif "Escanteios" in team_name:
            # Mercado de escanteios
            corners_data = original_probabilities.get("corners", {})
            expected_corners = corners_data.get("expected_corners", 0)
            
            # Estatísticas de escanteios - Use os dados diretamente do dicionário de times
            home_team_data = original_probabilities.get("home_team", {})
            away_team_data = original_probabilities.get("away_team", {})
            home_corners_per_game = home_team_data.get("cornersAVG_overall", 0) or home_team_data.get("corners_per_game", 0)
            away_corners_per_game = away_team_data.get("cornersAVG_overall", 0) or away_team_data.get("corners_per_game", 0)
            
            if "Over" in team_name:
                threshold = re.search(r"Over (\d+\.?\d*)", team_name).group(1)
                return f"{home_team} ({home_corners_per_game:.2f}) vs {away_team} ({away_corners_per_game:.2f})\nescanteios em média. Previsão {expected_corners:.1f} escanteios, acima de {threshold}. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
            else:
                threshold = re.search(r"Under (\d+\.?\d*)", team_name).group(1)
                return f"{home_team} ({home_corners_per_game:.2f}) vs {away_team} ({away_corners_per_game:.2f})\nescanteios em média. Previsão {expected_corners:.1f} escanteios, abaixo de {threshold}. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
                
        elif "Cartões" in team_name:
            # Mercado de cartões
            cards_data = original_probabilities.get("cards", {})
            expected_cards = cards_data.get("expected_cards", 0)
            
            # Estatísticas de cartões
            home_team_data = original_probabilities.get("home_team", {})
            away_team_data = original_probabilities.get("away_team", {})
            home_cards_per_game = home_team_data.get("cards_per_game", 0)
            away_cards_per_game = away_team_data.get("cards_per_game", 0)
            
            if "Over" in team_name:
                threshold = re.search(r"Over (\d+\.?\d*)", team_name).group(1)
                return f"{home_team} ({home_cards_per_game:.2f}) vs {away_team} ({away_cards_per_game:.2f})\ncartões em média. Previsão {expected_cards:.1f} cartões, acima de {threshold}. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
            else:
                threshold = re.search(r"Under (\d+\.?\d*)", team_name).group(1)
                return f"{home_team} ({home_cards_per_game:.2f}) vs {away_team} ({away_cards_per_game:.2f})\ncartões em média. Previsão {expected_cards:.1f} cartões, abaixo de {threshold}. Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
                
        else:
            # Mercado genérico
            return f"Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%, vantagem de {real_prob-implied_prob:.1f}%."
            
    except Exception as e:
        logger.error(f"Erro ao gerar justificativa condensada: {str(e)}")
        return f"Odds {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."

def form_to_points(form_str):
    """
    Converte string de forma em pontos (W=3, D=1, L=0)
    
    Args:
        form_str (str): String com a sequência de resultados (ex: "WDLWW")
        
    Returns:
        int: Pontuação total (máximo 15 pontos para 5 jogos)
    """
    if not form_str or not isinstance(form_str, str):
        return 0
        
    points = 0
    # Garantir que estamos usando apenas os últimos 5 jogos
    recent_form = form_str[-5:] if len(form_str) >= 5 else form_str
    
    # Calcular pontos
    for result in recent_form:
        result = result.upper()  # Converter para maiúscula para garantir
        if result == 'W':
            points += 3
        elif result == 'D':
            points += 1
        # result == 'L' ou outros caracteres = 0 pontos
    
    return points  # Valor entre 0 e 15
