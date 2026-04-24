
import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURĀCIJA UN DATU IELĀDE
st.set_page_config(page_title="Product Crisis Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    df['Order_Date'] = pd.to_datetime(df['Order_Date'])
    tix['Date_Logged'] = pd.to_datetime(tix['Date_Logged'])
    return df, tix

df, tix = load_data()

# 2. SIDEBAR (FILTRI) - Prasība: Vismaz 2 filtri
st.sidebar.header("📊 Analīzes Filtri")

# Filtrs 1: Kategorija
kategorijas = st.sidebar.multiselect(
    "Produktu kategorija:",
    options=df['Kategorija_LV'].unique(),
    default=df['Kategorija_LV'].unique()
)

# Filtrs 2: Laika periods
min_date = df['Order_Date'].min().date()
max_date = df['Order_Date'].max().date()
date_range = st.sidebar.date_input("Periods:", [min_date, max_date])

# Datu filtrēšana pēc izvēlētajiem parametriem
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df['Kategorija_LV'].isin(kategorijas)) &            (df['Order_Date'].dt.date >= start_date) &            (df['Order_Date'].dt.date <= end_date)
    df_f = df[mask]
    tix_f = tix[(tix['Date_Logged'].dt.date >= start_date) & (tix['Date_Logged'].dt.date <= end_date)]
else:
    df_f = df
    tix_f = tix

# 3. KPI RINDA - Prasība: Vismaz 3 rādītāji
st.title("🚀 Biznesa procesu krīzes analīze")
st.markdown("---")

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    total_rev = df_f['Total_Value'].sum()
    st.metric("Kopējie ieņēmumi", f"{total_rev:,.2f} €")
with kpi2:
    total_ref = df_f['Refund_Amount_Clean'].sum()
    ref_pct = (total_ref / total_rev * 100) if total_rev > 0 else 0
    st.metric("Atgriezumu summa", f"{total_ref:,.2f} €", f"{ref_pct:.1f}% no ieņ.")
with kpi3:
    st.metric("Sūdzību skaits (MI)", len(tix_f), delta="Kritiskie gadījumi")

st.markdown("---")

# 4. VIZUĀĻI - Prasība: Vismaz 2 interaktīvi grafiki
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Atgriešanas pa produktiem (€)")
    # Grupējam datus grafikam
    prod_ref = df_f.groupby('Product_Name')['Refund_Amount_Clean'].sum().sort_values(ascending=False).head(10).reset_index()
    fig1 = px.bar(prod_ref, x='Refund_Amount_Clean', y='Product_Name', orientation='h',
                  color='Refund_Amount_Clean', color_continuous_scale='Reds')
    fig1.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    st.subheader("Sūdzību tēmu sadalījums (OpenAI)")
    topic_counts = tix_f['topic_lv'].value_counts().reset_index()
    fig2 = px.pie(topic_counts, values='count', names='topic_lv', hole=0.4,
                  color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig2, use_container_width=True)

# 5. DATU TABULA - Prasība: 1 datu tabula ("Top problem cases")
st.subheader("🚨 Top problēmgadījumi (Kritiskās sūdzības)")
# Atlasām kritiskākās sūdzības rādīšanai
critical_cases = tix_f[tix_f['priority'] == 'Critical'][['Date_Logged', 'Product_Name', 'topic_lv', 'Message_Body']]
st.dataframe(critical_cases.head(20), use_container_width=True)

st.success("Analīzes rīks ir gatavs darbam.")
