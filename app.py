import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Business Crisis Control", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # AGRESĪVĀ KONVERTĒŠANA: noņemam jebkādu laiku, atstājam tikai YYYY-MM-DD
    date_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.normalize()
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce').dt.normalize()
    
    return df, tix, date_col

df, tix, date_col = load_data()

# --- SIDEBAR ---
st.sidebar.header("📊 Filtri")
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
kategorijas = st.sidebar.multiselect("Kategorija:", options=df[cat_col].unique(), default=df[cat_col].unique())

# SVARĪGI: pārveidojam filtra datumus uz Timestamp, lai tie sakristu ar datiem
min_d = df[date_col].min()
max_d = df[date_col].max()
date_range = st.sidebar.date_input("Periods:", [min_d, max_d])

# --- FILTRĒŠANAS LOĢIKA ---
if len(date_range) == 2:
    # Piespiežam filtra datumus kļūt par Timestamp objektiem
    start_dt = pd.Timestamp(date_range[0]).normalize()
    end_dt = pd.Timestamp(date_range[1]).normalize()
    
    df_f = df[(df[cat_col].isin(kategorijas)) & (df[date_col] >= start_dt) & (df[date_col] <= end_dt)]
    tix_f = tix[(tix['Date_Logged'] >= start_dt) & (tix['Date_Logged'] <= end_dt)]
else:
    df_f = df[df[cat_col].isin(kategorijas)]
    tix_f = tix.copy()

# --- DASHBOARD ---
st.title("🚨 Biznesa procesu krīzes vadība")

if df_f.empty:
    st.error(f"Dati nav atrasti! Filtra datumi: {date_range}. Datu paraugs: {df[date_col].iloc[0]}")
else:
    k1, k2, k3 = st.columns(3)
    k1.metric("Ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
    k2.metric("Zaudējumi", f"{df_f['Refund_Amount_Clean'].sum():,.2f} €")
    k3.metric("Sūdzības", len(tix_f))

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Sūdzību grafiks")
        t_daily = tix_f.groupby('Date_Logged').size().reset_index(name='Skaits')
        fig1 = px.line(t_daily, x='Date_Logged', y='Skaits', color_discrete_sequence=['red'])
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        st.subheader("Sūdzību tēmas")
        t_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
        fig2 = px.pie(tix_f, names=t_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Top zaudējumu produkti")
    l_data = df_f.groupby('Product_Name')['Refund_Amount_Clean'].sum().sort_values(ascending=False).head(10).reset_index()
    fig3 = px.bar(l_data, x='Refund_Amount_Clean', y='Product_Name', orientation='h', color_continuous_scale='Reds')
    st.plotly_chart(fig3, use_container_width=True)
