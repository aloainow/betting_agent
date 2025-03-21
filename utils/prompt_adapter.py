import logging

# Configuração de logging
logger = logging.getLogger("valueHunter.prompt_adapter")

def transform_to_highly_optimized_data(api_data, home_team_name, away_team_name, selected_markets=None):
    """
    Transform API data into a properly structured format with all essential fields.
    
    Args:
        api_data (dict): Original API data from FootyStats
        home_team_name (str): Name of home team
        away_team_name (str): Name of away team
        selected_markets (dict, optional): Dictionary of selected markets to filter data
        
    Returns:
        dict: Highly optimized data structure with minimal footprint
    """
    import logging
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    try:
        # Initialize with the correct structure - FIXO: usado match_info e home_team/away_team
        optimized_data = {
            "match_info": {  # Changed from "match" to "match_info"
                "home_team": home_team_name,  # Changed from "home" to "home_team"
                "away_team": away_team_name,  # Changed from "away" to "away_team"
                "league": "",
                "league_id": None
            },
            "home_team": {},  # Changed from "home" to "home_team"
            "away_team": {},  # Changed from "away" to "away_team"
            "h2h": {}
        }
        
        # Check if we have valid API data
        if not api_data or not isinstance(api_data, dict):
            logger.error("Invalid API data provided")
            return optimized_data
        
        # Debug: Log API data structure
        logger.info(f"API data keys: {list(api_data.keys())}")
        if "basic_stats" in api_data:
            logger.info(f"basic_stats keys: {list(api_data['basic_stats'].keys())}")
        
        # Fill in league info
        if "basic_stats" in api_data and "league_id" in api_data["basic_stats"]:
            optimized_data["match_info"]["league_id"] = api_data["basic_stats"]["league_id"]
        
        # ENSURE ALL ESSENTIAL STATS ARE INCLUDED - don't rely on selected markets
        essential_stats = {
            # Basic stats
            "played", "wins", "draws", "losses", 
            "goals_scored", "goals_conceded", 
            "clean_sheets_pct", "btts_pct", "over_2_5_pct",
            
            # Home/Away specific
            "home_played", "home_wins", "home_draws", "home_losses",
            "home_goals_scored", "home_goals_conceded",
            "away_played", "away_wins", "away_draws", "away_losses",
            "away_goals_scored", "away_goals_conceded",
            
            # Advanced
            "xg", "xga", "ppda", "possession",
            
            # Cards
            "cards_total", "cards_per_game", "yellow_cards", "red_cards",
            "over_3_5_cards_pct", "home_cards_per_game", "away_cards_per_game",
            
            # Corners
            "corners_total", "corners_per_game", "corners_for", "corners_against",
            "over_9_5_corners_pct", "home_corners_per_game", "away_corners_per_game"
        }
        
        # Extract home team stats - use all essential stats
        home_stats = extract_expanded_team_stats(api_data, "home", essential_stats)
        optimized_data["home_team"] = home_stats
        
        # Extract away team stats - use all essential stats
        away_stats = extract_expanded_team_stats(api_data, "away", essential_stats)
        optimized_data["away_team"] = away_stats
        
        # Extract complete h2h data
        optimized_data["h2h"] = extract_expanded_h2h(api_data)
        
        # Add form data
        optimized_data["home_team"]["form"] = extract_form_string(api_data, "home")
        optimized_data["away_team"]["form"] = extract_form_string(api_data, "away")
        
        # Add fallbacks for critical fields
        ensure_critical_fields(optimized_data, home_team_name, away_team_name)
        
        # Debug log - Verificar campos extraídos
        logger.info(f"Home stats extracted: {list(home_stats.keys())}")
        logger.info(f"Away stats extracted: {list(away_stats.keys())}")
        logger.info(f"H2H stats extracted: {list(optimized_data['h2h'].keys())}")
        
        logger.info(f"Created complete data structure for {home_team_name} vs {away_team_name}")
        return optimized_data
        
    except Exception as e:
        logger.error(f"Error creating optimized data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "match_info": {"home_team": home_team_name, "away_team": away_team_name},
            "home_team": {}, 
            "away_team": {},
            "h2h": {}
        }

