# utils/ai.py - Funções de Inteligência Artificial
import os
import logging
import streamlit as st
import json
# REMOVER ESTA LINHA: from utils.ai import format_highly_optimized_prompt

# Configuração de logging
logger = logging.getLogger("valueHunter.ai")

try:
    from openai import OpenAI, OpenAIError
    logger.info("OpenAI importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar OpenAI: {str(e)}")
    class DummyOpenAI:
        def __init__(self, **kwargs):
            pass
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    class FakeResponse:
                        class FakeChoice:
                            class FakeMessage:
                                content = "Serviço de IA temporariamente indisponível."
                            message = FakeMessage()
                        choices = [FakeChoice()]
                    return FakeResponse()
        
    OpenAI = DummyOpenAI
    class OpenAIError(Exception):
        pass

@st.cache_resource
def get_openai_client():
    # Melhor tratamento de erros para obtenção da API key
    try:
        # Se estamos no Render, usar variáveis de ambiente diretamente
        if "RENDER" in os.environ:
            api_key = os.environ.get("OPENAI_API_KEY", "")
            logger.info("Usando API key da OpenAI de variáveis de ambiente no Render")
        else:
            # Tente usar secrets (para desenvolvimento local ou Streamlit Cloud)
            try:
                api_key = st.secrets.get("OPENAI_API_KEY", "")
                logger.info("Usando API key da OpenAI de st.secrets")
            except Exception as e:
                logger.warning(f"Erro ao tentar carregar API key da OpenAI de st.secrets: {str(e)}")
                api_key = os.environ.get("OPENAI_API_KEY", "")
                logger.info("Usando API key da OpenAI de variáveis de ambiente locais")
        
        if not api_key:
            logger.error("OpenAI API key não encontrada em nenhuma configuração")
            return None
            
        try:
            client = OpenAI(api_key=api_key)
            logger.info("Cliente OpenAI inicializado com sucesso")
            return client
        except Exception as e:
            logger.error(f"Erro ao criar cliente OpenAI: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Erro não tratado em get_openai_client: {str(e)}")
        return None

# Função auxiliar para extrair linhas de over/under das odds fornecidas
def extract_overunder_lines(odds_data, market_type="gols"):
    """
    Extrai as linhas de over/under disponíveis para o mercado especificado
    
    Args:
        odds_data (str): String contendo as odds em formato texto
        market_type (str): Tipo de mercado ("gols", "escanteios", "cartoes")
        
    Returns:
        list: Lista de linhas (valores float) disponíveis para o mercado
    """
    import re
    
    # Definir padrões de busca baseados no tipo de mercado
    if market_type == "gols":
        pattern = r'(?:Over|Under)\s+(\d+(?:\.\d+)?)\s+[Gg]ols?'
    elif market_type == "escanteios":
        pattern = r'(?:Over|Under)\s+(\d+(?:\.\d+)?)\s+(?:[Ee]scanteios?|[Cc]orners?)'
    elif market_type == "cartoes":
        pattern = r'(?:Over|Under)\s+(\d+(?:\.\d+)?)\s+(?:[Cc]art[õoea][eo]s?)'
    else:
        return [2.5]  # Valor padrão para gols
    
    # Encontrar todas as correspondências do padrão
    matches = re.findall(pattern, odds_data)
    
    # Converter para float e remover duplicatas
    lines = sorted(set([float(match) for match in matches if match]))
    
    # Se não encontrar linhas, retornar valores padrão
    if not lines:
        if market_type == "gols":
            return [2.5]
        elif market_type == "escanteios":
            return [9.5]
        elif market_type == "cartoes":
            return [3.5]
    
    return lines

# Função para calcular probabilidade de over/under para uma linha específica
def calculate_overunder_probability(expected_value, line, market_type="gols"):
    """
    Calcula a probabilidade de over/under para uma linha específica
    
    Args:
        expected_value (float): Valor esperado (médio) de gols/escanteios/cartões
        line (float): Linha de over/under para calcular a probabilidade
        market_type (str): Tipo de mercado para ajustar parâmetros
        
    Returns:
        tuple: (prob_over, prob_under) em porcentagem
    """
    import math
    
    # Ajustar parâmetros da curva logística baseado no tipo de mercado
    if market_type == "gols":
        steepness = 1.5
    elif market_type == "escanteios":
        steepness = 0.8
    elif market_type == "cartoes":
        steepness = 1.2
    else:
        steepness = 1.5
    
    # Usar uma função logística para mapear valores esperados para probabilidades
    over_prob = 1 / (1 + math.exp(-steepness * (expected_value - line)))
    under_prob = 1 - over_prob
    
    # Converter para porcentagem
    over_prob_pct = over_prob * 100
    under_prob_pct = under_prob * 100
    
    return (over_prob_pct, under_prob_pct)

# Função para mapear parâmetros de mercado para exibição
def get_market_display_info(selected_markets, odds_data):
    """
    Extrai informações de exibição para todos os mercados selecionados
    
    Args:
        selected_markets (dict): Mercados selecionados pelo usuário
        odds_data (str): String contendo as odds em formato texto
        
    Returns:
        dict: Dicionário com informações de exibição para cada mercado
    """
    # Inicializar resultado
    market_info = {}
    
    # Processar Over/Under de Gols
    if selected_markets.get("over_under", False):
        gol_lines = extract_overunder_lines(odds_data, "gols")
        market_info["over_under_gols"] = {
            "lines": gol_lines,
            "display_name": "Over/Under Gols",
            "primary_line": gol_lines[0] if gol_lines else 2.5
        }
    
    # Processar Escanteios
    if selected_markets.get("escanteios", False):
        corner_lines = extract_overunder_lines(odds_data, "escanteios")
        market_info["escanteios"] = {
            "lines": corner_lines,
            "display_name": "Escanteios",
            "primary_line": corner_lines[0] if corner_lines else 9.5
        }
    
    # Processar Cartões
    if selected_markets.get("cartoes", False):
        card_lines = extract_overunder_lines(odds_data, "cartoes")
        market_info["cartoes"] = {
            "lines": card_lines,
            "display_name": "Cartões",
            "primary_line": card_lines[0] if card_lines else 3.5
        }
    
    # Processar Money Line
    if selected_markets.get("money_line", False):
        market_info["money_line"] = {
            "display_name": "Money Line (1X2)"
        }
    
    # Processar Chance Dupla
    if selected_markets.get("chance_dupla", False):
        market_info["chance_dupla"] = {
            "display_name": "Chance Dupla (Double Chance)"
        }
    
    # Processar Ambos Marcam
    if selected_markets.get("ambos_marcam", False):
        market_info["ambos_marcam"] = {
            "display_name": "Ambos Marcam (BTTS)"
        }
    
    return market_info

def format_highly_optimized_prompt(optimized_data, home_team, away_team, odds_data, selected_markets):
    """
    Format prompt for GPT with improved layout and comprehensive home/away data.
    """
    import logging
    import traceback
    import math
    import numpy as np
    
    logger = logging.getLogger("valueHunter.ai")
    
    logger.info(f"Formatting highly optimized prompt for {home_team} vs {away_team}")
    
    try:
        # Extract main data structures
        home = optimized_data.get("home_team", {})
        away = optimized_data.get("away_team", {})
        h2h = optimized_data.get("h2h", {})
        match_info = optimized_data.get("match_info", {"league": ""})
        
        # Extract league name if available
        league_name = match_info.get("league", "")
        
        # Verifica qualidade dos dados - se temos estatísticas mínimas
        has_stats_data = (
            (home.get("played", 0) > 0 or home.get("wins", 0) > 0 or home.get("goals_scored", 0) > 0) and
            (away.get("played", 0) > 0 or away.get("wins", 0) > 0 or away.get("goals_scored", 0) > 0)
        )
        
        # Log da qualidade dos dados
        home_fields = sum(1 for k, v in home.items() 
                       if (isinstance(v, (int, float)) and v != 0) or 
                          (isinstance(v, str) and v not in ["", "?????"]))
        away_fields = sum(1 for k, v in away.items() 
                       if (isinstance(v, (int, float)) and v != 0) or 
                          (isinstance(v, str) and v not in ["", "?????"]))
        
        logger.info(f"Qualidade dos dados: Casa={home_fields} campos, Visitante={away_fields} campos")
        logger.info(f"Estatísticas suficientes: {has_stats_data}")
        
        if not has_stats_data:
            logger.warning("AVISO: Dados estatísticos insuficientes. Usando cálculos de fallback.")
        
        # 1. FUNDAMENTAL STATISTICS
        fundamental_stats = f"""
# ESTATÍSTICAS FUNDAMENTAIS: {home_team} vs {away_team}
## {league_name}

### Desempenho Geral na Temporada
* {home_team}: {home.get('wins', 0)}V {home.get('draws', 0)}E {home.get('losses', 0)}D | {home.get('goals_scored', 0)} gols marcados, {home.get('goals_conceded', 0)} sofridos
* {away_team}: {away.get('wins', 0)}V {away.get('draws', 0)}E {away.get('losses', 0)}D | {away.get('goals_scored', 0)} gols marcados, {away.get('goals_conceded', 0)} sofridos

### Posição na Tabela
* {home_team}: {home.get('leaguePosition_overall', '?')}º geral | {home.get('leaguePosition_home', '?')}º em casa
* {away_team}: {away.get('leaguePosition_overall', '?')}º geral | {away.get('leaguePosition_away', '?')}º fora

### Desempenho em Casa/Fora
* {home_team} como mandante: {home.get('home_wins', 0)}V {home.get('home_draws', 0)}E {home.get('home_losses', 0)}D
  - Gols marcados em casa: {home.get('home_goals_scored', 0)}
  - Gols sofridos em casa: {home.get('home_goals_conceded', 0)}
  - Pontos por jogo em casa: {home.get('seasonPPG_home', 0)}
  - Forma em casa: {home.get('home_form', '?????')}

* {away_team} como visitante: {away.get('away_wins', 0)}V {away.get('away_draws', 0)}E {away.get('away_losses', 0)}D
  - Gols marcados fora: {away.get('away_goals_scored', 0)}
  - Gols sofridos fora: {away.get('away_goals_conceded', 0)}
  - Pontos por jogo fora: {away.get('seasonPPG_away', 0)}
  - Forma fora: {away.get('away_form', '?????')}

### Forma Recente (últimos 5 jogos)
* {home_team}: {home.get('form', '?????')}
* {away_team}: {away.get('form', '?????')}

### Métricas Expected Goals (xG)
* {home_team}: 
  - xG total: {home.get('xg', 0)} | xG em casa: {home.get('home_xg', 0)}
  - xGA total: {home.get('xga', 0)} | xGA em casa: {home.get('home_xga', 0)}
  - xG médio por jogo: {home.get('xg_for_avg_overall', 0)}

* {away_team}: 
  - xG total: {away.get('xg', 0)} | xG fora: {away.get('away_xg', 0)}
  - xGA total: {away.get('xga', 0)} | xGA fora: {away.get('away_xga', 0)}
  - xG médio por jogo: {away.get('xg_for_avg_overall', 0)}

### Confronto Direto (H2H)
* Jogos totais: {h2h.get('total_matches', 0)}
* Vitórias {home_team}: {h2h.get('home_wins', 0)}
* Vitórias {away_team}: {h2h.get('away_wins', 0)}
* Empates: {h2h.get('draws', 0)}
* Média de gols: {h2h.get('avg_goals', 0)}
"""

        # Adicionar aviso no prompt caso não tenhamos dados estatísticos suficientes
        if not has_stats_data:
            fundamental_stats += """
### AVISO IMPORTANTE
⚠️ Os dados estatísticos para esta partida são limitados ou inexistentes.
As probabilidades calculadas estão utilizando a metodologia de fallback e devem ser consideradas aproximações.
Recomenda-se cautela ao tomar decisões baseadas nesta análise.
"""

        # 2. STATS FOR RESULT MARKETS
        result_stats = ""
        if any(selected_markets.get(m) for m in ["money_line", "chance_dupla"]):
            result_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE RESULTADO

### Percentuais de Resultados
* {home_team}:
  - Vitória: {home.get('win_pct', 0)}%
  - Empate: {home.get('draw_pct', 0)}%
  - Derrota: {home.get('loss_pct', 0)}%

* {away_team}:
  - Vitória: {away.get('win_pct', 0)}%
  - Empate: {away.get('draw_pct', 0)}%
  - Derrota: {away.get('loss_pct', 0)}%

### Pontos por Jogo
* {home_team}:
  - Geral: {home.get('seasonPPG_overall', 0)}
  - Em casa: {home.get('seasonPPG_home', 0)}
  - Recente: {home.get('seasonRecentPPG', 0)}

* {away_team}:
  - Geral: {away.get('seasonPPG_overall', 0)}
  - Fora: {away.get('seasonPPG_away', 0)}
  - Recente: {away.get('seasonRecentPPG', 0)}

