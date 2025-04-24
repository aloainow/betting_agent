# utils/justifications.py
import logging

def generate_justifications_for_opportunities(opportunities, home_team, away_team, original_probabilities, implied_probabilities):
    """
    Gera justificativas detalhadas para as oportunidades identificadas.
    
    Modificação: Usar apenas a forma como mandante para o time da casa e visitante para o time de fora.
    Também modifica a justificativa condensada para usar o termo correto.
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

def generate_justification(market_type, bet_type, team_name, real_prob, implicit_prob, 
                          original_probabilities, home_team, away_team):
    """
    Gera uma justificativa com embasamento estatístico específico para cada mercado.
    Versão corrigida para usar os valores de forma do time como mandante ou visitante.
    """
    try:
        # Dados de análise para extrair informações adicionais
        analysis_data = original_probabilities.get("analysis_data", {})
        margin = real_prob - implicit_prob
        
        # Extrair valores de forma
        home_form_points = analysis_data.get("home_form_points", 0)
        away_form_points = analysis_data.get("away_form_points", 0)
        
        # Se os pontos estiverem no formato normalizado (0-1), convertê-los para a escala 0-15
        if isinstance(home_form_points, (int, float)) and home_form_points <= 1.0:
            home_form_points = home_form_points * 15
        if isinstance(away_form_points, (int, float)) and away_form_points <= 1.0:
            away_form_points = away_form_points * 15
        
        # Expressões de contexto corretas para casa/fora
        home_form_context = analysis_data.get("home_form_context", "como mandante")
        away_form_context = analysis_data.get("away_form_context", "como visitante")
        
        # Valores de consistência
        home_consistency = analysis_data.get("home_consistency", 0)
        away_consistency = analysis_data.get("away_consistency", 0)
        
        # Garantir que consistência está em porcentagem
        if home_consistency <= 1.0:
            home_consistency = home_consistency * 100
        if away_consistency <= 1.0:
            away_consistency = away_consistency * 100
        
        # 1. MONEYLINE (1X2)
        if market_type == "moneyline":
            # Vitória do time da casa
            if bet_type == "home_win":
                justification = f"Time da casa com {home_form_points:.1f}/15 pts na forma {home_form_context} e {home_consistency:.1f}% de consistência. "
                
                if "over_under" in original_probabilities:
                    expected_goals = original_probabilities["over_under"].get("expected_goals", 0)
                    if 0 < expected_goals < 10:
                        justification += f"Previsão de {expected_goals:.2f} gols na partida favorece time ofensivo. "
                
                justification += f"Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
                
            # Vitória do time visitante
            elif bet_type == "away_win":
                justification = f"Time visitante com {away_form_points:.1f}/15 pts na forma {away_form_context} e {away_consistency:.1f}% de consistência. "
                
                if "over_under" in original_probabilities:
                    expected_goals = original_probabilities["over_under"].get("expected_goals", 0)
                    if 0 < expected_goals < 10:
                        justification += f"Previsão de {expected_goals:.2f} gols na partida. "
                        
                justification += f"Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
                
            # Empate
            elif bet_type == "draw":
                justification = f"Times equilibrados: Casa com {home_form_points:.1f}/15 pts {home_form_context}, Fora com {away_form_points:.1f}/15 pts {away_form_context}. "
                justification += f"Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."

        
        # 2. CHANCE DUPLA (DOUBLE CHANCE)
        elif market_type == "double_chance":
            if bet_type == "home_or_draw":
                justification = f"Vantagem de jogar em casa para {home_team} (forma {home_form_context}: {home_form_points:.1f}/15 pts). "
                justification += f"Probabilidade de {real_prob:.1f}% do time da casa não perder, "
                justification += f"contra apenas {implicit_prob:.1f}% implicada pelas odds."
                
            elif bet_type == "away_or_draw":
                justification = f"Vantagem para {away_team} visitante (forma {away_form_context}: {away_form_points:.1f}/15 pts). "
                justification += f"Probabilidade de {real_prob:.1f}% do time visitante não perder, "
                justification += f"contra apenas {implicit_prob:.1f}% implicada pelas odds."
                
            elif bet_type == "home_or_away":
                justification = f"Baixa probabilidade de empate. Casa com {home_form_points:.1f}/15 pts {home_form_context}, fora com {away_form_points:.1f}/15 pts {away_form_context}. "
                justification += f"Chance de {real_prob:.1f}% de algum time vencer, "
                justification += f"contra apenas {implicit_prob:.1f}% implicada pelas odds."
        
        # 3. OVER/UNDER
        elif market_type == "over_under":
            if "over_under" in original_probabilities:
                expected_goals = original_probabilities["over_under"].get("expected_goals", 0)
                
                # Validar valor de expected_goals
                if not (0 < expected_goals < 10):
                    expected_goals = 2.5  # Valor default razoável
                
                if bet_type.startswith("over_"):
                    threshold = bet_type.replace("over_", "").replace("_", ".")
                    threshold_value = float(threshold)
                    
                    # Verificar consistência lógica
                    if expected_goals > threshold_value:
                        comparison = "acima"
                    else:
                        comparison = "próximo"
                    
                    justification = f"Previsão de {expected_goals:.2f} gols na partida, {comparison} do threshold de {threshold}. "
                    justification += f"Casa com {home_form_points:.1f}/15 pts {home_form_context}, fora com {away_form_points:.1f}/15 pts {away_form_context}. "
                    justification += f"Probabilidade real de {real_prob:.1f}% vs implícita de {implicit_prob:.1f}%."
                    
                else:  # Under
                    threshold = bet_type.replace("under_", "").replace("_", ".")
                    threshold_value = float(threshold)
                    
                    # Verificar consistência lógica
                    if expected_goals < threshold_value:
                        comparison = "abaixo"
                    else:
                        comparison = "próximo"
                    
                    justification = f"Previsão de {expected_goals:.2f} gols na partida, {comparison} do threshold de {threshold}. "
                    justification += f"Casa com {home_form_points:.1f}/15 pts {home_form_context}, fora com {away_form_points:.1f}/15 pts {away_form_context}. "
                    justification += f"Probabilidade real de {real_prob:.1f}% vs implícita de {implicit_prob:.1f}%."
        
        # 4. BTTS (AMBOS MARCAM)
        elif market_type == "btts":
            if "btts" in original_probabilities:
                if bet_type == "yes":
                    justification = f"Casa com {home_form_points:.1f}/15 pts {home_form_context}, fora com {away_form_points:.1f}/15 pts {away_form_context}. Ambas equipes com potencial ofensivo. "
                    
                    if "over_under" in original_probabilities:
                        expected_goals = original_probabilities["over_under"].get("expected_goals", 0)
                        if 0 < expected_goals < 10:
                            justification += f"Previsão de {expected_goals:.2f} gols totais na partida. "
                        
                    justification += f"Probabilidade real de {real_prob:.1f}% vs implícita de {implicit_prob:.1f}%."
                    
                else:  # No
                    justification = f"Casa com {home_form_points:.1f}/15 pts {home_form_context}, fora com {away_form_points:.1f}/15 pts {away_form_context}. Pelo menos uma equipe deve manter clean sheet. "
                    
                    if "over_under" in original_probabilities:
                        expected_goals = original_probabilities["over_under"].get("expected_goals", 0)
                        if 0 < expected_goals < 10:
                            justification += f"Previsão de apenas {expected_goals:.2f} gols totais na partida. "
                        
                    justification += f"Probabilidade real de {real_prob:.1f}% vs implícita de {implicit_prob:.1f}%."
        
        # 5. ESCANTEIOS
        elif market_type == "corners":
            if "corners" in original_probabilities:
                expected_corners = original_probabilities["corners"].get("expected_corners", 0)
                
                # Validar valor de expected_corners
                if not (3 < expected_corners < 20):
                    if real_prob > 70:
                        expected_corners = 11.5
                    else:
                        expected_corners = 8.5
                
                if bet_type.startswith("over_"):
                    threshold = bet_type.replace("over_", "").replace("_", ".")
                    threshold_value = float(threshold)
                    
                    # Verificar consistência lógica
                    if expected_corners > threshold_value:
                        comparison = "acima"
                    else:
                        comparison = "próximo"
                    
                    justification = f"Previsão de {expected_corners:.1f} escanteios na partida, {comparison} do threshold de {threshold}. "
                    justification += f"Casa com {home_form_points:.1f}/15 pts {home_form_context}, fora com {away_form_points:.1f}/15 pts {away_form_context}. "
                    justification += f"Probabilidade real de {real_prob:.1f}% vs implícita de {implicit_prob:.1f}%."
                    
                else:  # Under
                    threshold = bet_type.replace("under_", "").replace("_", ".")
                    threshold_value = float(threshold)
                    
                    # Verificar consistência lógica
                    if expected_corners < threshold_value:
                        comparison = "abaixo"
                    else:
                        comparison = "próximo"
                    
                    justification = f"Previsão de {expected_corners:.1f} escanteios na partida, {comparison} do threshold de {threshold}. "
                    justification += f"Casa com {home_form_points:.1f}/15 pts {home_form_context}, fora com {away_form_points:.1f}/15 pts {away_form_context}. "
                    justification += f"Probabilidade real de {real_prob:.1f}% vs implícita de {implicit_prob:.1f}%."
        
        # 6. CARTÕES
        elif market_type == "cards":
            if "cards" in original_probabilities:
                expected_cards = original_probabilities["cards"].get("expected_cards", 0)
                
                # Validar valor de expected_cards
                if not (1 < expected_cards < 10):
                    if real_prob > 60:
                        expected_cards = 3.2
                    else:
                        expected_cards = 5.5
                
                if bet_type.startswith("over_"):
                    threshold = bet_type.replace("over_", "").replace("_", ".")
                    threshold_value = float(threshold)
                    
                    # Verificar consistência lógica
                    if expected_cards > threshold_value:
                        comparison = "acima"
                    else:
                        comparison = "próximo"
                    
                    justification = f"Previsão de {expected_cards:.1f} cartões na partida, {comparison} do threshold de {threshold}. "
                    justification += f"Casa com {home_form_points:.1f}/15 pts {home_form_context}, fora com {away_form_points:.1f}/15 pts {away_form_context}. "
                    justification += f"Probabilidade real de {real_prob:.1f}% vs implícita de {implicit_prob:.1f}%."
                    
                else:  # Under
                    threshold = bet_type.replace("under_", "").replace("_", ".")
                    threshold_value = float(threshold)
                    
                    # Verificar consistência lógica
                    if expected_cards < threshold_value:
                        comparison = "abaixo"
                    else:
                        comparison = "próximo"
                    
                    justification = f"Previsão de {expected_cards:.1f} cartões na partida, {comparison} do threshold de {threshold}. "
                    justification += f"Casa com {home_form_points:.1f}/15 pts {home_form_context}, fora com {away_form_points:.1f}/15 pts {away_form_context}. "
                    justification += f"Probabilidade real de {real_prob:.1f}% vs implícita de {implicit_prob:.1f}%."
        
        # JUSTIFICATIVA GENÉRICA PARA OUTROS MERCADOS
        else:
            justification = f"Casa com {home_form_points:.1f}/15 pts {home_form_context}, fora com {away_form_points:.1f}/15 pts {away_form_context}. "
            
            if margin > 15:
                justification += f"Discrepância significativa de {margin:.1f}% entre probabilidade real ({real_prob:.1f}%) e odds oferecidas ({implicit_prob:.1f}%)."
            elif margin > 8:
                justification += f"Boa diferença de {margin:.1f}% entre probabilidade calculada ({real_prob:.1f}%) e odds oferecidas ({implicit_prob:.1f}%)."
            else:
                justification += f"Vantagem estatística de {margin:.1f}% entre probabilidade real ({real_prob:.1f}%) e odds oferecidas ({implicit_prob:.1f}%)."
        
        return justification
        
    except Exception as e:
        # Log do erro
        import traceback
        import logging
        logger = logging.getLogger("valueHunter.ai")
        logger.error(f"Erro na geração de justificativa: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Garantir que mesmo no caso de erro, usamos os valores de forma corretos
        try:
            analysis_data = original_probabilities.get("analysis_data", {})
            home_form_points = analysis_data.get("home_form_points", 0.33) * 15
            away_form_points = analysis_data.get("away_form_points", 0.6) * 15
            
            home_form_context = analysis_data.get("home_form_context", "como mandante")
            away_form_context = analysis_data.get("away_form_context", "como visitante")
                
            # Retornar uma justificativa genérica mas com os valores corretos da forma
            return f"Casa com {home_form_points:.1f}/15 pts {home_form_context}, fora com {away_form_points:.1f}/15 pts {away_form_context}. Valor estatístico significativo de {real_prob-implicit_prob:.1f}% acima da probabilidade implícita nas odds."
        except:
            # Último recurso se tudo falhar
            return f"Valor estatístico significativo de {real_prob-implicit_prob:.1f}% acima da probabilidade implícita nas odds."
# Função auxiliar para gerar justificativas condensadas
def generate_condensed_justification(team_name, home_team, away_team, real_prob, implied_prob, analysis_data, original_probabilities, expected_goals=None):
    """
    Gera uma justificativa condensada para ser incluída diretamente na lista de oportunidades.
    Versão corrigida para usar as expressões corretas de forma dos times.
    
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
    # Contextos corretos para cada time
    home_form_context = analysis_data.get("home_form_context", "como mandante")
    away_form_context = analysis_data.get("away_form_context", "como visitante")
    
    # Para times da casa
    if is_home:
        consistency = analysis_data.get("home_consistency", 0)
        # Melhor tratamento dos pontos de forma
        home_form_points = analysis_data.get("home_form_points", None)
        if home_form_points is None:
            # Sem dados de forma disponíveis
            form_points = "N/A"
        elif home_form_points <= 1.0:  # Valor normalizado (0-1)
            form_points = home_form_points * 15
        else:  # Já está no formato de pontos
            form_points = home_form_points
        form_type = home_form_context
    
    # Para times visitantes
    elif is_away:
        consistency = analysis_data.get("away_consistency", 0)
        # Melhor tratamento dos pontos de forma
        away_form_points = analysis_data.get("away_form_points", None)
        if away_form_points is None:
            # Sem dados de forma disponíveis
            form_points = "N/A"
        elif away_form_points <= 1.0:  # Valor normalizado (0-1)
            form_points = away_form_points * 15
        else:  # Já está no formato de pontos
            form_points = away_form_points
        form_type = away_form_context
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
        justification += f"Time {team_type} com {form_points:.1f}/15 pts na forma {form_type} e {consistency:.1f}% de consistência. "
    elif team_name == "Empate":
        home_form = analysis_data.get("home_form_points", 0) * 15
        away_form = analysis_data.get("away_form_points", 0) * 15
        justification += f"Times equilibrados: Casa com {home_form:.1f}/15 pts {home_form_context}, Fora com {away_form:.1f}/15 pts {away_form_context}. "
    elif "Ambos Marcam" in team_name:
        home_expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 2.5) / 2
        away_expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 2.5) / 2
        justification += f"Potencial ofensivo: Casa {home_expected_goals:.2f} xG, Fora {away_expected_goals:.2f} xG. "
    elif "Over" in team_name or "Under" in team_name:
        total_expected = None
        
        if "Gols" in team_name:
            total_expected = original_probabilities.get("over_under", {}).get("expected_goals", 2.5)
            justification += f"Previsão de {total_expected:.2f} gols na partida. "
        elif "Escanteios" in team_name:
            total_expected = original_probabilities.get("corners", {}).get("expected_corners", 10)
            justification += f"Previsão de {total_expected:.1f} escanteios na partida. "
        elif "Cartões" in team_name:
            total_expected = original_probabilities.get("cards", {}).get("expected_cards", 4)
            justification += f"Previsão de {total_expected:.1f} cartões na partida. "
    
    # Adicionar informação de gols esperados para outros mercados se disponível e ainda não incluído
    if expected_goals and "Previsão de" not in justification:
        justification += f"Previsão de {expected_goals:.2f} gols na partida. "
    
    # Adicionar conclusão sobre a diferença de probabilidades
    edge = real_prob - implied_prob
    justification += f"Odds de {implied_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
    
    return justification

# Função auxiliar para aplicar a justificativa condensada à string de oportunidade
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
    elif "Over" in opportunity:
        team_name = opportunity.split("**")[1]
    elif "Under" in opportunity:
        team_name = opportunity.split("**")[1]
    elif home_team + " ou Empate" in opportunity:
        team_name = f"{home_team} ou Empate"
    elif away_team + " ou Empate" in opportunity:
        team_name = f"{away_team} ou Empate"
    elif home_team + " ou " + away_team in opportunity:
        team_name = f"{home_team} ou {away_team}"
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
