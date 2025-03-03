"""
Admin Panel for ValueHunter
"""
import streamlit as st
import os
import json
from datetime import datetime
import sys

# Adicione o diretório pai ao path para importar os módulos necessários
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessários da aplicação principal
# Dependendo de como você organizou seu código, você pode precisar ajustar estes imports
try:
    from app import show_valuehunter_logo, DATA_DIR, UserManager
except ImportError:
    st.error("Não foi possível importar os módulos necessários do arquivo principal. Verifique a estrutura do projeto.")
    st.stop()

# Configuração da página
st.set_page_config(
    page_title="ValueHunter Admin",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar logger
import logging
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
            
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado em: {user_data_path}")
    except json.JSONDecodeError:
        st.error("Erro ao decodificar arquivo JSON - formato inválido")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
else:
    st.error("Senha incorreta")