### Posse de Bola
* {home_team}: {home.get('possession', 0)}% geral | {home.get('home_possession', 0)}% em casa
* {away_team}: {away.get('possession', 0)}% geral | {away.get('away_possession', 0)}% fora
"""

        # 3. GOALS MARKETS STATS
        goals_stats = ""
        if any(selected_markets.get(m) for m in ["over_under", "ambos_marcam"]):
            goals_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE GOLS

### Médias de Gols
* {home_team}:
  - Média gols marcados: {home.get('goals_per_game', 0)} geral | {home.get('home_goals_scored', 0) / max(1, home.get('home_played', 1)):.2f} em casa
  - Média gols sofridos: {home.get('conceded_per_game', 0)} geral | {home.get('home_goals_conceded', 0) / max(1, home.get('home_played', 1)):.2f} em casa
  - Total gols por jogo: {home.get('seasonGoalsTotal_overall', 0) / max(1, home.get('played', 1)):.2f} geral | {home.get('seasonGoalsTotal_home', 0) / max(1, home.get('home_played', 1)):.2f} em casa

* {away_team}:
  - Média gols marcados: {away.get('goals_per_game', 0)} geral | {away.get('away_goals_scored', 0) / max(1, away.get('away_played', 1)):.2f} fora
  - Média gols sofridos: {away.get('conceded_per_game', 0)} geral | {away.get('away_goals_conceded', 0) / max(1, away.get('away_played', 1)):.2f} fora
  - Total gols por jogo: {away.get('seasonGoalsTotal_overall', 0) / max(1, away.get('played', 1)):.2f} geral | {away.get('seasonGoalsTotal_away', 0) / max(1, away.get('away_played', 1)):.2f} fora

### Clean Sheets e Ambos Marcam
* {home_team}: 
  - Clean sheets: {home.get('seasonCS_overall', 0)} geral ({home.get('clean_sheets_pct', 0)}%) | {home.get('seasonCS_home', 0)} em casa
* {away_team}: 
  - Clean sheets: {away.get('seasonCS_overall', 0)} geral ({away.get('clean_sheets_pct', 0)}%) | {away.get('seasonCS_away', 0)} fora
* {home_team} jogos com Ambos Marcam: {home.get('btts_pct', 0)}%
* {away_team} jogos com Ambos Marcam: {away.get('btts_pct', 0)}%
* Jogos H2H com Ambos Marcam: {h2h.get('btts_pct', 0)}%

### Distribuição de Gols por Jogo
* Jogos do {home_team} com Over 2.5: {home.get('over_2_5_pct', 0)}%
* Jogos do {away_team} com Over 2.5: {away.get('over_2_5_pct', 0)}%
* Jogos H2H com Over 2.5: {h2h.get('over_2_5_pct', 0)}%

### Estatísticas de Chutes
* {home_team}:
  - Chutes por jogo: {home.get('shotsAVG_overall', 0)} geral | {home.get('shotsAVG_home', 0)} em casa
  - Chutes no alvo por jogo: {home.get('shotsOnTargetAVG_overall', 0)} geral | {home.get('shotsOnTargetAVG_home', 0)} em casa

* {away_team}:
  - Chutes por jogo: {away.get('shotsAVG_overall', 0)} geral | {away.get('shotsAVG_away', 0)} fora
  - Chutes no alvo por jogo: {away.get('shotsOnTargetAVG_overall', 0)} geral | {away.get('shotsOnTargetAVG_away', 0)} fora
"""

        # 4. CARDS AND CORNERS if selected
        other_stats = ""
        if selected_markets.get("escanteios"):
            other_stats += f"""
# ESTATÍSTICAS PARA MERCADOS DE ESCANTEIOS

### Dados de Escanteios
* {home_team}:
  - Média de escanteios por jogo: {home.get('corners_per_game', 0)} geral | {home.get('home_corners_per_game', 0)} em casa
  - Escanteios a favor: {home.get('corners_for', 0)} total | {home.get('cornersAVG_overall', 0)} média geral | {home.get('cornersAVG_home', 0)} média em casa
  - Escanteios contra: {home.get('corners_against', 0)} total | {home.get('cornersAgainstAVG_overall', 0)} média geral | {home.get('cornersAgainstAVG_home', 0)} média em casa
  - Jogos com Over 9.5 escanteios: {home.get('over_9_5_corners_pct', 0)}%

* {away_team}:
  - Média de escanteios por jogo: {away.get('corners_per_game', 0)} geral | {away.get('away_corners_per_game', 0)} fora
  - Escanteios a favor: {away.get('corners_for', 0)} total | {away.get('cornersAVG_overall', 0)} média geral | {away.get('cornersAVG_away', 0)} média fora
  - Escanteios contra: {away.get('corners_against', 0)} total | {away.get('cornersAgainstAVG_overall', 0)} média geral | {away.get('cornersAgainstAVG_away', 0)} média fora
  - Jogos com Over 9.5 escanteios: {away.get('over_9_5_corners_pct', 0)}%

* Média de escanteios em confrontos diretos: {h2h.get('avg_corners', 0)}
"""

        if selected_markets.get("cartoes"):
            other_stats += f"""
# ESTATÍSTICAS PARA MERCADOS DE CARTÕES

### Dados de Cartões
* {home_team}:
  - Média de cartões por jogo: {home.get('cards_per_game', 0)} geral | {home.get('home_cards_per_game', 0)} em casa
  - Total de cartões: {home.get('cardsTotal_overall', 0)} geral | {home.get('cardsTotal_home', 0)} em casa
  - Cartões amarelos: {home.get('yellow_cards', 0)}
  - Cartões vermelhos: {home.get('red_cards', 0)}
  - Jogos com Over 3.5 cartões: {home.get('over_3_5_cards_pct', 0)}%

* {away_team}:
  - Média de cartões por jogo: {away.get('cards_per_game', 0)} geral | {away.get('away_cards_per_game', 0)} fora
  - Total de cartões: {away.get('cardsTotal_overall', 0)} geral | {away.get('cardsTotal_away', 0)} fora
  - Cartões amarelos: {away.get('yellow_cards', 0)}
  - Cartões vermelhos: {away.get('red_cards', 0)}
  - Jogos com Over 3.5 cartões: {away.get('over_3_5_cards_pct', 0)}%

* Média de cartões em confrontos diretos: {h2h.get('avg_cards', 0)}
"""

        # 5. PROBABILITY CALCULATION USING DISPERSAL AND WEIGHTING METHOD
        # Calculate probability using our advanced method
        
        # Form points (35%)
        def form_to_points(form_str):
            points = 0
            weight = 1.0
            total_weight = 0
            
            for i, result in enumerate(reversed(form_str[:5])):
                if result == 'W':
                    points += 3 * weight
                elif result == 'D':
                    points += 1 * weight
                elif result == 'L':
                    points += 0
                else:
                    points += 1 * weight  # Neutral value for '?'
                
                total_weight += weight
                weight *= 0.8  # Decay for older games
            
            return points / max(total_weight, 1)
        
        # Convert form to points (scale 0-1)
        home_form = home.get('form', '?????')
        away_form = away.get('form', '?????')
        home_form_points = form_to_points(home_form) / 15
        away_form_points = form_to_points(away_form) / 15
        
        # Team stats score (25%)
        home_xg = home.get('xg', 0)
        home_xga = home.get('xga', 0)
        away_xg = away.get('xg', 0)
        away_xga = away.get('xga', 0)
        
        max_xg = max(home_xg, away_xg, 60)
        
        home_offensive = (home_xg / max(max_xg, 1)) * 0.6 + (home.get('goals_per_game', 0) / 3) * 0.4
        home_defensive = (1 - min(1, home_xga / max(max_xg, 1))) * 0.6 + (1 - min(1, home.get('conceded_per_game', 0) / 3)) * 0.4
        away_offensive = (away_xg / max(max_xg, 1)) * 0.6 + (away.get('goals_per_game', 0) / 3) * 0.4
        away_defensive = (1 - min(1, away_xga / max(max_xg, 1))) * 0.6 + (1 - min(1, away.get('conceded_per_game', 0) / 3)) * 0.4
        
        home_stats_score = home_offensive * 0.6 + home_defensive * 0.4
        away_stats_score = away_offensive * 0.6 + away_defensive * 0.4
        
        # Table position (20%) - estimated from win rate
        home_position_score = home.get('win_pct', 50) / 100
        away_position_score = away.get('win_pct', 50) / 100
        
        # Creation metrics (20%)
        home_possession = home.get('possession', 50) / 100
        away_possession = away.get('possession', 50) / 100
        
        home_creation = home_offensive * 0.7 + home_possession * 0.3
        away_creation = away_offensive * 0.7 + away_possession * 0.3
        
        # APPLY WEIGHTS
        home_total_score = (
            home_form_points * 0.35 +      # Recent form: 35%
            home_stats_score * 0.25 +      # Team stats: 25%
            home_position_score * 0.20 +   # Position: 20%
            home_creation * 0.20           # Creation: 20%
        )
        
        away_total_score = (
            away_form_points * 0.35 +      # Recent form: 35%
            away_stats_score * 0.25 +      # Team stats: 25%
            away_position_score * 0.20 +   # Position: 20%
            away_creation * 0.20           # Creation: 20%
        )
        
        # 1. Moneyline calculation
        raw_home_win = home_total_score / (home_total_score + away_total_score) * 0.8
        raw_away_win = away_total_score / (home_total_score + away_total_score) * 0.8
        raw_draw = 1 - (raw_home_win + raw_away_win)
        
        # Home advantage adjustment
        home_advantage = 0.12
        adjusted_home_win = raw_home_win + home_advantage
        adjusted_away_win = raw_away_win - (home_advantage * 0.5)
        adjusted_draw = raw_draw - (home_advantage * 0.5)
        
        # Normalize to sum to 1
        total = adjusted_home_win + adjusted_draw + adjusted_away_win
        home_win_prob = (adjusted_home_win / total) * 100
        draw_prob = (adjusted_draw / total) * 100
        away_win_prob = (adjusted_away_win / total) * 100
        
        # Round values
        home_win_prob = round(home_win_prob, 1)
        draw_prob = round(draw_prob, 1)
        away_win_prob = round(away_win_prob, 1)
        
        # Calculate team consistency (dispersion)
        home_results = [
            home.get('win_pct', 0) / 100,
            home.get('draw_pct', 0) / 100,
            home.get('loss_pct', 0) / 100
        ]
        
        away_results = [
            away.get('win_pct', 0) / 100,
            away.get('draw_pct', 0) / 100,
            away.get('loss_pct', 0) / 100
        ]
        
        # Calculate standard deviation for dispersion
        try:
            home_dispersion = np.std(home_results) * 3
            away_dispersion = np.std(away_results) * 3
            
            # Convert to consistency (inverse of dispersion)
            home_consistency = (1 - min(1, home_dispersion)) * 100
            away_consistency = (1 - min(1, away_dispersion)) * 100
        except:
            # Fallback if numpy isn't available
            home_consistency = 50
            away_consistency = 50
        
        # Extrair informações de todos os mercados
        market_display_info = get_market_display_info(selected_markets, odds_data)

        # 2. Over/Under Gols - Agora dinâmico para qualquer linha
        over_under_probs = {}
        if selected_markets.get("gols", False):
            # Use a combinação de estatísticas de time e xG
            home_expected_goals = home.get('xg_for_avg_overall', 0) if home.get('xg_for_avg_overall', 0) > 0 else home.get('goals_per_game', 0)
            away_expected_goals = away.get('xg_for_avg_overall', 0) if away.get('xg_for_avg_overall', 0) > 0 else away.get('goals_per_game', 0)
            
            # Considerar força defensiva
            home_expected_conceded = away_expected_goals * (home.get('conceded_per_game', 0) / 1.5) if home.get('conceded_per_game', 0) > 0 else away_expected_goals * 0.8
            away_expected_conceded = home_expected_goals * (away.get('conceded_per_game', 0) / 1.5) if away.get('conceded_per_game', 0) > 0 else home_expected_goals * 0.8
            
            # Total esperado de gols
            total_expected_goals = home_expected_conceded + away_expected_conceded
            
            # Calcular para cada linha encontrada
            if "over_under_gols" in market_display_info:
                gol_lines = market_display_info["over_under_gols"]["lines"]
                for line in gol_lines:
                    over_prob, under_prob = calculate_overunder_probability(total_expected_goals, line, "gols")
                    over_under_probs[line] = {
                        "over": over_prob,
                        "under": under_prob
                    }
            else:
                # Fallback para 2.5 se não encontrar linhas
                over_prob, under_prob = calculate_overunder_probability(total_expected_goals, 2.5, "gols")
                over_under_probs[2.5] = {
                    "over": over_prob,
                    "under": under_prob
                }

        # 3. Both Teams To Score (BTTS) - Não precisa mudança, pois é binário
        btts_yes_prob = 0
        btts_no_prob = 0
        if selected_markets.get("ambos_marcam", False):
            # Usar probabilidade de marcação de cada time
            home_scoring_prob = 1 - (1 / (1 + math.exp(home_expected_goals - 0.5)))
            away_scoring_prob = 1 - (1 / (1 + math.exp(away_expected_goals - 0.5)))
            
            # Probabilidade BTTS é o produto das probabilidades de ambos marcarem
            btts_yes_prob = home_scoring_prob * away_scoring_prob * 100
            btts_no_prob = 100 - btts_yes_prob

        # 4. Escanteios - Agora dinâmico para qualquer linha
        corners_probs = {}
        total_corners_expected = 0
        if selected_markets.get("escanteios", False):
            # Calcular expectativa de escanteios
            home_corners_avg = home.get("cornersAVG_overall", 0) or home.get("corners_per_game", 0) / 2
            away_corners_avg = away.get("cornersAVG_overall", 0) or away.get("corners_per_game", 0) / 2
            
            home_corners_against_avg = home.get("cornersAgainstAVG_overall", 0) or home.get("corners_per_game", 0) / 2
            away_corners_against_avg = away.get("cornersAgainstAVG_overall", 0) or away.get("corners_per_game", 0) / 2
            
            # Ajuste para jogo específico
            home_corners_expected = (home_corners_avg + away_corners_against_avg) / 2
            away_corners_expected = (away_corners_avg + home_corners_against_avg) / 2
            
            # Total esperado de escanteios
            total_corners_expected = home_corners_expected + away_corners_expected
            
            # Calcular para cada linha encontrada
            if "escanteios" in market_display_info:
                corner_lines = market_display_info["escanteios"]["lines"]
                for line in corner_lines:
                    over_prob, under_prob = calculate_overunder_probability(total_corners_expected, line, "escanteios")
                    corners_probs[line] = {
                        "over": over_prob,
                        "under": under_prob
                    }
            else:
                # Fallback para 9.5 se não encontrar linhas
                over_prob, under_prob = calculate_overunder_probability(total_corners_expected, 9.5, "escanteios")
                corners_probs[9.5] = {
                    "over": over_prob,
                    "under": under_prob
                }

        # 5. Cartões - Agora dinâmico para qualquer linha
        cards_probs = {}
        total_cards_expected = 0
        if selected_markets.get("cartoes", False):
            # Calcular expectativa de cartões
            home_cards_avg = home.get("cards_per_game", 0)
            away_cards_avg = away.get("cards_per_game", 0)
            
            # Ajuste baseado em histórico de confrontos
            h2h_cards_avg = h2h.get("avg_cards", 0)
            
            # Ajustar baseado em intensidade esperada (maior se os times são mais próximos)
            intensity_factor = 1 + max(0, (1 - abs(home_total_score - away_total_score))) * 0.3
            
            # Total esperado de cartões
            total_cards_expected = (home_cards_avg + away_cards_avg) * intensity_factor
            
            # Se temos dados H2H, dar algum peso para isso
            if h2h_cards_avg > 0:
                total_cards_expected = (total_cards_expected * 0.7) + (h2h_cards_avg * 0.3)
            
            # Calcular para cada linha encontrada
            if "cartoes" in market_display_info:
                card_lines = market_display_info["cartoes"]["lines"]
                for line in card_lines:
                    over_prob, under_prob = calculate_overunder_probability(total_cards_expected, line, "cartoes")
                    cards_probs[line] = {
                        "over": over_prob,
                        "under": under_prob
                    }
            else:
                # Fallback para 3.5 se não encontrar linhas
                over_prob, under_prob = calculate_overunder_probability(total_cards_expected, 3.5, "cartoes")
                cards_probs[3.5] = {
                    "over": over_prob,
                    "under": under_prob
                }

        # 6. Chance Dupla (Double Chance)
        home_draw_prob = home_win_prob + draw_prob
        away_draw_prob = away_win_prob + draw_prob
        home_away_prob = home_win_prob + away_win_prob
        
        # PROBABILITY SECTION
        if not has_stats_data:
            prob_title = "PROBABILIDADES CALCULADAS (MODELO DE FALLBACK)"
            prob_explanation = """
### Observação Importante
Devido à falta de dados estatísticos suficientes, estas probabilidades são aproximações 
baseadas em um modelo simplificado e podem não refletir com precisão as chances reais."""
        else:
            prob_title = "PROBABILIDADES CALCULADAS (MÉTODO DE DISPERSÃO E PONDERAÇÃO)"
            prob_explanation = """
### Metodologia
As probabilidades foram calculadas usando nossa metodologia de dispersão e ponderação com:
- Forma recente: 35%
- Estatísticas de equipe: 25%
- Posição na tabela: 20%
- Métricas de criação: 20%"""

        # Start building the probability section
        probability_section = f"""
# {prob_title}
{prob_explanation}
"""

        # Only include Money Line if selected
        if selected_markets.get("money_line", False):
            probability_section += f"""
### Moneyline (1X2)
* {home_team}: {home_win_prob}%
* Empate: {draw_prob}%
* {away_team}: {away_win_prob}%
* Total: {home_win_prob + draw_prob + away_win_prob}%
"""

        # Only include Double Chance if selected
        if selected_markets.get("chance_dupla", False):
            probability_section += f"""
### Chance Dupla (Double Chance)
* {home_team} ou Empate (1X): {home_draw_prob:.1f}%
* {home_team} ou {away_team} (12): {home_away_prob:.1f}%
* {away_team} ou Empate (X2): {away_draw_prob:.1f}%
"""

        # Only include Over/Under if selected - AGORA COM SUPORTE A MÚLTIPLAS LINHAS
        if selected_markets.get("over_under", False):
            probability_section += f"""
### Over/Under Gols
"""
            # Adicionar probabilidades para cada linha
            for line in sorted(over_under_probs.keys()):
                probability_section += f"""
* Over {line}: {over_under_probs[line]['over']:.1f}%
* Under {line}: {over_under_probs[line]['under']:.1f}%
"""
            probability_section += f"""
* Total esperado de gols: {total_expected_goals:.2f}
"""

        # Only include BTTS if selected
        if selected_markets.get("ambos_marcam", False):
            probability_section += f"""
### Ambos Marcam (BTTS)
* Sim: {btts_yes_prob:.1f}%
* Não: {btts_no_prob:.1f}%
"""

        # Only include Corners (Escanteios) if selected - AGORA COM SUPORTE A MÚLTIPLAS LINHAS
        if selected_markets.get("escanteios", False):
            probability_section += f"""
### Escanteios
"""
            # Adicionar probabilidades para cada linha
            for line in sorted(corners_probs.keys()):
                probability_section += f"""
* Over {line}: {corners_probs[line]['over']:.1f}%
* Under {line}: {corners_probs[line]['under']:.1f}%
"""
            probability_section += f"""
* Total esperado de escanteios: {total_corners_expected:.1f}
"""

        # Only include Cards (Cartões) if selected - AGORA COM SUPORTE A MÚLTIPLAS LINHAS
        if selected_markets.get("cartoes", False):
            probability_section += f"""
### Cartões
"""
            # Adicionar probabilidades para cada linha
            for line in sorted(cards_probs.keys()):
                probability_section += f"""
* Over {line}: {cards_probs[line]['over']:.1f}%
* Under {line}: {cards_probs[line]['under']:.1f}%
"""
            probability_section += f"""
* Total esperado de cartões: {total_cards_expected:.1f}
"""

        probability_section += f"""
### Índices de Confiança
* Consistência {home_team}: {home_consistency:.1f}%
* Consistência {away_team}: {away_consistency:.1f}%
* Forma recente {home_team} (pontos): {home_form_points*15:.1f}/15
* Forma recente {away_team} (pontos): {away_form_points*15:.1f}/15
"""

        # 7. AVAILABLE MARKETS AND ODDS
        markets_info = f"""
# MERCADOS DISPONÍVEIS E ODDS
{odds_data}
"""

        # 8. INSTRUCTIONS
        # Preparar informações de exibição para as instruções
        over_under_lines = []
        if "over_under_gols" in market_display_info:
            for line in market_display_info["over_under_gols"]["lines"]:
                over_under_lines.append(f"Over/Under {line} Gols")
        
        corner_lines = []
        if "escanteios" in market_display_info:
            for line in market_display_info["escanteios"]["lines"]:
                corner_lines.append(f"Over/Under {line} Escanteios")
        
        card_lines = []
        if "cartoes" in market_display_info:
            for line in market_display_info["cartoes"]["lines"]:
                card_lines.append(f"Over/Under {line} Cartões")
        
        # Preparar lista completa de mercados para as instruções
        selected_market_names = []
        if selected_markets.get("money_line", False):
            selected_market_names.append("Money Line (1X2)")
        if selected_markets.get("chance_dupla", False):
            selected_market_names.append("Chance Dupla (Double Chance)")
        if over_under_lines:
            selected_market_names.extend(over_under_lines)
        if selected_markets.get("ambos_marcam", False):
            selected_market_names.append("Ambos Marcam (BTTS)")
        if corner_lines:
            selected_market_names.extend(corner_lines)
        if card_lines:
            selected_market_names.extend(card_lines)
        
        # Join the market names into a string
        selected_markets_str = ", ".join(selected_market_names)
        
        # Gerar instruções adaptadas
        instructions = f"""
# INSTRUÇÕES PARA ANÁLISE

Analise os dados estatísticos fornecidos para identificar valor nas odds.
Você é um especialista em probabilidades esportivas que utiliza nosso método avançado de Dispersão e Ponderação.

IMPORTANTE: As probabilidades REAIS já foram calculadas para você para os seguintes mercados selecionados e somam exatamente 100% em cada mercado:
{selected_markets_str}

Todas as probabilidades reais estão na seção "PROBABILIDADES CALCULADAS".

VOCÊ DEVE ORGANIZAR SUA RESPOSTA COM ESTAS REGRAS ESTRITAS:

1. Organizar mercados em categorias SEPARADAS e EXPLÍCITAS:
   - Money Line (1X2)
   - Chance Dupla (Double Chance)
   - Over/Under Gols (NUNCA misturar com escanteios ou cartões)
   - Ambos Marcam (BTTS)
   - Escanteios (específico para Corners, SEMPRE separado de gols)
   - Cartões (específico para Cards, SEMPRE separado de gols)

2. Na seção de probabilidades calculadas, criar tabelas SEPARADAS para CADA tipo de mercado:
   - Uma tabela para Money Line (1X2)
   - Uma tabela para Chance Dupla
   - Uma tabela para Over/Under Gols (apenas gols, com as linhas específicas)
   - Uma tabela para Ambos Marcam
   - Uma tabela para Escanteios (apenas escanteios, com as linhas específicas)
   - Uma tabela para Cartões (apenas cartões, com as linhas específicas)

VOCÊ DEVE responder EXATAMENTE no formato abaixo:

# 📊 ANÁLISE DE PARTIDA 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚽ {home_team} 🆚 {away_team} ⚽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 📈 ANÁLISE DE MERCADOS DISPONÍVEIS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
[Resumo detalhado APENAS dos mercados selecionados ({selected_markets_str}) 
com suas odds e probabilidades implícitas]

### 🔄 PROBABILIDADES CALCULADAS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
   ┌────────────┬────────────┬────────────┐
   │  MERCADO   │  REAL (%)  │ IMPLÍCITA  │
   └────────────┴────────────┴────────────┘
[Compare as probabilidades REAIS calculadas com as probabilidades 
IMPLÍCITAS nas odds APENAS para os mercados selecionados ({selected_markets_str})]

### 💰 OPORTUNIDADES IDENTIFICADAS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
[Liste cada mercado onde você encontrou valor/edge, mostrando a 
porcentagem de vantagem]
- Considere valor quando a probabilidade real for pelo menos 2% maior que a implícita

### 🎯 NÍVEL DE CONFIANÇA GERAL: [Baixo/Médio/Alto]
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
[Explique o nível de confiança, incluindo uma explicação clara sobre:]

  ► CONSISTÊNCIA: Medida (%) que indica quão previsível é o desempenho da equipe
  
  ► FORMA: Pontuação dos últimos 5 jogos (X.X/15)
     • Vitória = 3 pontos
     • Empate = 1 ponto
     • Derrota = 0 pontos
  
  ► INFLUÊNCIA: Como esses fatores influenciam a confiança na análise

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                © RELATÓRIO DE ANÁLISE ESPORTIVA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # Adicionar aviso quando utilizamos o modelo de fallback
        if not has_stats_data:
            instructions += """
