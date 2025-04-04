# pages/landing.py - Página Inicial
import streamlit as st
import logging
from utils.core import show_valuehunter_logo, go_to_login, go_to_register

# Configuração de logging
logger = logging.getLogger("valueHunter.landing")

def show_landing_page():
    """Display landing page with about content and login/register buttons"""
    try:
        # Aplicar estilos personalizados
        apply_custom_styles()
        # Esconder a barra lateral do Streamlit apenas na página inicial
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Logo e botões de navegação
        col1, col2 = st.columns([5, 1])
        with col1:
            show_valuehunter_logo()
        with col2:
            c1, c2 = st.columns([1, 1], gap="small")
            with c1:
                if st.button("Sign In", key="landing_signin_btn"):
                    go_to_login()
            with c2:
                if st.button("Sign Up", key="landing_signup_btn"):
                    go_to_register()
                
        # Conteúdo principal
        st.markdown("""
            <div class="hero">
                <h1>Maximize o Valor em Apostas Esportivas</h1>
                <p style="color: #FFFFFF;">Identifique oportunidades de valor com precisão matemática e análise de dados avançada.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Seção Sobre - SEM O RETÂNGULO CINZA
        st.markdown('<h2 style="color: #fd7014; margin-bottom: 0.8rem; text-align: left;">Sobre o ValueHunter</h2>', unsafe_allow_html=True)
        
        # Conteúdo da seção sobre
        with st.container():
            st.markdown('<p style="color: #FFFFFF;">O ValueHunter se fundamenta em um princípio crucial: "Ganhar não é sobre escolher o vencedor e sim conseguir o preço certo e depois deixar a variância fazer o trabalho dela."</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">Percebemos que o sucesso nas apostas esportivas não depende de prever corretamente cada resultado individual. Em vez disso, o ValueHunter busca identificar sistematicamente quando existe uma discrepância favorável entre o valor real, calculado pela nossa Engine e o valor implícito, oferecido pelas casas de apostas.</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">ValueHunter opera na interseção entre análise de dados e apostas esportivas. O ValueHunter trabalha para:</p>', unsafe_allow_html=True)
            
            st.markdown("""
            <ol style="color: #FFFFFF;">
                <li>Calcular probabilidades reais de eventos esportivos baseadas em modelos matemáticos e análise de dados</li>
                <li>Comparar essas probabilidades com as odds implícitas oferecidas pelas casas de apostas</li>
                <li>Identificar oportunidades onde existe uma vantagem estatística significativa</li>
            </ol>
            """, unsafe_allow_html=True)
            
            st.markdown('<p style="color: #FFFFFF;">Quando a probabilidade real calculada pelo ValueHunter é maior que a probabilidade implícita nas odds da casa, ele encontra uma "oportunidade" - uma aposta com valor positivo esperado a longo prazo.</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">Esta abordagem reconhece que, embora cada evento individual seja incerto, a matemática da expectativa estatística garante que, com disciplina e paciência suficientes, apostar consistentemente em situações com valor positivo me levará a lucros no longo prazo, desde que o agente de IA esteja calibrado adequadamente.</p>', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF;">Em resumo, meu agente não tenta "vencer o jogo" prevendo resultados individuais, mas sim "vencer o mercado" identificando inconsistências nas avaliações de probabilidade, permitindo que a variância natural do esporte trabalhe a meu favor através de uma vantagem matemática consistente.</p>', unsafe_allow_html=True)
        
        # Botão centralizado
        st.markdown('<div class="btn-container"></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("FAÇA SEU TESTE GRÁTIS", use_container_width=True, key="landing_free_test_btn"):
                go_to_register()
                
        # Footer
        st.markdown("""
            <div class="footer">
                <p style="color: #b0b0b0;">© 2025 ValueHunter. Todos os direitos reservados.</p>
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao exibir página inicial: {str(e)}")
        st.error("Erro ao carregar a página. Por favor, tente novamente.")
        st.write(f"Detalhes do erro: {str(e)}")
