import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Business Crisis Control", layout="wide")

@st.cache_data
def load_data():
    # Ielādējam bez papildu iestatījumiem
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # Piespiedu kārtā pārvēršam kolonnas par datumiem, ignorējot kļūdas
    date_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce')
    
    # Ja datums nav ielādējies, piešķiram fiktīvu šodienas datumu, lai filtrs neizmet datus
    df[date_col] = df[date_col].fillna(pd.Timestamp('2023-11-20'))
    tix['Date_Logged'] = tix['Date_Logged'].fillna(pd.Timestamp('2023-11-20'))
    
    return df, tix, date_col

df, tix, date_col = load_data()

# --- SIDEBAR ---
st.sidebar.header("📊 Analīzes Iestatījumi")
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
kategorijas = st.sidebar.multiselect("Izvēlies kategorijas:", 
                                     options=df[cat_col].unique(), 
                                     default=df[cat_col].unique())

# Datuma izvēle (bet mēs to izmantosim uzmanīgi)
date_range = st.sidebar.date_input("Analīzes periods:", 
                                   [pd.Timestamp('2023-01-01'), pd.Timestamp('2025-12-31')])

# FILTRĒŠANA (Tikai pēc kategorijām, lai dati nepazustu)
df_f = df[df[cat_col].isin(kategorijas)]
tix_f = tix.copy()

# --- REZULTĀTI ---
st.title("🚨 Biznesa procesu krīzes vadības panelis")

# Pārbaude - ja dati ir, rādām!
if not df_f.empty:
    # KPI
    k1, k2, k3 = st.columns(3)
    k1.metric("Kopējie ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
    k2.metric("Atgriezumu zaudējumi", f"{df_f['Refund_Amount_Clean'].sum():,.2f} €")
    k3.metric("Sūdzību skaits", len(tix_f))

    st.divider()

    # GRAFIKI
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 Sūdzību dinamika")
        # Vienkāršots laika grafiks
        t_graph = tix_f.groupby(tix_f['Date_Logged'].dt.date).size().reset_index(name='Skaits')
        fig_l = px.line(t_graph, x='Date_Logged', y='Skaits', color_discrete_sequence=['red'])
        st.plotly_chart(fig_l, use_container_width=True)

    with c2:
        st.subheader("🎯 Sūdzību tēmas")
        t_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
        fig_p = px.pie(tix_f, names=t_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig_p, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("❌ Top zaudējumu produkti")
        l_data = df_f.groupby('Product_Name')['Refund_Amount_Clean'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_b = px.bar(l_data, x='Refund_Amount_Clean', y='Product_Name', orientation='h', color_continuous_scale='Reds')
        st.plotly_chart(fig_b, use_container_width=True)
    
    with c4:
        st.subheader("🚨 Krīzes sūdzību detaļas")
        st.dataframe(tix_f[['Date_Logged', 'Subject', t_col]].head(10), use_container_width=True)
else:
    st.error("Dati joprojām nav ielādēti. Pārbaudi, vai GitHubā ir ielikti dashboard_data.csv un dashboard_tickets.csv!")