ATENÇÃO: Os dados estatísticos para esta partida são limitados. Use apenas as informações disponíveis e seja claro quando não houver dados suficientes para uma análise completa.
"""
        
        # Compile the final prompt
        sections = [
            fundamental_stats,
        ]
        
        # Only include result stats if moneyline or double chance are selected
        if selected_markets.get("money_line") or selected_markets.get("chance_dupla"):
            sections.append(result_stats)
        
        # Only include goals stats if over/under or btts are selected
        if selected_markets.get("gols") or selected_markets.get("ambos_marcam"):
            sections.append(goals_stats)
        
        # Only include other stats if relevant markets are selected
        if other_stats and (selected_markets.get("escanteios") or selected_markets.get("cartoes")):
            sections.append(other_stats)
        
        # Always include probability section and markets info
        sections.append(probability_section)
        sections.append(markets_info)
        sections.append(instructions)
        
        full_prompt = "\n".join([s for s in sections if s])
        logger.info(f"Prompt prepared successfully for {home_team} vs {away_team}")
        
        return full_prompt
        
    except Exception as e:
        logger.error(f"Error formatting highly optimized prompt: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a simplified prompt as fallback
        return f"""
# ESTATÍSTICAS BÁSICAS
{home_team} vs {away_team}

{odds_data}

# PROBABILIDADES CALCULADAS
* {home_team}: 56.6%
* Empate: 14.0% 
* {away_team}: 29.4%
* Total: 100.0%

# INSTRUÇÕES
Analise as odds e identifique oportunidades de valor.
Responda com EXATAMENTE este formato:

# 📊 ANÁLISE DE PARTIDA 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚽ {home_team} 🆚 {away_team} ⚽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 📈 ANÁLISE DE MERCADOS DISPONÍVEIS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
[Resumo detalhado dos mercados com odds]

### 🔄 PROBABILIDADES CALCULADAS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
[Comparação de probabilidades]

### 💰 OPORTUNIDADES IDENTIFICADAS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
[Lista de oportunidades]

### 🎯 NÍVEL DE CONFIANÇA GERAL: [Baixo/Médio/Alto]
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
[Explicação com consistência e forma]
"""

def analyze_with_gpt(prompt, original_probabilites=None, selected_markets=None, home_team=None, away_team=None):
    try:
        client = get_openai_client()
        if not client:
            st.error("Cliente OpenAI não inicializado")
            return None
            
        with st.spinner("Analisando dados e calculando probabilidades..."):
            logger.info("Enviando prompt para análise com GPT")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um Agente Analista de Probabilidades Esportivas especializado. Trabalhe com quaisquer dados estatísticos disponíveis, mesmo que sejam limitados. Na ausência de dados completos, forneça análise com base nas odds implícitas e nos poucos dados disponíveis, sendo transparente sobre as limitações, mas ainda oferecendo recomendações práticas."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                timeout=60  # Timeout de 60 segundos
            )
            logger.info("Resposta recebida do GPT com sucesso")
            
            # Se temos as probabilidades originais, aplicar a formatação melhorada
            response_text = response.choices[0].message.content
            if home_team and away_team:
                logger.info("Aplicando formatação avançada com filtragem de mercados")
                # Importante: passamos selected_markets e original_probabilites para filtrar os mercados
                from utils.ai import format_analysis_response
                response_text = format_analysis_response(
                    response_text, 
                    home_team, 
                    away_team, 
                    selected_markets=selected_markets, 
                    original_probabilities=original_probabilites
                )
                
            return response_text
    except OpenAIError as e:
        logger.error(f"Erro na API OpenAI: {str(e)}")
        st.error(f"Erro na API OpenAI: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        st.error(f"Erro inesperado: {str(e)}")
        return None

# Correções para eliminar duplicação nas tabelas e remover marcadores duplos

# 1. Correção para prevenir duplicação de linhas nas tabelas
def corrigir_formatacao_tabelas(category, options):
    """
    Corrige a formatação das tabelas de probabilidades para evitar duplicação
    e truncamento nas linhas.
    
    Args:
        category (str): O nome da categoria/mercado
        options (dict): Opções e probabilidades para o mercado
    
    Returns:
        str: Código HTML da tabela formatada corretamente
    """
    table_html = f"""
[{category}]
┌────────────┬────────────┬────────────┐
│  MERCADO   │  REAL (%)  │ IMPLÍCITA  │
├────────────┼────────────┼────────────┤"""
    
    # Processar cada opção sem duplicação
    processed_options = set()
    for option, probs in options.items():
        # Prevenir duplicação usando um set para rastrear opções processadas
        option_key = option.lower().strip()
        if option_key in processed_options:
            continue
            
        processed_options.add(option_key)
        
        # Garantir que o nome da opção seja exibido completamente
        option_display = option
        if len(option) > 8:
            # Truncar mantendo a parte mais significativa
            if "Over" in option or "Under" in option:
                parts = option.split()
                if len(parts) >= 2:
                    option_display = f"{parts[0]} {parts[1]}"
            else:
                option_display = option[:7] + "."
                
        # Garantir que as probabilidades estejam formatadas corretamente
        real_prob = probs.get('real', 'N/A')
        impl_prob = probs.get('implicit', 'N/A')
        
        # Adicionar a linha na tabela
        table_html += f"""
│  {option_display.ljust(8)} │ {str(real_prob).center(10)} │ {str(impl_prob).center(10)} │"""
    
    # Fechar a tabela
    table_html += """
└────────────┴────────────┴────────────┘"""
    
    return table_html

# 2. Correção para remover marcadores duplicados nos mercados
def limpar_marcadores_mercados(market_line):
    """
    Remove duplicação de marcadores (•) em linhas de mercado.
    
    Args:
        market_line (str): Linha de mercado original
        
    Returns:
        str: Linha de mercado corrigida
    """
    # Remover duplicação de marcadores
    clean_line = market_line.replace("• •", "•").replace("••", "•")
    
    # Garantir consistência no formato
    if not clean_line.startswith("•"):
        clean_line = "• " + clean_line.lstrip("- ")
    
    # Remover espaços extras
    clean_line = " ".join(clean_line.split())
    
    return clean_line

# Implementação melhorada da função que formata os mercados
def formatar_mercados_disponiveis(market_categories):
    """
    Formata os mercados disponíveis com categorias separadas
    e sem duplicação de marcadores.
    
    Args:
        market_categories (dict): Categorias e seus mercados correspondentes
        
    Returns:
        str: HTML formatado dos mercados
    """
    mercados_html = """
