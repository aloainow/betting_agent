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

# Add to utils/ai.py

def format_highly_optimized_prompt(optimized_data, home_team, away_team, odds_data, selected_markets):
    """
    Format prompt for GPT using the highly optimized data structure.
    Ensures ALL statistics are included for comprehensive analysis.
    
    Args:
        optimized_data (dict): Data in the highly optimized format
        home_team (str): Home team name
        away_team (str): Away team name
        odds_data (str): Formatted odds data
        selected_markets (dict): Dictionary of selected markets
        
    Returns:
        str: Formatted prompt
    """
    logger.info(f"Formatting highly optimized prompt for {home_team} vs {away_team}")
    
    try:
        # Verify we have valid data
        if not optimized_data or not isinstance(optimized_data, dict):
            logger.error("Missing or invalid optimized data structure")
            # Proceed with empty structure but log the error
            optimized_data = {
                "match_info": {"home_team": home_team, "away_team": away_team, "league": "", "league_id": None},
                "home_team": {}, "away_team": {}, "h2h": {}
            }
        
        # 1. FUNDAMENTAL STATISTICS (relevant for all markets)
        home = optimized_data.get("home_team", {})
        away = optimized_data.get("away_team", {})
        h2h = optimized_data.get("h2h", {})
        match_info = optimized_data.get("match_info", {"league": ""})
        
        # Extract league name if available
        league_name = match_info.get("league", "")
        
        fundamental_stats = f"""
# ESTATÍSTICAS FUNDAMENTAIS: {home_team} vs {away_team}
## {league_name}

### Desempenho Geral na Temporada
* {home_team}: {home.get('wins', 0)}V {home.get('draws', 0)}E {home.get('losses', 0)}D | {home.get('goals_scored', 0)} gols marcados, {home.get('goals_conceded', 0)} sofridos
* {away_team}: {away.get('wins', 0)}V {away.get('draws', 0)}E {away.get('losses', 0)}D | {away.get('goals_scored', 0)} gols marcados, {away.get('goals_conceded', 0)} sofridos

### Forma Recente (últimos 5 jogos)
* {home_team}: {home.get('form', '?????')}
* {away_team}: {away.get('form', '?????')}

### Métricas Expected Goals (xG)
* {home_team}: {home.get('xg', 0)} xG a favor, {home.get('xga', 0)} xG contra
* {away_team}: {away.get('xg', 0)} xG a favor, {away.get('xga', 0)} xG contra

### Confronto Direto (H2H)
* Jogos totais: {h2h.get('total_matches', 0)}
* Vitórias {home_team}: {h2h.get('home_wins', 0)}
* Vitórias {away_team}: {h2h.get('away_wins', 0)}
* Empates: {h2h.get('draws', 0)}
"""

        # 2. STATS FOR RESULT MARKETS (1X2, Double Chance)
        result_stats = ""
        if any(selected_markets.get(m) for m in ["money_line", "chance_dupla"]):
            result_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE RESULTADO

### Desempenho em Casa/Fora
* {home_team} como mandante: {home.get('home_wins', 0)}V {home.get('home_draws', 0)}E {home.get('home_losses', 0)}D | {home.get('home_goals_scored', 0)} gols marcados, {home.get('home_goals_conceded', 0)} sofridos
* {away_team} como visitante: {away.get('away_wins', 0)}V {away.get('away_draws', 0)}E {away.get('away_losses', 0)}D | {away.get('away_goals_scored', 0)} gols marcados, {away.get('away_goals_conceded', 0)} sofridos

