import os
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

st.set_page_config(page_title="Media Trends Dashboard", page_icon="📰", layout="wide")

# Custom CSS for Pink Violet Dark Theme
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f0524 0%, #1e0a4d 100%);
    }
    .main {
        background: transparent;
    }
    h1, h2, h3, p {
        color: #e0d0ff !important;
        font-family: 'Inter', sans-serif;
    }
    .stMetric {
        background: rgba(255, 0, 255, 0.05);
        border: 1px solid rgba(255, 0, 255, 0.2);
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricValue"] {
        color: #ff00ff !important;
        font-size: 2rem !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #ff00ff, #7a00ff);
        color: white;
        border: none;
        border-radius: 20px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px #ff00ff;
    }
    .stDivider {
        border-bottom: 2px solid rgba(255, 0, 255, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=os.environ.get("POSTGRES_PORT", 5432),
        dbname=os.environ.get("POSTGRES_DB", "mediatrends"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres")
    )
    data = {}
    try:
        data['source'] = pd.read_sql("SELECT * FROM agg_articles_by_source", conn)
    except:
        data['source'] = pd.DataFrame(columns=['source', 'number_of_articles'])
    try:
        data['day'] = pd.read_sql("SELECT * FROM agg_articles_by_day", conn)
    except:
        data['day'] = pd.DataFrame(columns=['publication_date', 'number_of_articles'])
    try:
        data['category'] = pd.read_sql("SELECT * FROM agg_articles_by_category", conn)
    except:
        data['category'] = pd.DataFrame(columns=['category', 'number_of_articles'])
    try:
        data['keywords'] = pd.read_sql("SELECT * FROM agg_top_keywords", conn)
    except:
        data['keywords'] = pd.DataFrame(columns=['keyword', 'frequency'])
    conn.close()
    return data

data = load_data()

st.title("🔮 Dashboard des tendances médiatiques")
st.markdown("<p style='font-size: 1.2rem; opacity: 0.8;'>Visualisation interactive des données avec un pipeline Big Data moderne.</p>", unsafe_allow_html=True)

st.sidebar.header("Filtres")
st.sidebar.info("Note : Les données de la couche Gold étant pré-agrégées, ces filtres s'appliquent de manière isolée sur chaque graphique concerné.")

all_sources = data['source']['source'].tolist() if 'source' in data['source'].columns else []
selected_sources = st.sidebar.multiselect("Filtrer par Source", options=all_sources, default=all_sources)

all_categories = data['category']['category'].tolist() if 'category' in data['category'].columns else []
selected_categories = st.sidebar.multiselect("Filtrer par Catégorie", options=all_categories, default=all_categories)

total_articles = data['source']['number_of_articles'].sum() if not data['source'].empty else 0

st.subheader("Indicateurs Clés")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total des Articles", f"{int(total_articles):,}")
col2.metric("Sources Analysées", len(all_sources))
col3.metric("Catégories Couvertes", len(all_categories))
col4.metric("Mots-clés Pertinents", len(data['keywords']) if not data['keywords'].empty else 0)

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Répartition des Articles par Source")
    if not data['source'].empty and selected_sources:
        df_source = data['source'][data['source']['source'].isin(selected_sources)]
        fig = px.bar(df_source, x='source', y='number_of_articles', color='source',
                     text='number_of_articles',
                     color_discrete_sequence=['#ff00ff', '#7a00ff', '#e0d0ff', '#9d00ff'],
                     labels={'source': 'Source', 'number_of_articles': "Nombre d'articles"})
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e0d0ff',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour les sources.")

    st.subheader("Répartition des Articles par Catégorie")
    if not data['category'].empty and selected_categories:
        df_cat = data['category'][data['category']['category'].isin(selected_categories)]
        fig = px.pie(df_cat, names='category', values='number_of_articles', hole=0.4,
                     color_discrete_sequence=['#ff00ff', '#7a00ff', '#e0d0ff', '#9d00ff', '#4b0082'])
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e0d0ff',
            legend_font_color='#e0d0ff'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour les catégories.")

with col_right:
    st.subheader("Volume de Publication par Jour")
    if not data['day'].empty:
        df_day = data['day'].sort_values(by='publication_date')
        fig = px.line(df_day, x='publication_date', y='number_of_articles', markers=True)
        fig.update_traces(line_color='#ff00ff', marker=dict(size=10, color='#7a00ff', line=dict(width=2, color='#e0d0ff')))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e0d0ff',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour les jours.")

    st.subheader("Top 10 Mots-clés les plus fréquents")
    if not data['keywords'].empty:
        df_kw = data['keywords'].nlargest(10, 'frequency').sort_values(by='frequency', ascending=True)
        fig = px.bar(df_kw, x='frequency', y='keyword', orientation='h',
                     color='frequency', color_continuous_scale=['#4b0082', '#7a00ff', '#ff00ff'])
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e0d0ff',
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(showgrid=False),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour les mots-clés.")