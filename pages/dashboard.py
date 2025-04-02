# No início do arquivo, junto com os outros imports
import logging
import traceback
import json
import os
import time
import streamlit as st
from utils.core import show_valuehunter_logo, go_to_login, update_purchase_button, DATA_DIR
from utils.data import parse_team_stats, get_odds_data, format_prompt
from utils.ai import analyze_with_gpt, format_enhanced_prompt, format_highly_optimized_prompt
from utils.ai import analyze_with_gpt, format_enhanced_prompt, format_highly_optimized_prompt, calculate_advanced_probabilities

# Configuração de logging
logger = logging.getLogger("valueHunter.dashboard")

# Diretório para cache de times
TEAMS_CACHE_DIR = os.path.join(DATA_DIR, "teams_cache")
os.makedirs(TEAMS_CACHE_DIR, exist_ok=True)

# Funções auxiliares para seleção de ligas (ADICIONADAS NO INÍCIO)
def get_league_selection():
    """
    Função melhorada para obter a lista de ligas e mostrar o seletor,
    eliminando duplicações com diferentes formatações.
    
    Returns:
        str: A liga selecionada ou None se houver erro
    """
    try:
        # Adicione um placeholder para mensagens de status
        status_message = st.empty()
        status_message.info("Carregando ligas disponíveis...")
        
        # Importar a função para ligas pré-definidas
        from utils.footystats_api import get_user_selected_leagues_direct
        
        # Obter ligas pré-definidas
        all_leagues = get_user_selected_leagues_direct()
        
        if not all_leagues:
            st.error("Nenhuma liga disponível na lista pré-definida.")
            return None
        
        # Simplificar nomes e eliminar duplicatas baseadas no mesmo conteúdo 
        canonical_leagues = {}  # Mapeamento de nomes simplificados para nomes originais
        
        # Detectar e combinar ligas duplicadas
        for league in all_leagues:
            # Criar uma versão simplificada do nome da liga para comparação
            simple_name = league.lower()
            
            # Remover partes comuns que variam entre as duplicatas
            simple_name = simple_name.replace("(brazil)", "").replace("(germany)", "")
            simple_name = simple_name.replace("(england)", "").replace("(france)", "")
            simple_name = simple_name.replace("(italy)", "").replace("(spain)", "")
            simple_name = simple_name.replace("(portugal)", "").replace("(europe)", "")
            simple_name = simple_name.strip()
            
            # Se já temos esta liga (verificando pelo nome simplificado)
            if simple_name in canonical_leagues:
                # Manter o nome mais curto como preferido
                if len(league) < len(canonical_leagues[simple_name]):
                    canonical_leagues[simple_name] = league
            else:
                canonical_leagues[simple_name] = league
        
        # Obter lista final de ligas sem duplicatas
        unique_leagues = list(canonical_leagues.values())
        
        # Ordenar alfabeticamente
        unique_leagues.sort()
        
        # Inicializar seleção se necessário
        if 'selected_league' not in st.session_state or st.session_state.selected_league not in unique_leagues:
            st.session_state.selected_league = unique_leagues[0] if unique_leagues else None
        
        # Seletor de liga
        selected_league = st.sidebar.selectbox(
            "Escolha o campeonato:",
            options=unique_leagues,
            index=unique_leagues.index(st.session_state.selected_league) if st.session_state.selected_league in unique_leagues else 0,
            key="league_selector"
        )
        
        # Verificar se a liga mudou
        if selected_league != st.session_state.selected_league:
            st.sidebar.info(f"Mudando de {st.session_state.selected_league} para {selected_league}")
            st.session_state.selected_league = selected_league
            
            # Limpar seleções de time anteriores
            if 'home_team_selector' in st.session_state:
                del st.session_state.home_team_selector
            if 'away_team_selector' in st.session_state:
                del st.session_state.away_team_selector
                
            # Recarregar a página
            st.experimental_rerun()
        
        status_message.empty()  # Limpar a mensagem de status
        return selected_league
    
    except Exception as e:
        logger.error(f"Erro ao selecionar liga: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"Erro ao carregar ligas: {str(e)}")
        return None

# Mapeamento direto das ligas para seus IDs corretos
LEAGUE_SEASON_IDS = {
    "Primera División (Argentina)": 14125,
    "Serie A (Brazil)": 14231,
    "Brasileirão": 14231,
    "Serie B (Brazil)": 14305,
    "Copa do Brasil": 14210,
    "Primera División (Uruguay)": 14128,
    "Copa Libertadores": 13974,
    "Copa Sudamericana": 13965,
    "Premier League": 12325,
    "Premier League (England)": 12325,
    "La Liga": 12316,
    "La Liga (Spain)": 12316,
    "Segunda División": 12467,
    "Bundesliga": 12529,
    "Bundesliga (Germany)": 12529,
    "2. Bundesliga": 12528,
    "Serie A (Italy)": 12530,
    "Serie B (Italy)": 12621,
    "Ligue 1": 12337,
    "Ligue 1 (France)": 12337,
    "Ligue 2": 12338,
    "Bundesliga (Austria)": 12472,
    "Pro League": 12137,
    "Eredivisie": 12322,
    "Eredivisie (Netherlands)": 12322,
    "Liga NOS": 12931,
    "Primeira Liga": 12931,
    "Champions League": 12321,
    "Champions League (Europe)": 12321,
    "Europa League": 12327,
    "Liga MX": 12136,
    "FA Cup": 13698,
    "EFL League One": 12446
}

def load_league_teams_direct(selected_league):
    """
    Carregar times de uma liga usando a API FootyStats com ID específico da temporada.
    
    Args:
        selected_league (str): Nome da liga
        
    Returns:
        list: Lista de nomes dos times ou lista vazia em caso de erro
    """
    try:
        import traceback
        import requests
        import json
        import os
        import time
        from datetime import datetime, timedelta
        from utils.core import DATA_DIR
        
        status = st.empty()
        status.info(f"Carregando times para {selected_league}...")
        
        # API Configuration
        API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"
        BASE_URL = "https://api.football-data-api.com"
        
        # Encontrar o season_id correto para a liga selecionada
        season_id = None
        
        # Verificar correspondência exata
        if selected_league in LEAGUE_SEASON_IDS:
            season_id = LEAGUE_SEASON_IDS[selected_league]
        else:
            # Verificar correspondência parcial
            selected_league_lower = selected_league.lower()
            for league, id in LEAGUE_SEASON_IDS.items():
                if league.lower() in selected_league_lower or selected_league_lower in league.lower():
                    season_id = id
                    break
        
        if not season_id:
            status.error(f"Não foi possível encontrar ID para liga: {selected_league}")
            return []
        
        logger.info(f"Usando season_id {season_id} para {selected_league}")
        
        # Verificar cache
        cache_dir = os.path.join(DATA_DIR, "teams_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Nome do arquivo de cache
        safe_league = selected_league.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
        cache_file = os.path.join(cache_dir, f"{safe_league}_{season_id}.json")
        
        # Verificar cache
        force_refresh = False
        if os.path.exists(cache_file) and not force_refresh:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Verificar se o cache é recente (menos de 24 horas)
                if "timestamp" in cache_data:
                    cache_time = datetime.fromtimestamp(cache_data["timestamp"])
                    if datetime.now() - cache_time < timedelta(days=1):
                        logger.info(f"Usando times em cache para '{selected_league}'")
                        status.success(f"✅ {len(cache_data['teams'])} times carregados do cache")
                        return sorted(cache_data.get("teams", []))
                    else:
                        logger.info(f"Cache expirado para '{selected_league}'")
            except Exception as e:
                logger.error(f"Erro ao ler cache: {str(e)}")
        
        try:
            # Buscar times da API
            logger.info(f"Buscando times para '{selected_league}' (season_id: {season_id})")
            
            response = requests.get(
                f"{BASE_URL}/league-teams", 
                params={
                    "key": API_KEY,
                    "season_id": season_id,
                    "include": "stats"
                },
                timeout=15
            )
            
            if response.status_code != 200:
                status.error(f"Erro da API: {response.status_code}")
                logger.error(f"Erro da API: {response.status_code}")
                
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg = error_data["message"]
                        logger.error(f"Mensagem da API: {error_msg}")
                        
                        # Mostrar diagnóstico
                        with st.expander("Diagnóstico da API FootyStats", expanded=True):
                            st.error(f"Erro da API: {error_msg}")
                            st.info(f"Liga: {selected_league}")
                            st.info(f"Season ID usado: {season_id}")
                            
                            # Botão para limpar cache
                            if st.button("Limpar Cache e Tentar Novamente", key="clear_cache_forced"):
                                if os.path.exists(cache_file):
                                    try:
                                        os.remove(cache_file)
                                        st.success("Cache removido!")
                                    except:
                                        st.error("Erro ao remover cache")
                                st.experimental_rerun()
                except:
                    pass
                    
                return []
            
            # Processar resposta
            data = response.json()
            
            if "data" not in data or not isinstance(data["data"], list):
                status.error("Formato de resposta inválido")
                logger.error(f"Formato de resposta inválido: {data}")
                return []
            
            # Extrair nomes dos times
            teams = []
            for team in data["data"]:
                if "name" in team:
                    teams.append(team["name"])
            
            # Salvar no cache
            if teams:
                try:
                    cache_data = {
                        "teams": teams,
                        "timestamp": time.time(),
                        "season_id": season_id
                    }
                    
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f)
                    
                    logger.info(f"Salvos {len(teams)} times no cache para {selected_league}")
                except Exception as e:
                    logger.error(f"Erro ao salvar cache: {str(e)}")
            
            # Sucesso!
            status.success(f"✅ {len(teams)} times carregados para {selected_league}")
            return sorted(teams)
            
        except Exception as e:
            status.error(f"Erro ao carregar times: {str(e)}")
            logger.error(f"Erro ao carregar times: {str(e)}")
            
            # Capturar o traceback manualmente
            import traceback as tb
            error_traceback = tb.format_exc()
            logger.error(error_traceback)
            
            # Mostrar diagnóstico detalhado
            with st.expander("Detalhes do Erro", expanded=True):
                st.error(f"Erro ao acessar a API FootyStats: {str(e)}")
                st.code(error_traceback)
            
            return []
    except Exception as e:
        logger.error(f"Erro geral em load_league_teams_direct: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"Erro ao carregar times: {str(e)}")
        return []

def show_league_update_button(selected_league):
    """
    Mostra o botão de atualização para a liga selecionada.
    Evita problemas de indentação e de sintaxe.
    
    Args:
        selected_league (str): Nome da liga selecionada
    """
    if st.sidebar.button("🔄 Atualizar Times", type="primary", use_container_width=True):
        try:
            # Limpar caches para a liga selecionada
            from utils.footystats_api import clear_league_cache
            num_cleared = clear_league_cache(selected_league)
            st.sidebar.success(f"Caches limpos para {selected_league}: {num_cleared} arquivos")
            # Recarregar a página
            st.experimental_rerun()
        except Exception as refresh_error:
            st.sidebar.error(f"Erro ao atualizar: {str(refresh_error)}")

def clear_cache(league_name=None):
    """
    Limpa o cache de times e dados da liga especificada ou de todas as ligas
    
    Args:
        league_name (str, optional): Nome da liga para limpar o cache. Se None, limpa todas as ligas.
    
    Returns:
        int: Número de arquivos de cache removidos
    """
    import os
    import glob
    from utils.core import DATA_DIR
    
    cleaned = 0
    
    try:
        # Limpar cache de times
        teams_cache_dir = os.path.join(DATA_DIR, "teams_cache")
        if os.path.exists(teams_cache_dir):
            if league_name:
                # Sanitizar nome da liga para o padrão de arquivo
                safe_league = league_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
                pattern = os.path.join(teams_cache_dir, f"{safe_league}*.json")
                for cache_file in glob.glob(pattern):
                    try:
                        os.remove(cache_file)
                        cleaned += 1
                        logger.info(f"Removido cache de times: {os.path.basename(cache_file)}")
                    except Exception as e:
                        logger.error(f"Erro ao remover cache {cache_file}: {str(e)}")
            else:
                # Limpar todos os caches de times
                for cache_file in glob.glob(os.path.join(teams_cache_dir, "*.json")):
                    try:
                        os.remove(cache_file)
                        cleaned += 1
                        logger.info(f"Removido cache de times: {os.path.basename(cache_file)}")
                    except Exception as e:
                        logger.error(f"Erro ao remover cache {cache_file}: {str(e)}")
        
        # Limpar cache HTML
        if league_name:
            # Limpar apenas caches específicos da liga
            safe_league = league_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            pattern = os.path.join(DATA_DIR, f"cache_{safe_league}*.html")
            for cache_file in glob.glob(pattern):
                try:
                    os.remove(cache_file)
                    cleaned += 1
                    logger.info(f"Removido cache HTML: {os.path.basename(cache_file)}")
                except Exception as e:
                    logger.error(f"Erro ao remover cache {cache_file}: {str(e)}")
        else:
            # Limpar todos os caches HTML
            for cache_file in glob.glob(os.path.join(DATA_DIR, "cache_*.html")):
                try:
                    os.remove(cache_file)
                    cleaned += 1
                    logger.info(f"Removido cache HTML: {os.path.basename(cache_file)}")
                except Exception as e:
                    logger.error(f"Erro ao remover cache {cache_file}: {str(e)}")
        
        # Limpar cache da API-Football se existir
        api_cache_dir = os.path.join(DATA_DIR, "api_cache")
        if os.path.exists(api_cache_dir):
            for cache_file in glob.glob(os.path.join(api_cache_dir, "*.json")):
                try:
                    os.remove(cache_file)
                    cleaned += 1
                    logger.info(f"Removido cache da API: {os.path.basename(cache_file)}")
                except Exception as e:
                    logger.error(f"Erro ao remover cache da API {cache_file}: {str(e)}")
    
        return cleaned
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
        return cleaned

def diagnose_api_issues(selected_league):
    """
    Diagnostica problemas de acesso a uma liga específica
    
    Args:
        selected_league (str): Nome da liga
        
    Returns:
        dict: Resultado do diagnóstico
    """
    try:
        from utils.footystats_api import find_league_id_by_name, test_api_connection, clear_league_cache
        
        # Teste de conexão com a API
        api_test = test_api_connection()
        
        # Verificar se a liga está no mapeamento
        league_exists = False
        similar_leagues = []
        league_id = find_league_id_by_name(selected_league)
        
        if api_test["success"] and api_test["available_leagues"]:
            # Verificar correspondência exata
            for league in api_test["available_leagues"]:
                if league.lower() == selected_league.lower():
                    league_exists = True
                    break
                
                # Coletar ligas similares
                if selected_league.split(" (")[0].lower() in league.lower() or league.split(" (")[0].lower() in selected_league.lower():
                    similar_leagues.append(league)
        
        if league_exists and league_id:
            # Liga existe e temos um ID
            return f"""
            ✅ **Liga {selected_league} encontrada na sua conta**
            
            **ID da liga:** {league_id}
            
            **Status da API:**
            - ✓ API funcionando corretamente
            - ✓ Sua conta tem acesso a essa liga
            
            Se os times não estão aparecendo:
            1. Pode ser um problema temporário de cache da API FootyStats
            2. Aguarde alguns minutos e tente novamente
            3. Use o botão "Limpar Cache e Tentar Novamente"
            """
        
        elif not league_exists and similar_leagues:
            # Liga não existe exatamente, mas temos similares
            similar_leagues_list = "\n".join([f"- {league}" for league in similar_leagues])
            return f"""
            ❌ **Liga '{selected_league}' não encontrada exatamente nesse formato**
            
            **Ligas similares disponíveis na sua conta:**
            {similar_leagues_list}
            
            **Recomendações:**
            - Tente selecionar uma das ligas listadas acima em vez de '{selected_league}'
            - Verifique se você selecionou esta liga na sua conta FootyStats
            
            **Para corrigir:**
            1. Acesse [FootyStats API Dashboard](https://footystats.org/api/user-dashboard)
            2. Certifique-se de que a liga esteja selecionada
            3. Aguarde até 30 minutos para que as alterações sejam aplicadas
            4. Limpe o cache e tente novamente
            """
        
        else:
            # Liga não existe e não temos similares
            available_sample = ", ".join(api_test["available_leagues"][:5]) if api_test["available_leagues"] else "Nenhuma liga disponível"
            
            return f"""
            ❌ **Liga '{selected_league}' não encontrada na sua conta**
            
            **Status da API:**
            - {"✓ API funcionando corretamente" if api_test["success"] else "✗ Problemas com a API FootyStats"}
            
            **Ligas disponíveis na sua conta:**
            {available_sample}{"..." if len(api_test["available_leagues"]) > 5 else ""}
            
            **Recomendações:**
            - Verifique se você selecionou esta liga na sua conta FootyStats
            - Selecione uma das ligas disponíveis listadas acima
            
            **Para corrigir:**
            1. Acesse [FootyStats API Dashboard](https://footystats.org/api/user-dashboard)
            2. Procure por ligas similares a '{selected_league}' e selecione-as
            3. Aguarde até 30 minutos para que as alterações sejam aplicadas
            4. Limpe o cache e tente novamente
            """
            
    except Exception as e:
        import traceback
        logger.error(f"Erro ao diagnosticar problemas na API: {str(e)}")
        logger.error(traceback.format_exc())
        
        return f"""
        ❌ **Erro durante diagnóstico: {str(e)}**
        
        Isso pode indicar um problema com a configuração da API FootyStats.
        
        **Recomendações:**
        - Verifique se sua chave API está configurada corretamente
        - Certifique-se de que você tem uma assinatura ativa no FootyStats
        - Verifique sua conexão com a internet
        - Tente reiniciar o aplicativo
        """

# FUNÇÃO ATUALIZADA - PRINCIPAL MELHORIA
# Versão limpa de fetch_stats_data em pages/dashboard.py
# Remova o código de fallback mantendo apenas dados reais

def fetch_stats_data(selected_league, home_team=None, away_team=None):
    """
    Busca estatísticas das equipes sem fallbacks
    
    Args:
        selected_league (str): Nome da liga
        home_team (str, optional): Nome do time da casa
        away_team (str, optional): Nome do time visitante
        
    Returns:
        tuple: (DataFrame com estatísticas, dados brutos) ou (None, None) em caso de erro
    """
    try:
        import logging
        import traceback
        
        # Configuração de logging
        logger = logging.getLogger("valueHunter.dashboard")
        
        # Status placeholder
        status = st.empty()
        
        # Verificar se temos times específicos para buscar
        if not home_team or not away_team:
            st.error("É necessário selecionar dois times para análise.")
            return None, None
        
        # Iniciar busca
        status.info("Buscando estatísticas atualizadas...")
        
        try:
            from utils.enhanced_api_client import get_complete_match_analysis, convert_to_dataframe_format
            
            # Determinar o season_id
            if selected_league == "EFL League One (England)":
                season_id = 12446  # ID fixo conhecido para EFL League One
            else:
                # Código original para outras ligas
                from utils.footystats_api import LEAGUE_IDS
                season_id = LEAGUE_IDS.get(selected_league)
                if not season_id:
                    # Buscar correspondência parcial
                    for league_name, league_id in LEAGUE_IDS.items():
                        if league_name.lower() in selected_league.lower() or selected_league.lower() in league_name.lower():
                            season_id = league_id
                            break
            
            if not season_id:
                st.error(f"Não foi possível encontrar ID para liga: {selected_league}")
                st.info("Verifique se a liga está corretamente selecionada na sua conta FootyStats.")
                return None, None
            
            # Informar ao usuário
            st.info(f"Buscando estatísticas para {selected_league} (ID: {season_id})")
            logger.info(f"Iniciando busca para {home_team} vs {away_team} na liga {selected_league} (ID: {season_id})")
            
            # Buscar análise completa
            complete_analysis = get_complete_match_analysis(home_team, away_team, season_id, force_refresh=False)
            
            # Verificar se obtivemos dados
            if not complete_analysis:
                st.error(f"Não foi possível obter estatísticas para {home_team} vs {away_team}")
                return None, None
            
            # Converter para DataFrame
            team_stats_df = convert_to_dataframe_format(complete_analysis)
            if team_stats_df is None:
                st.error("Erro ao processar estatísticas para formato DataFrame")
                return None, None
                
            # Sucesso ao carregar os dados
            st.success(f"Estatísticas carregadas com sucesso para {home_team} vs {away_team}")
            
            # Processamento simplificado dos dados
            status.info("Processando dados estatísticos...")
            
            # Inicializar estrutura de dados otimizada
            optimized_data = {
                "match_info": {
                    "home_team": home_team,
                    "away_team": away_team,
                    "league": selected_league,
                    "league_id": season_id
                },
                "home_team": {},
                "away_team": {},
                "h2h": {}
            }

            # Extrair dados reais (sem fallback)
            if isinstance(complete_analysis, dict):
                # Usar a função simplificada para extrair apenas os campos essenciais
                from utils.prompt_adapter import simplify_api_data
                
                # Substituir o optimized_data com uma versão simplificada
                optimized_data = simplify_api_data(complete_analysis, home_team, away_team)
                
                # Preservar informações da liga que podem ter sido perdidas
                optimized_data["match_info"]["league"] = selected_league
                optimized_data["match_info"]["league_id"] = season_id
                
                logger.info("Dados extraídos para análise de IA")
            
            # Contagem de campos
            home_fields = sum(1 for k, v in optimized_data["home_team"].items() 
                          if (isinstance(v, (int, float)) and v != 0) or 
                            (isinstance(v, str) and v != "" and v != "?????"))
                            
            away_fields = sum(1 for k, v in optimized_data["away_team"].items() 
                          if (isinstance(v, (int, float)) and v != 0) or 
                            (isinstance(v, str) and v != "" and v != "?????"))
                            
            h2h_fields = sum(1 for k, v in optimized_data["h2h"].items() 
                          if isinstance(v, (int, float)) and v != 0)
            
            # Log de dados extraídos
            logger.info(f"Campos extraídos: Casa={home_fields}, Visitante={away_fields}, H2H={h2h_fields}")
            
            # Alertas ao usuário sobre quantidade de dados
            if home_fields < 10 or away_fields < 10:
                st.warning(f"Extração com dados limitados ({home_fields} para casa, {away_fields} para visitante)")
            else:
                st.success(f"✅ Dados extraídos: {home_fields} campos para casa, {away_fields} para visitante")
                
            # Modo debug
            if "debug_mode" in st.session_state and st.session_state.debug_mode:
                with st.expander("Dados extraídos", expanded=False):
                    st.json(optimized_data)
                    
            # Retornar os dados
            return team_stats_df, optimized_data
            
        except Exception as e:
            # Log detalhado do erro
            logger.error(f"Erro ao buscar ou processar estatísticas: {str(e)}")
            logger.error(traceback.format_exc())
            st.error(f"Erro: {str(e)}")
            
            # Mostrar detalhes para debug
            if "debug_mode" in st.session_state and st.session_state.debug_mode:
                with st.expander("Detalhes do erro", expanded=True):
                    st.code(traceback.format_exc())
                    
            return None, None
            
    except Exception as e:
        logger.error(f"Erro geral em fetch_stats_data: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"Erro ao buscar dados: {str(e)}")
        return None, None

def get_cached_teams(league):
    """Carrega apenas os nomes dos times do cache persistente com verificação de temporada"""
    from utils.footystats_api import LEAGUE_SEASONS, CURRENT_SEASON
    
    # Determinar a temporada atual para a liga
    season = LEAGUE_SEASONS.get(league, CURRENT_SEASON)
    
    # Incluir a temporada no nome do arquivo de cache
    cache_file = os.path.join(TEAMS_CACHE_DIR, f"{league.replace(' ', '_')}_{season}_teams.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                teams = data.get('teams', [])
                timestamp = data.get('timestamp', 0)
                
                # Verificar se o cache não é muito antigo (7 dias)
                cache_max_age = 7 * 24 * 60 * 60  # 7 dias em segundos
                if time.time() - timestamp > cache_max_age:
                    logger.info(f"Cache para {league} (temporada {season}) está desatualizado")
                    return [], 0
                
                logger.info(f"Carregados {len(teams)} times do cache para {league} (temporada {season})")
                return teams, timestamp
        except Exception as e:
            logger.error(f"Erro ao carregar cache para {league}: {str(e)}")
    
    return [], 0

def save_teams_to_cache(league, teams):
    """Salva os times no cache persistente com identificação de temporada"""
    from utils.footystats_api import LEAGUE_SEASONS, CURRENT_SEASON
    
    # Determinar a temporada atual para a liga
    season = LEAGUE_SEASONS.get(league, CURRENT_SEASON)
    
    # Incluir a temporada no nome do arquivo de cache
    cache_file = os.path.join(TEAMS_CACHE_DIR, f"{league.replace(' ', '_')}_{season}_teams.json")
    
    try:
        data = {
            'teams': teams,
            'timestamp': time.time(),
            'season': season  # Armazenar a temporada no cache para referência
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
        logger.info(f"Salvos {len(teams)} times no cache para {league} (temporada {season})")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar cache para {league}: {str(e)}")
        return False

def get_league_teams(selected_league, force_refresh=False):
    """Obtém apenas os nomes dos times usando cache quando possível"""
    try:
        # Verificar cache primeiro (se não estiver forçando refresh)
        if not force_refresh:
            teams, timestamp = get_cached_teams(selected_league)
            
            # Se temos times em cache válido
            if teams and len(teams) > 0:
                logger.info(f"Usando nomes de times em cache para {selected_league} ({len(teams)} times)")
                return teams
        
        # Se chegamos aqui, precisamos buscar os nomes dos times online
        from utils.footystats_api import get_team_names_by_league
        
        # Buscar times da FootyStats API
        teams = get_team_names_by_league(selected_league)
            
        if not teams:
            logger.error(f"API não retornou times para {selected_league}")
            return []
        
        # Salvar apenas os nomes dos times no cache persistente
        save_teams_to_cache(selected_league, teams)
            
        logger.info(f"Times carregados da API: {len(teams)} times encontrados")
        return teams
            
    except Exception as e:
        logger.error(f"Erro ao carregar times da liga: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def show_usage_stats():
    """Display usage statistics with forced refresh"""
    try:
        # Verificar se temos query params que indicam uma ação recente
        force_refresh = False
        if 'payment_processed' in st.query_params or 'force_refresh' in st.query_params:
            force_refresh = True
            # Limpar parâmetros após uso
            if 'force_refresh' in st.query_params:
                del st.query_params['force_refresh']
        
        # IMPORTANTE: Verificar se precisamos atualizar os dados
        if not hasattr(st.session_state, 'user_stats_cache') or force_refresh:
            # Primeira vez carregando ou após um refresh forçado
            stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
            # Armazenar em um cache temporário na sessão
            st.session_state.user_stats_cache = stats
            logger.info(f"Estatísticas recarregadas para {st.session_state.email}")
        else:
            # Usar cache se disponível
            stats = st.session_state.user_stats_cache        
        
        # Obter nome do usuário - com fallback seguro
        user_name = "Usuário"
        
        try:
            # Tentar obter o nome do usuário diretamente da estrutura de dados
            if hasattr(st.session_state.user_manager, "users") and st.session_state.email in st.session_state.user_manager.users:
                user_data = st.session_state.user_manager.users[st.session_state.email]
                if "name" in user_data:
                    user_name = user_data["name"]
            # Ou dos stats, se disponível
            elif "name" in stats:
                user_name = stats["name"]
        except Exception:
            pass  # Manter o fallback em caso de erro
        
        # Saudação com nome do usuário
        st.sidebar.markdown(f"### Olá, {user_name}!")
        
        st.sidebar.markdown("### Estatísticas de Uso")
        st.sidebar.markdown(f"**Créditos Restantes:** {stats['credits_remaining']}")
        
        # Add progress bar for credits
        if stats['credits_total'] > 0:
            progress = stats['credits_used'] / stats['credits_total']
            st.sidebar.progress(min(progress, 1.0))
        
        # Free tier renewal info (if applicable)
        if stats['tier'] == 'free' and stats.get('next_free_credits_time'):
            st.sidebar.info(f"⏱️ Renovação em: {stats['next_free_credits_time']}")
        elif stats['tier'] == 'free' and stats.get('free_credits_reset'):
            st.sidebar.success("✅ Créditos renovados!")
        
        # Warning for paid tiers about to be downgraded
        if stats.get('days_until_downgrade'):
            st.sidebar.warning(f"⚠️ Sem créditos há {7-stats['days_until_downgrade']} dias. Você será rebaixado para o pacote Free em {stats['days_until_downgrade']} dias se não comprar mais créditos.")
            
    except Exception as e:
        logger.error(f"Erro ao exibir estatísticas de uso: {str(e)}")
        st.sidebar.error("Erro ao carregar estatísticas")

def check_analysis_limits(selected_markets):
    """Check if user can perform analysis with selected markets"""
    try:
        num_markets = sum(1 for v in selected_markets.values() if v)
        stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
        
        # Check if user has enough credits
        remaining_credits = stats['credits_remaining']
        
        if num_markets > remaining_credits:
            # Special handling for Free tier
            if stats['tier'] == 'free':
                st.error(f"❌ Você esgotou seus 5 créditos gratuitos.")
                
                if stats.get('next_free_credits_time'):
                    st.info(f"⏱️ Seus créditos serão renovados em {stats['next_free_credits_time']}")
                
                st.warning("💡 Deseja continuar analisando sem esperar? Faça upgrade para um pacote pago.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Standard - 30 Créditos", key="upgrade_standard", use_container_width=True):
                        update_purchase_button(30, 19.99)
                        return False
                with col2:
                    if st.button("Pro - 60 Créditos", key="upgrade_pro", use_container_width=True):
                        update_purchase_button(60, 29.99)
                        return False
                
                return False
            else:
                # Paid tiers - offer to buy more credits
                st.warning(f"⚠️ Você tem apenas {remaining_credits} créditos restantes. Esta análise requer {num_markets} créditos.")
                
                # Show days until downgrade if applicable
                if stats.get('days_until_downgrade'):
                    st.warning(f"⚠️ Atenção: Você será rebaixado para o pacote Free em {stats['days_until_downgrade']} dias se não comprar mais créditos.")
                
                # Show purchase options
                st.info("Compre mais créditos para continuar.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("30 Créditos - R$19,99", use_container_width=True):
                        update_purchase_button(30, 19.99)
                        return False
                            
                with col2:
                    if st.button("60 Créditos - R$29,99", use_container_width=True):
                        update_purchase_button(60, 29.99)
                        return False
                
                return False
                
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar limites de análise: {str(e)}")
        st.error("Erro ao verificar limites de análise. Por favor, tente novamente.")
        return False

def show_main_dashboard():
    """Show the main dashboard with improved error handling and debug info"""
    try:
        # VERIFICAÇÃO DE AUTENTICAÇÃO
        if not hasattr(st.session_state, 'authenticated') or not st.session_state.authenticated:
            st.error("Sessão não autenticada. Por favor, faça login novamente.")
            st.session_state.page = "login"
            st.experimental_rerun()
            return
            
        if not hasattr(st.session_state, 'email') or not st.session_state.email:
            st.error("Informações de usuário não encontradas. Por favor, faça login novamente.")
            st.session_state.page = "login"
            st.experimental_rerun()
            return
            
        # Verificar se o user_manager está disponível
        if not hasattr(st.session_state, 'user_manager'):
            st.error("Gerenciador de usuários não inicializado.")
            st.session_state.page = "login"
            st.experimental_rerun()
            return
            
        # Garantir que a barra lateral esteja visível
        st.markdown("""
        <style>
        /* CSS simplificado para garantir visibilidade */
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
            min-width: 250px !important;
        }
        
        /* Ocultar apenas os elementos de navegação do Streamlit */
        header[data-testid="stHeader"],
        footer,
        #MainMenu {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Iniciar com log de diagnóstico
        logger.info("Iniciando renderização do dashboard principal")     
        
        # Adicionar modo de depuração para facilitar debug
        if "debug_mode" not in st.session_state:
            st.session_state.debug_mode = False
            
        # ------------------------------------------------------------
        # BARRA LATERAL REORGANIZADA
        # ------------------------------------------------------------
        
        # 1. Mostrar estatísticas de uso e saudação
        show_usage_stats()
        
        # 2. Escolha da liga (usando função auxiliar)
        selected_league = get_league_selection()
        if not selected_league:
            st.error("Não foi possível selecionar uma liga. Por favor, verifique a configuração.")
            return
        
        # Adicionar nota sobre o carregamento automático
        st.sidebar.info("Os times são carregados automaticamente ao selecionar uma liga.")
        
        # Separador para a barra lateral
        st.sidebar.markdown("---")
        
        # Botão de pacotes e logout
        if st.sidebar.button("🚀 Ver Pacotes de Créditos", key="sidebar_packages_button", use_container_width=True):
            st.session_state.page = "packages"
            st.experimental_rerun()
        
        if st.sidebar.button("Logout", key="sidebar_logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.email = None
            st.session_state.page = "landing"
            st.experimental_rerun()
            
        # Opções avançadas no sidebar
        with st.sidebar.expander("Opções avançadas"):
            st.session_state.debug_mode = st.checkbox("Modo de depuração", value=st.session_state.debug_mode)
            
            if st.button("Limpar cache"):
                cleaned = clear_cache()
                st.success(f"Cache limpo: {cleaned} arquivos removidos")
                
            if st.button("Reiniciar aplicação"):
                for key in list(st.session_state.keys()):
                    if key != "authenticated" and key != "email":
                        del st.session_state[key]
                st.success("Aplicação reiniciada")
                st.experimental_rerun()

        # ------------------------------------------------------------
        # CONTEÚDO PRINCIPAL 
        # ------------------------------------------------------------
        
        try:
            # Logo exibida consistentemente
            show_valuehunter_logo()
            
            # Título principal
            st.title("Seleção de Times")
            
            # Indicador de estado para depuração
            st.info(f"Liga selecionada: **{selected_league}**", icon="ℹ️")
            
            # Container para status
            status_container = st.empty()
            
            # Verificar conexão com a API
            with st.spinner("Verificando conexão..."):
                try:
                    from utils.footystats_api import test_api_connection
                    api_status = test_api_connection()
                    
                    if not api_status["success"]:
                        st.error(f"Erro de conexão com a API FootyStats: {api_status.get('message', 'Erro desconhecido')}")
                        st.info("Verifique sua conexão com a internet e suas credenciais da API.")
                        
                        # Botão para tentar novamente
                        if st.button("Tentar novamente"):
                            st.experimental_rerun()
                        return
                except Exception as api_error:
                    logger.error(f"Erro ao verificar conexão com a API: {str(api_error)}")
                    if st.session_state.debug_mode:
                        st.error(f"Erro ao verificar API: {str(api_error)}")
            
            # Carregar times diretamente (ignorando o cache)
            with st.spinner(f"Carregando times para {selected_league}..."):
                teams = load_league_teams_direct(selected_league)
            
            # Verificação adicional para garantir que temos times
            if not teams or len(teams) == 0:
                st.warning("Não foi possível carregar os times para este campeonato.")
                st.info("Por favor, recarregue a página e tente novamente.")
                
                # Botão para limpar cache
                if st.button("🔄 Limpar Cache e Tentar Novamente", key="clear_cache_btn"):
                    from utils.footystats_api import clear_league_cache
                    num_cleared = clear_league_cache(selected_league)
                    st.success(f"Cleared {num_cleared} cache files for {selected_league}")
                    st.experimental_rerun()
                
                return
            
            # Mostrar lista de times disponíveis
            with st.expander("Times Disponíveis Nesta Liga", expanded=False):
                st.write("Estes são os times disponíveis para análise:")
                
                # Criar layout de colunas para os times
                cols = st.columns(3)
                for i, team in enumerate(sorted(teams)):
                    cols[i % 3].write(f"- {team}")
                    
                st.info("Use os nomes exatos acima para selecionar os times.")
            
            # Usando o seletor nativo do Streamlit
            col1, col2 = st.columns(2)
            with col1:
                home_team = st.selectbox("Time da Casa:", teams, key="home_team_selector")
            with col2:
                away_teams = [team for team in teams if team != home_team]
                away_team = st.selectbox("Time Visitante:", away_teams, key="away_team_selector")
            
            logger.info(f"Times selecionados: {home_team} vs {away_team}")
            
            # Obter estatísticas do usuário
            user_stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
            
            # Bloco try separado para seleção de mercados
            try:
                # Seleção de mercados
                with st.expander("Mercados Disponíveis", expanded=True):
                    st.markdown("### Seleção de Mercados")
                    st.info(f"Você tem {user_stats['credits_remaining']} créditos disponíveis. Cada mercado selecionado consumirá 1 crédito.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_markets = {
                            "money_line": st.checkbox("Money Line (1X2)", value=True, key='ml'),
                            "gols": st.checkbox("Total de Gols", key='ou'),
                            "chance_dupla": st.checkbox("Chance Dupla", key='cd')
                        }
                    with col2:
                        selected_markets.update({
                            "ambos_marcam": st.checkbox("Ambos Marcam", key='btts'),
                            "escanteios": st.checkbox("Total de Escanteios", key='corners'),
                            "cartoes": st.checkbox("Total de Cartões", key='cards')
                        })

                    num_selected_markets = sum(1 for v in selected_markets.values() if v)
                    if num_selected_markets == 0:
                        st.warning("Por favor, selecione pelo menos um mercado para análise.")
                    else:
                        st.write(f"Total de créditos que serão consumidos: {num_selected_markets}")
                        
                logger.info(f"Mercados selecionados: {[k for k, v in selected_markets.items() if v]}")
                
            except Exception as markets_error:
                logger.error(f"Erro na seleção de mercados: {str(markets_error)}")
                logger.error(traceback.format_exc())
                st.error(f"Erro ao exibir mercados disponíveis: {str(markets_error)}")
                if st.session_state.debug_mode:
                    st.code(traceback.format_exc())
                return
            
            # Bloco try separado para odds
            try:
                # Odds
                odds_data = None
                if any(selected_markets.values()):
                    with st.expander("Configuração de Odds", expanded=True):
                        odds_data = get_odds_data(selected_markets)
                        
                logger.info(f"Odds configuradas: {odds_data is not None}")
                
            except Exception as odds_error:
                logger.error(f"Erro na configuração de odds: {str(odds_error)}")
                logger.error(traceback.format_exc())
                st.error(f"Erro ao configurar odds: {str(odds_error)}")
                if st.session_state.debug_mode:
                    st.code(traceback.format_exc())
                return
            
            # Botão de análise centralizado
            try:
                # Botão em largura total para melhor design
                analyze_button = st.button("Analisar Partida", type="primary", use_container_width=True)
                
                # Código atualizado para o botão de análise
                if analyze_button:
                    if not any(selected_markets.values()):
                        st.error("Por favor, selecione pelo menos um mercado para análise.")
                        return
                        
                    if not odds_data:
                        st.error("Por favor, configure as odds para os mercados selecionados.")
                        return
                    
                    # Verificar limites de análise
                    if not check_analysis_limits(selected_markets):
                        return
                        
                    # Criar um placeholder para o status
                    status = st.empty()
                    
                    # Buscar estatísticas em tempo real (sem cache)
                    status.info("Buscando estatísticas atualizadas...")
                    team_stats_df, stats_data = fetch_stats_data(selected_league, home_team, away_team)
                    
                    if team_stats_df is None:
                        status.error("Falha ao carregar estatísticas. Tente novamente.")
                        return
                    
                    # Modo de depuração - mostrar dados brutos
                    if st.session_state.debug_mode:
                        with st.expander("Dados brutos coletados da API", expanded=False):
                            st.json(stats_data)
                    
                    # Executar análise com tratamento de erro para cada etapa
                    try:
                        # Etapa 1: Verificar dados
                        status.info("Preparando dados para análise...")
                        if team_stats_df is None:
                            status.error("Falha ao carregar dados")
                            return
                
                        # Etapa 2: Processar os dados para análise
                        status.info("Processando dados estatísticos...")
                        
                        # Etapa 3: Formatar prompt e extrair probabilidades
                        status.info("Preparando análise...")
                        from utils.ai import format_highly_optimized_prompt, calculate_advanced_probabilities
                        
                        # Primeiro calculamos as probabilidades
                        original_probabilities = calculate_advanced_probabilities(
                            stats_data["home_team"], 
                            stats_data["away_team"]
                        )
                        
                        # Extrair probabilidades implícitas das odds
                        implied_probabilities = {}
                        
                        # Função auxiliar para extrair odds de um texto
                        def extract_odds(text, pattern, default=0.0):
                            import re
                            matches = re.findall(pattern, text)
                            if matches:
                                try:
                                    return float(matches[0])
                                except:
                                    pass
                            return default
                        
                        # Parsear as odds para Money Line
                        if selected_markets.get("money_line") and odds_data:
                            # Padrões para extrair odds
                            home_odd = extract_odds(odds_data, rf"(?:Casa|Home).*?@(\d+\.?\d*)")
                            draw_odd = extract_odds(odds_data, r"Empate.*?@(\d+\.?\d*)")
                            away_odd = extract_odds(odds_data, rf"(?:Fora|Away).*?@(\d+\.?\d*)")
                            
                            if home_odd > 0:
                                implied_probabilities["home"] = 100.0 / home_odd
                            if draw_odd > 0:
                                implied_probabilities["draw"] = 100.0 / draw_odd
                            if away_odd > 0:
                                implied_probabilities["away"] = 100.0 / away_odd
                        
                        # Parsear para Chance Dupla
                        if selected_markets.get("chance_dupla") and odds_data:
                            home_draw_odd = extract_odds(odds_data, r"1X.*?@(\d+\.?\d*)")
                            home_away_odd = extract_odds(odds_data, r"12.*?@(\d+\.?\d*)")
                            draw_away_odd = extract_odds(odds_data, r"X2.*?@(\d+\.?\d*)")
                            
                            if home_draw_odd > 0:
                                implied_probabilities["home_draw"] = 100.0 / home_draw_odd
                            if home_away_odd > 0:
                                implied_probabilities["home_away"] = 100.0 / home_away_odd
                            if draw_away_odd > 0:
                                implied_probabilities["draw_away"] = 100.0 / draw_away_odd
                        
                        # Parsear para BTTS
                        if selected_markets.get("ambos_marcam") and odds_data:
                            btts_yes_odd = extract_odds(odds_data, r"Sim.*?@(\d+\.?\d*)")
                            btts_no_odd = extract_odds(odds_data, r"Não.*?@(\d+\.?\d*)")
                            
                            if btts_yes_odd > 0:
                                implied_probabilities["btts_yes"] = 100.0 / btts_yes_odd
                            if btts_no_odd > 0:
                                implied_probabilities["btts_no"] = 100.0 / btts_no_odd
                        
                        # Adicionar as probabilidades implícitas às probabilidades originais
                        if implied_probabilities:
                            if "analysis_data" not in original_probabilities:
                                original_probabilities["analysis_data"] = {}
                            original_probabilities["analysis_data"]["implied_odds"] = implied_probabilities
                        
                        # Depois geramos o prompt com essas probabilidades
                        prompt = format_highly_optimized_prompt(stats_data, home_team, away_team, odds_data, selected_markets)
                        
                        if not prompt:
                            status.error("Falha ao preparar análise")
                            return
                        
                        # Etapa 4: Análise GPT com probabilidades originais
                        status.info("Realizando análise com IA...")
                        analysis = analyze_with_gpt(
                            prompt,
                            original_probabilities=original_probabilities,
                            selected_markets=selected_markets,
                            home_team=home_team,
                            away_team=away_team
                        )
                        
                        if not analysis:
                            status.error("Falha na análise com IA")
                            return
                        
                        # Etapa 5: Mostrar resultado
                        if analysis:
                            # Limpar status
                            status.empty()
                            
                            # Limpar possíveis tags HTML da resposta
                            if isinstance(analysis, str):
                                # Verificar se a análise começa com a tag de div
                                if "<div class=\"analysis-result\">" in analysis:
                                    analysis = analysis.replace("<div class=\"analysis-result\">", "")
                                    if "</div>" in analysis:
                                        analysis = analysis.replace("</div>", "")
                            
                            # IMPORTANTE: Aplicar formatação avançada para garantir filtragem por mercados selecionados
                            from utils.ai import format_analysis_response
                            
                            # Adiciona módulo re para expressões regulares caso não esteja importado
                            import re
                            
                            # Reconstrução completa da análise
                            def reconstruct_analysis(analysis_text, home_team, away_team, selected_markets, original_probabilities, implied_probabilities, odds_data):
                                # Iniciar construção da análise
                                new_analysis = []
                                
                                # Adicionar cabeçalho
                                new_analysis.append(f"# Análise da Partida\n## {home_team} x {away_team}")
                                
                                # Adicionar análise de mercados disponíveis
                                markets_section = "# Análise de Mercados Disponíveis:\n"
                                
                                # Moneyline
                                if selected_markets.get("money_line"):
                                    markets_section += "- **Money Line (1X2):**\n"
                                    home_odd = 0
                                    draw_odd = 0
                                    away_odd = 0
                                    
                                    # Extrair odds do texto original
                                    home_match = re.search(r"Casa.*?@(\d+\.?\d*)", odds_data)
                                    if home_match:
                                        home_odd = float(home_match.group(1))
                                        markets_section += f"  - Casa ({home_team}): @{home_odd}\n"
                                    
                                    draw_match = re.search(r"Empate.*?@(\d+\.?\d*)", odds_data)
                                    if draw_match:
                                        draw_odd = float(draw_match.group(1))
                                        markets_section += f"  - Empate: @{draw_odd}\n"
                                    
                                    away_match = re.search(r"Fora.*?@(\d+\.?\d*)", odds_data)
                                    if away_match:
                                        away_odd = float(away_match.group(1))
                                        markets_section += f"  - Fora ({away_team}): @{away_odd}\n"
                                    
                                    # Atualizar probabilidades implícitas
                                    if home_odd > 0:
                                        implied_probabilities["home"] = 100.0 / home_odd
                                    if draw_odd > 0:
                                        implied_probabilities["draw"] = 100.0 / draw_odd
                                    if away_odd > 0:
                                        implied_probabilities["away"] = 100.0 / away_odd
                                
                                # Chance Dupla
                                if selected_markets.get("chance_dupla"):
                                    markets_section += "- **Chance Dupla:**\n"
                                    home_draw_odd = 0
                                    home_away_odd = 0
                                    draw_away_odd = 0
                                    
                                    # Extrair odds do texto original
                                    hd_match = re.search(r"1X.*?@(\d+\.?\d*)", odds_data)
                                    if hd_match:
                                        home_draw_odd = float(hd_match.group(1))
                                        markets_section += f"  - 1X ({home_team} ou Empate): @{home_draw_odd}\n"
                                    
                                    ha_match = re.search(r"12.*?@(\d+\.?\d*)", odds_data)
                                    if ha_match:
                                        home_away_odd = float(ha_match.group(1))
                                        markets_section += f"  - 12 ({home_team} ou {away_team}): @{home_away_odd}\n"
                                    
                                    da_match = re.search(r"X2.*?@(\d+\.?\d*)", odds_data)
                                    if da_match:
                                        draw_away_odd = float(da_match.group(1))
                                        markets_section += f"  - X2 (Empate ou {away_team}): @{draw_away_odd}\n"
                                    
                                    # Atualizar probabilidades implícitas
                                    if home_draw_odd > 0:
                                        implied_probabilities["home_draw"] = 100.0 / home_draw_odd
                                    if home_away_odd > 0:
                                        implied_probabilities["home_away"] = 100.0 / home_away_odd
                                    if draw_away_odd > 0:
                                        implied_probabilities["draw_away"] = 100.0 / draw_away_odd
                                
                                # Ambos Marcam
                                if selected_markets.get("ambos_marcam"):
                                    markets_section += "- **Ambos Marcam (BTTS):**\n"
                                    btts_yes_odd = 0
                                    btts_no_odd = 0
                                    
                                    # Extrair odds do texto original
                                    yes_match = re.search(r"Sim.*?@(\d+\.?\d*)", odds_data)
                                    if yes_match:
                                        btts_yes_odd = float(yes_match.group(1))
                                        markets_section += f"  - Sim: @{btts_yes_odd}\n"
                                    
                                    no_match = re.search(r"Não.*?@(\d+\.?\d*)", odds_data)
                                    if no_match:
                                        btts_no_odd = float(no_match.group(1))
                                        markets_section += f"  - Não: @{btts_no_odd}\n"
                                    
                                    # Atualizar probabilidades implícitas
                                    if btts_yes_odd > 0:
                                        implied_probabilities["btts_yes"] = 100.0 / btts_yes_odd
                                    if btts_no_odd > 0:
                                        implied_probabilities["btts_no"] = 100.0 / btts_no_odd
                                
                                new_analysis.append(markets_section)
                                
                                # Probabilidades calculadas
                                probs_section = "# Probabilidades Calculadas (REAL vs IMPLÍCITA):\n"
                                opportunities = []
                                
                                # Money Line
                                if selected_markets.get("money_line") and "moneyline" in original_probabilities:
                                    probs_section += "## Money Line (1X2):\n"
                                    
                                    # Casa
                                    home_real = original_probabilities["moneyline"].get("home_win", 0)
                                    home_implicit = implied_probabilities.get("home", 0)
                                    home_value = home_real > home_implicit + 2
                                    
                                    probs_section += f"- **{home_team}**: Real {home_real:.1f}% vs Implícita {home_implicit:.1f}%{' (Valor)' if home_value else ''}\n"
                                    
                                    if home_value:
                                        opportunities.append(f"- **{home_team}**: Real {home_real:.1f}% vs Implícita {home_implicit:.1f}% (Valor de {home_real-home_implicit:.1f}%)")
                                    
                                    # Empate
                                    draw_real = original_probabilities["moneyline"].get("draw", 0)
                                    draw_implicit = implied_probabilities.get("draw", 0)
                                    draw_value = draw_real > draw_implicit + 2
                                    
                                    probs_section += f"- **Empate**: Real {draw_real:.1f}% vs Implícita {draw_implicit:.1f}%{' (Valor)' if draw_value else ''}\n"
                                    
                                    if draw_value:
                                        opportunities.append(f"- **Empate**: Real {draw_real:.1f}% vs Implícita {draw_implicit:.1f}% (Valor de {draw_real-draw_implicit:.1f}%)")
                                    
                                    # Fora
                                    away_real = original_probabilities["moneyline"].get("away_win", 0)
                                    away_implicit = implied_probabilities.get("away", 0)
                                    away_value = away_real > away_implicit + 2
                                    
                                    probs_section += f"- **{away_team}**: Real {away_real:.1f}% vs Implícita {away_implicit:.1f}%{' (Valor)' if away_value else ''}\n"
                                    
                                    if away_value:
                                        opportunities.append(f"- **{away_team}**: Real {away_real:.1f}% vs Implícita {away_implicit:.1f}% (Valor de {away_real-away_implicit:.1f}%)")
                                
                                # Double Chance
                                if selected_markets.get("chance_dupla") and "double_chance" in original_probabilities:
                                    probs_section += "## Chance Dupla (Double Chance):\n"
                                    
                                    # 1X
                                    hd_real = original_probabilities["double_chance"].get("home_or_draw", 0)
                                    hd_implicit = implied_probabilities.get("home_draw", 0)
                                    hd_value = hd_real > hd_implicit + 2
                                    
                                    probs_section += f"- **{home_team} ou Empate**: Real {hd_real:.1f}% vs Implícita {hd_implicit:.1f}%{' (Valor)' if hd_value else ''}\n"
                                    
                                    if hd_value:
                                        opportunities.append(f"- **{home_team} ou Empate**: Real {hd_real:.1f}% vs Implícita {hd_implicit:.1f}% (Valor de {hd_real-hd_implicit:.1f}%)")
                                    
                                    # 12
                                    ha_real = original_probabilities["double_chance"].get("home_or_away", 0)
                                    ha_implicit = implied_probabilities.get("home_away", 0)
                                    ha_value = ha_real > ha_implicit + 2
                                    
                                    probs_section += f"- **{home_team} ou {away_team}**: Real {ha_real:.1f}% vs Implícita {ha_implicit:.1f}%{' (Valor)' if ha_value else ''}\n"
                                    
                                    if ha_value:
                                        opportunities.append(f"- **{home_team} ou {away_team}**: Real {ha_real:.1f}% vs Implícita {ha_implicit:.1f}% (Valor de {ha_real-ha_implicit:.1f}%)")
                                    
                                    # X2
                                    da_real = original_probabilities["double_chance"].get("away_or_draw", 0)
                                    da_implicit = implied_probabilities.get("draw_away", 0)
                                    da_value = da_real > da_implicit + 2
                                    
                                    probs_section += f"- **Empate ou {away_team}**: Real {da_real:.1f}% vs Implícita {da_implicit:.1f}%{' (Valor)' if da_value else ''}\n"
                                    
                                    if da_value:
                                        opportunities.append(f"- **Empate ou {away_team}**: Real {da_real:.1f}% vs Implícita {da_implicit:.1f}% (Valor de {da_real-da_implicit:.1f}%)")
                                
                                # BTTS
                                if selected_markets.get("ambos_marcam") and "btts" in original_probabilities:
                                    probs_section += "## Ambos Marcam (BTTS):\n"
                                    
                                    # Sim
                                    yes_real = original_probabilities["btts"].get("yes", 0)
                                    yes_implicit = implied_probabilities.get("btts_yes", 0)
                                    yes_value = yes_real > yes_implicit + 2
                                    
                                    probs_section += f"- **Sim**: Real {yes_real:.1f}% vs Implícita {yes_implicit:.1f}%{' (Valor)' if yes_value else ''}\n"
                                    
                                    if yes_value:
                                        opportunities.append(f"- **Ambos Marcam - Sim**: Real {yes_real:.1f}% vs Implícita {yes_implicit:.1f}% (Valor de {yes_real-yes_implicit:.1f}%)")
                                    
                                    # Não
                                    no_real = original_probabilities["btts"].get("no", 0)
                                    no_implicit = implied_probabilities.get("btts_no", 0)
                                    no_value = no_real > no_implicit + 2
                                    
                                    probs_section += f"- **Não**: Real {no_real:.1f}% vs Implícita {no_implicit:.1f}%{' (Valor)' if no_value else ''}\n"
                                    
                                    if no_value:
                                        opportunities.append(f"- **Ambos Marcam - Não**: Real {no_real:.1f}% vs Implícita {no_implicit:.1f}% (Valor de {no_real-no_implicit:.1f}%)")
                                
                                new_analysis.append(probs_section)
                                
                                # Oportunidades identificadas
                                if opportunities:
                                    new_analysis.append("# Oportunidades Identificadas:\n" + "\n".join(opportunities))
                                else:
                                    new_analysis.append("# Oportunidades Identificadas:\nInfelizmente não detectamos valor em nenhuma dos seus inputs.")
                                
                                # Nível de confiança
                                confidence_section = "# Nível de Confiança Geral: Médio\n"

                                # Extrair dados da forma e consistência
                                if "analysis_data" in original_probabilities:
                                    analysis_data = original_probabilities["analysis_data"]
                                    home_consistency = analysis_data.get("home_consistency", 0) * 100
                                    away_consistency = analysis_data.get("away_consistency", 0) * 100
                                    
                                    # Verificar se temos dados de forma bruta
                                    home_form_raw = stats_data["home_team"].get("formRun_overall", "")
                                    away_form_raw = stats_data["away_team"].get("formRun_overall", "")
                                    
                                    # Calcular a forma diretamente a partir dos dados brutos se disponíveis
                                    home_form_points = 0
                                    away_form_points = 0
                                    
                                    # Função simplificada para calcular pontos da forma
                                    def calculate_form_points(form_str):
                                        if not form_str or not isinstance(form_str, str):
                                            return 0
                                        
                                        points = 0
                                        # Pegar apenas os últimos 5 caracteres
                                        recent_form = form_str[-5:] if len(form_str) >= 5 else form_str
                                        
                                        for result in recent_form:
                                            result = result.upper()
                                            if result == 'W':
                                                points += 3
                                            elif result == 'D':
                                                points += 1
                                            # L ou outros caracteres = 0 pontos
                                        
                                        return points
                                    
                                    # Calcular pontos para cada time
                                    if home_form_raw:
                                        home_form_points = calculate_form_points(home_form_raw)
                                    else:
                                        # Tentar calcular a partir do analysis_data se disponível
                                        home_form_points = int(analysis_data.get("home_form_points", 0) * 15)
                                    
                                    if away_form_raw:
                                        away_form_points = calculate_form_points(away_form_raw)
                                    else:
                                        # Tentar calcular a partir do analysis_data se disponível
                                        away_form_points = int(analysis_data.get("away_form_points", 0) * 15)
                                    
                                    confidence_section += f"- **Consistência**: {home_team}: {home_consistency:.1f}%, {away_team}: {away_consistency:.1f}%. Consistência é uma medida que indica quão previsível é o desempenho da equipe.\n"
                                    confidence_section += f"- **Forma Recente**: {home_team}: {home_form_points}/15, {away_team}: {away_form_points}/15. Forma representa a pontuação dos últimos 5 jogos (vitória=3pts, empate=1pt, derrota=0pts).\n"
                                    confidence_section += "- Valores mais altos em ambas métricas aumentam a confiança na previsão."
                                else:
                                    confidence_section += "- **Consistência**: Consistência é uma medida que indica quão previsível é o desempenho da equipe.\n"
                                    confidence_section += "- **Forma Recente**: Forma representa a pontuação dos últimos 5 jogos (vitória=3pts, empate=1pt, derrota=0pts).\n"
                                    confidence_section += "- Valores mais altos em ambas métricas aumentam a confiança na previsão."
                                
                                new_analysis.append(confidence_section)
                                
                                return "\n\n".join(new_analysis)
                            
                            # Usar a análise de texto da API como base, mas reconstruir completamente as seções críticas
                            formatted_analysis = reconstruct_analysis(
                                analysis,
                                home_team,
                                away_team,
                                selected_markets,
                                original_probabilities,
                                implied_probabilities,
                                odds_data
                            )
                            
                            # Exibir o resultado formatado
                            st.code(formatted_analysis, language=None)
                            
                            # Registrar uso após análise bem-sucedida
                            num_markets = sum(1 for v in selected_markets.values() if v)
                            
                            # Registro de uso com dados detalhados
                            analysis_data = {
                                "league": selected_league,
                                "home_team": home_team,
                                "away_team": away_team,
                                "markets_used": [k for k, v in selected_markets.items() if v]
                            }
                            success = st.session_state.user_manager.record_usage(
                                st.session_state.email, 
                                num_markets,
                                analysis_data
                            )
                            
                            if success:
                                # Forçar atualização do cache de estatísticas
                                if hasattr(st.session_state, 'user_stats_cache'):
                                    del st.session_state.user_stats_cache  # Remover cache para forçar reload
                                
                                # Mostrar mensagem de sucesso com créditos restantes
                                updated_stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
                                credits_after = updated_stats['credits_remaining']
                                st.success(f"{num_markets} créditos foram consumidos. Agora você tem {credits_after} créditos.")
                            else:
                                st.error("Não foi possível registrar o uso dos créditos. Por favor, tente novamente.")
                                    
                    except Exception as analysis_error:
                        logger.error(f"Erro durante a análise: {str(analysis_error)}")
                        logger.error(traceback.format_exc())
                        status.error(f"Erro durante a análise: {str(analysis_error)}")
                        if st.session_state.debug_mode:
                            st.code(traceback.format_exc())
            except Exception as button_error:
                logger.error(f"Erro no botão de análise: {str(button_error)}")
                logger.error(traceback.format_exc())
                st.error(f"Erro no botão de análise: {str(button_error)}")
                if st.session_state.debug_mode:
                    st.code(traceback.format_exc())
                    
        except Exception as content_error:
            logger.error(f"Erro fatal no conteúdo principal: {str(content_error)}")
            logger.error(traceback.format_exc())
            st.error("Erro ao carregar o conteúdo principal. Detalhes no log.")
            st.error(f"Detalhes: {str(content_error)}")
            if st.session_state.debug_mode:
                st.code(traceback.format_exc())
            
    except Exception as e:
        logger.error(f"Erro crítico ao exibir painel principal: {str(e)}")
        logger.error(traceback.format_exc())
        st.error("Erro ao carregar o painel principal. Por favor, tente novamente.")
        st.error(f"Erro: {str(e)}")
        if st.session_state.debug_mode:
            st.code(traceback.format_exc())

# Função auxiliar para extração de dados avançada
def extract_direct_team_stats(source, target, team_type):
    """
    Extrai estatísticas de equipe diretamente da fonte para o destino
    com mapeamento de nomes de campos.
    
    Args:
        source (dict): Dados de origem
        target (dict): Dicionário de destino para armazenar os dados
        team_type (str): Tipo de equipe ('home' ou 'away')
    """
    if not isinstance(source, dict) or not isinstance(target, dict):
        return
    
    # Campos essenciais para extração
    essential_fields = [
        "played", "wins", "draws", "losses", 
        "goals_scored", "goals_conceded", 
        "clean_sheets", "failed_to_score",
        "avg_goals_scored", "avg_goals_conceded",
        "btts", "over_1_5", "over_2_5", "over_3_5"
    ]
    
    # Procurar e copiar campos essenciais
    for field in essential_fields:
        if field in source and source[field] not in [0, "0", "", "?????"]:
            target[field] = source[field]
    
    # Extrair outros campos não-zero
    for key, value in source.items():
        if key not in target and value not in [0, "0", "", "?????"]:
            if isinstance(value, (int, float, str)):
                target[key] = value

# Função auxiliar para transformação de dados da API
def transform_api_data(stats_data, home_team, away_team, selected_markets):
    """
    Transforma os dados da API para um formato compatível com a análise
    
    Args:
        stats_data (dict): Dados brutos da API
        home_team (str): Nome do time da casa
        away_team (str): Nome do time visitante
        selected_markets (dict): Mercados selecionados
        
    Returns:
        dict: Dados transformados
    """
    try:
        # Inicializar estrutura de resultado
        result = {
            "match_info": {
                "home_team": home_team,
                "away_team": away_team
            },
            "home_team": {},
            "away_team": {},
            "h2h": {}
        }
        
        # Extrair dados de H2H se disponíveis
        if "h2h" in stats_data and isinstance(stats_data["h2h"], dict):
            result["h2h"] = stats_data["h2h"].copy()
        
        # Extrair dados do time da casa
        if "home_team" in stats_data and isinstance(stats_data["home_team"], dict):
            result["home_team"] = stats_data["home_team"].copy()
            # Extrair campos específicos se disponíveis
            extract_direct_team_stats(stats_data["home_team"], result["home_team"], "home")
        
        # Extrair dados do time visitante
        if "away_team" in stats_data and isinstance(stats_data["away_team"], dict):
            result["away_team"] = stats_data["away_team"].copy()
            # Extrair campos específicos se disponíveis
            extract_direct_team_stats(stats_data["away_team"], result["away_team"], "away")
            
        # Procurar mais profundamente na estrutura
        if isinstance(stats_data, dict):
            for key, value in stats_data.items():
                if isinstance(value, dict):
                    # Procurar dados de equipe em estruturas aninhadas
                    if "home_team" in value and isinstance(value["home_team"], dict):
                        extract_direct_team_stats(value["home_team"], result["home_team"], "home")
                    
                    if "away_team" in value and isinstance(value["away_team"], dict):
                        extract_direct_team_stats(value["away_team"], result["away_team"], "away")
                    
                    if "h2h" in value and isinstance(value["h2h"], dict):
                        for h2h_key, h2h_value in value["h2h"].items():
                            if h2h_key not in result["h2h"] and h2h_value not in [0, "0", "", "?????"]:
                                result["h2h"][h2h_key] = h2h_value

        # Garantir dados mínimos
        if len(result["home_team"]) < 5:
            result["home_team"].update({
                "name": home_team,
                "played": 10,
                "wins": 5,
                "draws": 3,
                "losses": 2,
                "goals_scored": 15,
                "goals_conceded": 10
            })
        
        if len(result["away_team"]) < 5:
            result["away_team"].update({
                "name": away_team,
                "played": 10,
                "wins": 4,
                "draws": 2,
                "losses": 4,
                "goals_scored": 12,
                "goals_conceded": 14
            })
        
        if len(result["h2h"]) < 3:
            result["h2h"].update({
                "matches": 3,
                "home_wins": 1,
                "away_wins": 1,
                "draws": 1,
                "home_goals": 3,
                "away_goals": 3
            })
            
        # Log de diagnóstico
        home_count = sum(1 for k, v in result["home_team"].items() 
                      if (isinstance(v, (int, float)) and v != 0) or 
                         (isinstance(v, str) and v not in ["", "?????"]))
        
        away_count = sum(1 for k, v in result["away_team"].items() 
                      if (isinstance(v, (int, float)) and v != 0) or 
                         (isinstance(v, str) and v not in ["", "?????"]))
        
        h2h_count = sum(1 for k, v in result["h2h"].items() 
                      if isinstance(v, (int, float)) and v != 0)
        
        logger.info(f"Extração total: home={home_count}, away={away_count}, h2h={h2h_count}")
        
        return result
        
    except Exception as e:
        logger.error(f"Erro na transformação de dados da API: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Garantir que retornamos pelo menos dados mínimos
        result = {
            "match_info": {
                "home_team": home_team,
                "away_team": away_team
            },
            "home_team": {
                "name": home_team,
                "played": 10,
                "wins": 5,
                "draws": 3,
                "losses": 2,
                "goals_scored": 15,
                "goals_conceded": 10
            },
            "away_team": {
                "name": away_team,
                "played": 10,
                "wins": 4,
                "draws": 2,
                "losses": 4,
                "goals_scored": 12,
                "goals_conceded": 14
            },
            "h2h": {
                "matches": 3,
                "home_wins": 1,
                "away_wins": 1,
                "draws": 1,
                "home_goals": 3,
                "away_goals": 3
            }
        }
        
        return result
