import streamlit as st
import pandas as pd
import openai
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time

# Configuração da página
st.set_page_config(
    page_title="Análise de Apostas Esportivas",
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

@st.cache_data(ttl=3600)
 # Adicione essa linha após seus imports
st.debug = st.write  # Para permitir logs de debug

def parse_team_stats(html_content):
    """Processa os dados do time com tratamento de erros aprimorado"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Busca mais generalizada por tabelas de estatísticas
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
                
        # Se ainda não encontrou, tenta buscar qualquer tabela com estatísticas
        if not stats_table:
            all_tables = soup.find_all('table')
            for table in all_tables:
                # Verifica se a tabela tem "Squad" ou "Team" no cabeçalho
                headers = table.find_all('th')
                header_text = [h.get_text(strip=True) for h in headers]
                if any(text in ['Squad', 'Team'] for text in header_text):
                    stats_table = table
                    break
        
        if not stats_table:
            st.error("Não foi possível encontrar a tabela de estatísticas")
            return None
        
        # Usa pandas para ler a tabela HTML
        df = pd.read_html(str(stats_table))[0]
        
        # Limpa os nomes das colunas multinível
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(-1)
        
        # Procura pela coluna com os nomes dos times
        team_col = None
        for col in df.columns:
            if isinstance(col, str) and col.strip() in ['Squad', 'Team']:
                team_col = col
                break
        
        if team_col:
            df = df.rename(columns={team_col: 'Squad'})
        else:
            # Se não encontrar a coluna específica, assume que a primeira coluna é a dos times
            df = df.rename(columns={df.columns[0]: 'Squad'})
        
        # Limpa os nomes dos times
        df['Squad'] = df['Squad'].str.strip()
        
        # Remove linhas com valores nulos e duplicatas
        df = df.dropna(subset=['Squad'])
        df = df.drop_duplicates(subset=['Squad'])
        
        # Log informações úteis
        st.write(f"Colunas encontradas: {df.columns.tolist()}")
        st.write(f"Número de times encontrados: {len(df)}")
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

def fetch_fbref_data(url):
    """Busca dados do FBref com tratamento de erros aprimorado"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Aumenta o timeout e adiciona retries
        session = requests.Session()
        retries = 3
        
        for attempt in range(retries):
            try:
                response = session.get(url, headers=headers, timeout=60)
                response.raise_for_status()
                
                # Verifica se o conteúdo é HTML válido
                if not response.text or '<html' not in response.text.lower():
                    raise ValueError("Conteúdo HTML inválido recebido")
                
                # Pequeno delay para evitar sobrecarga
                time.sleep(2)
                
                return response.text
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt == retries - 1:
                    raise
                time.sleep(5 * (attempt + 1))  # Backoff exponencial
                
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
        
        prompt = f"""Role: Agente Analista de Probabilidades Esportivas

KNOWLEDGE BASE INTERNO:
- Estatísticas Home Team ({home_team}):
  * Posição: {home_stats.get('Rk', 'N/A')}
  * Gols Marcados: {home_stats.get('GF', 'N/A')}
  * Gols Sofridos: {home_stats.get('GA', 'N/A')}
  * Expected Goals: {home_stats.get('xG', 'N/A')}
  * Expected Goals Against: {home_stats.get('xGA', 'N/A')}

- Estatísticas Away Team ({away_team}):
  * Posição: {away_stats.get('Rk', 'N/A')}
  * Gols Marcados: {away_stats.get('GF', 'N/A')}
  * Gols Sofridos: {away_stats.get('GA', 'N/A')}
  * Expected Goals: {away_stats.get('xG', 'N/A')}
  * Expected Goals Against: {away_stats.get('xGA', 'N/A')}

ODDS DOS MERCADOS:
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
    except Exception as e:
        st.error(f"Erro ao formatar prompt: {str(e)}")
        return None

def main():
    try:
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
        
        # Busca dados do campeonato
        with st.spinner("Carregando dados do campeonato..."):
            st.session_state.load_state = 'loading'
            status_container.info("Carregando dados...")
            
            stats_html = fetch_fbref_data(FBREF_URLS[selected_league]["stats"])
            
            if stats_html:
                team_stats_df = parse_team_stats(stats_html)
                
                if team_stats_df is not None and 'Squad' in team_stats_df.columns:
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
                    
                    # Seção de Mercados e Odds
                    st.markdown("### Odds dos Mercados")
                    
                    with st.expander("Money Line", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            odd_home = st.number_input("Casa (@)", min_value=1.01, value=1.50, format="%.2f", key="ml_home")
                        with col2:
                            odd_draw = st.number_input("Empate (@)", min_value=1.01, value=4.00, format="%.2f", key="ml_draw")
                        with col3:
                            odd_away = st.number_input("Fora (@)", min_value=1.01, value=6.50, format="%.2f", key="ml_away")

                    with st.expander("Over/Under", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            goals_line = st.number_input("Linha", min_value=0.5, value=2.5, step=0.5, format="%.1f")
                        with col2:
                            odd_over = st.number_input(f"Over {goals_line} (@)", min_value=1.01, value=1.85, format="%.2f", key="ou_over")
                        with col3:
                            odd_under = st.number_input(f"Under {goals_line} (@)", min_value=1.01, value=1.95, format="%.2f", key="ou_under")

                    with st.expander("Chance Dupla", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            odd_1x = st.number_input("1X (@)", min_value=1.01, value=1.20, format="%.2f", key="dc_1x")
                        with col2:
                            odd_12 = st.number_input("12 (@)", min_value=1.01, value=1.25, format="%.2f", key="dc_12")
                        with col3:
                            odd_x2 = st.number_input("X2 (@)", min_value=1.01, value=2.40, format="%.2f", key="dc_x2")

                    with st.expander("Ambos Marcam", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            odd_btts_yes = st.number_input("Sim (@)", min_value=1.01, value=1.75, format="%.2f", key="btts_yes")
                        with col2:
                            odd_btts_no = st.number_input("Não (@)", min_value=1.01, value=2.05, format="%.2f", key="btts_no")

# Formata os dados das odds
                    odds_data = f"""Money Line:
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
- Não: @{odd_btts_no:.2f} (Implícita: {(100/odd_btts_no):.1f}%)"""

                    # Botão de análise
                    if st.button("Analisar Partida", type="primary"):
                        with st.spinner("Realizando análise..."):
                            try:
                                # Formata o prompt completo
                                prompt = format_prompt(
                                    team_stats_df,
                                    home_team,
                                    away_team,
                                    odds_data
                                )
                                
                                if prompt:
                                    # Faz a chamada para o GPT-4
                                    response = openai.chat.completions.create(
                                        model="gpt-4o-2024-08-06",
                                        messages=[
                                            {
                                                "role": "system", 
                                                "content": "Você é um Agente Analista de Probabilidades Esportivas especializado. Você DEVE seguir EXATAMENTE o formato de saída especificado no prompt do usuário, preenchendo todos os campos com os valores calculados."
                                            },
                                            {"role": "user", "content": prompt}
                                        ],
                                        temperature=0.3,
                                        max_tokens=4000
                                    )
                                    
                                    analysis = response.choices[0].message.content
                                    
                                    # Mostra o resultado
                                    st.markdown("### Resultado da Análise")
                                    st.markdown(analysis)
                                    
                                    # Botão para baixar análise
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
                                if "openai" in str(e).lower():
                                    st.error("Verifique sua chave da API OpenAI")

    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        st.error("Por favor, recarregue a página e tente novamente.")
        # Log do erro para debug
        st.write("Detalhes do erro (para debug):")
        st.code(str(e))

if __name__ == "__main__":
    main()


