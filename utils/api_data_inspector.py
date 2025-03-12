"""
API Data Inspector - Ferramenta para diagnóstico de dados da API FootyStats

Este script analisa os dados recebidos da API FootyStats e ajuda a identificar problemas
na estrutura de dados que possam estar causando falhas na análise.

Uso:
1. Salve em um arquivo separado para diagnóstico
2. Adicione chamadas para suas funções principais em modo DEBUG
3. Analise a saída para entender como os dados estão estruturados
"""

import json
import logging
import pprint
import os
import sys
import pandas as pd
import streamlit as st

# Configuring logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("valueHunter.inspector")

def inspect_data(data, title="API Data Inspection", output_file=None):
    """
    Analisa detalhadamente a estrutura e conteúdo de dados de API
    
    Args:
        data: Objeto de dados a ser analisado
        title (str): Título para o relatório
        output_file (str, optional): Caminho para arquivo de saída
    """
    # Preparar saída
    output = ["=" * 80]
    output.append(f" {title} ".center(80, "="))
    output.append("=" * 80 + "\n")
    
    # Função para imprimir de forma detalhada
    pp = pprint.PrettyPrinter(indent=2)
    
    # 1. Tipo de dado básico
    output.append(f"Tipo de dado: {type(data).__name__}\n")
    
    # 2. Analisar estrutura baseada no tipo
    if isinstance(data, dict):
        # Analisar dicionário
        output.append(f"Número de chaves: {len(data)}")
        output.append("Chaves no nível superior:")
        for key in sorted(data.keys()):
            value = data[key]
            value_type = type(value).__name__
            
            # Para valores simples, mostrar o valor
            if isinstance(value, (str, int, float, bool)) or value is None:
                output.append(f"  - {key} ({value_type}): {value}")
            # Para listas, mostrar tamanho
            elif isinstance(value, list):
                output.append(f"  - {key} (list): {len(value)} itens")
                # Verificar o primeiro item
                if value and len(value) > 0:
                    first_item_type = type(value[0]).__name__
                    output.append(f"    Primeiro item é do tipo: {first_item_type}")
                    if isinstance(value[0], dict) and len(value[0]) < 10:
                        output.append(f"    Amostra: {value[0]}")
            # Para dicionários, mostrar suas chaves
            elif isinstance(value, dict):
                output.append(f"  - {key} (dict): {len(value)} chaves")
                # Mostrar as chaves do dicionário interno
                if value:
                    output.append(f"    Chaves: {', '.join(sorted(value.keys()))}")
            else:
                output.append(f"  - {key} ({value_type})")
        
        # Procurar e analisar objetos aninhados importantes
        if "basic_stats" in data:
            output.append("\nAnálise de Dados Básicos:")
            basic_stats = data["basic_stats"]
            
            # Analisar estatísticas do time da casa
            if "home_team" in basic_stats:
                home_team = basic_stats["home_team"]
                output.append(f"\nTime da Casa: {home_team.get('name', 'Desconhecido')}")
                
                if "stats" in home_team and isinstance(home_team["stats"], dict):
                    home_stats = home_team["stats"]
                    output.append("  Estatísticas disponíveis:")
                    
                    # Verificar valores não-zero
                    non_zero_stats = {}
                    zero_stats = {}
                    
                    for key, value in home_stats.items():
                        if isinstance(value, (int, float)) and value != 0:
                            non_zero_stats[key] = value
                        elif isinstance(value, (int, float)):
                            zero_stats[key] = value
                    
                    # Mostrar estatísticas não-zero
                    output.append(f"  Estatísticas NÃO-ZERO ({len(non_zero_stats)}):")
                    for key, value in non_zero_stats.items():
                        output.append(f"    - {key}: {value}")
                    
                    # Mostrar algumas estatísticas zero (limitar a 10)
                    output.append(f"  Estatísticas ZERO ({len(zero_stats)}):")
                    for i, (key, value) in enumerate(zero_stats.items()):
                        if i < 10:  # Mostrar apenas 10 exemplos
                            output.append(f"    - {key}: {value}")
                        else:
                            output.append(f"    - ... e mais {len(zero_stats) - 10} estatísticas zeradas")
                            break
            
            # Analisar estatísticas do time visitante
            if "away_team" in basic_stats:
                away_team = basic_stats["away_team"]
                output.append(f"\nTime Visitante: {away_team.get('name', 'Desconhecido')}")
                
                if "stats" in away_team and isinstance(away_team["stats"], dict):
                    away_stats = away_team["stats"]
                    output.append("  Estatísticas disponíveis:")
                    
                    # Verificar valores não-zero
                    non_zero_stats = {}
                    zero_stats = {}
                    
                    for key, value in away_stats.items():
                        if isinstance(value, (int, float)) and value != 0:
                            non_zero_stats[key] = value
                        elif isinstance(value, (int, float)):
                            zero_stats[key] = value
                    
                    # Mostrar estatísticas não-zero
                    output.append(f"  Estatísticas NÃO-ZERO ({len(non_zero_stats)}):")
                    for key, value in non_zero_stats.items():
                        output.append(f"    - {key}: {value}")
                    
                    # Mostrar algumas estatísticas zero (limitar a 10)
                    output.append(f"  Estatísticas ZERO ({len(zero_stats)}):")
                    for i, (key, value) in enumerate(zero_stats.items()):
                        if i < 10:  # Mostrar apenas 10 exemplos
                            output.append(f"    - {key}: {value}")
                        else:
                            output.append(f"    - ... e mais {len(zero_stats) - 10} estatísticas zeradas")
                            break
        
        # Analisar histórico H2H
        if "head_to_head" in data:
            h2h = data["head_to_head"]
            output.append("\nAnálise de Head-to-Head:")
            if isinstance(h2h, dict):
                if h2h:
                    output.append(f"  Chaves disponíveis: {', '.join(sorted(h2h.keys()))}")
                    # Analisar valores numéricos não-zero
                    non_zero_h2h = {k: v for k, v in h2h.items() if isinstance(v, (int, float)) and v != 0}
                    if non_zero_h2h:
                        output.append(f"  Valores não-zero: {non_zero_h2h}")
                    else:
                        output.append("  Não há valores não-zero nos dados H2H")
                else:
                    output.append("  Objeto H2H vazio")
            else:
                output.append(f"  Tipo inesperado: {type(h2h).__name__}")
                
        # Analisar estatísticas avançadas
        if "advanced_stats" in data:
            output.append("\nAnálise de Estatísticas Avançadas:")
            advanced = data["advanced_stats"]
            
            for team_type in ["home", "away"]:
                if team_type in advanced:
                    team_advanced = advanced[team_type]
                    output.append(f"\n  {team_type.capitalize()}:")
                    
                    if isinstance(team_advanced, dict):
                        if team_advanced:
                            # Contagem de valores não-zero
                            non_zero_vals = sum(1 for v in team_advanced.values() 
                                               if isinstance(v, (int, float)) and v != 0)
                            
                            output.append(f"    Total de métricas: {len(team_advanced)}")
                            output.append(f"    Métricas não-zero: {non_zero_vals}")
                            
                            # Mostrar as métricas não-zero
                            if non_zero_vals > 0:
                                output.append("    Métricas não-zero disponíveis:")
                                for key, value in team_advanced.items():
                                    if isinstance(value, (int, float)) and value != 0:
                                        output.append(f"      - {key}: {value}")
                        else:
                            output.append("    Objeto de estatísticas avançadas vazio")
                    else:
                        output.append(f"    Tipo inesperado: {type(team_advanced).__name__}")
    
    elif isinstance(data, list):
        output.append(f"Lista com {len(data)} itens")
        
        if data:
            # Analisar o primeiro item
            first_item = data[0]
            output.append(f"Tipo do primeiro item: {type(first_item).__name__}")
            
            if isinstance(first_item, dict):
                output.append(f"Chaves no primeiro item: {sorted(first_item.keys())}")
    
    elif isinstance(data, pd.DataFrame):
        output.append("DataFrame pandas")
        output.append(f"Dimensões: {data.shape}")
        output.append(f"Colunas: {list(data.columns)}")
        
        # Analisar valores não-nulos
        non_null_counts = data.count()
        output.append("\nContagem de valores não-nulos por coluna:")
        for col, count in non_null_counts.items():
            output.append(f"  - {col}: {count}/{len(data)}")
            
        # Analisar valores diferentes de zero
        output.append("\nContagem de valores não-zero por coluna:")
        for col in data.columns:
            if pd.api.types.is_numeric_dtype(data[col]):
                non_zero = (data[col] != 0).sum()
                output.append(f"  - {col}: {non_zero}/{len(data)}")
    
    # 3. Recomendações 
    output.append("\nRECOMENDAÇÕES:")
    
    # Verificar se existem estatísticas reais
    has_stats = False
    if isinstance(data, dict):
        if "basic_stats" in data:
            home_team = data["basic_stats"].get("home_team", {})
            away_team = data["basic_stats"].get("away_team", {})
            
            home_stats = home_team.get("stats", {})
            away_stats = away_team.get("stats", {})
            
            # Verificar por valores não-zero
            home_non_zero = any(isinstance(v, (int, float)) and v != 0 for v in home_stats.values())
            away_non_zero = any(isinstance(v, (int, float)) and v != 0 for v in away_stats.values())
            
            has_stats = home_non_zero or away_non_zero
    
    if has_stats:
        output.append("✅ Existem estatísticas reais não-zero nos dados")
    else:
        output.append("❌ Todas as estatísticas são zero ou vazias")
        output.append("   Recomendação: Verificar se a API está retornando dados reais")
        output.append("   Usar valores default para análise básica")
    
    # Imprimir o relatório
    output_str = "\n".join(output)
    print(output_str)
    
    # Salvar em arquivo se solicitado
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_str)
        print(f"Relatório salvo em: {output_file}")
    
    return output_str

