# Standard library imports
import os
import json
import hashlib
import time
import re
import traceback
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

# Third party imports
import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from openai import OpenAI, OpenAIError


# Definição das URLs do FBref
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
    },
    "Bundesliga": {
        "stats": "https://fbref.com/en/comps/20/Bundesliga-Stats",
        "fixtures": "https://fbref.com/en/comps/20/schedule/Bundesliga-Scores-and-Fixtures"
    },
    "Ligue 1": {
        "stats": "https://fbref.com/en/comps/13/Ligue-1-Stats",
        "fixtures": "https://fbref.com/en/comps/13/schedule/Ligue-1-Scores-and-Fixtures"
    },
    "Champions League": {
        "stats": "https://fbref.com/en/comps/8/Champions-League-Stats",
        "fixtures": "https://fbref.com/en/comps/8/schedule/Champions-League-Scores-and-Fixtures"
    }
}


@dataclass
class UserTier:
    name: str
    total_credits: int  # Total credits in package
    market_limit: int   # Limit of markets per analysis

# Função init_session_state deve vir ANTES da classe UserManager
def init_session_state():
    """Initialize session state variables"""
    if "page" not in st.session_state:
        st.session_state.page = "landing"  # Nova variável para controlar a página atual
        
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "email" not in st.session_state:
        st.session_state.email = None
    
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = datetime.now()
    elif (datetime.now() - st.session_state.last_activity).total_seconds() > 3600:  # 1 hora
        st.session_state.authenticated = False
        st.session_state.email = None
        st.warning("Sua sessão expirou. Por favor, faça login novamente.")
    
    # Variáveis para a página de landing
    if "show_register" not in st.session_state:
        st.session_state.show_register = False
    
    # UserManager deve ser o último a ser inicializado
    if "user_manager" not in st.session_state:
        st.session_state.user_manager = UserManager()
    
    # Atualizar timestamp de última atividade
    st.session_state.last_activity = datetime.now()
    
def go_to_login():
    """Navigate to login page"""
    st.session_state.page = "login"
    st.session_state.show_register = False
    st.experimental_rerun()

def go_to_register():
    """Navigate to register page"""
    st.session_state.page = "register"
    st.session_state.show_register = True
    st.experimental_rerun()

def go_to_landing():
    """Navigate to landing page"""
    st.session_state.page = "landing"
    st.experimental_rerun()

