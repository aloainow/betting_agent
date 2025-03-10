# pages/dashboard.py - Solução com integrações de API-Football
import streamlit as st
import logging
import traceback  # Importado globalmente para evitar o erro
import json
import os
import time
from utils.core import show_valuehunter_logo, go_to_login, update_purchase_button, DATA_DIR
from utils.data import parse_team_stats, get_odds_data, format_prompt
from utils.ai import analyze_with_gpt

# Configuração de logging
logger = logging.getLogger("valueHunter.dashboard")

# Diretório para cache de times
TEAMS_CACHE_DIR = os.path.join(DATA_DIR, "teams_cache")
os.makedirs(TEAMS_CACHE_DIR, exist_ok=True)

# Funções auxiliares para seleção de ligas (ADICIONADAS NO INÍCIO)
def get_league_selection():
    """
    Função separada para obter a lista de ligas e mostrar o seletor.
    Evita problemas de indentação e de sintaxe.
    
    Returns:
        str: A liga selecionada ou None se houver erro
    """
    try:
        # Importar a função para ligas pré-definidas
        from utils.footystats_api import get_user_selected_leagues_direct
        
        # Obter ligas pré-definidas
        available_leagues = get_user_selected_leagues_direct()
        
        if not available_leagues:
            st.error("Nenhuma liga disponível na lista pré-definida.")
            return None
        
        # Inicializar seleção se necessário
        if 'selected_league' not in st.session_state or st.session_state.selected_league not in available_leagues:
            st.session_state.selected_league = available_leagues[0]
        
        # Seletor de liga
        selected_league = st.sidebar.selectbox(
            "Escolha o campeonato:",
            options=available_leagues,
            index=available_leagues.index(st.session_state.selected_league) if st.session_state.selected_league in available_leagues else 0,
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
        
        return selected_league
    
    except Exception as e:
        logger.error(f"Erro ao selecionar liga: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        st.error(f"Erro ao carregar ligas: {str(e)}")
        return None

def load_league_teams_direct(selected_league):
    """
    Função otimizada para carregar times da liga usando os season IDs exatos.
    
    Args:
        selected_league (str): Nome da liga selecionada
        
    Returns:
        list: Lista de nomes dos times ou lista vazia se falhar
    """
    import traceback
    import streamlit as st
    from utils.direct_api import get_teams_direct
    
    status = st.empty()
    status.info(f"Carregando times para {selected_league}...")
    
    try:
        # Buscar times usando a função especializada com IDs exatos
        teams = get_teams_direct(selected_league, force_refresh=False)
        
        if teams and len(teams) > 0:
            # Sucesso!
            status.success(f"✅ {len(teams)} times carregados para {selected_league}")
            return sorted(teams)  # Ordenar times alfabeticamente
        else:
            # API não retornou times
            status.warning(f"Nenhum time encontrado para {selected_league}")
            
            # Mostrar diagnóstico
            with st.expander("Diagnóstico da API FootyStats", expanded=True):
                st.error(f"Não foi possível carregar times para {selected_league}.")
                st.info("Tente limpar o cache e atualizar a página.")
                
                # Botão para limpar cache e forçar atualização
                if st.button("Limpar Cache e Tentar Novamente", key="clear_cache_btn"):
                    try:
                        # Forçar atualização ignorando o cache
                        teams = get_teams_direct(selected_league, force_refresh=True)
                        if teams and len(teams) > 0:
                            st.success(f"✅ {len(teams)} times encontrados após forçar atualização!")
                            status.success(f"✅ {len(teams)} times carregados para {selected_league}")
                            return sorted(teams)  # Ordenar times alfabeticamente
                        else:
                            st.error("Não foi possível encontrar times mesmo após forçar atualização.")
                            
                            # Mostrar informações de ajuda
                            from utils.league_ids import get_season_id
                            season_id = get_season_id(selected_league)
                            if season_id:
                                st.info(f"Liga: {selected_league}")
                                st.info(f"Season ID: {season_id}")
                                
                                # Mostrar URL para ajudar no diagnóstico
                                api_url = f"https://api.football-data-api.com/league-teams?key=***&season_id={season_id}&include=stats"
                                st.code(f"URL da API: {api_url}")
                    except Exception as e:
                        st.error(f"Erro ao forçar atualização: {str(e)}")
    except Exception as e:
        status.error(f"Erro ao carregar times: {str(e)}")
        logger.error(f"Erro ao carregar times: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Mostrar diagnóstico detalhado em caso de erro
        with st.expander("Detalhes do Erro", expanded=True):
            st.error(f"Erro ao acessar a API FootyStats: {str(e)}")
            st.code(traceback.format_exc())
    
    # Retornar lista vazia se falhou
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
    Diagnóstico detalhado de problemas na API para uma liga específica.
    Sem qualquer uso de exemplos ou fallbacks.
    
    Args:
        selected_league (str): Nome da liga
        
    Returns:
        str: Mensagem de diagnóstico formatada em Markdown
    """
    try:
        from utils.footystats_api import find_league_id_by_name, test_api_connection, clear_league_cache
        
        # Teste de conexão com a API
        api_test = test_api_connection()
        
        # Verificar se a liga existe na lista de ligas disponíveis
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

def fetch_stats_data(selected_league, home_team=None, away_team=None):
    """
    Buscar estatísticas das equipes pela API FootyStats
    
    Args:
        selected_league (str): Nome da liga
        home_team (str, optional): Nome do time da casa
        away_team (str, optional): Nome do time visitante
        
    Returns:
        tuple: (DataFrame com estatísticas, dados brutos) ou (None, None) em caso de erro
    """
    try:
        with st.spinner("Buscando estatísticas atualizadas..."):
            # Verificar se temos times específicos para buscar
            if home_team and away_team:
                # Obter estatísticas da API FootyStats
                try:
                    from utils.footystats_api import get_fixture_statistics, convert_api_stats_to_df_format
                    
                    # Mostrar qual temporada estamos usando
                    from utils.footystats_api import LEAGUE_SEASONS, CURRENT_SEASON
                    season = LEAGUE_SEASONS.get(selected_league, CURRENT_SEASON)
                    st.info(f"Buscando estatísticas da temporada {season} para {selected_league}")
                    
                    # Obter estatísticas da API
                    fixture_stats = get_fixture_statistics(home_team, away_team, selected_league)
                    
                    if fixture_stats:
                        # Converter para o formato de DataFrame esperado
                        team_stats_df = convert_api_stats_to_df_format(fixture_stats)
                        
                        if team_stats_df is not None:
                            st.success(f"Estatísticas carregadas com sucesso para {home_team} vs {away_team}")
                            return team_stats_df, fixture_stats
                        else:
                            st.error("Erro ao processar estatísticas")
                            return None, None
                    else:
                        st.error("Estatísticas não disponíveis para estes times")
                        st.info("Isso pode ocorrer se os times não fizerem parte da mesma liga ou temporada.")
                        return None, None
                
                except Exception as api_error:
                    st.error(f"Erro ao obter estatísticas da API: {str(api_error)}")
                    logger.error(f"Erro na API de estatísticas: {str(api_error)}")
                    return None, None
            else:
                st.error("É necessário selecionar dois times para análise.")
                return None, None
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {str(e)}")
        st.error(f"Erro ao buscar estatísticas: {str(e)}")
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
        # Garantir que a barra lateral esteja visível
        st.markdown("""
        <style>
        /* FORÇA a barra lateral a ficar visível */
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
            transform: none !important;
        }
        
        /* Ocultar apenas os elementos de navegação do Streamlit, não a barra toda */
        header[data-testid="stHeader"],
        footer,
        #MainMenu {
            display: none !important;
        }
        
        /* Apenas ocultar o CONTAINER de navegação, não a barra lateral inteira */
        section[data-testid="stSidebarNavContainer"] {
            display: none !important;
        }
        
        /* Corrigir - NÃO ocultar o primeiro div do sidebar, apenas elementos específicos */
        [data-testid="stSidebar"] > div:first-child > div:nth-child(2),  /* Este é o container de navegação */
        button.stSidebarButton,
        div.stSidebarNavItems {
            display: none !important;
        }
        
        /* Seletores mais específicos para navegação */
        ul.st-emotion-cache-pbk8do,
        div.st-emotion-cache-16idsys {
            display: none !important;
        }
        
        /* Remover espaço extra no topo que normalmente é ocupado pelo menu */
        .main .block-container {
            padding-top: 1rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Iniciar com log de diagnóstico
        logger.info("Iniciando renderização do dashboard principal")     
        
        # ------------------------------------------------------------
        # BARRA LATERAL REORGANIZADA
        # ------------------------------------------------------------
        
        # 1. Mostrar estatísticas de uso e saudação
        show_usage_stats()
        
        # Adicionar botão de diagnóstico da API
        if st.sidebar.button("🔬 Diagnóstico API", type="primary", use_container_width=True):
            with st.spinner("Realizando diagnóstico completo..."):
                try:
                    # Capturar a saída da função
                    import io
                    import sys
                    from contextlib import redirect_stdout
                    
                    # Importar a função de diagnóstico
                    from utils.footystats_api import diagnose_api_in_detail
                    
                    # Capturar stdout para o diagnóstico
                    f = io.StringIO()
                    with redirect_stdout(f):
                        successful_combos = diagnose_api_in_detail()
                    
                    # Recuperar a saída
                    output = f.getvalue()
                    
                    # Mostrar resultado em um expansor
                    with st.expander("Resultado do Diagnóstico", expanded=True):
                        st.code(output, language="text")
                        
                        # Se encontrou configurações que funcionam
                        if successful_combos:
                            st.success("✅ Encontrado pelo menos uma configuração que funciona!")
                            
                            # Contar sucessos por combinação
                            param_counts = {}
                            for combo in successful_combos:
                                params = combo["params"]
                                if params not in param_counts:
                                    param_counts[params] = 0
                                param_counts[params] += 1
                            
                            # Encontrar a melhor combinação
                            best_params = max(param_counts.items(), key=lambda x: x[1])
                            st.info(f"Recomendação: Use os parâmetros **{best_params[0]}**")
                            
                            # Adicionar botão para aplicar configuração
                            if st.button("Aplicar Configuração Recomendada & Limpar Cache"):
                                # Limpar cache
                                from utils.footystats_api import clear_all_cache
                                num_cleared = clear_all_cache()
                                st.success(f"Cache limpo: {num_cleared} arquivos")
                                st.info("Recarregando página em 3 segundos...")
                                import time
                                time.sleep(3)
                                st.experimental_rerun()
                        else:
                            st.error("❌ Nenhuma configuração funcionou!")
                            st.info("Verifique sua conta FootyStats e API key.")
                        
                        # Adicionar botão para visualizar API key
                        if st.checkbox("Mostrar API key"):
                            from utils.footystats_api import API_KEY
                            st.code(f"API Key atual: {API_KEY}")
                            st.warning("Mantenha sua API key segura e não a compartilhe!")
                    
                except Exception as e:
                    st.error(f"Erro ao executar diagnóstico: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # 2. Escolha da liga (usando função auxiliar)
        selected_league = get_league_selection()
        if not selected_league:
            st.error("Não foi possível selecionar uma liga. Por favor, verifique a configuração.")
            return
        
        # Botão de atualização
        show_league_update_button(selected_league)
        
        # Botão para listar ligas disponíveis
        if st.sidebar.button("📋 Listar Ligas Disponíveis", use_container_width=True):
            st.sidebar.info("Buscando ligas disponíveis na sua conta...")
            
            try:
                # Fazer requisição direta à API
                import requests
                from utils.footystats_api import API_KEY, BASE_URL
                
                response = requests.get(f"{BASE_URL}/league-list", params={"key": API_KEY}, timeout=15)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        if "data" in data and isinstance(data["data"], list):
                            leagues = data["data"]
                            
                            st.sidebar.success(f"✅ Encontradas {len(leagues)} ligas na sua conta!")
                            
                            # Mostrar as primeiras 10 ligas
                            with st.sidebar.expander("Ligas disponíveis (10 primeiras)"):
                                for i, league in enumerate(leagues[:10]):
                                    name = league.get("name", "Desconhecido")
                                    country = league.get("country", "Desconhecido")
                                    league_id = league.get("id", "Desconhecido")
                                    st.write(f"{i+1}. **{name}** ({country}) - ID: {league_id}")
                            
                            # Verificar se ligas específicas estão selecionadas
                            popular_leagues = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]
                            selected_popular = []
                            
                            for league in leagues:
                                name = league.get("name", "")
                                if any(popular in name for popular in popular_leagues):
                                    selected_popular.append(f"{name} ({league.get('country', '')})")
                            
                            if selected_popular:
                                st.sidebar.success(f"Ligas populares encontradas: {', '.join(selected_popular)}")
                            else:
                                st.sidebar.warning("Nenhuma liga popular encontrada em sua conta")
                                st.sidebar.info("Selecione ligas em seu dashboard FootyStats")
                        else:
                            st.sidebar.error("Formato de resposta inesperado")
                            st.sidebar.code(str(data)[:500])
                    except ValueError:
                        st.sidebar.error("Resposta não é um JSON válido")
                        st.sidebar.code(response.text[:500])
                else:
                    st.sidebar.error(f"Erro HTTP {response.status_code}")
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            st.sidebar.error(f"Mensagem: {error_data['message']}")
                    except:
                        st.sidebar.code(response.text[:500])
            except Exception as e:
                st.sidebar.error(f"Erro ao listar ligas: {str(e)}")
        
        # Botão para limpar todo o cache
        if st.sidebar.button("🧹 Limpar Todo o Cache", use_container_width=True):
            try:
                from utils.footystats_api import clear_all_cache
                num_cleared = clear_all_cache()
                st.sidebar.success(f"Cache limpo: {num_cleared} arquivos removidos")
                st.sidebar.info("Recarregando página...")
                time.sleep(2)
                st.experimental_rerun()
            except Exception as e:
                st.sidebar.error(f"Erro ao limpar cache: {str(e)}")
        
        # Resto do código para a barra lateral
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
            
            # Carregar times diretamente (ignorando o cache)
            with st.spinner(f"Carregando times para {selected_league}..."):
                teams = load_league_teams_direct(selected_league)
            
            # Verificação adicional para garantir que temos times
            if not teams or len(teams) == 0:
                st.warning("Não foi possível carregar os times para este campeonato.")
                st.info("Por favor, use o botão 'Atualizar Times' na barra lateral e tente novamente.")
                
                # Botão de atualização de emergência
                if st.button("🆘 Tentar Novamente", type="primary"):
                    # Forçar nova tentativa
                    st.experimental_rerun()
                    
                return
            
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
                            "over_under": st.checkbox("Over/Under", key='ou'),
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
                st.error(f"Erro ao exibir mercados disponíveis: {str(markets_error)}")
                traceback.print_exc()
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
                st.error(f"Erro ao configurar odds: {str(odds_error)}")
                traceback.print_exc()
                return
            
            # Botão de análise centralizado
            try:
                # Botão em largura total para melhor design
                analyze_button = st.button("Analisar Partida", type="primary", use_container_width=True)
                
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
                    
                    # Buscar estatísticas sempre em tempo real (sem cache)
                    status.info("Buscando estatísticas atualizadas...")
                    team_stats_df, stats_data = fetch_stats_data(selected_league, home_team, away_team)
                    
                    if team_stats_df is None:
                        status.error("Falha ao carregar estatísticas. Tente novamente.")
                        return
                        
                    # Executar análise com tratamento de erro para cada etapa
                    try:
                        # Etapa 1: Verificar dados
                        status.info("Preparando dados para análise...")
                        if team_stats_df is None:
                            status.error("Falha ao carregar dados")
                            return
                            
                        # Etapa 2: Formatar prompt
                        status.info("Preparando análise...")
                        prompt = format_prompt(team_stats_df, home_team, away_team, odds_data, selected_markets)
                        if not prompt:
                            status.error("Falha ao preparar análise")
                            return
                            
                        # Etapa 3: Análise GPT
                        status.info("Realizando análise com IA...")
                        analysis = analyze_with_gpt(prompt)
                        if not analysis:
                            status.error("Falha na análise com IA")
                            return
                        
                       # Etapa 4: Mostrar resultado
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
                            
                            # Exibir a análise em uma div com largura total
                            st.markdown(f'''
                            <style>
                            .analysis-result {{
                                width: 100% !important;
                                max-width: 100% !important;
                                padding: 2rem !important;
                                background-color: #575760;
                                border-radius: 8px;
                                border: 1px solid #6b6b74;
                                margin: 1rem 0;
                            }}
                            
                            /* Estilos para deixar o cabeçalho mais bonito */
                            .analysis-result h1, 
                            .analysis-result h2,
                            .analysis-result h3 {{
                                color: #fd7014;
                                margin-top: 1.5rem;
                                margin-bottom: 1rem;
                            }}
                            
                            /* Estilos para parágrafos */
                            .analysis-result p {{
                                margin-bottom: 1rem;
                                line-height: 1.5;
                            }}
                            
                            /* Estilos para listas */
                            .analysis-result ul, 
                            .analysis-result ol {{
                                margin-left: 1.5rem;
                                margin-bottom: 1rem;
                            }}
                            
                            /* Oportunidades destacadas */
                            .analysis-result strong {{
                                color: #fd7014;
                            }}
                            </style>
                            <div class="analysis-result">{analysis}</div>
                            ''', unsafe_allow_html=True)
                            
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
                        status.error(f"Erro durante a análise: {str(analysis_error)}")
                        traceback.print_exc()
                        
            except Exception as button_error:
                logger.error(f"Erro no botão de análise: {str(button_error)}")
                st.error(f"Erro no botão de análise: {str(button_error)}")
                traceback.print_exc()
                    
        except Exception as content_error:
            logger.error(f"Erro fatal no conteúdo principal: {str(content_error)}")
            st.error("Erro ao carregar o conteúdo principal. Detalhes no log.")
            st.error(f"Detalhes: {str(content_error)}")
            traceback.print_exc()
            
    except Exception as e:
        logger.error(f"Erro crítico ao exibir painel principal: {str(e)}")
        st.error("Erro ao carregar o painel principal. Por favor, tente novamente.")
        st.error(f"Erro: {str(e)}")
        traceback.print_exc()
