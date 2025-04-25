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
    Versão corrigida para usar APENAS os dados de forma específica (mandante/visitante).
    """
    try:
        import logging
        import json
        logger = logging.getLogger("valueHunter.ai")
        
        # DEBUG: Imprimir estrutura de original_probabilities para análise
        if "analysis_data" in original_probabilities:
            logger.info("Estrutura de analysis_data: " + json.dumps(original_probabilities["analysis_data"], indent=2))
        
        # IMPORTANTE: Vamos usar APENAS os dados específicos (mandante/visitante)
        # e não os dados ponderados (que misturam específico e geral)
        
        # Primeiro verificamos se temos os dados detalhados de forma
        form_details = {}
        if "analysis_data" in original_probabilities and "form_details" in original_probabilities["analysis_data"]:
            form_details = original_probabilities["analysis_data"]["form_details"]
            logger.info("Usando dados detalhados de forma específica (mandante/visitante)")
            
            # Extrair apenas os dados específicos (mandante/visitante)
            home_specific = form_details.get("home_specific", {})
            away_specific = form_details.get("away_specific", {})
            
            # Usar apenas os pontos específicos, não os ponderados
            home_form_points = home_specific.get("points", 0)
            away_form_points = away_specific.get("points", 0)
            
            logger.info(f"Pontos específicos - Home: {home_form_points}/15, Away: {away_form_points}/15")
            
        else:
            # Se não temos dados detalhados, fazemos log e usamos o que estiver disponível
            logger.warning("⚠️ Dados detalhados de forma não disponíveis na estrutura!")
            logger.info("Chaves em analysis_data: " + str(original_probabilities.get("analysis_data", {}).keys()))
            
            # Tentar extrair dados brutos da análise
            analysis_data = original_probabilities.get("analysis_data", {})
            
            # Usar valores resumidos com adaptação para escala 0-15
            home_form_points_raw = analysis_data.get("home_form_points", 0)
            if isinstance(home_form_points_raw, float) and home_form_points_raw <= 1.0:
                home_form_points = home_form_points_raw * 15
            else:
                home_form_points = home_form_points_raw
            
            away_form_points_raw = analysis_data.get("away_form_points", 0)
            if isinstance(away_form_points_raw, float) and away_form_points_raw <= 1.0:
                away_form_points = away_form_points_raw * 15
            else:
                away_form_points = away_form_points_raw
            
            logger.info(f"Usando valores resumidos - Home: {home_form_points}/15, Away: {away_form_points}/15")
        
        # Extrair consistências e contextos
        analysis_data = original_probabilities.get("analysis_data", {})
        home_consistency = analysis_data.get("home_consistency", 0)
        away_consistency = analysis_data.get("away_consistency", 0)
        home_form_context = analysis_data.get("home_form_context", "como mandante")
        away_form_context = analysis_data.get("away_form_context", "como visitante")
        
        # Garantir que consistência está em porcentagem (0-100)
        if home_consistency <= 1.0:
            home_consistency = home_consistency * 100
        if away_consistency <= 1.0:
            away_consistency = away_consistency * 100
            
        # Margem entre probabilidades
        margin = real_prob - implicit_prob
        
        # 1. MONEYLINE (1X2)
        if market_type == "moneyline":
            # Vitória do time da casa
            if bet_type == "home_win":
                justification = f"Time da casa com {home_form_points:.0f}/15 pts na forma {home_form_context} e {home_consistency:.1f}% de consistência. "
                
                if "over_under" in original_probabilities:
                    expected_goals = original_probabilities["over_under"].get("expected_goals", 0)
                    if 0 < expected_goals < 10:
                        justification += f"Previsão de {expected_goals:.2f} gols na partida favorece time ofensivo. "
                
                justification += f"Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
                
            # Vitória do time visitante
            elif bet_type == "away_win":
                justification = f"Time visitante com {away_form_points:.0f}/15 pts na forma {away_form_context} e {away_consistency:.1f}% de consistência. "
                
                if "over_under" in original_probabilities:
                    expected_goals = original_probabilities["over_under"].get("expected_goals", 0)
                    if 0 < expected_goals < 10:
                        justification += f"Previsão de {expected_goals:.2f} gols na partida. "
                        
                justification += f"Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."
                
            # Empate
            elif bet_type == "draw":
                justification = f"Times equilibrados: Casa com {home_form_points:.0f}/15 pts {home_form_context}, Fora com {away_form_points:.0f}/15 pts {away_form_context}. "
                justification += f"Odds de {implicit_prob:.1f}% subestimam probabilidade real de {real_prob:.1f}%."

        
        # 2. CHANCE DUPLA (DOUBLE CHANCE)
        elif market_type == "double_chance":
            if bet_type == "home_or_draw":
                justification = f"Vantagem de jogar em casa para {home_team} (forma {home_form_context}: {home_form_points:.0f}/15 pts). "
                justification += f"Probabilidade de {real_prob:.1f}% do time da casa não perder, "
                justification += f"contra apenas {implicit_prob:.1f}% implicada pelas odds."
                
            elif bet_type == "away_or_draw":
                justification = f"Vantagem para {away_team} visitante (forma {away_form_context}: {away_form_points:.0f}/15 pts). "
                justification += f"Probabilidade de {real_prob:.1f}% do time visitante não perder, "
                justification += f"contra apenas {implicit_prob:.1f}% implicada pelas odds."
                
            elif bet_type == "home_or_away":
                justification = f"Baixa probabilidade de empate. Casa com {home_form_points:.0f}/15 pts {home_form_context}, fora com {away_form_points:.0f}/15 pts {away_form_context}. "
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
                    justification += f"Casa com {home_form_points:.0f}/15 pts {home_form_context}, fora com {away_form_points:.0f}/15 pts {away_form_context}. "
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
                    justification += f"Casa com {home_form_points:.0f}/15 pts {home_form_context}, fora com {away_form_points:.0f}/15 pts {away_form_context}. "
                    justification += f"Probabilidade real de {real_prob:.1f}% vs implícita de {implicit_prob:.1f}%."
        
        # 4. BTTS (AMBOS MARCAM)
        elif market_type == "btts":
            if "btts" in original_probabilities:
                if bet_type == "yes":
                    justification = f"Casa com {home_form_points:.0f}/15 pts {home_form_context}, fora com {away_form_points:.0f}/15 pts {away_form_context}. Ambas equipes com potencial ofensivo. "
                    
                    if "over_under" in original_probabilities:
                        expected_goals = original_probabilities["over_under"].get("expected_goals", 0)
                        if 0 < expected_goals < 10:
                            justification += f"Previsão de {expected_goals:.2f} gols totais na partida. "
                        
                    justification += f"Probabilidade real de {real_prob:.1f}% vs implícita de {implicit_prob:.1f}%."
                    
                else:  # No
                    justification = f"Casa com {home_form_points:.0f}/15 pts {home_form_context}, fora com {away_form_points:.0f}/15 pts {away_form_context}. Pelo menos uma equipe deve manter clean sheet. "
                    
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
                    justification += f"Casa com {home_form_points:.0f}/15 pts {home_form_context}, fora com {away_form_points:.0f}/15 pts {away_form_context}. "
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
                    justification += f"Casa com {home_form_points:.0f}/15 pts {home_form_context}, fora com {away_form_points:.0f}/15 pts {away_form_context}. "
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
                    justification += f"Casa com {home_form_points:.0f}/15 pts {home_form_context}, fora com {away_form_points:.0f}/15 pts {away_form_context}. "
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
                    justification += f"Casa com {home_form_points:.0f}/15 pts {home_form_context}, fora com {away_form_points:.0f}/15 pts {away_form_context}. "
                    justification += f"Probabilidade real de {real_prob:.1f}% vs implícita de {implicit_prob:.1f}%."
        
        # JUSTIFICATIVA GENÉRICA PARA OUTROS MERCADOS
        else:
            justification = f"Casa com {home_form_points:.0f}/15 pts {home_form_context}, fora com {away_form_points:.0f}/15 pts {away_form_context}. "
            
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
            return f"Casa com {home_form_points:.0f}/15 pts {home_form_context}, fora com {away_form_points:.0f}/15 pts {away_form_context}. Valor estatístico significativo de {real_prob-implicit_prob:.1f}% acima da probabilidade implícita nas odds."
        except:
            # Último recurso se tudo falhar
            return f"Valor estatístico significativo de {real_prob-implicit_prob:.1f}% acima da probabilidade implícita nas odds."

def generate_condensed_justification(team_name, home_team, away_team, real_prob, implied_prob, analysis_data, original_probabilities, expected_goals=None):
    """
    Gera uma justificativa condensada específica para cada tipo de mercado,
    identificando dinamicamente a linha (threshold) escolhida pelo usuário.
    """
    import logging
    import re
    logger = logging.getLogger("valueHunter.ai")
    
    # Extrair dados básicos
    home_form_points = analysis_data.get("home_form_points", 0) * 15
    away_form_points = analysis_data.get("away_form_points", 0) * 15
    home_consistency = analysis_data.get("home_consistency", 0)
    away_consistency = analysis_data.get("away_consistency", 0)
    
    # EXTRAIR DINAMICAMENTE A LINHA/THRESHOLD DO NOME DA OPORTUNIDADE
    threshold = None
    threshold_direction = None
    
    # Padrão para identificar a linha (threshold) e direção (over/under)
    threshold_pattern = r'([Oo]ver|[Uu]nder)\s+(\d+\.?\d*)'
    threshold_match = re.search(threshold_pattern, team_name)
    
    if threshold_match:
        threshold = float(threshold_match.group(2))
        threshold_direction = threshold_match.group(1).lower()  # "over" ou "under"
    
    # Determinar o tipo de mercado
    if team_name == home_team or team_name == away_team or team_name == "Empate":
        market_type = "moneyline"
    elif "ou" in team_name:
        market_type = "double_chance"
    elif "Ambos Marcam" in team_name:
        market_type = "btts"
    elif ("Gols" in team_name) and (threshold is not None):
        market_type = "goals"
    elif ("Escanteios" in team_name) and (threshold is not None):
        market_type = "corners"
    elif ("Cartões" in team_name) and (threshold is not None):
        market_type = "cards"
    else:
        market_type = "unknown"
    
    # Iniciar justificativa
    justification = ""
    
    # 1. MERCADOS DE RESULTADO - MONEYLINE E DUPLA CHANCE
    if market_type in ["moneyline", "double_chance"]:
        # Time da casa
        if team_name == home_team or home_team in team_name:
            # Dados de forma e consistência
            justification += f"Time da casa com {home_form_points:.0f}/15 pts como mandante e {home_consistency:.1f}% de consistência. "
            
            # Adicionar dados de desempenho em casa
            home_stats = original_probabilities.get("home_team", {})
            home_wins = home_stats.get("home_wins", 0)
            home_draws = home_stats.get("home_draws", 0)
            home_losses = home_stats.get("home_losses", 0)
            
            if home_wins + home_draws + home_losses > 0:
                justification += f"Desempenho como mandante: {home_wins}V {home_draws}E {home_losses}D. "
            
            if "h2h" in original_probabilities:
                h2h = original_probabilities.get("h2h", {})
                home_h2h_wins = h2h.get("home_wins", 0)
                total_h2h = h2h.get("total_matches", 0)
                if total_h2h > 0:
                    justification += f"No histórico H2H, venceu {home_h2h_wins} de {total_h2h} confrontos. "
        
        # Time visitante
        elif team_name == away_team or away_team in team_name:
            # Dados de forma e consistência
            justification += f"Time visitante com {away_form_points:.0f}/15 pts como visitante e {away_consistency:.1f}% de consistência. "
            
            # Adicionar dados de desempenho fora
            away_stats = original_probabilities.get("away_team", {})
            away_wins = away_stats.get("away_wins", 0)
            away_draws = away_stats.get("away_draws", 0)
            away_losses = away_stats.get("away_losses", 0)
            
            if away_wins + away_draws + away_losses > 0:
                justification += f"Desempenho como visitante: {away_wins}V {away_draws}E {away_losses}D. "
            
            if "h2h" in original_probabilities:
                h2h = original_probabilities.get("h2h", {})
                away_h2h_wins = h2h.get("away_wins", 0)
                total_h2h = h2h.get("total_matches", 0)
                if total_h2h > 0:
                    justification += f"No histórico H2H, venceu {away_h2h_wins} de {total_h2h} confrontos. "
        
        # Empate
        elif team_name == "Empate" or ("ou Empate" in team_name):
            justification += f"Casa com {home_form_points:.0f}/15 pts como mandante, fora com {away_form_points:.0f}/15 pts como visitante. "
            
            # Adicionar percentual de empates de ambos os times
            home_stats = original_probabilities.get("home_team", {})
            away_stats = original_probabilities.get("away_team", {})
            home_draw_pct = home_stats.get("draw_pct", 0)
            away_draw_pct = away_stats.get("draw_pct", 0)
            
            if home_draw_pct > 0 or away_draw_pct > 0:
                justification += f"Tendência de empates: Casa {home_draw_pct:.0f}%, Fora {away_draw_pct:.0f}%. "
            
            if "h2h" in original_probabilities:
                h2h = original_probabilities.get("h2h", {})
                draws_h2h = h2h.get("draws", 0)
                total_h2h = h2h.get("total_matches", 0)
                if total_h2h > 0:
                    draw_pct = (draws_h2h / total_h2h) * 100
                    justification += f"No histórico H2H, {draw_pct:.0f}% dos jogos terminaram empatados. "
    
    # 2. MERCADOS DE GOLS - OVER/UNDER E AMBOS MARCAM
    elif market_type == "goals":
        # Extrair dados de xG e médias de gols
        home_stats = original_probabilities.get("home_team", {})
        away_stats = original_probabilities.get("away_team", {})
        
        # xG geral e específico
        home_xg = home_stats.get("xg_for_avg_overall", 0)
        home_xg_home = home_stats.get("xg_for_avg_home", home_xg)
        away_xg = away_stats.get("xg_for_avg_overall", 0)
        away_xg_away = away_stats.get("xg_for_avg_away", away_xg)
        
        # Médias de gols
        home_goals_avg = home_stats.get("goals_per_game", 0)
        home_goals_home = home_stats.get("home_goals_scored", 0) / max(1, home_stats.get("home_played", 1))
        away_goals_avg = away_stats.get("goals_per_game", 0)
        away_goals_away = away_stats.get("away_goals_scored", 0) / max(1, away_stats.get("away_played", 1))
        
        # Gols sofridos
        home_conceded_home = home_stats.get("home_goals_conceded", 0) / max(1, home_stats.get("home_played", 1))
        away_conceded_away = away_stats.get("away_goals_conceded", 0) / max(1, away_stats.get("away_played", 1))
        
        total_expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 0)
        
        # Verificar se o total esperado de gols é maior/menor que o threshold
        if threshold_direction == "over":
            if total_expected_goals > threshold:
                comparison = "acima"
            else:
                comparison = "próximo"
        else:  # Under
            if total_expected_goals < threshold:
                comparison = "abaixo"
            else:
                comparison = "próximo"
        
        # Construir justificativa específica para mercado de gols
        # Tentar identificar a linha específica
        over_key = f"over_{str(threshold).replace('.', '_')}_percentage"
        home_over_pct = home_stats.get(over_key, 0)
        away_over_pct = away_stats.get(over_key, 0)
        
        justification += f"xG: Casa {home_xg_home:.2f} (mandante), Fora {away_xg_away:.2f} (visitante). "
        justification += f"Média de gols: Casa marca {home_goals_home:.2f} e sofre {home_conceded_home:.2f} (mandante), "
        justification += f"Fora marca {away_goals_away:.2f} e sofre {away_conceded_away:.2f} (visitante). "
        
        if home_over_pct > 0 or away_over_pct > 0:
            justification += f"Over {threshold} histórico: Casa {home_over_pct:.0f}%, Fora {away_over_pct:.0f}%. "
        
        justification += f"Previsão de {total_expected_goals:.2f} gols, {comparison} do threshold {threshold}. "
    
    # AMBOS MARCAM (BTTS)
    elif market_type == "btts":
        # Extrair dados de xG e médias de gols
        home_stats = original_probabilities.get("home_team", {})
        away_stats = original_probabilities.get("away_team", {})
        
        # xG geral e específico
        home_xg = home_stats.get("xg_for_avg_overall", 0)
        home_xg_home = home_stats.get("xg_for_avg_home", home_xg)
        away_xg = away_stats.get("xg_for_avg_overall", 0)
        away_xg_away = away_stats.get("xg_for_avg_away", away_xg)
        
        # Médias de gols
        home_goals_home = home_stats.get("home_goals_scored", 0) / max(1, home_stats.get("home_played", 1))
        away_goals_away = away_stats.get("away_goals_scored", 0) / max(1, away_stats.get("away_played", 1))
        
        # Percentuais de BTTS e Clean Sheets
        home_btts_pct = home_stats.get("btts_pct", 0)
        away_btts_pct = away_stats.get("btts_pct", 0)
        home_cs_pct = home_stats.get("clean_sheets_pct", 0)
        away_cs_pct = away_stats.get("clean_sheets_pct", 0)
        
        # Probabilidade BTTS do histórico H2H
        h2h_btts_pct = original_probabilities.get("h2h", {}).get("btts_pct", 0)
        
        # Total esperado de gols
        total_expected_goals = original_probabilities.get("over_under", {}).get("expected_goals", 0)
        
        if "Sim" in team_name:
            justification += f"xG: Casa {home_xg_home:.2f} (mandante), Fora {away_xg_away:.2f} (visitante). "
            justification += f"Média de gols: Casa {home_goals_home:.2f}, Fora {away_goals_away:.2f}. "
            justification += f"Histórico BTTS: Casa {home_btts_pct:.0f}%, Fora {away_btts_pct:.0f}%"
            
            if h2h_btts_pct > 0:
                justification += f", H2H {h2h_btts_pct:.0f}%. "
            else:
                justification += ". "
                
            justification += f"Previsão de {total_expected_goals:.2f} gols totais. "
        else:  # Não
            justification += f"Clean sheets: Casa {home_cs_pct:.0f}%, Fora {away_cs_pct:.0f}%. "
            justification += f"xG: Casa {home_xg_home:.2f} (mandante), Fora {away_xg_away:.2f} (visitante). "
            justification += f"Histórico BTTS-Não: Casa {100-home_btts_pct:.0f}%, Fora {100-away_btts_pct:.0f}%. "
            justification += f"Previsão de {total_expected_goals:.2f} gols totais. "
    
    # 3. ESCANTEIOS
    elif market_type == "corners":
        # Extrair dados de escanteios
        home_stats = original_probabilities.get("home_team", {})
        away_stats = original_probabilities.get("away_team", {})
        
        # Médias de escanteios
        home_corners_avg = home_stats.get("corners_per_game", 0)
        home_corners_home = home_stats.get("home_corners_per_game", home_corners_avg)
        away_corners_avg = away_stats.get("corners_per_game", 0)
        away_corners_away = away_stats.get("away_corners_per_game", away_corners_avg)
        
        # Escanteios contra
        home_corners_against_avg = home_stats.get("cornersAgainstAVG_home", 0) or home_stats.get("cornersAgainstAVG_overall", 0)
        away_corners_against_avg = away_stats.get("cornersAgainstAVG_away", 0) or away_stats.get("cornersAgainstAVG_overall", 0)
        
        # Posse de bola (influencia escanteios)
        home_possession = home_stats.get("possession", 50)
        away_possession = away_stats.get("possession", 50)
        
        total_expected_corners = original_probabilities.get("corners", {}).get("expected_corners", 0)
        
        # Verificar se o total esperado de escanteios é maior/menor que o threshold
        if threshold_direction == "over":
            if total_expected_corners > threshold:
                comparison = "acima"
            else:
                comparison = "próximo"
        else:  # Under
            if total_expected_corners < threshold:
                comparison = "abaixo"
            else:
                comparison = "próximo"
        
        # Tentar identificar estatísticas para a linha específica
        over_key = f"over_{str(threshold).replace('.', '_')}_corners_percentage"
        home_over_corners_pct = home_stats.get(over_key, 0)
        away_over_corners_pct = away_stats.get(over_key, 0)
        
        justification += f"Escanteios: Casa {home_corners_home:.1f} a favor vs {home_corners_against_avg:.1f} contra (mandante), "
        justification += f"Fora {away_corners_away:.1f} a favor vs {away_corners_against_avg:.1f} contra (visitante). "
        
        if home_possession > 0 and away_possession > 0:
            justification += f"Posse de bola: Casa {home_possession:.0f}% vs Fora {away_possession:.0f}%. "
        
        if home_over_corners_pct > 0 or away_over_corners_pct > 0:
            justification += f"Over {threshold} histórico: Casa {home_over_corners_pct:.0f}%, Fora {away_over_corners_pct:.0f}%. "
        
        justification += f"Previsão de {total_expected_corners:.1f} escanteios, {comparison} do threshold {threshold}. "
    
    # 4. CARTÕES
    elif market_type == "cards":
        # Extrair dados de cartões
        home_stats = original_probabilities.get("home_team", {})
        away_stats = original_probabilities.get("away_team", {})
        
        # Médias de cartões
        home_cards_avg = home_stats.get("cards_per_game", 0)
        home_cards_home = home_stats.get("home_cards_per_game", home_cards_avg)
        away_cards_avg = away_stats.get("cards_per_game", 0)
        away_cards_away = away_stats.get("away_cards_per_game", away_cards_avg)
        
        # Cartões contra (provocados)
        home_cards_against = home_stats.get("cards_against", 0) / max(1, home_stats.get("played", 1))
        away_cards_against = away_stats.get("cards_against", 0) / max(1, away_stats.get("played", 1))
        
        total_expected_cards = original_probabilities.get("cards", {}).get("expected_cards", 0)
        
        # Árbitro (se disponível)
        referee = original_probabilities.get("match_info", {}).get("referee", "")
        referee_avg_cards = original_probabilities.get("match_info", {}).get("referee_avg_cards", 0)
        
        # Verificar se o total esperado de cartões é maior/menor que o threshold
        if threshold_direction == "over":
            if total_expected_cards > threshold:
                comparison = "acima"
            else:
                comparison = "próximo"
        else:  # Under
            if total_expected_cards < threshold:
                comparison = "abaixo"
            else:
                comparison = "próximo"
        
        # Tentar identificar estatísticas para a linha específica
        over_key = f"over_{str(threshold).replace('.', '_')}_cards_percentage"
        home_over_cards_pct = home_stats.get(over_key, 0)
        away_over_cards_pct = away_stats.get(over_key, 0)
        
        justification += f"Cartões: Casa {home_cards_home:.1f} recebidos/"
        justification += f"{home_cards_against:.1f} provocados (mandante), "
        justification += f"Fora {away_cards_away:.1f} recebidos/"
        justification += f"{away_cards_against:.1f} provocados (visitante). "
        
        if home_over_cards_pct > 0 or away_over_cards_pct > 0:
            justification += f"Over {threshold} histórico: Casa {home_over_cards_pct:.0f}%, Fora {away_over_cards_pct:.0f}%. "
        
        # Adicionar informação do árbitro se disponível
        if referee and referee_avg_cards > 0:
            justification += f"Árbitro {referee} com média de {referee_avg_cards:.1f} cartões/jogo. "
            
        justification += f"Previsão de {total_expected_cards:.1f} cartões, {comparison} do threshold {threshold}. "
    
    # Caso não seja identificado o tipo de mercado
    else:
        justification += f"Casa com {home_form_points:.0f}/15 pts como mandante, fora com {away_form_points:.0f}/15 pts como visitante. "
        if expected_goals:
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
