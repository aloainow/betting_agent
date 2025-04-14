"""
Módulo para geração de justificativas para análises de apostas esportivas.
Este módulo centraliza a lógica de criação e formatação de justificativas
para diferentes mercados e oportunidades identificadas.
"""

import logging
logger = logging.getLogger("valueHunter.justifications")

def generate_team_win_justification(team_name, is_home, form_points, consistency, 
                                    real_prob, implicit_prob, expected_goals=None):
    """
    Gera justificativa para oportunidades de vitória do time.
    
    Args:
        team_name (str): Nome do time
        is_home (bool): Se é o time da casa
        form_points (int): Pontos de forma (0-15)
        consistency (float): Consistência do time (0-100)
        real_prob (float): Probabilidade real calculada
        implicit_prob (float): Probabilidade implícita das odds
        expected_goals (float, opcional): Total esperado de gols
        
    Returns:
        str: Justificativa formatada
    """
    team_type = "casa" if is_home else "visitante"
    
    justification = [
        f"## Justificativa para {team_name}:",
        f"- Time da {team_type} com {form_points}/15 pts na forma recente e {consistency:.1f}% de consistência."
    ]
    
    if expected_goals:
        justification.append(f"- Previsão de {expected_goals:.2f} gols na partida {'favorece time ofensivo' if is_home else ''}.")
    
    justification.append(f"- Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%.")
    
    return "\n".join(justification)

def generate_draw_justification(home_team, away_team, home_consistency, away_consistency,
                              real_prob, implicit_prob, home_form_points=None, away_form_points=None):
    """
    Gera justificativa para oportunidades de empate.
    
    Args:
        home_team (str): Nome do time da casa
        away_team (str): Nome do time visitante
        home_consistency (float): Consistência do time da casa (0-100)
        away_consistency (float): Consistência do time visitante (0-100)
        real_prob (float): Probabilidade real calculada
        implicit_prob (float): Probabilidade implícita das odds
        home_form_points (int, opcional): Pontos de forma do time da casa (0-15)
        away_form_points (int, opcional): Pontos de forma do time visitante (0-15)
        
    Returns:
        str: Justificativa formatada
    """
    avg_consistency = (home_consistency + away_consistency) / 2
    
    justification = [
        "## Justificativa para Empate:"
    ]
    
    if home_form_points is not None and away_form_points is not None:
        justification.append(f"- Equilíbrio entre as equipes ({home_team}: {home_form_points}/15 pts, {away_team}: {away_form_points}/15 pts).")
    else:
        justification.append(f"- Equilíbrio entre as equipes.")
    
    justification.append(f"- Consistência média de {avg_consistency:.1f}%.")
    justification.append(f"- Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%.")
    
    return "\n".join(justification)

def generate_over_under_justification(is_over, threshold, real_prob, implicit_prob, expected_goals):
    """
    Gera justificativa para oportunidades de Over/Under.
    
    Args:
        is_over (bool): Se é uma oportunidade de Over (True) ou Under (False)
        threshold (float): Linha de gols (2.5, 3.5, etc.)
        real_prob (float): Probabilidade real calculada
        implicit_prob (float): Probabilidade implícita das odds
        expected_goals (float): Total esperado de gols
        
    Returns:
        str: Justificativa formatada
    """
    market_type = "Over" if is_over else "Under"
    
    justification = [
        f"## Justificativa para {market_type} {threshold} Gols:"
    ]
    
    if is_over:
        if expected_goals > threshold:
            justification.append(f"- Previsão de {expected_goals:.2f} gols na partida, acima da linha de {threshold}.")
        else:
            justification.append(f"- Previsão de {expected_goals:.2f} gols na partida.")
    else:
        if expected_goals < threshold:
            justification.append(f"- Previsão de apenas {expected_goals:.2f} gols na partida, abaixo da linha de {threshold}.")
        else:
            justification.append(f"- Previsão de {expected_goals:.2f} gols na partida.")
    
    justification.append(f"- Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%.")
    
    return "\n".join(justification)

def generate_btts_justification(is_yes, real_prob, implicit_prob, expected_goals, 
                              home_scoring_prob=None, away_scoring_prob=None):
    """
    Gera justificativa para oportunidades de Ambos Marcam (BTTS).
    
    Args:
        is_yes (bool): Se é uma oportunidade de BTTS Sim (True) ou Não (False)
        real_prob (float): Probabilidade real calculada
        implicit_prob (float): Probabilidade implícita das odds
        expected_goals (float): Total esperado de gols
        home_scoring_prob (float, opcional): Probabilidade do time da casa marcar
        away_scoring_prob (float, opcional): Probabilidade do time visitante marcar
        
    Returns:
        str: Justificativa formatada
    """
    market_type = "Sim" if is_yes else "Não"
    
    justification = [
        f"## Justificativa para Ambos Marcam - {market_type}:"
    ]
    
    if is_yes:
        justification.append(f"- Ambas equipes têm potencial ofensivo. Previsão de {expected_goals:.2f} gols totais.")
        
        if home_scoring_prob and away_scoring_prob:
            justification.append(f"- Probabilidade de cada equipe marcar: Casa {home_scoring_prob:.1f}%, Visitante {away_scoring_prob:.1f}%.")
    else:
        justification.append(f"- Pelo menos uma equipe tem boa defesa e/ou ataque ineficiente.")
        
        if home_scoring_prob and away_scoring_prob:
            if home_scoring_prob < 50:
                justification.append(f"- Time da casa tem baixa probabilidade de marcar: {home_scoring_prob:.1f}%.")
            if away_scoring_prob < 50:
                justification.append(f"- Time visitante tem baixa probabilidade de marcar: {away_scoring_prob:.1f}%.")
    
    justification.append(f"- Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%.")
    
    return "\n".join(justification)