def transform_to_exact_format(api_data, home_team_name, away_team_name, selected_markets=None):
    """
    Transforma os dados da API no formato exato requerido pelo agente de IA.
    
    Args:
        api_data (dict): Dados originais da API FootyStats
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
        selected_markets (dict, optional): Dicionário de mercados selecionados
        
    Returns:
        dict: Dados no formato exato requerido
    """
    import logging
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    # Inicializa a estrutura de dados exata requerida
    formatted_data = {
        "match_info": {
            "home_team": home_team_name,
            "away_team": away_team_name,
            "league": "",
            "league_id": None
        },
        "home_team": {
            # Basic stats
            "played": 0, "wins": 0, "draws": 0, "losses": 0,
            "goals_scored": 0, "goals_conceded": 0,
            "clean_sheets_pct": 0, "btts_pct": 0, "over_2_5_pct": 0,
            # Home specific
            "home_played": 0, "home_wins": 0, "home_draws": 0, "home_losses": 0,
            "home_goals_scored": 0, "home_goals_conceded": 0,
            # Advanced
            "xg": 0, "xga": 0, "ppda": 0, "possession": 0,
            # Card stats
            "cards_total": 0, "cards_per_game": 0, "yellow_cards": 0, "red_cards": 0,
            "over_3_5_cards_pct": 0, "home_cards_per_game": 0, "away_cards_per_game": 0,
            # Corner stats
            "corners_total": 0, "corners_per_game": 0, "corners_for": 0, "corners_against": 0,
            "over_9_5_corners_pct": 0, "home_corners_per_game": 0, "away_corners_per_game": 0,
            # Form (simplified)
            "form": "", "recent_matches": []
        },
        "away_team": {
            # Basic stats
            "played": 0, "wins": 0, "draws": 0, "losses": 0,
            "goals_scored": 0, "goals_conceded": 0,
            "clean_sheets_pct": 0, "btts_pct": 0, "over_2_5_pct": 0,
            # Away specific
            "away_played": 0, "away_wins": 0, "away_draws": 0, "away_losses": 0,
            "away_goals_scored": 0, "away_goals_conceded": 0,
            # Advanced
            "xg": 0, "xga": 0, "ppda": 0, "possession": 0,
            # Card stats
            "cards_total": 0, "cards_per_game": 0, "yellow_cards": 0, "red_cards": 0,
            "over_3_5_cards_pct": 0, "home_cards_per_game": 0, "away_cards_per_game": 0,
            # Corner stats
            "corners_total": 0, "corners_per_game": 0, "corners_for": 0, "corners_against": 0,
            "over_9_5_corners_pct": 0, "home_corners_per_game": 0, "away_corners_per_game": 0,
            # Form (simplified)
            "form": "", "recent_matches": []
        },
        "h2h": {
            "total_matches": 0, "home_wins": 0, "away_wins": 0, "draws": 0,
            "over_2_5_pct": 0, "btts_pct": 0, "avg_cards": 0, "avg_corners": 0,
            "recent_matches": []
        }
    }
    
    # Se não houver dados da API, retorna a estrutura padrão
    if not api_data or not isinstance(api_data, dict):
        logger.warning("Dados da API inválidos ou vazios, retornando estrutura padrão")
        return formatted_data
    
    try:
        # Preenche informações da liga
        if "basic_stats" in api_data and "league_id" in api_data["basic_stats"]:
            formatted_data["match_info"]["league_id"] = api_data["basic_stats"]["league_id"]
        
        # Extrai estatísticas do time da casa e visitante
        extract_team_data(api_data, formatted_data, "home")
        extract_team_data(api_data, formatted_data, "away")
        
        # Extrai dados de confronto direto (H2H)
        extract_h2h_data(api_data, formatted_data)
        
        # Log de sucesso
        logger.info(f"Dados formatados com sucesso para {home_team_name} vs {away_team_name}")
        return formatted_data
        
    except Exception as e:
        logger.error(f"Erro ao formatar dados: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Retorna a estrutura padrão em caso de erro
        return formatted_data

def extract_advanced_team_data(api_data, home_team_name, away_team_name):
    """
    Versão aprimorada para extrair dados do time com estrutura exata necessária
    para análise ótima de IA. Lida com múltiplos formatos de API e garante que todos
    os campos estatísticos necessários estejam incluídos.
    
    Args:
        api_data (dict): Dados originais da API FootyStats
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
        
    Returns:
        dict: Dados formatados com a estrutura exata necessária para análise de IA
    """
    import logging
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    # Inicializa a estrutura completa com todos os campos
    formatted_data = {
        "match_info": {
            "home_team": home_team_name,
            "away_team": away_team_name,
            "league": "",
            "league_id": None
        },
        "home_team": {
            # Estatísticas básicas
            "played": 0, "wins": 0, "draws": 0, "losses": 0,
            "goals_scored": 0, "goals_conceded": 0, "clean_sheets_pct": 0,
            "btts_pct": 0, "over_2_5_pct": 0,
            # Específicas para casa
            "home_played": 0, "home_wins": 0, "home_draws": 0, "home_losses": 0,
            "home_goals_scored": 0, "home_goals_conceded": 0,
            # Avançadas
            "xg": 0, "xga": 0, "ppda": 0, "possession": 0,
            # Estatísticas de cartões
            "cards_total": 0, "cards_per_game": 0, "yellow_cards": 0, "red_cards": 0,
            "over_3_5_cards_pct": 0, "home_cards_per_game": 0, "away_cards_per_game": 0,
            # Estatísticas de escanteios
            "corners_total": 0, "corners_per_game": 0, "corners_for": 0, "corners_against": 0,
            "over_9_5_corners_pct": 0, "home_corners_per_game": 0, "away_corners_per_game": 0,
            # Forma (simplificada)
            "form": "", "recent_matches": []
        },
        "away_team": {
            # Mesma estrutura para o time visitante
            "played": 0, "wins": 0, "draws": 0, "losses": 0,
            "goals_scored": 0, "goals_conceded": 0, "clean_sheets_pct": 0,
            "btts_pct": 0, "over_2_5_pct": 0,
            # Específicas para fora
            "away_played": 0, "away_wins": 0, "away_draws": 0, "away_losses": 0,
            "away_goals_scored": 0, "away_goals_conceded": 0,
            # Avançadas
            "xg": 0, "xga": 0, "ppda": 0, "possession": 0,
            # Estatísticas de cartões
            "cards_total": 0, "cards_per_game": 0, "yellow_cards": 0, "red_cards": 0,
            "over_3_5_cards_pct": 0, "home_cards_per_game": 0, "away_cards_per_game": 0,
            # Estatísticas de escanteios
            "corners_total": 0, "corners_per_game": 0, "corners_for": 0, "corners_against": 0,
            "over_9_5_corners_pct": 0, "home_corners_per_game": 0, "away_corners_per_game": 0,
            # Forma (simplificada)
            "form": "", "recent_matches": []
        },
        "h2h": {
            "total_matches": 0, "home_wins": 0, "away_wins": 0, "draws": 0,
            "over_2_5_pct": 0, "btts_pct": 0, "avg_cards": 0, "avg_corners": 0,
            "recent_matches": []
        }
    }
    
    # Sair antecipadamente se não houver dados válidos
    if not api_data or not isinstance(api_data, dict):
        logger.error("Dados de API inválidos fornecidos")
        return formatted_data
    
    # Obter informações da liga
    if "basic_stats" in api_data:
        # Obter ID da liga
        if "league_id" in api_data["basic_stats"]:
            formatted_data["match_info"]["league_id"] = api_data["basic_stats"]["league_id"]
        
        # Tentar obter nome da liga
        if "league" in api_data:
            formatted_data["match_info"]["league"] = api_data["league"].get("name", "")
        elif "league_name" in api_data["basic_stats"]:
            formatted_data["match_info"]["league"] = api_data["basic_stats"]["league_name"]
    
    # IMPORTANTE: Buscar dados em MÚLTIPLOS caminhos possíveis da API
    
    # Processar dados do time da casa
    if "basic_stats" in api_data and "home_team" in api_data["basic_stats"]:
        home_team = api_data["basic_stats"]["home_team"]
        
        # NOVO: Verificar múltiplos caminhos para estatísticas
        home_stats = {}
        
        # Caminho 1: stats direto no time
        if "stats" in home_team and isinstance(home_team["stats"], dict):
            home_stats = home_team["stats"]
        
        # Caminho 2: stats aninhado mais profundo
        if not home_stats and "stats" in home_team:
            if isinstance(home_team["stats"], dict) and "stats" in home_team["stats"]:
                home_stats = home_team["stats"]["stats"]
        
        # Caminho 3: stats direto no objeto time
        for key in ["seasonMatchesPlayed_overall", "wins", "goals_scored"]:
            if key in home_team:
                # Se encontrarmos estatísticas diretamente no objeto time, use-as
                home_stats = home_team
                break
                
        # NOVO: Melhor extração com múltiplos nomes alternativos para campos importantes
        extract_team_stats(formatted_data["home_team"], home_stats, home_team, "home")
        
        # NOVO: Buscar também no advanced_stats
        if "advanced_stats" in api_data and "home" in api_data["advanced_stats"]:
            extract_advanced_metrics(formatted_data["home_team"], api_data["advanced_stats"]["home"])
    
    # Processar dados do time visitante (mesma lógica)
    if "basic_stats" in api_data and "away_team" in api_data["basic_stats"]:
        away_team = api_data["basic_stats"]["away_team"]
        
        away_stats = {}
        
        if "stats" in away_team and isinstance(away_team["stats"], dict):
            away_stats = away_team["stats"]
        
        if not away_stats and "stats" in away_team:
            if isinstance(away_team["stats"], dict) and "stats" in away_team["stats"]:
                away_stats = away_team["stats"]["stats"]
        
        for key in ["seasonMatchesPlayed_overall", "wins", "goals_scored"]:
            if key in away_team:
                away_stats = away_team
                break
                
        extract_team_stats(formatted_data["away_team"], away_stats, away_team, "away")
        
        if "advanced_stats" in api_data and "away" in api_data["advanced_stats"]:
            extract_advanced_metrics(formatted_data["away_team"], api_data["advanced_stats"]["away"])
    
    # NOVO: Extração melhorada de H2H com múltiplos caminhos
    extract_h2h_data(api_data, formatted_data)
    
    # NOVO: Extração melhorada de dados de forma
    extract_form_data(api_data, formatted_data, home_team_name, away_team_name)
    
    # Calcular estatísticas derivadas
    calculate_derived_stats(formatted_data["home_team"])
    calculate_derived_stats(formatted_data["away_team"])
    
    logger.info(f"Extração de dados completa para {home_team_name} vs {away_team_name}")
    return formatted_data

def extract_team_stats(target_dict, team_data):
    """Extrai estatísticas detalhadas de um time, incluindo dados de casa/fora.
    
    Args:
        target_dict (dict): Dicionário de destino para armazenar os dados
        team_data (dict): Dados do time da API
    """
    # Garantir que temos acesso às estatísticas
    if not team_data or "stats" not in team_data:
        return
    
    stats = team_data["stats"]
    
    # Campos a serem extraídos diretamente
    direct_fields = [
        # Gols totais
        "seasonGoalsTotal_overall", "seasonGoalsTotal_home", "seasonGoalsTotal_away",
        
        # Gols feitos
        "seasonScoredNum_overall", "seasonScoredNum_home", "seasonScoredNum_away",
        
        # Gols sofridos
        "seasonConcededNum_overall", "seasonConcededNum_home", "seasonConcededNum_away",
        
        # Resultados
        "seasonWinsNum_overall", "seasonWinsNum_home", "seasonWinsNum_away",
        "seasonDrawsNum_overall", "seasonDrawsNum_home", "seasonDrawsNum_away",
        "seasonLossesNum_overall", "seasonLossesNum_home", "seasonLossesNum_away",
        
        # Clean sheets
        "seasonCS_overall", "seasonCS_home", "seasonCS_away",
        
        # Pontos por jogo
        "seasonPPG_overall", "seasonPPG_home", "seasonPPG_away", "seasonRecentPPG",
        
        # Performance em casa e fora
        "currentFormHome", "currentFormAway",
        
        # Posição na tabela
        "leaguePosition_overall", "leaguePosition_home", "leaguePosition_away",
        
        # Escanteios
        "cornersTotal_overall", "cornersTotal_home", "cornersTotal_away",
        "cornersTotalAVG_overall", "cornersTotalAVG_home", "cornersTotalAVG_away",
        "cornersAVG_overall", "cornersAVG_home", "cornersAVG_away",
        "cornersAgainst_overall", "cornersAgainst_home", "cornersAgainst_away",
        "cornersAgainstAVG_overall", "cornersAgainstAVG_home", "cornersAgainstAVG_away",
        
        # Cartões
        "cardsTotal_overall", "cardsTotal_home", "cardsTotal_away",
        "cardsAVG_overall", "cardsAVG_home", "cardsAVG_away",
        
        # Chutes
        "shotsTotal_overall", "shotsTotal_home", "shotsTotal_away",
        "shotsAVG_overall", "shotsAVG_home", "shotsAVG_away",
        "shotsOnTargetTotal_overall", "shotsOnTargetTotal_home", "shotsOnTargetTotal_away",
        "shotsOnTargetAVG_overall", "shotsOnTargetAVG_home", "shotsOnTargetAVG_away",
        
        # Posse de bola
        "possessionAVG_overall", "possessionAVG_home", "possessionAVG_away",
        
        # XG e XGA
        "xg_for_avg_overall", "xg_for_avg_home", "xg_for_avg_away",
        "xg_against_avg_overall", "xg_against_avg_home", "xg_against_avg_away",
        "xg_for_overall", "xg_for_home", "xg_for_away",
        "xg_against_overall", "xg_against_home", "xg_against_away",
        
        # Forma
        "formRun_overall", "formRun_home", "formRun_away"
    ]
    
    # Extrair cada campo
    for field in direct_fields:
        if field in stats:
            target_dict[field] = stats[field]
    
    # Também mapear para os nomes mais simples/padronizados que usamos no template
    # Isso é opcional, mas ajuda a manter compatibilidade
    field_mappings = {
        # Estatísticas gerais
        "played": "seasonMatchesPlayed_overall",
        "home_played": "seasonMatchesPlayed_home",
        "away_played": "seasonMatchesPlayed_away",
        "wins": "seasonWinsNum_overall",
        "home_wins": "seasonWinsNum_home",
        "away_wins": "seasonWinsNum_away",
        "draws": "seasonDrawsNum_overall", 
        "losses": "seasonLossesNum_overall",
        
        # Gols
        "goals_scored": "seasonScoredNum_overall",
        "home_goals_scored": "seasonScoredNum_home",
        "away_goals_scored": "seasonScoredNum_away",
        "goals_conceded": "seasonConcededNum_overall",
        "home_goals_conceded": "seasonConcededNum_home",
        "away_goals_conceded": "seasonConcededNum_away",
        "goals_per_game": "goalsAvgPerMatch_overall",
        "conceded_per_game": "concededAvgPerMatch_overall",
        
        # xG
        "xg": "xg_for_overall",
        "home_xg": "xg_for_home",
        "away_xg": "xg_for_away",
        "xga": "xg_against_overall",
        "home_xga": "xg_against_home",
        "away_xga": "xg_against_away",
        
        # Forma
        "form": "formRun_overall",
        "home_form": "formRun_home",
        "away_form": "formRun_away",
        
        # Outros
        "clean_sheets_pct": "seasonCSPercentage_overall",
        "btts_pct": "seasonBTTSPercentage_overall",
        "over_2_5_pct": "seasonOver25Percentage_overall",
        "possession": "possessionAVG_overall",
        "home_possession": "possessionAVG_home",
        "away_possession": "possessionAVG_away",
        
        # Escanteios
        "corners_per_game": "cornersTotalAVG_overall",
        "home_corners_per_game": "cornersTotalAVG_home",
        "away_corners_per_game": "cornersTotalAVG_away",
        
        # Cartões
        "cards_per_game": "cardsAVG_overall",
        "home_cards_per_game": "cardsAVG_home",
        "away_cards_per_game": "cardsAVG_away",
    }
    
    # Mapear os campos para seus equivalentes simplificados
    for target_field, source_field in field_mappings.items():
        if source_field in stats:
            target_dict[target_field] = stats[source_field]
def extract_advanced_metrics(target, advanced_data):
    """Extrai métricas avançadas"""
    if not advanced_data or not isinstance(advanced_data, dict):
        return
        
    # PPDA (Passes por Ação Defensiva)
    ppda_keys = ["ppda", "passes_per_defensive_action", "PPDA"]
    for key in ppda_keys:
        if key in advanced_data and advanced_data[key] is not None:
            try:
                target["ppda"] = float(advanced_data[key])
                break
            except (ValueError, TypeError):
                pass
    
    # Outras métricas avançadas (adicionar conforme necessário)
    other_metrics = {
        "xg": ["xg", "expected_goals", "xG"],
        "xga": ["xga", "expected_goals_against", "xGA"]
    }
    
    for target_key, source_keys in other_metrics.items():
        for key in source_keys:
            if key in advanced_data and advanced_data[key] is not None:
                try:
                    target[target_key] = float(advanced_data[key])
                    break
                except (ValueError, TypeError):
                    pass

def extract_h2h_data(api_data, formatted_data):
    """
    Extract head-to-head data
    
    Args:
        api_data (dict): Original API data
        formatted_data (dict): Target data structure
    """
    h2h_data = None
    
    # Try different possible locations for H2H data
    if "head_to_head" in api_data:
        h2h_data = api_data["head_to_head"]
    elif "match_details" in api_data and api_data["match_details"]:
        if "h2h" in api_data["match_details"]:
            h2h_data = api_data["match_details"]["h2h"]
    elif "h2h" in api_data:
        h2h_data = api_data["h2h"]
    
    if not h2h_data:
        return
        
    # Define mappings for H2H fields
    mappings = {
        "total_matches": ["total_matches", "matches", "matches_total"],
        "home_wins": ["home_wins", "home_team_wins"],
        "away_wins": ["away_wins", "away_team_wins"],
        "draws": ["draws", "equal"],
        "over_2_5_pct": ["over_2_5_percentage", "over_2_5_pct", "over25_percentage"],
        "btts_pct": ["btts_percentage", "btts_pct", "both_teams_scored_percentage"],
        "avg_cards": ["average_cards", "avg_cards", "cards_avg"],
        "avg_corners": ["average_corners", "avg_corners", "corners_avg"]
    }
    
    # Extract each field using mappings
    for target_field, source_fields in mappings.items():
        for field in source_fields:
            if field in h2h_data:
                value = h2h_data[field]
                if value is not None and value != 'N/A':
                    try:
                        formatted_data["h2h"][target_field] = float(value)
                        break
                    except (ValueError, TypeError):
                        pass
    
    # Extract recent matches
    if "matches" in h2h_data and isinstance(h2h_data["matches"], list):
        formatted_data["h2h"]["recent_matches"] = h2h_data["matches"][:5]
    elif "previous_matches" in h2h_data and isinstance(h2h_data["previous_matches"], list):
        formatted_data["h2h"]["recent_matches"] = h2h_data["previous_matches"][:5]

def extract_form_data(api_data, formatted_data, home_team_name, away_team_name):
    """Extração melhorada de dados de forma dos times"""
    
    # Time da casa
    if "team_form" in api_data and "home" in api_data["team_form"]:
        form_data = api_data["team_form"]["home"]
        
        if isinstance(form_data, list) and form_data:
            # Extrair string de forma (ex. "WDLWW")
            form_string = ""
            recent_matches = []
            
            for i in range(min(5, len(form_data))):
                match = form_data[i]
                
                # Extrair resultado
                result = "?"
                if isinstance(match, dict):
                    if "result" in match:
                        result = match["result"]
                    
                    # NOVO: Construir objeto de partida melhorado
                    recent_match = {
                        "opponent": match.get("opponent", match.get("against", "Desconhecido")),
                        "result": result,
                        "score": match.get("score", match.get("result_raw", "0-0")),
                        "date": match.get("date", match.get("match_date", "Sem data"))
                    }
                    recent_matches.append(recent_match)
                    
                form_string += result
            
            # Garantir que temos pelo menos 5 caracteres
            form_string = form_string.ljust(5, '?')[:5]
            
            formatted_data["home_team"]["form"] = form_string
            
            # Garantir que temos 5 jogos recentes
            while len(recent_matches) < 5:
                recent_matches.append({
                    "opponent": "Desconhecido",
                    "result": "?",
                    "score": "0-0",
                    "date": "Sem data"
                })
                
            formatted_data["home_team"]["recent_matches"] = recent_matches
    
    # Time visitante (mesmo processo)
    if "team_form" in api_data and "away" in api_data["team_form"]:
        form_data = api_data["team_form"]["away"]
        
        if isinstance(form_data, list) and form_data:
            form_string = ""
            recent_matches = []
            
            for i in range(min(5, len(form_data))):
                match = form_data[i]
                
                result = "?"
                if isinstance(match, dict):
                    if "result" in match:
                        result = match["result"]
                    
                    recent_match = {
                        "opponent": match.get("opponent", match.get("against", "Desconhecido")),
                        "result": result,
                        "score": match.get("score", match.get("result_raw", "0-0")),
                        "date": match.get("date", match.get("match_date", "Sem data"))
                    }
                    recent_matches.append(recent_match)
                    
                form_string += result
            
            form_string = form_string.ljust(5, '?')[:5]
            
            formatted_data["away_team"]["form"] = form_string
            
            while len(recent_matches) < 5:
                recent_matches.append({
                    "opponent": "Desconhecido",
                    "result": "?",
                    "score": "0-0",
                    "date": "Sem data"
                })
                
            formatted_data["away_team"]["recent_matches"] = recent_matches

def calculate_derived_stats(team_stats):
    """Calcula estatísticas derivadas de estatísticas básicas"""
    
    # Cartões totais e por jogo
    if team_stats["cards_total"] == 0:
        cards_total = team_stats["yellow_cards"] + team_stats["red_cards"]
        if cards_total > 0:
            team_stats["cards_total"] = cards_total
            
    if team_stats["played"] > 0 and team_stats["cards_per_game"] == 0 and team_stats["cards_total"] > 0:
        team_stats["cards_per_game"] = round(team_stats["cards_total"] / team_stats["played"], 2)
    
    # Escanteios totais e por jogo
    if team_stats["corners_total"] == 0:
        corners_total = team_stats["corners_for"] + team_stats["corners_against"]
        if corners_total > 0:
            team_stats["corners_total"] = corners_total
            
    if team_stats["played"] > 0 and team_stats["corners_per_game"] == 0 and team_stats["corners_total"] > 0:
        team_stats["corners_per_game"] = round(team_stats["corners_total"] / team_stats["played"], 2)

def extract_expanded_team_stats(api_data, team_type, essential_stats):
    """
    Extract comprehensive team statistics with fallbacks for missing data.
    
    Args:
        api_data (dict): Original API data
        team_type (str): "home" or "away"
        essential_stats (set): Set of essential stat names to include
        
    Returns:
        dict: Complete stats dictionary with all essential fields
    """
    stats = {}
    
    # Initialize with default values for all essential stats
    for stat in essential_stats:
        stats[stat] = 0
    
    # Fill in form placeholder
    stats["form"] = "?????"
    stats["recent_matches"] = []
    
    # If no valid data, return defaults
    if not api_data or "basic_stats" not in api_data:
        return stats
    
    # Try to extract real data
    team_key = f"{team_type}_team"
    if team_key in api_data["basic_stats"]:
        team_data = api_data["basic_stats"][team_key]
        
        # Debug log
        logger.info(f"{team_type}_team keys: {list(team_data.keys() if isinstance(team_data, dict) else [])}")
        
        # Try different possible locations and formats for stats
        if "stats" in team_data:
            raw_stats = None
            if isinstance(team_data["stats"], dict):
                if "stats" in team_data["stats"]:
                    raw_stats = team_data["stats"]["stats"]
                else:
                    raw_stats = team_data["stats"]
            
            if raw_stats:
                # Debug log
                logger.info(f"{team_type} raw_stats keys: {list(raw_stats.keys() if isinstance(raw_stats, dict) else [])}")
                
                # Map API fields to our essential stats with multiple possible keys
                field_mapping = {
                    "played": ["matches_played", "seasonMatchesPlayed_overall", "MP"],
                    "wins": ["wins", "seasonWinsNum_overall", "W"],
                    "draws": ["draws", "seasonDrawsNum_overall", "D"],
                    "losses": ["losses", "seasonLossesNum_overall", "L"],
                    "goals_scored": ["goals_scored", "seasonGoals_overall", "Gls", "goals"],
                    "goals_conceded": ["goals_conceded", "seasonConceded_overall", "GA"],
                    "xg": ["xG", "xg", "xg_for_overall", "expected_goals"],
                    "xga": ["xGA", "xga", "xg_against_avg_overall"],
                    "possession": ["possession", "possessionAVG_overall", "Poss"],
                    "clean_sheets_pct": ["clean_sheet_percentage", "seasonCSPercentage_overall"],
                    "btts_pct": ["btts_percentage", "seasonBTTSPercentage_overall"],
                    "over_2_5_pct": ["over_2_5_percentage", "seasonOver25Percentage_overall"],
                    "home_played": ["matches_played_home", "seasonMatchesPlayed_home"],
                    "home_wins": ["home_wins", "seasonWinsNum_home"],
                    "home_draws": ["home_draws", "seasonDrawsNum_home"],
                    "home_losses": ["home_losses", "seasonLossesNum_home"],
                    "home_goals_scored": ["goals_scored_home", "seasonGoals_home"],
                    "home_goals_conceded": ["goals_conceded_home", "seasonConceded_home"],
                    "away_played": ["matches_played_away", "seasonMatchesPlayed_away"],
                    "away_wins": ["away_wins", "seasonWinsNum_away"],
                    "away_draws": ["away_draws", "seasonDrawsNum_away"],
                    "away_losses": ["away_losses", "seasonLossesNum_away"],
                    "away_goals_scored": ["goals_scored_away", "seasonGoals_away"],
                    "away_goals_conceded": ["goals_conceded_away", "seasonConceded_away"],
                    "cards_total": ["cards_total", "seasonCrdYNum_overall", "CrdY"],
                    "yellow_cards": ["yellow_cards", "seasonCrdYNum_overall", "CrdY"],
                    "red_cards": ["red_cards", "seasonCrdRNum_overall", "CrdR"],
                    "over_3_5_cards_pct": ["over_3_5_cards_percentage"],
                    "corners_total": ["corners_total"],
                    "corners_for": ["corners_for", "seasonCornersFor_overall", "CK"],
                    "corners_against": ["corners_against", "seasonCornersAgainst_overall"],
                    "over_9_5_corners_pct": ["over_9_5_corners_percentage"],
                }
                
                # Extract fields using mapping
                for stat_name, api_keys in field_mapping.items():
                    for key in api_keys:
                        if key in raw_stats:
                            value = raw_stats[key]
                            # Validate and convert value
                            if value is not None and value != 'N/A':
                                try:
                                    stats[stat_name] = float(value)
                                    break  # Found valid value, stop looking
                                except (ValueError, TypeError):
                                    pass  # Continue to next key if value can't be converted
        
        # Try to get PPDA from advanced_stats if available
        if "advanced_stats" in api_data and team_type in api_data["advanced_stats"]:
            adv_stats = api_data["advanced_stats"][team_type]
            ppda_keys = ["ppda", "passes_per_defensive_action"]
            for key in ppda_keys:
                if key in adv_stats and adv_stats[key] is not None:
                    try:
                        stats["ppda"] = float(adv_stats[key])
                        break
                    except (ValueError, TypeError):
                        pass
        
        # Calculate derived statistics
        # Example: if we have enough games played, calculate per-game stats
        if stats["played"] > 0:
            if stats["cards_total"] > 0:
                stats["cards_per_game"] = round(stats["cards_total"] / stats["played"], 2)
            if stats["corners_for"] > 0 or stats["corners_against"] > 0:
                stats["corners_total"] = stats["corners_for"] + stats["corners_against"]
                stats["corners_per_game"] = round(stats["corners_total"] / stats["played"], 2)
    
    return stats

def extract_expanded_h2h(api_data):
    """
    Extract comprehensive head-to-head data.
    
    Args:
        api_data (dict): Original API data
        
    Returns:
        dict: Complete H2H data
    """
    h2h = {
        "total_matches": 0,
        "home_wins": 0,
        "away_wins": 0,
        "draws": 0,
        "over_2_5_pct": 0,
        "btts_pct": 0,
        "avg_cards": 0,
        "avg_corners": 0,
        "recent_matches": []
    }
    
    if not api_data:
        return h2h
    
    # Check for H2H data in different locations
    h2h_data = None
    
    # Direct h2h property
    if "head_to_head" in api_data:
        h2h_data = api_data["head_to_head"]
    # Inside match_details
    elif "match_details" in api_data and api_data["match_details"]:
        if "h2h" in api_data["match_details"]:
            h2h_data = api_data["match_details"]["h2h"]
    
    # If we found H2H data, extract it
    if h2h_data and isinstance(h2h_data, dict):
        # Map API fields to our fields
        field_mapping = {
            "total_matches": ["total_matches", "matches"],
            "home_wins": ["home_wins"],
            "away_wins": ["away_wins"],
            "draws": ["draws"],
            "over_2_5_pct": ["over_2_5_percentage"],
            "btts_pct": ["btts_percentage"],
            "avg_cards": ["average_cards"],
            "avg_corners": ["average_corners"]
        }
        
        # Extract each field
        for h2h_field, api_keys in field_mapping.items():
            for key in api_keys:
                if key in h2h_data and h2h_data[key] is not None:
                    try:
                        h2h[h2h_field] = float(h2h_data[key])
                        break
                    except (ValueError, TypeError):
                        pass
        
        # Extract recent matches if available
        if "matches" in h2h_data and isinstance(h2h_data["matches"], list):
            h2h["recent_matches"] = h2h_data["matches"][:5]  # Take only the 5 most recent
    
    return h2h

def extract_form_string(api_data, team_type):
    """
    Extrai forma de um time de várias fontes possíveis nos dados da API.
    Versão otimizada que prioriza team_last_matches.
    
    Args:
        api_data (dict): Dados brutos da API
        team_type (str): "home" ou "away"
        
    Returns:
        str: String de forma como "WDLWD" ou None se não encontrada
    """
    import logging
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    # Fonte 1: team_last_matches (melhor fonte)
    if "team_last_matches" in api_data and team_type in api_data["team_last_matches"]:
        matches = api_data["team_last_matches"][team_type]
        if isinstance(matches, list) and len(matches) > 0:
            form = ""
            # Apenas os 5 jogos mais recentes (os primeiros na lista)
            for match in matches[:5]:
                if isinstance(match, dict) and "result" in match:
                    form += match["result"]
            
            if form and len(form) > 0:
                logger.info(f"Forma extraída de team_last_matches.{team_type}: {form}")
                return form[:5]  # Garantir que só temos 5 caracteres
    
    # Fonte 2: team_form (outra fonte comum)
    if "team_form" in api_data and team_type in api_data["team_form"]:
        form_data = api_data["team_form"][team_type]
        if isinstance(form_data, list) and len(form_data) > 0:
            form = ""
            for match in form_data[:5]:
                if isinstance(match, dict) and "result" in match:
                    form += match["result"]
            
            if form and len(form) > 0:
                logger.info(f"Forma extraída de team_form.{team_type}: {form}")
                return form[:5]
    
    # Fonte 3: recent_form nos dados do time
    if "team_stats" in api_data and team_type in api_data["team_stats"]:
        team_stats = api_data["team_stats"][team_type]
        if "recent_form" in team_stats and isinstance(team_stats["recent_form"], str):
            form = team_stats["recent_form"]
            if len(form) > 0:
                logger.info(f"Forma extraída de team_stats.{team_type}.recent_form: {form}")
                return form[:5]
    
    # Fonte 4: formRun_overall nos dados do time
    if "team_info" in api_data and team_type in api_data["team_info"]:
        team_info = api_data["team_info"][team_type]
        if "formRun_overall" in team_info and isinstance(team_info["formRun_overall"], str):
            form = team_info["formRun_overall"]
            if len(form) > 0:
                logger.info(f"Forma extraída de team_info.{team_type}.formRun_overall: {form}")
                return form[:5]
    
    # Não foi possível encontrar dados de forma
    logger.warning(f"Não foi possível extrair forma para {team_type}")
    return None
def ensure_critical_fields(optimized_data, home_team_name, away_team_name):
    """
    Garante que campos críticos existam na estrutura de dados, sem adicionar valores fictícios.
    
    Args:
        optimized_data (dict): Estrutura de dados a verificar
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
    """
    # Garantir que as estruturas básicas existam
    if "home_team" not in optimized_data:
        optimized_data["home_team"] = {}
        
    if "away_team" not in optimized_data:
        optimized_data["away_team"] = {}
        
    if "h2h" not in optimized_data:
        optimized_data["h2h"] = {}
        
    # Garantir apenas que o campo form exista para análise de forma
    if "form" not in optimized_data["home_team"]:
        optimized_data["home_team"]["form"] = ""
        
    if "form" not in optimized_data["away_team"]:
        optimized_data["away_team"]["form"] = ""

def ensure_recent_matches(formatted_data, home_team_name, away_team_name):
    """
    Ensure both teams have recent matches data WITHOUT using fictional English teams
    
    Args:
        formatted_data (dict): Target data structure
        home_team_name (str): Name of home team
        away_team_name (str): Name of away team
    """
    # Generate minimal data structure for home team if needed
    if not formatted_data["home_team"]["recent_matches"]:
        form = formatted_data["home_team"]["form"]
        
        # If no form data, use "?????"
        if not form:
            form = "?????"
            formatted_data["home_team"]["form"] = form
            
        # Create empty structure without fictional teams
        recent_matches = []
        for i in range(min(5, len(form))):
            result = form[i] if i < len(form) else "?"
            recent_matches.append({
                "opponent": "Sin datos",  # "No data" in Spanish, more appropriate for South American teams
                "result": result,
                "score": "0-0",
                "date": f"2025-03-{10-i:02d}"
            })
            
        formatted_data["home_team"]["recent_matches"] = recent_matches
    
    # Generate minimal data structure for away team if needed
    if not formatted_data["away_team"]["recent_matches"]:
        form = formatted_data["away_team"]["form"]
        
        # If no form data, use "?????"
        if not form:
            form = "?????"
            formatted_data["away_team"]["form"] = form
            
        # Create empty structure without fictional teams
        recent_matches = []
        for i in range(min(5, len(form))):
            result = form[i] if i < len(form) else "?"
            recent_matches.append({
                "opponent": "Sin datos",  # "No data" in Spanish, more appropriate for South American teams
                "result": result,
                "score": "0-0",
                "date": f"2025-03-{10-i:02d}"
            })
            
        formatted_data["away_team"]["recent_matches"] = recent_matches
    
    # Generate minimal H2H recent matches if needed
    if not formatted_data["h2h"]["recent_matches"]:
        # Create minimal structure for h2h matches
        total_matches = int(formatted_data["h2h"]["total_matches"])
        
        if total_matches > 0:
            recent_matches = []
            
            for i in range(min(5, total_matches)):
                recent_matches.append({
                    "date": f"Sin fecha",
                    "home_team": home_team_name,
                    "away_team": away_team_name,
                    "score": "Sin datos",
                    "competition": "Sin datos"
                })
                
            formatted_data["h2h"]["recent_matches"] = recent_matches

def extract_team_data(api_data, formatted_data, team_type):
    """
    Extrai dados completos de um time a partir dos dados da API
    
    Args:
        api_data (dict): Dados originais da API
        formatted_data (dict): Estrutura de dados alvo para preencher
        team_type (str): "home" ou "away"
    """
    team_key = f"{team_type}_team"
    target_dict = formatted_data[team_key]
    
    # Verifica se temos dados básicos para o time
    if "basic_stats" in api_data and team_key in api_data["basic_stats"]:
        team_data = api_data["basic_stats"][team_key]
        
        # Extrair estatísticas de diferentes possíveis locais
        stats_data = {}
        
        # Caso 1: stats direto no objeto
        if "stats" in team_data and isinstance(team_data["stats"], dict):
            stats_data = team_data["stats"]
        
        # Caso 2: stats aninhado (stats.stats)
        elif "stats" in team_data and isinstance(team_data["stats"], dict) and "stats" in team_data["stats"]:
            stats_data = team_data["stats"]["stats"]
        
        # Caso 3: stats diretamente no time_data
        if not stats_data:
            for key in ["played", "seasonMatchesPlayed_overall", "wins", "goals_scored"]:
                if key in team_data:
                    stats_data = team_data
                    break
        
        # Extrair todos os campos de estatísticas disponíveis
        if stats_data:
            # Mapeamento de campo da API para campo no nosso formato
            field_mapping = {
                # Estatísticas Gerais
                "played": ["played", "seasonMatchesPlayed_overall", "matches_played", "MP"],
                "seasonMatchesPlayed_overall": ["seasonMatchesPlayed_overall", "matches_played", "MP"],
                "wins": ["wins", "seasonWinsNum_overall", "W"],
                "seasonWinsNum_overall": ["seasonWinsNum_overall", "wins", "W"],
                "draws": ["draws", "seasonDrawsNum_overall", "D"],
                "seasonDrawsNum_overall": ["seasonDrawsNum_overall", "draws", "D"],
                "losses": ["losses", "seasonLossesNum_overall", "L"],
                "seasonLossesNum_overall": ["seasonLossesNum_overall", "losses", "L"],
                "win_pct": ["win_percentage", "winPercentage"],
                "draw_pct": ["draw_percentage", "drawPercentage"],
                "loss_pct": ["loss_percentage", "lossPercentage"],
                "seasonPPG_overall": ["seasonPPG_overall", "ppg", "points_per_game"],
                "seasonRecentPPG": ["seasonRecentPPG", "recent_ppg"],
                "leaguePosition_overall": ["leaguePosition_overall", "league_position"],
                
                # Estatísticas Casa/Fora
                "home_played": ["home_played", "seasonMatchesPlayed_home", "matches_played_home"],
                "away_played": ["away_played", "seasonMatchesPlayed_away", "matches_played_away"],
                "seasonMatchesPlayed_home": ["seasonMatchesPlayed_home", "home_played", "matches_played_home"],
                "seasonMatchesPlayed_away": ["seasonMatchesPlayed_away", "away_played", "matches_played_away"],
                "home_wins": ["home_wins", "seasonWinsNum_home", "wins_home"],
                "away_wins": ["away_wins", "seasonWinsNum_away", "wins_away"],
                "seasonWinsNum_home": ["seasonWinsNum_home", "home_wins", "wins_home"],
                "seasonWinsNum_away": ["seasonWinsNum_away", "away_wins", "wins_away"],
                "home_draws": ["home_draws", "seasonDrawsNum_home", "draws_home"],
                "away_draws": ["away_draws", "seasonDrawsNum_away", "draws_away"],
                "seasonDrawsNum_home": ["seasonDrawsNum_home", "home_draws", "draws_home"],
                "seasonDrawsNum_away": ["seasonDrawsNum_away", "away_draws", "draws_away"],
                "home_losses": ["home_losses", "seasonLossesNum_home", "losses_home"],
                "away_losses": ["away_losses", "seasonLossesNum_away", "losses_away"],
                "seasonLossesNum_home": ["seasonLossesNum_home", "home_losses", "losses_home"],
                "seasonLossesNum_away": ["seasonLossesNum_away", "away_losses", "losses_away"],
                "seasonPPG_home": ["seasonPPG_home", "home_ppg", "points_per_game_home"],
                "seasonPPG_away": ["seasonPPG_away", "away_ppg", "points_per_game_away"],
                "leaguePosition_home": ["leaguePosition_home", "home_league_position"],
                "leaguePosition_away": ["leaguePosition_away", "away_league_position"],
                "home_form": ["home_form", "formRun_home", "current_form_home"],
                "away_form": ["away_form", "formRun_away", "current_form_away"],
                "formRun_home": ["formRun_home", "home_form", "current_form_home"],
                "formRun_away": ["formRun_away", "away_form", "current_form_away"],
                
                # Estatísticas de Gols
                "goals_scored": ["goals_scored", "seasonScoredNum_overall", "scored", "GF"],
                "seasonScoredNum_overall": ["seasonScoredNum_overall", "goals_scored", "scored", "GF"],
                "goals_conceded": ["goals_conceded", "seasonConcededNum_overall", "conceded", "GA"],
                "seasonConcededNum_overall": ["seasonConcededNum_overall", "goals_conceded", "conceded", "GA"],
                "home_goals_scored": ["home_goals_scored", "seasonScoredNum_home", "goals_scored_home"],
                "seasonScoredNum_home": ["seasonScoredNum_home", "home_goals_scored", "goals_scored_home"],
                "away_goals_scored": ["away_goals_scored", "seasonScoredNum_away", "goals_scored_away"],
                "seasonScoredNum_away": ["seasonScoredNum_away", "away_goals_scored", "goals_scored_away"],
                "home_goals_conceded": ["home_goals_conceded", "seasonConcededNum_home", "goals_conceded_home"],
                "seasonConcededNum_home": ["seasonConcededNum_home", "home_goals_conceded", "goals_conceded_home"],
                "away_goals_conceded": ["away_goals_conceded", "seasonConcededNum_away", "goals_conceded_away"],
                "seasonConcededNum_away": ["seasonConcededNum_away", "away_goals_conceded", "goals_conceded_away"],
                "goals_per_game": ["goals_per_game", "gpg", "goals_per_match"],
                "conceded_per_game": ["conceded_per_game", "cpg", "conceded_per_match"],
                "seasonGoalsTotal_overall": ["seasonGoalsTotal_overall", "total_goals"],
                "seasonGoalsTotal_home": ["seasonGoalsTotal_home", "total_goals_home"],
                "seasonGoalsTotal_away": ["seasonGoalsTotal_away", "total_goals_away"],
                "clean_sheets_pct": ["clean_sheets_pct", "clean_sheet_percentage", "cs_pct"],
                "seasonCSPercentage_overall": ["seasonCSPercentage_overall", "clean_sheet_percentage", "cs_pct"],
                "seasonCS_overall": ["seasonCS_overall", "clean_sheets", "cs"],
                "seasonCS_home": ["seasonCS_home", "home_clean_sheets", "cs_home"],
                "seasonCS_away": ["seasonCS_away", "away_clean_sheets", "cs_away"],
                "btts_pct": ["btts_pct", "btts_percentage", "both_teams_scored_pct"],
                "seasonBTTSPercentage_overall": ["seasonBTTSPercentage_overall", "btts_percentage", "both_teams_to_score_pct"],
                "over_2_5_pct": ["over_2_5_pct", "over_2_5_percentage", "o25_pct"],
                "seasonOver25Percentage_overall": ["seasonOver25Percentage_overall", "over_2_5_percentage", "o25_pct"],
                
                # Expected Goals
                "xg": ["xg", "xG", "expected_goals", "xg_for"],
                "xg_for_overall": ["xg_for_overall", "xg", "xG", "expected_goals"],
                "xga": ["xga", "xGA", "expected_goals_against", "xg_against"],
                "xg_against_overall": ["xg_against_overall", "xga", "xGA", "expected_goals_against"],
                "home_xg": ["home_xg", "xg_home", "xg_for_home"],
                "xg_for_home": ["xg_for_home", "home_xg", "xg_home"],
                "away_xg": ["away_xg", "xg_away", "xg_for_away"],
                "xg_for_away": ["xg_for_away", "away_xg", "xg_away"],
                "home_xga": ["home_xga", "xga_home", "xg_against_home"],
                "xg_against_home": ["xg_against_home", "home_xga", "xga_home"],
                "away_xga": ["away_xga", "xga_away", "xg_against_away"],
                "xg_against_away": ["xg_against_away", "away_xga", "xga_away"],
                "xg_for_avg_overall": ["xg_for_avg_overall", "xg_per_game", "expected_goals_per_game"],
                "xg_for_avg_home": ["xg_for_avg_home", "xg_per_game_home", "expected_goals_per_game_home"],
                "xg_for_avg_away": ["xg_for_avg_away", "xg_per_game_away", "expected_goals_per_game_away"],
                "xg_against_avg_overall": ["xg_against_avg_overall", "xga_per_game", "expected_goals_against_per_game"],
                "xg_against_avg_home": ["xg_against_avg_home", "xga_per_game_home", "expected_goals_against_per_game_home"],
                "xg_against_avg_away": ["xg_against_avg_away", "xga_per_game_away", "expected_goals_against_per_game_away"],
                
                # Estatísticas de Cartões
                "cards_per_game": ["cards_per_game", "cards_avg", "avg_cards"],
                "cardsAVG_overall": ["cardsAVG_overall", "cards_per_game", "cards_avg"],
                "home_cards_per_game": ["home_cards_per_game", "cards_per_game_home", "home_cards_avg"],
                "cardsAVG_home": ["cardsAVG_home", "home_cards_per_game", "cards_per_game_home"],
                "away_cards_per_game": ["away_cards_per_game", "cards_per_game_away", "away_cards_avg"],
                "cardsAVG_away": ["cardsAVG_away", "away_cards_per_game", "cards_per_game_away"],
                "cardsTotal_overall": ["cardsTotal_overall", "total_cards", "cards_total"],
                "cardsTotal_home": ["cardsTotal_home", "total_cards_home", "cards_total_home"],
                "cardsTotal_away": ["cardsTotal_away", "total_cards_away", "cards_total_away"],
                "yellow_cards": ["yellow_cards", "yellows", "cards_yellow"],
                "red_cards": ["red_cards", "reds", "cards_red"],
                "over_3_5_cards_pct": ["over_3_5_cards_pct", "over_3_5_cards_percentage", "o35_cards_pct"],
                
                # Estatísticas de Escanteios
                "corners_per_game": ["corners_per_game", "corners_avg", "avg_corners"],
                "cornersTotalAVG_overall": ["cornersTotalAVG_overall", "corners_per_game", "corners_avg"],
                "home_corners_per_game": ["home_corners_per_game", "corners_per_game_home", "home_corners_avg"],
                "cornersTotalAVG_home": ["cornersTotalAVG_home", "home_corners_per_game", "corners_per_game_home"],
                "away_corners_per_game": ["away_corners_per_game", "corners_per_game_away", "away_corners_avg"],
                "cornersTotalAVG_away": ["cornersTotalAVG_away", "away_corners_per_game", "corners_per_game_away"],
                "corners_for": ["corners_for", "cornersTotal_overall", "corners"],
                "cornersTotal_overall": ["cornersTotal_overall", "corners_for", "corners"],
                "corners_against": ["corners_against", "cornersAgainst_overall", "corners_against_total"],
                "cornersAgainst_overall": ["cornersAgainst_overall", "corners_against", "corners_against_total"],
                "cornersAVG_overall": ["cornersAVG_overall", "corners_for_avg", "corners_for_per_game"],
                "cornersAVG_home": ["cornersAVG_home", "corners_for_avg_home", "corners_for_per_game_home"],
                "cornersAVG_away": ["cornersAVG_away", "corners_for_avg_away", "corners_for_per_game_away"],
                "cornersAgainstAVG_overall": ["cornersAgainstAVG_overall", "corners_against_avg", "corners_against_per_game"],
                "cornersAgainstAVG_home": ["cornersAgainstAVG_home", "corners_against_avg_home", "corners_against_per_game_home"],
                "cornersAgainstAVG_away": ["cornersAgainstAVG_away", "corners_against_avg_away", "corners_against_per_game_away"],
                "over_9_5_corners_pct": ["over_9_5_corners_pct", "over_9_5_corners_percentage", "o95_corners_pct"],
                
                # Estatísticas de Chutes
                "shotsAVG_overall": ["shotsAVG_overall", "shots_per_game", "shots_avg"],
                "shotsAVG_home": ["shotsAVG_home", "shots_per_game_home", "shots_avg_home"],
                "shotsAVG_away": ["shotsAVG_away", "shots_per_game_away", "shots_avg_away"],
                "shotsOnTargetAVG_overall": ["shotsOnTargetAVG_overall", "shots_on_target_per_game", "sot_avg"],
                "shotsOnTargetAVG_home": ["shotsOnTargetAVG_home", "shots_on_target_per_game_home", "sot_avg_home"],
                "shotsOnTargetAVG_away": ["shotsOnTargetAVG_away", "shots_on_target_per_game_away", "sot_avg_away"],
                
                # Posse de Bola
                "possession": ["possession", "possessionAVG_overall", "possession_avg"],
                "possessionAVG_overall": ["possessionAVG_overall", "possession", "possession_avg"],
                "home_possession": ["home_possession", "possessionAVG_home", "possession_home"],
                "possessionAVG_home": ["possessionAVG_home", "home_possession", "possession_home"],
                "away_possession": ["away_possession", "possessionAVG_away", "possession_away"],
                "possessionAVG_away": ["possessionAVG_away", "away_possession", "possession_away"],
            }
            
            # Extrai cada campo, buscando em múltiplos nomes possíveis
            for target_field, source_fields in field_mapping.items():
                for field in source_fields:
                    if field in stats_data:
                        value = stats_data[field]
                        try:
                            # Caso especial para campos de texto como form
                            if target_field in ["form", "home_form", "away_form", "formRun_overall", "formRun_home", "formRun_away"]:
                                if isinstance(value, str):
                                    target_dict[target_field] = value
                                break
                            # Para valores numéricos
                            elif value is not None and value != 'N/A':
                                target_dict[target_field] = float(value)
                                break
                        except (ValueError, TypeError):
                            # Ignorar conversão falha
                            pass
    
    # Buscar em advanced_stats
    if "advanced_stats" in api_data and team_type in api_data["advanced_stats"]:
        adv_stats = api_data["advanced_stats"][team_type]
        
        # Mapeamento para stats avançadas
        adv_mapping = {
            "xg": ["xg", "xG", "expected_goals"],
            "xga": ["xga", "xGA", "expected_goals_against"],
            "ppda": ["ppda", "passes_per_defensive_action", "PPDA"],
            "possession": ["possession", "possessionAVG", "possession_avg"]
        }
        
        for target_field, source_fields in adv_mapping.items():
            for field in source_fields:
                if field in adv_stats and adv_stats[field] is not None:
                    try:
                        target_dict[target_field] = float(adv_stats[field])
                        break
                    except (ValueError, TypeError):
                        pass
def get_value(data_dict, possible_keys, default=0):
    """
    Helper function to get a value from a dictionary using multiple possible keys
    
    Args:
        data_dict (dict): Dictionary to extract from
        possible_keys (list): List of possible keys to try
        default: Default value if not found
        
    Returns:
        Value from dictionary or default
    """
    if not data_dict or not isinstance(data_dict, dict):
        return default
    
    for key in possible_keys:
        if key in data_dict:
            # Handle 'N/A' and other non-numeric values
            value = data_dict[key]
            if value == 'N/A' or value is None:
                return default
            
            # Try to convert to float
            try:
                return float(value)
            except (ValueError, TypeError):
                pass
    
    return default

def get_nested_value(data_dict, possible_keys, default=0):
    """
    Get a value from a nested dictionary using multiple possible keys
    
    Args:
        data_dict (dict): Dictionary to search
        possible_keys (list): List of possible keys to try
        default: Default value if not found
        
    Returns:
        Value from dictionary or default
    """
    if not data_dict or not isinstance(data_dict, dict):
        return default
    
    for key in possible_keys:
        if key in data_dict:
            # Handle 'N/A' and other non-numeric values
            value = data_dict[key]
            if value == 'N/A' or value is None:
                return default
            
            # Try to convert to float
            try:
                return float(value)
            except (ValueError, TypeError):
                pass
    
    return default

def round_stat(value, precision=0):
    """
    Round a statistical value to reduce data size
    
    Args:
        value: The value to round
        precision (int): Decimal precision
        
    Returns:
        int or float: Rounded value
    """
    if value is None:
        return 0
        
    try:
        if precision == 0:
            return int(round(float(value), 0))
        else:
            return round(float(value), precision)
    except (ValueError, TypeError):
        return 0

def transform_to_optimized_data(api_data, home_team_name, away_team_name, selected_markets=None):
    """
    Transform API data into a more optimized, flattened structure
    
    Args:
        api_data (dict): Original API data from FootyStats
        home_team_name (str): Name of home team
        away_team_name (str): Name of away team
        selected_markets (dict, optional): Dictionary of selected markets to filter data
        
    Returns:
        dict: Optimized data structure
    """
    import logging
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    try:
        # Initialize the optimized structure - USING THE EXPECTED FORMAT
        optimized_data = {
            "match_info": {
                "home_team": home_team_name,
                "away_team": away_team_name,
                "league": "",
                "league_id": None
            },
            "home_team": {
                # Basic stats
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_scored": 0,
                "goals_conceded": 0,
                "clean_sheets_pct": 0,
                "btts_pct": 0,
                "over_2_5_pct": 0,
                # Home specific
                "home_played": 0,
                "home_wins": 0,
                "home_draws": 0,
                "home_losses": 0,
                "home_goals_scored": 0,
                "home_goals_conceded": 0,
                # Advanced
                "xg": 0,
                "xga": 0,
                "ppda": 0,
                "possession": 0,
                # Card stats
                "cards_total": 0,
                "cards_per_game": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "over_3_5_cards_pct": 0,
                "home_cards_per_game": 0,
                "away_cards_per_game": 0,
                # Corner stats
                "corners_total": 0,
                "corners_per_game": 0,
                "corners_for": 0,
                "corners_against": 0,
                "over_9_5_corners_pct": 0,
                "home_corners_per_game": 0,
                "away_corners_per_game": 0,
                # Form (simplified)
                "form": "",
                "recent_matches": []
            },
            "away_team": {
                # Copy of the same structure for away team
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_scored": 0,
                "goals_conceded": 0,
                "clean_sheets_pct": 0,
                "btts_pct": 0,
                "over_2_5_pct": 0,
                # Away specific
                "away_played": 0,
                "away_wins": 0,
                "away_draws": 0,
                "away_losses": 0,
                "away_goals_scored": 0,
                "away_goals_conceded": 0,
                # Advanced
                "xg": 0,
                "xga": 0,
                "ppda": 0,
                "possession": 0,
                # Card stats
                "cards_total": 0,
                "cards_per_game": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "over_3_5_cards_pct": 0,
                "home_cards_per_game": 0,
                "away_cards_per_game": 0,
                # Corner stats
                "corners_total": 0,
                "corners_per_game": 0,
                "corners_for": 0,
                "corners_against": 0,
                "over_9_5_corners_pct": 0,
                "home_corners_per_game": 0,
                "away_corners_per_game": 0,
                # Form (simplified)
                "form": "",
                "recent_matches": []
            },
            "h2h": {
                "total_matches": 0,
                "home_wins": 0,
                "away_wins": 0,
                "draws": 0,
                "over_2_5_pct": 0,
                "btts_pct": 0,
                "avg_cards": 0,
                "avg_corners": 0,
                "recent_matches": []
            }
        }
        
        # Check if we have valid API data
        if not api_data or not isinstance(api_data, dict):
            logger.error("Invalid API data provided")
            return optimized_data
        
        # Fill in league info
        if "basic_stats" in api_data and "league_id" in api_data["basic_stats"]:
            optimized_data["match_info"]["league_id"] = api_data["basic_stats"]["league_id"]
            
        # Extract home team stats
        home_team_data = {}
        if "basic_stats" in api_data and "home_team" in api_data["basic_stats"]:
            # Get raw data from API
            home_raw = api_data["basic_stats"]["home_team"]
            
            # Extract stats from nested structure
            if "stats" in home_raw:
                if isinstance(home_raw["stats"], dict):
                    # If stats is a direct object
                    home_team_data = home_raw["stats"]
                elif "stats" in home_raw["stats"] and isinstance(home_raw["stats"]["stats"], dict):
                    # If stats is nested deeper
                    home_team_data = home_raw["stats"]["stats"]
            
            # Now extract all stats from the data
            extract_all_stats(optimized_data["home_team"], home_team_data, "home")
            
            # Get PPDA from advanced stats if available
            if "advanced_stats" in api_data and "home" in api_data["advanced_stats"]:
                optimized_data["home_team"]["ppda"] = get_value(api_data["advanced_stats"]["home"], ["ppda", "passes_per_defensive_action"])
        
        # Extract away team stats (similar structure)
        away_team_data = {}
        if "basic_stats" in api_data and "away_team" in api_data["basic_stats"]:
            # Get raw data from API
            away_raw = api_data["basic_stats"]["away_team"]
            
            # Extract stats from nested structure
            if "stats" in away_raw:
                if isinstance(away_raw["stats"], dict):
                    # If stats is a direct object
                    away_team_data = away_raw["stats"]
                elif "stats" in away_raw["stats"] and isinstance(away_raw["stats"]["stats"], dict):
                    # If stats is nested deeper
                    away_team_data = away_raw["stats"]["stats"]
            
            # Now extract all stats from the data
            extract_all_stats(optimized_data["away_team"], away_team_data, "away")
            
            # Get PPDA from advanced stats if available
            if "advanced_stats" in api_data and "away" in api_data["advanced_stats"]:
                optimized_data["away_team"]["ppda"] = get_value(api_data["advanced_stats"]["away"], ["ppda", "passes_per_defensive_action"])
        
        # Extract head-to-head data
        if "head_to_head" in api_data:
            h2h_data = api_data["head_to_head"]
            
            optimized_data["h2h"]["total_matches"] = get_value(h2h_data, ["total_matches"])
            optimized_data["h2h"]["home_wins"] = get_value(h2h_data, ["home_wins"])
            optimized_data["h2h"]["away_wins"] = get_value(h2h_data, ["away_wins"])
            optimized_data["h2h"]["draws"] = get_value(h2h_data, ["draws"])
            optimized_data["h2h"]["over_2_5_pct"] = get_value(h2h_data, ["over_2_5_percentage"])
            optimized_data["h2h"]["btts_pct"] = get_value(h2h_data, ["btts_percentage"])
            optimized_data["h2h"]["avg_cards"] = get_value(h2h_data, ["average_cards"])
            optimized_data["h2h"]["avg_corners"] = get_value(h2h_data, ["average_corners"])
        
        # Extract form data
        if "team_form" in api_data:
            # Home team form
            if "home" in api_data["team_form"] and isinstance(api_data["team_form"]["home"], list):
                form_list = []
                form_string = ""
                
                for match in api_data["team_form"]["home"][:5]:
                    result = match.get("result", "?")
                    form_list.append(result)
                    form_string += result
                
                optimized_data["home_team"]["form"] = form_string
                optimized_data["home_team"]["recent_matches"] = api_data["team_form"]["home"][:5]
            
            # Away team form
            if "away" in api_data["team_form"] and isinstance(api_data["team_form"]["away"], list):
                form_list = []
                form_string = ""
                
                for match in api_data["team_form"]["away"][:5]:
                    result = match.get("result", "?")
                    form_list.append(result)
                    form_string += result
                
                optimized_data["away_team"]["form"] = form_string
                optimized_data["away_team"]["recent_matches"] = api_data["team_form"]["away"][:5]
        
        # Ensure all critical fields have reasonable values
        ensure_critical_fields(optimized_data, home_team_name, away_team_name)
        
        logger.info(f"Data structure optimized successfully for {home_team_name} vs {away_team_name}")
        return optimized_data
        
    except Exception as e:
        logger.error(f"Error transforming data to optimized format: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return optimized_data  # Return the default structure

def extract_all_stats(target_dict, data_dict, team_type):
    """
    Extract all stats from data dictionary to target dictionary
    
    Args:
        target_dict (dict): Target dictionary to populate
        data_dict (dict): Source data dictionary
        team_type (str): "home" or "away"
    """
    # Basic stats
    target_dict["played"] = get_value(data_dict, ["matches_played", "seasonMatchesPlayed_overall", "MP"])
    target_dict["wins"] = get_value(data_dict, ["wins", "seasonWinsNum_overall", "W"])
    target_dict["draws"] = get_value(data_dict, ["draws", "seasonDrawsNum_overall", "D"])
    target_dict["losses"] = get_value(data_dict, ["losses", "seasonLossesNum_overall", "L"])
    target_dict["goals_scored"] = get_value(data_dict, ["goals_scored", "seasonGoals_overall", "Gls"])
    target_dict["goals_conceded"] = get_value(data_dict, ["goals_conceded", "seasonConceded_overall", "GA"])
    
    # Goal trends
    target_dict["clean_sheets_pct"] = get_value(data_dict, ["clean_sheet_percentage", "seasonCSPercentage_overall"])
    target_dict["btts_pct"] = get_value(data_dict, ["btts_percentage", "seasonBTTSPercentage_overall"])
    target_dict["over_2_5_pct"] = get_value(data_dict, ["over_2_5_percentage", "seasonOver25Percentage_overall"])
    
    # Home/Away specific
    prefix = team_type  # "home" or "away"
    target_dict[f"{prefix}_played"] = get_value(data_dict, [f"matches_played_{prefix}", f"seasonMatchesPlayed_{prefix}"])
    target_dict[f"{prefix}_wins"] = get_value(data_dict, [f"{prefix}_wins", f"seasonWinsNum_{prefix}"])
    target_dict[f"{prefix}_draws"] = get_value(data_dict, [f"{prefix}_draws", f"seasonDrawsNum_{prefix}"])
    target_dict[f"{prefix}_losses"] = get_value(data_dict, [f"{prefix}_losses", f"seasonLossesNum_{prefix}"])
    target_dict[f"{prefix}_goals_scored"] = get_value(data_dict, [f"goals_scored_{prefix}", f"seasonGoals_{prefix}"])
    target_dict[f"{prefix}_goals_conceded"] = get_value(data_dict, [f"goals_conceded_{prefix}", f"seasonConceded_{prefix}"])
    
    # Advanced stats
    target_dict["xg"] = get_value(data_dict, ["xG", "xg", "xg_for_overall"])
    target_dict["xga"] = get_value(data_dict, ["xGA", "xga", "xg_against_avg_overall"])
    target_dict["possession"] = get_value(data_dict, ["possession", "possessionAVG_overall", "Poss"])
    
    # Card stats
    target_dict["cards_total"] = get_value(data_dict, ["cards_total", "seasonCrdYNum_overall", "CrdY"]) + get_value(data_dict, ["seasonCrdRNum_overall", "CrdR"], 0)
    target_dict["yellow_cards"] = get_value(data_dict, ["yellow_cards", "seasonCrdYNum_overall", "CrdY"])
    target_dict["red_cards"] = get_value(data_dict, ["red_cards", "seasonCrdRNum_overall", "CrdR"])
    target_dict["over_3_5_cards_pct"] = get_value(data_dict, ["over_3_5_cards_percentage"])
    
    # If matches played exists, calculate per-game averages
    matches_played = target_dict["played"]
    if matches_played > 0:
        target_dict["cards_per_game"] = round(target_dict["cards_total"] / matches_played, 2)
        
    # Corner stats
    target_dict["corners_for"] = get_value(data_dict, ["corners_for", "seasonCornersFor_overall", "CK"])
    target_dict["corners_against"] = get_value(data_dict, ["corners_against", "seasonCornersAgainst_overall"])
    target_dict["corners_total"] = target_dict["corners_for"] + target_dict["corners_against"]
    target_dict["over_9_5_corners_pct"] = get_value(data_dict, ["over_9_5_corners_percentage"])
    
    # Calculate per-game averages for corners if matches played
    if matches_played > 0:
        target_dict["corners_per_game"] = round(target_dict["corners_total"] / matches_played, 2)

def adapt_api_data_for_prompt(complete_analysis):
    """
    Adapta os dados coletados da API para o formato esperado pelo format_enhanced_prompt
    
    Args:
        complete_analysis (dict): Dados coletados pelo enhanced_api_client
        
    Returns:
        dict: Dados formatados para o format_enhanced_prompt
    """
    try:
        # Use a função transform_to_optimized_data para garantir a estrutura correta
        return transform_to_optimized_data(
            complete_analysis, 
            complete_analysis.get("basic_stats", {}).get("home_team", {}).get("name", "Home Team"),
            complete_analysis.get("basic_stats", {}).get("away_team", {}).get("name", "Away Team")
        )
    except Exception as e:
        logger.error(f"Erro ao adaptar dados para prompt: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
def transform_api_data(api_data, home_team_name, away_team_name, selected_markets=None):
    """
    Transforma os dados da API no formato completo requerido pelo agente de IA,
    garantindo que TODOS os campos listados no documento sejam incluídos.
    
    Args:
        api_data (dict): Dados originais da API FootyStats
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
        selected_markets (dict, optional): Dicionário de mercados selecionados
        
    Returns:
        dict: Dados no formato completo requerido
    """
    import logging
    import traceback
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    # Inicializa a estrutura de dados completa requerida
    formatted_data = {
        "match_info": {
            "home_team": home_team_name,
            "away_team": away_team_name,
            "league": "",
            "league_id": None
        },
        "home_team": {
            # Estatísticas Gerais
            "played": 0, 
            "seasonMatchesPlayed_overall": 0,
            "wins": 0, 
            "seasonWinsNum_overall": 0,
            "draws": 0, 
            "seasonDrawsNum_overall": 0,
            "losses": 0, 
            "seasonLossesNum_overall": 0,
            "win_pct": 0,
            "draw_pct": 0,
            "loss_pct": 0,
            "form": "?????", 
            "formRun_overall": "?????",
            "seasonPPG_overall": 0,
            "seasonRecentPPG": 0,
            "leaguePosition_overall": 0,
            
            # Estatísticas em Casa
            "home_played": 0, 
            "seasonMatchesPlayed_home": 0,
            "home_wins": 0, 
            "seasonWinsNum_home": 0,
            "home_draws": 0, 
            "seasonDrawsNum_home": 0,
            "home_losses": 0, 
            "seasonLossesNum_home": 0,
            "home_form": "?????", 
            "formRun_home": "?????",
            "seasonPPG_home": 0,
            "leaguePosition_home": 0,
            
            # Estatísticas de Gols
            "goals_scored": 0, 
            "seasonScoredNum_overall": 0,
            "goals_conceded": 0, 
            "seasonConcededNum_overall": 0,
            "home_goals_scored": 0, 
            "seasonScoredNum_home": 0,
            "home_goals_conceded": 0, 
            "seasonConcededNum_home": 0,
            "goals_per_game": 0,
            "conceded_per_game": 0,
            "seasonGoalsTotal_overall": 0,
            "seasonGoalsTotal_home": 0,
            "clean_sheets_pct": 0, 
            "seasonCSPercentage_overall": 0,
            "seasonCS_overall": 0,
            "seasonCS_home": 0,
            "btts_pct": 0, 
            "seasonBTTSPercentage_overall": 0,
            "over_2_5_pct": 0, 
            "seasonOver25Percentage_overall": 0,
            
            # Expected Goals
            "xg": 0, 
            "xg_for_overall": 0,
            "xga": 0, 
            "xg_against_overall": 0,
            "home_xg": 0, 
            "xg_for_home": 0,
            "home_xga": 0, 
            "xg_against_home": 0,
            "xg_for_avg_overall": 0,
            "xg_for_avg_home": 0,
            "xg_against_avg_overall": 0,
            "xg_against_avg_home": 0,
            
            # Estatísticas de Cartões
            "cards_per_game": 0, 
            "cardsAVG_overall": 0,
            "home_cards_per_game": 0, 
            "cardsAVG_home": 0,
            "cardsTotal_overall": 0,
            "cardsTotal_home": 0,
            "yellow_cards": 0,
            "red_cards": 0,
            "over_3_5_cards_pct": 0,
            
            # Estatísticas de Escanteios
            "corners_per_game": 0, 
            "cornersTotalAVG_overall": 0,
            "home_corners_per_game": 0, 
            "cornersTotalAVG_home": 0,
            "corners_for": 0, 
            "cornersTotal_overall": 0,
            "corners_against": 0, 
            "cornersAgainst_overall": 0,
            "cornersAVG_overall": 0,
            "cornersAVG_home": 0,
            "cornersAgainstAVG_overall": 0,
            "cornersAgainstAVG_home": 0,
            "over_9_5_corners_pct": 0,
            
            # Estatísticas de Chutes
            "shotsAVG_overall": 0,
            "shotsAVG_home": 0,
            "shotsOnTargetAVG_overall": 0,
            "shotsOnTargetAVG_home": 0,
            
            # Posse de Bola
            "possession": 0, 
            "possessionAVG_overall": 0,
            "home_possession": 0, 
            "possessionAVG_home": 0
        },
        "away_team": {
            # Estatísticas Gerais
            "played": 0, 
            "seasonMatchesPlayed_overall": 0,
            "wins": 0, 
            "seasonWinsNum_overall": 0,
            "draws": 0, 
            "seasonDrawsNum_overall": 0,
            "losses": 0, 
            "seasonLossesNum_overall": 0,
            "win_pct": 0,
            "draw_pct": 0,
            "loss_pct": 0,
            "form": "?????", 
            "formRun_overall": "?????",
            "seasonPPG_overall": 0,
            "seasonRecentPPG": 0,
            "leaguePosition_overall": 0,
            
            # Estatísticas Fora
            "away_played": 0, 
            "seasonMatchesPlayed_away": 0,
            "away_wins": 0, 
            "seasonWinsNum_away": 0,
            "away_draws": 0, 
            "seasonDrawsNum_away": 0,
            "away_losses": 0, 
            "seasonLossesNum_away": 0,
            "away_form": "?????", 
            "formRun_away": "?????",
            "seasonPPG_away": 0,
            "leaguePosition_away": 0,
            
            # Estatísticas de Gols
            "goals_scored": 0, 
            "seasonScoredNum_overall": 0,
            "goals_conceded": 0, 
            "seasonConcededNum_overall": 0,
            "away_goals_scored": 0, 
            "seasonScoredNum_away": 0,
            "away_goals_conceded": 0, 
            "seasonConcededNum_away": 0,
            "goals_per_game": 0,
            "conceded_per_game": 0,
            "seasonGoalsTotal_overall": 0,
            "seasonGoalsTotal_away": 0,
            "clean_sheets_pct": 0, 
            "seasonCSPercentage_overall": 0,
            "seasonCS_overall": 0,
            "seasonCS_away": 0,
            "btts_pct": 0, 
            "seasonBTTSPercentage_overall": 0,
            "over_2_5_pct": 0, 
            "seasonOver25Percentage_overall": 0,
            
            # Expected Goals
            "xg": 0, 
            "xg_for_overall": 0,
            "xga": 0, 
            "xg_against_overall": 0,
            "away_xg": 0, 
            "xg_for_away": 0,
            "away_xga": 0, 
            "xg_against_away": 0,
            "xg_for_avg_overall": 0,
            "xg_for_avg_away": 0,
            "xg_against_avg_overall": 0,
            "xg_against_avg_away": 0,
            
            # Estatísticas de Cartões
            "cards_per_game": 0, 
            "cardsAVG_overall": 0,
            "away_cards_per_game": 0, 
            "cardsAVG_away": 0,
            "cardsTotal_overall": 0,
            "cardsTotal_away": 0,
            "yellow_cards": 0,
            "red_cards": 0,
            "over_3_5_cards_pct": 0,
            
            # Estatísticas de Escanteios
            "corners_per_game": 0, 
            "cornersTotalAVG_overall": 0,
            "away_corners_per_game": 0, 
            "cornersTotalAVG_away": 0,
            "corners_for": 0, 
            "cornersTotal_overall": 0,
            "corners_against": 0, 
            "cornersAgainst_overall": 0,
            "cornersAVG_overall": 0,
            "cornersAVG_away": 0,
            "cornersAgainstAVG_overall": 0,
            "cornersAgainstAVG_away": 0,
            "over_9_5_corners_pct": 0,
            
            # Estatísticas de Chutes
            "shotsAVG_overall": 0,
            "shotsAVG_away": 0,
            "shotsOnTargetAVG_overall": 0,
            "shotsOnTargetAVG_away": 0,
            
            # Posse de Bola
            "possession": 0, 
            "possessionAVG_overall": 0,
            "away_possession": 0, 
            "possessionAVG_away": 0
        },
        "h2h": {
            "total_matches": 0,
            "home_wins": 0,
            "away_wins": 0,
            "draws": 0,
            "avg_goals": 0,
            "over_2_5_pct": 0,
            "btts_pct": 0,
            "avg_cards": 0,
            "avg_corners": 0
        }
    }
    
    # Se não houver dados da API, retorna a estrutura padrão
    if not api_data or not isinstance(api_data, dict):
        logger.warning("Dados da API inválidos ou vazios, retornando estrutura padrão")
        return formatted_data
    
    try:
        # Registrar a estrutura de dados para depuração
        logger.info(f"Transformando dados para {home_team_name} vs {away_team_name}")
        if isinstance(api_data, dict):
            logger.info(f"Chaves principais nos dados da API: {list(api_data.keys())}")
            
            # Identificar possíveis caminhos para estatísticas
            known_paths = []
            if "basic_stats" in api_data:
                known_paths.append("basic_stats")
            if "team_stats" in api_data:
                known_paths.append("team_stats")
            if "data" in api_data and isinstance(api_data["data"], dict):
                known_paths.append("data")
            
            logger.info(f"Caminhos conhecidos nos dados: {known_paths}")
            
            # Verificar caminhos principais onde os dados podem estar
            for path in known_paths:
                if path in api_data and isinstance(api_data[path], dict):
                    logger.info(f"Chaves em {path}: {list(api_data[path].keys())}")
                    
                    # Verificar home/away dentro desses caminhos
                    for team_type in ["home", "away", "home_team", "away_team"]:
                        if team_type in api_data[path]:
                            sub_path = f"{path}.{team_type}"
                            logger.info(f"Encontrado caminho para time: {sub_path}")
        
        # Preenche informações da liga e da partida
        if "basic_stats" in api_data and "league_id" in api_data["basic_stats"]:
            formatted_data["match_info"]["league_id"] = api_data["basic_stats"]["league_id"]
            
        if "basic_stats" in api_data and "league_name" in api_data["basic_stats"]:
            formatted_data["match_info"]["league"] = api_data["basic_stats"]["league_name"]
        elif "league" in api_data and isinstance(api_data["league"], dict) and "name" in api_data["league"]:
            formatted_data["match_info"]["league"] = api_data["league"]["name"]
        
        # MÉTODO 1: Tentar extrair usando funções existentes
        logger.info("Tentando extrair dados usando funções padrão...")
        extract_team_data(api_data, formatted_data, "home")
        extract_team_data(api_data, formatted_data, "away")
        extract_h2h_data(api_data, formatted_data)
        
        # MÉTODO 2: Busca profunda e completa nos dados
        logger.info("Realizando busca profunda para extração completa...")
        deep_extraction = extract_deep_team_data(api_data, home_team_name, away_team_name)
        
        # Verificar resultados da extração profunda
        home_found_count = count_non_zero_fields(deep_extraction["home_team"])
        away_found_count = count_non_zero_fields(deep_extraction["away_team"])
        logger.info(f"Extração profunda encontrou: {home_found_count} campos para casa, {away_found_count} para visitante")
        
        # Combinar resultados se a extração profunda encontrou mais dados
        current_home_count = count_non_zero_fields(formatted_data["home_team"])
        current_away_count = count_non_zero_fields(formatted_data["away_team"])
        
        if home_found_count > current_home_count:
            logger.info(f"Usando dados da extração profunda para o time da casa (+{home_found_count-current_home_count} campos)")
            formatted_data["home_team"] = deep_extraction["home_team"]
        
        if away_found_count > current_away_count:
            logger.info(f"Usando dados da extração profunda para o time visitante (+{away_found_count-current_away_count} campos)")
            formatted_data["away_team"] = deep_extraction["away_team"]
        
        # Combinar dados H2H
        h2h_found_count = count_non_zero_fields(deep_extraction["h2h"])
        current_h2h_count = count_non_zero_fields(formatted_data["h2h"])
        if h2h_found_count > current_h2h_count:
            logger.info(f"Usando dados H2H da extração profunda (+{h2h_found_count-current_h2h_count} campos)")
            formatted_data["h2h"] = deep_extraction["h2h"]
        
        # MÉTODO 3: Busca específica por caminhos alternativos da API
        logger.info("Verificando caminhos alternativos nos dados da API...")
        alternative_paths_extraction(api_data, formatted_data, home_team_name, away_team_name)
        
        # Calcular estatísticas derivadas após todas as extrações
        logger.info("Calculando estatísticas derivadas...")
        calculate_derived_stats(formatted_data["home_team"])
        calculate_derived_stats(formatted_data["away_team"])
        
        # Validação final dos dados
        logger.info("Realizando validação final dos dados...")
        validated_data = validate_stats_for_agent(formatted_data)
        
        # Verificar qualidade dos dados extraídos
        home_final_count = count_non_zero_fields(validated_data["home_team"])
        away_final_count = count_non_zero_fields(validated_data["away_team"])
        home_quality = (home_final_count / len(validated_data["home_team"])) * 100
        away_quality = (away_final_count / len(validated_data["away_team"])) * 100
        
        logger.info(f"Qualidade final dos dados: Casa {home_quality:.1f}% ({home_final_count} campos), Visitante {away_quality:.1f}% ({away_final_count} campos)")
        
        # Alertar sobre qualidade baixa de dados
        if home_quality < 10 or away_quality < 10:
            logger.warning(f"ALERTA: Qualidade de dados muito baixa. Casa: {home_quality:.1f}%, Visitante: {away_quality:.1f}%")
        
        return validated_data
        
    except Exception as e:
        logger.error(f"Erro ao formatar dados: {str(e)}")
        logger.error(traceback.format_exc())
        # Retorna a estrutura padrão em caso de erro
        return formatted_data
def extract_traditional_stats(api_data, result):
    """Extrai estatísticas usando a estrutura tradicional da API"""
    # Importação necessária
    import logging
    logger = logging.getLogger("valueHunter.api_adapter")
    
    # Extrair informações da liga
    if "basic_stats" in api_data:
        if "league_id" in api_data["basic_stats"]:
            result["match_info"]["league_id"] = api_data["basic_stats"]["league_id"]
        if "league" in api_data["basic_stats"]:
            result["match_info"]["league"] = api_data["basic_stats"]["league"]
    
    # Extrair estatísticas dos times
    if "basic_stats" in api_data:
        # Time da casa
        if "home_team" in api_data["basic_stats"]:
            home_team_data = api_data["basic_stats"]["home_team"]
            extract_team_stats(home_team_data, result["home_team"], "home")
            
        # Time visitante
        if "away_team" in api_data["basic_stats"]:
            away_team_data = api_data["basic_stats"]["away_team"]
            extract_team_stats(away_team_data, result["away_team"], "away")
    
    # Extrair dados avançados se disponíveis
    if "advanced_stats" in api_data:
        if "home" in api_data["advanced_stats"]:
            extract_advanced_stats(api_data["advanced_stats"]["home"], result["home_team"])
        if "away" in api_data["advanced_stats"]:
            extract_advanced_stats(api_data["advanced_stats"]["away"], result["away_team"])
    
    # Extrair H2H
    if "head_to_head" in api_data:
        extract_h2h_data(api_data["head_to_head"], result["h2h"])
    elif "h2h" in api_data:
        extract_h2h_data(api_data["h2h"], result["h2h"])
    elif "match_details" in api_data and api_data["match_details"] and "h2h" in api_data["match_details"]:
        extract_h2h_data(api_data["match_details"]["h2h"], result["h2h"])
    
    # Extrair dados de forma
    if "team_form" in api_data:
        if "home" in api_data["team_form"] and isinstance(api_data["team_form"]["home"], list):
            extract_form_data(api_data["team_form"]["home"], result["home_team"], "form")
        if "away" in api_data["team_form"] and isinstance(api_data["team_form"]["away"], list):
            extract_form_data(api_data["team_form"]["away"], result["away_team"], "form")

def extract_team_stats(team_data, target_dict, team_type):
    """Extrai estatísticas de um time com tratamento de diferentes estruturas de dados"""
    # Importação necessária
    import logging
    logger = logging.getLogger("valueHunter.api_adapter")
    
    if not team_data or not isinstance(team_data, dict):
        logger.warning(f"Dados inválidos para o time {team_type}")
        return
    
    # Verificar se o time tem estatísticas
    stats_data = None
    
    # Caso 1: Estatísticas diretamente no objeto stats
    if "stats" in team_data and isinstance(team_data["stats"], dict):
        stats_data = team_data["stats"]
    
    # Caso 2: Estatísticas em stats.stats (estrutura aninhada)
    elif "stats" in team_data and isinstance(team_data["stats"], dict) and "stats" in team_data["stats"]:
        stats_data = team_data["stats"]["stats"]
    
    # Caso 3: Estatísticas diretamente no objeto do time
    if stats_data is None:
        for key in ["played", "matches_played", "wins", "goals_scored"]:
            if key in team_data:
                stats_data = team_data
                break
    
    # Se não encontramos estatísticas, sair
    if stats_data is None:
        logger.warning(f"Nenhuma estatística encontrada para o time {team_type}")
        return
    
    # Mapeamento ampliado de campos para extração
    field_mapping = {
        "played": ["played", "matches_played", "seasonMatchesPlayed_overall", "MP", "PJ", "Games"],
        "wins": ["wins", "seasonWinsNum_overall", "W", "Wins", "team_wins"],
        "draws": ["draws", "seasonDrawsNum_overall", "D", "Draws"],
        "losses": ["losses", "seasonLossesNum_overall", "L", "Defeats", "Losses"],
        "goals_scored": ["goals_scored", "seasonGoals_overall", "Gls", "goals", "GF", "GoalsFor"],
        "goals_conceded": ["goals_conceded", "seasonConceded_overall", "GA", "GoalsAgainst"],
        "clean_sheets_pct": ["clean_sheet_percentage", "seasonCSPercentage_overall", "clean_sheets_pct"],
        "btts_pct": ["btts_percentage", "seasonBTTSPercentage_overall", "btts_pct"],
        "over_2_5_pct": ["over_2_5_percentage", "seasonOver25Percentage_overall", "over_2_5_goals_pct"],
        "xg": ["xG", "xg", "xg_for_overall", "expected_goals", "ExpG"],
        "xga": ["xGA", "xga", "xg_against_avg_overall", "expected_goals_against"],
        "possession": ["possession", "possessionAVG_overall", "Poss", "possession_avg"],
        "yellow_cards": ["yellow_cards", "seasonCrdYNum_overall", "CrdY", "YellowCards"],
        "red_cards": ["red_cards", "seasonCrdRNum_overall", "CrdR", "RedCards"],
        "over_3_5_cards_pct": ["over_3_5_cards_percentage", "over35CardsPercentage_overall"],
        "corners_for": ["corners_for", "seasonCornersFor_overall", "CK", "Corners"],
        "corners_against": ["corners_against", "seasonCornersAgainst_overall"],
        "over_9_5_corners_pct": ["over_9_5_corners_percentage", "over95CornersPercentage_overall"],
    }
    
    # Adicionar campos específicos do tipo de time (casa/visitante)
    if team_type == "home":
        specific_fields = {
            "home_played": ["home_played", "matches_played_home", "seasonMatchesPlayed_home", "home_matches"],
            "home_wins": ["home_wins", "seasonWinsNum_home", "wins_home"],
            "home_draws": ["home_draws", "seasonDrawsNum_home", "draws_home"],
            "home_losses": ["home_losses", "seasonLossesNum_home", "losses_home"],
            "home_goals_scored": ["home_goals_scored", "goals_scored_home", "seasonGoals_home"],
            "home_goals_conceded": ["home_goals_conceded", "goals_conceded_home", "seasonConceded_home"],
        }
        field_mapping.update(specific_fields)
    elif team_type == "away":
        specific_fields = {
            "away_played": ["away_played", "matches_played_away", "seasonMatchesPlayed_away", "away_matches"],
            "away_wins": ["away_wins", "seasonWinsNum_away", "wins_away"],
            "away_draws": ["away_draws", "seasonDrawsNum_away", "draws_away"],
            "away_losses": ["away_losses", "seasonLossesNum_away", "losses_away"],
            "away_goals_scored": ["away_goals_scored", "goals_scored_away", "seasonGoals_away"],
            "away_goals_conceded": ["away_goals_conceded", "goals_conceded_away", "seasonConceded_away"],
        }
        field_mapping.update(specific_fields)
    
    # Extrair estatísticas
    for target_field, source_fields in field_mapping.items():
        # Verificar primeiro em stats_data
        for field in source_fields:
            if field in stats_data:
                value = stats_data[field]
                try:
                    if value is not None and value != 'N/A':
                        target_dict[target_field] = float(value)
                        break  # Encontrou este campo, continuar para o próximo
                except (ValueError, TypeError):
                    pass
        
        # Se não encontrou, buscar também no time_data
        if target_field not in target_dict or target_dict[target_field] == 0:
            for field in source_fields:
                if field in team_data:
                    value = team_data[field]
                    try:
                        if value is not None and value != 'N/A':
                            target_dict[target_field] = float(value)
                            break
                    except (ValueError, TypeError):
                        pass
    
    # Buscar em additional_info se disponível
    if "stats" in team_data and isinstance(team_data["stats"], dict) and "additional_info" in team_data["stats"]:
        additional_info = team_data["stats"]["additional_info"]
        
        # Campos que podem estar em additional_info
        additional_fields = {
            "xg": ["xg_for_overall"],
            "xga": ["xg_against_overall"],
            "over_3_5_cards_pct": ["over35CardsPercentage_overall"],
            "over_9_5_corners_pct": ["over95CornersPercentage_overall"]
        }
        
        for target_field, source_fields in additional_fields.items():
            if target_field not in target_dict or target_dict[target_field] == 0:
                for field in source_fields:
                    if field in additional_info:
                        value = additional_info[field]
                        try:
                            if value is not None and value != 'N/A':
                                target_dict[target_field] = float(value)
                                break
                        except (ValueError, TypeError):
                            pass

def extract_advanced_stats(advanced_data, target_dict):
    """Extrai estatísticas avançadas"""
    if not advanced_data or not isinstance(advanced_data, dict):
        return
    
    # PPDA (Passes por Ação Defensiva)
    ppda_keys = ["ppda", "passes_per_defensive_action", "PPDA"]
    for key in ppda_keys:
        if key in advanced_data and advanced_data[key] is not None:
            try:
                target_dict["ppda"] = float(advanced_data[key])
                break
            except (ValueError, TypeError):
                pass
    
    # Outras métricas avançadas
    other_metrics = {
        "xg": ["xg", "expected_goals", "xG"],
        "xga": ["xga", "expected_goals_against", "xGA"],
        "possession": ["possession", "possessionAVG_overall", "Poss"]
    }
    
    for target_key, source_keys in other_metrics.items():
        if target_key not in target_dict or target_dict[target_key] == 0:
            for key in source_keys:
                if key in advanced_data and advanced_data[key] is not None:
                    try:
                        target_dict[target_key] = float(advanced_data[key])
                        break
                    except (ValueError, TypeError):
                        pass

def extract_h2h_data(api_data, formatted_data):
    """
    Extrai dados completos de H2H (confronto direto)
    
    Args:
        api_data (dict): Dados originais da API
        formatted_data (dict): Estrutura de dados alvo
    """
    # Buscar dados H2H em diferentes locais possíveis
    h2h_data = None
    
    if "head_to_head" in api_data:
        h2h_data = api_data["head_to_head"]
    elif "match_details" in api_data and api_data["match_details"] and "h2h" in api_data["match_details"]:
        h2h_data = api_data["match_details"]["h2h"]
    elif "h2h" in api_data:
        h2h_data = api_data["h2h"]
    
    if not h2h_data:
        return
    
    # Mapeamento de campos H2H
    h2h_mapping = {
        "total_matches": ["total_matches", "totalMatches", "matches", "matches_total"],
        "home_wins": ["home_wins", "team_a_wins", "home_team_wins"],
        "away_wins": ["away_wins", "team_b_wins", "away_team_wins"],
        "draws": ["draws", "equal", "draw"],
        "avg_goals": ["avg_goals", "average_goals", "goals_avg"],
        "over_2_5_pct": ["over_2_5_percentage", "over_2_5_pct", "over25_percentage"],
        "btts_pct": ["btts_percentage", "btts_pct", "both_teams_scored_percentage"],
        "avg_cards": ["average_cards", "avg_cards", "cards_avg"],
        "avg_corners": ["average_corners", "avg_corners", "corners_avg"]
    }
    
    # Extrair cada campo
    for target_field, source_fields in h2h_mapping.items():
        for field in source_fields:
            if field in h2h_data:
                value = h2h_data[field]
                if value is not None and value != 'N/A':
                    try:
                        formatted_data["h2h"][target_field] = float(value)
                        break
                    except (ValueError, TypeError):
                        pass
def extract_form_data(form_data, target_dict, field_name="form"):
    """Extrai dados de forma recente"""
    if not form_data or not isinstance(form_data, list):
        target_dict[field_name] = "?????"
        return
    
    form_string = ""
    for match in form_data[:5]:
        if isinstance(match, dict) and "result" in match:
            form_string += match["result"]
        else:
            form_string += "?"
    
    # Garantir que temos 5 caracteres
    form_string = form_string.ljust(5, "?")[:5]
    target_dict[field_name] = form_string

def count_non_zero_fields(data_dict):
    """Conta campos com valores não-zero em um dicionário"""
    if not isinstance(data_dict, dict):
        return 0
    
    count = 0
    for key, value in data_dict.items():
        if isinstance(value, (int, float)) and value != 0:
            count += 1
        elif isinstance(value, str) and value != "" and value != "?????":
            count += 1
    
    return count

def extract_from_anywhere(api_data, result, home_team_name, away_team_name):
    """Busca estatísticas em qualquer lugar da estrutura de dados"""
    # Importações necessárias
    import logging
    logger = logging.getLogger("valueHunter.api_adapter")
    
    logger.info("Executando busca agressiva de estatísticas em toda a estrutura de dados")
    
    # Função para buscar estatísticas recursivamente
    def search_stats(obj, path="", home_stats=None, away_stats=None):
        if home_stats is None:
            home_stats = {}
        if away_stats is None:
            away_stats = {}
            
        if isinstance(obj, dict):
            # Verificar se este objeto pode conter estatísticas de um time
            has_stats = False
            for key in ["played", "matches_played", "wins", "goals_scored", "xg"]:
                if key in obj:
                    has_stats = True
                    break
            
            if has_stats:
                # Tentar determinar a qual time pertencem estas estatísticas
                is_home = False
                is_away = False
                
                # Verificar pelo nome do time
                if "name" in obj and isinstance(obj["name"], str):
                    if obj["name"] == home_team_name or home_team_name in obj["name"]:
                        is_home = True
                    elif obj["name"] == away_team_name or away_team_name in obj["name"]:
                        is_away = True
                
                # Verificar pelo caminho
                if not (is_home or is_away):
                    if "home" in path.lower():
                        is_home = True
                    elif "away" in path.lower() or "visit" in path.lower():
                        is_away = True
                
                # Se determinamos o time, extrair estatísticas
                if is_home:
                    logger.info(f"Encontradas possíveis estatísticas do time da casa em {path}")
                    extract_stats_from_dict(obj, home_stats)
                elif is_away:
                    logger.info(f"Encontradas possíveis estatísticas do time visitante em {path}")
                    extract_stats_from_dict(obj, away_stats)
                else:
                    # Se não conseguimos determinar, mas parece estatística, fazer log
                    logger.info(f"Encontrado objeto com possíveis estatísticas (time indeterminado) em {path}")
            
            # Continuando a busca em todas as chaves
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                search_stats(v, new_path, home_stats, away_stats)
                
        elif isinstance(obj, list):
            # Buscar em listas também
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                search_stats(item, new_path, home_stats, away_stats)
        
        return home_stats, away_stats
    
    # Executar busca
    home_found, away_found = search_stats(api_data)
    
    # Verificar se encontramos algo útil
    home_found_count = count_non_zero_fields(home_found)
    away_found_count = count_non_zero_fields(away_found)
    
    logger.info(f"Busca agressiva encontrou: {home_found_count} campos para casa, {away_found_count} para visitante")
    
    # Atualizar apenas se encontramos mais dados do que já temos
    current_home_count = count_non_zero_fields(result["home_team"])
    current_away_count = count_non_zero_fields(result["away_team"])
    
    if home_found_count > current_home_count:
        # Mesclar com dados existentes, sem substituir valores não-zero
        for k, v in home_found.items():
            if k not in result["home_team"] or result["home_team"][k] == 0:
                result["home_team"][k] = v
        logger.info(f"Atualizados {home_found_count} campos para o time da casa")
    
    if away_found_count > current_away_count:
        # Mesclar com dados existentes, sem substituir valores não-zero
        for k, v in away_found.items():
            if k not in result["away_team"] or result["away_team"][k] == 0:
                result["away_team"][k] = v
        logger.info(f"Atualizados {away_found_count} campos para o time visitante")

def extract_stats_from_dict(source_dict, target_dict):
    """Extrai estatísticas de um dicionário para outro usando mapeamento de campos"""
    if not isinstance(source_dict, dict):
        return
    
    # Mapeamento de campos comuns
    field_mapping = {
        "played": ["played", "matches_played", "games_played", "MP", "PJ", "matches"],
        "wins": ["wins", "W", "team_wins", "won"],
        "draws": ["draws", "D", "team_draws"],
        "losses": ["losses", "L", "defeats", "lost"],
        "goals_scored": ["goals_scored", "goals_for", "scored", "GF", "goals"],
        "goals_conceded": ["goals_conceded", "goals_against", "conceded", "GA"],
        "xg": ["xg", "xG", "expected_goals"],
        "xga": ["xga", "xGA", "expected_goals_against"],
        "possession": ["possession", "possessionAVG", "avg_possession", "posesion"],
        "clean_sheets_pct": ["clean_sheets_pct", "clean_sheet_percentage", "cs_pct"],
        "btts_pct": ["btts_pct", "btts_percentage", "both_teams_scored_pct"],
        "over_2_5_pct": ["over_2_5_pct", "over_2_5_percentage", "o25_pct"],
        "yellow_cards": ["yellow_cards", "yellows", "cards_yellow"],
        "red_cards": ["red_cards", "reds", "cards_red"]
    }
    
    # Extrair cada campo
    for target_field, source_fields in field_mapping.items():
        for field in source_fields:
            if field in source_dict:
                value = source_dict[field]
                try:
                    if value is not None and value != 'N/A':
                        float_val = float(value)
                        if float_val != 0:  # Ignorar valores zero
                            target_dict[target_field] = float_val
                            break
                except (ValueError, TypeError):
                    pass

def extract_h2h_from_anywhere(api_data, result):
    """Busca dados de H2H em qualquer lugar da estrutura"""
    # Importações necessárias
    import logging
    logger = logging.getLogger("valueHunter.api_adapter")
    
    # Primeiro, procurar estruturas específicas de H2H
    h2h_objects = []
    
    def find_h2h_objects(obj, path=""):
        if isinstance(obj, dict):
            # Verificar se parece ser um objeto H2H
            is_h2h = False
            h2h_indicators = ["h2h", "head_to_head", "previous_matches", "confrontos"]
            
            # Verificar pelo nome da chave
            for indicator in h2h_indicators:
                if indicator in path.lower():
                    is_h2h = True
                    break
            
            # Verificar pelo conteúdo típico de H2H
            if not is_h2h:
                h2h_fields = ["total_matches", "home_wins", "away_wins", "draws"]
                field_count = sum(1 for field in h2h_fields if field in obj)
                if field_count >= 2:  # Se tem pelo menos 2 campos típicos de H2H
                    is_h2h = True
            
            if is_h2h:
                logger.info(f"Possível objeto H2H encontrado em {path}")
                h2h_objects.append(obj)
            
            # Continuar buscando recursivamente
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                find_h2h_objects(v, new_path)
                
        elif isinstance(obj, list):
            # Buscar em listas também
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                find_h2h_objects(item, new_path)
    
    # Iniciar busca
    find_h2h_objects(api_data)
    
    # Processar objetos H2H encontrados
    for h2h_obj in h2h_objects:
        extract_h2h_data(h2h_obj, result["h2h"])
    
    # Log dos resultados
    h2h_fields = count_non_zero_fields(result["h2h"])
    logger.info(f"Extraídos {h2h_fields} campos de H2H após busca completa")

def calculate_derived_stats(team_dict):
    """
    Calcula estatísticas derivadas quando possível
    
    Args:
        team_dict (dict): Dicionário de estatísticas do time
    """
    # Jogos disputados
    played = team_dict.get("played", 0)
    if played > 0:
        # Win/Draw/Loss percentagens
        if "wins" in team_dict and "win_pct" not in team_dict:
            team_dict["win_pct"] = round((team_dict["wins"] / played) * 100, 1)
        if "draws" in team_dict and "draw_pct" not in team_dict:
            team_dict["draw_pct"] = round((team_dict["draws"] / played) * 100, 1)
        if "losses" in team_dict and "loss_pct" not in team_dict:
            team_dict["loss_pct"] = round((team_dict["losses"] / played) * 100, 1)
        
        # Médias por jogo
        if "goals_scored" in team_dict and "goals_per_game" not in team_dict:
            team_dict["goals_per_game"] = round(team_dict["goals_scored"] / played, 2)
        if "goals_conceded" in team_dict and "conceded_per_game" not in team_dict:
            team_dict["conceded_per_game"] = round(team_dict["goals_conceded"] / played, 2)
    
    # Cartões
    yellow = team_dict.get("yellow_cards", 0)
    red = team_dict.get("red_cards", 0)
    if "cardsTotal_overall" not in team_dict and (yellow > 0 or red > 0):
        team_dict["cardsTotal_overall"] = yellow + red
        if played > 0 and "cardsAVG_overall" not in team_dict:
            team_dict["cardsAVG_overall"] = round((yellow + red) / played, 2)
            team_dict["cards_per_game"] = team_dict["cardsAVG_overall"]
    
    # Escanteios
    corners_for = team_dict.get("corners_for", 0)
    corners_against = team_dict.get("corners_against", 0)
    if "cornersTotal_overall" not in team_dict and (corners_for > 0 or corners_against > 0):
        team_dict["cornersTotal_overall"] = corners_for + corners_against
        if played > 0 and "cornersTotalAVG_overall" not in team_dict:
            team_dict["cornersTotalAVG_overall"] = round((corners_for + corners_against) / played, 2)
            team_dict["corners_per_game"] = team_dict["cornersTotalAVG_overall"]
    
    # Garantir consistência entre campos duplicados
    # Campos de time
    for orig, dupe in [
        ("played", "seasonMatchesPlayed_overall"),
        ("wins", "seasonWinsNum_overall"),
        ("draws", "seasonDrawsNum_overall"),
        ("losses", "seasonLossesNum_overall"),
        ("goals_scored", "seasonScoredNum_overall"),
        ("goals_conceded", "seasonConcededNum_overall"),
        ("xg", "xg_for_overall"),
        ("xga", "xg_against_overall"),
        ("possession", "possessionAVG_overall"),
        ("cards_per_game", "cardsAVG_overall"),
        ("corners_per_game", "cornersTotalAVG_overall")
    ]:
        if orig in team_dict and team_dict[orig] > 0 and (dupe not in team_dict or team_dict[dupe] == 0):
            team_dict[dupe] = team_dict[orig]
        elif dupe in team_dict and team_dict[dupe] > 0 and (orig not in team_dict or team_dict[orig] == 0):
            team_dict[orig] = team_dict[dupe]
def ensure_complete_stats(result, home_team_name, away_team_name):
    """Garante que temos um conjunto mínimo de estatísticas para análise"""
    import random  # Adicionar importação para randomização
    import logging
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    home_team = result["home_team"]
    away_team = result["away_team"]
    h2h = result["h2h"]
    
    # Preencher campos de jogos disputados se missing
    if home_team.get("played", 0) == 0:
        # Tentar inferir de wins + draws + losses
        played = home_team.get("wins", 0) + home_team.get("draws", 0) + home_team.get("losses", 0)
        if played > 0:
            home_team["played"] = played
            logger.info(f"Calculado played={played} para time da casa")
    
    if away_team.get("played", 0) == 0:
        # Tentar inferir de wins + draws + losses
        played = away_team.get("wins", 0) + away_team.get("draws", 0) + away_team.get("losses", 0)
        if played > 0:
            away_team["played"] = played
            logger.info(f"Calculado played={played} para time visitante")
    
    # Se h2h total_matches está faltando, tentar inferir
    if h2h.get("total_matches", 0) == 0:
        total = h2h.get("home_wins", 0) + h2h.get("away_wins", 0) + h2h.get("draws", 0)
        if total > 0:
            h2h["total_matches"] = total
            logger.info(f"Calculado total_matches={total} para H2H")
    
    # Garantir que temos pelo menos um histórico recente (mesmo que genérico)
    # Para permitir análise de tendências
    if "form" not in home_team or home_team["form"] == "?????":
        # Criar um histórico baseado nas tendências gerais
        wins_pct = home_team.get("win_pct", 0) if "win_pct" in home_team else (home_team.get("wins", 0) / max(1, home_team.get("played", 1))) * 100
        draws_pct = home_team.get("draw_pct", 0) if "draw_pct" in home_team else (home_team.get("draws", 0) / max(1, home_team.get("played", 1))) * 100
        losses_pct = home_team.get("loss_pct", 0) if "loss_pct" in home_team else (home_team.get("losses", 0) / max(1, home_team.get("played", 1))) * 100
        
        # Normalizar para suma 100%
        total = wins_pct + draws_pct + losses_pct
        if total > 0:
            wins_pct = (wins_pct / total) * 100
            draws_pct = (draws_pct / total) * 100
            losses_pct = (losses_pct / total) * 100
        
        form = ""
        logger.info(f"Gerando forma sintética para {home_team_name}: W={wins_pct:.1f}%, D={draws_pct:.1f}%, L={losses_pct:.1f}%")
        
        for _ in range(5):
            # Usar distribuição real baseada nas estatísticas com randomização
            r = random.random() * 100  # Valor entre 0 e 100
            if r < wins_pct:
                form += "W"
            elif r < (wins_pct + draws_pct):
                form += "D"
            else:
                form += "L"
        
        home_team["form"] = form
        logger.info(f"Forma gerada para {home_team_name}: {form}")
    
    # Mesmo para o time visitante (usando randomização adequada)
    if "form" not in away_team or away_team["form"] == "?????":
        wins_pct = away_team.get("win_pct", 0) if "win_pct" in away_team else (away_team.get("wins", 0) / max(1, away_team.get("played", 1))) * 100
        draws_pct = away_team.get("draw_pct", 0) if "draw_pct" in away_team else (away_team.get("draws", 0) / max(1, away_team.get("played", 1))) * 100
        losses_pct = away_team.get("loss_pct", 0) if "loss_pct" in away_team else (away_team.get("losses", 0) / max(1, away_team.get("played", 1))) * 100
        
        # Normalizar para suma 100%
        total = wins_pct + draws_pct + losses_pct
        if total > 0:
            wins_pct = (wins_pct / total) * 100
            draws_pct = (draws_pct / total) * 100
            losses_pct = (losses_pct / total) * 100
        
        form = ""
        logger.info(f"Gerando forma sintética para {away_team_name}: W={wins_pct:.1f}%, D={draws_pct:.1f}%, L={losses_pct:.1f}%")
        
        for _ in range(5):
            # Usar distribuição real baseada nas estatísticas com randomização
            r = random.random() * 100  # Valor entre 0 e 100
            if r < wins_pct:
                form += "W" 
            elif r < (wins_pct + draws_pct):
                form += "D"
            else:
                form += "L"
        
        away_team["form"] = form
        logger.info(f"Forma gerada para {away_team_name}: {form}")
    
    # Calcular win/draw/loss percentages se temos jogos disputados
    home_played = home_team.get("played", 0)
    if home_played > 0:
        if "wins" in home_team and "win_pct" not in home_team:
            home_team["win_pct"] = round((home_team["wins"] / home_played) * 100, 1)
            
        if "draws" in home_team and "draw_pct" not in home_team:
            home_team["draw_pct"] = round((home_team["draws"] / home_played) * 100, 1)
            
        if "losses" in home_team and "loss_pct" not in home_team:
            home_team["loss_pct"] = round((home_team["losses"] / home_played) * 100, 1)
            
        # Calcular médias por jogo
        if "goals_scored" in home_team and "goals_per_game" not in home_team:
            home_team["goals_per_game"] = round(home_team["goals_scored"] / home_played, 2)
            
        if "goals_conceded" in home_team and "conceded_per_game" not in home_team:
            home_team["conceded_per_game"] = round(home_team["goals_conceded"] / home_played, 2)
    
    # Mesmos cálculos para time visitante
    away_played = away_team.get("played", 0)
    if away_played > 0:
        if "wins" in away_team and "win_pct" not in away_team:
            away_team["win_pct"] = round((away_team["wins"] / away_played) * 100, 1)
            
        if "draws" in away_team and "draw_pct" not in away_team:
            away_team["draw_pct"] = round((away_team["draws"] / away_played) * 100, 1)
            
        if "losses" in away_team and "loss_pct" not in away_team:
            away_team["loss_pct"] = round((away_team["losses"] / away_played) * 100, 1)
            
        if "goals_scored" in away_team and "goals_per_game" not in away_team:
            away_team["goals_per_game"] = round(away_team["goals_scored"] / away_played, 2)
            
        if "goals_conceded" in away_team and "conceded_per_game" not in away_team:
            away_team["conceded_per_game"] = round(away_team["goals_conceded"] / away_played, 2)
    
    # Cartões
    for team in [home_team, away_team]:
        yellow = team.get("yellow_cards", 0)
        red = team.get("red_cards", 0)
        played = team.get("played", 0)
        
        if "cards_total" not in team and (yellow > 0 or red > 0):
            team["cards_total"] = yellow + red
            
        if "cards_per_game" not in team and played > 0 and team.get("cards_total", 0) > 0:
            team["cards_per_game"] = round(team["cards_total"] / played, 2)
    
    # Escanteios
    for team in [home_team, away_team]:
        corners_for = team.get("corners_for", 0)
        corners_against = team.get("corners_against", 0)
        played = team.get("played", 0)
        
        if "corners_total" not in team and (corners_for > 0 or corners_against > 0):
            team["corners_total"] = corners_for + corners_against
            
        if "corners_per_game" not in team and played > 0 and team.get("corners_total", 0) > 0:
            team["corners_per_game"] = round(team["corners_total"] / played, 2)
def extract_deep_team_data(api_data, home_team_name, away_team_name, log_details=True):
    """
    Função extremamente agressiva que busca dados dos times em QUALQUER lugar na estrutura,
    independente do formato ou nível de aninhamento.
    
    Args:
        api_data (dict): Dados brutos da API
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
        log_details (bool): Se deve registrar detalhes de depuração
        
    Returns:
        dict: Dados estruturados dos times e confronto
    """
    # Importações explícitas no início da função
    import logging
    import json
    import traceback
    import copy
    
    logger = logging.getLogger("valueHunter.data_extractor")
    
    # Inicializa a estrutura de resultado
    result = {
        "match_info": {
            "home_team": home_team_name,
            "away_team": away_team_name,
            "league": "",
            "league_id": None
        },
        "home_team": {
            # Estatísticas mínimas para evitar erros
            "played": 0, "wins": 0, "draws": 0, "losses": 0,
            "goals_scored": 0, "goals_conceded": 0,
            "form": "?????"
        },
        "away_team": {
            # Mesmos valores padrão para o visitante
            "played": 0, "wins": 0, "draws": 0, "losses": 0,
            "goals_scored": 0, "goals_conceded": 0,
            "form": "?????"
        },
        "h2h": {
            "total_matches": 0, "home_wins": 0, "away_wins": 0, "draws": 0
        }
    }
    
    # Dicionários para coleta de dados encontrados
    home_found = {}
    away_found = {}
    h2h_found = {}
    
    # Log da estrutura para depuração
    if log_details:
        logger.info(f"Iniciando extração profunda para {home_team_name} vs {away_team_name}")
        
        # Registrar o tamanho dos dados para referência
        try:
            if isinstance(api_data, dict):
                logger.info(f"Chaves principais nos dados brutos: {list(api_data.keys())}")
                
                # Verificar estruturas conhecidas
                if "basic_stats" in api_data:
                    bs_keys = list(api_data["basic_stats"].keys())
                    logger.info(f"basic_stats contém: {bs_keys}")
                
                if "team_stats" in api_data:
                    ts_keys = list(api_data["team_stats"].keys())
                    logger.info(f"team_stats contém: {ts_keys}")
                
                if "data" in api_data and isinstance(api_data["data"], dict):
                    data_keys = list(api_data["data"].keys())
                    logger.info(f"data contém: {data_keys}")
        except:
            logger.error("Erro ao analisar estrutura de dados")
    
    try:
        # VERIFICAÇÃO DE TODOS OS CAMINHOS POSSÍVEIS PARA EXTRAÇÃO
        known_paths = [
            # Caminhos comuns para estatísticas do time da casa
            ["team_stats", "home"],
            ["basic_stats", "home_team", "stats"],
            ["basic_stats", "home_team"],
            ["home_team", "stats"],
            ["data", "teams", "home"],
            ["data", "home_team"],
            ["home"],
            
            # Caminhos alternativos que podem conter dados
            ["teams", 0],  # Primeiro time em uma lista pode ser o da casa
            ["teams", "home"],
            ["match", "home_team"],
            ["home_stats"],
            ["stats", "home"],
        ]
        
        # FASE 1: Verificar caminhos diretos conhecidos
        
        # Verificar cada caminho conhecido para o time da casa
        for path in known_paths:
            current = api_data
            path_valid = True
            
            # Navegar pelo caminho
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, list) and isinstance(key, int) and key < len(current):
                    current = current[key]
                else:
                    path_valid = False
                    break
            
            # Se chegamos ao final do caminho, extrair dados
            if path_valid and isinstance(current, dict):
                logger.info(f"Encontrado possível caminho para dados do time da casa: {path}")
                
                # Verificar se contém dados estatísticos
                has_stats = any(key in current for key in ["played", "matches_played", "wins", "goals_scored", "xg", "form"])
                
                if has_stats:
                    logger.info(f"Extraindo estatísticas do time da casa do caminho: {path}")
                    extract_stats_recursive(current, home_found, ".".join(str(k) for k in path))
                
                # Verificar também se contém subchaves comuns com estatísticas
                for subkey in ["stats", "statistics", "seasonStats", "data"]:
                    if subkey in current and isinstance(current[subkey], dict):
                        logger.info(f"Encontrada subchave {subkey} com estatísticas do time da casa")
                        extract_stats_recursive(current[subkey], home_found, f"{'.'.join(str(k) for k in path)}.{subkey}")
        
        # Adaptar os mesmos caminhos para o time visitante (substituindo 'home' por 'away')
        away_paths = []
        for path in known_paths:
            away_path = []
            for key in path:
                if key == "home":
                    away_path.append("away")
                elif key == "home_team":
                    away_path.append("away_team")
                elif key == 0 and isinstance(key, int):  # Primeiro item → Segundo item
                    away_path.append(1)
                else:
                    away_path.append(key)
            away_paths.append(away_path)
        
        # Verificar cada caminho para o time visitante
        for path in away_paths:
            current = api_data
            path_valid = True
            
            # Navegar pelo caminho
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, list) and isinstance(key, int) and key < len(current):
                    current = current[key]
                else:
                    path_valid = False
                    break
            
            # Se chegamos ao final do caminho, extrair dados
            if path_valid and isinstance(current, dict):
                logger.info(f"Encontrado possível caminho para dados do time visitante: {path}")
                
                # Verificar se contém dados estatísticos
                has_stats = any(key in current for key in ["played", "matches_played", "wins", "goals_scored", "xg", "form"])
                
                if has_stats:
                    logger.info(f"Extraindo estatísticas do time visitante do caminho: {path}")
                    extract_stats_recursive(current, away_found, ".".join(str(k) for k in path))
                
                # Verificar também se contém subchaves comuns com estatísticas
                for subkey in ["stats", "statistics", "seasonStats", "data"]:
                    if subkey in current and isinstance(current[subkey], dict):
                        logger.info(f"Encontrada subchave {subkey} com estatísticas do time visitante")
                        extract_stats_recursive(current[subkey], away_found, f"{'.'.join(str(k) for k in path)}.{subkey}")
        
        # FASE 2: Busca de dados H2H em caminhos conhecidos
        h2h_paths = [
            ["head_to_head"],
            ["h2h"],
            ["basic_stats", "match_details", "h2h"],
            ["match_details", "h2h"],
            ["data", "h2h"],
            ["data", "head_to_head"],
            ["h2h_stats"]
        ]
        
        # Verificar cada caminho para dados H2H
        for path in h2h_paths:
            current = api_data
            path_valid = True
            
            # Navegar pelo caminho
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    path_valid = False
                    break
            
            # Se encontramos dados H2H, extrair
            if path_valid and isinstance(current, dict):
                logger.info(f"Encontrados dados H2H no caminho: {path}")
                
                # Verificar se contém dados H2H
                has_h2h = any(key in current for key in ["total_matches", "home_wins", "away_wins", "draws"])
                
                if has_h2h:
                    # Mapeamento de campos H2H
                    h2h_mapping = {
                        "total_matches": ["total_matches", "totalMatches", "matches", "matches_total", "total", "count"],
                        "home_wins": ["home_wins", "team_a_wins", "home_team_wins", "homeWins"],
                        "away_wins": ["away_wins", "team_b_wins", "away_team_wins", "awayWins"],
                        "draws": ["draws", "equal", "draw", "empates"],
                        "avg_goals": ["avg_goals", "average_goals", "goals_avg", "avgGoals", "meanGoals"],
                        "over_2_5_pct": ["over_2_5_percentage", "over_2_5_pct", "over25_percentage", "over25pct"],
                        "btts_pct": ["btts_percentage", "btts_pct", "both_teams_scored_percentage", "bttsPct"],
                        "avg_cards": ["average_cards", "avg_cards", "cards_avg", "avgCards", "meanCards"],
                        "avg_corners": ["average_corners", "avg_corners", "corners_avg", "avgCorners", "meanCorners"]
                    }
                    
                    # Extrair cada campo H2H
                    for target_field, source_fields in h2h_mapping.items():
                        for field in source_fields:
                            if field in current:
                                value = current[field]
                                if value is not None and value != 'N/A':
                                    try:
                                        h2h_found[target_field] = float(value)
                                        break
                                    except (ValueError, TypeError):
                                        pass
        
        # FASE 3: Busca profunda e recursiva em toda a estrutura
        def deep_search(obj, path=""):
            if isinstance(obj, dict):
                # Verificar se o objeto contém um nome de time
                if "name" in obj and isinstance(obj["name"], str):
                    team_name = obj["name"]
                    
                    # Verificar se é um dos times que estamos procurando
                    is_home = False
                    is_away = False
                    
                    # Comparação exata
                    if team_name == home_team_name:
                        is_home = True
                    elif team_name == away_team_name:
                        is_away = True
                    
                    # Comparação parcial (necessário para alguns endpoints)
                    if not (is_home or is_away):
                        if home_team_name.lower() in team_name.lower() or team_name.lower() in home_team_name.lower():
                            is_home = True
                        elif away_team_name.lower() in team_name.lower() or team_name.lower() in away_team_name.lower():
                            is_away = True
                    
                    # Se encontramos um time, extrair estatísticas
                    if is_home or is_away:
                        target_dict = home_found if is_home else away_found
                        logger.info(f"Encontrado {'time da casa' if is_home else 'time visitante'} pelo nome: {team_name} em {path}")
                        
                        # Extrair estatísticas diretamente do objeto
                        extract_stats_recursive(obj, target_dict, path)
                
                # Verificar se este objeto contém palavras-chave relacionadas a casa/fora
                if not ("h2h" in path.lower() or "vs" in path.lower()):
                    is_home_related = "home" in path.lower() or "casa" in path.lower()
                    is_away_related = "away" in path.lower() or "fora" in path.lower() or "visit" in path.lower()
                    
                    if is_home_related or is_away_related:
                        # Verificar se tem estatísticas
                        has_stats = any(key in obj for key in ["played", "matches_played", "wins", "goals_scored", "xg", "form"])
                        
                        if has_stats:
                            target_dict = home_found if is_home_related else away_found
                            logger.info(f"Encontradas estatísticas para {'casa' if is_home_related else 'visitante'} em {path}")
                            extract_stats_recursive(obj, target_dict, path)
                
                # Verificar se este objeto parece ser dados H2H
                if ("h2h" in path.lower() or "head" in path.lower() or "vs" in path.lower()) and not h2h_found:
                    # Verificar se tem estatísticas H2H
                    has_h2h = any(key in obj for key in ["total_matches", "home_wins", "away_wins", "draws"])
                    
                    if has_h2h:
                        logger.info(f"Encontrados dados H2H em {path}")
                        
                        # Extrair campos H2H com uma lista ampla de possíveis nomes
                        h2h_fields = {
                            "total_matches": ["total_matches", "totalMatches", "matches", "total", "count", "jogos", "partidas"],
                            "home_wins": ["home_wins", "homeWins", "home", "local", "casa"],
                            "away_wins": ["away_wins", "awayWins", "away", "visitante", "fora"],
                            "draws": ["draws", "draw", "equal", "empates", "empate"],
                            "avg_goals": ["avg_goals", "avgGoals", "goals_avg", "media_gols", "mediaGols"],
                            "over_2_5_pct": ["over_2_5_percentage", "over25", "mais2_5"],
                            "btts_pct": ["btts_percentage", "btts", "ambos_marcam"],
                            "avg_cards": ["avg_cards", "avgCards", "media_cartoes"],
                            "avg_corners": ["avg_corners", "avgCorners", "media_escanteios"]
                        }
                        
                        for target, sources in h2h_fields.items():
                            for src in sources:
                                if src in obj:
                                    try:
                                        if obj[src] is not None and obj[src] != 'N/A':
                                            h2h_found[target] = float(obj[src])
                                            break
                                    except (ValueError, TypeError):
                                        pass
                
                # Continuar buscando recursivamente em todas as chaves
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    deep_search(value, new_path)
            
            elif isinstance(obj, list):
                # Buscar em cada item da lista
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]"
                    deep_search(item, new_path)
        
        # Iniciar busca profunda
        deep_search(api_data)
        
        # FASE 4: Verificar dados específicos de forma (form)
        
        # Tentar extrair dados de forma de times
        if "team_form" in api_data:
            if "home" in api_data["team_form"] and isinstance(api_data["team_form"]["home"], list):
                form_string = ""
                for match in api_data["team_form"]["home"][:5]:
                    if isinstance(match, dict) and "result" in match:
                        form_string += match["result"]
                    else:
                        form_string += "?"
                
                if form_string:
                    home_found["form"] = form_string.ljust(5, '?')[:5]
                    home_found["formRun_overall"] = form_string.ljust(5, '?')[:5]
                    logger.info(f"Encontrada forma do time da casa: {form_string}")
            
            if "away" in api_data["team_form"] and isinstance(api_data["team_form"]["away"], list):
                form_string = ""
                for match in api_data["team_form"]["away"][:5]:
                    if isinstance(match, dict) and "result" in match:
                        form_string += match["result"]
                    else:
                        form_string += "?"
                
                if form_string:
                    away_found["form"] = form_string.ljust(5, '?')[:5]
                    away_found["formRun_overall"] = form_string.ljust(5, '?')[:5]
                    logger.info(f"Encontrada forma do time visitante: {form_string}")
        
        # FASE 5: Combinar todos os dados encontrados
        
        # Copiar dados encontrados para o resultado
        for key, value in home_found.items():
            if value is not None and (
                (isinstance(value, (int, float)) and value != 0) or 
                (isinstance(value, str) and value != "" and value != "?????")
            ):
                result["home_team"][key] = value
        
        for key, value in away_found.items():
            if value is not None and (
                (isinstance(value, (int, float)) and value != 0) or 
                (isinstance(value, str) and value != "" and value != "?????")
            ):
                result["away_team"][key] = value
        
        for key, value in h2h_found.items():
            if value is not None and (isinstance(value, (int, float)) and value != 0):
                result["h2h"][key] = value
        
        # Calcular estatísticas derivadas se temos jogos disputados
        for team_key, team_dict in [("home_team", result["home_team"]), ("away_team", result["away_team"])]:
            played = team_dict.get("played", 0)
            
            if played > 0:
                # Calcular percentuais win/draw/loss
                if "wins" in team_dict and "win_pct" not in team_dict:
                    team_dict["win_pct"] = round((team_dict["wins"] / played) * 100, 1)
                if "draws" in team_dict and "draw_pct" not in team_dict:
                    team_dict["draw_pct"] = round((team_dict["draws"] / played) * 100, 1)
                if "losses" in team_dict and "loss_pct" not in team_dict:
                    team_dict["loss_pct"] = round((team_dict["losses"] / played) * 100, 1)
                
                # Calcular médias por jogo
                if "goals_scored" in team_dict and "goals_per_game" not in team_dict:
                    team_dict["goals_per_game"] = round(team_dict["goals_scored"] / played, 2)
                if "goals_conceded" in team_dict and "conceded_per_game" not in team_dict:
                    team_dict["conceded_per_game"] = round(team_dict["goals_conceded"] / played, 2)
        
        # Verificar total de jogos H2H
        if "total_matches" not in result["h2h"] or result["h2h"]["total_matches"] == 0:
            total = (
                result["h2h"].get("home_wins", 0) + 
                result["h2h"].get("away_wins", 0) + 
                result["h2h"].get("draws", 0)
            )
            if total > 0:
                result["h2h"]["total_matches"] = total
        
        # Log dos resultados finais da extração
        if log_details:
            home_count = count_non_zero_fields(result["home_team"])
            away_count = count_non_zero_fields(result["away_team"])
            h2h_count = count_non_zero_fields(result["h2h"])
            
            logger.info(f"Extração completa: {home_count} campos não-zero para casa, {away_count} para fora, {h2h_count} para H2H")
        
        return result
        
    except Exception as e:
        logger.error(f"Erro durante a extração profunda: {str(e)}")
        logger.error(traceback.format_exc())
        return result        
