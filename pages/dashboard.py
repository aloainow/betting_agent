# pages/dashboard.py - Versão de diagnóstico simplificada
import streamlit as st
import logging
import traceback
import os
import json
from datetime import datetime

# Configuração de logging aprimorada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dashboard_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("valueHunter.dashboard_debug")

def show_main_dashboard():
    """Versão mínima para diagnóstico"""
    try:
        # Título para diagnóstico
        st.title("Diagnóstico - Dashboard")
        
        # Exibir informações de ambiente
        st.header("1. Informações de Ambiente")
        
        # Exibir informações da sessão
        st.subheader("Variáveis da sessão")
        
        # Criar tabela com variáveis da sessão
        session_vars = []
        for key in st.session_state:
            # Evitar mostrar objetos grandes
            if key in ['user_manager', 'stats_html', 'team_stats_df']:
                val = f"<objeto {type(st.session_state[key]).__name__}>"
            else:
                try:
                    val = str(st.session_state[key])
                    if len(val) > 100:
                        val = val[:100] + "..."
                except:
                    val = "<não representável>"
                    
            session_vars.append({"Chave": key, "Valor": val})
            
        if session_vars:
            st.dataframe(session_vars)
        else:
            st.warning("Nenhuma variável encontrada na sessão.")
        
        # Exibir query params
        st.subheader("Query Parameters")
        st.json(dict(st.query_params))
        
        # Verificar diretórios
        st.header("2. Verificação de Diretórios")
        
        # Verificar o diretório DATA_DIR
        try:
            from utils.core import DATA_DIR
            st.write(f"DATA_DIR = {DATA_DIR}")
            
            if os.path.exists(DATA_DIR):
                st.success(f"✅ Diretório DATA_DIR existe: {DATA_DIR}")
                
                # Listar arquivos
                files = os.listdir(DATA_DIR)
                st.write(f"Arquivos em DATA_DIR ({len(files)}):")
                for f in files:
                    fpath = os.path.join(DATA_DIR, f)
                    fsize = os.path.getsize(fpath)
                    fmod = datetime.fromtimestamp(os.path.getmtime(fpath))
                    st.write(f"- {f} ({fsize} bytes, modificado em {fmod})")
            else:
                st.error(f"❌ Diretório DATA_DIR não existe: {DATA_DIR}")
        except Exception as e:
            st.error(f"Erro ao verificar DATA_DIR: {str(e)}")
            st.code(traceback.format_exc())
        
        # Verificar acesso ao FBref
        st.header("3. Teste de Importações")
        
        # Testar imports
        imports_to_test = [
            "from utils.data import FBREF_URLS",
            "from utils.data import fetch_fbref_data",
            "from utils.data import parse_team_stats",
            "from utils.data import get_odds_data",
            "from utils.ai import analyze_with_gpt",
            "from utils.ai import format_prompt",
            "from utils.core import show_valuehunter_logo"
        ]
        
        for imp in imports_to_test:
            try:
                exec(imp)
                st.success(f"✅ Import bem-sucedido: {imp}")
            except Exception as e:
                st.error(f"❌ Erro ao importar: {imp}")
                st.write(f"Erro: {str(e)}")
        
        # Teste simplificado de seleção de liga
        st.header("4. Teste Simples de Seleção de Liga")
        
        try:
            # Teste 1: Seleção de liga com Streamlit nativo
            from utils.data import FBREF_URLS
            available_leagues = list(FBREF_URLS.keys())
            
            st.subheader("4.1 Seleção com componente nativo")
            league = st.selectbox(
                "Selecione uma liga (teste):",
                available_leagues,
                key="test_league"
            )
            st.write(f"Liga selecionada: {league}")
            
            # Teste 2: Formulário HTML simples
            st.subheader("4.2 Seleção com HTML")
            html = f"""
            <form method="get" action="" id="test_form">
                <select name="test_league" id="test_league" onchange="this.form.submit()">
                    {" ".join([f'<option value="{l}" {"selected" if l == st.query_params.get("test_league", "") else ""}>{l}</option>' for l in available_leagues])}
                </select>
            </form>
            """
            st.markdown(html, unsafe_allow_html=True)
            
            if "test_league" in st.query_params:
                st.write(f"Liga selecionada via HTML: {st.query_params.test_league}")
                
        except Exception as e:
            st.error(f"Erro no teste de seleção: {str(e)}")
            st.code(traceback.format_exc())
        
        # Teste de carregamento de times
        st.header("5. Teste de Carregamento de Times")
        
        # Liga para teste
        test_league = "Premier League"  # Liga fixa para teste
        
        try:
            st.subheader(f"5.1 Teste com {test_league}")
            if st.button("Carregar times da Premier League (teste)"):
                st.info(f"Tentando carregar times para {test_league}...")
                
                # Importar função de carregamento
                from utils.data import fetch_fbref_data, parse_team_stats
                
                # Pegar URL
                from utils.data import FBREF_URLS
                stats_url = FBREF_URLS[test_league].get("stats")
                
                if stats_url:
                    st.write(f"URL: {stats_url}")
                    
                    # Buscar HTML
                    with st.spinner("Buscando dados..."):
                        stats_html = fetch_fbref_data(stats_url)
                    
                    if stats_html:
                        st.success(f"HTML obtido: {len(stats_html)} caracteres")
                        
                        # Parsear times
                        with st.spinner("Processando dados..."):
                            team_stats_df = parse_team_stats(stats_html)
                        
                        if team_stats_df is not None and 'Squad' in team_stats_df.columns:
                            teams = team_stats_df['Squad'].dropna().unique().tolist()
                            st.success(f"Times encontrados: {len(teams)}")
                            st.write(teams)
                        else:
                            st.error("Não foi possível extrair times do DataFrame")
                            if team_stats_df is not None:
                                st.write(f"Colunas disponíveis: {team_stats_df.columns.tolist()}")
                            else:
                                st.error("DataFrame é None")
                    else:
                        st.error("Falha ao obter HTML")
                else:
                    st.error(f"URL não encontrada para {test_league}")
                
        except Exception as e:
            st.error(f"Erro no teste de carregamento: {str(e)}")
            st.code(traceback.format_exc())
        
        # Criar botão para logs
        st.header("6. Logs")
        if os.path.exists("dashboard_debug.log"):
            with open("dashboard_debug.log", "r") as f:
                logs = f.readlines()
                # Mostrar últimas 20 linhas
                st.code("".join(logs[-20:]))
        else:
            st.warning("Arquivo de log não encontrado")
            
    except Exception as e:
        st.error(f"Erro global no diagnóstico: {str(e)}")
        st.code(traceback.format_exc())
