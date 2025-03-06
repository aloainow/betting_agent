# pages/dashboard.py - Solução com cache apenas para nomes dos times
import streamlit as st
import logging
import traceback
import json
import os
import time
from utils.core import show_valuehunter_logo, go_to_login, update_purchase_button, DATA_DIR
from utils.data import fetch_fbref_data, parse_team_stats, get_odds_data
from utils.ai import analyze_with_gpt, format_prompt

# Configuração de logging
logger = logging.getLogger("valueHunter.dashboard")

# Diretório para cache de times
TEAMS_CACHE_DIR = os.path.join(DATA_DIR, "teams_cache")
os.makedirs(TEAMS_CACHE_DIR, exist_ok=True)

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
    
        return cleaned
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
        return cleaned

def show_league_selector(available_leagues, status_container):
    """
    Função melhorada para mostrar o seletor de ligas e gerenciar o estado
    
    Args:
        available_leagues (list): Lista de ligas disponíveis
        status_container: Container do Streamlit para mostrar status
    
    Returns:
        str: Nome da liga selecionada
    """
    try:
        # Obter liga da URL ou da sessão
        liga_atual = st.query_params.get('league', None) 
        
        if liga_atual is None and 'selected_league' in st.session_state:
            liga_atual = st.session_state.selected_league
        elif liga_atual is not None:
            # Verifica se a liga existe na lista disponível
            if liga_atual in available_leagues:
                st.session_state.selected_league = liga_atual
                # Limpar caches antigos e forçar atualização
                clear_cache(liga_atual)
                logger.info(f"Liga mudada via URL: {liga_atual}")
            else:
                # Se a liga da URL não existe na lista, usa a primeira disponível
                liga_atual = available_leagues[0]
                st.session_state.selected_league = liga_atual
                logger.warning(f"Liga inválida na URL: {st.query_params.get('league')}, usando {liga_atual}")
        elif available_leagues:
            liga_atual = available_leagues[0]
            st.session_state.selected_league = liga_atual
            
        # Adicionar botão de redefinição para depuração
        debug_col1, debug_col2 = st.sidebar.columns([3, 1])
        with debug_col1:
            status_container.info(f"Liga atual: {liga_atual}")
        with debug_col2:
            if st.button("🔄", help="Redefinir seleção de liga", key="reset_league"):
                clear_cache(liga_atual)
                status_container.success(f"Caches limpos para {liga_atual}")
                # Força recarregamento da página
                liga_param = f"league={liga_atual}"
                force_param = f"force_refresh={int(time.time())}"
                st.query_params.league = liga_atual
                st.query_params.force_refresh = int(time.time())
                st.rerun()
                
        # Mostrar índice da liga atual (para seleção correta)
        try:
            current_index = available_leagues.index(liga_atual)
        except (ValueError, TypeError):
            current_index = 0
            
        logger.info(f"Liga atual: {liga_atual}, índice: {current_index}")
        
        # Form HTML com recarregamento direto e debug info
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
          <input type="hidden" name="force_refresh" value="1">
        </form>
        
        <script>
        // Garantir que o formulário seja submetido quando a liga mudar
        document.addEventListener('DOMContentLoaded', function() {
            const select = document.getElementById('league');
            if (select) {
                select.addEventListener('change', function() {
                    // Adiciona timestamp para forçar refresh e evitar cache do navegador
                    const forceInput = document.createElement('input');
                    forceInput.type = 'hidden';
                    forceInput.name = 'force_refresh';
                    forceInput.value = Date.now();
                    document.getElementById('league_form').appendChild(forceInput);
                    document.getElementById('league_form').submit();
                });
            }
        });
        </script>
        """
        
        # Renderizar seletor HTML
        st.sidebar.markdown(html_liga_form, unsafe_allow_html=True)
        
        return liga_atual
        
    except Exception as e:
        logger.error(f"Erro no seletor de ligas: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        if available_leagues:
            return available_leagues[0]
        return "Premier League"  # Fallback

def get_cached_teams(league):
    """Carrega apenas os nomes dos times do cache persistente"""
    # Sanitizar nome da liga para evitar problemas com caracteres especiais
    safe_league_name = league.replace(' ', '_').replace('/', '_').replace('\\', '_')
    cache_file = os.path.join(TEAMS_CACHE_DIR, f"{safe_league_name}_teams.json")
    
    logger.info(f"Verificando cache de times para liga '{league}' em: {cache_file}")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                teams = data.get('teams', [])
                timestamp = data.get('timestamp', 0)
                
                # Verificar se os dados são válidos
                if not teams or len(teams) < 3:  # Espera-se pelo menos alguns times
                    logger.warning(f"Cache para {league} tem poucos times: {len(teams)}")
                    return [], 0
                    
                logger.info(f"Carregados {len(teams)} times do cache para {league}")
                return teams, timestamp
        except Exception as e:
            logger.error(f"Erro ao carregar cache para {league}: {str(e)}")
            
            # Tentar fazer backup do arquivo corrompido
            try:
                backup_file = f"{cache_file}.bak.{int(time.time())}"
                os.rename(cache_file, backup_file)
                logger.info(f"Backup do cache corrompido criado: {backup_file}")
            except:
                pass
    else:
        logger.info(f"Nenhum cache encontrado para {league}")
        
    return [], 0

def save_teams_to_cache(league, teams):
    """Salva apenas os nomes dos times no cache persistente"""
    # Sanitizar nome da liga para evitar problemas com caracteres especiais
    safe_league_name = league.replace(' ', '_').replace('/', '_').replace('\\', '_')
    cache_file = os.path.join(TEAMS_CACHE_DIR, f"{safe_league_name}_teams.json")
    
    try:
        # Verificar se os dados são válidos para salvar
        if not teams or len(teams) < 3:  # Espera-se pelo menos alguns times
            logger.warning(f"Tentando salvar cache com poucos times para {league}: {len(teams)}")
            return False
            
        # Verificar se o diretório existe
        if not os.path.exists(TEAMS_CACHE_DIR):
            os.makedirs(TEAMS_CACHE_DIR, exist_ok=True)
            logger.info(f"Diretório de cache de times criado: {TEAMS_CACHE_DIR}")
        
        # Salvar temporariamente primeiro para garantir atomicidade
        temp_file = f"{cache_file}.tmp"
        
        data = {
            'teams': teams,
            'timestamp': time.time(),
            'league': league,  # Guardar o nome original da liga
            'count': len(teams)
        }
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        # Renomear o arquivo temporário para o arquivo final
        os.replace(temp_file, cache_file)
            
        logger.info(f"Salvos {len(teams)} times no cache para {league}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar cache para {league}: {str(e)}")
        return False

def load_league_teams(selected_league, status_container, force_refresh=False):
    """
    Função completa para carregar times de uma liga com tratamento de erros
    
    Args:
        selected_league (str): Nome da liga selecionada
        status_container: Container do Streamlit para mostrar status
        force_refresh (bool): Se deve forçar atualização ignorando o cache
    
    Returns:
        list: Lista de times da liga
    """
    try:
        # Verificar parâmetros na URL para forçar refresh
        if 'force_refresh' in st.query_params:
            force_refresh = True
            logger.info(f"Forçando atualização pelos parâmetros da URL")
            
        # Se a seleção de liga mudou, forçar refresh
        if 'last_league' in st.session_state and st.session_state.last_league != selected_league:
            force_refresh = True
            logger.info(f"Liga mudou de {st.session_state.last_league} para {selected_league}: forçando atualização")
            
        # Atualizar última liga selecionada
        st.session_state.last_league = selected_league
            
        # Verificar cache primeiro (se não estiver forçando refresh)
        if not force_refresh:
            teams, timestamp = get_cached_teams(selected_league)
            
            # Se temos times em cache e não são muito antigos (30 dias)
            cache_max_age = 30 * 24 * 60 * 60  # 30 dias em segundos
            if teams and len(teams) > 5 and (time.time() - timestamp) < cache_max_age:
                logger.info(f"Usando nomes de times em cache para {selected_league} ({len(teams)} times)")
                
                # Mostrar feedback ao usuário
                status_container.success(f"✅ {len(teams)} times carregados para {selected_league}")
                return teams
                
            logger.info(f"Cache não encontrado ou expirado para {selected_league}")
        else:
            logger.info(f"Ignorando cache para {selected_league} (force_refresh={force_refresh})")
        
        # Se chegamos aqui, precisamos buscar os nomes dos times online
        from utils.data import FBREF_URLS
        
        # Verificar se a liga existe
        if selected_league not in FBREF_URLS:
            logger.error(f"Liga {selected_league} não encontrada em FBREF_URLS")
            status_container.error(f"⚠️ Liga '{selected_league}' não encontrada na configuração")
            return []
            
        # Obter URL das estatísticas
        stats_url = FBREF_URLS[selected_league].get("stats")
        if not stats_url:
            logger.error(f"URL de estatísticas ausente para {selected_league}")
            status_container.error(f"⚠️ URL de estatísticas não encontrada para {selected_league}")
            return []
        
        # Mostrar mensagem de loading  
        status_container.info(f"🔄 Buscando times para {selected_league}...")
            
        # Buscar dados
        from utils.data import fetch_fbref_data
        stats_html = fetch_fbref_data(stats_url, force_reload=force_refresh, league_name=selected_league)
        if not stats_html:
            logger.error(f"fetch_fbref_data retornou None para {stats_url}")
            status_container.error(f"❌ Falha ao carregar dados para {selected_league}")
            return []
        
        # Parsear estatísticas dos times (só para extrair nomes)
        from utils.data import parse_team_stats
        team_stats_df = parse_team_stats(stats_html)
        if team_stats_df is None or 'Squad' not in team_stats_df.columns:
            logger.error("Erro ao processar dados de estatísticas dos times")
            status_container.error("❌ Erro ao processar dados dos times")
            return []
        
        # Extrair lista de times
        teams = team_stats_df['Squad'].dropna().unique().tolist()
        if not teams:
            logger.error("Lista de times vazia após dropna() e unique()")
            status_container.error("❌ Nenhum time encontrado na resposta")
            return []
            
        # Validação extra - deve ter pelo menos alguns times
        if len(teams) < 5:
            logger.warning(f"Poucos times encontrados para {selected_league}: {len(teams)}")
            status_container.warning(f"⚠️ Apenas {len(teams)} times encontrados. Dados podem estar incompletos.")
            
            # Mostrar os times encontrados para debug
            logger.info(f"Times encontrados: {teams}")
            
            # Mesmo com poucos times, continuamos para permitir testes
        
        # Salvar apenas os nomes dos times no cache persistente
        save_teams_to_cache(selected_league, teams)
            
        # Sucesso
        logger.info(f"Nomes de times carregados online: {len(teams)} times encontrados")
        status_container.success(f"✅ {len(teams)} times carregados para {selected_league}")
        
        return teams
            
    except Exception as e:
        logger.error(f"Erro ao carregar times da liga: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        status_container.error(f"❌ Erro: {str(e)}")
        return []

def fetch_stats_data(selected_league):
    """Busca as estatísticas completas (sem cache)"""
    try:
        from utils.data import FBREF_URLS
        
        # Verificar se a liga existe
        if selected_league not in FBREF_URLS:
            st.error(f"Liga não encontrada: {selected_league}")
            return None, None
            
        # Obter URL das estatísticas
        stats_url = FBREF_URLS[selected_league].get("stats")
        if not stats_url:
            st.error(f"URL de estatísticas não encontrada para {selected_league}")
            return None, None
            
        # Buscar dados - com tratamento de erro explícito e MODIFICADO para incluir nome da liga
        with st.spinner("Buscando estatísticas atualizadas..."):
            stats_html = fetch_fbref_data(stats_url, league_name=selected_league)
            if not stats_html:
                st.error(f"Não foi possível carregar os dados do campeonato {selected_league}")
                return None, None
            
            # Parsear estatísticas dos times
            team_stats_df = parse_team_stats(stats_html)
            if team_stats_df is None:
                st.error("Erro ao processar dados de estatísticas dos times")
                return None, None
                
            return team_stats_df, stats_html
            
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {str(e)}")
        st.error(f"Erro ao buscar estatísticas: {str(e)}")
        return None, None

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
            
            # Usar o novo seletor de ligas
            selected_league = show_league_selector(available_leagues, status_container)
                
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
            
            # Verificar se a liga foi mudada ou se há forçar refresh
            force_refresh = False
            if 'force_refresh' in st.query_params:
                force_refresh = True
                logger.info("Forçando atualização pelos parâmetros de URL")
                
            # Container para status
            status_container = st.empty()
            
            # Usando a nova função de carregamento de times
            teams = load_league_teams(selected_league, status_container, force_refresh)
            
            # Verificação adicional para garantir que temos times
            if not teams or len(teams) == 0:
                st.warning("Não foi possível carregar os times para este campeonato.")
                st.info("Por favor, clique no botão 'Atualizar Times' na barra lateral para tentar novamente.")
                
                # Botão de atualização de emergência
                if st.button("🆘 Forçar Recarga Completa", type="primary"):
                    # Limpar todo o cache
                    cleared = clear_cache()
                    st.success(f"Limpeza de cache completa: {cleared} arquivos removidos")
                    # Recarregamento forçado
                    st.query_params.force_refresh = int(time.time())
                    st.rerun()
                    
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
                    team_stats_df, stats_html = fetch_stats_data(selected_league)
                    
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
