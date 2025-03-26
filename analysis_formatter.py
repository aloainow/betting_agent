import re
import streamlit as st
import pandas as pd
import logging

logger = logging.getLogger("valueHunter.analysis_display")

def parse_analysis_response(analysis_text):
    """
    Extrai dados estruturados da resposta textual da IA
    
    Args:
        analysis_text (str): Texto da análise gerada pela IA
    
    Returns:
        dict: Dados estruturados extraídos da análise
    """
    # Inicializar estrutura para armazenar os dados extraídos
    data = {
        "title": "",
        "opportunities": [],
        "probabilities": {
            "money_line": [],
            "over_under": [],
            "chance_dupla": [],
            "ambos_marcam": []
        },
        "confidence": {
            "level": "",
            "teams_consistency": {},
            "recent_form": {},
            "observations": []
        }
    }
    
    try:
        # Extrair título (times da partida)
        title_match = re.search(r'# Análise da Partida\s*\n## ([^\n]+)', analysis_text)
        if title_match:
            data["title"] = title_match.group(1).strip()
        
        # Extrair oportunidades identificadas
        opp_section = extract_section(analysis_text, "# Oportunidades Identificadas")
        if opp_section:
            # Procurar por padrões como "**Money Line** | Albacete Balompié | @2.01 | +1.8% | ⭐⭐"
            # Ou "- **Money Line**: Albacete Balompié (@2.01) - Vantagem: +1.8% - Confiança: ⭐⭐"
            opportunities = []
            
            # Tentar o padrão com barras verticais primeiro
            pattern1 = r'\*\*([\w\s]+)\*\* \| ([\w\s]+) \| @([\d\.]+) \| \+([\d\.]+)% \| (⭐+)'
            matches = re.findall(pattern1, opp_section)
            
            if matches:
                for match in matches:
                    opportunities.append({
                        "mercado": match[0].strip(),
                        "selecao": match[1].strip(),
                        "odds": float(match[2]),
                        "vantagem": float(match[3]),
                        "confianca": len(match[4])  # Número de estrelas
                    })
            else:
                # Tentar padrão alternativo com hífens
                pattern2 = r'- \*\*([\w\s]+)\*\*:?\s+([\w\s]+) \(@([\d\.]+)\).+Vantagem: \+([\d\.]+)%.+Confiança: (⭐+)'
                matches = re.findall(pattern2, opp_section)
                
                # Se ainda não encontrou, tentar um padrão mais genérico
                if not matches:
                    pattern3 = r'\*\*([\w\s/]+)\*\*:?\s+([\w\s]+).+@([\d\.]+).+\+([\d\.]+)%'
                    matches = re.findall(pattern3, opp_section)
                    
                    if matches:
                        for match in matches:
                            # Estimar nível de confiança pela vantagem
                            vantagem = float(match[3])
                            confianca = 2
                            if vantagem > 15:
                                confianca = 4
                            elif vantagem > 10:
                                confianca = 3
                            elif vantagem < 3:
                                confianca = 1
                                
                            opportunities.append({
                                "mercado": match[0].strip(),
                                "selecao": match[1].strip(),
                                "odds": float(match[2]),
                                "vantagem": vantagem,
                                "confianca": confianca
                            })
                
                # Se encontrou com o segundo padrão, processar
                if matches:
                    for match in matches:
                        opportunities.append({
                            "mercado": match[0].strip(),
                            "selecao": match[1].strip(),
                            "odds": float(match[2]),
                            "vantagem": float(match[3]),
                            "confianca": len(match[4])  # Número de estrelas
                        })
            
            # Extrair manualmente se os padrões não funcionarem
            if not opportunities:
                # Dividir por linhas e procurar por mercados conhecidos
                for line in opp_section.split('\n'):
                    if '**Money Line**' in line or '**Over/Under**' in line or '**Chance Dupla**' in line or '**Ambos Marcam**' in line:
                        parts = line.split('|') if '|' in line else line.split('-')
                        if len(parts) >= 3:
                            mercado = extract_text_between_asterisks(parts[0])
                            selecao = parts[1].strip() if '|' in line else extract_text_without_parentheses(parts[1])
                            
                            # Extrair odds
                            odds_match = re.search(r'@([\d\.]+)', line)
                            odds = float(odds_match.group(1)) if odds_match else 0.0
                            
                            # Extrair vantagem
                            vantagem_match = re.search(r'\+([\d\.]+)%', line)
                            vantagem = float(vantagem_match.group(1)) if vantagem_match else 0.0
                            
                            # Extrair confiança
                            confianca_match = re.search(r'(⭐+)', line)
                            confianca = len(confianca_match.group(1)) if confianca_match else 0
                            
                            # Se não encontrou estrelas, estimar pela vantagem
                            if confianca == 0:
                                if vantagem > 15:
                                    confianca = 4
                                elif vantagem > 10:
                                    confianca = 3
                                elif vantagem > 5:
                                    confianca = 2
                                else:
                                    confianca = 1
                            
                            opportunities.append({
                                "mercado": mercado,
                                "selecao": selecao,
                                "odds": odds,
                                "vantagem": vantagem,
                                "confianca": confianca
                            })
            
            # Atualizar oportunidades
            data["opportunities"] = opportunities
        
        # Extrair probabilidades
        prob_section = extract_section(analysis_text, "# Probabilidades Calculadas")
        if prob_section:
            # Processar as diferentes seções de mercados
            markets = ["Money", "Over/Under", "Chance Dupla", "Ambos Marcam"]
            market_keys = ["money_line", "over_under", "chance_dupla", "ambos_marcam"]
            
            for i, market in enumerate(markets):
                market_section = extract_section(prob_section, f"### {market}", include_title=False, end_marker="###")
                
                if market_section:
                    # Extrair probabilidades e comparativos
                    probabilities = []
                    
                    # Extrair por linhas
                    for line in market_section.split('\n'):
                        if '*' in line and '%' in line and ':' in line:
                            # Formato esperado: "* Resultado: XX% (Diferença: +/-XX%)"
                            parts = line.split(':')
                            if len(parts) >= 2:
                                resultado = parts[0].replace('*', '').strip()
                                
                                # Extrair probabilidade implícita
                                prob_match = re.search(r'([0-9.]+)%', parts[1])
                                prob_impl = float(prob_match.group(1)) if prob_match else 0.0
                                
                                # Extrair probabilidade real e diferença
                                prob_real = 0.0
                                diferenca = 0.0
                                
                                # Procurar por "Prob. Real: XX%"
                                real_match = re.search(r'Real: ([0-9.]+)%', line)
                                if real_match:
                                    prob_real = float(real_match.group(1))
                                
                                # Procurar por "Diferença: +/-XX%"
                                diff_match = re.search(r'Diferença: ([+-][0-9.]+)%', line)
                                if diff_match:
                                    diferenca = float(diff_match.group(1))
                                
                                # Se probabilidade real não encontrada mas diferença sim, calcular real
                                if prob_real == 0.0 and diferenca != 0.0:
                                    prob_real = prob_impl + diferenca
                                
                                # Calcular diferença se não encontrada
                                if diferenca == 0.0 and prob_real != 0.0:
                                    diferenca = prob_real - prob_impl
                                
                                # Se não temos probabilidade real, assumir implícita
                                if prob_real == 0.0:
                                    # Buscar valor explícito
                                    real_expl_match = re.search(r'(\d+\.\d+)%.*?\(([+-]\d+\.\d+)%\)', line)
                                    if real_expl_match:
                                        prob_impl = float(real_expl_match.group(1))
                                        diferenca = float(real_expl_match.group(2))
                                        prob_real = prob_impl + diferenca
                                    else:
                                        prob_real = prob_impl
                                
                                # Determinar se é vantajoso (check mark ou x)
                                vantajoso = '✅' if diferenca > 0 else '❌'
                                
                                probabilities.append({
                                    "resultado": resultado,
                                    "odds": 0.0,  # Odds não disponível aqui, será preenchido depois
                                    "prob_impl": prob_impl,
                                    "prob_real": prob_real,
                                    "diferenca": diferenca,
                                    "vantajoso": vantajoso
                                })
                    
                    # Se não encontrou por esse método, tentar uma abordagem mais simples
                    if not probabilities:
                        # Procurar linhas com percentuais
                        lines = [line.strip() for line in market_section.split('\n') if '%' in line and '*' in line]
                        
                        for line in lines:
                            result_match = re.search(r'\* (.+?):', line)
                            if result_match:
                                resultado = result_match.group(1).strip()
                                
                                # Extrair percentuais
                                percentages = re.findall(r'(\d+\.\d+)%', line)
                                
                                if len(percentages) >= 1:
                                    prob_impl = float(percentages[0])
                                    prob_real = float(percentages[1]) if len(percentages) >= 2 else prob_impl
                                    diferenca = prob_real - prob_impl
                                    vantajoso = '✅' if diferenca > 0 else '❌'
                                    
                                    probabilities.append({
                                        "resultado": resultado,
                                        "odds": 0.0,
                                        "prob_impl": prob_impl,
                                        "prob_real": prob_real,
                                        "diferenca": diferenca,
                                        "vantajoso": vantajoso
                                    })
                    
                    # Atualizar probabilidades para este mercado
                    data["probabilities"][market_keys[i]] = probabilities
        
        # Extrair informações de confiança
        conf_section = extract_section(analysis_text, "# Nível de Confiança")
        if conf_section:
            # Extrair nível de confiança geral
            level_match = re.search(r'Nível de Confiança Geral: (\w+)', analysis_text)
            if level_match:
                data["confidence"]["level"] = level_match.group(1).strip()
            else:
                # Tentar outro padrão (pode estar como título de seção)
                level_match = re.search(r'# Nível de Confiança Geral: (\w+)', analysis_text)
                if level_match:
                    data["confidence"]["level"] = level_match.group(1).strip()
            
            # Extrair consistência das equipes
            consistency_pattern = r'(?:consistência|consistencia) .+?:(?: |: |)(\d+\.?\d*)%'
            consistency_matches = re.findall(consistency_pattern, conf_section, re.IGNORECASE)
            
            # Extrair nomes dos times do título
            teams = []
            if data["title"]:
                teams = data["title"].split(' x ')
            
            if len(consistency_matches) >= 2 and len(teams) >= 2:
                data["confidence"]["teams_consistency"] = {
                    teams[0]: float(consistency_matches[0]),
                    teams[1]: float(consistency_matches[1]) if len(consistency_matches) > 1 else 0.0
                }
            
            # Extrair forma recente
            form_pattern = r'forma.+?:(?: |: |)(\d+\.?\d*)/15'
            form_matches = re.findall(form_pattern, conf_section, re.IGNORECASE)
            
            if len(form_matches) >= 2 and len(teams) >= 2:
                data["confidence"]["recent_form"] = {
                    teams[0]: float(form_matches[0]),
                    teams[1]: float(form_matches[1]) if len(form_matches) > 1 else 0.0
                }
            
            # Extrair observações
            observations = []
            for line in conf_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('Nível de Confiança') and \
                   not re.search(r'consistência|consistencia|forma', line, re.IGNORECASE):
                    # Remover marcadores de lista se presentes
                    if line.startswith('- ') or line.startswith('* '):
                        line = line[2:]
                    observations.append(line)
            
            data["confidence"]["observations"] = observations
    
    except Exception as e:
        logger.error(f"Erro ao extrair dados da análise: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    return data

def extract_section(text, section_title, include_title=True, end_marker=None):
    """
    Extrai uma seção do texto baseada no título da seção
    
    Args:
        text (str): Texto completo
        section_title (str): Título da seção a extrair
        include_title (bool): Se deve incluir o título na saída
        end_marker (str): Marcador que indica o fim da seção (opcional)
    
    Returns:
        str: Seção extraída ou string vazia se não encontrada
    """
    if not text or not section_title:
        return ""
    
    start_idx = text.find(section_title)
    if start_idx == -1:
        return ""
    
    # Encontrar o fim da seção
    if end_marker:
        end_idx = text.find(end_marker, start_idx + len(section_title))
        # Se não encontrar o marcador de fim, pegar até o final do texto
        if end_idx == -1:
            end_idx = len(text)
    else:
        # Procurar pelo próximo cabeçalho do mesmo nível
        next_header_level = section_title.count('#')
        next_header = '#' * next_header_level + ' '
        
        end_idx = text.find(next_header, start_idx + len(section_title))
        if end_idx == -1:
            end_idx = len(text)
    
    # Extrair a seção
    if include_title:
        return text[start_idx:end_idx].strip()
    else:
        return text[start_idx + len(section_title):end_idx].strip()

def extract_text_between_asterisks(text):
    """Extrai texto entre asteriscos duplos"""
    match = re.search(r'\*\*(.*?)\*\*', text)
    return match.group(1) if match else text.strip()

def extract_text_without_parentheses(text):
    """Extrai texto removendo qualquer conteúdo entre parênteses"""
    return re.sub(r'\([^)]*\)', '', text).strip()

def display_formatted_analysis(analysis_data):
    """
    Exibe a análise formatada usando componentes Streamlit com estilos melhorados
    
    Args:
        analysis_data (dict): Dados estruturados da análise
    """
    try:
        # Aplicar estilos CSS personalizados
        apply_custom_styles()
        
        # Container para toda a análise
        st.markdown('<div class="analysis-container">', unsafe_allow_html=True)
        
        # Título da análise
        if analysis_data["title"]:
            st.markdown(f'<h1 class="analysis-title">📊 Análise da Partida: {analysis_data["title"]}</h1>', unsafe_allow_html=True)
        else:
            st.markdown('<h1 class="analysis-title">📊 Análise da Partida</h1>', unsafe_allow_html=True)
        
        # Oportunidades identificadas
        st.markdown("## 🎯 Oportunidades Identificadas")
        if analysis_data["opportunities"]:
            # Criar DataFrame para exibição em tabela
            opportunities_df = pd.DataFrame(analysis_data["opportunities"])
            
            # Converter coluna de confiança para estrelas
            if "confianca" in opportunities_df.columns:
                opportunities_df["confianca"] = opportunities_df["confianca"].apply(lambda x: "⭐" * int(x))
            
            # Renomear colunas para exibição
            opportunities_df = opportunities_df.rename(columns={
                "mercado": "Mercado",
                "selecao": "Seleção",
                "odds": "Odds",
                "vantagem": "Vantagem",
                "confianca": "Confiança"
            })
            
            # Formatar colunas numéricas
            if "Odds" in opportunities_df.columns:
                opportunities_df["Odds"] = opportunities_df["Odds"].apply(lambda x: f"@{x:.2f}")
            
            if "Vantagem" in opportunities_df.columns:
                opportunities_df["Vantagem"] = opportunities_df["Vantagem"].apply(lambda x: f"+{x:.1f}%")
            
            # Exibir tabela com estilos
            st.dataframe(
                opportunities_df,
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Nenhuma oportunidade identificada.")
        
        # Comparativo de probabilidades
        st.markdown("## 📈 Comparativo de Probabilidades")
        
        # Mostrar cada mercado em uma seção
        market_titles = {
            "money_line": "Money Line",
            "over_under": "Over/Under 2.5",
            "chance_dupla": "Chance Dupla",
            "ambos_marcam": "Ambos Marcam"
        }
        
        for market_key, title in market_titles.items():
            probabilities = analysis_data["probabilities"].get(market_key, [])
            
            if probabilities:
                st.markdown(f"### {title}")
                
                # Criar DataFrame para exibição em tabela
                probs_df = pd.DataFrame(probabilities)
                
                # Renomear colunas para exibição
                probs_df = probs_df.rename(columns={
                    "resultado": "Resultado",
                    "odds": "Odds",
                    "prob_impl": "Prob. Implícita",
                    "prob_real": "Prob. Real",
                    "diferenca": "Diferença",
                    "vantajoso": ""
                })
                
                # Formatar colunas numéricas
                if "Odds" in probs_df.columns and probs_df["Odds"].sum() > 0:
                    probs_df["Odds"] = probs_df["Odds"].apply(lambda x: f"@{x:.2f}" if x > 0 else "")
                else:
                    probs_df = probs_df.drop("Odds", axis=1, errors="ignore")
                
                if "Prob. Implícita" in probs_df.columns:
                    probs_df["Prob. Implícita"] = probs_df["Prob. Implícita"].apply(lambda x: f"{x:.1f}%")
                
                if "Prob. Real" in probs_df.columns:
                    probs_df["Prob. Real"] = probs_df["Prob. Real"].apply(lambda x: f"{x:.1f}%")
                
                if "Diferença" in probs_df.columns:
                    probs_df["Diferença"] = probs_df["Diferença"].apply(lambda x: f"{x:+.1f}%" if x != 0 else "0.0%")
                
                # Exibir tabela com estilos
                st.dataframe(
                    probs_df,
                    hide_index=True,
                    use_container_width=True
                )
        
        # Análise de confiança
        st.markdown("## 🔍 Análise de Confiança")
        
        # Nível de confiança geral
        confidence_level = analysis_data["confidence"].get("level", "Médio")
        stars = "⭐" * get_confidence_stars(confidence_level)
        st.markdown(f'<div class="confidence-stars">**Nível de Confiança Geral: {confidence_level}** {stars}</div>', unsafe_allow_html=True)
        
        # Consistência das equipes
        if analysis_data["confidence"]["teams_consistency"]:
            st.markdown("### Consistência das Equipes")
            
            # Criar dataframe para exibição tabular das consistências
            consistency_data = []
            for team, consistency in analysis_data["confidence"]["teams_consistency"].items():
                consistency_desc = get_consistency_description(consistency)
                consistency_data.append({
                    "Equipe": team,
                    "Consistência": f"{consistency:.1f}%",
                    "Previsibilidade": consistency_desc
                })
            
            if consistency_data:
                st.dataframe(
                    pd.DataFrame(consistency_data),
                    hide_index=True,
                    use_container_width=True
                )
        
        # Forma recente
        if analysis_data["confidence"]["recent_form"]:
            st.markdown("### Forma Recente (últimos 5 jogos)")
            
            # Criar dataframe para exibição tabular da forma
            form_data = []
            for team, form in analysis_data["confidence"]["recent_form"].items():
                form_desc = get_form_description(form)
                form_data.append({
                    "Equipe": team,
                    "Pontos": f"{form:.1f}/15",
                    "Avaliação": form_desc
                })
            
            if form_data:
                st.dataframe(
                    pd.DataFrame(form_data),
                    hide_index=True,
                    use_container_width=True
                )
        
        # Observações
        if analysis_data["confidence"]["observations"]:
            st.markdown("### Observações")
            for obs in analysis_data["confidence"]["observations"]:
                # Verificar se já começa com marcador de lista
                if not (obs.startswith('-') or obs.startswith('*')):
                    obs = f"- {obs}"
                st.markdown(obs)
        
        # Fechar container
        st.markdown('</div>', unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erro ao exibir análise formatada: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
def get_confidence_stars(level):
    """Retorna o número de estrelas baseado no nível de confiança"""
    mapping = {
        "Muito Baixo": 1,
        "Baixo": 2,
        "Médio": 3,
        "Alto": 4,
        "Muito Alto": 5
    }
    # Normalizar para caso sensível
    normalized_level = level.capitalize()
    
    # Mapear para formato específico
    if normalized_level == "Medio":
        normalized_level = "Médio"
    elif normalized_level == "Baixa":
        normalized_level = "Baixo"
    elif normalized_level == "Alta":
        normalized_level = "Alto"
        
    return mapping.get(normalized_level, 3)

def get_consistency_description(consistency):
    """Retorna descrição da consistência baseada no valor percentual"""
    if consistency >= 90:
        return "Muito alta previsibilidade"
    elif consistency >= 75:
        return "Alta previsibilidade"
    elif consistency >= 60:
        return "Média previsibilidade"
    elif consistency >= 40:
        return "Baixa previsibilidade"
    else:
        return "Muito baixa previsibilidade"

def get_form_description(form):
    """Retorna descrição da forma baseada nos pontos"""
    if form >= 12:
        return "Excelente"
    elif form >= 9:
        return "Boa"
    elif form >= 6:
        return "Regular"
    elif form >= 3:
        return "Baixa"
    else:
        return "Muito baixa"

def integrate_formatted_analysis(analysis_text):
    """
    Função principal para integrar a análise formatada no dashboard.
    Extrai os dados estruturados e exibe o componente formatado.
    
    Args:
        analysis_text (str): Resposta textual da IA
        
    Returns:
        bool: Sucesso da operação
    """
    try:
        # Extrair dados estruturados da análise
        analysis_data = parse_analysis_response(analysis_text)
        
        # Exibir análise formatada
        display_formatted_analysis(analysis_data)
        
        return True
    except Exception as e:
        st.error(f"Erro ao processar análise: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        
        # Fallback para exibição simples do texto original
        st.markdown(analysis_text)
        
        return False
