import streamlit as st
import pandas as pd
from datetime import date
import os
from fpdf import FPDF # Importando a biblioteca de PDF
#python -m streamlit run app.py
# 1. Configuração da Página
st.set_page_config(page_title="Sistema de Antecipação", page_icon="🏦", layout="wide")

# --- FUNÇÕES DE BANCO DE DADOS ---
DB_FILE = "historico_antecipacoes.csv"

def salvar_no_historico(cliente, total_bruto, total_liquido, total_juros):
    novo_dado = {
        "Data Operação": date.today().strftime("%d/%m/%Y"),
        "Cliente": cliente,
        "Total Bruto": f"{total_bruto:.2f}",
        "Total Juros": f"{total_juros:.2f}",
        "Total Líquido": f"{total_liquido:.2f}"
    }
    df_novo = pd.DataFrame([novo_dado])
    
    if not os.path.isfile(DB_FILE):
        df_novo.to_csv(DB_FILE, index=False, sep=";", mode='w', header=True)
    else:
        df_novo.to_csv(DB_FILE, index=False, sep=";", mode='a', header=False)

# --- FUNÇÃO GERADORA DE PDF ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            # x, y, w (ajuste conforme o tamanho da sua logo)
            self.image("logo.png", 10, 8, 33) 
        self.set_font('Arial', 'B', 15)
        self.cell(80) # Move para a direita
        self.cell(30, 10, 'Relatório de Antecipação', 0, 0, 'C')
        self.ln(20) # Quebra de linha

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_pdf(cliente, df_dados, t_bruto, t_juros, t_liq):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Cabeçalho do Cliente
    pdf.set_fill_color(200, 220, 255) # Cor de fundo azul claro
    pdf.cell(0, 10, txt=f"Cliente: {cliente}", ln=True, align='L', fill=True)
    pdf.cell(0, 10, txt=f"Data da Operação: {date.today().strftime('%d/%m/%Y')}", ln=True, align='L')
    pdf.ln(10)
    
    # Cabeçalho da Tabela
    pdf.set_font("Arial", 'B', 10)
    col_widths = [40, 40, 20, 40, 40] # Largura das colunas
    headers = ["Valor Original", "Vencimento", "Dias", "Desconto", "Líquido"]
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 10, h, 1, 0, 'C')
    pdf.ln()
    
    # Dados da Tabela
    pdf.set_font("Arial", size=10)
    for index, row in df_dados.iterrows():
        pdf.cell(col_widths[0], 10, f"R$ {row['Valor Original']:,.2f}", 1, 0, 'R')
        pdf.cell(col_widths[1], 10, f"{row['Vencimento']}", 1, 0, 'C')
        pdf.cell(col_widths[2], 10, f"{row['Dias']}", 1, 0, 'C')
        pdf.cell(col_widths[3], 10, f"R$ {row['Juros']:,.2f}", 1, 0, 'R')
        pdf.cell(col_widths[4], 10, f"R$ {row['Líquido']:,.2f}", 1, 0, 'R')
        pdf.ln()
        
    pdf.ln(10)
    
    # Totais
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Total Bruto: R$ {t_bruto:,.2f}", ln=True)
    pdf.set_text_color(200, 0, 0) # Vermelho
    pdf.cell(0, 10, f"Total Descontos: - R$ {t_juros:,.2f}", ln=True)
    pdf.set_text_color(0, 100, 0) # Verde
    pdf.cell(0, 10, f"Valor Líquido a Pagar: R$ {t_liq:,.2f}", ln=True)
    
    # Retorna o PDF como string binária
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=200)
st.sidebar.divider()
st.sidebar.info(f"📅 Hoje: {date.today().strftime('%d/%m/%Y')}")

aba1, aba2 = st.tabs(["📊 Nova Operação", "🔍 Consultar Histórico"])

with aba1:
    st.title("Nova Antecipação (Juros Simples)")
    
    col_cli, col_tax = st.columns([2, 1])
    with col_cli:
        nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
    with col_tax:
        taxa_mensal = st.selectbox("Taxa Mensal (%)", [2.0, 2.5, 2.8, 3.0, 3.5, 4.0, 5.0], index=3)
        # MUDANÇA 1: Taxa Diária Simples (Linear)
        taxa_diaria = (taxa_mensal / 100) / 30

    if 'cheques' not in st.session_state:
        st.session_state['cheques'] = []

    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        val = c1.number_input("Valor (R$)", min_value=0.0, step=100.0)
        venc = c2.date_input("Vencimento", date.today())
        
        if c3.button("➕ Adicionar", use_container_width=True):
            dias = (venc - date.today()).days
            if dias >= 0 and val > 0:
                # MUDANÇA 2: Cálculo de Desconto Simples
                desconto = val * (taxa_diaria * dias)
                v_liq = val - desconto
                
                st.session_state['cheques'].append({
                    "Cliente": nome_cliente,
                    "Valor Original": val,
                    "Vencimento": venc.strftime("%d/%m/%Y"),
                    "Dias": dias,
                    "Juros": desconto,
                    "Líquido": v_liq
                })
                st.rerun()
            else:
                st.error("Dados inválidos!")

    if st.session_state['cheques']:
        st.divider()
        df = pd.DataFrame(st.session_state['cheques'])
        
        # Exibição na Tela
        df_show = df.copy()
        for col in ["Valor Original", "Juros", "Líquido"]:
            df_show[col] = df_show[col].map("R$ {:,.2f}".format)
        st.table(df_show.drop(columns=["Cliente"]))
        
        # Totais\Users\User\Documents\CalcFinanc2\Users\User\Documents\CalcFinanc2
        t_bruto = df["Valor Original"].sum()
        t_juros = df["Juros"].sum()
        t_liq = df["Líquido"].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Bruto", f"R$ {t_bruto:,.2f}")
        m2.metric("Juros", f"- R$ {t_juros:,.2f}")
        m3.metric("Líquido", f"R$ {t_liq:,.2f}")
        
        st.divider()
        c_pdf, c_save = st.columns(2)
        
        # --- BOTÃO DE PDF ---
        with c_pdf:
            if nome_cliente:
                # Gera o PDF em memória
                pdf_bytes = gerar_pdf(nome_cliente, df, t_bruto, t_juros, t_liq)
                st.download_button(
                    label="📄 Baixar PDF do Relatório",
                    data=pdf_bytes,
                    file_name=f"Relatorio_{nome_cliente}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("Preencha o nome do cliente para liberar o PDF.")

        # --- BOTÃO DE SALVAR ---
        with c_save:
            if st.button("💾 Finalizar e Arquivar", type="primary", use_container_width=True):
                if nome_cliente:
                    salvar_no_historico(nome_cliente, t_bruto, t_liq, t_juros)
                    st.session_state['cheques'] = []
                    st.success("Salvo!")
                    st.rerun()
                else:
                    st.warning("Preencha o nome!")

with aba2:
    st.title("Histórico")
    if os.path.exists(DB_FILE):
        hist_df = pd.read_csv(DB_FILE, sep=";")
        busca = st.text_input("Buscar Cliente")
        check_data = st.checkbox("Filtrar Data")
        data_busca = st.date_input("Data", date.today())
        
        if busca:
            hist_df = hist_df[hist_df['Cliente'].str.contains(busca, case=False, na=False)]
        if check_data:
            hist_df = hist_df[hist_df['Data Operação'] == data_busca.strftime("%d/%m/%Y")]
            
        st.dataframe(hist_df.iloc[::-1], use_container_width=True)
    else:
        st.info("Sem histórico ainda.")