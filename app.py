import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Business Crisis Control", layout="wide")

@st.cache_data
def load_data():
    # Ielādējam failus
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # Piespiežam kolonnas pārvērsties par DATUMA objektiem (bez laika daļas)
    date_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.date
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce').dt.date
    
    # Nodrošinām, ka nav tukšu datumu (NaT), aizstājot tos ar decembra sākumu
    backup_date = pd.Timestamp('2023-12-01').date()
    df[date_col] = df[date_col].fillna(backup_date)
    tix['Date_Logged'] = tix['Date_Logged'].fillna(backup_date)
    
    return df, tix, date_col

df, tix, date_col = load_data()

# --- SIDEBAR FILTRI ---
st.sidebar.header("📊 Analīzes Iestatījumi")

# 1. Kategoriju filtrs
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
kategorijas = st.sidebar.multiselect("Izvēlies kategorijas:", 
                                     options=sorted(df[cat_col].unique()), 
                                     default=df[cat_col].unique())

# 2. Datuma filtrs (izmantojam reālos datumus no faila)
min_d = df[date_col].min()
max_d = df[date_col].max()

# Šī rinda novērsīs 1970. gada parādīšanos
date_range = st.sidebar.date_input("Analīzes periods:", [min_d, max_d], min_value=min_d, max_value=max_d)

# --- FILTRĒŠANAS LOĢIKA ---
if len(date_range) == 2:
    start_d, end_d = date_range[0], date_range[1]
    
    # Filtrējam abus datu rāmjus
    df_f = df[(df[cat_col].isin(kategorijas)) & (df[date_col] >= start_d) & (df[date_col] <= end_d)]
    tix_f = tix[(tix['Date_Logged'] >= start_d) & (tix['Date_Logged'] <= end_d)]
else:
    df_f = df[df[cat_col].isin(kategorijas)]
    tix_f = tix.copy()

# --- DASHBOARD ATTĒLOŠANA ---
st.title("🚨 Biznesa procesu krīzes vadības panelis")

if df_f.empty and tix_f.empty:
    st.warning("⚠️ Atlasītajā periodā datu nav. Pamēģini paplašināt datumu filtru sānā!")
else:
    # KPI rinda
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Kopējie ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
    with k2:
        refund_sum = df_f['Refund_Amount_Clean'].sum()
        st.metric("Atgriezumu zaudējumi", f"{refund_sum:,.2f} €", delta="- Zaudējumi", delta_color="inverse")
    with k3:
        st.metric("Sūdzību skaits", len(tix_f))

    st.divider()

    # Vizuāļu pirmā rinda
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 Sūdzību dinamika laikā")
        t_daily = tix_f.groupby('Date_Logged').size().reset_index(name='Skaits')
        fig_l = px.line(t_daily, x='Date_Logged', y='Skaits', color_discrete_sequence=['red'], markers=True)
        st.plotly_chart(fig_l, use_container_width=True)

    with col2:
        st.subheader("🎯 Sūdzību tēmas (MI)")
        t_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
        fig_p = px.pie(tix_f, names=t_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig_p, use_container_width=True)

    # Vizuāļu otrā rinda
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("❌ Top zaudējumu produkti")
        l_data = df_f.groupby('Product_Name')['Refund_Amount_Clean'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_b = px.bar(l_data, x='Refund_Amount_Clean', y='Product_Name', orientation='h', color='Refund_Amount_Clean', color_continuous_scale='Reds')
        st.plotly_chart(fig_b, use_container_width=True)
    
    with col4:
        st.subheader("🚨 Krīzes sūdzību detaļas")
        st.dataframe(tix_f[['Date_Logged', 'Subject', t_col]].head(15), use_container_width=True)
