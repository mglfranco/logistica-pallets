import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import string
import os

# --- TENTA IMPORTAR A CONEXÃO ---
try:
    from streamlit_gsheets import GSheetsConnection
    GSHEETS_DISPONIVEL = True
except ImportError:
    GSHEETS_DISPONIVEL = False

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Logística Pro - Google Sheets", page_icon="🚜")

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_dados():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Salva o estoque
        conn.update(worksheet="Estoque", data=st.session_state.estoque)
        
        # Salva Configurações das Ruas
        df_cfg = pd.DataFrame([{'Rua': k, 'Capacidade': v} for k, v in st.session_state.config_ruas.items()])
        conn.update(worksheet="Config_Ruas", data=df_cfg)
        
        # Salva Config Global
        df_g = pd.DataFrame([{"cap_galpao": st.session_state.cap_total_galpao, "cap_padrao": st.session_state.capacidade_padrao}])
        conn.update(worksheet="Config_Global", data=df_g)
    except Exception as e:
        st.error(f"Erro ao salvar na nuvem: {e}")

def carregar_dados():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_e = conn.read(worksheet="Estoque")
        if df_e is not None and not df_e.empty:
            df_e['Validade'] = pd.to_datetime(df_e['Validade']).dt.date
            st.session_state.estoque = df_e
            
        df_c = conn.read(worksheet="Config_Ruas")
        if df_c is not None and not df_c.empty:
            st.session_state.config_ruas = dict(zip(df_c.Rua, df_c.Capacidade))
            
        df_g = conn.read(worksheet="Config_Global")
        if df_g is not None and not df_g.empty:
            st.session_state.cap_total_galpao = int(df_g.iloc[0]['cap_galpao'])
            st.session_state.capacidade_padrao = int(df_g.iloc[0]['cap_padrao'])
    except:
        # Se falhar, mantém o que está na memória para não dar tela preta
        pass

# --- INICIALIZAÇÃO SEGURA ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = pd.DataFrame()
    st.session_state.config_ruas = {}
    st.session_state.capacidade_padrao = 41
    st.session_state.cap_total_galpao = 2000
    if GSHEETS_DISPONIVEL:
        carregar_dados()

def inicializar_rua(nome_rua, capacidade):
    dados = []
    posicoes_uteis = []
    for f in range(1, 15):
        limite_h = 2 if f == 1 else 3
        for n in range(3, 0, -1):
            if n <= limite_h: posicoes_uteis.append((f, n))
    
    for f in range(1, 15):
        for n in range(1, 4):
            id_p = f"{posicoes_uteis.index((f, n)) + 1:02d}" if (f, n) in posicoes_uteis[:capacidade] else "--"
            status = "Vazio" if id_p != "--" else "BLOQUEADO"
            dados.append({
                "Rua": nome_rua, "Fileira": f, "Nivel": n, "ID": id_p,
                "Lote": "", "Validade": None, "Status": status, "Cliente": "", "Data_Entrada": None
            })
    df_nova = pd.DataFrame(dados)
    if st.session_state.estoque.empty:
        st.session_state.estoque = df_nova
    else:
        st.session_state.estoque = pd.concat([st.session_state.estoque[st.session_state.estoque['Rua'] != nome_rua], df_nova])
    st.session_state.config_ruas[nome_rua] = capacidade
    salvar_dados()

# --- INTERFACE ---
st.title("🚜 Gestão Logística")

if not GSHEETS_DISPONIVEL:
    st.warning("⚠️ Instale 'st-gsheets-connection' no requirements.txt")

with st.sidebar:
    st.header("⚙️ Configurações")
    st.session_state.cap_total_galpao = st.number_input("Capacidade Galpão", 1, 50000, st.session_state.cap_total_galpao)
    ruas = [f"Rua {l}{n}" for l in string.ascii_uppercase for n in [1, 2]]
    rua_sel = st.selectbox("Selecionar Rua", ruas)
    
    if rua_sel not in st.session_state.config_ruas:
        inicializar_rua(rua_sel, 41)
    
    if st.button("🔄 Sincronizar Nuvem"):
        salvar_dados()
        st.rerun()

# --- MAPA E OPERAÇÕES (RESUMIDO PARA FUNCIONAR) ---
# Aqui você continua com as TABS e o MAPA que já tínhamos.
st.info(f"Rua Selecionada: {rua_sel} | Clique em Sincronizar se os dados não aparecerem.")

# ... (Mantenha aqui seu código de Mapa e Tabs de Entrada/Saída)
