"""
Admin Panel for ValueHunter
"""
import streamlit as st
import os
import json
from datetime import datetime
import sys
import logging
import random
import string

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
    
    # Nova seção - Botão de atualização da página
    refresh_col1, refresh_col2 = st.columns([3, 1])
    with refresh_col2:
        if st.button("🔄 Atualizar Página", use_container_width=True):
            st.experimental_rerun()
   
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
            verified = "✓" if user.get('verified', False) else "✗"
            
            # Formatar como uma linha com emoji
            tier_emoji = "🆓" if tier == "free" else "💎"
            st.write(f"{tier_emoji} **{name}** ({email}) - Pacote: {tier.capitalize()}, Créditos: {credits}, Verificado: {verified}")

        # Adicionar seção de gerenciamento de cache
        st.header("Gerenciamento de Cache")
        
        # Importar a função de limpeza de cache
        try:
            from pages.dashboard import clear_cache
            
            # Adicionar opções de limpeza
            cache_col1, cache_col2, cache_col3 = st.columns(3)
            
            with cache_col1:
                if st.button("🧹 Limpar Todo o Cache", type="primary", use_container_width=True):
                    num_cleared = clear_cache()
                    st.success(f"✅ Cache limpo com sucesso! {num_cleared} arquivos removidos.")
                    st.info("O cache incluía arquivos de times, estatísticas e requisições API.")
            
            with cache_col2:
                # Botão para limpar apenas cache de times
                if st.button("🧹 Limpar Cache de Times", use_container_width=True):
                    import os
                    import glob
                    from utils.core import DATA_DIR
                    
                    # Diretório de cache de times
                    teams_cache_dir = os.path.join(DATA_DIR, "teams_cache")
                    cleared = 0
                    
                    if os.path.exists(teams_cache_dir):
                        for cache_file in glob.glob(os.path.join(teams_cache_dir, "*.json")):
                            try:
                                os.remove(cache_file)
                                cleared += 1
                            except Exception as e:
                                logger.error(f"Erro ao remover {cache_file}: {str(e)}")
                    
                    st.success(f"✅ Cache de times limpo: {cleared} arquivos removidos.")
            
            with cache_col3:
                # Botão para limpar cache de uma liga específica
                from utils.footystats_api import get_user_selected_leagues_direct, clear_league_cache
                leagues = get_user_selected_leagues_direct()
                
                selected_league = st.selectbox("Selecione uma liga", options=leagues)
                
                if st.button("🧹 Limpar Cache desta Liga", use_container_width=True):
                    try:
                        num_cleared = clear_league_cache(selected_league)
                        st.success(f"✅ Cache da liga {selected_league} limpo: {num_cleared} arquivos removidos.")
                    except Exception as e:
                        st.error(f"Erro ao limpar cache da liga: {str(e)}")
            
            # Adicionar informações sobre o cache
            st.info("""
            **Informações sobre o Cache:**
            - A limpeza do cache força o sistema a buscar dados atualizados.
            - Útil quando houver erros ou quando quiser garantir dados recentes.
            - O cache de times armazena listas de times por liga.
            - O cache de requisições armazena respostas da API FootyStats.
            
            **Observação:** Após limpar o cache, pode haver um pequeno atraso na próxima execução enquanto os dados são recarregados.
            """)
        except ImportError as e:
            st.error(f"Não foi possível importar a função de limpeza de cache: {str(e)}")
            st.info("Verifique se a função clear_cache está disponível no módulo 'pages.dashboard'.")
        # Nova seção: Gerenciamento de Usuários
        st.header("Gerenciamento de Usuários")

        # Subsection: Gerenciar Créditos
        with st.expander("Adicionar Créditos a Usuário", expanded=True):
            # Criar uma lista de emails para o selectbox
            user_emails = list(users_data.keys())
            
            # Dropdown para selecionar usuário
            selected_user = st.selectbox("Selecionar Usuário", user_emails)
            
            # Campo para quantidade de créditos
            credit_amount = st.number_input("Quantidade de Créditos", min_value=1, max_value=1000, value=10)
            
            # Botão para adicionar créditos
            if st.button("Adicionar Créditos", key="add_credits_button"):
                try:
                    # Inicializar UserManager
                    user_manager = UserManager()
                    
                    # Adicionar créditos
                    if user_manager.add_credits(selected_user, credit_amount):
                        st.success(f"{credit_amount} créditos adicionados com sucesso para {selected_user}")
                        
                        # Recarregar dados após adição
                        with open(user_data_path, 'r', encoding='utf-8') as f:
                            users_data = json.load(f)
                    else:
                        st.error(f"Falha ao adicionar créditos para {selected_user}")
                except Exception as e:
                    st.error(f"Erro ao adicionar créditos: {str(e)}")

        # Subsection: Excluir Usuário
        with st.expander("Excluir Usuário", expanded=False):
            # Dropdown para selecionar usuário para exclusão
            user_to_delete = st.selectbox("Selecionar Usuário para Excluir", user_emails, key="delete_user_select")
            
            # Confirmação e botão de exclusão
            confirm_delete = st.checkbox("Confirmo que desejo excluir permanentemente esta conta")
            
            if st.button("Excluir Usuário", type="primary", disabled=not confirm_delete):
                try:
                    # Remover usuário do dicionário
                    if user_to_delete in users_data:
                        del users_data[user_to_delete]
                        
                        # Salvar arquivo atualizado
                        with open(user_data_path, 'w', encoding='utf-8') as f:
                            json.dump(users_data, f, indent=2)
                        
                        st.success(f"Usuário {user_to_delete} excluído com sucesso")
                        
                        # Atualizar a lista de emails no selectbox
                        st.experimental_rerun()
                    else:
                        st.error(f"Usuário {user_to_delete} não encontrado")
                except Exception as e:
                    st.error(f"Erro ao excluir usuário: {str(e)}")

        # Adicione também uma seção para resetar créditos e verificação
        with st.expander("Operações em Lote", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Resetar Créditos de Todos", type="secondary"):
                    try:
                        # Inicializar UserManager
                        user_manager = UserManager()
                        
                        # Iterar sobre todos os usuários
                        for email in users_data:
                            # Resetar créditos
                            users_data[email]["free_credits_exhausted_at"] = None
                            users_data[email]["paid_credits_exhausted_at"] = None
                            users_data[email]["usage"] = {"daily": [], "total": []}
                        
                        # Salvar alterações
                        with open(user_data_path, 'w', encoding='utf-8') as f:
                            json.dump(users_data, f, indent=2)
                        
                        st.success("Créditos resetados para todos os usuários")
                    except Exception as e:
                        st.error(f"Erro ao resetar créditos: {str(e)}")
            
            with col2:
                if st.button("Resetar Verificação de Todos", type="secondary"):
                    try:
                        # Iterar sobre todos os usuários
                        for email in users_data:
                            # Resetar verificação
                            users_data[email]["verified"] = False
                            # Gerar novo código de verificação
                            users_data[email]["verification_code"] = ''.join(random.choices(string.digits, k=6))
                        
                        # Salvar alterações
                        with open(user_data_path, 'w', encoding='utf-8') as f:
                            json.dump(users_data, f, indent=2)
                        
                        st.success("Status de verificação resetado para todos os usuários")
                    except Exception as e:
                        st.error(f"Erro ao resetar verificação: {str(e)}")

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