ANÁLISE DE MERCADOS DISPONÍVEIS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"""
    
    has_mercados = False
    
    # Adicionar cada categoria separadamente
    for category, markets in market_categories.items():
        if markets and len(markets) > 0:
            has_mercados = True
            mercados_html += f"\n\n[{category}]"
            
            # Processamento para evitar duplicação de mercados
            seen_markets = set()
            for market in markets:
                clean_market = limpar_marcadores_mercados(market)
                
                # Extração para verificar duplicação
                market_text = clean_market.split('@')[0].strip() if '@' in clean_market else clean_market
                if market_text not in seen_markets:
                    mercados_html += f"\n{clean_market}"
                    seen_markets.add(market_text)
    
    if not has_mercados:
        mercados_html += "\nInformações de mercados não disponíveis."
    
    return mercados_html

# 3. Correção do problema com as tabelas de Over/Under, Escanteios e Cartões
def processar_mercado_dynamico(original_probabilities, market_type, selected_line, default_key_prefix):
    """
    Processa mercados dinâmicos (Over/Under, Escanteios, Cartões) para gerar probabilidades
    para a linha selecionada sem duplicação.
    
    Args:
        original_probabilities (dict): Probabilidades originais calculadas
        market_type (str): Tipo de mercado ('over_under', 'corners', 'cards')
        selected_line (float): Linha selecionada para o mercado (2.5, 9.5, 3.5, etc.)
        default_key_prefix (str): Prefixo para as chaves padrão ('over_2_5', 'over_9_5', etc.)
        
    Returns:
        dict: Probabilidades calculadas para a linha específica
    """
    import math
    
    # Verificar se temos o valor esperado para cálculo dinâmico
    expected_key = {
        'over_under': 'expected_goals',
        'corners': 'expected_corners',
        'cards': 'expected_cards'
    }.get(market_type)
    
    # Ajustar steepness com base no tipo de mercado
    steepness = {
        'over_under': 1.5,
        'corners': 0.8,
        'cards': 1.2
    }.get(market_type, 1.0)
    
    # Se temos o valor esperado, calcular dinamicamente para a linha específica
    if expected_key and expected_key in original_probabilities[market_type]:
        total_expected = original_probabilities[market_type][expected_key]
        
        # Função genérica para calcular probabilidades over/under
        def calculate_probs(expected, line, steep):
            over_prob = 1 / (1 + math.exp(-steep * (expected - line)))
            return over_prob * 100, (1-over_prob) * 100
        
        over_prob, under_prob = calculate_probs(total_expected, selected_line, steepness)
        
        return {
            f"Over {selected_line}": {"real": f"{over_prob:.1f}%", "implicit": "N/A"},
            f"Under {selected_line}": {"real": f"{under_prob:.1f}%", "implicit": "N/A"}
        }
    else:
        # Usar valores padrão com a linha específica
        over_key = f"over_{default_key_prefix}"
        under_key = f"under_{default_key_prefix}"
        
        return {
            f"Over {selected_line}": {"real": f"{original_probabilities[market_type][over_key]:.1f}%", "implicit": "N/A"},
            f"Under {selected_line}": {"real": f"{original_probabilities[market_type][under_key]:.1f}%", "implicit": "N/A"}
        }
# Atualizar a função que gera as probabilidades originais
def gerar_probabilidades_originais(original_probabilities):
    """
    Gera o dicionário de probabilidades formatadas a partir das probabilidades originais
    usando nomes de mercado mais claros e consistentes.
    
    Args:
        original_probabilities (dict): Probabilidades originais calculadas
        
    Returns:
        dict: Dicionário formatado de probabilidades
    """
    formatted_probs = {}
    
    # 1. Money Line (1X2)
    if "moneyline" in original_probabilities:
        formatted_probs["Money Line (1X2)"] = {
            "Casa": {"real": f"{original_probabilities['moneyline']['home_win']:.1f}%", "implicit": "N/A"},
            "Empate": {"real": f"{original_probabilities['moneyline']['draw']:.1f}%", "implicit": "N/A"},
            "Fora": {"real": f"{original_probabilities['moneyline']['away_win']:.1f}%", "implicit": "N/A"}
        }
    
    # 2. Chance Dupla (Double Chance)
    if "double_chance" in original_probabilities:
        formatted_probs["Chance Dupla"] = {
            "1X": {"real": f"{original_probabilities['double_chance']['home_or_draw']:.1f}%", "implicit": "N/A"},
            "12": {"real": f"{original_probabilities['double_chance']['home_or_away']:.1f}%", "implicit": "N/A"},
            "X2": {"real": f"{original_probabilities['double_chance']['away_or_draw']:.1f}%", "implicit": "N/A"}
        }
    
    # 3. Total de Gols (antigo Over/Under)
    if "over_under" in original_probabilities:
        formatted_probs["Total de Gols"] = {
            "Over 2.5": {"real": f"{original_probabilities['over_under']['over_2_5']:.1f}%", "implicit": "N/A"},
            "Under 2.5": {"real": f"{original_probabilities['over_under']['under_2_5']:.1f}%", "implicit": "N/A"}
        }
    
    # 4. Ambos Marcam
    if "btts" in original_probabilities:
        formatted_probs["Ambos Marcam"] = {
            "Sim": {"real": f"{original_probabilities['btts']['yes']:.1f}%", "implicit": "N/A"},
            "Não": {"real": f"{original_probabilities['btts']['no']:.1f}%", "implicit": "N/A"}
        }
    
    # 5. Total de Escanteios (antigo Escanteios)
    if "corners" in original_probabilities:
        formatted_probs["Total de Escanteios"] = {
            "Over 9.5": {"real": f"{original_probabilities['corners']['over_9_5']:.1f}%", "implicit": "N/A"},
            "Under 9.5": {"real": f"{original_probabilities['corners']['under_9_5']:.1f}%", "implicit": "N/A"}
        }
    
    # 6. Total de Cartões (antigo Cartões)
    if "cards" in original_probabilities:
        formatted_probs["Total de Cartões"] = {
            "Over 3.5": {"real": f"{original_probabilities['cards']['over_3_5']:.1f}%", "implicit": "N/A"},
            "Under 3.5": {"real": f"{original_probabilities['cards']['under_3_5']:.1f}%", "implicit": "N/A"}
        }
    
    return formatted_probs

# Função auxiliar para categorizar mercados para exibição
def categorizar_mercado(mercado_texto):
    """
    Categoriza um mercado com base no seu texto para garantir
    que seja atribuído à categoria correta.
    
    Args:
        mercado_texto (str): Texto do mercado
        
    Returns:
        str: Nome da categoria
    """
    texto_lower = mercado_texto.lower()
    
    # Verificar o tipo de mercado
    if "casa" in texto_lower or "empate" in texto_lower or "fora" in texto_lower or "1x2" in texto_lower:
        return "Money Line (1X2)"
    elif "1x" in texto_lower or "12" in texto_lower or "x2" in texto_lower or "dupla" in texto_lower:
        return "Chance Dupla"
    elif "over" in texto_lower or "under" in texto_lower:
        if "escanteio" in texto_lower or "corner" in texto_lower or any(str(n) in texto_lower for n in [8, 9, 10, 11, 12]):
            return "Total de Escanteios"
        elif "cartão" in texto_lower or "cartoes" in texto_lower or "card" in texto_lower or any(str(n) in texto_lower for n in [3, 4, 5, 6]):
            return "Total de Cartões"
        else:
            return "Total de Gols"
    elif "ambos" in texto_lower or "btts" in texto_lower or ("sim" in texto_lower and "não" in texto_lower):
        return "Ambos Marcam"
    
    # Fallback para categoria indefinida
    return "Outros"

# Coletando e organizando todos os mercados sem duplicação
def coletar_mercados_organizados(odd_lines, selected_markets):
    """
    Coleta e organiza todos os mercados em categorias apropriadas,
    removendo duplicações e garantindo formatação consistente.
    
    Args:
        odd_lines (list): Linhas de odds do input do usuário
        selected_markets (dict): Mercados selecionados pelo usuário
        
    Returns:
        dict: Mercados organizados por categoria
    """
    organized_markets = {
        "Money Line (1X2)": [],
        "Chance Dupla": [],
        "Total de Gols": [],
        "Ambos Marcam": [],
        "Total de Escanteios": [],
        "Total de Cartões": []
    }
    
    # Mapeamento inverso para verificar mercados selecionados
    inverse_mapping = {v: k for k, v in market_mapping.items()}
    
    # Processar cada linha de odds
    for line in odd_lines:
        # Limpar formatação da linha
        clean_line = limpar_marcadores_mercados(line)
        
        # Categorizar o mercado
        category = categorizar_mercado(clean_line)
        
        # Verificar se esta categoria está nos mercados selecionados
        market_key = None
        for cat, key in market_mapping.items():
            if cat == category:
                market_key = key
                break
        
        # Adicionar apenas se o mercado estiver selecionado
        if market_key and selected_markets.get(market_key, False):
            # Verificar duplicação
            market_text = clean_line.split('@')[0].strip() if '@' in clean_line else clean_line
            
            # Evitar duplicação dentro da mesma categoria
            existing_items = [item.split('@')[0].strip() for item in organized_markets[category]]
            if market_text not in existing_items:
                organized_markets[category].append(clean_line)
    
    return organized_markets

def format_analysis_response(analysis_text, home_team, away_team, selected_markets=None, original_probabilities=None):
    """
    Constrói uma análise limpa com INSERÇÃO FORÇADA das probabilidades originais
    
    Args:
        analysis_text: Texto da análise do GPT
        home_team: Nome do time da casa
        away_team: Nome do time visitante
        selected_markets: Dicionário com os mercados selecionados pelo usuário
        original_probabilities: Probabilidades originais calculadas
    """
    import re
    import logging
    import math
    
    logger = logging.getLogger("valueHunter.ai")
    logger.info(f"Formatando resposta da análise para {home_team} vs {away_team}")
    
    # Remover tags HTML e caracteres problemáticos
    for tag in ["<div", "</div", "<span", "</span", "class=", "id=", "style="]:
        analysis_text = analysis_text.replace(tag, "")
    
    # Estruturas para armazenar dados extraídos
    market_categories = {
        "Money Line (1X2)": [],
        "Chance Dupla": [],
        "Total de Gols": [],  # Renomeado de "Over/Under Gols"
        "Ambos Marcam": [],
        "Total de Escanteios": [],  # Renomeado de "Escanteios"
        "Total de Cartões": []  # Renomeado de "Cartões"
    }
    
    all_probabilities = {}
    opportunities = []
    confidence_level = "Não disponível"
    consistency_info = ""
    form_info = ""
    influence_info = ""
    
    # PARTE 1: EXTRAÇÃO DOS MERCADOS DISPONÍVEIS
    # ==========================================
    markets_section = ""
    market_section_found = False
    
    # Tentar diferentes padrões para encontrar a seção de mercados
    if "ANÁLISE DE MERCADOS DISPONÍVEIS" in analysis_text:
        try:
            markets_section = analysis_text.split("ANÁLISE DE MERCADOS DISPONÍVEIS")[1].split("PROBABILIDADES CALCULADAS")[0]
            market_section_found = True
        except:
            logger.warning("Falha ao extrair seção de mercados após encontrar o cabeçalho")
    
    if not market_section_found and "Análise de Mercados" in analysis_text:
        try:
            markets_section = analysis_text.split("Análise de Mercados")[1].split("Probabilidades")[0]
            market_section_found = True
        except:
            logger.warning("Falha ao extrair seção de mercados (alternativo)")
    
    # Forçar separação de mercados baseada em padrões específicos
    if market_section_found:
        lines = markets_section.strip().split("\n")
        
        # Classificadores mais específicos para cada tipo de mercado
        money_line_items = []
        chance_dupla_items = []
        total_gols_items = []
        ambos_marcam_items = []
        total_escanteios_items = []
        total_cartoes_items = []
        
        current_section = None
        for line in lines:
            line = line.strip()
            
            # Detectar cabeçalhos de seção
            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1].lower()
                
                if "1x2" in section_name or "money" in section_name:
                    current_section = "money_line"
                elif "dupla" in section_name or "chance" in section_name:
                    current_section = "chance_dupla"
                elif "gol" in section_name:
                    current_section = "total_gols"
                elif "btts" in section_name or "ambos" in section_name or "marcam" in section_name:
                    current_section = "ambos_marcam"
                elif "escanteio" in section_name or "corner" in section_name:
                    current_section = "total_escanteios"
                elif "cartão" in section_name or "cartões" in section_name or "card" in section_name:
                    current_section = "total_cartoes"
                else:
                    current_section = None
                
                continue
                
            # Pular linhas vazias ou sem odds
            if not line or "@" not in line:
                continue
            
            # Remover marcadores duplicados e limpar a linha
            clean_line = line.replace("• •", "•").replace("••", "•").strip()
            if not clean_line.startswith("•"):
                clean_line = "• " + clean_line
            
            # FORÇAR CLASSIFICAÇÃO com base no conteúdo da linha
            classified = False
            
            # 1. Money Line - verificamos primeiro porque é o mais específico
            if (home_team in line or "Casa" in line) and "@" in line:
                money_line_items.append(clean_line)
                classified = True
            elif "Empate" in line and "@" in line and "X2" not in line and "1X" not in line:
                money_line_items.append(clean_line)
                classified = True
            elif (away_team in line or "Fora" in line) and "@" in line and "X2" not in line and "12" not in line:
                money_line_items.append(clean_line)
                classified = True
            
            # 2. Chance Dupla - verificar padrões específicos
            elif ("1X" in line or "X1" in line) and "@" in line:
                chance_dupla_items.append(clean_line)
                classified = True
            elif ("12" in line or "21" in line) and "@" in line:
                chance_dupla_items.append(clean_line)
                classified = True
            elif ("X2" in line or "2X" in line) and "@" in line:
                chance_dupla_items.append(clean_line)
                classified = True
            elif "Dupla" in line and "@" in line:
                chance_dupla_items.append(clean_line)
                classified = True
            
            # 3. Ambos Marcam (BTTS) - procurar padrões específicos
            elif "Sim" in line and "@" in line and "BTTS" in line:
                ambos_marcam_items.append(clean_line)
                classified = True
            elif "Não" in line and "@" in line and "BTTS" in line:
                ambos_marcam_items.append(clean_line)
                classified = True
            elif "Ambos" in line and "marcam" in line.lower() and "@" in line:
                ambos_marcam_items.append(clean_line)
                classified = True
            elif "Sim" in line and "@" in line and any("Não" in l and "@" in l for l in lines):
                # Se há um "Sim" e um "Não" como opções, provavelmente é BTTS
                if not any("over" in line.lower() or "under" in line.lower() for l in [line]):
                    ambos_marcam_items.append(clean_line)
                    classified = True
            elif "Não" in line and "@" in line and any("Sim" in l and "@" in l for l in lines):
                # Par do caso acima
                if not any("over" in line.lower() or "under" in line.lower() for l in [line]):
                    ambos_marcam_items.append(clean_line)
                    classified = True
            
            # 4. Total de Escanteios - verificação explícita
            elif "escanteio" in line.lower() or "corner" in line.lower():
                total_escanteios_items.append(clean_line)
                classified = True
            elif "over" in line.lower() and any(str(n) in line for n in [8, 9, 10, 11, 12]):
                # Linhas típicas de escanteios são Over/Under 8.5, 9.5, 10.5, etc.
                total_escanteios_items.append(clean_line)
                classified = True
            elif "under" in line.lower() and any(str(n) in line for n in [8, 9, 10, 11, 12]):
                total_escanteios_items.append(clean_line)
                classified = True
            
            # 5. Total de Cartões - verificação explícita
            elif "cartão" in line.lower() or "cartões" in line.lower() or "card" in line.lower():
                total_cartoes_items.append(clean_line)
                classified = True
            elif "over" in line.lower() and any(str(n) in line for n in [3, 4, 5, 6]):
                # Linhas típicas de cartões são Over/Under 3.5, 4.5, 5.5, etc.
                total_cartoes_items.append(clean_line)
                classified = True
            elif "under" in line.lower() and any(str(n) in line for n in [3, 4, 5, 6]):
                total_cartoes_items.append(clean_line)
                classified = True
            
            # 6. Total de Gols - qualquer over/under que não seja escanteios ou cartões
            elif ("over" in line.lower() or "under" in line.lower()) and "@" in line:
                # Verificar se menciona explicitamente gols
                if "gol" in line.lower():
                    total_gols_items.append(clean_line)
                    classified = True
                # Verificar as linhas típicas de gols 0.5, 1.5, 2.5, 3.5, 4.5
                elif any(f"{n}.5" in line for n in [0, 1, 2, 3, 4]):
                    # Se não for um mercado explícito de cartões ou escanteios
                    if not any(termo in line.lower() for termo in ["cartão", "cartões", "card", "escanteio", "corner"]):
                        total_gols_items.append(clean_line)
                        classified = True
            
            # Se não foi classificado por nenhum dos critérios específicos, usar a seção atual
            if not classified and current_section:
                if current_section == "money_line":
                    money_line_items.append(clean_line)
                elif current_section == "chance_dupla":
                    chance_dupla_items.append(clean_line)
                elif current_section == "total_gols":
                    total_gols_items.append(clean_line)
                elif current_section == "ambos_marcam":
                    ambos_marcam_items.append(clean_line)
                elif current_section == "total_escanteios":
                    total_escanteios_items.append(clean_line)
                elif current_section == "total_cartoes":
                    total_cartoes_items.append(clean_line)
        
        # Atribuir os itens classificados às categorias corretas
        market_categories["Money Line (1X2)"] = money_line_items
        market_categories["Chance Dupla"] = chance_dupla_items
        market_categories["Total de Gols"] = total_gols_items
        market_categories["Ambos Marcam"] = ambos_marcam_items
        market_categories["Total de Escanteios"] = total_escanteios_items
        market_categories["Total de Cartões"] = total_cartoes_items    
    
   # PARTE 2: EXTRAÇÃO DE PROBABILIDADES
    # ===================================
    probs_section = ""
    if "PROBABILIDADES CALCULADAS" in analysis_text:
        try:
            probs_section = analysis_text.split("PROBABILIDADES CALCULADAS")[1].split("OPORTUNIDADES")[0]
        except:
            logger.warning("Não foi possível extrair seção de probabilidades calculadas")
    
    # Detectar e processar tabelas de probabilidades
    if probs_section:
        # Tentar extrair tabelas formatadas
        tables = re.split(r'\[([^]]+)\]', probs_section)
        
        # Processar tabelas encontradas
        for i in range(1, len(tables), 2):
            if i+1 < len(tables):
                table_name = tables[i].strip()
                table_content = tables[i+1].strip()
                
                # Determinar o tipo de mercado para esta tabela
                market_type = None
                if "1X2" in table_name or "Money" in table_name or "Moneyline" in table_name:
                    market_type = "Money Line (1X2)"
                elif "Dupla" in table_name or "Double" in table_name:
                    market_type = "Chance Dupla"
                elif "Gol" in table_name:
                    market_type = "Total de Gols"
                elif "BTTS" in table_name or "Ambos" in table_name or "marcam" in table_name.lower():
                    market_type = "Ambos Marcam"
                elif "Escanteio" in table_name or "Corner" in table_name:
                    market_type = "Total de Escanteios"
                elif "Cartão" in table_name or "Cartões" in table_name or "Card" in table_name:
                    market_type = "Total de Cartões"
                
                if market_type:
                    all_probabilities[market_type] = {}
                    
                    # Extrair linhas da tabela formatada
                    table_rows = re.findall(r'│([^│]+)│([^│]+)│([^│]+)│', table_content)
                    
                    for row in table_rows:
                        if "MERCADO" in row[0] or "────" in row[0]:
                            continue
                        
                        option = row[0].strip()
                        real_prob = row[1].strip()
                        impl_prob = row[2].strip()
                        
                        all_probabilities[market_type][option] = {
                            "real": real_prob,
                            "implicit": impl_prob
                        }
    
    # PARTE 3: EXTRAÇÃO DE OPORTUNIDADES IDENTIFICADAS
    # ===============================================
    if "OPORTUNIDADES IDENTIFICADAS" in analysis_text:
        try:
            opps_section = analysis_text.split("OPORTUNIDADES IDENTIFICADAS")[1].split("NÍVEL DE CONFIANÇA")[0]
            
            for line in opps_section.strip().split("\n"):
                line = line.strip().replace("•", "").replace("-", "").replace("▔", "").strip()
                if line and len(line) > 5:
                    opportunities.append("• " + line)
        except Exception as e:
            logger.warning(f"Erro ao extrair seção de oportunidades: {str(e)}")
    
    # PARTE 4: EXTRAÇÃO DO NÍVEL DE CONFIANÇA
    # ======================================
    if "NÍVEL DE CONFIANÇA" in analysis_text:
        try:
            conf_section = analysis_text.split("NÍVEL DE CONFIANÇA")[1]
            
            # Extrair o nível (Baixo/Médio/Alto)
            confidence_match = re.search(r'(?:GERAL|GLOBAL)[:]\s*(\w+)', conf_section, re.IGNORECASE)
            if confidence_match:
                confidence_level = confidence_match.group(1).strip()
            else:
                # Procurar por padrões alternativos
                for level in ["Baixo", "Médio", "Alto"]:
                    if level in conf_section[:100]:
                        confidence_level = level
                        break
            
            # Extrair componentes
            if "CONSISTÊNCIA" in conf_section:
                consistency_parts = conf_section.split("CONSISTÊNCIA")[1].split("FORMA")[0]
                consistency_info = consistency_parts.strip().replace(":", "").replace("**", "").replace("►", "")
            
            if "FORMA" in conf_section:
                form_parts = conf_section.split("FORMA")[1].split("INFLUÊNCIA")[0]
                form_info = form_parts.strip().replace(":", "").replace("**", "").replace("►", "")
            
            if "INFLUÊNCIA" in conf_section:
                influence_parts = conf_section.split("INFLUÊNCIA")[1]
                if "©" in influence_parts:
                    influence_parts = influence_parts.split("©")[0]
                influence_info = influence_parts.strip().replace(":", "").replace("**", "").replace("►", "")
        except Exception as e:
            logger.warning(f"Erro ao extrair nível de confiança: {str(e)}")
    
    # PARTE 5: INSERIR PROBABILIDADES ORIGINAIS CALCULADAS SE DISPONÍVEIS
    # =================================================================
    if original_probabilities:
        logger.info("Inserindo probabilidades originais calculadas forçadamente")
        
        # Converter probabilidades originais para o formato necessário
        formatted_probs = {}
        
        # 1. Money Line (1X2)
        if "moneyline" in original_probabilities:
            formatted_probs["Money Line (1X2)"] = {
                "Casa": {"real": f"{original_probabilities['moneyline']['home_win']:.1f}%", "implicit": "N/A"},
                "Empate": {"real": f"{original_probabilities['moneyline']['draw']:.1f}%", "implicit": "N/A"},
                "Fora": {"real": f"{original_probabilities['moneyline']['away_win']:.1f}%", "implicit": "N/A"}
            }
        
        # 2. Chance Dupla (Double Chance)
        if "double_chance" in original_probabilities:
            formatted_probs["Chance Dupla"] = {
                "1X": {"real": f"{original_probabilities['double_chance']['home_or_draw']:.1f}%", "implicit": "N/A"},
                "12": {"real": f"{original_probabilities['double_chance']['home_or_away']:.1f}%", "implicit": "N/A"},
                "X2": {"real": f"{original_probabilities['double_chance']['away_or_draw']:.1f}%", "implicit": "N/A"}
            }
        
        # 3. Total de Gols (Over/Under)
        if "over_under" in original_probabilities:
            # Identificar a linha selecionada nos mercados
            selected_line = 2.5  # Linha padrão
            
            for item in market_categories["Total de Gols"]:
                line_match = re.search(r'Over\s+(\d+\.?\d+)', item, re.IGNORECASE)
                if line_match:
                    try:
                        selected_line = float(line_match.group(1))
                        break
                    except (ValueError, TypeError):
                        pass
            
            logger.info(f"Linha de gols selecionada: {selected_line}")
            
            # Calcular probabilidades para a linha específica
            if "expected_goals" in original_probabilities["over_under"]:
                expected_goals = original_probabilities["over_under"]["expected_goals"]
                
                # Calcular over/under para a linha específica
                steepness = 1.5  # Ajuste para gols
                over_prob = 1 / (1 + math.exp(-steepness * (expected_goals - selected_line)))
                under_prob = 1 - over_prob
                
                formatted_probs["Total de Gols"] = {
                    f"Over {selected_line}": {"real": f"{over_prob * 100:.1f}%", "implicit": "N/A"},
                    f"Under {selected_line}": {"real": f"{under_prob * 100:.1f}%", "implicit": "N/A"}
                }
            else:
                # Usar os valores padrão para 2.5, mas adaptar para a linha selecionada
                formatted_probs["Total de Gols"] = {
                    f"Over {selected_line}": {"real": f"{original_probabilities['over_under']['over_2_5']:.1f}%", "implicit": "N/A"},
                    f"Under {selected_line}": {"real": f"{original_probabilities['over_under']['under_2_5']:.1f}%", "implicit": "N/A"}
                }
        
        # 4. BTTS
        if "btts" in original_probabilities:
            formatted_probs["Ambos Marcam"] = {
                "Sim": {"real": f"{original_probabilities['btts']['yes']:.1f}%", "implicit": "N/A"},
                "Não": {"real": f"{original_probabilities['btts']['no']:.1f}%", "implicit": "N/A"}
            }
        
        # 5. Total de Escanteios
        if "corners" in original_probabilities:
            # Identificar a linha selecionada nos mercados
            selected_line = 9.5  # Linha padrão
            
            for item in market_categories["Total de Escanteios"]:
                line_match = re.search(r'Over\s+(\d+\.?\d+)', item, re.IGNORECASE)
                if line_match:
                    try:
                        selected_line = float(line_match.group(1))
                        break
                    except (ValueError, TypeError):
                        pass
            
            logger.info(f"Linha de escanteios selecionada: {selected_line}")
            
            # Calcular probabilidades para a linha específica
            if "expected_corners" in original_probabilities["corners"]:
                expected_corners = original_probabilities["corners"]["expected_corners"]
                
                # Calcular over/under para a linha específica
                steepness = 0.8  # Ajuste para escanteios
                over_prob = 1 / (1 + math.exp(-steepness * (expected_corners - selected_line)))
                under_prob = 1 - over_prob
                
                formatted_probs["Total de Escanteios"] = {
                    f"Over {selected_line}": {"real": f"{over_prob * 100:.1f}%", "implicit": "N/A"},
                    f"Under {selected_line}": {"real": f"{under_prob * 100:.1f}%", "implicit": "N/A"}
                }
            else:
                # Usar os valores padrão para 9.5, mas adaptar para a linha selecionada
                formatted_probs["Total de Escanteios"] = {
                    f"Over {selected_line}": {"real": f"{original_probabilities['corners']['over_9_5']:.1f}%", "implicit": "N/A"},
                    f"Under {selected_line}": {"real": f"{original_probabilities['corners']['under_9_5']:.1f}%", "implicit": "N/A"}
                }
        
        # 6. Total de Cartões
        if "cards" in original_probabilities:
            # Identificar a linha selecionada nos mercados
            selected_line = 3.5  # Linha padrão
            
            for item in market_categories["Total de Cartões"]:
                line_match = re.search(r'Over\s+(\d+\.?\d+)', item, re.IGNORECASE)
                if line_match:
                    try:
                        selected_line = float(line_match.group(1))
                        break
                    except (ValueError, TypeError):
                        pass
            
            logger.info(f"Linha de cartões selecionada: {selected_line}")
            
            # Calcular probabilidades para a linha específica
            if "expected_cards" in original_probabilities["cards"]:
                expected_cards = original_probabilities["cards"]["expected_cards"]
                
                # Calcular over/under para a linha específica
                steepness = 1.2  # Ajuste para cartões
                over_prob = 1 / (1 + math.exp(-steepness * (expected_cards - selected_line)))
                under_prob = 1 - over_prob
                
                formatted_probs["Total de Cartões"] = {
                    f"Over {selected_line}": {"real": f"{over_prob * 100:.1f}%", "implicit": "N/A"},
                    f"Under {selected_line}": {"real": f"{under_prob * 100:.1f}%", "implicit": "N/A"}
                }
            else:
                # Usar os valores padrão para 3.5, mas adaptar para a linha selecionada
                formatted_probs["Total de Cartões"] = {
                    f"Over {selected_line}": {"real": f"{original_probabilities['cards']['over_3_5']:.1f}%", "implicit": "N/A"},
                    f"Under {selected_line}": {"real": f"{original_probabilities['cards']['under_3_5']:.1f}%", "implicit": "N/A"}
                }
                
        # Adicionar probabilidades implícitas das odds
        for category, markets in market_categories.items():
            if category in formatted_probs:
                # Extrair probabilidades implícitas dos mercados listados
                for market_line in markets:
                    # Extrair o nome da opção e a odds implícita
                    parts = market_line.split("@")
                    if len(parts) >= 2:
                        option_text = parts[0].replace("•", "").strip()
                        # Extrair probabilidade implícita se estiver no formato (XX.X%)
                        impl_match = re.search(r'\(Implícita:\s*(\d+\.?\d*)%\)', market_line)
                        if impl_match:
                            impl_prob = impl_match.group(1) + "%"
                            
                            # Identificar a opção correta no dicionário
                            for opt in formatted_probs[category]:
                                # Verificar se a opção atual contém o nome da opção no texto
                                if opt.lower() in option_text.lower() or any(term.lower() in option_text.lower() for term in opt.lower().split()):
                                    formatted_probs[category][opt]["implicit"] = impl_prob
                                    break
                            
                            # Tratamento especial para casa/fora
                            if "casa" in option_text.lower() and "Casa" in formatted_probs[category]:
                                formatted_probs[category]["Casa"]["implicit"] = impl_prob
                            elif "fora" in option_text.lower() and "Fora" in formatted_probs[category]:
                                formatted_probs[category]["Fora"]["implicit"] = impl_prob
                            elif home_team in option_text and "Casa" in formatted_probs[category]:
                                formatted_probs[category]["Casa"]["implicit"] = impl_prob
                            elif away_team in option_text and "Fora" in formatted_probs[category]:
                                formatted_probs[category]["Fora"]["implicit"] = impl_prob
                                
                            # Para mercados de linhas (gols, escanteios, cartões)
                            if category in ["Total de Gols", "Total de Escanteios", "Total de Cartões"]:
                                for opt in formatted_probs[category]:
                                    if ("Over" in opt and "Over" in option_text) or ("Under" in opt and "Under" in option_text):
                                        # Extrair valor da linha se possível
                                        line_in_opt = re.search(r'(\d+\.?\d*)', opt)
                                        line_in_text = re.search(r'(\d+\.?\d*)', option_text)
                                        
                                        if line_in_opt and line_in_text:
                                            # Se a linha é a mesma ou não especificada no texto
                                            if line_in_opt.group(1) == line_in_text.group(1) or not line_in_text:
                                                formatted_probs[category][opt]["implicit"] = impl_prob
                                                break
        
        # Substituir ou juntar com as probabilidades extraídas da resposta
        for category, options in formatted_probs.items():
            if category not in all_probabilities or len(all_probabilities[category]) == 0:
                # Se não tiver probabilidades para esta categoria, usar as originais
                all_probabilities[category] = options
            else:
                # Se já tiver, verificar se há informações faltantes
                for option, probs in options.items():
                    if option not in all_probabilities[category]:
                        all_probabilities[category][option] = probs
                    elif "real" not in all_probabilities[category][option] or all_probabilities[category][option]["real"] == "N/A":
                        all_probabilities[category][option]["real"] = probs["real"]
                        
        # CRUCIAL: GARANTIR QUE TEMOS TODAS AS CATEGORIAS NECESSÁRIAS BASEADAS NOS MERCADOS SELECIONADOS
        if selected_markets:
            # Mapear mercados selecionados para categorias
            category_map = {
                "money_line": "Money Line (1X2)",
                "chance_dupla": "Chance Dupla",
                "over_under": "Total de Gols",
                "ambos_marcam": "Ambos Marcam", 
                "escanteios": "Total de Escanteios",
                "cartoes": "Total de Cartões"
            }
            
            # Garantir que temos uma seção para cada mercado selecionado
            for market_key, is_selected in selected_markets.items():
                if is_selected and market_key in category_map:
                    category_name = category_map[market_key]
                    if category_name not in all_probabilities and category_name in formatted_probs:
                        all_probabilities[category_name] = formatted_probs[category_name]
    
       # PARTE 6: PREPARAR E CORRIGIR OPORTUNIDADES IDENTIFICADAS
        # ====================================================
        corrected_opportunities = []
        
        # Corrigir linhas das oportunidades para usar as linhas corretas de over/under
        for opportunity in opportunities:
            # Verificar se menciona uma linha incorreta
            corrected_opp = opportunity
        
        # Corrigir linhas de gols
        if "Gols" in opportunity or "gols" in opportunity:
            # Identificar a linha de gols correta para usar
            gols_line = 2.5  # Valor padrão
            for item in market_categories["Total de Gols"]:
                line_match = re.search(r'Over\s+(\d+\.?\d+)', item, re.IGNORECASE)
                if line_match:
                    try:
                        gols_line = float(line_match.group(1))
                        break
                    except (ValueError, TypeError):
                        pass
        # Substituir a linha nas oportunidades
            opp_line_match = re.search(r'Over\s+(\d+\.?\d+)\s+Gols', corrected_opp, re.IGNORECASE)
            if opp_line_match:
                current_line = opp_line_match.group(1)
                if current_line != str(gols_line):
                    corrected_opp = corrected_opp.replace(f"Over {current_line} Gols", f"Over {gols_line} Gols")
            
        # Corrigir linhas de escanteios        
        elif "Escanteio" in opportunity or "escanteio" in opportunity or "Corner" in opportunity or "corner" in opportunity:
            # Identificar a linha de escanteios correta
            corners_line = 9.5  # Valor padrão
            for item in market_categories["Total de Escanteios"]:
                line_match = re.search(r'Over\s+(\d+\.?\d+)', item, re.IGNORECASE)
                if line_match:
                    try:
                        corners_line = float(line_match.group(1))
                        break
                    except (ValueError, TypeError):
                        pass
                        
            # Substituir a linha nas oportunidades
            opp_line_match = re.search(r'Over\s+(\d+\.?\d+)', corrected_opp, re.IGNORECASE)
            if opp_line_match:
                current_line = opp_line_match.group(1)
                if current_line != str(corners_line):
                    corrected_opp = corrected_opp.replace(f"Over {current_line}", f"Over {corners_line}")
                    
        # Corrigir linhas de cartões
        elif "Cartões" in opportunity or "cartões" in opportunity or "Cartão" in opportunity or "cartão" in opportunity:
            # Identificar a linha de cartões correta
            cards_line = 3.5  # Valor padrão
            for item in market_categories["Total de Cartões"]:
                line_match = re.search(r'Over\s+(\d+\.?\d+)', item, re.IGNORECASE)
                if line_match:
                    try:
                        cards_line = float(line_match.group(1))
                        break
                    except (ValueError, TypeError):
                        pass
                        
            # Substituir a linha nas oportunidades
            opp_line_match = re.search(r'Over\s+(\d+\.?\d+)', corrected_opp, re.IGNORECASE)
            if opp_line_match:
                current_line = opp_line_match.group(1)
                if current_line != str(cards_line):
                    corrected_opp = corrected_opp.replace(f"Over {current_line}", f"Over {cards_line}")
                    
        corrected_opportunities.append(corrected_opp)
                
    # PARTE 7: CONSTRUÇÃO DO RELATÓRIO FINAL FORMATADO
    # ==============================================
    clean_report = f"""
