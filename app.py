import streamlit as st
import pandas as pd
from supabase import create_client

# -------------------------
# CONFIG SUPABASE
# -------------------------
url = "https://pbogddjphxhilwiqbulq.supabase.co"
key = "sb_publishable_ABtEce9FyxzepSoAkQstWw_zLnRbJrr"

supabase = create_client(url, key)

# -------------------------
# LISTA DE ESTAMPAS (GENERACIÓN AUTOMÁTICA)
# -------------------------
prefijos = [
    "PANINI", "WC", "MEX", "RSA", "CZE", "BIH", "SUI", "MARR", "SCO", "PAR", 
    "TUR", "CUW", "ECU", "JPN", "TUN", "BEL", "IRN", "ESP", "KSA", "FRA", 
    "IRQ", "ARG", "AUT", "POR", "UZB", "ENG", "GHA", "FWC", "KOR", "CAN", 
    "QAT", "BRA", "HAI", "USA", "AUS", "GER", "CIV", "NED", "SWE", "CC", 
    "EGY", "NZL", "CPV", "URU", "SEN", "NOR", "ALG", "JOR", "COD", "COL", 
    "CRO", "PAN"
]

stickers = []
for p in prefijos:
    # Determinamos el límite para que no se salte números
    # range(1, 21) genera del 1 al 20
    if p in ["PANINI", "WC", "FWC"]:
        limite = 20 
    else:
        limite = 21 

    for i in range(1, limite):
        # Lógica de nombrado: PANINI-1, PANINI-2... vs MEX1, MEX2...
        codigo = f"{p}-{i}" if p == "PANINI" else f"{p}{i}"
        stickers.append(codigo)

# Estampa especial inicial
if "PANINI-00" not in stickers: 
    stickers.insert(0, "PANINI-00")

# -------------------------
# UI - INTERFAZ DE USUARIO
# -------------------------
st.set_page_config(page_title="Álbum Panini PRO", page_icon="📘")
st.title("📘 Álbum Panini PRO")

user = st.text_input("👤 Usuario", placeholder="Escribe tu nombre...")

if user == "":
    st.warning("Pon tu nombre para empezar")
    st.stop()

# -------------------------
# CARGAR DATOS DEL USUARIO
# -------------------------
response = supabase.table("album").select("*").eq("user_id", user).execute()
data = response.data

# -------------------------
# SI EL USUARIO NO TIENE ÁLBUM → CREARLO (OPTIMIZADO)
# -------------------------
if len(data) == 0:
    with st.spinner("🚀 Generando álbum completo... esto será rápido"):
        # Preparamos todas las filas en una lista (Bulk Insert)
        batch_stickers = [
            {"user_id": user, "estampa": s, "tengo": 0, "repetidas": 0} 
            for s in stickers
        ]
        
        # Enviamos TODO de un solo golpe
        supabase.table("album").insert(batch_stickers).execute()

    st.success("¡Álbum creado exitosamente!")
    # Recargar datos después de la inserción
    response = supabase.table("album").select("*").eq("user_id", user).execute()
    data = response.data

df = pd.DataFrame(data)

# -------------------------
# MÉTRICAS PRINCIPALES
# -------------------------
tienes = df["tengo"].sum()
total = len(df)
faltan = total - tienes

col1, col2, col3 = st.columns(3)
col1.metric("Tienes", int(tienes))
col2.metric("Faltan", int(faltan))
col3.metric("% Completado", f"{(tienes/total)*100:.2f}%")

# -------------------------
# EDITAR ESTAMPAS
# -------------------------
st.divider()
st.subheader("📝 Gestionar Estampas")

# Ordenamos los códigos para que sea fácil buscarlos
lista_codigos = sorted(df["estampa"].unique())
selected = st.selectbox("Busca o selecciona una estampa", lista_codigos)

# Obtener datos de la estampa seleccionada
row = df[df["estampa"] == selected]
idx = row.index[0]

c1, c2 = st.columns(2)
with c1:
    tengo = st.checkbox("La tengo", value=bool(df.at[idx, "tengo"]))
with c2:
    reps = st.number_input("Cantidad de repetidas", value=int(df.at[idx, "repetidas"]), min_value=0)

if st.button("Guardar cambios", use_container_width=True):
    supabase.table("album").update({
        "tengo": int(tengo),
        "repetidas": reps
    }).eq("user_id", user).eq("estampa", selected).execute()
    
    st.toast(f"¡{selected} actualizada!")
    st.rerun()

# -------------------------
# VISUALIZACIÓN DE TABLAS
# -------------------------
st.divider()
tab1, tab2 = st.tabs(["❌ Faltantes", "🔁 Repetidas"])

with tab1:
    st.write(f"Te faltan {int(faltan)} estampas")
    df_faltantes = df[df["tengo"] == 0][["estampa"]]
    st.dataframe(df_faltantes, use_container_width=True, hide_index=True)

with tab2:
    df_repetidas = df[df["repetidas"] > 0][["estampa", "repetidas"]]
    st.write(f"Tienes {len(df_repetidas)} modelos repetidos")
    st.dataframe(df_repetidas, use_container_width=True, hide_index=True)
