import streamlit as st
import pandas as pd
import openai
from datetime import datetime
import json

# Configuração da página
st.set_page_config(
    page_title="Agente de Apostas Esportivas",
    layout="wide"
)

# Configuração da API OpenAI
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Função para carregar dados dos campeonatos
def load_league_data(league_name):
    try:
        # Aqui você implementará a lógica para carregar os dados do seu banco
        # Por exemplo, usando pandas para ler um CSV ou conexão com banco de dados
        df = pd.read_csv(f"data/{league_name.lower()}.csv")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Função para formatar o prompt com os dados
def format_prompt(home_team, away_team, league_data):
    # Extrai dados relevantes do DataFrame league_data
    # Aqui você implementará a lógica para formatar os dados conforme seu KB
    
    prompt = f"""Role: Agente Analista de Probabilidades Esportivas
    Analise a partida entre {home_team} x {away_team} usando os seguintes dados:
    
    [Dados do Knowledge Base aqui]
    
    {league_data}
    
    Por favor, siga o processo de cálculo e forneça a saída no formato especificado."""
    
    return prompt

# Função para fazer a chamada à API do GPT-4
def get_gpt4_analysis(prompt):
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
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Erro na chamada da API: {str(e)}")
        return None

# Interface principal
def main():
    # Sidebar
    st.sidebar.title("Configurações")
    
    # Seleção de campeonato
    leagues = ["Brasileirão Série A", "Premier League", "La Liga", "Serie A"]
    selected_league = st.sidebar.selectbox("Escolha o campeonato:", leagues)
    
    # Carrega dados do campeonato selecionado
    league_data = load_league_data(selected_league)
    
    if league_data is not None:
        # Lista de times do campeonato
        teams = league_data["team"].unique().tolist()
        
        # Layout principal
        st.title("Análise de Apostas Esportivas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            home_team = st.selectbox("Time da Casa:", teams)
        
        with col2:
            # Remove o time da casa das opções do time visitante
            away_teams = [team for team in teams if team != home_team]
            away_team = st.selectbox("Time Visitante:", away_teams)
        
        if st.button("Analisar Partida"):
            with st.spinner("Realizando análise..."):
                # Formata o prompt com os dados
                prompt = format_prompt(home_team, away_team, league_data)
                
                # Obtém análise do GPT-4
                analysis = get_gpt4_analysis(prompt)
                
                if analysis:
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

if __name__ == "__main__":
    main()
