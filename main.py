import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import altair as alt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import locale
from datetime import datetime, date
import re
from PIL import Image as PILImage  # Adicionando a importação da PIL

# Configurar a localização para formatação adequada de números em português
# Tratamento para evitar erros em diferentes ambientes (como Streamlit Cloud)
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        # Tentar alternativas comuns
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except locale.Error:
        try:
            # Fallback para português de Portugal se Brasil não estiver disponível
            locale.setlocale(locale.LC_ALL, 'pt_PT.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'pt_PT')
            except locale.Error:
                # Se nenhum locale português estiver disponível, usar o padrão do sistema
                locale.setlocale(locale.LC_ALL, '')

# Função para inicializar o Firebase (será chamada automaticamente quando necessário)
def initialize_firebase():
    """Inicializa a conexão com o Firebase se ainda não estiver inicializada"""
    if not firebase_admin._apps:
        try:
            # Para Streamlit Cloud: usar secrets no novo formato
            if 'firebase' in st.secrets:
                # Obter todas as configurações necessárias dos secrets
                firebase_config = {
                    "type": st.secrets.firebase.type,
                    "project_id": st.secrets.firebase.project_id,
                    "private_key_id": st.secrets.firebase.private_key_id,
                    "private_key": st.secrets.firebase.private_key,
                    "client_email": st.secrets.firebase.client_email,
                    "client_id": st.secrets.firebase.client_id,
                    "auth_uri": st.secrets.firebase.auth_uri,
                    "token_uri": st.secrets.firebase.token_uri,
                    "auth_provider_x509_cert_url": st.secrets.firebase.auth_provider_x509_cert_url,
                    "client_x509_cert_url": st.secrets.firebase.client_x509_cert_url
                }
                
                # Alternativa: se a codificação base64 for usada
                # import base64
                # if 'firebase_json_base64' in st.secrets:
                #     json_str = base64.b64decode(st.secrets.firebase_json_base64).decode('utf-8')
                #     firebase_config = json.loads(json_str)
                
                cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(cred)
                return True
        except Exception as e:
            # Em caso de erro, apenas continue - a aplicação funciona sem o Firebase
            print(f"Erro ao inicializar Firebase: {e}")
            return False
    return True

# Função para salvar um usuário no Firestore
def save_user_to_firebase(user_data):
    """Salva os dados do usuário no Firestore silenciosamente"""
    try:
        # Inicializar Firebase
        if not initialize_firebase():
            return False
        
        # Conectar ao Firestore
        db = firestore.client()
        
        # Adicionar timestamp de cadastro
        user_data['data_cadastro'] = datetime.now()
        
        # Salvar no Firestore (coleção 'usuarios')
        db.collection('usuarios').add(user_data)
        return True
    except Exception as e:
        # Em caso de erro, apenas continue - o usuário não precisa saber
        # que houve falha ao salvar no Firebase
        print(f"Erro ao salvar no Firebase: {e}")
        return False

# Função para formatar valores monetários sem depender totalmente do locale
def format_currency(value):
    try:
        # Tentar usar o locale configurado
        return locale.currency(value, grouping=True, symbol=True)
    except (locale.Error, ValueError):
        # Formatação manual caso o locale falhe
        if value >= 0:
            text = f"R$ {value:,.2f}"
            # Ajustar para padrão brasileiro (ponto como separador de milhares, vírgula para decimais)
            if ',' in text:
                text = text.replace(',', 'X').replace('.', ',').replace('X', '.')
            return text
        else:
            # Para valores negativos
            text = f"R$ -{abs(value):,.2f}"
            if ',' in text:
                text = text.replace(',', 'X').replace('.', ',').replace('X', '.')
            return text

# Função para formatar horas
def format_hours(hours):
    if hours == int(hours):
        return f"{int(hours)} hora{'s' if hours != 1 else ''}"
    else:
        hours_int = int(hours)
        minutes = int((hours - hours_int) * 60)
        if hours_int == 0:
            return f"{minutes} minuto{'s' if minutes != 1 else ''}"
        else:
            return f"{hours_int}h{minutes:02d}min"

# Função para formatar percentuais
def format_percent(value):
    return f"{value:.1f}%"

# Função para converter figura Plotly em imagem para o PDF
def plotly_fig_to_image(fig, width=700, height=400, scale=1):
    """Converte uma figura Plotly em imagem para usar no PDF."""
    img_bytes = fig.to_image(format="png", width=width, height=height, scale=scale)
    img_buffer = io.BytesIO(img_bytes)
    img = PILImage.open(img_buffer)
    
    # Convertendo para o formato que o ReportLab pode usar
    img_bytes_for_reportlab = io.BytesIO()
    img.save(img_bytes_for_reportlab, format='PNG')
    img_bytes_for_reportlab.seek(0)
    
    return img_bytes_for_reportlab

# Dados de benchmarking por setor
def get_benchmark_data():
    return {
        "Tecnologia": {
            "Infraestrutura": 85,
            "Políticas": 82,
            "Proteção": 88,
            "Total": 85
        },
        "Finanças": {
            "Infraestrutura": 90,
            "Políticas": 92,
            "Proteção": 94,
            "Total": 92
        },
        "Saúde": {
            "Infraestrutura": 78,
            "Políticas": 85,
            "Proteção": 82,
            "Total": 82
        },
        "Varejo": {
            "Infraestrutura": 70,
            "Políticas": 65,
            "Proteção": 68,
            "Total": 68
        },
        "Educação": {
            "Infraestrutura": 65,
            "Políticas": 70,
            "Proteção": 62,
            "Total": 66
        },
        "Manufatura": {
            "Infraestrutura": 72,
            "Políticas": 68,
            "Proteção": 70,
            "Total": 70
        },
        "Serviços": {
            "Infraestrutura": 68,
            "Políticas": 72,
            "Proteção": 65,
            "Total": 68
        }
    }

# Função para criar PDF completo com os resultados
def create_pdf_report(results, vulnerabilities, recommendations, company_name="Sua Empresa", report_type=None, figures=None):
    # Verificar se há dados suficientes para gerar o relatório
    if not results or len(results) == 0:
        # Retornar um PDF vazio ou básico quando não há dados suficientes
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
    styles = getSampleStyleSheet()
    elements = []
    
    # Definir estilos personalizados
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=1,
        spaceAfter=16,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=16,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading3'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=8,
        textColor=colors.darkblue
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=10
    )
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=1,
        textColor=colors.gray
    )
    
    # Cabeçalho do relatório
    if report_type == "complete":
        elements.append(Paragraph(f"RELATÓRIO COMPLETO DE SEGURANÇA DE DADOS", title_style))
    else:
        elements.append(Paragraph(f"RELATÓRIO DE SEGURANÇA DE DADOS", title_style))
    elements.append(Paragraph(f"{company_name}", subtitle_style))
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Relatório Completo - incluindo todas as análises
    if report_type == "complete":
        # Seção de Resumo Executivo
        elements.append(Paragraph("RESUMO EXECUTIVO", subtitle_style))
        
        # Sumário com principais pontos
        summary_text = f"""Este relatório apresenta uma análise completa de segurança de dados para {company_name}, 
        incluindo avaliação de vulnerabilidades, análise de retorno sobre investimento (ROI) e benchmarking de segurança 
        comparado ao setor. O objetivo é fornecer uma visão abrangente do estado atual de segurança da informação 
        e orientações para melhoria."""
        
        elements.append(Paragraph(summary_text, normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Tabela de resumo executivo com principais métricas
        table_data = [["Métrica", "Valor", "Status"]]
        
        # Adicionar métricas principais de cada análise
        if 'Pontuação Geral' in results:
            risk_level = results.get('Nível de Risco', '')
            risk_color = colors.red if risk_level == "Crítico" else colors.orange if risk_level == "Moderado" else colors.green
            
            table_data.append([
                Paragraph("<b>Pontuação Geral de Segurança</b>", normal_style),
                Paragraph(f"<b>{format_percent(results['Pontuação Geral'])}</b>", normal_style),
                Paragraph(f"<font color={risk_color}><b>{risk_level}</b></font>", normal_style)
            ])
            
        if 'ROI' in results:
            roi_value = results['ROI']
            roi_color = colors.green if roi_value > 0 else colors.red
            
            table_data.append([
                "ROI em Segurança", 
                Paragraph(f"<font color={roi_color}><b>{format_percent(roi_value)}</b></font>", normal_style),
                ""
            ])
            
        if 'Média do Setor' in results:
            diff_value = results.get('Diferença com Setor', 0)
            diff_color = colors.green if diff_value >= 0 else colors.red
            diff_status = "Acima da Média" if diff_value >= 0 else "Abaixo da Média"
            
            table_data.append([
                "Comparação com Setor", 
                Paragraph(f"<font color={diff_color}><b>{diff_value:+.1f}%</b></font>", normal_style),
                diff_status
            ])
            
        if 'Total de Vulnerabilidades' in results:
            vuln_count = results['Total de Vulnerabilidades']
            vuln_color = colors.red if vuln_count > 5 else colors.orange if vuln_count > 2 else colors.green
            
            table_data.append([
                "Vulnerabilidades Identificadas", 
                Paragraph(f"<font color={vuln_color}><b>{vuln_count}</b></font>", normal_style),
                "Crítico" if vuln_count > 5 else "Moderado" if vuln_count > 2 else "Baixo"
            ])
            
        table = Table(table_data, colWidths=[2.4*inch, 1.8*inch, 1.8*inch])
        
        # Estilo da tabela
        table_style = [
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Corpo da tabela
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            
            # Valores (coluna do meio) alinhados à direita
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            
            # Classificação (última coluna) centralizada
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            
            # Linhas alternadas com cores suaves
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
            ('BACKGROUND', (0, 3), (-1, 3), colors.lightgrey),
            
            # Bordas refinadas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('LINEABOVE', (0, 1), (-1, 1), 1, colors.black),
        ]
        
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(Spacer(1, 0.4*inch))
        
        # SEÇÃO 1: TESTE DE VULNERABILIDADE
        if 'Pontuação Geral' in results and 'Pontuação Infraestrutura' in results:
            elements.append(Paragraph("PARTE 1: AVALIAÇÃO DE VULNERABILIDADE", subtitle_style))
            
            # Adicionar gráfico do velocímetro se disponível
            if figures and 'gauge' in figures:
                elements.append(Paragraph("Nível de Segurança", section_style))
                
                # Converter figura para imagem
                img_data = plotly_fig_to_image(figures['gauge'])
                img = Image(img_data, width=450, height=250)
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))
            
            # Tabela de vulnerabilidade
            vuln_data = [["Métrica", "Valor", "Classificação"]]
            
            # Pontuação geral com destaque
            risk_level = results.get('Nível de Risco', '')
            risk_color = colors.red if risk_level == "Crítico" else colors.orange if risk_level == "Moderado" else colors.green
            
            vuln_data.append([
                Paragraph("<b>Pontuação Geral</b>", normal_style),
                Paragraph(f"<b>{format_percent(results['Pontuação Geral'])}</b>", normal_style),
                Paragraph(f"<font color={risk_color}><b>{risk_level}</b></font>", normal_style)
            ])
            
            # Outras métricas
            if 'Pontuação Infraestrutura' in results:
                vuln_data.append([
                    "Infraestrutura", 
                    format_percent(results['Pontuação Infraestrutura']),
                    ""
                ])
            
            if 'Pontuação Políticas' in results:
                vuln_data.append([
                    "Políticas", 
                    format_percent(results['Pontuação Políticas']),
                    ""
                ])
                
            if 'Pontuação Proteção' in results:
                vuln_data.append([
                    "Proteção", 
                    format_percent(results['Pontuação Proteção']),
                    ""
                ])
                
            if 'Total de Vulnerabilidades' in results:
                vuln_data.append([
                    "Vulnerabilidades Detectadas", 
                    str(results['Total de Vulnerabilidades']),
                    ""
                ])
                
            # Criar tabela de vulnerabilidade
            vuln_table = Table(vuln_data, colWidths=[2.4*inch, 1.8*inch, 1.8*inch])
            vuln_table.setStyle(TableStyle(table_style))
            elements.append(vuln_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Adicionar gráfico de categorias se disponível
            if figures and 'category' in figures:
                elements.append(Paragraph("Pontuação por Categoria", section_style))
                
                # Converter figura para imagem
                img_data = plotly_fig_to_image(figures['category'])
                img = Image(img_data, width=450, height=250)
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))
            
            # Explicação sobre a pontuação
            if 'Pontuação Geral' in results:
                score = results['Pontuação Geral']
                if score <= 40:
                    vuln_explanation = """
                    <b>RISCO CRÍTICO:</b> A segurança da empresa está extremamente vulnerável. 
                    Há alto risco de sofrer ataques cibernéticos que podem resultar em perda de dados, 
                    fraudes e violações de compliance. É necessário implementar medidas de segurança urgentemente.
                    """
                elif score <= 70:
                    vuln_explanation = """
                    <b>RISCO MODERADO:</b> A empresa possui algumas medidas de segurança, mas há brechas significativas. 
                    Um ataque pode comprometer as operações e informações sensíveis. É recomendado fortalecer 
                    os controles de segurança existentes.
                    """
                else:
                    vuln_explanation = """
                    <b>SEGURANÇA ACEITÁVEL:</b> A empresa tem uma boa estrutura de segurança, mas ainda pode melhorar. 
                    O ideal é refinar processos e testar a resiliência contra ameaças cada vez mais sofisticadas.
                    """
                
                elements.append(Paragraph(vuln_explanation, normal_style))
            
            # Adicionar vulnerabilidades se existirem
            if vulnerabilities:
                elements.append(Spacer(1, 0.2*inch))
                elements.append(Paragraph("VULNERABILIDADES IDENTIFICADAS", section_style))
                
                # Adicionar cada vulnerabilidade com número
                for i, vuln in enumerate(vulnerabilities, 1):
                    vuln_text = Paragraph(
                        f"<strong>{i}.</strong> {vuln}",
                        ParagraphStyle(
                            'VulnStyle',
                            parent=styles['Normal'],
                            fontSize=10,
                            textColor=colors.darkred,
                            leftIndent=15,
                            spaceBefore=6,
                            spaceAfter=6
                        )
                    )
                    elements.append(vuln_text)
            
            elements.append(Spacer(1, 0.3*inch))
        
        # SEÇÃO 2: ANÁLISE DE ROI
        if 'Investimento' in results and 'Economia' in results:
            elements.append(Paragraph("PARTE 2: ANÁLISE DE RETORNO SOBRE INVESTIMENTO (ROI)", subtitle_style))
            
            # Adicionar gráfico de ROI se disponível
            if figures and 'roi' in figures:
                elements.append(Paragraph("Análise de ROI", section_style))
                
                # Converter figura para imagem
                img_data = plotly_fig_to_image(figures['roi'], width=700, height=350)
                img = Image(img_data, width=500, height=280)
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))
            
            # Tabela de resumo para ROI
            roi_data = [["Métrica", "Valor", ""]]
            
            if 'Investimento' in results:
                roi_data.append([
                    "Investimento em Segurança", 
                    format_currency(results['Investimento']),
                    ""
                ])
                
            if 'Economia' in results:
                roi_data.append([
                    "Economia Projetada", 
                    format_currency(results['Economia']),
                    ""
                ])
                
            if 'ROI' in results:
                # Formatar o ROI com cor baseada no valor
                roi_value = results['ROI']
                roi_color = colors.green if roi_value > 0 else colors.red
                
                roi_data.append([
                    "Retorno sobre Investimento (ROI)", 
                    Paragraph(f"<font color={roi_color}><b>{format_percent(roi_value)}</b></font>", normal_style),
                    ""
                ])
                
            if 'Perda de Clientes' in results:
                roi_data.append([
                    "Perda de Receita (Clientes)", 
                    format_currency(results['Perda de Clientes']),
                    ""
                ])
                
            if 'Impacto Total' in results:
                roi_data.append([
                    "Impacto Financeiro Total", 
                    format_currency(results['Impacto Total']),
                    ""
                ])
                
            # Adicionar detalhes sobre custos antes e depois
            if 'Custo Total Antes' in results and 'Custo Total Depois' in results:
                roi_data.append([
                    "Custo Total Antes do Investimento", 
                    format_currency(results['Custo Total Antes']),
                    ""
                ])
                
                roi_data.append([
                    "Custo Total Após o Investimento", 
                    format_currency(results['Custo Total Depois']),
                    ""
                ])
                
            # Criar tabela de ROI
            roi_table = Table(roi_data, colWidths=[2.7*inch, 2.0*inch, 1.3*inch])
            roi_table_style = table_style.copy()
            roi_table_style.extend([
                ('BACKGROUND', (0, 2), (-1, 2), colors.lightgrey),
                ('BACKGROUND', (0, 4), (-1, 4), colors.lightgrey),
                ('BACKGROUND', (0, 6), (-1, 6), colors.lightgrey),
            ])
            roi_table.setStyle(TableStyle(roi_table_style))
            elements.append(roi_table)
            
            # Explicação sobre o ROI
            if 'ROI' in results:
                roi_value = results['ROI']
                elements.append(Spacer(1, 0.2*inch))
                
                if roi_value > 100:
                    roi_explanation = """
                    <b>ROI EXCEPCIONAL:</b> O investimento em segurança está gerando um retorno excepcional. 
                    Os custos evitados superam significativamente o valor investido, demonstrando alta eficácia das medidas implementadas.
                    """
                elif roi_value > 0:
                    roi_explanation = """
                    <b>ROI POSITIVO:</b> O investimento em segurança está gerando retorno positivo. 
                    As medidas implementadas estão reduzindo efetivamente os custos com incidentes de segurança.
                    """
                else:
                    roi_explanation = """
                    <b>ROI NEGATIVO:</b> O investimento em segurança ainda não está gerando retorno positivo. 
                    Recomenda-se avaliar a eficácia das medidas implementadas e considerar ajustes na estratégia de segurança.
                    """
                
                elements.append(Paragraph(roi_explanation, normal_style))
                
            elements.append(Spacer(1, 0.3*inch))
            
            # Detalhes sobre incidentes
            elements.append(Paragraph("Análise de Incidentes", section_style))
            
            incidents_data = [["Métrica", "Antes do Investimento", "Após o Investimento"]]
            
            if 'Num Incidentes Antes' in results and 'Num Incidentes Depois' in results:
                incidents_data.append([
                    "Número de Incidentes", 
                    str(results['Num Incidentes Antes']),
                    str(results['Num Incidentes Depois'])
                ])
                
            if 'Custo por Incidente Antes' in results and 'Custo por Incidente Depois' in results:
                incidents_data.append([
                    "Custo por Incidente", 
                    format_currency(results['Custo por Incidente Antes']),
                    format_currency(results['Custo por Incidente Depois'])
                ])
                
            if 'Horas por Incidente Antes' in results and 'Horas por Incidente Depois' in results:
                incidents_data.append([
                    "Tempo de Resolução", 
                    format_hours(results['Horas por Incidente Antes']),
                    format_hours(results['Horas por Incidente Depois'])
                ])
                
            incidents_table = Table(incidents_data, colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
            incidents_table_style = [
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                
                # Corpo da tabela
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (0, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                
                # Valores (colunas 1 e 2) alinhados à direita
                ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
                
                # Linhas alternadas
                ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
                ('BACKGROUND', (0, 3), (-1, 3), colors.lightgrey),
                
                # Bordas
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ]
            incidents_table.setStyle(TableStyle(incidents_table_style))
            elements.append(incidents_table)
            
            # Adicionar gráficos de pizza se disponíveis
            if figures and 'pie_before' in figures and 'pie_after' in figures:
                elements.append(Spacer(1, 0.2*inch))
                elements.append(Paragraph("Comparação de Custos Antes e Depois", section_style))
                
                # Criar tabela para acomodar os dois gráficos lado a lado
                img_before = plotly_fig_to_image(figures['pie_before'], width=350, height=300)
                img_after = plotly_fig_to_image(figures['pie_after'], width=350, height=300)
                
                before_img = Image(img_before, width=250, height=200)
                after_img = Image(img_after, width=250, height=200)
                
                data = [[before_img, after_img]]
                t = Table(data, colWidths=[250, 250])
                t.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(t)
                
            elements.append(Spacer(1, 0.3*inch))
        
        # SEÇÃO 3: BENCHMARKING
        if 'Média do Setor' in results and 'Diferença com Setor' in results:
            elements.append(Paragraph("PARTE 3: ANÁLISE COMPARATIVA DE BENCHMARKING", subtitle_style))
            
            # Adicionar gráfico de radar se disponível
            if figures and 'radar' in figures:
                elements.append(Paragraph("Comparação por Categoria com o Setor", section_style))
                
                # Converter figura para imagem
                img_data = plotly_fig_to_image(figures['radar'], width=600, height=400)
                img = Image(img_data, width=450, height=300)
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))
            
            # Adicionar gráfico de comparação com todos os setores se disponível
            if figures and 'all_sectors' in figures:
                elements.append(Paragraph("Comparação com Todos os Setores", section_style))
                
                # Converter figura para imagem
                img_data = plotly_fig_to_image(figures['all_sectors'], width=700, height=400)
                img = Image(img_data, width=500, height=280)
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))
            
            # Tabela de resumo para benchmarking
            bench_data = [["Métrica", "Valor", "Status"]]
            
            if 'Pontuação Geral' in results:
                bench_data.append([
                    "Pontuação da Empresa", 
                    format_percent(results['Pontuação Geral']),
                    ""
                ])
                
            if 'Média do Setor' in results:
                bench_data.append([
                    "Média do Setor", 
                    format_percent(results['Média do Setor']),
                    ""
                ])
                
            if 'Diferença com Setor' in results:
                # Formatar a diferença com cor baseada no valor
                diff_value = results['Diferença com Setor']
                diff_color = colors.green if diff_value >= 0 else colors.red
                diff_status = "Acima da Média" if diff_value >= 0 else "Abaixo da Média"
                
                bench_data.append([
                    "Diferença", 
                    Paragraph(f"<font color={diff_color}><b>{diff_value:+.1f}%</b></font>", normal_style),
                    diff_status
                ])
                
            # Adicionar detalhes por categoria se disponíveis
            if 'Pontuação Infraestrutura' in results:
                bench_data.append([
                    "Infraestrutura", 
                    format_percent(results['Pontuação Infraestrutura']),
                    ""
                ])
                
            if 'Pontuação Políticas' in results:
                bench_data.append([
                    "Políticas", 
                    format_percent(results['Pontuação Políticas']),
                    ""
                ])
                
            if 'Pontuação Proteção' in results:
                bench_data.append([
                    "Proteção", 
                    format_percent(results['Pontuação Proteção']),
                    ""
                ])
                
            # Criar tabela de benchmarking
            bench_table = Table(bench_data, colWidths=[2.4*inch, 1.8*inch, 1.8*inch])
            bench_table_style = table_style.copy()
            bench_table_style.extend([
                ('BACKGROUND', (0, 2), (-1, 2), colors.lightgrey),
                ('BACKGROUND', (0, 4), (-1, 4), colors.lightgrey),
            ])
            bench_table.setStyle(TableStyle(bench_table_style))
            elements.append(bench_table)
            
            # Explicação sobre o benchmarking
            if 'Diferença com Setor' in results:
                diff_value = results['Diferença com Setor']
                elements.append(Spacer(1, 0.2*inch))
                
                if diff_value >= 10:
                    benchmark_explanation = """
                    <b>DESTAQUE NO SETOR:</b> A empresa está significativamente acima da média do setor em segurança da informação.
                    Esta posição de liderança representa uma vantagem competitiva e demonstra excelência nas práticas de segurança.
                    """
                elif diff_value >= 0:
                    benchmark_explanation = """
                    <b>ACIMA DA MÉDIA:</b> A empresa está acima da média do setor em segurança da informação.
                    Esta posição favorável demonstra boas práticas, mas ainda há oportunidades para ampliar a vantagem competitiva.
                    """
                elif diff_value >= -10:
                    benchmark_explanation = """
                    <b>PRÓXIMO À MÉDIA:</b> A empresa está ligeiramente abaixo da média do setor em segurança da informação.
                    É recomendável implementar melhorias para, no mínimo, alcançar o padrão do setor.
                    """
                else:
                    benchmark_explanation = """
                    <b>SIGNIFICATIVAMENTE ABAIXO DA MÉDIA:</b> A empresa está consideravelmente abaixo da média do setor em segurança da informação.
                    Esta posição representa uma vulnerabilidade competitiva e exige atenção imediata para implementar melhorias.
                    """
                
                elements.append(Paragraph(benchmark_explanation, normal_style))
            
            elements.append(Spacer(1, 0.3*inch))
        
        # SEÇÃO 4: RECOMENDAÇÕES CONSOLIDADAS
        if recommendations:
            elements.append(Paragraph("RECOMENDAÇÕES CONSOLIDADAS", subtitle_style))
            
            # Agrupar recomendações por categorias para melhor organização
            infra_recs = []
            policy_recs = []
            protect_recs = []
            other_recs = []
            
            for rec in recommendations:
                if any(term in rec.lower() for term in ["firewall", "autenticação", "mfa", "backup", "criptografia", "servidor"]):
                    infra_recs.append(rec)
                elif any(term in rec.lower() for term in ["política", "treinamento", "conscientização", "plano", "norma"]):
                    policy_recs.append(rec)
                elif any(term in rec.lower() for term in ["senha", "ataque", "invasão", "ameaça", "vazamento", "proteção"]):
                    protect_recs.append(rec)
                else:
                    other_recs.append(rec)
            
            # Adicionar recomendações por categoria
            if infra_recs:
                elements.append(Paragraph("Infraestrutura e Tecnologia", section_style))
                for i, rec in enumerate(infra_recs, 1):
                    rec_text = Paragraph(
                        f"<strong>{i}.</strong> {rec}",
                        ParagraphStyle(
                            'RecStyle',
                            parent=styles['Normal'],
                            fontSize=10,
                            textColor=colors.darkgreen,
                            leftIndent=15,
                            spaceBefore=6,
                            spaceAfter=6
                        )
                    )
                    elements.append(rec_text)
            
            if policy_recs:
                elements.append(Paragraph("Políticas e Procedimentos", section_style))
                for i, rec in enumerate(policy_recs, 1):
                    rec_text = Paragraph(
                        f"<strong>{i}.</strong> {rec}",
                        ParagraphStyle(
                            'RecStyle',
                            parent=styles['Normal'],
                            fontSize=10,
                            textColor=colors.darkgreen,
                            leftIndent=15,
                            spaceBefore=6,
                            spaceAfter=6
                        )
                    )
                    elements.append(rec_text)
            
            if protect_recs:
                elements.append(Paragraph("Proteção Contra Ameaças", section_style))
                for i, rec in enumerate(protect_recs, 1):
                    rec_text = Paragraph(
                        f"<strong>{i}.</strong> {rec}",
                        ParagraphStyle(
                            'RecStyle',
                            parent=styles['Normal'],
                            fontSize=10,
                            textColor=colors.darkgreen,
                            leftIndent=15,
                            spaceBefore=6,
                            spaceAfter=6
                        )
                    )
                    elements.append(rec_text)
            
            if other_recs:
                elements.append(Paragraph("Recomendações Gerais", section_style))
                for i, rec in enumerate(other_recs, 1):
                    rec_text = Paragraph(
                        f"<strong>{i}.</strong> {rec}",
                        ParagraphStyle(
                            'RecStyle',
                            parent=styles['Normal'],
                            fontSize=10,
                            textColor=colors.darkgreen,
                            leftIndent=15,
                            spaceBefore=6,
                            spaceAfter=6
                        )
                    )
                    elements.append(rec_text)
            
        # SEÇÃO 5: PRÓXIMOS PASSOS E CONCLUSÃO
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("PRÓXIMOS PASSOS RECOMENDADOS", subtitle_style))
        
        next_steps = [
            "Priorize as vulnerabilidades críticas identificadas e crie um plano de ação com prazos definidos.",
            "Implemente as recomendações de segurança de acordo com o ROI projetado, começando pelas medidas de maior impacto.",
            "Realize uma nova avaliação de segurança em 3-6 meses para medir o progresso e identificar novas áreas de melhoria.",
            "Considere a realização de treinamentos de conscientização em segurança para todos os funcionários.",
            "Desenvolva ou atualize o plano de resposta a incidentes de segurança da informação."
        ]
        
        for i, step in enumerate(next_steps, 1):
            step_text = Paragraph(
                f"<strong>{i}.</strong> {step}",
                ParagraphStyle(
                    'StepStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.black,
                    leftIndent=15,
                    spaceBefore=6,
                    spaceAfter=6
                )
            )
            elements.append(step_text)
        
        # Conclusão
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("CONCLUSÃO", subtitle_style))
        
        conclusion_text = f"""Este relatório apresenta uma análise completa da postura de segurança da {company_name}. 
        Com base nas avaliações realizadas, identificamos as principais áreas de vulnerabilidade, analisamos o retorno 
        sobre investimento em segurança e comparamos o desempenho da empresa com a média do setor.
        
        A implementação das recomendações apresentadas neste relatório ajudará a fortalecer significativamente a postura de 
        segurança da empresa, reduzir riscos de violações de dados e garantir conformidade com regulamentações de segurança 
        da informação.
        
        Recomendamos a realização de novas avaliações periódicas para medir o progresso e manter as práticas de segurança 
        atualizadas frente às ameaças em constante evolução."""
        
        elements.append(Paragraph(conclusion_text, normal_style))
    
    else:
        # Tratamento para relatórios individuais (código original)
        # Determinar que tipo de relatório estamos gerando com base nas chaves presentes
        report_type = ""
        if 'Pontuação Geral' in results and 'Pontuação Infraestrutura' in results:
            report_type = "vulnerability"
        elif 'Investimento' in results and 'Economia' in results:
            report_type = "roi"
        elif 'Média do Setor' in results and 'Diferença' in results:
            report_type = "benchmark"
        
        # Resumo de resultados com formatação baseada no tipo de relatório
        if report_type == "vulnerability":
            elements.append(Paragraph("RESUMO DA AVALIAÇÃO DE VULNERABILIDADE", subtitle_style))
            
            # Tabela de resumo para relatório de vulnerabilidade
            table_data = [["Métrica", "Valor", "Classificação"]]
            
            # Pontuação geral com destaque
            risk_level = results.get('Nível de Risco', '')
            risk_color = colors.red if risk_level == "Crítico" else colors.orange if risk_level == "Moderado" else colors.green
            
            table_data.append([
                Paragraph("<b>Pontuação Geral</b>", normal_style),
                Paragraph(f"<b>{format_percent(results['Pontuação Geral'])}</b>", normal_style),
                Paragraph(f"<font color={risk_color}><b>{risk_level}</b></font>", normal_style)
            ])
            
            # Outras métricas
            if 'Pontuação Infraestrutura' in results:
                table_data.append([
                    "Infraestrutura", 
                    format_percent(results['Pontuação Infraestrutura']),
                    ""
                ])
            
            if 'Pontuação Políticas' in results:
                table_data.append([
                    "Políticas", 
                    format_percent(results['Pontuação Políticas']),
                    ""
                ])
                
            if 'Pontuação Proteção' in results:
                table_data.append([
                    "Proteção", 
                    format_percent(results['Pontuação Proteção']),
                    ""
                ])
                
            if 'Total de Vulnerabilidades' in results:
                table_data.append([
                    "Vulnerabilidades Detectadas", 
                    str(results['Total de Vulnerabilidades']),
                    ""
                ])
                
        elif report_type == "roi":
            elements.append(Paragraph("ANÁLISE DE RETORNO SOBRE INVESTIMENTO (ROI)", subtitle_style))
            
            # Tabela de resumo para relatório de ROI
            table_data = [["Métrica", "Valor", ""]]
            
            if 'Investimento' in results:
                table_data.append([
                    "Investimento em Segurança", 
                    format_currency(results['Investimento']),
                    ""
                ])
                
            if 'Economia' in results:
                table_data.append([
                    "Economia Projetada", 
                    format_currency(results['Economia']),
                    ""
                ])
                
            if 'ROI' in results:
                # Formatar o ROI com cor baseada no valor
                roi_value = results['ROI']
                roi_color = colors.green if roi_value > 0 else colors.red
                
                table_data.append([
                    "Retorno sobre Investimento (ROI)", 
                    Paragraph(f"<font color={roi_color}><b>{format_percent(roi_value)}</b></font>", normal_style),
                    ""
                ])
                
            if 'Perda de Clientes' in results:
                table_data.append([
                    "Perda de Receita (Clientes)", 
                    format_currency(results['Perda de Clientes']),
                    ""
                ])
                
            if 'Impacto Total' in results:
                table_data.append([
                    "Impacto Financeiro Total", 
                    format_currency(results['Impacto Total']),
                    ""
                ])
                
        elif report_type == "benchmark":
            elements.append(Paragraph("ANÁLISE COMPARATIVA DE BENCHMARKING", subtitle_style))
            
            # Tabela de resumo para relatório de benchmarking
            table_data = [["Métrica", "Valor", "Status"]]
            
            if 'Pontuação Geral' in results:
                table_data.append([
                    "Pontuação da Empresa", 
                    format_percent(results['Pontuação Geral']),
                    ""
                ])
                
            if 'Média do Setor' in results:
                table_data.append([
                    "Média do Setor", 
                    format_percent(results['Média do Setor']),
                    ""
                ])
                
            if 'Diferença' in results:
                # Formatar a diferença com cor baseada no valor
                diff_value = results['Diferença']
                diff_color = colors.green if diff_value >= 0 else colors.red
                diff_status = results.get('Nível de Risco', '')
                
                table_data.append([
                    "Diferença", 
                    Paragraph(f"<font color={diff_color}><b>{diff_value:+.1f}%</b></font>", normal_style),
                    diff_status
                ])
                
            if 'Pontuação Infraestrutura' in results:
                table_data.append([
                    "Infraestrutura", 
                    format_percent(results['Pontuação Infraestrutura']),
                    ""
                ])
                
            if 'Pontuação Políticas' in results:
                table_data.append([
                    "Políticas", 
                    format_percent(results['Pontuação Políticas']),
                    ""
                ])
                
            if 'Pontuação Proteção' in results:
                table_data.append([
                    "Proteção", 
                    format_percent(results['Pontuação Proteção']),
                    ""
                ])
        else:
            # Relatório genérico se não for identificado um tipo específico
            elements.append(Paragraph("RESUMO DE RESULTADOS", subtitle_style))
            
            # Tabela de dados genérica
            table_data = [["Métrica", "Valor", ""]]
            for key, value in results.items():
                # Determinar o formato adequado com base no nome da chave e no tipo do valor
                if isinstance(value, (int, float)) and 'percent' in key.lower() or key.lower() in ['roi', 'pontuação']:
                    formatted_value = format_percent(value)
                elif isinstance(value, (int, float)) and any(term in key.lower() for term in ['custo', 'valor', 'preço', 'investimento']):
                    formatted_value = format_currency(value)
                else:
                    formatted_value = str(value)
                    
                table_data.append([key, formatted_value, ""])
        
        # Criar tabela com estilo melhorado
        # Ajustar larguras de coluna com base no tipo de relatório
        if report_type == "roi":
            # Para ROI, dar mais espaço para os valores monetários
            col_widths = [2.7*inch, 2.0*inch, 1.3*inch]
        else:
            col_widths = [2.4*inch, 1.8*inch, 1.8*inch]
            
        table = Table(table_data, colWidths=col_widths)
        
        # Estilo da tabela mais sofisticado
        table_style = [
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Corpo da tabela
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            
            # Valores (coluna do meio) alinhados à direita
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            
            # Classificação (última coluna) centralizada
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            
            # Linhas alternadas com cores suaves
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
            ('BACKGROUND', (0, 3), (-1, 3), colors.lightgrey),
            ('BACKGROUND', (0, 5), (-1, 5), colors.lightgrey),
            
            # Bordas refinadas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('LINEABOVE', (0, 1), (-1, 1), 1, colors.black),
        ]
        
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Adicionar vulnerabilidades
        if vulnerabilities:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("VULNERABILIDADES IDENTIFICADAS", subtitle_style))
            
            # Criar lista numerada de vulnerabilidades para melhor legibilidade
            for i, vuln in enumerate(vulnerabilities, 1):
                # Usar parágrafos em vez de tabela para melhor formatação de texto
                vuln_text = Paragraph(
                    f"<strong>{i}.</strong> {vuln}",
                    ParagraphStyle(
                        'VulnStyle',
                        parent=styles['Normal'],
                        fontSize=10,
                        textColor=colors.darkred,
                        leftIndent=15,
                        spaceBefore=6,
                        spaceAfter=6
                    )
                )
                elements.append(vuln_text)
            
            elements.append(Spacer(1, 0.2*inch))
        
        # Adicionar recomendações
        if recommendations:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("RECOMENDAÇÕES DE MELHORIA", subtitle_style))
            
            # Criar lista de recomendações com ícones
            for i, rec in enumerate(recommendations, 1):
                # Usar parágrafos para melhor formatação
                rec_text = Paragraph(
                    f"<strong>{i}.</strong> {rec}",
                    ParagraphStyle(
                        'RecStyle',
                        parent=styles['Normal'],
                        fontSize=10,
                        textColor=colors.darkgreen,
                        leftIndent=15,
                        spaceBefore=6,
                        spaceAfter=6
                    )
                )
                elements.append(rec_text)
    
    # Adicionar observações finais
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        "OBSERVAÇÕES FINAIS",
        subtitle_style
    ))
    
    if report_type == "complete":
        obs_text = """Este relatório completo apresenta uma visão abrangente da segurança de dados da sua empresa, 
        incluindo avaliação de vulnerabilidades, análise de ROI em segurança e benchmarking comparativo com o setor. 
        As recomendações apresentadas devem ser implementadas de acordo com a prioridade, começando pelas vulnerabilidades 
        mais críticas. Recomenda-se repetir esta avaliação periodicamente para medir o progresso e ajustar a estratégia 
        de segurança conforme necessário."""
    elif report_type == "vulnerability":
        obs_text = """Este relatório apresenta uma avaliação do nível de segurança de dados da sua empresa com base nas respostas fornecidas. 
        As recomendações devem ser implementadas de acordo com a prioridade das vulnerabilidades identificadas. 
        Recomenda-se realizar uma nova avaliação após a implementação das melhorias."""
    elif report_type == "roi":
        obs_text = """Este relatório apresenta uma análise do retorno sobre investimento em segurança da informação. 
        Os valores são baseados nos dados fornecidos e representam projeções que podem variar de acordo com o cenário real.
        Recomenda-se revisar periodicamente os investimentos em segurança para maximizar o ROI."""
    elif report_type == "benchmark":
        obs_text = """Este relatório apresenta uma comparação do nível de segurança da sua empresa com a média do setor.
        Os benchmarks utilizados são baseados em dados coletados de empresas do mesmo segmento.
        Recomenda-se utilizar esta análise como referência para definir metas de melhoria."""
    else:
        obs_text = """Este relatório apresenta uma análise baseada nos dados fornecidos.
        Recomenda-se utilizar estas informações como base para tomada de decisões relacionadas à segurança da informação."""
    
    elements.append(Paragraph(
        obs_text,
        ParagraphStyle(
            'ObsStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            spaceBefore=6,
            spaceAfter=6
        )
    ))
    
    # Adicionar rodapé
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        f"© {datetime.now().year} Beirama - Segurança da Informação. Todos os direitos reservados.",
        ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )
    ))
    
    # Finalizar o PDF
    doc.build(elements)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

