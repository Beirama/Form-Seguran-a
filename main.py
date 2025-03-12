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
from datetime import datetime
import re

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
def create_pdf_report(results, vulnerabilities, recommendations, company_name="Sua Empresa"):
    buffer = io.BytesIO()
    # Usar margens menores para mais espaço útil na página
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
    elements.append(Paragraph(f"RELATÓRIO DE SEGURANÇA DE DADOS", title_style))
    elements.append(Paragraph(f"{company_name}", subtitle_style))
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    elements.append(Spacer(1, 0.5*inch))
    
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
    
    if report_type == "vulnerability":
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
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email))

# Função para salvar dados do usuário
def save_user_data():
    st.session_state.user_data['nome_completo'] = st.session_state.nome_completo
    st.session_state.user_data['telefone'] = st.session_state.telefone
    st.session_state.user_data['email'] = st.session_state.email
    st.session_state.user_data['empresa'] = st.session_state.empresa
    
    # Validar dados antes de prosseguir
    if not st.session_state.nome_completo:
        st.error("Por favor, informe seu nome completo.")
        return False
    
    if not validate_phone(st.session_state.telefone):
        st.error("Por favor, informe um número de telefone válido com DDD.")
        return False
    
    if not validate_email(st.session_state.email):
        st.error("Por favor, informe um endereço de e-mail válido.")
        return False
    
    if not st.session_state.empresa:
        st.error("Por favor, informe o nome da sua empresa.")
        return False
    
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
        hours_per_incident = st.number_input("Quanto tempo sua equipe gastou para mitigar cada incidente? (horas)", min_value=0.0, value=0.0, step=1.0, key="roi_hours_per_incident")
        hourly_cost = st.number_input("Qual o custo médio por hora dos profissionais envolvidos na mitigação? (R$)", min_value=0.0, value=0.0, step=10.0, key="roi_hourly_cost")
        
        # Dados históricos de incidentes (opcional)
        st.subheader("Histórico de Incidentes (Opcional)")
        show_history = st.checkbox("Adicionar dados históricos de incidentes", key="roi_show_history")
        
        if show_history:
            col1, col2 = st.columns(2)
            with col1:
                incidents_history = {}
                months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho"]
                for month in months:
                    incidents_history[month] = st.number_input(f"Número de incidentes em {month}:", min_value=0, value=0, step=1, key=f"hist_{month}")
            
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
            new_hours_per_incident = st.number_input("Novo tempo de resposta por incidente (horas):", min_value=0.0, value=0.0, step=1.0, key="roi_new_hours_per_incident")
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

    # Seção de Resumo Completo
    st.markdown("<h2 id='resumo'>📊 Resumo Completo da Avaliação</h2>", unsafe_allow_html=True)
    
    # Definir se a seção deve estar expandida
    summary_expanded = True
    
    summary_section = st.expander("Visualizar Resumo Completo", expanded=summary_expanded)
    
    with summary_section:
        st.subheader(f"Resumo Completo da Avaliação para {st.session_state.user_data['empresa']}")
        
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
            st.warning(f"Atenção: Você ainda não completou as seguintes análises: {', '.join(incomplete_data)}. Para um relatório completo, recomendamos preencher todas as seções.")
        else:
            st.success("Parabéns! Você completou todas as análises. Abaixo está o resumo completo.")
        
        # Dados do usuário
        st.write("### 👤 Dados do Contato")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Nome**: {st.session_state.user_data['nome_completo']}")
            st.write(f"**Telefone**: {st.session_state.user_data['telefone']}")
        with col2:
            st.write(f"**E-mail**: {st.session_state.user_data['email']}")
            st.write(f"**Empresa**: {st.session_state.user_data['empresa']}")
        st.write(f"**Setor**: {st.session_state.user_data['industry']}")
        
        # Resultados de Vulnerabilidade
        if has_vulnerability:
            st.write("### 🔒 Resultados da Avaliação de Vulnerabilidade")
            col1, col2 = st.columns(2)
            
            with col1:
                score = st.session_state.vulnerability_results["Pontuação Geral"]
                risk_level = st.session_state.vulnerability_results["Nível de Risco"]
                
                # Mostrar o medidor de pontuação
                gauge_chart = create_gauge_chart_plotly(score)
                st.plotly_chart(gauge_chart, use_container_width=True, key="gauge_summary")
                
                if score <= 40:
                    st.error(f"🚨 Nível de Risco: **{risk_level}**")
                elif score <= 70:
                    st.warning(f"⚠️ Nível de Risco: **{risk_level}**")
                else:
                    st.success(f"✅ Nível de Risco: **{risk_level}**")
            
            with col2:
                # Pontuações por categoria
                category_scores = {
                    "Infraestrutura": st.session_state.vulnerability_results["Pontuação Infraestrutura"],
                    "Políticas": st.session_state.vulnerability_results["Pontuação Políticas"],
                    "Proteção": st.session_state.vulnerability_results["Pontuação Proteção"]
                }
                category_chart = create_category_chart_plotly(category_scores)
                st.plotly_chart(category_chart, use_container_width=True, key="category_summary")
            