ANÁLISE DE PARTIDA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{home_team} vs {away_team}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANÁLISE DE MERCADOS DISPONÍVEIS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"""
    
    # Adicionar mercados organizados por categoria
    any_markets = False
    for category, markets in market_categories.items():
        if markets:
            any_markets = True
            clean_report += f"\n\n[{category}]"
            for market in markets:
                clean_report += f"\n{market}"
    
    if not any_markets:
        clean_report += "\nInformações de mercados não disponíveis."
    
    clean_report += f"""

PROBABILIDADES CALCULADAS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"""
    
    # Mapeamento entre categorias e mercados selecionados
    market_mapping = {
        "Money Line (1X2)": "money_line",
        "Chance Dupla": "chance_dupla",
        "Total de Gols": "gols",
        "Ambos Marcam": "ambos_marcam",
        "Total de Escanteios": "escanteios",
        "Total de Cartões": "cartoes"
    }
    
    # Adicionar tabelas de probabilidades APENAS para mercados selecionados
    any_probs = False
    for category, options in all_probabilities.items():
        # Verificar se este mercado foi selecionado pelo usuário
        market_key = market_mapping.get(category)
        is_selected = selected_markets.get(market_key, False) if selected_markets else True
        
        if options and is_selected:
            any_probs = True
            clean_report += f"""

