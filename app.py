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
# GENERACIÓN DE LISTA MAESTRA (SIN BANDERAS)
# -------------------------
paises = [
    "MEX", "RSA", "CZE", "BIH", "SUI", "MARR", "SCO", "PAR", "TUR", "CUW", 
    "ECU", "JPN", "TUN", "BEL", "IRN", "ESP", "KSA", "FRA", "IRQ", "ARG", 
    "AUT", "POR", "UZB", "ENG", "GHA", "KOR", "CAN", "QAT", "BRA", "HAI", 
    "USA", "AUS", "GER", "CIV", "NED", "SWE", "EGY", "NZL", "CPV", "URU", 
    "SEN", "NOR", "ALG", "JOR", "COD", "COL", "CRO", "PAN"
]

secciones_master = {
    "ESPECIALES": ["PANINI 00"] + [f"WC {i}" for i in range(1, 9)] + [f"FWC{i}" for i in range(9, 20)],
    "COPA CONFEDERACIONES": [f"CC{i}" for i in range(1, 15)]
}
for p in paises:
    secciones_master[p] = [f"{p}{i}" for i in range(1, 21)]

# -------------------------
# UI INICIAL
# -------------------------
st.set_page_config(page_title="Álbum Pro 2026", layout="wide")
st.title("📘 Gestión de Álbum 2026")

user_input = st.text_input("👤 Usuario", placeholder="Escribe tu nombre...")
user = user_input.strip().lower()

if not user:
    st.info("Ingresa tu nombre para ver tus datos.")
    st.stop()

# -------------------------
# DATA LOGIC
# -------------------------
response = supabase.table("album").select("*").eq("user_id", user).execute()
data = response.data

if len(data) == 0:
    with st.spinner("Creando álbum inicial..."):
        all_stickers = []
        for l in secciones_master.values(): all_stickers.extend(l)
        batch = [{"user_id": user, "estampa": s, "tengo": 0, "repetidas": 0} for s in all_stickers]
        for i in range(0, len(batch), 500): 
            supabase.table("album").insert(batch[i:i+500]).execute()
    st.rerun()

df = pd.DataFrame(data)

# Métricas
t1, t2, t3 = st.columns(3)
t1.metric("Tienes", int(df["tengo"].sum()))
t2.metric("Repetidas Totales", int(df["repetidas"].sum()))
t3.metric("Faltantes", int(len(df) - df["tengo"].sum()))

st.warning("⚠️ Recuerda darle al botón 'GUARDAR TODOS LOS CAMBIOS' al final antes de salir.")

# -------------------------
# INTERFAZ CHECKLIST
# -------------------------
cambios_tengo = {}
cambios_reps = {}

for seccion, lista in secciones_master.items():
    with st.expander(seccion):
        cols = st.columns(4)
        for i, cod in enumerate(lista):
            # Buscar info actual
            info = df[df["estampa"] == cod].iloc[0]
            with cols[i % 4]:
                st.write(f"**{cod}**")
                c_t, c_r = st.columns([1, 1.2])
                with c_t:
                    t = st.checkbox("T", value=bool(info["tengo"]), key=f"t_{cod}", label_visibility="collapsed")
                    cambios_tengo[cod] = 1 if t else 0
                with c_r:
                    r = st.number_input("R", min_value=0, value=int(info["repetidas"]), key=f"r_{cod}", label_visibility="collapsed")
                    cambios_reps[cod] = r
                st.write("---")

# -------------------------
# BOTÓN GUARDAR
# -------------------------
st.divider()
if st.button("💾 GUARDAR TODOS LOS CAMBIOS", use_container_width=True, type="primary"):
    with st.spinner("Guardando en la nube..."):
        for cod in cambios_tengo.keys():
            nt, nr = cambios_tengo[cod], cambios_reps[cod]
            ot, or_old = int(df[df["estampa"] == cod]["tengo"].iloc[0]), int(df[df["estampa"] == cod]["repetidas"].iloc[0])
            
            # Solo actualizamos si hubo cambios para que sea más rápido
            if nt != ot or nr != or_old:
                supabase.table("album").update({"tengo": nt, "repetidas": nr}).eq("user_id", user).eq("estampa", cod).execute()
    st.success("¡Datos guardados! 🔥")
    st.rerun()

# -------------------------
# LISTA DE REPETIDAS
# -------------------------
st.subheader("🔁 Tus Repetidas")
df_reps = df[df["repetidas"] > 0][["estampa", "repetidas"]]
if not df_reps.empty:
    st.table(df_reps)
else:
    st.write("No tienes repetidas marcadas aún.")