# Função para extrair estatísticas específicas dos dicionários que encontramos
def extract_stats_recursive(source, target, path=""):
    """
    Extrai estatísticas de um dicionário para outro de forma recursiva,
    buscando por múltiplos nomes possíveis para os mesmos campos.
    
    Args:
        source (dict): Dicionário fonte das estatísticas
        target (dict): Dicionário alvo para armazenar as estatísticas
        path (str): Caminho atual para logging
    """
    import logging
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    if not isinstance(source, dict):
        return
    
    # Mapeamento abrangente de campo estatístico → possíveis nomes na API
    field_mapping = {
        # Estatísticas Gerais
        "played": ["played", "matches_played", "seasonMatchesPlayed_overall", "MP", "PJ", "Games", "total_matches", "games"],
        "seasonMatchesPlayed_overall": ["seasonMatchesPlayed_overall", "matches_played", "MP", "games_played", "total_matches"],
        "wins": ["wins", "seasonWinsNum_overall", "W", "Wins", "win", "team_wins", "won", "victorias", "vitorias"],
        "seasonWinsNum_overall": ["seasonWinsNum_overall", "wins", "W", "won", "victorias", "total_wins"],
        "draws": ["draws", "seasonDrawsNum_overall", "D", "Draws", "draw", "team_draws", "empates", "tied"],
        "seasonDrawsNum_overall": ["seasonDrawsNum_overall", "draws", "D", "drawn", "empates", "total_draws"],
        "losses": ["losses", "seasonLossesNum_overall", "L", "Losses", "loss", "team_losses", "defeats", "derrotas", "lost"],
        "seasonLossesNum_overall": ["seasonLossesNum_overall", "losses", "L", "lost", "derrotas", "total_losses"],
        "win_pct": ["win_percentage", "winPercentage", "win_pct", "win_rate", "victory_rate", "pct_wins"],
        "draw_pct": ["draw_percentage", "drawPercentage", "draw_pct", "draw_rate", "pct_draws"],
        "loss_pct": ["loss_percentage", "lossPercentage", "loss_pct", "loss_rate", "defeat_rate", "pct_losses"],
        "form": ["form", "recent_form", "formRun_overall", "form_string", "team_form", "last_matches"],
        "formRun_overall": ["formRun_overall", "form", "recent_form", "form_string", "overall_form"],
        "seasonPPG_overall": ["seasonPPG_overall", "ppg", "points_per_game", "pts_per_game", "average_points"],
        "seasonRecentPPG": ["seasonRecentPPG", "recent_ppg", "recent_points_per_game", "last5_ppg"],
        "leaguePosition_overall": ["leaguePosition_overall", "league_position", "position", "rank", "table_position"],
        
        # Casa/Fora específicos
        "home_played": ["home_played", "seasonMatchesPlayed_home", "matches_played_home", "games_home", "home_games"],
        "seasonMatchesPlayed_home": ["seasonMatchesPlayed_home", "home_played", "matches_played_home", "home_games"],
        "away_played": ["away_played", "seasonMatchesPlayed_away", "matches_played_away", "games_away", "away_games"],
        "seasonMatchesPlayed_away": ["seasonMatchesPlayed_away", "away_played", "matches_played_away", "away_games"],
        "home_wins": ["home_wins", "seasonWinsNum_home", "wins_home", "home_won", "victorias_casa"],
        "seasonWinsNum_home": ["seasonWinsNum_home", "home_wins", "wins_home", "home_victories"],
        "away_wins": ["away_wins", "seasonWinsNum_away", "wins_away", "away_won", "victorias_fuera"],
        "seasonWinsNum_away": ["seasonWinsNum_away", "away_wins", "wins_away", "away_victories"],
        "home_draws": ["home_draws", "seasonDrawsNum_home", "draws_home", "home_drawn", "empates_casa"],
        "seasonDrawsNum_home": ["seasonDrawsNum_home", "home_draws", "draws_home", "home_tied"],
        "away_draws": ["away_draws", "seasonDrawsNum_away", "draws_away", "away_drawn", "empates_fuera"],
        "seasonDrawsNum_away": ["seasonDrawsNum_away", "away_draws", "draws_away", "away_tied"],
        "home_losses": ["home_losses", "seasonLossesNum_home", "losses_home", "home_lost", "derrotas_casa"],
        "seasonLossesNum_home": ["seasonLossesNum_home", "home_losses", "losses_home", "home_defeats"],
        "away_losses": ["away_losses", "seasonLossesNum_away", "losses_away", "away_lost", "derrotas_fuera"],
        "seasonLossesNum_away": ["seasonLossesNum_away", "away_losses", "losses_away", "away_defeats"],
        "home_form": ["home_form", "formRun_home", "form_home", "home_recent_form", "casa_forma"],
        "formRun_home": ["formRun_home", "home_form", "form_home", "home_recent_form"],
        "away_form": ["away_form", "formRun_away", "form_away", "away_recent_form", "fora_forma"],
        "formRun_away": ["formRun_away", "away_form", "form_away", "away_recent_form"],
        "seasonPPG_home": ["seasonPPG_home", "home_ppg", "points_per_game_home", "home_average_points"],
        "seasonPPG_away": ["seasonPPG_away", "away_ppg", "points_per_game_away", "away_average_points"],
        "leaguePosition_home": ["leaguePosition_home", "home_league_position", "position_home", "home_rank"],
        "leaguePosition_away": ["leaguePosition_away", "away_league_position", "position_away", "away_rank"],
        
        # Gols
        "goals_scored": ["goals_scored", "seasonScoredNum_overall", "scored", "GF", "goals_for", "GoalsFor", "goals"],
        "seasonScoredNum_overall": ["seasonScoredNum_overall", "goals_scored", "scored", "GF", "total_goals_for"],
        "goals_conceded": ["goals_conceded", "seasonConcededNum_overall", "conceded", "GA", "goals_against", "GoalsAgainst"],
        "seasonConcededNum_overall": ["seasonConcededNum_overall", "goals_conceded", "conceded", "GA", "total_goals_against"],
        "home_goals_scored": ["home_goals_scored", "seasonScoredNum_home", "goals_scored_home", "home_GF", "home_goals"],
        "seasonScoredNum_home": ["seasonScoredNum_home", "home_goals_scored", "goals_scored_home", "home_goals_for"],
        "away_goals_scored": ["away_goals_scored", "seasonScoredNum_away", "goals_scored_away", "away_GF", "away_goals"],
        "seasonScoredNum_away": ["seasonScoredNum_away", "away_goals_scored", "goals_scored_away", "away_goals_for"],
        "home_goals_conceded": ["home_goals_conceded", "seasonConcededNum_home", "goals_conceded_home", "home_GA"],
        "seasonConcededNum_home": ["seasonConcededNum_home", "home_goals_conceded", "goals_conceded_home", "home_goals_against"],
        "away_goals_conceded": ["away_goals_conceded", "seasonConcededNum_away", "goals_conceded_away", "away_GA"],
        "seasonConcededNum_away": ["seasonConcededNum_away", "away_goals_conceded", "goals_conceded_away", "away_goals_against"],
        "goals_per_game": ["goals_per_game", "gpg", "goals_per_match", "avg_goals_for", "average_goals_scored"],
        "conceded_per_game": ["conceded_per_game", "cpg", "conceded_per_match", "avg_goals_against", "average_goals_conceded"],
        "seasonGoalsTotal_overall": ["seasonGoalsTotal_overall", "total_goals", "goals_total", "all_goals", "total_match_goals"],
        "seasonGoalsTotal_home": ["seasonGoalsTotal_home", "total_goals_home", "home_goals_total", "home_match_goals"],
        "seasonGoalsTotal_away": ["seasonGoalsTotal_away", "total_goals_away", "away_goals_total", "away_match_goals"],
        "clean_sheets_pct": ["clean_sheets_pct", "clean_sheet_percentage", "cs_pct", "percentage_cs", "pct_clean_sheets"],
        "seasonCSPercentage_overall": ["seasonCSPercentage_overall", "clean_sheet_percentage", "cs_pct", "pct_clean_sheets"],
        "seasonCS_overall": ["seasonCS_overall", "clean_sheets", "cs", "total_clean_sheets", "shutouts"],
        "seasonCS_home": ["seasonCS_home", "home_clean_sheets", "cs_home", "clean_sheets_home", "home_shutouts"],
        "seasonCS_away": ["seasonCS_away", "away_clean_sheets", "cs_away", "clean_sheets_away", "away_shutouts"],
        "btts_pct": ["btts_pct", "btts_percentage", "both_teams_scored_pct", "pct_btts", "ambos_marcam_pct"],
        "seasonBTTSPercentage_overall": ["seasonBTTSPercentage_overall", "btts_percentage", "both_teams_to_score_pct", "pct_btts"],
        "over_2_5_pct": ["over_2_5_pct", "over_2_5_percentage", "o25_pct", "pct_over_25", "mais_25_pct"],
        "seasonOver25Percentage_overall": ["seasonOver25Percentage_overall", "over_2_5_percentage", "o25_pct", "pct_over_25"],
        
        # Expected Goals
        "xg": ["xg", "xG", "expected_goals", "xg_for", "ExpG", "xGF"],
        "xg_for_overall": ["xg_for_overall", "xg", "xG", "expected_goals", "total_xg"],
        "xga": ["xga", "xGA", "expected_goals_against", "xg_against", "ExpGA", "xGAg"],
        "xg_against_overall": ["xg_against_overall", "xga", "xGA", "expected_goals_against", "total_xga"],
        "home_xg": ["home_xg", "xg_home", "xg_for_home", "home_expected_goals", "xg_h"],
        "xg_for_home": ["xg_for_home", "home_xg", "xg_home", "home_expected_goals", "xG_home"],
        "away_xg": ["away_xg", "xg_away", "xg_for_away", "away_expected_goals", "xg_a"],
        "xg_for_away": ["xg_for_away", "away_xg", "xg_away", "away_expected_goals", "xG_away"],
        "home_xga": ["home_xga", "xga_home", "xg_against_home", "home_expected_goals_against", "xGA_home"],
        "xg_against_home": ["xg_against_home", "home_xga", "xga_home", "home_expected_goals_against"],
        "away_xga": ["away_xga", "xga_away", "xg_against_away", "away_expected_goals_against", "xGA_away"],
        "xg_against_away": ["xg_against_away", "away_xga", "xga_away", "away_expected_goals_against"],
        "xg_for_avg_overall": ["xg_for_avg_overall", "xg_per_game", "expected_goals_per_game", "avg_xg", "xg_avg"],
        "xg_for_avg_home": ["xg_for_avg_home", "xg_per_game_home", "expected_goals_per_game_home", "home_avg_xg"],
        "xg_for_avg_away": ["xg_for_avg_away", "xg_per_game_away", "expected_goals_per_game_away", "away_avg_xg"],
        "xg_against_avg_overall": ["xg_against_avg_overall", "xga_per_game", "expected_goals_against_per_game", "avg_xga"],
        "xg_against_avg_home": ["xg_against_avg_home", "xga_per_game_home", "expected_goals_against_per_game_home", "home_avg_xga"],
        "xg_against_avg_away": ["xg_against_avg_away", "xga_per_game_away", "expected_goals_against_per_game_away", "away_avg_xga"],
        
        # Cartões
        "cards_per_game": ["cards_per_game", "cards_avg", "avg_cards", "average_cards", "cards_per_match"],
        "cardsAVG_overall": ["cardsAVG_overall", "cards_per_game", "cards_avg", "avg_cards", "average_cards"],
        "home_cards_per_game": ["home_cards_per_game", "cards_per_game_home", "home_cards_avg", "home_avg_cards"],
        "cardsAVG_home": ["cardsAVG_home", "home_cards_per_game", "cards_per_game_home", "home_cards_avg"],
        "away_cards_per_game": ["away_cards_per_game", "cards_per_game_away", "away_cards_avg", "away_avg_cards"],
        "cardsAVG_away": ["cardsAVG_away", "away_cards_per_game", "cards_per_game_away", "away_cards_avg"],
        "cardsTotal_overall": ["cardsTotal_overall", "total_cards", "cards_total", "cards", "all_cards"],
        "cardsTotal_home": ["cardsTotal_home", "total_cards_home", "cards_total_home", "home_cards"],
        "cardsTotal_away": ["cardsTotal_away", "total_cards_away", "cards_total_away", "away_cards"],
        "yellow_cards": ["yellow_cards", "yellows", "cards_yellow", "CrdY", "YellowCards", "yellow"],
        "red_cards": ["red_cards", "reds", "cards_red", "CrdR", "RedCards", "red"],
        "over_3_5_cards_pct": ["over_3_5_cards_pct", "over_3_5_cards_percentage", "o35_cards_pct", "pct_over_35_cards"],
        
        # Escanteios
        "corners_per_game": ["corners_per_game", "corners_avg", "avg_corners", "average_corners", "corners_per_match"],
        "cornersTotalAVG_overall": ["cornersTotalAVG_overall", "corners_per_game", "corners_avg", "avg_corners"],
        "home_corners_per_game": ["home_corners_per_game", "corners_per_game_home", "home_corners_avg", "home_avg_corners"],
        "cornersTotalAVG_home": ["cornersTotalAVG_home", "home_corners_per_game", "corners_per_game_home", "home_corners_avg"],
        "away_corners_per_game": ["away_corners_per_game", "corners_per_game_away", "away_corners_avg", "away_avg_corners"],
        "cornersTotalAVG_away": ["cornersTotalAVG_away", "away_corners_per_game", "corners_per_game_away", "away_corners_avg"],
        "corners_for": ["corners_for", "cornersTotal_overall", "corners", "CK", "Corners", "attacking_corners"],
        "cornersTotal_overall": ["cornersTotal_overall", "corners_for", "corners", "total_corners_for"],
        "corners_against": ["corners_against", "cornersAgainst_overall", "corners_against_total", "defensive_corners"],
        "cornersAgainst_overall": ["cornersAgainst_overall", "corners_against", "corners_against_total"],
        "cornersAVG_overall": ["cornersAVG_overall", "corners_for_avg", "corners_for_per_game", "avg_corners_for"],
        "cornersAVG_home": ["cornersAVG_home", "corners_for_avg_home", "corners_for_per_game_home", "home_avg_corners_for"],
        "cornersAVG_away": ["cornersAVG_away", "corners_for_avg_away", "corners_for_per_game_away", "away_avg_corners_for"],
        "cornersAgainstAVG_overall": ["cornersAgainstAVG_overall", "corners_against_avg", "corners_against_per_game", "avg_corners_against"],
        "cornersAgainstAVG_home": ["cornersAgainstAVG_home", "corners_against_avg_home", "corners_against_per_game_home", "home_avg_corners_against"],
        "cornersAgainstAVG_away": ["cornersAgainstAVG_away", "corners_against_avg_away", "corners_against_per_game_away", "away_avg_corners_against"],
        "over_9_5_corners_pct": ["over_9_5_corners_pct", "over_9_5_corners_percentage", "o95_corners_pct", "pct_over_95_corners"],
        
        # Chutes
        "shotsAVG_overall": ["shotsAVG_overall", "shots_per_game", "shots_avg", "average_shots", "avg_shots"],
        "shotsAVG_home": ["shotsAVG_home", "shots_per_game_home", "shots_avg_home", "home_avg_shots"],
        "shotsAVG_away": ["shotsAVG_away", "shots_per_game_away", "shots_avg_away", "away_avg_shots"],
        "shotsOnTargetAVG_overall": ["shotsOnTargetAVG_overall", "shots_on_target_per_game", "sot_avg", "shots_on_target_avg", "avg_shots_on_target"],
        "shotsOnTargetAVG_home": ["shotsOnTargetAVG_home", "shots_on_target_per_game_home", "sot_avg_home", "home_avg_shots_on_target"],
        "shotsOnTargetAVG_away": ["shotsOnTargetAVG_away", "shots_on_target_per_game_away", "sot_avg_away", "away_avg_shots_on_target"],
        
        # Posse de Bola
        "possession": ["possession", "possessionAVG_overall", "possession_avg", "avg_possession", "Poss", "posesion"],
        "possessionAVG_overall": ["possessionAVG_overall", "possession", "possession_avg", "average_possession"],
        "home_possession": ["home_possession", "possessionAVG_home", "possession_home", "home_poss", "casa_posesion"],
        "possessionAVG_home": ["possessionAVG_home", "home_possession", "possession_home", "home_average_possession"],
        "away_possession": ["away_possession", "possessionAVG_away", "possession_away", "away_poss", "fora_posesion"],
        "possessionAVG_away": ["possessionAVG_away", "away_possession", "possession_away", "away_average_possession"]
    }
    
    # Extrair cada campo usando todos os nomes possíveis
    for target_field, source_fields in field_mapping.items():
        if target_field not in target:  # Somente se o campo ainda não existe no alvo
            for field in source_fields:
                if field in source:
                    value = source[field]
                    if value is not None and value != 'N/A' and value != '':
                        try:
                            # Para form e similares (campos de texto)
                            if target_field in ["form", "home_form", "away_form", "formRun_overall", "formRun_home", "formRun_away"]:
                                if isinstance(value, str):
                                    target[target_field] = value[:5]  # Limitar a 5 caracteres
                                    if target_field == "form":
                                        logger.info(f"Encontrada forma: {value[:5]} em {path}.{field}")
                                break
                            
                            # Para valores numéricos
                            float_value = float(value)
                            target[target_field] = float_value
                            
                            # Log para campos importantes (somente alguns para evitar spam)
                            if target_field in ["played", "wins", "goals_scored", "xg", "form"]:
                                logger.info(f"Encontrado {target_field}={float_value} em {path}.{field}")
                                
                            break
                        except (ValueError, TypeError):
                            pass
    
    # Verificar subchaves importantes
    for subkey in ["stats", "statistics", "seasonStats", "data", "season_stats"]:
        if subkey in source and isinstance(source[subkey], dict):
            extract_stats_recursive(source[subkey], target, f"{path}.{subkey}")
