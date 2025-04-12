
import os
import logging
import streamlit as st
import json
import math
import numpy as np  # Se você também estiver usando numpy
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
  - xG total: {home.get('xg', 0)} | xG em casa: {home.get('', 0)}
  - xGA total: {home.get('xga', 0)} | xGA em casa: {home.get('a', 0)}
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
        
        
        home_form = "WDLWW"  # Exemplo de string representando os últimos 5 jogos do time da casa
        away_form = "WDWWL"  # Exemplo para o time visitante
        # Primeiro, calculamos os pontos de forma
        home_form_points = form_to_points(home_form)
        away_form_points = form_to_points(away_form)
        
        # Normalizar para uso nos cálculos (0-1)
        home_form_normalized = home_form_points / 15.0
        away_form_normalized = away_form_points / 15.0
        
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
        
        # IMPORTANTE: Calcular home_stats_score e away_stats_score ANTES de usá-los
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
        
        # ONLY NOW - APPLY WEIGHTS with all variables correctly defined
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
        
        # Armazenar os valores para uso posterior
        analysis_data = {
            "home_consistency": home_consistency,
            "away_consistency": away_consistency,
            "home_form_points": home_form_points / 15.0,  # Armazenar como normalizado, mas o valor bruto é usado na exibição
            "away_form_points": away_form_points / 15.0,
            "home_total_score": home_total_score,
            "away_total_score": away_total_score
        }
        
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
        
def calculate_advanced_probabilities(home_team, away_team, league_id='generic', match_conditions=None):
    """
    Cálculo avançado de probabilidades utilizando método aprimorado de Dispersão e Ponderação
    
    Args:
        home_team (dict): Estatísticas do time da casa
        away_team (dict): Estatísticas do time visitante
        league_id (str): Identificador da liga para ajustes específicos
        match_conditions (dict): Condições da partida (clima, etc.)
        
    Returns:
        dict: Probabilidades calculadas para diferentes mercados
    """
    try:
        import math
        import numpy as np  # Adicione esta importação se necessário
        
        # 1. Obter fatores específicos da liga
        league_factors = calculate_league_factors(league_id, None)
        
        
        # 2. Calcular forma recente (35%)
        home_form_points = calculate_form_points(home_team.get('form', 'DLWDL'))
        away_form_points = calculate_form_points(away_team.get('form', 'DWLDL'))
        
        # Normalizar para 0-1
        home_form_normalized = home_form_points / 15.0
        away_form_normalized = away_form_points / 15.0
        
        # 3. Calcular consistência
        home_consistency = calculate_team_consistency(home_team) / 100.0
        away_consistency = calculate_team_consistency(away_team) / 100.0
        
        # 4. Calcular fatores de fadiga
        home_fatigue = calculate_team_fatigue(home_team)
        away_fatigue = calculate_team_fatigue(away_team)
        
        # 5. Calcular estatísticas técnicas (25%)
        home_offensive = calculate_offensive_strength(home_team)
        home_defensive = calculate_defensive_strength(home_team)
        away_offensive = calculate_offensive_strength(away_team)
        away_defensive = calculate_defensive_strength(away_team)
        
        # Ajustar por fadiga
        home_offensive *= home_fatigue
        home_defensive *= home_fatigue
        away_offensive *= away_fatigue
        away_defensive *= away_fatigue
        
        home_stats_score = home_offensive * 0.6 + home_defensive * 0.4
        away_stats_score = away_offensive * 0.6 + away_defensive * 0.4
        
        # 6. Calcular posição na tabela (20%)
        home_position_score = min(0.9, max(0.1, home_team.get('win_pct', 50) / 100))
        away_position_score = min(0.9, max(0.1, away_team.get('win_pct', 50) / 100))
        
        # 7. Calcular métricas de criação (20%)
        home_possession = min(0.8, max(0.2, home_team.get('possession', 50) / 100))
        away_possession = min(0.8, max(0.2, away_team.get('possession', 50) / 100))
        
        home_creation = home_offensive * 0.7 + home_possession * 0.3
        away_creation = away_offensive * 0.7 + away_possession * 0.3
        
        # 8. APLICAR PONDERAÇÕES
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
        
        # 9. Ajustar por condições da partida
        if match_conditions:
            # Fatores como clima, campo, etc.
            home_advantage_modifier = calculate_home_advantage_modifier(match_conditions)
        else:
            home_advantage_modifier = 1.0
        
        # 10. CALCULAR PROBABILIDADES POR MERCADO
        
        # 10.1. Moneyline (1X2)
        home_win_prob, draw_prob, away_win_prob = calculate_1x2_probabilities(
            home_total_score, away_total_score, 
            home_consistency, away_consistency,
            home_advantage_modifier
        )
        
        # 10.2. Expected goals e mercados relacionados
        home_expected_goals, away_expected_goals = calculate_advanced_expected_goals(
            home_team, away_team, league_factors
        )
        
        total_expected_goals = home_expected_goals + away_expected_goals
        
        # 10.3. Probabilidades Over/Under para múltiplos thresholds
        over_under_probabilities = {}
        for threshold in [0.5, 1.5, 2.5, 3.5, 4.5]:
            over_prob = calculate_over_probability(home_expected_goals, away_expected_goals, threshold)
            over_under_probabilities[f"over_{threshold}"] = over_prob * 100
            over_under_probabilities[f"under_{threshold}"] = (1 - over_prob) * 100
        
        # 10.4. Ambos Marcam (BTTS)
        btts_yes_prob, btts_no_prob = calculate_btts_probability(
            home_expected_goals, away_expected_goals, league_factors[1]
        )
        
        # 10.5. Escanteios
        over_corners_prob, under_corners_prob, expected_corners = calculate_corners_probability(
            home_team, away_team, 9.5, league_factors[3]
        )
        
        # 10.6. Cartões
        over_cards_prob, under_cards_prob, expected_cards = calculate_cards_probability(
            home_team, away_team, 4.5, league_factors[2],
            abs(home_total_score - away_total_score)
        )
        
        # 11. Retornar resultados completos
        return {
            "moneyline": {
                "home_win": round(home_win_prob * 100, 1),
                "draw": round(draw_prob * 100, 1),
                "away_win": round(away_win_prob * 100, 1)
            },
            "double_chance": {
                "home_or_draw": round((home_win_prob + draw_prob) * 100, 1),
                "away_or_draw": round((away_win_prob + draw_prob) * 100, 1),
                "home_or_away": round((home_win_prob + away_win_prob) * 100, 1)
            },
            "over_under": {
                "over_2_5": round(over_under_probabilities["over_2.5"], 1),
                "under_2_5": round(over_under_probabilities["under_2.5"], 1),
                "expected_goals": round(total_expected_goals, 2),
                # Incluir outros thresholds
                "over_1_5": round(over_under_probabilities["over_1.5"], 1),
                "under_1_5": round(over_under_probabilities["under_1.5"], 1),
                "over_3_5": round(over_under_probabilities["over_3.5"], 1),
                "under_3_5": round(over_under_probabilities["under_3.5"], 1)
            },
            "btts": {
                "yes": round(btts_yes_prob * 100, 1),
                "no": round(btts_no_prob * 100, 1)
            },
            "cards": {
                "over_4_5": round(over_cards_prob * 100, 1),
                "under_4_5": round(under_cards_prob * 100, 1),
                "expected_cards": round(expected_cards, 1)
            },
            "corners": {
                "over_9_5": round(over_corners_prob * 100, 1),
                "under_9_5": round(under_corners_prob * 100, 1),
                "expected_corners": round(expected_corners, 1)
            },
            "analysis_data": {
                "home_consistency": round(home_consistency * 100, 1),
                "away_consistency": round(away_consistency * 100, 1),
                "home_form_points": home_form_points / 15.0,
                "away_form_points": away_form_points / 15.0,
                "home_total_score": round(home_total_score, 2),
                "away_total_score": round(away_total_score, 2),
                "home_fatigue": round(home_fatigue * 100, 1),
                "away_fatigue": round(away_fatigue * 100, 1)
            }
        }
        
    except Exception as e:
        import logging
        import traceback
        logging.getLogger("valueHunter.ai").error(f"Erro no cálculo avançado: {str(e)}")
        logging.getLogger("valueHunter.ai").error(traceback.format_exc())
        
        # Re-raise a exception para que seja tratada apropriadamente em outro lugar
        # Não usar fallback, conforme solicitado
        raise

