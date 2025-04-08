# utils/email_verification.py
import random
import string
import smtplib
import logging
from email.mime.text import MIMEText
import streamlit as st

# Configuração de logging
logger = logging.getLogger("valueHunter.email")

def generate_verification_code():
    """Gera um código de verificação de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, verification_code):
    """
    Envia e-mail de verificação usando as credenciais configuradas
    
    Args:
        email (str): Email do destinatário
        verification_code (str): Código de verificação
        
    Returns:
        bool: True se o e-mail foi enviado com sucesso, False caso contrário
    """
    try:
        # Obter credenciais de email
        if hasattr(st, 'secrets') and 'email' in st.secrets:
            sender_email = st.secrets.email.sender
            password = st.secrets.email.password
            smtp_server = st.secrets.email.smtp_server
            smtp_port = st.secrets.email.smtp_port
        else:
            # Valores padrão para desenvolvimento (substitua em produção)
            sender_email = "seu-email@gmail.com"
            password = "sua-senha-app"
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
        
        # Criar mensagem
        subject = "ValueHunter - Verificação de Email"
        body = f"""
        Olá,
        
        Obrigado por se cadastrar no ValueHunter!
        
        Seu código de verificação é: {verification_code}
        
        Por favor, insira este código no aplicativo para ativar sua conta e receber seus créditos gratuitos.
        
        Atenciosamente,
        Equipe ValueHunter
        """
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = email
        
        # Enviar email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email de verificação enviado para {email}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email de verificação: {str(e)}")
        return False
