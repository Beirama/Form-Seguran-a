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

# Configurar a localização para formatação adequada de números em português
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Configurar a página
st.set_page_config(
    page_title="Avaliação de Segurança de Dados",
    page_icon="🔒",
    layout="wide",
)

# Função para formatar valores monetários
def format_currency(value):
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

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
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Nível de Segurança<br><span style='font-size:0.8em;color:{color}'>{risk_level}</span>", 'font': {'size': 24}},
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
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
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

# Sidebar para navegação
st.sidebar.title("📊 Avaliação de Segurança")
page = st.sidebar.radio("Selecione uma opção:", ["Teste de Vulnerabilidade", "Calculadora de ROI", "Benchmarking"])

# Página principal
if page == "Teste de Vulnerabilidade":
    st.title("🔒 Teste de Vulnerabilidade")
    st.subheader("Avalie o nível de segurança dos dados da sua empresa")
    
    # Informações da empresa
    company_name = st.text_input("Nome da sua empresa:", "Minha Empresa S.A.")
    
    # Criar as seções do formulário
    st.header("🔍 1. Infraestrutura e Acesso")
    
    infra_q1 = st.radio("Sua empresa utiliza autenticação multifator (MFA) para acessos críticos?", ["Sim", "Não"])
    infra_q2 = st.radio("Os funcionários possuem diferentes níveis de acesso aos dados, de acordo com suas funções?", ["Sim", "Não"])
    infra_q3 = st.radio("Os servidores da sua empresa estão protegidos por firewalls e monitoramento contínuo?", ["Sim", "Não"])
    infra_q4 = st.selectbox("A empresa realiza backup frequente dos dados críticos?", ["Selecione uma opção", "Diariamente", "Semanalmente", "Mensalmente", "Nunca"])
    infra_q5 = st.radio("Os dispositivos utilizados pelos funcionários possuem criptografia de dados ativada?", ["Sim", "Não"])
    
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
    
    policy_q1 = st.radio("Sua empresa possui uma política de segurança da informação formalizada e documentada?", ["Sim", "Não"])
    policy_q2 = st.radio("Os funcionários passam por treinamentos regulares de conscientização sobre segurança da informação?", ["Sim", "Não"])
    policy_q3 = st.radio("Há um plano de resposta a incidentes para lidar com ataques cibernéticos?", ["Sim", "Não"])
    policy_q4 = st.radio("Os fornecedores e terceiros que acessam dados da empresa seguem normas de segurança definidas?", ["Sim", "Não"])
    policy_q5 = st.radio("Existe uma política de atualização frequente para sistemas e softwares críticos?", ["Sim", "Não"])
    
    # Seção de Proteção Contra Ataques
    st.header("🛡️ 3. Proteção Contra Ataques Cibernéticos")
    
    protect_q1 = st.radio("A empresa realiza testes de invasão (pentests) regularmente para avaliar a segurança da rede?", ["Sim", "Não"])
    protect_q2 = st.radio("Existem sistemas ativos de detecção e resposta a ameaças (EDR, SIEM)?", ["Sim", "Não"])
    protect_q3 = st.radio("As senhas utilizadas pelos funcionários seguem boas práticas (mínimo de 12 caracteres, complexas, não reutilizadas)?", ["Sim", "Não"])
    protect_q4 = st.radio("Há um controle ativo para detectar vazamentos de dados da empresa na dark web?", ["Sim", "Não"])
    protect_q5 = st.radio("Existe uma política formal para gerenciamento de dispositivos móveis e trabalho remoto?", ["Sim", "Não"])
    
    # Botão para calcular a pontuação
    if st.button("Calcular Nível de Vulnerabilidade"):
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
        
        # Exibir resultados
        st.header("📊 Resultados da Avaliação")
        
        # Exibir gráfico de velocímetro com Plotly
        st.subheader("Pontuação Geral")
        gauge_chart = create_gauge_chart_plotly(total_percent)
        st.plotly_chart(gauge_chart, use_container_width=True)
        
        # Classificação de risco
        if total_percent <= 40:
            st.error("🚨 RISCO CRÍTICO: A segurança da sua empresa está extremamente vulnerável. Você corre alto risco de sofrer ataques cibernéticos que podem resultar em perda de dados, fraudes e violações de compliance.")
            st.error("Ação recomendada: Implementar imediatamente um plano de segurança robusto.")
        elif total_percent <= 70:
            st.warning("⚠️ RISCO MODERADO: Sua empresa possui algumas medidas de segurança, mas há brechas significativas. Um ataque pode comprometer suas operações e informações sensíveis.")
            st.warning("Ação recomendada: Revisar processos, treinar equipe e reforçar a proteção digital.")
        else:
            st.success("✅ SEGURANÇA ACEITÁVEL: Sua empresa tem uma boa estrutura de segurança, mas ainda pode melhorar. O ideal é refinar processos e testar a resiliência contra ameaças cada vez mais sofisticadas.")
        
        # Exibir pontuação por categoria usando Plotly
        st.subheader("Análise por Categoria")
        category_scores = {
            "Infraestrutura": infra_percent,
            "Políticas": policy_percent,
            "Proteção": protect_percent
        }
        category_chart = create_category_chart_plotly(category_scores)
        st.plotly_chart(category_chart, use_container_width=True)
        
        # Recomendações específicas
        st.subheader("Principais Vulnerabilidades Detectadas")
        
        vulnerabilities = []
        recommendations = []
        
        # Infraestrutura
        if infra_q1 == "Não":
            vulnerabilities.append("Falta de autenticação multifator (MFA)")
            recommendations.append("Implemente MFA para todos os acessos críticos e contas de administrador")
            
        if infra_q2 == "Não":
            vulnerabilities.append("Ausência de controle de acesso baseado em funções")
            recommendations.append("Defina e implemente diferentes níveis de acesso para os funcionários")
            
        if infra_q3 == "Não":
            vulnerabilities.append("Servidores sem proteção adequada de firewall")
            recommendations.append("Instale e configure firewalls e implemente monitoramento contínuo")
            
        if infra_q4 == "Nunca" or infra_q4 == "Selecione uma opção":
            vulnerabilities.append("Ausência de backup de dados críticos")
            recommendations.append("Implemente uma rotina de backup diário e teste regularmente a restauração")
            
        if infra_q5 == "Não":
            vulnerabilities.append("Dispositivos sem criptografia de dados")
            recommendations.append("Ative a criptografia em todos os dispositivos corporativos")
        
        # Políticas
        if policy_q1 == "Não":
            vulnerabilities.append("Ausência de política de segurança formalizada")
            recommendations.append("Desenvolva e documente uma política de segurança da informação")
            
        if policy_q2 == "Não":
            vulnerabilities.append("Falta de treinamento de segurança para funcionários")
            recommendations.append("Implemente treinamentos regulares de conscientização sobre segurança")
            
        if policy_q3 == "Não":
            vulnerabilities.append("Sem plano de resposta a incidentes")
            recommendations.append("Desenvolva um plano de resposta a incidentes de segurança")
            
        if policy_q4 == "Não":
            vulnerabilities.append("Terceiros acessam dados sem seguir normas de segurança")
            recommendations.append("Estabeleça requisitos de segurança para fornecedores e parceiros")
            
        if policy_q5 == "Não":
            vulnerabilities.append("Falta de política de atualização de sistemas")
            recommendations.append("Crie uma política para atualização regular de sistemas e softwares")
        
        # Proteção
        if protect_q1 == "Não":
            vulnerabilities.append("Ausência de testes de invasão regulares")
            recommendations.append("Realize pentests semestralmente para identificar vulnerabilidades")
            
        if protect_q2 == "Não":
            vulnerabilities.append("Sem sistemas de detecção e resposta a ameaças")
            recommendations.append("Implemente soluções EDR/SIEM para monitoramento em tempo real")
            
        if protect_q3 == "Não":
            vulnerabilities.append("Senhas fracas ou reutilizadas")
            recommendations.append("Implemente política de senhas fortes e use gerenciador de senhas")
            
        if protect_q4 == "Não":
            vulnerabilities.append("Sem monitoramento de vazamentos na dark web")
            recommendations.append("Contrate serviço de monitoramento de vazamentos de dados")
            
        if protect_q5 == "Não":
            vulnerabilities.append("Ausência de política para dispositivos móveis e trabalho remoto")
            recommendations.append("Desenvolva política específica para trabalho remoto e BYOD")
        
        # Exibir vulnerabilidades
        if vulnerabilities:
            for i, vuln in enumerate(vulnerabilities):
                st.error(f"• {vuln}")
        else:
            st.success("Não foram detectadas vulnerabilidades críticas.")
        
        # Exibir recomendações
        st.subheader("Recomendações de Melhoria")
        if recommendations:
            for i, rec in enumerate(recommendations):
                st.info(f"✓ {rec}")
        
        # Preparar dados para os relatórios
        results_data = {
            "Pontuação Geral": total_percent,
            "Nível de Risco": "Crítico" if total_percent <= 40 else "Moderado" if total_percent <= 70 else "Bom",
            "Pontuação Infraestrutura": infra_percent,
            "Pontuação Políticas": policy_percent,
            "Pontuação Proteção": protect_percent,
            "Total de Vulnerabilidades": len(vulnerabilities)
        }
        
        # Criar PDF para download
        pdf_data = create_pdf_report(results_data, vulnerabilities, recommendations, company_name)
        
        # Botão para download do relatório PDF
        st.subheader("Relatório Completo")
        st.markdown(get_pdf_download_link(pdf_data, f"relatorio_seguranca_{company_name.replace(' ', '_')}.pdf", "📥 Baixar Relatório Completo em PDF"), unsafe_allow_html=True)
        
        # Call to Action
        st.subheader("Próximos Passos")
        st.info("Para uma análise detalhada e um plano de ação personalizado, consulte um especialista em segurança da informação.")
        
        # Mostrar análise detalhada com Altair (visualização interativa)
        st.subheader("Análise Detalhada por Subcategoria")
        
        # Converter dados para formato adequado para Altair
        detailed_data = pd.DataFrame({
            'Subcategoria': [
                'Autenticação MFA', 'Controle de Acesso', 'Proteção de Servidores',
                'Backup de Dados', 'Criptografia de Dispositivos', 'Política Documentada',
                'Treinamento da Equipe', 'Resposta a Incidentes', 'Normas para Fornecedores',
                'Atualização de Sistemas', 'Testes de Invasão', 'Sistemas de Detecção',
                'Política de Senhas', 'Monitoramento de Vazamentos', 'Gestão de Dispositivos Móveis'
            ],
            'Categoria': [
                'Infraestrutura', 'Infraestrutura', 'Infraestrutura', 'Infraestrutura', 'Infraestrutura',
                'Políticas', 'Políticas', 'Políticas', 'Políticas', 'Políticas',
                'Proteção', 'Proteção', 'Proteção', 'Proteção', 'Proteção'
            ],
            'Status': [
                infra_q1 == "Sim", infra_q2 == "Sim", infra_q3 == "Sim", 
                infra_q4 != "Nunca" and infra_q4 != "Selecione uma opção", infra_q5 == "Sim",
                policy_q1 == "Sim", policy_q2 == "Sim", policy_q3 == "Sim", policy_q4 == "Sim", policy_q5 == "Sim",
                protect_q1 == "Sim", protect_q2 == "Sim", protect_q3 == "Sim", protect_q4 == "Sim", protect_q5 == "Sim"
            ],
            'Valor': [
                100 if infra_q1 == "Sim" else 0,
                100 if infra_q2 == "Sim" else 0,
                100 if infra_q3 == "Sim" else 0,
                backup_score * 100,
                100 if infra_q5 == "Sim" else 0,
                100 if policy_q1 == "Sim" else 0,
                100 if policy_q2 == "Sim" else 0,
                100 if policy_q3 == "Sim" else 0,
                100 if policy_q4 == "Sim" else 0,
                100 if policy_q5 == "Sim" else 0,
                100 if protect_q1 == "Sim" else 0,
                100 if protect_q2 == "Sim" else 0,
                100 if protect_q3 == "Sim" else 0,
                100 if protect_q4 == "Sim" else 0,
                100 if protect_q5 == "Sim" else 0
            ]
        })
        
        # Criar gráfico interativo com Altair
        chart = alt.Chart(detailed_data).mark_bar().encode(
            x=alt.X('Subcategoria:N', sort=None, title='Subcategoria'),
            y=alt.Y('Valor:Q', title='Pontuação (%)'),
            color=alt.condition(
                alt.datum.Status,
                alt.value('green'),
                alt.value('red')
            ),
            tooltip=['Subcategoria', 'Categoria', 'Valor', 'Status']
        ).properties(
            width=700,
            height=400,
            title='Análise Detalhada de Controles de Segurança'
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)