[{category}]
┌────────────┬────────────┬────────────┐
│  MERCADO   │  REAL (%)  │ IMPLÍCITA  │
├────────────┼────────────┼────────────┤"""
            
            for option, probs in options.items():
                option_display = option if len(option) <= 8 else option[:7] + "."
                clean_report += f"""
│  {option_display.ljust(8)} │ {probs['real'].center(10)} │ {probs['implicit'].center(10)} │"""
            
            clean_report += """
└────────────┴────────────┴────────────┘"""
    
    if not any_probs:
        clean_report += "\nProbabilidades não disponíveis para análise."
    
    clean_report += f"""

OPORTUNIDADES IDENTIFICADAS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
"""
    
    # Adicionar oportunidades corrigidas
    if corrected_opportunities:
        for opp in corrected_opportunities:
            clean_report += f"{opp}\n"
    else:
        clean_report += "Nenhuma oportunidade de valor identificada.\n"
    
    clean_report += f"""
NÍVEL DE CONFIANÇA GERAL: {confidence_level}
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔

► CONSISTÊNCIA: {consistency_info}

► FORMA: {form_info}

► INFLUÊNCIA: {influence_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     © RELATÓRIO VALUE HUNTER DE ANÁLISE ESPORTIVA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    return clean_report
    def determine_market_type(table_name, table_content):
        """
        Determina o tipo de mercado com base no nome da tabela e seu conteúdo
        """
        if ("Money" in table_name or "1X2" in table_name or 
            "Casa" in table_content or "Empate" in table_content or
            home_team in table_content or away_team in table_content):
            return "Money Line (1X2)"
            
        elif ("Dupla" in table_name or "1X" in table_content or 
              "12" in table_content or "X2" in table_content):
            return "Chance Dupla"
            
        elif ("Ambos" in table_name or "BTTS" in table_name or 
              ("Sim" in table_content and "Não" in table_content)):
            return "Ambos Marcam"
            
        elif ("Escanteio" in table_name.lower() or "Corner" in table_name or 
              "escanteio" in table_content.lower() or "corner" in table_content.lower()):
            return "Escanteios"
            
        elif ("Cartão" in table_name or "Cartões" in table_name or 
              "cartão" in table_content.lower() or "cartões" in table_content.lower()):
            return "Cartões"
            
        elif "Over" in table_content or "Under" in table_content:
            # Verificar contexto para determinar tipo de over/under
            if any(f"{n}.5" in table_content for n in [8, 9, 10, 11, 12]):
                return "Escanteios"
            elif any(f"{n}.5" in table_content for n in [3, 4, 5, 6]):
                if "cartão" in table_content.lower() or "cartões" in table_content.lower():
                    return "Cartões"
                # Pode ser gols ou cartões, verificar contexto
                for line in table_content.split("\n"):
                    if "cartão" in line.lower() or "cartões" in line.lower():
                        return "Cartões"
            
            # Se não encontrou escanteios ou cartões, assume que é gols
            return "Over/Under Gols"
        
        # Padrão para caso não consiga identificar
        return "Outros"
    
    # Padrões melhorados para detecção
    over_under_pattern = re.compile(r'(?:Over|Under)\s+(\d+(?:\.\d+)?)')
    
    # Extrair e categorizar mercados disponíveis
    markets_section = ""
    if "MERCADOS DISPONÍVEIS" in analysis_text:
        try:
            markets_section = analysis_text.split("MERCADOS DISPONÍVEIS")[1].split("PROBABILIDADES")[0]
        except:
            try:
                markets_section = analysis_text.split("ANÁLISE DE MERCADOS DISPONÍVEIS")[1].split("PROBABILIDADES CALCULADAS")[0]
            except:
                logger.warning("Não foi possível extrair seção de mercados disponíveis")
    elif "Análise de Mercados" in analysis_text:
        try:
            markets_section = analysis_text.split("Análise de Mercados")[1].split("Probabilidades")[0]
        except:
            logger.warning("Não foi possível extrair seção de mercados disponíveis (alternativo)")
    
    if markets_section:
        lines = markets_section.strip().split("\n")
        
        # Pré-processamento para identificar seções específicas
        current_section = None
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detectar cabeçalhos de seção
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]  # Remover colchetes
                continue
                
            # Limpar linha
            clean_line = line.replace("•", "").replace("-", "").strip()
            if not clean_line or "@" not in clean_line:
                continue
            
            # Se temos uma seção definida, usamos ela
            if current_section and current_section in market_categories:
                market_categories[current_section].append("• " + clean_line)
                continue
            
            # Categorização baseada no conteúdo da linha
            if "escanteio" in clean_line.lower() or "corner" in clean_line.lower():
                market_categories["Escanteios"].append("• " + clean_line)
            elif "cartão" in clean_line.lower() or "cartões" in clean_line.lower() or "card" in clean_line.lower():
                market_categories["Cartões"].append("• " + clean_line)
            elif "1X" in clean_line or "12" in clean_line or "X2" in clean_line or "Dupla" in clean_line:
                market_categories["Chance Dupla"].append("• " + clean_line)
            elif ("Sim" in clean_line and "@" in clean_line) or ("Não" in clean_line and "@" in clean_line) or "BTTS" in clean_line:
                market_categories["Ambos Marcam"].append("• " + clean_line)
            elif clean_line.startswith(("Casa", home_team)) or ("Empate" in clean_line) or clean_line.startswith(("Fora", away_team)):
                market_categories["Money Line (1X2)"].append("• " + clean_line)
            elif "Over" in clean_line or "Under" in clean_line:
                # Verificar contexto para over/under
                if "escanteio" in clean_line.lower() or "corner" in clean_line.lower():
                    market_categories["Escanteios"].append("• " + clean_line)
                elif "cartão" in clean_line.lower() or "cartões" in clean_line.lower() or "card" in clean_line.lower():
                    market_categories["Cartões"].append("• " + clean_line)
                else:
                    market_categories["Over/Under Gols"].append("• " + clean_line)
            else:
                # Caso não consiga categorizar
                market_categories["Money Line (1X2)"].append("• " + clean_line)
    
    # Extrair todas as probabilidades
    probs_section = ""
    if "PROBABILIDADES CALCULADAS" in analysis_text:
        try:
            probs_section = analysis_text.split("PROBABILIDADES CALCULADAS")[1].split("OPORTUNIDADES")[0]
        except:
            logger.warning("Não foi possível extrair seção de probabilidades calculadas")
    
    if probs_section:
        # Detectar e separar tabelas de probabilidades
        tables = re.split(r'\[([^]]+)\]', probs_section)
        
        # Processar tabelas
        for i in range(1, len(tables), 2):
            if i+1 < len(tables):
                table_name = tables[i].strip()
                table_content = tables[i+1].strip()
                
                # Detectar o tipo de mercado para cada tabela
                market_type = determine_market_type(table_name, table_content)
                
                # Se identificamos o tipo de mercado, vamos processar a tabela
                if market_type:
                    all_probabilities[market_type] = {}
                    
                    # Extrair linhas da tabela
                    table_rows = re.findall(r'│([^│]+)│([^│]+)│([^│]+)│', table_content)
                    
                    for row in table_rows:
                        # Ignorar cabeçalho
                        if "MERCADO" in row[0] or "────" in row[0]:
                            continue
                            
                        option = row[0].strip()
                        real_prob = row[1].strip()
                        impl_prob = row[2].strip()
                        
                        all_probabilities[market_type][option] = {
                            "real": real_prob,
                            "implicit": impl_prob
                        }
    
    # Extrair oportunidades identificadas
    if "OPORTUNIDADES IDENTIFICADAS" in analysis_text:
        try:
            opps_section = analysis_text.split("OPORTUNIDADES IDENTIFICADAS")[1].split("NÍVEL DE CONFIANÇA")[0]
            
            for line in opps_section.strip().split("\n"):
                line = line.strip().replace("•", "").replace("-", "").replace("▔", "").strip()
                if line and len(line) > 5:
                    opportunities.append("• " + line)
        except:
            logger.warning("Erro ao extrair oportunidades identificadas")
    
    # Extrair nível de confiança e componentes
    if "NÍVEL DE CONFIANÇA" in analysis_text:
        try:
            conf_section = analysis_text.split("NÍVEL DE CONFIANÇA")[1]
            
            # Extrair o nível (Baixo/Médio/Alto)
            if ":" in conf_section[:50]:
                confidence_level = conf_section.split(":")[1].split("\n")[0].strip().replace("**", "")
            
            # Extrair componentes (remover caracteres extras)
            if "CONSISTÊNCIA" in conf_section:
                consistency_parts = conf_section.split("CONSISTÊNCIA")[1].split("FORMA")[0]
                consistency_info = consistency_parts.strip().replace(":", "").replace("**", "").replace("►", "")
            
            if "FORMA" in conf_section:
                form_parts = conf_section.split("FORMA")[1].split("INFLUÊNCIA")[0]
                form_info = form_parts.strip().replace(":", "").replace("**", "").replace("►", "")
            
            if "INFLUÊNCIA" in conf_section:
                influence_parts = conf_section.split("INFLUÊNCIA")[1]
                if "©" in influence_parts:
                    influence_parts = influence_parts.split("©")[0]
                influence_info = influence_parts.strip().replace(":", "").replace("**", "").replace("►", "")
        except:
            logger.warning("Erro ao extrair nível de confiança")
    
    # Construir o relatório limpo e organizado
    clean_report = f"""
📊 ANÁLISE DE PARTIDA 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚽ {home_team} 🆚 {away_team} ⚽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 ANÁLISE DE MERCADOS DISPONÍVEIS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"""
    
    # Adicionar mercados organizados por categoria
    any_markets = False
    for category, markets in market_categories.items():
        if markets:
            any_markets = True
            clean_report += f"\n\n[{category}]"
            for market in markets:
                clean_report += f"\n{market}"
    
    if not any_markets:
        clean_report += "\nInformações de mercados não disponíveis."
    
    clean_report = f"""
📊 ANÁLISE DE PARTIDA 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚽ {home_team} 🆚 {away_team} ⚽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 ANÁLISE DE MERCADOS DISPONÍVEIS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"""
    
    # Adicionar mercados organizados por categoria
    any_markets = False
    for category, markets in market_categories.items():
        if markets:
            any_markets = True
            clean_report += f"\n\n[{category}]"
            for market in markets:
                clean_report += f"\n{market}"
    
    if not any_markets:
        clean_report += "\nInformações de mercados não disponíveis."
    
    clean_report += f"""

🔄 PROBABILIDADES CALCULADAS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"""
    
    # Mapeamento entre categorias e mercados selecionados
    market_mapping = {
        "Money Line (1X2)": "money_line",
        "Chance Dupla": "chance_dupla",
        "Over/Under Gols": "over_under",
        "Ambos Marcam": "ambos_marcam",
        "Escanteios": "escanteios",
        "Cartões": "cartoes"
    }
    
    # Adicionar tabelas de probabilidades APENAS para mercados selecionados
    any_probs = False
    for category, options in all_probabilities.items():
        # Verificar se este mercado foi selecionado pelo usuário
        market_key = market_mapping.get(category)
        is_selected = selected_markets.get(market_key, False) if selected_markets else True
        
        if options and is_selected:
            any_probs = True
            clean_report += f"""

[{category}]
┌────────────┬────────────┬────────────┐
│  MERCADO   │  REAL (%)  │ IMPLÍCITA  │
├────────────┼────────────┼────────────┤"""
            
            for option, probs in options.items():
                option_display = option if len(option) <= 8 else option[:7] + "."
                clean_report += f"""
│  {option_display.ljust(8)} │ {probs['real'].center(10)} │ {probs['implicit'].center(10)} │"""
            
            clean_report += """
└────────────┴────────────┴────────────┘"""
    
    # Se não temos probabilidades para mostrar, verificamos se temos probabilidades originais
    if not any_probs and original_probabilities and selected_markets:
        # Montar probabilidades a partir dos dados originais
        formatted_probs = {}
        
        # 1. Money Line (1X2)
        if selected_markets.get('money_line', False) and "moneyline" in original_probabilities:
            formatted_probs["Money Line (1X2)"] = {
                "Casa": {"real": f"{original_probabilities['moneyline']['home_win']:.1f}%", "implicit": "N/A"},
                "Empate": {"real": f"{original_probabilities['moneyline']['draw']:.1f}%", "implicit": "N/A"},
                "Fora": {"real": f"{original_probabilities['moneyline']['away_win']:.1f}%", "implicit": "N/A"}
            }
        
        # 2. Chance Dupla (Double Chance)
        if selected_markets.get('chance_dupla', False) and "double_chance" in original_probabilities:
            formatted_probs["Chance Dupla"] = {
                "1X": {"real": f"{original_probabilities['double_chance']['home_or_draw']:.1f}%", "implicit": "N/A"},
                "12": {"real": f"{original_probabilities['double_chance']['home_or_away']:.1f}%", "implicit": "N/A"},
                "X2": {"real": f"{original_probabilities['double_chance']['away_or_draw']:.1f}%", "implicit": "N/A"}
            }
        
        # 3. Over/Under
        if selected_markets.get('over_under', False) and "over_under" in original_probabilities:
            formatted_probs["Over/Under Gols"] = {
                "Over 2.5": {"real": f"{original_probabilities['over_under']['over_2_5']:.1f}%", "implicit": "N/A"},
                "Under 2.5": {"real": f"{original_probabilities['over_under']['under_2_5']:.1f}%", "implicit": "N/A"}
            }
        
        # 4. BTTS
        if selected_markets.get('ambos_marcam', False) and "btts" in original_probabilities:
            formatted_probs["Ambos Marcam"] = {
                "Sim": {"real": f"{original_probabilities['btts']['yes']:.1f}%", "implicit": "N/A"},
                "Não": {"real": f"{original_probabilities['btts']['no']:.1f}%", "implicit": "N/A"}
            }
        
        # 5. Cantos
        if selected_markets.get('escanteios', False) and "corners" in original_probabilities:
            formatted_probs["Escanteios"] = {
                "Over 9.5": {"real": f"{original_probabilities['corners']['over_9_5']:.1f}%", "implicit": "N/A"},
                "Under 9.5": {"real": f"{original_probabilities['corners']['under_9_5']:.1f}%", "implicit": "N/A"}
            }
        
        # 6. Cartões
        if selected_markets.get('cartoes', False) and "cards" in original_probabilities:
            formatted_probs["Cartões"] = {
                "Over 3.5": {"real": f"{original_probabilities['cards']['over_3_5']:.1f}%", "implicit": "N/A"},
                "Under 3.5": {"real": f"{original_probabilities['cards']['under_3_5']:.1f}%", "implicit": "N/A"}
            }
            
        # Adicionar probabilidades implícitas das odds
        for category, markets in market_categories.items():
            if category in formatted_probs:
                # Extrair probabilidades implícitas dos mercados listados
                for market_line in markets:
                    # Extrair o nome da opção e a odds implícita
                    parts = market_line.split("@")
                    if len(parts) >= 2:
                        option_text = parts[0].replace("•", "").strip()
                        # Extrair probabilidade implícita se estiver no formato (XX.X%)
                        impl_match = re.search(r'\(Implícita:\s*(\d+\.?\d*)%\)', market_line)
                        if impl_match:
                            impl_prob = impl_match.group(1) + "%"
                            
                            # Identificar a opção correta no dicionário
                            for opt in formatted_probs[category]:
                                # Verificar se a opção atual contém o nome da opção no texto
                                if opt.lower() in option_text.lower() or any(term.lower() in option_text.lower() for term in opt.lower().split()):
                                    formatted_probs[category][opt]["implicit"] = impl_prob
                                    break
                            
                            # Tratamento especial para casa/fora
                            if "casa" in option_text.lower() and "Casa" in formatted_probs[category]:
                                formatted_probs[category]["Casa"]["implicit"] = impl_prob
                            elif "fora" in option_text.lower() and "Fora" in formatted_probs[category]:
                                formatted_probs[category]["Fora"]["implicit"] = impl_prob
                            elif home_team in option_text and "Casa" in formatted_probs[category]:
                                formatted_probs[category]["Casa"]["implicit"] = impl_prob
                            elif away_team in option_text and "Fora" in formatted_probs[category]:
                                formatted_probs[category]["Fora"]["implicit"] = impl_prob
            
        # Adicionar as probabilidades ao relatório
        for category, options in formatted_probs.items():
            if options:
                any_probs = True
                clean_report += f"""

[{category}]
┌────────────┬────────────┬────────────┐
│  MERCADO   │  REAL (%)  │ IMPLÍCITA  │
├────────────┼────────────┼────────────┤"""
                
                for option, probs in options.items():
                    option_display = option if len(option) <= 8 else option[:7] + "."
                    real_val = probs['real'].center(10) if 'real' in probs else "N/A".center(10)
                    impl_val = probs['implicit'].center(10) if 'implicit' in probs else "N/A".center(10)
                    clean_report += f"""
│  {option_display.ljust(8)} │ {real_val} │ {impl_val} │"""
                
                clean_report += """
└────────────┴────────────┴────────────┘"""
    
    if not any_probs:
        clean_report += "\nProbabilidades não disponíveis para análise."

    clean_report += f"""

💰 OPORTUNIDADES IDENTIFICADAS
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
"""
    
    # Adicionar oportunidades limpas
    if opportunities:
        for opp in opportunities:
            clean_report += f"{opp}\n"
    else:
        clean_report += "Nenhuma oportunidade de valor identificada.\n"
    
    clean_report += f"""

🎯 NÍVEL DE CONFIANÇA GERAL: {confidence_level}
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔

► CONSISTÊNCIA: {consistency_info}

► FORMA: {form_info}

► INFLUÊNCIA: {influence_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     © RELATÓRIO VALUE HUNTER DE ANÁLISE ESPORTIVA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""" 

    return clean_report
    
