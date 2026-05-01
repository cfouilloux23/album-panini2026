import streamlit as st
import pandas as pd
from supabase import create_client

# -------------------------
# CONFIG SUPABASE
# -------------------------
# Se eliminó el "/rest/v1/" de la URL para evitar errores de conexión
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
    # Ajuste de rangos: la mayoría son 1-20
    limite = 21 if p not in ["PANINI", "WC", "FWC"] else 20 
    for i in range(1, limite):
        codigo = f"{p}-{i}" if p == "PANINI" else f"{p}{i}"
        stickers.append(codigo)

# Agregar la estampa especial 00
if "PANINI-00" not in stickers: 
    stickers.insert(0, "PANINI-00")

# -------------------------
# UI
# -------------------------
st.title("📘 Álbum Panini PRO")

user = st.text_input("👤 Usuario")

if user == "":
    st.warning("Pon tu nombre para empezar")
    st.stop()

# -------------------------
# CARGAR DATOS DEL USUARIO
# -------------------------
# Línea 78 corregida para filtrar por usuario
response = supabase.table("album").select("*").eq("user_id", user).execute()
data = response.data

# -------------------------
# SI EL USUARIO NO TIENE ÁLBUM → CREARLO
# -------------------------
if len(data) == 0:
    st.info("Creando tu álbum por primera vez, espera un momento...")
    for s in stickers:
        supabase.table("album").insert({
            "user_id": user,
            "estampa": s,
            "tengo": 0,
            "repetidas": 0
        }).execute()

    # Recargar datos después de la inserción
    response = supabase.table("album").select("*").eq("user_id", user).execute()
    data = response.data

df = pd.DataFrame(data)

# -------------------------
# MÉTRICAS
# -------------------------
tienes = df["tengo"].sum()
total = len(df)
faltan = total - tienes

col1, col2, col3 = st.columns(3)

col1.metric("Tienes", int(tienes))
col2.metric("Faltan", int(faltan))
col3.metric("%", f"{(tienes/total)*100:.2f}%")

# -------------------------
# EDITAR ESTAMPAS
# -------------------------
st.divider()
selected = st.selectbox("🔍 Selecciona estampa", df["estampa"].unique())

row = df[df["estampa"] == selected]
idx = row.index[0]

# Interfaz para actualizar estado
tengo = st.checkbox("La tengo", value=bool(df.at[idx, "tengo"]))
reps = st.number_input("Repetidas", value=int(df.at[idx, "repetidas"]), min_value=0)

if st.button("Guardar Cambios"):
    supabase.table("album").update({
        "tengo": int(tengo),
        "repetidas": reps
    }).eq("user_id", user).eq("estampa", selected).execute()
    
    st.success(f"¡{selected} actualizada! Refrescando...")
    st.rerun()

# -------------------------
# TABLAS DE CONTROL
# -------------------------
tab1, tab2 = st.tabs(["❌ Faltantes", "🔁 Repetidas"])

with tab1:
    st.subheader("Estampas que te faltan")
    st.dataframe(df[df["tengo"] == 0][["estampa"]])

with tab2:
    st.subheader("Tus repetidas para cambiar")
    st.dataframe(df[df["repetidas"] > 0][["estampa", "repetidas"]])
