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

# --- ESTILIZAÇÃO CSS PARA ELEGÂNCIA ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stTable { border-radius: 10px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE PERSISTÊNCIA (GOOGLE SHEETS) ---
def salvar_dados():
    if not GSHEETS_DISPONIVEL: return
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Salva o estoque
        conn.update(worksheet="Estoque", data=st.session_state.estoque)
        
        # Salva Configurações das Ruas (Capacidade e Altura)
        df_cfg = pd.DataFrame([
            {'Rua': k, 'Capacidade': v['cap'], 'Altura': v['alt']} 
            for k, v in st.session_state.config_ruas.items()
        ])
        conn.update(worksheet="Config_Ruas", data=df_cfg)
        
        # Salva Config Global
        df_g = pd.DataFrame([{"cap_galpao": st.session_state.cap_total_galpao, "cap_padrao": st.session_state.capacidade_padrao}])
        conn.update(worksheet="Config_Global", data=df_g)
    except Exception as e:
        st.error(f"Erro ao salvar na nuvem: {e}")

def carregar_dados():
    if not GSHEETS_DISPONIVEL: return
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_e = conn.read(worksheet="Estoque")
        if df_e is not None and not df_e.empty:
            df_e['Validade'] = pd.to_datetime(df_e['Validade']).dt.date
            df_e['Lote'] = df_e['Lote'].fillna("")
            df_e['Cliente'] = df_e['Cliente'].fillna("")
            st.session_state.estoque = df_e
            
        df_c = conn.read(worksheet="Config_Ruas")
        if df_c is not None and not df_c.empty:
            st.session_state.config_ruas = {
                row['Rua']: {'cap': int(row['Capacidade']), 'alt': int(row['Altura'])} 
                for _, row in df_c.iterrows()
            }
            
        df_g = conn.read(worksheet="Config_Global")
        if df_g is not None and not df_g.empty:
            st.session_state.cap_total_galpao = int(df_g.iloc[0]['cap_galpao'])
            st.session_state.capacidade_padrao = int(df_g.iloc[0]['cap_padrao'])
    except:
        pass

# --- INICIALIZAÇÃO SEGURA ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = pd.DataFrame()
    st.session_state.config_ruas = {}
    st.session_state.capacidade_padrao = 41
    st.session_state.cap_total_galpao = 2000
    carregar_dados()

def inicializar_rua(nome_rua, capacidade, altura_max):
    dados = []
    posicoes_uteis = []
    altura_saida = max(1, altura_max - 1)

    for f in range(1, 15):
        limite_f = altura_saida if f == 1 else altura_max
        for n in range(altura_max, 0, -1):
            if n <= limite_f:
                posicoes_uteis.append((f, n))
    
    for f in range(1, 15):
        for n in range(1, 4):
            status = "Vazio"
            id_p = "--"
            limite_atual = altura_saida if f == 1 else altura_max
            
            if n > limite_atual:
                status = "BLOQUEADO"
            elif (f, n) in posicoes_uteis[:capacidade]:
                idx_num = posicoes_uteis.index((f, n)) + 1
                id_p = f"{idx_num:02d}"
            else:
                status = "BLOQUEADO"
            
            dados.append({
                "Rua": nome_rua, "Fileira": f, "Nivel": n, "ID": id_p,
                "Lote": "", "Validade": None, "Status": status, "Cliente": "", "Data_Entrada": None
            })
    
    df_nova = pd.DataFrame(dados)
    if st.session_state.estoque.empty:
        st.session_state.estoque = df_nova
    else:
        st.session_state.estoque = pd.concat([st.session_state.estoque[st.session_state.estoque['Rua'] != nome_rua], df_nova])
    
    st.session_state.config_ruas[nome_rua] = {'cap': capacidade, 'alt': altura_max}
    salvar_dados()

# --- INTERFACE ---
st.title("🚜 Gestão Logística Master")

with st.sidebar:
    st.header("⚙️ Configurações")
    st.session_state.cap_total_galpao = st.number_input("Capacidade Galpão", 1, 50000, st.session_state.cap_total_galpao)
    
    lista_ruas = [f"Rua {l}{n}" for l in string.ascii_uppercase for n in [1, 2]]
    rua_sel = st.selectbox("📍 Selecionar Rua", lista_ruas)
    
    if rua_sel not in st.session_state.config_ruas:
        inicializar_rua(rua_sel, 41, 3)

    with st.expander("🏗️ Estrutura da Rua"):
        cap_ajuste = st.number_input("Capacidade", 1, 41, int(st.session_state.config_ruas[rua_sel]['cap']))
        alt_ajuste = st.selectbox("Altura Máxima", [1, 2, 3], index=int(st.session_state.config_ruas[rua_sel]['alt'])-1)
        if st.button("🔧 Reconstruir Rua"):
            inicializar_rua(rua_sel, cap_ajuste, alt_ajuste)
            st.rerun()
    
    if st.button("🔄 Sincronizar Nuvem"):
        salvar_dados()
        st.success("Dados sincronizados!")

