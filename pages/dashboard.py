# pages/dashboard.py - Dashboard Principal (solução com JavaScript)
import streamlit as st
import logging
import traceback
from utils.core import show_valuehunter_logo, go_to_login, update_purchase_button
from utils.data import fetch_fbref_data, parse_team_stats, get_odds_data
from utils.ai import analyze_with_gpt, format_prompt

# Configuração de logging
logger = logging.getLogger("valueHunter.dashboard")

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

def load_league_teams(selected_league):
    """Função para carregar os times da liga selecionada"""
    try:
        # Importar URLs do FBref
        from utils.data import FBREF_URLS
        
        # Exibir mensagem de carregamento
        with st.spinner(f"Carregando dados do campeonato {selected_league}..."):
            # Verificar se a liga existe
            if selected_league not in FBREF_URLS:
                st.error(f"Liga não encontrada: {selected_league}")
                logger.error(f"Liga {selected_league} não encontrada em FBREF_URLS")
                return None, None, None
                
            # Obter URL das estatísticas
            stats_url = FBREF_URLS[selected_league].get("stats")
            if not stats_url:
                st.error(f"URL de estatísticas não encontrada para {selected_league}")
                logger.error(f"URL de estatísticas ausente para {selected_league}")
                return None, None, None
                
            # Buscar dados - com tratamento de erro explícito
            stats_html = fetch_fbref_data(stats_url)
            if not stats_html:
                st.error(f"Não foi possível carregar os dados do campeonato {selected_league}")
                logger.error(f"fetch_fbref_data retornou None para {stats_url}")
                return None, None, None
            
            # Parsear estatísticas dos times
            team_stats_df = parse_team_stats(stats_html)
            if team_stats_df is None:
                st.error("Erro ao processar dados de estatísticas dos times")
                logger.error("parse_team_stats retornou None")
                return None, None, None
                
            if 'Squad' not in team_stats_df.columns:
                st.error("Dados incompletos: coluna 'Squad' não encontrada")
                logger.error(f"Colunas disponíveis: {team_stats_df.columns.tolist()}")
                return None, None, None
            
            # Extrair lista de times
            teams = team_stats_df['Squad'].dropna().unique().tolist()
            if not teams:
                st.error("Não foi possível encontrar os times do campeonato")
                logger.error("Lista de times vazia após dropna() e unique()")
                return None, None, None
                
            logger.info(f"Dados carregados: {len(teams)} times encontrados")
            return teams, team_stats_df, stats_html
            
    except Exception as e:
        logger.error(f"Erro ao carregar times da liga: {str(e)}")
        st.error(f"Erro ao carregar times: {str(e)}")
        return None, None, None

