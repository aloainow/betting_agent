import streamlit as st
import pandas as pd
import openai
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time

# Configuração da página
st.set_page_config(
    page_title="Agente de Apostas Esportivas",
    layout="wide"
)

# Configuração da API OpenAI
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Dicionário com URLs do FBref
FBREF_URLS = {
    "Premier League": {
        "stats": "https://fbref.com/en/comps/9/Premier-League-Stats",
        "fixtures": "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    },
    "La Liga": {
        "stats": "https://fbref.com/en/comps/12/La-Liga-Stats",
        "fixtures": "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"
    },
    "Ligue 1": {
        "stats": "https://fbref.com/en/comps/13/Ligue-1-Stats",
        "fixtures": "https://fbref.com/en/comps/13/schedule/Ligue-1-Scores-and-Fixtures"
    },
    "Serie A": {
        "stats": "https://fbref.com/en/comps/11/Serie-A-Stats",
        "fixtures": "https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures"
    },
    "Bundesliga": {
        "stats": "https://fbref.com/en/comps/20/Bundesliga-Stats",
        "fixtures": "https://fbref.com/en/comps/20/schedule/Bundesliga-Scores-and-Fixtures"
    },
    "Champions League": {
        "stats": "https://fbref.com/en/comps/8/Champions-League-Stats",
        "fixtures": "https://fbref.com/en/comps/8/schedule/Champions-League-Scores-and-Fixtures"
    },
    "Liga Argentina": {
        "stats": "https://fbref.com/en/comps/21/Liga-Profesional-Argentina-Stats",
        "fixtures": "https://fbref.com/en/comps/21/schedule/Liga-Profesional-Argentina-Scores-and-Fixtures"
    }
}

# Headers para simular um navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

@st.cache_data(ttl=3600)  # Cache por 1 hora
def fetch_fbref_data(url):
    """
    Busca dados do FBref com web scraping
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except Exception as e:
        st.error(f"Erro ao buscar dados do FBref: {str(e)}")
        return None

def handle_champions_league_data(df):
    """
    Trata especificamente os dados da Champions League que podem ter estrutura diferente
    """
    if df is None:
        return None
        
    # Remove linhas de grupo/classificação se existirem
    df = df[~df['Squad'].str.contains('Group', na=False)]
    
    # Remove linhas vazias ou com informações de qualificação
    df = df[df['Squad'].notna()]
    df = df[~df['Squad'].str.contains('Qualification|Qual.|qualifying', na=False, case=False)]
    
    return df

def parse_team_stats(html_content, league_name=''):
    """
    Extrai estatísticas dos times do HTML do FBref
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    stats_table = soup.find('table', {'id': 'stats_squads_standard_for'})
    
    if not stats_table:
        return None
    
    df = pd.read_html(str(stats_table))[0]
    
    # Tratamento especial para Champions League
    if league_name == 'Champions League':
        df = handle_champions_league_data(df)
        
    return df

def parse_fixtures(html_content):
    """
    Extrai dados de partidas do HTML do FBref
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    fixtures_table = soup.find('table', {'id': 'sched_all'})
    
    if not fixtures_table:
        return None
    
    df = pd.read_html(str(fixtures_table))[0]
    return df

def get_team_recent_form(fixtures_df, team_name):
    """
    Obtém forma recente do time baseado nos últimos jogos
    """
    team_matches = fixtures_df[
        (fixtures_df['Home'] == team_name) | 
        (fixtures_df['Away'] == team_name)
    ].tail(5)
    
    return team_matches

def get_h2h_matches(fixtures_df, home_team, away_team):
    """
    Obtém histórico de confrontos diretos
    """
    h2h_matches = fixtures_df[
        ((fixtures_df['Home'] == home_team) & (fixtures_df['Away'] == away_team)) |
        ((fixtures_df['Home'] == away_team) & (fixtures_df['Away'] == home_team))
    ].tail(3)
    
    return h2h_matches

def format_last_matches(matches_df):
    """Formata os últimos jogos em uma string legível"""
    results = []
    for _, match in matches_df.iterrows():
        if match['Home'] == match['Squad']:
            result = f"vs {match['Away']} (H): {match['Score']}"
        else:
            result = f"vs {match['Home']} (A): {match['Score']}"
        results.append(result)
    return "\n    - " + "\n    - ".join(results)

def calculate_home_performance(fixtures_df, team):
    """Calcula o desempenho como mandante"""
    home_matches = fixtures_df[fixtures_df['Home'] == team].tail(10)
    wins = len(home_matches[home_matches['Result'] == 'W'])
    draws = len(home_matches[home_matches['Result'] == 'D'])
    losses = len(home_matches[home_matches['Result'] == 'L'])
    return {'wins': wins, 'draws': draws, 'losses': losses}

def calculate_away_performance(fixtures_df, team):
    """Calcula o desempenho como visitante"""
    away_matches = fixtures_df[fixtures_df['Away'] == team].tail(10)
    wins = len(away_matches[away_matches['Result'] == 'W'])
    draws = len(away_matches[away_matches['Result'] == 'D'])
    losses = len(away_matches[away_matches['Result'] == 'L'])
    return {'wins': wins, 'draws': draws, 'losses': losses}

def format_performance(performance):
    """Formata o desempenho em uma string legível"""
    return f"{performance['wins']}V {performance['draws']}E {performance['losses']}D"

def format_h2h(h2h_df):
    """Formata o histórico H2H em uma string legível"""
    results = []
    for _, match in h2h_df.iterrows():
        result = f"{match['Home']} {match['Score']} {match['Away']}"
        results.append(result)
    return "\n    - " + "\n    - ".join(results)
    if competition != 'Champions League':
        return None
        
    knockout_matches = fixtures_df[
        (fixtures_df['Round'].str.contains('16|Quarter-finals|Semi-finals|Final', na=False)) &
        ((fixtures_df['Home'] == team_name) | (fixtures_df['Away'] == team_name))
    ]
    
    stats = {
        'matches_played': len(knockout_matches),
        'wins': len(knockout_matches[
            ((knockout_matches['Home'] == team_name) & (knockout_matches['Score'].str.contains('W', na=False))) |
            ((knockout_matches['Away'] == team_name) & (knockout_matches['Score'].str.contains('L', na=False)))
        ]),
        'clean_sheets': len(knockout_matches[
            ((knockout_matches['Home'] == team_name) & (knockout_matches['Score'].str.contains('0', na=False))) |
            ((knockout_matches['Away'] == team_name) & (knockout_matches['Score'].str.contains('0', na=False)))
        ])
    }
    
    return stats

def format_prompt(home_team, away_team, team_stats_df, fixtures_df, competition):
    """
    Formata o prompt com os dados do FBref seguindo a estrutura exata do agente
    """
    # Obtém estatísticas dos times
    home_stats = team_stats_df[team_stats_df['Squad'] == home_team].iloc[0]
    away_stats = team_stats_df[team_stats_df['Squad'] == away_team].iloc[0]
    
    # Obtém últimos 10 jogos
    home_last_10 = get_team_recent_form(fixtures_df, home_team, 10)
    away_last_10 = get_team_recent_form(fixtures_df, away_team, 10)
    
    # Obtém H2H (últimos 3 confrontos)
    h2h = get_h2h_matches(fixtures_df, home_team, away_team)
    
    # Calcula home/away performance
    home_performance = calculate_home_performance(fixtures_df, home_team)
    away_performance = calculate_away_performance(fixtures_df, away_team)
    
    kb_data = f"""KNOWLEDGE BASE INTERNO:
    
    {home_team} (Casa):
    - Posição atual: {home_stats['Rk']}
    - Gols marcados: {home_stats['GF']}
    - Gols sofridos: {home_stats['GA']}
    - Expected Goals (xG): {home_stats['xG']}
    - Expected Goals Against (xGA): {home_stats['xGA']}
    - Clean sheets: {home_stats['CS']}
    - Últimos 10 jogos: {format_last_matches(home_last_10)}
    - Desempenho como mandante: {format_performance(home_performance)}
    
    {away_team} (Fora):
    - Posição atual: {away_stats['Rk']}
    - Gols marcados: {away_stats['GF']}
    - Gols sofridos: {away_stats['GA']}
    - Expected Goals (xG): {away_stats['xG']}
    - Expected Goals Against (xGA): {away_stats['xGA']}
    - Clean sheets: {away_stats['CS']}
    - Últimos 10 jogos: {format_last_matches(away_last_10)}
    - Desempenho como visitante: {format_performance(away_performance)}
    
    Histórico H2H (últimos 3 jogos):
    {format_h2h(h2h)}"""
    
    # Coleta todas as odds
    odds_data = f"""ODDS DOS MERCADOS:

Money Line:
- Casa: @{odd_home:.2f} (Implícita: {(100/odd_home):.1f}%)
- Empate: @{odd_draw:.2f} (Implícita: {(100/odd_draw):.1f}%)
- Fora: @{odd_away:.2f} (Implícita: {(100/odd_away):.1f}%)

Over/Under {goals_line}:
- Over: @{odd_over:.2f} (Implícita: {(100/odd_over):.1f}%)
- Under: @{odd_under:.2f} (Implícita: {(100/odd_under):.1f}%)

Chance Dupla:
- 1X: @{odd_1x:.2f} (Implícita: {(100/odd_1x):.1f}%)
- 12: @{odd_12:.2f} (Implícita: {(100/odd_12):.1f}%)
- X2: @{odd_x2:.2f} (Implícita: {(100/odd_x2):.1f}%)

Ambos Marcam:
- Sim: @{odd_btts_yes:.2f} (Implícita: {(100/odd_btts_yes):.1f}%)
- Não: @{odd_btts_no:.2f} (Implícita: {(100/odd_btts_no):.1f}%)
"""

    prompt = f"""Role: Agente Analista de Probabilidades Esportivas

{kb_data}

{odds_data}

INSTRUÇÕES CRÍTICAS:
1. CALCULAR probabilidades usando knowledge base interno
2. Converter odds em probabilidades implícitas (100/odd)
3. Analisar TODOS os mercados apresentados
4. Comparar probabilidades CALCULADAS vs IMPLÍCITAS
5. Identificar edges (diferença entre calculada e implícita)

[PROCESSO DE CÁLCULO OBRIGATÓRIO]
1. Base Calculation [35%]
- Form recente (últimos 5 jogos do KB)
- H2H (últimos 3 confrontos do KB)
- Home/Away performance (KB)
- Tendência de gols (KB)

2. Technical Factors [25%]
- Expected goals (xG do KB)
- Gols marcados/sofridos (KB)
- Clean sheets (KB)
- Posição na tabela (KB)

3. Market Analysis [20%]
- Linha base de probabilidade por mercado
- Ajustes por padrão de jogo (baseado no KB)
- Fatores situacionais (KB)

4. Edge Calculation [20%]
- Calc vs Implied difference
- Confidence rating
- Risk assessment

[SAÍDA OBRIGATÓRIA]
Partida: {home_team} x {away_team}

Use EXATAMENTE este formato para cada mercado:
Money Line:
- Casa: [CALCULADO via KB]% | Implícita: [100/odd]% (odd @x.xx)
- Empate: [CALCULADO via KB]% | Implícita: [100/odd]% (odd @x.xx)
- Fora: [CALCULADO via KB]% | Implícita: [100/odd]% (odd @x.xx)

Over/Under [linha]:
- Over: [CALCULADO via KB]% | Implícita: [100/odd]% (odd @x.xx)
- Under: [CALCULADO via KB]% | Implícita: [100/odd]% (odd @x.xx)

Chance Dupla:
- 1X: [CALCULADO via KB]% | Implícita: [100/odd]% (odd @x.xx)
- 12: [CALCULADO via KB]% | Implícita: [100/odd]% (odd @x.xx)
- X2: [CALCULADO via KB]% | Implícita: [100/odd]% (odd @x.xx)

Ambos Marcam:
- Sim: [CALCULADO via KB]% | Implícita: [100/odd]% (odd @x.xx)
- Não: [CALCULADO via KB]% | Implícita: [100/odd]% (odd @x.xx)

Valor Identificado:
- Mercado: [mercado com maior edge]
- Edge: [CALCULADO - Implícita]%

Nível de Confiança: [Baixo/Médio/Alto]
Alerta: [Se relevante]

CHECKLIST FINAL:
1. Knowledge Base foi usado para cálculos? [S/N]
2. Todos os mercados foram analisados? [S/N]
3. Edges foram calculados corretamente? [S/N]
4. Times identificados corretamente? [S/N]"""
    
    return prompt

def main():
    st.title("Análise de Apostas Esportivas")
    
    # Sidebar
    st.sidebar.title("Configurações")
    
    # Seleção de campeonato
    selected_league = st.sidebar.selectbox(
        "Escolha o campeonato:",
        list(FBREF_URLS.keys())
    )
    
    # Busca dados do campeonato selecionado
    with st.spinner("Carregando dados do campeonato..."):
        # Busca estatísticas
        stats_html = fetch_fbref_data(FBREF_URLS[selected_league]["stats"])
        fixtures_html = fetch_fbref_data(FBREF_URLS[selected_league]["fixtures"])
        
        if stats_html and fixtures_html:
            team_stats_df = parse_team_stats(stats_html)
            fixtures_df = parse_fixtures(fixtures_html)
            
            if team_stats_df is not None and fixtures_df is not None:
                # Lista de times
                teams = team_stats_df['Squad'].tolist()
                
                # Layout principal
                col1, col2 = st.columns(2)
                
                with col1:
                    home_team = st.selectbox("Time da Casa:", teams)
                
                with col2:
                    away_teams = [team for team in teams if team != home_team]
                    away_team = st.selectbox("Time Visitante:", away_teams)
                
                # Seção de Mercados e Odds
                st.markdown("### Odds dos Mercados")
                
                with st.expander("Money Line", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        odd_home = st.number_input("Casa (@)", min_value=1.01, format="%.2f", key="ml_home")
                    with col2:
                        odd_draw = st.number_input("Empate (@)", min_value=1.01, format="%.2f", key="ml_draw")
                    with col3:
                        odd_away = st.number_input("Fora (@)", min_value=1.01, format="%.2f", key="ml_away")

                with st.expander("Over/Under", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        goals_line = st.number_input("Linha", min_value=0.5, value=2.5, step=0.5, format="%.1f")
                    with col2:
                        odd_over = st.number_input(f"Over {goals_line} (@)", min_value=1.01, format="%.2f", key="ou_over")
                    with col3:
                        odd_under = st.number_input(f"Under {goals_line} (@)", min_value=1.01, format="%.2f", key="ou_under")

                with st.expander("Chance Dupla", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        odd_1x = st.number_input("1X (@)", min_value=1.01, format="%.2f", key="dc_1x")
                    with col2:
                        odd_12 = st.number_input("12 (@)", min_value=1.01, format="%.2f", key="dc_12")
                    with col3:
                        odd_x2 = st.number_input("X2 (@)", min_value=1.01, format="%.2f", key="dc_x2")

                with st.expander("Ambos Marcam", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        odd_btts_yes = st.number_input("Sim (@)", min_value=1.01, format="%.2f", key="btts_yes")
                    with col2:
                        odd_btts_no = st.number_input("Não (@)", min_value=1.01, format="%.2f", key="btts_no")

                if st.button("Analisar Partida"):
                    with st.spinner("Realizando análise..."):
                        # Formata o prompt com os dados
                        prompt = format_prompt(
                            home_team,
                            away_team,
                            team_stats_df,
                            fixtures_df
                        )
                        
                        # Obtém análise do GPT-4
                        try:
                            response = openai.ChatCompletion.create(
                                model="gpt-4",
                                messages=[
                                    {"role": "system", "content": "Você é um especialista em análise de probabilidades esportivas."},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.2,
                                max_tokens=2000
                            )
                            
                            analysis = response.choices[0].message.content
                            
                            st.markdown("### Resultado da Análise")
                            st.markdown(analysis)
                            
                            # Adiciona botão para baixar a análise
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"analise_{home_team}_vs_{away_team}_{timestamp}.txt"
                            st.download_button(
                                label="Baixar Análise",
                                data=analysis,
                                file_name=filename,
                                mime="text/plain"
                            )
                            
                        except Exception as e:
                            st.error(f"Erro na análise: {str(e)}")

if __name__ == "__main__":
    main()
