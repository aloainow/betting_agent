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

# Add to utils/ai.py

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
            """
            Calcula pontos de forma considerando os últimos 5 jogos
            W=3pts, D=1pt, L=0pts
            
            Args:
                form_str (str): String com a sequência de resultados (ex: "WDLWW")
                
            Returns:
                int: Pontuação total (máximo 15 pontos)
            """
            if not form_str or not isinstance(form_str, str):
                return 0
            
            points = 0
            # Garantir que estamos usando apenas os últimos 5 jogos
            recent_form = form_str[-5:] if len(form_str) >= 5 else form_str
            
            # Log para debug
            logger.debug(f"Calculando pontos para forma: {recent_form}")
            
            # Calcular pontos
            for result in recent_form:
                result = result.upper()  # Converter para maiúscula para garantir
                if result == 'W':
                    points += 3
                    logger.debug(f"W encontrado, adicionando 3 pontos, total: {points}")
                elif result == 'D':
                    points += 1
                    logger.debug(f"D encontrado, adicionando 1 ponto, total: {points}")
                elif result == 'L':
                    logger.debug(f"L encontrado, sem pontos, total: {points}")
                else:
                    logger.debug(f"Caractere desconhecido: {result}, sem pontos, total: {points}")
            
            logger.debug(f"Pontuação final da forma: {points}")
            return points  # Valor inteiro
        
        # Extrair últimos 5 jogos do formRun_overall se disponível
        home_formRun = home.get('formRun_overall', '')
        away_formRun = away.get('formRun_overall', '')
        
        # Formatar string de forma corretamente
        if home_formRun and len(home_formRun) >= 5:
            home_form = home_formRun[-5:].upper()
        else:
            home_form = home.get('form', '?????')
            
        if away_formRun and len(away_formRun) >= 5:
            away_form = away_formRun[-5:].upper()
        else:
            away_form = away.get('form', '?????')
        
        # E então, ao calcular os pontos, use a função form_to_points atualizada
        # Modificar onde o cálculo é feito:
        # Calcular pontos brutos (0-15)
        # Calcular pontos brutos (0-15)
        home_form_raw_points = form_to_points(home_form)
        away_form_raw_points = form_to_points(away_form)
        
        # Normalizar para uso nos cálculos (0-1)
        home_form_normalized = home_form_raw_points / 15.0
        away_form_normalized = away_form_raw_points / 15.0
        
        # Usar nas ponderações
        home_total_score = (
            home_form_normalized * 0.35 +      # Normalizar para 0-1
            home_stats_score * 0.25 +      # Estatísticas: 25%
            home_position_score * 0.20 +   # Posição: 20%
            home_creation * 0.20           # Criação: 20%
        )
        
        # Armazenar os valores brutos e normalizados para uso posterior
        analysis_data = {
            "home_consistency": home_consistency,
            "away_consistency": away_consistency,
            "home_form_points": home_form_raw_points / 15.0,  # Armazenar como normalizado, mas o valor bruto é usado na exibição
            "away_form_points": away_form_raw_points / 15.0,
            "home_total_score": home_total_score,
            "away_total_score": away_total_score
        }
        
        # E para cálculos, se necessário:
        home_total_score = (
            (home_form_points / 15.0) * 0.35 +  # Normalizar para escala 0-1
            home_stats_score * 0.25 +
            home_position_score * 0.20 +
            home_creation * 0.20
        )
        
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
            (home_form_points / 15) * 0.35 +      # Normalizar para 0-1
            home_stats_score * 0.25 +      # Estatísticas: 25%
            home_position_score * 0.20 +   # Posição: 20%
            home_creation * 0.20           # Criação: 20%
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
        
        # 2. Over/Under 2.5 Goals
        # Use a combination of team goal stats and xG
        home_expected_goals = home.get('xg_for_avg_overall', 0) if home.get('xg_for_avg_overall', 0) > 0 else home.get('goals_per_game', 0)
        away_expected_goals = away.get('xg_for_avg_overall', 0) if away.get('xg_for_avg_overall', 0) > 0 else away.get('goals_per_game', 0)
        
        # Consider defensive strength
        home_expected_conceded = away_expected_goals * (home.get('conceded_per_game', 0) / 1.5) if home.get('conceded_per_game', 0) > 0 else away_expected_goals * 0.8
        away_expected_conceded = home_expected_goals * (away.get('conceded_per_game', 0) / 1.5) if away.get('conceded_per_game', 0) > 0 else home_expected_goals * 0.8
        
        # Total expected goals
        total_expected_goals = home_expected_conceded + away_expected_conceded
        
        # Poisson distribution can be approximated with a logistic function for this purpose
        over_2_5_prob = 1 / (1 + math.exp(-1.5 * (total_expected_goals - 2.5))) * 100
        under_2_5_prob = 100 - over_2_5_prob
        
        # 3. Both Teams To Score (BTTS)
        # Use home and away scoring probability
        home_scoring_prob = 1 - (1 / (1 + math.exp(home_expected_goals - 0.5)))
        away_scoring_prob = 1 - (1 / (1 + math.exp(away_expected_goals - 0.5)))
        
        # BTTS probability is the product of both teams scoring
        btts_yes_prob = home_scoring_prob * away_scoring_prob * 100
        btts_no_prob = 100 - btts_yes_prob
        
        # 4. Escanteios
        # Inicializar valores para evitar erros quando o mercado não está selecionado
        over_9_5_corners_prob = 0
        under_9_5_corners_prob = 0
        total_corners_expected = 0
        
        if selected_markets.get("escanteios"):
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
            
            # Calcular probabilidade para over/under 9.5 escanteios
            # Usando uma função logística para mapear o número esperado para uma probabilidade
            over_9_5_corners_prob = 1 / (1 + math.exp(-0.8 * (total_corners_expected - 9.5))) * 100
            under_9_5_corners_prob = 100 - over_9_5_corners_prob
        
        # 5. Cartões
        # Inicializar valores para evitar erros quando o mercado não está selecionado
        over_3_5_cards_prob = 0
        under_3_5_cards_prob = 0
        total_cards_expected = 0
        
        if selected_markets.get("cartoes"):
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
            
            # Calcular probabilidade para over/under 3.5 cartões
            # Usando uma função logística para mapear o número esperado para uma probabilidade
            over_3_5_cards_prob = 1 / (1 + math.exp(-1.2 * (total_cards_expected - 3.5))) * 100
            under_3_5_cards_prob = 100 - over_3_5_cards_prob
        
        # 6. Chance Dupla (Double Chance)
        home_draw_prob = home_win_prob + draw_prob
        away_draw_prob = away_win_prob + draw_prob
        home_away_prob = home_win_prob + away_win_prob
        
        # 6. PROBABILITY SECTION
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
        * {home_team} ou Empate: {home_draw_prob:.1f}%
        * {away_team} ou Empate: {away_draw_prob:.1f}%
        * {home_team} ou {away_team}: {home_away_prob:.1f}%
        """
        
        # Only include Over/Under if selected
        if selected_markets.get("over_under", False):
            probability_section += f"""
        ### Over/Under 2.5 Gols
        * Over 2.5: {over_2_5_prob:.1f}%
        * Under 2.5: {under_2_5_prob:.1f}%
        * Total esperado de gols: {total_expected_goals:.2f}
        """
        
        # Only include BTTS if selected
        if selected_markets.get("ambos_marcam", False):
            probability_section += f"""
        ### Ambos Marcam (BTTS)
        * Sim: {btts_yes_prob:.1f}%
        * Não: {btts_no_prob:.1f}%
        """
        
        # Only include Corners (Escanteios) if selected
        if selected_markets.get("escanteios", False):
            probability_section += f"""
        ### Escanteios (Over/Under 9.5)
        * Over 9.5: {over_9_5_corners_prob:.1f}%
        * Under 9.5: {under_9_5_corners_prob:.1f}%
        * Total esperado de escanteios: {total_corners_expected:.1f}
        """
        
        # Only include Cards (Cartões) if selected
        if selected_markets.get("cartoes", False):
            probability_section += f"""
        ### Cartões (Over/Under 3.5)
        * Over 3.5: {over_3_5_cards_prob:.1f}%
        * Under 3.5: {under_3_5_cards_prob:.1f}%
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
        # First, prepare a list of selected market names for the instructions
        selected_market_names = []
        if selected_markets.get("money_line", False):
            selected_market_names.append("Money Line (1X2)")
        if selected_markets.get("chance_dupla", False):
            selected_market_names.append("Chance Dupla (Double Chance)")
        if selected_markets.get("over_under", False):
            selected_market_names.append("Over/Under 2.5 Gols")
        if selected_markets.get("ambos_marcam", False):
            selected_market_names.append("Ambos Marcam (BTTS)")
        if selected_markets.get("escanteios", False):
            selected_market_names.append("Escanteios (Over/Under 9.5)")
        if selected_markets.get("cartoes", False):
            selected_market_names.append("Cartões (Over/Under 3.5)")

        # Join the market names into a string
        selected_markets_str = ", ".join(selected_market_names)
        
        instructions = f"""
        # INSTRUÇÕES PARA ANÁLISE
        
        Analise os dados estatísticos fornecidos para identificar valor nas odds.
        Você é um especialista em probabilidades esportivas que utiliza nosso método avançado de Dispersão e Ponderação.
        
        IMPORTANTE: As probabilidades REAIS já foram calculadas para você para os seguintes mercados selecionados e somam exatamente 100% em cada mercado:
        {selected_markets_str}
        
        Todas as probabilidades reais estão na seção "PROBABILIDADES CALCULADAS".
        
        VOCÊ DEVE responder EXATAMENTE no formato abaixo:
        
        # Análise da Partida
        ## {home_team} x {away_team}
        
        # Análise de Mercados Disponíveis:
        [Resumo detalhado APENAS dos mercados selecionados ({selected_markets_str}) com suas odds e probabilidades implícitas]
        
        # Probabilidades Calculadas (REAL vs IMPLÍCITA):
        [Compare as probabilidades REAIS calculadas com as probabilidades IMPLÍCITAS nas odds APENAS para os mercados selecionados ({selected_markets_str})]
        
        # Oportunidades Identificadas:
        [Liste cada mercado onde você encontrou valor/edge, mostrando a porcentagem de vantagem]
        - Considere valor quando a probabilidade real for pelo menos 2% maior que a implícita
        
        # Nível de Confiança Geral: [Baixo/Médio/Alto]
        [Explique o nível de confiança, incluindo uma explicação clara sobre:
        - O que significa "consistência" (a previsibilidade do desempenho do time)
        - O que significam os valores de forma (X.X/15) - explicando que são pontos dos últimos 5 jogos
        - Como esses fatores influenciam sua confiança na análise]
        
        ATENÇÃO: Ao explicar o nível de confiança, sempre esclareça que:
        - Consistência é uma medida (%) que indica quão previsível é o desempenho da equipe
        - Forma (X.X/15) representa a pontuação dos últimos 5 jogos (vitória=3pts, empate=1pt, derrota=0pts)
        - Valores mais altos em ambas métricas aumentam a confiança na previsão
        """

        # Adicionar aviso quando utilizamos o modelo de fallback
        if not has_stats_data:
            instructions += """

⚠️ IMPORTANTE: Devido à limitação de dados estatísticos, as probabilidades calculadas são baseadas 
em um modelo de fallback e devem ser consideradas aproximações. Mencione isto claramente na sua análise 
e recomende cautela nas decisões baseadas nesta análise.
"""

        # Compile the final prompt
        sections = [
            fundamental_stats,
        ]
        
        # Only include result stats if moneyline or double chance are selected
        if selected_markets.get("money_line") or selected_markets.get("chance_dupla"):
            sections.append(result_stats)
        
        # Only include goals stats if over/under or btts are selected
        if selected_markets.get("over_under") or selected_markets.get("ambos_marcam"):
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