elif page == "Calculadora de ROI":
    st.title("💰 Calculadora de ROI em Segurança da Informação")
    st.subheader("Avalie o retorno sobre investimento em segurança cibernética")
    
    # Informações da empresa
    company_name = st.text_input("Nome da sua empresa:", "Minha Empresa S.A.")
    
    # Custos com Incidentes
    st.header("💰 1. Custos com Incidentes Cibernéticos")
    
    num_incidents = st.number_input("Quantos ataques cibernéticos sua empresa sofreu nos últimos 12 meses?", min_value=0, value=0, step=1)
    cost_per_incident = st.number_input("Qual foi o custo médio de cada incidente? (R$)", min_value=0.0, value=0.0, step=1000.0)
    hours_per_incident = st.number_input("Quanto tempo sua equipe gastou para mitigar cada incidente? (horas)", min_value=0.0, value=0.0, step=1.0)
    hourly_cost = st.number_input("Qual o custo médio por hora dos profissionais envolvidos na mitigação? (R$)", min_value=0.0, value=0.0, step=10.0)
    
    # Dados históricos de incidentes (opcional)
    st.subheader("Histórico de Incidentes (Opcional)")
    show_history = st.checkbox("Adicionar dados históricos de incidentes")
    
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
                st.plotly_chart(trend_chart, use_container_width=True)
            else:
                st.info("Adicione dados de incidentes para visualizar a tendência.")
    
    # Investimentos em Segurança
    st.header("🔐 2. Investimentos em Segurança")
    
    security_investment = st.number_input("Quanto sua empresa investiu em segurança da informação nos últimos 12 meses? (R$)", min_value=0.0, value=0.0, step=1000.0)
    reduced_incidents = st.radio("Esse investimento reduziu a frequência ou o impacto dos ataques?", ["Sim", "Não"])
    
    if reduced_incidents == "Sim":
        new_num_incidents = st.number_input("Número reduzido de ataques por ano após o investimento:", min_value=0, value=0, step=1)
        new_cost_per_incident = st.number_input("Novo custo médio por incidente após o investimento (R$):", min_value=0.0, value=0.0, step=1000.0)
        new_hours_per_incident = st.number_input("Novo tempo de resposta por incidente (horas):", min_value=0.0, value=0.0, step=1.0)
    else:
        new_num_incidents = num_incidents
        new_cost_per_incident = cost_per_incident
        new_hours_per_incident = hours_per_incident
    
    # Impacto nos Negócios
    st.header("📈 3. Impacto nos Negócios")
    
    lost_customers = st.radio("Algum incidente de segurança resultou na perda de clientes?", ["Sim", "Não"])
    
    if lost_customers == "Sim":
        num_lost_customers = st.number_input("Quantos clientes foram perdidos?", min_value=0, value=0, step=1)
        average_ticket = st.number_input("Qual é o ticket médio anual de um cliente para sua empresa? (R$)", min_value=0.0, value=0.0, step=1000.0)
    else:
        num_lost_customers = 0
        average_ticket = 0.0
    
    # Botão para calcular ROI
    if st.button("Calcular ROI"):
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
        
        # Exibir resultados
        st.header("📊 Resultados da Análise de ROI")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Custos Antes do Investimento")
            st.info(f"Número de incidentes: {num_incidents}")
            st.info(f"Custo médio por incidente: {format_currency(cost_per_incident)}")
            st.info(f"Tempo médio de resolução: {format_hours(hours_per_incident)}")
            st.info(f"Custo total com incidentes: {format_currency(total_cost_before)}")
        
        with col2:
            st.subheader("Custos Após o Investimento")
            st.info(f"Investimento em segurança: {format_currency(security_investment)}")
            st.info(f"Número reduzido de incidentes: {new_num_incidents}")
            st.info(f"Novo custo médio por incidente: {format_currency(new_cost_per_incident)}")
            st.info(f"Custo total reduzido: {format_currency(total_cost_after)}")
        
        # Exibir gráfico de ROI com Plotly
        st.subheader("Análise de ROI")
        roi_chart = create_roi_chart_plotly(security_investment, total_cost_before, total_cost_after)
        st.plotly_chart(roi_chart, use_container_width=True)
        
        # Resumo financeiro
        st.subheader("Resumo Financeiro")
        st.success(f"Economia direta obtida: {format_currency(savings)}")
        
        if roi >= 0:
            st.success(f"ROI do investimento em segurança: {format_percent(roi)}")
        else:
            st.error(f"ROI do investimento em segurança: {format_percent(roi)}")
            
        if lost_customers == "Sim" and num_lost_customers > 0:
            st.error(f"Perda de receita devido a clientes perdidos: {format_currency(revenue_loss)}")
            st.info(f"Impacto financeiro total (economia - perda de clientes): {format_currency(savings - revenue_loss)}")
        
        # Adicionar visualização avançada: divisão detalhada dos custos
        st.subheader("Análise Detalhada de Custos")
        
        # Preparar dados para gráfico de pizza
        cost_breakdown_before = {
            "Custos diretos com incidentes": num_incidents * cost_per_incident,
            "Custos com horas de trabalho": num_incidents * hours_per_incident * hourly_cost
        }
        
        cost_breakdown_after = {
            "Custos diretos com incidentes": new_num_incidents * new_cost_per_incident,
            "Custos com horas de trabalho": new_num_incidents * new_hours_per_incident * hourly_cost
        }
        
        # Criar subplots para os gráficos de pizza
        fig = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]],
                           subplot_titles=("Custos Antes do Investimento", "Custos Após o Investimento"))
        
        # Gráfico de pizza para antes
        fig.add_trace(
            go.Pie(
                labels=list(cost_breakdown_before.keys()),
                values=list(cost_breakdown_before.values()),
                textinfo='percent+label',
                marker=dict(colors=['#FF6B6B', '#4ECDC4']),
                name="Antes"
            ),
            row=1, col=1
        )
        
        # Gráfico de pizza para depois
        fig.add_trace(
            go.Pie(
                labels=list(cost_breakdown_after.keys()),
                values=list(cost_breakdown_after.values()),
                textinfo='percent+label',
                marker=dict(colors=['#FF6B6B', '#4ECDC4']),
                name="Depois"
            ),
            row=1, col=2
        )
        
        # Atualizar layout
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Conclusão
        st.subheader("Conclusão")
        
        if roi > 100:
            st.success(f"O investimento de {format_currency(security_investment)} em segurança gerou um excelente retorno de {format_percent(roi)}, economizando {format_currency(savings)} para a empresa.")
        elif roi > 0:
            st.success(f"O investimento de {format_currency(security_investment)} em segurança gerou um retorno positivo de {format_percent(roi)}, economizando {format_currency(savings)} para a empresa.")
        else:
            st.warning(f"O investimento de {format_currency(security_investment)} em segurança ainda não gerou retorno financeiro positivo ({format_percent(roi)}). Considere avaliar a eficácia das medidas implementadas.")
        
        # Recomendações
        st.subheader("Recomendações Estratégicas")
        
        if roi < 0:
            st.info("• Reavalie as medidas de segurança implementadas para garantir maior eficácia.")
            st.info("• Considere investir em soluções com melhor custo-benefício.")
            st.info("• Concentre os recursos em proteger os ativos mais críticos primeiro.")
        elif roi < 50:
            st.info("• Continue investindo em segurança, focando em áreas de maior risco.")
            st.info("• Implemente treinamentos de conscientização para reduzir incidentes causados por erro humano.")
            st.info("• Considere automatizar processos de segurança para reduzir custos operacionais.")
        else:
            st.info("• Mantenha o investimento em segurança e considere expandi-lo para outras áreas.")
            st.info("• Compartilhe métricas de sucesso com a liderança para garantir continuidade do orçamento.")
            st.info("• Implemente um programa de melhoria contínua para manter os resultados positivos.")
        
        # Criar PDF para download
        roi_results = {
            "Investimento": security_investment,
            "Economia": savings,
            "ROI": roi,
            "Perda de Clientes": revenue_loss,
            "Impacto Total": savings - revenue_loss
        }
        
        # Criar PDF para download
        pdf_data = create_pdf_report(roi_results, [], [], company_name)
        
        # Botão para download do relatório PDF
        st.subheader("Relatório Completo")
        st.markdown(get_pdf_download_link(pdf_data, f"relatorio_roi_seguranca_{company_name.replace(' ', '_')}.pdf", "📥 Baixar Relatório Completo em PDF"), unsafe_allow_html=True)
        
        # Call to Action
        st.subheader("Próximos Passos")
        st.info("Para uma análise detalhada e estratégia de investimento em segurança personalizada, consulte um especialista em segurança da informação.")

