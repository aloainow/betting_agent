import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from openai import OpenAI
import traceback
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Análise de Apostas Esportivas",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definição das URLs do FBref
FBREF_URLS = {
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

def get_odds_data(selected_markets):
    """Função para coletar e formatar os dados das odds"""
    odds_data = {}
    formatted_odds = []

    # Money Line
    if selected_markets.get("money_line", False):
        st.markdown("### Money Line")
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["home"] = st.number_input("Casa (@)", min_value=1.01, step=0.01, value=1.01, format="%.2f", key="ml_home")
        with col2:
            odds_data["draw"] = st.number_input("Empate (@)", min_value=1.01, step=0.01, value=1.01, format="%.2f", key="ml_draw")
        with col3:
            odds_data["away"] = st.number_input("Fora (@)", min_value=1.01, step=0.01, value=1.01, format="%.2f", key="ml_away")

        if all(odds_data.get(k, 0) > 1.01 for k in ["home", "draw", "away"]):
            formatted_odds.append(f"""Money Line:
- Casa: @{odds_data['home']:.2f} (Implícita: {(100/odds_data['home']):.1f}%)
- Empate: @{odds_data['draw']:.2f} (Implícita: {(100/odds_data['draw']):.1f}%)
- Fora: @{odds_data['away']:.2f} (Implícita: {(100/odds_data['away']):.1f}%)""")

    # Over/Under
    if selected_markets.get("over_under", False):
        st.markdown("### Over/Under")
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["goals_line"] = st.number_input("Linha", min_value=0.5, value=2.5, step=0.5, format="%.1f", key="goals_line")
        with col2:
            odds_data["over"] = st.number_input(f"Over (@)", min_value=1.01, step=0.01, value=1.01, format="%.2f", key="ou_over")
        with col3:
            odds_data["under"] = st.number_input(f"Under (@)", min_value=1.01, step=0.01, value=1.01, format="%.2f", key="ou_under")

        if all(odds_data.get(k, 0) > 1.01 for k in ["over", "under"]):
            formatted_odds.append(f"""Over/Under {odds_data['goals_line']}:
- Over: @{odds_data['over']:.2f} (Implícita: {(100/odds_data['over']):.1f}%)
- Under: @{odds_data['under']:.2f} (Implícita: {(100/odds_data['under']):.1f}%)""")

    # Ambos Marcam
    if selected_markets.get("ambos_marcam", False):
        st.markdown("### Ambos Marcam")
        col1, col2 = st.columns(2)
        with col1:
            odds_data["btts_yes"] = st.number_input("Sim (@)", min_value=1.01, step=0.01, value=1.01, format="%.2f", key="btts_yes")
        with col2:
            odds_data["btts_no"] = st.number_input("Não (@)", min_value=1.01, step=0.01, value=1.01, format="%.2f", key="btts_no")

        if all(odds_data.get(k, 0) > 1.01 for k in ["btts_yes", "btts_no"]):
            formatted_odds.append(f"""Ambos Marcam:
- Sim: @{odds_data['btts_yes']:.2f} (Implícita: {(100/odds_data['btts_yes']):.1f}%)
- Não: @{odds_data['btts_no']:.2f} (Implícita: {(100/odds_data['btts_no']):.1f}%)""")

    # Total de Escanteios
    if selected_markets.get("escanteios", False):
        st.markdown("### Total de Escanteios")
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["corners_line"] = st.number_input("Linha Escanteios", min_value=0.5, value=9.5, step=0.5, format="%.1f", key="corners_line")
        with col2:
            odds_data["corners_over"] = st.number_input("Over Escanteios (@)", min_value=1.01, step=0.01, value=1.01, format="%.2f", key="corners_over")
        with col3:
            odds_data["corners_under"] = st.number_input("Under Escanteios (@)", min_value=1.01, step=0.01, value=1.01, format="%.2f", key="corners_under")

        if all(odds_data.get(k, 0) > 1.01 for k in ["corners_over", "corners_under"]):
            formatted_odds.append(f"""Total de Escanteios {odds_data['corners_line']}:
- Over: @{odds_data['corners_over']:.2f} (Implícita: {(100/odds_data['corners_over']):.1f}%)
- Under: @{odds_data['corners_under']:.2f} (Implícita: {(100/odds_data['corners_under']):.1f}%)""")

    # Total de Cartões
    if selected_markets.get("cartoes", False):
        st.markdown("### Total de Cartões")
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["cards_line"] = st.number_input("Linha Cartões", min_value=0.5, value=3.5, step=0.5, format="%.1f", key="cards_line")
        with col2:
            odds_data["cards_over"] = st.number_input("Over Cartões (@)", min_value=1.01, step=0.01, value=1.01, format="%.2f", key="cards_over")
        with col3:
            odds_data["cards_under"] = st.number_input("Under Cartões (@)", min_value=1.01, step=0.01, value=1.01, format="%.2f", key="cards_under")

        if all(odds_data.get(k, 0) > 1.01 for k in ["cards_over", "cards_under"]):
            formatted_odds.append(f"""Total de Cartões {odds_data['cards_line']}:
- Over: @{odds_data['cards_over']:.2f} (Implícita: {(100/odds_data['cards_over']):.1f}%)
- Under: @{odds_data['cards_under']:.2f} (Implícita: {(100/odds_data['cards_under']):.1f}%)""")

    return "\n\n".join(formatted_odds)
    
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

@st.cache_resource
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
            model="gpt-4",
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



def parse_team_stats(html_content):
    """Processa os dados do time com tratamento melhorado para extrair estatísticas"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Procurar todas as tabelas que podem conter as estatísticas
        stats_table = None
        
        # Lista de IDs de tabelas conhecidos
        table_ids = [
            'stats_squads_standard_for',
            'stats_squads_standard_stats',
            'stats_squads_standard_overall',
            'stats_squads_keeper_for'
        ]
        
        # Tentar encontrar a tabela por ID
        for table_id in table_ids:
            stats_table = soup.find('table', {'id': table_id})
            if stats_table:
                break
        
        # Se não encontrou por ID, procurar por conteúdo
        if not stats_table:
            all_tables = soup.find_all('table')
            for table in all_tables:
                headers = table.find_all('th')
                if headers:
                    header_text = [h.get_text(strip=True).lower() for h in headers]
                    if any(keyword in ' '.join(header_text) for keyword in ['squad', 'team', 'goals']):
                        stats_table = table
                        break
        
        if not stats_table:
            return None
        
        # Ler a tabela com pandas
        df = pd.read_html(str(stats_table))[0]
        
        # Tratar colunas multi-índice e duplicadas
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[-1] if isinstance(col, tuple) else col for col in df.columns]
        
        # Remover colunas duplicadas mantendo a primeira ocorrência
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Limpar nomes das colunas
        df.columns = [str(col).strip() for col in df.columns]
        
        # Função para encontrar a coluna correta
        def find_column(possible_names, df_columns):
            for name in possible_names:
                # Procura exata
                if name in df_columns:
                    return name
                # Procura case-insensitive
                matches = [col for col in df_columns if str(col).strip().lower() == name.lower()]
                if matches:
                    return matches[0]
                # Procura por substring
                matches = [col for col in df_columns if name.lower() in str(col).strip().lower()]
                if matches:
                    return matches[0]
            return None

        # Mapear colunas importantes
        column_mapping = {
            'Squad': ['Squad', 'Team', 'Equipe'],
            'MP': ['MP', 'Matches', 'Jogos'],
            'Gls': ['Gls', 'Goals', 'Gols', 'G'],
            'G90': ['G90', 'Goals90', 'Gols90'],
            'xG': ['xG', 'Expected Goals'],
            'xG90': ['xG90', 'ExpectedGoals90'],
            'Poss': ['Poss', 'Possession', 'PosseBola']
        }
        
        # Encontrar e renomear colunas usando find_column
        new_columns = {}
        for new_name, possible_names in column_mapping.items():
            found_col = find_column(possible_names, df.columns)
            if found_col:
                new_columns[found_col] = new_name
        
        # Aplicar o mapeamento de colunas
        df = df.rename(columns=new_columns)
        
        # Garantir coluna Squad
        if 'Squad' not in df.columns and len(df.columns) > 0:
            df = df.rename(columns={df.columns[0]: 'Squad'})
        
        # Limpar dados
        df['Squad'] = df['Squad'].astype(str).str.strip()
        df = df.dropna(subset=['Squad'])
        df = df.drop_duplicates(subset=['Squad'])
        
        # Converter colunas numéricas com segurança
        numeric_columns = ['MP', 'Gls', 'G90', 'xG', 'xG90', 'Poss']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    # Primeiro, garantir que a coluna é uma série e não um DataFrame
                    if isinstance(df[col], pd.DataFrame):
                        df[col] = df[col].iloc[:, 0]
                    
                    # Limpar e converter para número
                    df[col] = pd.to_numeric(
                        df[col].astype(str)
                           .str.replace(',', '.')
                           .str.extract('([-+]?\d*\.?\d+)', expand=False),
                        errors='coerce'
                    )
                except Exception:
                    df[col] = np.nan
        
        # Preencher valores ausentes
        df = df.fillna('N/A')
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        return None

def fetch_fbref_data(url):
    """Busca dados do FBref com retry melhorado e headers customizados"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
    }
    
    session = requests.Session()
    retries = 3
    
    for attempt in range(retries):
        try:
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            if 'cf-browser-verification' in response.text.lower():
                st.warning(f"Detectado Cloudflare protection. Tentativa {attempt + 1}/{retries}...")
                time.sleep(5 * (attempt + 1))
                continue
            
            if '<table' not in response.text.lower():
                st.warning(f"Nenhuma tabela encontrada na resposta. Tentativa {attempt + 1}/{retries}...")
                time.sleep(5 * (attempt + 1))
                continue
                
            return response.text
            
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                st.error(f"Erro ao buscar dados (tentativa {attempt + 1}/{retries}): {str(e)}")
                return None
            st.warning(f"Erro na tentativa {attempt + 1}, tentando novamente em {5 * (attempt + 1)} segundos...")
            time.sleep(5 * (attempt + 1))
    
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
        # Título principal na sidebar
        st.sidebar.title("Análise de Apostas Esportivas")
        
        # Configurações na sidebar
        st.sidebar.title("Configurações")
        selected_league = st.sidebar.selectbox(
            "Escolha o campeonato:",
            list(FBREF_URLS.keys())
        )
        
        # Container de status para mensagens
        status_container = st.sidebar.empty()
        
        try:
            # Busca dados do campeonato
            with st.spinner("Carregando dados do campeonato..."):
                stats_html = fetch_fbref_data(FBREF_URLS[selected_league]["stats"])
                
                if not stats_html:
                    st.error("Não foi possível carregar os dados do campeonato")
                    return
                
                team_stats_df = parse_team_stats(stats_html)
                
                if team_stats_df is None or 'Squad' not in team_stats_df.columns:
                    st.error("Erro ao processar dados dos times")
                    return
                
                status_container.success("Dados carregados com sucesso!")
                
                teams = team_stats_df['Squad'].dropna().unique().tolist()
                
                if not teams:
                    st.error("Não foi possível encontrar os times do campeonato")
                    return
                
                # Área principal
                st.title("Seleção de Times")
                
                # Seleção dos times em duas colunas
                col1, col2 = st.columns(2)
                with col1:
                    home_team = st.selectbox("Time da Casa:", teams, key='home_team')
                with col2:
                    away_teams = [team for team in teams if team != home_team]
                    away_team = st.selectbox("Time Visitante:", away_teams, key='away_team')

                # Seleção de mercados em container separado
                with st.expander("Mercados Disponíveis", expanded=True):
                    st.markdown("### Seleção de Mercados")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        selected_markets = {
                            "money_line": st.checkbox("Money Line (1X2)", key='ml'),
                            "over_under": st.checkbox("Over/Under", key='ou'),
                            "chance_dupla": st.checkbox("Chance Dupla", key='cd')
                        }
                    
                    with col2:
                        selected_markets.update({
                            "ambos_marcam": st.checkbox("Ambos Marcam", key='btts'),
                            "escanteios": st.checkbox("Total de Escanteios", key='corners'),
                            "cartoes": st.checkbox("Total de Cartões", key='cards')
                        })

                # Inputs de odds em container separado
                if any(selected_markets.values()):
                    with st.expander("Configuração de Odds", expanded=True):
                        odds_data = get_odds_data(selected_markets)

                # Botão de análise centralizado
                col1, col2, col3 = st.columns([1,1,1])
                with col2:
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
                                    if analysis:
                                        st.markdown("## Análise da Partida")
                                        st.markdown(analysis)
                            except Exception as e:
                                st.error(f"Erro na análise: {str(e)}")
                
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            
    except Exception as e:
        st.error(f"Erro geral na aplicação: {str(e)}")

if __name__ == "__main__":
    main()