def test_enhanced_api_client():
    """
    Teste da função get_complete_match_analysis do enhanced_api_client
    """
    from utils.enhanced_api_client import get_complete_match_analysis
    
    # Liga e times conhecidos para testar
    test_leagues = [
        {"name": "Premier League", "id": 12325, "teams": ["Manchester City", "Arsenal"]},
        {"name": "La Liga", "id": 12316, "teams": ["Barcelona", "Real Madrid"]}
    ]
    
    for league in test_leagues:
        league_name = league["name"]
        season_id = league["id"]
        teams = league["teams"]
        
        if len(teams) >= 2:
            home_team, away_team = teams[0], teams[1]
            
            print(f"\nTestando análise para {home_team} vs {away_team} na liga {league_name}")
            
            # Realizar análise
            analysis = get_complete_match_analysis(home_team, away_team, season_id)
            
            if analysis:
                # Salvar os dados brutos para análise
                output_file = f"debug_{league_name.replace(' ', '_')}_{home_team.replace(' ', '_')}_{away_team.replace(' ', '_')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, indent=2)
                print(f"Dados salvos em: {output_file}")
                
                # Analisar os dados
                inspect_data(analysis, f"Análise de {home_team} vs {away_team} na liga {league_name}")
            else:
                print(f"❌ Falha ao obter dados para {home_team} vs {away_team}")

