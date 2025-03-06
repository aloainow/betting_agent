import os
import glob
import shutil

def clear_all_caches():
    """Limpa todos os caches do aplicativo para resolver problemas persistentes"""
    
    # Diretório de dados (ajuste se necessário)
    DATA_DIR = "data"
    if "RENDER" in os.environ:
        DATA_DIR = "/mnt/value-hunter-data"
    
    print(f"Verificando diretório de dados: {DATA_DIR}")
    
    if not os.path.exists(DATA_DIR):
        print(f"O diretório {DATA_DIR} não existe. Nada a limpar.")
        return
    
    # Diretório de cache de times
    teams_cache_dir = os.path.join(DATA_DIR, "teams_cache")
    if os.path.exists(teams_cache_dir):
        print(f"Limpando diretório de cache de times: {teams_cache_dir}")
        # Opção 1: Remover todo o diretório e recriar (mais simples)
        try:
            shutil.rmtree(teams_cache_dir)
            os.makedirs(teams_cache_dir, exist_ok=True)
            print(f"Diretório de cache de times limpo e recriado com sucesso.")
        except Exception as e:
            print(f"Erro ao limpar diretório: {str(e)}")
            
            # Opção 2: Tentar remover arquivos individualmente
            try:
                for cache_file in glob.glob(os.path.join(teams_cache_dir, "*.json")):
                    try:
                        os.remove(cache_file)
                        print(f"Removido: {os.path.basename(cache_file)}")
                    except Exception as e2:
                        print(f"Erro ao remover {cache_file}: {str(e2)}")
            except Exception as e2:
                print(f"Erro ao limpar arquivos individuais: {str(e2)}")
    else:
        print(f"Diretório de cache de times não encontrado: {teams_cache_dir}")
        os.makedirs(teams_cache_dir, exist_ok=True)
        print(f"Diretório de cache de times criado.")
    
    # Arquivos de cache HTML
    html_cache_files = glob.glob(os.path.join(DATA_DIR, "cache_*.html"))
    if html_cache_files:
        print(f"Removendo {len(html_cache_files)} arquivos de cache HTML...")
        for cache_file in html_cache_files:
            try:
                os.remove(cache_file)
                print(f"Removido: {os.path.basename(cache_file)}")
            except Exception as e:
                print(f"Erro ao remover {cache_file}: {str(e)}")
    else:
        print("Nenhum arquivo de cache HTML encontrado.")
    
    # Outros arquivos de cache, se houver
    other_cache_files = glob.glob(os.path.join(DATA_DIR, "*.cache"))
    if other_cache_files:
        print(f"Removendo {len(other_cache_files)} outros arquivos de cache...")
        for cache_file in other_cache_files:
            try:
                os.remove(cache_file)
                print(f"Removido: {os.path.basename(cache_file)}")
            except Exception as e:
                print(f"Erro ao remover {cache_file}: {str(e)}")
    
    print("Limpeza de cache concluída.")
    print("Reinicie o aplicativo para aplicar as alterações.")

if __name__ == "__main__":
    print("Iniciando limpeza de todos os caches...")
    clear_all_caches()