def calculate_league_factors(league_id, league_data=None):
    """
    Calcula fatores específicos por liga para ajustar as probabilidades
    
    Args:
        league_id (str): Identificador da liga
        league_data (dict, optional): Dados adicionais da liga
        
    Returns:
        list: Lista de fatores de ajuste [gols, btts, cartões, escanteios]
    """
    # Importações necessárias
    from utils.footystats_api import LEAGUE_IDS, get_league_id_mapping
    import logging
    logger = logging.getLogger("valueHunter.ai")
    
    # Verificar se league_id existe ou é um valor genérico
    if not league_id or league_id in ['default', 'generic']:
        logger.info(f"Usando fatores genéricos para league_id: {league_id}")
        return [1.0, 1.0, 1.0, 1.0]  # Fatores neutros para gols, btts, cartões, escanteios
        
    # Se temos dados específicos da liga, usar esses dados
    if league_data and isinstance(league_data, dict):
        # Extrair fatores dos dados, sem usar fallback
        if 'goals_factor' not in league_data or 'btts_factor' not in league_data:
            raise ValueError(f"Dados insuficientes para liga ID {league_id}")
            
        return [
            league_data.get('goals_factor'),
            league_data.get('btts_factor'),
            league_data.get('cards_factor'),
            league_data.get('corners_factor')
        ]
    
    # Mapeamento de fatores específicos por liga
    # Usando os mesmos league_ids que estão em utils/footystats_api.py
    league_factors = {
        # Liga IDs estão no arquivo footystats_api.py
        # Brasileirão
        14231: [1.0, 0.95, 1.15, 1.05],  
        
        # Premier League 
        12325: [1.1, 1.1, 1.0, 1.15],  
        
        # La Liga
        12316: [1.1, 1.05, 1.2, 0.95],  
        
        # Bundesliga 
        12529: [1.2, 1.15, 0.9, 1.1],   
        
        # Serie A (Italy)
        12530: [0.9, 0.85, 1.15, 0.9],  
        
        # Ligue 1
        12337: [1.0, 0.95, 1.05, 1.0],  
        
        # Primeira Liga
        12931: [1.05, 1.0, 1.25, 1.05], 
        
        # Eredivisie
        12322: [1.15, 1.1, 0.95, 1.05],  
        
        # Liga MX
        12136: [1.1, 1.05, 1.05, 1.0],   
        
        # Champions League
        12321: [1.05, 1.0, 1.1, 1.1],
        
        # Outras ligas importantes
        14125: [1.05, 1.0, 1.2, 1.0],   # Primera División (Argentina)
        14305: [1.0, 0.95, 1.15, 1.05], # Serie B (Brazil)
        12467: [1.0, 0.95, 1.15, 0.9],  # Segunda División
        12528: [1.15, 1.1, 0.9, 1.05],  # 2. Bundesliga
        12621: [0.9, 0.85, 1.1, 0.9],   # Serie B (Italy)
        12338: [0.95, 0.9, 1.0, 0.95],  # Ligue 2
    }
    
    # Verificar se a liga está no dicionário
    # Converter league_id para int para garantir compatibilidade
    try:
        league_id_int = int(league_id)
        if league_id_int in league_factors:
            logger.info(f"Fatores encontrados para liga ID {league_id_int}")
            return league_factors[league_id_int]
    except (ValueError, TypeError):
        # Se league_id não for um número, pode ser um código de string
        pass
        
    # Se liga não encontrada, tentar buscar via mapeamento
    try:
        # Buscar o mapeamento completo (sem fallback)
        league_mapping = get_league_id_mapping()
        
        # Se league_id é um nome de liga, tente encontrar o ID numérico
        if league_id in league_mapping:
            numeric_id = league_mapping[league_id]
            if numeric_id in league_factors:
                logger.info(f"Fatores encontrados para liga '{league_id}' (ID {numeric_id})")
                return league_factors[numeric_id]
    except Exception as e:
        logger.error(f"Erro ao buscar mapeamento de ligas: {str(e)}")
    
    # Se a liga não é encontrada em lugar algum, lançar erro
    raise ValueError(f"Liga ID {league_id} não suportada e sem dados para calibração")
