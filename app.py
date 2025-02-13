import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
from openai import OpenAI

# Configuração da página
st.set_page_config(
    page_title="Análise de Apostas Esportivas",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource(show_spinner=False)
def get_openai_client():
    """Função para criar e retornar o cliente OpenAI usando cache_resource"""
    try:
        return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    except Exception as e:
        st.error(f"Erro ao criar cliente OpenAI: {str(e)}")
        return None

def analyze_with_gpt(prompt):
    """Função para fazer a chamada à API do GPT"""
    try:
        client = get_openai_client()
        if not client:
            st.error("Não foi possível inicializar o cliente OpenAI")
            return None
            
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um Agente Analista de Probabilidades Esportivas especializado. Você DEVE seguir EXATAMENTE o formato de saída especificado no prompt do usuário, preenchendo todos os campos com os valores calculados."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Erro na chamada da API: {str(e)}")
        return None
# Funções do config.py agora diretamente no app.py
def get_fbref_urls():
    """Retorna o dicionário de URLs do FBref"""
    return {
        "Premier League": {
            "stats": "https://fbref.com/en/comps/9/Premier-League-Stats",
            "fixtures": "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
        },
        "La Liga": {
            "stats": "https://fbref.com/en/comps/12/La-Liga-Stats",
            "fixtures": "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"
        },
        "Serie A": {
            "stats": "https://fbref.com/en/comps/11/Serie-A-Stats",
            "fixtures": "https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures"
        },
        "Bundesliga": {
            "stats": "https://fbref.com/en/comps/20/Bundesliga-Stats",
            "fixtures": "https://fbref.com/en/comps/20/schedule/Bundesliga-Scores-and-Fixtures"
        },
        "Ligue 1": {
            "stats": "https://fbref.com/en/comps/13/Ligue-1-Stats",
            "fixtures": "https://fbref.com/en/comps/13/schedule/Ligue-1-Scores-and-Fixtures"
        },
        "Champions League": {
            "stats": "https://fbref.com/en/comps/8/Champions-League-Stats",
            "fixtures": "https://fbref.com/en/comps/8/schedule/Champions-League-Scores-and-Fixtures"
        }
    }