### Métricas Avançadas
* Posse de Bola: {home_team} {home.get('possession', 0)}% vs {away_team} {away.get('possession', 0)}%
* PPDA (Passes por Ação Defensiva): {home_team} {home.get('ppda', 'N/A')} vs {away_team} {away.get('ppda', 'N/A')} (menor = pressão mais intensa)
"""

        # 3. STATS FOR GOALS MARKETS (Over/Under, Both Teams To Score)
        goals_stats = ""
        if any(selected_markets.get(m) for m in ["over_under", "ambos_marcam"]):
            goals_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE GOLS

### Médias de Gols
* {home_team} média de gols marcados: {float(home.get('goals_scored', 0)) / max(float(home.get('played', 1)), 1):.2f} por jogo
* {away_team} média de gols marcados: {float(away.get('goals_scored', 0)) / max(float(away.get('played', 1)), 1):.2f} por jogo
* {home_team} média de gols sofridos: {float(home.get('goals_conceded', 0)) / max(float(home.get('played', 1)), 1):.2f} por jogo
* {away_team} média de gols sofridos: {float(away.get('goals_conceded', 0)) / max(float(away.get('played', 1)), 1):.2f} por jogo

### Clean Sheets e Ambos Marcam
* {home_team} clean sheets %: {home.get('clean_sheets_pct', 0)}%
* {away_team} clean sheets %: {away.get('clean_sheets_pct', 0)}%
* {home_team} jogos com Ambos Marcam: {home.get('btts_pct', 0)}%
* {away_team} jogos com Ambos Marcam: {away.get('btts_pct', 0)}%

### Distribuição de Gols por Jogo
* Jogos do {home_team} com Over 2.5: {home.get('over_2_5_pct', 0)}%
* Jogos do {away_team} com Over 2.5: {away.get('over_2_5_pct', 0)}%
* Jogos H2H com Over 2.5: {h2h.get('over_2_5_pct', 0)}%
"""

        # 4. STATS FOR CORNERS MARKETS
        corners_stats = ""
        if selected_markets.get("escanteios"):
            corners_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE ESCANTEIOS

### Médias de Escanteios
* {home_team} média de escanteios por jogo: {home.get('corners_per_game', 0)}
* {away_team} média de escanteios por jogo: {away.get('corners_per_game', 0)}
* {home_team} escanteios a favor: {home.get('corners_for', 0)}
* {home_team} escanteios contra: {home.get('corners_against', 0)}
* {away_team} escanteios a favor: {away.get('corners_for', 0)}
* {away_team} escanteios contra: {away.get('corners_against', 0)}
* Total médio de escanteios em confrontos H2H: {h2h.get('avg_corners', 'N/A')}

### Tendências de Escanteios
* Jogos do {home_team} com Over 9.5 escanteios: {home.get('over_9_5_corners_pct', 0)}%
* Jogos do {away_team} com Over 9.5 escanteios: {away.get('over_9_5_corners_pct', 0)}%
"""

        # 5. STATS FOR CARDS MARKETS
        cards_stats = ""
        if selected_markets.get("cartoes"):
            cards_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE CARTÕES

### Médias de Cartões
* {home_team} média de cartões por jogo: {home.get('cards_per_game', 0)}
* {away_team} média de cartões por jogo: {away.get('cards_per_game', 0)}
* {home_team} cartões amarelos: {home.get('yellow_cards', 0)}
* {home_team} cartões vermelhos: {home.get('red_cards', 0)}
* {away_team} cartões amarelos: {away.get('yellow_cards', 0)}
* {away_team} cartões vermelhos: {away.get('red_cards', 0)}
* Média de cartões em jogos H2H: {h2h.get('avg_cards', 'N/A')}

### Tendências de Cartões
* Jogos do {home_team} com Over 3.5 cartões: {home.get('over_3_5_cards_pct', 0)}%
* Jogos do {away_team} com Over 3.5 cartões: {away.get('over_3_5_cards_pct', 0)}%
"""

        # 6. AVAILABLE MARKETS AND ODDS
        markets_info = f"""
# MERCADOS DISPONÍVEIS E ODDS
{odds_data}
"""

        # 7. INSTRUCTIONS FOR THE MODEL
        instructions = f"""
# INSTRUÇÕES PARA ANÁLISE

Analise os dados estatísticos fornecidos para identificar valor nas odds.
Você é um especialista em probabilidades esportivas que deve calcular probabilidades REAIS com base nos dados.

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
        # Compile the final prompt
        sections = [
            fundamental_stats,
            result_stats,
            goals_stats,
            corners_stats,
            cards_stats,
            markets_info,
            instructions
        ]
        
        full_prompt = "\n".join([s for s in sections if s])
        logger.info(f"Prompt prepared successfully for {home_team} vs {away_team}")
        
        return full_prompt
        
    except Exception as e:
        logger.error(f"Error formatting highly optimized prompt: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return a simplified prompt as fallback
        return f"""
# ESTATÍSTICAS BÁSICAS
{home_team} vs {away_team}

{odds_data}

# INSTRUÇÕES
Você DEVE analisar as odds e identificar oportunidades de valor, mesmo com dados limitados.
Responda com EXATAMENTE este formato, com todas as seções:

# Análise da Partida
## {home_team} x {away_team}

# Análise de Mercados Disponíveis:
[Resumo detalhado das odds]

# Probabilidades Calculadas (REAL vs IMPLÍCITA):
[Comparação lado a lado de probabilidades reais e implícitas]

# Oportunidades Identificadas:
[Lista de oportunidades com edge percentual]