def calibrated_logistic(x, threshold, market_type):
    """
    Função logística calibrada por tipo de mercado
    """
    # Parâmetros calibrados por mercado
    params = {
        'goals': {'slope': 0.6, 'shift': 0.0},     # Over/Under gols
        'btts': {'slope': 0.7, 'shift': 0.1},      # Ambos marcam
        'corners': {'slope': 0.45, 'shift': 0.05}, # Escanteios
        'cards': {'slope': 0.5, 'shift': -0.1},    # Cartões
        'result': {'slope': 0.65, 'shift': 0.0}    # 1X2
    }
    
    p = params.get(market_type, {'slope': 0.5, 'shift': 0.0})
    slope, shift = p['slope'], p['shift']
    
    # Cálculo com parâmetros calibrados
    return 1 / (1 + math.exp(-slope * (x - threshold + shift)))

def ensemble_prediction(models_output, weights=None):
    """
    Combina previsões de diferentes modelos usando pesos
    """
    if weights is None:
        # Pesos default
        weights = [0.5, 0.3, 0.2]  # Ajustar conforme a confiança em cada modelo
    
    # Normalizar pesos
    weights = [w / sum(weights) for w in weights]
    
    # Combinação ponderada
    result = 0
    for i, model_output in enumerate(models_output):
        result += model_output * weights[i]
    
    return result

# Uso:
def calculate_over_under_probability(home_team, away_team, threshold=2.5):
    # Modelo 1: Baseado em xG
    model1 = calculate_xg_based_probability(home_team, away_team, threshold)
    
    # Modelo 2: Baseado em resultados históricos
    model2 = calculate_historical_probability(home_team, away_team, threshold)
    
    # Modelo 3: Baseado em tendências recentes
    model3 = calculate_recent_trend_probability(home_team, away_team, threshold)
    
    # Combinar modelos
    final_prob = ensemble_prediction([model1, model2, model3], [0.5, 0.3, 0.2])
    
    return final_prob

def calculate_team_fatigue(team_data):
    """
    Calcula o fator de fadiga baseado em jogos recentes e viagens
    """
    # Dias desde o último jogo
    days_since_last_match = team_data.get('days_since_last_match', 5)
    
    # Número de jogos nos últimos 15 dias
    recent_matches = team_data.get('matches_last_15_days', 2)
    
    # Distância de viagem para o jogo (em km)
    travel_distance = team_data.get('travel_distance', 100)
    
    # Cálculo do fator de fadiga (0-1, onde 1 = sem fadiga)
    rest_factor = min(1.0, days_since_last_match / 5)
    schedule_factor = max(0.7, 1 - (recent_matches - 2) * 0.1)
    travel_factor = max(0.8, 1 - (travel_distance / 1000) * 0.05)
    
    # Fator combinado
    fatigue_factor = rest_factor * 0.4 + schedule_factor * 0.4 + travel_factor * 0.2
    
    return fatigue_factor

def update_calibration_parameters(prediction_history, actual_results, market_type):
    """
    Atualiza parâmetros de calibração baseado em desempenho histórico
    """
    # Minimum sample size before adjusting parameters
    if len(prediction_history) < 50:
        return None
    
    # Calculate calibration error (Brier score)
    brier_score = sum((p - a) ** 2 for p, a in zip(prediction_history, actual_results)) / len(prediction_history)
    
    # Calibration parameters
    calibration = {
        'mean_prediction': sum(prediction_history) / len(prediction_history),
        'mean_outcome': sum(actual_results) / len(actual_results),
        'brier_score': brier_score,
        'sample_size': len(prediction_history)
    }
    
    # Calculate adjustment factor
    adjustment = (calibration['mean_outcome'] - calibration['mean_prediction'])
    
    # Calculate new calibration parameters
    new_params = {
        'slope': max(0.3, min(1.0, 0.5 + adjustment * 2)),
        'shift': max(-0.3, min(0.3, adjustment * 3))
    }
    
    return new_params

def calculate_team_consistency(team_data):
    """
    Calcula consistência da equipe baseada em variação de desempenho
    """
    # Obter histórico de resultados recentes
    recent_results = team_data.get('recent_results', [])
    
    if not recent_results or len(recent_results) < 5:
        return 0.5  # Valor médio default
    
    # Calcular pontos por jogo
    points_per_game = []
    for result in recent_results[:10]:  # Últimos 10 jogos
        if result.upper() == 'W':
            points_per_game.append(3)
        elif result.upper() == 'D':
            points_per_game.append(1)
        else:
            points_per_game.append(0)
    
    # Calcular desvio padrão dos pontos
    if len(points_per_game) >= 2:
        mean_points = sum(points_per_game) / len(points_per_game)
        variance = sum((p - mean_points) ** 2 for p in points_per_game) / len(points_per_game)
        std_dev = math.sqrt(variance)
        
        # Convertendo desvio para consistência (inverso)
        # Desvio padrão max teórico é ~1.5 para futebol
        consistency = 1 - min(1, std_dev / 1.5)
        
        # Escalar para percentual entre 30% e 90%
        consistency_pct = 30 + consistency * 60
        
        return consistency_pct
    
    return 60  # Valor moderado default

def calculate_advanced_expected_goals(home_team, away_team, league_factors):
    """
    Calcula expected goals considerando múltiplos fatores
    """
    # Extrair estatísticas base
    home_xg_per_game = home_team.get('xg_for_avg', home_team.get('goals_per_game', 1.3))
    home_xga_per_game = home_team.get('xg_against_avg', home_team.get('conceded_per_game', 1.3))
    away_xg_per_game = away_team.get('xg_for_avg', away_team.get('goals_per_game', 1.1))
    away_xga_per_game = away_team.get('xg_against_avg', away_team.get('conceded_per_game', 1.5))
    
    # Ajustes para casa/fora
    home_xg_per_game_home = home_team.get('home_xg_for_avg', home_xg_per_game * 1.1)
    away_xg_per_game_away = away_team.get('away_xg_for_avg', away_xg_per_game * 0.9)
    home_xga_per_game_home = home_team.get('home_xg_against_avg', home_xga_per_game * 0.9)
    away_xga_per_game_away = away_team.get('away_xg_against_avg', away_xga_per_game * 1.1)
    
    # Calcular xG esperado para o jogo
    home_expected_goals = (home_xg_per_game_home + away_xga_per_game_away) / 2
    away_expected_goals = (away_xg_per_game_away + home_xga_per_game_home) / 2
    
    # Ajustar pelo fator da liga
    league_goals_factor = league_factors[0]
    home_expected_goals *= league_goals_factor
    away_expected_goals *= league_goals_factor
    
    # Ajustar por fadiga (se disponível)
    home_fatigue = calculate_team_fatigue(home_team)
    away_fatigue = calculate_team_fatigue(away_team)
    
    home_expected_goals *= home_fatigue
    away_expected_goals *= away_fatigue
    
    # Considerar probabilidade de clean sheet
    home_cs_prob = home_team.get('clean_sheet_probability', 0.3)
    away_cs_prob = away_team.get('clean_sheet_probability', 0.2)
    
    # Ajustar expected goals por probabilidade de clean sheet
    home_expected_goals *= (1 - away_cs_prob)
    away_expected_goals *= (1 - home_cs_prob)
    
    return home_expected_goals, away_expected_goals