elif page == "Benchmarking":
    st.title("🌐 Benchmarking de Segurança")
    st.subheader("Compare o nível de segurança da sua empresa com a média do seu setor")
    
    # Informações da empresa
    company_name = st.text_input("Nome da sua empresa:", "Minha Empresa S.A.")
    industry = st.selectbox("Setor de atuação:", ["Tecnologia", "Finanças", "Saúde", "Varejo", "Educação", "Manufatura", "Serviços"])
    
    # Resultados da avaliação de segurança
    st.header("📊 Resultados da sua Avaliação de Segurança")
    st.info("Insira abaixo os resultados obtidos na aba 'Teste de Vulnerabilidade'")
    
    infra_score = st.slider("Pontuação em Infraestrutura (%):", 0, 100, 50)
    policy_score = st.slider("Pontuação em Políticas (%):", 0, 100, 50)
    protect_score = st.slider("Pontuação em Proteção (%):", 0, 100, 50)
    
    # Calcular pontuação total
    total_score = (infra_score + policy_score + protect_score) / 3
    
    # Obter dados de benchmark
    benchmark_data = get_benchmark_data()
    
    # Botão para comparar
    if st.button("Comparar com o Setor"):
        st.header("📈 Análise Comparativa")
        
        # Criar dados para comparação
        company_scores = {
            "Infraestrutura": infra_score,
            "Políticas": policy_score,
            "Proteção": protect_score,
            "Total": total_score
        }
        
        # Visualização da pontuação geral
        st.subheader("Pontuação Geral vs. Média do Setor")
        
        # Criar DataFrame para comparação
        comparison_df = pd.DataFrame({
            'Entidade': ['Sua Empresa', f'Média do Setor: {industry}'],
            'Pontuação': [total_score, benchmark_data[industry]['Total']]
        })
        
        # Criar gráfico de barras para comparação geral
        fig_general = px.bar(
            comparison_df, 
            x='Entidade', 
            y='Pontuação',
            color='Entidade',
            text_auto='.1f',
            title=f"Comparação da Pontuação Geral - {company_name} vs. Média do Setor: {industry}",
            color_discrete_map={'Sua Empresa': 'blue', f'Média do Setor: {industry}': 'green'}
        )
        
        fig_general.update_layout(
            yaxis_title="Pontuação (%)",
            yaxis=dict(range=[0, 100]),
            height=400
        )
        
        st.plotly_chart(fig_general, use_container_width=True)
        
        # Análise por categoria com gráfico de radar
        st.subheader("Análise Detalhada por Categoria")
        radar_chart = create_radar_chart(company_scores, benchmark_data, industry)
        st.plotly_chart(radar_chart, use_container_width=True)
        
        # Diferenças por categoria
        st.subheader("Diferenças por Categoria")
        
        # Criar DataFrame para diferenças
        diff_data = []
        for category in ['Infraestrutura', 'Políticas', 'Proteção', 'Total']:
            company_value = company_scores[category]
            benchmark_value = benchmark_data[industry][category]
            diff = company_value - benchmark_value
            
            diff_data.append({
                'Categoria': category,
                'Sua Empresa': company_value,
                f'Média do Setor: {industry}': benchmark_value,
                'Diferença': diff,
                'Status': 'Acima da Média' if diff >= 0 else 'Abaixo da Média'
            })
        
        diff_df = pd.DataFrame(diff_data)
        
        # Criar gráfico para diferenças
        fig_diff = go.Figure()
        
        # Adicionar barras para empresa
        fig_diff.add_trace(go.Bar(
            x=diff_df['Categoria'],
            y=diff_df['Sua Empresa'],
            name='Sua Empresa',
            marker_color='blue'
        ))
        
        # Adicionar barras para benchmark
        fig_diff.add_trace(go.Bar(
            x=diff_df['Categoria'],
            y=diff_df[f'Média do Setor: {industry}'],
            name=f'Média do Setor: {industry}',
            marker_color='green'
        ))
        
        # Atualizar layout
        fig_diff.update_layout(
            title='Comparativo Detalhado por Categoria',
            yaxis_title='Pontuação (%)',
            yaxis=dict(range=[0, 100]),
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig_diff, use_container_width=True)
        
        # Tabela de comparação
        st.subheader("Tabela Comparativa")
        
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
            'Pontuação': total_score
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
        
        st.plotly_chart(fig_all, use_container_width=True)
        
        # Recomendações baseadas nas diferenças
        st.subheader("Análise e Recomendações")
        
        overall_status = "acima" if total_score >= benchmark_data[industry]["Total"] else "abaixo"
        st.write(f"Sua empresa está **{overall_status}** da média do setor **{industry}**, com uma pontuação geral de **{total_score:.1f}%** comparada à média de **{benchmark_data[industry]['Total']}%**.")
        
        # Identificar pontos fortes e fracos
        strengths = []
        weaknesses = []
        
        for category in ['Infraestrutura', 'Políticas', 'Proteção']:
            diff = company_scores[category] - benchmark_data[industry][category]
            if diff >= 5:
                strengths.append(category)
            elif diff <= -5:
                weaknesses.append(category)
        
        # Exibir pontos fortes
        if strengths:
            st.success("#### 💪 Pontos Fortes")
            for strength in strengths:
                st.success(f"• {strength}: Sua empresa está **{company_scores[strength] - benchmark_data[industry][strength]:+.1f}%** acima da média do setor.")
        
        # Exibir pontos fracos
        if weaknesses:
            st.error("#### ⚠️ Áreas para Melhoria")
            for weakness in weaknesses:
                st.error(f"• {weakness}: Sua empresa está **{company_scores[weakness] - benchmark_data[industry][weakness]:+.1f}%** abaixo da média do setor.")
                
                # Recomendações específicas
                if weakness == "Infraestrutura":
                    st.info("**Recomendações**: Implemente autenticação multifator, reforce a proteção de servidores e estabeleça política de backup regular.")
                elif weakness == "Políticas":
                    st.info("**Recomendações**: Desenvolva política formal de segurança, realize treinamentos regulares e crie planos de resposta a incidentes.")
                elif weakness == "Proteção":
                    st.info("**Recomendações**: Implemente sistemas de detecção e resposta a ameaças, realize testes de invasão regularmente e reforce políticas de senhas.")
        
        # Se não houver pontos fracos significativos
        if not weaknesses:
            st.success("Parabéns! Sua empresa está em boa posição em relação à média do setor. Continue mantendo altos padrões de segurança e busque melhorias contínuas.")
        
        # Criar PDF para download
        benchmark_results = {
            "Pontuação Geral": total_score,
            "Média do Setor": benchmark_data[industry]["Total"],
            "Diferença": total_score - benchmark_data[industry]["Total"],
            "Pontuação Infraestrutura": infra_score,
            "Pontuação Políticas": policy_score,
            "Pontuação Proteção": protect_score,
            "Nível de Risco": "Acima da Média" if total_score >= benchmark_data[industry]["Total"] else "Abaixo da Média"
        }
        
        # Criar recomendações para o PDF
        benchmark_recommendations = []
        if weaknesses:
            for weakness in weaknesses:
                if weakness == "Infraestrutura":
                    benchmark_recommendations.append("Implemente autenticação multifator, reforce a proteção de servidores e estabeleça política de backup regular.")
                elif weakness == "Políticas":
                    benchmark_recommendations.append("Desenvolva política formal de segurança, realize treinamentos regulares e crie planos de resposta a incidentes.")
                elif weakness == "Proteção":
                    benchmark_recommendations.append("Implemente sistemas de detecção e resposta a ameaças, realize testes de invasão regularmente e reforce políticas de senhas.")
        else:
            benchmark_recommendations.append("Continue mantendo altos padrões de segurança e busque melhorias contínuas.")
        
        # Criar PDF para download
        pdf_data = create_pdf_report(benchmark_results, [], benchmark_recommendations, company_name)
        
        # Botão para download do relatório PDF
        st.subheader("Relatório de Benchmarking")
        st.markdown(get_pdf_download_link(pdf_data, f"relatorio_benchmarking_{company_name.replace(' ', '_')}.pdf", "📥 Baixar Relatório de Benchmarking em PDF"), unsafe_allow_html=True)

# Rodapé
st.markdown("---")
st.markdown("Desenvolvido por Beirama para avaliação de segurança da informação | © 2025")