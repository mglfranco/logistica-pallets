import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date
import string
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Logística Master A-Z - FEFO e Lotes")

# --- PERSISTÊNCIA DE DADOS ---
DB_FILE = "banco_dados_estoque.csv"
CONFIG_FILE = "config_ruas.csv"
GLOBAL_CFG = "config_global.csv"

def salvar_dados():
    st.session_state.estoque.to_csv(DB_FILE, index=False)
    pd.DataFrame(list(st.session_state.config_ruas.items()), columns=['Rua', 'Capacidade']).to_csv(CONFIG_FILE, index=False)
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
st.title("🚜 Controle Logístico - Gestão de Ruas 🚜")

if not st.session_state.estoque.empty:
    st.divider()
    st.subheader("📊 Painel Estratégico do Galpão")
    col_m1, col_m2, col_m3 = st.columns(3)
    ocupados_global = len(st.session_state.estoque[st.session_state.estoque['Status'].isin(['Disponível', 'Reservado'])])
    percentual_galpao = (ocupados_global / st.session_state.cap_total_galpao) * 100 if st.session_state.cap_total_galpao > 0 else 0
    col_m1.metric("Capacidade Galpão", f"{st.session_state.cap_total_galpao}")
    col_m2.metric("Ocupação Total", f"{ocupados_global} un.")
    with col_m3:
        st.write(f"**Uso do Espaço: {percentual_galpao:.1f}%**")
        st.progress(min(percentual_galpao / 100, 1.0))
    st.divider()

with st.sidebar:
    st.header("⚙️ Configurações Globais")
    st.session_state.cap_total_galpao = st.number_input("Capacidade Total Galpão", 1, 100000, st.session_state.cap_total_galpao)
    st.session_state.capacidade_padrao = st.number_input("Capacidade Padrão p/ Novas Ruas", 1, 41, st.session_state.capacidade_padrao)
    if st.button("💾 Salvar Configurações"):
        salvar_dados()
        st.success("Configurações salvas!")

    st.divider()
    st.header("📍 Navegação")
    rua_sel = st.selectbox("Selecione a Rua", lista_ruas_opcoes)
    if rua_sel not in st.session_state.config_ruas:
        inicializar_rua(rua_sel, st.session_state.capacidade_padrao)

    with st.expander("📏 Ajustar Tamanho da Rua"):
        nova_cap = st.number_input(f"Capacidade {rua_sel}", 1, 41, int(st.session_state.config_ruas[rua_sel]))
        if st.button("💾 Redefinir Rua"):
            inicializar_rua(rua_sel, nova_cap)
            st.rerun()

    df_atual = st.session_state.estoque[st.session_state.estoque['Rua'] == rua_sel]
    cap_rua = st.session_state.config_ruas[rua_sel]
    qtd_vazio = len(df_atual[df_atual['Status'] == 'Vazio'])
    st.metric("🟢 Disponíveis", len(df_atual[df_atual['Status'] == 'Disponível']))
    st.metric("🟠 Reservados", len(df_atual[df_atual['Status'] == 'Reservado']))
    st.metric("⚪ Livres nesta Rua", f"{qtd_vazio} / {cap_rua}")

tab1, tab2, tab3 = st.tabs(["📥 Entrada", "🟠 Reserva", "⚪ Saída"])

with tab1:
    l_in = st.text_input("Lote")
    v_in = st.date_input("Validade")
    q_in = st.number_input("Qtd Entrada", 1, max(1, qtd_vazio))
    if st.button("📥 Adicionar"):
        vagas = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'] == 'Vazio')].sort_values(by=['Fileira', 'Nivel'], ascending=[False, True])
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        for i in range(min(int(q_in), len(vagas))):
            idx = vagas.index[i]
            st.session_state.estoque.at[idx, 'Lote'], st.session_state.estoque.at[idx, 'Validade'], st.session_state.estoque.at[idx, 'Status'], st.session_state.estoque.at[idx, 'Data_Entrada'] = l_in, v_in, 'Disponível', agora
        salvar_dados(); st.rerun()

