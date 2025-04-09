# utils/email_verification.py
import random
import string
import smtplib
import ssl
import logging
import traceback
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

# Configuração de logging
logger = logging.getLogger("valueHunter.email")

def generate_verification_code(length=6):
    """Gera um código de verificação de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=length))

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
        # Tentar usar secrets, com fallback para variáveis de ambiente
        try:
            sender_email = st.secrets.email.sender
            password = st.secrets.email.password
            smtp_server = st.secrets.email.smtp_server
            smtp_port = st.secrets.email.smtp_port
        except:
            # Fallback para variáveis de ambiente ou valores fixos
            sender_email = os.environ.get("EMAIL_SENDER", "contact@valuehunter.app")
            password = os.environ.get("EMAIL_PASSWORD", "N@bundinha1")
            smtp_server = os.environ.get("EMAIL_SMTP_SERVER", "smtpout.secureserver.net")
            smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "465"))
        
        # Criar mensagem HTML formatada
        subject = "ValueHunter - Verificação de Email"
        
        # Corpo do email em HTML
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <div style="background-color: #fd7014; padding: 15px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0; font-family: Arial, sans-serif; font-size: 1.8rem;"><span style="color: #333;">V</span>ValueHunter</h1>
            </div>
            
            <h2 style="color: #333;">Verificação de Email</h2>
            
            <p>Olá,</p>
            
            <p>Obrigado por se registrar no ValueHunter! Para completar seu cadastro, utilize o código de verificação abaixo:</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0; font-size: 24px; letter-spacing: 5px; font-weight: bold;">
                {verification_code}
            </div>
            
            <p>Este código expirará em 24 horas.</p>
            
            <p>Se você não solicitou este código, por favor ignore este email.</p>
            
            <p>Atenciosamente,<br>Equipe ValueHunter</p>
        </div>
        """
        
        # Criar mensagem MIME
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = email
        
        # Adicionar versão HTML
        msg.attach(MIMEText(body_html, 'html'))
        
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
        logger.error(traceback.format_exc())
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
        if not stored_code or not user_provided_code:
            logger.warning(f"Verificação falhou: código ausente para {email}")
            return False
            
        # Converter para string e comparar
        return str(user_provided_code) == str(stored_code)
    except Exception as e:
        logger.error(f"Erro ao verificar código para {email}: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def send_password_recovery_email(email, recovery_code):
    """
    Envia um email de recuperação de senha contendo um código
    
    Args:
        email (str): Email do destinatário
        recovery_code (str): Código de recuperação
        
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    try:
        # Tentar usar secrets, com fallback para variáveis de ambiente
        try:
            sender_email = st.secrets.email.sender
            password = st.secrets.email.password
            smtp_server = st.secrets.email.smtp_server
            smtp_port = st.secrets.email.smtp_port
        except:
            # Fallback para variáveis de ambiente ou valores fixos
            sender_email = os.environ.get("EMAIL_SENDER", "contact@valuehunter.app")
            password = os.environ.get("EMAIL_PASSWORD", "N@bundinha1")
            smtp_server = os.environ.get("EMAIL_SMTP_SERVER", "smtpout.secureserver.net")
            smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "465"))
        
        # Assunto do email
        subject = "ValueHunter - Recuperação de Senha"
        
        # Corpo do email em HTML
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <div style="background-color: #fd7014; padding: 15px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0; font-family: Arial, sans-serif; font-size: 1.8rem;"><span style="color: #333;">V</span>ValueHunter</h1>
            </div>
            
            <h2 style="color: #333;">Recuperação de Senha</h2>
            
            <p>Olá,</p>
            
            <p>Recebemos uma solicitação de recuperação de senha para sua conta. Para redefinir sua senha, utilize o código abaixo:</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0; font-size: 24px; letter-spacing: 5px; font-weight: bold;">
                {recovery_code}
            </div>
            
            <p>Este código expirará em 1 hora.</p>
            
            <p>Se você não solicitou esta recuperação, por favor ignore este email.</p>
            
            <p>Atenciosamente,<br>Equipe ValueHunter</p>
        </div>
        """
        
        # Criar mensagem MIME
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = email
        
        # Adicionar versão HTML
        msg.attach(MIMEText(body_html, 'html'))
        
        # Configurar contexto SSL
        context = ssl.create_default_context()
        
        # Enviar email usando SSL
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email de recuperação de senha enviado para {email}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email de recuperação de senha: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# Função genérica de envio de email (útil para outras necessidades futuras)
def send_email(to_email, subject, body_html):
    """
    Função genérica para enviar email
    
    Args:
        to_email (str): Email do destinatário
        subject (str): Assunto do email
        body_html (str): Corpo do email em HTML
        
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    try:
        # Tentar usar secrets, com fallback para variáveis de ambiente
        try:
            sender_email = st.secrets.email.sender
            password = st.secrets.email.password
            smtp_server = st.secrets.email.smtp_server
            smtp_port = st.secrets.email.smtp_port
        except:
            # Fallback para variáveis de ambiente ou valores fixos
            sender_email = os.environ.get("EMAIL_SENDER", "contact@valuehunter.app")
            password = os.environ.get("EMAIL_PASSWORD", "N@bundinha1")
            smtp_server = os.environ.get("EMAIL_SMTP_SERVER", "smtpout.secureserver.net")
            smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "465"))
        
        # Criar mensagem MIME
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = to_email
        
        # Adicionar versão HTML
        msg.attach(MIMEText(body_html, 'html'))
        
        # Configurar contexto SSL
        context = ssl.create_default_context()
        
        # Enviar email usando SSL
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email enviado com sucesso para: {to_email}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email para {to_email}: {str(e)}")
        logger.error(traceback.format_exc())
        return False
