import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Business Crisis Control", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # Konvertējam uz datetime un noņemam laika daļu (atstājam tikai datumu)
    date_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.date
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce').dt.date
    
    # Aizpildām tukšumus ar rezerves datumu, ja nepieciešams
    df[date_col] = df[date_col].fillna(pd.Timestamp('2023-12-01').date())
    tix['Date_Logged'] = tix['Date_Logged'].fillna(pd.Timestamp('2023-12-01').date())
    
    return df, tix, date_col

df, tix, date_col = load_data()

# --- SIDEBAR ---
st.sidebar.header("📊 Analīzes Iestatījumi")
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
kategorijas = st.sidebar.multiselect("Izvēlies kategorijas:", 
                                     options=df[cat_col].unique(), 
                                     default=df[cat_col].unique())

# Datuma filtrs
min_d, max_d = df[date_col].min(), df[date_col].max()
date_range = st.sidebar.date_input("Analīzes periods:", [min_d, max_d])

# --- FILTRĒŠANA ---
# Svarīgi: salīdzinām date objektus
if len(date_range) == 2:
    start_d, end_d = date_range[0], date_range[1]
    
    df_f = df[(df[cat_col].isin(kategorijas)) & 
              (df[date_col] >= start_d) & 
              (df[date_col] <= end_d)]
    
    tix_f = tix[(tix['Date_Logged'] >= start_d) & 
                (tix['Date_Logged'] <= end_d)]
else:
    df_f = df[df[cat_col].isin(kategorijas)]
    tix_f = tix.copy()

# --- REZULTĀTI ---
st.title("🚨 Biznesa procesu krīzes vadības panelis")

if df_f.empty and tix_f.empty:
    st.warning("⚠️ Atlasītajā periodā datu nav. Paplašini laika filtru sānā!")
else:
    # KPI Rinda
    k1, k2, k3 = st.columns(3)
    k1.metric("Kopējie ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
    refund_col = 'Refund_Amount_Clean'
    k2.metric("Atgriezumu zaudējumi", f"{df_f[refund_col].sum():,.2f} €")
    k3.metric("Sūdzību skaits", len(tix_f))

    st.divider()

    # Grafiku rinda
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 Sūdzību dinamika")
        t_graph = tix_f.groupby('Date_Logged').size().reset_index(name='Skaits')
        fig_l = px.line(t_graph, x='Date_Logged', y='Skaits', color_discrete_sequence=['red'])
        st.plotly_chart(fig_l, use_container_width=True)

    with c2:
        st.subheader("🎯 Sūdzību tēmas")
        t_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
        fig_p = px.pie(tix_f, names=t_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig_p, use_container_width=True)

    # Produktu grafiks un tabula
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("❌ Top zaudējumu produkti")
        l_data = df_f.groupby('Product_Name')[refund_col].sum().sort_values(ascending=False).head(10).reset_index()
        fig_b = px.bar(l_data, x=refund_col, y='Product_Name', orientation='h', color_continuous_scale='Reds')
        st.plotly_chart(fig_b, use_container_width=True)
    
    with c4:
        st.subheader("🚨 Krīzes sūdzību detaļas")
        st.dataframe(tix_f[['Date_Logged', 'Subject', t_col]].head(10), use_container_width=True)
