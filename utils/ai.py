# utils/ai.py - Funções de Inteligência Artificial
import os
import logging
import streamlit as st

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
                        "content": "Você é um Agente Analista de Probabilidades Esportivas especializado."
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

# Substitua a função format_prompt em utils/ai.py

def format_prompt(stats_df, home_team, away_team, odds_data, selected_markets):
    """Formata o prompt para o GPT-4 com os dados coletados"""
    try:
        # Alterar importação
        from utils.footystats_api import LEAGUE_SEASONS, CURRENT_SEASON
        
        # Extrair estatísticas detalhadas de ambos os times
        from utils.data import get_stat
        
        # Importe a função de extração
        try:
            from utils.data import extract_team_stats
        except ImportError:
            # Se a função estiver no mesmo arquivo (utils/ai.py)
            extract_team_stats = globals().get('extract_team_stats')
        
        # Extrair estatísticas completas
        home_team_full_stats = extract_team_stats(stats_df, home_team)
        away_team_full_stats = extract_team_stats(stats_df, away_team)
        
        if not home_team_full_stats or not away_team_full_stats:
            logger.error("Falha ao extrair estatísticas completas dos times")
            
            # Fallback para o método antigo se a extração falhar
            home_stats = stats_df[stats_df['Squad'] == home_team].iloc[0]
            away_stats = stats_df[stats_df['Squad'] == away_team].iloc[0]
            
            # Formatação básica antiga
            home_team_stats = f"""
  * Jogos Disputados: {get_stat(home_stats, 'MP')}
  * Gols Marcados: {get_stat(home_stats, 'Gls')}
  * Expected Goals (xG): {get_stat(home_stats, 'xG')}
  * Posse de Bola: {get_stat(home_stats, 'Poss')}%"""

            away_team_stats = f"""
  * Jogos Disputados: {get_stat(away_stats, 'MP')}
  * Gols Marcados: {get_stat(away_stats, 'Gls')}
  * Expected Goals (xG): {get_stat(away_stats, 'xG')}
  * Posse de Bola: {get_stat(away_stats, 'Poss')}%"""
        else:
            # Formatação avançada com todas as estatísticas
            home_team_stats = f"""
### Estatísticas Básicas
* Jogos Disputados: {home_team_full_stats['matches_played']}
* Pontos: {home_team_full_stats['points']} ({home_team_full_stats['points_per_game']} por jogo)

### Estatísticas Ofensivas
* Gols Marcados: {home_team_full_stats['goals_scored']} ({home_team_full_stats['goals_per_game']} por jogo)
* Expected Goals (xG): {home_team_full_stats['expected_goals']} ({home_team_full_stats['expected_goals_per_game']} por jogo)
* Eficiência Ofensiva: {home_team_full_stats['goal_efficiency']}% (relação Gols/xG)
* Chutes: {home_team_full_stats['shots']} (média de {round(home_team_full_stats['shots'] / home_team_full_stats['matches_played'], 1)} por jogo)
* Chutes no Alvo: {home_team_full_stats['shots_on_target']} ({home_team_full_stats['shots_on_target_percentage']}% de precisão)

### Estatísticas Defensivas
* Gols Sofridos: {home_team_full_stats['goals_against']} ({home_team_full_stats['goals_against_per_game']} por jogo)
* Expected Goals Against (xGA): {home_team_full_stats['expected_goals_against']} ({home_team_full_stats['expected_goals_against_per_game']} por jogo)
* Clean Sheets: {home_team_full_stats['clean_sheets']} ({home_team_full_stats['clean_sheets_percentage']}% dos jogos)

### Estatísticas de Jogo
* Posse de Bola: {home_team_full_stats['possession']}%
* Passes Completados: {home_team_full_stats['passes_completed']} de {home_team_full_stats['passes_attempted']} ({home_team_full_stats['pass_completion']}%)
* Escanteios: {home_team_full_stats['corners']}
* Cartões Amarelos: {home_team_full_stats['yellow_cards']}
* Cartões Vermelhos: {home_team_full_stats['red_cards']}

### Diferencial
* Saldo de Gols: {home_team_full_stats['goal_difference']}
* Saldo de Expected Goals: {home_team_full_stats['expected_goal_difference']}"""

            away_team_stats = f"""
### Estatísticas Básicas
* Jogos Disputados: {away_team_full_stats['matches_played']}
* Pontos: {away_team_full_stats['points']} ({away_team_full_stats['points_per_game']} por jogo)

### Estatísticas Ofensivas
* Gols Marcados: {away_team_full_stats['goals_scored']} ({away_team_full_stats['goals_per_game']} por jogo)
* Expected Goals (xG): {away_team_full_stats['expected_goals']} ({away_team_full_stats['expected_goals_per_game']} por jogo)
* Eficiência Ofensiva: {away_team_full_stats['goal_efficiency']}% (relação Gols/xG)
* Chutes: {away_team_full_stats['shots']} (média de {round(away_team_full_stats['shots'] / away_team_full_stats['matches_played'], 1)} por jogo)
* Chutes no Alvo: {away_team_full_stats['shots_on_target']} ({away_team_full_stats['shots_on_target_percentage']}% de precisão)

### Estatísticas Defensivas
* Gols Sofridos: {away_team_full_stats['goals_against']} ({away_team_full_stats['goals_against_per_game']} por jogo)
* Expected Goals Against (xGA): {away_team_full_stats['expected_goals_against']} ({away_team_full_stats['expected_goals_against_per_game']} por jogo)
* Clean Sheets: {away_team_full_stats['clean_sheets']} ({away_team_full_stats['clean_sheets_percentage']}% dos jogos)

### Estatísticas de Jogo
* Posse de Bola: {away_team_full_stats['possession']}%
* Passes Completados: {away_team_full_stats['passes_completed']} de {away_team_full_stats['passes_attempted']} ({away_team_full_stats['pass_completion']}%)
* Escanteios: {away_team_full_stats['corners']}
* Cartões Amarelos: {away_team_full_stats['yellow_cards']}
* Cartões Vermelhos: {away_team_full_stats['red_cards']}

### Diferencial
* Saldo de Gols: {away_team_full_stats['goal_difference']}
* Saldo de Expected Goals: {away_team_full_stats['expected_goal_difference']}"""

        # Calcular probabilidades reais com base no xG e outros fatores
        try:
            # Extrai valores-chave para o cálculo
            home_xg = home_team_full_stats.get('expected_goals', 0)
            away_xg = away_team_full_stats.get('expected_goals', 0)
            home_games = home_team_full_stats.get('matches_played', 1)
            away_games = away_team_full_stats.get('matches_played', 1)
            
            # Usar a função calculate_real_prob para calcular probabilidades
            real_probs = calculate_real_prob(home_xg, away_xg, home_games, away_games)
        except:
            # Se falhar, tentar método baseado em estatísticas básicas
            real_probs = None
            
            # Tente extrair estatísticas básicas para cálculo alternativo
            try:
                home_stats = stats_df[stats_df['Squad'] == home_team].iloc[0]
                away_stats = stats_df[stats_df['Squad'] == away_team].iloc[0]
                from utils.data import get_stat
                
                home_xg = float(get_stat(home_stats, 'xG', 0))
                away_xg = float(get_stat(away_stats, 'xG', 0))
                home_games = float(get_stat(home_stats, 'MP', 1))
                away_games = float(get_stat(away_stats, 'MP', 1))
                
                real_probs = calculate_real_prob(home_xg, away_xg, home_games, away_games)
            except:
                pass

        # Montar o prompt completo
        full_prompt = f"""Role: Agente Analista de Probabilidades Esportivas

KNOWLEDGE BASE INTERNO:
# Estatísticas de {home_team} (Mandante): 
{home_team_stats}

# Estatísticas de {away_team} (Visitante):
{away_team_stats}

# PROBABILIDADES CALCULADAS:
"""
        
        if real_probs:
            full_prompt += f"""- Vitória {home_team}: {real_probs['home']:.1f}% (Real)
- Empate: {real_probs['draw']:.1f}% (Real)
- Vitória {away_team}: {real_probs['away']:.1f}% (Real)
"""
        else:
            full_prompt += "Dados insuficientes para cálculo de probabilidades reais\n"

        # Explicações das estatísticas para o modelo
        full_prompt += """
# GLOSSÁRIO DE ESTATÍSTICAS:
- Expected Goals (xG): Medida da qualidade das chances de gol criadas
- Expected Goals Against (xGA): Medida da qualidade das chances de gol concedidas
- Eficiência Ofensiva: Relação entre gols marcados e xG (>100% = eficiência acima do esperado)
- Eficiência Defensiva: Relação entre gols sofridos e xGA (<100% = defesa melhor que o esperado)
- Clean Sheets: Jogos sem sofrer gols
- xG Difference: Diferença entre xG e xGA (valor positivo indica time ofensivamente dominante)
"""

        # Adicionar informações sobre quais mercados foram selecionados
        selected_market_names = []
        full_prompt += "\n# MERCADOS SELECIONADOS PARA ANÁLISE:\n"
        for market, selected in selected_markets.items():
            if selected:
                market_names = {
                    "money_line": "Money Line (1X2)",
                    "over_under": "Over/Under Gols",
                    "chance_dupla": "Chance Dupla",
                    "ambos_marcam": "Ambos Marcam",
                    "escanteios": "Total de Escanteios",
                    "cartoes": "Total de Cartões"
                }
                market_name = market_names.get(market, market)
                selected_market_names.append(market_name)
                full_prompt += f"- {market_name}\n"

        # Instrução muito clara sobre o formato de saída
        full_prompt += f"""
INSTRUÇÕES ESPECIAIS: VOCÊ DEVE CALCULAR PROBABILIDADES REAIS PARA TODOS OS MERCADOS LISTADOS ACIMA, não apenas para o Money Line. Use os dados disponíveis e sua expertise para estimar probabilidades reais para CADA mercado selecionado.

[SAÍDA OBRIGATÓRIA]

# Análise da Partida
## {home_team} x {away_team}

# Análise de Mercados Disponíveis:
{odds_data}

# Probabilidades Calculadas (REAL vs IMPLÍCITA):
[IMPORTANTE - Para cada um dos mercados abaixo, você DEVE mostrar a probabilidade REAL calculada, bem como a probabilidade IMPLÍCITA nas odds:]
{chr(10).join([f"- {name}" for name in selected_market_names])}

# Oportunidades Identificadas (Edges >3%):
[Listagem detalhada de cada mercado selecionado, indicando explicitamente se há edge ou não para cada opção.]

# Nível de Confiança Geral: [Baixo/Médio/Alto]
[Breve explicação da sua confiança na análise, baseada na qualidade e completude dos dados disponíveis]
"""
        return full_prompt

    except Exception as e:
        logger.error(f"Erro ao formatar prompt: {str(e)}")
        return None
