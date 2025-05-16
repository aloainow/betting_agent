# pages/packages.py - Página de Pacotes
import streamlit as st
import logging
from utils.core import (
    show_valuehunter_logo, update_purchase_button, check_payment_success
)
# Configuração de logging
logger = logging.getLogger("valueHunter.packages")

def show_packages_page():
    """Display credit purchase page with improved session handling"""
    try:
        # Esconder a barra lateral e aplicar estilos simplificados
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        
        /* Estilos mais simples com menos aninhamento */
        .simple-card {
            background-color: #1e1e1e;
            border-radius: 12px;
            border: 1px solid #333;
            padding: 25px 20px 20px 20px;
            text-align: center;
            height: 340px;
            margin-bottom: 15px;
        }
        
        .simple-icon {
            font-size: 38px;
            margin-bottom: 12px;
        }
        
        .simple-title {
            font-size: 24px;
            font-weight: bold;
            color: white;
            margin-bottom: 10px;
        }
        
        .simple-price {
            font-size: 32px;
            font-weight: bold;
            color: #fd7014;
            margin-bottom: 10px;
        }
        
        .simple-desc {
            font-size: 16px;
            color: #aaa;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #333;
        }
        
        .feature-list {
            text-align: left;
            padding-top: 5px;
        }
        
        .feature-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 8px;
            color: #ddd;
        }
        
        .check {
            color: #fd7014;
            margin-right: 8px;
        }
        
        /* Estilo botões */
        div.element-container div.row-widget.stButton > button {
            background-color: #fd7014;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            width: 100%;
            padding: 10px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        
        # Botão para voltar
        col_back, col_empty = st.columns([1, 3])
        with col_back:
            if st.button("← Voltar para análises", key="back_to_analysis"):
                try:
                    from utils.data import UserManager
                    st.session_state.user_manager = UserManager()
                    if hasattr(st.session_state, 'user_stats_cache'):
                        del st.session_state.user_stats_cache
                    logger.info(f"Dados recarregados ao voltar para análises: {st.session_state.email}")
                except Exception as e:
                    logger.error(f"Erro ao recarregar dados ao voltar: {str(e)}")
                    
                st.session_state.page = "main"
                st.experimental_rerun()
        
        # Se estamos em uma página especial, mostrar apenas o conteúdo dela
        if check_payment_success():
            return
        
        # Atualizar dados do usuário
        if st.session_state.authenticated and st.session_state.email:
            try:
                from utils.data import UserManager
                st.session_state.user_manager = UserManager()
                if hasattr(st.session_state, 'user_stats_cache'):
                    del st.session_state.user_stats_cache
                logger.info(f"Dados do usuário recarregados na página de pacotes para: {st.session_state.email}")
            except Exception as e:
                logger.error(f"Erro ao atualizar dados do usuário na página de pacotes: {str(e)}")
        
        st.title("Comprar Mais Créditos")
        st.markdown("Adquira mais créditos quando precisar, sem necessidade de mudar de pacote.")
        
        # Mostrar créditos atuais para o usuário ver
        if st.session_state.authenticated and st.session_state.email:
            stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
            st.info(f"💰 Você atualmente tem **{stats['credits_remaining']} créditos** disponíveis em sua conta.")
        
        # Layout em colunas
        col1, col2 = st.columns(2)
        
        # HTML MUITO simplificado para o Pacote Standard
        with col1:
            st.markdown("""
            <div class="simple-card">
                <div class="simple-icon">💼</div>
                <div class="simple-title">30 Créditos</div>
                <div class="simple-price">R$ 19,99</div>
                <div class="simple-desc">Pacote Standard</div>
                <div class="feature-list">
                    <div class="feature-item"><span class="check">✓</span> Análise para múltiplos mercados</div>
                    <div class="feature-item"><span class="check">✓</span> Análises estendidas</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar 30 Créditos", use_container_width=True, key="buy_30c"):
                update_purchase_button(30, 19.99)
        
        # HTML MUITO simplificado para o Pacote Pro
        with col2:
            st.markdown("""
            <div class="simple-card">
                <div class="simple-icon">🚀</div>
                <div class="simple-title">60 Créditos</div>
                <div class="simple-price">R$ 29,99</div>
                <div class="simple-desc">Pacote Pro</div>
                <div class="feature-list">
                    <div class="feature-item"><span class="check">✓</span> Análise para múltiplos mercados</div>
                    <div class="feature-item"><span class="check">✓</span> Melhor custo-benefício</div>
                    <div class="feature-item"><span class="check">✓</span> Análises estendidas</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar 60 Créditos", use_container_width=True, key="buy_60c"):
                update_purchase_button(60, 29.99)
        
        # Add payment instructions
        st.markdown("""
        ### Como funciona o processo de pagamento:
        
        1. Ao clicar em "Comprar Créditos", uma nova janela será aberta para pagamento
        2. Complete seu pagamento na página do Stripe
        3. Após o pagamento, você verá uma mensagem de confirmação
        4. Seus créditos serão adicionados à sua conta imediatamente
        5. Clique em "Voltar para análises" para continuar usando o aplicativo
        
        **Nota:** Todo o processo é seguro e seus dados de pagamento são protegidos pelo Stripe
        """)
        
        # Test mode notice
        if st.session_state.stripe_test_mode:
            st.warning("""
            ⚠️ **Modo de teste ativado**
            
            Use o cartão 4242 4242 4242 4242 com qualquer data futura e CVC para simular um pagamento bem-sucedido.
            """)
        
    except Exception as e:
        logger.error(f"Erro ao exibir página de pacotes: {str(e)}")
        st.error("Erro ao carregar a página de pacotes. Por favor, tente novamente.")
