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
# GENERACIÓN EXACTA DE ESTAMPAS
# -------------------------
paises = [
    "MEX", "RSA", "CZE", "BIH", "SUI", "MARR", "SCO", "PAR", 
    "TUR", "CUW", "ECU", "JPN", "TUN", "BEL", "IRN", "ESP", "KSA", "FRA", 
    "IRQ", "ARG", "AUT", "POR", "UZB", "ENG", "GHA", "KOR", "CAN", 
    "QAT", "BRA", "HAI", "USA", "AUS", "GER", "CIV", "NED", "SWE", 
    "EGY", "NZL", "CPV", "URU", "SEN", "NOR", "ALG", "JOR", "COD", "COL", 
    "CRO", "PAN"
]

stickers = []

# 1. PANINI 00 (Única en su tipo)
stickers.append("PANINI 00")

# 2. WC (Del 1 al 8)
for i in range(1, 9):
    stickers.append(f"WC {i}")

# 3. FWC (Del 9 al 19)
for i in range(9, 20):
    stickers.append(f"FWC{i}")

# 4. CC (Del 1 al 14)
for i in range(1, 15):
    stickers.append(f"CC{i}")

# 5. Países (1 al 20)
for p in paises:
    for i in range(1, 21):
        stickers.append(f"{p}{i}")

# -------------------------
# UI - INTERFAZ
# -------------------------
st.set_page_config(page_title="Álbum Panini PRO", page_icon="📘")
st.title("📘 Álbum Panini PRO")

user_input = st.text_input("👤 Usuario", placeholder="Escribe tu nombre...")
user = user_input.strip().lower()

if user == "":
    st.warning("Escribe tu nombre para cargar tu álbum.")
    st.stop()

# -------------------------
# LÓGICA DE BASE DE DATOS
# -------------------------
response = supabase.table("album").select("*").eq("user_id", user).execute()
data = response.data

# CREACIÓN MASIVA SI EL USUARIO ES NUEVO
if len(data) == 0:
    with st.spinner(f"🚀 Creando álbum de {len(stickers)} estampas para {user}..."):
        batch = [
            {"user_id": user, "estampa": s, "tengo": 0, "repetidas": 0} 
            for s in stickers
        ]
        # Inserción por bloques para estabilidad
        for i in range(0, len(batch), 500):
            supabase.table("album").insert(batch[i:i+500]).execute()
            
    st.success("¡Álbum generado con los rangos correctos!")
    response = supabase.table("album").select("*").eq("user_id", user).execute()
    data = response.data

df = pd.DataFrame(data)

# -------------------------
# MÉTRICAS
# -------------------------
tienes = df["tengo"].sum()
total_album = len(df)
faltan = total_album - tienes

c1, c2, c3 = st.columns(3)
c1.metric("Tienes", int(tienes))
c2.metric("Faltan", int(faltan))
c3.metric("%", f"{(tienes/total_album)*100:.2f}%")

# -------------------------
# GESTIÓN
# -------------------------
st.divider()
# Orden natural para que PANINI 00 salga primero
lista_ordenada = sorted(df["estampa"].unique(), key=lambda x: (x.split()[0] if ' ' in x else x))
selected = st.selectbox("🔍 Buscar estampa", lista_ordenada)

row = df[df["estampa"] == selected]
idx = row.index[0]

col_a, col_b = st.columns(2)
with col_a:
    tengo = st.checkbox("La tengo", value=bool(df.at[idx, "tengo"]))
with col_b:
    reps = st.number_input("Repetidas", value=int(df.at[idx, "repetidas"]), min_value=0)

if st.button("Guardar Cambios", use_container_width=True):
    supabase.table("album").update({
        "tengo": int(tengo),
        "repetidas": reps
    }).eq("user_id", user).eq("estampa", selected).execute()
    st.rerun()

# -------------------------
# TABLAS
# -------------------------
t1, t2 = st.tabs(["❌ Faltantes", "🔁 Repetidas"])
with t1:
    st.dataframe(df[df["tengo"] == 0][["estampa"]], use_container_width=True, hide_index=True)
with t2:
    st.dataframe(df[df["repetidas"] > 0][["estampa", "repetidas"]], use_container_width=True, hide_index=True)
