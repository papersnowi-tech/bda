import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Business Crisis Control", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # 1. Stingra datumu konvertēšana
    date_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce')
    
    # 2. Aizpildām tukšumus, ja tādi radušies, lai filtrs neizmet datus
    df[date_col] = df[date_col].fillna(pd.Timestamp('2023-12-01'))
    tix['Date_Logged'] = tix['Date_Logged'].fillna(pd.Timestamp('2023-12-01'))
    
    return df, tix, date_col

df, tix, date_col = load_data()

# --- SIDEBAR ---
st.sidebar.header("📊 Analīzes Iestatījumi")
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
kategorijas = st.sidebar.multiselect("Izvēlies kategorijas:", 
                                     options=df[cat_col].unique(), 
                                     default=df[cat_col].unique())

# Datuma filtrs - iestatām noklusējuma vērtības no datiem
start_init = df[date_col].min().date()
end_init = df[date_col].max().date()
date_range = st.sidebar.date_input("Analīzes periods:", [start_init, end_init])

# --- FILTRĒŠANAS LOĢIKA (SVARĪGI!) ---
if len(date_range) == 2:
    start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    
    # Filtrējam abus datu rāmjus pēc laika UN kategorijas
    df_f = df[(df[cat_col].isin(kategorijas)) & 
              (df[date_col] >= start_d) & 
              (df[date_col] <= end_d)]
    
    tix_f = tix[(tix['Date_Logged'] >= start_d) & 
                (tix['Date_Logged'] <= end_d)]
else:
    df_f = df[df[cat_col].isin(kategorijas)]
    tix_f = tix.copy()

# --- REZULTĀTU ATTĒLOŠANA ---
st.title("🚨 Biznesa procesu krīzes vadības panelis")

if df_f.empty and tix_f.empty:
    st.warning("⚠️ Šajā periodā datu nav. Pamēģini paplašināt laika filtru!")
else:
    # KPI Rinda
    k1, k2, k3 = st.columns(3)
    k1.metric("Kopējie ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
    refund_col = 'Refund_Amount_Clean'
    k2.metric("Atgriezumu zaudējumi", f"{df_f[refund_col].sum():,.2f} €", delta_color="inverse")
    k3.metric("Sūdzību skaits", len(tix_f))

    st.divider()

    # Grafiku rinda 1
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 Sūdzību dinamika")
        t_graph = tix_f.groupby(tix_f['Date_Logged'].dt.date).size().reset_index(name='Skaits')
        fig_l = px.line(t_graph, x='Date_Logged', y='Skaits', color_discrete_sequence=['red'])
        st.plotly_chart(fig_l, use_container_width=True)

    with c2:
        st.subheader("🎯 Sūdzību tēmas")
        t_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
        fig_p = px.pie(tix_f, names=t_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig_p, use_container_width=True)

    # Grafiku rinda 2
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("❌ Top zaudējumu produkti")
        l_data = df_f.groupby('Product_Name')[refund_col].sum().sort_values(ascending=False).head(10).reset_index()
        fig_b = px.bar(l_data, x=refund_col, y='Product_Name', orientation='h', color_continuous_scale='Reds')
        st.plotly_chart(fig_b, use_container_width=True)
    
    with c4:
        st.subheader("🚨 Krīzes sūdzību detaļas")
        st.dataframe(tix_f[['Date_Logged', 'Subject', t_col]].head(10), use_container_width=True)
