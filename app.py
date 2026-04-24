import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Business Crisis Control", layout="wide")

# 1. DATU IELĀDE (Maksimāli vienkārša)
def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # Datumu sakārtošana, lai laika filtrs beidzot strādātu
    d_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[d_col] = pd.to_datetime(df[d_col], errors='coerce').dt.date
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce').dt.date
    
    # Izmetam tikai pilnīgi tukšās rindas
    df = df.dropna(subset=[d_col, 'Product_Name'])
    tix = tix.dropna(subset=['Date_Logged'])
    
    return df, tix, d_col

df, tix, d_col = load_data()

# --- SIDEBAR FILTRI (Tieši šie mainīs datus!) ---
st.sidebar.header("📊 Filtri")

# Kategoriju filtrs
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
all_cats = sorted(df[cat_col].unique())
selected_cats = st.sidebar.multiselect("Izvēlies kategoriju:", options=all_cats, default=all_cats)

# Laika filtrs
min_d, max_d = df[d_col].min(), df[d_col].max()
date_range = st.sidebar.date_input("Periods:", [min_d, max_d])

# --- FILTRĒŠANAS MEHĀNISMS (SVARĪGĀKĀ DAĻA) ---
# Šeit mēs izveidojam 'df_f' un 'tix_f', kas mainās atkarībā no izvēles
if len(date_range) == 2:
    start_d, end_d = date_range
    # Filtrējam pēc kategorijas UN laika
    df_f = df[(df[cat_col].isin(selected_cats)) & (df[d_col] >= start_d) & (df[d_col] <= end_d)]
    tix_f = tix[(tix['Date_Logged'] >= start_d) & (tix['Date_Logged'] <= end_d)]
else:
    df_f = df[df[cat_col].isin(selected_cats)]
    tix_f = tix.copy()

# --- DASHBOARD ATTĒLOŠANA ---
st.title("🚨 Biznesa procesu krīzes vadības panelis")

if df_f.empty:
    st.warning("⚠️ Nav datu ar šādu atlasi! Pamēģini pievienot vairāk kategoriju vai paplašināt laiku.")
else:
    # KPI Rinda - TAGAD MAINĪSIES!
    k1, k2, k3 = st.columns(3)
    k1.metric("Ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
    k2.metric("Zaudējumi", f"{df_f['Refund_Amount_Clean'].sum():,.2f} €")
    k3.metric("Sūdzību skaits", len(tix_f))

    st.divider()

    # Grafiku rinda
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 Sūdzību dinamika")
        t_counts = tix_f.groupby('Date_Logged').size().reset_index(name='Skaits')
        fig1 = px.line(t_counts, x='Date_Logged', y='Skaits', color_discrete_sequence=['red'])
        st.plotly_chart(fig1, use_container_width=True)
    
    with c2:
        st.subheader("🎯 Sūdzību tēmas")
        t_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
        fig2 = px.pie(tix_f, names=t_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig2, use_container_width=True)

    # Top produkti
    st.subheader("❌ Top zaudējumu produkti")
    top_p = df_f.groupby('Product_Name')['Refund_Amount_Clean'].sum().sort_values(ascending=False).head(10).reset_index()
    fig3 = px.bar(top_p, x='Refund_Amount_Clean', y='Product_Name', orientation='h', color='Refund_Amount_Clean', color_continuous_scale='Reds')
    st.plotly_chart(fig3, use_container_width=True)