# Função para gerar um link de download para o PDF
def get_pdf_download_link(pdf_data, filename, text):
    b64 = base64.b64encode(pdf_data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Função para criar o gráfico de velocímetro com Plotly
def create_gauge_chart_plotly(score):
    if score <= 40:
        color = "red"
        risk_level = "🚨 CRÍTICO"
    elif score <= 70:
        color = "orange"
        risk_level = "⚠️ MODERADO"
    else:
        color = "green"
        risk_level = "✅ BOM"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {
            'text': f"Nível de Segurança<br><span style='font-size:0.8em;color:{color}'>{risk_level}</span>", 
            'font': {'size': 20},
            'align': 'center'
        },
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(255, 0, 0, 0.3)'},
                {'range': [40, 70], 'color': 'rgba(255, 165, 0, 0.3)'},
                {'range': [70, 100], 'color': 'rgba(0, 128, 0, 0.3)'}],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score}}))
    
    fig.update_layout(
        height=350,  # Aumentar a altura para acomodar o título
        margin=dict(l=20, r=20, t=90, b=20),  # Aumentar a margem superior (t) para o título
        paper_bgcolor="white",
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig

# Função para criar gráfico de barras para categorias com Plotly
def create_category_chart_plotly(scores, benchmark_data=None, industry=None):
    categories = list(scores.keys())
    values = list(scores.values())
    
    # Criar DataFrame para Plotly
    df = pd.DataFrame({
        'Categoria': categories,
        'Pontuação': values
    })
    
    # Adicionar dados de benchmark se disponíveis
    if benchmark_data and industry:
        benchmark_values = []
        for cat in categories:
            if cat in benchmark_data[industry]:
                benchmark_values.append(benchmark_data[industry][cat])
            else:
                benchmark_values.append(0)
        
        df['Benchmark'] = benchmark_values
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Categoria'],
            y=df['Pontuação'],
            name='Sua Empresa',
            marker_color='blue'
        ))
        fig.add_trace(go.Bar(
            x=df['Categoria'],
            y=df['Benchmark'],
            name=f'Média do Setor: {industry}',
            marker_color='green'
        ))
    else:
        # Definir as cores com base nos valores
        colors = []
        for value in values:
            if value <= 40:
                colors.append('red')
            elif value <= 70:
                colors.append('orange')
            else:
                colors.append('green')
                
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Categoria'],
            y=df['Pontuação'],
            marker_color=colors
        ))
    
    fig.update_layout(
        title='Pontuação por Categoria',
        xaxis_title='Categoria',
        yaxis_title='Pontuação (%)',
        yaxis=dict(range=[0, 100]),
        bargap=0.2,
        bargroupgap=0.1,
        height=400,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Adicionar anotações com valores
    for i, value in enumerate(values):
        fig.add_annotation(
            x=categories[i],
            y=value,
            text=f"{value:.1f}%",
            showarrow=False,
            yshift=10,
            font=dict(size=14)
        )
        
    return fig

# Função para criar gráfico de radar para comparação de benchmarking
def create_radar_chart(scores, benchmark_data, industry):
    # Preparar os dados
    categories = list(scores.keys())
    company_values = list(scores.values())
    
    benchmark_values = []
    for cat in categories:
        if cat in benchmark_data[industry]:
            benchmark_values.append(benchmark_data[industry][cat])
        else:
            benchmark_values.append(0)
    
    # Criar o gráfico de radar
    fig = go.Figure()
    
    # Adicionar dados da empresa
    fig.add_trace(go.Scatterpolar(
        r=company_values,
        theta=categories,
        fill='toself',
        name='Sua Empresa',
        line_color='blue'
    ))
    
    # Adicionar dados do benchmark
    fig.add_trace(go.Scatterpolar(
        r=benchmark_values,
        theta=categories,
        fill='toself',
        name=f'Média do Setor: {industry}',
        line_color='green'
    ))
    
    # Atualizar layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title=f"Comparação com o Setor: {industry}",
        height=500
    )
    
    return fig

