from datetime import datetime, timedelta
import time

import re
import requests

import webbrowser
from google.cloud import bigquery
import pydata_google_auth
import pandas as pd
from googleapiclient.discovery import build
import getpass
import os, sys

# Email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import tools.send_email as send_email,tools.pdf_generator as pdf_generator

import csv

# Limpar tela de prompt
clear = lambda: os.system('cls')

# Credentials
SCOPES =  ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/cloud-platform','https://www.googleapis.com/auth/bigquery',]
CREDENTIALS = pydata_google_auth.get_user_credentials(SCOPES, auth_local_webserver=True)

# Obtenha a data e hora atuais
now = datetime.now()

# Formate a data e hora como uma string para incluir no nome do arquivo
timestamp_str = now.strftime("%Y-%m-%d-%H-%M-%S")

def create_file(content, file_name, dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

    f = open(os.path.join(dir, file_name), 'a')
    f.write(content)

def merge(sheet_id, sheet_range, df, service):

    result = service.spreadsheets().get(spreadsheetId=sheet_id,
                                        ranges=sheet_range,
                                        fields="sheets/merges"
                                        ).execute()
    
    try:
        # obtendo o número de mesclagens
        num_merges = len(result["sheets"][0]["merges"])

        if (num_merges > 0):
            for i in range(num_merges):
                startRowIndex = result['sheets'][0]["merges"][i]['startRowIndex']
                endRowIndex = result['sheets'][0]["merges"][i]['endRowIndex']
                startColumnIndex = result['sheets'][0]["merges"][i]['startColumnIndex']
                endColumnIndex = result['sheets'][0]["merges"][i]['endColumnIndex']

                value_of_merge = df.iat[startRowIndex,startColumnIndex]

                for j in range(startRowIndex+1, endRowIndex):
                    df.iat[j,startColumnIndex] = value_of_merge
    except Exception:
        pass

def remove_unnecessary_fields(df):
    aux_index_list=[]
    index_list=[]
    check_soak_fd_date = False
    for index, row in df.iterrows():
        if (df[0][index][0] == "Produto"):
            for item in row:
                aux_index_list.append(str(item[0]))
            index_list = [c.upper() for c in aux_index_list]
        if (df[0][index][0] == "END"):
            end=index
            break

    df = df.iloc[0:end , :]
    df.columns=index_list
    df = df.drop(df.index[0])
    df = df.reset_index(drop=True)

    return df

def getting_spreadsheet_data(sheet_id, sheet_range, service):
    result=service.spreadsheets().get(spreadsheetId=sheet_id,
                                                        ranges=sheet_range,
                                                        fields="sheets/data/rowData/values",
                                                        ).execute()

    column=0
    row=1
    n_row=len(result['sheets'][0]["data"][0]["rowData"])
    n_col=len(result['sheets'][0]["data"][0]["rowData"][row]['values'])

    total_list=[]
    for row in range(n_row):
        row_list=[]
        for column in range(n_col):
            try:
                content=result['sheets'][0]["data"][0]["rowData"][row]['values'][column]['userEnteredValue']['stringValue']
            except:
                try: 
                    content=result['sheets'][0]["data"][0]["rowData"][row]['values'][column]['userEnteredValue']['numberValue'] 
                except:
                    try:
                        content=str(result['sheets'][0]["data"][0]["rowData"][row]['values'][column]['userEnteredValue']['formulaValue'])
                        content=content.split(',')[1]
                        content=content.replace('"',"").replace(')',"")
                    except:
                        try:
                            content=str(result['sheets'][0]["data"][0]["rowData"][row]['values'][column]['userEnteredValue']['boolValue'])
                        except:
                            content="N/A"
            try:
                link=result['sheets'][0]["data"][0]["rowData"][row]['values'][column]['userEnteredFormat']['textFormat']['link']['uri']
            except:
                link="https://TBD"
            try:
                note=result['sheets'][0]["data"][0]["rowData"][row]['values'][column]['note']
            except:
                note='N/A'

            row_list.append([content,link,note])                
        total_list.append(row_list)
    df=pd.DataFrame(total_list)

    merge(sheet_id, sheet_range, df, service)

    return df

def change_header(df_dastc, row):
    header = tuple((df_dastc.iloc[row]))
    df_dastc.columns = header
    df_dastc = df_dastc.drop(df_dastc.index[row])
    df_dastc = df_dastc.reset_index(drop=True)

    return df_dastc

def vl_aba_index(vl_link, service):
    vl_id = (vl_link.split("/"))[5]
    aba_name_list= []
    sheet_metadata = service.spreadsheets().get(spreadsheetId = vl_id).execute()
    properties = sheet_metadata.get('sheets')
    for  item in properties:
        sheet_name = item.get("properties").get('title')
        aba_name_list.append(sheet_name)
    
    num=0
    yes_or_no = 'n'
    yes_choices = ['yes', 'y', 'sim', 's']
    # no_choices = ['no', 'n']
    while yes_or_no not in yes_choices:
        op='more'
        while op == 'more' or op == 'back':
            clear()
            print("Worksheets available:\n")
            if len(aba_name_list) <= num:
                print("No more options available...")
                num -= lmt  # Go back to the previous set of options
                continue
            lmt = min(15, len(aba_name_list) - num)
            for i in range(num, num + lmt):
                print(f"[{i}] - {aba_name_list[i]}")
            op = input("\nSelect an option: (type 'more' for more options or 'back' to go back): ")
            if op == 'more': num += lmt
            elif op == 'back':
                if num <= 15: num = 0
                else: num -= 15

        print(f"\n{aba_name_list[int(op)]}")

        yes_or_no = (input("Is this option selected correctly? [y/n]: "))

        if yes_or_no.lower() in yes_choices:
            break
        else:
            continue        
    return vl_id,aba_name_list[int(op)]

def menu():
    clear()
    print("Menu:")
    print("\n[1] - Filter by Country\n[2] - Filter by Manager\n[3] - Filter by Branch\n[4] - Filter by Country + Availability\n[5] - Filter by Product >= 1000\n[6] - No filter (Complete Table)\n[0] - Finalizar script")

def actions_menu():
    clear()
    print("Menu:")
    print("\n[1] - Fill out form\n[2] - Create PDF file\n[3] - Send e-mail")
            

def printing_the_current_status(value):
    dot = ''
    for i in range(3):
        dot += '.'
        print(f"\r{value}{dot}", end='')
        time.sleep(0.5)
    print("")

def main():
    real_path = os.path.realpath(os.path.dirname(__file__))

    # definir lista de erros (vazia)
    error = []

    project_id = 'gpd-analytics'
    client = bigquery.Client(project=project_id, credentials=CREDENTIALS)
    service = build('sheets', 'v4', credentials=CREDENTIALS)     
    sheet = service.spreadsheets()

    clear()

    vl_link = input("Enter Google Sheets link: ")
    vl_id, vl_range = vl_aba_index(vl_link, service)

    try:
        df = getting_spreadsheet_data(vl_id, vl_range, service)
        df = remove_unnecessary_fields(df)

        opt = "opt"
        while opt != 0:
            pdf_content = []
            menu()
            opt = int(input("\nEnter the option: "))

            if opt == 1:
                temp_list = df['PAÍS'].tolist()
                country_list = []

                if temp_list:
                    for value in temp_list:
                        if isinstance(value, list) and len(value) > 0:
                            country = value[0]
                            if isinstance(country, str) and country not in country_list:
                                country_list.append(country)

                clear()
                print("Countries available:\n")
                for i in range(len(country_list)):
                    print(f"[{i}] - {country_list[i]}")
                        
                country_opt = int(input("\nEnter country key: "))
                filtered_df = df[df['PAÍS'].apply(lambda x: country_list[country_opt] in x)]
                        
                pdf_content = [1, country_list[country_opt]]

            elif opt == 2:
                temp_list = df['GERENTE'].tolist()
                manager_list = []

                if temp_list:
                    for value in temp_list:
                        if isinstance(value, list) and len(value) > 0:
                            manager_name = value[0]
                            if isinstance(manager_name, str) and manager_name not in manager_list:
                                manager_list.append(manager_name)

                clear()
                print("Managers available:\n")
                for i in range(len(manager_list)):
                    print(f"[{i}] - {manager_list[i]}")
                        
                manager_opt = int(input("\nEnter the option: "))
                filtered_df = df[df['GERENTE'].apply(lambda x: manager_list[manager_opt] in x)]

                
                pdf_content = [2, manager_list[manager_opt]]

            elif opt == 3:
                temp_list = df['FILIAL'].tolist()
                branch_list = []

                if temp_list:
                    for value in temp_list:
                        if isinstance(value, list) and len(value) > 0:
                            branch = value[0]
                            if isinstance(branch, str) and branch not in branch_list:
                                branch_list.append(branch)

                clear()
                print("Branches available:\n")
                for i in range(len(branch_list)):
                    print(f"[{i}] - {branch_list[i]}")
                        
                branch_opt = int(input("\nEnter the option: "))
                filtered_df = df[df['FILIAL'].apply(lambda x: branch_list[branch_opt] in x)]
                
                pdf_content = [3, branch_list[branch_opt]]

            elif opt == 4:
                temp_list = df['PAÍS'].tolist()
                country_and_available_list = []

                if temp_list:
                    for value in temp_list:
                        if isinstance(value, list) and len(value) > 0:
                            country_and_available = value[0]
                            if isinstance(country_and_available, str) and country_and_available not in country_and_available_list:
                                country_and_available_list.append(country_and_available)
                
                clear()
                print("Countries available:\n")
                for i in range(len(country_and_available_list)):
                    print(f"[{i}] - {country_and_available_list[i]}")
                        
                country_and_available_opt = int(input("\nEnter country key: "))
                filtered_df = df[df['PAÍS'].apply(lambda x: country_and_available_list[country_and_available_opt] in x) & df['DISPONIBILIDADE'].apply(lambda x: 'True' in x)]
                
                pdf_content = [4, country_and_available_list[country_and_available_opt]]

            elif opt == 5:
                filtered_df = df[(df['QUANTIDADE'].apply(lambda x: x[0] if isinstance(x, list) else 0) >= 1000) & (df['DISPONIBILIDADE'].apply(lambda x: 'True' in x))]
                
                pdf_content = [5, 'Maior ou igual a 1000 unidades.']

            elif opt == 6:
                filtered_df = df
                
                pdf_content = [6, 'Full table.']

            elif opt == 0:
                sys.exit()
            
            else:
                print("\nOption not found.")
                exit()
                

            print('\n')
            printing_the_current_status("Collecting and storing data")
            time.sleep(2)
            
            while True:
                actions_menu()
                opt_action = int(input("\nEnter the option: "))
                
                if opt_action in [1, 2, 3]:
                    # Sai do loop se a opção for válida
                    break 
                else:
                    print("Option not found. Please choose 1, 2 or 3.")
            
            if opt_action == 2 or opt_action == 3:
                csv_data = []
            
            for index, row in filtered_df.iterrows():

                product_name = filtered_df['PRODUTO'][index][0]
                amount = filtered_df['QUANTIDADE'][index][0]
                price = str(filtered_df['PREÇO'][index][0]).split("R$")[1]
                link = filtered_df['LINK'][index][1]
                availability = filtered_df['DISPONIBILIDADE'][index][0]
                country = filtered_df['PAÍS'][index][0]
                branch = filtered_df['FILIAL'][index][0]
                manager = filtered_df['GERENTE'][index][0]

                if str(availability).upper() == "TRUE":
                    availability = "yes"
                else:
                    availability = "no"

                if opt_action == 1:
                    create_link = f'http://127.0.0.1:5500/forms.html?produto={product_name}&quantidade={amount}&preco={price}&link={link}&disponibilidade={availability}&pais={country}&filial={branch}&gerente={manager}'
                    webbrowser.open(create_link)

                elif opt_action == 2:
                    csv_row = [product_name, amount, price, link, availability, country, branch, manager]
                    csv_data.append(csv_row)

                elif opt_action == 3:
                    csv_row = [product_name, amount, price, link, availability, country, branch, manager]
                    csv_data.append(csv_row)
                    
            if opt_action == 2 or opt_action == 3:
                # Especifique o nome do arquivo CSV
                csv_filename = 'tools\\frutaria.csv'
                # Escreva os dados no arquivo CSV
                with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    # Criar um objeto de escrita CSV
                    csv_writer = csv.writer(csvfile)

                    # Defini cabeçalho
                    csv_writer.writerow(['PRODUTO', 'QUANTIDADE', 'PREÇO (R$)', 'LINK', 'DISPONIBILIDADE', 'PAÍS', 'FILIAL', 'GERENTE'])

                    # Escreva as linhas de dados
                    csv_writer.writerows(csv_data)
                
                if opt_action == 2:
                    pdf_generator.main(pdf_content)
                
                elif opt_action == 3:
                    send_email.main(pdf_content)
            
            input("\nPress Enter key to continue...")

    except Exception as e:
                error = (f"{e}")
                print(error)

if __name__ == '__main__':
    main()