from datetime import datetime, timedelta
import time

import pandas as pd
from googleapiclient.discovery import build
import getpass
import os, sys

import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
import numpy as np

def create_table(df):
    tabela_html = df.to_html(index=False, escape=False, classes='table table-bordered', header='true')
    tabela_html = tabela_html.replace('<thead>', '<thead style="text-align: center;">')

    return tabela_html

def plot_and_save_to_pdf(dataframe, pdf_content):
    if pdf_content[0] == 1:
        country = pdf_content[1]

        # Cria uma nova figura e eixo
        plt.figure()
        # Cria um gráfico de barras
        plt.bar(dataframe['PRODUTO'], dataframe['QUANTIDADE'])
        plt.xlabel('PRODUTO')
        plt.ylabel('QUANTIDADE')
        plt.title(f'País - {country}')

        # Salva o gráfico como PDF
        plt.savefig(f'{country}.pdf', format='pdf')
        
        # Fecha a figura para evitar sobreposição
        plt.close()

    elif pdf_content[0] == 2:
        manager = pdf_content[1]

        # Cria uma nova figura e eixo
        plt.figure()
        # Cria um gráfico de barras
        plt.bar(dataframe['PRODUTO'], dataframe['QUANTIDADE'])
        plt.xlabel('PRODUTO')
        plt.ylabel('QUANTIDADE')
        plt.title(f'Gerente - {manager}')

        # Salva o gráfico como PDF
        plt.savefig(f'{manager}.pdf', format='pdf')
        
        # Fecha a figura para evitar sobreposição
        plt.close()
        
    elif pdf_content[0] == 3:
        branch = pdf_content[1]

        # Cria uma nova figura e eixo
        plt.figure()
        # Cria um gráfico de barras
        plt.bar(dataframe['PRODUTO'], dataframe['QUANTIDADE'])
        plt.xlabel('PRODUTO')
        plt.ylabel('QUANTIDADE')
        plt.title(f'Filial - {branch}')

        # Salva o gráfico como PDF
        plt.savefig(f'{branch}.pdf', format='pdf')
        
        # Fecha a figura para evitar sobreposição
        plt.close()
        
    elif pdf_content[0] == 4:
        c_and_a = f'{", ".join(map(str, dataframe["PAÍS"].unique()))} e sua Disponibilidade'

        # Cria uma nova figura e eixo
        plt.figure()
        # Cria um gráfico de barras
        plt.bar(dataframe['PRODUTO'], dataframe['QUANTIDADE'])
        plt.xlabel('PRODUTO')
        plt.ylabel('QUANTIDADE')
        plt.title(f'{c_and_a}')

        # Salva o gráfico como PDF
        plt.savefig(f'{c_and_a}.pdf', format='pdf')
        
        # Fecha a figura para evitar sobreposição
        plt.close()
        
    elif pdf_content[0] == 5:
        over_than_1000 = pdf_content[1]
        
        # Cria uma nova figura e eixo
        plt.figure()
        # Cria um gráfico de barras
        plt.bar(dataframe['PRODUTO'], dataframe['QUANTIDADE'])
        plt.xlabel('PRODUTO')
        plt.ylabel('QUANTIDADE')
        plt.title(f'{over_than_1000}')

        # Salva o gráfico como PDF
        plt.savefig(f'{over_than_1000}.pdf', format='pdf')
        
        # Fecha a figura para evitar sobreposição
        plt.close()
    
    elif pdf_content[0] == 6:
        # Criação de um objeto PDF
        pdf_file = 'All_table.pdf'
        
        # Cria uma figura com tamanho personalizado
        fig, ax = plt.subplots(figsize=(8, 6))

        # Remove eixos da figura para que apenas a tabela seja exibida
        ax.axis('off')

        # Ajusta o layout da tabela usando cellLoc
        table = ax.table(cellText=dataframe.values, colLabels=dataframe.columns, loc='center', cellLoc='center')

        # Ajusta automaticamente a largura das colunas com base no conteúdo
        table.auto_set_column_width(col=list(range(len(dataframe.columns))))

        # Salva a figura como PDF
        plt.savefig(pdf_file, format='pdf', bbox_inches='tight')

        table.remove()
    
    print("\nPDF file created successfully!")

def main(pdf_content):
    current_dir = os.path.realpath(os.path.dirname(__file__))
    csv_file = os.path.join(current_dir, 'frutaria.csv')
    df = pd.read_csv(csv_file)
    
    # Criar tabela HTML
    tabela_html = create_table(df)

    plot_and_save_to_pdf(df, pdf_content)

if __name__ == '__main__':
    main()