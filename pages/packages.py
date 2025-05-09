# pages/packages.py - Página de Pacotes
import streamlit as st
import logging
from utils.core import (
    show_valuehunter_logo, update_purchase_button, check_payment_success, apply_custom_styles, apply_dark_theme
)
# Configuração de logging
logger = logging.getLogger("valueHunter.packages")

def show_packages_page():
    """Display credit purchase page with improved session handling"""
    try:
        # Aplicar tema escuro
        apply_dark_theme()
        # Aplicar estilos personalizados
        apply_custom_styles()

        # Esconder a barra lateral na página de pacotes
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        
        /* Grid layout para resolver o alinhamento */
        .packages-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-gap: 20px;
            margin-bottom: 20px;
        }
        
        /* Card principal com altura fixa */
        .package-card {
            background-color: #1e1e1e;
            border-radius: 12px;
            border: 1px solid #333;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            height: 380px; /* Altura fixa para uniformidade */
            display: flex;
            flex-direction: column;
        }
        
        /* Cabeçalho do card */
        .package-header {
            padding: 25px 25px 0 25px;
            text-align: center;
        }
        
        .package-icon {
            font-size: 40px;
            margin-bottom: 20px;
        }
        
        .package-title {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 15px;
            color: #ffffff;
        }
        
        .package-price {
            font-size: 32px;
            font-weight: 800;
            color: #fd7014;
            margin-bottom: 15px;
        }
        
        .package-desc {
            font-size: 16px;
            color: #bbbbbb;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #333;
        }
        
        /* Lista de recursos */
        .feature-list {
            padding: 0 25px;
            flex-grow: 1;
        }
        
        .feature-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 10px;
            color: #dddddd;
        }
        
        .feature-check {
            color: #fd7014;
            margin-right: 10px;
            min-width: 15px;
        }
        
        /* Para esconder o excesso de conteúdo */
        div.row-widget.stButton > button {
            width: 100%;
            background-color: #fd7014;
            color: white;
            border: none;
            padding: 12px 0;
            border-radius: 6px;
            font-weight: bold;
            margin-top: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header com a logo
        show_valuehunter_logo()
        
        # Botão para voltar - MOVIDO PARA LOGO ABAIXO DO LOGO
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
        
        # Container para os pacotes (usa uma div em vez de columns do Streamlit)
        st.markdown("""
        <div class="packages-container">
            <div class="package-card">
                <div class="package-header">
                    <div class="package-icon">💼</div>
                    <div class="package-title">30 Créditos</div>
                    <div class="package-price">R$ 19,99</div>
                    <div class="package-desc">Pacote Standard</div>
                </div>
                <div class="feature-list">
                    <div class="feature-item">
                        <span class="feature-check">✓</span> 
                        <span>Análise para mercados simples</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-check">✓</span> 
                        <span>Renovação automática com créditos</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-check">✓</span> 
                        <span>Suporte básico</span>
                    </div>
                </div>
            </div>
            
            <div class="package-card">
                <div class="package-header">
                    <div class="package-icon">🚀</div>
                    <div class="package-title">60 Créditos</div>
                    <div class="package-price">R$ 29,99</div>
                    <div class="package-desc">Pacote Pro</div>
                </div>
                <div class="feature-list">
                    <div class="feature-item">
                        <span class="feature-check">✓</span> 
                        <span>Análise para múltiplos mercados</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-check">✓</span> 
                        <span>Melhor custo-benefício</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-check">✓</span> 
                        <span>Análises estendidas</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-check">✓</span> 
                        <span>Suporte prioritário</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botões de compra (separados dos cards para melhor controle)
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Comprar 30 Créditos", use_container_width=True, key="buy_30c"):
                update_purchase_button(30, 19.99)
        
        with col2:
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