def show_main_dashboard():
    """Show the main dashboard with improved error handling and debug info"""
    try:
        # Garantir que a barra lateral esteja visível na página principal (dashboard)
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
        
        # 2. Escolha da liga (movida para cima)
        try:
            # Importar URLs do FBref
            from utils.data import FBREF_URLS
            
            # Lista de ligas disponíveis com fallback seguro
            available_leagues = list(FBREF_URLS.keys())
            if not available_leagues:
                st.sidebar.error("Erro: Nenhuma liga disponível.")
                logger.error("FBREF_URLS está vazia")
                return
            
            # Inicializar liga selecionada se não existir
            if 'selected_league' not in st.session_state and available_leagues:
                st.session_state.selected_league = available_leagues[0]
            
            # Container para status
            status_container = st.sidebar.empty()
            
            # Verificar se temos o parâmetro de liga na URL
            current_league = st.query_params.get('league', '')
            
            # Se temos liga na URL e é diferente da selecionada atualmente
            if current_league and current_league in available_leagues and current_league != st.session_state.get('selected_league', ''):
                logger.info(f"Detectada liga na URL: {current_league}, atualizando seleção")
                st.session_state.selected_league = current_league
                
                # Carregar times para a nova liga
                teams, team_stats_df, stats_html = load_league_teams(current_league)
                if teams and team_stats_df is not None and stats_html is not None:
                    # Salvar dados em session_state
                    st.session_state.stats_html = stats_html
                    st.session_state.team_stats_df = team_stats_df
                    st.session_state.league_teams = teams
                    
                    status_container.success(f"Dados de {current_league} carregados com sucesso!")
            
            # SOLUÇÃO JAVASCRIPT: Usar JavaScript para detectar mudanças e recarregar a página
            # Script to reload the page when league changes
            js_reload = """
            <script>
            // Função para detectar a mudança e recarregar a página
            const selectBox = document.querySelector('div[data-testid="stSelectbox"]:has(label:contains("Escolha o campeonato"))');
            if (selectBox) {
                // Observe todas as mudanças no DOM do selectbox
                const observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        // Verificar se a mudança é uma seleção de valor
                        if (mutation.type === 'attributes' || 
                            (mutation.type === 'childList' && mutation.target.classList.contains('st-emotion-cache-1gulkj5'))) {
                            
                            // Pegar valor selecionado
                            const selectedText = selectBox.querySelector('.st-emotion-cache-1gulkj5')?.textContent;
                            
                            if (selectedText && selectedText.trim() !== '') {
                                // Adicionar à URL e recarregar
                                const encodedLeague = encodeURIComponent(selectedText.trim());
                                const currentUrl = new URL(window.location.href);
                                
                                // Se a liga mudou, atualizar URL e recarregar
                                if (currentUrl.searchParams.get('league') !== encodedLeague) {
                                    currentUrl.searchParams.set('league', encodedLeague);
                                    window.location.href = currentUrl.toString();
                                }
                            }
                        }
                    });
                });
                
                // Observar o selectbox para quaisquer mudanças
                observer.observe(selectBox, { 
                    attributes: true, 
                    childList: true, 
                    subtree: true 
                });
                
                console.log("Observer de selectbox configurado com sucesso");
            } else {
                console.log("Selectbox não encontrado na página");
            }
            </script>
            """
            st.components.v1.html(js_reload, height=0)
            
            # Selectbox normal para a liga
            selected_league = st.sidebar.selectbox(
                "Escolha o campeonato:",
                available_leagues,
                index=available_leagues.index(st.session_state.selected_league) if st.session_state.selected_league in available_leagues else 0
            )
            
            # Atualize o estado sempre que a seleção mudar
            if selected_league != st.session_state.get('selected_league', ''):
                logger.info(f"Liga alterada: {st.session_state.get('selected_league', '')} -> {selected_league}")
                st.session_state.selected_league = selected_league
                
                # Atualizar a URL
                st.query_params['league'] = selected_league
                
                # Tentar carregar times (embora o JavaScript deva recarregar a página)
                status_container.info(f"Alterando para {selected_league}...")
                
                # Carregar times
                teams, team_stats_df, stats_html = load_league_teams(selected_league)
                if teams and team_stats_df is not None and stats_html is not None:
                    # Salvar dados em session_state
                    st.session_state.stats_html = stats_html
                    st.session_state.team_stats_df = team_stats_df
                    st.session_state.league_teams = teams
                    
                    status_container.success(f"Dados de {selected_league} carregados com sucesso!")
            
            # Botão para carregamento manual (backup)
            load_teams = st.sidebar.button("Recarregar Times desta Liga", 
                                    use_container_width=True,
                                    type="primary")
            
            # Inicializar times, team_stats_df e stats_html
            teams = []
            team_stats_df = None
            stats_html = None
            
            # Se o botão foi clicado, buscar os times
            if load_teams:
                with st.spinner(f"Carregando dados do campeonato {selected_league}..."):
                    teams, team_stats_df, stats_html = load_league_teams(selected_league)
                    if teams and team_stats_df is not None and stats_html is not None:
                        # Salvar dados em session_state
                        st.session_state.stats_html = stats_html
                        st.session_state.team_stats_df = team_stats_df
                        st.session_state.league_teams = teams
                        st.session_state.selected_league = selected_league
                        
                        # Mostrar mensagem de sucesso
                        status_container.success(f"Dados de {selected_league} carregados com sucesso!")
                        logger.info(f"Dados carregados: {len(teams)} times encontrados")
                    else:
                        status_container.error(f"Erro ao carregar times de {selected_league}")
            
            # Verificar se temos times na sessão
            elif 'league_teams' in st.session_state:
                teams = st.session_state.league_teams
                team_stats_df = st.session_state.get('team_stats_df')
                stats_html = st.session_state.get('stats_html')
                if teams and len(teams) > 0:
                    status_container.info(f"Usando dados em cache para {selected_league}. {len(teams)} times disponíveis.")
                else:
                    # Se temos dados na sessão mas times vazios, tentar carregar novamente
                    logger.warning(f"Dados em cache para {selected_league} parecem inválidos. Tentando recarregar automaticamente...")
                    teams, team_stats_df, stats_html = load_league_teams(selected_league)
                    if teams and team_stats_df is not None and stats_html is not None:
                        # Salvar dados em session_state
                        st.session_state.stats_html = stats_html
                        st.session_state.team_stats_df = team_stats_df
                        st.session_state.league_teams = teams
                        status_container.success(f"Dados de {selected_league} recarregados automaticamente.")
                    else:
                        status_container.warning(f"Não foi possível carregar dados para {selected_league}. Use o botão para recarregar.")

        except Exception as sidebar_error:
            logger.error(f"Erro na seleção de liga: {str(sidebar_error)}")
            st.sidebar.error("Erro ao carregar ligas disponíveis.")
            traceback.print_exc()
            return
        
        # Separador
        st.sidebar.markdown("---")
        
        # 3. Botão de pacotes (agora em segundo lugar)
        if st.sidebar.button("🚀 Ver Pacotes de Créditos", key="sidebar_packages_button", use_container_width=True):
            st.session_state.page = "packages"
            st.experimental_rerun()
        
        # 4. Botão de logout (movido para o final)
        if st.sidebar.button("Logout", key="sidebar_logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.email = None
            st.session_state.page = "landing"
            st.experimental_rerun()
        
        # Log de progresso
        logger.info("Sidebar reorganizada renderizada com sucesso")
        
        # ------------------------------------------------------------
        # CONTEÚDO PRINCIPAL 
        # ------------------------------------------------------------
        
        try:
            # Logo exibida consistentemente
            show_valuehunter_logo()
            
            # Título principal
            st.title("Seleção de Times")
            
            # A partir daqui, só mostrar a seleção de times se tivermos dados para isso
            if teams and len(teams) > 0:
                try:
                    # Seleção de times
                    col1, col2 = st.columns(2)
                    with col1:
                        home_team = st.selectbox("Time da Casa:", teams, key='home_team')
                    with col2:
                        away_teams = [team for team in teams if team != home_team]
                        away_team = st.selectbox("Time Visitante:", away_teams, key='away_team')
                        
                    logger.info(f"Times selecionados: {home_team} vs {away_team}")
                    
                    # Resto do código para mercados, odds e análise
                    # [Código omitido para brevidade]
                    
                except Exception as teams_error:
                    logger.error(f"Erro ao selecionar times: {str(teams_error)}")
                    st.error(f"Erro ao exibir seleção de times: {str(teams_error)}")
                    traceback.print_exc()
                    return
            else:
                st.info("Selecione uma liga no menu lateral. Os times serão carregados automaticamente.")
                if selected_league:
                    st.warning(f"Nenhum time disponível para {selected_league}. Clique em 'Recarregar Times desta Liga' para tentar novamente.")
                
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
