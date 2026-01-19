import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import string
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Logística Master - Controle de ruas/estoque")

# --- FUNÇÃO PARA SALVAR/CARREGAR DADOS (PERSISTÊNCIA) ---
DB_FILE = "banco_dados_estoque.csv"
CONFIG_FILE = "config_ruas.csv"

def salvar_dados():
    st.session_state.estoque.to_csv(DB_FILE, index=False)
    pd.DataFrame(list(st.session_state.config_ruas.items()), columns=['Rua', 'Capacidade']).to_csv(CONFIG_FILE, index=False)

def carregar_dados():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # CORREÇÃO: Garante que colunas vazias sejam lidas como texto vazio e não como Nulo (NaN)
        df['Lote'] = df['Lote'].fillna("")
        df['Cliente'] = df['Cliente'].fillna("")
        df['Validade'] = pd.to_datetime(df['Validade']).dt.date
        st.session_state.estoque = df
    if os.path.exists(CONFIG_FILE):
        df_cfg = pd.read_csv(CONFIG_FILE)
        st.session_state.config_ruas = dict(zip(df_cfg.Rua, df_cfg.Capacidade))

# --- INICIALIZAÇÃO DO ESTADO ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = pd.DataFrame()
    st.session_state.config_ruas = {}
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

# --- INTERFACE PRINCIPAL ---
st.title("🚜 Controle Logístico - Gestão de Ruas 🚜")

if not st.session_state.estoque.empty:
    st.divider()
    st.subheader("📊 Painel Estratégico do Armazém")
    col_m1, col_m2, col_m3 = st.columns(3)
    total_pallets_global = len(st.session_state.estoque[st.session_state.estoque['Status'] != 'BLOQUEADO'])
    ocupados_global = len(st.session_state.estoque[st.session_state.estoque['Status'].isin(['Disponível', 'Reservado'])])
    percentual = (ocupados_global / total_pallets_global) * 100 if total_pallets_global > 0 else 0
    col_m1.metric("Capacidade Total", f"{total_pallets_global} Pallets")
    col_m2.metric("Ocupação Geral", f"{ocupados_global} Unid.")
    with col_m3:
        st.write(f"**Progresso de Ocupação: {percentual:.1f}%**")
        st.progress(percentual / 100)
    st.divider()

with st.sidebar:
    st.header("⚙️ Configurações")
    rua_sel = st.selectbox("Selecione a Rua", lista_ruas_opcoes)
    if rua_sel not in st.session_state.config_ruas:
        inicializar_rua(rua_sel, 41)
    with st.expander("📏 Ajustar Tamanho da Rua"):
        nova_cap = st.number_input(f"Capacidade da {rua_sel}", 1, 41, int(st.session_state.config_ruas[rua_sel]))
        if st.button("💾 Aplicar Nova Capacidade"):
            inicializar_rua(rua_sel, nova_cap)
            st.rerun()
    st.divider()
    df_atual = st.session_state.estoque[st.session_state.estoque['Rua'] == rua_sel]
    cap_max = st.session_state.config_ruas[rua_sel]
    qtd_disp = len(df_atual[df_atual['Status'] == 'Disponível'])
    qtd_res = len(df_atual[df_atual['Status'] == 'Reservado'])
    qtd_vazio = len(df_atual[df_atual['Status'] == 'Vazio'])
    st.metric("🟢 Disponíveis", qtd_disp); st.metric("🟠 Reservados", qtd_res); st.metric("⚪ Livres", f"{qtd_vazio} / {cap_max}")
    tab1, tab2, tab3 = st.tabs(["📥 Entrada", "🟠 Reserva", "⚪ Saída"])
    with tab1:
        lote_in = st.text_input("Lote")
        val_in = st.date_input("Validade")
        qtd_in = st.number_input("Qtd Entrada", 1, max(1, qtd_vazio))
        if st.button("📥 Adicionar"):
            vagas = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'] == 'Vazio')]
            vagas = vagas.sort_values(by=['Fileira', 'Nivel'], ascending=[False, True])
            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
            for i in range(min(int(qtd_in), len(vagas))):
                idx = vagas.index[i]
                st.session_state.estoque.at[idx, 'Lote'], st.session_state.estoque.at[idx, 'Validade'], st.session_state.estoque.at[idx, 'Status'], st.session_state.estoque.at[idx, 'Data_Entrada'] = lote_in, val_in, 'Disponível', agora
            salvar_dados(); st.rerun()
    with tab2:
        cliente_res = st.text_input("Cliente")
        qtd_res_in = st.number_input("Qtd Reservar", 1, max(1, qtd_disp))
        if st.button("🟠 Confirmar Reserva"):
            if not cliente_res: st.warning("Digite o cliente!")
            else:
                disp = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'] == 'Disponível')].sort_values(by='ID')
                for i in range(min(int(qtd_res_in), len(disp))):
                    idx = disp.index[i]
                    st.session_state.estoque.at[idx, 'Status'], st.session_state.estoque.at[idx, 'Cliente'] = 'Reservado', cliente_res.upper()
                salvar_dados(); st.rerun()
    with tab3:
        qtd_out = st.number_input("Qtd Retirar", 1, int(cap_max))
        modo_saida = st.radio("Regra de Saída:", ["Somente Reservados", "Saída Direta (Ajuste)"])
        if st.button("⚪ Confirmar Saída"):
            filtro = ['Reservado'] if modo_saida == "Somente Reservados" else ['Disponível', 'Reservado']
            alvos = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'].isin(filtro))].sort_values(by='ID')
            if alvos.empty: st.error("Nenhum pallet compatível!")
            else:
                for i in range(min(int(qtd_out), len(alvos))):
                    idx = alvos.index[i]
                    st.session_state.estoque.loc[idx, ['Lote', 'Status', 'Validade', 'Cliente', 'Data_Entrada']] = ["", "Vazio", None, "", None]
                salvar_dados(); st.rerun()

# --- LÓGICA DO MAPA (AQUI ESTAVA O ERRO) ---
df_mapa = st.session_state.estoque[st.session_state.estoque['Rua'] == rua_sel].copy()
df_mapa['Visual'] = df_mapa['Status']
df_ordem = df_mapa[df_mapa['ID'] != '--'].sort_values(by='ID')
lote_ant = None
for idx, row in df_ordem.iterrows():
    if row['Status'] != 'Vazio':
        if lote_ant is not None and row['Lote'] != lote_ant:
            df_mapa.at[idx, 'Visual'] = 'TROCA'
        lote_ant = row['Lote']

# CORREÇÃO DA LINHA 183: Usamos str(r['Cliente']) para evitar o erro de tipo
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
            style_df.loc[r, c] = f'{color}; font-size: 10px; font-weight: bold; text-align: center; height: 80px; min-width: 110px; white-space: pre-wrap;'
    return style_df

st.subheader(f"🗺️ Mapa: {rua_sel} (Capacidade: {cap_max})")
st.table(mapa_t[sorted(mapa_t.columns, reverse=True)].sort_index(ascending=False).style.apply(style_fn, axis=None))

st.subheader("📋 Detalhamento de Conferência")
df_conf = df_mapa[df_mapa['Status'] != "Vazio"].sort_values(by='ID')[['ID', 'Lote', 'Validade', 'Status', 'Cliente', 'Data_Entrada']]
st.dataframe(df_conf, use_container_width=True, hide_index=True)
