import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import string
import time

# --- TENTA IMPORTAR A CONEXÃO COM GOOGLE SHEETS ---
try:
    from streamlit_gsheets import GSheetsConnection
    GSHEETS_DISPONIVEL = True
except ImportError:
    GSHEETS_DISPONIVEL = False

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Logística Pro - Autosave", page_icon="🚜")

# --- CSS (Design Responsivo e Dark Mode) ---
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid var(--faded-text-10);
        border-radius: 10px;
        padding: 10px;
    }
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 48px;
        font-weight: 600;
    }
    .stTable { font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS ---
def salvar_dados():
    """Salva e limpa o cache."""
    if not GSHEETS_DISPONIVEL: return
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        with st.spinner('Salvando...'):
            conn.update(worksheet="Estoque", data=st.session_state.estoque)
            
            df_cfg = pd.DataFrame([
                {'Rua': k, 'Capacidade': v.get('cap', 41), 'Altura': v.get('alt', 3)} 
                for k, v in st.session_state.config_ruas.items()
            ])
            conn.update(worksheet="Config_Ruas", data=df_cfg)
            
            # Salva a capacidade global atualizada
            df_g = pd.DataFrame([{"cap_galpao": st.session_state.cap_total_galpao, "cap_padrao": st.session_state.capacidade_padrao}])
            conn.update(worksheet="Config_Global", data=df_g)
            
            st.cache_data.clear()
        
        st.toast("Salvo na nuvem!", icon="✅")
        
    except Exception as e:
        st.error(f"Erro ao Salvar: {e}")

def carregar_dados():
    """Lê os dados com ttl=0."""
    if not GSHEETS_DISPONIVEL: return
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        df_e = conn.read(worksheet="Estoque", ttl=0)
        
        if df_e is not None and not df_e.empty:
            df_e['Validade'] = pd.to_datetime(df_e['Validade']).dt.date
            df_e['ID'] = df_e['ID'].astype(str)
            df_e['Lote'] = df_e['Lote'].fillna("").astype(str)
            df_e['Cliente'] = df_e['Cliente'].fillna("").astype(str)
            st.session_state.estoque = df_e
            
        df_c = conn.read(worksheet="Config_Ruas", ttl=0)
        if df_c is not None and not df_c.empty:
            st.session_state.config_ruas = {} 
            for _, row in df_c.iterrows():
                st.session_state.config_ruas[row['Rua']] = {
                    'cap': int(row.get('Capacidade', 41)), 
                    'alt': int(row.get('Altura', 3))
                }
            
        df_g = conn.read(worksheet="Config_Global", ttl=0)
        if df_g is not None and not df_g.empty:
            st.session_state.cap_total_galpao = int(df_g.iloc[0]['cap_galpao'])
    except Exception as e:
        time.sleep(1)

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
    altura_saida = max(1, altura_max - 1)

    for f in range(1, 15):
        limite_f = altura_saida if f == 1 else altura_max
        for n in range(altura_max, 0, -1):
            if n <= limite_f: posicoes_uteis.append((f, n))
    
    for f in range(1, 15):
        for n in range(1, 4):
            status = "Vazio"
            id_p = "--"
            limite_atual = altura_saida if f == 1 else altura_max
            if n > limite_atual: status = "BLOQUEADO"
            elif (f, n) in posicoes_uteis[:capacidade]:
                idx_num = posicoes_uteis.index((f, n)) + 1
                id_p = f"{idx_num:02d}"
            else: status = "BLOQUEADO"
            
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

# --- SIDEBAR ---
lista_ruas = [f"Rua {l}{n}" for l in string.ascii_uppercase for n in [1, 2]]

with st.sidebar:
    st.header("⚙️ Painel")
    rua_sel = st.selectbox("📍 Selecionar Rua", lista_ruas)
    
    if rua_sel not in st.session_state.config_ruas:
        inicializar_rua(rua_sel, 41, 3)

    st.divider()
    with st.expander("🏗️ Configurar Rua"):
        val_cap = st.session_state.config_ruas[rua_sel].get('cap', 41)
        val_alt = st.session_state.config_ruas[rua_sel].get('alt', 3)
        
        novo_cap = st.number_input("Capacidade", 1, 41, int(val_cap))
        novo_alt = st.selectbox("Altura", [1, 2, 3], index=int(val_alt)-1)
        
        if novo_cap != val_cap or novo_alt != val_alt:
            inicializar_rua(rua_sel, novo_cap, novo_alt)
            st.rerun()

    # --- NOVA ÁREA: CAPACIDADE GLOBAL ---
    st.divider()
    st.header("🏢 Galpão Global")
    # O on_change garante que salve assim que você alterar o número
    st.session_state.cap_total_galpao = st.number_input(
        "Capacidade Total do Galpão", 
        min_value=1, 
        max_value=100000, 
        value=int(st.session_state.cap_total_galpao),
        step=50,
        on_change=salvar_dados
    )
    
    st.divider()
    if st.button("☁️ FORÇAR SALVAMENTO", type="primary"):
        salvar_dados()

# --- CONTEÚDO PRINCIPAL ---
st.title(f"🚜 Gestão: {rua_sel}")

# Busca
busca = st.text_input("🔍 Buscar Lote/Cliente:", placeholder="Digite...")
if busca:
    res = st.session_state.estoque[
        st.session_state.estoque['Lote'].astype(str).str.contains(busca, case=False) | 
        st.session_state.estoque['Cliente'].astype(str).str.contains(busca, case=False)
    ]
    if not res.empty:
        st.success(f"Encontrado em: {', '.join(res['Rua'].unique())}")
        st.dataframe(res[['Rua', 'ID', 'Lote', 'Cliente']], hide_index=True)

# Métricas
df_atual = st.session_state.estoque[st.session_state.estoque['Rua'] == rua_sel]
cap_rua = st.session_state.config_ruas[rua_sel].get('cap', 41)
qtd_vazio = len(df_atual[df_atual['Status'] == 'Vazio']) if not df_atual.empty else cap_rua
qtd_disp = len(df_atual[df_atual['Status'] == 'Disponível']) if not df_atual.empty else 0
qtd_res = len(df_atual[df_atual['Status'] == 'Reservado']) if not df_atual.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Capacidade", cap_rua)
c2.metric("Livres", qtd_vazio)
c3.metric("Disponíveis", qtd_disp)
c4.metric("Reservados", qtd_res)

# Barra Global (Calculada com a nova capacidade global)
ocupados_global = len(st.session_state.estoque[st.session_state.estoque['Status'].isin(['Disponível', 'Reservado'])]) if not st.session_state.estoque.empty else 0
perc = (ocupados_global / st.session_state.cap_total_galpao) * 100
st.progress(min(perc/100, 1.0))
st.caption(f"Ocupação Global do Galpão: {perc:.1f}% ({ocupados_global} de {st.session_state.cap_total_galpao})")

st.divider()

# --- OPERAÇÕES ---
tab_ent, tab_res, tab_sai = st.tabs(["📥 ENTRADA", "🟠 RESERVA", "⚪ SAÍDA"])

with tab_ent:
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: lote_in = st.text_input("📦 Lote")
    with c2: val_in = st.date_input("📅 Validade")
    with c3: qtd_in = st.number_input("🔢 Qtd", 1, max(1, qtd_vazio if qtd_vazio > 0 else 1), value=1)
    
    if st.button("📥 Confirmar Entrada", type="primary"):
        if qtd_vazio < qtd_in: st.error("Cheio!")
        else:
            # Ordena numérica para preencher corretamente
            vagas = df_atual[df_atual['Status'] == 'Vazio'].sort_values(by=['Fileira', 'Nivel'], ascending=[False, True])
            agora = datetime.now().strftime("%d/%m %H:%M")
            for i in range(int(qtd_in)):
                idx = vagas.index[i]
                st.session_state.estoque.at[idx, 'Lote'] = str(lote_in)
                st.session_state.estoque.at[idx, 'Validade'] = val_in
                st.session_state.estoque.at[idx, 'Status'] = 'Disponível'
                st.session_state.estoque.at[idx, 'Data_Entrada'] = agora
            salvar_dados()
            st.rerun()

with tab_res:
    c1, c2 = st.columns([3, 1])
    with c1: cli_res = st.text_input("👤 Cliente")
    with c2: qtd_res_in = st.number_input("🔢 Reservar", 1, max(1, qtd_disp if qtd_disp > 0 else 1), value=1)
    
    if st.button("🟠 Reservar"):
        if not cli_res: st.warning("Digite o cliente")
        else:
            # Ordenação numérica correta do ID
            disp = df_atual[df_atual['Status'] == 'Disponível'].copy()
            disp['ID_NUM'] = pd.to_numeric(disp['ID'], errors='coerce')
            disp = disp.sort_values(by='ID_NUM')
            
            for i in range(int(qtd_res_in)):
                idx = disp.index[i]
                st.session_state.estoque.at[idx, 'Status'] = 'Reservado'
                st.session_state.estoque.at[idx, 'Cliente'] = str(cli_res).upper()
            salvar_dados()
            st.rerun()

with tab_sai:
    c1, c2 = st.columns([1, 2])
    with c2: modo = st.radio("Regra:", ["Somente Reservados", "Saída Direta"], horizontal=True)
    
    if modo == "Somente Reservados":
        limite_saida = qtd_res
        aviso = "Nada reservado."
    else:
        limite_saida = qtd_disp + qtd_res
        aviso = "Rua vazia."
        
    with c1: 
        if limite_saida > 0:
            qtd_out = st.number_input("🔢 Retirar", 1, limite_saida, value=1)
        else:
            qtd_out = 0
            st.info(aviso)
    
    if st.button("⚪ Confirmar Saída"):
        if limite_saida > 0:
            filtro = ['Reservado'] if modo == "Somente Reservados" else ['Disponível', 'Reservado']
            
            # Ordenação numérica correta do ID
            alvos = df_atual[df_atual['Status'].isin(filtro)].copy()
            alvos['ID_NUM'] = pd.to_numeric(alvos['ID'], errors='coerce')
            alvos = alvos.sort_values(by='ID_NUM')
            
            if len(alvos) >= qtd_out:
                for i in range(int(qtd_out)):
                    idx = alvos.index[i]
                    st.session_state.estoque.loc[idx, ['Lote', 'Status', 'Validade', 'Cliente', 'Data_Entrada']] = ["", "Vazio", None, "", None]
                salvar_dados()
                st.rerun()

# --- MAPA VISUAL ---
st.divider()
st.subheader("🗺️ Mapa Visual")
df_mapa = df_atual.copy()
if not df_mapa.empty:
    df_mapa['ID'] = df_mapa['ID'].astype(str)
    df_mapa['Visual'] = df_mapa['Status']
    df_mapa['Aura_FEFO'] = False
    hoje = date.today()

    # Ordenação Numérica para o Loop de Cores
    df_mapa['ID_NUM'] = pd.to_numeric(df_mapa['ID'], errors='coerce')
    df_ordem = df_mapa[df_mapa['ID'] != '--'].sort_values(by='ID_NUM')
    
    lote_ant = None
    for idx, row in df_ordem.iterrows():
        if row['Status'] in ["Disponível", "Reservado"]:
            if row['Validade'] and (row['Validade'] - hoje).days <= 180: 
                df_mapa.at[idx, 'Aura_FEFO'] = True
            
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
                borda = "border: 4px solid #FFFF00; box-shadow: inset 0 0 10px #FFFF00;" if fefo else "border: 1px solid #dee2e6;"
                
                if v == "TROCA": color = 'background-color: #007bff; color: white;' 
                elif v == "Disponível": color = 'background-color: #28a745; color: white;' 
                elif v == "Reservado": color = 'background-color: #fd7e14; color: white;' 
                elif v == "Vazio": color = 'background-color: #e9ecef; color: #333;' 
                else: color = 'background-color: transparent; color: transparent; border: none;' 
                
                style_df.loc[r, c] = f'{color} {borda} font-size: 10px; font-weight: bold; text-align: center; height: 85px; min-width: 105px; white-space: pre-wrap; border-radius: 8px;'
        return style_df

    st.table(mapa_t[sorted(mapa_t.columns, reverse=True)].sort_index(ascending=False).style.apply(style_fn, axis=None))

# --- TABELA DETALHADA ---
st.divider()
st.subheader("📋 Relatório")
if not df_mapa.empty:
    df_mapa['ID_NUM'] = pd.to_numeric(df_mapa['ID'], errors='coerce')
    df_conf = df_mapa[df_mapa['Status'] != "Vazio"].sort_values(by='ID_NUM').copy()
    if not df_conf.empty:
        df_conf['Status FEFO'] = df_conf['Aura_FEFO'].apply(lambda x: "⚠️ VENCENDO" if x else "✅ OK")
        st.dataframe(
            df_conf[['ID', 'Lote', 'Validade', 'Status', 'Cliente', 'Data_Entrada', 'Status FEFO']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Validade": st.column_config.DateColumn("Validade", format="DD/MM/YYYY"),
                "Status FEFO": st.column_config.TextColumn("Vencimento")
            }
        )