# Nível de Confiança Geral: [Baixo/Médio/Alto]
[Justificativa]
"""
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

# Add this new function to utils/ai.py

def format_analysis_response(analysis_text, home_team, away_team):
    """
    Garante que a resposta da análise seja formatada corretamente com todas as seções necessárias,
    sem adicionar dados artificiais.
    
    Args:
        analysis_text (str): Resposta bruta da análise da IA
        home_team (str): Nome do time da casa
        away_team (str): Nome do time visitante
        
    Returns:
        str: Análise formatada corretamente
    """
    # Verificar se a análise já tem os cabeçalhos de seção adequados
    if "# Análise da Partida" in analysis_text and "# Probabilidades Calculadas" in analysis_text:
        return analysis_text
        
    # Se não estiver formatada corretamente, reestruturar
    formatted_sections = []
    
    # Adicionar seção de título
    formatted_sections.append(f"# Análise da Partida\n## {home_team} x {away_team}\n")
    
    # Procurar seção de mercados ou criá-la
    if "# Análise de Mercados Disponíveis:" in analysis_text:
        # Encontrar a seção e seu conteúdo
        market_section = analysis_text.split("# Análise de Mercados Disponíveis:")[1]
        if "#" in market_section:
            market_section = market_section.split("#")[0]
        formatted_sections.append(f"# Análise de Mercados Disponíveis:\n{market_section.strip()}\n")
    else:
        formatted_sections.append("# Análise de Mercados Disponíveis:\nNão foi possível estruturar uma análise detalhada dos mercados a partir do texto.\n")
    
    # Procurar seção de probabilidades ou criá-la
    if "# Probabilidades Calculadas" in analysis_text:
        prob_section = analysis_text.split("# Probabilidades Calculadas")[1]
        if "#" in prob_section:
            prob_section = prob_section.split("#")[0]
        formatted_sections.append(f"# Probabilidades Calculadas (REAL vs IMPLÍCITA):\n{prob_section.strip()}\n")
    else:
        formatted_sections.append("# Probabilidades Calculadas (REAL vs IMPLÍCITA):\nNão há dados estatísticos suficientes para calcular probabilidades reais.\n")
    
    # Procurar seção de oportunidades ou criá-la
    if "# Oportunidades Identificadas" in analysis_text:
        opp_section = analysis_text.split("# Oportunidades Identificadas")[1]
        if "#" in opp_section:
            opp_section = opp_section.split("#")[0]
        formatted_sections.append(f"# Oportunidades Identificadas:\n{opp_section.strip()}\n")
    else:
        formatted_sections.append("# Oportunidades Identificadas:\nNão há dados suficientes para identificar oportunidades claras.\n")
    
    # Procurar seção de nível de confiança ou criá-la
    if "# Nível de Confiança" in analysis_text:
        conf_section = analysis_text.split("# Nível de Confiança")[1]
        if "#" in conf_section:
            conf_section = conf_section.split("#")[0]
        formatted_sections.append(f"# Nível de Confiança Geral: {conf_section.strip()}\n")
    else:
        formatted_sections.append("# Nível de Confiança Geral: Baixo\nDevido à limitação de dados estatísticos disponíveis, o nível de confiança é baixo.\n")
    
    # Combinar todas as seções
    return "\n".join(formatted_sections)
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
# Add this to utils/ai.py

def format_optimized_prompt(optimized_data, home_team, away_team, odds_data, selected_markets):
    """
    Format prompt for GPT using the optimized data structure
    
    Args:
        optimized_data (dict): Data in the optimized format
        home_team (str): Home team name
        away_team (str): Away team name
        odds_data (str): Formatted odds data
        selected_markets (dict): Dictionary of selected markets
        
    Returns:
        str: Formatted prompt
    """
    logger.info(f"Formatting optimized prompt for {home_team} vs {away_team}")
    
    try:
        # 1. FUNDAMENTAL STATISTICS (relevant for all markets)
        fundamental_stats = f"""
# ESTATÍSTICAS FUNDAMENTAIS ({home_team} vs {away_team})

## Desempenho Geral na Temporada
* {home_team}: {optimized_data['home_team'].get('wins', 0)}V {optimized_data['home_team'].get('draws', 0)}E {optimized_data['home_team'].get('losses', 0)}D | {optimized_data['home_team'].get('goals_scored', 0)} gols marcados, {optimized_data['home_team'].get('goals_conceded', 0)} sofridos
* {away_team}: {optimized_data['away_team'].get('wins', 0)}V {optimized_data['away_team'].get('draws', 0)}E {optimized_data['away_team'].get('losses', 0)}D | {optimized_data['away_team'].get('goals_scored', 0)} gols marcados, {optimized_data['away_team'].get('goals_conceded', 0)} sofridos

