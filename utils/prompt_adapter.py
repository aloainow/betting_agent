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

def extract_team_stats(target, stats_data, team_raw_data, team_type):
    """Extrai estatísticas com melhores mapeamentos e fallbacks"""
    
    # NOVO: Mapeamento expandido com mais nomes alternativos para cada campo
    mappings = {
        "played": ["matches_played", "seasonMatchesPlayed_overall", "MP", "PJ", "Games"],
        "wins": ["wins", "seasonWinsNum_overall", "W", "Wins"],
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
    
    # Adicionar campos específicos com base no tipo de time
    if team_type == "home":
        specific_fields = {
            "home_played": ["matches_played_home", "seasonMatchesPlayed_home", "home_matches"],
            "home_wins": ["home_wins", "seasonWinsNum_home", "wins_home"],
            "home_draws": ["home_draws", "seasonDrawsNum_home", "draws_home"],
            "home_losses": ["home_losses", "seasonLossesNum_home", "losses_home"],
            "home_goals_scored": ["goals_scored_home", "seasonGoals_home"],
            "home_goals_conceded": ["goals_conceded_home", "seasonConceded_home"],
            "home_cards_per_game": ["cards_per_game_home", "cardsAVG_home", "seasonCardsAVG_home"],
            "home_corners_per_game": ["corners_per_game_home", "cornersAVG_home", "cornersTotalAVG_home"]
        }
    else:  # visitante
        specific_fields = {
            "away_played": ["matches_played_away", "seasonMatchesPlayed_away", "away_matches"],
            "away_wins": ["away_wins", "seasonWinsNum_away", "wins_away"],
            "away_draws": ["away_draws", "seasonDrawsNum_away", "draws_away"],
            "away_losses": ["away_losses", "seasonLossesNum_away", "losses_away"],
            "away_goals_scored": ["goals_scored_away", "seasonGoals_away"],
            "away_goals_conceded": ["goals_conceded_away", "seasonConceded_away"],
            "away_cards_per_game": ["cards_per_game_away", "cardsAVG_away", "seasonCardsAVG_away"],
            "away_corners_per_game": ["corners_per_game_away", "cornersAVG_away", "cornersTotalAVG_away"]
        }
        
    mappings.update(specific_fields)
    
    # NOVO: Também buscar valores através das chaves em maiúsculas/minúsculas
    # criando um mapeamento que também inclui versões em maiúsculas e minúsculas
    case_insensitive_data = {}
    if isinstance(stats_data, dict):
        for key, value in stats_data.items():
            case_insensitive_data[key.lower()] = value
    
    # Extrair cada campo usando mapeamentos
    for target_field, source_fields in mappings.items():
        # Tentar os campos originais primeiro
        found = False
        for field in source_fields:
            # 1. Tentar correspondência exata
            if isinstance(stats_data, dict) and field in stats_data:
                value = stats_data[field]
                if value is not None and value != 'N/A':
                    try:
                        # Converter para float para valores numéricos
                        target[target_field] = float(value)
                        found = True
                        break
                    except (ValueError, TypeError):
                        pass
                        
            # 2. Tentar correspondência em minúsculas
            field_lower = field.lower()
            if not found and field_lower in case_insensitive_data:
                value = case_insensitive_data[field_lower]
                if value is not None and value != 'N/A':
                    try:
                        target[target_field] = float(value)
                        found = True
                        break
                    except (ValueError, TypeError):
                        pass
        
        # 3. Tentar buscar direto no objeto team_raw_data
        if not found and isinstance(team_raw_data, dict):
            for field in source_fields:
                if field in team_raw_data:
                    value = team_raw_data[field]
                    if value is not None and value != 'N/A':
                        try:
                            target[target_field] = float(value)
                            found = True
                            break
                        except (ValueError, TypeError):
                            pass
    
    # Buscar em stats se existir como um objeto aninhado
    if isinstance(team_raw_data, dict) and "stats" in team_raw_data and isinstance(team_raw_data["stats"], dict):
        nested_stats = team_raw_data["stats"]
        for target_field, source_fields in mappings.items():
            # Pular se já encontrado
            if target[target_field] != 0:
                continue
                
            for field in source_fields:
                if field in nested_stats:
                    value = nested_stats[field]
                    if value is not None and value != 'N/A':
                        try:
                            target[target_field] = float(value)
                            break
                        except (ValueError, TypeError):
                            pass

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
    Extract recent form as a simple string like "WWDLD" instead of an array.
    
    Args:
        api_data (dict): Original API data
        team_type (str): "home" or "away"
        
    Returns:
        str: Form string like "WWDLD"
    """
    form = ""
    
    if "team_form" not in api_data or team_type not in api_data["team_form"]:
        return "?????"
        
    team_form = api_data["team_form"][team_type]
    
    if isinstance(team_form, list) and len(team_form) > 0:
        # Extract up to 5 recent results
        for i in range(min(5, len(team_form))):
            if isinstance(team_form[i], dict) and "result" in team_form[i]:
                form += team_form[i]["result"]
            else:
                form += "?"
    elif isinstance(team_form, dict) and "data" in team_form and isinstance(team_form["data"], list):
        # Handle API lastx format
        data = team_form["data"]
        for i in range(min(5, len(data))):
            match = data[i]
            result = "?"
            
            # Try to determine result based on goals
            if "homeGoals" in match and "awayGoals" in match and "teamID" in match:
                if ("homeID" in match and match["homeID"] == match["teamID"]):
                    # Home team
                    if match["homeGoals"] > match["awayGoals"]:
                        result = "W"
                    elif match["homeGoals"] < match["awayGoals"]:
                        result = "L"
                    else:
                        result = "D"
                elif ("awayID" in match and match["awayID"] == match["teamID"]):
                    # Away team
                    if match["homeGoals"] < match["awayGoals"]:
                        result = "W"
                    elif match["homeGoals"] > match["awayGoals"]:
                        result = "L"
                    else:
                        result = "D"
            
            form += result
    
    # Ensure we return exactly 5 characters
    while len(form) < 5:
        form += "?"
        
    return form

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
    Extract team data from API data and fill in the formatted data structure
    
    Args:
        api_data (dict): Original API data
        formatted_data (dict): Target data structure to fill
        team_type (str): "home" or "away" team
    """
    team_key = f"{team_type}_team"
    
    if "basic_stats" in api_data and team_key in api_data["basic_stats"]:
        team_data = api_data["basic_stats"][team_key]
        
        # Extract stats from different possible locations
        stats_data = {}
        
        # Try stats directly on team
        if "stats" in team_data and isinstance(team_data["stats"], dict):
            stats_data = team_data["stats"]
        # Try nested stats
        elif "stats" in team_data and isinstance(team_data["stats"], dict) and "stats" in team_data["stats"]:
            stats_data = team_data["stats"]["stats"]
        
        # Extract each stat field
        extract_team_stats(formatted_data[team_key], stats_data, team_data, team_type)
        
        # Get advanced stats if available
        if "advanced_stats" in api_data and team_type in api_data["advanced_stats"]:
            extract_advanced_metrics(formatted_data[team_key], api_data["advanced_stats"][team_type])

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
    Função unificada para transformar dados da API FootyStats, identificando automaticamente
    o tipo de endpoint e aplicando o extrator adequado.
    
    Args:
        api_data (dict): Dados da API (qualquer endpoint)
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
        selected_markets (dict, optional): Mercados selecionados
        
    Returns:
        dict: Estrutura de dados unificada com estatísticas extraídas
    """
    import logging
    import traceback
    
    logger = logging.getLogger("valueHunter.api_adapter")
    
    # Inicializa a estrutura padrão
    result = {
        "match_info": {
            "home_team": home_team_name,
            "away_team": away_team_name,
            "league": "",
            "league_id": None
        },
        "home_team": {},
        "away_team": {},
        "h2h": {}
    }
    
    if not api_data or not isinstance(api_data, dict):
        logger.error("Dados da API inválidos ou vazios")
        return result
    
    try:
        # Detectar o tipo de endpoint com base na estrutura
        endpoint_type = detect_endpoint_type(api_data)
        logger.info(f"Tipo de endpoint detectado: {endpoint_type}")
        
        # Aplicar o extrator apropriado
        if endpoint_type == "match_details":
            extract_from_match_details(api_data, result, home_team_name, away_team_name)
        elif endpoint_type == "team_lastx":
            extract_from_team_lastx(api_data, result, home_team_name, away_team_name)
        elif endpoint_type == "league_matches":
            extract_from_league_matches(api_data, result, home_team_name, away_team_name)
        elif endpoint_type == "league_teams":
            extract_from_league_teams(api_data, result, home_team_name, away_team_name)
        else:
            # Fallback para extrator genérico
            logger.warning("Tipo de endpoint não identificado. Usando extrator genérico.")
            extract_generic(api_data, result, home_team_name, away_team_name)
        
        # Verificar se temos dados reais extraídos
        home_fields = count_non_zero_fields(result["home_team"])
        away_fields = count_non_zero_fields(result["away_team"])
        h2h_fields = count_non_zero_fields(result["h2h"])
        
        logger.info(f"Campos extraídos - Casa: {home_fields}, Visitante: {away_fields}, H2H: {h2h_fields}")
        
        # Calcular estatísticas derivadas se necessário
        if result["home_team"]:
            calculate_derived_stats(result["home_team"])
        
        if result["away_team"]:
            calculate_derived_stats(result["away_team"])
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao transformar dados da API: {str(e)}")
        logger.error(traceback.format_exc())
        return result

def detect_endpoint_type(api_data):
    """
    Detecta o tipo de endpoint com base na estrutura da resposta
    
    Args:
        api_data (dict): Dados da resposta da API
        
    Returns:
        str: Tipo de endpoint detectado (match_details, team_lastx, league_matches, league_teams)
    """
    # Match Details (data específica de uma partida com h2h, etc.)
    if "data" in api_data and isinstance(api_data["data"], dict) and "h2h" in api_data["data"]:
        return "match_details"
    
    # Team Last X (estatísticas das últimas N partidas)
    if "data" in api_data and isinstance(api_data["data"], list) and len(api_data["data"]) > 0:
        if isinstance(api_data["data"][0], dict) and "formRun_overall" in api_data.get("data", [{}])[0].get("stats", {}):
            return "team_lastx"
    
    # League Matches (lista de partidas de uma liga)
    if "data" in api_data and isinstance(api_data["data"], list) and len(api_data["data"]) > 0:
        if "homeGoals" in api_data["data"][0] and "awayGoals" in api_data["data"][0]:
            return "league_matches"
    
    # League Teams (lista de times com estatísticas)
    if "data" in api_data and isinstance(api_data["data"], list) and len(api_data["data"]) > 0:
        if "stats" in api_data["data"][0] and "seasonMatchesPlayed_overall" in api_data["data"][0].get("stats", {}):
            return "league_teams"
    
    return "unknown"

def extract_from_match_details(api_data, result, home_team_name, away_team_name):
    """
    Extrai dados do endpoint Match Details
    
    Args:
        api_data (dict): Dados da API
        result (dict): Estrutura para armazenar resultados
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
    """
    import logging
    logger = logging.getLogger("valueHunter.api_adapter")
    
    if "data" not in api_data or not isinstance(api_data["data"], dict):
        logger.warning("Estrutura de Match Details inválida")
        return
    
    match_data = api_data["data"]
    
    # Extrair informações da partida
    if "competition_id" in match_data:
        result["match_info"]["league_id"] = match_data["competition_id"]
    
    # Extrair estatísticas do time da casa
    home_team = {}
    away_team = {}
    
    # Estatísticas básicas
    if "team_a_shots" in match_data:
        home_team["shots"] = match_data.get("team_a_shots", 0)
        home_team["shots_on_target"] = match_data.get("team_a_shotsOnTarget", 0)
        home_team["possession"] = match_data.get("team_a_possession", 0)
        home_team["corners_for"] = match_data.get("team_a_corners", 0)
        home_team["cards_total"] = match_data.get("team_a_cards_num", 0)
        home_team["yellow_cards"] = match_data.get("team_a_yellow_cards", 0)
        home_team["red_cards"] = match_data.get("team_a_red_cards", 0)
    
    # Estatísticas do time visitante
    if "team_b_shots" in match_data:
        away_team["shots"] = match_data.get("team_b_shots", 0)
        away_team["shots_on_target"] = match_data.get("team_b_shotsOnTarget", 0)
        away_team["possession"] = match_data.get("team_b_possession", 0)
        away_team["corners_for"] = match_data.get("team_b_corners", 0)
        away_team["cards_total"] = match_data.get("team_b_cards_num", 0)
        away_team["yellow_cards"] = match_data.get("team_b_yellow_cards", 0)
        away_team["red_cards"] = match_data.get("team_b_red_cards", 0)
    
    # Extrair dados xG se disponíveis
    if "team_a_xg" in match_data:
        home_team["xg"] = match_data["team_a_xg"]
    if "team_b_xg" in match_data:
        away_team["xg"] = match_data["team_b_xg"]
    
    # Buscar informações de head-to-head
    if "h2h" in match_data and isinstance(match_data["h2h"], dict):
        h2h_data = match_data["h2h"]
        
        # Extrair estatísticas H2H
        h2h = {}
        
        # Histórico de confrontos
        if "previous_matches_results" in h2h_data:
            h2h_results = h2h_data["previous_matches_results"]
            h2h["total_matches"] = h2h_results.get("totalMatches", 0)
            h2h["home_wins"] = h2h_results.get("team_a_wins", 0)
            h2h["away_wins"] = h2h_results.get("team_b_wins", 0)
            h2h["draws"] = h2h_results.get("draw", 0)
        
        # Estatísticas de apostas/tendências
        if "betting_stats" in h2h_data:
            betting_stats = h2h_data["betting_stats"]
            h2h["over_2_5_pct"] = betting_stats.get("over25Percentage", 0)
            h2h["btts_pct"] = betting_stats.get("bttsPercentage", 0)
            h2h["avg_goals"] = betting_stats.get("avg_goals", 0)
        
        result["h2h"] = h2h
    
    # Atualizar resultados
    result["home_team"] = home_team
    result["away_team"] = away_team
    
    # Tentativa adicional para obter mais dados dos times
    if "home_url" in match_data and "away_url" in match_data:
        team_data = extract_team_data_from_urls(match_data)
        if team_data and "home" in team_data and len(team_data["home"]) > 0:
            result["home_team"].update(team_data["home"])
        if team_data and "away" in team_data and len(team_data["away"]) > 0:
            result["away_team"].update(team_data["away"])

def extract_from_team_lastx(api_data, result, home_team_name, away_team_name):
    """
    Extrai dados do endpoint Team Last X
    
    Args:
        api_data (dict): Dados da API
        result (dict): Estrutura para armazenar resultados
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
    """
    import logging
    logger = logging.getLogger("valueHunter.api_adapter")
    
    if "data" not in api_data or not isinstance(api_data["data"], list):
        logger.warning("Estrutura de Team LastX inválida")
        return
    
    # Pode conter dados de vários times - procurar os times correspondentes
    for team_data in api_data["data"]:
        if not isinstance(team_data, dict) or "name" not in team_data:
            continue
        
        team_name = team_data["name"]
        
        # Identificar se é o time da casa ou visitante
        target_dict = None
        if team_name == home_team_name:
            target_dict = result["home_team"]
            team_type = "home"
        elif team_name == away_team_name:
            target_dict = result["away_team"]
            team_type = "away"
        else:
            continue
        
        # Extrair estatísticas deste time
        if "stats" in team_data and isinstance(team_data["stats"], dict):
            stats = team_data["stats"]
            
            # Mapeamento de campos
            field_mappings = {
                "played": ["seasonMatchesPlayed_overall"],
                "wins": ["seasonWinsNum_overall"],
                "draws": ["seasonDrawsNum_overall"],
                "losses": ["seasonLossesNum_overall"],
                "goals_scored": ["seasonScoredNum_overall", "seasonGoals_overall"],
                "goals_conceded": ["seasonConcededNum_overall"],
                "clean_sheets_pct": ["seasonCSPercentage_overall"],
                "btts_pct": ["seasonBTTSPercentage_overall"],
                "over_2_5_pct": ["seasonOver25Percentage_overall"],
                "possession": ["possessionAVG_overall"],
                "cards_total": ["cardsTotal_overall"],
                "cards_per_game": ["cardsAVG_overall"],
                "corners_per_game": ["cornersAVG_overall", "cornersTotalAVG_overall"],
                "corners_for": ["cornersTotal_overall"],
                "yellow_cards": ["team_a_yellow_cards"],
                "red_cards": ["team_a_red_cards"]
            }
            
            # Campos específicos para casa/fora
            if team_type == "home":
                specific_mappings = {
                    "home_played": ["seasonMatchesPlayed_home"],
                    "home_wins": ["seasonWinsNum_home"],
                    "home_draws": ["seasonDrawsNum_home"],
                    "home_losses": ["seasonLossesNum_home"],
                    "home_goals_scored": ["seasonScoredNum_home", "seasonGoals_home"],
                    "home_goals_conceded": ["seasonConcededNum_home"],
                    "home_cards_per_game": ["cardsAVG_home"],
                    "home_corners_per_game": ["cornersAVG_home"]
                }
                field_mappings.update(specific_mappings)
            elif team_type == "away":
                specific_mappings = {
                    "away_played": ["seasonMatchesPlayed_away"],
                    "away_wins": ["seasonWinsNum_away"],
                    "away_draws": ["seasonDrawsNum_away"],
                    "away_losses": ["seasonLossesNum_away"],
                    "away_goals_scored": ["seasonScoredNum_away", "seasonGoals_away"],
                    "away_goals_conceded": ["seasonConcededNum_away"],
                    "away_cards_per_game": ["cardsAVG_away"],
                    "away_corners_per_game": ["cornersAVG_away"]
                }
                field_mappings.update(specific_mappings)
            
            # Extrair cada campo
            for target_field, source_fields in field_mappings.items():
                for field in source_fields:
                    if field in stats:
                        value = stats[field]
                        try:
                            if value is not None and value != 'N/A':
                                target_dict[target_field] = float(value)
                                break
                        except (ValueError, TypeError):
                            pass
            
            # Dados de forma
            if "formRun_overall" in stats:
                form = stats["formRun_overall"]
                if isinstance(form, str):
                    target_dict["form"] = form[:5]
            
            # Extrair dados adicionais
            if "additional_info" in stats and isinstance(stats["additional_info"], dict):
                add_info = stats["additional_info"]
                
                if "xg_for_overall" in add_info:
                    target_dict["xg"] = float(add_info["xg_for_overall"])
                if "xg_against_overall" in add_info:
                    target_dict["xga"] = float(add_info["xg_against_overall"])
                
                # Extrair outras estatísticas de additional_info
                if "over35CardsPercentage_overall" in add_info:
                    target_dict["over_3_5_cards_pct"] = float(add_info["over35CardsPercentage_overall"])
                if "over95CornersPercentage_overall" in add_info:
                    target_dict["over_9_5_corners_pct"] = float(add_info["over95CornersPercentage_overall"])
                
                logger.info(f"Extraídos dados adicionais para {team_name}: xG={target_dict.get('xg', 'N/A')}, xGA={target_dict.get('xga', 'N/A')}")

def extract_from_league_matches(api_data, result, home_team_name, away_team_name):
    """
    Extrai dados do endpoint League Matches
    
    Args:
        api_data (dict): Dados da API
        result (dict): Estrutura para armazenar resultados
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
    """
    import logging
    logger = logging.getLogger("valueHunter.api_adapter")
    
    if "data" not in api_data or not isinstance(api_data["data"], list):
        logger.warning("Estrutura de League Matches inválida")
        return
    
    # Inicializar estatísticas dos times
    home_stats = {}
    away_stats = {}
    
    # Processar cada partida para extrair tendências
    for match in api_data["data"]:
        if not isinstance(match, dict):
            continue
        
        # Verificar se temos os IDs dos times
        if "homeID" not in match or "awayID" not in match:
            continue
        
        # Aqui precisamos de uma forma de mapear IDs para nomes
        # Como não temos isso, vamos tentar usar outras informações
        # Esta parte precisaria ser adaptada para seu sistema específico
        
        # Extrair estatísticas do jogo
        if "team_a_shots" in match:
            # Estatísticas do time da casa
            shots_home = match.get("team_a_shots", 0)
            shots_on_target_home = match.get("team_a_shotsOnTarget", 0)
            possession_home = match.get("team_a_possession", 0)
            corners_home = match.get("team_a_corners", 0)
            cards_home = match.get("team_a_cards_num", 0)
            
            # Estatísticas do time visitante
            shots_away = match.get("team_b_shots", 0)
            shots_on_target_away = match.get("team_b_shotsOnTarget", 0)
            possession_away = match.get("team_b_possession", 0)
            corners_away = match.get("team_b_corners", 0)
            cards_away = match.get("team_b_cards_num", 0)
            
            # Armazenar estatísticas
            # Como não sabemos qual time é qual, não podemos atribuir corretamente
            # Esta é uma limitação da API
    
    # Se não conseguimos extrair estatísticas significativas, log de aviso
    logger.warning("League Matches: Não foi possível mapear times por ID. Dados limitados.")
    
    # Armazenar o que conseguimos extrair
    if home_stats:
        result["home_team"] = home_stats
    if away_stats:
        result["away_team"] = away_stats

def extract_from_league_teams(api_data, result, home_team_name, away_team_name):
    """
    Extrai dados do endpoint League Teams
    
    Args:
        api_data (dict): Dados da API
        result (dict): Estrutura para armazenar resultados
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
    """
    import logging
    logger = logging.getLogger("valueHunter.api_adapter")
    
    if "data" not in api_data or not isinstance(api_data["data"], list):
        logger.warning("Estrutura de League Teams inválida")
        return
    
    # Procurar os times por nome
    home_team_data = None
    away_team_data = None
    
    for team in api_data["data"]:
        if not isinstance(team, dict) or "name" not in team:
            continue
        
        team_name = team["name"]
        
        if team_name == home_team_name:
            home_team_data = team
            logger.info(f"Time da casa encontrado: {home_team_name}")
        elif team_name == away_team_name:
            away_team_data = team
            logger.info(f"Time visitante encontrado: {away_team_name}")
        
        # Se encontramos ambos os times, podemos parar
        if home_team_data and away_team_data:
            break
    
    # Extrair estatísticas do time da casa
    if home_team_data:
        home_stats = extract_team_stats_from_league_teams(home_team_data)
        result["home_team"] = home_stats
    
    # Extrair estatísticas do time visitante
    if away_team_data:
        away_stats = extract_team_stats_from_league_teams(away_team_data)
        result["away_team"] = away_stats
    
    # Verificar se conseguimos extrair dados
    if not home_team_data:
        logger.warning(f"Time da casa não encontrado: {home_team_name}")
    if not away_team_data:
        logger.warning(f"Time visitante não encontrado: {away_team_name}")

def extract_team_stats_from_league_teams(team_data):
    """
    Extrai estatísticas de um time do endpoint League Teams
    
    Args:
        team_data (dict): Dados do time
        
    Returns:
        dict: Estatísticas extraídas
    """
    import logging
    logger = logging.getLogger("valueHunter.api_adapter")
    
    stats = {}
    
    if "stats" not in team_data or not isinstance(team_data["stats"], dict):
        return stats
    
    team_stats = team_data["stats"]
    
    # Mapeamento de campos
    field_mappings = {
        "played": ["seasonMatchesPlayed_overall"],
        "wins": ["seasonWinsNum_overall"],
        "draws": ["seasonDrawsNum_overall"],
        "losses": ["seasonLossesNum_overall"],
        "goals_scored": ["seasonScoredNum_overall", "seasonGoals_overall"],
        "goals_conceded": ["seasonConcededNum_overall"],
        "clean_sheets_pct": ["seasonCSPercentage_overall"],
        "btts_pct": ["seasonBTTSPercentage_overall"],
        "over_2_5_pct": ["seasonOver25Percentage_overall"],
        "possession": ["possessionAVG_overall"],
        "cards_total": ["cardsTotal_overall"],
        "cards_per_game": ["cardsAVG_overall"],
        "corners_per_game": ["cornersAVG_overall", "cornersTotalAVG_overall"],
        "corners_for": ["cornersTotal_overall"],
        "yellow_cards": ["yellow_cards", "team_a_yellow_cards"],
        "red_cards": ["red_cards", "team_a_red_cards"],
        "home_played": ["seasonMatchesPlayed_home"],
        "home_wins": ["seasonWinsNum_home"],
        "home_draws": ["seasonDrawsNum_home"],
        "home_losses": ["seasonLossesNum_home"],
        "home_goals_scored": ["seasonScoredNum_home", "seasonGoals_home"],
        "home_goals_conceded": ["seasonConcededNum_home"],
        "away_played": ["seasonMatchesPlayed_away"],
        "away_wins": ["seasonWinsNum_away"],
        "away_draws": ["seasonDrawsNum_away"],
        "away_losses": ["seasonLossesNum_away"],
        "away_goals_scored": ["seasonScoredNum_away", "seasonGoals_away"],
        "away_goals_conceded": ["seasonConcededNum_away"]
    }
    
    # Extrair cada campo
    for target_field, source_fields in field_mappings.items():
        for field in source_fields:
            if field in team_stats:
                value = team_stats[field]
                try:
                    if value is not None and value != 'N/A':
                        stats[target_field] = float(value)
                        break
                except (ValueError, TypeError):
                    pass
    
    # Dados de forma
    if "formRun_overall" in team_stats:
        form = team_stats["formRun_overall"]
        if isinstance(form, str):
            stats["form"] = form[:5]
    
    # Dados adicionais se disponíveis
    if "additional_info" in team_stats and isinstance(team_stats["additional_info"], dict):
        add_info = team_stats["additional_info"]
        
        # xG data
        if "xg_for_overall" in add_info:
            stats["xg"] = float(add_info["xg_for_overall"])
        if "xg_against_overall" in add_info:
            stats["xga"] = float(add_info["xg_against_overall"])
        
        # Outras estatísticas
        if "over35CardsPercentage_overall" in add_info:
            stats["over_3_5_cards_pct"] = float(add_info["over35CardsPercentage_overall"])
        if "over95CornersPercentage_overall" in add_info:
            stats["over_9_5_corners_pct"] = float(add_info["over95CornersPercentage_overall"])
    
    # Log de estatísticas extraídas
    non_zero_fields = count_non_zero_fields(stats)
    logger.info(f"Extraídos {non_zero_fields} campos não-zero para o time")
    
    return stats

def extract_generic(api_data, result, home_team_name, away_team_name):
    """
    Extrator genérico que tenta buscar dados em vários lugares possíveis
    
    Args:
        api_data (dict): Dados da API
        result (dict): Estrutura para armazenar resultados
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
    """
    import logging
    logger = logging.getLogger("valueHunter.api_adapter")
    
    # Tentar extrair de toda a estrutura - abordagem mais agressiva
    logger.info("Usando extrator genérico - buscando em todas as estruturas possíveis")
    
    # Procurar equipes em qualquer lugar da estrutura
    if "basic_stats" in api_data:
        if "home_team" in api_data["basic_stats"]:
            home_data = api_data["basic_stats"]["home_team"]
            extract_from_any_team_object(home_data, result["home_team"])
        
        if "away_team" in api_data["basic_stats"]:
            away_data = api_data["basic_stats"]["away_team"]
            extract_from_any_team_object(away_data, result["away_team"])
    
    # Se temos "data" como um array, tentar encontrar times por nome
    if "data" in api_data and isinstance(api_data["data"], list):
        for item in api_data["data"]:
            if isinstance(item, dict) and "name" in item:
                team_name = item["name"]
                
                if team_name == home_team_name:
                    extract_from_any_team_object(item, result["home_team"])
                elif team_name == away_team_name:
                    extract_from_any_team_object(item, result["away_team"])
    
    # Procurar dados de h2h em qualquer lugar
    if "head_to_head" in api_data:
        extract_from_any_h2h_object(api_data["head_to_head"], result["h2h"])
    elif "h2h" in api_data:
        extract_from_any_h2h_object(api_data["h2h"], result["h2h"])
    
    # Se temos data como um objeto contendo h2h
    if "data" in api_data and isinstance(api_data["data"], dict):
        if "h2h" in api_data["data"]:
            extract_from_any_h2h_object(api_data["data"]["h2h"], result["h2h"])

def extract_from_any_team_object(team_obj, target_dict):
    """
    Extrai estatísticas de qualquer objeto que represente um time
    
    Args:
        team_obj (dict): Objeto do time (pode ter qualquer estrutura)
        target_dict (dict): Dicionário para armazenar resultados
    """
    if not isinstance(team_obj, dict):
        return
    
    # Se temos stats diretamente
    if "stats" in team_obj and isinstance(team_obj["stats"], dict):
        stats_obj = team_obj["stats"]
        
        # Procurar em stats
        extract_stats_from_dict(stats_obj, target_dict)
        
        # Procurar em additional_info
        if "additional_info" in stats_obj and isinstance(stats_obj["additional_info"], dict):
            extract_stats_from_dict(stats_obj["additional_info"], target_dict)
    
    # Procurar estatísticas diretamente no objeto
    keys_to_check = [
        "seasonMatchesPlayed_overall", "seasonWinsNum_overall", "seasonDrawsNum_overall",
        "seasonLossesNum_overall", "seasonScoredNum_overall", "seasonConcededNum_overall"
    ]
    
    for key in keys_to_check:
        if key in team_obj:
            # Estamos procurando estatísticas diretas - mapear para nossos campos
            target_key = None
            if key == "seasonMatchesPlayed_overall":
                target_key = "played"
            elif key == "seasonWinsNum_overall":
                target_key = "wins"
            elif key == "seasonDrawsNum_overall":
                target_key = "draws"
            elif key == "seasonLossesNum_overall":
                target_key = "losses"
            elif key == "seasonScoredNum_overall":
                target_key = "goals_scored"
            elif key == "seasonConcededNum_overall":
                target_key = "goals_conceded"
            
            if target_key:
                value = team_obj[key]
                try:
                    if value is not None and value != 'N/A':
                        target_dict[target_key] = float(value)
                except (ValueError, TypeError):
                    pass

def extract_stats_from_dict(source_dict, target_dict):
    """
    Extrai estatísticas de um dicionário para outro usando mapeamento de campos
    
    Args:
        source_dict (dict): Dicionário fonte
        target_dict (dict): Dicionário alvo
    """
    if not isinstance(source_dict, dict):
        return
    
    # Mapeamento de campos
    field_mappings = {
        "played": ["matches_played", "seasonMatchesPlayed_overall", "MP", "matches_completed_minimum"],
        "wins": ["wins", "seasonWinsNum_overall", "W"],
        "draws": ["draws", "seasonDrawsNum_overall", "D"],
        "losses": ["losses", "seasonLossesNum_overall", "L"],
        "goals_scored": ["goals_scored", "seasonScoredNum_overall", "seasonGoals_overall", "Gls"],
        "goals_conceded": ["goals_conceded", "seasonConcededNum_overall", "seasonConceded_overall", "GA"],
        "clean_sheets_pct": ["clean_sheet_percentage", "seasonCSPercentage_overall"],
        "btts_pct": ["btts_percentage", "seasonBTTSPercentage_overall"],
        "over_2_5_pct": ["over_2_5_percentage", "seasonOver25Percentage_overall"],
        "xg": ["xg_for_overall", "xg_for_home", "xg_for_away", "xG", "expected_goals"],
        "xga": ["xg_against_overall", "xg_against_home", "xg_against_away", "xGA"],
        "possession": ["possession", "possessionAVG_overall", "Poss"],
        "cards_total": ["cards_total", "cardsTotal_overall"],
        "cards_per_game": ["cards_per_game", "cardsAVG_overall"],
        "yellow_cards": ["yellow_cards", "team_a_yellow_cards", "team_b_yellow_cards"],
        "red_cards": ["red_cards", "team_a_red_cards", "team_b_red_cards"],
        "over_3_5_cards_pct": ["over_3_5_cards_percentage", "over35CardsPercentage_overall"],
        "corners_per_game": ["corners_per_game", "cornersAVG_overall", "cornersTotalAVG_overall"],
        "corners_for": ["corners_for", "cornersTotal_overall"],
        "corners_against": ["corners_against"],
        "over_9_5_corners_pct": ["over_9_5_corners_percentage", "over95CornersPercentage_overall"],
        "home_played": ["home_matches", "matches_played_home", "seasonMatchesPlayed_home"],
        "home_wins": ["home_wins", "seasonWinsNum_home"],
        "home_draws": ["home_draws", "seasonDrawsNum_home"],
        "home_losses": ["home_losses", "seasonLossesNum_home"],
        "home_goals_scored": ["home_goals_scored", "seasonScoredNum_home", "seasonGoals_home"],
        "home_goals_conceded": ["home_goals_conceded", "seasonConcededNum_home", "seasonConceded_home"],
        "away_played": ["away_matches", "matches_played_away", "seasonMatchesPlayed_away"],
        "away_wins": ["away_wins", "seasonWinsNum_away"],
        "away_draws": ["away_draws", "seasonDrawsNum_away"],
        "away_losses": ["away_losses", "seasonLossesNum_away"],
        "away_goals_scored": ["away_goals_scored", "seasonScoredNum_away", "seasonGoals_away"],
        "away_goals_conceded": ["away_goals_conceded", "seasonConcededNum_away", "seasonConceded_away"]
    }
    
    # Extrair cada campo
    for target_field, source_fields in field_mappings.items():
        if target_field in target_dict and target_dict[target_field] != 0:
            continue  # Já temos este campo
            
        for field in source_fields:
            if field in source_dict:
                value = source_dict[field]
                try:
                    if value is not None and value != 'N/A':
                        target_dict[target_field] = float(value)
                        break
                except (ValueError, TypeError):
                    pass

def extract_from_any_h2h_object(h2h_obj, target_dict):
    """
    Extrai dados de qualquer objeto que represente confrontos diretos (H2H)
    
    Args:
        h2h_obj (dict): Objeto H2H (pode ter qualquer estrutura)
        target_dict (dict): Dicionário para armazenar resultados
    """
    if not isinstance(h2h_obj, dict):
        return
    
    # Mapeamento de campos H2H
    h2h_mappings = {
        "total_matches": ["total_matches", "totalMatches", "matches"],
        "home_wins": ["home_wins", "team_a_wins", "team_a_win_percentage"],
        "away_wins": ["away_wins", "team_b_wins", "team_b_win_percentage"],
        "draws": ["draws", "draw", "draw_percentage"],
        "over_2_5_pct": ["over_2_5_percentage", "over25Percentage", "over_2_5_pct"],
        "btts_pct": ["btts_percentage", "bttsPercentage", "btts_pct"],
        "avg_cards": ["avg_cards", "average_cards", "cards_avg"],
        "avg_corners": ["avg_corners", "average_corners", "corners_avg"]
    }
    
    # Extrair campos diretos
    for target_field, source_fields in h2h_mappings.items():
        for field in source_fields:
            if field in h2h_obj:
                value = h2h_obj[field]
                try:
                    if value is not None and value != 'N/A':
                        target_dict[target_field] = float(value)
                        break
                except (ValueError, TypeError):
                    pass
    
    # Procurar campos aninhados
    if "previous_matches_results" in h2h_obj and isinstance(h2h_obj["previous_matches_results"], dict):
        results = h2h_obj["previous_matches_results"]
        
        if "totalMatches" in results:
            target_dict["total_matches"] = float(results["totalMatches"])
        if "team_a_win_percentage" in results:
            target_dict["home_wins_pct"] = float(results["team_a_win_percentage"])
        if "team_b_win_percentage" in results:
            target_dict["away_wins_pct"] = float(results["team_b_win_percentage"])
    
    # Procurar em betting_stats
    if "betting_stats" in h2h_obj and isinstance(h2h_obj["betting_stats"], dict):
        betting = h2h_obj["betting_stats"]
        
        if "over25Percentage" in betting:
            target_dict["over_2_5_pct"] = float(betting["over25Percentage"])
        if "bttsPercentage" in betting:
            target_dict["btts_pct"] = float(betting["bttsPercentage"])
        if "avg_goals" in betting:
            target_dict["avg_goals"] = float(betting["avg_goals"])

def calculate_derived_stats(team_dict):
    """
    Calcula estatísticas derivadas quando possível
    
    Args:
        team_dict (dict): Dicionário de estatísticas do time
    """
    # Verificar se temos jogos disputados
    if "played" in team_dict and team_dict["played"] > 0:
        # Calcular cards_per_game se temos cards_total
        if "cards_total" in team_dict and team_dict["cards_total"] > 0 and "cards_per_game" not in team_dict:
            team_dict["cards_per_game"] = round(team_dict["cards_total"] / team_dict["played"], 2)
        
        # Calcular cards_total se temos yellow_cards e red_cards
        if "cards_total" not in team_dict and "yellow_cards" in team_dict and "red_cards" in team_dict:
            team_dict["cards_total"] = team_dict["yellow_cards"] + team_dict["red_cards"]
            
            if "cards_per_game" not in team_dict:
                team_dict["cards_per_game"] = round(team_dict["cards_total"] / team_dict["played"], 2)
        
        # Calcular corners_per_game se temos corners_for e corners_against
        if "corners_for" in team_dict and "corners_against" in team_dict:
            total_corners = team_dict["corners_for"] + team_dict["corners_against"]
            
            if "corners_total" not in team_dict:
                team_dict["corners_total"] = total_corners
                
            if "corners_per_game" not in team_dict:
                team_dict["corners_per_game"] = round(total_corners / team_dict["played"], 2)

def count_non_zero_fields(data_dict):
    """
    Conta campos com valores não-zero em um dicionário
    
    Args:
        data_dict (dict): Dicionário para analisar
        
    Returns:
        int: Número de campos com valores não-zero
    """
    if not isinstance(data_dict, dict):
        return 0
        
    count = 0
    for key, value in data_dict.items():
        if isinstance(value, (int, float)) and value != 0:
            count += 1
    
    return count

def extract_team_data_from_urls(match_data):
    """
    Extrai dados adicionais de times a partir das URLs na partida
    
    Args:
        match_data (dict): Dados da partida
        
    Returns:
        dict: Dicionário com dados extraídos {'home': {...}, 'away': {...}}
    """
    
    return {'home': {}, 'away': {}}
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
    import logging
    import json
    
    logger = logging.getLogger("valueHunter.data_extractor")
    
    # Inicializa a estrutura de resultado
    result = {
        "match_info": {
            "home_team": home_team_name,
            "away_team": away_team_name,
            "league": "",
            "league_id": None
        },
        "home_team": {},
        "away_team": {},
        "h2h": {}
    }
    
    # Função para logar estrutura de forma mais clara
    def log_structure(data, prefix=""):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    logger.info(f"{prefix}{key}: {type(value).__name__} com {len(value)} itens")
                else:
                    logger.info(f"{prefix}{key}: {type(value).__name__}")
        elif isinstance(data, list) and len(data) > 0:
            logger.info(f"{prefix}Lista com {len(data)} itens, primeiro é {type(data[0]).__name__}")
    
    # Registrar estrutura para depuração
    if log_details:
        logger.info(f"Estrutura de alto nível dos dados da API:")
        log_structure(api_data)
        
        # Regitrar o tamanho dos dados para referência
        try:
            data_size = len(json.dumps(api_data))
            logger.info(f"Tamanho total dos dados: {data_size} caracteres")
        except:
            pass
    
    # FASE 1: Procura por dados básicos/meta
    if isinstance(api_data, dict):
        # Procurar league_id em vários lugares possíveis
        if "basic_stats" in api_data and isinstance(api_data["basic_stats"], dict):
            if "league_id" in api_data["basic_stats"]:
                result["match_info"]["league_id"] = api_data["basic_stats"]["league_id"]
            
            # Tentar extrair nome da liga
            if "league_name" in api_data["basic_stats"]:
                result["match_info"]["league"] = api_data["basic_stats"]["league_name"]
        
        # Procurar em data diretamente
        if "data" in api_data:
            data_obj = api_data["data"]
            if isinstance(data_obj, dict):
                # Pode ser match details
                if "league" in data_obj:
                    result["match_info"]["league"] = data_obj["league"]
                if "competition_id" in data_obj:
                    result["match_info"]["league_id"] = data_obj["competition_id"]
    
    # FASE 2: Busca profunda por times
    
    # Dicionário para armazenar dados encontrados para cada time
    home_found = {}
    away_found = {}
    
    # Função para buscar recursivamente em toda a estrutura
    def deep_search(obj, path=""):
        if isinstance(obj, dict):
            # Verificar se este objeto pode ser o time da casa ou visitante
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
                    if home_team_name in team_name or team_name in home_team_name:
                        is_home = True
                    elif away_team_name in team_name or team_name in away_team_name:
                        is_away = True
                
                # Se encontramos um time, extrair suas estatísticas
                if is_home or is_away:
                    target_dict = home_found if is_home else away_found
                    current_path = f"{path}.{team_name}"
                    
                    logger.info(f"Encontrado {'time da casa' if is_home else 'time visitante'} em {current_path}")
                    
                    # Verificar se tem stats diretamente
                    if "stats" in obj and isinstance(obj["stats"], dict):
                        stats_obj = obj["stats"]
                        extract_stats_recursive(stats_obj, target_dict, current_path + ".stats")
                        
                        # Verificar se tem additional_info
                        if "additional_info" in stats_obj and isinstance(stats_obj["additional_info"], dict):
                            extract_stats_recursive(stats_obj["additional_info"], target_dict, current_path + ".stats.additional_info")
                    
                    # Verificar se stats estão diretamente no objeto do time
                    for stat_key in ["seasonMatchesPlayed_overall", "wins", "seasonWinsNum_overall", 
                                    "seasonGoals_overall", "seasonConceded_overall"]:
                        if stat_key in obj:
                            # Encontramos estatísticas diretas
                            extract_stats_recursive(obj, target_dict, current_path)
                            break
            
            # Continuar a busca em todos os campos
            for key, value in obj.items():
                deep_search(value, f"{path}.{key}" if path else key)
        
        elif isinstance(obj, list):
            # Buscar em cada item da lista
            for i, item in enumerate(obj):
                deep_search(item, f"{path}[{i}]")
    
    # Função para extrair estatísticas específicas dos dicionários que encontramos
    def extract_stats_recursive(source, target, path=""):
        if not isinstance(source, dict):
            return
        
        # Mapeamento de campos estatísticos comuns que procuramos
        field_mappings = {
            "played": ["matches_played", "seasonMatchesPlayed_overall", "MP", "PJ", "Games"],
            "wins": ["wins", "seasonWinsNum_overall", "W", "Wins"],
            "draws": ["draws", "seasonDrawsNum_overall", "D", "Draws"],
            "losses": ["losses", "seasonLossesNum_overall", "L", "Losses"],
            "goals_scored": ["goals_scored", "seasonScoredNum_overall", "seasonGoals_overall", "Gls", "goals", "GF"],
            "goals_conceded": ["goals_conceded", "seasonConcededNum_overall", "seasonConceded_overall", "GA"],
            "clean_sheets_pct": ["clean_sheet_percentage", "seasonCSPercentage_overall"],
            "btts_pct": ["btts_percentage", "seasonBTTSPercentage_overall"],
            "over_2_5_pct": ["over_2_5_percentage", "seasonOver25Percentage_overall"],
            "xg": ["xG", "xg", "xg_for_overall", "expected_goals", "ExpG"],
            "xga": ["xGA", "xga", "xg_against_overall", "xg_against_avg_overall"],
            "possession": ["possession", "possessionAVG_overall", "Poss", "possession_avg"],
            "home_played": ["home_matches", "matches_played_home", "seasonMatchesPlayed_home"],
            "home_wins": ["home_wins", "seasonWinsNum_home"],
            "home_draws": ["home_draws", "seasonDrawsNum_home"],
            "home_losses": ["home_losses", "seasonLossesNum_home"],
            "home_goals_scored": ["home_goals_scored", "seasonScoredNum_home", "seasonGoals_home"],
            "home_goals_conceded": ["home_goals_conceded", "seasonConcededNum_home", "seasonConceded_home"],
            "away_played": ["away_matches", "matches_played_away", "seasonMatchesPlayed_away"],
            "away_wins": ["away_wins", "seasonWinsNum_away"],
            "away_draws": ["away_draws", "seasonDrawsNum_away"],
            "away_losses": ["away_losses", "seasonLossesNum_away"],
            "away_goals_scored": ["away_goals_scored", "seasonScoredNum_away", "seasonGoals_away"],
            "away_goals_conceded": ["away_goals_conceded", "seasonConcededNum_away", "seasonConceded_away"]
        }
            
        # Processar cada campo que estamos procurando
        for target_field, source_fields in field_mappings.items():
            if target_field in target and target[target_field] != 0:
                continue  # Já temos este campo, pular
                
            for field in source_fields:
                if field in source:
                    value = source[field]
                    if value is not None and value != 'N/A':
                        try:
                            # Converter para float/int
                            float_value = float(value)
                            target[target_field] = float_value
                            if log_details:
                                logger.info(f"Encontrado {target_field}={float_value} em {path}.{field}")
                            break  # Encontrou este campo, continuar para o próximo
                        except (ValueError, TypeError):
                            pass  # Ignorar valores que não podem ser convertidos
        
        # Buscar em todos os objetos aninhados também
        for key, value in source.items():
            if isinstance(value, dict):
                # Também procurar em objetos aninhados
                extract_stats_recursive(value, target, f"{path}.{key}")
    
    # FASE 3: Busca específica para H2H
    h2h_data = None
    
    # Procurar dados H2H em vários lugares possíveis
    if isinstance(api_data, dict):
        # Caminho direto
        if "head_to_head" in api_data:
            h2h_data = api_data["head_to_head"]
            if log_details:
                logger.info("Dados H2H encontrados em api_data.head_to_head")
        
        # Caminho na estrutura match_details
        elif "data" in api_data and isinstance(api_data["data"], dict):
            data_obj = api_data["data"]
            if "h2h" in data_obj:
                h2h_data = data_obj["h2h"]
                if log_details:
                    logger.info("Dados H2H encontrados em api_data.data.h2h")
        
        # Procurar h2h diretamente
        elif "h2h" in api_data:
            h2h_data = api_data["h2h"]
            if log_details:
                logger.info("Dados H2H encontrados em api_data.h2h")
    
    # Extrair dados H2H se encontrados
    if h2h_data and isinstance(h2h_data, dict):
        # Procurar campos diretamente
        h2h_fields = {
            "total_matches": ["total_matches", "totalMatches", "matches"],
            "home_wins": ["home_wins", "team_a_wins"],
            "away_wins": ["away_wins", "team_b_wins"],
            "draws": ["draws", "draw"],
            "over_2_5_pct": ["over_2_5_percentage", "over25Percentage", "over_2_5_pct"],
            "btts_pct": ["btts_percentage", "bttsPercentage", "btts_pct"],
            "avg_cards": ["avg_cards", "average_cards"],
            "avg_corners": ["avg_corners", "average_corners"],
            "avg_goals": ["avg_goals", "average_goals"]
        }
        
        for target_field, source_fields in h2h_fields.items():
            for field in source_fields:
                if field in h2h_data:
                    value = h2h_data[field]
                    if value is not None and value != 'N/A':
                        try:
                            result["h2h"][target_field] = float(value)
                            break
                        except (ValueError, TypeError):
                            pass
        
        # Procurar em estruturas aninhadas
        if "previous_matches_results" in h2h_data and isinstance(h2h_data["previous_matches_results"], dict):
            prev_results = h2h_data["previous_matches_results"]
            
            if "totalMatches" in prev_results and result["h2h"].get("total_matches", 0) == 0:
                result["h2h"]["total_matches"] = float(prev_results["totalMatches"])
                
            if "team_a_wins" in prev_results and result["h2h"].get("home_wins", 0) == 0:
                result["h2h"]["home_wins"] = float(prev_results["team_a_wins"])
                
            if "team_b_wins" in prev_results and result["h2h"].get("away_wins", 0) == 0:
                result["h2h"]["away_wins"] = float(prev_results["team_b_wins"])
                
            if "draw" in prev_results and result["h2h"].get("draws", 0) == 0:
                result["h2h"]["draws"] = float(prev_results["draw"])
        
        # Procurar em betting_stats
        if "betting_stats" in h2h_data and isinstance(h2h_data["betting_stats"], dict):
            betting = h2h_data["betting_stats"]
            
            if "over25Percentage" in betting and result["h2h"].get("over_2_5_pct", 0) == 0:
                result["h2h"]["over_2_5_pct"] = float(betting["over25Percentage"])
                
            if "bttsPercentage" in betting and result["h2h"].get("btts_pct", 0) == 0:
                result["h2h"]["btts_pct"] = float(betting["bttsPercentage"])
                
            if "avg_goals" in betting and result["h2h"].get("avg_goals", 0) == 0:
                result["h2h"]["avg_goals"] = float(betting["avg_goals"])
    
    # FASE 4: Busca recursiva em todos os dados
    deep_search(api_data)
    
    # FASE 5: Verificar quantidade de dados encontrados
    if log_details:
        logger.info(f"Dados encontrados para time da casa: {len(home_found)} campos")
        if home_found:
            logger.info(f"Campos da casa: {', '.join(home_found.keys())}")
            
        logger.info(f"Dados encontrados para time visitante: {len(away_found)} campos")
        if away_found:
            logger.info(f"Campos do visitante: {', '.join(away_found.keys())}")
            
        logger.info(f"Dados H2H encontrados: {len(result['h2h'])} campos")
        if result["h2h"]:
            logger.info(f"Campos H2H: {', '.join(result['h2h'].keys())}")
    
    # Copiar dados encontrados para o resultado
    if home_found:
        result["home_team"] = home_found
        
    if away_found:
        result["away_team"] = away_found
    
    # FASE 6: Se ainda não temos dados suficientes, procurar por campos genéricos em qualquer lugar
    if len(home_found) < 3 or len(away_found) < 3:
        # Último recurso: procurar qualquer campo que pareça ser estatística em qualquer lugar
        if log_details:
            logger.warning("Poucos dados encontrados, tentando busca profunda por campos estatísticos")
            
        def find_all_stats_fields(obj, prefix="", paths=None):
            if paths is None:
                paths = []
                
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{prefix}.{key}" if prefix else key
                    
                    # Identificar campos que parecem ser estatísticos
                    is_stat_field = False
                    if key.lower().find("season") >= 0 or key.lower().find("match") >= 0:
                        is_stat_field = True
                    elif key.lower() in ["wins", "losses", "draws", "goals", "points", "xg", "xga"]:
                        is_stat_field = True
                        
                    if is_stat_field and isinstance(value, (int, float, str)):
                        try:
                            numeric_value = float(value)
                            paths.append((current_path, key, numeric_value))
                        except (ValueError, TypeError):
                            pass
                    
                    # Recursão em objetos aninhados
                    if isinstance(value, (dict, list)):
                        find_all_stats_fields(value, current_path, paths)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{prefix}[{i}]"
                    if isinstance(item, (dict, list)):
                        find_all_stats_fields(item, current_path, paths)
            
            return paths
        
        # Procurar campos estatísticos em qualquer lugar
        all_stats_fields = find_all_stats_fields(api_data)
        
        if log_details and all_stats_fields:
            logger.info(f"Encontrados {len(all_stats_fields)} campos estatísticos em toda a estrutura")
            
        # Tentar atribuir campos encontrados a home/away based on some heuristics
        home_indicators = ["home", "team_a", "club_a"]
        away_indicators = ["away", "team_b", "club_b"]
        
        for path, key, value in all_stats_fields:
            # Verificar se o caminho indica a qual time pertence
            is_home = any(indicator in path.lower() for indicator in home_indicators)
            is_away = any(indicator in path.lower() for indicator in away_indicators)
            
            # Tentar mapear o campo para nossas estatísticas conhecidas
            target_field = None
            
            if "match" in key.lower() or "played" in key.lower():
                target_field = "played"
            elif "win" in key.lower():
                target_field = "wins"
            elif "draw" in key.lower():
                target_field = "draws"
            elif "loss" in key.lower() or "defeat" in key.lower():
                target_field = "losses"
            elif "goal" in key.lower() and "score" in key.lower():
                target_field = "goals_scored"
            elif "goal" in key.lower() and "concede" in key.lower():
                target_field = "goals_conceded"
            elif "xg" == key.lower() or "expected_goal" in key.lower():
                target_field = "xg"
            elif "xga" == key.lower() or "expected_goal_against" in key.lower():
                target_field = "xga"
            elif "posse" in key.lower():
                target_field = "possession"
            elif "btts" in key.lower() or "both_team" in key.lower():
                target_field = "btts_pct"
            elif "over25" in key.lower() or "over_2_5" in key.lower():
                target_field = "over_2_5_pct"
            
            # Se conseguimos mapear o campo e determinar o time
            if target_field:
                if is_home and target_field not in result["home_team"]:
                    result["home_team"][target_field] = value
                    if log_details:
                        logger.info(f"Atribuído {path} ({value}) como {target_field} para time da casa")
                        
                elif is_away and target_field not in result["away_team"]:
                    result["away_team"][target_field] = value
                    if log_details:
                        logger.info(f"Atribuído {path} ({value}) como {target_field} para time visitante")
    
    # FASE 7: Se ainda não temos forma (form), tentar extrair
    if "form" not in result["home_team"] or "form" not in result["away_team"]:
        if "team_form" in api_data:
            # Extração de forma padrão
            if "home" in api_data["team_form"] and isinstance(api_data["team_form"]["home"], list):
                form_list = api_data["team_form"]["home"]
                if form_list:
                    form_string = ""
                    for match in form_list[:5]:
                        if isinstance(match, dict) and "result" in match:
                            form_string += match["result"]
                        else:
                            form_string += "?"
                    
                    result["home_team"]["form"] = form_string
                    
            if "away" in api_data["team_form"] and isinstance(api_data["team_form"]["away"], list):
                form_list = api_data["team_form"]["away"]
                if form_list:
                    form_string = ""
                    for match in form_list[:5]:
                        if isinstance(match, dict) and "result" in match:
                            form_string += match["result"]
                        else:
                            form_string += "?"
                    
                    result["away_team"]["form"] = form_string
    
    return result