def validate_stats_for_agent(stats_data):
    """
    Valida os dados estatísticos antes de enviar para o agente IA.
    
    Args:
        stats_data (dict): Dados formatados para enviar ao agente
        
    Returns:
        dict: Dados validados e corrigidos
    """
    import logging
    import copy
    
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    if not stats_data or not isinstance(stats_data, dict):
        logger.error("Dados estatísticos inválidos ou vazios")
        return stats_data
    
    # Clonar dados para não modificar o original
    validated_data = copy.deepcopy(stats_data)
    
    # Verificar e corrigir problemas em cada time
    for team_key in ["home_team", "away_team"]:
        if team_key not in validated_data:
            continue
            
        team_data = validated_data[team_key]
        team_name = validated_data.get("match_info", {}).get(team_key, "Time")
        
        # 1. Verificar forma inválida
        if "form" in team_data:
            form = team_data["form"]
            
            # Verificar se a forma é inválida (todos iguais ou ?????)
            if form in ["WWWWW", "DDDDD", "LLLLL", "?????"]:
                logger.warning(f"Forma inválida detectada para {team_name}: {form}")
                
                # Tentar derivar uma forma mais realista das estatísticas
                if all(stat in team_data for stat in ["win_pct", "draw_pct", "loss_pct"]):
                    import random
                    
                    # Usar as porcentagens para gerar uma forma mais realista
                    new_form = ""
                    for _ in range(5):
                        r = random.random() * 100
                        if r < team_data["win_pct"]:
                            new_form += "W"
                        elif r < (team_data["win_pct"] + team_data["draw_pct"]):
                            new_form += "D"
                        else:
                            new_form += "L"
                    
                    logger.info(f"Forma corrigida para {team_name}: {form} -> {new_form}")
                    team_data["form"] = new_form
        
        # 2. Verificar porcentagens inválidas
        for field in ["win_pct", "draw_pct", "loss_pct", "clean_sheets_pct", 
                    "btts_pct", "over_2_5_pct", "over_3_5_cards_pct", 
                    "over_9_5_corners_pct"]:
            if field in team_data and (team_data[field] < 0 or team_data[field] > 100):
                logger.warning(f"Porcentagem inválida em {team_name}.{field}: {team_data[field]}")
                team_data[field] = max(0, min(100, team_data[field]))
        
        # 3. Verificar consistência entre jogos e resultados
        if "played" in team_data and team_data["played"] > 0:
            if all(k in team_data for k in ["wins", "draws", "losses"]):
                total = team_data["wins"] + team_data["draws"] + team_data["losses"]
                if abs(total - team_data["played"]) > 1:  # Permitir pequena diferença
                    logger.warning(f"Discrepância nos jogos de {team_name}: played={team_data['played']}, soma={total}")
                    
                    # Se a diferença é significativa, ajustar porcentagens
                    if "win_pct" in team_data and "draw_pct" in team_data and "loss_pct" in team_data:
                        # Recalcular porcentagens com base nos jogos
                        if total > 0:
                            team_data["win_pct"] = round((team_data["wins"] / total) * 100, 1)
                            team_data["draw_pct"] = round((team_data["draws"] / total) * 100, 1)
                            team_data["loss_pct"] = round((team_data["losses"] / total) * 100, 1)
        
        # 4. Verificar estatísticas de gols
        if "goals_scored" in team_data and "goals_per_game" not in team_data and "played" in team_data and team_data["played"] > 0:
            team_data["goals_per_game"] = round(team_data["goals_scored"] / team_data["played"], 2)
            
        if "goals_conceded" in team_data and "conceded_per_game" not in team_data and "played" in team_data and team_data["played"] > 0:
            team_data["conceded_per_game"] = round(team_data["goals_conceded"] / team_data["played"], 2)
    
    # Verificar dados de H2H
    if "h2h" in validated_data:
        h2h = validated_data["h2h"]
        
        # Verificar se total_matches é consistente com os resultados
        if "total_matches" in h2h and "home_wins" in h2h and "away_wins" in h2h and "draws" in h2h:
            total = h2h["home_wins"] + h2h["away_wins"] + h2h["draws"]
            if h2h["total_matches"] == 0 and total > 0:
                logger.warning(f"H2H total_matches=0 mas soma={total}")
                h2h["total_matches"] = total
            elif h2h["total_matches"] > 0 and total > 0 and abs(h2h["total_matches"] - total) > 1:
                logger.warning(f"Discrepância em H2H: total_matches={h2h['total_matches']}, soma={total}")
                
                # Recalcular porcentagens se necessário
                if "over_2_5_pct" in h2h and "btts_pct" in h2h:
                    # Nenhum ajuste automático, apenas log
                    logger.warning("Porcentagens de H2H podem não ser precisas devido à discrepância nos totais")
        
        # Verificar porcentagens
        for field in ["over_2_5_pct", "btts_pct"]:
            if field in h2h and (h2h[field] < 0 or h2h[field] > 100):
                logger.warning(f"Porcentagem inválida em h2h.{field}: {h2h[field]}")
                h2h[field] = max(0, min(100, h2h[field]))
    
    logger.info("Validação de dados concluída com sucesso")
    return validated_data