## Métricas Expected Goals (xG)
* {home_team}: {optimized_data['home_team'].get('xg', 0)} xG a favor, {optimized_data['home_team'].get('xga', 0)} xG contra | Saldo: {float(optimized_data['home_team'].get('xg', 0)) - float(optimized_data['home_team'].get('xga', 0)):.2f}
* {away_team}: {optimized_data['away_team'].get('xg', 0)} xG a favor, {optimized_data['away_team'].get('xga', 0)} xG contra | Saldo: {float(optimized_data['away_team'].get('xg', 0)) - float(optimized_data['away_team'].get('xga', 0)):.2f}

## Forma Recente (últimos 5 jogos)
* {home_team}: {optimized_data['home_team'].get('form', '?????')}
* {away_team}: {optimized_data['away_team'].get('form', '?????')}

## Head-to-Head
* Jogos totais: {optimized_data['h2h'].get('total_matches', 0)}
* Vitórias {home_team}: {optimized_data['h2h'].get('home_wins', 0)}
* Vitórias {away_team}: {optimized_data['h2h'].get('away_wins', 0)}
* Empates: {optimized_data['h2h'].get('draws', 0)}
"""

        # 2. STATS FOR RESULT MARKETS (1X2, Double Chance)
        result_stats = ""
        if any(selected_markets.get(m) for m in ["money_line", "chance_dupla"]):
            result_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE RESULTADO

## Desempenho como Mandante/Visitante
* {home_team} como mandante: {optimized_data['home_team'].get('home_wins', 0)}V {optimized_data['home_team'].get('home_draws', 0)}E {optimized_data['home_team'].get('home_losses', 0)}D
* {away_team} como visitante: {optimized_data['away_team'].get('away_wins', 0)}V {optimized_data['away_team'].get('away_draws', 0)}E {optimized_data['away_team'].get('away_losses', 0)}D

## Posse de Bola
* {home_team}: {optimized_data['home_team'].get('possession', 0)}%
* {away_team}: {optimized_data['away_team'].get('possession', 0)}%

## Métricas Avançadas
* PPDA (Passes por Ação Defensiva): {home_team} {optimized_data['home_team'].get('ppda', 'N/A')} vs {away_team} {optimized_data['away_team'].get('ppda', 'N/A')} (menor = pressão mais intensa)
"""

        # 3. STATS FOR GOALS MARKETS (Over/Under, Both Teams To Score)
        goals_stats = ""
        if any(selected_markets.get(m) for m in ["over_under", "ambos_marcam"]):
            # Calculate goals per game
            home_gpg = optimized_data['home_team'].get('goals_scored', 0) / max(optimized_data['home_team'].get('played', 1), 1)
            away_gpg = optimized_data['away_team'].get('goals_scored', 0) / max(optimized_data['away_team'].get('played', 1), 1)
            home_gcpg = optimized_data['home_team'].get('goals_conceded', 0) / max(optimized_data['home_team'].get('played', 1), 1)
            away_gcpg = optimized_data['away_team'].get('goals_conceded', 0) / max(optimized_data['away_team'].get('played', 1), 1)
            
            goals_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE GOLS

## Médias de Gols
* {home_team} média de gols marcados: {home_gpg:.2f} por jogo
* {away_team} média de gols marcados: {away_gpg:.2f} por jogo
* {home_team} média de gols sofridos: {home_gcpg:.2f} por jogo
* {away_team} média de gols sofridos: {away_gcpg:.2f} por jogo

## Clean Sheets e BTTS
* {home_team} clean sheets %: {optimized_data['home_team'].get('clean_sheets_pct', 0)}%
* {away_team} clean sheets %: {optimized_data['away_team'].get('clean_sheets_pct', 0)}%
* {home_team} jogos com Ambos Marcam: {optimized_data['home_team'].get('btts_pct', 0)}%
* {away_team} jogos com Ambos Marcam: {optimized_data['away_team'].get('btts_pct', 0)}%