with tab2:
    cli_res = st.text_input("Cliente")
    q_res = st.number_input("Qtd Reservar", 1, max(1, len(df_atual[df_atual['Status'] == 'Disponível'])))
    if st.button("🟠 Confirmar Reserva"):
        disp = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'] == 'Disponível')].sort_values(by='ID')
        for i in range(min(int(q_res), len(disp))):
            idx = disp.index[i]
            st.session_state.estoque.at[idx, 'Status'], st.session_state.estoque.at[idx, 'Cliente'] = 'Reservado', cli_res.upper()
        salvar_dados(); st.rerun()

with tab3:
    q_out = st.number_input("Qtd Retirar", 1, int(cap_rua))
    modo = st.radio("Regra:", ["Somente Reservados", "Saída Direta"], horizontal=True)
    if st.button("⚪ Confirmar Saída"):
        filtro = ['Reservado'] if modo == "Somente Reservados" else ['Disponível', 'Reservado']
        alvos = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'].isin(filtro))].sort_values(by='ID')
        for i in range(min(int(q_out), len(alvos))):
            idx = alvos.index[i]
            st.session_state.estoque.loc[idx, ['Lote', 'Status', 'Validade', 'Cliente', 'Data_Entrada']] = ["", "Vazio", None, "", None]
        salvar_dados(); st.rerun()

# --- LÓGICA DO MAPA ---

df_mapa = st.session_state.estoque[st.session_state.estoque['Rua'] == rua_sel].copy()
df_mapa['Visual'] = df_mapa['Status']
df_mapa['Aura_FEFO'] = False

# Cálculo FEFO (6 meses)
hoje = date.today()
for idx, row in df_mapa.iterrows():
    if row['Status'] != 'Vazio' and row['Validade'] is not None:
        try:
            val = row['Validade']
            if isinstance(val, str): val = datetime.strptime(val, '%Y-%m-%d').date()
            if (val - hoje).days <= 180: df_mapa.at[idx, 'Aura_FEFO'] = True
        except: pass

# LÓGICA COR AZUL: Pula para o primeiro pallet do próximo lote na sequência numérica
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
mapa_fefo = df_mapa.pivot(index='Nivel', columns='Fileira', values='Aura_FEFO')

def style_fn(x):
    style_df = pd.DataFrame('', index=x.index, columns=x.columns)
    for r in x.index:
        for c in x.columns:
            v = mapa_v.loc[r, c]
            fefo = mapa_fefo.loc[r, c]
            borda = "border: 4px solid #ffff00;" if fefo else "border: 1px solid #ddd;"
            
            if v == "TROCA": color = 'background-color: #007bff; color: white;' 
            elif v == "Disponível": color = 'background-color: #28a745; color: white' 
            elif v == "Reservado": color = 'background-color: #fd7e14; color: white' 
            elif v == "Vazio": color = 'background-color: #ffffff; color: #444;' 
            else: color = 'background-color: #111; color: #333' 
            
            style_df.loc[r, c] = f'{color} {borda} font-size: 10px; font-weight: bold; text-align: center; height: 80px; min-width: 110px; white-space: pre-wrap;'
    return style_df

st.table(mapa_t[sorted(mapa_t.columns, reverse=True)].sort_index(ascending=False).style.apply(style_fn, axis=None))
st.subheader("📋 Conferência Detalhada")
df_conf = df_mapa[df_mapa['Status'] != "Vazio"].sort_values(by='ID').copy()
df_conf['FEFO'] = df_conf['Aura_FEFO'].apply(lambda x: "⚠️ VENC. PRÓXIMO" if x else "✅ OK")
st.dataframe(df_conf[['ID', 'Lote', 'Validade', 'Status', 'Cliente', 'FEFO']], use_container_width=True, hide_index=True)
