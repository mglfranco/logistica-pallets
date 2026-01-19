import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import string
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Gestão Logística - Capacidade Galpão")

# --- PERSISTÊNCIA DE DADOS ---
DB_FILE = "banco_dados_estoque.csv"
CONFIG_FILE = "config_ruas.csv"
GLOBAL_CFG = "config_global.csv"

def salvar_dados():
    st.session_state.estoque.to_csv(DB_FILE, index=False)
    pd.DataFrame(list(st.session_state.config_ruas.items()), columns=['Rua', 'Capacidade']).to_csv(CONFIG_FILE, index=False)
    # Salva configurações globais (Capacidade do Galpão e Padrão de Rua)
    pd.DataFrame([{"cap_galpao": st.session_state.cap_total_galpao, "cap_padrao": st.session_state.capacidade_padrao}]).to_csv(GLOBAL_CFG, index=False)

def carregar_dados():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Lote'] = df['Lote'].fillna("")
        df['Cliente'] = df['Cliente'].fillna("")
        df['Validade'] = pd.to_datetime(df['Validade']).dt.date
        st.session_state.estoque = df
    if os.path.exists(CONFIG_FILE):
        df_cfg = pd.read_csv(CONFIG_FILE)
        st.session_state.config_ruas = dict(zip(df_cfg.Rua, df_cfg.Capacidade))
    if os.path.exists(GLOBAL_CFG):
        df_g = pd.read_csv(GLOBAL_CFG)
        st.session_state.cap_total_galpao = int(df_g.iloc[0]['cap_galpao'])
        st.session_state.capacidade_padrao = int(df_g.iloc[0]['cap_padrao'])

# --- INICIALIZAÇÃO ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = pd.DataFrame()
    st.session_state.config_ruas = {}
    st.session_state.capacidade_padrao = 41
    st.session_state.cap_total_galpao = 2000 # Valor inicial sugerido
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
st.title("🚜 Gestão Logística Master A-Z")

with st.sidebar:
    st.header("🏢 Configuração do Galpão")
    # OPÇÃO SOLICITADA: Mexer na capacidade total do galpão
    st.session_state.cap_total_galpao = st.number_input("Capacidade Total Galpão (Pallets)", 1, 100000, st.session_state.cap_total_galpao)
    st.session_state.capacidade_padrao = st.number_input("Capacidade Padrão p/ Novas Ruas", 1, 41, st.session_state.capacidade_padrao)
    
    if st.button("💾 Salvar Configurações"):
        salvar_dados()
        st.success("Configurações salvas!")

    st.divider()
    st.header("📍 Navegação")
    rua_sel = st.selectbox("Selecione a Rua", lista_ruas_opcoes)
    
    if rua_sel not in st.session_state.config_ruas:
        inicializar_rua(rua_sel, st.session_state.capacidade_padrao)

    with st.expander("📏 Ajustar Tamanho desta Rua"):
        nova_cap = st.number_input(f"Capacidade {rua_sel}", 1, 41, int(st.session_state.config_ruas[rua_sel]))
        if st.button("💾 Redefinir Rua"):
            inicializar_rua(rua_sel, nova_cap)
            st.rerun()

# --- DASHBOARD DE OCUPAÇÃO ---
if not st.session_state.estoque.empty:
    st.subheader("📊 Painel Estratégico")
    col_m1, col_m2, col_m3 = st.columns(3)
    
    # Capacidade Instalada (Soma das ruas configuradas)
    cap_instalada = sum(st.session_state.config_ruas.values())
    ocupados_global = len(st.session_state.estoque[st.session_state.estoque['Status'].isin(['Disponível', 'Reservado'])])
    
    # Cálculo baseado na capacidade do galpão configurada pelo usuário
    percentual_galpao = (ocupados_global / st.session_state.cap_total_galpao) * 100
    
    col_m1.metric("Capacidade Configurada", f"{st.session_state.cap_total_galpao} un.")
    col_m2.metric("Ocupação Real", f"{ocupados_global} pallets")
    
    # Alerta visual se passar de 90%
    cor_alerta = "normal" if percentual_galpao < 90 else "inverse"
    col_m3.metric("Uso do Galpão", f"{percentual_galpao:.1f}%", delta=f"{st.session_state.cap_total_galpao - ocupados_global} livres", delta_color=cor_alerta)
    
    st.progress(min(percentual_galpao / 100, 1.0))
    st.divider()

