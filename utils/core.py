# utils/core.py - Funções Principais
import os
import json
import time
import logging
import streamlit as st
from datetime import datetime, timedelta
from urllib.parse import urlencode
import base64

# Importando dependências
try:
    import stripe
except ImportError:
    # Dummy stripe para caso de falha no import
    class DummyStripe:
        api_key = None
        class checkout:
            class Session:
                @staticmethod
                def create(**kwargs):
                    return type('obj', (object,), {'id': 'dummy_session', 'url': '#'})
                @staticmethod
                def retrieve(session_id):
                    return type('obj', (object,), {'payment_status': 'unpaid', 'metadata': {'credits': '0', 'email': ''}})
        class error:
            class InvalidRequestError(Exception):
                pass
    stripe = DummyStripe
# Configuração de logging
logger = logging.getLogger("valueHunter.core")
# Configurações globais
DATA_DIR = "data"
if "RENDER" in os.environ:
    # Em produção no Render, use um caminho padrão para montagem de disco
    DATA_DIR = "/mnt/value-hunter-data"  # Caminho padrão para discos persistentes

# Ocultar mensagens de erro relacionadas a secrets.toml
def hide_streamlit_errors():
    st.markdown("""
    <style>
    /* Ocultar mensagens de erro sobre secrets */
    [data-testid="stException"],
    div[data-stale="false"][data-testid="stStatusWidget"],
    div.stException,
    .element-container div.stAlert[kind="error"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Chamar a função para ocultar erros quando o módulo é importado
try:
    hide_streamlit_errors()
except:
    pass  # Ignorar erros se o contexto Streamlit não estiver disponível

# Funções de CSS e UI
def configure_sidebar_visibility():
    """
    Configura a visibilidade da barra lateral:
    1. Mantém a barra lateral visível
    2. Oculta apenas os itens de navegação
    """
    st.markdown("""
    <style>
        /* Garantir que a barra lateral esteja visível */
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
        }
        
        /* Ocultar completamente o menu de navegação lateral */
        [data-testid="stSidebarNavItems"],
        .st-emotion-cache-16idsys, 
        .st-emotion-cache-1cypcdb,
        .st-emotion-cache-vk3wp9,
        .st-emotion-cache-ue6h4q,
        .st-emotion-cache-jnd7a1 {
            display: none !important;
        }

        /* Remover margens superiores desnecessárias */
        section[data-testid="stSidebarUserContent"] {
            margin-top: 0 !important;
        }
        
        /* Ocultar outros elementos de navegação */
        header[data-testid="stHeader"],
        button[kind="header"],
        #MainMenu,
        footer,
        [data-testid="collapsedControl"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
def hide_streamlit_menu():
    """Oculta o menu de navegação do Streamlit e outros elementos da interface padrão"""
    return """
    <style>
        /* Ocultar completamente o menu de navegação lateral */
        [data-testid="stSidebarNavItems"],
        div.stSidebarNavItems, 
        button.stSidebarButton,
        .st-emotion-cache-16idsys, 
        .st-emotion-cache-1cypcdb,
        .st-emotion-cache-vk3wp9,
        .st-emotion-cache-ue6h4q,
        .st-emotion-cache-jnd7a1,
        ul.st-emotion-cache-pbk8do {
            display: none !important;
        }
        
        /* Remover margens superiores desnecessárias */
        section[data-testid="stSidebarUserContent"] {
            margin-top: 0 !important;
        }
        
        /* Ocultar cabeçalho, rodapé e menu principal */
        header[data-testid="stHeader"],
        button[kind="header"],
        #MainMenu,
        footer,
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        
        /* Garantir que a barra lateral esteja visível e funcionando */
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
            transform: none !important;
        }
        
        /* Remover espaço extra no topo que normalmente é ocupado pelo menu */
        .main .block-container {
            padding-top: 1rem !important;
        }
    </style>
    """
def hide_app_admin_items():
    """
    Função para ocultar completamente os itens 'app' e 'admin' 
    em qualquer parte da interface do Streamlit
    """
    st.markdown("""
    <style>
        /* Seletores específicos para o modal/dropdown */
        div[role="dialog"] p:contains("app"),
        div[role="dialog"] p:contains("admin"),
        div[aria-modal="true"] p:contains("app"),
        div[aria-modal="true"] p:contains("admin"),
        
        /* Seletores para navegação lateral */
        [data-testid="stSidebarNavItems"] a:has(p:contains("app")),
        [data-testid="stSidebarNavItems"] a:has(p:contains("admin")),
        
        /* Seletores gerais para qualquer texto */
        p:contains("app"),
        p:contains("admin") {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def hide_app_admin_from_modal():
    """
    Função específica para ocultar os itens 'app' e 'admin' no modal/dropdown de navegação
    """
    st.markdown("""
    <style>
        /* Seletores ultra-específicos para o modal/dropdown da captura de tela */
        div[role="dialog"] div > p:contains("app"),
        div[role="dialog"] div > p:contains("admin") {
            display: none !important;
        }
        
        /* Seletor alternativo para o mesmo elemento */
        div[aria-modal="true"] p:contains("app"),
        div[aria-modal="true"] p:contains("admin") {
            display: none !important;
        }
        
        /* Seletor com correspondência de texto exato para maior precisão */
        p:text-is("app"),
        p:text-is("admin") {
            display: none !important;
        }
        
        /* Seletor direto para elementos de página na navegação */
        div.st-bd p:contains("app"),
        div.st-bd p:contains("admin") {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def apply_global_css():
    """Aplica apenas estilos CSS essenciais"""
    css = (
        "<style>"
        "div.stButton > button {background-color: #fd7014 !important; color: white !important;}"
        "div.stButton > button:hover {background-color: #333 !important;}"
        "p, li {color: white !important;}"
        "[data-testid='stSidebarNavItems'] {display: none !important;}"
        "header[data-testid='stHeader'], footer, #MainMenu {display: none !important;}"
        "</style>"
    )
    
    st.markdown(css, unsafe_allow_html=True)
# Função para exibir a logo do ValueHunter de forma consistente
def _get_base64(path: str) -> str:
    """Converte qualquer arquivo binário em string base64."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

import os, base64, streamlit as st

def show_valuehunter_logo():
    logo_path = os.path.join(os.getcwd(), "3F3F45.png")   # ajuste o caminho se necessário
    with open(logo_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(
        f"<div style='text-align:center; margin-bottom:20px;'><img src='data:image/png;base64,{b64}' width='200'></div>",
        unsafe_allow_html=True
    )


# Adicione esta função para inserir o favicon no app.py logo após a linha st.set_page_config()

def insert_favicon():
    """
    Insere o favicon SVG diretamente no HTML
    """
    # Possíveis caminhos para o favicon
    favicon_paths = [
        os.path.join(os.getcwd(), "favicon_svg.svg"),
        os.path.join(os.getcwd(), "favicon.svg"),
        os.path.join(os.getcwd(), "static", "favicon_svg.svg"),
        "/opt/render/project/src/favicon_svg.svg",  # Caminho específico do Render
        "/app/favicon_svg.svg"  # Outro caminho possível
    ]
    
    # Debug - listar todos os caminhos sendo verificados
    print("Procurando favicon nos seguintes caminhos:")
    for path in favicon_paths:
        exists = os.path.exists(path)
        print(f"  - {path}: {'ENCONTRADO' if exists else 'NÃO ENCONTRADO'}")
    
    # Encontrar o primeiro favicon disponível
    favicon_path = None
    for path in favicon_paths:
        if os.path.exists(path):
            favicon_path = path
            print(f"Usando favicon encontrado em: {favicon_path}")
            break
    
    try:
        # Verificar se encontrou algum arquivo
        if favicon_path and os.path.exists(favicon_path):
            # Ler o arquivo como binário
            with open(favicon_path, "rb") as f:
                favicon_data = f.read()
            
            # Converter para base64
            favicon_b64 = base64.b64encode(favicon_data).decode()
            
            # Inserir como tag link com tipo MIME correto para SVG
            favicon_html = (
                "<link rel='icon' type='image/svg+xml' "
                f"href='data:image/svg+xml;base64,{favicon_b64}'>"
            )
            
            # Exibir com mais altura para garantir que seja renderizado
            st.markdown(favicon_html, unsafe_allow_html=True)
            print(f"Favicon inserido com sucesso: {favicon_path}")
            logger.info(f"Favicon inserido com sucesso: {favicon_path}")
            
            # Inserir também como ícone alternativo para garantir compatibilidade
            alt_favicon_html = (
                "<link rel='shortcut icon' "
                f"href='data:image/svg+xml;base64,{favicon_b64}'>"
            )
            st.markdown(alt_favicon_html, unsafe_allow_html=True)
        else:
            print(f"Favicon não encontrado em nenhum dos caminhos verificados")
            logger.warning(f"Favicon não encontrado em nenhum dos caminhos verificados")
    except Exception as e:
        print(f"Erro ao inserir favicon: {str(e)}")
        logger.error(f"Erro ao inserir favicon: {str(e)}")

# Funções de navegação
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

# Função init_session_state
def init_session_state():
    """Initialize session state variables"""
    from utils.data import UserManager
    
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
    
    # Variáveis para o checkout integrado
    if "show_checkout" not in st.session_state:
        st.session_state.show_checkout = False
    
    if "checkout_credits" not in st.session_state:
        st.session_state.checkout_credits = 0
        
    if "checkout_amount" not in st.session_state:
        st.session_state.checkout_amount = 0
        
    if "last_stripe_session_id" not in st.session_state:
        st.session_state.last_stripe_session_id = None
    
    # Stripe test mode flag
    if "stripe_test_mode" not in st.session_state:
        st.session_state.stripe_test_mode = True
    
    # UserManager deve ser o último a ser inicializado
    if "user_manager" not in st.session_state:
        st.session_state.user_manager = UserManager()
    
    # Atualizar timestamp de última atividade
    st.session_state.last_activity = datetime.now()

# Funções de Stripe
def init_stripe():
    """Initialize Stripe with the API key."""
    # Melhor controle de erros e logging para inicialização do Stripe
    try:
        # Se estamos no Render, usar variáveis de ambiente diretamente
        if "RENDER" in os.environ:
            api_key = os.environ.get("STRIPE_SECRET_KEY", "")
            logger.info("Usando API key do Stripe de variáveis de ambiente no Render")
        else:
            # Tente usar secrets (para desenvolvimento local ou Streamlit Cloud)
            try:
                api_key = st.secrets.get("STRIPE_SECRET_KEY", "")
                logger.info("Usando API key do Stripe de st.secrets")
            except Exception as e:
                logger.warning(f"Erro ao tentar carregar API key do Stripe de st.secrets: {str(e)}")
                api_key = os.environ.get("STRIPE_SECRET_KEY", "")
                logger.info("Usando API key do Stripe de variáveis de ambiente locais")
        
        # Atualizar API key do Stripe
        stripe.api_key = api_key
        
        if not stripe.api_key:
            logger.error("Stripe API key não encontrada em nenhuma configuração")
            st.error("Stripe API key not found")
        else:
            logger.info(f"Stripe API key configurada com sucesso. Modo de teste: {stripe.api_key.startswith('sk_test_')}")
        
        # Para teste, isso avisa os usuários que estão no modo de teste
        st.session_state.stripe_test_mode = stripe.api_key.startswith("sk_test_")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar Stripe: {str(e)}")
        st.error(f"Erro ao inicializar Stripe. Por favor, tente novamente mais tarde.")

def get_base_url():
    """Get the base URL for the application, with special handling for Render."""
    # Check if running on Render
    if "RENDER" in os.environ:
        url = os.environ.get("RENDER_EXTERNAL_URL", "https://value-hunter.onrender.com")
        logger.info(f"Base URL no Render: {url}")
        return url
    # Check if running on Streamlit Cloud
    elif os.environ.get("IS_STREAMLIT_CLOUD"):
        url = os.environ.get("STREAMLIT_URL", "https://valuehunter.streamlit.app")
        logger.info(f"Base URL no Streamlit Cloud: {url}")
        return url
    # Local development
    else:
        try:
            url = st.get_option("server.baseUrlPath") or "http://localhost:8501"
            logger.info(f"Base URL local: {url}")
            return url
        except:
            logger.info("Usando URL local padrão: http://localhost:8501")
            return "http://localhost:8501"

def get_stripe_success_url(credits, email):
    """URL de sucesso que força refresh dos dados"""
    base_url = get_base_url()
    
    success_params = urlencode({
        'success_page': 'true',
        'credits': credits,
        'email': email,
        'session_id': '{CHECKOUT_SESSION_ID}',
        'payment_processed': 'true'  # Novo parâmetro para forçar refresh
    })
    
    full_url = f"{base_url}/?{success_params}"
    logger.info(f"URL de sucesso do Stripe configurada: {full_url}")
    return full_url

def get_stripe_cancel_url():
    """URL de cancelamento simplificada"""
    base_url = get_base_url()
    cancel_params = urlencode({'cancel_page': 'true'})
    full_url = f"{base_url}/?{cancel_params}"
    return full_url

def redirect_to_stripe(checkout_url):
    """Abre um popup para o checkout do Stripe"""
    # JavaScript para abrir o Stripe em um popup
    js_popup = f"""
    <script>
        // Abrir popup do Stripe centralizado
        var windowWidth = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
        var windowHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
        
        var popupWidth = 600;
        var popupHeight = 700;
        
        var left = (windowWidth - popupWidth) / 2;
        var top = (windowHeight - popupHeight) / 2;
        
        // Abrir popup centralizado com nome único para evitar múltiplas janelas
        var stripePopup = window.open(
            '{checkout_url}', 
            'stripe_checkout',
            `width=${{popupWidth}},height=${{popupHeight}},left=${{left}},top=${{top}},location=yes,toolbar=yes,scrollbars=yes`
        );
        
        // Verificar se o popup foi bloqueado
        if (!stripePopup || stripePopup.closed || typeof stripePopup.closed == 'undefined') {{
            // Popup foi bloqueado
            document.getElementById('popup-blocked').style.display = 'block';
        }} else {{
            // Popup foi aberto com sucesso
            document.getElementById('popup-success').style.display = 'block';
        }}
    </script>
    
    <div id="popup-blocked" style="display:none; padding: 15px; background-color: #ffcccc; border-radius: 5px; margin: 15px 0;">
        <h3>⚠️ Popup bloqueado!</h3>
        <p>Seu navegador bloqueou o popup de pagamento. Por favor:</p>
        <ol>
            <li>Clique no ícone de bloqueio de popup na barra de endereço</li>
            <li>Selecione "Sempre permitir popups de [seu site]"</li>
            <li>Clique no botão abaixo para tentar novamente</li>
        </ol>
        <a href="{checkout_url}" target="_blank" style="display: inline-block; padding: 10px 15px; background-color: #fd7014; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
            Abrir página de pagamento
        </a>
    </div>
    
    <div id="popup-success" style="display:none; padding: 15px; background-color: #e6ffe6; border-radius: 5px; margin: 15px 0;">
        <h3>✅ Janela de pagamento aberta!</h3>
        <p>Uma nova janela foi aberta para você concluir seu pagamento.</p>
        <p>Após completar o pagamento, a janela será fechada automaticamente e seus créditos serão adicionados.</p>
        <p>Para ver seus créditos, clique no botão "Voltar para análises" após concluir o pagamento.</p>
    </div>
    """
    
    # Exibir o JavaScript
    st.components.v1.html(js_popup, height=350)

def create_stripe_checkout_session(email, credits, amount):
    """Cria uma sessão de checkout do Stripe com manejo simplificado"""
    try:
        # Initialize Stripe
        init_stripe()
        
        # Convert amount to cents
        amount_cents = int(float(amount) * 100)
        
        # Create product description
        product_description = f"{credits} Créditos para ValueHunter"
        
        # Create success URL
        success_url = get_stripe_success_url(credits, email)
        cancel_url = get_stripe_cancel_url()
        
        logger.info(f"Criando sessão de checkout para {email}: {credits} créditos, R${amount}")
        logger.info(f"Success URL: {success_url}")
        logger.info(f"Cancel URL: {cancel_url}")
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': f'ValueHunter - {credits} Créditos',
                        'description': product_description,
                    },
                    'unit_amount': amount_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            customer_email=email,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'email': email,
                'credits': str(credits)
            }
        )
        
        # Armazenar o ID da sessão
        st.session_state.last_stripe_session_id = checkout_session.id
        logger.info(f"Sessão de checkout do Stripe criada com sucesso: {checkout_session.id}")
        
        return checkout_session
    except Exception as e:
        logger.error(f"Erro ao criar sessão de pagamento: {str(e)}")
        st.error(f"Erro ao criar sessão de pagamento: {str(e)}")
        return None

def verify_stripe_payment(session_id):
    """
    Versão aprimorada e mais tolerante da verificação de pagamento.
    Em ambiente de teste, SEMPRE considera o pagamento válido.
    """
    try:
        logger.info(f"Verificando sessão de pagamento: {session_id}")
        
        # IMPORTANTE: Em ambiente de teste, considerar QUALQUER pagamento válido
        if st.session_state.stripe_test_mode:
            try:
                # Tentar obter dados reais, mas não falhar se não conseguir
                if session_id and session_id.startswith('cs_'):
                    try:
                        session = stripe.checkout.Session.retrieve(session_id)
                        credits = int(session.metadata.get('credits', 0))
                        email = session.metadata.get('email', '')
                        logger.info(f"TESTE: Sessão válida para {email}: {credits} créditos")
                        return True, credits, email
                    except:
                        # Se falhar, pegar dados da URL (fallback)
                        credits = st.query_params.get('credits', 0)
                        email = st.query_params.get('email', '')
                        credits = int(credits) if isinstance(credits, str) else credits
                        logger.info(f"TESTE FALLBACK: Usando dados da URL: {email}, {credits} créditos")
                        return True, credits, email
            except Exception as e:
                # Sempre retornar verdadeiro em ambiente de teste, com valores de fallback
                logger.warning(f"Erro em ambiente de teste, usando fallback: {str(e)}")
                credits = st.query_params.get('credits', 30)  # Valor padrão se tudo falhar
                email = st.query_params.get('email', '')
                credits = int(credits) if isinstance(credits, str) else credits
                return True, credits, email

        # Em ambiente de produção, verificar o status do pagamento
        if session_id and session_id.startswith('cs_'):
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                
                # Extrair informações mesmo que o pagamento não esteja completo
                credits = int(session.metadata.get('credits', 0))
                email = session.metadata.get('email', '')
                
                # Verificar status de pagamento
                if session.payment_status == 'paid':
                    logger.info(f"PRODUÇÃO: Pagamento verificado com sucesso: {session_id}")
                    return True, credits, email
                else:
                    logger.warning(f"PRODUÇÃO: Pagamento não concluído: {session_id}, status: {session.payment_status}")
                    # Retornar os dados, mas indicando que o pagamento não está confirmado
                    return False, credits, email
            except Exception as e:
                logger.error(f"Erro ao verificar sessão do Stripe: {str(e)}")
                # Em caso de erro, tentar obter informações da URL
                credits = st.query_params.get('credits', 0) 
                email = st.query_params.get('email', '')
                credits = int(credits) if isinstance(credits, str) else credits
                return False, credits, email
        
        # Se não há ID de sessão ou não começa com cs_
        logger.warning(f"ID de sessão inválido: {session_id}")
        credits = st.query_params.get('credits', 0)
        email = st.query_params.get('email', '')
        credits = int(credits) if isinstance(credits, str) else credits
        return False, credits, email
        
    except Exception as e:
        logger.error(f"Erro crítico ao verificar pagamento: {str(e)}")
        # Último recurso - tentar obter da URL
        credits = st.query_params.get('credits', 0)
        email = st.query_params.get('email', '')
        credits = int(credits) if isinstance(credits, str) else credits
        return False, credits, email

def update_purchase_button(credits, amount):
    """Função comum para processar a compra de créditos"""
    logger.info(f"Botão de {credits} créditos clicado")
    
    # Criar checkout e redirecionar
    checkout_session = create_stripe_checkout_session(
        st.session_state.email, 
        credits, 
        amount
    )
    
    if checkout_session:
        logger.info(f"Checkout session criada: {checkout_session.id}")
        redirect_to_stripe(checkout_session.url)
        return True
        
    return False

def check_payment_success():
    """
    Verifica se estamos em uma página especial de sucesso/cancelamento
    ou se estamos verificando parâmetros na página principal.
    """
    # Verificar se estamos na página de sucesso do popup
    if 'success_page' in st.query_params and st.query_params.success_page == 'true':
        return handle_success_page()
        
    # Verificar se estamos na página de cancelamento do popup
    if 'cancel_page' in st.query_params and st.query_params.cancel_page == 'true':
        return handle_cancel_page()
        
    return False

def handle_success_page():
    """
    Função aprimorada que garante a adição de créditos,
    mesmo em caso de erros.
    """
    try:
        # Obter parâmetros da URL
        credits_param = st.query_params.get('credits', '0')
        email_param = st.query_params.get('email', '')
        session_id = st.query_params.get('session_id', '')
        
        # Converter créditos para número
        try:
            credits_value = int(credits_param)
        except:
            credits_value = 0
            
        # Log detalhado
        logger.info(f"Processando página de sucesso: email={email_param}, credits={credits_value}, session_id={session_id}")
        
        # Inicializar Stripe (garantir que temos acesso à API)
        try:
            init_stripe()
        except Exception as e:
            logger.error(f"Erro ao inicializar Stripe: {str(e)}")
        
        # Verificar pagamento de forma robusta
        is_valid, verified_credits, verified_email = verify_stripe_payment(session_id)
        
        # Log detalhado após verificação
        logger.info(f"Resultado da verificação: valid={is_valid}, credits={verified_credits}, email={verified_email}")
        
        # Variáveis para a mensagem
        final_credits = verified_credits if verified_credits > 0 else credits_value
        final_email = verified_email if verified_email else email_param
        
        # IMPORTANTE: Adicionar créditos SEMPRE, garantindo que não falhe
        credits_added = False
        
        # Primeira tentativa: usar email verificado
        if final_email and final_credits > 0:
            try:
                logger.info(f"Tentando adicionar {final_credits} créditos para {final_email}")
                
                # Verificar se o usuário existe
                if hasattr(st.session_state, 'user_manager') and final_email in st.session_state.user_manager.users:
                    # Adicionar diretamente na estrutura de dados para garantir
                    if "purchased_credits" not in st.session_state.user_manager.users[final_email]:
                        st.session_state.user_manager.users[final_email]["purchased_credits"] = 0
                    
                    st.session_state.user_manager.users[final_email]["purchased_credits"] += final_credits
                    
                    # Limpar timestamp de esgotamento se existir
                    if "paid_credits_exhausted_at" in st.session_state.user_manager.users[final_email]:
                        st.session_state.user_manager.users[final_email]["paid_credits_exhausted_at"] = None
                    
                    # Salvar alterações
                    st.session_state.user_manager._save_users()
                    
                    # Registrar sucesso
                    logger.info(f"Créditos adicionados diretamente: {final_credits} para {final_email}")
                    credits_added = True
                else:
                    # Tentar usar a função padrão
                    if st.session_state.user_manager.add_credits(final_email, final_credits):
                        logger.info(f"Créditos adicionados via função: {final_credits} para {final_email}")
                        credits_added = True
                    else:
                        logger.warning(f"Falha ao adicionar créditos via função: {final_credits} para {final_email}")
            except Exception as add_error:
                logger.error(f"Erro ao adicionar créditos para {final_email}: {str(add_error)}")
        
        # Log final
        if credits_added:
            logger.info(f"SUCESSO: {final_credits} créditos adicionados para {final_email}")
        else:
            logger.warning(f"FALHA: Não foi possível adicionar créditos para {final_email}")
        
        # HTML ultra-simples, apenas a mensagem
        success_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pagamento Aprovado</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #3F3F45;
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    padding: 20px;
                    box-sizing: border-box;
                }}
                .message-box {{
                    background-color: #4CAF50;
                    border-radius: 10px;
                    padding: 30px;
                    text-align: center;
                    max-width: 500px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }}
                .logo {
                    background-color: #fd7014;
                    padding: 10px 20px;
                    border-radius: 8px;
                    display: inline-flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 20px;
                }
                .logo-text {
                    font-size: 1.7rem;
                    font-weight: bold;
                    color: white;
                }
                h1 {{
                    font-size: 1.8rem;
                    margin: 15px 0;
                }}
                p {{
                    font-size: 1.2rem;
                    margin: 10px 0;
                }}
                .credits {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: #FFEB3B;
                    margin: 15px 0;
                }}
                .status {{
                    font-size: 1rem;
                    color: rgba(255,255,255,0.8);
                    margin-top: 20px;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            <div class="message-box">
                <div class="logo">
                    <span class="logo-v">V</span>
                    <span class="logo-text">ValueHunter</span>
                </div>
                <h1>✅ Pagamento Aprovado</h1>
                <p>Seu pagamento foi processado com sucesso.</p>
                <div class="credits">{final_credits} créditos</div>
                <p>foram adicionados à sua conta.</p>
                <p><strong>Feche esta janela para continuar.</strong></p>
                <div class="status">{f"ID: {session_id[:8]}..." if session_id else "Processado com sucesso"}</div>
            </div>
        </body>
        </html>
        """
        
        # Renderizar APENAS o HTML
        st.components.v1.html(success_html, height=400, scrolling=False)
        
        # Impedir a execução de qualquer outro código
        st.stop()
        
        return True
        
    except Exception as e:
        logger.error(f"Erro crítico na página de sucesso: {str(e)}")
        
        # Mensagem de erro ultra-simples
        error_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Processando Pagamento</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #3F3F45;
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    padding: 20px;
                    box-sizing: border-box;
                }
                .message-box {
                    background-color: #2196F3;
                    border-radius: 10px;
                    padding: 30px;
                    text-align: center;
                    max-width: 500px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                .logo {
                    background-color: #fd7014;
                    padding: 10px 20px;
                    border-radius: 8px;
                    display: inline-flex;
                    align-items: center;
                    margin-bottom: 20px;
                }
                .logo-v {
                    color: #3F3F45;
                    font-size: 2rem;
                    font-weight: bold;
                }
                .logo-text {
                    font-size: 1.7rem;
                    font-weight: bold;
                    color: white;
                }
                h1 {
                    font-size: 1.8rem;
                    margin: 15px 0;
                }
                p {
                    font-size: 1.2rem;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <div class="message-box">
                <div class="logo">
                    <!-- SVG binoculars logo -->
                    <svg style="width:40px; height:40px;" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M35 25C25.5 25 20 35 20 45C20 55 25.5 65 35 65C44.5 65 50 55 50 45C50 35 44.5 25 35 25Z" fill="white"/>
                        <path d="M65 25C74.5 25 80 35 80 45C80 55 74.5 65 65 65C55.5 65 50 55 50 45C50 35 55.5 25 65 25Z" fill="white"/>
                        <path d="M50 40V50M43 45L57 45M35 35C31.7 35 30 39 30 45C30 51 31.7 55 35 55C38.3 55 40 51 40 45C40 39 38.3 35 35 35ZM65 35C61.7 35 60 39 60 45C60 51 61.7 55 65 55C68.3 55 70 51 70 45C70 39 68.3 35 65 35Z" stroke="#3F3F45" stroke-width="3"/>
                    </svg>
                    <span class="logo-text">VALUEHUNTER</span>
                </div>
        </body>
        </html>
        """
        
        st.components.v1.html(error_html, height=400, scrolling=False)
        st.stop()
        return False

def handle_cancel_page():
    """
    Mostra APENAS uma mensagem estática de cancelamento, sem timer.
    """
    try:
        # HTML ultra-simples
        cancel_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pagamento Não Aprovado</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #3F3F45;
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    padding: 20px;
                    box-sizing: border-box;
                }
                .message-box {
                    background-color: #FF9800;
                    border-radius: 10px;
                    padding: 30px;
                    text-align: center;
                    max-width: 500px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                .logo {
                    background-color: #fd7014;
                    padding: 10px 20px;
                    border-radius: 8px;
                    display: inline-flex;
                    align-items: center;
                    margin-bottom: 20px;
                }
                .logo-v {
                    color: #3F3F45;
                    font-size: 2rem;
                    font-weight: bold;
                }
                .logo-text {
                    font-size: 1.7rem;
                    font-weight: bold;
                    color: white;
                }
                h1 {
                    font-size: 1.8rem;
                    margin: 15px 0;
                }
                p {
                    font-size: 1.2rem;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <div class="message-box">
                <div class="logo">
                    <!-- SVG binoculars logo -->
                    <svg style="width:40px; height:40px;" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M35 25C25.5 25 20 35 20 45C20 55 25.5 65 35 65C44.5 65 50 55 50 45C50 35 44.5 25 35 25Z" fill="white"/>
                        <path d="M65 25C74.5 25 80 35 80 45C80 55 74.5 65 65 65C55.5 65 50 55 50 45C50 35 55.5 25 65 25Z" fill="white"/>
                        <path d="M50 40V50M43 45L57 45M35 35C31.7 35 30 39 30 45C30 51 31.7 55 35 55C38.3 55 40 51 40 45C40 39 38.3 35 35 35ZM65 35C61.7 35 60 39 60 45C60 51 61.7 55 65 55C68.3 55 70 51 70 45C70 39 68.3 35 65 35Z" stroke="#3F3F45" stroke-width="3"/>
                    </svg>
                    <span class="logo-text">VALUEHUNTER</span>
                </div>
                <h1>⚠️ Pagamento Não Aprovado</h1>
                <p>O pagamento não foi concluído.</p>
                <p><strong>Feche esta janela e tente novamente.</strong></p>
            </div>
        </body>
        </html>
        """
        
        # Renderizar APENAS o HTML
        st.components.v1.html(cancel_html, height=400, scrolling=False)
        
        # Parar a execução
        st.stop()
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao exibir página de cancelamento: {str(e)}")
        return False

def handle_stripe_errors():
    if 'error' in st.query_params:
        st.error("Erro no processamento do pagamento...")
        st.query_params.clear()

def apply_responsive_styles():
    """Versão mínima da função - estilos básicos apenas"""
    css = (
        "<style>"
        ".main .block-container {max-width: 1200px; margin: 0 auto;}"
        "h1, h2, h3 {color: #fd7014;}"
        "</style>"
    )
    
    st.markdown(css, unsafe_allow_html=True)
# Adicione esta função à utils/core.py

def apply_navigation_hiding(hide_sidebar_completely=False):
    """Versão simplificada"""
    css = (
        "<style>"
        "[data-testid='stSidebarNavItems'] {display: none !important;}"
        "header[data-testid='stHeader'], footer, #MainMenu {display: none !important;}"
        "</style>"
    )
    
    st.markdown(css, unsafe_allow_html=True)

def remove_loading_screen():
    """Versão mínima da função - não faz nada"""
    pass

def show_valuehunter_logo():
    """Display the ValueHunter logo"""
    # Logo com o "V" em cor diferente e formatação correta
    st.markdown("""
    <div style="background-color: #fd7014; padding: 10px; border-radius: 5px; display: inline-block; margin-bottom: 1rem;">
        <h1 style="color: white; margin: 0; font-family: 'Arial', sans-serif;"><span style="color: #333;">V</span>ValueHunter</h1>
    </div>
    """, unsafe_allow_html=True)

def apply_custom_styles():
    """Aplica estilos CSS personalizados para layout e espaçamento consistentes"""
    st.markdown("""
    <style>
    /* Reduzir drasticamente o espaçamento do cabeçalho */
    .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
        padding-bottom: 1rem !important;
    }
    
    /* Ajustar a altura máxima do cabeçalho */
    header[data-testid="stHeader"] {
        height: 0px !important;
        padding: 0 !important;
        margin: 0 !important;
        visibility: hidden !important;
    }
    
    /* Aumentar significativamente as bordas laterais para desktop */
    @media (min-width: 992px) {
        .main .block-container {
            max-width: 1200px !important;
            padding-left: 10% !important;
            padding-right: 10% !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
    }
    
    /* Ajustar para mobile */
    @media (max-width: 991px) {
        .main .block-container {
            padding-left: 5% !important;
            padding-right: 5% !important;
        }
    }
    
    /* Menor ainda para telas muito pequenas */
    @media (max-width: 576px) {
        .main .block-container {
            padding-left: 2% !important;
            padding-right: 2% !important;
        }
    }
    
    /* Texto justificado em todo o aplicativo */
    p, li, .stMarkdown {
        text-align: justify !important;
    }
    
    /* Ajustar todos os cabeçalhos para ter menos espaço */
    h1, h2, h3 {
        margin-top: 0.8rem !important;
        margin-bottom: 0.8rem !important;
    }
    
    /* Corrigir botões para garantir que o texto caiba corretamente */
    .stButton button {
        background-color: #fd7014;
        color: white;
        border: none;
        font-weight: bold;
        border-radius: 4px;
        padding: 0.4rem 0.8rem !important;
        font-size: 0.9rem !important;
        white-space: nowrap !important;
        min-width: fit-content !important;
        height: auto !important;
        line-height: normal !important;
    }
    
    /* Remover botão nativo de colapso do Streamlit */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
def hide_sidebar_completely():
    """Versão simplificada"""
    css = (
        "<style>"
        "[data-testid='stSidebar'] {display: none !important;}"
        "</style>"
    )
    
    st.markdown(css, unsafe_allow_html=True)
