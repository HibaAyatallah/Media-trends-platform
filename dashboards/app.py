import os
import streamlit as st
import pandas as pd
import plotly.express as px

# Configuration de la page (doit être le premier appel Streamlit)
st.set_page_config(
    page_title="Media Trends Dashboard",
    page_icon="📰",
    layout="wide"
)

# Fonction pour charger les données CSV avec mise en cache pour optimiser les performances
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    gold_dir = os.path.join(project_root, "data_lake", "gold")
    
    data = {}
    
    # Chargement robuste de chaque fichier (gère l'absence de fichier avec des DataFrames vides)
    try:
        data['source'] = pd.read_csv(os.path.join(gold_dir, "articles_by_source.csv"))
    except FileNotFoundError:
        data['source'] = pd.DataFrame(columns=['source', 'number_of_articles'])
        
    try:
        data['day'] = pd.read_csv(os.path.join(gold_dir, "articles_by_day.csv"))
    except FileNotFoundError:
        data['day'] = pd.DataFrame(columns=['publication_date', 'number_of_articles'])
        
    try:
        data['category'] = pd.read_csv(os.path.join(gold_dir, "articles_by_category.csv"))
    except FileNotFoundError:
        data['category'] = pd.DataFrame(columns=['category', 'number_of_articles'])
        
    try:
        data['keywords'] = pd.read_csv(os.path.join(gold_dir, "top_keywords.csv"))
    except FileNotFoundError:
        data['keywords'] = pd.DataFrame(columns=['keyword', 'frequency'])
        
    return data

# Chargement des données
data = load_data()

# Titre principal
st.title("📰 Dashboard des tendances médiatiques")
st.markdown("Visualisation interactive des données extraites, nettoyées et agrégées par notre pipeline de données.")

# ----------------- SIDEBAR ET FILTRES -----------------
st.sidebar.header("Filtres")
st.sidebar.info("Note : Les données de la couche Gold étant pré-agrégées, "
                "ces filtres s'appliquent de manière isolée sur chaque graphique concerné.")

# Filtre par source
all_sources = data['source']['source'].tolist() if 'source' in data['source'].columns else []
selected_sources = st.sidebar.multiselect(
    "Filtrer par Source",
    options=all_sources,
    default=all_sources
)

# Filtre par catégorie
all_categories = data['category']['category'].tolist() if 'category' in data['category'].columns else []
selected_categories = st.sidebar.multiselect(
    "Filtrer par Catégorie",
    options=all_categories,
    default=all_categories
)

# ----------------- INDICATEURS CLÉS -----------------
# Calcul du nombre total d'articles depuis l'agrégation par source
total_articles = data['source']['number_of_articles'].sum() if not data['source'].empty else 0

st.subheader("Indicateurs Clés")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total des Articles", f"{total_articles:,}")
col2.metric("Sources Analysées", len(all_sources))
col3.metric("Catégories Couvertes", len(all_categories))
col4.metric("Mots-clés Pertinents", len(data['keywords']) if not data['keywords'].empty else 0)

st.divider()

# ----------------- GRAPHIQUES -----------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Répartition des Articles par Source")
    if not data['source'].empty:
        # Application du filtre source
        df_source = data['source'][data['source']['source'].isin(selected_sources)]
        fig_source = px.bar(
            df_source, 
            x='source', 
            y='number_of_articles', 
            color='source', 
            text='number_of_articles',
            labels={'source': 'Source', 'number_of_articles': "Nombre d'articles"}
        )
        fig_source.update_traces(textposition='outside')
        st.plotly_chart(fig_source, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour les sources.")

    st.subheader("Répartition des Articles par Catégorie")
    if not data['category'].empty:
        # Application du filtre catégorie
        df_category = data['category'][data['category']['category'].isin(selected_categories)]
        fig_category = px.pie(
            df_category, 
            names='category', 
            values='number_of_articles', 
            hole=0.4,
            labels={'category': 'Catégorie'}
        )
        st.plotly_chart(fig_category, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour les catégories.")

with col_right:
    st.subheader("Volume de Publication par Jour")
    if not data['day'].empty:
        # On s'assure que la date est triée
        df_day = data['day'].sort_values(by='publication_date')
        fig_day = px.line(
            df_day, 
            x='publication_date', 
            y='number_of_articles', 
            markers=True,
            labels={'publication_date': 'Date de publication', 'number_of_articles': "Articles publiés"}
        )
        st.plotly_chart(fig_day, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour les jours.")

    st.subheader("Top 10 Mots-clés les plus fréquents")
    if not data['keywords'].empty:
        # Récupération des 10 premiers mots-clés (les données doivent déjà être triées par fréquence, mais on assure)
        df_top10 = data['keywords'].nlargest(10, 'frequency').sort_values(by='frequency', ascending=True)
        fig_keywords = px.bar(
            df_top10, 
            x='frequency', 
            y='keyword', 
            orientation='h', 
            color='frequency', 
            color_continuous_scale='Blues',
            labels={'frequency': 'Fréquence', 'keyword': 'Mot-clé'}
        )
        st.plotly_chart(fig_keywords, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour les mots-clés.")
