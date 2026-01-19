import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date, timedelta
import string
import os
from streamlit_gsheets import GSheetsConnection # IMPORTAÇÃO QUE FALTAVA

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Logística Master A-Z - Google Sheets")

# --- CONEXÃO GOOGLE SHEETS ---
# Certifique-se de configurar a URL nas 'Secrets' do Streamlit Cloud como:
# [connections.gsheets]
# spreadsheet = "SUA_URL_DA_PLANILHA"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- PERSISTÊNCIA DE DADOS (AGORA VIA GOOGLE SHEETS) ---
def salvar_dados():
    # Salva o estoque na aba "Estoque" da sua planilha
    conn.update(worksheet="Estoque", data=st.session_state.estoque)
    # Salva as configurações em abas separadas para não perder nada
    df_cfg = pd.DataFrame(list(st.session_state.config_ruas.items()), columns=['Rua', 'Capacidade'])
    conn.update(worksheet="Config_Ruas", data=df_cfg)
    
    df_global = pd.DataFrame([{"cap_galpao": st.session_state.cap_total_galpao, "cap_padrao": st.session_state.capacidade_padrao}])
    conn.update(worksheet="Config_Global", data=df_global)

def carregar_dados():
    try:
        # Tenta carregar os dados das abas do Google Sheets
        df_estoque = conn.read(worksheet="Estoque")
        if not df_estoque.empty:
            df_estoque['Lote'] = df_estoque['Lote'].fillna("")
            df_estoque['Cliente'] = df_estoque['Cliente'].fillna("")
            df_estoque['Validade'] = pd.to_datetime(df_estoque['Validade']).dt.date
            st.session_state.estoque = df_estoque
            
        df_cfg = conn.read(worksheet="Config_Ruas")
        if not df_cfg.empty:
            st.session_state.config_ruas = dict(zip(df_cfg.Rua, df_cfg.Capacidade))
            
        df_g = conn.read(worksheet="Config_Global")
        if not df_g.empty:
            st.session_state.cap_total_galpao = int(df_g.iloc[0]['cap_galpao'])
            st.session_state.capacidade_padrao = int(df_g.iloc[0]['cap_padrao'])
    except Exception as e:
        st.error(f"Aguardando configuração ou planilha vazia: {e}")

# --- INICIALIZAÇÃO ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = pd.DataFrame()
    st.session_state.config_ruas = {}
    st.session_state.capacidade_padrao = 41
    st.session_state.cap_total_galpao = 2000
    carregar_dados()

def inicializar_rua(nome_rua, capacidade):
    dados = []
    posicoes_uteis = []
    for f in range(1, 15):
        limite_altura = 2 if f == 1 else 3
        for n in range(3, 0, -1):
            if n <= limite_altura:
                posicoes_uteis.append((f, n))
    
    for f in range(1, 15):
        for n in range(1, 4):
            pallet_id = "--"
            status = "Vazio"
            if (f, n) in posicoes_uteis[:capacidade]:
                idx_num = posicoes_uteis.index((f, n)) + 1
                pallet_id = f"{idx_num:02d}"
            else:
                status = "BLOQUEADO"
            
            dados.append({
                "Rua": nome_rua, "Fileira": f, "Nivel": n,
                "ID": pallet_id, "Lote": "", "Validade": None, 
                "Status": status, "Cliente": "", "Data_Entrada": None
            })
    
    novo_df = pd.DataFrame(dados)
    if st.session_state.estoque.empty:
        st.session_state.estoque = novo_df
    else:
        st.session_state.estoque = pd.concat([st.session_state.estoque[st.session_state.estoque['Rua'] != nome_rua], novo_df])
    st.session_state.config_ruas[nome_rua] = capacidade
    salvar_dados()

lista_ruas_opcoes = []
for letra in string.ascii_uppercase:
    lista_ruas_opcoes.extend([f"Rua {letra}1", f"Rua {letra}2"])

# --- INTERFACE ---
st.title("🚜 Gestão Logística - Google Sheets FEFO 🚜")

with st.sidebar:
    st.header("⚙️ Configurações")
    st.session_state.cap_total_galpao = st.number_input("Capacidade Galpão", 1, 100000, st.session_state.cap_total_galpao)
    st.session_state.capacidade_padrao = st.number_input("Padrão p/ Novas Ruas", 1, 41, st.session_state.capacidade_padrao)
    if st.button("💾 Sincronizar com Nuvem"):
        salvar_dados()
        st.success("Dados enviados para o Google Sheets!")

    st.divider()
    rua_sel = st.selectbox("Selecione a Rua", lista_ruas_opcoes)
    if rua_sel not in st.session_state.config_ruas:
        inicializar_rua(rua_sel, st.session_state.capacidade_padrao)

    with st.expander("📏 Redimensionar Rua"):
        nova_cap = st.number_input(f"Capacidade {rua_sel}", 1, 41, int(st.session_state.config_ruas.get(rua_sel, 41)))
        if st.button("💾 Aplicar"):
            inicializar_rua(rua_sel, nova_cap)
            st.rerun()

    df_atual = st.session_state.estoque[st.session_state.estoque['Rua'] == rua_sel] if not st.session_state.estoque.empty else pd.DataFrame()
    cap_rua = st.session_state.config_ruas.get(rua_sel, 41)
    
    if not df_atual.empty:
        qtd_vazio = len(df_atual[df_atual['Status'] == 'Vazio'])
        st.metric("🟢 Disponíveis", len(df_atual[df_atual['Status'] == 'Disponível']))
        st.metric("⚪ Livres", f"{qtd_vazio} / {cap_rua}")
    else:
        qtd_vazio = 0

# --- DASHBOARD E MAPA (Mantendo sua lógica original) ---
# ... (O restante do seu código de Dashboard, Tabs e Mapa continua aqui exatamente igual)
# Apenas certifique-se de que o cálculo de qtd_vazio nas abas aponte para a variável correta.

# --- TABELA DE CONFERÊNCIA ---
# (Seu código de mapa e estilo continua igual ao anterior)
