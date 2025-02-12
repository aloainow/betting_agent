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
    }
}

@st.cache_data(ttl=3600)
def fetch_fbref_data(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        st.error(f"Erro ao buscar dados: {str(e)}")
        return None

def parse_team_stats(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    stats_table = soup.find('table', {'id': 'stats_squads_standard_for'})
    
    if not stats_table:
        return None
    
    df = pd.read_html(str(stats_table))[0]
    return df

def main():
    # Título principal
    st.title("Análise de Apostas Esportivas")
    
    # Sidebar
    st.sidebar.title("Configurações")
    selected_league = st.sidebar.selectbox(
        "Escolha o campeonato:",
        list(FBREF_URLS.keys())
    )
    
    # Busca dados do campeonato selecionado
    with st.spinner("Carregando dados do campeonato..."):
        stats_html = fetch_fbref_data(FBREF_URLS[selected_league]["stats"])
        if stats_html:
            team_stats_df = parse_team_stats(stats_html)
            
            if team_stats_df is not None:
                teams = team_stats_df['Squad'].tolist()
                
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

                # Botão de análise
                if st.button("Analisar Partida", type="primary"):
                    with st.spinner("Realizando análise..."):
                        try:
                            prompt = format_prompt(
                                home_team, 
                                away_team, 
                                team_stats_df,
                                odd_home, odd_draw, odd_away,
                                goals_line, odd_over, odd_under,
                                odd_1x, odd_12, odd_x2,
                                odd_btts_yes, odd_btts_no
                            )
                            
                            response = openai.chat.completions.create(
                                model="gpt-4-0125-preview",
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

if __name__ == "__main__":
    main()
