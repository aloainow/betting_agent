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

# Adicione todas essas funções no início do arquivo pages/dashboard.py,
# antes das outras funções que as utilizam

def format_text_for_display(text, max_width=70):
    """
    Formata um texto para garantir que nenhuma linha exceda o comprimento máximo especificado.
    
    Args:
        text (str): Texto a ser formatado
        max_width (int): Largura máxima de cada linha em caracteres
        
    Returns:
        str: Texto formatado com quebras de linha
    """
    lines = []
    for line in text.split('\n'):
        if len(line) <= max_width:
            lines.append(line)
        else:
            # Quebrar linhas muito longas
            current_line = ""
            words = line.split()
            
            for word in words:
                if len(current_line) + len(word) + 1 <= max_width:
                    # Adicionar palavra à linha atual
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
                else:
                    # Iniciar nova linha
                    lines.append(current_line)
                    current_line = word
            
            # Adicionar a última linha
            if current_line:
                lines.append(current_line)
    
    return '\n'.join(lines)

def format_generic_section(section):
    """
    Formata seções genéricas da análise
    
    Args:
        section (str): Texto da seção
        
    Returns:
        str: Seção formatada
    """
    lines = section.split('\n')
    formatted_lines = []
    
    # Cabeçalho sempre permanece igual
    if lines and lines[0].startswith('# '):
        formatted_lines.append(lines[0])
        start_idx = 1
    else:
        start_idx = 0
    
    # Formatar as demais linhas
    for i in range(start_idx, len(lines)):
        formatted_lines.append(format_text_for_display(lines[i], max_width=70))
    
    return '\n'.join(formatted_lines)

def format_confidence_section(section):
    """
    Formata especificamente a seção de Nível de Confiança
    
    Args:
        section (str): Texto da seção de confiança
        
    Returns:
        str: Seção de confiança formatada
    """
    lines = section.split('\n')
    formatted_lines = []
    
    # Cabeçalho sempre permanece igual
    if lines and lines[0].startswith('# '):
        formatted_lines.append(lines[0])
        start_idx = 1
    else:
        start_idx = 0
    
    # Formatar cada linha de conteúdo
    for i in range(start_idx, len(lines)):
        line = lines[i]
        
        # Se a linha começa com um marcador, processar especialmente
        if line.strip().startswith('- **'):
            # Dividir em marcador e conteúdo
            parts = line.split(':', 1)
            
            if len(parts) > 1:
                # Adicionar o marcador
                formatted_lines.append(parts[0] + ':')
                
                # Formatar o conteúdo com indentação
                content = parts[1].strip()
                formatted_content = format_text_for_display(content, max_width=65)
                
                # Adicionar indentação às linhas de conteúdo
                for content_line in formatted_content.split('\n'):
                    formatted_lines.append('  ' + content_line)
            else:
                # Se não conseguir dividir, adicionar linha inteira formatada
                formatted_lines.append(format_text_for_display(line, max_width=70))
        else:
            # Para outras linhas, simplesmente formatar
            formatted_lines.append(format_text_for_display(line, max_width=70))
    
    return '\n'.join(formatted_lines)

def update_opportunities_format(opportunities_section):
    """
    Atualiza a formatação da seção de oportunidades para evitar linhas muito longas
    que exijam rolagem horizontal.
    
    Args:
        opportunities_section (str): Texto da seção de oportunidades
        
    Returns:
        str: Texto reformatado para limitar a largura
    """
    # Dividir o texto em linhas
    lines = opportunities_section.split('\n')
    formatted_lines = []
    
    # Largura máxima por linha (ajuste conforme necessário)
    max_width = 70
    
    for line in lines:
        # Se a linha for uma oportunidade (começa com '- **')
        if line.startswith('- **'):
            # Manter a primeira linha como está (título da oportunidade)
            formatted_lines.append(line)
        # Se for uma justificativa (começa com '  *Justificativa:')
        elif line.strip().startswith('*Justificativa:'):
            # Verificar se já está dividida em múltiplas linhas
            if '\n' in line:
                # Já está formatada, adicionar todas as linhas
                formatted_lines.extend(line.split('\n'))
            else:
                # Separar a parte inicial "*Justificativa:" do resto do texto
                prefix = "  *Justificativa:"
                content = line.strip()[len(prefix):].strip()
                
                # Formatar o conteúdo da justificativa
                current_line = prefix + " "
                words = content.split()
                
                for word in words:
                    # Se adicionar a palavra não ultrapassar a largura máxima
                    if len(current_line) + len(word) + 1 <= max_width:
                        # Adicionar palavra à linha atual
                        if current_line.endswith(" "):
                            current_line += word
                        else:
                            current_line += " " + word
                    else:
                        # Adicionar a linha atual e começar uma nova
                        formatted_lines.append(current_line)
                        # Alinhar a nova linha com a justificativa (espaços antes)
                        current_line = "    " + word
                
                # Adicionar a última linha da justificativa
                if current_line:
                    formatted_lines.append(current_line)
        else:
            # Outras linhas são mantidas como estão
            formatted_lines.append(line)
    
    # Juntar as linhas formatadas
    return '\n'.join(formatted_lines)

def format_opportunities_section(section):
    """
    Formata especificamente a seção de Oportunidades Identificadas,
    mantendo apenas o formato básico da oportunidade sem estatísticas adicionais.
    
    Args:
        section (str): Texto da seção de oportunidades
        
    Returns:
        str: Seção de oportunidades formatada e simplificada
    """
    # Se não houver oportunidades ou apenas a mensagem de que não há valor
    if "Infelizmente não detectamos valor" in section:
        return section
    
    import re
    
    lines = section.split('\n')
    formatted_lines = []
    
    # Cabeçalho sempre permanece igual
    if lines and lines[0].startswith('# '):
        formatted_lines.append(lines[0])
    else:
        formatted_lines.append("# Oportunidades Identificadas:")
    
    # Procurar padrões de oportunidades e reescrever no formato desejado
    pattern = r"- \*\*([^*]+)\*\*: Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(Valor de (\d+\.\d+)%\)"
    
    for line in lines:
        match = re.search(pattern, line)
        if match:
            opportunity_name, real_prob, implied_prob, margin = match.groups()
            # Formatar exatamente como desejado, sem nenhuma estatística adicional
            formatted_line = f"- **{opportunity_name.strip()}**: Real {real_prob}% vs Implícita {implied_prob}% (Valor de {margin}%)"
            formatted_lines.append(formatted_line)
    
    return "\n".join(formatted_lines)

def format_all_analysis_sections(analysis_text):
    """
    Formata todas as seções da análise para evitar linhas muito longas.
    
    Args:
        analysis_text (str): Texto completo da análise
        
    Returns:
        str: Texto da análise com todas as seções formatadas
    """
    # Quebrar o texto em seções principais
    sections = []
    current_section = []
    
    for line in analysis_text.split('\n'):
        # Se for um cabeçalho de seção (começa com #)
        if line.startswith('# '):
            # Se já temos uma seção anterior, adicionar às seções
            if current_section:
                sections.append('\n'.join(current_section))
                current_section = []
            
            # Iniciar nova seção com o cabeçalho
            current_section.append(line)
        else:
            # Adicionar linha à seção atual
            current_section.append(line)
    
    # Adicionar a última seção se existir
    if current_section:
        sections.append('\n'.join(current_section))
    
    # Formatar cada seção individualmente
    formatted_sections = []
    
    for section in sections:
        # Identificar seções especiais para tratamento específico
        if section.startswith('# Nível de Confiança Geral'):
            formatted_sections.append(format_confidence_section(section))
        elif section.startswith('# Oportunidades Identificadas'):
            formatted_sections.append(format_opportunities_section(section))
        else:
            # Formatar seções genéricas
            formatted_sections.append(format_generic_section(section))
    
    # Juntar todas as seções formatadas
    return '\n\n'.join(formatted_sections)