# Função auxiliar para calcular probabilidades reais
def calculate_real_prob(home_xg, away_xg, home_games, away_games):
    """Calcula probabilidades reais com handling melhorado para valores inválidos"""
    try:
        # Tratar valores não numéricos
        try:
            home_xg = float(home_xg) if home_xg != 'N/A' else 0
            away_xg = float(away_xg) if away_xg != 'N/A' else 0
            home_games = float(home_games) if home_games != 'N/A' else 1
            away_games = float(away_games) if away_games != 'N/A' else 1
        except (ValueError, TypeError):
            # Fallback para caso não consiga converter
            logger.warning("Falha ao converter valores para cálculo de probabilidade")
            return None
            
        # Calcular xG por jogo
        home_xg_per_game = home_xg / home_games if home_games > 0 else 0
        away_xg_per_game = away_xg / away_games if away_games > 0 else 0
        
        # Se não temos xG válidos, não podemos calcular probabilidades
        if home_xg_per_game == 0 and away_xg_per_game == 0:
            return None
            
        # Ajuste baseado em home advantage
        home_advantage = 1.1
        adjusted_home_xg = home_xg_per_game * home_advantage
        
        # Calcular probabilidades
        total_xg = adjusted_home_xg + away_xg_per_game
        if total_xg == 0:
            return None
            
        home_prob = (adjusted_home_xg / total_xg) * 100
        away_prob = (away_xg_per_game / total_xg) * 100
        
        # Ajustar probs para somar 100%
        total_prob = home_prob + away_prob
        if total_prob > 100:
            factor = 100 / total_prob
            home_prob *= factor
            away_prob *= factor
        
        draw_prob = 100 - (home_prob + away_prob)
        
        # Ajustar para valores realistas
        if draw_prob < 5:
            draw_prob = 5
            excess = (home_prob + away_prob + draw_prob) - 100
            home_prob -= excess * (home_prob / (home_prob + away_prob))
            away_prob -= excess * (away_prob / (home_prob + away_prob))
        
        return {
            'home': home_prob,
            'draw': draw_prob,
            'away': away_prob
        }
    except Exception as e:
        logger.error(f"Erro no cálculo de probabilidades: {str(e)}")
        return None

# Função para verificar a qualidade dos dados estatísticos
def check_data_quality(stats_dict):
    """Verifica se há dados estatísticos significativos"""
    if not stats_dict:
        return False
        
    # Contar valores não-zero
    non_zero_values = 0
    total_values = 0
    
    for key, value in stats_dict.items():
        if isinstance(value, (int, float)) and key not in ['id']:
            total_values += 1
            if value != 0:
                non_zero_values += 1
    
    # Se temos pelo menos alguns valores não-zero, considerar ok
    if total_values > 0:
        quality = non_zero_values / total_values
        logger.info(f"Qualidade dos dados: {quality:.2f} ({non_zero_values}/{total_values} valores não-zero)")
        return quality > 0.1  # Pelo menos 10% dos valores são não-zero
    
    return False

def format_enhanced_prompt(complete_analysis, home_team, away_team, odds_data, selected_markets):
    """
    Função aprimorada para formatar prompt de análise multi-mercados
    aproveitando os dados avançados da FootyStats, com melhor handling de dados limitados
    """
    # Verificar qualidade dos dados
    has_home_data = check_data_quality(complete_analysis["basic_stats"]["home_team"]["stats"])
    has_away_data = check_data_quality(complete_analysis["basic_stats"]["away_team"]["stats"])
    data_quality = "baixa" if not (has_home_data and has_away_data) else "média"
    
    # Log para diagnóstico
    logger.info(f"Qualidade de dados: {data_quality} (home: {has_home_data}, away: {has_away_data})")
    
    # Extrair dados do objeto de análise completa
    basic_stats = complete_analysis["basic_stats"]
    home_stats = basic_stats["home_team"]["stats"] 
    away_stats = basic_stats["away_team"]["stats"]
    home_form = complete_analysis["team_form"]["home"]
    away_form = complete_analysis["team_form"]["away"]
    h2h_data = complete_analysis["head_to_head"]
    home_advanced = complete_analysis["advanced_stats"]["home"]
    away_advanced = complete_analysis["advanced_stats"]["away"]
    
    # 1. ESTATÍSTICAS FUNDAMENTAIS (relevantes para todos os mercados)
    fundamental_stats = f"""
# ESTATÍSTICAS FUNDAMENTAIS ({home_team} vs {away_team})

## Desempenho Geral na Temporada
* {home_team}: {get_stat(home_stats, 'wins', 0)}V {get_stat(home_stats, 'draws', 0)}E {get_stat(home_stats, 'losses', 0)}D | {get_stat(home_stats, 'goals_scored', 0)} gols marcados, {get_stat(home_stats, 'goals_conceded', 0)} sofridos
* {away_team}: {get_stat(away_stats, 'wins', 0)}V {get_stat(away_stats, 'draws', 0)}E {get_stat(away_stats, 'losses', 0)}D | {get_stat(away_stats, 'goals_scored', 0)} gols marcados, {get_stat(away_stats, 'goals_conceded', 0)} sofridos

## Métricas Expected Goals (xG)
* {home_team}: {get_stat(home_stats, 'xG', 0)} xG a favor, {get_stat(home_stats, 'xGA', 0)} xG contra | Saldo: {float(get_stat(home_stats, 'xG', 0)) - float(get_stat(home_stats, 'xGA', 0)):.2f}
* {away_team}: {get_stat(away_stats, 'xG', 0)} xG a favor, {get_stat(away_stats, 'xGA', 0)} xG contra | Saldo: {float(get_stat(away_stats, 'xG', 0)) - float(get_stat(away_stats, 'xGA', 0)):.2f}

## Forma Recente (últimos 5 jogos)
* {home_team}: {' '.join(result.get('result', '?') for result in home_form[:5])}
* {away_team}: {' '.join(result.get('result', '?') for result in away_form[:5])}

## Head-to-Head
* Jogos totais: {h2h_data.get('total_matches', 0)}
* Vitórias {home_team}: {h2h_data.get('home_wins', 0)}
* Vitórias {away_team}: {h2h_data.get('away_wins', 0)}
* Empates: {h2h_data.get('draws', 0)}
"""

    # 2. ESTATÍSTICAS PARA MERCADOS DE RESULTADO (1X2, Dupla Chance)
    result_stats = ""
    if any(m in selected_markets for m in ["money_line", "chance_dupla"]):
        result_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE RESULTADO

## Desempenho como Mandante/Visitante
* {home_team} como mandante: {get_stat(home_stats, 'home_wins', 0)}V {get_stat(home_stats, 'home_draws', 0)}E {get_stat(home_stats, 'home_losses', 0)}D
* {away_team} como visitante: {get_stat(away_stats, 'away_wins', 0)}V {get_stat(away_stats, 'away_draws', 0)}E {get_stat(away_stats, 'away_losses', 0)}D

## Tendências de Resultado
* {home_team} % vitórias: {get_stat(home_stats, 'win_percentage', 0)}%
* {away_team} % vitórias: {get_stat(away_stats, 'win_percentage', 0)}%
* % empates nos jogos de {home_team}: {get_stat(home_stats, 'draw_percentage', 0)}%
* % empates nos jogos de {away_team}: {get_stat(away_stats, 'draw_percentage', 0)}%

## Métricas Avançadas Relevantes
* Posse média: {get_stat(home_stats, 'possession', 0)}% vs {get_stat(away_stats, 'possession', 0)}%
* Passes p/ Ação Defensiva: {home_advanced.get('ppda', 'N/A')} vs {away_advanced.get('ppda', 'N/A')} (menor = pressão mais intensa)
* Deep Completions: {home_advanced.get('deep_completions', 'N/A')} vs {away_advanced.get('deep_completions', 'N/A')}
"""

    # 3. ESTATÍSTICAS PARA MERCADOS DE GOLS (Over/Under, Ambos Marcam)
    goals_stats = ""
    if any(m in selected_markets for m in ["over_under", "ambos_marcam"]):
        goals_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE GOLS

## Médias de Gols
* {home_team} média de gols marcados: {float(get_stat(home_stats, 'goals_scored', 0)) / max(float(get_stat(home_stats, 'matches_played', 1)), 1):.2f} por jogo
* {away_team} média de gols marcados: {float(get_stat(away_stats, 'goals_scored', 0)) / max(float(get_stat(away_stats, 'matches_played', 1)), 1):.2f} por jogo
* {home_team} média de gols sofridos: {float(get_stat(home_stats, 'goals_conceded', 0)) / max(float(get_stat(home_stats, 'matches_played', 1)), 1):.2f} por jogo
* {away_team} média de gols sofridos: {float(get_stat(away_stats, 'goals_conceded', 0)) / max(float(get_stat(away_stats, 'matches_played', 1)), 1):.2f} por jogo

## Clean Sheets e BTTS
* {home_team} clean sheets: {get_stat(home_stats, 'clean_sheets', 0)} ({get_stat(home_stats, 'clean_sheet_percentage', 0)}%)
* {away_team} clean sheets: {get_stat(away_stats, 'clean_sheets', 0)} ({get_stat(away_stats, 'clean_sheet_percentage', 0)}%)
* {home_team} jogos com Ambos Marcam: {get_stat(home_stats, 'btts_percentage', 0)}%
* {away_team} jogos com Ambos Marcam: {get_stat(away_stats, 'btts_percentage', 0)}%

## Distribuição de Gols por Jogo
* Jogos do {home_team} com Over 2.5: {get_stat(home_stats, 'over_2_5_percentage', 0)}%
* Jogos do {away_team} com Over 2.5: {get_stat(away_stats, 'over_2_5_percentage', 0)}%
* Jogos H2H com Over 2.5: {h2h_data.get('over_2_5_percentage', 0)}%
"""

    # 4. ESTATÍSTICAS PARA MERCADOS DE ESCANTEIOS
    corners_stats = ""
    if "escanteios" in selected_markets:
        corners_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE ESCANTEIOS

## Médias de Escanteios
* {home_team} média de escanteios a favor: {float(get_stat(home_stats, 'corners_for', 0)) / max(float(get_stat(home_stats, 'matches_played', 1)), 1):.2f} por jogo
* {away_team} média de escanteios a favor: {float(get_stat(away_stats, 'corners_for', 0)) / max(float(get_stat(away_stats, 'matches_played', 1)), 1):.2f} por jogo
* {home_team} média de escanteios contra: {float(get_stat(home_stats, 'corners_against', 0)) / max(float(get_stat(home_stats, 'matches_played', 1)), 1):.2f} por jogo
* {away_team} média de escanteios contra: {float(get_stat(away_stats, 'corners_against', 0)) / max(float(get_stat(away_stats, 'matches_played', 1)), 1):.2f} por jogo

