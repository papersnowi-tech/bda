import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Crisis Dashboard", layout="wide")

def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # 1. Piespiedu kārtā pārvēršam par datumu, nederīgos izmetam
    d_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[d_col] = pd.to_datetime(df[d_col], errors='coerce')
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'], errors='coerce')
    
    # 2. SVARĪGI: Izmetam rindas, kur datums nav saprotams (NaT)
    df = df.dropna(subset=[d_col])
    tix = tix.dropna(subset=['Date_Logged'])
    
    # 3. Pārvēršam par tīru datumu (bez laika) salīdzināšanai
    df[d_col] = df[d_col].dt.date
    tix['Date_Logged'] = tix['Date_Logged'].dt.date
    
    return df, tix, d_col

df, tix, d_col = load_data()

# --- SIDEBAR ---
st.sidebar.header("Filtri")
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df.columns else 'Product_Category'
selected_cats = st.sidebar.multiselect("Kategorija:", options=df[cat_col].unique(), default=df[cat_col].unique())

# Filtra noklusējuma vērtības no datiem (vairs nebūs 1970)
start_date = df[d_col].min()
end_date = df[d_col].max()

date_range = st.sidebar.date_input("Periods:", [start_date, end_date])

# --- FILTRĒŠANA ---
# Ja filtrā ir abi datumi, filtrējam. Ja nē, rādām visu.
if isinstance(date_range, list) and len(date_range) == 2:
    s, e = date_range
    df_f = df[(df[cat_col].isin(selected_cats)) & (df[d_col] >= s) & (df[d_col] <= e)]
    tix_f = tix[(tix['Date_Logged'] >= s) & (tix['Date_Logged'] <= e)]
else:
    df_f = df[df[cat_col].isin(selected_cats)]
    tix_f = tix.copy()

# --- DASHBOARD ---
st.title("🚨 Krīzes vadības panelis")

# KPI
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
        t_counts = tix_f.groupby('Date_Logged').size().reset_index(name='Skaits')
        fig1 = px.line(t_counts, x='Date_Logged', y='Skaits', color_discrete_sequence=['red'])
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Nav datu šajā periodā")

with c2:
    st.subheader("Sūdzību tēmas")
    t_col = 'topic_lv' if 'topic_lv' in tix.columns else 'Topic'
    if not tix_f.empty:
        fig2 = px.pie(tix_f, names=t_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig2, use_container_width=True)

st.subheader("Top zaudējumu produkti")
top_prod = df_f.groupby('Product_Name')['Refund_Amount_Clean'].sum().sort_values(ascending=False).head(10).reset_index()
fig3 = px.bar(top_prod, x='Product_Name', y='Refund_Amount_Clean', color_discrete_sequence=['#FF4B4B'])
st.plotly_chart(fig3, use_container_width=True)
