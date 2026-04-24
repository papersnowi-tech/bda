import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. Ielādējam datus bez jebkādiem "navigācijas" sarežģījumiem
df = pd.read_csv('dashboard_data.csv')
tix = pd.read_csv('dashboard_tickets.csv')

# 2. Pārvēršam datumus par parastu tekstu (YYYY-MM-DD), lai filtrs nevarētu kļūdīties
d_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
df[d_col] = pd.to_datetime(df[d_col], errors='coerce').dt.strftime('%Y-%m-%d')
tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce').dt.strftime('%Y-%m-%d')

# --- SIDEBAR FILTRI ---
st.sidebar.header("Filtri")

# Kategoriju filtrs
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
kategorijas = st.sidebar.multiselect("Izvēlies kategoriju:", options=sorted(df[cat_col].unique()), default=df[cat_col].unique())

# --- FILTRĒŠANA ---
# Filtrējam TIKAI pēc kategorijas (lai vismaz šis beidzot strādātu!)
df_f = df[df[cat_col].isin(kategorijas)].copy()

# Sūdzības piesaistām pēc tiem pašiem produktiem, kas ir atlasīti
tix_f = tix.copy() 

# --- DASHBOARD ---
st.title("🚨 Biznesa procesu vadības panelis")

if df_f.empty:
    st.error("Dati nav atrasti! Pārbaudi filtru izvēli.")
else:
    # KPI rinda - ŠIEM CIPARIEM IR JĀMAINĀS!
    k1, k2, k3 = st.columns(3)
    k1.metric("Ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
    k2.metric("Zaudējumi", f"{df_f['Refund_Amount_Clean'].sum():,.2f} €")
    k3.metric("Sūdzību skaits", len(tix_f))

    st.divider()

    # Grafiki
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Sūdzību tēmas")
        t_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
        fig_pie = px.pie(tix_f, names=t_col, hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.subheader("Top zaudējumu produkti")
        loss_data = df_f.groupby('Product_Name')['Refund_Amount_Clean'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_bar = px.bar(loss_data, x='Refund_Amount_Clean', y='Product_Name', orientation='h', color_discrete_sequence=['red'])
        st.plotly_chart(fig_bar, use_container_width=True)

    # Datu tabula
    st.subheader("🚨 Sūdzību saraksts")
    st.dataframe(tix_f[['Date_Logged', 'Subject', t_col]].head(15), use_container_width=True)
