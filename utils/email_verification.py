# utils/email_verification.py
import random
import string
import smtplib
import ssl
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
        # Configurações de email do GoDaddy
        sender_email = "contact@valuehunter.app"
        password = "sua-senha-aqui"  # Por segurança, substitua por secrets em produção
        smtp_server = "smtpout.secureserver.net"
        smtp_port = 465
        
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
        
        # Configurar contexto SSL
        context = ssl.create_default_context()
        
        # Enviar email usando SSL
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email de verificação enviado para {email}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email de verificação: {str(e)}")
        return False

def verify_email_code(email, user_provided_code, stored_code):
    """
    Verifica se o código fornecido pelo usuário corresponde ao código armazenado
    
    Args:
        email (str): Email do usuário
        user_provided_code (str): Código fornecido pelo usuário
        stored_code (str): Código armazenado no sistema
        
    Returns:
        bool: True se o código for válido, False caso contrário
    """
    try:
        # Verificação simples de correspondência
        return user_provided_code == stored_code
    except Exception as e:
        logger.error(f"Erro ao verificar código para {email}: {str(e)}")
        return False
