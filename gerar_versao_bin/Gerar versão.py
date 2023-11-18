import os
import pickle


current_dir = os.path.realpath(os.path.dirname(__file__))
caminho_arquivo = os.path.join(current_dir, 'config.bin')
# Define o número a ser salvo no arquivo binário
numero = input("Qual o numero da versão? ex: (1.0 / 1.1 / 2.4)")

# Serializa o número usando a biblioteca pickle
numero_serializado = pickle.dumps(numero)

# Salva o número serializado em um arquivo binário
with open(caminho_arquivo, 'wb') as arquivo:
    arquivo.write(numero_serializado)

print(f"Arquivo config.bin criado com a versão {numero}")