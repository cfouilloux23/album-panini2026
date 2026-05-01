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
# GENERACIÓN DE LISTA MAESTRA (Rangos solicitados)
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
st.title("📋 Gestión Total: Checklist y Repetidas")

user_input = st.text_input("👤 Usuario", placeholder="Tu nombre...")
user = user_input.strip().lower()

if not user:
    st.warning("Ingresa tu nombre para continuar.")
    st.stop()

# -------------------------
# DATA LOGIC
# -------------------------
response = supabase.table("album").select("*").eq("user_id", user).execute()
data = response.data

if len(data) == 0:
    with st.spinner("Generando álbum inicial..."):
        all_stickers = []
        for s_list in secciones_master.values():
            all_stickers.extend(s_list)
        
        batch = [{"user_id": user, "estampa": s, "tengo": 0, "repetidas": 0} for s in all_stickers]
        for i in range(0, len(batch), 500):
            supabase.table("album").insert(batch[i:i+500]).execute()
    st.rerun()

df = pd.DataFrame(data)

# -------------------------
# MÉTRICAS
# -------------------------
tienes = df["tengo"].sum()
total = len(df)
reps_totales = df["repetidas"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Obtenidas", f"{int(tienes)} / {total}")
c2.metric("Faltan", int(total - tienes))
c3.metric("Total Repetidas", int(reps_totales))
c4.metric("Progreso", f"{(tienes/total)*100:.1f}%")

# -------------------------
# INTERFAZ DE CHECKLIST + REPETIDAS
# -------------------------
st.info("💡 Marca las que tienes y usa los números para las repetidas. ¡No olvides Guardar!")

# Diccionarios para capturar cambios
cambios_tengo = {}
cambios_reps = {}

for nombre_seccion, lista_estampas in secciones_master.items():
    with st.expander(f"📍 {nombre_seccion}"):
        # Usamos 4 columnas para que quepa bien el checkbox y el número
        cols = st.columns(4) 
        for index, s_id in enumerate(lista_estampas):
            # Obtener datos actuales
            row = df[df["estampa"] == s_id]
            val_tengo = bool(row["tengo"].values[0])
            val_reps = int(row["repetidas"].values[0])
            
            with cols[index % 4]:
                st.markdown(f"**{s_id}**")
                # Fila interna para checkbox y repetidas
                sub_c1, sub_c2 = st.columns([1, 1.5])
                with sub_c1:
                    check = st.checkbox("Tengo", value=val_tengo, key=f"t_{s_id}", label_visibility="collapsed")
                    cambios_tengo[s_id] = 1 if check else 0
                with sub_c2:
                    n_reps = st.number_input("Reps", min_value=0, value=val_reps, key=f"r_{s_id}", label_visibility="collapsed")
                    cambios_reps[s_id] = n_reps
                st.write("---")

# -------------------------
# GUARDADO MASIVO
# -------------------------
st.divider()
if st.button("💾 GUARDAR TODOS LOS CAMBIOS", use_container_width=True, type="primary"):
    with st.spinner("Sincronizando con la nube..."):
        for s_id in cambios_tengo.keys():
            v_tengo = cambios_tengo[s_id]
            v_reps = cambios_reps[s_id]
            
            # Solo actualizar si algo cambió para que sea más rápido
            old_t = int(df[df["estampa"] == s_id]["tengo"].values[0])
            old_r = int(df[df["estampa"] == s_id]["repetidas"].values[0])
            
            if v_tengo != old_t or v_reps != old_r:
                supabase.table("album").update({
                    "tengo": v_tengo,
                    "repetidas": v_reps
                }).eq("user_id", user).eq("estampa", s_id).execute()
    
    st.success("¡Todo guardado! 🔥")
    st.rerun()
