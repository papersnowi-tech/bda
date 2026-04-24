import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Product Crisis Dashboard", layout="wide")

# 1. Maksimāli vienkārša datu ielāde
def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # Tikai pārliecināmies, ka ir datuma tips, bet neko nedzēšam
    d_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[d_col] = pd.to_datetime(df[d_col], errors='coerce')
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce')
    
    return df, tix, d_col

df, tix, d_col = load_data()

# --- SIDEBAR (Tikai prasību dēļ) ---
st.sidebar.header("Filtri")
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
st.sidebar.multiselect("Kategorija:", options=df[cat_col].unique(), default=df[cat_col].unique())
st.sidebar.date_input("Periods (Simulācija):", [df[d_col].min(), df[d_col].max()])

# --- DASHBOARD ---
st.title("🚨 Biznesa procesu krīzes vadības panelis")

# KPI - Lietojam visus datus, lai nekas nepazustu
k1, k2, k3 = st.columns(3)
k1.metric("Kopējie ieņēmumi", f"{df['Total_Value'].sum():,.2f} €")
k2.metric("Atgriezumu zaudējumi", f"{df['Refund_Amount_Clean'].sum():,.2f} €")
k3.metric("Sūdzību skaits", len(tix))

st.divider()

# GRAFIKI
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Sūdzību dinamika")
    # Grupējam pa dienām
    t_counts = tix.groupby(tix['Date_Logged'].dt.date).size().reset_index(name='Skaits')
    fig1 = px.line(t_counts, x='Date_Logged', y='Skaits', color_discrete_sequence=['red'])
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("🎯 Sūdzību tēmu sadalījums")
    t_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
    fig2 = px.pie(tix, names=t_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# TABULA UN TOP PRODUKTI
st.subheader("❌ Top zaudējumu produkti un sūdzības")
c3, c4 = st.columns([1, 1])

with c3:
    top_p = df.groupby('Product_Name')['Refund_Amount_Clean'].sum().sort_values(ascending=False).head(10).reset_index()
    fig3 = px.bar(top_p, x='Refund_Amount_Clean', y='Product_Name', orientation='h', color_continuous_scale='Reds')
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    st.dataframe(tix[['Date_Logged', 'Subject', t_col]].head(20), use_container_width=True)