def parse_team_stats(html_content):
    """Processa os dados do time com tratamento de erros aprimorado"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        possible_table_ids = [
            'stats_squads_standard_for',
            'stats_squads_standard_overall',
            'stats_squads_standard_stats_squads',
            'stats_squads_standard_big5',
            'stats_squads_keeper_for',
            'stats_squads_keeper'
        ]
        
        stats_table = None
        for table_id in possible_table_ids:
            stats_table = soup.find('table', {'id': table_id})
            if stats_table:
                break
        
        if not stats_table:
            all_tables = soup.find_all('table')
            for table in all_tables:
                headers = table.find_all('th')
                header_text = [h.get_text(strip=True) for h in headers]
                if any(text in ['Squad', 'Team'] for text in header_text):
                    stats_table = table
                    break
        
        if not stats_table:
            st.error("Não foi possível encontrar a tabela de estatísticas")
            return None
        
        df = pd.read_html(str(stats_table))[0]
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(-1)
        
        team_col = None
        for col in df.columns:
            if isinstance(col, str) and col.strip() in ['Squad', 'Team']:
                team_col = col
                break
        
        if team_col:
            df = df.rename(columns={team_col: 'Squad'})
        else:
            df = df.rename(columns={df.columns[0]: 'Squad'})
        
        df['Squad'] = df['Squad'].str.strip()
        df = df.dropna(subset=['Squad'])
        df = df.drop_duplicates(subset=['Squad'])
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

def fetch_fbref_data(url):
    """Busca dados do FBref com tratamento de erros aprimorado"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        session = requests.Session()
        retries = 3
        
        for attempt in range(retries):
            try:
                response = session.get(url, headers=headers, timeout=60)
                response.raise_for_status()
                
                if not response.text or '<html' not in response.text.lower():
                    raise ValueError("Conteúdo HTML inválido recebido")
                
                time.sleep(2)
                return response.text
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt == retries - 1:
                    raise
                time.sleep(5 * (attempt + 1))
                
    except requests.Timeout:
        st.error("Timeout ao buscar dados. Por favor, tente novamente.")
        return None
    except requests.RequestException as e:
        st.error(f"Erro ao buscar dados: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return None

def format_prompt(stats_df, home_team, away_team, odds_data):
    """Formata o prompt para o GPT-4 com os dados coletados"""
    try:
        home_stats = stats_df[stats_df['Squad'] == home_team].iloc[0]
        away_stats = stats_df[stats_df['Squad'] == away_team].iloc[0]
        
        def get_stat(stats, col, default='N/A'):
            try:
                value = stats[col]
                if pd.notna(value):
                    return value
                return default
            except:
                return default

        # Mapeamento das colunas existentes
        home_team_stats = f"""
  * Jogos Disputados: {get_stat(home_stats, 'MP')}
  * Gols Marcados: {get_stat(home_stats, 'Gls')}
  * Gols por 90min: {get_stat(home_stats, 'G90')}
  * Expected Goals (xG): {get_stat(home_stats, 'xG')}
  * Expected Goals por 90min: {get_stat(home_stats, 'xG90')}
  * Posse de Bola: {get_stat(home_stats, 'Poss')}%"""

        away_team_stats = f"""
  * Jogos Disputados: {get_stat(away_stats, 'MP')}
  * Gols Marcados: {get_stat(away_stats, 'Gls')}
  * Gols por 90min: {get_stat(away_stats, 'G90')}
  * Expected Goals (xG): {get_stat(away_stats, 'xG')}
  * Expected Goals por 90min: {get_stat(away_stats, 'xG90')}
  * Posse de Bola: {get_stat(away_stats, 'Poss')}%"""
        
        prompt = f"""Role: Agente Analista de Probabilidades Esportivas

KNOWLEDGE BASE INTERNO:
- Estatísticas Home Team ({home_team}):{home_team_stats}

- Estatísticas Away Team ({away_team}):{away_team_stats}

ODDS DOS MERCADOS:
{odds_data}

INSTRUÇÕES CRÍTICAS:
1. CALCULAR probabilidades usando knowledge base interno
2. Converter odds em probabilidades implícitas (100/odd)
3. Analisar TODOS os mercados apresentados
4. Comparar probabilidades CALCULADAS vs IMPLÍCITAS
5. Identificar edges POSITIVOS significativos (diferença calculada - implícita > +3%)
   IMPORTANTE: Apenas edges POSITIVOS indicam valor para apostas!

[PROCESSO DE CÁLCULO OBRIGATÓRIO]
1. Base Calculation [35%]
- Desempenho geral (gols marcados, xG)
- Eficiência ofensiva e defensiva
- Posse de bola e controle de jogo
- Tendência de gols por 90 minutos

2. Technical Factors [25%]
- Expected goals (xG) e eficiência
- Gols marcados vs xG (over/underperformance)
- Média de gols por jogo
- Padrões ofensivos e defensivos

3. Market Analysis [20%]
- Linha base de probabilidade por mercado
- Ajustes por padrão de jogo
- Fatores situacionais
- Correlação entre mercados

4. Edge Identification [20%]
- Focar em edges POSITIVOS > +3%
- Força do edge (+3% a +5% moderado, >+5% forte)
- Risk assessment
- Consistência entre mercados correlacionados

[SAÍDA OBRIGATÓRIA - FORMATO ESTRITO]
Partida: {home_team} x {away_team}

Money Line:
- Casa: {home_team} [CALCULADO]% (edge: [+/-X.X]%) | Implícita: [100/odd]%
- Empate: [CALCULADO]% (edge: [+/-X.X]%) | Implícita: [100/odd]%
- Fora: {away_team} [CALCULADO]% (edge: [+/-X.X]%) | Implícita: [100/odd]%

Over/Under [linha]:
- Over: [CALCULADO]% (edge: [+/-X.X]%) | Implícita: [100/odd]%
- Under: [CALCULADO]% (edge: [+/-X.X]%) | Implícita: [100/odd]%

Chance Dupla:
- 1X: [CALCULADO]% (edge: [+/-X.X]%) | Implícita: [100/odd]%
- 12: [CALCULADO]% (edge: [+/-X.X]%) | Implícita: [100/odd]%
- X2: [CALCULADO]% (edge: [+/-X.X]%) | Implícita: [100/odd]%

Ambos Marcam:
- Sim: [CALCULADO]% (edge: [+/-X.X]%) | Implícita: [100/odd]%
- Não: [CALCULADO]% (edge: [+/-X.X]%) | Implícita: [100/odd]%

OPORTUNIDADES IDENTIFICADAS (Edges Positivos >3%):
1. [Mercado] - Edge: +[X.X]% [FORTE/MODERADO]
2. [Mercado] - Edge: +[X.X]% [FORTE/MODERADO]
[Listar apenas edges POSITIVOS >3%]

Nível de Confiança Geral: [Baixo/Médio/Alto]
Recomendação de Valor: [Destacar apenas os mercados com edges POSITIVOS significativos]

CHECKLIST FINAL:
1. Knowledge Base foi usado para cálculos? [S/N]
2. Todos os mercados foram analisados? [S/N]
3. Edges POSITIVOS foram identificados corretamente? [S/N]
4. Times identificados corretamente? [S/N]"""
        
        return prompt
    except Exception as e:
        st.error(f"Erro ao formatar prompt: {str(e)}")
        return None

def main():
    try:
        # Inicializa os URLs do FBref
        FBREF_URLS = get_fbref_urls()
        
        # Estado da aplicação
        if 'load_state' not in st.session_state:
            st.session_state.load_state = 'initial'

        # Título principal
        st.title("Análise de Apostas Esportivas")
        
        # Sidebar
        st.sidebar.title("Configurações")
        
        # Mostrar status de carregamento
        status_container = st.empty()
        
        selected_league = st.sidebar.selectbox(
            "Escolha o campeonato:",
            list(FBREF_URLS.keys())
        )
        
        try:
            # Busca dados do campeonato
            with st.spinner("Carregando dados do campeonato..."):
                st.session_state.load_state = 'loading'
                status_container.info("Carregando dados...")
                
                stats_html = fetch_fbref_data(FBREF_URLS[selected_league]["stats"])
                
                if not stats_html:
                    st.error("Não foi possível carregar os dados do campeonato")
                    return
                
                team_stats_df = parse_team_stats(stats_html)
                
                if team_stats_df is None or 'Squad' not in team_stats_df.columns:
                    st.error("Erro ao processar dados dos times")
                    return
                
                st.session_state.load_state = 'loaded'
                status_container.success("Dados carregados com sucesso!")
                
                teams = team_stats_df['Squad'].dropna().unique().tolist()
                
                if not teams:
                    st.error("Não foi possível encontrar os times do campeonato")
                    return
                
                # Seleção dos times
                col1, col2 = st.columns(2)
                with col1:
                    home_team = st.selectbox("Time da Casa:", teams)
                with col2:
                    away_teams = [team for team in teams if team != home_team]
                    away_team = st.selectbox("Time Visitante:", away_teams)
                
                # Seleção de Mercados
                st.markdown("### Seleção de Mercados")

                # Seleção de mercados
                mercados = {
                    "money_line": "Money Line (1X2)",
                    "over_under": "Over/Under",
                    "chance_dupla": "Chance Dupla",
                    "ambos_marcam": "Ambos Marcam",
                    "escanteios": "Total de Escanteios",
                    "cartoes": "Total de Cartões"
                }

                selected_markets = {}
                col1, col2 = st.columns(2)

                with col1:
                    for mercado in list(mercados.keys())[:3]:
                        selected_markets[mercado] = st.checkbox(mercados[mercado], value=False)

                with col2:
                    for mercado in list(mercados.keys())[3:]:
                        selected_markets[mercado] = st.checkbox(mercados[mercado], value=False)

                # Seção de Odds
                st.markdown("### Odds dos Mercados")

                odds_data = {}

                if selected_markets["money_line"]:
                    with st.expander("Money Line", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            odds_data["home"] = st.number_input("Casa (@)", min_value=1.01, value=0.0, format="%.2f", key="ml_home")
                        with col2:
                            odds_data["draw"] = st.number_input("Empate (@)", min_value=1.01, value=0.0, format="%.2f", key="ml_draw")
                        with col3:
                            odds_data["away"] = st.number_input("Fora (@)", min_value=1.01, value=0.0, format="%.2f", key="ml_away")

if selected_markets["over_under"]:
    with st.expander("Over/Under", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["goals_line"] = st.number_input("Linha", min_value=0.5, value=2.5, step=0.5, format="%.1f")
        with col2:
            odds_data["over"] = st.number_input(f"Over (@)", min_value=1.01, value=0.0, format="%.2f", key="ou_over")
        with col3:
            odds_data["under"] = st.number_input(f"Under (@)", min_value=1.01, value=0.0, format="%.2f", key="ou_under")

if selected_markets["chance_dupla"]:
    with st.expander("Chance Dupla", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["1x"] = st.number_input("1X (@)", min_value=1.01, value=0.0, format="%.2f", key="dc_1x")
        with col2:
            odds_data["12"] = st.number_input("12 (@)", min_value=1.01, value=0.0, format="%.2f", key="dc_12")
        with col3:
            odds_data["x2"] = st.number_input("X2 (@)", min_value=1.01, value=0.0, format="%.2f", key="dc_x2")

if selected_markets["ambos_marcam"]:
    with st.expander("Ambos Marcam", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            odds_data["btts_yes"] = st.number_input("Sim (@)", min_value=1.01, value=0.0, format="%.2f", key="btts_yes")
        with col2:
            odds_data["btts_no"] = st.number_input("Não (@)", min_value=1.01, value=0.0, format="%.2f", key="btts_no")

if selected_markets["escanteios"]:
    with st.expander("Total de Escanteios", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["corners_line"] = st.number_input("Linha Escanteios", min_value=0.5, value=9.5, step=0.5, format="%.1f")
        with col2:
            odds_data["corners_over"] = st.number_input("Over Escanteios (@)", min_value=1.01, value=0.0, format="%.2f", key="corners_over")
        with col3:
            odds_data["corners_under"] = st.number_input("Under Escanteios (@)", min_value=1.01, value=0.0, format="%.2f", key="corners_under")

if selected_markets["cartoes"]:
    with st.expander("Total de Cartões", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["cards_line"] = st.number_input("Linha Cartões", min_value=0.5, value=3.5, step=0.5, format="%.1f")
        with col2:
            odds_data["cards_over"] = st.number_input("Over Cartões (@)", min_value=1.01, value=0.0, format="%.2f", key="cards_over")
        with col3:
            odds_data["cards_under"] = st.number_input("Under Cartões (@)", min_value=1.01, value=0.0, format="%.2f", key="cards_under")

# Formata os dados das odds apenas para mercados selecionados com odds preenchidas
formatted_odds = []

if selected_markets["money_line"] and all(odds_data.get(k, 0) > 0 for k in ["home", "draw", "away"]):
    formatted_odds.append(f"""Money Line:
- Casa: @{odds_data['home']:.2f} (Implícita: {(100/odds_data['home']):.1f}%)
- Empate: @{odds_data['draw']:.2f} (Implícita: {(100/odds_data['draw']):.1f}%)
- Fora: @{odds_data['away']:.2f} (Implícita: {(100/odds_data['away']):.1f}%)""")

if selected_markets["over_under"] and all(odds_data.get(k, 0) > 0 for k in ["over", "under"]):
    formatted_odds.append(f"""Over/Under {odds_data['goals_line']}:
- Over: @{odds_data['over']:.2f} (Implícita: {(100/odds_data['over']):.1f}%)
- Under: @{odds_data['under']:.2f} (Implícita: {(100/odds_data['under']):.1f}%)""")

if selected_markets["chance_dupla"] and all(odds_data.get(k, 0) > 0 for k in ["1x", "12", "x2"]):
    formatted_odds.append(f"""Chance Dupla:
- 1X: @{odds_data['1x']:.2f} (Implícita: {(100/odds_data['1x']):.1f}%)
- 12: @{odds_data['12']:.2f} (Implícita: {(100/odds_data['12']):.1f}%)
- X2: @{odds_data['x2']:.2f} (Implícita: {(100/odds_data['x2']):.1f}%)""")

if selected_markets["ambos_marcam"] and all(odds_data.get(k, 0) > 0 for k in ["btts_yes", "btts_no"]):
    formatted_odds.append(f"""Ambos Marcam:
- Sim: @{odds_data['btts_yes']:.2f} (Implícita: {(100/odds_data['btts_yes']):.1f}%)
- Não: @{odds_data['btts_no']:.2f} (Implícita: {(100/odds_data['btts_no']):.1f}%)""")

if selected_markets["escanteios"] and all(odds_data.get(k, 0) > 0 for k in ["corners_over", "corners_under"]):
    formatted_odds.append(f"""Total de Escanteios {odds_data['corners_line']}:
- Over: @{odds_data['corners_over']:.2f} (Implícita: {(100/odds_data['corners_over']):.1f}%)
- Under: @{odds_data['corners_under']:.2f} (Implícita: {(100/odds_data['corners_under']):.1f}%)""")

if selected_markets["cartoes"] and all(odds_data.get(k, 0) > 0 for k in ["cards_over", "cards_under"]):
    formatted_odds.append(f"""Total de Cartões {odds_data['cards_line']}:
- Over: @{odds_data['cards_over']:.2f} (Implícita: {(100/odds_data['cards_over']):.1f}%)
- Under: @{odds_data['cards_under']:.2f} (Implícita: {(100/odds_data['cards_under']):.1f}%)""")

                odds_data = "\n\n".join(formatted_odds)

                # Botão de análise
                if st.button("Analisar Partida", type="primary"):
                    with st.spinner("Realizando análise..."):
                        try:
                            prompt = format_prompt(
                                team_stats_df,
                                home_team,
                                away_team,
                                odds_data
                            )
                            
                            if prompt:
                                analysis = analyze_with_gpt(prompt)
                                st.markdown("## Análise da Partida")
                                st.markdown(analysis)
                        except Exception as e:
                            st.error(f"Erro na análise: {str(e)}")
                            import traceback
                            st.error(f"Traceback:\n```\n{traceback.format_exc()}\n```")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            import traceback
            st.error(f"Traceback:\n```\n{traceback.format_exc()}\n```")
    except Exception as e:
        st.error(f"Erro geral na aplicação: {str(e)}")
        import traceback
        st.error(f"Traceback:\n```\n{traceback.format_exc()}\n```")

if __name__ == "__main__":
    main()