# Função para criar gráfico de ROI com Plotly
def create_roi_chart_plotly(investment, total_before, total_after):
    savings = total_before - total_after
    roi = ((savings - investment) / investment) * 100 if investment > 0 else 0
    
    # Criar DataFrame para Plotly
    df = pd.DataFrame({
        'Categoria': ['Investimento', 'Economia', 'ROI (%)'],
        'Valor': [investment, savings, roi]
    })
    
    # Definir cores
    colors = ['blue', 'green', 'orange']
    
    # Criar dois subplots: um para valores monetários, outro para percentual
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "bar"}, {"type": "bar"}]])
    
    # Valores monetários
    fig.add_trace(
        go.Bar(
            x=['Investimento', 'Economia'],
            y=[investment, savings],
            marker_color=['blue', 'green'],
            text=[format_currency(investment), format_currency(savings)],
            textposition='auto',
            name='Valores (R$)'
        ),
        row=1, col=1
    )
    
    # ROI percentual
    fig.add_trace(
        go.Bar(
            x=['ROI'],
            y=[roi],
            marker_color='orange',
            text=[f"{roi:.1f}%"],
            textposition='auto',
            name='ROI (%)'
        ),
        row=1, col=2
    )
    
    # Atualizar layout
    fig.update_layout(
        title='Análise de ROI em Segurança da Informação',
        height=400,
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    fig.update_yaxes(title_text="Valor (R$)", row=1, col=1)
    fig.update_yaxes(title_text="Percentual (%)", row=1, col=2)
    
    return fig

# Função para criar gráfico de tendências de incidentes
def create_incident_trend_chart(incidents_data):
    fig = px.line(
        incidents_data, 
        x='Mês', 
        y='Número de Incidentes',
        markers=True,
        line_shape='linear',
        title='Tendência de Incidentes de Segurança'
    )
    
    fig.update_layout(
        xaxis_title='Mês',
        yaxis_title='Número de Incidentes',
        height=400,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

# Função para criar gráfico de pizza melhorado
def create_pie_chart_plotly(data, title):
    labels = list(data.keys())
    values = list(data.values())
    
    # Criar gráfico de pizza com tamanho adequado
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        textinfo='percent+label',
        insidetextorientation='radial',
        textposition='inside',
        hole=0.3,
        marker=dict(
            colors=['#FF6B6B', '#4ECDC4'],
            line=dict(color='#FFFFFF', width=2)
        )
    )])
    
    fig.update_layout(
        title=title,
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        font=dict(size=12)
    )
    
    # Ajuste para garantir visibilidade adequada dos rótulos
    fig.update_traces(
        textfont_size=12,
        hoverinfo="label+percent+value"
    )
    
    return fig