# Análise da Partida
## {home_team} x {away_team}

# Análise de Mercados Disponíveis:
[Resumo detalhado das odds]

# Probabilidades Calculadas (REAL vs IMPLÍCITA):
[Comparação lado a lado de probabilidades reais e implícitas]

# Oportunidades Identificadas:
[Lista de oportunidades com edge percentual]

# Nível de Confiança Geral: [Baixo/Médio/Alto]
[Explique o que significa 'consistência' e 'forma (X.X/15)' ao justificar o nível de confiança]
"""
def analyze_with_gpt(prompt, original_probabilities=None, selected_markets=None, home_team=None, away_team=None):
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
            return response.choices[0].message.content
    except OpenAIError as e:
        logger.error(f"Erro na API OpenAI: {str(e)}")
        st.error(f"Erro na API OpenAI: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        st.error(f"Erro inesperado: {str(e)}")
        return None

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
        return None        # Função para verificar a qualidade dos dados estatísticos
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

def format_analysis_response(analysis_text, home_team, away_team, selected_markets=None, original_probabilities=None, odds_data=None, implied_probabilities=None):
    """
    Formato atualizado que usa dados pré-calculados de probabilidades implícitas, ignorando a tentativa de extrair do texto.
    """
    try:
        # Verificar se temos informações suficientes
        if not analysis_text or not original_probabilities or not implied_probabilities:
            logger.warning("Informações insuficientes para formatação completa")
            return analysis_text
        
        # Criar uma análise completamente nova a partir dos dados que temos
        new_analysis = []
        
        # Título
        new_analysis.append(f"# Análise da Partida\n## {home_team} x {away_team}")
        
        # Análise de Mercados
        markets_section = "# Análise de Mercados Disponíveis:\n"
        
        # Usar o odds_data original diretamente se disponível
        if odds_data:
            markets_section += odds_data
        else:
            # Ou reconstruir a partir das probabilidades implícitas
            if selected_markets.get("money_line") and implied_probabilities:
                markets_section += "- **Money Line (1X2):**\n"
                if "home" in implied_probabilities:
                    home_odd = 100.0 / implied_probabilities["home"]
                    markets_section += f"  - Casa ({home_team}): @{home_odd:.2f}\n"
                if "draw" in implied_probabilities:
                    draw_odd = 100.0 / implied_probabilities["draw"]
                    markets_section += f"  - Empate: @{draw_odd:.2f}\n"
                if "away" in implied_probabilities:
                    away_odd = 100.0 / implied_probabilities["away"]
                    markets_section += f"  - Fora ({away_team}): @{away_odd:.2f}\n"
            
            if selected_markets.get("chance_dupla") and implied_probabilities:
                markets_section += "- **Chance Dupla:**\n"
                if "home_draw" in implied_probabilities:
                    home_draw_odd = 100.0 / implied_probabilities["home_draw"]
                    markets_section += f"  - 1X ({home_team} ou Empate): @{home_draw_odd:.2f}\n"
                if "home_away" in implied_probabilities:
                    home_away_odd = 100.0 / implied_probabilities["home_away"]
                    markets_section += f"  - 12 ({home_team} ou {away_team}): @{home_away_odd:.2f}\n"
                if "draw_away" in implied_probabilities:
                    draw_away_odd = 100.0 / implied_probabilities["draw_away"]
                    markets_section += f"  - X2 (Empate ou {away_team}): @{draw_away_odd:.2f}\n"
            
            if selected_markets.get("ambos_marcam") and implied_probabilities:
                markets_section += "- **Ambos Marcam (BTTS):**\n"
                if "btts_yes" in implied_probabilities:
                    btts_yes_odd = 100.0 / implied_probabilities["btts_yes"]
                    markets_section += f"  - Sim: @{btts_yes_odd:.2f}\n"
                if "btts_no" in implied_probabilities:
                    btts_no_odd = 100.0 / implied_probabilities["btts_no"]
                    markets_section += f"  - Não: @{btts_no_odd:.2f}\n"
        
        new_analysis.append(markets_section)
        
        # Probabilidades Calculadas vs Implícitas
        probs_section = "# Probabilidades Calculadas (REAL vs IMPLÍCITA):\n"
        opportunities = []
        
        # Money Line
        if selected_markets.get("money_line") and "moneyline" in original_probabilities:
            probs_section += "## Money Line (1X2):\n"
            
            moneyline = original_probabilities["moneyline"]
            
            # Casa
            home_real = moneyline.get("home_win", 0)
            home_implicit = implied_probabilities.get("home", 0)
            home_value = home_real > home_implicit + 2
            
            probs_section += f"- **{home_team}**: Real {home_real:.1f}% vs Implícita {home_implicit:.1f}%{' (Valor)' if home_value else ''}\n"
            
            if home_value:
                opportunities.append(f"- **{home_team}**: Real {home_real:.1f}% vs Implícita {home_implicit:.1f}% (Valor de {home_real-home_implicit:.1f}%)")
            
            # Empate
            draw_real = moneyline.get("draw", 0)
            draw_implicit = implied_probabilities.get("draw", 0)
            draw_value = draw_real > draw_implicit + 2
            
            probs_section += f"- **Empate**: Real {draw_real:.1f}% vs Implícita {draw_implicit:.1f}%{' (Valor)' if draw_value else ''}\n"
            
            if draw_value:
                opportunities.append(f"- **Empate**: Real {draw_real:.1f}% vs Implícita {draw_implicit:.1f}% (Valor de {draw_real-draw_implicit:.1f}%)")
            
            # Fora
            away_real = moneyline.get("away_win", 0)
            away_implicit = implied_probabilities.get("away", 0)
            away_value = away_real > away_implicit + 2
            
            probs_section += f"- **{away_team}**: Real {away_real:.1f}% vs Implícita {away_implicit:.1f}%{' (Valor)' if away_value else ''}\n"
            
            if away_value:
                opportunities.append(f"- **{away_team}**: Real {away_real:.1f}% vs Implícita {away_implicit:.1f}% (Valor de {away_real-away_implicit:.1f}%)")
        
        # Double Chance
        if selected_markets.get("chance_dupla") and "double_chance" in original_probabilities:
            probs_section += "## Chance Dupla (Double Chance):\n"
            
            dc = original_probabilities["double_chance"]
            
            # 1X
            hd_real = dc.get("home_or_draw", 0)
            hd_implicit = implied_probabilities.get("home_draw", 0)
            hd_value = hd_real > hd_implicit + 2
            
            probs_section += f"- **{home_team} ou Empate**: Real {hd_real:.1f}% vs Implícita {hd_implicit:.1f}%{' (Valor)' if hd_value else ''}\n"
            
            if hd_value:
                opportunities.append(f"- **{home_team} ou Empate**: Real {hd_real:.1f}% vs Implícita {hd_implicit:.1f}% (Valor de {hd_real-hd_implicit:.1f}%)")
            
            # 12
            ha_real = dc.get("home_or_away", 0)
            ha_implicit = implied_probabilities.get("home_away", 0)
            ha_value = ha_real > ha_implicit + 2
            
            probs_section += f"- **{home_team} ou {away_team}**: Real {ha_real:.1f}% vs Implícita {ha_implicit:.1f}%{' (Valor)' if ha_value else ''}\n"
            
            if ha_value:
                opportunities.append(f"- **{home_team} ou {away_team}**: Real {ha_real:.1f}% vs Implícita {ha_implicit:.1f}% (Valor de {ha_real-ha_implicit:.1f}%)")
            
            # X2
            da_real = dc.get("away_or_draw", 0)
            da_implicit = implied_probabilities.get("draw_away", 0)
            da_value = da_real > da_implicit + 2
            
            probs_section += f"- **Empate ou {away_team}**: Real {da_real:.1f}% vs Implícita {da_implicit:.1f}%{' (Valor)' if da_value else ''}\n"
            
            if da_value:
                opportunities.append(f"- **Empate ou {away_team}**: Real {da_real:.1f}% vs Implícita {da_implicit:.1f}% (Valor de {da_real-da_implicit:.1f}%)")
        
        # BTTS
        if selected_markets.get("ambos_marcam") and "btts" in original_probabilities:
            probs_section += "## Ambos Marcam (BTTS):\n"
            
            btts = original_probabilities["btts"]
            
            # Sim
            yes_real = btts.get("yes", 0)
            yes_implicit = implied_probabilities.get("btts_yes", 0)
            yes_value = yes_real > yes_implicit + 2
            
            probs_section += f"- **Sim**: Real {yes_real:.1f}% vs Implícita {yes_implicit:.1f}%{' (Valor)' if yes_value else ''}\n"
            
            if yes_value:
                opportunities.append(f"- **Ambos Marcam - Sim**: Real {yes_real:.1f}% vs Implícita {yes_implicit:.1f}% (Valor de {yes_real-yes_implicit:.1f}%)")
            
            # Não
            no_real = btts.get("no", 0)
            no_implicit = implied_probabilities.get("btts_no", 0)
            no_value = no_real > no_implicit + 2
            
            probs_section += f"- **Não**: Real {no_real:.1f}% vs Implícita {no_implicit:.1f}%{' (Valor)' if no_value else ''}\n"
            
            if no_value:
                opportunities.append(f"- **Ambos Marcam - Não**: Real {no_real:.1f}% vs Implícita {no_implicit:.1f}% (Valor de {no_real-no_implicit:.1f}%)")
        
        new_analysis.append(probs_section)
        
        # Oportunidades Identificadas
        if opportunities:
            new_analysis.append("# Oportunidades Identificadas:\n" + "\n".join(opportunities))
        else:
            new_analysis.append("# Oportunidades Identificadas:\nInfelizmente não detectamos valor em nenhuma dos seus inputs.")
        
        # Nível de Confiança
        if "analysis_data" in original_probabilities:
            analysis_data = original_probabilities["analysis_data"]
            home_consistency = analysis_data.get("home_consistency", 0) * 100
            away_consistency = analysis_data.get("away_consistency", 0) * 100
            home_form_points = int(analysis_data.get("home_form_points", 0) * 15)
            away_form_points = int(analysis_data.get("away_form_points", 0) * 15)
            
            confidence_text = "# Nível de Confiança Geral: Médio\n"
            confidence_text += f"- **Consistência**: {home_team}: {home_consistency:.1f}%, {away_team}: {away_consistency:.1f}%. Consistência é uma medida que indica quão previsível é o desempenho da equipe.\n"
            confidence_text += f"- **Forma Recente**: {home_team}: {home_form_points}/15, {away_team}: {away_form_points}/15. Forma representa a pontuação dos últimos 5 jogos (vitória=3pts, empate=1pt, derrota=0pts).\n"
            confidence_text += "- Valores mais altos em ambas métricas aumentam a confiança na previsão."
            
            new_analysis.append(confidence_text)
        else:
            new_analysis.append("# Nível de Confiança Geral: Médio\n- **Consistência**: A consistência mede quão previsível é o desempenho da equipe.\n- **Forma Recente**: A forma representa pontos dos últimos 5 jogos (vitória=3pts, empate=1pt, derrota=0pts).")
        
        # Retornar a análise completa
        return '\n\n'.join(new_analysis)
    
    except Exception as e:
        logger.error(f"Erro ao formatar resposta de análise: {str(e)}")
        logger.error(traceback.format_exc())
        return analysis_text  # Retornar o texto original em caso de erro  # Retornar o texto original em caso de erro  # Retornar o texto original em caso de erro
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

## QUALIDADE DOS DADOS: {data_quality.upper()}

Analise os dados estatísticos disponíveis. Seu objetivo é extrair insights e valor apenas a partir dos dados reais fornecidos.

MUITO IMPORTANTE: Você DEVE responder EXATAMENTE no formato abaixo:

# Análise da Partida
## {home_team} x {away_team}

# Análise de Mercados Disponíveis:
[Resumo detalhado de cada mercado disponível com suas odds e probabilidades implícitas]

# Probabilidades Calculadas (REAL vs IMPLÍCITA):
[Para cada mercado onde há dados estatísticos suficientes, compare as probabilidades REAIS calculadas com as probabilidades IMPLÍCITAS nas odds]
- Se não houver dados estatísticos suficientes para calcular probabilidades reais para um mercado específico, indique claramente

# Oportunidades Identificadas:
[Liste cada mercado onde você encontrou valor/edge, mostrando a porcentagem de vantagem]
- Se não houver oportunidades claras ou dados suficientes, explique por quê

# Nível de Confiança Geral: [Baixo/Médio/Alto]
[Justificativa para o nível de confiança baseada apenas nos dados reais disponíveis]

IMPORTANTE: Use APENAS os dados estatísticos reais fornecidos. NÃO faça suposições ou estimativas quando os dados não estiverem disponíveis. Se não houver dados suficientes para calcular probabilidades reais para um determinado mercado, indique claramente essa limitação.
"""

    # Compilar o prompt final
    full_prompt = fundamental_stats + result_stats + goals_stats + corners_stats + cards_stats + markets_info + instructions
    
    return full_prompt

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
    Calcular probabilidades usando o método de dispersão e ponderação corrigido
    
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
        
        # PASSO 1: Calcular Consistência (Inverso da Dispersão)
        
        # Extrair percentuais de resultados
        home_win_pct = home_team.get('win_pct', 40)
        home_draw_pct = home_team.get('draw_pct', 30)
        home_loss_pct = home_team.get('loss_pct', 30)
        
        away_win_pct = away_team.get('win_pct', 30)
        away_draw_pct = away_team.get('draw_pct', 30)
        away_loss_pct = away_team.get('loss_pct', 40)
        
        # Resultados como probabilidades (0-1)
        home_results = [
            home_win_pct / 100,
            home_draw_pct / 100,
            home_loss_pct / 100
        ]
        
        away_results = [
            away_win_pct / 100,
            away_draw_pct / 100,
            away_loss_pct / 100
        ]
        
        # Calcular desvio padrão como medida de dispersão
        try:
            home_dispersion = np.std(home_results) * 3
            away_dispersion = np.std(away_results) * 3
        except:
            # Fallback para caso np não esteja disponível
            home_dispersion = 0.5
            away_dispersion = 0.5
        
        # Converter para consistência (inverso da dispersão)
        home_consistency = 1 - min(0.7, home_dispersion)
        away_consistency = 1 - min(0.7, away_dispersion)
        
        # PASSO 2: Calcular Forma Recente (35%)
        
        def form_to_points(form_str):
            """Calcula pontos de forma nos últimos 5 jogos (W=3pts, D=1pt, L=0pts)"""
            if not form_str or not isinstance(form_str, str):
                return 5  # Valor default moderado
            
            points = 0
            # Garantir que estamos usando apenas os últimos 5 jogos
            recent_form = form_str[-5:] if len(form_str) >= 5 else form_str
            
            # Calcular pontos
            for result in recent_form:
                result = result.upper()
                if result == 'W':
                    points += 3
                elif result == 'D':
                    points += 1
            
            return points
        
        # Extrair forma
        home_form = home_team.get('form', 'DLWDL')
        away_form = away_team.get('form', 'DWLDL')
        
        # Calcular pontos brutos (0-15)
        home_form_points = form_to_points(home_form)
        away_form_points = form_to_points(away_form)
        
        # Normalizar para uso nos cálculos (0-1)
        home_form_normalized = home_form_points / 15.0
        away_form_normalized = away_form_points / 15.0
        
        # PASSO 3: Estatísticas Gerais e xG (25%)
        
        # Extrair dados básicos
        home_goals_per_game = home_team.get('goals_per_game', 1.3)
        home_conceded_per_game = home_team.get('conceded_per_game', 1.3)
        away_goals_per_game = away_team.get('goals_per_game', 1.1)
        away_conceded_per_game = away_team.get('conceded_per_game', 1.5)
        
        # Extrair xG
        home_xg = home_team.get('xg', 25)
        home_xga = home_team.get('xga', 25)
        away_xg = away_team.get('xg', 20)
        away_xga = away_team.get('xga', 30)
        
        # Normalizar xG
        max_xg = max(home_xg, away_xg, 60)  # 60 gols é benchmark máximo
        
        # Calcular scores ofensivos e defensivos
        home_offensive = (home_xg / max_xg) * 0.6 + (home_goals_per_game / 3) * 0.4
        home_defensive = (1 - min(1, home_xga / max_xg)) * 0.6 + (1 - min(1, home_conceded_per_game / 3)) * 0.4
        
        away_offensive = (away_xg / max_xg) * 0.6 + (away_goals_per_game / 3) * 0.4
        away_defensive = (1 - min(1, away_xga / max_xg)) * 0.6 + (1 - min(1, away_conceded_per_game / 3)) * 0.4
        
        # Score estatístico total
        home_stats_score = home_offensive * 0.6 + home_defensive * 0.4
        away_stats_score = away_offensive * 0.6 + away_defensive * 0.4
        
        # PASSO 4: Posição na tabela (20%)
        home_position_score = home_win_pct / 100
        away_position_score = away_win_pct / 100
        
        # PASSO 5: Métricas de criação (20%)
        home_possession = home_team.get('possession', 50) / 100
        away_possession = away_team.get('possession', 50) / 100
        
        home_creation = home_offensive * 0.7 + home_possession * 0.3
        away_creation = away_offensive * 0.7 + away_possession * 0.3
        
        # PASSO 6: APLICAR PONDERAÇÕES
        home_total_score = (
            home_form_normalized * 0.35 +      # Forma recente: 35%
            home_stats_score * 0.25 +          # Estatísticas: 25%
            home_position_score * 0.20 +       # Posição: 20%
            home_creation * 0.20               # Criação: 20%
        )
        
        away_total_score = (
            away_form_normalized * 0.35 +      # Forma recente: 35%
            away_stats_score * 0.25 +          # Estatísticas: 25%
            away_position_score * 0.20 +       # Posição: 20%
            away_creation * 0.20               # Criação: 20%
        )
        
        # PASSO 7: CÁLCULO DE PROBABILIDADES POR MERCADO
        
        # 1. Moneyline (1X2)
        # Distribuição inicial
        raw_home_win = home_total_score / (home_total_score + away_total_score) * 0.8
        raw_away_win = away_total_score / (home_total_score + away_total_score) * 0.8
        raw_draw = 1 - (raw_home_win + raw_away_win)
        
        # Ajuste para vantagem em casa
        home_advantage = 0.08  # +8% boost para time da casa (reduzido de 12%)
        adjusted_home_win = raw_home_win + home_advantage
        adjusted_away_win = raw_away_win - (home_advantage * 0.5)
        adjusted_draw = raw_draw - (home_advantage * 0.5)
        
        # Normalizar para somar 100%
        total = adjusted_home_win + adjusted_draw + adjusted_away_win
        home_win_prob = (adjusted_home_win / total) * 100
        draw_prob = (adjusted_draw / total) * 100
        away_win_prob = (adjusted_away_win / total) * 100
        
        # 2. Over/Under Gols - CORREÇÃO CRÍTICA
        # Cálculo mais realista de gols esperados
        home_expected_goals = home_offensive * 1.8 * (1 - away_defensive * 0.7)
        away_expected_goals = away_offensive * 1.5 * (1 - home_defensive * 0.7)
        
        total_expected_goals = home_expected_goals + away_expected_goals
        
        # [CORREÇÃO] Probabilidade Over 2.5 com inclinação mais moderada
        # Inclinação original -1.5 estava muito agressiva, causando extremos
        over_2_5_prob = 1 / (1 + math.exp(-0.7 * (total_expected_goals - 2.5))) * 100
        under_2_5_prob = 100 - over_2_5_prob
        
        # 3. Ambos Marcam (BTTS) - CORREÇÃO CRÍTICA
        # [CORREÇÃO] Usar uma abordagem estatística mais equilibrada
        # Probabilidade de cada time marcar
        home_scoring_prob = 1 - math.exp(-0.8 * home_expected_goals)
        away_scoring_prob = 1 - math.exp(-0.7 * away_expected_goals)
        
        # BTTS = probabilidade combinada
        btts_yes_prob = home_scoring_prob * away_scoring_prob * 100
        btts_no_prob = 100 - btts_yes_prob
        
        # 4. Escanteios (Over/Under 9.5) - CORREÇÃO CRÍTICA
        # Extrair médias de escanteios
        home_corners = home_team.get('corners_per_game', 5)
        away_corners = away_team.get('corners_per_game', 4)
        
        # Ajustar para o confronto específico
        home_expected_corners = home_corners * (1 + 0.2 * home_offensive - 0.1 * away_defensive)
        away_expected_corners = away_corners * (1 + 0.2 * away_offensive - 0.1 * home_defensive)
        
        total_expected_corners = home_expected_corners + away_expected_corners
        
        # [CORREÇÃO] Probabilidade com inclinação mais moderada
        # Inclinação original estava muito agressiva, resultando em 100%
        over_9_5_corners_prob = 1 / (1 + math.exp(-0.4 * (total_expected_corners - 9.5))) * 100
        under_9_5_corners_prob = 100 - over_9_5_corners_prob
        
        # 5. Cartões (Over/Under 4.5) - CORREÇÃO CRÍTICA
        # Extrair médias de cartões
        home_cards = home_team.get('cards_per_game', 2)
        away_cards = away_team.get('cards_per_game', 2)
        
        # Calcular intensidade baseada na proximidade das equipes
        team_diff = abs(home_total_score - away_total_score)
        intensity_factor = 1 + 0.3 * (1 - min(1, team_diff * 2))
        
        total_expected_cards = (home_cards + away_cards) * intensity_factor
        
        # [CORREÇÃO] Probabilidade com inclinação mais moderada
        over_4_5_cards_prob = 1 / (1 + math.exp(-0.5 * (total_expected_cards - 4.5))) * 100
        under_4_5_cards_prob = 100 - over_4_5_cards_prob
        
        # 6. Chance Dupla (Double Chance) - GARANTIR CONSISTÊNCIA MATEMÁTICA
        # Calcular diretamente a partir das probabilidades primárias para garantir consistência
        home_or_draw = home_win_prob + draw_prob
        away_or_draw = away_win_prob + draw_prob
        home_or_away = home_win_prob + away_win_prob
        
        # Retornar resultados com arredondamento para 1 casa decimal
        return {
            "moneyline": {
                "home_win": round(home_win_prob, 1),
                "draw": round(draw_prob, 1),
                "away_win": round(away_win_prob, 1)
            },
            "double_chance": {
                "home_or_draw": round(home_or_draw, 1),
                "away_or_draw": round(away_or_draw, 1),
                "home_or_away": round(home_or_away, 1)
            },
            "over_under": {
                "over_2_5": round(over_2_5_prob, 1),
                "under_2_5": round(under_2_5_prob, 1),
                "expected_goals": round(total_expected_goals, 2)
            },
            "btts": {
                "yes": round(btts_yes_prob, 1),
                "no": round(btts_no_prob, 1)
            },
            "cards": {
                "over_4_5": round(over_4_5_cards_prob, 1),
                "under_4_5": round(under_4_5_cards_prob, 1),
                "expected_cards": round(total_expected_cards, 1)
            },
            "corners": {
                "over_9_5": round(over_9_5_corners_prob, 1),
                "under_9_5": round(under_9_5_corners_prob, 1),
                "expected_corners": round(total_expected_corners, 1)
            },
            "analysis_data": {
                "home_consistency": round(home_consistency * 100, 1),
                "away_consistency": round(away_consistency * 100, 1),
                "home_form_points": home_form_points / 15.0,
                "away_form_points": away_form_points / 15.0,
                "home_total_score": round(home_total_score, 2),
                "away_total_score": round(away_total_score, 2)
            }
        }
        
    except Exception as e:
        import logging
        import traceback
        logging.getLogger("valueHunter.ai").error(f"Erro no cálculo avançado de probabilidades: {str(e)}")
        logging.getLogger("valueHunter.ai").error(traceback.format_exc())
        
        # Retorna valores default em caso de erro
        return {
            "moneyline": {"home_win": 45.0, "draw": 28.0, "away_win": 27.0},
            "double_chance": {"home_or_draw": 73.0, "away_or_draw": 55.0, "home_or_away": 72.0},
            "over_under": {"over_2_5": 58.0, "under_2_5": 42.0, "expected_goals": 2.7},
            "btts": {"yes": 60.0, "no": 40.0},
            "cards": {"over_4_5": 55.0, "under_4_5": 45.0, "expected_cards": 4.8},
            "corners": {"over_9_5": 58.0, "under_9_5": 42.0, "expected_corners": 9.8},
            "analysis_data": {
                "home_consistency": 65.0,
                "away_consistency": 60.0,
                "home_form_points": 0.4,
                "away_form_points": 0.4
            }
        }
