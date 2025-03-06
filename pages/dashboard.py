# pages/dashboard.py - Dashboard Principal (solução radical)
import streamlit as st
import logging
import traceback
import time
from utils.core import show_valuehunter_logo, go_to_login, update_purchase_button
from utils.data import fetch_fbref_data, parse_team_stats, get_odds_data
from utils.ai import analyze_with_gpt, format_prompt

# Configuração de logging
logger = logging.getLogger("valueHunter.dashboard")

# Funções do código original - show_usage_stats, check_analysis_limits, etc.
# (omitidos para brevidade)

# Função para carregar times com depuração aprimorada
def load_league_teams(selected_league):
    """Função para carregar os times da liga selecionada com depuração detalhada"""
    try:
        # Importar URLs do FBref
        from utils.data import FBREF_URLS
        
        # Exibir mensagem de carregamento
        with st.spinner(f"Carregando dados do campeonato {selected_league}..."):
            logger.info(f"Iniciando carregamento para liga: {selected_league}")
            
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
            
            logger.info(f"URL para {selected_league}: {stats_url}")
                
            # Buscar dados - com tratamento de erro explícito
            logger.info("Buscando HTML da página...")
            stats_html = fetch_fbref_data(stats_url)
            if not stats_html:
                st.error(f"Não foi possível carregar os dados do campeonato {selected_league}")
                logger.error(f"fetch_fbref_data retornou None para {stats_url}")
                return None, None, None
            
            logger.info(f"HTML obtido: {len(stats_html)} caracteres")
            
            # Parsear estatísticas dos times
            logger.info("Extraindo estatísticas de times...")
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
                
            logger.info(f"Dados carregados com sucesso: {len(teams)} times encontrados")
            logger.info(f"Times: {teams}")
            return teams, team_stats_df, stats_html
            
    except Exception as e:
        logger.error(f"Erro ao carregar times da liga: {str(e)}")
        st.error(f"Erro ao carregar times: {str(e)}")
        traceback.print_exc()
        return None, None, None