def show_landing_page():
    """Display landing page with about content and login/register buttons"""
    # Custom CSS para a página de landing
    st.markdown("""
        <style>
            body {
                background-color: #3F3F45;
                color: #FFFFFF;
            }
            .landing-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            .navbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1.5rem;
            }
            .logo {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .logo-text {
                font-size: 2.5rem !important;
                font-weight: bold;
                color: #FFFFFF;
            }
            .logo-v {
                color: #3F3F45;
                font-size: 3rem !important;
                font-weight: bold;
            }
            .logo-container {
                background-color: #fd7014;
                padding: 12px 25px !important;
                border-radius: 8px;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            .hero {
                margin: 2rem 0;
                text-align: left;
            }
            .hero h1 {
                font-size: 2.8rem;
                color: #fd7014;
                margin-bottom: 1rem;
            }
            .hero p {
                font-size: 1.25rem;
                color: #FFFFFF;
                max-width: 90%;
                margin-left: 0;
            }
            .about-content {
                max-width: 90%;
                margin-left: 0;
                line-height: 1.6;
                margin-top: 2rem;
                margin-bottom: 2rem;
            }
            .about-content h2 {
                color: #fd7014;
                margin-bottom: 0.8rem;
                text-align: left;
            }
            .footer {
                margin-top: 2rem;
                text-align: center;
                color: #b0b0b0;
            }
            .btn-container {
                display: flex;
                justify-content: flex-start;
                gap: 20px;
                margin-top: 1.5rem;
            }
            p, li {
                color: #FFFFFF !important;
            }
            /* Estilo para TODOS os botões - LARANJA COM TEXTO BRANCO */
            div.stButton > button {
                background-color: #fd7014 !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 4px;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }
            
            div.stButton > button:hover {
                background-color: #27272a !important; /* Cinza escuro no hover */
                color: white !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Logo e botões de navegação
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown('<div class="logo-container"><span class="logo-v">V</span><span class="logo-text">ValueHunter</span></div>', unsafe_allow_html=True)
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
def show_login():
    """Display login form"""
    # Header com a logo - MAIOR
    st.markdown('<div class="logo-container" style="width: fit-content; padding: 12px 25px;"><span class="logo-v" style="font-size: 3rem;">V</span><span class="logo-text" style="font-size: 2.5rem;">ValueHunter</span></div>', unsafe_allow_html=True)
    st.title("Login")
    
    # Botão para voltar à página inicial
    if st.button("← Voltar para a página inicial"):
        go_to_landing()
    
    # Login form
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if st.session_state.user_manager.authenticate(email, password):
                st.session_state.authenticated = True
                st.session_state.email = email
                st.success("Login successful!")
                st.session_state.page = "main"  # Ir para a página principal
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
    
    # Registration link
    st.markdown("---")
    st.markdown("<div style='text-align: center;'>Não tem uma conta?</div>", unsafe_allow_html=True)
    if st.button("Registre-se aqui", use_container_width=True):
        go_to_register()
def show_register():
    """Display registration form"""
    # Header com a logo - MAIOR
    st.markdown('<div class="logo-container" style="width: fit-content; padding: 12px 25px;"><span class="logo-v" style="font-size: 3rem;">V</span><span class="logo-text" style="font-size: 2.5rem;">ValueHunter</span></div>', unsafe_allow_html=True)
    st.title("Register")
    
    # Botão para voltar à página inicial
    if st.button("← Voltar para a página inicial"):
        go_to_landing()
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
        with col2:
            st.markdown("### Pacotes Disponíveis")
            st.markdown("🔒 **Free:** 5 créditos (renovação a cada 24h), múltiplos mercados")
            st.markdown("⭐ **Standard:** 30 créditos por R$19,99")
            st.markdown("💎 **Pro:** 60 créditos por R$29,99")
            tier = st.selectbox("Selecione seu Pacote", ["free", "standard", "pro"])
        
        submitted = st.form_submit_button("Register")
        
        if submitted:
            success, message = st.session_state.user_manager.register_user(email, password, tier)
            if success:
                st.success(message)
                st.session_state.page = "login"
                st.session_state.show_register = False
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error(message)
    
    st.markdown("---")
    st.markdown("<div style='text-align: center;'>Já tem uma conta?</div>", unsafe_allow_html=True)
    if st.button("Fazer login", use_container_width=True):
        go_to_login()
def show_packages_page():
    """Display credit packages page for subscription options"""
    # Header com a logo
    st.markdown('<div class="logo-container" style="width: fit-content; padding: 12px 25px;"><span class="logo-v" style="font-size: 3rem;">V</span><span class="logo-text" style="font-size: 2.5rem;">ValueHunter</span></div>', unsafe_allow_html=True)
    
    st.title("Pacotes de Créditos")
    st.markdown("Escolha o pacote que melhor atende às suas necessidades de análises esportivas.")
    
    # Obter informações do usuário atual
    user_stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
    current_package = user_stats['tier']
    
    # CSS simplificado para os cartões de pacotes
    st.markdown("""
    <style>
        .package-card {
            background-color: #FFFFFF;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .package-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #222831;
        }
        .package-price {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #222831;
        }
        .package-credits {
            font-size: 18px;
            margin-bottom: 20px;
            color: #222831;
        }
        .package-desc {
            margin-bottom: 20px;
            color: #222831;
            text-align: left;
        }
        .popular-tag {
            background-color: #e44d87;
            color: white;
            font-size: 14px;
            font-weight: bold;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Layout dos pacotes usando colunas
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("""
        <div class="package-card" style="border-top: 4px solid #e44d87;">
            <div class="package-title">Free</div>
            <div class="package-price">Grátis</div>
            <div class="package-credits">5 créditos</div>
            <div class="package-desc">
                • Renovação a cada 24h<br>
                • Múltiplos mercados<br>
                • Acesso à análise básica<br>
                • Suporte ao cliente
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if current_package == 'free':
            st.info("Seu pacote atual")
        else:
            if st.button("Selecionar Pacote Free", key="select_free"):
                st.session_state.user_manager._downgrade_to_free(st.session_state.email)
                st.success("Alterado para Pacote Free com sucesso!")
                time.sleep(1)
                st.experimental_rerun()

    with col2:
        st.markdown("""
        <div class="package-card" style="border-top: 4px solid #0077b6;">
            <div class="popular-tag">Popular</div>
            <div class="package-title">Standard</div>
            <div class="package-price">R$ 19,99</div>
            <div class="package-credits">30 créditos</div>
            <div class="package-desc">
                • Único pagamento<br>
                • Múltiplos mercados<br>
                • Análise avançada<br>
                • Suporte prioritário
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if current_package == 'standard':
            st.info("Seu pacote atual")
        else:
            if st.button("Selecionar Pacote Standard", key="select_standard"):
                st.session_state.user_manager._upgrade_to_standard(st.session_state.email)
                st.success("Alterado para Pacote Standard com sucesso!")
                time.sleep(1)
                st.experimental_rerun()

    with col3:
        st.markdown("""
        <div class="package-card" style="border-top: 4px solid #0abab5;">
            <div class="package-title">Pro</div>
            <div class="package-price">R$ 29,99</div>
            <div class="package-credits">60 créditos</div>
            <div class="package-desc">
                • Único pagamento<br>
                • Múltiplos mercados<br>
                • Análise premium<br>
                • Suporte VIP<br>
                • Dados históricos completos
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if current_package == 'pro':
            st.info("Seu pacote atual")
        else:
            if st.button("Selecionar Pacote Pro", key="select_pro"):
                st.session_state.user_manager._upgrade_to_pro(st.session_state.email)
                st.success("Alterado para Pacote Pro com sucesso!")
                time.sleep(1)
                st.experimental_rerun()
    
    # Pacotes de recarga
    st.markdown("## Comprar Mais Créditos")
    st.markdown("Adquira mais créditos quando precisar, sem necessidade de mudar de pacote.")
    
    recharge_col1, recharge_col2 = st.columns(2)
    
    with recharge_col1:
        st.markdown("""
        <div class="package-card" style="border: 2px solid #0077b6;">
            <div class="package-title">30 Créditos</div>
            <div class="package-price">R$ 19,99</div>
            <div style="color: #0077b6; margin-top: 10px;">Pacote Padrão</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Comprar 30 Créditos", key="buy_30c"):
            if st.session_state.user_manager.add_credits(st.session_state.email, 30):
                st.success("30 créditos adicionados!")
                time.sleep(1)
                st.experimental_rerun()
    
    with recharge_col2:
        st.markdown("""
        <div class="package-card" style="border: 2px solid #0abab5;">
            <div class="package-title">60 Créditos</div>
            <div class="package-price">R$ 29,99</div>
            <div style="color: #0abab5; margin-top: 10px;">Melhor custo-benefício</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Comprar 60 Créditos", key="buy_60c"):
            if st.session_state.user_manager.add_credits(st.session_state.email, 60):
                st.success("60 créditos adicionados!")
                time.sleep(1)
                st.experimental_rerun()
    
    # Botão para voltar
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Voltar para análises", key="back_to_analysis"):
        st.session_state.page = "main"
        st.experimental_rerun()
def show_usage_stats():
    """Display usage statistics"""
    stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
    
    st.sidebar.markdown("### Estatísticas de Uso")
    st.sidebar.markdown(f"**Pacote Atual:** {stats['tier_display']}")
    st.sidebar.markdown(f"**Créditos Restantes:** {stats['credits_remaining']}")
    
    # Add progress bar for credits
    if stats['credits_total'] > 0:
        progress = stats['credits_used'] / stats['credits_total']
        st.sidebar.progress(min(progress, 1.0))
    
    # Package descriptions
    if stats['tier'] == 'free':
        info_text = "🔒 **Pacote Free:**\n- 5 créditos\n- Múltiplos mercados por análise"
        
        # Show renewal info if credits exhausted
        if stats.get('next_free_credits_time'):
            info_text += f"\n- Renovação em: {stats['next_free_credits_time']}"
        elif stats.get('free_credits_reset'):
            info_text += "\n- ✅ Créditos renovados!"
            
        st.sidebar.info(info_text)
        
        # Show upgrade button if credits are low
        if stats['credits_remaining'] < 2:
            if st.sidebar.button("🚀 Fazer Upgrade", key="upgrade_button", use_container_width=True):
                st.session_state.page = "packages"
                st.experimental_rerun()
                
    elif stats['tier'] == 'standard':
        st.sidebar.info("⭐ **Pacote Standard:**\n- 30 créditos\n- Múltiplos mercados por análise")
        
        # Show days remaining info if in 7-day grace period
        if stats.get('days_until_downgrade'):
            st.sidebar.warning(f"⚠️ Seus créditos acabaram! Você será automaticamente rebaixado para o pacote Free em {stats['days_until_downgrade']} dias se não comprar mais créditos.")
        
    elif stats['tier'] == 'pro':
        st.sidebar.success("💎 **Pacote Pro:**\n- 60 créditos\n- Múltiplos mercados por análise")
        
        # Show days remaining info if in 7-day grace period
        if stats.get('days_until_downgrade'):
            st.sidebar.warning(f"⚠️ Seus créditos acabaram! Você será automaticamente rebaixado para o pacote Free em {stats['days_until_downgrade']} dias se não comprar mais créditos.")
    
    # Show purchase button when credits are low for paid tiers
    if stats['tier'] != 'free' and stats['credits_remaining'] < 10:
        if st.sidebar.button("📦 Comprar Mais Créditos", key="buy_more_credits"):
            st.sidebar.markdown("### Pacotes de Créditos")
            
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("30 Créditos - R$19,99", key="buy_30"):
                    st.session_state.user_manager.add_credits(st.session_state.email, 30)
                    st.success("30 créditos adicionados!")
                    time.sleep(1)
                    st.experimental_rerun()
            
            with col2:
                if st.button("60 Créditos - R$29,99", key="buy_60"):
                    st.session_state.user_manager.add_credits(st.session_state.email, 60)
                    st.success("60 créditos adicionados!")
                    time.sleep(1)
                    st.experimental_rerun()

def check_analysis_limits(selected_markets):
    """Check if user can perform analysis with selected markets"""
    num_markets = sum(1 for v in selected_markets.values() if v)
    stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
    
    # Check if user has enough credits
    remaining_credits = stats['credits_remaining']
    
    if num_markets > remaining_credits:
        # Special handling for Free tier
        if stats['tier'] == 'free':
            st.error(f"❌ Você esgotou seus 5 créditos gratuitos.")
            
            if stats.get('next_free_credits_time'):
                st.info(f"⏱️ Seus créditos serão renovados em {stats['next_free_credits_time']}")
            
            st.warning("💡 Deseja continuar analisando sem esperar? Faça upgrade para um pacote pago.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Standard - 30 Créditos", key="upgrade_standard"):
                    st.session_state.user_manager._upgrade_to_standard(st.session_state.email)
                    st.success("Parabéns! Você agora tem o pacote Standard com 30 créditos!")
                    time.sleep(1)
                    st.experimental_rerun()
            with col2:
                if st.button("Pro - 60 Créditos", key="upgrade_pro"):
                    st.session_state.user_manager._upgrade_to_pro(st.session_state.email)
                    st.success("Parabéns! Você agora tem o pacote Pro com 60 créditos!")
                    time.sleep(1)
                    st.experimental_rerun()
            
            return False
        else:
            # Paid tiers - offer to buy more credits
            st.warning(f"⚠️ Você tem apenas {remaining_credits} créditos restantes. Esta análise requer {num_markets} créditos.")
            
            # Show days until downgrade if applicable
            if stats.get('days_until_downgrade'):
                st.warning(f"⚠️ Atenção: Você será rebaixado para o pacote Free em {stats['days_until_downgrade']} dias se não comprar mais créditos.")
            
            # Show purchase options
            st.info("Compre mais créditos para continuar.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("30 Créditos - R$19,99"):
                    if st.session_state.user_manager.add_credits(st.session_state.email, 30):
                        st.success("30 créditos adicionados!")
                        time.sleep(1)
                        st.experimental_rerun()
                        
            with col2:
                if st.button("60 Créditos - R$29,99"):
                    if st.session_state.user_manager.add_credits(st.session_state.email, 60):
                        st.success("60 créditos adicionados!")
                        time.sleep(1)
                        st.experimental_rerun()
            
            return False
            
    return True

def show_main_dashboard():
    """Show the main dashboard after login"""
    # Show usage stats in sidebar
    show_usage_stats()
    
    # Título principal na sidebar
    st.sidebar.title("Análise de Apostas")
    
    # Add logout button
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.email = None
        st.session_state.page = "landing"
        st.experimental_rerun()
        
    # Obter informações do usuário atual
    user_stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)
    
    # Adicionar botão de Ver Pacotes
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚀 Ver Pacotes de Créditos", key="packages_button", use_container_width=True):
        st.session_state.page = "packages"  # Página de pacotes
        st.experimental_rerun()
    
    # Configurações na sidebar
    st.sidebar.title("Configurações")
    selected_league = st.sidebar.selectbox(
        "Escolha o campeonato:",
        list(FBREF_URLS.keys())
    )
    
    # Container de status para mensagens
    status_container = st.sidebar.empty()
    
    # Header com a logo na área principal - LOGO AUMENTADO
    st.markdown('<div class="logo-container" style="width: fit-content; padding: 12px 25px;"><span class="logo-v" style="font-size: 3rem;">V</span><span class="logo-text" style="font-size: 2.5rem;">ValueHunter</span></div>', unsafe_allow_html=True)
        
    # Busca dados do campeonato
    with st.spinner("Carregando dados do campeonato..."):
        stats_html = fetch_fbref_data(FBREF_URLS[selected_league]["stats"])
        
        if not stats_html:
            st.error("Não foi possível carregar os dados do campeonato")
            return
        
        team_stats_df = parse_team_stats(stats_html)
        
        if team_stats_df is None or 'Squad' not in team_stats_df.columns:
            st.error("Erro ao processar dados dos times")
            return
        
        status_container.success("Dados carregados com sucesso!")
        
        teams = team_stats_df['Squad'].dropna().unique().tolist()
        
        if not teams:
            st.error("Não foi possível encontrar os times do campeonato")
            return
    
    # Área principal
    st.title("Seleção de Times")
    
    # Seleção dos times em duas colunas
    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox("Time da Casa:", teams, key='home_team')
    with col2:
        away_teams = [team for team in teams if team != home_team]
        away_team = st.selectbox("Time Visitante:", away_teams, key='away_team')

    # Get user tier limits
    user_stats = st.session_state.user_manager.get_usage_stats(st.session_state.email)

    # Seleção de mercados em container separado
    with st.expander("Mercados Disponíveis", expanded=True):
        st.markdown("### Seleção de Mercados")
        
        # Mostrar informação de créditos
        st.info(f"Você tem {user_stats['credits_remaining']} créditos disponíveis. Cada mercado selecionado consumirá 1 crédito.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_markets = {
                "money_line": st.checkbox("Money Line (1X2)", value=True, key='ml'),
                "over_under": st.checkbox("Over/Under", key='ou'),
                "chance_dupla": st.checkbox("Chance Dupla", key='cd')
            }
        
        with col2:
            selected_markets.update({
                "ambos_marcam": st.checkbox("Ambos Marcam", key='btts'),
                "escanteios": st.checkbox("Total de Escanteios", key='corners'),
                "cartoes": st.checkbox("Total de Cartões", key='cards')
            })

        # Verificar número de mercados selecionados
        num_selected_markets = sum(1 for v in selected_markets.values() if v)
        if num_selected_markets == 0:
            st.warning("Por favor, selecione pelo menos um mercado para análise.")
        else:
            st.write(f"Total de créditos que serão consumidos: {num_selected_markets}")

    # Inputs de odds em container separado
    odds_data = None
    if any(selected_markets.values()):
        with st.expander("Configuração de Odds", expanded=True):
            odds_data = get_odds_data(selected_markets)

    # Botão de análise centralizado
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        analyze_button = st.button("Analisar Partida", type="primary")
        
        if analyze_button:
            if not any(selected_markets.values()):
                st.error("Por favor, selecione pelo menos um mercado para análise.")
                return
                
            if not odds_data:
                st.error("Por favor, configure as odds para os mercados selecionados.")
                return
            
            # Verificar limites de análise
            if not check_analysis_limits(selected_markets):
                return
                
            # Criar um placeholder para o status
            status = st.empty()
            
            try:
                # Etapa 1: Carregar dados
                status.info("Carregando dados dos times...")
                if not stats_html or not team_stats_df is not None:
                    status.error("Falha ao carregar dados")
                    return
                    
                # Etapa 2: Formatar prompt
                status.info("Preparando análise...")
                prompt = format_prompt(team_stats_df, home_team, away_team, odds_data)
                if not prompt:
                    status.error("Falha ao preparar análise")
                    return
                    
                # Etapa 3: Análise GPT
                status.info("Realizando análise com IA...")
                analysis = analyze_with_gpt(prompt)
                if not analysis:
                    status.error("Falha na análise")
                    return
                
                # Etapa 4: Mostrar resultado
                if analysis:
                    # Primeiro aplica o estilo
                    st.markdown("""
                        <style>
                            .analysis-result {
                                width: 100% !important;
                                max-width: 100% !important;
                                padding: 1rem !important;
                                background-color: #575760;
                                border-radius: 8px;
                                border: 1px solid #6b6b74;
                            }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    # Depois mostra o conteúdo
                    st.markdown(f'<div class="analysis-result">{analysis}</div>', unsafe_allow_html=True)
                    
                    # Registrar uso após análise bem-sucedida
                    num_markets = sum(1 for v in selected_markets.values() if v)
                    st.session_state.user_manager.record_usage(st.session_state.email, num_markets)
                    
                    # Atualizar estatísticas de uso
                    show_usage_stats()
                    
            except Exception as e:
                status.error(f"Erro durante a análise: {str(e)}")
        
class UserManager:
    def __init__(self, storage_path: str = ".streamlit/users.json"):
        self.storage_path = storage_path
        self.users = self._load_users()
        
        # Define user tiers/packages
        self.tiers = {
            "free": UserTier("free", 5, float('inf')),     # 5 credits, multiple markets
            "standard": UserTier("standard", 30, float('inf')),  # 30 credits, multiple markets
            "pro": UserTier("pro", 60, float('inf'))       # 60 credits, multiple markets
        }
        
    def _load_users(self) -> Dict:
        """Load users from JSON file"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_users(self):
        """Save users to JSON file"""
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # Criar backup antes de salvar
            if os.path.exists(self.storage_path):
                backup_path = f"{self.storage_path}.backup"
                with open(self.storage_path, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())
                    
            # Salvar dados atualizados
            with open(self.storage_path, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            st.error(f"Erro ao salvar dados dos usuários: {str(e)}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))
    
    def _format_tier_name(self, tier: str) -> str:
        """Format tier name for display (capitalize)"""
        tier_display = {
            "free": "Free",
            "standard": "Standard", 
            "pro": "Pro"
        }
        return tier_display.get(tier, tier.capitalize())
    
    def register_user(self, email: str, password: str, tier: str = "free") -> tuple[bool, str]:
        """Register a new user"""
        if not self._validate_email(email):
            return False, "Email inválido"
        if email in self.users:
            return False, "Email já registrado"
        if len(password) < 6:
            return False, "Senha deve ter no mínimo 6 caracteres"
        if tier not in self.tiers:
            return False, "Tipo de usuário inválido"
            
        self.users[email] = {
            "password": self._hash_password(password),
            "tier": tier,
            "usage": {
                "daily": [],
                "total": []  # Track total usage
            },
            "purchased_credits": 0,  # Track additional purchased credits
            "free_credits_exhausted_at": None,  # Timestamp when free credits run out
            "paid_credits_exhausted_at": None,  # Timestamp when paid credits run out
            "created_at": datetime.now().isoformat()
        }
        self._save_users()
        return True, "Registro realizado com sucesso"
    
    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate a user"""
        if email not in self.users:
            return False
            
        # Check if the password matches
        if self.users[email]["password"] != self._hash_password(password):
            return False
            
        # Check for auto-downgrade to Free when logging in
        if self.users[email]["tier"] in ["standard", "pro"]:
            self._check_downgrade_to_free(email)
            
        return True
    
    def _check_downgrade_to_free(self, email: str) -> None:
        """Check if user should be downgraded to Free due to inactivity"""
        if email not in self.users:
            return
            
        user = self.users[email]
        
        # If user has no credits and has a timestamp when credits were exhausted
        if user.get("paid_credits_exhausted_at") and user["tier"] in ["standard", "pro"]:
            exhausted_time = datetime.fromisoformat(user["paid_credits_exhausted_at"])
            current_time = datetime.now()
            
            # If 7 days (604800 seconds) have passed since credits were exhausted
            if (current_time - exhausted_time).total_seconds() >= 604800:
                self._downgrade_to_free(email)
    
    def add_credits(self, email: str, amount: int) -> bool:
        """Add more credits to a user account"""
        if email not in self.users:
            return False
            
        if "purchased_credits" not in self.users[email]:
            self.users[email]["purchased_credits"] = 0
            
        self.users[email]["purchased_credits"] += amount
        
        # Clear paid credits exhausted timestamp when adding credits
        if self.users[email].get("paid_credits_exhausted_at"):
            self.users[email]["paid_credits_exhausted_at"] = None
            
        self._save_users()
        return True
    
    def get_usage_stats(self, email: str) -> Dict:
        """Get usage statistics for a user"""
        if email not in self.users:
            return {}
            
        user = self.users[email]
        
        # Check for auto-downgrade to Free
        if user["tier"] in ["standard", "pro"]:
            self._check_downgrade_to_free(email)
            # Refresh user data after potential downgrade
            user = self.users[email]
        
        # Calculate total credits used
        total_credits_used = sum(
            u["markets"] for u in user["usage"]["total"]
        )
        
        # Get initial credits from tier
        tier = self.tiers[user["tier"]]
        initial_credits = tier.total_credits
        
        # Add any purchased credits
        purchased_credits = user.get("purchased_credits", 0)
        
        # Special handling for Free tier - check if 24h have passed since credits exhausted
        free_credits_reset = False
        next_free_credits_time = None
        days_until_downgrade = None
        
        if user["tier"] == "free":
            # Se ele já usou créditos e tem marcação de esgotamento
            if user.get("free_credits_exhausted_at"):
                # Convert stored time to datetime
                exhausted_time = datetime.fromisoformat(user["free_credits_exhausted_at"])
                current_time = datetime.now()
                
                # Check if 24 hours have passed
                if (current_time - exhausted_time).total_seconds() >= 86400:  # 24 hours in seconds
                    # Reset credits - IMPORTANTE: sempre será 5 créditos, não acumula
                    user["free_credits_exhausted_at"] = None
                    
                    # Clear usage history for free users after reset
                    user["usage"]["total"] = []
                    free_credits_reset = True
                    self._save_users()
                    
                    # Após resetar, não há créditos usados
                    total_credits_used = 0
                else:
                    # Calculate time remaining
                    time_until_reset = exhausted_time + timedelta(days=1) - current_time
                    hours = int(time_until_reset.total_seconds() // 3600)
                    minutes = int((time_until_reset.total_seconds() % 3600) // 60)
                    next_free_credits_time = f"{hours}h {minutes}min"
        elif user["tier"] in ["standard", "pro"] and user.get("paid_credits_exhausted_at"):
            # Calculate days until downgrade for paid tiers
            exhausted_time = datetime.fromisoformat(user["paid_credits_exhausted_at"])
            current_time = datetime.now()
            
            # Calculate days remaining until 7-day mark
            days_passed = (current_time - exhausted_time).total_seconds() / 86400  # Convert to days
            days_until_downgrade = max(0, int(7 - days_passed))
            
            if days_until_downgrade == 0:
                # This will be caught on the next check/login
                pass
        
        # Calculate remaining credits
        remaining_credits = max(0, initial_credits + purchased_credits - total_credits_used)
        
        # Check if paid user is out of credits and set exhausted timestamp
        if user["tier"] in ["standard", "pro"] and remaining_credits == 0 and not user.get("paid_credits_exhausted_at"):
            user["paid_credits_exhausted_at"] = datetime.now().isoformat()
            self._save_users()
        
        return {
            "tier": user["tier"],
            "tier_display": self._format_tier_name(user["tier"]),
            "credits_used": total_credits_used,
            "credits_total": initial_credits + purchased_credits,
            "credits_remaining": remaining_credits,
            "market_limit": tier.market_limit,
            "free_credits_reset": free_credits_reset,
            "next_free_credits_time": next_free_credits_time,
            "days_until_downgrade": days_until_downgrade
        }
    
    def record_usage(self, email: str, num_markets: int):
        """Record usage for a user (each market consumes one credit)"""
        if email not in self.users:
            return
            
        today = datetime.now().date().isoformat()
        usage = {
            "date": today,
            "markets": num_markets  # Each market = 1 credit
        }
        
        # Still track daily for analytics purposes
        self.users[email]["usage"]["daily"].append(usage)
        
        # Track total usage
        self.users[email]["usage"]["total"].append(usage)
        
        # Get current usage stats
        stats = self.get_usage_stats(email)
        remaining_after_usage = max(0, stats['credits_remaining'] - num_markets)
        
        # Check if Free tier user has exhausted credits
        if self.users[email]["tier"] == "free":
            if remaining_after_usage == 0 and not self.users[email].get("free_credits_exhausted_at"):
                # Mark when credits were exhausted
                self.users[email]["free_credits_exhausted_at"] = datetime.now().isoformat()
        
        # Check if paid tier user has exhausted credits
        elif self.users[email]["tier"] in ["standard", "pro"]:
            if remaining_after_usage == 0 and not self.users[email].get("paid_credits_exhausted_at"):
                # Mark when credits were exhausted
                self.users[email]["paid_credits_exhausted_at"] = datetime.now().isoformat()
        
        self._save_users()
    
    def can_analyze(self, email: str, num_markets: int) -> bool:
        """Check if user can perform analysis"""
        stats = self.get_usage_stats(email)
        
        # Check if user has enough credits
        return stats['credits_remaining'] >= num_markets
    
    # Métodos de upgrade/downgrade
    def _upgrade_to_standard(self, email: str) -> bool:
        """Upgrade a user to Standard package"""
        if email not in self.users:
            return False
            
        self.users[email]["tier"] = "standard"
        # Reset usage and timestamps for upgrade
        self.users[email]["free_credits_exhausted_at"] = None
        self.users[email]["paid_credits_exhausted_at"] = None
        self.users[email]["usage"]["total"] = []
        self.users[email]["purchased_credits"] = 0
        self._save_users()
        return True
        
    def _upgrade_to_pro(self, email: str) -> bool:
        """Upgrade a user to Pro package"""
        if email not in self.users:
            return False
            
        self.users[email]["tier"] = "pro"
        # Reset usage and timestamps for upgrade
        self.users[email]["free_credits_exhausted_at"] = None
        self.users[email]["paid_credits_exhausted_at"] = None
        self.users[email]["usage"]["total"] = []
        self.users[email]["purchased_credits"] = 0
        self._save_users()
        return True
        
    def _downgrade_to_free(self, email: str) -> bool:
        """Downgrade a user to Free package"""
        if email not in self.users:
            return False
            
        self.users[email]["tier"] = "free"
        # Reset usage for free users
        self.users[email]["usage"]["total"] = []
        self.users[email]["purchased_credits"] = 0
        self.users[email]["free_credits_exhausted_at"] = None
        self.users[email]["paid_credits_exhausted_at"] = None
        self._save_users()
        return True

def get_odds_data(selected_markets):
    """Função para coletar e formatar os dados das odds"""
    odds_data = {}
    odds_text = []
    has_valid_odds = False

    # Money Line
    if selected_markets.get("money_line", False):
        st.markdown("### Money Line")
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["home"] = st.number_input("Casa (@)", min_value=1.01, step=0.01, value=1.50, format="%.2f", key="ml_home")
        with col2:
            odds_data["draw"] = st.number_input("Empate (@)", min_value=1.01, step=0.01, value=4.00, format="%.2f", key="ml_draw")
        with col3:
            odds_data["away"] = st.number_input("Fora (@)", min_value=1.01, step=0.01, value=6.50, format="%.2f", key="ml_away")

        if all(odds_data.get(k, 0) > 1.01 for k in ["home", "draw", "away"]):
            has_valid_odds = True
            odds_text.append(f"""Money Line:
- Casa: @{odds_data['home']:.2f} (Implícita: {(100/odds_data['home']):.1f}%)
- Empate: @{odds_data['draw']:.2f} (Implícita: {(100/odds_data['draw']):.1f}%)
- Fora: @{odds_data['away']:.2f} (Implícita: {(100/odds_data['away']):.1f}%)""")

    # Over/Under
    if selected_markets.get("over_under", False):
        st.markdown("### Over/Under")
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["goals_line"] = st.number_input("Linha", min_value=0.5, value=2.5, step=0.5, format="%.1f", key="goals_line")
        with col2:
            odds_data["over"] = st.number_input(f"Over {odds_data.get('goals_line', 2.5)} (@)", min_value=1.01, step=0.01, value=1.85, format="%.2f", key="ou_over")
        with col3:
            odds_data["under"] = st.number_input(f"Under {odds_data.get('goals_line', 2.5)} (@)", min_value=1.01, step=0.01, value=1.95, format="%.2f", key="ou_under")

        if all(odds_data.get(k, 0) > 1.01 for k in ["over", "under"]):
            has_valid_odds = True
            odds_text.append(f"""Over/Under {odds_data['goals_line']}:
- Over: @{odds_data['over']:.2f} (Implícita: {(100/odds_data['over']):.1f}%)
- Under: @{odds_data['under']:.2f} (Implícita: {(100/odds_data['under']):.1f}%)""")

    # Chance Dupla
    if selected_markets.get("chance_dupla", False):
        st.markdown("### Chance Dupla")
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["1x"] = st.number_input("1X (@)", min_value=1.01, step=0.01, value=1.20, format="%.2f", key="cd_1x")
        with col2:
            odds_data["12"] = st.number_input("12 (@)", min_value=1.01, step=0.01, value=1.30, format="%.2f", key="cd_12")
        with col3:
            odds_data["x2"] = st.number_input("X2 (@)", min_value=1.01, step=0.01, value=1.40, format="%.2f", key="cd_x2")

        if all(odds_data.get(k, 0) > 1.01 for k in ["1x", "12", "x2"]):
            has_valid_odds = True
            odds_text.append(f"""Chance Dupla:
- 1X: @{odds_data['1x']:.2f} (Implícita: {(100/odds_data['1x']):.1f}%)
- 12: @{odds_data['12']:.2f} (Implícita: {(100/odds_data['12']):.1f}%)
- X2: @{odds_data['x2']:.2f} (Implícita: {(100/odds_data['x2']):.1f}%)""")

    # Ambos Marcam
    if selected_markets.get("ambos_marcam", False):
        st.markdown("### Ambos Marcam")
        col1, col2 = st.columns(2)
        with col1:
            odds_data["btts_yes"] = st.number_input("Sim (@)", min_value=1.01, step=0.01, value=1.75, format="%.2f", key="btts_yes")
        with col2:
            odds_data["btts_no"] = st.number_input("Não (@)", min_value=1.01, step=0.01, value=2.05, format="%.2f", key="btts_no")

        if all(odds_data.get(k, 0) > 1.01 for k in ["btts_yes", "btts_no"]):
            has_valid_odds = True
            odds_text.append(f"""Ambos Marcam:
- Sim: @{odds_data['btts_yes']:.2f} (Implícita: {(100/odds_data['btts_yes']):.1f}%)
- Não: @{odds_data['btts_no']:.2f} (Implícita: {(100/odds_data['btts_no']):.1f}%)""")

    # Total de Escanteios
    if selected_markets.get("escanteios", False):
        st.markdown("### Total de Escanteios")
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["corners_line"] = st.number_input("Linha Escanteios", min_value=0.5, value=9.5, step=0.5, format="%.1f", key="corners_line")
        with col2:
            odds_data["corners_over"] = st.number_input("Over Escanteios (@)", min_value=1.01, step=0.01, value=1.85, format="%.2f", key="corners_over")
        with col3:
            odds_data["corners_under"] = st.number_input("Under Escanteios (@)", min_value=1.01, step=0.01, value=1.95, format="%.2f", key="corners_under")

        if all(odds_data.get(k, 0) > 1.01 for k in ["corners_over", "corners_under"]):
            has_valid_odds = True
            odds_text.append(f"""Total de Escanteios {odds_data['corners_line']}:
- Over: @{odds_data['corners_over']:.2f} (Implícita: {(100/odds_data['corners_over']):.1f}%)
- Under: @{odds_data['corners_under']:.2f} (Implícita: {(100/odds_data['corners_under']):.1f}%)""")

    # Total de Cartões
    if selected_markets.get("cartoes", False):
        st.markdown("### Total de Cartões")
        col1, col2, col3 = st.columns(3)
        with col1:
            odds_data["cards_line"] = st.number_input("Linha Cartões", min_value=0.5, value=3.5, step=0.5, format="%.1f", key="cards_line")
        with col2:
            odds_data["cards_over"] = st.number_input("Over Cartões (@)", min_value=1.01, step=0.01, value=1.85, format="%.2f", key="cards_over")
        with col3:
            odds_data["cards_under"] = st.number_input("Under Cartões (@)", min_value=1.01, step=0.01, value=1.95, format="%.2f", key="cards_under")

        if all(odds_data.get(k, 0) > 1.01 for k in ["cards_over", "cards_under"]):
            has_valid_odds = True
            odds_text.append(f"""Total de Cartões {odds_data['cards_line']}:
- Over: @{odds_data['cards_over']:.2f} (Implícita: {(100/odds_data['cards_over']):.1f}%)
- Under: @{odds_data['cards_under']:.2f} (Implícita: {(100/odds_data['cards_under']):.1f}%)""")

    if not has_valid_odds:
        return None
        
    return "\n\n".join(odds_text)

def get_fbref_urls():
    """Retorna o dicionário de URLs do FBref"""
    return FBREF_URLS

@st.cache_resource
def get_openai_client():
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        return client
    except Exception as e:
        st.error(f"Erro ao criar cliente OpenAI: {str(e)}")
        return None


def analyze_with_gpt(prompt):
    try:
        client = get_openai_client()
        if not client:
            st.error("Cliente OpenAI não inicializado")
            return None
            
        st.write("Enviando requisição para API...")  # Log para debug
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um Agente Analista de Probabilidades Esportivas especializado."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=60  # Timeout de 60 segundos
        )
        st.write("Resposta recebida da API!")  # Log para debug
        return response.choices[0].message.content
    except OpenAIError as e:
        st.error(f"Erro na API OpenAI: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        st.write(f"Traceback completo: {traceback.format_exc()}")  # Log detalhado do erro
        return None
def parse_team_stats(html_content):
    """Processa os dados do time com tratamento melhorado para extrair estatísticas"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Procurar todas as tabelas que podem conter as estatísticas
        stats_table = None
        
        # Lista de IDs de tabelas conhecidos
        table_ids = [
            'stats_squads_standard_for',
            'stats_squads_standard_stats',
            'stats_squads_standard_overall',
            'stats_squads_keeper_for'
        ]
        
        # Tentar encontrar a tabela por ID
        for table_id in table_ids:
            stats_table = soup.find('table', {'id': table_id})
            if stats_table:
                break
        
        # Se não encontrou por ID, procurar por conteúdo
        if not stats_table:
            all_tables = soup.find_all('table')
            for table in all_tables:
                headers = table.find_all('th')
                if headers:
                    header_text = [h.get_text(strip=True).lower() for h in headers]
                    if any(keyword in ' '.join(header_text) for keyword in ['squad', 'team', 'goals']):
                        stats_table = table
                        break
        
        if not stats_table:
            return None
        
        # Ler a tabela com pandas
        df = pd.read_html(str(stats_table))[0]
        
        # Tratar colunas multi-índice e duplicadas
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[-1] if isinstance(col, tuple) else col for col in df.columns]
        
        # Remover colunas duplicadas mantendo a primeira ocorrência
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Limpar nomes das colunas
        df.columns = [str(col).strip() for col in df.columns]
        
        # Função para encontrar a coluna correta
        def find_column(possible_names, df_columns):
            for name in possible_names:
                # Procura exata
                if name in df_columns:
                    return name
                # Procura case-insensitive
                matches = [col for col in df_columns if str(col).strip().lower() == name.lower()]
                if matches:
                    return matches[0]
                # Procura por substring
                matches = [col for col in df_columns if name.lower() in str(col).strip().lower()]
                if matches:
                    return matches[0]
            return None

        # Mapear colunas importantes
        column_mapping = {
            'Squad': ['Squad', 'Team', 'Equipe'],
            'MP': ['MP', 'Matches', 'Jogos'],
            'Gls': ['Gls', 'Goals', 'Gols', 'G'],
            'G90': ['G90', 'Goals90', 'Gols90'],
            'xG': ['xG', 'Expected Goals'],
            'xG90': ['xG90', 'ExpectedGoals90'],
            'Poss': ['Poss', 'Possession', 'PosseBola']
        }
        
        # Encontrar e renomear colunas usando find_column
        new_columns = {}
        for new_name, possible_names in column_mapping.items():
            found_col = find_column(possible_names, df.columns)
            if found_col:
                new_columns[found_col] = new_name
        
        # Aplicar o mapeamento de colunas
        df = df.rename(columns=new_columns)
        
        # Garantir coluna Squad
        if 'Squad' not in df.columns and len(df.columns) > 0:
            df = df.rename(columns={df.columns[0]: 'Squad'})
        
        # Limpar dados
        df['Squad'] = df['Squad'].astype(str).str.strip()
        df = df.dropna(subset=['Squad'])
        df = df.drop_duplicates(subset=['Squad'])
        
        # Converter colunas numéricas com segurança
        numeric_columns = ['MP', 'Gls', 'G90', 'xG', 'xG90', 'Poss']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    # Primeiro, garantir que a coluna é uma série e não um DataFrame
                    if isinstance(df[col], pd.DataFrame):
                        df[col] = df[col].iloc[:, 0]
                    
                    # Limpar e converter para número
                    df[col] = pd.to_numeric(
                        df[col].astype(str)
                           .str.replace(',', '.')
                           .str.extract('([-+]?\d*\.?\d+)', expand=False),
                        errors='coerce'
                    )
                except Exception:
                    df[col] = np.nan
        
        # Preencher valores ausentes
        df = df.fillna('N/A')
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        return None

def rate_limit(seconds):
    def decorator(func):
        last_called = [0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < seconds:
                time.sleep(seconds - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

@rate_limit(1)  # 1 requisição por segundo
def fetch_fbref_data(url):
    """Busca dados do FBref com melhor tratamento de erros e timeout"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    try:
        with st.spinner(f"Buscando dados de {url}..."):
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.text
            else:
                st.error(f"Erro ao buscar dados: Status {response.status_code}")
                return None
                
    except requests.Timeout:
        st.error("Timeout ao buscar dados. Tente novamente.")
        return None
    except requests.RequestException as e:
        st.error(f"Erro na requisição: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return None

def get_stat(stats, col, default='N/A'):
    """
    Função auxiliar para extrair estatísticas com tratamento de erro
    """
    try:
        value = stats[col]
        if pd.notna(value) and value != '':
            return value
        return default
    except:
        return default

def format_prompt(stats_df, home_team, away_team, odds_data):
    """Formata o prompt para o GPT-4 com os dados coletados"""
    try:
        st.write("Iniciando formatação do prompt...")  # Novo log
        # Extrair dados dos times
        home_stats = stats_df[stats_df['Squad'] == home_team].iloc[0]
        away_stats = stats_df[stats_df['Squad'] == away_team].iloc[0]
        
        # Calcular probabilidades reais baseadas em xG e outros dados
        def calculate_real_prob(home_xg, away_xg, home_games, away_games):
            try:
                if pd.isna(home_xg) or pd.isna(away_xg):
                    return None
                
                home_xg_per_game = home_xg / home_games if home_games > 0 else 0
                away_xg_per_game = away_xg / away_games if away_games > 0 else 0
                
                # Ajuste baseado em home advantage
                home_advantage = 1.1
                adjusted_home_xg = home_xg_per_game * home_advantage
                
                total_xg = adjusted_home_xg + away_xg_per_game
                if total_xg == 0:
                    return None
                    
                home_prob = (adjusted_home_xg / total_xg) * 100
                away_prob = (away_xg_per_game / total_xg) * 100
                draw_prob = 100 - (home_prob + away_prob)
                
                return {
                    'home': home_prob,
                    'draw': draw_prob,
                    'away': away_prob
                }
            except:
                return None

        # Formatar estatísticas dos times
        home_team_stats = f"""
  * Jogos Disputados: {get_stat(home_stats, 'MP')}
  * Gols Marcados: {get_stat(home_stats, 'Gls')}
  * Expected Goals (xG): {get_stat(home_stats, 'xG')}
  * Posse de Bola: {get_stat(home_stats, 'Poss')}%"""

        away_team_stats = f"""
  * Jogos Disputados: {get_stat(away_stats, 'MP')}
  * Gols Marcados: {get_stat(away_stats, 'Gls')}
  * Expected Goals (xG): {get_stat(away_stats, 'xG')}
  * Posse de Bola: {get_stat(away_stats, 'Poss')}%"""

        st.write("Calculando probabilidades...")  # Novo log

        # Calcular probabilidades reais
        real_probs = calculate_real_prob(
            float(get_stat(home_stats, 'xG', 0)),
            float(get_stat(away_stats, 'xG', 0)),
            float(get_stat(home_stats, 'MP', 1)),
            float(get_stat(away_stats, 'MP', 1))
        )

        # Montar o prompt completo
        full_prompt = f"""Role: Agente Analista de Probabilidades Esportivas

KNOWLEDGE BASE INTERNO:
- Estatísticas Home Team ({home_team}):{home_team_stats}

- Estatísticas Away Team ({away_team}):{away_team_stats}

PROBABILIDADES CALCULADAS:
"""
        
        if real_probs:
            full_prompt += f"""- Vitória {home_team}: {real_probs['home']:.1f}% (Real)
- Empate: {real_probs['draw']:.1f}% (Real)
- Vitória {away_team}: {real_probs['away']:.1f}% (Real)
"""
        else:
            full_prompt += "Dados insuficientes para cálculo de probabilidades reais\n"

        full_prompt += f"""
[SAÍDA OBRIGATÓRIA]

# Análise da Partida
## {home_team} x {away_team}

# Análise de Mercados Disponíveis:
{odds_data}

# Probabilidades Calculadas:
[Detalhamento das probabilidades reais vs implícitas por mercado]

# Oportunidades Identificadas (Edges >3%):
[Listagem detalhada dos mercados com edges significativos]

# Nível de Confiança Geral: [Baixo/Médio/Alto]
"""
        st.write("Prompt formatado com sucesso!")  # Log final
        return full_prompt

    except Exception as e:
        st.error(f"Erro ao formatar prompt: {str(e)}")
        return None

def main():
    try:
        # Initialize session state
        init_session_state()
        
        # Configuração inicial do Streamlit
        st.set_page_config(
            page_title="ValueHunter - Análise de Apostas Esportivas",
            page_icon="⚽",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # CSS global atualizado para remover o retângulo cinza ao redor do título "Sobre o ValueHunter"
        st.markdown("""
            <style>
                /* Estilo geral da aplicação - background principal */
                .stApp {
                    background-color: #3F3F45;
                }
                
                /* Contêineres e elementos de fundo */
                .st-emotion-cache-ffhzg2,
                .st-emotion-cache-16txtl3,
                section[data-testid="stSidebar"],
                .sidebar .sidebar-content,
                .st-cx {
                    background-color: #3F3F45;
                }
                
                /* Texto branco para todos os elementos */
                p, div, span, li, a, label, text, .st-emotion-cache-16idsys p, .st-emotion-cache-16idsys {
                    color: #FFFFFF !important;
                }
                
                /* Textos nos inputs */
                .stTextInput>div>div>input, .stSelectbox {
                    color: #FFFFFF !important;
                    background-color: #575760 !important;
                    border: 1px solid #6b6b74 !important;
                }
                
                /* Manter o laranja para títulos e botões principais */
                h1, h2, h3, h4, h5, h6 {
                    color: #fd7014 !important;
                }
                
                /* Ajustes na logo - AUMENTADO TAMANHO */
                .logo-container {
                    background-color: #fd7014;
                    padding: 12px 25px !important; /* Maior padding */
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    width: fit-content;
                }
                .logo-text {
                    font-size: 2.5rem !important; /* Maior fonte */
                    font-weight: bold;
                    color: #FFFFFF !important;
                }
                .logo-v {
                    color: #3F3F45 !important;
                    font-size: 3rem !important; /* Maior fonte */
                    font-weight: bold;
                }
                
                /* NOVO: Estilo para TODOS os botões - LARANJA COM TEXTO BRANCO */
                div.stButton > button {
                    background-color: #fd7014 !important;
                    color: #FFFFFF !important;
                    border: none !important;
                    border-radius: 4px;
                    font-weight: bold;
                    transition: background-color 0.3s ease;
                }
                
                div.stButton > button:hover {
                    background-color: #27272a !important; /* Cinza escuro no hover */
                    color: white !important;
                }
                
                /* Estilo para botão primário */
                button[kind="primary"] {
                    background-color: #fd7014 !important;
                    color: white !important;
                    font-size: 1.1rem !important;
                    padding: 0.6rem 1.2rem !important;
                }
                
                /* Ajuste do contraste da sidebar */
                section[data-testid="stSidebar"] {
                    background-color: #27272a !important;
                    border-right: 1px solid #fd7014;
                }
                
                /* Container principal mais escuro */
                .main .block-container {
                    background-color: #3F3F45;
                    padding: 1rem !important;
                }
                
                /* REMOVIDO o estilo .about-section que criava o retângulo cinza */
                
                /* Ajustado para substituir o about-section */
                .about-content {
                    max-width: 90% !important;
                    margin-left: 0 !important;
                    line-height: 1.6;
                    margin-top: 2rem;
                    margin-bottom: 2rem;
                }
                
                /* Reduzir espaçamento entre títulos e conteúdo */
                h1, h2, h3 {
                    margin-bottom: 0.8rem !important;
                }
                
                /* Ajustar espaçamento entre seções */
                .hero {
                    margin: 2rem 0 !important; /* Reduzido de 3rem para 2rem */
                    text-align: left !important; /* Alinhado à esquerda */
                }
                
                /* Melhorar contraste dos widgets */
                .stSelectbox > div > div,
                .stNumberInput > div > div {
                    background-color: #575760 !important;
                }
                
                /* Cores das mensagens e alertas - manter para legibilidade */
                .stAlert p {
                    color: inherit !important;
                }
                
                /* Ajuste no tamanho do título principal */
                .hero h1 {
                    font-size: 2.8rem !important;
                    color: #fd7014 !important;
                    margin-bottom: 1rem !important;
                }
                
                /* Ajustar margens para título principal */
                h1:first-of-type {
                    margin-top: 0.5rem !important;
                }
                
                /* Destaque para resultados de análise */
                .analysis-result {
                    width: 100% !important;
                    max-width: 100% !important;
                    padding: 1rem !important;
                    background-color: #575760;
                    border-radius: 8px;
                    border: 1px solid #6b6b74;
                }

                /* Estilos para a página de planos */
                .plan-container {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    gap: 20px;
                    margin-top: 2rem;
                }
                .plan-card {
                    background-color: #ffffff;
                    border-radius: 10px;
                    padding: 1.5rem;
                    width: 250px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    text-align: center;
                    display: flex;
                    flex-direction: column;
                    border: 1px solid #e2e8f0;
                }
                .plan-card.free {
                    border-top: 4px solid #e44d87;
                }
                .plan-card.standard {
                    border-top: 4px solid #0077b6;
                    transform: scale(1.05);
                }
                .plan-card.pro {
                    border-top: 4px solid #0abab5;
                }
                .plan-title {
                    color: #222831;
                    font-size: 1.5rem;
                    font-weight: bold;
                    margin-bottom: 1rem;
                }
                .plan-price {
                    color: #222831;
                    font-size: 2.2rem;
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                }
                .plan-period {
                    color: #64748b;
                    font-size: 0.9rem;
                    margin-bottom: 1.5rem;
                }
                .plan-feature {
                    color: #222831;
                    text-align: left;
                    margin-bottom: 0.5rem;
                    display: flex;
                    align-items: center;
                }
                .plan-feature i {
                    color: #0abab5;
                    margin-right: 10px;
                }
                .plan-button {
                    background-color: #fd7014;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 0.75rem 1rem;
                    font-weight: bold;
                    cursor: pointer;
                    margin-top: auto;
                    transition: background-color 0.3s;
                }
                .plan-button:hover {
                    background-color: #e05f00;
                }
                .plan-button.current {
                    background-color: #27272a;
                    cursor: default;
                }
                .plan-popular {
                    position: absolute;
                    top: -10px;
                    right: 20px;
                    background-color: #e44d87;
                    color: white;
                    font-size: 0.8rem;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                }
                .plan-icon {
                    font-size: 3rem;
                    margin-bottom: 1rem;
                }
                .free-icon {
                    color: #e44d87;
                }
                .standard-icon {
                    color: #0077b6;
                }
                .pro-icon {
                    color: #0abab5;
                }
                .plan-card-container {
                    position: relative;
                    padding-top: 10px;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Lógica de roteamento de páginas
        if st.session_state.page == "landing":
            show_landing_page()
        elif st.session_state.page == "login":
            show_login()
        elif st.session_state.page == "register":
            show_register()
        elif st.session_state.page == "main":
            if not st.session_state.authenticated:
                st.warning("Sua sessão expirou. Por favor, faça login novamente.")
                go_to_login()
                return
                
            # Mostrar dashboard principal
            show_main_dashboard()
        elif st.session_state.page == "packages":
            if not st.session_state.authenticated:
                st.warning("Você precisa fazer login para acessar os pacotes.")
                go_to_login()
                return
                
            # Mostrar página de pacotes
            show_packages_page()
        else:
            # Página padrão - redirecionando para landing
            st.session_state.page = "landing"
            st.experimental_rerun()

    except Exception as e:
        st.error(f"Erro geral na aplicação: {str(e)}")

if __name__ == "__main__":
    main()