def generate_corners_justification(is_over, threshold, real_prob, implicit_prob, expected_corners):
    """
    Gera justificativa para oportunidades de escanteios.
    
    Args:
        is_over (bool): Se é uma oportunidade de Over (True) ou Under (False)
        threshold (float): Linha de escanteios (9.5, 10.5, etc.)
        real_prob (float): Probabilidade real calculada
        implicit_prob (float): Probabilidade implícita das odds
        expected_corners (float): Total esperado de escanteios
        
    Returns:
        str: Justificativa formatada
    """
    market_type = "Over" if is_over else "Under"
    
    justification = [
        f"## Justificativa para Escanteios {market_type} {threshold}:"
    ]
    
    if is_over:
        if expected_corners > threshold:
            justification.append(f"- Previsão de {expected_corners:.1f} escanteios na partida, acima da linha de {threshold}.")
        else:
            justification.append(f"- Previsão de {expected_corners:.1f} escanteios na partida.")
    else:
        if expected_corners < threshold:
            justification.append(f"- Previsão de apenas {expected_corners:.1f} escanteios na partida, abaixo da linha de {threshold}.")
        else:
            justification.append(f"- Previsão de {expected_corners:.1f} escanteios na partida.")
    
    justification.append(f"- Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%.")
    
    return "\n".join(justification)

def generate_cards_justification(is_over, threshold, real_prob, implicit_prob, expected_cards,
                               home_consistency=None, away_consistency=None):
    """
    Gera justificativa para oportunidades de cartões.
    
    Args:
        is_over (bool): Se é uma oportunidade de Over (True) ou Under (False)
        threshold (float): Linha de cartões (3.5, 4.5, etc.)
        real_prob (float): Probabilidade real calculada
        implicit_prob (float): Probabilidade implícita das odds
        expected_cards (float): Total esperado de cartões
        home_consistency (float, opcional): Consistência do time da casa
        away_consistency (float, opcional): Consistência do time visitante
        
    Returns:
        str: Justificativa formatada
    """
    market_type = "Over" if is_over else "Under"
    
    justification = [
        f"## Justificativa para Cartões {market_type} {threshold}:"
    ]
    
    if is_over:
        if expected_cards > threshold:
            justification.append(f"- Previsão de {expected_cards:.1f} cartões na partida, acima da linha de {threshold}.")
        else:
            justification.append(f"- Previsão de {expected_cards:.1f} cartões na partida.")
            
        # Para over, inconsistência aumenta a probabilidade de cartões
        if home_consistency and away_consistency:
            avg_consistency = (home_consistency + away_consistency) / 2
            if avg_consistency < 60:
                justification.append(f"- Baixa consistência média das equipes ({avg_consistency:.1f}%) favorece mais cartões.")
    else:
        if expected_cards < threshold:
            justification.append(f"- Previsão de apenas {expected_cards:.1f} cartões na partida, abaixo da linha de {threshold}.")
        else:
            justification.append(f"- Previsão de {expected_cards:.1f} cartões na partida.")
            
        # Para under, alta consistência favorece menos cartões
        if home_consistency and away_consistency:
            avg_consistency = (home_consistency + away_consistency) / 2
            if avg_consistency > 70:
                justification.append(f"- Alta consistência média das equipes ({avg_consistency:.1f}%) favorece menos cartões.")
    
    justification.append(f"- Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%.")
    
    return "\n".join(justification)

