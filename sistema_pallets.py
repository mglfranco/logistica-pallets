import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import string
import time
import io # Import para criar o arquivo Excel na memória

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Logística Pro - Master", page_icon="🚜")

# --- BANCO DE DADOS DE PRODUTOS (Extraído das Imagens) ---
# Formato: SKU: {'nome': '', 'camadas': 0, 'lastro': 0, 'total': 0}
# Lastro = Quantidade por camada
DB_PRODUTOS = {
    # IMAGEM 1
    "10033": {"nome": "OPA PILSEN 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "10001": {"nome": "OPA PILSEN 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "20101": {"nome": "OPA PILSEN 269ML", "camadas": 12, "lastro": 28, "total": 336},
    "22571": {"nome": "OPA MERECIDA EXTRA 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "10094": {"nome": "OPA MERECIDA 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "10092": {"nome": "OPA MERECIDA 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "10049": {"nome": "OPA IPA 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "10011": {"nome": "OPA IPA 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "12103": {"nome": "OPA RADLER 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "10051": {"nome": "OPA COQUETEL 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "10070": {"nome": "OPA COQUETEL 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "15118": {"nome": "OPA GERMAN LAGER 350ML - KOCH", "camadas": 10, "lastro": 28, "total": 280},
    "15108": {"nome": "OPA GERMAN LAGER 600ML - KOCH", "camadas": 6, "lastro": 15, "total": 90},
    "20113": {"nome": "OPA GERMAN LAGER 269ML", "camadas": 12, "lastro": 28, "total": 336},
    "70003": {"nome": "GERMAN LAGER SEM GLÚTEN 355ML", "camadas": 6, "lastro": 22, "total": 132},
    "10121": {"nome": "OPA GERMAN LAGER 600ML", "camadas": 6, "lastro": 15, "total": 90},
    "17001": {"nome": "OPA JOINVILLE BIER 600ML", "camadas": 6, "lastro": 15, "total": 90},
    "10098": {"nome": "OPA BRASILEIRA 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "10096": {"nome": "OPA BRASILEIRA 600ML", "camadas": 6, "lastro": 15, "total": 90},
    "10045": {"nome": "OPA PARQUE 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "10029": {"nome": "OPA PARQUE 600ML", "camadas": 5, "lastro": 15, "total": 75},
    
    # IMAGEM 2
    "10115": {"nome": "OPA PREMIUM LAGER PARQUE 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "10111": {"nome": "OPA PREMIUM LAGER PARQUE 600ML", "camadas": 6, "lastro": 15, "total": 90},
    "15021": {"nome": "OPA HEFE WEIZEN 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "15013": {"nome": "OPA KRISTAL WEIZEN 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "15007": {"nome": "OPA DUNKEL WEIZEN 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "10003": {"nome": "OPA PORTER 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "10009": {"nome": "OPA OLD ALE 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "10007": {"nome": "OPA PALE ALE 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "10021": {"nome": "OPA STRONG GOLDEN ALE 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "46001": {"nome": "OPA HOP LAGER 355ML", "camadas": 6, "lastro": 22, "total": 132},
    "40116": {"nome": "OPA HOP LAGER SEM ÁLCOOL 355ML", "camadas": 6, "lastro": 22, "total": 132},
    "15005": {"nome": "POWER TRADICIONAL 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "15019": {"nome": "POWER SEM AÇÚCARES 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "15040": {"nome": "POWER AÇAÍ 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "15044": {"nome": "POWER MELANCIA 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "15046": {"nome": "POWER MAÇÃ VERDE 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "15048": {"nome": "POWER FRUTAS VERMELHAS 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "15050": {"nome": "POWER FRUTAS TROPICAIS 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "15068": {"nome": "POWER TANGERINA 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "15042": {"nome": "POWER PITAYA 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "19009": {"nome": "POWER MORANGO 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "15090": {"nome": "POWER TRADICIONAL 2LT", "camadas": 4, "lastro": 20, "total": 80},

    # IMAGEM 3
    "90009": {"nome": "MORMAII AÇAÍ 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "10201": {"nome": "POWER TRADICIONAL 350ML (C/6)", "camadas": 10, "lastro": 56, "total": 560},
    "10202": {"nome": "POWER SEM AÇÚCARES 350ML (C/6)", "camadas": 10, "lastro": 56, "total": 560},
    "10203": {"nome": "POWER AÇAÍ 350ML (C/6)", "camadas": 10, "lastro": 56, "total": 560},
    "10204": {"nome": "POWER MELANCIA 350ML (C/6)", "camadas": 10, "lastro": 56, "total": 560},
    "10205": {"nome": "POWER MAÇÃ VERDE 350ML (C/6)", "camadas": 10, "lastro": 56, "total": 560},
    "10206": {"nome": "POWER FRU. VERMELHAS 350ML (C/6)", "camadas": 10, "lastro": 56, "total": 560},
    "10207": {"nome": "POWER FRUT. TROPICAIS 350ML (C/6)", "camadas": 10, "lastro": 56, "total": 560},
    "10208": {"nome": "POWER TANGERINA 350ML (C/6)", "camadas": 10, "lastro": 56, "total": 560},
    "10209": {"nome": "POWER PITAYA 350ML (C/6)", "camadas": 10, "lastro": 56, "total": 560},
    "22189": {"nome": "POWER MORANGO 350ML (C/6)", "camadas": 10, "lastro": 56, "total": 560},
    "60082": {"nome": "SODA CITRUS 269ML (C/6)", "camadas": 12, "lastro": 56, "total": 672},
    "60086": {"nome": "SODA MAÇÃ V. E FRAMB. 269ML (C/6)", "camadas": 12, "lastro": 56, "total": 672},
    "60083": {"nome": "SODA ABAC. E HORTELÃ 269ML (C/6)", "camadas": 12, "lastro": 56, "total": 672},
    "60084": {"nome": "SODA ABACAXI E COCO 269ML (C/6)", "camadas": 12, "lastro": 56, "total": 672},
    "60085": {"nome": "SODA CHÁ M. E PÊSSEGO 269ML (C/6)", "camadas": 12, "lastro": 56, "total": 672},
    "60087": {"nome": "SODA SEM AROMA 269ML (C/6)", "camadas": 12, "lastro": 56, "total": 672},
    "90151": {"nome": "PX PULSAR SEM AÇÚCARES 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "14005": {"nome": "OPA PREMIUM LAGER 355ML - EXP", "camadas": 6, "lastro": 22, "total": 132},
    "14007": {"nome": "OPA IPA 600ML - EXPORTAÇÃO", "camadas": 5, "lastro": 15, "total": 75},
    "15033": {"nome": "OPA PILSEN 473ML - EXPORTAÇÃO", "camadas": 10, "lastro": 22, "total": 220},
    "20154": {"nome": "OPA BRASILEIRA 473ML - EXP", "camadas": 10, "lastro": 22, "total": 220},

    # IMAGEM 4
    "19001": {"nome": "POWER TRADICIONAL JEC 2LT", "camadas": 4, "lastro": 20, "total": 80},
    "15092": {"nome": "POWER SEM AÇÚCARES 2LT", "camadas": 4, "lastro": 20, "total": 80},
    "19003": {"nome": "POWER SEM AÇÚCARES JEC 2LT", "camadas": 4, "lastro": 20, "total": 80},
    "15100": {"nome": "POWER MAÇÃ VERDE 2LT", "camadas": 4, "lastro": 20, "total": 80},
    "19005": {"nome": "POWER MAÇÃ VERDE JEC 2LT", "camadas": 4, "lastro": 20, "total": 80},
    "15102": {"nome": "POWER FRUTAS VERMELHAS 2LT", "camadas": 4, "lastro": 20, "total": 80},
    "19007": {"nome": "POWER FRUTAS VERMELHAS JEC 2LT", "camadas": 4, "lastro": 20, "total": 80},
    "60039": {"nome": "OPA REFRI LARANJINHA 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "60037": {"nome": "OPA REFRI GUARANÁ 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "60041": {"nome": "OPA REFRI LIMÃO 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "60035": {"nome": "OPA REFRI FRUT. VERMELHAS 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "60043": {"nome": "OPA REFRI UVA 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "60005": {"nome": "OPA REFRI LARANJINHA 600ML", "camadas": 6, "lastro": 15, "total": 90},
    "60007": {"nome": "OPA REFRI GUARANÁ 600ML", "camadas": 6, "lastro": 15, "total": 90},
    "60003": {"nome": "OPA REFRI LIMÃO 600ML", "camadas": 6, "lastro": 15, "total": 90},
    "60009": {"nome": "OPA REFRI FRUT. VERMELHAS 600ML", "camadas": 6, "lastro": 15, "total": 90},
    "60045": {"nome": "OPA REFRI UVA 600ML", "camadas": 6, "lastro": 15, "total": 90},
    "60069": {"nome": "OPA REFRI ÁGUA TÔNICA 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "15141": {"nome": "OPA VODKA 220ML", "camadas": 13, "lastro": 28, "total": 364},
    "90001": {"nome": "MORMAII TRADICIONAL 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "90003": {"nome": "MORMAII ZERO AÇÚCARES 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "90007": {"nome": "MORMAII MELANCIA 350ML", "camadas": 10, "lastro": 28, "total": 280},

    # IMAGEM 5
    "40010": {"nome": "OPA PILSEN 269ML - EXPORTAÇÃO", "camadas": 12, "lastro": 28, "total": 336},
    "40026": {"nome": "OPA PILSEN 600ML - EXPORTAÇÃO", "camadas": 5, "lastro": 15, "total": 75},
    "40003": {"nome": "OPA PREMIUM LAGER 269ML - EXP", "camadas": 12, "lastro": 28, "total": 336},
    "40005": {"nome": "OPA PREMIUM LAGER 600ML - EXP", "camadas": 6, "lastro": 15, "total": 90},
    "70005": {"nome": "GERMAN LAGER S. GLÚTEN 355 - EXP", "camadas": 6, "lastro": 22, "total": 132},
    "15025": {"nome": "CERVEJA JERKE 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "10084": {"nome": "CERVEJA KENTUCKY 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "10113": {"nome": "OPA PREMIUM LAGER PARQUE 355ML", "camadas": 6, "lastro": 22, "total": 132},
    "10119": {"nome": "OPA AMERICAN LAGER 355ML", "camadas": 6, "lastro": 22, "total": 132},
    "10074": {"nome": "OPA PILSEN 473ML - LATÃO", "camadas": 10, "lastro": 22, "total": 220},
    "10076": {"nome": "OPA PARQUE 473ML - LATÃO", "camadas": 10, "lastro": 22, "total": 220},
    "40114": {"nome": "OPA BRASILEIRA 473ML - LATÃO", "camadas": 10, "lastro": 22, "total": 220},
    "14001": {"nome": "CERVEJA CATARINA LAGER 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "15036": {"nome": "CERVEJA DINKEL 2MALTES 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "15130": {"nome": "CERVEJA CORUJA LAGER 350ML", "camadas": 13, "lastro": 22, "total": 286},
    "15126": {"nome": "OPA SESSION IPA 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "15015": {"nome": "OPA ENGLISH IPA 600ML", "camadas": 5, "lastro": 15, "total": 75},
    "15116": {"nome": "OPA GERMAN LAGER 355ML - KOCH", "camadas": 6, "lastro": 22, "total": 132},
    "17451": {"nome": "BODEBROWN GERMAN LAGER 473ML", "camadas": 10, "lastro": 22, "total": 220},
    "20216": {"nome": "BODEBROWN EASY LAGER 473ML", "camadas": 10, "lastro": 22, "total": 220},
    "20108": {"nome": "OPA EISBOCK 500ML", "camadas": 6, "lastro": 7, "total": 42},
    "22432": {"nome": "MAUY TRADICIONAL 269ML", "camadas": 12, "lastro": 28, "total": 336},

    # IMAGEM 6 (Alguns itens repetidos ou versões C/6)
    "22431": {"nome": "MAUY TRADICIONAL 269ML (C/6)", "camadas": 12, "lastro": 56, "total": 672},
    "40122": {"nome": "OPA ICE MORANGO 269ML", "camadas": 12, "lastro": 28, "total": 336},
    "40121": {"nome": "OPA ICE MORANGO 269ML (C/6)", "camadas": 12, "lastro": 56, "total": 672},
    "22832": {"nome": "PICHAU ORIGINAL 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "22835": {"nome": "PICHAU ZERO AÇÚCARES 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "22838": {"nome": "PICHAU TROPICAL 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "23752": {"nome": "PICHAU MAÇÃ VERDE 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "20117": {"nome": "MAGIC OZ SEM AÇÚCARES 350ML", "camadas": 10, "lastro": 28, "total": 280},
    "24201": {"nome": "MAGIC OZ MARACUJÁ S/A 350ML", "camadas": 10, "lastro": 28, "total": 280},
}

# --- CSS PERSONALIZADO ---
st.markdown("""
    <style>
    /* Cards de Métricas */
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        border: 1px solid #dcdcdc;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetric"] label {
        color: #555;
    }
    
    /* Botões */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 48px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* Tabela Visual do Mapa */
    .stTable { 
        font-family: 'Courier New', monospace; 
        font-size: 0.8rem;
    }
    
    /* Ajuste de Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 5px 5px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 2px solid #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TENTA IMPORTAR A CONEXÃO COM GOOGLE SHEETS ---
try:
    from streamlit_gsheets import GSheetsConnection
    if "gsheets" in st.secrets:
        GSHEETS_DISPONIVEL = True
    else:
        GSHEETS_DISPONIVEL = False
except Exception:
    GSHEETS_DISPONIVEL = False

# --- FUNÇÕES DE BANCO DE DADOS ---
def salvar_dados():
    """Salva os dados no Session State e no Google Sheets se disponível."""
    if not GSHEETS_DISPONIVEL:
        st.toast("Salvo localmente (Sessão)", icon="💾")
        return

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        with st.spinner('Sincronizando com a nuvem...'):
            df_estoque = st.session_state.estoque.copy()
            # Converte datas para string
            if 'Validade' in df_estoque.columns:
                df_estoque['Validade'] = df_estoque['Validade'].astype(str)
            
            conn.update(worksheet="Estoque", data=df_estoque)
            
            # Salva Config Ruas (AGORA COM CHAVE COMPOSTA)
            dados_config = []
            for (g, r), v in st.session_state.config_ruas.items():
                dados_config.append({
                    'Galpao': g,
                    'Rua': r,
                    'Capacidade': v.get('cap', 41),
                    'Altura': v.get('alt', 3)
                })
            
            df_cfg = pd.DataFrame(dados_config)
            conn.update(worksheet="Config_Ruas", data=df_cfg)
            
            # Salva Config Global e Lista de Galpões
            str_galpoes = ",".join(st.session_state.lista_galpoes)
            df_g = pd.DataFrame([{"cap_galpao": st.session_state.cap_total_galpao, "lista_galpoes": str_galpoes}])
            conn.update(worksheet="Config_Global", data=df_g)
            
            st.cache_data.clear()
        st.toast("Salvo na nuvem!", icon="☁️")
    except Exception as e:
        st.error(f"Erro ao Salvar na Nuvem (Usando modo local): {e}")

def carregar_dados():
    """Carrega dados do GSheets ou inicia vazios."""
    if not GSHEETS_DISPONIVEL:
        return 
        
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Carrega Estoque
        try:
            df_e = conn.read(worksheet="Estoque", ttl=0)
            if df_e is not None and not df_e.empty:
                df_e['Validade'] = pd.to_datetime(df_e['Validade'], errors='coerce').dt.date
                df_e['ID'] = df_e['ID'].astype(str)
                df_e['Lote'] = df_e['Lote'].fillna("").astype(str)
                df_e['Cliente'] = df_e['Cliente'].fillna("").astype(str)
                # Novas Colunas
                if 'Produto' not in df_e.columns: df_e['Produto'] = ""
                if 'Qtd_Itens' not in df_e.columns: df_e['Qtd_Itens'] = 0
                if 'Galpao' not in df_e.columns: df_e['Galpao'] = "Principal"
                
                df_e['Produto'] = df_e['Produto'].fillna("").astype(str)
                df_e['Qtd_Itens'] = pd.to_numeric(df_e['Qtd_Itens'], errors='coerce').fillna(0).astype(int)
                
                st.session_state.estoque = df_e
        except Exception:
            pass

        # Carrega Config Ruas (COM CHAVE COMPOSTA)
        try:
            df_c = conn.read(worksheet="Config_Ruas", ttl=0)
            if df_c is not None and not df_c.empty:
                st.session_state.config_ruas = {} 
                for _, row in df_c.iterrows():
                    # Chave composta: (Galpao, Rua)
                    chave = (row.get('Galpao', 'Principal'), row['Rua'])
                    st.session_state.config_ruas[chave] = {
                        'cap': int(row.get('Capacidade', 41)), 
                        'alt': int(row.get('Altura', 3)),
                        'galpao': row.get('Galpao', 'Principal')
                    }
        except Exception:
            pass

        # Carrega Config Global
        try:
            df_g = conn.read(worksheet="Config_Global", ttl=0)
            if df_g is not None and not df_g.empty:
                st.session_state.cap_total_galpao = int(df_g.iloc[0]['cap_galpao'])
                if 'lista_galpoes' in df_g.columns:
                    galpoes_str = str(df_g.iloc[0]['lista_galpoes'])
                    st.session_state.lista_galpoes = [g.strip() for g in galpoes_str.split(",") if g.strip()]
        except Exception:
            pass

    except Exception:
        time.sleep(0.5)

# --- INICIALIZAÇÃO DO ESTADO ---
if 'estoque' not in st.session_state:
    st.session_state.estoque = pd.DataFrame(columns=[
        "Galpao", "Rua", "Fileira", "Nivel", "ID", "Lote", "Validade", 
        "Status", "Cliente", "Data_Entrada", "Produto", "Qtd_Itens"
    ])
    st.session_state.config_ruas = {}
    st.session_state.cap_total_galpao = 2000
    st.session_state.lista_galpoes = ["Principal"]
    st.session_state.galpao_atual = "Principal"
    carregar_dados() 

# --- LÓGICA DE GERAR RUA ---
def inicializar_rua(nome_galpao, nome_rua, capacidade, altura_max):
    """Cria a estrutura física da rua vinculada a um galpão."""
    dados = []
    id_counter = 1 
    pallets_criados = 0
    
    for f in range(1, 15): 
        altura_desta_fileira = 2 if f == 1 else altura_max
        for n in range(1, 4): 
            status = "Vazio"
            id_p = "--"
            eh_posicao_valida = False
            
            if n <= altura_desta_fileira:
                if pallets_criados < capacidade:
                    eh_posicao_valida = True
                    pallets_criados += 1
                    id_p = f"{pallets_criados:02d}"
                else:
                    status = "BLOQUEADO"
            else:
                status = "BLOQUEADO"
            
            if eh_posicao_valida: status = "Vazio"
            
            dados.append({
                "Galpao": nome_galpao, "Rua": nome_rua, 
                "Fileira": f, "Nivel": n, "ID": id_p,
                "Lote": "", "Validade": None, "Status": status, 
                "Cliente": "", "Data_Entrada": None,
                "Produto": "", "Qtd_Itens": 0
            })
    
    df_nova = pd.DataFrame(dados)
    
    # Remove dados antigos dessa rua/galpão
    if not st.session_state.estoque.empty:
        mask = (st.session_state.estoque['Rua'] == nome_rua) & (st.session_state.estoque['Galpao'] == nome_galpao)
        st.session_state.estoque = st.session_state.estoque[~mask]
    
    st.session_state.estoque = pd.concat([st.session_state.estoque, df_nova], ignore_index=True)
    
    # SALVA A CONFIGURAÇÃO USANDO CHAVE COMPOSTA (GALPAO, RUA)
    chave_config = (nome_galpao, nome_rua)
    st.session_state.config_ruas[chave_config] = {'cap': capacidade, 'alt': altura_max, 'galpao': nome_galpao}
    salvar_dados()

# --- SIDEBAR (CONTROLES) ---
with st.sidebar:
    st.title("⚙️ Painel de Controle")
    st.info(f"Modo: {'☁️ Online' if GSHEETS_DISPONIVEL else '💻 Local'}")

    # 1. Seleção de Galpão
    st.header("🏢 Galpão")
    col_g1, col_g2 = st.columns([3, 1])
    with col_g1:
        galpao_sel = st.selectbox("Selecione o Galpão", st.session_state.lista_galpoes, index=0)
        st.session_state.galpao_atual = galpao_sel
    with col_g2:
        if st.button("➕", help="Novo Galpão"):
            st.session_state.novo_galpao_mode = True
            
    if st.session_state.get('novo_galpao_mode', False):
        novo_g_nome = st.text_input("Nome do Novo Galpão")
        if st.button("Criar Galpão"):
            if novo_g_nome and novo_g_nome not in st.session_state.lista_galpoes:
                st.session_state.lista_galpoes.append(novo_g_nome)
                st.session_state.galpao_atual = novo_g_nome
                st.session_state.novo_galpao_mode = False
                salvar_dados()
                st.rerun()

    st.divider()

    # 2. Seleção de Rua (Filtrada pelo Galpão)
    st.header("📍 Rua")
    # Gera lista padrão A1..Z2
    lista_padrao = [f"Rua {l}{n}" for l in string.ascii_uppercase for n in [1, 2]]
    
    # Se quiser ruas personalizadas, poderia adicionar aqui, mas vamos usar a padrao + filtro
    rua_sel = st.selectbox("Selecione a Rua", lista_padrao)
    
    # Verifica se rua existe neste galpão, senão cria
    mask_rua = (st.session_state.estoque['Galpao'] == galpao_sel) & (st.session_state.estoque['Rua'] == rua_sel)
    if st.session_state.estoque[mask_rua].empty:
        inicializar_rua(galpao_sel, rua_sel, 41, 3)

    with st.expander("🏗️ Configurar Rua"):
        # BUSCA CONFIGURAÇÃO ESPECÍFICA DO GALPÃO ATUAL
        chave_busca = (galpao_sel, rua_sel)
        cfg_atual = st.session_state.config_ruas.get(chave_busca, {'cap': 41, 'alt': 3})
        
        novo_cap = st.number_input("Capacidade", 1, 60, int(cfg_atual['cap']))
        novo_alt = st.selectbox("Altura Máxima", [1, 2, 3], index=int(cfg_atual['alt'])-1)
        
        if st.button("Resetar Rua", type="primary"):
            inicializar_rua(galpao_sel, rua_sel, novo_cap, novo_alt)
            st.toast("Rua resetada!", icon="♻️")
            st.rerun()

    st.divider()
    if st.button("💾 Salvar Dados"):
        salvar_dados()

# --- ÁREA PRINCIPAL ---
st.title(f"🚜 {galpao_sel} > {rua_sel}")

# Dados da Rua Atual
mask_atual = (st.session_state.estoque['Galpao'] == galpao_sel) & (st.session_state.estoque['Rua'] == rua_sel)
df_atual = st.session_state.estoque[mask_atual].copy()

# Busca Capacidade (USANDO CHAVE COMPOSTA)
chave_busca_main = (galpao_sel, rua_sel)
cap_rua = st.session_state.config_ruas.get(chave_busca_main, {}).get('cap', 41)

# KPI
qtd_vazio = len(df_atual[df_atual['Status'] == 'Vazio'])
qtd_disp = len(df_atual[df_atual['Status'] == 'Disponível'])
qtd_res = len(df_atual[df_atual['Status'] == 'Reservado'])
soma_itens = df_atual['Qtd_Itens'].sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Capacidade", f"{cap_rua} Pallets")
k2.metric("Livres", qtd_vazio)
k3.metric("Ocupados", qtd_disp + qtd_res)
k4.metric("Qtd. Itens (Fardos)", int(soma_itens))

st.divider()

# --- OPERAÇÕES ---
tab_ent, tab_res, tab_edit, tab_sai, tab_rel = st.tabs([
    "📥 ENTRADA", "🟠 RESERVA", "✏️ PICAGEM / AJUSTE", "⚪ SAÍDA", "📊 RELATÓRIOS"
])

with tab_ent:
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    
    with c1:
        # Cria lista de opções combinando SKU e Nome para busca fácil
        opcoes_produtos = [""] + [f"{sku} - {dados['nome']}" for sku, dados in DB_PRODUTOS.items()]
        prod_selecionado = st.selectbox("🍺 Selecione o Produto (Busca por SKU ou Nome)", opcoes_produtos)
        
        # Lógica de autopreenchimento
        nome_auto = ""
        qtd_padrao = 0
        desc_config = "Selecione um produto"
        
        if prod_selecionado:
            sku_sel = prod_selecionado.split(" - ")[0]
            if sku_sel in DB_PRODUTOS:
                dados_prod = DB_PRODUTOS[sku_sel]
                nome_auto = dados_prod['nome']
                qtd_padrao = dados_prod['total']
                desc_config = f"Padrão: {dados_prod['camadas']} camadas x {dados_prod['lastro']} = {dados_prod['total']} fardos/cx"
    
    # Campos editáveis (caso o pallet esteja quebrado ou diferente do padrão)
    with c2: 
        lote_in = st.text_input("📦 Lote")
    with c3: 
        # Usa o valor do banco como padrão, mas permite edição
        qtd_itens_in = st.number_input("🔢 Fardos/Pallet", 0, 5000, int(qtd_padrao), help=desc_config)
        st.caption(desc_config)
    with c4: 
        qtd_pallets_in = st.number_input("🔢 Qtd Pallets", 1, max(1, qtd_vazio), 1)
    
    val_in = st.date_input("📅 Validade")
    
    if st.button("📥 Registrar Entrada", type="primary", use_container_width=True):
        if not lote_in or not prod_selecionado:
            st.error("Selecione um Produto e digite o Lote.")
        elif qtd_vazio < qtd_pallets_in:
            st.error(f"Espaço insuficiente! Vagas: {qtd_vazio}")
        else:
            # Lógica: Preenche do fundo (fileira alta) para frente
            vagas = df_atual[df_atual['Status'] == 'Vazio'].sort_values(by=['Fileira', 'Nivel'], ascending=[False, True])
            indices = vagas.index[:int(qtd_pallets_in)]
            
            agora = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Como df_atual é um slice, precisamos atualizar no dataframe original usando o índice
            idx_global = df_atual.loc[indices].index
            
            st.session_state.estoque.loc[idx_global, 'Lote'] = str(lote_in)
            st.session_state.estoque.loc[idx_global, 'Produto'] = str(nome_auto).upper()
            st.session_state.estoque.loc[idx_global, 'Qtd_Itens'] = int(qtd_itens_in)
            st.session_state.estoque.loc[idx_global, 'Validade'] = val_in
            st.session_state.estoque.loc[idx_global, 'Status'] = 'Disponível'
            st.session_state.estoque.loc[idx_global, 'Data_Entrada'] = agora
            
            salvar_dados()
            st.toast(f"{qtd_pallets_in} pallets de {nome_auto} adicionados!", icon="✅")
            st.rerun()

with tab_res:
    c1, c2 = st.columns([3, 1])
    with c1: cli_res = st.text_input("👤 Cliente")
    with c2: qtd_res_in = st.number_input("🔢 Qtd Reservar", 1, max(1, qtd_disp), 1)
    
    if st.button("🟠 Reservar"):
        if cli_res:
            disp = df_atual[df_atual['Status'] == 'Disponível'].copy()
            # Ordena ID crescente (Frente -> Fundo)
            disp['ID_N'] = pd.to_numeric(disp['ID'], errors='coerce')
            disp = disp.sort_values('ID_N')
            
            indices = disp.index[:int(qtd_res_in)]
            idx_global = df_atual.loc[indices].index
            
            st.session_state.estoque.loc[idx_global, 'Status'] = 'Reservado'
            st.session_state.estoque.loc[idx_global, 'Cliente'] = str(cli_res).upper()
            salvar_dados()
            st.rerun()

with tab_edit:
    st.info("Modifique a quantidade de itens em um pallet específico (Picagem).")
    col_e1, col_e2 = st.columns([1, 2])
    with col_e1:
        # Lista IDs ocupados na rua atual
        ids_ocupados = df_atual[df_atual['Status'].isin(['Disponível', 'Reservado'])]['ID'].unique()
        id_edit = st.selectbox("Selecione o ID do Pallet", sorted(ids_ocupados))
    
    if id_edit:
        # Pega dados atuais
        linha_edit = df_atual[df_atual['ID'] == id_edit].iloc[0]
        idx_global_edit = linha_edit.name
        
        with col_e2:
            st.write(f"**Produto:** {linha_edit['Produto']} | **Lote:** {linha_edit['Lote']}")
            nova_qtd = st.number_input("Quantidade Atual (Fardos/Dúzias)", 0, 10000, int(linha_edit['Qtd_Itens']))
            
            if st.button("💾 Atualizar Quantidade"):
                st.session_state.estoque.at[idx_global_edit, 'Qtd_Itens'] = nova_qtd
                if nova_qtd == 0:
                    st.warning("Quantidade zerada. Para liberar a vaga, use a aba 'Saída'.")
                salvar_dados()
                st.toast(f"Pallet {id_edit} atualizado para {nova_qtd} itens.", icon="✏️")
                st.rerun()

with tab_sai:
    c1, c2 = st.columns([1, 2])
    with c2: modo = st.radio("Modo:", ["Somente Reservados", "Qualquer Disponível"], horizontal=True)
    limit = qtd_res if modo == "Somente Reservados" else qtd_disp + qtd_res
    
    with c1: qtd_out = st.number_input("🔢 Qtd Pallets a Retirar", 0, limit, 0)
    
    if st.button("⚪ Confirmar Saída Total"):
        if qtd_out > 0:
            filtro = ['Reservado'] if modo == "Somente Reservados" else ['Disponível', 'Reservado']
            alvos = df_atual[df_atual['Status'].isin(filtro)].copy()
            alvos['ID_N'] = pd.to_numeric(alvos['ID'], errors='coerce')
            alvos = alvos.sort_values('ID_N') # Sai da frente primeiro
            
            indices = alvos.index[:int(qtd_out)]
            idx_global = df_atual.loc[indices].index
            
            # Limpa
            cols_limpar = ['Lote', 'Status', 'Validade', 'Cliente', 'Data_Entrada', 'Produto', 'Qtd_Itens']
            st.session_state.estoque.loc[idx_global, cols_limpar] = ["", "Vazio", None, "", None, "", 0]
            
            salvar_dados()
            st.rerun()

with tab_rel:
    st.subheader("📊 Relatórios e Pesquisa")
    
    # --- EXPORTAÇÃO EXCEL ---
    st.markdown("### 📤 Exportar Dados para Excel")
    
    if st.button("Gerar Arquivo Excel"):
        if not st.session_state.estoque.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                # Aba 1: Resumo
                df_resumo = st.session_state.estoque[st.session_state.estoque['Status'] != 'Vazio'].groupby(
                    ['Galpao', 'Produto']
                ).agg(
                    Total_Pallets=('ID', 'count'),
                    Total_Itens=('Qtd_Itens', 'sum')
                ).reset_index()
                df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
                
                # Aba 2: Detalhado (Raw Data)
                df_detalhe = st.session_state.estoque[st.session_state.estoque['Status'] != 'Vazio'].copy()
                if not df_detalhe.empty:
                    # Organiza colunas
                    colunas_export = ['Galpao', 'Rua', 'ID', 'Produto', 'Lote', 'Qtd_Itens', 'Validade', 'Status', 'Cliente', 'Data_Entrada']
                    # Garante que só exporta colunas que existem
                    colunas_existentes = [c for c in colunas_export if c in df_detalhe.columns]
                    df_detalhe[colunas_existentes].to_excel(writer, sheet_name='Detalhado', index=False)
            
            st.download_button(
                label="📥 Baixar Planilha (.xlsx)",
                data=buffer,
                file_name=f"estoque_logistica_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.ms-excel"
            )
        else:
            st.warning("O estoque está vazio, nada para exportar.")
    
    st.divider()

    # Pesquisa Global
    termo = st.text_input("🔎 Pesquisar Produto ou Lote (Em todos os galpões)")
    
    if termo:
        mask_search = (
            st.session_state.estoque['Produto'].str.contains(termo, case=False) |
            st.session_state.estoque['Lote'].str.contains(termo, case=False)
        )
        res = st.session_state.estoque[mask_search & (st.session_state.estoque['Status'] != 'Vazio')]
        
        if not res.empty:
            # Agrupa
            st.markdown(f"### Resultados para '{termo}'")
            total_pallets = len(res)
            total_itens = res['Qtd_Itens'].sum()
            
            m1, m2 = st.columns(2)
            m1.metric("Total Pallets Encontrados", total_pallets)
            m2.metric("Soma Total Itens", f"{int(total_itens)}")
            
            st.dataframe(
                res[['Galpao', 'Rua', 'ID', 'Produto', 'Lote', 'Qtd_Itens', 'Validade']],
                use_container_width=True, hide_index=True
            )
        else:
            st.warning("Nada encontrado.")
            
    st.divider()
    st.markdown("### Resumo por Galpão")
    df_all = st.session_state.estoque[st.session_state.estoque['Status'] != 'Vazio']
    if not df_all.empty:
        resumo = df_all.groupby(['Galpao', 'Produto']).agg(
            Pallets=('ID', 'count'),
            Total_Itens=('Qtd_Itens', 'sum')
        ).reset_index()
        st.dataframe(resumo, use_container_width=True)

# --- MAPA VISUAL ---
st.divider()
col_head_map, col_filter_map = st.columns([3, 1])
with col_head_map:
    st.subheader(f"🗺️ Visualização: {galpao_sel} - {rua_sel}")
with col_filter_map:
    modo_vis = st.selectbox("Colorir por:", ["Status (Padrão)", "Idade do Lote (Antigo vs Novo)"])

if not df_atual.empty:
    df_mapa = df_atual.copy()
    hoje = date.today()
    
    # Prepara dados visuais
    def get_cell_style(row):
        status = row['Status']
        prod = row['Produto']
        qtd = row['Qtd_Itens']
        lote = row['Lote']
        
        # Cor de fundo
        bg = "#f1f2f6"
        color = "#a4b0be"
        border = "1px dashed #ccc"
        
        if status == "BLOQUEADO":
            bg = "#2f3542"; color = "#57606f"; border = "none"
        elif status != "Vazio":
            # Cores baseadas no modo
            if modo_vis == "Status (Padrão)":
                if status == "Reservado": bg = "#ff9f43"
                else: bg = "#2ecc71"
                color = "white"
                border = "1px solid #ddd"
                
                # Borda vermelha se vencendo
                if row['Validade']:
                    try:
                        venc = pd.to_datetime(row['Validade']).date()
                        if (venc - hoje).days <= 180:
                            border = "3px solid #e74c3c"
                    except: pass
                    
            elif modo_vis == "Idade do Lote (Antigo vs Novo)":
                # Gradiente Azul. Mais antigo = Azul Escuro. Mais novo = Azul Claro.
                try:
                    dt_ent = pd.to_datetime(row['Data_Entrada']).date()
                    dias = (hoje - dt_ent).days
                    # Escala: 0 dias -> Claro, 365 dias -> Escuro
                    intensidade = min(dias * 2, 200) + 50 
                    bg = f"rgb(0, {255-intensidade}, {255-intensidade/2})" # Gammers blueish
                    color = "white"
                    border = "1px solid #fff"
                except:
                    bg = "#2ecc71"; color="white"

        # Texto
        if status == "Vazio":
            txt = f"🟢 VAZIO\nID:{row['ID']}"
        elif status == "BLOQUEADO":
            txt = ""
        else:
            txt = f"{prod}\nL:{lote}\nQ:{qtd}\nID:{row['ID']}"
            
        return f"""
            background-color: {bg}; color: {color}; border: {border};
            white-space: pre-wrap; text-align: center; vertical-align: middle;
            height: 90px; min-width: 90px; font-weight: bold; font-size: 11px;
            border-radius: 6px;
        """, txt

    # Aplica estilos linha a linha
    df_mapa['Style'], df_mapa['Text'] = zip(*df_mapa.apply(get_cell_style, axis=1))
    
    # Pivots
    mapa_txt = df_mapa.pivot(index='Nivel', columns='Fileira', values='Text')
    mapa_sty = df_mapa.pivot(index='Nivel', columns='Fileira', values='Style')
    
    # Render
    st.write(
        mapa_txt.sort_index(ascending=False)
        .style.apply(lambda x: mapa_sty, axis=None)
        .to_html(), 
        unsafe_allow_html=True
    )
    
    if modo_vis == "Idade do Lote (Antigo vs Novo)":
        st.caption("Legenda: Quanto mais escuro/azul, mais antigo é o lote no estoque.")
    else:
        st.caption("Legenda: 🟢 Disponível | 🟠 Reservado | 🔴 Borda Vermelha = Vencendo")
