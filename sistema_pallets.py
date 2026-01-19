import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date, timedelta
import string
import os

# --- TENTA IMPORTAR A CONEXÃO DO GOOGLE ---
try:
    from streamlit_gsheets import GSheetsConnection
    GSHEETS_DISPONIVEL = True
except ModuleNotFoundError:
    GSHEETS_DISPONIVEL = False

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Logística Master A-Z - Google Sheets")

if not GSHEETS_DISPONIVEL:
    st.error("⚠️ Biblioteca 'st-gsheets-connection' não encontrada. Verifique se ela está no seu requirements.txt no GitHub.")
    st.stop()

# --- CONEXÃO GOOGLE SHEETS ---
# Certifique-se de que a URL está nas 'Secrets' do Streamlit
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.warning("⚠️ Erro na conexão com Google Sheets. Verifique as 'Secrets' no painel do Streamlit.")
    st.stop()

# --- PERSISTÊNCIA DE DADOS ---
def salvar_dados():
    # Envia os dados para a planilha
    conn.update(worksheet="Estoque", data=st.session_state.estoque)
    
    df_cfg = pd.DataFrame(list(st.session_state.config_ruas.items()), columns=['Rua', 'Capacidade'])
    conn.update(worksheet="Config_Ruas", data=df_cfg)
    
    df_global = pd.DataFrame([{"cap_galpao": st.session_state.cap_total_galpao, "cap_padrao": st.session_state.capacidade_padrao}])
    conn.update(worksheet="Config_Global", data=df_global)

def carregar_dados():
    try:
        df_estoque = conn.read(worksheet="Estoque")
        if df_estoque is not None and not df_estoque.empty:
            df_estoque['Lote'] = df_estoque['Lote'].fillna("")
            df_estoque['Cliente'] = df_estoque['Cliente'].fillna("")
            # Converte validade para data de forma segura
            df_estoque['Validade'] = pd.to_datetime(df_estoque['Validade']).dt.date
            st.session_state.estoque = df_estoque
            
        df_cfg = conn.read(worksheet="Config_Ruas")
        if df_cfg is not None and not df_cfg.empty:
            st.session_state.config_ruas = dict(zip(df_cfg.Rua, df_cfg.Capacidade))
            
        df_g = conn.read(worksheet="Config_Global")
        if df_g is not None and not df_g.empty:
            st.session_state.cap_total_galpao = int(df_g.iloc[0]['cap_galpao'])
            st.session_state.capacidade_padrao = int(df_g.iloc[0]['cap_padrao'])
    except:
        st.info("ℹ️ Planilha nova detectada. Começando com dados vazios.")

# (Restante do código de inicialização de ruas, dashboard e mapa permanece igual)
