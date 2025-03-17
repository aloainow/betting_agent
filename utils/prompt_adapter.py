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

# Adicione isso ao arquivo utils/prompt_adapter.py

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
    extract_h2h_data_improved(api_data, formatted_data)
    
    # NOVO: Extração melhorada de dados de forma
    extract_form_data_improved(api_data, formatted_data, home_team_name, away_team_name)
    
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
    """Extração melhorada de dados H2H"""
    # Buscar em múltiplos caminhos possíveis
    h2h_data = None
    
    # Caminho 1: Direto no objeto principal
    if "head_to_head" in api_data:
        h2h_data = api_data["head_to_head"]
    
    # Caminho 2: Nos detalhes da partida
    elif "match_details" in api_data and api_data["match_details"]:
        if "h2h" in api_data["match_details"]:
            h2h_data = api_data["match_details"]["h2h"]
    
    # Caminho 3: No objeto h2h
    elif "h2h" in api_data:
        h2h_data = api_data["h2h"]
        
    if not h2h_data:
        return
        
    # Mapeamento de campos H2H
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
    
    # Extrair usando mapeamentos
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
    
    # Extrair partidas recentes
    if "matches" in h2h_data and isinstance(h2h_data["matches"], list):
        formatted_data["h2h"]["recent_matches"] = h2h_data["matches"][:5]  # Apenas as 5 mais recentes
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
    
    if not h2h_data:
        return
        
    # Define mappings for H2H fields
    mappings = {
        "total_matches": ["total_matches", "matches"],
        "home_wins": ["home_wins"],
        "away_wins": ["away_wins"],
        "draws": ["draws"],
        "over_2_5_pct": ["over_2_5_percentage"],
        "btts_pct": ["btts_percentage"],
        "avg_cards": ["average_cards"],
        "avg_corners": ["average_corners"]
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


def calculate_derived_stats(team_stats):
    """
    Calculate derived statistics from basic statistics
    
    Args:
        team_stats (dict): Team statistics dictionary
    """
    # Calculate cards_total if not present
    if team_stats["cards_total"] == 0:
        team_stats["cards_total"] = team_stats["yellow_cards"] + team_stats["red_cards"]
    
    # Calculate cards_per_game if not present
    if team_stats["played"] > 0 and team_stats["cards_per_game"] == 0:
        team_stats["cards_per_game"] = round(team_stats["cards_total"] / team_stats["played"], 2)
    
    # Calculate corners_total if not present
    if team_stats["corners_total"] == 0:
        team_stats["corners_total"] = team_stats["corners_for"] + team_stats["corners_against"]
    
    # Calculate corners_per_game if not present
    if team_stats["played"] > 0 and team_stats["corners_per_game"] == 0:
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
def extract_form_data(api_data, formatted_data):
    """
    Extract form data for both teams
    
    Args:
        api_data (dict): Original API data
        formatted_data (dict): Target data structure
    """
    # Process home team form
    if "team_form" in api_data and "home" in api_data["team_form"]:
        form_data = api_data["team_form"]["home"]
        
        if isinstance(form_data, list) and form_data:
            # Extract form string (e.g., "WDLWW")
            form_string = ""
            for i in range(min(5, len(form_data))):
                if isinstance(form_data[i], dict) and "result" in form_data[i]:
                    form_string += form_data[i]["result"]
            
            if form_string:
                formatted_data["home_team"]["form"] = form_string
                formatted_data["home_team"]["recent_matches"] = form_data[:5]
    
    # Process away team form
    if "team_form" in api_data and "away" in api_data["team_form"]:
        form_data = api_data["team_form"]["away"]
        
        if isinstance(form_data, list) and form_data:
            # Extract form string (e.g., "WDLWW")
            form_string = ""
            for i in range(min(5, len(form_data))):
                if isinstance(form_data[i], dict) and "result" in form_data[i]:
                    form_string += form_data[i]["result"]
            
            if form_string:
                formatted_data["away_team"]["form"] = form_string
                formatted_data["away_team"]["recent_matches"] = form_data[:5]

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