def calculate_form_points(form_str):
    """Calcula pontos baseados na forma recente"""
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

def calculate_offensive_strength(team):
    """Calcula a força ofensiva baseada em xG e gols marcados"""
    xg = team.get('xg', 0)
    goals = team.get('goals_scored', 0)
    games = max(1, team.get('matches_played', 1))
    
    # Normalizar para média por jogo
    xg_per_game = xg / games
    goals_per_game = goals / games
    
    # Valor combinado com limite
    return min(0.9, max(0.1, (xg_per_game / 2.5) * 0.7 + (goals_per_game / 2.5) * 0.3))

def calculate_defensive_strength(team):
    """Calcula a força defensiva baseada em xGA e gols sofridos"""
    xga = team.get('xga', 0)
    goals_against = team.get('goals_conceded', 0)
    games = max(1, team.get('matches_played', 1))
    
    # Normalizar para média por jogo
    xga_per_game = xga / games
    conceded_per_game = goals_against / games
    
    # Força defensiva (inverso da fraqueza)
    return min(0.9, max(0.1, 1 - ((xga_per_game / 2.5) * 0.7 + (conceded_per_game / 2.5) * 0.3)))

def calculate_1x2_probabilities(home_score, away_score, home_consistency, away_consistency, home_adv_mod=1.0):
    """Calcula probabilidades 1X2 com distribuição ajustada"""
    # Base raw probabilities
    total_score = home_score + away_score
    base_home = home_score / total_score
    base_away = away_score / total_score
    
    # Ajustar para vantagem em casa
    home_advantage = 0.07 * home_adv_mod  # Ajustável por condições
    
    # Aplicar vantagem em casa
    adjusted_home = min(0.75, base_home + home_advantage)
    adjusted_away = max(0.15, base_away - (home_advantage * 0.7))
    
    # Calcular empate baseado em consistências
    # Equipes mais consistentes = menos empates
    avg_consistency = (home_consistency + away_consistency) / 2
    draw_factor = 1 - avg_consistency  # Menor consistência = mais empates
    
    # Base draw probability
    base_draw = 0.25 * draw_factor
    
    # Ajustar distribuição para garantir soma 1
    total_raw = adjusted_home + adjusted_away + base_draw
    
    home_win = adjusted_home / total_raw
    away_win = adjusted_away / total_raw
    draw = base_draw / total_raw
    
    return home_win, draw, away_win

def calculate_over_probability(home_xg, away_xg, threshold):
    """Calcula probabilidade de Over usando distribuição de Poisson"""
    lambda_total = home_xg + away_xg
    
    # Usar cálculo exato de Poisson para o threshold
    cumulative_prob = 0
    for i in range(int(threshold) + 1):
        cumulative_prob += math.exp(-lambda_total) * (lambda_total ** i) / math.factorial(i)
    
    # Probabilidade de Over = 1 - P(gols <= threshold)
    return min(0.95, max(0.05, 1 - cumulative_prob))

def calculate_btts_probability(home_xg, away_xg, league_btts_factor):
    """Calcula probabilidade de Ambos Marcam"""
    # Probabilidade de cada time não marcar (Poisson para 0 gols)
    p_home_no_goal = math.exp(-home_xg)
    p_away_no_goal = math.exp(-away_xg)
    
    # Probabilidade de pelo menos um time não marcar
    p_not_btts = p_home_no_goal + p_away_no_goal - (p_home_no_goal * p_away_no_goal)
    
    # Probabilidade de ambos marcarem
    p_btts = 1 - p_not_btts
    
    # Ajustar pelo fator da liga
    p_btts *= league_btts_factor
    
    # Limitar a valores razoáveis
    p_btts = min(0.85, max(0.25, p_btts))
    
    return p_btts, 1 - p_btts