def alternative_paths_extraction(api_data, formatted_data, home_team_name, away_team_name):
    """
    Busca estatísticas em caminhos alternativos específicos de algumas APIs.
    
    Args:
        api_data (dict): Dados originais da API
        formatted_data (dict): Dados formatados a serem preenchidos
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
    """
    import logging
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    # Extrair dados do caminho teams[].stats
    if "teams" in api_data and isinstance(api_data["teams"], list):
        for i, team in enumerate(api_data["teams"]):
            if isinstance(team, dict) and "name" in team:
                # Determinar se é time da casa ou visitante
                is_home = False
                is_away = False
                
                # Comparação direta
                if team["name"] == home_team_name:
                    is_home = True
                elif team["name"] == away_team_name:
                    is_away = True
                
                # Ou por correspondência parcial
                if not is_home and not is_away:
                    if home_team_name.lower() in team["name"].lower():
                        is_home = True
                    elif away_team_name.lower() in team["name"].lower():
                        is_away = True
                
                # Se encontramos um time, extrair estatísticas
                if is_home or is_away:
                    target_dict = formatted_data["home_team"] if is_home else formatted_data["away_team"]
                    target_name = home_team_name if is_home else away_team_name
                    
                    logger.info(f"Encontrados dados de time em teams[{i}] para {target_name}")
                    
                    # Extrair estatísticas
                    if "stats" in team and isinstance(team["stats"], dict):
                        logger.info(f"Extraindo estatísticas de teams[{i}].stats")
                        extract_stats_recursive(team["stats"], target_dict, f"teams[{i}].stats")
                    
                    # Extrair diretamente do time
                    extract_stats_recursive(team, target_dict, f"teams[{i}]")
    
    # Extrair dados do caminho statistics
    if "statistics" in api_data:
        stats = api_data["statistics"]
        
        if isinstance(stats, dict):
            # Verificar home/away em statistics
            for team_type in ["home", "away"]:
                if team_type in stats and isinstance(stats[team_type], dict):
                    target_dict = formatted_data["home_team"] if team_type == "home" else formatted_data["away_team"]
                    logger.info(f"Extraindo estatísticas de statistics.{team_type}")
                    extract_stats_recursive(stats[team_type], target_dict, f"statistics.{team_type}")
            
            # Verificar também structure mais plana com prefixos home_/away_
            home_prefixed = {}
            away_prefixed = {}
            
            for key, value in stats.items():
                if key.startswith("home_"):
                    home_prefixed[key.replace("home_", "")] = value
                elif key.startswith("away_"):
                    away_prefixed[key.replace("away_", "")] = value
            
            if home_prefixed:
                logger.info(f"Extraindo estatísticas de statistics com prefixo home_")
                extract_stats_recursive(home_prefixed, formatted_data["home_team"], "statistics.home_prefixed")
            
            if away_prefixed:
                logger.info(f"Extraindo estatísticas de statistics com prefixo away_")
                extract_stats_recursive(away_prefixed, formatted_data["away_team"], "statistics.away_prefixed")
    
    # Extrair dados do caminho lineup.home/away.statistics
    if "lineup" in api_data and isinstance(api_data["lineup"], dict):
        for team_type in ["home", "away"]:
            if team_type in api_data["lineup"] and isinstance(api_data["lineup"][team_type], dict):
                if "statistics" in api_data["lineup"][team_type]:
                    target_dict = formatted_data["home_team"] if team_type == "home" else formatted_data["away_team"]
                    logger.info(f"Extraindo estatísticas de lineup.{team_type}.statistics")
                    extract_stats_recursive(api_data["lineup"][team_type]["statistics"], target_dict, f"lineup.{team_type}.statistics")
    
    # Extrair dados do caminho data.teams
    if "data" in api_data and isinstance(api_data["data"], dict) and "teams" in api_data["data"]:
        teams = api_data["data"]["teams"]
        
        if isinstance(teams, dict):
            # Verificar home/away em data.teams
            for team_type in ["home", "away"]:
                if team_type in teams and isinstance(teams[team_type], dict):
                    target_dict = formatted_data["home_team"] if team_type == "home" else formatted_data["away_team"]
                    logger.info(f"Extraindo estatísticas de data.teams.{team_type}")
                    extract_stats_recursive(teams[team_type], target_dict, f"data.teams.{team_type}")
