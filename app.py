import streamlit as st
import pandas as pd
import plotly.express as px

# 1. NOŅEMAM @st.cache_data - tas var "iesaldēt" vecos datus
def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # Pārveidojam par datumiem bez laika (Normalize)
    d_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[d_col] = pd.to_datetime(df[d_col], errors='coerce').dt.normalize()
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce').dt.normalize()
    
    return df, tix, d_col

df, tix, d_col = load_data()

# --- SIDEBAR ---
st.sidebar.header("📊 Filtri")
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
kategorijas = st.sidebar.multiselect("Kategorija:", options=df[cat_col].unique(), default=df[cat_col].unique())

# Iegūstam galējos datumus
min_d = df[d_col].min()
max_d = df[d_col].max()
date_range = st.sidebar.date_input("Periods:", [min_d, max_d])

# --- FILTRĒŠANA (Tieša un agresīva) ---
if len(date_range) == 2:
    # Filtra datumus pārvēršam par Timestamp, lai sakristu ar Pandas
    s_dt = pd.to_datetime(date_range[0]).normalize()
    e_dt = pd.to_datetime(date_range[1]).normalize()
    
    # Izveidojam jaunus, filtrētus DataFrame
    df_filtered = df[(df[cat_col].isin(kategorijas)) & (df[d_col] >= s_dt) & (df[d_col] <= e_dt)].copy()
    tix_filtered = tix[(tix['Date_Logged'] >= s_dt) & (tix['Date_Logged'] <= e_dt)].copy()
else:
    df_filtered = df[df[cat_col].isin(kategorijas)].copy()
    tix_filtered = tix.copy()

# --- DASHBOARD ---
st.title("🚨 Krīzes vadības panelis")

# KPI - Izmantojam TIKAI filtrētos datus (df_filtered)
k1, k2, k3 = st.columns(3)
k1.metric("Ieņēmumi", f"{df_filtered['Total_Value'].sum():,.2f} €")
k2.metric("Zaudējumi", f"{df_filtered['Refund_Amount_Clean'].sum():,.2f} €")
k3.metric("Sūdzības", len(tix_filtered))

st.divider()

# GRAFIKI - Izmantojam TIKAI filtrētos datus
c1, c2 = st.columns(2)
with c1:
    st.subheader("Sūdzību grafiks")
    t_counts = tix_filtered.groupby('Date_Logged').size().reset_index(name='Skaits')
    if not t_counts.empty:
        st.line_chart(t_counts.set_index('Date_Logged'))
    else:
        st.write("Nav sūdzību šajā periodā")

with c2:
    st.subheader("Sūdzību tēmas")
    t_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
    if not tix_filtered.empty:
        fig = px.pie(tix_filtered, names=t_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Top zaudējumu produkti")
top_prod = df_filtered.groupby('Product_Name')['Refund_Amount_Clean'].sum().sort_values(ascending=False).head(10).reset_index()
if not top_prod.empty:
    st.bar_chart(data=top_prod, x='Product_Name', y='Refund_Amount_Clean', color='#FF4B4B')