def add_inspection_to_streamlit():
    """
    Adiciona funções de inspeção para usar com Streamlit
    """
    def inspect_api_data():
        """
        Função para ser chamada de dentro de um app Streamlit
        """
        st.write("### Diagnóstico de Dados da API")
        
        if st.button("Executar Diagnóstico", key="run_diag"):
            if "complete_analysis" in st.session_state:
                analysis = st.session_state.complete_analysis
                results = inspect_data(analysis, "Análise de Dados da API Atual")
                st.code(results, language="text")
            else:
                st.error("Não há dados de análise disponíveis na sessão")
    
    return inspect_api_data

def inspect_prompt_data(complete_analysis, home_team, away_team, odds_data, selected_markets):
    """
    Testa o formato do prompt com os dados reais
    """
    from utils.ai import format_enhanced_prompt
    
    # Gerar o prompt
    prompt = format_enhanced_prompt(complete_analysis, home_team, away_team, odds_data, selected_markets)
    
    # Analisar o prompt
    print("\n" + "=" * 80)
    print(" ANÁLISE DO PROMPT ".center(80, "="))
    print("=" * 80 + "\n")
    
    # Verificar se existem dados estatísticos no prompt
    import re
    
    # Procurar por estatísticas numéricas não-zero
    stats_pattern = r'([A-Za-z\s]+): (\d+\.?\d*)'
    matches = re.findall(stats_pattern, prompt)
    
    non_zero_stats = [(name, float(value)) for name, value in matches if float(value) > 0]
    total_stats = len(matches)
    
    print(f"Estatísticas totais encontradas no prompt: {total_stats}")
    print(f"Estatísticas não-zero: {len(non_zero_stats)}")
    
    if non_zero_stats:
        print("\nExemplos de estatísticas não-zero:")
        for name, value in non_zero_stats[:10]:  # Mostrar até 10 exemplos
            print(f"  - {name.strip()}: {value}")
    
    # Salvar o prompt para análise
    prompt_file = f"debug_prompt_{home_team.replace(' ', '_')}_{away_team.replace(' ', '_')}.txt"
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    print(f"\nPrompt completo salvo em: {prompt_file}")
    
    return len(non_zero_stats) / total_stats if total_stats > 0 else 0