# --- DASHBOARD ---
ocupados_global = len(st.session_state.estoque[st.session_state.estoque['Status'].isin(['Disponível', 'Reservado'])]) if not st.session_state.estoque.empty else 0
perc = (ocupados_global / st.session_state.cap_total_galpao) * 100
c1, c2, c3 = st.columns(3)
c1.metric("Estoque Total", ocupados_global)
c2.metric("Capacidade Galpão", st.session_state.cap_total_galpao)
c3.metric("Ocupação", f"{perc:.1f}%")
st.progress(min(perc/100, 1.0))

# --- OPERAÇÕES ---
st.divider()
df_atual = st.session_state.estoque[st.session_state.estoque['Rua'] == rua_sel]
qtd_vazio = len(df_atual[df_atual['Status'] == 'Vazio'])
tab1, tab2, tab3 = st.tabs(["📥 Entrada", "🟠 Reserva", "⚪ Saída"])

with tab1:
    col_a, col_b, col_c = st.columns(3)
    l_in = col_a.text_input("Lote")
    v_in = col_b.date_input("Validade")
    q_in = col_c.number_input("Quantidade", 1, 41)
    if st.button("📥 Confirmar Entrada"):
        vagas = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'] == 'Vazio')].sort_values(by=['Fileira', 'Nivel'], ascending=[False, True])
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        for i in range(min(int(q_in), len(vagas))):
            idx = vagas.index[i]
            st.session_state.estoque.at[idx, 'Lote'], st.session_state.estoque.at[idx, 'Validade'], st.session_state.estoque.at[idx, 'Status'], st.session_state.estoque.at[idx, 'Data_Entrada'] = l_in, v_in, 'Disponível', agora
        salvar_dados(); st.rerun()

with tab2:
    col_a, col_b = st.columns(2)
    cli = col_a.text_input("Cliente")
    q_res = col_b.number_input("Qtd Reserva", 1, 41)
    if st.button("🟠 Confirmar Reserva"):
        disp = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'] == 'Disponível')].sort_values(by='ID')
        for i in range(min(int(q_res), len(disp))):
            idx = disp.index[i]
            st.session_state.estoque.at[idx, 'Status'], st.session_state.estoque.at[idx, 'Cliente'] = 'Reservado', cli.upper()
        salvar_dados(); st.rerun()

with tab3:
    col_a, col_b = st.columns(2)
    q_out = col_a.number_input("Qtd Saída", 1, 41)
    modo = col_b.radio("Regra:", ["Somente Reservados", "Saída Direta"], horizontal=True)
    if st.button("⚪ Confirmar Saída"):
        filtro = ['Reservado'] if modo == "Somente Reservados" else ['Disponível', 'Reservado']
        alvos = st.session_state.estoque[(st.session_state.estoque['Rua'] == rua_sel) & (st.session_state.estoque['Status'].isin(filtro))].sort_values(by='ID')
        for i in range(min(int(q_out), len(alvos))):
            idx = alvos.index[i]
            st.session_state.estoque.loc[idx, ['Lote', 'Status', 'Validade', 'Cliente', 'Data_Entrada']] = ["", "Vazio", None, "", None]
        salvar_dados(); st.rerun()

# --- MAPA INTELIGENTE ---
st.subheader(f"🗺️ Mapa da {rua_sel}")
df_mapa = st.session_state.estoque[st.session_state.estoque['Rua'] == rua_sel].copy()
df_mapa['Visual'] = df_mapa['Status']
df_mapa['Aura_FEFO'] = False
hoje = date.today()

# Processamento de Cores e FEFO
df_ordem = df_mapa[df_mapa['ID'] != '--'].sort_values(by='ID')
lote_ant = None
for idx, row in df_ordem.iterrows():
    if row['Status'] not in ["Vazio", "BLOQUEADO"]:
        # Aura amarela se validade < 6 meses
        if row['Validade'] and (row['Validade'] - hoje).days <= 180:
            df_mapa.at[idx, 'Aura_FEFO'] = True
        # Cor azul na troca de lote
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
            borda = "border: 4px solid #FFFF00; box-shadow: inset 0 0 10px #FFFF00;" if fefo else "border: 1px solid #ddd;"
            
            if v == "TROCA": color = 'background-color: #007bff; color: white;' 
            elif v == "Disponível": color = 'background-color: #28a745; color: white' 
            elif v == "Reservado": color = 'background-color: #fd7e14; color: white' 
            elif v == "Vazio": color = 'background-color: #ffffff; color: #adb5bd;' 
            else: color = 'background-color: #f8f9fa; color: #f8f9fa; border: none;' 
            
            style_df.loc[r, c] = f'{color} {borda} font-size: 10px; font-weight: bold; text-align: center; height: 85px; min-width: 105px; white-space: pre-wrap; border-radius: 5px;'
    return style_df

st.table(mapa_t[sorted(mapa_t.columns, reverse=True)].sort_index(ascending=False).style.apply(style_fn, axis=None))

# --- LISTAGEM FINAL ---
st.subheader("📋 Conferência Detalhada")
df_conf = df_mapa[df_mapa['Status'] != "Vazio"].sort_values(by='ID').copy()
df_conf['FEFO'] = df_conf['Aura_FEFO'].apply(lambda x: "⚠️ ALERTA" if x else "✅ OK")
st.dataframe(df_conf[['ID', 'Lote', 'Validade', 'Status', 'Cliente', 'FEFO', 'Data_Entrada']], use_container_width=True, hide_index=True)
