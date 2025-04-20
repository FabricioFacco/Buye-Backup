import shutil
import os
import json
from datetime import datetime
from colorama import init, Fore, Style
from zipfile import ZipFile

init(autoreset=True)

def corrigir_caminho_json(conteudo):
    if isinstance(conteudo, dict):
        for chave in conteudo:
            if isinstance(conteudo[chave], list):
                conteudo[chave] = [caminho.replace("\\", "\\\\") for caminho in conteudo[chave]]
            elif isinstance(conteudo[chave], str):
                conteudo[chave] = conteudo[chave].replace("\\", "\\\\")
    return conteudo

def criar_config_exemplo(caminho_config):
    exemplo = {
        "origens": [
            "C:\\Exemplo\\Pasta1",
            "C:\\Exemplo\\Pasta2"
        ],
        "destino_base": "C:\\Exemplo\\Backup"
    }
    with open(caminho_config, 'w', encoding='utf-8') as file:
        json.dump(exemplo, file, indent=4)
    print(Fore.YELLOW + f"[INFO] Arquivo {caminho_config} foi criado! Edite ele com seus caminhos de backup.")

def carregar_config(caminho_config):
    if not os.path.exists(caminho_config):
        criar_config_exemplo(caminho_config)
        return None

    try:
        with open(caminho_config, 'r', encoding='utf-8') as file:
            raw_data = file.read().replace("\\", "\\\\")
            conteudo = json.loads(raw_data)
            return corrigir_caminho_json(conteudo)
    except Exception as e:
        print(Fore.RED + f"[ERRO] Falha ao ler {caminho_config}: {e}")
        return None

def exibir_origens(origens, destino_base):
    print(Fore.CYAN + "\n=== CONFIGURAÇÕES ATUAIS ===")
    print(Fore.YELLOW + "Pastas de origem para backup:")
    for i, origem in enumerate(origens, 1):
        print(Fore.YELLOW + f" {i}. {origem}")
    print(Fore.GREEN + f"\nDestino dos backups: {destino_base}\n")

def checar_espaco(destino_base):
    total, usado, livre = shutil.disk_usage(destino_base)
    livre_gb = livre / (1024 ** 3)
    print(Fore.CYAN + f"[INFO] Espaço livre no disco: {livre_gb:.2f} GB")
    if livre_gb < 1:
        print(Fore.RED + "[ERRO] Pouco espaço livre! Recomenda-se ao menos 1GB para backup.")
        return False
    return True

def pasta_modificada_hoje(caminho):
    hoje = datetime.now().date()
    mod_time = datetime.fromtimestamp(os.path.getmtime(caminho)).date()
    return mod_time == hoje

def compactar_pasta(origem, destino_zip):
    with ZipFile(destino_zip, 'w') as zipf:
        for root, _, files in os.walk(origem):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, origem)
                zipf.write(file_path, arcname)

def copiar_pastas_com_log(origens, destino_base):
    data_pasta = datetime.now().strftime("%d-%m-%Y")
    destino_data = os.path.join(destino_base, data_pasta)
    os.makedirs(destino_data, exist_ok=True)

    log_path = os.path.join(destino_data, "log.txt")
    total_pastas = 0
    total_arquivos = 0
    inicio = datetime.now()

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n=== Backup iniciado em {inicio.strftime('%d-%m-%Y %H:%M:%S')} ===\n")
        print(Fore.CYAN + f"\n[INFO] Backup iniciado às {inicio.strftime('%d-%m-%Y %H:%M:%S')}\n")

        for origem in origens:
            if not os.path.exists(origem):
                mensagem = f"[ERRO] Origem não encontrada: {origem}"
                print(Fore.RED + mensagem)
                log.write(mensagem + "\n")
                continue

            for item in os.listdir(origem):
                caminho_completo = os.path.join(origem, item)
                if os.path.isdir(caminho_completo) and pasta_modificada_hoje(caminho_completo):
                    hora = datetime.now().strftime("%Hh%M")
                    nome_zip = f"{item}_{hora}.zip"
                    destino_zip = os.path.join(destino_data, nome_zip)

                    try:
                        compactar_pasta(caminho_completo, destino_zip)
                        pastas = sum(len(dirs) for _, dirs, _ in os.walk(caminho_completo))
                        arquivos = sum(len(files) for _, _, files in os.walk(caminho_completo))
                        total_pastas += pastas
                        total_arquivos += arquivos
                        mensagem = f"[OK] '{item}' compactado ({pastas} pastas, {arquivos} arquivos)"
                        print(Fore.GREEN + mensagem)
                        log.write(mensagem + "\n")
                    except Exception as e:
                        mensagem = f"[ERRO] Falha ao compactar '{item}': {e}"
                        print(Fore.RED + mensagem)
                        log.write(mensagem + "\n")

        fim = datetime.now()
        duracao = fim - inicio
        log.write(f"=== Backup finalizado em {fim.strftime('%d-%m-%Y %H:%M:%S')} ===\n")
        log.write(f"Total de pastas: {total_pastas} | Total de arquivos: {total_arquivos}\n")
        log.write(f"Duração: {duracao}\n")

    print(Fore.CYAN + f"\n=== RESUMO DO BACKUP ===")
    print(Fore.GREEN + f"Total de Pastas Compactadas: {total_pastas}")
    print(Fore.GREEN + f"Total de Arquivos Compactados: {total_arquivos}")
    print(Fore.GREEN + f"Tempo Total: {duracao}")
    print(Fore.CYAN + "Backup concluído com sucesso!\n")

# Programa principal
if __name__ == "__main__":
    config = carregar_config("config.json")
    if config:
        exibir_origens(config["origens"], config["destino_base"])
        if checar_espaco(config["destino_base"]):
            confirm = input(Fore.MAGENTA + "Deseja iniciar o backup? (S/N): ").strip().lower()
            if confirm == "s":
                copiar_pastas_com_log(config["origens"], config["destino_base"])
                input(Fore.CYAN + "\nPressione Enter para sair.")
            else:
                print(Fore.YELLOW + "Backup cancelado pelo usuário.")