def add_api_debug_utils_to_dashboard():
    """
    Retorna funções de debug para adicionar ao app
    """
    def debug_api_data(complete_analysis, home_team, away_team, odds_data, selected_markets=None):
        """
        Função para ser chamada no app Streamlit quando dados são recebidos
        """
        # Criar diretório de debug
        debug_dir = "debug_output"
        os.makedirs(debug_dir, exist_ok=True)
        
        # Nome de arquivo único para esta análise
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{debug_dir}/api_data_{home_team.replace(' ', '_')}_{away_team.replace(' ', '_')}_{timestamp}.json"
        
        # Salvar dados completos em JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(complete_analysis, f, indent=2)
        
        # Analisar dados
        analysis_file = f"{debug_dir}/analysis_{home_team.replace(' ', '_')}_{away_team.replace(' ', '_')}_{timestamp}.txt"
        inspect_data(complete_analysis, f"Análise de {home_team} vs {away_team}", analysis_file)
        
        # Se tivermos mercados selecionados, testar a geração do prompt
        if selected_markets is not None:
            prompt_quality = inspect_prompt_data(complete_analysis, home_team, away_team, odds_data, selected_markets)
            return filename, analysis_file, prompt_quality
        
        return filename, analysis_file, None
    
    return debug_api_data

# Função principal para usar como script independente
def main():
    """
    Executa testes independentes
    """
    print("=== API Data Inspector ===")
    print("Escolha uma opção:")
    print("1. Testar enhanced_api_client")
    print("2. Analisar arquivo JSON existente")
    print("3. Sair")
    
    choice = input("Opção: ")
    
    if choice == "1":
        test_enhanced_api_client()
    elif choice == "2":
        file_path = input("Caminho para o arquivo JSON: ")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            inspect_data(data, f"Análise de {file_path}")
        else:
            print(f"Arquivo não encontrado: {file_path}")
    else:
        print("Saindo...")
        return

if __name__ == "__main__":
    main()
