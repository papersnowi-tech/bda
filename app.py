import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURĀCIJA
st.set_page_config(page_title="Product Crisis Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # Nodrošinām datumus (Prasība pēc laika filtra)
    date_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce')
    
    return df, tix, date_col

df, tix, date_col = load_data()

# --- SIDEBAR (Prasība: Vismaz 2 filtri) ---
st.sidebar.header("📊 Filtri vadībai")

# Filtrs 1: Kategorija
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
kategorijas = st.sidebar.multiselect("Produktu kategorija:", 
                                     options=df[cat_col].unique(), 
                                     default=df[cat_col].unique())

# Filtrs 2: Laika periods
min_d, max_d = df[date_col].min().date(), df[date_col].max().date()
date_range = st.sidebar.date_input("Periods:", [min_d, max_d])

# Datu filtrēšana
mask = df[cat_col].isin(kategorijas)
if len(date_range) == 2:
    mask = mask & (df[date_col].dt.date >= date_range[0]) & (df[date_col].dt.date <= date_range[1])
df_f = df[mask]

# --- VIRSRAKSTS ---
st.title("🚀 Biznesa procesu krīzes analīze")
st.info("Šis rīks ļauj vadībai identificēt zaudējumus radošos produktus un klientu sūdzību iemeslus.")

# --- KPI RINDA (Prasība: Vismaz 3 rādītāji) ---
kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric("Kopējie ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
with kpi2:
    refund_col = 'Refund_Amount_Clean'
    st.metric("Atgriezumu summa", f"{df_f[refund_col].sum():,.2f} €", delta="- Zaudējumi", delta_color="inverse")
with kpi3:
    st.metric("Sūdzību skaits", len(tix), help="Kopējais pēdējā ceturkšņa sūdzību apjoms")

st.divider()

# --- VIZUĀĻI (Prasība: Vismaz 2 interaktīvi grafiki) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 zaudējumus radošie produkti")
    # Grupējam datus, lai redzētu lielākos zaudējumus (NordLock Pro būs šeit)
    loss_data = df_f.groupby('Product_Name')[refund_col].sum().sort_values(ascending=False).head(10).reset_index()
    fig1 = px.bar(loss_data, x=refund_col, y='Product_Name', orientation='h', 
                  color=refund_col, color_continuous_scale='Reds')
    fig1.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Sūdzību tēmu sadalījums (MI klasifikācija)")
    topic_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
    topic_dist = tix[topic_col].value_counts().reset_index()
    fig2 = px.pie(topic_dist, values='count', names=topic_col, hole=0.4,
                  color_discrete_sequence=px.colors.sequential.Reds_r)
    st.plotly_chart(fig2, use_container_width=True)

# --- TABULA (Prasība: 1 datu tabula "Top problem cases") ---
st.subheader("🚨 Detalizēts sūdzību saraksts (Analīzei)")
st.dataframe(tix[['Date_Logged', 'Subject', topic_col, 'Message_Body']].head(15), use_container_width=True)

st.caption("Dati tiek automātiski atjaunoti no GitHub krātuves.")