def calculate_corners_probability(home_team, away_team, threshold, league_corner_factor):
    """Calcula probabilidades para mercados de escanteios"""
    # Extrair estatísticas de escanteios
    home_corners_for = home_team.get('corners_for', 0) / max(1, home_team.get('matches_played', 1))
    home_corners_against = home_team.get('corners_against', 0) / max(1, home_team.get('matches_played', 1))
    away_corners_for = away_team.get('corners_for', 0) / max(1, away_team.get('matches_played', 1))
    away_corners_against = away_team.get('corners_against', 0) / max(1, away_team.get('matches_played', 1))
    
    # Escanteios esperados para cada time
    home_expected = (home_corners_for + away_corners_against) / 2
    away_expected = (away_corners_for + home_corners_against) / 2
    
    # Total esperado
    total_expected = (home_expected + away_expected) * league_corner_factor
    
    # Cálculo de probabilidade usando aproximação normal
    # Desvio padrão estimado
    std_dev = math.sqrt(total_expected)
    
    # Z-score para threshold
    z = (threshold - total_expected) / std_dev
    
    # Aproximação da função de distribuição normal cumulativa
    def normal_cdf(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    # Probabilidade under
    p_under = normal_cdf(z)
    
    # Limitar a valores razoáveis
    p_under = min(0.9, max(0.1, p_under))
    p_over = 1 - p_under
    
    return p_over, p_under, total_expected

def calculate_cards_probability(home_team, away_team, threshold, league_card_factor, team_diff):
    """Calcula probabilidades para mercados de cartões"""
    # Extrair estatísticas de cartões
    home_cards = home_team.get('cards_per_game', 2)
    away_cards = away_team.get('cards_per_game', 2)
    
    # Fator de intensidade baseado na proximidade das equipes
    intensity_factor = 1 + 0.3 * (1 - min(1, team_diff * 2))
    
    # Cartões esperados ajustados por intensidade e fator da liga
    expected_cards = (home_cards + away_cards) * intensity_factor * league_card_factor
    
    # Usando aproximação normal
    std_dev = math.sqrt(expected_cards * 0.7)  # Desvio estimado
    
    # Z-score para threshold
    z = (threshold - expected_cards) / std_dev
    
    # Aproximação da função de distribuição normal cumulativa
    def normal_cdf(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    # Probabilidade under
    p_under = normal_cdf(z)
    
    # Limitar a valores razoáveis
    p_under = min(0.85, max(0.15, p_under))
    p_over = 1 - p_under
    
    return p_over, p_under, expected_cards

def calculate_home_advantage_modifier(conditions):
    """Calcula modificador para vantagem em casa baseado em condições da partida"""
    # Valores default
    mod = 1.0
    
    # Ajustes baseados em condições
    if conditions.get('crowd_percentage', 100) < 50:
        mod *= 0.8  # Menos torcida = menos vantagem
    
    if conditions.get('weather', '').lower() in ['snow', 'heavy_rain']:
        mod *= 0.9  # Clima ruim reduz vantagem
    
    if conditions.get('neutral_venue', False):
        mod *= 0.5  # Campo neutro reduz significativamente a vantagem
    
    if conditions.get('altitude_difference', 0) > 1000:
        mod *= 1.2  # Grande diferença de altitude aumenta vantagem
    
    return max(0.3, min(1.5, mod))  # Limitar entre 0.3 e 1.5

def analyze_missing_players(team_data):
    """
    Analisa o impacto de jogadores lesionados ou suspensos
    """
    missing_players = team_data.get('missing_players', [])
    
    if not missing_players:
        return 1.0  # Sem impacto
    
    total_impact = 0
    
    for player in missing_players:
        position = player.get('position', '').lower()
        importance = player.get('importance', 'medium').lower()
        
        # Definir peso de impacto por posição e importância
        position_weights = {
            'goalkeeper': 0.15,
            'defender': 0.10,
            'midfielder': 0.08,
            'forward': 0.12
        }
        
        importance_multipliers = {
            'key': 1.5,      # Jogador-chave
            'starter': 1.0,  # Titular regular
            'rotation': 0.6, # Jogador de rotação 
            'backup': 0.3    # Reserva
        }
        
        # Calcular impacto
        position_weight = position_weights.get(position, 0.05)
        importance_multiplier = importance_multipliers.get(importance, 0.5)
        
        player_impact = position_weight * importance_multiplier
        total_impact += player_impact
    
    # Limitar impacto total
    total_impact = min(0.5, total_impact)
    
    # Retornar fator de ajuste (1.0 = sem impacto, <1.0 = impacto negativo)
    return 1.0 - total_impact
def analyze_game_trends(home_team, away_team):
    """
    Analisa tendências de jogo baseadas no estilo de cada equipe
    """
    # Extrair métricas de estilo
    home_possession = home_team.get('possession', 50) / 100
    away_possession = away_team.get('possession', 50) / 100
    
    home_pass_completion = home_team.get('pass_completion', 75) / 100
    away_pass_completion = away_team.get('pass_completion', 75) / 100
    
    home_shots_per_game = home_team.get('shots_per_game', 12)
    away_shots_per_game = away_team.get('shots_per_game', 12)
    
    # Determinar estilos de jogo
    home_direct_play = 1 - home_pass_completion  # Menor pass completion = jogo mais direto
    away_direct_play = 1 - away_pass_completion
    
    home_attacking_intensity = home_shots_per_game / 15  # Normalizado para ~1.0
    away_attacking_intensity = away_shots_per_game / 15
    
    # Calcular probabilidades de ritmo de jogo
    game_tempo = (home_attacking_intensity + away_attacking_intensity) / 2
    
    # Contraste de estilos
    style_contrast = abs(home_direct_play - away_direct_play) + abs(home_possession - away_possession)
    
    # Probabilidade de jogo aberto vs fechado
    open_game_prob = (game_tempo * 0.7 + style_contrast * 0.3) * 100
    
    # Probabilidade de muitos gols
    high_scoring_prob = open_game_prob * 0.8
    
    # Probabilidade de jogo intenso (muitos cartões)
    intense_game_prob = (style_contrast * 0.6 + game_tempo * 0.4) * 100
    
    return {
        'open_game_probability': min(85, max(15, open_game_prob)),
        'high_scoring_probability': min(80, max(20, high_scoring_prob)),
        'intense_game_probability': min(80, max(20, intense_game_prob))
    }

def get_adaptive_league_calibration(league_id, database_stats):
    """
    Obtém calibração adaptativa para ligas com poucos dados
    """
    # Verificar se temos dados suficientes específicos para a liga
    league_matches = database_stats.get('matches_per_league', {}).get(league_id, 0)
    
    if league_matches < 50:
        # Poucos dados: usar calibração baseada em ligas similares
        region = get_league_region(league_id)
        tier = get_league_tier(league_id)
        
        # Encontrar ligas similares
        similar_leagues = find_similar_leagues(region, tier)
        
        # Usar média ponderada das calibrações de ligas similares
        if similar_leagues:
            calibration = average_league_calibrations(similar_leagues)
            return calibration
    
    # Dados suficientes: usar calibração específica
    return get_specific_league_calibration(league_id)

class AdvancedPredictionSystem:
    """
    Sistema avançado de predição que incorpora múltiplos modelos sem fallbacks
    """
    
    def __init__(self, database_connection=None, config=None):
        """Inicializa o sistema de predição"""
        self.database = database_connection
        self.config = config or {}
        
        # Verificar se temos conexão com banco de dados
        if not self.database:
            raise ValueError("Conexão com banco de dados é obrigatória")
            
        # Carregar dados de calibração
        self.calibration_data = self._load_calibration_data()
        self.league_factors = self._load_league_factors()
        self.performance_metrics = {}
    
    def _load_calibration_data(self):
        """Carrega dados de calibração do banco de dados - sem fallback"""
        # Tentar carregar do banco de dados
        try:
            return self.database.get_calibration_data()
        except Exception as e:
            # Em vez de fornecer fallback, propagar o erro
            raise ValueError(f"Falha ao carregar dados de calibração: {str(e)}")
    
    def _load_league_factors(self):
        """Carrega fatores específicos por liga - sem fallback"""
        try:
            # Tentar carregar do banco de dados
            return self.database.get_league_factors()
        except Exception as e:
            # Em vez de fornecer fallback, propagar o erro
            raise ValueError(f"Falha ao carregar fatores de liga: {str(e)}")
    
    def predict_match(self, home_team, away_team, league_id, match_conditions=None):
        """
        Realiza predição completa para uma partida sem usar fallbacks
        """
        # Verificar se os dados necessários estão presentes
        self._validate_team_data(home_team, "home_team")
        self._validate_team_data(away_team, "away_team")
        
        if not league_id:
            raise ValueError("ID da liga é obrigatório")
        
        # Obter fatores específicos da liga
        if league_id not in self.league_factors:
            raise ValueError(f"Fatores para liga ID {league_id} não encontrados")
            
        league_factors = self.league_factors[league_id]
        
        # Aplicar análise de jogadores ausentes
        home_injury_factor = self._analyze_missing_players(home_team)
        away_injury_factor = self._analyze_missing_players(away_team)
        
        # Ajustar estatísticas baseado em lesões/suspensões
        adjusted_home_team = self._adjust_for_injuries(home_team, home_injury_factor)
        adjusted_away_team = self._adjust_for_injuries(away_team, away_injury_factor)
        
        # Analisar tendências de jogo
        game_trends = self._analyze_game_trends(adjusted_home_team, adjusted_away_team)
        
        # Obter calibração adaptativa para a liga
        calibration = self._get_adaptive_league_calibration(league_id)
        
        # Executar cálculo avançado
        return self._calculate_advanced_probabilities(
            adjusted_home_team, 
            adjusted_away_team, 
            league_factors, 
            calibration,
            match_conditions,
            game_trends
        )
    
    def _validate_team_data(self, team_data, team_type):
        """
        Valida se os dados do time contêm campos essenciais
        Lança exceção em vez de usar valores padrão
        """
        essential_fields = [
            "played", "wins", "draws", "losses",
            "goals_scored", "goals_conceded",
            "form"
        ]
        
        missing_fields = [field for field in essential_fields if field not in team_data]
        
        if missing_fields:
            raise ValueError(f"Dados incompletos para {team_type}. Campos ausentes: {missing_fields}")
            
        # Verificar valores zero que poderiam causar divisão por zero
        if team_data.get("played", 0) == 0:
            raise ValueError(f"{team_type} tem 'played' igual a zero, impossível calcular médias")
    
    def _analyze_missing_players(self, team_data):
        """
        Analisa o impacto de jogadores lesionados ou suspensos
        Sem fallback - requer dados de jogadores ausentes
        """
        if "missing_players" not in team_data or not team_data["missing_players"]:
            return 1.0  # Sem impacto quando não há dados
        
        missing_players = team_data["missing_players"]
        total_impact = 0
        
        for player in missing_players:
            # Verificar se temos dados suficientes
            if "position" not in player or "importance" not in player:
                raise ValueError("Dados incompletos para jogadores ausentes")
                
            position = player["position"].lower()
            importance = player["importance"].lower()
            
            # Definir peso de impacto por posição e importância
            position_weights = {
                'goalkeeper': 0.15,
                'defender': 0.10,
                'midfielder': 0.08,
                'forward': 0.12
            }
            
            importance_multipliers = {
                'key': 1.5,      # Jogador-chave
                'starter': 1.0,  # Titular regular
                'rotation': 0.6, # Jogador de rotação 
                'backup': 0.3    # Reserva
            }
            
            # Verificar se a posição e importância estão nas categorias conhecidas
            if position not in position_weights:
                raise ValueError(f"Posição desconhecida: {position}")
                
            if importance not in importance_multipliers:
                raise ValueError(f"Importância desconhecida: {importance}")
            
            # Calcular impacto
            position_weight = position_weights[position]
            importance_multiplier = importance_multipliers[importance]
            
            player_impact = position_weight * importance_multiplier
            total_impact += player_impact
        
        # Limitar impacto total
        total_impact = min(0.5, total_impact)
        
        # Retornar fator de ajuste (1.0 = sem impacto, <1.0 = impacto negativo)
        return 1.0 - total_impact
    
    def _adjust_for_injuries(self, team_data, injury_factor):
        """Ajusta estatísticas do time baseado em lesões/suspensões"""
        adjusted_team = team_data.copy()
        
        # Ajustar estatísticas ofensivas
        for stat in ['xg', 'goals_scored', 'shots_per_game']:
            if stat in adjusted_team:
                adjusted_team[stat] = adjusted_team[stat] * injury_factor
        
        return adjusted_team
    
    def _analyze_game_trends(self, home_team, away_team):
        """
        Analisa tendências de jogo baseadas no estilo de cada equipe
        """
        # Verificar dados essenciais
        required_fields = ["possession", "pass_completion", "shots_per_game"]
        
        for field in required_fields:
            if field not in home_team:
                raise ValueError(f"Campo ausente em home_team: {field}")
            if field not in away_team:
                raise ValueError(f"Campo ausente em away_team: {field}")
        
        # Extrair métricas de estilo
        home_possession = home_team["possession"] / 100
        away_possession = away_team["possession"] / 100
        
        home_pass_completion = home_team["pass_completion"] / 100
        away_pass_completion = away_team["pass_completion"] / 100
        
        home_shots_per_game = home_team["shots_per_game"]
        away_shots_per_game = away_team["shots_per_game"]
        
        # Determinar estilos de jogo
        home_direct_play = 1 - home_pass_completion
        away_direct_play = 1 - away_pass_completion
        
        home_attacking_intensity = home_shots_per_game / 15
        away_attacking_intensity = away_shots_per_game / 15
        
        # Calcular probabilidades de ritmo de jogo
        game_tempo = (home_attacking_intensity + away_attacking_intensity) / 2
        
        # Contraste de estilos
        style_contrast = abs(home_direct_play - away_direct_play) + abs(home_possession - away_possession)
        
        # Probabilidade de jogo aberto vs fechado
        open_game_prob = (game_tempo * 0.7 + style_contrast * 0.3) * 100
        
        # Probabilidade de muitos gols
        high_scoring_prob = open_game_prob * 0.8
        
        # Probabilidade de jogo intenso (muitos cartões)
        intense_game_prob = (style_contrast * 0.6 + game_tempo * 0.4) * 100
        
        return {
            'open_game_probability': min(85, max(15, open_game_prob)),
            'high_scoring_probability': min(80, max(20, high_scoring_prob)),
            'intense_game_probability': min(80, max(20, intense_game_prob))
        }
    
    def _get_adaptive_league_calibration(self, league_id):
        """
        Obtém calibração adaptativa para liga específica
        """
        # Verificar se temos calibração específica para esta liga
        league_specific_key = f"league_{league_id}"
        
        if league_specific_key in self.calibration_data:
            return self.calibration_data[league_specific_key]
        
        # Não usar fallback - exigir calibração específica
        raise ValueError(f"Calibração não encontrada para liga ID {league_id}")
    
    def _calculate_advanced_probabilities(self, home_team, away_team, league_factors, 
                                        calibration, match_conditions, game_trends):
        """
        Implementação do algoritmo de cálculo avançado sem fallbacks
        """
        import math
        
        # 1. FORMA RECENTE (35%)
        # Calcular forma usando os pontos dos últimos 5 jogos
        home_form = home_team["form"]
        away_form = away_team["form"]
        
        # Validar forma
        if len(home_form) < 5 or len(away_form) < 5:
            raise ValueError("Forma incompleta (menos de 5 jogos)")
        
        # Converter forma para pontos
        home_form_points = 0
        for result in home_form[:5]:
            if result.upper() == 'W':
                home_form_points += 3
            elif result.upper() == 'D':
                home_form_points += 1
        
        away_form_points = 0
        for result in away_form[:5]:
            if result.upper() == 'W':
                away_form_points += 3
            elif result.upper() == 'D':
                away_form_points += 1
        
        # Normalizar para uso nos cálculos (0-1)
        home_form_normalized = home_form_points / 15.0
        away_form_normalized = away_form_points / 15.0
        
        # 2. ESTATÍSTICAS GERAIS E XG (25%)
        # Validar dados essenciais
        for team, team_name in [(home_team, "home"), (away_team, "away")]:
            required_stats = ["xg", "xga", "possession", "goals_per_game", "conceded_per_game"]
            missing = [stat for stat in required_stats if stat not in team]
            if missing:
                raise ValueError(f"Estatísticas ausentes para {team_name}: {missing}")
        
        # Calcular scores ofensivos e defensivos
        home_offensive = (home_team["xg"] / 60) * 0.6 + (home_team["goals_per_game"] / 3) * 0.4
        home_defensive = (1 - min(1, home_team["xga"] / 60)) * 0.6 + (1 - min(1, home_team["conceded_per_game"] / 3)) * 0.4
        
        away_offensive = (away_team["xg"] / 60) * 0.6 + (away_team["goals_per_game"] / 3) * 0.4
        away_defensive = (1 - min(1, away_team["xga"] / 60)) * 0.6 + (1 - min(1, away_team["conceded_per_game"] / 3)) * 0.4
        
        # Score estatístico total
        home_stats_score = home_offensive * 0.6 + home_defensive * 0.4
        away_stats_score = away_offensive * 0.6 + away_defensive * 0.4
        
        # 3. POSIÇÃO NA TABELA (20%)
        if "win_pct" not in home_team or "win_pct" not in away_team:
            raise ValueError("Percentual de vitórias ausente")
            
        home_position_score = home_team["win_pct"] / 100
        away_position_score = away_team["win_pct"] / 100
        
        # 4. MÉTRICAS DE CRIAÇÃO (20%)
        home_possession = home_team["possession"] / 100
        away_possession = away_team["possession"] / 100
        
        home_creation = home_offensive * 0.7 + home_possession * 0.3
        away_creation = away_offensive * 0.7 + away_possession * 0.3
        
        # 5. APLICAR PONDERAÇÕES
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
        
        # 6. CÁLCULO DE PROBABILIDADES POR MERCADO
        
        # 6.1. Moneyline (1X2)
        # Usar inclinação calibrada do mercado 'result'
        slope = calibration["result"]["slope"]
        shift = calibration["result"]["shift"]
        
        # Distribuição inicial
        raw_home_win = home_total_score / (home_total_score + away_total_score) * 0.8
        raw_away_win = away_total_score / (home_total_score + away_total_score) * 0.8
        raw_draw = 1 - (raw_home_win + raw_away_win)
        
        # Ajuste para vantagem em casa
        home_advantage = 0.08  # +8% boost para time da casa
        adjusted_home_win = raw_home_win + home_advantage
        adjusted_away_win = raw_away_win - (home_advantage * 0.5)
        adjusted_draw = 1 - (adjusted_home_win + adjusted_away_win)
        
        # Normalizar para somar 100%
        total = adjusted_home_win + adjusted_draw + adjusted_away_win
        home_win_prob = (adjusted_home_win / total) * 100
        draw_prob = (adjusted_draw / total) * 100
        away_win_prob = (adjusted_away_win / total) * 100
        
        # 6.2. Over/Under 2.5
        # Usar inclinação calibrada do mercado 'goals'
        goals_slope = calibration["goals"]["slope"]
        goals_shift = calibration["goals"]["shift"]
        
        # Calcular gols esperados
        home_expected_goals = home_offensive * 1.8 * (1 - away_defensive * 0.7)
        away_expected_goals = away_offensive * 1.5 * (1 - home_defensive * 0.7)
        
        total_expected_goals = home_expected_goals + away_expected_goals
        
        # Usar distribuição de Poisson para calcular o over 2.5
        lambda_total = total_expected_goals
        
        # Calcular P(gols < 3) = P(0) + P(1) + P(2)
        p_0 = math.exp(-lambda_total)
        p_1 = p_0 * lambda_total / 1  # P(1) = P(0) * lambda / 1!
        p_2 = p_1 * lambda_total / 2  # P(2) = P(1) * lambda / 2!
        
        under_2_5_prob = (p_0 + p_1 + p_2) * 100
        over_2_5_prob = 100 - under_2_5_prob
        
        # 6.3. BTTS (Ambos Marcam)
        # Usar inclinação calibrada do mercado 'btts'
        btts_slope = calibration["btts"]["slope"]
        btts_shift = calibration["btts"]["shift"]
        
        # Calcular probabilidade de cada time marcar
        p_home_no_goal = math.exp(-home_expected_goals)  # P(home = 0)
        p_away_no_goal = math.exp(-away_expected_goals)  # P(away = 0)
        
        p_home_scores = 1 - p_home_no_goal
        p_away_scores = 1 - p_away_no_goal
        
        # BTTS = P(home > 0) * P(away > 0)
        btts_yes_prob = p_home_scores * p_away_scores * 100
        btts_no_prob = 100 - btts_yes_prob
        
        # 6.4. Escanteios (Over/Under 9.5)
        # Usar inclinação calibrada do mercado 'corners'
        corners_slope = calibration["corners"]["slope"]
        corners_shift = calibration["corners"]["shift"]
        
        # Verificar se temos estatísticas de escanteios
        if "corners_per_game" not in home_team or "corners_per_game" not in away_team:
            raise ValueError("Estatísticas de escanteios ausentes")
        
        # Calcular escanteios esperados
        home_corners = home_team["corners_per_game"]
        away_corners = away_team["corners_per_game"]
        
        # Ajustar com base no estilo de jogo e posse
        home_expected_corners = home_corners * (1 + 0.2 * home_offensive - 0.1 * away_defensive)
        away_expected_corners = away_corners * (1 + 0.2 * away_offensive - 0.1 * home_defensive)
        
        total_expected_corners = home_expected_corners + away_expected_corners
        
        # Usar aproximação normal para calcular probabilidade over/under
        # Média = total_expected_corners, desvio = sqrt(total_expected_corners)
        corners_std = math.sqrt(total_expected_corners)
        z_score = (9.5 - total_expected_corners) / corners_std
        
        # Aproximação da função de distribuição normal
        def normal_cdf(x):
            return 0.5 * (1 + math.erf(x / math.sqrt(2)))
        
        under_9_5_corners_prob = normal_cdf(z_score) * 100
        over_9_5_corners_prob = 100 - under_9_5_corners_prob
        
        # 6.5. Cartões (Over/Under 4.5)
        # Usar inclinação calibrada do mercado 'cards'
        cards_slope = calibration["cards"]["slope"]
        cards_shift = calibration["cards"]["shift"]
        
        # Verificar se temos estatísticas de cartões
        if "cards_per_game" not in home_team or "cards_per_game" not in away_team:
            raise ValueError("Estatísticas de cartões ausentes")
        
        # Calcular cartões esperados
        home_cards = home_team["cards_per_game"]
        away_cards = away_team["cards_per_game"]
        
        # Fator de intensidade baseado na proximidade das equipes
        team_diff = abs(home_total_score - away_total_score)
        intensity_factor = 1 + 0.3 * (1 - min(1, team_diff * 2))
        
        # Incorporar tendência de jogo intenso
        intensity_factor *= (1 + game_trends["intense_game_probability"] / 200)
        
        total_expected_cards = (home_cards + away_cards) * intensity_factor
        
        # Usar aproximação normal para calcular probabilidade
        cards_std = math.sqrt(total_expected_cards * 0.8)
        z_score_cards = (4.5 - total_expected_cards) / cards_std
        
        under_4_5_cards_prob = normal_cdf(z_score_cards) * 100
        over_4_5_cards_prob = 100 - under_4_5_cards_prob
        
        # 6.6. Chance Dupla (Double Chance) - Derivado diretamente de 1X2
        home_draw_prob = home_win_prob + draw_prob
        away_draw_prob = away_win_prob + draw_prob
        home_away_prob = home_win_prob + away_win_prob
        
        # Montar resultado final
        return {
            "moneyline": {
                "home_win": round(home_win_prob, 1),
                "draw": round(draw_prob, 1),
                "away_win": round(away_win_prob, 1)
            },
            "double_chance": {
                "home_or_draw": round(home_draw_prob, 1),
                "away_or_draw": round(away_draw_prob, 1),
                "home_or_away": round(home_away_prob, 1)
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
    
    def update_calibration(self, prediction_history, actual_results):
        """Atualiza parâmetros de calibração baseado em resultados históricos"""
        if len(prediction_history) < 50:
            raise ValueError("Dados insuficientes para recalibração (mínimo 50)")
        
        # Coletar dados para recalibração
        market_data = {}
        
        # Preparar dados por mercado
        for market in ['goals', 'btts', 'corners', 'cards', 'result']:
            market_data[market] = {
                'predictions': [],
                'outcomes': []
            }
        
        # Extrair previsões e resultados
        for pred, result in zip(prediction_history, actual_results):
            # Moneyline
            if 'moneyline' in pred and 'moneyline' in result:
                # Home win
                market_data['result']['predictions'].append(pred['moneyline']['home_win'] / 100)
                market_data['result']['outcomes'].append(1 if result['moneyline']['home_win'] else 0)
                
                # Draw
                market_data['result']['predictions'].append(pred['moneyline']['draw'] / 100)
                market_data['result']['outcomes'].append(1 if result['moneyline']['draw'] else 0)
                
                # Away win
                market_data['result']['predictions'].append(pred['moneyline']['away_win'] / 100)
                market_data['result']['outcomes'].append(1 if result['moneyline']['away_win'] else 0)
            
            # Over 2.5
            if 'over_under' in pred and 'over_under' in result:
                market_data['goals']['predictions'].append(pred['over_under']['over_2_5'] / 100)
                market_data['goals']['outcomes'].append(1 if result['over_under']['over_2_5'] else 0)
            
            # BTTS
            if 'btts' in pred and 'btts' in result:
                market_data['btts']['predictions'].append(pred['btts']['yes'] / 100)
                market_data['btts']['outcomes'].append(1 if result['btts']['yes'] else 0)
            
            # Corners
            if 'corners' in pred and 'corners' in result:
                market_data['corners']['predictions'].append(pred['corners']['over_9_5'] / 100)
                market_data['corners']['outcomes'].append(1 if result['corners']['over_9_5'] else 0)
            
            # Cards
            if 'cards' in pred and 'cards' in result:
                market_data['cards']['predictions'].append(pred['cards']['over_4_5'] / 100)
                market_data['cards']['outcomes'].append(1 if result['cards']['over_4_5'] else 0)
        
        # Realizar otimização para cada mercado
        new_calibration = {}
        
        for market, data in market_data.items():
            if len(data['predictions']) < 30:
                raise ValueError(f"Dados insuficientes para recalibrar mercado {market}")
                
            # Calcular brier score
            brier_score = sum((p - o) ** 2 for p, o in zip(data['predictions'], data['outcomes'])) / len(data['predictions'])
            
            # Calcular calibração média
            mean_pred = sum(data['predictions']) / len(data['predictions'])
            mean_outcome = sum(data['outcomes']) / len(data['outcomes'])
            
            # Estimar novos parâmetros de inclinação e deslocamento
            # Isto é uma simplificação - na prática, deveria usar otimização mais sofisticada
            adjustment = mean_outcome - mean_pred
            
            new_slope = self.calibration_data[market]['slope']
            new_shift = self.calibration_data[market]['shift'] + adjustment
            
            new_calibration[market] = {
                'slope': new_slope,
                'shift': new_shift,
                'brier_score': brier_score,
                'sample_size': len(data['predictions'])
            }
        
        # Salvar nova calibração
        if self.database:
            self.database.save_calibration_data(new_calibration)
            self.calibration_data = new_calibration
        else:
            raise ValueError("Sem banco de dados para salvar calibração")
        
