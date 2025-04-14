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

         Oportunidades Identificadas:
        - **Empoli FC**: Real 31.3% vs Implícita 10.0% (Valor de 21.3%)
          *Justificativa: Time visitante com 5/15 pts na forma recente e 50.0%
        de consistência. Previsão de 1.66 gols na partida. Odds de 10.0%
        subestimam probabilidade real de 31.3%.*

def generate_condensed_justification(team_name, home_team, away_team, real_prob, implied_prob, analysis_data, original_probabilities, expected_goals=None):
    """
    Gera uma justificativa condensada para ser incluída diretamente na lista de oportunidades.
    
    Args:
        team_name (str): Nome do time ou mercado (ex: "Time A", "Empate", "Ambos Marcam - Sim")
        home_team (str): Nome do time da casa
        away_team (str): Nome do time visitante
        real_prob (float): Probabilidade real calculada
        implied_prob (float): Probabilidade implícita na odd
        analysis_data (dict): Dados de análise com consistência, forma, etc.
        original_probabilities (dict): Dados de probabilidades completos
        expected_goals (float, optional): Total esperado de gols, se relevante
        
    Returns:
        str: Justificativa condensada formatada
    """
    # Determinar se estamos lidando com o time da casa, visitante, ou outro mercado
    is_home = team_name == home_team
    is_away = team_name == away_team
    
    # Obter dados de consistência e forma apropriados
    if is_home:
        consistency = analysis_data.get("home_consistency", 0)
        form_points = analysis_data.get("home_form_points", 0) * 15
        # Especificar que é forma como mandante
        form_type = "como mandante"
    elif is_away:
        consistency = analysis_data.get("away_consistency", 0)
        form_points = analysis_data.get("away_form_points", 0) * 15
        # Especificar que é forma como visitante
        form_type = "como visitante"
    else:
        # Para mercados como empate, ambos marcam, etc.
        home_consistency = analysis_data.get("home_consistency", 0)
        away_consistency = analysis_data.get("away_consistency", 0)
        consistency = (home_consistency + away_consistency) / 2
        form_points = None
        form_type = None
    
    # Iniciar a justificativa
    justification = ""
    
    # Adicionar informação de forma para time da casa ou visitante
    if is_home or is_away:
        team_type = "da casa" if is_home else "visitante"
        justification += f"Time {team_type} com {form_points:.0f}/15 pts na forma {form_type} e {consistency:.1f}% de consistência. "
    elif team_name == "Empate":
        home_form = analysis_data.get("home_form_points", 0) * 15
        away_form = analysis_data.get("away_form_points", 0) * 15
        justification += f"Times equilibrados: Casa com {home_form:.0f}/15 pts como mandante, Fora com {away_form:.0f}/15 pts como visitante. "
    elif "Ambos Marcam" in team_name:
        home_offensive = original_probabilities.get("home_expected_goals", 1.0)
        away_offensive = original_probabilities.get("away_expected_goals", 0.8)
        justification += f"Potencial ofensivo: Casa {home_offensive:.2f} xG, Fora {away_offensive:.2f} xG. "
    
    # Adicionar informação de gols esperados se disponível
    if expected_goals:
        justification += f"Previsão de {expected_goals:.2f} gols na partida. "
    
    # Adicionar conclusão sobre a diferença de probabilidades
    edge = real_prob - implied_prob
    justification += f"Odds de {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
    
    return justification

# Adicionar ao código principal para usar essa função
def format_opportunity_with_justification(opportunity, home_team, away_team, original_probabilities, implied_probabilities):
    """
    Formata uma oportunidade com sua justificativa condensada.
    """
    # Extrair informações da oportunidade
    # Exemplo de formato: "- **Empoli FC**: Real 31.3% vs Implícita 10.0% (Valor de 21.3%)"
    
    # Identificar o time ou mercado
    if home_team in opportunity:
        team_name = home_team
    elif away_team in opportunity:
        team_name = away_team
    elif "Empate" in opportunity:
        team_name = "Empate"
    elif "Ambos Marcam - Sim" in opportunity:
        team_name = "Ambos Marcam - Sim"
    elif "Ambos Marcam - Não" in opportunity:
        team_name = "Ambos Marcam - Não"
    elif home_team + " ou Empate" in opportunity:
        team_name = f"{home_team} ou Empate"
    elif away_team + " ou Empate" in opportunity:
        team_name = f"{away_team} ou Empate"
    else:
        team_name = "Mercado"
    
    # Extrair probabilidades
    import re
    real_prob_match = re.search(r"Real (\d+\.\d+)%", opportunity)
    implied_prob_match = re.search(r"Implícita (\d+\.\d+)%", opportunity)
    
    if real_prob_match and implied_prob_match:
        real_prob = float(real_prob_match.group(1))
        implied_prob = float(implied_prob_match.group(1))
        
        # Obter dados de análise
        analysis_data = original_probabilities.get("analysis_data", {})
        
        # Obter expected goals se disponível
        expected_goals = None
        if "over_under" in original_probabilities:
            expected_goals = original_probabilities["over_under"].get("expected_goals")
        
        # Gerar justificativa condensada
        justification = generate_condensed_justification(
            team_name, 
            home_team, 
            away_team, 
            real_prob, 
            implied_prob, 
            analysis_data, 
            original_probabilities, 
            expected_goals
        )
        
        # Adicionar justificativa à oportunidade
        formatted_opportunity = f"{opportunity} *Justificativa: {justification}*"
        return formatted_opportunity
    
    return opportunity  # Retornar original se não conseguir extrair probabilidades
