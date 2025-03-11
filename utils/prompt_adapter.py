import logging

# Configuração de logging
logger = logging.getLogger("valueHunter.prompt_adapter")

def adapt_api_data_for_prompt(complete_analysis):
    """
    Adapta os dados coletados da API para o formato esperado pelo format_enhanced_prompt
    
    Args:
        complete_analysis (dict): Dados coletados pelo enhanced_api_client
        
    Returns:
        dict: Dados formatados para o format_enhanced_prompt
    """
    try:
        # Verificar se os dados são válidos
        if not complete_analysis or not isinstance(complete_analysis, dict):
            logger.error("Dados de análise inválidos")
            return None
        
        # Inicializar a estrutura adaptada
        adapted_data = {
            "basic_stats": {
                "home_team": {"name": "", "stats": {}},
                "away_team": {"name": "", "stats": {}},
                "referee": "Não informado"
            },
            "team_form": {
                "home": [],
                "away": []
            },
            "head_to_head": {},
            "advanced_stats": {
                "home": {},
                "away": {}
            }
        }
        
        # 1. Adaptar estatísticas básicas
        if "basic_stats" in complete_analysis:
            # Copiar estrutura básica
            adapted_data["basic_stats"] = complete_analysis["basic_stats"]
            
            # Garantir que a estrutura esteja correta
            if "home_team" in complete_analysis["basic_stats"]:
                home_team = complete_analysis["basic_stats"]["home_team"]
                if "stats" in home_team:
                    # Se "stats" for um objeto, extrair estatísticas do objeto completo
                    if isinstance(home_team["stats"], dict):
                        # Verificar se há um subobjeto "stats" dentro do objeto "stats"
                        if "stats" in home_team["stats"] and isinstance(home_team["stats"]["stats"], dict):
                            adapted_data["basic_stats"]["home_team"]["stats"] = home_team["stats"]["stats"]
                        else:
                            adapted_data["basic_stats"]["home_team"]["stats"] = extract_stats(home_team["stats"])
            
            if "away_team" in complete_analysis["basic_stats"]:
                away_team = complete_analysis["basic_stats"]["away_team"]
                if "stats" in away_team:
                    # Se "stats" for um objeto, extrair estatísticas do objeto completo
                    if isinstance(away_team["stats"], dict):
                        # Verificar se há um subobjeto "stats" dentro do objeto "stats"
                        if "stats" in away_team["stats"] and isinstance(away_team["stats"]["stats"], dict):
                            adapted_data["basic_stats"]["away_team"]["stats"] = away_team["stats"]["stats"]
                        else:
                            adapted_data["basic_stats"]["away_team"]["stats"] = extract_stats(away_team["stats"])
        
        # 2. Adaptar form recente
        if "team_form" in complete_analysis:
            # Verificar se temos dados de form
            if "home" in complete_analysis["team_form"] and isinstance(complete_analysis["team_form"]["home"], dict):
                # Se estiver no formato da API lastx
                if "data" in complete_analysis["team_form"]["home"] and isinstance(complete_analysis["team_form"]["home"]["data"], list):
                    adapted_data["team_form"]["home"] = adapt_last_matches(complete_analysis["team_form"]["home"]["data"])
                else:
                    adapted_data["team_form"]["home"] = []
            elif "home" in complete_analysis["team_form"] and isinstance(complete_analysis["team_form"]["home"], list):
                # Se já estiver em lista
                adapted_data["team_form"]["home"] = complete_analysis["team_form"]["home"]
            
            if "away" in complete_analysis["team_form"] and isinstance(complete_analysis["team_form"]["away"], dict):
                # Se estiver no formato da API lastx
                if "data" in complete_analysis["team_form"]["away"] and isinstance(complete_analysis["team_form"]["away"]["data"], list):
                    adapted_data["team_form"]["away"] = adapt_last_matches(complete_analysis["team_form"]["away"]["data"])
                else:
                    adapted_data["team_form"]["away"] = []
            elif "away" in complete_analysis["team_form"] and isinstance(complete_analysis["team_form"]["away"], list):
                # Se já estiver em lista
                adapted_data["team_form"]["away"] = complete_analysis["team_form"]["away"]
        
        # 3. Adaptar Head-to-Head
        if "head_to_head" in complete_analysis:
            adapted_data["head_to_head"] = complete_analysis["head_to_head"]
        elif "match_details" in complete_analysis and complete_analysis["match_details"]:
            # Se temos detalhes da partida, verificar se há H2H
            if "h2h" in complete_analysis["match_details"]:
                adapted_data["head_to_head"] = complete_analysis["match_details"]["h2h"]
        
        # 4. Adaptar Advanced Stats
        if "advanced_stats" in complete_analysis:
            adapted_data["advanced_stats"] = complete_analysis["advanced_stats"]
        
        logger.info("Dados adaptados com sucesso para formato do prompt")
        return adapted_data
    
    except Exception as e:
        logger.error(f"Erro ao adaptar dados para prompt: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def extract_stats(stats_obj):
    """
    Extrai estatísticas relevantes de um objeto de estatísticas
    
    Args:
        stats_obj (dict): Objeto com estatísticas do time
        
    Returns:
        dict: Estatísticas extraídas no formato esperado
    """
    stats = {}
    
    # Mapeamento de campos da API para o formato esperado
    field_mapping = {
        'matches_played': ['seasonMatchesPlayed_overall', 'matches_played', 'MP'],
        'wins': ['seasonWinsNum_overall', 'wins', 'W'],
        'draws': ['seasonDrawsNum_overall', 'draws', 'D'],
        'losses': ['seasonLossesNum_overall', 'losses', 'L'],
        'goals_scored': ['seasonGoals_overall', 'goals_scored', 'Gls'],
        'goals_conceded': ['seasonConceded_overall', 'goals_conceded', 'GA'],
        'xG': ['xg_for_overall', 'xg', 'xG'],
        'xGA': ['xg_against_avg_overall', 'xga', 'xGA'],
        'possession': ['possessionAVG_overall', 'possession', 'Poss'],
        'win_percentage': ['winPercentage_overall'],
        'draw_percentage': ['drawPercentage_overall'],
        'clean_sheets': ['seasonCS_overall'],
        'clean_sheet_percentage': ['seasonCSPercentage_overall'],
        'btts_percentage': ['seasonBTTSPercentage_overall'],
        'over_2_5_percentage': ['seasonOver25Percentage_overall'],
        'home_wins': ['seasonWinsNum_home'],
        'home_draws': ['seasonDrawsNum_home'],
        'home_losses': ['seasonLossesNum_home'],
        'away_wins': ['seasonWinsNum_away'],
        'away_draws': ['seasonDrawsNum_away'],
        'away_losses': ['seasonLossesNum_away']
    }
    
    # Extrair campos usando o mapeamento
    for target_field, source_fields in field_mapping.items():
        for source_field in source_fields:
            if source_field in stats_obj:
                stats[target_field] = stats_obj[source_field]
                break
    
    return stats

def adapt_last_matches(matches_data):
    """
    Adapta os dados dos últimos jogos para o formato esperado
    
    Args:
        matches_data (list): Lista de jogos da API
        
    Returns:
        list: Lista formatada para o prompt
    """
    if not matches_data or not isinstance(matches_data, list):
        return []
    
    # Limitando aos últimos 5 jogos
    matches = matches_data[:5]
    
    # Converter para o formato esperado
    formatted_matches = []
    for match in matches:
        result = "?"
        
        # Determinar resultado (W/D/L)
        if "result" in match:
            result = match["result"]
        elif "homeID" in match and "awayID" in match and "homeGoals" in match and "awayGoals" in match and "teamID" in match:
            # Se for o time da casa
            if match["homeID"] == match["teamID"]:
                if match["homeGoals"] > match["awayGoals"]:
                    result = "W"
                elif match["homeGoals"] < match["awayGoals"]:
                    result = "L"
                else:
                    result = "D"
            # Se for o time visitante
            elif match["awayID"] == match["teamID"]:
                if match["homeGoals"] < match["awayGoals"]:
                    result = "W"
                elif match["homeGoals"] > match["awayGoals"]:
                    result = "L"
                else:
                    result = "D"
        
        formatted_matches.append({"result": result})
    
    # Preencher com placeholders se necessário
    while len(formatted_matches) < 5:
        formatted_matches.append({"result": "?"})
    
    return formatted_matches
