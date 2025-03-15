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
    Função robusta para extrair dados de times com suporte a múltiplos formatos da API FootyStats
    
    Args:
        api_data (dict): Dados originais da API
        home_team_name (str): Nome do time da casa
        away_team_name (str): Nome do time visitante
        
    Returns:
        dict: Dados formatados na estrutura exata requerida
    """
    import logging
    logger = logging.getLogger("valueHunter.prompt_adapter")
    
    # Estrutura vazia padronizada
    formatted_data = {
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
    
    # Inicializar estruturas vazias com zeros
    for team_key in ["home_team", "away_team"]:
        formatted_data[team_key] = {
            # Stats básicos
            "played": 0, "wins": 0, "draws": 0, "losses": 0,
            "goals_scored": 0, "goals_conceded": 0, "clean_sheets_pct": 0,
            "btts_pct": 0, "over_2_5_pct": 0,
            # Específicos casa/fora
            "home_played": 0, "home_wins": 0, "home_draws": 0, "home_losses": 0,
            "home_goals_scored": 0, "home_goals_conceded": 0,
            "away_played": 0, "away_wins": 0, "away_draws": 0, "away_losses": 0,
            "away_goals_scored": 0, "away_goals_conceded": 0,
            # Stats avançados
            "xg": 0, "xga": 0, "ppda": 0, "possession": 0,
            # Stats de cartões
            "cards_total": 0, "cards_per_game": 0, "yellow_cards": 0, "red_cards": 0,
            "over_3_5_cards_pct": 0, "home_cards_per_game": 0, "away_cards_per_game": 0,
            # Stats de escanteios
            "corners_total": 0, "corners_per_game": 0, "corners_for": 0, "corners_against": 0,
            "over_9_5_corners_pct": 0, "home_corners_per_game": 0, "away_corners_per_game": 0,
            # Forma simplificada
            "form": "", "recent_matches": []
        }
    
    formatted_data["h2h"] = {
        "total_matches": 0, "home_wins": 0, "away_wins": 0, "draws": 0,
        "over_2_5_pct": 0, "btts_pct": 0, "avg_cards": 0, "avg_corners": 0,
        "recent_matches": []
    }
    
    if not api_data or not isinstance(api_data, dict):
        logger.error("Dados da API vazios ou inválidos")
        return formatted_data
    
    # Log da estrutura da API para depuração
    logger.info(f"API data keys: {list(api_data.keys())}")
    
    # Explorar diferentes caminhos para encontrar os dados
    try:
        # 1. ID da Liga
        if "basic_stats" in api_data and "league_id" in api_data["basic_stats"]:
            formatted_data["match_info"]["league_id"] = api_data["basic_stats"]["league_id"]
            logger.info(f"League ID encontrado: {formatted_data['match_info']['league_id']}")
        
        # 2. Procurar dados diretos do time (PATH 1)
        for team_type, team_name in [("home", home_team_name), ("away", away_team_name)]:
            team_key = f"{team_type}_team"
            
            # Caminho 1: basic_stats -> team_key -> stats
            if "basic_stats" in api_data and team_key in api_data["basic_stats"]:
                team_data = api_data["basic_stats"][team_key]
                
                if isinstance(team_data, dict):
                    logger.info(f"Encontrados dados para {team_name} via basic_stats->team_key")
                    
                    # Extrair estatísticas aninhadas
                    if "stats" in team_data:
                        raw_stats = None
                        
                        if isinstance(team_data["stats"], dict):
                            if "stats" in team_data["stats"]:
                                raw_stats = team_data["stats"]["stats"]
                            else:
                                raw_stats = team_data["stats"]
                        
                        # Se encontramos estatísticas, extrair dados específicos
                        if raw_stats and isinstance(raw_stats, dict):
                            logger.info(f"Encontradas estatísticas aninhadas para {team_name}")
                            
                            # Mapeamentos de chaves (múltiplas possibilidades)
                            key_mappings = {
                                "played": ["matches_played", "seasonMatchesPlayed_overall", "MP"],
                                "wins": ["wins", "seasonWinsNum_overall", "W"],
                                "draws": ["draws", "seasonDrawsNum_overall", "D"],
                                "losses": ["losses", "seasonLossesNum_overall", "L"],
                                "goals_scored": ["goals_scored", "seasonGoals_overall", "Gls", "goals"],
                                "goals_conceded": ["goals_conceded", "seasonConceded_overall", "GA"],
                                "xg": ["xG", "xg", "xg_for_overall", "expected_goals"],
                                "xga": ["xGA", "xga", "xg_against_overall", "xg_against_avg_overall"],
                                "possession": ["possession", "possessionAVG_overall", "Poss"],
                                "clean_sheets_pct": ["clean_sheet_percentage", "seasonCSPercentage_overall"],
                                "btts_pct": ["btts_percentage", "seasonBTTSPercentage_overall", "seasonBTTS_overall"],
                                "over_2_5_pct": ["over_2_5_percentage", "seasonOver25Percentage_overall"],
                                "cards_total": ["cards_total", "seasonCrdYNum_overall", "CrdY"],
                                "yellow_cards": ["yellow_cards", "seasonCrdYNum_overall", "CrdY"],
                                "red_cards": ["red_cards", "seasonCrdRNum_overall", "CrdR"],
                                "corners_for": ["corners_for", "seasonCornersFor_overall", "CK"],
                                "corners_against": ["corners_against", "seasonCornersAgainst_overall"]
                            }
                            
                            # Adicionar chaves específicas para home/away
                            if team_type == "home":
                                home_keys = {
                                    "home_played": ["home_matches_played", "seasonMatchesPlayed_home"],
                                    "home_wins": ["home_wins", "seasonWinsNum_home"],
                                    "home_draws": ["home_draws", "seasonDrawsNum_home"],
                                    "home_losses": ["home_losses", "seasonLossesNum_home"],
                                    "home_goals_scored": ["home_goals_scored", "seasonGoals_home"],
                                    "home_goals_conceded": ["home_goals_conceded", "seasonConceded_home"]
                                }
                                key_mappings.update(home_keys)
                            else:
                                away_keys = {
                                    "away_played": ["away_matches_played", "seasonMatchesPlayed_away"],
                                    "away_wins": ["away_wins", "seasonWinsNum_away"],
                                    "away_draws": ["away_draws", "seasonDrawsNum_away"],
                                    "away_losses": ["away_losses", "seasonLossesNum_away"],
                                    "away_goals_scored": ["away_goals_scored", "seasonGoals_away"],
                                    "away_goals_conceded": ["away_goals_conceded", "seasonConceded_away"]
                                }
                                key_mappings.update(away_keys)
                            
                            # Extrair cada campo
                            for target_field, source_fields in key_mappings.items():
                                for field in source_fields:
                                    if field in raw_stats:
                                        value = raw_stats[field]
                                        if value is not None and value != 'N/A':
                                            try:
                                                # Converter para número e armazenar
                                                formatted_data[team_key][target_field] = float(value)
                                                break  # Encontrou um valor, passar para o próximo campo
                                            except (ValueError, TypeError):
                                                pass
                    else:
                        logger.warning(f"Não encontrou stats aninhadas para {team_name}")
            
            # 3. Tentar extrair dados avançados
            if "advanced_stats" in api_data and team_type in api_data["advanced_stats"]:
                adv_stats = api_data["advanced_stats"][team_type]
                if "ppda" in adv_stats:
                    try:
                        formatted_data[team_key]["ppda"] = float(adv_stats["ppda"])
                        logger.info(f"PPDA encontrado para {team_name}: {adv_stats['ppda']}")
                    except (ValueError, TypeError):
                        pass
            
            # 4. Extrair dados de forma recente
            if "team_form" in api_data and team_type in api_data["team_form"]:
                form_data = api_data["team_form"][team_type]
                if isinstance(form_data, list) and form_data:
                    form_string = ""
                    for i in range(min(5, len(form_data))):
                        if isinstance(form_data[i], dict) and "result" in form_data[i]:
                            form_string += form_data[i]["result"]
                    
                    if form_string:
                        formatted_data[team_key]["form"] = form_string
                        formatted_data[team_key]["recent_matches"] = form_data[:5]
                        logger.info(f"Forma recente encontrada para {team_name}: {form_string}")
        
        # 5. Extrair dados de H2H
        h2h_data = None
        
        # Verificar diferentes locais para dados H2H
        if "head_to_head" in api_data:
            h2h_data = api_data["head_to_head"]
            logger.info("Dados H2H encontrados em head_to_head")
        elif "match_details" in api_data and api_data["match_details"]:
            if "h2h" in api_data["match_details"]:
                h2h_data = api_data["match_details"]["h2h"]
                logger.info("Dados H2H encontrados em match_details.h2h")
        
        if h2h_data and isinstance(h2h_data, dict):
            # Mapear campos H2H
            h2h_mappings = {
                "total_matches": ["total_matches", "matches"],
                "home_wins": ["home_wins"],
                "away_wins": ["away_wins"],
                "draws": ["draws"],
                "over_2_5_pct": ["over_2_5_percentage"],
                "btts_pct": ["btts_percentage"],
                "avg_cards": ["average_cards"],
                "avg_corners": ["average_corners"]
            }
            
            # Extrair valores
            for target_field, source_fields in h2h_mappings.items():
                for field in source_fields:
                    if field in h2h_data:
                        value = h2h_data[field]
                        if value is not None and value != 'N/A':
                            try:
                                formatted_data["h2h"][target_field] = float(value)
                                break
                            except (ValueError, TypeError):
                                pass
            
            # Extrair partidas recentes H2H
            if "matches" in h2h_data and isinstance(h2h_data["matches"], list):
                formatted_data["h2h"]["recent_matches"] = h2h_data["matches"][:5]
        
        # 6. Calcular estatísticas derivadas
        for team_key in ["home_team", "away_team"]:
            team_stats = formatted_data[team_key]
            
            # Calcular estatísticas por jogo se tivermos jogos
            if team_stats["played"] > 0:
                # Cartões por jogo
                if team_stats["cards_total"] > 0:
                    team_stats["cards_per_game"] = round(team_stats["cards_total"] / team_stats["played"], 2)
                
                # Escanteios totais e por jogo
                if team_stats["corners_for"] > 0 or team_stats["corners_against"] > 0:
                    team_stats["corners_total"] = team_stats["corners_for"] + team_stats["corners_against"]
                    team_stats["corners_per_game"] = round(team_stats["corners_total"] / team_stats["played"], 2)
        
        # Log do status dos dados
        home_stats_count = sum(1 for v in formatted_data["home_team"].values() if isinstance(v, (int, float)) and v > 0)
        away_stats_count = sum(1 for v in formatted_data["away_team"].values() if isinstance(v, (int, float)) and v > 0)
        h2h_stats_count = sum(1 for v in formatted_data["h2h"].values() if isinstance(v, (int, float)) and v > 0)
        
        logger.info(f"Extração concluída: {home_stats_count} valores para casa, {away_stats_count} para visitante, {h2h_stats_count} para H2H")
        
        return formatted_data
        
    except Exception as e:
        import traceback
        logger.error(f"Erro durante extração de dados: {str(e)}")
        logger.error(traceback.format_exc())
        return formatted_data


def extract_team_data(api_data, formatted_data, team_type):
    """
    Extrai dados de um time específico.
    
    Args:
        api_data (dict): Dados da API
        formatted_data (dict): Estrutura formatada
        team_type (str): "home" ou "away"
    """
    # Mapeia campos da API para nossos campos
    field_mapping = {
        "played": ["matches_played", "seasonMatchesPlayed_overall", "MP"],
        "wins": ["wins", "seasonWinsNum_overall", "W"],
        "draws": ["draws", "seasonDrawsNum_overall", "D"],
        "losses": ["losses", "seasonLossesNum_overall", "L"],
        "goals_scored": ["goals_scored", "seasonGoals_overall", "Gls", "goals"],
        "goals_conceded": ["goals_conceded", "seasonConceded_overall", "GA"],
        "clean_sheets_pct": ["clean_sheet_percentage", "seasonCSPercentage_overall"],
        "btts_pct": ["btts_percentage", "seasonBTTSPercentage_overall"],
        "over_2_5_pct": ["over_2_5_percentage", "seasonOver25Percentage_overall"],
        "xg": ["xG", "xg", "xg_for_overall", "expected_goals"],
        "xga": ["xGA", "xga", "xg_against_avg_overall"],
        "possession": ["possession", "possessionAVG_overall", "Poss"],
        # Cartões
        "cards_total": ["cards_total", "seasonCrdYNum_overall"],
        "yellow_cards": ["yellow_cards", "seasonCrdYNum_overall", "CrdY"],
        "red_cards": ["red_cards", "seasonCrdRNum_overall", "CrdR"],
        "over_3_5_cards_pct": ["over_3_5_cards_percentage"],
        # Escanteios
        "corners_for": ["corners_for", "seasonCornersFor_overall", "CK"],
        "corners_against": ["corners_against", "seasonCornersAgainst_overall"],
        "over_9_5_corners_pct": ["over_9_5_corners_percentage"],
    }
    
    # Campos específicos para casa/visitante
    if team_type == "home":
        specific_mapping = {
            "home_played": ["matches_played_home", "seasonMatchesPlayed_home"],
            "home_wins": ["home_wins", "seasonWinsNum_home"],
            "home_draws": ["home_draws", "seasonDrawsNum_home"],
            "home_losses": ["home_losses", "seasonLossesNum_home"],
            "home_goals_scored": ["goals_scored_home", "seasonGoals_home"],
            "home_goals_conceded": ["goals_conceded_home", "seasonConceded_home"],
            "home_cards_per_game": ["cards_per_game_home"],
            "home_corners_per_game": ["corners_per_game_home"],
        }
        field_mapping.update(specific_mapping)
    else:
        specific_mapping = {
            "away_played": ["matches_played_away", "seasonMatchesPlayed_away"],
            "away_wins": ["away_wins", "seasonWinsNum_away"],
            "away_draws": ["away_draws", "seasonDrawsNum_away"],
            "away_losses": ["away_losses", "seasonLossesNum_away"],
            "away_goals_scored": ["goals_scored_away", "seasonGoals_away"],
            "away_goals_conceded": ["goals_conceded_away", "seasonConceded_away"],
            "away_cards_per_game": ["cards_per_game_away"],
            "away_corners_per_game": ["corners_per_game_away"],
        }
        field_mapping.update(specific_mapping)

    # Localiza os dados do time na estrutura da API
    team_stats = {}
    team_key = f"{team_type}_team"
    
    # Encontra a raiz dos dados do time
    if "basic_stats" in api_data and team_key in api_data["basic_stats"]:
        team_data = api_data["basic_stats"][team_key]
        
        # Extrai estatísticas da estrutura aninhada
        if "stats" in team_data:
            if isinstance(team_data["stats"], dict):
                # Se stats é um objeto direto
                team_stats = team_data["stats"]
            elif isinstance(team_data["stats"], dict) and "stats" in team_data["stats"]:
                # Se stats está aninhado mais profundamente
                team_stats = team_data["stats"]["stats"]
    
    # Extrai cada campo mapeado
    for target_field, source_fields in field_mapping.items():
        for source_field in source_fields:
            if source_field in team_stats:
                value = team_stats[source_field]
                if value is not None and value != 'N/A':
                    try:
                        formatted_data[f"{team_type}_team"][target_field] = float(value)
                        break
                    except (ValueError, TypeError):
                        pass
    
    # Extrai dados avançados se disponíveis
    if "advanced_stats" in api_data and team_type in api_data["advanced_stats"]:
        adv_stats = api_data["advanced_stats"][team_type]
        if "ppda" in adv_stats:
            formatted_data[f"{team_type}_team"]["ppda"] = float(adv_stats["ppda"]) if adv_stats["ppda"] not in [None, 'N/A'] else 0
    
    # Extrai dados de forma
    if "team_form" in api_data and team_type in api_data["team_form"]:
        form_data = api_data["team_form"][team_type]
        if isinstance(form_data, list) and form_data:
            form_string = ""
            for match in form_data[:5]:
                if isinstance(match, dict) and "result" in match:
                    form_string += match["result"]
            formatted_data[f"{team_type}_team"]["form"] = form_string
            formatted_data[f"{team_type}_team"]["recent_matches"] = form_data[:5]
    
    # Calcula estatísticas derivadas se necessário
    calc_derived_stats(formatted_data[f"{team_type}_team"])

def extract_h2h_data(api_data, formatted_data):
    """
    Extrai dados de confronto direto (H2H).
    
    Args:
        api_data (dict): Dados da API
        formatted_data (dict): Estrutura formatada
    """
    h2h_data = None
    
    # Tenta encontrar os dados H2H em diferentes locais
    if "head_to_head" in api_data:
        h2h_data = api_data["head_to_head"]
    elif "match_details" in api_data and api_data["match_details"] and "h2h" in api_data["match_details"]:
        h2h_data = api_data["match_details"]["h2h"]
    
    if h2h_data and isinstance(h2h_data, dict):
        # Mapeia campos
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
        
        # Extrai cada campo
        for target_field, source_fields in field_mapping.items():
            for source_field in source_fields:
                if source_field in h2h_data:
                    value = h2h_data[source_field]
                    if value is not None and value != 'N/A':
                        try:
                            formatted_data["h2h"][target_field] = float(value)
                            break
                        except (ValueError, TypeError):
                            pass
        
        # Extrai partidas recentes
        if "matches" in h2h_data and isinstance(h2h_data["matches"], list):
            formatted_data["h2h"]["recent_matches"] = h2h_data["matches"][:5]

def calc_derived_stats(team_stats):
    """
    Calcula estatísticas derivadas com base nas estatísticas básicas.
    
    Args:
        team_stats (dict): Estatísticas do time para calcular derivadas
    """
    # Calcula cartões por jogo
    if team_stats["played"] > 0:
        if team_stats["cards_total"] > 0:
            team_stats["cards_per_game"] = round(team_stats["cards_total"] / team_stats["played"], 2)
        
        # Calcula escanteios totais e por jogo
        if team_stats["corners_for"] > 0 or team_stats["corners_against"] > 0:
            team_stats["corners_total"] = team_stats["corners_for"] + team_stats["corners_against"]
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
