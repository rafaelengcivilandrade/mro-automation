import streamlit as st
import pandas as pd
from datetime import datetime
import erp_connector
import whatsapp_notifier
import os

st.set_page_config(page_title="MRO Processor", page_icon="🏭", layout="wide")

@st.cache_resource
def get_erp(erp_escolhido):
    if erp_escolhido == "Mock (Teste)":
        return erp_connector.MockERPConnector()
    elif erp_escolhido == "SAP":
        return erp_connector.SAPConnector()
    elif erp_escolhido == "TOTVS":
        return erp_connector.TOTVSConnector()
    return erp_connector.MockERPConnector()

@st.cache_resource
def get_whatsapp(usar_real):
    if usar_real:
        return whatsapp_notifier.TwilioWhatsAppNotifier()
    return whatsapp_notifier.MockWhatsAppNotifier()

st.title("🏭 Sistema de Integração MRO & WhatsApp")
st.markdown("Faça upload da planilha de itens de manutenção para cadastro automático no ERP.")

with st.sidebar:
    st.header("⚙️ Configurações")
    erp_escolhido = st.selectbox("Selecione o ERP", ["Mock (Teste)", "SAP", "TOTVS"])
    whatsapp_numero = st.text_input("Nº WhatsApp (ex: 5511999999999)", value="5511999999999")
    usar_wp_real = st.checkbox("Usar WhatsApp Real (Twilio)?", value=False)
    st.markdown("---")
    st.caption("Servidor GCP Ativo")

MAPEAMENTO_PADRAO = {
    'part number': 'Part Number', 'partnumber': 'Part Number', 'pn': 'Part Number',
    'descrição': 'Description', 'descricao': 'Description', 'description': 'Description', 'desc': 'Description',
    'fabricante': 'Manufacturer', 'manufacturer': 'Manufacturer', 'mfr': 'Manufacturer',
    'quantidade': 'Qty', 'qty': 'Qty', 'quantity': 'Qty', 'qtd': 'Qty',
    'preço': 'Price', 'preco': 'Price', 'price': 'Price', 'valor': 'Price'
}

def processar_planilha(df_raw):
    df_raw.columns = [str(col).strip().lower() for col in df_raw.columns]
    df_raw = df_raw.rename(columns=MAPEAMENTO_PADRAO)
    colunas_necessarias = ['Part Number', 'Description', 'Manufacturer', 'Qty', 'Price']
    df_processado = pd.DataFrame()
    for col in colunas_necessarias:
        df_processado[col] = df_raw[col] if col in df_raw.columns else None
    return df_processado

uploaded_file = st.file_uploader("Escolha a planilha Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df_bruto = pd.read_excel(uploaded_file)
        df_mro = processar_planilha(df_bruto)
        
        st.subheader("📋 Dados Extraídos da Planilha")
        st.dataframe(df_mro, use_container_width=True)
        
        if st.button("🚀 Processar e Cadastrar no ERP", type="primary", use_container_width=True):
            erp = get_erp(erp_escolhido)
            wp = get_whatsapp(usar_wp_real)
            
            resultados = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_linhas = len(df_mro)
            sucessos = 0
            falhas = 0
            
            for index, row in df_mro.iterrows():
                status_text.text(f"Processando Item {index + 1} de {total_linhas}...")
                progress_bar.progress((index + 1) / total_linhas)
                
                item_dict = row.to_dict()
                retorno_erp = erp.cadastrar_item_mro(item_dict)
                
                resultados.append({
                    "Part Number": item_dict.get('Part Number'),
                    "Descrição": item_dict.get('Description'),
                    "Status": "✅ Sucesso" if retorno_erp["sucesso"] else "❌ Falha",
                    "Código ERP": retorno_erp.get("codigo_erp", ""),
                    "Mensagem": retorno_erp["mensagem"]
                })
                
                if retorno_erp["sucesso"]: sucessos += 1
                else: falhas += 1
            
            progress_bar.progress(1.0)
            status_text.text("Processamento concluído!")
            
            df_resultado = pd.DataFrame(resultados)
            
            st.subheader("📊 Relatório de Processamento")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Processado", total_linhas)
            col2.metric("Sucessos", sucessos)
            col3.metric("Falhas", falhas)
            
            st.dataframe(df_resultado, use_container_width=True)
            
            csv = df_resultado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Relatório (CSV)",
                data=csv,
                file_name=f'relatorio_mro_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv'
            )
            
            st.subheader("📱 Notificação WhatsApp")
            msg_wp = f"*🚀 Relatório MRO Automático*\n\n*Data:* {datetime.now().strftime('%d/%m/%Y %H:%M')}\n*ERP:* {erp_escolhido}\n\n*Resultados:*\n- Total: {total_linhas}\n- ✅ Sucesso: {sucessos}\n- ❌ Falhas: {falhas}\n\n_Aguardando correções._"
            
            if st.button("Enviar Resumo via WhatsApp", use_container_width=True):
                with st.spinner("Enviando mensagem..."):
                    envio_ok = wp.enviar_relatorio(whatsapp_numero, msg_wp)
                    if envio_ok:
                        st.success("Mensagem enviada com sucesso!")
                    else:
                        st.error("Falha ao enviar mensagem.")
                        
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