# Funções auxiliares para seleção de ligas (ADICIONADAS NO INÍCIO)
def get_league_selection(key_suffix=""):
    """
    Função melhorada para obter a lista de ligas e mostrar o seletor,
    eliminando duplicações com diferentes formatações e garantindo que Serie B (Brazil) e Serie B (Italy) estejam incluídas.
    
    Args:
        key_suffix (str): Sufixo para tornar a chave única
    
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
            # Mesmo sem ligas da API, vamos adicionar as Series B
            all_leagues = ["Serie B (Brazil)", "Serie B (Italy)"]
        else:
            # Verificar se a Serie B (Brazil) já está na lista
            serie_b_brazil_exists = False
            serie_b_italy_exists = False
            
            for league in all_leagues:
                if "serie b" in league.lower() and "brazil" in league.lower():
                    serie_b_brazil_exists = True
                if "serie b" in league.lower() and "italy" in league.lower():
                    serie_b_italy_exists = True
            
            # Adicionar as ligas faltantes
            if not serie_b_brazil_exists:
                all_leagues.append("Serie B (Brazil)")
            if not serie_b_italy_exists:
                all_leagues.append("Serie B (Italy)")
        
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
        
        # Garantir que Serie B (Brazil) e Serie B (Italy) são preservadas após a simplificação
        if "serie b" in canonical_leagues:
            # Verificar qual Serie B está mapeada para "serie b"
            current_serie_b = canonical_leagues["serie b"]
            
            # Remover a entrada existente para "serie b"
            del canonical_leagues["serie b"]
            
            # Adicionar entradas específicas para cada Serie B
            canonical_leagues["serie b brazil"] = "Serie B (Brazil)"
            canonical_leagues["serie b italy"] = "Serie B (Italy)"
        else:
            # Se não existe um mapeamento para "serie b", simplesmente adicionar ambas
            canonical_leagues["serie b brazil"] = "Serie B (Brazil)"
            canonical_leagues["serie b italy"] = "Serie B (Italy)"
        
        # Obter lista final de ligas sem duplicatas
        unique_leagues = list(canonical_leagues.values())
        
        # Ordenar alfabeticamente
        unique_leagues.sort()
        
        # Inicializar seleção se necessário
        if 'selected_league' not in st.session_state or st.session_state.selected_league not in unique_leagues:
            st.session_state.selected_league = unique_leagues[0] if unique_leagues else None
        
        # Seletor de liga com chave única
        unique_key = f"league_selector{key_suffix}"
        
        selected_league = st.sidebar.selectbox(
            "Escolha o campeonato:",
            options=unique_leagues,
            index=unique_leagues.index(st.session_state.selected_league) if st.session_state.selected_league in unique_leagues else 0,
            key=unique_key
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

def _league_update_button(selected_league):
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

# Modify the _usage_stats() function to use consistent naming
def _usage_stats():
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
        
        # Fix: Use consistent naming for credits
        # First, check which key exists in the stats dictionary
        if 'credits_remaining' in stats:
            credits_key = 'credits_remaining'
        elif 'credits_reing' in stats:
            credits_key = 'credits_reing'
        else:
            # If neither exists, provide a fallback
            credits_key = None
            logger.warning("Neither 'credits_remaining' nor 'credits_reing' found in stats")
        
        # Display remaining credits
        if credits_key:
            st.sidebar.markdown(f"**Créditos Restantes:** {stats[credits_key]}")
        else:
            st.sidebar.markdown("**Créditos Restantes:** Indisponível")
        
        # Add progress bar for credits
        if stats.get('credits_total', 0) > 0:
            progress = stats.get('credits_used', 0) / stats['credits_total']
            st.sidebar.progress(min(progress, 1.0))
        
        # Free tier renewal info (if applicable)
        if stats.get('tier') == 'free' and stats.get('next_free_credits_time'):
            st.sidebar.info(f"⏱️ Renovação em: {stats['next_free_credits_time']}")
        elif stats.get('tier') == 'free' and stats.get('free_credits_reset'):
            st.sidebar.success("✅ Créditos renovados!")
        
        # Warning for paid tiers about to be downgraded
        if stats.get('days_until_downgrade'):
            st.sidebar.warning(f"⚠️ Sem créditos há {7-stats['days_until_downgrade']} dias. Você será rebaixado para o pacote Free em {stats['days_until_downgrade']} dias se não comprar mais créditos.")
            
    except Exception as e:
        logger.error(f"Erro ao exibir estatísticas de uso: {str(e)}")
        st.sidebar.error("Erro ao carregar estatísticas")


# Update check_analysis_limits function to use consistent naming
def check_analysis_limits(selected_markets):
    """Check if user can perform analysis with selected markets"""
    try:
        num_markets = sum(1 for v in selected_markets.values() if v)
        stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
        
        # Check which key exists in the stats dictionary
        if 'credits_remaining' in stats:
            credits_key = 'credits_remaining'
        elif 'credits_reing' in stats:
            credits_key = 'credits_reing'
        else:
            # If neither exists, provide a fallback
            credits_key = None
            logger.warning("Neither 'credits_remaining' nor 'credits_reing' found in stats")
            return False
        
        # Get remaining credits
        remaining_credits = stats[credits_key]
        
        # Check if user has enough credits
        if num_markets > remaining_credits:
            # Special handling for Free tier
            if stats.get('tier') == 'free':
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
                
                # days until downgrade if applicable
                if stats.get('days_until_downgrade'):
                    st.warning(f"⚠️ Atenção: Você será rebaixado para o pacote Free em {stats['days_until_downgrade']} dias se não comprar mais créditos.")
                
                # purchase options
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
        
        # Se chegou até aqui, permite continuar (sem debitar)
        return True
        
    except Exception as e:
        logger.error(f"Erro ao verificar limites de análise: {str(e)}")
        logger.error(traceback.format_exc())
        st.error("Erro ao verificar limites de análise. Por favor, tente novamente.")
        return False
        

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
        
        # Fix: Use consistent naming for credits
        # First, check which key exists in the stats dictionary
        if 'credits_remaining' in stats:
            credits_key = 'credits_remaining'
        elif 'credits_reing' in stats:
            credits_key = 'credits_reing'
        else:
            # If neither exists, provide a fallback
            credits_key = None
            logger.warning("Neither 'credits_remaining' nor 'credits_reing' found in stats")
        
        # Display remaining credits
        if credits_key:
            st.sidebar.markdown(f"**Créditos Restantes:** {stats[credits_key]}")
        else:
            st.sidebar.markdown("**Créditos Restantes:** Indisponível")
        
        # Add progress bar for credits
        if stats.get('credits_total', 0) > 0:
            progress = stats.get('credits_used', 0) / stats['credits_total']
            st.sidebar.progress(min(progress, 1.0))
        
        # Free tier renewal info (if applicable)
        if stats.get('tier') == 'free' and stats.get('next_free_credits_time'):
            st.sidebar.info(f"⏱️ Renovação em: {stats['next_free_credits_time']}")
        elif stats.get('tier') == 'free' and stats.get('free_credits_reset'):
            st.sidebar.success("✅ Créditos renovados!")
        
        # Warning for paid tiers about to be downgraded
        if stats.get('days_until_downgrade'):
            st.sidebar.warning(f"⚠️ Sem créditos há {7-stats['days_until_downgrade']} dias. Você será rebaixado para o pacote Free em {stats['days_until_downgrade']} dias se não comprar mais créditos.")
            
    except Exception as e:
        logger.error(f"Erro ao exibir estatísticas de uso: {str(e)}")
        st.sidebar.error("Erro ao carregar estatísticas")

def show_main_dashboard():
    """Show the main dashboard com navegação mobile nativa do Streamlit"""
    try:
        # Aplicar correção para animação da sidebar
        fix_sidebar_animation()
        # Aplicar tema escuro
        apply_dark_theme()
        # Aplicar correção para cores de dropdown no mobile
        fix_mobile_dropdown_colors()
        
        
        # First CSS block - Fix for text color
        st.markdown("""
        <style>
        /* Global text color fix for all elements */
        .stCheckbox label p,
        .stSelectbox label,
        .stSelectbox span,
        [data-baseweb="select"] span,
        [role="option"],
        .streamlit-expanderHeader,
        div.row-widget p,
        div.row-widget span {
            color: #f8f8f2 !important;
        }
        
        /* Backgrounds for better contrast */
        .stCheckbox,
        .stSelectbox [data-baseweb="select"],
        [data-baseweb="menu"],
        [role="listbox"] {
            background-color: #27272a !important;
            border: 1px solid #3F3F45 !important;
        }
        
        /* Mobile specific enhancements */
        @media (max-width: 767px) {
            .stCheckbox label p,
            .stSelectbox label {
                font-weight: bold !important;
                padding: 3px !important;
            }
            
            .stCheckbox,
            .stSelectbox [data-baseweb="select"] {
                border-left: 2px solid #fd7014 !important;
                padding: 5px !important;
                margin: 5px 0 !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Second CSS block - More targeted spacing fix
        st.markdown("""
        <style>
        /* Mild spacing adjustments only for mobile */
        @media (max-width: 767px) {
            /* Make info boxes more compact */
            .stAlert {
                padding: 8px !important;
                margin-bottom: 8px !important;
            }
            
            /* Slightly reduce title size */
            h1 {
                font-size: 1.7rem !important;
            }
            
            /* Make dropdowns and checkboxes more compact */
            .stSelectbox, .stCheckbox {
                margin-bottom: 8px !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        # Third CSS block - Fix for top white space
        st.markdown("""
        <style>
        /* Remover completamente o espaço extra no topo da página */
        .main .block-container {
            padding-top: 0 !important;
            margin-top: 0 !important;
            gap: 0 !important;
        }
        
        /* Remover espaço entre elementos no topo */
        .main .element-container:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* Forçar o header a ficar sem altura e totalmente escondido */
        header[data-testid="stHeader"] {
            height: 0 !important;
            min-height: 0 !important;
            visibility: hidden !important;
            position: absolute !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        
        /* Remover margem do título principal */
        h1:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* Garantir que não haja espaços extras no início do app */
        .stApp {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Verificações de autenticação
        if not hasattr(st.session_state, 'authenticated') or not st.session_state.authenticated:
            st.error("Sessão não autenticada. Por favor, faça login novamente.")
            st.session_state.page = "login"
            st.experimental_rerun()
            return

        # IMPORTANTE: Adicionar antes de qualquer outro elemento
        # Mensagem de instrução no topo da página
        st.info("📱 **Versão Mobile**: Para acessar o menu, toque no botão ≡ no CANTO SUPERIOR ESQUERDO da tela.", icon="ℹ️")

        # Sidebar normal do Streamlit
        with st.sidebar:
            st.title("ValueHunter")
            st.markdown("---")
            
            # Mostrar estatísticas de uso
            show_usage_stats()
            
            # Escolha da liga
            selected_league = get_league_selection(key_suffix="_main_dashboard")
            if not selected_league:
                st.error("Não foi possível selecionar uma liga. Por favor, verifique a configuração.")
                selected_league = "Nenhuma liga selecionada"
                
            # Nota sobre carregamento
            st.info("Os times são carregados automaticamente ao selecionar uma liga.")
            
            # Separador
            st.markdown("---")
            
            # Botões de navegação
            if st.button("🚀 Ver Pacotes de Créditos", key="packages_button", use_container_width=True):
                st.session_state.page = "packages"
                st.experimental_rerun()
            
            if st.button("Logout", key="logout_btn", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.email = None
                st.session_state.page = "landing"
                st.experimental_rerun()
        
        # CONTEÚDO PRINCIPAL
        # Logo do app
        show_valuehunter_logo()
        
        # Título principal
        st.title("Seleção de Times")
        
        # Indicador de liga
        st.info(f"Liga selecionada: **{selected_league}**", icon="ℹ️")
        
        # Código CSS para mostrar/esconder o botão nativo do Streamlit no mobile
        st.markdown("""
        <style>
        /* Garantir que o botão nativo do Streamlit esteja visível em mobile */
        @media (max-width: 767px) {
            [data-testid="collapsedControl"] {
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                z-index: 10000 !important;
                background-color: #fd7014 !important;
                padding: 10px !important;
                border-radius: 5px !important;
                box-shadow: 0 3px 6px rgba(0,0,0,0.3) !important;
            }
            
            /* Aumentar o tamanho do botão para facilitar o toque */
            [data-testid="collapsedControl"] span {
                font-size: 24px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 36px !important;
                height: 36px !important;
            }
            
            /* Garantir que a sidebar seja visível quando expandida */
            [data-testid="stSidebar"].css-1b50fye {
                width: 300px !important;
                min-width: 300px !important;
                max-width: 300px !important;
            }
        }
        
        /* Em desktop, esconder o botão nativo do Streamlit */
        @media (min-width: 768px) {
            [data-testid="collapsedControl"] {
                display: none !important;
            }
        }
        </style>
        
        <script>
        // Script simples para garantir que o botão do Streamlit esteja sempre visível em mobile
        function ensureButtonVisibility() {
            if (window.innerWidth <= 767) {
                const streamlitButton = document.querySelector('[data-testid="collapsedControl"]');
                if (streamlitButton) {
                    streamlitButton.style.display = 'block';
                    streamlitButton.style.visibility = 'visible';
                    streamlitButton.style.opacity = '1';
                }
            }
        }
        
        // Executar no carregamento e periodicamente
        window.addEventListener('load', ensureButtonVisibility);
        setInterval(ensureButtonVisibility, 1000);
        </script>
        """, unsafe_allow_html=True)
        
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
            # Na seção de seleção de mercados, modifique o código para adicionar o botão "Selecionar todos"
            with st.expander("Mercados Disponíveis", expanded=True):
                st.markdown("### Seleção de Mercados")
                st.info(f"Você tem {user_stats['credits_remaining']} créditos disponíveis. Cada mercado selecionado consumirá 1 crédito.")
                
                # Inicializar o estado para "selecionar todos" se não existir
                if 'select_all_markets' not in st.session_state:
                    st.session_state.select_all_markets = False
                
                # Botão "Selecionar todos"
                if st.button("Selecionar todos os mercados", key="select_all_btn"):
                    st.session_state.select_all_markets = not st.session_state.select_all_markets
                    # Forçar recarregamento da página para atualizar os checkboxes
                    st.experimental_rerun()
                
                # Status atual
                if st.session_state.select_all_markets:
                    st.success("Todos os mercados selecionados! Clique no botão novamente para desmarcar todos.")
                
                col1, col2 = st.columns(2)
                with col1:
                    selected_markets = {
                        "money_line": st.checkbox("Money Line (1X2)", 
                                                 value=st.session_state.select_all_markets, 
                                                 key='ml'),
                        "over_under": st.checkbox("Total de Gols", 
                                                 value=st.session_state.select_all_markets, 
                                                 key='ou'),
                        "chance_dupla": st.checkbox("Chance Dupla", 
                                                   value=st.session_state.select_all_markets, 
                                                   key='cd')
                    }
                with col2:
                    selected_markets.update({
                        "ambos_marcam": st.checkbox("Ambos Marcam", 
                                                   value=st.session_state.select_all_markets, 
                                                   key='btts'),
                        "escanteios": st.checkbox("Total de Escanteios", 
                                                 value=st.session_state.select_all_markets, 
                                                 key='corners'),
                        "cartoes": st.checkbox("Total de Cartões", 
                                              value=st.session_state.select_all_markets, 
                                              key='cards')
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
                    
                    # Obter o ID da liga a partir dos dados estatísticos ou do mapeamento de ligas
                    league_id = None
                    
                    # Primeiro tentar obter do match_info nos dados estatísticos
                    if stats_data and "match_info" in stats_data and "league_id" in stats_data["match_info"]:
                        league_id = stats_data["match_info"]["league_id"]
                    # Se não encontrou, buscar do mapeamento de ligas
                    elif selected_league in LEAGUE_SEASON_IDS:
                        league_id = LEAGUE_SEASON_IDS[selected_league]
                    # Se ainda não encontrou, fazer correspondência parcial
                    else:
                        # Buscar correspondência parcial
                        selected_league_lower = selected_league.lower()
                        for league_name, league_id_value in LEAGUE_SEASON_IDS.items():
                            if league_name.lower() in selected_league_lower or selected_league_lower in league_name.lower():
                                league_id = league_id_value
                                break
                    
                    # Se mesmo assim não encontrou, usar um valor genérico
                    if not league_id:
                        league_id = 'generic'
                    
                    logger.info(f"Usando league_id: {league_id} para {selected_league}")
                    
                    # Primeiro calculamos as probabilidades
                    original_probabilities = calculate_advanced_probabilities(
                        stats_data["home_team"], 
                        stats_data["away_team"],
                        league_id  # Adicionar o ID da liga aqui
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
                        
                        def reconstruct_analysis(analysis_text, home_team, away_team, selected_markets, original_probabilities, implied_probabilities, odds_data):
                            """
                            Reconstrução completa da análise com justificativas detalhadas e formatação adequada.
                            """
                            try:
                                # Logs para depuração
                                print(f"Selected markets: {selected_markets}")
                                print(f"Original probabilities keys: {original_probabilities.keys() if original_probabilities else 'None'}")
                                print(f"Implied probabilities keys: {implied_probabilities.keys() if implied_probabilities else 'None'}")
                                print(f"Odds data: {odds_data}")
                                
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
                                
                                # Over/Under
                                if selected_markets.get("over_under"):
                                    markets_section += "- **Over/Under:**\n"
                                    
                                    # Extrair linha e odds
                                    line_match = re.search(r"Over\s+(\d+\.?\d*)\s+Gols", odds_data)
                                    over_match = re.search(r"Over\s+\d+\.?\d*\s+Gols:.*?@(\d+\.?\d*)", odds_data)
                                    under_match = re.search(r"Under\s+\d+\.?\d*\s+Gols:.*?@(\d+\.?\d*)", odds_data)
                                    
                                    if line_match:
                                        line = float(line_match.group(1))
                                        
                                        if over_match:
                                            over_odd = float(over_match.group(1))
                                            markets_section += f"  - Over {line} Gols: @{over_odd}\n"
                                            implied_probabilities[f"over_{str(line).replace('.', '_')}"] = 100.0 / over_odd
                                        
                                        if under_match:
                                            under_odd = float(under_match.group(1))
                                            markets_section += f"  - Under {line} Gols: @{under_odd}\n"
                                            implied_probabilities[f"under_{str(line).replace('.', '_')}"] = 100.0 / under_odd
                                
                                # Escanteios
                                if selected_markets.get("escanteios"):
                                    markets_section += "- **Escanteios:**\n"
                                    
                                    # Extrair linha e odds
                                    line_match = re.search(r"Over\s+(\d+\.?\d*)\s+Escanteios", odds_data)
                                    over_match = re.search(r"Over\s+\d+\.?\d*\s+Escanteios:.*?@(\d+\.?\d*)", odds_data)
                                    under_match = re.search(r"Under\s+\d+\.?\d*\s+Escanteios:.*?@(\d+\.?\d*)", odds_data)
                                    
                                    if line_match:
                                        line = float(line_match.group(1))
                                        
                                        if over_match:
                                            over_odd = float(over_match.group(1))
                                            markets_section += f"  - Over {line} Escanteios: @{over_odd}\n"
                                            implied_probabilities[f"corners_over_{str(line).replace('.', '_')}"] = 100.0 / over_odd
                                        
                                        if under_match:
                                            under_odd = float(under_match.group(1))
                                            markets_section += f"  - Under {line} Escanteios: @{under_odd}\n"
                                            implied_probabilities[f"corners_under_{str(line).replace('.', '_')}"] = 100.0 / under_odd
                                
                                # Cartões
                                if selected_markets.get("cartoes"):
                                    markets_section += "- **Cartões:**\n"
                                    
                                    # Extrair linha e odds
                                    line_match = re.search(r"Over\s+(\d+\.?\d*)\s+Cartões", odds_data)
                                    over_match = re.search(r"Over\s+\d+\.?\d*\s+Cartões:.*?@(\d+\.?\d*)", odds_data)
                                    under_match = re.search(r"Under\s+\d+\.?\d*\s+Cartões:.*?@(\d+\.?\d*)", odds_data)
                                    
                                    if line_match:
                                        line = float(line_match.group(1))
                                        
                                        if over_match:
                                            over_odd = float(over_match.group(1))
                                            markets_section += f"  - Over {line} Cartões: @{over_odd}\n"
                                            implied_probabilities[f"cards_over_{str(line).replace('.', '_')}"] = 100.0 / over_odd
                                        
                                        if under_match:
                                            under_odd = float(under_match.group(1))
                                            markets_section += f"  - Under {line} Cartões: @{under_odd}\n"
                                            implied_probabilities[f"cards_under_{str(line).replace('.', '_')}"] = 100.0 / under_odd
                                
                                # IMPORTANTE: Adicionar a seção de mercados ao resultado
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
                                        # Adicionar justificativa
                                        home_justification = generate_justification(
                                            "moneyline", "home_win", home_team, home_real, home_implicit,
                                            original_probabilities, home_team, away_team
                                        )
                                    # Empate
                                    draw_real = original_probabilities["moneyline"].get("draw", 0)
                                    draw_implicit = implied_probabilities.get("draw", 0)
                                    draw_value = draw_real > draw_implicit + 2
                                    
                                    probs_section += f"- **Empate**: Real {draw_real:.1f}% vs Implícita {draw_implicit:.1f}%{' (Valor)' if draw_value else ''}\n"
                                    
                                    if draw_value:
                                        # Adicionar justificativa
                                        draw_justification = generate_justification(
                                            "moneyline", "draw", "Empate", draw_real, draw_implicit,
                                            original_probabilities, home_team, away_team
                                        )
                                                                            
                                    # Fora
                                    away_real = original_probabilities["moneyline"].get("away_win", 0)
                                    away_implicit = implied_probabilities.get("away", 0)
                                    away_value = away_real > away_implicit + 2
                                    
                                    probs_section += f"- **{away_team}**: Real {away_real:.1f}% vs Implícita {away_implicit:.1f}%{' (Valor)' if away_value else ''}\n"
                                    
                                    if away_value:
                                        # Adicionar justificativa
                                        away_justification = generate_justification(
                                            "moneyline", "away_win", away_team, away_real, away_implicit,
                                            original_probabilities, home_team, away_team
                                        )
                                                                        
                                # Double Chance
                                if selected_markets.get("chance_dupla") and "double_chance" in original_probabilities:
                                    probs_section += "## Chance Dupla (Double Chance):\n"
                                    
                                    # 1X
                                    hd_real = original_probabilities["double_chance"].get("home_or_draw", 0)
                                    hd_implicit = implied_probabilities.get("home_draw", 0)
                                    hd_value = hd_real > hd_implicit + 2
                                    
                                    probs_section += f"- **{home_team} ou Empate**: Real {hd_real:.1f}% vs Implícita {hd_implicit:.1f}%{' (Valor)' if hd_value else ''}\n"
                                    
                                    if hd_value:
                                        # Adicionar justificativa
                                        hd_justification = generate_justification(
                                            "double_chance", "home_or_draw", f"{home_team} ou Empate", hd_real, hd_implicit,
                                            original_probabilities, home_team, away_team
                                        )
                                                                            
                                    # 12
                                    ha_real = original_probabilities["double_chance"].get("home_or_away", 0)
                                    ha_implicit = implied_probabilities.get("home_away", 0)
                                    ha_value = ha_real > ha_implicit + 2
                                    
                                    probs_section += f"- **{home_team} ou {away_team}**: Real {ha_real:.1f}% vs Implícita {ha_implicit:.1f}%{' (Valor)' if ha_value else ''}\n"
                                    
                                    if ha_value:
                                        # Adicionar justificativa
                                        ha_justification = generate_justification(
                                            "double_chance", "home_or_away", f"{home_team} ou {away_team}", ha_real, ha_implicit,
                                            original_probabilities, home_team, away_team
                                        )
                                                                            
                                    # X2
                                    da_real = original_probabilities["double_chance"].get("away_or_draw", 0)
                                    da_implicit = implied_probabilities.get("draw_away", 0)
                                    da_value = da_real > da_implicit + 2
                                    
                                    probs_section += f"- **Empate ou {away_team}**: Real {da_real:.1f}% vs Implícita {da_implicit:.1f}%{' (Valor)' if da_value else ''}\n"
                                    
                                    if da_value:
                                        # Adicionar justificativa
                                        da_justification = generate_justification(
                                            "double_chance", "away_or_draw", f"Empate ou {away_team}", da_real, da_implicit,
                                            original_probabilities, home_team, away_team
                                        )
                                                                        
                                # BTTS
                                if selected_markets.get("ambos_marcam") and "btts" in original_probabilities:
                                    probs_section += "## Ambos Marcam (BTTS):\n"
                                    
                                    # Sim
                                    yes_real = original_probabilities["btts"].get("yes", 0)
                                    yes_implicit = implied_probabilities.get("btts_yes", 0)
                                    yes_value = yes_real > yes_implicit + 2
                                    
                                    probs_section += f"- **Sim**: Real {yes_real:.1f}% vs Implícita {yes_implicit:.1f}%{' (Valor)' if yes_value else ''}\n"
                                    
                                    if yes_value:
                                        # Adicionar justificativa
                                        yes_justification = generate_justification(
                                            "btts", "yes", "Ambos Marcam - Sim", yes_real, yes_implicit,
                                            original_probabilities, home_team, away_team
                                        )
                                                                            
                                    # Não
                                    no_real = original_probabilities["btts"].get("no", 0)
                                    no_implicit = implied_probabilities.get("btts_no", 0)
                                    no_value = no_real > no_implicit + 2
                                    
                                    probs_section += f"- **Não**: Real {no_real:.1f}% vs Implícita {no_implicit:.1f}%{' (Valor)' if no_value else ''}\n"
                                    
                                    if no_value:
                                        # Adicionar justificativa
                                        no_justification = generate_justification(
                                            "btts", "no", "Ambos Marcam - Não", no_real, no_implicit,
                                            original_probabilities, home_team, away_team
                                        )
                                                                        
                                # Over/Under
                                if selected_markets.get("over_under") and "over_under" in original_probabilities:
                                    probs_section += "## Over/Under Gols:\n"
                                    
                                    # Extrair linha do texto de odds
                                    line_match = re.search(r"Over\s+(\d+\.?\d*)\s+Gols", odds_data)
                                    if line_match:
                                        line = float(line_match.group(1))
                                        line_str = str(line).replace('.', '_')
                                        
                                        # Over
                                        over_real = original_probabilities["over_under"].get("over_2_5", 0)  # Padrão para 2.5
                                        if line == 0.5:
                                            over_real = 90.0  # Aproximação para over 0.5
                                        elif line == 1.5:
                                            over_real = 75.0  # Aproximação para over 1.5
                                        elif line == 3.5:
                                            over_real = 40.0  # Aproximação para over 3.5
                                        elif line == 4.5:
                                            over_real = 25.0  # Aproximação para over 4.5
                                        
                                        over_implicit = implied_probabilities.get(f"over_{line_str}", 0)
                                        over_value = over_real > over_implicit + 2
                                        
                                        probs_section += f"- **Over {line} Gols**: Real {over_real:.1f}% vs Implícita {over_implicit:.1f}%{' (Valor)' if over_value else ''}\n"
                                        
                                        if over_value:
                                            # Adicionar justificativa
                                            over_justification = generate_justification(
                                                "over_under", f"over_{line_str}", f"Over {line} Gols", over_real, over_implicit,
                                                original_probabilities, home_team, away_team
                                            )
                                                                                    
                                        # Under
                                        under_real = 100.0 - over_real
                                        under_implicit = implied_probabilities.get(f"under_{line_str}", 0)
                                        under_value = under_real > under_implicit + 2
                                        
                                        probs_section += f"- **Under {line} Gols**: Real {under_real:.1f}% vs Implícita {under_implicit:.1f}%{' (Valor)' if under_value else ''}\n"
                                        
                                        if under_value:
                                            # Adicionar justificativa
                                            under_justification = generate_justification(
                                                "over_under", f"under_{line_str}", f"Under {line} Gols", under_real, under_implicit,
                                                original_probabilities, home_team, away_team
                                            )
                                                                            
                                # Escanteios
                                if selected_markets.get("escanteios") and "corners" in original_probabilities:
                                    probs_section += "## Escanteios:\n"
                                    
                                    # Extrair linha do texto de odds
                                    line_match = re.search(r"Over\s+(\d+\.?\d*)\s+Escanteios", odds_data)
                                    if line_match:
                                        line = float(line_match.group(1))
                                        line_str = str(line).replace('.', '_')
                                        
                                        # Ajustar as probabilidades reais com base na linha
                                        if line == 9.5:  # Linha padrão
                                            over_real = original_probabilities["corners"].get("over_9_5", 0)
                                        else:
                                            # Ajustes para outras linhas
                                            base_over = original_probabilities["corners"].get("over_9_5", 50)
                                            if line < 9.5:
                                                over_real = min(95, base_over + ((9.5 - line) * 10))  # +10% por cada ponto abaixo de 9.5
                                            else:
                                                over_real = max(5, base_over - ((line - 9.5) * 10))   # -10% por cada ponto acima de 9.5
                                        
                                        over_implicit = implied_probabilities.get(f"corners_over_{line_str}", 0)
                                        over_value = over_real > over_implicit + 2
                                        
                                        probs_section += f"- **Over {line} Escanteios**: Real {over_real:.1f}% vs Implícita {over_implicit:.1f}%{' (Valor)' if over_value else ''}\n"
                                        
                                        if over_value:
                                            # Adicionar justificativa
                                            over_corners_justification = generate_justification(
                                                "corners", f"over_{line_str}", f"Over {line} Escanteios", over_real, over_implicit,
                                                original_probabilities, home_team, away_team
                                            )
                                                                                    
                                        # Under
                                        under_real = 100.0 - over_real
                                        under_implicit = implied_probabilities.get(f"corners_under_{line_str}", 0)
                                        under_value = under_real > under_implicit + 2
                                        
                                        probs_section += f"- **Under {line} Escanteios**: Real {under_real:.1f}% vs Implícita {under_implicit:.1f}%{' (Valor)' if under_value else ''}\n"
                                        
                                        if under_value:
                                            # Adicionar justificativa
                                            under_corners_justification = generate_justification(
                                                "corners", f"under_{line_str}", f"Under {line} Escanteios", under_real, under_implicit,
                                                original_probabilities, home_team, away_team
                                            )
                                                                            
                                # Cartões - Código corrigido para usar expected_cards
                                if selected_markets.get("cartoes") and "cards" in original_probabilities:
                                    probs_section += "## Cartões:\n"
                                    
                                    # Extrair linha e odds do texto
                                    line_match = re.search(r"Over\s+(\d+\.?\d*)\s+Cartões", odds_data)
                                    over_match = re.search(r"Over\s+\d+\.?\d*\s+Cartões:.*?@(\d+\.?\d*)", odds_data)
                                    under_match = re.search(r"Under\s+\d+\.?\d*\s+Cartões:.*?@(\d+\.?\d*)", odds_data)
                                    
                                    if line_match:
                                        line = float(line_match.group(1))
                                        line_str = str(line).replace('.', '_')
                                        
                                        # Extrair e calcular probabilidades implícitas a partir das odds
                                        if over_match:
                                            over_odd = float(over_match.group(1))
                                            # Calcular probabilidade implícita (1/odd * 100)
                                            implied_probabilities[f"cards_over_{line_str}"] = 100.0 / over_odd
                                        
                                        if under_match:
                                            under_odd = float(under_match.group(1))
                                            # Calcular probabilidade implícita (1/odd * 100)
                                            implied_probabilities[f"cards_under_{line_str}"] = 100.0 / under_odd
                                        
                                        # Extrair o expected_cards e usar os valores originais calculados
                                        if "cards" in original_probabilities:
                                            cards_data = original_probabilities["cards"]
                                            
                                            # Se cards_data for uma tupla (over_prob, under_prob, expected_cards)
                                            if isinstance(cards_data, tuple) and len(cards_data) >= 3:
                                                # Usar os valores originais da função calculate_cards_probability
                                                over_real = cards_data[0] * 100
                                                under_real = cards_data[1] * 100
                                                expected_cards = cards_data[2]
                                                
                                                # Se o expected_cards for muito diferente do threshold, garantir valores extremos
                                                if expected_cards > line + 8:  # Muitos cartões
                                                    over_real = 95.0
                                                    under_real = 5.0
                                                elif expected_cards < line - 5:  # Poucos cartões
                                                    over_real = 5.0
                                                    under_real = 95.0
                                                    
                                            # Se cards_data for um dicionário
                                            elif isinstance(cards_data, dict):
                                                if "expected_cards" in cards_data:
                                                    expected_cards = cards_data["expected_cards"]
                                                    
                                                    # Calcular probabilidades com base na distribuição normal
                                                    import math
                                                    std_dev = math.sqrt(expected_cards * 0.75)
                                                    z_score = (line - expected_cards) / std_dev if std_dev > 0 else -5
                                                    
                                                    # Normal CDF para under probability
                                                    def normal_cdf(x):
                                                        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
                                                        
                                                    under_real = normal_cdf(z_score) * 100
                                                    over_real = 100.0 - under_real
                                                
                                                # Se tiver valores específicos para essa linha
                                                elif f"over_{line_str}" in cards_data and f"under_{line_str}" in cards_data:
                                                    over_real = cards_data[f"over_{line_str}"] * 100
                                                    under_real = cards_data[f"under_{line_str}"] * 100
                                                
                                                # Valores gerais se não houver específicos
                                                elif "over" in cards_data and "under" in cards_data:
                                                    over_real = cards_data["over"] * 100
                                                    under_real = cards_data["under"] * 100
                                                
                                                else:
                                                    # Valores padrão se não houver nenhum específico
                                                    over_real = 50.0
                                                    under_real = 50.0
                                            else:
                                                # Valores padrão se cards_data não for nem tupla nem dict
                                                over_real = 50.0
                                                under_real = 50.0
                                                
                                            # Verificação final para garantir que os valores são coerentes
                                            # Se temos logs indicando que o valor esperado é muito alto (>19)
                                            if isinstance(cards_data, dict) and "expected_cards" in cards_data and isinstance(cards_data["expected_cards"], (int, float)):
                                                expected_cards = cards_data["expected_cards"]
                                                # Para um threshold bem menor que o valor esperado, Over deve ser muito alto
                                                if expected_cards > line + 6:
                                                    over_real = max(over_real, 90.0)
                                                    under_real = min(under_real, 10.0)
                                                # Para um threshold bem maior que o valor esperado, Under deve ser muito alto
                                                elif expected_cards + 6 < line:
                                                    over_real = min(over_real, 10.0)
                                                    under_real = max(under_real, 90.0)
                                            elif isinstance(cards_data, tuple) and len(cards_data) >= 3:
                                                expected_cards = cards_data[2]
                                                if expected_cards > line + 6:
                                                    over_real = max(over_real, 90.0)
                                                    under_real = min(under_real, 10.0)
                                                elif expected_cards + 6 < line:
                                                    over_real = min(over_real, 10.0)
                                                    under_real = max(under_real, 90.0)
                                        else:
                                            # Se não houver dados de cards, usar valores neutros
                                            over_real = 50.0
                                            under_real = 50.0
                                        
                                        # Obter probabilidades implícitas das odds
                                        over_implicit = implied_probabilities.get(f"cards_over_{line_str}", 0)
                                        under_implicit = implied_probabilities.get(f"cards_under_{line_str}", 0)
                                        
                                        # Debug: imprimir valores para verificação
                                        print(f"DEBUG - Cartões: over_real={over_real}, over_implicit={over_implicit}, under_real={under_real}, under_implicit={under_implicit}")
                                        
                                        # Verificar valor
                                        over_value = over_real > over_implicit + 2
                                        under_value = under_real > under_implicit + 2
                                        
                                        # Adicionar ao output
                                        probs_section += f"- **Over {line} Cartões**: Real {over_real:.1f}% vs Implícita {over_implicit:.1f}%{' (Valor)' if over_value else ''}\n"
                                        
                                        if over_value:
                                            # Adicionar justificativa
                                            over_cards_justification = generate_justification(
                                                "cards", f"over_{line_str}", f"Over {line} Cartões", over_real, over_implicit,
                                                original_probabilities, home_team, away_team
                                            )
                                                                                    
                                        probs_section += f"- **Under {line} Cartões**: Real {under_real:.1f}% vs Implícita {under_implicit:.1f}%{' (Valor)' if under_value else ''}\n"
                                        
                                        if under_value:
                                            # Adicionar justificativa
                                            under_cards_justification = generate_justification(
                                                "cards", f"under_{line_str}", f"Under {line} Cartões", under_real, under_implicit,
                                                original_probabilities, home_team, away_team
                                            )
                                                                            
                                # CRÍTICO: Adicionar a seção de probabilidades ao resultado
                                new_analysis.append(probs_section)
                                
                                # Oportunidades identificadas# Oportunidades identificadas - usando nossa nova função
                                # Oportunidades identificadas com nossa nova função
                                opportunities_section, value_opportunities = generate_all_opportunities(
                                    selected_markets, 
                                    original_probabilities, 
                                    implied_probabilities, 
                                    home_team, 
                                    away_team, 
                                    odds_data
                                )
                                new_analysis.append(opportunities_section)
                                
                                # Nível de confiança
                                confidence_section = "# Nível de Confiança Geral: Médio\n"
                                
                                # Extrair dados da consistência
                                if "analysis_data" in original_probabilities:
                                    analysis_data = original_probabilities["analysis_data"]
                                    
                                    # Obter consistência dos times
                                    home_consistency = analysis_data.get("home_consistency", 0)
                                    away_consistency = analysis_data.get("away_consistency", 0)
                                    
                                    # Ajustar para valores percentuais se necessário
                                    if home_consistency <= 1.0:
                                        home_consistency = home_consistency * 100
                                    if away_consistency <= 1.0:
                                        away_consistency = away_consistency * 100
                                    
                                    # Adicionar apenas informações de consistência
                                    confidence_section += f"- **Consistência**: {home_team}: {home_consistency:.1f}%, {away_team}: {away_consistency:.1f}%\n"
                                    confidence_section += "- Valores mais altos de consistência indicam maior confiança na previsão."
                                else:
                                    confidence_section += "- Dados insuficientes para determinar a consistência das equipes."
                                
                                new_analysis.append(confidence_section)
                                
                                # Avaliação de viabilidade - APENAS UMA SEÇÃO PARA TODAS AS OPORTUNIDADES
                                viability_section = "# AVALIAÇÃO DE VIABILIDADE DE APOSTAS\n"
                                
                                # Avaliar cada oportunidade com valor
                                if value_opportunities:
                                    for opp in value_opportunities:
                                        name = opp["name"]
                                        real_prob = opp["real_prob"]
                                        edge = opp["edge"]
                                        
                                        # Determinar nível de viabilidade
                                        viability = ""
                                        assessment = ""
                                        recommendation = ""
                                        
                                        if real_prob > 70 and edge > 7:
                                            viability = "🔥🔥🔥 EXCELENTE"
                                            assessment = "Alta probabilidade e grande margem"
                                            recommendation = "Oportunidade excelente para apostar. Considere uma aposta com valor mais alto."
                                        elif real_prob > 60 and edge > 5:
                                            viability = "🔥🔥 MUITO BOA"
                                            assessment = "Boa probabilidade e margem significativa"
                                            recommendation = "Boa oportunidade para apostar. Valor recomendado."
                                        elif real_prob > 50 and edge > 3:
                                            viability = "🔥 BOA"
                                            assessment = "Probabilidade e margem razoáveis"
                                            recommendation = "Considere uma aposta com valor moderado."
                                        else:
                                            viability = "⚠️ RAZOÁVEL"
                                            assessment = "Ou boa probabilidade ou boa margem"
                                            recommendation = "Apostar com cautela e valor reduzido."
                                        
                                        # Adicionar à seção
                                        viability_section += f"## {name} - {viability}\n"
                                        viability_section += f"- Probabilidade: {real_prob:.1f}% | Margem: {edge:.1f}%\n"
                                        viability_section += f"- Avaliação: {assessment}\n"
                                        viability_section += f"- Recomendação: {recommendation}\n"
                                else:
                                    viability_section += "Não foram identificadas oportunidades com valor significativo para avaliação.\n"
                                
                                # Legenda
                                viability_section += "\n# LEGENDA DE VIABILIDADE\n"
                                viability_section += "- 🔥🔥🔥 EXCELENTE: Alta probabilidade (>70%) e grande margem (>7%)\n"
                                viability_section += "- 🔥🔥 MUITO BOA: Boa probabilidade (>60%) e margem significativa (>5%)\n"
                                viability_section += "- 🔥 BOA: Probabilidade e margem razoáveis (>50% e >3%)\n"
                                viability_section += "- ⚠️ RAZOÁVEL: Ou boa probabilidade ou boa margem\n"
                                viability_section += "- ❌ BAIXA: Probabilidade e margem insuficientes\n"
                                
                                new_analysis.append(viability_section)
                                
                                # Avaliar cada oportunidade
                                for opportunity in opportunities:
                                    # Extrair dados
                                    match = re.search(r"\*\*([^*]+)\*\*: Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(Valor de (\d+\.\d+)%\)", opportunity)
                                    if match:
                                        market = match.group(1)
                                        real_prob = float(match.group(2))
                                        implicit_prob = float(match.group(3))
                                        edge = float(match.group(4))
                                        
                                        # Inicializar a seção de viabilidade
                                        viability_section = "# AVALIAÇÃO DE VIABILIDADE DE APOSTAS\n"
                                        
                                        # Determinar nível de viabilidade
                                        viability = ""
                                        assessment = ""
                                        recommendation = ""
                                        
                                        if real_prob > 70 and edge > 7:
                                            viability = "🔥🔥🔥 EXCELENTE"
                                            assessment = "Alta probabilidade e grande margem"
                                            recommendation = "Oportunidade excelente para apostar. Considere uma aposta com valor mais alto."
                                        elif real_prob > 60 and edge > 5:
                                            viability = "🔥🔥 MUITO BOA"
                                            assessment = "Boa probabilidade e margem significativa"
                                            recommendation = "Boa oportunidade para apostar. Valor recomendado."
                                        elif real_prob > 50 and edge > 3:
                                            viability = "🔥 BOA"
                                            assessment = "Probabilidade e margem razoáveis"
                                            recommendation = "Considere uma aposta com valor moderado."
                                        else:
                                            viability = "⚠️ RAZOÁVEL"
                                            assessment = "Ou boa probabilidade ou boa margem"
                                            recommendation = "Apostar com cautela e valor reduzido."
                                        
                                        # Adicionar à seção
                                        viability_section += f"## {market} - {viability}\n"
                                        viability_section += f"- Probabilidade: {real_prob:.1f}% | Margem: {edge:.1f}%\n"
                                        viability_section += f"- Avaliação: {assessment}\n"
                                        viability_section += f"- Recomendação: {recommendation}\n"
                                        
                                        # Legenda
                                        viability_section += "# LEGENDA DE VIABILIDADE\n"
                                        viability_section += "- 🔥🔥🔥 EXCELENTE: Alta probabilidade (>70%) e grande margem (>7%)\n"
                                        viability_section += "- 🔥🔥 MUITO BOA: Boa probabilidade (>60%) e margem significativa (>5%)\n"
                                        viability_section += "- 🔥 BOA: Probabilidade e margem razoáveis (>50% e >3%)\n"
                                        viability_section += "- ⚠️ RAZOÁVEL: Ou boa probabilidade ou boa margem\n"
                                        viability_section += "- ❌ BAIXA: Probabilidade e margem insuficientes\n"
                                        
                                        new_analysis.append(viability_section)
                                # Juntar tudo
                                return "\n".join(new_analysis)
                                
                            except Exception as e:
                                logger.error(f"Erro durante a análise: {str(e)}")
                                logger.error(traceback.format_exc())
                                status.error(f"Erro durante a análise: {str(e)}")
                                if st.session_state.debug_mode:
                                    st.code(traceback.format_exc())
                        
                        # Mostrar análise formatada
                        formatted_analysis = reconstruct_analysis(
                            analysis, 
                            home_team, 
                            away_team, 
                            selected_markets, 
                            original_probabilities, 
                            implied_probabilities, 
                            odds_data
                        )
                        
                        # Exibir a análise formatada
                        st.markdown(formatted_analysis)
                        # IMPORTANTE: Registrar uso após análise bem-sucedida
                        try:
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
                                st.warning("Não foi possível registrar o uso. Por favor verifique seus créditos.")
                        except Exception as usage_error:
                            logger.error(f"Erro ao registrar uso: {str(usage_error)}")
                            logger.error(traceback.format_exc())
                            st.warning("Ocorreu um erro ao contabilizar créditos. Entre em contato com o suporte.")
                        
                except Exception as analysis_error:
                    status.error(f"Erro durante análise: {str(analysis_error)}")
                    logger.error(f"Erro durante análise: {str(analysis_error)}")
                    logger.error(traceback.format_exc())
                    if st.session_state.debug_mode:
                        st.code(traceback.format_exc())
        except Exception as button_error:
            logger.error(f"Erro no botão de análise: {str(button_error)}")
            logger.error(traceback.format_exc())
            st.error(f"Erro no botão de análise: {str(button_error)}")
            if st.session_state.debug_mode:
                st.code(traceback.format_exc())
                
    except Exception as e:
        st.error(f"Erro ao carregar o dashboard: {str(e)}")    
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

# Função de avaliação de oportunidades
def evaluate_opportunity(real_prob, margin):
    """Avalia a qualidade da oportunidade com base na probabilidade e margem"""
    if real_prob >= 70 and margin >= 7:
        return "EXCELENTE", "green", "Alta probabilidade e grande margem"
    elif real_prob >= 60 and margin >= 5:
        return "MUITO BOA", "lightgreen", "Boa probabilidade e margem significativa" 
    elif real_prob >= 50 and margin >= 3:
        return "BOA", "yellow", "Probabilidade e margem razoáveis"
    elif real_prob >= 60 or margin >= 5:
        return "RAZOÁVEL", "orange", "Ou boa probabilidade ou boa margem"
    else:
        return "BAIXA", "red", "Probabilidade e margem insuficientes"

# Função para adicionar a avaliação ao final da análise
def add_opportunity_evaluation(analysis_text):
    """
    Adiciona uma avaliação das oportunidades ao final do texto de análise
    
    Args:
        analysis_text (str): O texto da análise original
        
    Returns:
        str: Texto da análise com a avaliação adicionada
    """
    import re
    
    # Extrair as oportunidades com regex
    pattern = r"\*\*([^*]+)\*\*: Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(Valor de (\d+\.\d+)%\)"
    matches = re.findall(pattern, analysis_text)
    
    if not matches:
        # Se não encontrar oportunidades no formato esperado, tente outro padrão
        pattern = r"\- \*\*([^*]+)\*\*: Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(Valor de (\d+\.\d+)%\)"
        matches = re.findall(pattern, analysis_text)
        
    if not matches:
        # Tente um padrão mais genérico como último recurso
        pattern = r"([^-:]+): Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(?Valor de (\d+\.\d+)%\)?"
        matches = re.findall(pattern, analysis_text)
    
    # Se ainda não encontrou oportunidades, retorna o texto original
    if not matches:
        return analysis_text
    
    # Adicionar a seção de avaliação de oportunidades
    evaluation_text = "\n\n# AVALIAÇÃO DE VIABILIDADE DE APOSTAS\n"
    
    for match in matches:
        opportunity_name, real_prob_str, implicit_prob_str, margin_str = match
        
        try:
            # Converter para números
            real_prob = float(real_prob_str)
            margin = float(margin_str)
            
            # Avaliar a oportunidade
            rating, description = evaluate_opportunity(real_prob, margin)
            
            # Formatar classificação com símbolos
            rating_symbol = {
                "EXCELENTE": "🔥🔥🔥",
                "MUITO BOA": "🔥🔥",
                "BOA": "🔥",
                "RAZOÁVEL": "⚠️",
                "BAIXA": "❌"
            }.get(rating, "")
            
            # Adicionar à saída
            evaluation_text += f"\n## {opportunity_name.strip()} - {rating_symbol} {rating}\n"
            evaluation_text += f"- Probabilidade: {real_prob:.1f}% | Margem: {margin:.1f}%\n"
            evaluation_text += f"- Avaliação: {description}\n"
            
            # Adicionar recomendações específicas com base na classificação
            if rating == "EXCELENTE":
                evaluation_text += "- Recomendação: Oportunidade excelente para apostar. Considere uma aposta com valor mais alto.\n"
            elif rating == "MUITO BOA":
                evaluation_text += "- Recomendação: Boa oportunidade para apostar. Valor recomendado.\n"
            elif rating == "BOA":
                evaluation_text += "- Recomendação: Oportunidade viável para apostar com moderação.\n"
            elif rating == "RAZOÁVEL":
                evaluation_text += "- Recomendação: Apostar com cautela e valor reduzido.\n"
            else:
                evaluation_text += "- Recomendação: Não recomendamos esta aposta. Valor baixo detectado.\n"
            
        except (ValueError, TypeError):
            continue
    
    # Adicionar legenda
    evaluation_text += "\n# LEGENDA DE VIABILIDADE\n"
    evaluation_text += "- 🔥🔥🔥 EXCELENTE: Alta probabilidade (>70%) e grande margem (>7%)\n"
    evaluation_text += "- 🔥🔥 MUITO BOA: Boa probabilidade (>60%) e margem significativa (>5%)\n"
    evaluation_text += "- 🔥 BOA: Probabilidade e margem razoáveis (>50% e >3%)\n"
    evaluation_text += "- ⚠️ RAZOÁVEL: Ou boa probabilidade ou boa margem\n"
    evaluation_text += "- ❌ BAIXA: Probabilidade e margem insuficientes\n"
    
    # Retornar o texto original + a avaliação
    return analysis_text + evaluation_text

# Função alternativa caso os emojis não funcionem bem
def add_opportunity_evaluation_simple(analysis_text):
    """
    Versão sem emojis, caso eles não funcionem bem na sua implementação
    """
    import re
    
    # Extrair as oportunidades com regex
    pattern = r"\*\*([^*]+)\*\*: Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(Valor de (\d+\.\d+)%\)"
    matches = re.findall(pattern, analysis_text)
    
    if not matches:
        # Se não encontrar oportunidades no formato esperado, tente outro padrão
        pattern = r"\- \*\*([^*]+)\*\*: Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(Valor de (\d+\.\d+)%\)"
        matches = re.findall(pattern, analysis_text)
        
    if not matches:
        # Tente um padrão mais genérico como último recurso
        pattern = r"([^-:]+): Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(?Valor de (\d+\.\d+)%\)?"
        matches = re.findall(pattern, analysis_text)
    
    # Se ainda não encontrou oportunidades, retorna o texto original
    if not matches:
        return analysis_text
    
    # Adicionar a seção de avaliação de oportunidades
    evaluation_text = "\n\n# AVALIAÇÃO DE VIABILIDADE DE APOSTAS\n"
    
    for match in matches:
        opportunity_name, real_prob_str, implicit_prob_str, margin_str = match
        
        try:
            # Converter para números
            real_prob = float(real_prob_str)
            margin = float(margin_str)
            
            # Avaliar a oportunidade
            rating, description = evaluate_opportunity(real_prob, margin)
            
            # Formatar classificação com símbolos
            rating_symbol = {
                "EXCELENTE": "***",
                "MUITO BOA": "**",
                "BOA": "*",
                "RAZOÁVEL": "!",
                "BAIXA": "X"
            }.get(rating, "")
            
            # Adicionar à saída
            evaluation_text += f"\n## {opportunity_name.strip()} - {rating_symbol} {rating}\n"
            evaluation_text += f"- Probabilidade: {real_prob:.1f}% | Margem: {margin:.1f}%\n"
            evaluation_text += f"- Avaliação: {description}\n"
            
            # Adicionar recomendações específicas com base na classificação
            if rating == "EXCELENTE":
                evaluation_text += "- Recomendação: Oportunidade excelente para apostar. Considere uma aposta com valor mais alto.\n"
            elif rating == "MUITO BOA":
                evaluation_text += "- Recomendação: Boa oportunidade para apostar. Valor recomendado.\n"
            elif rating == "BOA":
                evaluation_text += "- Recomendação: Oportunidade viável para apostar com moderação.\n"
            elif rating == "RAZOÁVEL":
                evaluation_text += "- Recomendação: Apostar com cautela e valor reduzido.\n"
            else:
                evaluation_text += "- Recomendação: Não recomendamos esta aposta. Valor baixo detectado.\n"
            
        except (ValueError, TypeError):
            continue
    
    # Adicionar legenda
    evaluation_text += "\n# LEGENDA DE VIABILIDADE\n"
    evaluation_text += "- *** EXCELENTE: Alta probabilidade (>70%) e grande margem (>7%)\n"
    evaluation_text += "- ** MUITO BOA: Boa probabilidade (>60%) e margem significativa (>5%)\n"
    evaluation_text += "- * BOA: Probabilidade e margem razoáveis (>50% e >3%)\n"
    evaluation_text += "- ! RAZOÁVEL: Ou boa probabilidade ou boa margem\n"
    evaluation_text += "- X BAIXA: Probabilidade e margem insuficientes\n"
    
    # Retornar o texto original + a avaliação
    return analysis_text + evaluation_text


# Função para mostrar o indicador visual da oportunidade usando componentes do Streamlit
def show_opportunity_indicator_native(real_prob, margin, opportunity_name):
    """
    Mostra um indicador visual da qualidade da oportunidade usando componentes nativos do Streamlit
    
    Args:
        real_prob (float): Probabilidade real (0-100)
        margin (float): Margem (diferença entre prob real e implícita)
        opportunity_name (str): Nome da oportunidade/mercado
    """
    rating, color, description = evaluate_opportunity(real_prob, margin)
    
    # Mapear cores para cores do Streamlit
    color_map = {
        "green": "success",
        "lightgreen": "success",
        "yellow": "warning",
        "orange": "warning",
        "red": "error"
    }
    
    st_color = color_map.get(color, "primary")
    
    # Criar um container com bordas para o indicador
    with st.container():
        # Título da oportunidade
        st.subheader(opportunity_name)
        
        # Mostrar probabilidade com barra de progresso
        col1, col2 = st.columns([1, 3])
        with col1:
            st.write("Probabilidade:")
        with col2:
            st.progress(min(1.0, real_prob/100))
            st.write(f"{real_prob:.1f}%")
        
        # Mostrar margem com barra de progresso
        col1, col2 = st.columns([1, 3])
        with col1:
            st.write("Margem:")
        with col2:
            # Escalar a margem para melhor visualização (máximo considerado: 20%)
            st.progress(min(1.0, margin/20))
            st.write(f"{margin:.1f}%")
            
        # Mostrar classificação e descrição
        if st_color == "success":
            st.success(f"**Classificação: {rating}** - {description}")
        elif st_color == "warning":
            st.warning(f"**Classificação: {rating}** - {description}")
        elif st_color == "error":
            st.error(f"**Classificação: {rating}** - {description}")
        else:
            st.info(f"**Classificação: {rating}** - {description}")
            
        # Adicionar uma linha divisória
        st.markdown("---")

# Função modificada para extrair oportunidades identificadas e mostrar indicadores
def extract_and_show_opportunities_native(analysis_text):
    """
    Extrai oportunidades do texto de análise e mostra indicadores visuais
    usando apenas componentes nativos do Streamlit
    
    Args:
        analysis_text (str): Texto da análise
    """
    import re
    
    # Procurar a seção de Oportunidades Identificadas
    opportunities_section = None
    sections = analysis_text.split("#")
    
    for section in sections:
        if "Oportunidades Identificadas" in section:
            opportunities_section = section
            break
    
    if not opportunities_section:
        st.warning("Não foi possível encontrar oportunidades na análise.")
        return
    
    # Extrair oportunidades individuais
    opportunities = []
    
    # Padrão de regex para capturar: nome, probabilidade real, implícita e margem
    pattern = r"\*\*(.*?)\*\*: Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(Valor de (\d+\.\d+)%\)"
    
    matches = re.findall(pattern, opportunities_section)
    
    if not matches:
        st.warning("Nenhuma oportunidade específica encontrada na análise.")
        return
    
    # Mostrar cabeçalho
    st.markdown("## Indicadores de Oportunidades")
    st.markdown("Analise as oportunidades identificadas e suas classificações:")
    
    # Criar indicador para cada oportunidade
    for match in matches:
        opportunity_name, real_prob_str, implicit_prob_str, margin_str = match
        
        try:
            real_prob = float(real_prob_str)
            margin = float(margin_str)
            
            # Mostrar indicador usando componentes nativos
            show_opportunity_indicator_native(real_prob, margin, opportunity_name)
        except (ValueError, TypeError) as e:
            st.error(f"Erro ao processar oportunidade: {e}")
            continue
    
    # Adicionar legenda explicativa
    with st.expander("Legenda de Classificação", expanded=False):
        st.markdown("""
        ### Como interpretar as classificações:
        
        - **Excelente**: Alta probabilidade (>70%) e grande margem (>7%) - Oportunidade ideal para apostar
        - **Muito Boa**: Boa probabilidade (>60%) e margem significativa (>5%) - Forte recomendação
        - **Boa**: Probabilidade e margem razoáveis (>50% e >3%) - Recomendação moderada
        - **Razoável**: Ou boa probabilidade ou boa margem - Considerar com cautela
        - **Baixa**: Probabilidade e margem insuficientes - Não recomendado
        
        *A probabilidade indica a chance do evento acontecer, enquanto a margem representa a diferença entre a probabilidade real e a implícita nas odds.*
        """)

# Alternativa usando apenas texto formatado (sem elementos visuais)
def show_opportunities_text_only(analysis_text):
    """
    Versão alternativa que usa apenas texto formatado, sem elementos visuais do Streamlit
    
    Args:
        analysis_text (str): Texto da análise
    """
    import re
    
    # Procurar a seção de Oportunidades Identificadas
    opportunities_section = None
    sections = analysis_text.split("#")
    
    for section in sections:
        if "Oportunidades Identificadas" in section:
            opportunities_section = section
            break
    
    if not opportunities_section:
        st.write("Não foi possível encontrar oportunidades na análise.")
        return
    
    # Extrair oportunidades individuais
    pattern = r"\*\*(.*?)\*\*: Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(Valor de (\d+\.\d+)%\)"
    matches = re.findall(pattern, opportunities_section)
    
    if not matches:
        st.write("Nenhuma oportunidade específica encontrada na análise.")
        return
    
    # Preparar o texto de saída
    output_text = "## AVALIAÇÃO DE OPORTUNIDADES\n\n"
    
    for match in matches:
        opportunity_name, real_prob_str, implicit_prob_str, margin_str = match
        
        try:
            real_prob = float(real_prob_str)
            margin = float(margin_str)
            
            # Avaliar a oportunidade
            rating, _, description = evaluate_opportunity(real_prob, margin)
            
            # Formatar classificação com símbolos
            rating_symbol = {
                "Excelente": "🔥🔥🔥",
                "Muito Boa": "🔥🔥",
                "Boa": "🔥",
                "Razoável": "⚠️",
                "Baixa": "❌"
            }.get(rating, "")
            
            # Adicionar à saída
            output_text += f"### {opportunity_name} {rating_symbol}\n"
            output_text += f"- Probabilidade: {real_prob:.1f}% | Margem: {margin:.1f}%\n"
            output_text += f"- Classificação: **{rating}** - {description}\n\n"
            
        except (ValueError, TypeError):
            continue
    
    # Adicionar legenda
    output_text += "### Legenda:\n"
    output_text += "- 🔥🔥🔥 Excelente: Alta probabilidade (>70%) e grande margem (>7%)\n"
    output_text += "- 🔥🔥 Muito Boa: Boa probabilidade (>60%) e margem significativa (>5%)\n"
    output_text += "- 🔥 Boa: Probabilidade e margem razoáveis (>50% e >3%)\n"
    output_text += "- ⚠️ Razoável: Ou boa probabilidade ou boa margem\n"
    output_text += "- ❌ Baixa: Probabilidade e margem insuficientes\n"
    
    # Mostrar o texto
    st.markdown(output_text)

# Versão ultra minimalista usando apenas texto simples (sem markdown)
def show_opportunities_ultra_simple(analysis_text):
    """
    Versão ultra minimalista que usa apenas texto simples
    
    Args:
        analysis_text (str): Texto da análise
    """
    import re
    
    # Extrair oportunidades diretamente do texto completo
    pattern = r"\*\*(.*?)\*\*: Real (\d+\.\d+)% vs Implícita (\d+\.\d+)% \(Valor de (\d+\.\d+)%\)"
    matches = re.findall(pattern, analysis_text)
    
    if not matches:
        return
    
    # Adicionar as avaliações como texto puro após a análise
    new_text = analysis_text + "\n\n"
    new_text += "# AVALIAÇÃO DE OPORTUNIDADES\n\n"
    
    for match in matches:
        opportunity_name, real_prob_str, implicit_prob_str, margin_str = match
        
        try:
            real_prob = float(real_prob_str)
            margin = float(margin_str)
            
            # Avaliar a oportunidade
            rating, _, description = evaluate_opportunity(real_prob, margin)
            
            # Formatar classificação com símbolos
            rating_symbol = {
                "Excelente": "***",
                "Muito Boa": "**",
                "Boa": "*",
                "Razoável": "!",
                "Baixa": "X"
            }.get(rating, "")
            
            # Adicionar à saída
            new_text += f"{rating_symbol} {opportunity_name}\n"
            new_text += f"- Probabilidade: {real_prob:.1f}% | Margem: {margin:.1f}%\n"
            new_text += f"- Classificação: {rating} - {description}\n\n"
            
        except (ValueError, TypeError):
            continue
    
    # Adicionar legenda
    new_text += "Legenda:\n"
    new_text += "*** Excelente: Alta probabilidade (>70%) e grande margem (>7%)\n"
    new_text += "** Muito Boa: Boa probabilidade (>60%) e margem significativa (>5%)\n"
    new_text += "* Boa: Probabilidade e margem razoáveis (>50% e >3%)\n"
    new_text += "! Razoável: Ou boa probabilidade ou boa margem\n"
    new_text += "X Baixa: Probabilidade e margem insuficientes\n"
    
    return new_text
def format_text_for_display(text, max_width=70):
    """
    Formata um texto para garantir que nenhuma linha exceda o comprimento máximo especificado.
    
    Args:
        text (str): Texto a ser formatado
        max_width (int): Largura máxima de cada linha em caracteres
        
    Returns:
        str: Texto formatado com quebras de linha
    """
    lines = []
    for line in text.split('\n'):
        if len(line) <= max_width:
            lines.append(line)
        else:
            # Quebrar linhas muito longas
            current_line = ""
            words = line.split()
            
            for word in words:
                if len(current_line) + len(word) + 1 <= max_width:
                    # Adicionar palavra à linha atual
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
                else:
                    # Iniciar nova linha
                    lines.append(current_line)
                    current_line = word
            
            # Adicionar a última linha
            if current_line:
                lines.append(current_line)
    
    return '\n'.join(lines)

def update_opportunities_format(opportunities_section):
    """
    Atualiza a formatação da seção de oportunidades para evitar linhas muito longas
    que exijam rolagem horizontal e preserva a primeira letra das justificativas.
    
    Args:
        opportunities_section (str): Texto da seção de oportunidades
        
    Returns:
        str: Texto reformatado para limitar a largura
    """
    # Dividir o texto em linhas
    lines = opportunities_section.split('\n')
    formatted_lines = []
    
    # Largura máxima por linha (ajuste conforme necessário)
    max_width = 70
    
    for line in lines:
        # Se a linha for uma oportunidade (começa com '- **')
        if line.startswith('- **'):
            # Manter a primeira linha como está (título da oportunidade)
            formatted_lines.append(line)
        # Se for uma justificativa (contém "*Justificativa:")
        elif '*Justificativa:' in line:
            # Verificar se já está dividida em múltiplas linhas
            if '\n' in line:
                # Já está formatada, adicionar todas as linhas
                formatted_lines.extend(line.split('\n'))
            else:
                # Dividir em prefixo e conteúdo, preservando a primeira letra
                parts = line.split('*Justificativa:', 1)
                prefix = parts[0] + "*Justificativa:"
                content = parts[1].strip() if len(parts) > 1 else ""
                
                # Formatar o conteúdo da justificativa
                if content:
                    # Palavra por palavra para garantir que nenhuma letra seja perdida
                    words = content.split()
                    current_line = prefix + " " + words[0]  # Garantir que a primeira palavra esteja completa
                    
                    for word in words[1:]:
                        # Se adicionar a palavra não ultrapassar a largura máxima
                        if len(current_line) + len(word) + 1 <= max_width:
                            # Adicionar palavra à linha atual
                            current_line += " " + word
                        else:
                            # Adicionar a linha atual e começar uma nova
                            formatted_lines.append(current_line)
                            # Alinhar a nova linha com a justificativa (espaços antes)
                            current_line = "    " + word
                    
                    # Adicionar a última linha da justificativa
                    if current_line:
                        formatted_lines.append(current_line)
                else:
                    # Se não houver conteúdo, adicionar apenas o prefixo
                    formatted_lines.append(prefix)
        else:
            # Outras linhas são mantidas como estão
            formatted_lines.append(line)
    
    # Juntar as linhas formatadas
    return '\n'.join(formatted_lines)


def apply_responsive_sidebar_css():
    """
    Aplica CSS responsivo à sidebar para adaptação entre desktop e mobile,
    com uma solução simplificada e direta que foca no funcionamento.
    """
    import streamlit as st
    
    st.markdown("""
    <style>
        /* Estilos básicos para a sidebar */
        [data-testid="stSidebar"] {
            background-color: #27272a;
            border-right: 1px solid #3a3a3a;
        }
        
        /* Botão de menu simplificado para mobile */
        #mobile-menu-button {
            position: fixed;
            top: 10px;
            right: 10px;
            width: 42px;
            height: 42px;
            background-color: #fd7014;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
        
        /* Ocultar botão em desktop */
        @media (min-width: 768px) {
            #mobile-menu-button {
                display: none;
            }
        }
        
        /* Mostrar botão apenas em mobile */
        @media (max-width: 767px) {
            #mobile-menu-button {
                display: flex;
            }
            
            /* Ajuste para texto de ajuda em mobile */
            .mobile-help {
                display: block;
                background-color: rgba(253, 112, 20, 0.2);
                border: 1px solid #fd7014;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 15px;
                font-size: 14px;
            }
        }
        
        /* Ocultar texto de ajuda em desktop */
        @media (min-width: 768px) {
            .mobile-help {
                display: none;
            }
        }
    </style>
    
    <!-- Botão mobile simplificado -->
    <button id="mobile-menu-button">≡</button>
    
    <script>
        // Função simples que encontra e clica no botão de toggle da sidebar do Streamlit
        function setupSimpleMobileButton() {
            const mobileButton = document.getElementById('mobile-menu-button');
            
            if (mobileButton) {
                mobileButton.onclick = function() {
                    // Encontrar o botão de toggle original do Streamlit
                    const streamlitToggle = document.querySelector('[data-testid="collapsedControl"]');
                    
                    if (streamlitToggle) {
                        // Simular o clique no botão do Streamlit
                        streamlitToggle.click();
                    }
                };
            }
        }
        
        // Executar ao carregar
        document.addEventListener('DOMContentLoaded', setupSimpleMobileButton);
        
        // Executar agora também
        setupSimpleMobileButton();
        
        // E executar após meio segundo para garantir
        setTimeout(setupSimpleMobileButton, 500);
        setTimeout(setupSimpleMobileButton, 1000);
        setTimeout(setupSimpleMobileButton, 2000);
    </script>
    """, unsafe_allow_html=True)

# Complemento: Adicione esta função ao dashboard.py para forçar a sidebar a estar sempre disponível
def ensure_sidebar_visibility():
    """
    Força a sidebar a estar sempre disponível em telas mobile,
    independente da orientação. Chame esta função após apply_responsive_sidebar_css().
    """
    import streamlit as st
    
    st.markdown("""
    <script>
        // Função que garante que a sidebar está acessível
        function forceSidebarAccessibility() {
            // Verificar se estamos em mobile
            const isMobile = window.innerWidth <= 767;
            
            if (isMobile) {
                const sidebar = document.querySelector('[data-testid="stSidebar"]');
                const sidebarBtn = document.querySelector('[data-testid="collapsedControl"]');
                
                if (sidebar) {
                    // Garantir que a sidebar não tenha transformações que a ocultem completamente
                    sidebar.style.transition = 'transform 0.3s ease, width 0.3s ease, margin 0.3s ease';
                    
                    // Verificar se a sidebar está visível
                    const isVisible = window.getComputedStyle(sidebar).transform !== 'matrix(1, 0, 0, 1, -100, 0)' &&
                                      window.getComputedStyle(sidebar).width !== '0px';
                    
                    // Se a sidebar não estiver visível, garantir que o botão está
                    if (!isVisible && sidebarBtn) {
                        sidebarBtn.style.display = 'block';
                        sidebarBtn.style.opacity = '1';
                        sidebarBtn.style.visibility = 'visible';
                    }
                    
                    // Verificar se o nosso botão personalizado está visível
                    const mobileBtn = document.getElementById('mobile-menu-btn');
                    if (mobileBtn) {
                        mobileBtn.style.display = 'flex';
                    }
                }
            }
        }
        
        // Executar várias vezes para garantir que seja aplicado
        setInterval(forceSidebarAccessibility, 1000);
        
        // Também executar em carregamento e redimensionamento
        window.addEventListener('load', forceSidebarAccessibility);
        window.addEventListener('resize', forceSidebarAccessibility);
    </script>
    """, unsafe_allow_html=True)
    
def generate_justification(market_type, bet_type, team_name, real_prob, implied_prob, 
                         original_probabilities, home_team, away_team):
    """
    Versão modificada que retorna string vazia, eliminando justificativas
    """
    return ""  # Retorna string vazia em vez de gerar justificativas
    
def fix_sidebar_animation():
    """
    Corrige o problema de animação da sidebar durante o carregamento,
    eliminando o efeito de "movimento" indesejado.
    """
    st.markdown("""
    <style>
        /* Desabilitar completamente as animações da sidebar */
        [data-testid="stSidebar"] {
            transition: none !important;
            animation: none !important;
            transform: none !important;
        }
        
        /* Garantir que a sidebar tenha uma largura fixa e não se redimensione */
        [data-testid="stSidebar"][aria-expanded="true"] {
            width: 300px !important;
            margin-left: 0px !important;
        }
        
        /* Quando colapsada, garantir que fique completamente fora da tela */
        [data-testid="stSidebar"][aria-expanded="false"] {
            width: 300px !important;
            margin-left: -300px !important;
        }
        
        /* Desabilitar animações do botão de toggle também */
        [data-testid="collapsedControl"] {
            transition: none !important;
            animation: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
def fix_mobile_dropdown_colors():
    """
    Aplica estilos específicos para corrigir a cor dos dropdowns em dispositivos móveis.
    """
    st.markdown("""
    <style>
    /* Correção para dropdowns no mobile */
    [data-baseweb="select"],
    [data-baseweb="select"] div,
    [data-baseweb="select"] span,
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"],
    [role="option"] {
        background-color: #2d2d2d !important;
        color: white !important;
    }
    
    /* Melhor seleção para dispositivos móveis */
    @media (max-width: 767px) {
        div[role="listbox"],
        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        div[data-baseweb="select"] ul,
        div[data-baseweb="select"] li,
        [role="option"] {
            background-color: #2d2d2d !important;
            color: white !important;
        }
        
        /* Garantir que rótulos de selectbox sejam visíveis */
        label span {
            color: white !important;
        }
        
        /* Cor de fundo do dropdown quando aberto no mobile */
        [data-baseweb="popover"],
        [data-baseweb="popover"] [role="listbox"] {
            background-color: #2d2d2d !important;
            border: 1px solid #4d4d4d !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
def remove_top_whitespace():
    """
    Remove completamente qualquer espaço em branco no topo da página
    usando abordagem mais agressiva com !important em todos os seletores.
    """
    st.markdown("""
    <style>
    /* Abordagem agressiva para remover QUALQUER espaço no topo */
    
    /* 1. Remover padding/margin do container principal */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    
    /* 2. Forçar todos os elementos no topo a não terem margem */
    .main > div:first-child,
    .main .block-container > div:first-child,
    .element-container:first-child,
    .stMarkdown:first-child,
    section.main > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* 3. Ocultar cabeçalho completamente */
    header[data-testid="stHeader"],
    header.css-18ni7ap.e8zbici2,
    .css-18ni7ap.e8zbici2,
    [data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"] {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        visibility: hidden !important;
        position: absolute !important;
        z-index: -1000 !important;
    }
    
    /* 4. Forçar elementos a começarem imediatamente */
    .stApp {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* 5. Ocultar decorações no topo */
    .stApp::before,
    .stApp > div:first-child,
    .stApp > div:first-child > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
        min-height: 0 !important;
    }
    
    /* 6. Reset de layout para eliminação de gaps */
    section.main,
    .stApp [data-testid="stAppViewContainer"] > section,
    .stApp [data-testid="stAppViewContainer"],
    .stApp [data-testid="stAppViewContainer"] > div,
    .stApp [data-testid="stAppViewContainer"] > div > div {
        margin-top: 0 !important;
        padding-top: 0 !important;
        gap: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
def generate_all_opportunities(selected_markets, original_probabilities, implied_probabilities, 
                              home_team, away_team, odds_data):
    """
    Gera apenas as oportunidades com valor para os mercados selecionados.
    
    Returns:
        tuple: (texto_oportunidades, lista_oportunidades_valor)
    """
    import re
    
    # Lista para armazenar oportunidades com valor
    value_opportunities = []
    valid_opportunities = []  # Para armazenar textos das oportunidades com valor
    
    # 1. Money Line (se selecionado)
    if selected_markets.get("money_line") and "moneyline" in original_probabilities:
        # Casa
        home_real = original_probabilities["moneyline"].get("home_win", 0)
        home_implicit = implied_probabilities.get("home", 0)
        home_edge = home_real - home_implicit
        if home_edge > 2:
            opp_text = f"- **{home_team}**: Real {home_real:.1f}% vs Implícita {home_implicit:.1f}% (Valor de {home_edge:.1f}%)"
            valid_opportunities.append(("Money Line (1X2)", opp_text))
            value_opportunities.append({
                "name": f"{home_team}",
                "market": "Money Line",
                "real_prob": home_real,
                "implied_prob": home_implicit,
                "edge": home_edge
            })
        
        # Empate
        draw_real = original_probabilities["moneyline"].get("draw", 0)
        draw_implicit = implied_probabilities.get("draw", 0)
        draw_edge = draw_real - draw_implicit
        if draw_edge > 2:
            opp_text = f"- **Empate**: Real {draw_real:.1f}% vs Implícita {draw_implicit:.1f}% (Valor de {draw_edge:.1f}%)"
            valid_opportunities.append(("Money Line (1X2)", opp_text))
            value_opportunities.append({
                "name": "Empate",
                "market": "Money Line",
                "real_prob": draw_real,
                "implied_prob": draw_implicit,
                "edge": draw_edge
            })
        
        # Fora
        away_real = original_probabilities["moneyline"].get("away_win", 0)
        away_implicit = implied_probabilities.get("away", 0)
        away_edge = away_real - away_implicit
        if away_edge > 2:
            opp_text = f"- **{away_team}**: Real {away_real:.1f}% vs Implícita {away_implicit:.1f}% (Valor de {away_edge:.1f}%)"
            valid_opportunities.append(("Money Line (1X2)", opp_text))
            value_opportunities.append({
                "name": f"{away_team}",
                "market": "Money Line",
                "real_prob": away_real,
                "implied_prob": away_implicit,
                "edge": away_edge
            })
    
    # 2. Chance Dupla (se selecionado)
    if selected_markets.get("chance_dupla") and "double_chance" in original_probabilities:
        # 1X
        hd_real = original_probabilities["double_chance"].get("home_or_draw", 0)
        hd_implicit = implied_probabilities.get("home_draw", 0)
        hd_edge = hd_real - hd_implicit
        if hd_edge > 2:
            opp_text = f"- **{home_team} ou Empate**: Real {hd_real:.1f}% vs Implícita {hd_implicit:.1f}% (Valor de {hd_edge:.1f}%)"
            valid_opportunities.append(("Chance Dupla", opp_text))
            value_opportunities.append({
                "name": f"{home_team} ou Empate",
                "market": "Chance Dupla",
                "real_prob": hd_real,
                "implied_prob": hd_implicit,
                "edge": hd_edge
            })
        
        # 12
        ha_real = original_probabilities["double_chance"].get("home_or_away", 0)
        ha_implicit = implied_probabilities.get("home_away", 0)
        ha_edge = ha_real - ha_implicit
        if ha_edge > 2:
            opp_text = f"- **{home_team} ou {away_team}**: Real {ha_real:.1f}% vs Implícita {ha_implicit:.1f}% (Valor de {ha_edge:.1f}%)"
            valid_opportunities.append(("Chance Dupla", opp_text))
            value_opportunities.append({
                "name": f"{home_team} ou {away_team}",
                "market": "Chance Dupla",
                "real_prob": ha_real,
                "implied_prob": ha_implicit,
                "edge": ha_edge
            })
        
        # X2
        da_real = original_probabilities["double_chance"].get("away_or_draw", 0)
        da_implicit = implied_probabilities.get("draw_away", 0)
        da_edge = da_real - da_implicit
        if da_edge > 2:
            opp_text = f"- **Empate ou {away_team}**: Real {da_real:.1f}% vs Implícita {da_implicit:.1f}% (Valor de {da_edge:.1f}%)"
            valid_opportunities.append(("Chance Dupla", opp_text))
            value_opportunities.append({
                "name": f"Empate ou {away_team}",
                "market": "Chance Dupla",
                "real_prob": da_real,
                "implied_prob": da_implicit,
                "edge": da_edge
            })
    
    # 3. Ambos Marcam (se selecionado)
    if selected_markets.get("ambos_marcam") and "btts" in original_probabilities:
        # Sim
        yes_real = original_probabilities["btts"].get("yes", 0)
        yes_implicit = implied_probabilities.get("btts_yes", 0)
        yes_edge = yes_real - yes_implicit
        if yes_edge > 2:
            opp_text = f"- **Sim**: Real {yes_real:.1f}% vs Implícita {yes_implicit:.1f}% (Valor de {yes_edge:.1f}%)"
            valid_opportunities.append(("Ambos Marcam (BTTS)", opp_text))
            value_opportunities.append({
                "name": "Ambos Marcam - Sim",
                "market": "BTTS",
                "real_prob": yes_real,
                "implied_prob": yes_implicit,
                "edge": yes_edge
            })
        
        # Não
        no_real = original_probabilities["btts"].get("no", 0)
        no_implicit = implied_probabilities.get("btts_no", 0)
        no_edge = no_real - no_implicit
        if no_edge > 2:
            opp_text = f"- **Não**: Real {no_real:.1f}% vs Implícita {no_implicit:.1f}% (Valor de {no_edge:.1f}%)"
            valid_opportunities.append(("Ambos Marcam (BTTS)", opp_text))
            value_opportunities.append({
                "name": "Ambos Marcam - Não",
                "market": "BTTS",
                "real_prob": no_real,
                "implied_prob": no_implicit,
                "edge": no_edge
            })
    
    # 4. Over/Under (se selecionado)
    if selected_markets.get("over_under") and "over_under" in original_probabilities:
        # Extrair linha do texto de odds
        line_match = re.search(r"Over\s+(\d+\.?\d*)\s+Gols", odds_data)
        if line_match:
            line = float(line_match.group(1))
            line_str = str(line).replace('.', '_')
            
            # Over
            over_real = original_probabilities["over_under"].get(f"over_{line_str}", 0)
            if over_real == 0:  # Fallback para over_2_5 se específico não existir
                over_real = original_probabilities["over_under"].get("over_2_5", 0)
            over_implicit = implied_probabilities.get(f"over_{line_str}", 0)
            over_edge = over_real - over_implicit
            if over_edge > 2:
                opp_text = f"- **Over {line} Gols**: Real {over_real:.1f}% vs Implícita {over_implicit:.1f}% (Valor de {over_edge:.1f}%)"
                valid_opportunities.append(("Over/Under Gols", opp_text))
                value_opportunities.append({
                    "name": f"Over {line} Gols",
                    "market": "Over/Under",
                    "real_prob": over_real,
                    "implied_prob": over_implicit,
                    "edge": over_edge
                })
            
            # Under
            under_real = original_probabilities["over_under"].get(f"under_{line_str}", 0)
            if under_real == 0:  # Fallback ou cálculo
                under_real = 100.0 - over_real
            under_implicit = implied_probabilities.get(f"under_{line_str}", 0)
            under_edge = under_real - under_implicit
            if under_edge > 2:
                opp_text = f"- **Under {line} Gols**: Real {under_real:.1f}% vs Implícita {under_implicit:.1f}% (Valor de {under_edge:.1f}%)"
                valid_opportunities.append(("Over/Under Gols", opp_text))
                value_opportunities.append({
                    "name": f"Under {line} Gols",
                    "market": "Over/Under",
                    "real_prob": under_real,
                    "implied_prob": under_implicit,
                    "edge": under_edge
                })
    
    # 5. Escanteios (se selecionado)
    if selected_markets.get("escanteios") and "corners" in original_probabilities:
        # Extrair linha do texto de odds
        line_match = re.search(r"Over\s+(\d+\.?\d*)\s+Escanteios", odds_data)
        if line_match:
            line = float(line_match.group(1))
            line_str = str(line).replace('.', '_')
            
            # Calcular over e under para escanteios
            if f"over_{line_str}" in original_probabilities["corners"]:
                over_real = original_probabilities["corners"][f"over_{line_str}"] * 100
            else:
                # Use o padrão para over_9_5 e ajuste
                base_over = original_probabilities["corners"].get("over_9_5", 50)
                if isinstance(base_over, float) and base_over <= 1.0:
                    base_over = base_over * 100
                if line < 9.5:
                    over_real = min(95, base_over + ((9.5 - line) * 10))
                else:
                    over_real = max(5, base_over - ((line - 9.5) * 10))
            
            over_implicit = implied_probabilities.get(f"corners_over_{line_str}", 0)
            over_edge = over_real - over_implicit
            if over_edge > 2:
                opp_text = f"- **Over {line} Escanteios**: Real {over_real:.1f}% vs Implícita {over_implicit:.1f}% (Valor de {over_edge:.1f}%)"
                valid_opportunities.append(("Escanteios", opp_text))
                value_opportunities.append({
                    "name": f"Over {line} Escanteios",
                    "market": "Escanteios",
                    "real_prob": over_real,
                    "implied_prob": over_implicit,
                    "edge": over_edge
                })
            
            # Under
            under_real = 100.0 - over_real
            under_implicit = implied_probabilities.get(f"corners_under_{line_str}", 0)
            under_edge = under_real - under_implicit
            if under_edge > 2:
                opp_text = f"- **Under {line} Escanteios**: Real {under_real:.1f}% vs Implícita {under_implicit:.1f}% (Valor de {under_edge:.1f}%)"
                valid_opportunities.append(("Escanteios", opp_text))
                value_opportunities.append({
                    "name": f"Under {line} Escanteios",
                    "market": "Escanteios",
                    "real_prob": under_real,
                    "implied_prob": under_implicit,
                    "edge": under_edge
                })
    
    # 6. Cartões (se selecionado)
    if selected_markets.get("cartoes") and "cards" in original_probabilities:
        # Extrair linha do texto de odds
        line_match = re.search(r"Over\s+(\d+\.?\d*)\s+Cartões", odds_data)
        if line_match:
            line = float(line_match.group(1))
            line_str = str(line).replace('.', '_')
            
            # Calcular over e under para cartões
            if isinstance(original_probabilities["cards"], dict):
                if f"over_{line_str}" in original_probabilities["cards"]:
                    over_real = original_probabilities["cards"][f"over_{line_str}"] * 100
                else:
                    # Aproximação baseada em expected_cards
                    expected_cards = original_probabilities["cards"].get("expected_cards", 3.5)
                    if expected_cards > line + 1.5:
                        over_real = 75
                    elif expected_cards > line:
                        over_real = 60
                    elif expected_cards + 1.5 < line:
                        over_real = 25
                    else:
                        over_real = 40
            else:
                # Valor padrão se não tivermos dados específicos
                over_real = 50
            
            over_implicit = implied_probabilities.get(f"cards_over_{line_str}", 0)
            over_edge = over_real - over_implicit
            if over_edge > 2:
                opp_text = f"- **Over {line} Cartões**: Real {over_real:.1f}% vs Implícita {over_implicit:.1f}% (Valor de {over_edge:.1f}%)"
                valid_opportunities.append(("Cartões", opp_text))
                value_opportunities.append({
                    "name": f"Over {line} Cartões",
                    "market": "Cartões",
                    "real_prob": over_real,
                    "implied_prob": over_implicit,
                    "edge": over_edge
                })
            
            # Under
            under_real = 100.0 - over_real
            under_implicit = implied_probabilities.get(f"cards_under_{line_str}", 0)
            under_edge = under_real - under_implicit
            if under_edge > 2:
                opp_text = f"- **Under {line} Cartões**: Real {under_real:.1f}% vs Implícita {under_implicit:.1f}% (Valor de {under_edge:.1f}%)"
                valid_opportunities.append(("Cartões", opp_text))
                value_opportunities.append({
                    "name": f"Under {line} Cartões",
                    "market": "Cartões",
                    "real_prob": under_real,
                    "implied_prob": under_implicit,
                    "edge": under_edge
                })
    
    # Construir o texto final apenas com oportunidades que têm valor
    opportunities_text = "# Oportunidades Identificadas:\n"
    
    if valid_opportunities:
        # Agrupar oportunidades por mercado
        from collections import defaultdict
        grouped_opps = defaultdict(list)
        
        for market, opp_text in valid_opportunities:
            grouped_opps[market].append(opp_text)
        
        # Adicionar cada mercado e suas oportunidades
        for market, opps in grouped_opps.items():
            opportunities_text += f"## {market}:\n"
            opportunities_text += "\n".join(opps) + "\n"
    else:
        opportunities_text += "Infelizmente não detectamos valor em nenhuma das suas apostas."
    
    # Retornar tanto o texto quanto a lista de oportunidades com valor
    return opportunities_text, value_opportunities