# Validar formato de telefone brasileiro
def validate_phone(phone):
    # Remover caracteres não numéricos
    phone_clean = re.sub(r'\D', '', phone)
    
    # Verificar se o comprimento está correto (com DDD: 10 ou 11 dígitos)
    if len(phone_clean) < 10 or len(phone_clean) > 11:
        return False
    
    # Verificar o formato básico do número
    phone_pattern = re.compile(r'^([1-9]{2})(9?[0-9]{8})$')
    return bool(phone_pattern.match(phone_clean))

# Validar formato de e-mail
def validate_email(email):
    # Verificações básicas antes da regex
    if not email or '@' not in email:
        return False
        
    # Dividir o email em parte local e domínio
    try:
        local_part, domain = email.rsplit('@', 1)
    except ValueError:
        return False
        
    # Verificar se o domínio tem pelo menos um ponto
    if '.' not in domain:
        return False
        
    # Expressão regular mais permissiva para validar e-mails
    # Permite TLDs mais longos (.info, .store, etc) e mais caracteres especiais
    email_pattern = re.compile(r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$')
    
    return bool(email_pattern.match(email))

# Função para salvar dados do usuário
def save_user_data():
    # Obter os dados do formulário
    user_data = {
        'nome_completo': st.session_state.nome_completo,
        'telefone': st.session_state.telefone,
        'email': st.session_state.email,
        'empresa': st.session_state.empresa,
        'industry': st.session_state.industry
    }
    
    # Salvar no user_data para uso na aplicação (manter o comportamento atual)
    st.session_state.user_data['nome_completo'] = user_data['nome_completo']
    st.session_state.user_data['telefone'] = user_data['telefone']
    st.session_state.user_data['email'] = user_data['email']
    st.session_state.user_data['empresa'] = user_data['empresa']
    st.session_state.user_data['industry'] = user_data['industry']
    
    # Validar dados antes de prosseguir
    if not user_data['nome_completo']:
        st.error("Por favor, informe seu nome completo.")
        return False
    
    if not validate_phone(user_data['telefone']):
        st.error("Por favor, informe um número de telefone válido com DDD.")
        return False
    
    if not validate_email(user_data['email']):
        st.error("Por favor, informe um endereço de e-mail válido.")
        return False
    
    if not user_data['empresa']:
        st.error("Por favor, informe o nome da sua empresa.")
        return False
    
    # Tentar salvar no Firebase silenciosamente (sem feedback ao usuário)
    # Se falhar, a aplicação continua normalmente
    save_user_to_firebase(user_data)
    
    # Retornar sucesso de qualquer forma para o fluxo da aplicação continuar
    return True

# Função para inicializar as variáveis de estado da sessão
def initialize_session_state():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {
            'nome_completo': '',
            'telefone': '',
            'email': '',
            'empresa': '',
            'industry': 'Tecnologia'
        }
    
    if 'vulnerability_results' not in st.session_state:
        st.session_state.vulnerability_results = None
    
    if 'vulnerability_questions_answered' not in st.session_state:
        st.session_state.vulnerability_questions_answered = False
    
    if 'roi_results' not in st.session_state:
        st.session_state.roi_results = None
    
    if 'show_summary' not in st.session_state:
        st.session_state.show_summary = False
    
    # Variável para controlar o estado de registro
    if 'user_registered' not in st.session_state:
        st.session_state.user_registered = False

# Configurar a página
st.set_page_config(
    page_title="Avaliação de Segurança de Dados",
    page_icon="🔒",
    layout="wide",
)

# Inicializar variáveis de estado
initialize_session_state()

# Verificar se o usuário já está registrado
if not st.session_state.user_registered:
    st.title("🔒 Avaliação de Segurança de Dados")
    st.subheader("Por favor, forneça suas informações para continuar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Nome Completo", key="nome_completo")
        st.text_input("Telefone (com DDD)", key="telefone")
    
    with col2:
        st.text_input("E-mail", key="email")
        st.text_input("Empresa", key="empresa")
    
    st.selectbox(
        "Setor de atuação",
        ["Tecnologia", "Finanças", "Saúde", "Varejo", "Educação", "Manufatura", "Serviços"],
        key="industry"
    )
    
    if st.button("Começar Avaliação"):
        if save_user_data():
            st.session_state.user_registered = True
            st.success("Informações salvas com sucesso!")
            st.rerun()
else:
    # Após o registro, mostrar todas as seções na mesma página
    
    # Cabeçalho com informações do usuário
    st.subheader(f"Bem-vindo(a), {st.session_state.user_data['nome_completo']} | Empresa: {st.session_state.user_data['empresa']}")
    
    # Definimos um valor padrão para navegação 
    if 'nav_option' not in st.session_state:
        st.session_state.nav_option = "Teste de Vulnerabilidade"
    
    # Cabeçalho principal
    st.title("🔒 Avaliação de Segurança de Dados")
    st.write(f"Bem-vindo(a) à avaliação de segurança, {st.session_state.user_data['nome_completo']}. Complete as seções abaixo para obter um diagnóstico completo.")
    
    # Seção de Teste de Vulnerabilidade
    st.markdown("<h2 id='vulnerabilidade'>📊 Teste de Vulnerabilidade</h2>", unsafe_allow_html=True)
    st.subheader(f"Avalie o nível de segurança dos dados da {st.session_state.user_data['empresa']}")
    
    # Expandir esta seção por padrão, ou se estivermos no início
    vulnerability_expanded = True
    
    vulnerability_section = st.expander("Preencher Teste de Vulnerabilidade", expanded=vulnerability_expanded)
    
    with vulnerability_section:
        # Criar as seções do formulário
        st.header("🔍 1. Infraestrutura e Acesso")
        
        infra_q1 = st.radio(
            "Sua empresa utiliza autenticação multifator (MFA) para acessos críticos?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_infra_q1"
        )
        
        infra_q2 = st.radio(
            "Os funcionários possuem diferentes níveis de acesso aos dados, de acordo com suas funções?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_infra_q2"
        )
        
        infra_q3 = st.radio(
            "Os servidores da sua empresa estão protegidos por firewalls e monitoramento contínuo?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_infra_q3"
        )
        
        infra_q4 = st.selectbox(
            "A empresa realiza backup frequente dos dados críticos?", 
            ["Diariamente", "Semanalmente", "Mensalmente", "Nunca", "Não sei"],
            key="vulnerability_infra_q4"
        )
        
        infra_q5 = st.radio(
            "Os dispositivos utilizados pelos funcionários possuem criptografia de dados ativada?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_infra_q5"
        )
        
        # Converter resposta de backup para pontuação
        backup_score = 0
        if infra_q4 == "Diariamente":
            backup_score = 1
        elif infra_q4 == "Semanalmente":
            backup_score = 0.75
        elif infra_q4 == "Mensalmente":
            backup_score = 0.5
        
        # Seção de Políticas e Procedimentos
        st.header("🔑 2. Políticas e Procedimentos")
        
        policy_q1 = st.radio(
            "Sua empresa possui uma política de segurança da informação formalizada e documentada?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_policy_q1"
        )
        
        policy_q2 = st.radio(
            "Os funcionários passam por treinamentos regulares de conscientização sobre segurança da informação?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_policy_q2"
        )
        
        policy_q3 = st.radio(
            "Há um plano de resposta a incidentes para lidar com ataques cibernéticos?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_policy_q3"
        )
        
        policy_q4 = st.radio(
            "Os fornecedores e terceiros que acessam dados da empresa seguem normas de segurança definidas?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_policy_q4"
        )
        
        policy_q5 = st.radio(
            "Existe uma política de atualização frequente para sistemas e softwares críticos?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_policy_q5"
        )
        
        # Seção de Proteção Contra Ataques
        st.header("🛡️ 3. Proteção Contra Ataques Cibernéticos")
        
        protect_q1 = st.radio(
            "A empresa realiza testes de invasão (pentests) regularmente para avaliar a segurança da rede?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_protect_q1"
        )
        
        protect_q2 = st.radio(
            "Existem sistemas ativos de detecção e resposta a ameaças (EDR, SIEM)?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_protect_q2"
        )
        
        protect_q3 = st.radio(
            "As senhas utilizadas pelos funcionários seguem boas práticas (mínimo de 12 caracteres, complexas, não reutilizadas)?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_protect_q3"
        )
        
        protect_q4 = st.radio(
            "Há um controle ativo para detectar vazamentos de dados da empresa na dark web?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_protect_q4"
        )
        
        protect_q5 = st.radio(
            "Existe uma política formal para gerenciamento de dispositivos móveis e trabalho remoto?", 
            ["Sim", "Não", "Não sei"],
            key="vulnerability_protect_q5"
        )
        
        # Botão para calcular a pontuação
        if st.button("Calcular Nível de Vulnerabilidade", key="vulnerability_calculate"):
            # Considerar "Não sei" como "Não" para os cálculos
            # Coletar respostas da infraestrutura
            infra_score = (infra_q1 == "Sim") + (infra_q2 == "Sim") + (infra_q3 == "Sim") + backup_score + (infra_q5 == "Sim")
            
            # Coletar respostas das políticas
            policy_score = (policy_q1 == "Sim") + (policy_q2 == "Sim") + (policy_q3 == "Sim") + (policy_q4 == "Sim") + (policy_q5 == "Sim")
            
            # Coletar respostas de proteção
            protect_score = (protect_q1 == "Sim") + (protect_q2 == "Sim") + (protect_q3 == "Sim") + (protect_q4 == "Sim") + (protect_q5 == "Sim")
            
            # Calcular pontuação total
            total_points = infra_score + policy_score + protect_score
            total_percent = (total_points / 15) * 100
            
            # Calcular porcentagens por categoria
            infra_percent = (infra_score / 5) * 100
            policy_percent = (policy_score / 5) * 100
            protect_percent = (protect_score / 5) * 100
            
            # Classificação de risco
            risk_level = "Crítico" if total_percent <= 40 else "Moderado" if total_percent <= 70 else "Bom"
            
            # Identificar vulnerabilidades
            vulnerabilities = []
            recommendations = []
            
            # Infraestrutura
            if infra_q1 != "Sim":
                vulnerabilities.append("Falta de autenticação multifator (MFA)")
                recommendations.append("Implemente MFA para todos os acessos críticos e contas de administrador")
                
            if infra_q2 != "Sim":
                vulnerabilities.append("Ausência de controle de acesso baseado em funções")
                recommendations.append("Defina e implemente diferentes níveis de acesso para os funcionários")
                
            if infra_q3 != "Sim":
                vulnerabilities.append("Servidores sem proteção adequada de firewall")
                recommendations.append("Instale e configure firewalls e implemente monitoramento contínuo")
                
            if infra_q4 in ["Nunca", "Não sei"]:
                vulnerabilities.append("Ausência de backup de dados críticos")
                recommendations.append("Implemente uma rotina de backup diário e teste regularmente a restauração")
                
            if infra_q5 != "Sim":
                vulnerabilities.append("Dispositivos sem criptografia de dados")
                recommendations.append("Ative a criptografia em todos os dispositivos corporativos")
            
            # Políticas
            if policy_q1 != "Sim":
                vulnerabilities.append("Ausência de política de segurança formalizada")
                recommendations.append("Desenvolva e documente uma política de segurança da informação")
                
            if policy_q2 != "Sim":
                vulnerabilities.append("Falta de treinamento de segurança para funcionários")
                recommendations.append("Implemente treinamentos regulares de conscientização sobre segurança")
                
            if policy_q3 != "Sim":
                vulnerabilities.append("Sem plano de resposta a incidentes")
                recommendations.append("Desenvolva um plano de resposta a incidentes de segurança")
                
            if policy_q4 != "Sim":
                vulnerabilities.append("Terceiros acessam dados sem seguir normas de segurança")
                recommendations.append("Estabeleça requisitos de segurança para fornecedores e parceiros")
                
            if policy_q5 != "Sim":
                vulnerabilities.append("Falta de política de atualização de sistemas")
                recommendations.append("Crie uma política para atualização regular de sistemas e softwares")
            
            # Proteção
            if protect_q1 != "Sim":
                vulnerabilities.append("Ausência de testes de invasão regulares")
                recommendations.append("Realize pentests semestralmente para identificar vulnerabilidades")
                
            if protect_q2 != "Sim":
                vulnerabilities.append("Sem sistemas de detecção e resposta a ameaças")
                recommendations.append("Implemente soluções EDR/SIEM para monitoramento em tempo real")
                
            if protect_q3 != "Sim":
                vulnerabilities.append("Senhas fracas ou reutilizadas")
                recommendations.append("Implemente política de senhas fortes e use gerenciador de senhas")
                
            if protect_q4 != "Sim":
                vulnerabilities.append("Sem monitoramento de vazamentos na dark web")
                recommendations.append("Contrate serviço de monitoramento de vazamentos de dados")
                
            if protect_q5 != "Sim":
                vulnerabilities.append("Ausência de política para dispositivos móveis e trabalho remoto")
                recommendations.append("Desenvolva política específica para trabalho remoto e BYOD")
            
            # Salvar resultados na sessão
            st.session_state.vulnerability_results = {
                "Pontuação Geral": total_percent,
                "Nível de Risco": risk_level,
                "Pontuação Infraestrutura": infra_percent,
                "Pontuação Políticas": policy_percent,
                "Pontuação Proteção": protect_percent,
                "Total de Vulnerabilidades": len(vulnerabilities),
                "Vulnerabilidades": vulnerabilities,
                "Recomendações": recommendations
            }
            
            st.session_state.vulnerability_questions_answered = True
            st.rerun()

    # Mostrar resultados do teste de vulnerabilidade se disponíveis
    if st.session_state.vulnerability_results:
        st.subheader("📊 Resultados da Avaliação de Vulnerabilidade")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Exibir gráfico de velocímetro com Plotly
            gauge_chart = create_gauge_chart_plotly(st.session_state.vulnerability_results["Pontuação Geral"])
            st.plotly_chart(gauge_chart, use_container_width=True, key="gauge_vulnerability")
            
            # Classificação de risco
            risk_level = st.session_state.vulnerability_results["Nível de Risco"]
            total_percent = st.session_state.vulnerability_results["Pontuação Geral"]
            
            if total_percent <= 40:
                st.error("🚨 RISCO CRÍTICO: A segurança da sua empresa está extremamente vulnerável. Você corre alto risco de sofrer ataques cibernéticos que podem resultar em perda de dados, fraudes e violações de compliance.")
            elif total_percent <= 70:
                st.warning("⚠️ RISCO MODERADO: Sua empresa possui algumas medidas de segurança, mas há brechas significativas. Um ataque pode comprometer suas operações e informações sensíveis.")
            else:
                st.success("✅ SEGURANÇA ACEITÁVEL: Sua empresa tem uma boa estrutura de segurança, mas ainda pode melhorar. O ideal é refinar processos e testar a resiliência contra ameaças cada vez mais sofisticadas.")
        
        with col2:
            # Exibir pontuação por categoria usando Plotly
            category_scores = {
                "Infraestrutura": st.session_state.vulnerability_results["Pontuação Infraestrutura"],
                "Políticas": st.session_state.vulnerability_results["Pontuação Políticas"],
                "Proteção": st.session_state.vulnerability_results["Pontuação Proteção"]
            }
            category_chart = create_category_chart_plotly(category_scores)
            st.plotly_chart(category_chart, use_container_width=True, key="category_vulnerability")
        
        # Exibir vulnerabilidades
        show_vulns = st.checkbox("Mostrar vulnerabilidades e recomendações", value=True)
        if show_vulns:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Principais Vulnerabilidades Detectadas")
                if "Vulnerabilidades" in st.session_state.vulnerability_results:
                    for vuln in st.session_state.vulnerability_results["Vulnerabilidades"]:
                        st.error(f"• {vuln}")
                else:
                    st.success("Não foram detectadas vulnerabilidades críticas.")
            
            with col2:
                st.subheader("Recomendações de Melhoria")
                if "Recomendações" in st.session_state.vulnerability_results:
                    for rec in st.session_state.vulnerability_results["Recomendações"]:
                        st.info(f"✓ {rec}")
        
        # Opção para download do relatório
        with st.expander("Relatório de Vulnerabilidade"):
            # Criar PDF para download
            pdf_data = create_pdf_report(
                {
                    "Pontuação Geral": st.session_state.vulnerability_results["Pontuação Geral"],
                    "Nível de Risco": st.session_state.vulnerability_results["Nível de Risco"],
                    "Pontuação Infraestrutura": st.session_state.vulnerability_results["Pontuação Infraestrutura"],
                    "Pontuação Políticas": st.session_state.vulnerability_results["Pontuação Políticas"],
                    "Pontuação Proteção": st.session_state.vulnerability_results["Pontuação Proteção"],
                    "Total de Vulnerabilidades": len(st.session_state.vulnerability_results["Vulnerabilidades"]) if "Vulnerabilidades" in st.session_state.vulnerability_results else 0
                }, 
                st.session_state.vulnerability_results.get("Vulnerabilidades", []), 
                st.session_state.vulnerability_results.get("Recomendações", []), 
                st.session_state.user_data['empresa']
            )
            
            st.markdown(
                get_pdf_download_link(
                    pdf_data, 
                    f"relatorio_seguranca_{st.session_state.user_data['empresa'].replace(' ', '_')}.pdf", 
                    "📥 Baixar Relatório de Vulnerabilidade em PDF"
                ), 
                unsafe_allow_html=True
            )

    # Seção de Calculadora de ROI
    st.markdown("<h2 id='roi'>💰 Calculadora de ROI em Segurança da Informação</h2>", unsafe_allow_html=True)
    st.subheader(f"Avalie o retorno sobre investimento em segurança cibernética para {st.session_state.user_data['empresa']}")
    
    # Definir se a seção deve estar expandida
    roi_expanded = True
    
    roi_section = st.expander("Preencher Calculadora de ROI", expanded=roi_expanded)
    
    with roi_section:
        # Custos com Incidentes
        st.header("💰 1. Custos com Incidentes Cibernéticos")
        
        num_incidents = st.number_input("Quantos ataques cibernéticos sua empresa sofreu nos últimos 12 meses?", min_value=0, value=0, step=1, key="roi_num_incidents")
        cost_per_incident = st.number_input("Qual foi o custo médio de cada incidente? (R$)", min_value=0.0, value=0.0, step=1000.0, key="roi_cost_per_incident")
        
        # Campo de tempo corrigido para usar formato de horas
        st.subheader("Tempo gasto para mitigar cada incidente")
        col1, col2 = st.columns(2)
        with col1:
            hours = st.number_input("Horas", min_value=0, value=0, step=1, key="roi_hours")
        with col2:
            minutes = st.number_input("Minutos", min_value=0, max_value=59, value=0, step=5, key="roi_minutes")
        
        # Calcular o valor total em horas
        hours_per_incident = hours + (minutes / 60)
        
        hourly_cost = st.number_input("Qual o custo médio por hora dos profissionais envolvidos na mitigação? (R$)", min_value=0.0, value=0.0, step=10.0, key="roi_hourly_cost")
        
        # Dados históricos de incidentes (opcional)
        st.subheader("Histórico de Incidentes (Opcional)")
        show_history = st.checkbox("Adicionar dados históricos de incidentes", key="roi_show_history")
        
        if show_history:
            # Definir todos os meses do ano
            all_months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            
            # Adicionar seleção de período personalizado
            st.subheader("Selecione o período de interesse")
            period_option = st.radio("Escolha uma opção:", 
                                   ["Todo o ano", "Período personalizado"],
                                   key="period_option")
            
            if period_option == "Todo o ano":
                selected_months = all_months
            else:
                # Seletor de período personalizado
                start_month, end_month = st.select_slider(
                    "Selecione o intervalo de meses:",
                    options=all_months,
                    value=(all_months[0], all_months[-1]),
                    key="month_range"
                )
                
                # Extrair o período selecionado
                start_idx = all_months.index(start_month)
                end_idx = all_months.index(end_month)
                selected_months = all_months[start_idx:end_idx+1]
            
            # Criar interface para entrada dos dados históricos
            col1, col2 = st.columns(2)
            with col1:
                incidents_history = {}
                # Usar apenas os meses selecionados
                for month in selected_months:
                    incidents_history[month] = st.number_input(f"Número de incidentes em {month}:", 
                                                             min_value=0, value=0, step=1, 
                                                             key=f"hist_{month}")
            
            # Criar DataFrame com os dados históricos
            incidents_data = pd.DataFrame({
                'Mês': list(incidents_history.keys()),
                'Número de Incidentes': list(incidents_history.values())
            })
            
            # Mostrar gráfico de tendência
            with col2:
                if sum(incidents_history.values()) > 0:
                    trend_chart = create_incident_trend_chart(incidents_data)
                    st.plotly_chart(trend_chart, use_container_width=True, key="trend_incidents")
                else:
                    st.info("Adicione dados de incidentes para visualizar a tendência.")
        
        # Investimentos em Segurança
        st.header("🔐 2. Investimentos em Segurança")
        
        security_investment = st.number_input("Quanto sua empresa investiu em segurança da informação nos últimos 12 meses? (R$)", min_value=0.0, value=0.0, step=1000.0, key="roi_security_investment")
        reduced_incidents = st.radio("Esse investimento reduziu a frequência ou o impacto dos ataques?", ["Sim", "Não", "Não sei"], key="roi_reduced_incidents")
        
        if reduced_incidents == "Sim":
            new_num_incidents = st.number_input("Número reduzido de ataques por ano após o investimento:", min_value=0, value=0, step=1, key="roi_new_num_incidents")
            new_cost_per_incident = st.number_input("Novo custo médio por incidente após o investimento (R$):", min_value=0.0, value=0.0, step=1000.0, key="roi_new_cost_per_incident")
            
            # Novo campo de tempo para a mitigação após o investimento
            st.subheader("Novo tempo de mitigação após investimento")
            col1, col2 = st.columns(2)
            with col1:
                new_hours = st.number_input("Horas", min_value=0, value=0, step=1, key="roi_new_hours")
            with col2:
                new_minutes = st.number_input("Minutos", min_value=0, max_value=59, value=0, step=5, key="roi_new_minutes")
            
            # Calcular novo valor total em horas
            new_hours_per_incident = new_hours + (new_minutes / 60)
        else:
            new_num_incidents = num_incidents
            new_cost_per_incident = cost_per_incident
            new_hours_per_incident = hours_per_incident
        
        # Impacto nos Negócios
        st.header("📈 3. Impacto nos Negócios")
        
        lost_customers = st.radio("Algum incidente de segurança resultou na perda de clientes?", ["Sim", "Não", "Não sei"], key="roi_lost_customers")
        
        if lost_customers == "Sim":
            num_lost_customers = st.number_input("Quantos clientes foram perdidos?", min_value=0, value=0, step=1, key="roi_num_lost_customers")
            average_ticket = st.number_input("Qual é o ticket médio anual de um cliente para sua empresa? (R$)", min_value=0.0, value=0.0, step=1000.0, key="roi_average_ticket")
        else:
            num_lost_customers = 0
            average_ticket = 0.0
        
        # Botão para calcular ROI
        if st.button("Calcular ROI", key="roi_calculate"):
            # Tratar respostas "Não sei" como "Não"
            if reduced_incidents == "Não sei":
                reduced_incidents = "Não"
            
            if lost_customers == "Não sei":
                lost_customers = "Não"
            
            # Calcular custo total antes
            total_cost_before = (num_incidents * cost_per_incident) + (num_incidents * hours_per_incident * hourly_cost)
            
            # Calcular custo total depois
            total_cost_after = (new_num_incidents * new_cost_per_incident) + (new_num_incidents * new_hours_per_incident * hourly_cost)
            
            # Calcular economia obtida
            savings = total_cost_before - total_cost_after
            
            # Calcular ROI
            if security_investment > 0:
                roi = ((savings - security_investment) / security_investment) * 100
            else:
                roi = 0
            
            # Calcular perda de receita com clientes
            revenue_loss = num_lost_customers * average_ticket
            
            # Salvar resultados na sessão
            st.session_state.roi_results = {
                "Investimento": security_investment,
                "Economia": savings,
                "ROI": roi,
                "Perda de Clientes": revenue_loss,
                "Impacto Total": savings - revenue_loss,
                "Custo Total Antes": total_cost_before,
                "Custo Total Depois": total_cost_after,
                "Num Incidentes Antes": num_incidents,
                "Num Incidentes Depois": new_num_incidents,
                "Custo por Incidente Antes": cost_per_incident,
                "Custo por Incidente Depois": new_cost_per_incident,
                "Horas por Incidente Antes": hours_per_incident,
                "Horas por Incidente Depois": new_hours_per_incident,
                "hourly_cost": hourly_cost
            }
            
            st.rerun()
    
    # Mostrar resultados do ROI se disponíveis
    if st.session_state.roi_results:
        st.subheader("📊 Resultados da Análise de ROI")
        
        # Extrair dados para exibição
        investment = st.session_state.roi_results["Investimento"]
        savings = st.session_state.roi_results["Economia"]
        roi = st.session_state.roi_results["ROI"]
        total_cost_before = st.session_state.roi_results.get("Custo Total Antes", 0)
        total_cost_after = st.session_state.roi_results.get("Custo Total Depois", 0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Custos Antes do Investimento")
            st.info(f"Número de incidentes: {st.session_state.roi_results.get('Num Incidentes Antes', 0)}")
            st.info(f"Custo médio por incidente: {format_currency(st.session_state.roi_results.get('Custo por Incidente Antes', 0))}")
            st.info(f"Tempo médio de resolução: {format_hours(st.session_state.roi_results.get('Horas por Incidente Antes', 0))}")
            st.info(f"Custo total com incidentes: {format_currency(total_cost_before)}")
        
        with col2:
            st.subheader("Custos Após o Investimento")
            st.info(f"Investimento em segurança: {format_currency(investment)}")
            st.info(f"Número reduzido de incidentes: {st.session_state.roi_results.get('Num Incidentes Depois', 0)}")
            st.info(f"Novo custo médio por incidente: {format_currency(st.session_state.roi_results.get('Custo por Incidente Depois', 0))}")
            st.info(f"Custo total reduzido: {format_currency(total_cost_after)}")
        
        # Exibir gráfico de ROI com Plotly
        st.subheader("Análise de ROI")
        roi_chart = create_roi_chart_plotly(investment, total_cost_before, total_cost_after)
        st.plotly_chart(roi_chart, use_container_width=True, key="roi_chart_main")
        
        # Resumo financeiro
        st.subheader("Resumo Financeiro")
        st.success(f"Economia direta obtida: {format_currency(savings)}")
        
        if roi >= 0:
            st.success(f"ROI do investimento em segurança: {format_percent(roi)}")
        else:
            st.error(f"ROI do investimento em segurança: {format_percent(roi)}")
            
        # Exibir informações sobre perda de clientes se disponível
        if "Perda de Clientes" in st.session_state.roi_results and st.session_state.roi_results["Perda de Clientes"] > 0:
            revenue_loss = st.session_state.roi_results["Perda de Clientes"]
            st.error(f"Perda de receita devido a clientes perdidos: {format_currency(revenue_loss)}")
            st.info(f"Impacto financeiro total (economia - perda de clientes): {format_currency(savings - revenue_loss)}")
        
        # Análise detalhada de custos
        with st.expander("Análise Detalhada de Custos"):
            # Preparar dados para gráfico de pizza
            cost_breakdown_before = {
                "Custos diretos com incidentes": st.session_state.roi_results.get('Num Incidentes Antes', 0) * st.session_state.roi_results.get('Custo por Incidente Antes', 0),
                "Custos com horas de trabalho": st.session_state.roi_results.get('Num Incidentes Antes', 0) * st.session_state.roi_results.get('Horas por Incidente Antes', 0) * st.session_state.roi_results.get('hourly_cost', 0)
            }
            
            cost_breakdown_after = {
                "Custos diretos com incidentes": st.session_state.roi_results.get('Num Incidentes Depois', 0) * st.session_state.roi_results.get('Custo por Incidente Depois', 0),
                "Custos com horas de trabalho": st.session_state.roi_results.get('Num Incidentes Depois', 0) * st.session_state.roi_results.get('Horas por Incidente Depois', 0) * st.session_state.roi_results.get('hourly_cost', 0)
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                pie_before = create_pie_chart_plotly(cost_breakdown_before, "Custos Antes do Investimento")
                st.plotly_chart(pie_before, use_container_width=True, key="pie_before")
                
            with col2:
                pie_after = create_pie_chart_plotly(cost_breakdown_after, "Custos Após o Investimento")
                st.plotly_chart(pie_after, use_container_width=True, key="pie_after")
        
        # Recomendações
        if roi < 0:
            recommendations = [
                "Reavalie as medidas de segurança implementadas para garantir maior eficácia.",
                "Considere investir em soluções com melhor custo-benefício.",
                "Concentre os recursos em proteger os ativos mais críticos primeiro."
            ]
        elif roi < 50:
            recommendations = [
                "Continue investindo em segurança, focando em áreas de maior risco.",
                "Implemente treinamentos de conscientização para reduzir incidentes causados por erro humano.",
                "Considere automatizar processos de segurança para reduzir custos operacionais."
            ]
        else:
            recommendations = [
                "Mantenha o investimento em segurança e considere expandi-lo para outras áreas.",
                "Compartilhe métricas de sucesso com a liderança para garantir continuidade do orçamento.",
                "Implemente um programa de melhoria contínua para manter os resultados positivos."
            ]
        
        with st.expander("Recomendações Estratégicas"):
            for rec in recommendations:
                st.info(f"• {rec}")
                
            # Opção para download do relatório
            pdf_data = create_pdf_report(
                st.session_state.roi_results,
                [],
                recommendations,
                st.session_state.user_data['empresa']
            )
            
            st.markdown(
                get_pdf_download_link(
                    pdf_data,
                    f"relatorio_roi_seguranca_{st.session_state.user_data['empresa'].replace(' ', '_')}.pdf",
                    "📥 Baixar Relatório de ROI em PDF"
                ),
                unsafe_allow_html=True
            )

    # Seção de Benchmarking
    st.markdown("<h2 id='benchmarking'>🌐 Benchmarking de Segurança</h2>", unsafe_allow_html=True)
    st.subheader(f"Compare o nível de segurança da {st.session_state.user_data['empresa']} com a média do seu setor")
    
    # Definir se a seção deve estar expandida
    benchmark_expanded = True
    
    benchmark_section = st.expander("Visualizar Benchmarking", expanded=benchmark_expanded)
    
    with benchmark_section:
        # Verificar se temos resultados do teste de vulnerabilidade
        if not st.session_state.vulnerability_results:
            st.warning("Para realizar o benchmarking, é necessário primeiro completar o Teste de Vulnerabilidade.")
            
            # Botão para ir para o teste de vulnerabilidade
            if st.button("Ir para o Teste de Vulnerabilidade", key="go_to_vulnerability"):
                st.rerun()
        else:
            # Usar automaticamente os resultados do teste de vulnerabilidade
            infra_score = st.session_state.vulnerability_results["Pontuação Infraestrutura"]
            policy_score = st.session_state.vulnerability_results["Pontuação Políticas"]
            protect_score = st.session_state.vulnerability_results["Pontuação Proteção"]
            total_score = st.session_state.vulnerability_results["Pontuação Geral"]
            
            # Mostrar ao usuário que estamos usando os dados do teste anterior
            st.success("Utilizando automaticamente os resultados do seu teste de vulnerabilidade anterior.")
            
            # Exibir os valores utilizados
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Infraestrutura", f"{infra_score:.1f}%")
            with col2:
                st.metric("Políticas", f"{policy_score:.1f}%")
            with col3:
                st.metric("Proteção", f"{protect_score:.1f}%")
                
            st.metric("Pontuação Geral", f"{total_score:.1f}%")
            
            # Setor da empresa (já obtido no registro)
            industry = st.session_state.user_data['industry']
            st.write(f"Setor selecionado: **{industry}**")
            
            # Obter dados de benchmark
            benchmark_data = get_benchmark_data()
            
            # Botão para comparar
            if st.button("Comparar com o Setor", key="benchmark_compare"):
                # Criar dados para comparação
                company_scores = {
                    "Infraestrutura": infra_score,
                    "Políticas": policy_score,
                    "Proteção": protect_score,
                    "Total": total_score
                }
                
                # Salvar na sessão
                st.session_state.benchmark_results = {
                    "Company": company_scores,
                    "Industry": benchmark_data[industry],
                    "IndustryName": industry
                }
                
                st.rerun()
    
    # Mostrar resultados do benchmarking se disponíveis
    if hasattr(st.session_state, 'benchmark_results') and st.session_state.benchmark_results:
        benchmark_results = st.session_state.benchmark_results
        company_scores = benchmark_results["Company"]
        industry_data = benchmark_results["Industry"]
        industry = benchmark_results["IndustryName"]
        
        st.subheader("📈 Análise Comparativa de Benchmarking")
        
        # Visualização da pontuação geral
        st.write("### Pontuação Geral vs. Média do Setor")
        
        # Criar DataFrame para comparação
        comparison_df = pd.DataFrame({
            'Entidade': ['Sua Empresa', f'Média do Setor: {industry}'],
            'Pontuação': [company_scores['Total'], industry_data['Total']]
        })
        
        # Criar gráfico de barras para comparação geral
        fig_general = px.bar(
            comparison_df, 
            x='Entidade', 
            y='Pontuação',
            color='Entidade',
            text_auto='.1f',
            title=f"Comparação da Pontuação Geral - {st.session_state.user_data['empresa']} vs. Média do Setor: {industry}",
            color_discrete_map={'Sua Empresa': 'blue', f'Média do Setor: {industry}': 'green'}
        )
        
        fig_general.update_layout(
            yaxis_title="Pontuação (%)",
            yaxis=dict(range=[0, 100]),
            height=400
        )
        
        st.plotly_chart(fig_general, use_container_width=True, key="benchmark_general")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Análise por categoria com gráfico de radar
            st.write("### Análise Detalhada por Categoria")
            radar_chart = create_radar_chart(company_scores, benchmark_data, industry)
            st.plotly_chart(radar_chart, use_container_width=True, key="radar_benchmark")
        
        with col2:
            # Diferenças por categoria
            st.write("### Diferenças por Categoria")
            
            # Criar DataFrame para diferenças
            diff_data = []
            for category in ['Infraestrutura', 'Políticas', 'Proteção', 'Total']:
                company_value = company_scores[category]
                benchmark_value = industry_data[category]
                diff = company_value - benchmark_value
                
                diff_data.append({
                    'Categoria': category,
                    'Sua Empresa': company_value,
                    f'Média do Setor: {industry}': benchmark_value,
                    'Diferença': diff,
                    'Status': 'Acima da Média' if diff >= 0 else 'Abaixo da Média'
                })
            
            diff_df = pd.DataFrame(diff_data)
            
            # Formatar a tabela para exibição
            display_diff = diff_df.copy()
            display_diff['Sua Empresa'] = display_diff['Sua Empresa'].apply(lambda x: f"{x:.1f}%")
            display_diff[f'Média do Setor: {industry}'] = display_diff[f'Média do Setor: {industry}'].apply(lambda x: f"{x:.1f}%")
            display_diff['Diferença'] = display_diff['Diferença'].apply(lambda x: f"{x:+.1f}%")
            
            # Exibir tabela estilizada
            st.dataframe(
                display_diff[['Categoria', 'Sua Empresa', f'Média do Setor: {industry}', 'Diferença', 'Status']],
                use_container_width=True
            )
        
        # Expandir para mais análises
        with st.expander("Análise Adicional de Benchmarking"):
            # Gráfico de todos os setores para comparação
            st.subheader("Comparação com Todos os Setores")
            
            # Preparar dados para o gráfico
            all_industries_data = []
            for ind in benchmark_data.keys():
                all_industries_data.append({
                    'Setor': ind,
                    'Pontuação': benchmark_data[ind]['Total']
                })
            
            # Adicionar a empresa
            all_industries_data.append({
                'Setor': 'Sua Empresa',
                'Pontuação': company_scores['Total']
            })
            
            all_industries_df = pd.DataFrame(all_industries_data)
            
            # Ordenar por pontuação
            all_industries_df = all_industries_df.sort_values('Pontuação', ascending=False)
            
            # Criar gráfico de barras para todos os setores
            fig_all = px.bar(
                all_industries_df,
                x='Setor',
                y='Pontuação',
                text_auto='.1f',
                title='Comparação com Todos os Setores',
                color='Setor',
                color_discrete_map={
                    'Sua Empresa': 'blue',
                    **{ind: 'lightgreen' if ind == industry else 'lightgray' for ind in benchmark_data.keys()}
                }
            )
            
            fig_all.update_layout(
                yaxis_title='Pontuação (%)',
                yaxis=dict(range=[0, 100]),
                xaxis_title='',
                height=500
            )
            
            st.plotly_chart(fig_all, use_container_width=True, key="all_sectors")
            
            # Recomendações baseadas nas diferenças
            st.subheader("Análise e Recomendações")
            
            overall_status = "acima" if company_scores['Total'] >= industry_data["Total"] else "abaixo"
            st.write(f"Sua empresa está **{overall_status}** da média do setor **{industry}**, com uma pontuação geral de **{company_scores['Total']:.1f}%** comparada à média de **{industry_data['Total']}%**.")
            
            # Identificar pontos fortes e fracos
            strengths = []
            weaknesses = []
            
            for category in ['Infraestrutura', 'Políticas', 'Proteção']:
                diff = company_scores[category] - industry_data[category]
                if diff >= 5:
                    strengths.append((category, diff))
                elif diff <= -5:
                    weaknesses.append((category, diff))
            
            # Exibir pontos fortes
            if strengths:
                st.success("#### 💪 Pontos Fortes")
                for strength, diff in strengths:
                    st.success(f"• {strength}: Sua empresa está **{diff:+.1f}%** acima da média do setor.")
            
            # Exibir pontos fracos
            recommendations = []
            if weaknesses:
                st.error("#### ⚠️ Áreas para Melhoria")
                for weakness, diff in weaknesses:
                    st.error(f"• {weakness}: Sua empresa está **{diff:+.1f}%** abaixo da média do setor.")
                    
                    # Recomendações específicas
                    if weakness == "Infraestrutura":
                        rec = "Implemente autenticação multifator, reforce a proteção de servidores e estabeleça política de backup regular."
                        st.info(f"**Recomendações**: {rec}")
                        recommendations.append(rec)
                    elif weakness == "Políticas":
                        rec = "Desenvolva política formal de segurança, realize treinamentos regulares e crie planos de resposta a incidentes."
                        st.info(f"**Recomendações**: {rec}")
                        recommendations.append(rec)
                    elif weakness == "Proteção":
                        rec = "Implemente sistemas de detecção e resposta a ameaças, realize testes de invasão regularmente e reforce políticas de senhas."
                        st.info(f"**Recomendações**: {rec}")
                        recommendations.append(rec)
            
            # Se não houver pontos fracos significativos
            if not weaknesses:
                rec = "Continue mantendo altos padrões de segurança e busque melhorias contínuas."
                st.success(f"Parabéns! Sua empresa está em boa posição em relação à média do setor. {rec}")
                recommendations.append(rec)
            
            # Opção para download do relatório
            benchmark_report_data = {
                "Pontuação Geral": company_scores['Total'],
                "Média do Setor": industry_data["Total"],
                "Diferença": company_scores['Total'] - industry_data["Total"],
                "Pontuação Infraestrutura": company_scores['Infraestrutura'],
                "Pontuação Políticas": company_scores['Políticas'],
                "Pontuação Proteção": company_scores['Proteção'],
                "Nível de Risco": "Acima da Média" if company_scores['Total'] >= industry_data["Total"] else "Abaixo da Média"
            }
            
            # Criar PDF para download
            pdf_data = create_pdf_report(benchmark_report_data, [], recommendations, st.session_state.user_data['empresa'])
            
            st.markdown(
                get_pdf_download_link(
                    pdf_data, 
                    f"relatorio_benchmarking_{st.session_state.user_data['empresa'].replace(' ', '_')}.pdf", 
                    "📥 Baixar Relatório de Benchmarking em PDF"
                ), 
                unsafe_allow_html=True
            )

    # Seção para Download do Relatório Completo
    st.markdown("<h2 id='relatorio'>📊 Relatório Completo da Avaliação</h2>", unsafe_allow_html=True)
    
    with st.container():
        # Verificar quais análises foram realizadas
        has_vulnerability = 'vulnerability_results' in st.session_state and st.session_state.vulnerability_results
        has_roi = 'roi_results' in st.session_state and st.session_state.roi_results
        has_benchmark = hasattr(st.session_state, 'benchmark_results') and st.session_state.benchmark_results
        
        # Alertas sobre dados incompletos
        incomplete_data = []
        if not has_vulnerability:
            incomplete_data.append("Teste de Vulnerabilidade")
        if not has_roi:
            incomplete_data.append("Calculadora de ROI")
        if not has_benchmark:
            incomplete_data.append("Benchmarking")
        
        if incomplete_data:
            st.warning(f"⚠️ Atenção: Você ainda não completou as seguintes análises: {', '.join(incomplete_data)}. Para um relatório completo, recomendamos preencher todas as seções.")
        else:
            st.success("✅ Parabéns! Você completou todas as análises e seu relatório está pronto para download.")
        
        # Preparar dados para relatório integrado
        all_results = {}
        all_vulnerabilities = []
        all_recommendations = []
        
        if has_vulnerability:
            # Adicionar dados de vulnerabilidade
            for key, value in st.session_state.vulnerability_results.items():
                if key not in ["Vulnerabilidades", "Recomendações"]:
                    all_results[key] = value
            
            # Adicionar vulnerabilidades e recomendações
            if "Vulnerabilidades" in st.session_state.vulnerability_results:
                all_vulnerabilities.extend(st.session_state.vulnerability_results["Vulnerabilidades"])
            
            if "Recomendações" in st.session_state.vulnerability_results:
                all_recommendations.extend(st.session_state.vulnerability_results["Recomendações"])
        
        if has_roi:
            # Adicionar dados de ROI
            for key, value in st.session_state.roi_results.items():
                if key not in ["hourly_cost"]:  # Excluir dados auxiliares
                    all_results[key] = value
                
        if has_benchmark:
            # Adicionar dados de benchmarking
            all_results["Média do Setor"] = st.session_state.benchmark_results["Industry"]["Total"]
            all_results["Diferença com Setor"] = st.session_state.benchmark_results["Company"]["Total"] - st.session_state.benchmark_results["Industry"]["Total"]
        
        # Coletar os gráficos gerados
        figures = {}

        # Verificar quais gráficos estão disponíveis e adicioná-los
        if has_vulnerability:
            # Adicionar gráfico do velocímetro
            gauge_chart = create_gauge_chart_plotly(st.session_state.vulnerability_results["Pontuação Geral"])
            figures['gauge'] = gauge_chart
            
            # Adicionar gráfico de categorias
            category_scores = {
                "Infraestrutura": st.session_state.vulnerability_results["Pontuação Infraestrutura"],
                "Políticas": st.session_state.vulnerability_results["Pontuação Políticas"],
                "Proteção": st.session_state.vulnerability_results["Pontuação Proteção"]
            }
            category_chart = create_category_chart_plotly(category_scores)
            figures['category'] = category_chart

        if has_roi:
            # Adicionar gráfico de ROI
            investment = st.session_state.roi_results["Investimento"]
            total_before = st.session_state.roi_results.get("Custo Total Antes", 0)
            total_after = st.session_state.roi_results.get("Custo Total Depois", 0)
            roi_chart = create_roi_chart_plotly(investment, total_before, total_after)
            figures['roi'] = roi_chart
            
            # Dados para gráficos de pizza
            cost_breakdown_before = {
                "Custos diretos com incidentes": st.session_state.roi_results.get('Num Incidentes Antes', 0) * st.session_state.roi_results.get('Custo por Incidente Antes', 0),
                "Custos com horas de trabalho": st.session_state.roi_results.get('Num Incidentes Antes', 0) * st.session_state.roi_results.get('Horas por Incidente Antes', 0) * st.session_state.roi_results.get('hourly_cost', 0)
            }
            
            cost_breakdown_after = {
                "Custos diretos com incidentes": st.session_state.roi_results.get('Num Incidentes Depois', 0) * st.session_state.roi_results.get('Custo por Incidente Depois', 0),
                "Custos com horas de trabalho": st.session_state.roi_results.get('Num Incidentes Depois', 0) * st.session_state.roi_results.get('Horas por Incidente Depois', 0) * st.session_state.roi_results.get('hourly_cost', 0)
            }
            
            pie_before = create_pie_chart_plotly(cost_breakdown_before, "Custos Antes do Investimento")
            pie_after = create_pie_chart_plotly(cost_breakdown_after, "Custos Após o Investimento")
            
            figures['pie_before'] = pie_before
            figures['pie_after'] = pie_after

        if has_benchmark:
            # Adicionar gráfico de radar para benchmarking
            company_scores = st.session_state.benchmark_results["Company"]
            industry_data = get_benchmark_data()
            industry = st.session_state.benchmark_results["IndustryName"]
            
            radar_chart = create_radar_chart(company_scores, industry_data, industry)
            figures['radar'] = radar_chart
            
            # Preparar dados para o gráfico de todos os setores
            all_industries_data = []
            for ind in industry_data.keys():
                all_industries_data.append({
                    'Setor': ind,
                    'Pontuação': industry_data[ind]['Total']
                })
            
            # Adicionar a empresa
            all_industries_data.append({
                'Setor': 'Sua Empresa',
                'Pontuação': company_scores['Total']
            })
            
            all_industries_df = pd.DataFrame(all_industries_data)
            all_industries_df = all_industries_df.sort_values('Pontuação', ascending=False)
            
            fig_all = px.bar(
                all_industries_df,
                x='Setor',
                y='Pontuação',
                text_auto='.1f',
                title='Comparação com Todos os Setores',
                color='Setor',
                color_discrete_map={
                    'Sua Empresa': 'blue',
                    **{ind: 'lightgreen' if ind == industry else 'lightgray' for ind in industry_data.keys()}
                }
            )
            
            fig_all.update_layout(
                yaxis_title='Pontuação (%)',
                yaxis=dict(range=[0, 100]),
                xaxis_title='',
                height=500
            )
            
            figures['all_sectors'] = fig_all
        
# Criar PDF para download com o novo parâmetro "figures"
        try:
            if all_results and len(all_results) > 0:
                pdf_data = create_pdf_report(
                    all_results, 
                    all_vulnerabilities, 
                    all_recommendations, 
                    st.session_state.user_data['empresa'], 
                    report_type="complete", 
                    figures=figures
                )
            else:
                # Criar um PDF básico sem dados de avaliação
                pdf_data = create_pdf_report({}, [], [], st.session_state.user_data['empresa'])
        except Exception as e:
            st.error(f"Erro ao gerar o relatório. Por favor, tente novamente.")
            # Garantir que pdf_data seja definido mesmo em caso de erro
            pdf_data = None
        
        # Seção de download com destaque
        st.markdown("### 📥 Download do Relatório Completo")
        st.info("""
        O relatório completo inclui:
        - Resumo executivo de todas as análises realizadas
        - Detalhes das vulnerabilidades identificadas
        - Recomendações personalizadas
        - Análise financeira de ROI (se realizada)
        - Benchmarking do setor (se realizado)
        - Todos os gráficos e visualizações gerados durante a análise
        """)
        
        # Botão para download do relatório PDF completo em destaque
        centered_col = st.columns([1, 2, 1])[1]  # Criar uma coluna centralizada
        with centered_col:
            if pdf_data is not None:
                st.markdown(
                    get_pdf_download_link(
                        pdf_data, 
                        f"relatorio_completo_{st.session_state.user_data['empresa'].replace(' ', '_')}.pdf", 
                        "📥 BAIXAR RELATÓRIO COMPLETO EM PDF"
                    ), 
                    unsafe_allow_html=True
                )
            else:
                st.error("Não foi possível gerar o relatório PDF. Por favor, tente novamente.")
        
        st.markdown("---")
        
        # Botões de ação
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Começar Nova Avaliação", key="new_assessment"):
                # Limpar dados de sessão
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                
                # Reinicializar
                initialize_session_state()
                st.rerun()
# Rodapé
st.markdown("---")
st.markdown("Desenvolvido por Beirama para avaliação de segurança da informação | © 2025")