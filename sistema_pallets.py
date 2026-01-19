import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date, timedelta
import string
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Logística Pro - Gestão de Galpão", page_icon="🚜")

# --- ESTILIZAÇÃO CSS PARA ELEGÂNCIA ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stTable { border-radius: 10px; overflow: hidden; }
    div[data-testid="stExpander"] { border: none; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- PERSISTÊNCIA DE DADOS ---
DB_FILE = "banco_dados_estoque.csv"
CONFIG_FILE = "config_ruas.csv"
GLOBAL_CFG = "config_global.csv"

def salvar_dados():
    st.session_state.estoque.to_csv(DB_FILE, index=False)
    # Salva as configurações de cada rua (Capacidade e Altura Máxima)
    df_conf = pd.DataFrame([
        {'Rua': k, 'Capacidade': v['cap'], 'Altura': v['alt']} 
        for k, v in st.session_state.config_ruas.items()
    ])
    df_conf.to_csv(CONFIG_FILE, index=False)
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
        st.session_state.config_ruas = {row['Rua']: {'cap': row['Capacidade'], 'alt': row['Altura']} for _, row in df_cfg.iterrows()}
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

def inicializar_rua(nome_rua, capacidade, altura_max):
    dados = []
    posicoes_uteis = []
    
    # Define a regra de altura dinâmica
    # Se a rua é altura 3, a saída é 2. Se a rua é altura 2, a saída é 1. Se é 1, a saída é 1.
    altura_saida = max(1, altura_max - 1)

    for f in range(1, 15):
        limite_f = altura_saida if f == 1 else altura_max
        for n in range(altura_max, 0, -1): # Começa do topo configurado
            if n <= limite_f:
                posicoes_uteis.append((f, n))
    
    for f in range(1, 15):
        for n in range(1, 4): # O sistema base suporta até 3 para desenho
            pallet_id = "--"
            status = "Vazio"
            # Se o nível estiver acima da altura configurada para a rua, bloqueia
            if n > (altura_saida if f == 1 else altura_max):
                status = "BLOQUEADO"
            elif (f, n) in posicoes_uteis[:capacidade]:
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
    
    st.session_state.config_ruas[nome_rua] = {'cap': capacidade, 'alt': altura_max}
    salvar_dados()

# Lista de Ruas A-Z
lista_ruas = [f"Rua {l}{n}" for l in string.ascii_uppercase for n in [1, 2]]

# --- INTERFACE ---
with st.sidebar:
    st.title("⚙️ Painel de Controle")
    rua_sel = st.selectbox("📍 Selecionar Corredor", lista_ruas)
    
    if rua_sel not in st.session_state.config_ruas:
        inicializar_rua(rua_sel, st.session_state.capacidade_padrao, 3)

    st.divider()
    with st.expander("🏗️ Configurar Estrutura da Rua"):
        cap_ajuste = st.number_input("Capacidade Total", 1, 41, int(st.session_state.config_ruas[rua_sel]['cap']))
        alt_ajuste = st.selectbox("Altura Máxima da Rua", [1, 2, 3], index=int(st.session_state.config_ruas[rua_sel]['alt'])-1)
        st.caption("Nota: A Fileira 01 (Saída) terá sempre um nível a menos para segurança.")
        if st.button("🔧 Reconstruir Rua"):
            inicializar_rua(rua_sel, cap_ajuste, alt_ajuste)
            st.rerun()

    st.divider()
    st.header("🏢 Galpão")
    st.session_state.cap_total_galpao = st.number_input("Capacidade Galpão", 1, 100000, st.session_state.cap_total_galpao)
    if st.button("💾 Salvar Configurações"):
        salvar_dados()
        st.success("Salvo!")

# --- DASHBOARD ---
ocupados_global = len(st.session_state.estoque[st.session_state.estoque['Status'].isin(['Disponível', 'Reservado'])])
perc_galpao = (ocupados_global / st.session_state.cap_total_galpao) * 100

st.subheader("📊 Visão Estratégica")
c1, c2, c3 = st.columns(3)
c1.metric("Estoque Total", f"{ocupados_global} un.")
c2.metric("Capacidade Galpão", f"{st.session_state.cap_total_galpao}")
c3.metric("Ocupação", f"{perc_galpao:.1f}%")
st.progress(min(perc_galpao/100, 1.0))

# --- OPERAÇÕES ---
st.divider()
df_atual = st.session_state.estoque[st.session_state.estoque['Rua'] == rua_sel]
qtd_vazio = len(df_atual[df_atual['Status'] == 'Vazio'])
qtd_disp = len(df_atual[df_atual['Status'] == 'Disponível'])

tab1, tab2, tab3 = st.tabs(["📥 Entrada de Lote", "🟠 Reserva p/ Cliente", "⚪ Saída de Pallets"])

with tab1:
    col_a, col_b, col_c = st.columns(3)
    l_in = col_a.text_input("Lote/Produto")
    v_in = col_b.date_input("Validade")
    q_in = col_c.number_input("Quantidade", 1, max(1, qtd_vazio))
    if st.button("📥 Confirmar Entrada"):
        vagas = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'] == 'Vazio')].sort_values(by=['Fileira', 'Nivel'], ascending=[False, True])
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        for i in range(min(int(q_in), len(vagas))):
            idx = vagas.index[i]
            st.session_state.estoque.at[idx, 'Lote'], st.session_state.estoque.at[idx, 'Validade'], st.session_state.estoque.at[idx, 'Status'], st.session_state.estoque.at[idx, 'Data_Entrada'] = l_in, v_in, 'Disponível', agora
        salvar_dados(); st.rerun()

with tab2:
    col_a, col_b = st.columns(2)
    cli_res = col_a.text_input("Nome do Cliente")
    q_res = col_b.number_input("Qtd a Reservar", 1, max(1, qtd_disp))
    if st.button("🟠 Confirmar Reserva"):
        disp = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'] == 'Disponível')].sort_values(by='ID')
        for i in range(min(int(q_res), len(disp))):
            idx = disp.index[i]
            st.session_state.estoque.at[idx, 'Status'], st.session_state.estoque.at[idx, 'Cliente'] = 'Reservado', cli_res.upper()
        salvar_dados(); st.rerun()

with tab3:
    col_a, col_b = st.columns(2)
    q_out = col_a.number_input("Quantidade Saindo", 1, 41)
    modo = col_b.radio("Regra:", ["Somente Reservados", "Saída Direta"], horizontal=True)
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
hoje = date.today()

# FEFO + Alerta Azul
df_ordem = df_mapa[df_mapa['ID'] != '--'].sort_values(by='ID')
lote_ant = None
for idx, row in df_ordem.iterrows():
    if row['Status'] not in ["Vazio", "BLOQUEADO"]:
        if row['Validade'] and (row['Validade'] - hoje).days <= 180: df_mapa.at[idx, 'Aura_FEFO'] = True
        if lote_ant is not None and row['Lote'] != lote_ant: df_mapa.at[idx, 'Visual'] = 'TROCA'
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
            borda = "border: 4px solid #FFFF00; box-shadow: inset 0 0 8px #FFFF00;" if fefo else "border: 1px solid #dee2e6;"
            if v == "TROCA": color = 'background-color: #007bff; color: white;' 
            elif v == "Disponível": color = 'background-color: #28a745; color: white' 
            elif v == "Reservado": color = 'background-color: #fd7e14; color: white' 
            elif v == "Vazio": color = 'background-color: #ffffff; color: #adb5bd;' 
            else: color = 'background-color: #f1f3f5; color: #f1f3f5; border: none;' 
            style_df.loc[r, c] = f'{color} {borda} font-size: 10px; font-weight: bold; text-align: center; height: 85px; min-width: 110px; white-space: pre-wrap; border-radius: 8px;'
    return style_df

st.subheader(f"🗺️ Mapa Interativo: {rua_sel}")

st.table(mapa_t[sorted(mapa_t.columns, reverse=True)].sort_index(ascending=False).style.apply(style_fn, axis=None))

st.markdown("""
<div style="display: flex; gap: 20px; font-size: 12px; font-weight: bold;">
    <div><span style="color: #28a745;">⬛</span> Disponível</div>
    <div><span style="color: #fd7e14;">⬛</span> Reservado</div>
    <div><span style="color: #007bff;">⬛</span> Início Lote Novo</div>
    <div><span style="color: #FFFF00;">⬜</span> Aura: Vencimento < 6 meses</div>
</div>
""", unsafe_allow_html=True)

# --- TABELA FINAL ---
st.divider()
st.subheader("📋 Relatório de Conferência")
df_conf = df_mapa[df_mapa['Status'] != "Vazio"].sort_values(by='ID').copy()
df_conf['FEFO'] = df_conf['Aura_FEFO'].apply(lambda x: "⚠️ ALERTA" if x else "✅ OK")
st.dataframe(df_conf[['ID', 'Lote', 'Validade', 'Status', 'Cliente', 'FEFO', 'Data_Entrada']], use_container_width=True, hide_index=True)
