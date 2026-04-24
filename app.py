import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurācija
st.set_page_config(page_title="Business Crisis Dashboard", layout="wide")

@st.cache_data
def load_data():
    # Izmantojam tavus failus
    df = pd.read_csv('dashboard_data.csv')
    tix = pd.read_csv('dashboard_tickets.csv')
    
    # Nodrošinām, ka datums ir pareizā formātā (tāpat kā Notebook)
    date_col = 'Order_Date' if 'Order_Date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    return df, tix

df_master, tickets = load_data()

# 2. Galvenais virsraksts
st.title("🚨 Biznesa procesu krīzes analīzes rīks")
st.markdown(f"**Analīzes dati balstīti uz pēdējo ceturksni**")

# 3. Filtri sānā (Prasība pēc interaktivitātes)
st.sidebar.header("Iestatījumi")
cat_col = 'Kategorija_LV' if 'Kategorija_LV' in df_master.columns else 'Product_Category'
selected_cats = st.sidebar.multiselect("Izvēlies kategorijas:", 
                                     options=df_master[cat_col].unique(), 
                                     default=df_master[cat_col].unique())

# Datu filtrēšana pēc izvēles
df_filtered = df_master[df_master[cat_col].isin(selected_cats)]

# 4. KPI rādītāji (Tieši tie, ko analizēji Notebook)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Kopējie ieņēmumi", f"{df_filtered['Total_Value'].sum():,.2f} €")
with col2:
    # Izmantojam tieši to pašu atgriezumu kolonnu
    refund_col = 'Refund_Amount_Clean'
    st.metric("Kopējie zaudējumi (Refunds)", f"{df_filtered[refund_col].sum():,.2f} €", delta_color="inverse")
with col3:
    st.metric("Sūdzību skaits", len(tickets))

st.divider()

# 5. Vizuāļi (Saskaņā ar tavu analīzi par NordLock Pro un tēmām)
v1, v2 = st.columns(2)

with v1:
    st.subheader("Top 10 zaudējumus radošie produkti")
    # Grupēšana tieši tāda pati kā Notebook analīzē
    top_losses = df_filtered.groupby('Product_Name')[refund_col].sum().sort_values(ascending=False).head(10).reset_index()
    fig_losses = px.bar(top_losses, x=refund_col, y='Product_Name', orientation='h',
                       color=refund_col, color_continuous_scale='Reds',
                       labels={refund_col: 'Zaudējumi (€)', 'Product_Name': 'Produkts'})
    fig_losses.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_losses, use_container_width=True)

with v2:
    st.subheader("Klientu sūdzību iemesli (MI klasifikācija)")
    topic_col = 'topic_lv' if 'topic_lv' in tickets.columns else 'Topic'
    topic_dist = tickets[topic_col].value_counts().reset_index()
    fig_topics = px.pie(topic_dist, values='count', names=topic_col, hole=0.4,
                       color_discrete_sequence=px.colors.sequential.Reds_r)
    st.plotly_chart(fig_topics, use_container_width=True)

# 6. Datu tabula (Pārbaudei)
with st.expander("Skatīt detalizētus sūdzību datus"):
    st.dataframe(tickets[['Ticket_ID', 'Subject', topic_col]].head(20), use_container_width=True)
