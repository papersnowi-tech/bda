import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURĀCIJA
st.set_page_config(page_title="Business Crisis Control", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # Datumu apstrāde abiem failiem
    date_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce')
    
    return df, tix, date_col

df, tix, date_col = load_data()

# --- SIDEBAR (Prasība: Vismaz 2 filtri) ---
st.sidebar.header("📊 Analīzes Iestatījumi")

# Filtrs 1: Kategorija
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
kategorijas = st.sidebar.multiselect("Izvēlies kategorijas:", 
                                     options=df[cat_col].unique(), 
                                     default=df[cat_col].unique())

# Filtrs 2: Laika periods
min_d, max_d = df[date_col].min().date(), df[date_col].max().date()
date_range = st.sidebar.date_input("Analīzes periods:", [min_d, max_d])

# DATU FILTRĒŠANA
mask_df = df[cat_col].isin(kategorijas)
mask_tix = pd.Series([True] * len(tix)) # Sākumā atlasām visus

if len(date_range) == 2:
    start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    mask_df = mask_df & (df[date_col] >= start_d) & (df[date_col] <= end_d)
    mask_tix = (tix['Date_Logged'] >= start_d) & (tix['Date_Logged'] <= end_d)

df_f = df[mask_df]
tix_f = tix[mask_tix]

# --- VIRSRAKSTS ---
st.title("🚨 Biznesa procesu krīzes vadības panelis")
st.markdown("---")

# --- KPI RINDA (Prasība: 3 rādītāji) ---
kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric("Kopējie ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
with kpi2:
    refund_col = 'Refund_Amount_Clean'
    st.metric("Atgriezumu zaudējumi", f"{df_f[refund_col].sum():,.2f} €", delta_color="inverse")
with kpi3:
    st.metric("Atlasīto sūdzību skaits", len(tix_f))

st.markdown("---")

# --- 1. VIZUĀĻU RINDA (Laika grafiks un Tēmas) ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("📈 Sūdzību dinamika laikā")
    # Sagatavojam datus laika grafikam
    tix_daily = tix_f.groupby(tix_f['Date_Logged'].dt.date).size().reset_index(name='Skaits')
    fig_time = px.line(tix_daily, x='Date_Logged', y='Skaits', 
                       title="Sūdzību skaits pa dienām",
                       line_shape="spline", color_discrete_sequence=['red'])
    st.plotly_chart(fig_time, use_container_width=True)

with col_b:
    st.subheader("🎯 Sūdzību tēmu sadalījums")
    topic_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
    topic_dist = tix_f[topic_col].value_counts().reset_index()
    fig_pie = px.pie(topic_dist, values='count', names=topic_col, hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Reds_r)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- 2. VIZUĀĻU RINDA (Produktu zaudējumi un Tabula) ---
col_c, col_d = st.columns([1, 1])

with col_c:
    st.subheader("❌ Top zaudējumus radošie produkti")
    loss_data = df_f.groupby('Product_Name')[refund_col].sum().sort_values(ascending=False).head(10).reset_index()
    fig_bar = px.bar(loss_data, x=refund_col, y='Product_Name', orientation='h',
                     color=refund_col, color_continuous_scale='Reds')
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

with col_d:
    st.subheader("🚨 Krīzes sūdzību detaļas")
    st.dataframe(tix_f[['Date_Logged', 'Subject', topic_col]].head(15), use_container_width=True)

st.success("Dati sinhronizēti un gatavi analīzei.")