def generate_justifications_for_opportunities(opportunities, home_team, away_team, original_probabilities, implied_probabilities):
    """
    Gera justificativas detalhadas para as oportunidades identificadas.
    
    Modificação: Usar apenas a forma como mandante para o time da casa e visitante para o time de fora.
    """
    justifications = []
    analysis_data = original_probabilities.get("analysis_data", {})
    
    for opportunity in opportunities:
        # Determinar qual tipo de oportunidade é
        market_type = ""
        if home_team in opportunity:
            market_type = "home_win"
        elif away_team in opportunity:
            market_type = "away_win"
        elif "Empate" in opportunity:
            market_type = "draw"
        elif "Ambos Marcam - Sim" in opportunity:
            market_type = "btts_yes"
        elif "Ambos Marcam - Não" in opportunity:
            market_type = "btts_no"
        elif home_team + " ou Empate" in opportunity:
            market_type = "home_draw"
        elif away_team + " ou Empate" in opportunity:
            market_type = "away_draw"
        elif home_team + " ou " + away_team in opportunity:
            market_type = "home_away"
        
        # Gerar justificativa com base no tipo de mercado
        justification = ""
        
        if market_type == "home_win":
            # MODIFICAÇÃO: Usar forma como mandante em vez da forma geral
            home_form_points = analysis_data.get("home_form_points", 0) * 15
            
            # Aqui precisamos adicionar a lógica para obter a forma como mandante
            home_form_home = original_probabilities.get("home_team", {}).get("home_form", "?????")
            
            justification = f"""
### Justificativa para {home_team} (Vitória Casa)

- **Forma Recente como Mandante**: {home_form_home}
- **Consistência**: {analysis_data.get("home_consistency", 0):.1f}% 
- **Vantagem em casa**: O time tem um desempenho superior atuando como mandante
- **Comparação de pontuação**: Pontuação total de {analysis_data.get("home_total_score", 0):.2f} vs {analysis_data.get("away_total_score", 0):.2f} do adversário
            """
        
        elif market_type == "away_win":
            # MODIFICAÇÃO: Usar forma como visitante em vez da forma geral
            away_form_points = analysis_data.get("away_form_points", 0) * 15
            
            # Aqui precisamos adicionar a lógica para obter a forma como visitante
            away_form_away = original_probabilities.get("away_team", {}).get("away_form", "?????")
            
            justification = f"""
### Justificativa para {away_team} (Vitória Fora)

- **Forma Recente como Visitante**: {away_form_away}
- **Consistência**: {analysis_data.get("away_consistency", 0):.1f}%
- **Desempenho fora de casa**: O time tem demonstrado solidez atuando como visitante
- **Comparação de pontuação**: Pontuação total de {analysis_data.get("away_total_score", 0):.2f} vs {analysis_data.get("home_total_score", 0):.2f} do adversário
            """
        
        elif market_type == "draw":
            # Para empate, podemos mostrar a forma de ambos os times (casa/fora)
            home_form_home = original_probabilities.get("home_team", {}).get("home_form", "?????")
            away_form_away = original_probabilities.get("away_team", {}).get("away_form", "?????")
            
            justification = f"""
### Justificativa para Empate

- **Forma do {home_team} como Mandante**: {home_form_home}
- **Forma do {away_team} como Visitante**: {away_form_away}
- **Consistência das equipes**: Casa {analysis_data.get("home_consistency", 0):.1f}% vs Fora {analysis_data.get("away_consistency", 0):.1f}%
- **Equilíbrio de forças**: Pontuações totais próximas - Casa {analysis_data.get("home_total_score", 0):.2f} vs Fora {analysis_data.get("away_total_score", 0):.2f}
            """
        
        # Adicionar lógica similar para os outros mercados
        elif market_type == "home_draw":
            home_form_home = original_probabilities.get("home_team", {}).get("home_form", "?????")
            
            justification = f"""
### Justificativa para {home_team} ou Empate (Dupla Chance)

- **Forma do {home_team} como Mandante**: {home_form_home}
- **Consistência do {home_team}**: {analysis_data.get("home_consistency", 0):.1f}%
- **Vantagem em casa**: {home_team} tem demonstrado força atuando como mandante
- **Comparação**: Pontuação total de {analysis_data.get("home_total_score", 0):.2f} para o {home_team}
            """
        
        elif market_type == "away_draw":
            away_form_away = original_probabilities.get("away_team", {}).get("away_form", "?????")
            
            justification = f"""
### Justificativa para {away_team} ou Empate (Dupla Chance)

- **Forma do {away_team} como Visitante**: {away_form_away}
- **Consistência do {away_team}**: {analysis_data.get("away_consistency", 0):.1f}%
- **Desempenho fora**: {away_team} tem mostrado capacidade como visitante
- **Comparação**: Pontuação total de {analysis_data.get("away_total_score", 0):.2f} para o {away_team}
            """
        
        elif market_type in ["btts_yes", "btts_no"]:
            home_form_home = original_probabilities.get("home_team", {}).get("home_form", "?????")
            away_form_away = original_probabilities.get("away_team", {}).get("away_form", "?????")
            
            btts_type = "marcarem" if market_type == "btts_yes" else "não marcarem"
            
            justification = f"""
### Justificativa para Ambos Marcam - {"Sim" if market_type == "btts_yes" else "Não"}

- **Forma do {home_team} como Mandante**: {home_form_home}
- **Forma do {away_team} como Visitante**: {away_form_away}
- **Potencial ofensivo/defensivo**: As estatísticas indicam probabilidade de ambos os times {btts_type}
- **Expected Goals**: Projeção de gols favorece este resultado
            """
            
        # Adicionar a justificativa à lista se não estiver vazia
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
