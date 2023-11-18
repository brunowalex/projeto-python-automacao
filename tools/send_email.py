from datetime import datetime, timedelta
import time

import pandas as pd
from googleapiclient.discovery import build
import getpass
import os, sys

# Email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage

def get_email_credentials():
    return '<seu email', '<sua senha>'

def create_table(df):    
    # Criar tabela HTML
    tabela_html = df.to_html(index=True, escape=False, classes='table table-bordered', header='true')
    
    # Adicionar estilo CSS para centralizar o cabeçalho
    tabela_html = tabela_html.replace('<thead>', '<thead style="text-align:center;">')
    
    return tabela_html

def main(df):
    current_dir = os.path.realpath(os.path.dirname(__file__))
    csv_file = os.path.join(current_dir, 'frutaria.csv')
    df = pd.read_csv(csv_file)

    tabela_html = create_table(df)

    try:
        email, password = get_email_credentials()
        # Configurar o corpo do e-mail
        subject = 'Automação - Dados Frutaria'
        corpo_email = f"""
        <h2>{subject}</h2>\n
        <p>Prezados,</p>\n
        <p>Gostaria de informar que os dados dos nossos produtos foram atualizados. Abaixo, você encontrará a tabela correspondente com as informações mais recentes.</p>\n
        {tabela_html}\n
        <p>Se precisar de qualquer esclarecimento adicional ou se houver alguma dúvida, estou à disposição para ajudar.</p>
        <p>Atenciosamente,</p>
        <p>Bruno</p>
        """
        # Crie um e-mail
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = '<email>'
        msg['Subject'] = subject

        msg.attach(MIMEText(corpo_email, 'html'))

        # Conectar-se ao servidor SMTP do Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)

        # Envie o e-mail
        server.sendmail(email, '<email>', msg.as_string())

        # Feche a conexão com o servidor SMTP
        server.quit()

        print("\nEmail successfully sent!")
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()