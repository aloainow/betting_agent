"""
Admin Panel for ValueHunter
"""
import streamlit as st
import os
import json
from datetime import datetime
import sys
import logging

# Configuração da página
st.set_page_config(
    page_title="ValueHunter Admin",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar funções necessárias
try:
    from utils.core import show_valuehunter_logo, DATA_DIR
    from utils.data import UserManager
except ImportError:
    st.error("Não foi possível importar os módulos necessários. Verifique a estrutura do projeto.")
    st.stop()

# Inicializar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("valueHunter.admin")

# Senha de administrador
ADMIN_PASSWORD = "nabundinha1"  # Altere para sua senha

# Header 
show_valuehunter_logo()
st.title("Painel Administrativo")

# Verificação de senha
password = st.text_input("Senha de Administrador", type="password")

if password == ADMIN_PASSWORD:
    st.success("Acesso autorizado!")
    
    # Carregar dados dos usuários
    user_data_path = os.path.join(DATA_DIR, "user_data.json")
    
    try:
        with open(user_data_path, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
            
        # Seção 1: Download
        st.header("Gerenciamento de Dados")
        with open(user_data_path, 'r', encoding='utf-8') as f:
            data = f.read()
            
        st.download_button(
            "Baixar Dados de Usuários", 
            data, 
            "user_data.json", 
            "application/json"
        )
        
        # Mostrar estatísticas dos usuários
        st.header("Estatísticas do Sistema")
        
        num_users = len(users_data)
        st.metric("Total de Usuários", num_users)
        
        # Distribuição por tipo
        tier_counts = {}
        for email, user in users_data.items():
            tier = user.get('tier', 'desconhecido')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
        # Mostrar distribuição em texto
        col1, col2, col3 = st.columns(3)
        for i, (tier, count) in enumerate(tier_counts.items()):
            col = [col1, col2, col3][i % 3]
            with col:
                st.metric(f"Pacote {tier.capitalize()}", count)
        
        # Informações de armazenamento
        st.header("Informações de Armazenamento")
        st.write(f"📁 Diretório de dados: `{DATA_DIR}`")
        
        if os.path.exists(DATA_DIR):
            files = os.listdir(DATA_DIR)
            st.write(f"Arquivos encontrados: {len(files)}")
            
            # Tabela de arquivos
            file_data = []
            for file in files:
                file_path = os.path.join(DATA_DIR, file)
                file_size = os.path.getsize(file_path) / 1024  # KB
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_data.append({
                    "Nome": file,
                    "Tamanho (KB)": f"{file_size:.2f}",
                    "Modificado": modified_time.strftime("%Y-%m-%d %H:%M")
                })
            
            # Exibir como dataframe
            if file_data:
                st.dataframe(file_data)
        else:
            st.warning("Diretório de dados não encontrado!")
            
        # Lista de usuários
        st.header("Lista de Usuários")
        
        for email, user in users_data.items():
            tier = user.get('tier', 'desconhecido')
            name = user.get('name', email.split('@')[0])
            credits = user.get('purchased_credits', 0)
            
            # Formatar como uma linha com emoji
            tier_emoji = "🆓" if tier == "free" else "💎"
            st.write(f"{tier_emoji} **{name}** ({email}) - Pacote: {tier.capitalize()}, Créditos: {credits}")

        # Sessão 4: Estatísticas de Análise
        st.header("Estatísticas de Análise")
        
        # Coletar dados de análise
        all_analyses = []
        for email, user_data in users_data.items():
            if "usage" in user_data and "total" in user_data["usage"]:
                for usage in user_data["usage"]["total"]:
                    if "league" in usage:  # Verificar se contém dados detalhados
                        # Adicionar email do usuário aos dados
                        analysis = usage.copy()
                        analysis["email"] = email
                        all_analyses.append(analysis)
        
        if all_analyses:
            st.write(f"Total de análises detalhadas registradas: {len(all_analyses)}")
            
            # Estatísticas por liga
            leagues = {}
            for analysis in all_analyses:
                league = analysis.get("league", "Desconhecido")
                if league in leagues:
                    leagues[league] += 1
                else:
                    leagues[league] = 1
            
            # Times mais analisados
            teams = {}
            for analysis in all_analyses:
                home = analysis.get("home_team", "")
                away = analysis.get("away_team", "")
                
                for team in [home, away]:
                    if team:
                        if team in teams:
                            teams[team] += 1
                        else:
                            teams[team] = 1
            
            # Mercados mais utilizados
            markets = {}
            for analysis in all_analyses:
                for market in analysis.get("markets_used", []):
                    if market in markets:
                        markets[market] += 1
                    else:
                        markets[market] = 1
            
            # Exibir estatísticas em tabs
            tab1, tab2, tab3 = st.tabs(["Ligas", "Times", "Mercados"])
            
            with tab1:
                st.subheader("Ligas Mais Analisadas")
                if leagues:
                    # Ordenar por uso
                    sorted_leagues = dict(sorted(leagues.items(), 
                                           key=lambda x: x[1], reverse=True))
                    
                    # Criar gráfico ou lista
                    for league, count in sorted_leagues.items():
                        st.metric(league, count)
                else:
                    st.info("Nenhuma análise de liga registrada ainda.")
            
            with tab2:
                st.subheader("Times Mais Analisados")
                if teams:
                    # Mostrar top 10 times
                    top_teams = dict(sorted(teams.items(), 
                                    key=lambda x: x[1], reverse=True)[:10])
                    
                    # Exibir como barras horizontais ou métricas
                    for team, count in top_teams.items():
                        st.metric(team, count)
                else:
                    st.info("Nenhuma análise de time registrada ainda.")
            
            with tab3:
                st.subheader("Mercados Mais Utilizados")
                if markets:
                    market_names = {
                        "money_line": "Money Line (1X2)",
                        "over_under": "Over/Under Gols",
                        "chance_dupla": "Chance Dupla",
                        "ambos_marcam": "Ambos Marcam",
                        "escanteios": "Total de Escanteios",
                        "cartoes": "Total de Cartões"
                    }
                    
                    # Ordenar por uso
                    sorted_markets = dict(sorted(markets.items(), 
                                         key=lambda x: x[1], reverse=True))
                    
                    # Exibir métricas
                    for market_key, count in sorted_markets.items():
                        market_name = market_names.get(market_key, market_key)
                        st.metric(market_name, count)
                else:
                    st.info("Nenhuma análise de mercado registrada ainda.")
            
            # Análises recentes
            with st.expander("Análises Recentes"):
                # Ordenar por timestamp (mais recentes primeiro)
                recent = sorted(all_analyses, 
                               key=lambda x: x.get("timestamp", ""), 
                               reverse=True)[:20]
                
                for idx, analysis in enumerate(recent):
                    # Formatar como cartão
                    timestamp = datetime.fromisoformat(analysis.get("timestamp", "")).strftime("%d/%m/%Y %H:%M")
                    league = analysis.get("league", "Liga desconhecida")
                    home = analysis.get("home_team", "Time casa")
                    away = analysis.get("away_team", "Time visitante")
                    markets_used = ", ".join(analysis.get("markets_used", []))
                    
                    st.markdown(f"""
                    **Análise #{idx+1}** - {timestamp}
                    - **Liga:** {league}
                    - **Partida:** {home} x {away}
                    - **Mercados:** {markets_used}
                    - **Usuário:** {analysis.get("email")}
                    ---
                    """)
        else:
            st.info("Ainda não há dados detalhados de análise disponíveis. As novas análises serão registradas com detalhes.")
            
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado em: {user_data_path}")
    except json.JSONDecodeError:
        st.error("Erro ao decodificar arquivo JSON - formato inválido")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
else:
    st.error("Senha incorreta")
