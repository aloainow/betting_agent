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
        # Esconder a barra lateral na página de pacotes
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        
        # Se estamos em uma página especial, mostrar apenas o conteúdo dela
        if check_payment_success():
            return
        
        # IMPORTANTE: Forçar refresh dos dados do usuário para garantir que os créditos estão atualizados
        if st.session_state.authenticated and st.session_state.email:
            try:
                # Recarregar explicitamente os dados do usuário do disco
                from utils.data import UserManager
                st.session_state.user_manager = UserManager()
                # Limpar qualquer cache que possa existir para estatísticas
                if hasattr(st.session_state, 'user_stats_cache'):
                    del st.session_state.user_stats_cache
                # Log da atualização
                logger.info(f"Dados do usuário recarregados na página de pacotes para: {st.session_state.email}")
            except Exception as e:
                logger.error(f"Erro ao atualizar dados do usuário na página de pacotes: {str(e)}")
        
        st.title("Comprar Mais Créditos")
        st.markdown("Adquira mais créditos quando precisar, sem necessidade de mudar de pacote.")
        
        # Mostrar créditos atuais para o usuário ver
        if st.session_state.authenticated and st.session_state.email:
            stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
            st.info(f"💰 Você atualmente tem **{stats['credits_remaining']} créditos** disponíveis em sua conta.")
        
        # Layout da página de compra
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="credit-card">
                <div class="credit-title">30 Créditos</div>
                <div class="credit-price">R$ 19,99</div>
                <div class="credit-desc">Pacote Standard</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar 30 Créditos", use_container_width=True, key="buy_30c"):
                update_purchase_button(30, 19.99)
        
        with col2:
            st.markdown("""
            <div class="credit-card">
                <div class="credit-title">60 Créditos</div>
                <div class="credit-price">R$ 29,99</div>
                <div class="credit-desc">Pacote Pro</div>
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
        
        # Botão para voltar
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Voltar para análises", key="back_to_analysis", use_container_width=True):
            # IMPORTANTE: Forçar refresh dos dados ao voltar para análises
            try:
                # Recarregar a classe UserManager para garantir dados atualizados
                from utils.data import UserManager
                st.session_state.user_manager = UserManager()
                # Limpar qualquer cache de estatísticas
                if hasattr(st.session_state, 'user_stats_cache'):
                    del st.session_state.user_stats_cache
                logger.info(f"Dados recarregados ao voltar para análises: {st.session_state.email}")
            except Exception as e:
                logger.error(f"Erro ao recarregar dados ao voltar: {str(e)}")
                
            # Mudar a página
            st.session_state.page = "main"
            st.experimental_rerun()
    except Exception as e:
        logger.error(f"Erro ao exibir página de pacotes: {str(e)}")
        st.error("Erro ao carregar a página de pacotes. Por favor, tente novamente.")
