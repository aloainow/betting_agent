# pages/dashboard.py - Dashboard Principal
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
        # IMPORTANTE: Verificar se precisamos atualizar os dados
        if not hasattr(st.session_state, 'user_stats_cache'):
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
        # Garantir que a barra lateral esteja visível na página principal (dashboard)
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Ocultar menu de navegação do Streamlit
        st.markdown("""
        <style>
            /* Ocultar menu de navegação */
            header[data-testid="stHeader"] {
                display: none !important;
            }
            
            /* Ocultar hamburger menu e botão de navegação */
            button[kind="header"] {
                display: none !important;
            }
            
            /* Ocultar o menu de navegação de páginas na sidebar */
            section[data-testid="stSidebarNavContainer"] {
                display: none !important;
            }
            
            /* Seletores alternativos para nova versão do Streamlit */
            div.stSidebarNavItems, 
            button.stSidebarButton,
            div.st-emotion-cache-16idsys,
            ul.st-emotion-cache-pbk8do {
                display: none !important;
            }
            
            /* Adicionais seletores para atingir o mesmo alvo */
            [data-testid="collapsedControl"],
            #MainMenu,
            [data-testid="stSidebar"] > div:first-child > div:first-child > div > button,
            footer {
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
            
            # Seleção de liga
            selected_league = st.sidebar.selectbox(
                "Escolha o campeonato:",
                available_leagues
            )
            logger.info(f"Liga selecionada: {selected_league}")
            
            # Container para status
            status_container = st.sidebar.empty()
        except Exception as sidebar_error:
            logger.error(f"Erro na seleção de liga: {str(sidebar_error)}")
            st.sidebar.error("Erro ao carregar ligas disponíveis.")
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
        # CONTEÚDO PRINCIPAL (mantido como antes)
        # ------------------------------------------------------------
        
        # Conteúdo principal com tratamento de erro em cada etapa
        try:
            # Logo exibida consistentemente
            show_valuehunter_logo()
            
            # Título principal
            st.title("Seleção de Times")
                
            # Bloco try separado para carregar dados
            try:
                # Mostrar spinner enquanto carrega
                with st.spinner("Carregando dados do campeonato..."):
                    # Tentar carregar dados da liga selecionada
                    if selected_league not in FBREF_URLS:
                        st.error(f"Liga não encontrada: {selected_league}")
                        logger.error(f"Liga {selected_league} não encontrada em FBREF_URLS")
                        return
                        
                    # Obter URL das estatísticas
                    stats_url = FBREF_URLS[selected_league].get("stats")
                    if not stats_url:
                        st.error(f"URL de estatísticas não encontrada para {selected_league}")
                        logger.error(f"URL de estatísticas ausente para {selected_league}")
                        return
                        
                    # Buscar dados - com tratamento de erro explícito
                    stats_html = fetch_fbref_data(stats_url)
                    if not stats_html:
                        st.error(f"Não foi possível carregar os dados do campeonato {selected_league}")
                        logger.error(f"fetch_fbref_data retornou None para {stats_url}")
                        return
                    
                    # Parsear estatísticas dos times
                    team_stats_df = parse_team_stats(stats_html)
                    if team_stats_df is None:
                        st.error("Erro ao processar dados de estatísticas dos times")
                        logger.error("parse_team_stats retornou None")
                        return
                        
                    if 'Squad' not in team_stats_df.columns:
                        st.error("Dados incompletos: coluna 'Squad' não encontrada")
                        logger.error(f"Colunas disponíveis: {team_stats_df.columns.tolist()}")
                        return
                    
                    # Extrair lista de times
                    teams = team_stats_df['Squad'].dropna().unique().tolist()
                    if not teams:
                        st.error("Não foi possível encontrar os times do campeonato")
                        logger.error("Lista de times vazia após dropna() e unique()")
                        return
                        
                    # Mostrar mensagem de sucesso
                    status_container.success("Dados carregados com sucesso!")
                    logger.info(f"Dados carregados: {len(teams)} times encontrados")
                    
            except Exception as load_error:
                logger.error(f"Erro ao carregar dados: {str(load_error)}")
                st.error(f"Erro ao carregar dados: {str(load_error)}")
                traceback.print_exc()
                return
                
            # Bloco try separado para selecionar times
            try:
                # Seleção de times
                col1, col2 = st.columns(2)
                with col1:
                    home_team = st.selectbox("Time da Casa:", teams, key='home_team')
                with col2:
                    away_teams = [team for team in teams if team != home_team]
                    away_team = st.selectbox("Time Visitante:", away_teams, key='away_team')
                    
                logger.info(f"Times selecionados: {home_team} vs {away_team}")
                
                # Obter estatísticas do usuário
                user_stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
                
            except Exception as teams_error:
                logger.error(f"Erro ao selecionar times: {str(teams_error)}")
                st.error(f"Erro ao exibir seleção de times: {str(teams_error)}")
                traceback.print_exc()
                return
                
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
                col1, col2, col3 = st.columns([1,1,1])
                with col2:
                    analyze_button = st.button("Analisar Partida", type="primary")
                    
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
                        
                        # Executar análise com tratamento de erro para cada etapa
                        try:
                            # Etapa 1: Carregar dados
                            status.info("Carregando dados dos times...")
                            if not stats_html or team_stats_df is None:
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
                                
                                # Exibir a análise em uma div com largura total
                                st.markdown(f'<div class="analysis-result">{analysis}</div>', unsafe_allow_html=True)
                                
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
