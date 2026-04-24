import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Business Crisis Control", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # 1. Uzlabota datumu apstrāde (piespiežam formātu)
    date_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=False, errors='coerce')
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], dayfirst=False, errors='coerce')
    
    # 2. Ja pēc konvertēšanas ir tukšumi (NaT), aizpildām ar šodienu, lai filtrs nesalūztu
    if df[date_col].isnull().all():
        df[date_col] = pd.Timestamp.now()
    if tix['Date_Logged'].isnull().all():
        tix['Date_Logged'] = pd.Timestamp.now()
        
    return df, tix, date_col

df, tix, date_col = load_data()

# --- SIDEBAR ---
st.sidebar.header("📊 Analīzes Iestatījumi")

cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
kategorijas = st.sidebar.multiselect("Izvēlies kategorijas:", 
                                     options=df[cat_col].unique(), 
                                     default=df[cat_col].unique())

# Dinamiski iegūstam datumus no datiem
start_default = df[date_col].min().date()
end_default = df[date_col].max().date()

# Pievienojam drošības pārbaudi gadījumam, ja datumi joprojām ir 1970
if start_default.year < 2000:
    start_default = pd.Timestamp('2023-01-01').date()
    end_default = pd.Timestamp('2025-12-31').date()

date_range = st.sidebar.date_input("Analīzes periods:", [start_default, end_default])

# DATU FILTRĒŠANA
mask_df = df[cat_col].isin(kategorijas)
mask_tix = pd.Series([True] * len(tix))

if len(date_range) == 2:
    start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    mask_df = mask_df & (df[date_col] >= start_d) & (df[date_col] <= end_d)
    mask_tix = (tix['Date_Logged'] >= start_d) & (tix['Date_Logged'] <= end_d)

df_f = df[mask_df]
tix_f = tix[mask_tix]

# --- VIZUĀLĀ DAĻA ---
st.title("🚨 Biznesa procesu krīzes vadības panelis")

if df_f.empty:
    st.warning("⚠️ Atlasītajā periodā nav datu. Pamēģini paplašināt datumu filtru sānā!")
else:
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Kopējie ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
    kpi2.metric("Atgriezumu zaudējumi", f"{df_f['Refund_Amount_Clean'].sum():,.2f} €")
    kpi3.metric("Sūdzību skaits", len(tix_f))

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📈 Sūdzību dinamika laikā")
        tix_daily = tix_f.groupby(tix_f['Date_Logged'].dt.date).size().reset_index(name='Skaits')
        st.line_chart(tix_daily.set_index('Date_Logged'))

    with col_b:
        st.subheader("🎯 Sūdzību tēmu sadalījums")
        topic_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
        fig_pie = px.pie(tix_f, names=topic_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig_pie, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("❌ Top zaudējumus radošie produkti")
        loss_data = df_f.groupby('Product_Name')['Refund_Amount_Clean'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_bar = px.bar(loss_data, x='Refund_Amount_Clean', y='Product_Name', orientation='h', color_continuous_scale='Reds')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col_d:
        st.subheader("🚨 Krīzes sūdzību detaļas")
        st.dataframe(tix_f[['Date_Logged', 'Subject', topic_col]].head(15), use_container_width=True)
