import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Product Crisis Dashboard", layout="wide")

@st.cache_data
def load_data():
    # Ielādējam datus
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # Automātiski atrodam datuma kolonnu, ja nosaukums atšķiras
    for col in df.columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col])
            df.rename(columns={col: 'Order_Date'}, inplace=True)
            
    # Pievienojam rezerves kolonnu, ja Order_Date joprojām nav
    if 'Order_Date' not in df.columns:
        df['Order_Date'] = pd.to_datetime('2025-12-01')
        
    return df, tix

df, tix = load_data()

st.title("🚀 Biznesa procesu krīzes analīze")

# SIDEBAR
st.sidebar.header("📊 Filtri")
# Pārbaudām vai Kategorija_LV eksistē, ja nē - izmantojam Product_Category
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
kategorijas = st.sidebar.multiselect("Kategorija:", options=df[cat_col].unique(), default=df[cat_col].unique())

# FILTRĒŠANA
df_f = df[df[cat_col].isin(kategorijas)]

# KPI RINDA
kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric("Kopējie ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
with kpi2:
    refund_col = 'Refund_Amount_Clean' if 'Refund_Amount_Clean' in df.columns else df.columns[-1]
    st.metric("Atgriezumu summa", f"{df_f[refund_col].sum():,.2f} €")
with kpi3:
    st.metric("Sūdzību skaits", len(tix))

# VIZUĀĻI
col1, col2 = st.columns(2)
with col1:
    st.subheader("Zaudējumi pa produktiem")
    fig1 = px.bar(df_f.groupby('Product_Name')[refund_col].sum().reset_index(), x=refund_col, y='Product_Name', orientation='h')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Sūdzību tēmas")
    if 'topic_lv' in tix.columns:
        fig2 = px.pie(tix, names='topic_lv', hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.write("Sūdzību dati nav pieejami")

st.subheader("🚨 Detalizēta informācija")
st.dataframe(tix.head(10), use_container_width=True)
