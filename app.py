import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Krīzes vadība", layout="wide")

def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # Konvertējam kolonnas par datumiem
    d_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[d_col] = pd.to_datetime(df[d_col], errors='coerce').dt.date
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce').dt.date
    
    # Izmetam tukšos datumus, lai tie nebojā filtru (1970. gada problēma)
    df = df.dropna(subset=[d_col])
    tix = tix.dropna(subset=['Date_Logged'])
    
    return df, tix, d_col

df, tix, d_col = load_data()

# --- SIDEBAR ---
st.sidebar.header("Filtri")
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
selected_cats = st.sidebar.multiselect("Kategorija:", options=df[cat_col].unique(), default=df[cat_col].unique())

# SVARĪGI: Iestatām filtra robežas no reālajiem datiem
min_d, max_d = df[d_col].min(), df[d_col].max()
date_range = st.sidebar.date_input("Periods:", [min_d, max_d])

# --- FILTRĒŠANA (Šī daļa liek datiem mainīties) ---
if isinstance(date_range, list) and len(date_range) == 2:
    start_f, end_f = date_range
    df_f = df[(df[cat_col].isin(selected_cats)) & (df[d_col] >= start_f) & (df[d_col] <= end_f)]
    tix_f = tix[(tix['Date_Logged'] >= start_f) & (tix['Date_Logged'] <= end_f)]
else:
    df_f = df[df[cat_col].isin(selected_cats)]
    tix_f = tix[tix['Date_Logged'].isin(df_f[d_col])] # Sinhronizējam sūdzības

# --- DASHBOARD ---
st.title("🚨 Krīzes vadības panelis")

# KPI rēķinām tikai no filtrētajiem (df_f) datiem!
k1, k2, k3 = st.columns(3)
k1.metric("Ieņēmumi", f"{df_f['Total_Value'].sum():,.2f} €")
k2.metric("Zaudējumi", f"{df_f['Refund_Amount_Clean'].sum():,.2f} €")
k3.metric("Sūdzības", len(tix_f))

st.divider()

# GRAFIKI
c1, c2 = st.columns(2)
with c1:
    st.subheader("Sūdzību dinamika")
    if not tix_f.empty:
        # Grupējam pēc datuma, lai redzētu sūdzību skaitu pa dienām
        t_daily = tix_f.groupby('Date_Logged').size().reset_index(name='Skaits')
        fig1 = px.line(t_daily, x='Date_Logged', y='Skaits', color_discrete_sequence=['red'])
        st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.subheader("Sūdzību tēmas")
    t_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
    if not tix_f.empty:
        fig2 = px.pie(tix_f, names=t_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig2, use_container_width=True)

st.subheader("Top zaudējumu produkti")
top_p = df_f.groupby('Product_Name')['Refund_Amount_Clean'].sum().sort_values(ascending=False).head(10).reset_index()
fig3 = px.bar(top_p, x='Product_Name', y='Refund_Amount_Clean', color='Refund_Amount_Clean', color_continuous_scale='Reds')
st.plotly_chart(fig3, use_container_width=True)
