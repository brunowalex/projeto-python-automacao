import os.path
import configparser
import sys
import time
import pandas as pd

import pickle
import requests
import getpass

from google.cloud import bigquery
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import database.data_credentials
import tools.frutaria as frutaria

import io
import shutil

# Limpar tela de prompt
clear = lambda: os.system('cls')

current_dir = os.path.realpath(os.path.dirname(__file__))
bin_folder = os.path.join(current_dir, 'bin')
tools_folder = os.path.join(current_dir, 'tools')

try:
    os.mkdir('bin')
except:
    pass
try:
    os.mkdir('tools')
except:
    pass
sys.path.insert(1,tools_folder)

# Credentials
SCOPES =  ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/cloud-platform','https://www.googleapis.com/auth/bigquery','https://www.googleapis.com/auth/drive.readonly',]
CREDENTIALS = None

try:
    if os.path.exists(os.path.join(bin_folder, 'token.json')):
        CREDENTIALS = Credentials.from_authorized_user_file((os.path.join(bin_folder, 'token.json')), SCOPES)
    # Se não houver nenhuma credencial disponíveis, deixe o usuário fazer login.
    if not CREDENTIALS or not CREDENTIALS.valid:
        if CREDENTIALS and CREDENTIALS.expired and CREDENTIALS.refresh_token:
            CREDENTIALS.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                (os.path.join(bin_folder, 'credentials.json')), SCOPES)
            CREDENTIALS = flow.run_local_server(port=0)
        # Salve as credenciais para a próxima execução
        with open((os.path.join(bin_folder, 'token.json')), 'w') as token:
            token.write(CREDENTIALS.to_json())
except FileNotFoundError as e:
    print(f"Credentials.json not found, please follow the stps here: LINK \n {e}")
    sys.exit()

service_drive = build('drive', 'v3', credentials=CREDENTIALS)
service_sheets = build('sheets', 'v4', credentials = CREDENTIALS)
bq_client = bigquery.Client(project='gpd-analytics', credentials=CREDENTIALS)

def local_version():
    try:
        file = os.path.join(bin_folder, 'config.bin')
        with open(file, 'rb') as arquivo:
            numero_serializado = arquivo.read()
        l_version = pickle.loads(numero_serializado)
    except:
        l_version = '0'
    return l_version

def clouf_version():
    # Verifique a versão
    sheet_id ='<link planilha eletronica>'
    result = service_sheets.spreadsheets().values().get(spreadsheetId=sheet_id,range="'Versões'!A1:B100").execute()
    rows = result.get('values', [])
    dfin = pd.DataFrame(rows)
    dfin.columns = dfin.iloc[0]
    dfin=dfin.drop(dfin.index[0])
    dfin=dfin.reset_index(drop=True)
    df = dfin.iloc[-1:]
    c_version = df.iloc[0, 0]
    return c_version

def download_files():
    # Baixar arquivos pasta tools
    file = io.BytesIO()
    results = service_drive.files().list(
                q=f"'<link drive>' in parents",
                pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])    

    if not items:
        print('No files found.')
    else:
        for item in items:
            file_name = item['name']
            file_id = item['id']
            if file_name == 'tool.py':
                request = service_drive.files().get_media(fileId=file_id)
                file = io.BytesIO(request.execute())
                with io.open(os.path.join(current_dir, file_name), "wb") as f:
                    shutil.copyfileobj(file, f)
                print(f"Download de {file_name} completo.")
            else:
                request = service_drive.files().get_media(fileId=file_id)
                file = io.BytesIO(request.execute())
                with io.open(os.path.join(tools_folder, file_name), "wb") as f:
                    shutil.copyfileobj(file, f)
                print(f"Download de {file_name} completo.")
    # Baixar arquivos pasta bin
    file = io.BytesIO()
    results = service_drive.files().list(
                q=f"'<link drive>' in parents",
                pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])    

    if not items:
        print('No files found.')
    else:
        for item in items:
            file_name = item['name']
            file_id = item['id']

            request = service_drive.files().get_media(fileId=file_id)
            file = io.BytesIO(request.execute())
            with io.open(os.path.join(bin_folder, file_name), "wb") as f:
                shutil.copyfileobj(file, f)
            print(f"Download de {file_name} completo.")

# Função para obter as credenciais do usuário
def get_credentials():
    while True:
        # Chama uma função "clear()" para limpar a tela do console
        clear()
        print('[Enter your credentials]\n')
        user = input("username: ")
        password = getpass.getpass()
        
        # Chama a função "check_login()" para verificar as credenciais
        if database.data_credentials.check_login(user, password):
            # Retorna as credenciais se forem válidas
            return user, password 

# Função para salvar as credenciais no arquivo de configuração
def save_credentials(user, password, config_file):
    config = configparser.ConfigParser()
    config['Credentials'] = {'user': user, 'password': password}

    with open(config_file, 'w') as configfile:
        config.write(configfile)

    print('\n[Saved Successfully] Validated credentials.')

def main():
    # Define o caminho para o arquivo de configuração
    config_file = os.path.join(current_dir, 'database\\config.ini') 

    # Verifica se o arquivo de configuração existe
    if os.path.exists(config_file): 
        config = configparser.ConfigParser()
        # Lê as configurações do arquivo
        config.read(config_file) 

        user = config['Credentials']['user']
        password = config['Credentials']['password']

        # Verifica se as credenciais do arquivo são válidas
        if database.data_credentials.check_login(user, password): 
            print('[Login Succeeded] Validated credentials.')
        else:
            # Obtém novas credenciais do usuário
            user, password = get_credentials()
            # Salva as novas credenciais no arquivo
            save_credentials(user, password, config_file) 
    else:
        # Obtém novas credenciais do usuário
        user, password = get_credentials() 
        # Salva as novas credenciais no arquivo
        save_credentials(user, password, config_file) 

    # Verifica a versão local e a versão da cloud, e faz o download caso encontre uma versão nova disponivel
    try:
        l_version = local_version()
    except:
        download_files()
        l_version = local_version()
    c_version = clouf_version()    
    if str(l_version) != str(c_version):
        print(f"Atualizando Scripts")
        # Apaga os arquivos antigos para evitar conflito na hora de baixar os novos
        try:
            # Apaga arquivo de versão
            os.remove(os.path.join(bin_folder, 'config.bin')) 

            for f in os.listdir(tools_folder):
                # Apaga todos arquivos na pasta tools
                os.remove(os.path.join(tools_folder, f)) 
        except:
            pass     
        download_files()

    frutaria.main()

if __name__ == '__main__':
    main()