# --- OPERAÇÕES DA RUA SELECIONADA ---
# Métricas locais da rua
df_atual = st.session_state.estoque[st.session_state.estoque['Rua'] == rua_sel]
cap_rua = st.session_state.config_ruas[rua_sel]
qtd_disp = len(df_atual[df_atual['Status'] == 'Disponível'])
qtd_vazio = len(df_atual[df_atual['Status'] == 'Vazio'])

tab1, tab2, tab3 = st.tabs(["📥 Entrada", "🟠 Reserva", "⚪ Saída"])
# (Lógica das abas segue a mesma das versões anteriores com salvamento automático)
with tab1:
    l_in = st.text_input("Lote")
    v_in = st.date_input("Validade")
    q_in = st.number_input("Quantidade", 1, max(1, qtd_vazio))
    if st.button("📥 Confirmar Entrada"):
        vagas = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'] == 'Vazio')].sort_values(by=['Fileira', 'Nivel'], ascending=[False, True])
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        for i in range(min(int(q_in), len(vagas))):
            idx = vagas.index[i]
            st.session_state.estoque.at[idx, 'Lote'], st.session_state.estoque.at[idx, 'Validade'], st.session_state.estoque.at[idx, 'Status'], st.session_state.estoque.at[idx, 'Data_Entrada'] = l_in, v_in, 'Disponível', agora
        salvar_dados(); st.rerun()

# --- MAPA VISUAL ---

df_mapa = st.session_state.estoque[st.session_state.estoque['Rua'] == rua_sel].copy()
df_mapa['Visual'] = df_mapa['Status']
df_ordem = df_mapa[df_mapa['ID'] != '--'].sort_values(by='ID')
lote_ant = None
for idx, row in df_ordem.iterrows():
    if row['Status'] != 'Vazio':
        if lote_ant is not None and row['Lote'] != lote_ant:
            df_mapa.at[idx, 'Visual'] = 'TROCA'
        lote_ant = row['Lote']

df_mapa['Texto'] = df_mapa.apply(lambda r: f"P:{r['ID']}\n{str(r['Lote'])}\n{str(r['Cliente'])[:8]}" if r['Status'] not in ["Vazio", "BLOQUEADO"] else f"P:{r['ID']}" if r['Status'] == "Vazio" else "---", axis=1)
mapa_t = df_mapa.pivot(index='Nivel', columns='Fileira', values='Texto')
mapa_v = df_mapa.pivot(index='Nivel', columns='Fileira', values='Visual')

def style_fn(x):
    style_df = pd.DataFrame('', index=x.index, columns=x.columns)
    for r in x.index:
        for c in x.columns:
            v = mapa_v.loc[r, c]
            if v == "TROCA": color = 'background-color: #007bff; color: white; border: 3px solid white' 
            elif v == "Disponível": color = 'background-color: #28a745; color: white' 
            elif v == "Reservado": color = 'background-color: #fd7e14; color: white' 
            elif v == "Vazio": color = 'background-color: #ffffff; color: #444; border: 1px solid #ddd' 
            else: color = 'background-color: #111; color: #333' 
            style_df.loc[r, c] = f'{color}; font-size: 10px; font-weight: bold; text-align: center; height: 80px; min-width: 105px; white-space: pre-wrap;'
    return style_df

st.table(mapa_t[sorted(mapa_t.columns, reverse=True)].sort_index(ascending=False).style.apply(style_fn, axis=None))
st.dataframe(df_mapa[df_mapa['Status'] != "Vazio"].sort_values(by='ID')[['ID', 'Lote', 'Validade', 'Status', 'Cliente', 'Data_Entrada']], use_container_width=True, hide_index=True)