## Distribuição de Gols por Jogo
* Jogos do {home_team} com Over 2.5: {optimized_data['home_team'].get('over_2_5_pct', 0)}%
* Jogos do {away_team} com Over 2.5: {optimized_data['away_team'].get('over_2_5_pct', 0)}%
* Jogos H2H com Over 2.5: {optimized_data['h2h'].get('over_2_5_pct', 0)}%
"""

        # 4. STATS FOR CORNERS MARKETS
        corners_stats = ""
        if selected_markets.get("escanteios"):
            corners_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE ESCANTEIOS

## Médias de Escanteios
* {home_team} média de escanteios a favor: {optimized_data['home_team'].get('corners_per_game', 0):.2f} por jogo
* {away_team} média de escanteios a favor: {optimized_data['away_team'].get('corners_per_game', 0):.2f} por jogo
* {home_team} escanteios a favor: {optimized_data['home_team'].get('corners_for', 0)}
* {home_team} escanteios contra: {optimized_data['home_team'].get('corners_against', 0)}
* {away_team} escanteios a favor: {optimized_data['away_team'].get('corners_for', 0)}
* {away_team} escanteios contra: {optimized_data['away_team'].get('corners_against', 0)}

## Tendências de Escanteios
* Jogos do {home_team} com Over 9.5 escanteios: {optimized_data['home_team'].get('over_9_5_corners_pct', 0)}%
* Jogos do {away_team} com Over 9.5 escanteios: {optimized_data['away_team'].get('over_9_5_corners_pct', 0)}%
* Total médio de escanteios em confrontos H2H: {optimized_data['h2h'].get('avg_corners', 'N/A')}
"""

        # 5. STATS FOR CARDS MARKETS
        cards_stats = ""
        if selected_markets.get("cartoes"):
            cards_stats = f"""
# ESTATÍSTICAS PARA MERCADOS DE CARTÕES

## Médias de Cartões
* {home_team} média de cartões por jogo: {optimized_data['home_team'].get('cards_per_game', 0):.2f}
* {away_team} média de cartões por jogo: {optimized_data['away_team'].get('cards_per_game', 0):.2f}
* {home_team} cartões amarelos: {optimized_data['home_team'].get('yellow_cards', 0)}
* {home_team} cartões vermelhos: {optimized_data['home_team'].get('red_cards', 0)}
* {away_team} cartões amarelos: {optimized_data['away_team'].get('yellow_cards', 0)}
* {away_team} cartões vermelhos: {optimized_data['away_team'].get('red_cards', 0)}

## Tendências de Cartões
* Jogos do {home_team} com Over 3.5 cartões: {optimized_data['home_team'].get('over_3_5_cards_pct', 0)}%
* Jogos do {away_team} com Over 3.5 cartões: {optimized_data['away_team'].get('over_3_5_cards_pct', 0)}%
* Média de cartões em jogos H2H: {optimized_data['h2h'].get('avg_cards', 'N/A')}
"""

        # 6. AVAILABLE MARKETS AND ODDS
        markets_info = f"""
# MERCADOS DISPONÍVEIS E ODDS
{odds_data}
"""

        # 7. INSTRUCTIONS FOR THE MODEL
        instructions = f"""
# INSTRUÇÕES PARA ANÁLISE

Analise os dados estatísticos fornecidos para identificar valor nas odds.

1. Para cada mercado selecionado, calcule as probabilidades reais com base nas estatísticas
2. Compare as probabilidades reais com as probabilidades implícitas nas odds
3. Identifique oportunidades de valor (edges) onde há discrepâncias favoráveis
4. Para cada mercado, dê sua recomendação clara e objetiva

Formato da resposta:
# Análise da Partida
## {home_team} x {away_team}

# Análise de Mercados Disponíveis:
[Resumo das odds de cada mercado]

# Probabilidades Calculadas (REAL vs IMPLÍCITA):
[Para cada mercado, mostrando probabilidades calculadas vs. implícitas]

# Oportunidades Identificadas:
[Mercados onde você identificou valor, com o percentual de edge]

# Nível de Confiança Geral: [Baixo/Médio/Alto]
[Justificativa para o nível de confiança]
"""

        # Compile the final prompt
        sections = [
            fundamental_stats,
            result_stats,
            goals_stats,
            corners_stats,
            cards_stats,
            markets_info,
            instructions
        ]
        
        full_prompt = "\n".join([s for s in sections if s])
        logger.info(f"Prompt prepared successfully for {home_team} vs {away_team}")
        
        return full_prompt
        
    except Exception as e:
        logger.error(f"Error formatting optimized prompt: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return a simplified prompt as fallback
        return f"""
# ERRO NA FORMATAÇÃO DO PROMPT
Houve um erro ao formatar o prompt completo. Por favor, tente analisar a partida entre {home_team} e {away_team} com as informações estatísticas disponíveis.

{odds_data}

# INSTRUÇÕES
Mesmo com dados limitados, faça o melhor para analisar as probabilidades e identificar valor.
"""