# Vulnerabilidades e recomendações
st.subheader("Vulnerabilidades e Recomendações")
show_vuln_rec = st.checkbox("Mostrar detalhes de vulnerabilidades e recomendações", 
                            key="show_vuln_rec_summary")

if show_vuln_rec:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Principais Vulnerabilidades")
        if "Vulnerabilidades" in st.session_state.vulnerability_results and st.session_state.vulnerability_results["Vulnerabilidades"]:
            for vuln in st.session_state.vulnerability_results["Vulnerabilidades"]:
                st.error(f"• {vuln}")
        else:
            st.success("Não foram detectadas vulnerabilidades significativas.")
    
    with col2:
        st.subheader("Recomendações de Segurança")
        if "Recomendações" in st.session_state.vulnerability_results and st.session_state.vulnerability_results["Recomendações"]:
            for rec in st.session_state.vulnerability_results["Recomendações"]:
                st.info(f"✓ {rec}")
        else:
            st.warning("### 🔒 Avaliação de Vulnerabilidade não realizada")
            if st.button("Ir para Teste de Vulnerabilidade", key="goto_vuln"):
                st.rerun()
        
        # Resultados de ROI
        if has_roi:
            st.write("### 💰 Resultados da Análise de ROI")
            
            investment = st.session_state.roi_results["Investimento"]
            savings = st.session_state.roi_results["Economia"]
            roi = st.session_state.roi_results["ROI"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Investimento", format_currency(investment))
                st.metric("Economia", format_currency(savings))
                if "Perda de Clientes" in st.session_state.roi_results:
                    st.metric("Perda de Receita", format_currency(st.session_state.roi_results["Perda de Clientes"]))
            
            with col2:
                # Exibir o ROI com cor apropriada
                if roi >= 0:
                    st.success(f"ROI: **{format_percent(roi)}**")
                else:
                    st.error(f"ROI: **{format_percent(roi)}**")
                    
                if "Impacto Total" in st.session_state.roi_results:
                    if st.session_state.roi_results["Impacto Total"] >= 0:
                        st.success(f"Impacto Total: **{format_currency(st.session_state.roi_results['Impacto Total'])}**")
                    else:
                        st.error(f"Impacto Total: **{format_currency(st.session_state.roi_results['Impacto Total'])}**")
                        
            # Mostrar gráfico de ROI
            if "Custo Total Antes" in st.session_state.roi_results and "Custo Total Depois" in st.session_state.roi_results:
                roi_chart = create_roi_chart_plotly(
                    investment, 
                    st.session_state.roi_results["Custo Total Antes"], 
                    st.session_state.roi_results["Custo Total Depois"]
                )
                st.plotly_chart(roi_chart, use_container_width=True, key="roi_summary")
        else:
            st.warning("### 💰 Análise de ROI não realizada")
            if st.button("Ir para Calculadora de ROI", key="goto_roi"):
                st.rerun()
        
        # Resultados de Benchmarking
        if has_benchmark:
            st.write("### 🌐 Resultados do Benchmarking")
            
            benchmark_results = st.session_state.benchmark_results
            company_scores = benchmark_results["Company"]
            industry_data = benchmark_results["Industry"]
            industry = benchmark_results["IndustryName"]
            
            # Gráfico de radar comparativo
            radar_chart = create_radar_chart(company_scores, get_benchmark_data(), industry)
            st.plotly_chart(radar_chart, use_container_width=True, key="radar_summary")
            
            # Status geral
            company_total = company_scores["Total"]
            industry_total = industry_data["Total"]
            difference = company_total - industry_total
            
            if difference >= 0:
                st.success(f"Sua empresa está **{difference:+.1f}%** acima da média do setor **{industry}**.")
            else:
                st.error(f"Sua empresa está **{difference:+.1f}%** abaixo da média do setor **{industry}**.")
        elif has_vulnerability:
            st.warning("### 🌐 Benchmarking não realizado")
            if st.button("Ir para Benchmarking", key="goto_benchmark"):
                st.rerun()
        
        # Download do relatório completo
        st.write("### 📑 Relatório Completo")
        
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
        
        # Criar PDF para download
        pdf_data = create_pdf_report(all_results, all_vulnerabilities, all_recommendations, st.session_state.user_data['empresa'])
        
        # Botão para download do relatório PDF completo
        st.markdown(
            get_pdf_download_link(
                pdf_data, 
                f"relatorio_completo_{st.session_state.user_data['empresa'].replace(' ', '_')}.pdf", 
                "📥 Baixar Relatório Completo em PDF"
            ), 
            unsafe_allow_html=True
        )
        
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
        
       # with col2:
            #if st.button("Editar Informações de Contato", key="edit_contact"):
                #st.session_state.user_registered = False
                #st.rerun()

# Rodapé
st.markdown("---")
st.markdown("Desenvolvido por Beirama para avaliação de segurança da informação | © 2025")