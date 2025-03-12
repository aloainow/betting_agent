# utils/ai.py - Funções de Inteligência Artificial
import os
import logging
import streamlit as st
import json

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

def analyze_with_gpt(prompt):
    try:
        client = get_openai_client()
        if not client:
            st.error("Cliente OpenAI não inicializado")
            return None
            
        with st.spinner("Analisando dados e calculando probabilidades..."):
            logger.info("Enviando prompt para análise com GPT")
            response = client.chat.completions.create(
                model="gpt-4",
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
            # Valores de fallback baseados em médias da liga
            home_xg = 1.5 * home_games
            away_xg = 1.0 * away_games
            
        # Calcular xG por jogo
        home_xg_per_game = home_xg / home_games if home_games > 0 else 1.5
        away_xg_per_game = away_xg / away_games if away_games > 0 else 1.0
        
        # Ajuste baseado em home advantage
        home_advantage = 1.1
        adjusted_home_xg = home_xg_per_game * home_advantage
        
        # Calcular probabilidades
        total_xg = adjusted_home_xg + away_xg_per_game
        if total_xg == 0:
            # Valores padrão
            return {'home': 45.0, 'draw': 25.0, 'away': 30.0}
            
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
        # Retornar valores de fallback razoáveis
        return {'home': 45.0, 'draw': 25.0, 'away': 30.0}

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
* {home_team}: {home_stats.get('wins', 0)}V {home_stats.get('draws', 0)}E {home_stats.get('losses', 0)}D | {home_stats.get('goals_scored', 0)} gols marcados, {home_stats.get('goals_conceded', 0)} sofridos
* {away_team}: {away_stats.get('wins', 0)}V {away_stats.get('draws', 0)}E {away_stats.get('losses', 0)}D | {away_stats.get('goals_scored', 0)} gols marcados, {away_stats.get('goals_conceded', 0)} sofridos

## Métricas Expected Goals (xG)
* {home_team}: {home_stats.get('xG', 0)} xG a favor, {home_stats.get('xGA', 0)} xG contra | Saldo: {float(home_stats.get('xG', 0)) - float(home_stats.get('xGA', 0)):.2f}
* {away_team}: {away_stats.get('xG', 0)} xG a favor, {away_stats.get('xGA', 0)} xG contra | Saldo: {float(away_stats.get('xG', 0)) - float(away_stats.get('xGA', 0)):.2f}

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
* {home_team} como mandante: {home_stats.get('home_wins', 0)}V {home_stats.get('home_draws', 0)}E {home_stats.get('home_losses', 0)}D
* {away_team} como visitante: {away_stats.get('away_wins', 0)}V {away_stats.get('away_draws', 0)}E {away_stats.get('away_losses', 0)}D

## Tendências de Resultado
* {home_team} % vitórias: {home_stats.get('win_percentage', 0)}%
* {away_team} % vitórias: {away_stats.get('win_percentage', 0)}%
* % empates nos jogos de {home_team}: {home_stats.get('draw_percentage', 0)}%
* % empates nos jogos de {away_team}: {away_stats.get('draw_percentage', 0)}%

## Métricas Avançadas Relevantes
* Posse média: {home_stats.get('possession', 0)}% vs {away_stats.get('possession', 0)}%
* Passes p/ Ação Defensiva: {home_advanced.get('ppda', 'N/A')} vs {away_advanced.get('ppda', 'N/A')} (menor = pressão mais intensa)
* Deep Completions: {home_advanced.get('deep_completions', 'N/A')} vs {away_advanced.get('deep_completions', 'N/A')}
"""

    # 3. ESTATÍSTICAS PARA MERCADOS DE GOLS (Over/Under, Ambos Marcam)
    goals_stats = ""
    if any(m in selected_markets for m in ["over_under", "ambos_marcam"]):
        goals_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE GOLS

## Médias de Gols
* {home_team} média de gols marcados: {float(home_stats.get('goals_scored', 0)) / max(float(home_stats.get('matches_played', 1)), 1):.2f} por jogo
* {away_team} média de gols marcados: {float(away_stats.get('goals_scored', 0)) / max(float(away_stats.get('matches_played', 1)), 1):.2f} por jogo
* {home_team} média de gols sofridos: {float(home_stats.get('goals_conceded', 0)) / max(float(home_stats.get('matches_played', 1)), 1):.2f} por jogo
* {away_team} média de gols sofridos: {float(away_stats.get('goals_conceded', 0)) / max(float(away_stats.get('matches_played', 1)), 1):.2f} por jogo

## Clean Sheets e BTTS
* {home_team} clean sheets: {home_stats.get('clean_sheets', 0)} ({home_stats.get('clean_sheet_percentage', 0)}%)
* {away_team} clean sheets: {away_stats.get('clean_sheets', 0)} ({away_stats.get('clean_sheet_percentage', 0)}%)
* {home_team} jogos com Ambos Marcam: {home_stats.get('btts_percentage', 0)}%
* {away_team} jogos com Ambos Marcam: {away_stats.get('btts_percentage', 0)}%

## Distribuição de Gols por Jogo
* Jogos do {home_team} com Over 2.5: {home_stats.get('over_2_5_percentage', 0)}%
* Jogos do {away_team} com Over 2.5: {away_stats.get('over_2_5_percentage', 0)}%
* Jogos H2H com Over 2.5: {h2h_data.get('over_2_5_percentage', 0)}%
"""

    # 4. ESTATÍSTICAS PARA MERCADOS DE ESCANTEIOS
    corners_stats = ""
    if "escanteios" in selected_markets:
        corners_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE ESCANTEIOS

## Médias de Escanteios
* {home_team} média de escanteios a favor: {float(home_stats.get('corners_for', 0)) / max(float(home_stats.get('matches_played', 1)), 1):.2f} por jogo
* {away_team} média de escanteios a favor: {float(away_stats.get('corners_for', 0)) / max(float(away_stats.get('matches_played', 1)), 1):.2f} por jogo
* {home_team} média de escanteios contra: {float(home_stats.get('corners_against', 0)) / max(float(home_stats.get('matches_played', 1)), 1):.2f} por jogo
* {away_team} média de escanteios contra: {float(away_stats.get('corners_against', 0)) / max(float(away_stats.get('matches_played', 1)), 1):.2f} por jogo

## Tendências de Escanteios
* Jogos do {home_team} com Over 9.5 escanteios: {home_stats.get('over_9_5_corners_percentage', 0)}%
* Jogos do {away_team} com Over 9.5 escanteios: {away_stats.get('over_9_5_corners_percentage', 0)}%
* Total médio de escanteios em confrontos H2H: {h2h_data.get('average_corners', 'N/A')}
"""

    # 5. ESTATÍSTICAS PARA MERCADOS DE CARTÕES
    cards_stats = ""
    if "cartoes" in selected_markets:
        cards_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE CARTÕES

## Médias de Cartões
* {home_team} média de cartões recebidos: {float(home_stats.get('cards_total', 0)) / max(float(home_stats.get('matches_played', 1)), 1):.2f} por jogo
* {away_team} média de cartões recebidos: {float(away_stats.get('cards_total', 0)) / max(float(away_stats.get('matches_played', 1)), 1):.2f} por jogo
* {home_team} média de cartões provocados: {float(home_stats.get('cards_against', 0)) / max(float(home_stats.get('matches_played', 1)), 1):.2f} por jogo
* {away_team} média de cartões provocados: {float(away_stats.get('cards_against', 0)) / max(float(away_stats.get('matches_played', 1)), 1):.2f} por jogo

## Tendências de Cartões
* Jogos do {home_team} com Over 3.5 cartões: {home_stats.get('over_3_5_cards_percentage', 0)}%
* Jogos do {away_team} com Over 3.5 cartões: {away_stats.get('over_3_5_cards_percentage', 0)}%
* Média de cartões em jogos H2H: {h2h_data.get('average_cards', 'N/A')}
* Árbitro da partida: {basic_stats.get('referee', 'Não informado')} (Média de {basic_stats.get('referee_avg_cards', 'N/A')} cartões por jogo)
"""

    # 6. MERCADOS DISPONÍVEIS E ODDS
    markets_info = f"""
# MERCADOS DISPONÍVEIS E ODDS
{odds_data}
"""

    # 7. INSTRUÇÕES PARA O MODELO - MODIFICADA PARA LIDAR COM DADOS ESCASSOS
    instructions = f"""
# INSTRUÇÕES PARA ANÁLISE

## QUALIDADE DOS DADOS: {data_quality.upper()}

Analise os dados estatísticos disponíveis, mesmo que sejam limitados. Seu objetivo é extrair insights e valor mesmo de conjuntos de dados incompletos.

1. Trabalhe com quaisquer dados estatísticos disponíveis, por mínimos que sejam
2. Use as odds implícitas como ponto de partida quando os dados estatísticos forem escassos
3. Se os dados forem insuficientes para calcular probabilidades reais com precisão para algum mercado, explique isso claramente, mas ainda forneça análise baseada nas odds implícitas
4. Mesmo com dados limitados, tente identificar tendências ou oportunidades nos mercados disponíveis
5. Seja transparente sobre o nível de confiança, ajustando-o de acordo com a quantidade e qualidade dos dados disponíveis

IMPORTANTE: Você DEVE fornecer uma análise mesmo que os dados estatísticos sejam limitados ou quase todos zeros. Use as odds implícitas e qualquer outro dado disponível para oferecer orientação útil ao usuário.

Formato da resposta:
# Análise da Partida
## {home_team} x {away_team}

# Análise de Mercados Disponíveis:
[Resumo das odds de cada mercado]

# Probabilidades Calculadas (REAL vs IMPLÍCITA):
[Para cada mercado, mostrando probabilidades - mesmo se apenas as implícitas estiverem disponíveis devido à falta de dados]

# Oportunidades Identificadas:
[Mercados com potencial valor ou explicação da limitação na identificação de edges]

# Nível de Confiança Geral: [Baixo/Médio/Alto]
[Justificativa para o nível de confiança, considerando a qualidade dos dados disponíveis]
"""

    # Compilar o prompt final
    full_prompt = fundamental_stats + result_stats + goals_stats + corners_stats + cards_stats + markets_info + instructions
    
    return full_prompt