# Dados fixos de fallback caso tudo falhe
def get_fallback_teams(selected_league):
    """Fornece times de fallback caso o carregamento falhe"""
    fallback_teams = {
        "Premier League": ["Arsenal", "Aston Villa", "Brentford", "Brighton", "Chelsea", "Crystal Palace", "Everton", "Liverpool", "Manchester City", "Manchester United", "Newcastle", "Tottenham", "West Ham", "Wolves"],
        "La Liga": ["Atletico Madrid", "Barcelona", "Real Madrid", "Sevilla", "Valencia", "Villarreal", "Athletic Bilbao", "Real Sociedad", "Real Betis", "Celta Vigo"],
        "Serie A": ["AC Milan", "Inter Milan", "Juventus", "Napoli", "Roma", "Lazio", "Atalanta", "Fiorentina", "Torino", "Bologna"],
        "Bundesliga": ["Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Bayer Leverkusen", "Wolfsburg", "Frankfurt", "Monchengladbach", "Hoffenheim", "Stuttgart", "Union Berlin"],
        "Ligue 1": ["PSG", "Marseille", "Lyon", "Lille", "Monaco", "Rennes", "Nice", "Lens", "Montpellier", "Strasbourg"],
        "Champions League": ["Real Madrid", "Manchester City", "Bayern Munich", "Liverpool", "PSG", "Barcelona", "Chelsea", "Juventus", "Atletico Madrid", "Borussia Dortmund"]
    }
    return fallback_teams.get(selected_league, [])

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
        /* Outros estilos omitidos para brevidade */
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
            
            # Container para status
            status_container = st.sidebar.empty()
            
            # Obter a liga atual da URL ou sessão
            liga_atual = st.query_params.get('league', None) 
            if liga_atual is None and 'selected_league' in st.session_state:
                liga_atual = st.session_state.selected_league
            elif liga_atual is not None:
                st.session_state.selected_league = liga_atual
            elif available_leagues:
                liga_atual = available_leagues[0]
                st.session_state.selected_league = liga_atual
                
            # Mostrar índice da liga atual (para seleção correta)
            try:
                current_index = available_leagues.index(liga_atual)
            except (ValueError, TypeError):
                current_index = 0
                
            logger.info(f"Liga atual: {liga_atual}, índice: {current_index}")
            
            # SOLUÇÃO RADICAL: Form HTML puro que recarrega a página
            html_liga_form = f"""
            <form method="get" action="" id="league_form" style="margin-bottom: 15px;">
              <label for="league" style="font-weight: bold; display: block; margin-bottom: 5px;">Escolha o campeonato:</label>
              <select name="league" id="league" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc; background-color: #f0f0f0; color: #333;" onchange="this.form.submit()">
            """
            
            # Adicionar opções
            for league in available_leagues:
                selected = "selected" if league == liga_atual else ""
                html_liga_form += f'<option value="{league}" {selected}>{league}</option>\n'
            
            html_liga_form += """
              </select>
              <div style="text-align: center; margin-top: 8px;">
                <noscript><input type="submit" value="Selecionar" style="padding: 5px 15px;"></noscript>
                <small style="color: #666; font-style: italic;">Selecione uma liga para carregar os times</small>
              </div>
            </form>
            
            <script>
            // Garantir que o formulário seja submetido quando a liga mudar
            document.addEventListener('DOMContentLoaded', function() {
                const select = document.getElementById('league');
                if (select) {
                    select.addEventListener('change', function() {
                        document.getElementById('league_form').submit();
                    });
                }
            });
            </script>
            """
            
            # Renderizar seletor HTML
            st.sidebar.markdown(html_liga_form, unsafe_allow_html=True)
            
            # Carregar times para a liga atual
            selected_league = liga_atual
            
            # Verificar se já temos os times para esta liga em cache
            cache_key = f"teams_{selected_league}"
            if cache_key in st.session_state and st.session_state[cache_key] and len(st.session_state[cache_key]) > 0:
                logger.info(f"Usando times em cache para {selected_league}")
                teams = st.session_state[cache_key]
                team_stats_df = st.session_state.get('team_stats_df')
                stats_html = st.session_state.get('stats_html')
                status_container.info(f"Usando {len(teams)} times em cache para {selected_league}")
            else:
                # Carregar times
                logger.info(f"Carregando times para {selected_league} (sem cache)")
                status_container.info(f"Carregando times de {selected_league}...")
                
                teams, team_stats_df, stats_html = load_league_teams(selected_league)
                if teams and team_stats_df is not None and stats_html is not None:
                    # Salvar no cache
                    st.session_state[cache_key] = teams
                    st.session_state.team_stats_df = team_stats_df
                    st.session_state.stats_html = stats_html
                    
                    status_container.success(f"Dados de {selected_league} carregados! {len(teams)} times disponíveis.")
                else:
                    # Usar dados de fallback se o carregamento falhar
                    logger.warning(f"Usando dados de fallback para {selected_league}")
                    teams = get_fallback_teams(selected_league)
                    if teams:
                        st.session_state[cache_key] = teams
                        status_container.warning(f"Usando {len(teams)} times de fallback para {selected_league}")
                    else:
                        status_container.error(f"Não foi possível carregar times para {selected_league}")
                        
            # Botão para recarregar times
            if st.sidebar.button("🔄 Recarregar Times", type="primary", use_container_width=True):
                status_container.info(f"Recarregando times para {selected_league}...")
                
                # Forçar recarregamento
                teams, team_stats_df, stats_html = load_league_teams(selected_league)
                if teams and team_stats_df is not None and stats_html is not None:
                    # Atualizar cache
                    st.session_state[cache_key] = teams
                    st.session_state.team_stats_df = team_stats_df
                    st.session_state.stats_html = stats_html
                    
                    status_container.success(f"Dados recarregados! {len(teams)} times disponíveis.")
                    # Forçar atualização da página
                    st.experimental_rerun()
                else:
                    status_container.error(f"Erro ao recarregar times. Tente novamente.")
                    
            # Guardar seleção atual
            st.session_state.selected_league = selected_league
                    
        except Exception as sidebar_error:
            logger.error(f"Erro na seleção de liga: {str(sidebar_error)}")
            st.sidebar.error("Erro ao carregar ligas disponíveis.")
            traceback.print_exc()
            return
        
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
            
            # Verificação adicional para garantir que temos times
            if not teams or len(teams) == 0:
                # Tentar uma última vez carregar os times
                teams = get_fallback_teams(selected_league)
                if not teams or len(teams) == 0:
                    st.error("Não foi possível carregar os times. Por favor, selecione outro campeonato ou clique em 'Recarregar Times'.")
                    return
            
            # SELEÇÃO DE TIMES COM HTML PURO (se necessário, descomente isto)
            """
            # HTML puro para garantir seleção de times
            html_team_selector = f'''
            <div style="display: flex; gap: 20px; margin-bottom: 20px;">
              <div style="flex: 1;">
                <label style="font-weight: bold; display: block; margin-bottom: 5px;">Time da Casa:</label>
                <select id="home_team" name="home_team" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc;">
                  {' '.join([f'<option value="{team}">{team}</option>' for team in teams])}
                </select>
              </div>
              <div style="flex: 1;">
                <label style="font-weight: bold; display: block; margin-bottom: 5px;">Time Visitante:</label>
                <select id="away_team" name="away_team" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc;">
                  {' '.join([f'<option value="{team}">{team}</option>' for i, team in enumerate(teams) if i != 0])}
                </select>
              </div>
            </div>
            
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                // Função para atualizar times visitantes
                function updateAwayTeams() {
                    const homeTeam = document.getElementById('home_team').value;
                    const awaySelect = document.getElementById('away_team');
                    const teams = {str(teams)};
                    
                    // Limpar opções atuais
                    awaySelect.innerHTML = '';
                    
                    // Adicionar opções exceto o time da casa
                    teams.forEach(function(team) {
                        if (team !== homeTeam) {
                            const option = document.createElement('option');
                            option.value = team;
                            option.text = team;
                            awaySelect.appendChild(option);
                        }
                    });
                }
                
                // Configurar evento para atualizar quando o time da casa mudar
                const homeSelect = document.getElementById('home_team');
                if (homeSelect) {
                    homeSelect.addEventListener('change', updateAwayTeams);
                    // Executar na inicialização
                    updateAwayTeams();
                }
            });
            </script>
            '''
            
            # Exibir seletor HTML
            st.markdown(html_team_selector, unsafe_allow_html=True)
            """
            
            # Usando o seletor nativo do Streamlit
            col1, col2 = st.columns(2)
            with col1:
                home_team = st.selectbox("Time da Casa:", teams)
            with col2:
                away_teams = [team for team in teams if team != home_team]
                away_team = st.selectbox("Time Visitante:", away_teams)
                
            # Resto do código para análise e mercados...
            # [Omitido para brevidade]
                    
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