## Tendências de Escanteios
* Jogos do {home_team} com Over 9.5 escanteios: {get_stat(home_stats, 'over_9_5_corners_percentage', 0)}%
* Jogos do {away_team} com Over 9.5 escanteios: {get_stat(away_stats, 'over_9_5_corners_percentage', 0)}%
* Total médio de escanteios em confrontos H2H: {h2h_data.get('average_corners', 'N/A')}
"""

    # 5. ESTATÍSTICAS PARA MERCADOS DE CARTÕES
    cards_stats = ""
    if "cartoes" in selected_markets:
        cards_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE CARTÕES

## Médias de Cartões
* {home_team} média de cartões recebidos: {float(get_stat(home_stats, 'cards_total', 0)) / max(float(get_stat(home_stats, 'matches_played', 1)), 1):.2f} por jogo
* {away_team} média de cartões recebidos: {float(get_stat(away_stats, 'cards_total', 0)) / max(float(get_stat(away_stats, 'matches_played', 1)), 1):.2f} por jogo
* {home_team} média de cartões provocados: {float(get_stat(home_stats, 'cards_against', 0)) / max(float(get_stat(home_stats, 'matches_played', 1)), 1):.2f} por jogo
* {away_team} média de cartões provocados: {float(get_stat(away_stats, 'cards_against', 0)) / max(float(get_stat(away_stats, 'matches_played', 1)), 1):.2f} por jogo

## Tendências de Cartões
* Jogos do {home_team} com Over 3.5 cartões: {get_stat(home_stats, 'over_3_5_cards_percentage', 0)}%
* Jogos do {away_team} com Over 3.5 cartões: {get_stat(away_stats, 'over_3_5_cards_percentage', 0)}%
* Média de cartões em jogos H2H: {h2h_data.get('average_cards', 'N/A')}
* Árbitro da partida: {basic_stats.get('referee', 'Não informado')} (Média de {basic_stats.get('referee_avg_cards', 'N/A')} cartões por jogo)
"""

    # 6. MERCADOS DISPONÍVEIS E ODDS
    markets_info = f"""
# MERCADOS DISPONÍVEIS E ODDS
{odds_data}
"""

    # 7. INSTRUÇÕES PARA O MODELO - COM REQUISITOS ESTRITOS DE FORMATAÇÃO
    instructions = f"""
    # INSTRUÇÕES PARA ANÁLISE
    
    Analise os dados estatísticos fornecidos para identificar valor nas odds.
    Você é um especialista em probabilidades esportivas.
    
    INSTRUÇÕES MUITO IMPORTANTES:
    
    1. Você DEVE separar 100% dos mercados em suas categorias ESPECÍFICAS e PRÓPRIAS:
       - Money Line (1X2): Apenas 1 (Casa), X (Empate), 2 (Fora)
       - Chance Dupla: Apenas 1X, 12, X2
       - Over/Under Gols: Apenas mercados de gols, NUNCA misture com escanteios ou cartões
       - Ambos Marcam (BTTS): Apenas Sim/Não para ambas equipes marcarem
       - Escanteios: Apenas mercados de escanteios/corners, SEMPRE separado dos gols
       - Cartões: Apenas mercados de cartões, SEMPRE separado dos gols
    
    2. As probabilidades REAIS foram calculadas para cada mercado. Você DEVE apresentá-las na seção "PROBABILIDADES CALCULADAS" com este formato exato:
    
    [Money Line (1X2)]
    ┌────────────┬────────────┬────────────┐
    │  MERCADO   │  REAL (%)  │ IMPLÍCITA  │
    ├────────────┼────────────┼────────────┤
    │  Casa     │   74.3%    │   87.7%    │
    │  Empate   │   13.7%    │   13.3%    │
    │  Fora     │   12.0%    │    6.7%    │
    └────────────┴────────────┴────────────┘
    
    [Repita este formato para cada mercado, mantendo cada tipo em sua própria tabela separada]
    
    3. Nas oportunidades identificadas, inclua sempre AMBOS os valores percentuais:
       - Formato: **[Mercado] [Escolha]**: Real XX.X% vs Implícita XX.X% (Valor: +XX.X%)
    
    VOCÊ DEVE RESPONDER COM ESTE FORMATO ESTRITO:
    
    # 📊 ANÁLISE DE PARTIDA 📊
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    ## ⚽ {home_team} 🆚 {away_team} ⚽
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    ### 📈 ANÁLISE DE MERCADOS DISPONÍVEIS
    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
    
    [Money Line (1X2)]
    • Informações sobre o mercado 1X2 com odds e probabilidades implícitas
    
    [Chance Dupla]
    • Informações sobre o mercado de chance dupla com odds e probabilidades implícitas
    
    [Over/Under Gols]
    • Informações SOMENTE sobre gols (NUNCA misture com escanteios ou cartões)
    
    [Ambos Marcam]
    • Informações sobre o mercado BTTS com odds e probabilidades implícitas
    
    [Escanteios]
    • Informações ESPECÍFICAS de escanteios (NUNCA misture com gols)
    
    [Cartões]
    • Informações ESPECÍFICAS de cartões (NUNCA misture com gols)
    
    ### 🔄 PROBABILIDADES CALCULADAS
    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
    
    [TABELAS SEPARADAS PARA CADA MERCADO COM FORMATO ESTRITO]
    
    ### 💰 OPORTUNIDADES IDENTIFICADAS
    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
    • **[Mercado] [Escolha]**: Real XX.X% vs Implícita XX.X% (Valor: +XX.X%)
    
    ### 🎯 NÍVEL DE CONFIANÇA GERAL: [Baixo/Médio/Alto]
    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
    
      ► CONSISTÊNCIA: [Detalhes sobre consistência]
      
      ► FORMA: [Detalhes sobre forma recente]
      
      ► INFLUÊNCIA: [Como os fatores acima influenciam a análise]
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    © RELATÓRIO DE ANÁLISE ESPORTIVA
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    # Adicionar aviso quando utilizamos o modelo de fallback
    if not has_stats_data:
        instructions += """
    ATENÇÃO: Os dados estatísticos para esta partida são limitados. Use apenas as informações disponíveis e seja claro quando não houver dados suficientes para uma análise completa.
    """
def get_stat(stats, col, default='N/A'):
    """
    Função auxiliar melhorada para extrair estatísticas com tratamento de erro e fallback
    """
    try:
        # Primeiro tenta o nome exato da coluna
        if col in stats and pd.notna(stats[col]) and stats[col] != '':
            return stats[col]
        
        # Mapeamento de nomes alternativos de colunas
        col_map = {
            'MP': ['MP', 'PJ', 'Matches', 'Jogos', 'Games'],
            'Gls': ['Gls', 'G', 'Gols', 'Goals', 'GF'],
            'xG': ['xG', 'ExpG', 'Expected_Goals'],
            'Poss': ['Poss', 'Posse', 'Possession', '%Posse']
        }
        
        # Se a coluna original foi encontrada no mapa, tenta os alternativos
        if col in col_map:
            for alt_col in col_map[col]:
                if alt_col in stats and pd.notna(stats[alt_col]) and stats[alt_col] != '':
                    return stats[alt_col]
                    
        # Verificar variações de case (maiúsculas/minúsculas)
        for stats_col in stats.index:
            if stats_col.lower() == col.lower() and pd.notna(stats[stats_col]) and stats[stats_col] != '':
                return stats[stats_col]
                
        return default
    except Exception as e:
        logger.warning(f"Erro ao obter estatística '{col}': {str(e)}")
        return default
        
def calculate_advanced_probabilities(home_team, away_team, league_table=None):
    """
    Calcular probabilidades usando o método de dispersão e ponderação conforme especificado
    
    Args:
        home_team (dict): Estatísticas do time da casa
        away_team (dict): Estatísticas do time visitante
        league_table (dict, optional): Tabela do campeonato se disponível
        
    Returns:
        dict: Probabilidades calculadas para diferentes mercados
    """
    try:
        import numpy as np
        import math
        
        # PASSO 1: Cálculo de Dispersão Base
        
        # Extrair estatísticas básicas
        home_goals_per_game = home_team.get('goals_per_game', 0)
        home_conceded_per_game = home_team.get('conceded_per_game', 0)
        away_goals_per_game = away_team.get('goals_per_game', 0)
        away_conceded_per_game = away_team.get('conceded_per_game', 0)
        
        # Calcular dispersão através da variabilidade dos resultados
        home_results = [
            home_team.get('win_pct', 0) / 100,
            home_team.get('draw_pct', 0) / 100,
            home_team.get('loss_pct', 0) / 100
        ]
        
        away_results = [
            away_team.get('win_pct', 0) / 100,
            away_team.get('draw_pct', 0) / 100,
            away_team.get('loss_pct', 0) / 100
        ]
        
        # Calcular desvio padrão como medida de dispersão
        home_dispersion = np.std(home_results) * 3  # Multiplicamos por 3 para normalizar
        away_dispersion = np.std(away_results) * 3
        
        # Converter para consistência (inverso da dispersão)
        home_consistency = 1 - min(1, home_dispersion)
        away_consistency = 1 - min(1, away_dispersion)
        
        # PASSO 2: Ponderação de Fatores
        
        # 1. Forma recente (35%) - precisamos processar a string de forma
        def form_to_points(form_str):
            points = 0
            weight = 1.0
            total_weight = 0
            
            # Inverter string para dar mais peso aos jogos mais recentes
            for i, result in enumerate(reversed(form_str[:5])):
                if result == 'W':
                    points += 3 * weight
                elif result == 'D':
                    points += 1 * weight
                elif result == 'L':
                    points += 0
                else:
                    points += 1 * weight  # Valor neutro para '?'
                
                total_weight += weight
                weight *= 0.8  # Decaimento para jogos mais antigos
            
            return points / max(total_weight, 1)
        
        # Verificar se os dados de forma parecem suspeitos (ambos iguais a "DDDDD")
        home_form = home_team.get('form', '?????')
        away_form = away_team.get('form', '?????')
        
        if home_form == away_form == "DDDDD":
            # Gerar forma baseada nas estatísticas para evitar viés
            import random
            
            # Time da casa
            home_form = ""
            for _ in range(5):
                r = random.random()
                if r < home_team.get('win_pct', 40) / 100:
                    home_form += "W"
                elif r < (home_team.get('win_pct', 40) + home_team.get('draw_pct', 30)) / 100:
                    home_form += "D"
                else:
                    home_form += "L"
                    
            # Time visitante
            away_form = ""
            for _ in range(5):
                r = random.random()
                if r < away_team.get('win_pct', 30) / 100:
                    away_form += "W"
                elif r < (away_team.get('win_pct', 30) + away_team.get('draw_pct', 30)) / 100:
                    away_form += "D"
                else:
                    away_form += "L"
        
        # Converter forma para pontos (escala 0-1)
        home_form_points = form_to_points(home_form) / 15  # Normalizado para 0-1 (máximo 15 pontos)
        away_form_points = form_to_points(away_form) / 15
        
        # 2. Estatísticas da equipe (25%)
        home_xg = home_team.get('xg', 0)
        home_xga = home_team.get('xga', 0)
        away_xg = away_team.get('xg', 0)
        away_xga = away_team.get('xga', 0)
        
        # Normalizar dados de xG
        max_xg = max(home_xg, away_xg, 60)  # 60 gols é benchmark máximo
        
        # Calcular scores ofensivos e defensivos
        home_offensive = (home_xg / max(max_xg, 1)) * 0.6 + (home_goals_per_game / 3) * 0.4
        home_defensive = (1 - min(1, home_xga / max_xg)) * 0.6 + (1 - min(1, home_conceded_per_game / 3)) * 0.4
        
        away_offensive = (away_xg / max_xg) * 0.6 + (away_goals_per_game / 3) * 0.4
        away_defensive = (1 - min(1, away_xga / max_xg)) * 0.6 + (1 - min(1, away_conceded_per_game / 3)) * 0.4
        
        # Score estatístico total
        home_stats_score = home_offensive * 0.6 + home_defensive * 0.4
        away_stats_score = away_offensive * 0.6 + away_defensive * 0.4
        
        # 3. Posição na tabela (20%) - estimado a partir das taxas de vitória
        home_position_score = home_team.get('win_pct', 50) / 100
        away_position_score = away_team.get('win_pct', 50) / 100
        
        # 4. Métricas de criação (20%)
        home_possession = home_team.get('possession', 50) / 100
        away_possession = away_team.get('possession', 50) / 100
        
        # Métricas de criação total
        home_creation = home_offensive * 0.7 + home_possession * 0.3
        away_creation = away_offensive * 0.7 + away_possession * 0.3
        
        # APLICAR PONDERAÇÕES
        home_total_score = (
            home_form_points * 0.35 +      # Forma recente: 35%
            home_stats_score * 0.25 +      # Estatísticas: 25%
            home_position_score * 0.20 +   # Posição: 20%
            home_creation * 0.20           # Criação: 20%
        )
        
        away_total_score = (
            away_form_points * 0.35 +      # Forma recente: 35%
            away_stats_score * 0.25 +      # Estatísticas: 25%
            away_position_score * 0.20 +   # Posição: 20%
            away_creation * 0.20           # Criação: 20%
        )
        
        # PASSO 3: Análise por Mercado
        
        # 1. Moneyline (1X2)
        # Probabilidades base
        raw_home_win = home_total_score / (home_total_score + away_total_score) * 0.8
        raw_away_win = away_total_score / (home_total_score + away_total_score) * 0.8
        raw_draw = 1 - (raw_home_win + raw_away_win)
        
        # Ajuste para vantagem em casa
        home_advantage = 0.12  # +12% boost para time da casa
        adjusted_home_win = raw_home_win + home_advantage
        adjusted_away_win = raw_away_win - (home_advantage * 0.5)
        adjusted_draw = raw_draw - (home_advantage * 0.5)
        
        # Normalizar para somar 100%
        total = adjusted_home_win + adjusted_draw + adjusted_away_win
        home_win_prob = (adjusted_home_win / total) * 100
        draw_prob = (adjusted_draw / total) * 100
        away_win_prob = (adjusted_away_win / total) * 100
        
        # 2. Gols
        expected_goals_home = home_offensive * 2.5  # Potencial máximo de 2.5 gols
        expected_goals_away = away_offensive * 2.0  # Potencial máximo de 2.0 gols
        
        # Ajustar baseado nas defesas
        expected_goals_home *= (1 - away_defensive * 0.7)
        expected_goals_away *= (1 - home_defensive * 0.7)
        
        total_expected_goals = expected_goals_home + expected_goals_away
        
        # Probabilidade Over 2.5
        # Usar uma curva logística para mapear gols esperados para probabilidade
        over_2_5_prob = 1 / (1 + math.exp(-2 * (total_expected_goals - 2.5)))
        
        # 3. Ambos Marcam (BTTS)
        btts_base = min(1, (expected_goals_home * expected_goals_away) * 2)
        btts_historical = (home_team.get('btts_pct', 50) + away_team.get('btts_pct', 50)) / 200
        
        btts_prob = btts_base * 0.7 + btts_historical * 0.3
        
        # 4. Cartões
        home_cards = home_team.get('cards_per_game', 2)
        away_cards = away_team.get('cards_per_game', 2)
        
        # Ajuste baseado na intensidade do jogo (maior quando times próximos)
        intensity_factor = 1 + 0.3 * (1 - abs(home_total_score - away_total_score))
        expected_cards = (home_cards + away_cards) * intensity_factor
        
        # Probabilidade Over 3.5 cartões
        over_3_5_cards_prob = 1 / (1 + math.exp(-2 * (expected_cards - 3.5)))
        
        # 5. Escanteios
        home_corners = home_team.get('corners_per_game', 5)
        away_corners = away_team.get('corners_per_game', 5)
        
        # Ajustar para posse e estilo ofensivo
        expected_corners = (home_corners * (home_possession * 0.5 + 0.5) +
                           away_corners * (away_possession * 0.5 + 0.5))
        
        # Probabilidade Over 9.5 escanteios
        over_9_5_corners_prob = 1 / (1 + math.exp(-1.5 * (expected_corners - 9.5)))
        
        # Retornar todos os cálculos
        return {
            "moneyline": {
                "home_win": home_win_prob,
                "draw": draw_prob,
                "away_win": away_win_prob
            },
            "double_chance": {
                "home_or_draw": home_win_prob + draw_prob,
                "away_or_draw": away_win_prob + draw_prob,
                "home_or_away": home_win_prob + away_win_prob
            },
            "gols": {
                "over_2_5": over_2_5_prob * 100,
                "under_2_5": (1 - over_2_5_prob) * 100,
                "expected_goals": total_expected_goals
            },
            "btts": {
                "yes": btts_prob * 100,
                "no": (1 - btts_prob) * 100
            },
            "cards": {
                "over_3_5": over_3_5_cards_prob * 100,
                "under_3_5": (1 - over_3_5_cards_prob) * 100,
                "expected_cards": expected_cards
            },
            "corners": {
                "over_9_5": over_9_5_corners_prob * 100,
                "under_9_5": (1 - over_9_5_corners_prob) * 100,
                "expected_corners": expected_corners
            },
            "analysis_data": {
                "home_consistency": home_consistency,
                "away_consistency": away_consistency,
                "home_form_points": home_form_points,
                "away_form_points": away_form_points,
                "home_total_score": home_total_score,
                "away_total_score": away_total_score
            }
        }
        
    except Exception as e:
        logger.error(f"Erro no cálculo avançado de probabilidades: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Retornamos None em caso de erro
        return None
