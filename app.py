"""
Application Streamlit — Analyse exploratoire du catalogue Netflix
Parcours B : Projet Personnel
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Netflix Explorer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# CHARGEMENT & PRÉPARATION DES DONNÉES (cache → une seule fois)
# ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("netflix_titles.csv")

    # Films
    df_movies = df[df["type"] == "Movie"].copy()
    df_movies["duration_min"] = df_movies["duration"].str.extract(r"(\d+)").astype(float)
    df_movies = df_movies.dropna(subset=["duration_min"])
    df_movies["duration_min"] = df_movies["duration_min"].astype(int)
    df_movies["main_genre"] = df_movies["listed_in"].str.split(",").str[0].str.strip()
    df_movies["periode"] = pd.cut(
        df_movies["release_year"],
        bins=[1920, 1980, 2000, 2010, 2025],
        labels=["Avant 1980", "1980-2000", "2000-2010", "2010-2025"],
    )

    # Séries
    df_series = df[df["type"] == "TV Show"].copy()
    df_series["seasons"] = df_series["duration"].str.extract(r"(\d+)").astype(float)
    df_series = df_series.dropna(subset=["seasons"])
    df_series["seasons"] = df_series["seasons"].astype(int)

    # Liste complète des genres (pour le filtre)
    all_genres = (
        df["listed_in"].dropna().str.split(", ").explode().str.strip().unique().tolist()
    )
    all_genres = sorted(set(all_genres))

    return df, df_movies, df_series, all_genres


df, df_movies, df_series, all_genres = load_data()

YEAR_MIN = int(df["release_year"].min())
YEAR_MAX = int(df["release_year"].max())

# ──────────────────────────────────────────────────────────────
# SESSION STATE — valeurs initiales (une seule fois)
# ──────────────────────────────────────────────────────────────
defaults = {
    "page":          "🏠 Accueil",
    "selected_type": "Tous",
    "year_range":    (2000, YEAR_MAX),
    "top_n":         10,
    "selected_genre": "Tous les genres",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────────────────────────
# SIDEBAR — navigation + filtres
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎬 Netflix Explorer")
    st.markdown("---")

    st.radio(
        "Navigation",
        ["🏠 Accueil", "📊 Exploration & Visualisations", "🔍 Analyse Approfondie", "📋 Dashboard"],
        label_visibility="collapsed",
        key="page",
    )

    st.markdown("---")
    st.subheader("🎛️ Filtres globaux")
    st.caption("S'appliquent aux pages Exploration, Analyse et Dashboard.")

    # Filtre 1 — Type de contenu
    st.selectbox("Type de contenu", ["Tous", "Movie", "TV Show"], key="selected_type")

    # Filtre 2 — Plage d'années
    st.slider("Années de sortie", min_value=YEAR_MIN, max_value=YEAR_MAX, key="year_range")

    # Filtre 3 — Genre (NOUVEAU)
    genre_options = ["Tous les genres"] + all_genres
    st.selectbox("Genre", genre_options, key="selected_genre")

    # Filtre 4 — Top N pays
    st.slider("Top N pays à afficher", min_value=5, max_value=20, key="top_n")

    st.markdown("---")
    st.caption("📁 Source : Kaggle — Netflix Movies and TV Shows")

# ──────────────────────────────────────────────────────────────
# LECTURE DES FILTRES
# ──────────────────────────────────────────────────────────────
page           = st.session_state["page"]
selected_type  = st.session_state["selected_type"]
year_range     = st.session_state["year_range"]
top_n          = st.session_state["top_n"]
selected_genre = st.session_state["selected_genre"]

# ──────────────────────────────────────────────────────────────
# APPLICATION DES FILTRES
# df_filtered      → pages EDA (type + années + genre)
# df_movies_filtered → page Analyse (années + genre)
# ──────────────────────────────────────────────────────────────
df_filtered = df.copy()
if selected_type != "Tous":
    df_filtered = df_filtered[df_filtered["type"] == selected_type]
df_filtered = df_filtered[df_filtered["release_year"].between(year_range[0], year_range[1])]
if selected_genre != "Tous les genres":
    df_filtered = df_filtered[
        df_filtered["listed_in"].fillna("").str.contains(selected_genre, regex=False)
    ]

# Films filtrés pour la page Analyse
df_movies_filtered = df_movies[df_movies["release_year"].between(year_range[0], year_range[1])]
if selected_genre != "Tous les genres":
    df_movies_filtered = df_movies_filtered[
        df_movies_filtered["listed_in"].fillna("").str.contains(selected_genre, regex=False)
    ]

# ──────────────────────────────────────────────────────────────
# HELPER
# ──────────────────────────────────────────────────────────────
def empty_msg(detail=""):
    st.info("ℹ️ Aucune donnée à afficher pour cette sélection." + (f" {detail}" if detail else ""))


# ══════════════════════════════════════════════════════════════
#  PAGE 1 — ACCUEIL  (données complètes, pas de filtre)
# ══════════════════════════════════════════════════════════════
if page == "🏠 Accueil":

    # ── Titre ────────────────────────────────────────────────
    st.title("Netflix Explorer")
    st.markdown("*Analyse exploratoire du catalogue Netflix*")
    st.markdown("---")

    # ── Texte de présentation ────────────────────────────────
    st.subheader("Présentation du projet", anchor=False)
    st.markdown(
        """
        Netflix est aujourd'hui l'une des plateformes de streaming les plus importantes au monde.
        Elle propose un catalogue très diversifié comprenant des films et des séries provenant de
        nombreux pays et couvrant différents genres.

        Dans ce contexte, il est intéressant d'analyser la composition du catalogue Netflix afin
        de mieux comprendre les types de contenus proposés aux utilisateurs. Cette analyse
        exploratoire vise à identifier les tendances principales du catalogue, notamment en termes
        de genres dominants, de pays producteurs et de durée des films.

        L'objectif de ce projet est donc d'explorer ces données à l'aide de visualisations
        afin de mettre en évidence les caractéristiques principales du catalogue et son
        évolution dans le temps.
        """
    )

    st.subheader("Source des données", anchor=False)
    st.markdown(
        """
        Les données utilisées proviennent d'un dataset public disponible sur **Kaggle**,
        intitulé *Netflix Movies and TV Shows*. Ce dataset contient des informations sur les
        contenus présents sur Netflix : type (film ou série), pays de production, année de
        sortie, genre, durée et classification d'âge. Ces données permettent de réaliser une
        analyse exploratoire afin d'identifier les principales tendances du catalogue Netflix.
        """
    )

    st.subheader("Question de recherche", anchor=False)
    st.info(
        "Comment la composition du catalogue Netflix évolue-t-elle au fil du temps et quels "
        "types de contenus dominent la plateforme en termes de genres, de pays producteurs "
        "et de caractéristiques des films (durée) ?"
    )

    st.subheader("Pourquoi c'est intéressant ?", anchor=False)
    st.markdown(
        """
        Comprendre la composition du catalogue Netflix permet d'identifier les stratégies de
        contenu adoptées par la plateforme. L'analyse des genres, des pays producteurs et de
        l'évolution des contenus permet de mieux comprendre les préférences du public et les
        tendances de l'industrie du streaming. Cette étude met en évidence les caractéristiques
        principales du catalogue et son évolution au fil des années.
        """
    )

    st.markdown("---")

    # ── KPIs — 2 lignes de 4 colonnes ────────────────────────
    st.subheader("Métriques clés du catalogue", anchor=False)

    total_content = len(df)
    total_movies  = len(df[df["type"] == "Movie"])
    total_series  = len(df[df["type"] == "TV Show"])
    avg_duration  = round(df_movies["duration_min"].mean(), 1)
    median_dur    = int(df_movies["duration_min"].median())
    max_year      = int(df["release_year"].max())
    nb_countries  = df["country"].dropna().str.split(", ").explode().str.strip().nunique()
    miss_rate     = round(df.isnull().mean().mean() * 100, 1)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total de contenus",    f"{total_content:,}")
    k2.metric("Nombre de films",      f"{total_movies:,}",
              f"{total_movies/total_content*100:.1f} % du catalogue")
    k3.metric("Nombre de séries TV",  f"{total_series:,}",
              f"{total_series/total_content*100:.1f} % du catalogue")
    k4.metric("Durée moyenne films",  f"{avg_duration} min")

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Durée médiane films",    f"{median_dur} min")
    k6.metric("Année la plus récente",  f"{max_year}")
    k7.metric("Pays représentés",       f"{nb_countries}")
    k8.metric("Taux valeurs manquantes", f"{miss_rate} %")

    st.markdown("---")

    # ── Aperçu des données ────────────────────────────────────
    col_t1, col_f1 = st.columns([3, 1])
    col_t1.subheader("Aperçu des données", anchor=False)
    n_rows_acc = col_f1.selectbox("Lignes à afficher", [5, 10, 20, 50, 100], index=2, key="n_rows_accueil")
    st.dataframe(df.head(n_rows_acc), use_container_width=True)

    st.markdown("---")

    # ── Description des colonnes ──────────────────────────────
    st.subheader("Description des colonnes principales", anchor=False)
    st.dataframe(
        pd.DataFrame({
            "Colonne": [
                "type", "title", "director", "country",
                "release_year", "rating", "duration", "listed_in",
            ],
            "Description": [
                "Type de contenu : Film (Movie) ou Série TV (TV Show)",
                "Titre du contenu",
                "Réalisateur du film ou de la série",
                "Pays de production",
                "Année de sortie du contenu",
                "Classification d'âge (ex : PG-13, TV-MA…)",
                "Durée du film en minutes ou nombre de saisons pour les séries",
                "Genre(s) du contenu (ex : Dramas, Comedies, Documentaries…)",
            ],
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.caption("Netflix Explorer — Analyse exploratoire du catalogue Netflix | Parcours B")


# ══════════════════════════════════════════════════════════════
#  PAGE 2 — EXPLORATION & VISUALISATIONS
# ══════════════════════════════════════════════════════════════
elif page == "📊 Exploration & Visualisations":

    st.title("Exploration & Visualisations")

    genre_label = selected_genre if selected_genre != "Tous les genres" else "tous genres"
    st.caption(
        f"Filtres actifs : **{selected_type}** | "
        f"Années **{year_range[0]}–{year_range[1]}** | "
        f"Genre : **{genre_label}** | "
        f"**{len(df_filtered):,}** contenus affichés"
    )
    st.markdown("---")

    # ── KPIs dynamiques ──────────────────────────────────────
    st.subheader("Indicateurs clés (sélection filtrée)", anchor=False)

    total_f  = len(df_filtered)
    nb_mov_f = len(df_filtered[df_filtered["type"] == "Movie"])
    nb_ser_f = len(df_filtered[df_filtered["type"] == "TV Show"])
    miss_f   = round(df_filtered.isnull().mean().mean() * 100, 1) if total_f > 0 else 0
    pct_m    = round(nb_mov_f / total_f * 100, 1) if total_f > 0 else 0
    pct_s    = round(nb_ser_f / total_f * 100, 1) if total_f > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Contenus",           f"{total_f:,}")
    c2.metric("Films",              f"{nb_mov_f:,}",  f"{pct_m} %")
    c3.metric("Séries TV",          f"{nb_ser_f:,}",  f"{pct_s} %")
    c4.metric("Valeurs manquantes", f"{miss_f} %")

    st.markdown("---")

    col_t2, col_f2 = st.columns([3, 1])
    col_t2.subheader("Explorer les données filtrées", anchor=False)
    n_rows_eda = col_f2.selectbox("Lignes à afficher", [5, 10, 20, 50, 100], index=2, key="n_rows_eda")
    if total_f > 0:
        cols_show = ["type", "title", "director", "country",
                     "release_year", "rating", "duration", "listed_in"]
        st.dataframe(df_filtered[cols_show].head(n_rows_eda), use_container_width=True)
    else:
        empty_msg()

    st.markdown("---")

    # ── VIZ 1 : Pie Films / Séries ───────────────────────────
    st.subheader("Répartition des types de contenus", anchor=False)
    cl, cr = st.columns([1, 1])

    with cl:
        tc = df_filtered["type"].value_counts().reset_index()
        tc.columns = ["Type", "Nombre"]
        if len(tc) > 0:
            fig = px.pie(tc, names="Type", values="Nombre",
                         title="Films vs Séries TV",
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(title_x=0.5, title_xanchor="center")
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_msg()

    with cr:
        st.markdown("**Interprétation**")
        st.markdown(
            """
            La majorité des contenus sont des **films** (≈ 70 %), les séries représentant
            environ 30 %. Cette répartition reflète la stratégie historique de Netflix qui
            a d'abord misé sur les films avant de développer massivement ses séries originales.
            """
        )
        if len(tc) > 0:
            st.dataframe(tc, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── VIZ 2 : Évolution temporelle ─────────────────────────
    st.subheader("Évolution des contenus au fil des années", anchor=False)

    if total_f > 0:
        cy = df_filtered.groupby(["release_year", "type"]).size().reset_index(name="Nombre")
        if len(cy) > 0:
            fig = px.line(cy, x="release_year", y="Nombre", color="type",
                          title="Évolution du nombre de films et séries sur Netflix",
                          labels={"release_year": "Année", "type": "Type"},
                          color_discrete_sequence=px.colors.qualitative.Set1)
            fig.update_layout(title_x=0.5, title_xanchor="center", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_msg()
    else:
        empty_msg()

    with st.expander("Interprétation"):
        st.markdown(
            """
            Le catalogue reste faible avant 2000, puis explose à partir de **2010**.
            La production de séries accélère nettement après **2015**. La baisse post-**2020**
            est due à des données incomplètes dans le dataset.
            """
        )

    st.markdown("---")

    # ── VIZ 3 : Top 10 genres ────────────────────────────────
    st.subheader("Top 10 des genres les plus présents", anchor=False)

    if total_f > 0:
        gs = df_filtered["listed_in"].dropna().str.split(", ").explode().str.strip()
        if len(gs) > 0:
            tg = gs.value_counts().head(10).reset_index()
            tg.columns = ["Genre", "Nombre"]
            fig = px.bar(tg.sort_values("Nombre"), x="Nombre", y="Genre",
                         orientation="h",
                         title="Top 10 des genres les plus représentés",
                         color="Nombre", color_continuous_scale="Reds")
            fig.update_layout(title_x=0.5, title_xanchor="center", coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_msg()
    else:
        empty_msg()

    with st.expander("Interprétation"):
        st.markdown(
            """
            **International Movies** est le genre le plus représenté, suivi par **Dramas** et
            **Comedies**. Netflix mise sur la diversité internationale et les genres à large
            audience. Les **Documentaries** et **Action & Adventure** sont également bien présents.
            """
        )

    st.markdown("---")

    # ── VIZ 4 : Top N pays ───────────────────────────────────
    st.subheader(f"Top {top_n} des pays producteurs", anchor=False)

    if total_f > 0:
        cs = df_filtered["country"].dropna().str.split(", ").explode().str.strip()
        if len(cs) > 0:
            tc2 = cs.value_counts().head(top_n).reset_index()
            tc2.columns = ["Pays", "Nombre"]
            fig = px.bar(tc2, x="Pays", y="Nombre",
                         title=f"Top {top_n} des pays produisant le plus de contenus",
                         color="Nombre", color_continuous_scale="Blues")
            fig.update_layout(title_x=0.5, title_xanchor="center", coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_msg()
    else:
        empty_msg()

    with st.expander("Interprétation"):
        st.markdown(
            """
            Les **États-Unis** dominent largement. L'**Inde**, le **Royaume-Uni** et le **Canada**
            contribuent de façon significative, illustrant la diversité géographique du catalogue.
            """
        )

    st.markdown("---")

    # ── VIZ 5 : Distribution durée films ─────────────────────
    st.subheader("Distribution de la durée des films", anchor=False)

    df_mov_eda = df_filtered[df_filtered["type"] == "Movie"].copy()
    df_mov_eda["duration_min"] = df_mov_eda["duration"].str.extract(r"(\d+)").astype(float)
    df_mov_eda = df_mov_eda.dropna(subset=["duration_min"])

    if len(df_mov_eda) > 0:
        avg_d = df_mov_eda["duration_min"].mean()
        fig = px.histogram(df_mov_eda, x="duration_min", nbins=40,
                           title="Distribution de la durée des films",
                           labels={"duration_min": "Durée (minutes)"},
                           color_discrete_sequence=["#E50914"])
        fig.add_vline(x=avg_d, line_dash="dash", line_color="black",
                      annotation_text=f"Moyenne : {avg_d:.0f} min",
                      annotation_position="top right")
        fig.update_layout(title_x=0.5, title_xanchor="center", bargap=0.05)
        st.plotly_chart(fig, use_container_width=True)
    else:
        empty_msg("Aucun film dans la sélection — vérifiez le filtre Type de contenu.")

    with st.expander("Interprétation"):
        st.markdown(
            """
            La majorité des films ont une durée comprise entre **80 et 120 minutes**, format
            classique du cinéma. Les films très courts ou très longs restent marginaux.
            """
        )

    st.markdown("---")

    # ── VIZ 6 : Heatmap de corrélation ───────────────────────
    st.subheader("Corrélation entre variables numériques", anchor=False)

    df_corr_src = df_filtered[df_filtered["type"] == "Movie"].copy()
    df_corr_src["duration_min"] = df_corr_src["duration"].str.extract(r"(\d+)").astype(float)
    df_corr_src = df_corr_src.dropna(subset=["duration_min"])

    if len(df_corr_src) >= 5:
        corr_data = df_corr_src[["release_year", "duration_min"]].dropna()
        corr_matrix = corr_data.corr().round(2)

        labels = {"release_year": "Année de sortie", "duration_min": "Durée (min)"}
        corr_display = corr_matrix.rename(index=labels, columns=labels)

        fig_hm = go.Figure(
            data=go.Heatmap(
                z=corr_display.values,
                x=corr_display.columns.tolist(),
                y=corr_display.index.tolist(),
                colorscale="RdBu",
                zmid=0,
                zmin=-1, zmax=1,
                text=corr_display.values,
                texttemplate="%{text:.2f}",
                showscale=True,
            )
        )
        fig_hm.update_layout(
            title="Matrice de corrélation — Année de sortie vs Durée des films",
            title_x=0.5, title_xanchor="center",
            width=500,
            height=400,
        )

        col_hm, col_interp = st.columns([1, 1])
        with col_hm:
            st.plotly_chart(fig_hm, use_container_width=True)
        with col_interp:
            st.markdown("#### 💬 Interprétation")
            val_corr = corr_matrix.loc["release_year", "duration_min"]
            st.markdown(
                f"""
                La corrélation entre l'année de sortie et la durée des films est de
                **{val_corr:.2f}**, ce qui est **faible et légèrement négative**.

                Cela suggère que la durée des films **n'augmente pas** significativement
                avec le temps. Les films récents ne sont pas nécessairement plus longs que
                les anciens — la durée reste relativement stable dans le catalogue Netflix.
                """
            )
    else:
        empty_msg("Pas assez de films pour calculer la corrélation.")


# ══════════════════════════════════════════════════════════════
#  PAGE 3 — ANALYSE APPROFONDIE
#  Filtres appliqués : années + genre (+ type automatiquement Movie)
# ══════════════════════════════════════════════════════════════
elif page == "🔍 Analyse Approfondie":

    st.title("Analyse Approfondie")

    genre_label = selected_genre if selected_genre != "Tous les genres" else "tous genres"
    st.caption(
        f"Filtres actifs : Années **{year_range[0]}–{year_range[1]}** | "
        f"Genre : **{genre_label}** | "
        f"**{len(df_movies_filtered):,}** films analysés"
    )
    st.markdown("---")

    st.subheader("Question de recherche", anchor=False)
    st.info(
        "La durée des films présents sur Netflix a-t-elle évolué au fil du temps ?\n\n"
        "Cette section analyse si la durée des films a changé selon les années, les périodes "
        "et les genres, à travers quatre visualisations complémentaires."
    )
    st.markdown("---")

    # ── GRAPHIQUE 1 : Scatter + tendance ─────────────────────
    st.subheader("Relation entre l'année de sortie et la durée des films", anchor=False)

    if len(df_movies_filtered) >= 2:
        x_vals = df_movies_filtered["release_year"].values
        y_vals = df_movies_filtered["duration_min"].values
        has_trend = False
        try:
            z = np.polyfit(x_vals, y_vals, 1)
            trend_x = np.linspace(x_vals.min(), x_vals.max(), 300)
            trend_y = np.poly1d(z)(trend_x)
            has_trend = True
        except Exception:
            pass

        fig = px.scatter(
            df_movies_filtered, x="release_year", y="duration_min",
            opacity=0.25, color_discrete_sequence=["#636EFA"],
            title="Relation entre l'année de sortie et la durée des films",
            labels={"release_year": "Année de sortie", "duration_min": "Durée (minutes)"},
        )
        if has_trend:
            fig.add_trace(go.Scatter(
                x=trend_x, y=trend_y, mode="lines", name="Tendance",
                line=dict(color="red", width=3),
            ))
        fig.update_layout(title_x=0.5, title_xanchor="center")
        st.plotly_chart(fig, use_container_width=True)
    else:
        empty_msg("Pas assez de films — élargissez les filtres.")

    with st.expander("Interprétation"):
        st.markdown(
            """
            La majorité des films se situe entre **80 et 120 minutes** quelle que soit l'année.
            La ligne rouge indique une **légère pente négative** : la durée diminue très doucement
            avec le temps, probablement liée aux nouveaux formats de consommation sur les plateformes
            de streaming.
            """
        )

    st.markdown("---")

    # ── GRAPHIQUE 2 : Boxplot par période ─────────────────────
    st.subheader("Distribution de la durée selon les périodes", anchor=False)

    df_box = df_movies_filtered.dropna(subset=["periode"])
    if len(df_box) > 0 and df_box["periode"].nunique() > 0:
        fig = px.box(
            df_box, x="periode", y="duration_min", color="periode",
            title="Distribution de la durée des films selon les périodes",
            labels={"periode": "Période", "duration_min": "Durée (minutes)"},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_layout(title_x=0.5, title_xanchor="center", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        empty_msg("Aucune période disponible — élargissez la plage d'années.")

    with st.expander("Interprétation"):
        st.markdown(
            """
            La **médiane** de durée reste stable autour de **100 minutes** d'une période à l'autre.
            Légère baisse pour **2010–2025**. Les nombreux outliers confirment la diversité des
            formats disponibles sur Netflix.
            """
        )

    st.markdown("---")

    # ── GRAPHIQUE 3 : Moyenne mobile ─────────────────────────
    st.subheader("Évolution de la durée moyenne (moyenne mobile 5 ans)", anchor=False)

    if len(df_movies_filtered) >= 2:
        avg_yr = (
            df_movies_filtered.groupby("release_year")["duration_min"]
            .mean().reset_index()
            .rename(columns={"release_year": "Annee", "duration_min": "Duree"})
            .sort_values("Annee")
        )
        avg_yr["MM5"] = avg_yr["Duree"].rolling(window=5, min_periods=1).mean()

        if len(avg_yr) >= 2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=avg_yr["Annee"], y=avg_yr["Duree"],
                mode="lines", name="Durée moyenne annuelle",
                line=dict(color="#636EFA", width=1.5), opacity=0.5,
            ))
            fig.add_trace(go.Scatter(
                x=avg_yr["Annee"], y=avg_yr["MM5"],
                mode="lines", name="Moyenne mobile (5 ans)",
                line=dict(color="red", width=3),
            ))
            fig.update_layout(
                title="Évolution de la durée moyenne des films",
                xaxis_title="Année de sortie",
                yaxis_title="Durée moyenne (minutes)",
                title_x=0.5, title_xanchor="center", hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_msg("Pas assez d'années distinctes.")
    else:
        empty_msg("Pas assez de films — élargissez les filtres.")

    with st.expander("Interprétation"):
        st.markdown(
            """
            Pic historique dans les années **1950–1960** (≈ 170 min), puis stabilisation autour
            de **100–120 min**. La tendance récente pointe vers **95–100 min**, signe d'une
            adaptation aux nouvelles habitudes de consommation sur les plateformes de streaming.
            """
        )

    st.markdown("---")

    # ── GRAPHIQUE 4 : Durée par genre principal ───────────────
    st.subheader("Durée moyenne des films selon le genre principal", anchor=False)

    if len(df_movies_filtered) > 0:
        gd = (
            df_movies_filtered.groupby("main_genre")["duration_min"]
            .mean().dropna()
            .sort_values(ascending=False).head(10).reset_index()
        )
        gd.columns = ["Genre", "Duree_moy"]
        if len(gd) > 0:
            fig = px.bar(
                gd.sort_values("Duree_moy"),
                x="Duree_moy", y="Genre", orientation="h",
                title="Durée moyenne par genre principal (Top 10)",
                labels={"Duree_moy": "Durée moyenne (min)"},
                color="Duree_moy", color_continuous_scale="Oranges",
            )
            fig.update_layout(title_x=0.5, title_xanchor="center", coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_msg()
    else:
        empty_msg("Aucun film dans la sélection — vérifiez le filtre Genre.")

    with st.expander("Interprétation"):
        st.markdown(
            """
            La durée varie sensiblement selon le genre. Les **documentaires** et **drames**
            ont des durées moyennes plus élevées ; les **comédies** sont généralement plus courtes.
            La composition par genre influence directement la durée moyenne globale du catalogue.
            """
        )

    st.markdown("---")

    # ── Insights & Conclusions ────────────────────────────────
    st.subheader("Insights & Conclusions", anchor=False)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Résultats principaux**")
        st.markdown(
            """
            - Durée des films **globalement stable** autour de 90–110 min
            - **Légère tendance à la baisse** dans les années récentes
            - Durée variable selon le **genre** du film
            - Majorité des séries : **1 à 2 saisons** seulement
            - Domination des **États-Unis**, **Inde**, **Royaume-Uni**
            """
        )
        st.markdown("**Surprises dans les données**")
        st.markdown(
            """
            - Grande **variabilité** malgré une moyenne stable
            - Distribution **asymétrique** du nombre de saisons
            - Pic historique dans les années **1950–1960** (≈ 170 min)
            """
        )

    with c2:
        st.markdown("**Recommandations**")
        st.markdown(
            """
            - Maintenir une **diversité de formats** pour tous les publics
            - Équilibrer séries courtes et longues selon les marchés
            - Améliorer les **métadonnées** des contenus récents
            """
        )
        st.markdown("**Limitations**")
        st.markdown(
            """
            - Données **post-2020 incomplètes**
            - Analyse genre basée sur le **premier genre listé** uniquement
            - Pas de données sur les **vues ou les notes** utilisateurs
            - Dataset = **échantillon**, pas le catalogue complet Netflix
            """
        )

    st.markdown("---")
    st.caption("Netflix Explorer — Analyse exploratoire du catalogue Netflix | Parcours B")


# ══════════════════════════════════════════════════════════════
#  PAGE 4 — DASHBOARD INTERACTIF (BONUS)
#  Filtres globaux sidebar : type + années + genre + top_n
# ══════════════════════════════════════════════════════════════
elif page == "📋 Dashboard":

    st.title("Dashboard Interactif")
    st.markdown("*Vue d\'ensemble combinée — tous les filtres sont actifs*")

    genre_label = selected_genre if selected_genre != "Tous les genres" else "tous genres"
    st.caption(
        f"Filtres actifs : **{selected_type}** | "
        f"Années **{year_range[0]}–{year_range[1]}** | "
        f"Genre : **{genre_label}** | "
        f"**{len(df_filtered):,}** contenus affichés"
    )
    st.markdown("---")

    # ── KPIs globaux ─────────────────────────────────────────
    total_f  = len(df_filtered)
    nb_mov_f = len(df_filtered[df_filtered["type"] == "Movie"])
    nb_ser_f = len(df_filtered[df_filtered["type"] == "TV Show"])
    pct_m    = round(nb_mov_f / total_f * 100, 1) if total_f > 0 else 0
    pct_s    = round(nb_ser_f / total_f * 100, 1) if total_f > 0 else 0

    df_mov_db = df_filtered[df_filtered["type"] == "Movie"].copy()
    df_mov_db["duration_min"] = df_mov_db["duration"].str.extract(r"(\d+)").astype(float)
    df_mov_db = df_mov_db.dropna(subset=["duration_min"])
    avg_dur_db = round(df_mov_db["duration_min"].mean(), 1) if len(df_mov_db) > 0 else 0

    nb_countries_db = (
        df_filtered["country"].dropna().str.split(", ").explode().str.strip().nunique()
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Contenus sélectionnés", f"{total_f:,}")
    k2.metric("Films",                 f"{nb_mov_f:,}", f"{pct_m} %")
    k3.metric("Séries TV",             f"{nb_ser_f:,}", f"{pct_s} %")
    k4.metric("Durée moyenne films",   f"{avg_dur_db} min")

    k5, k6, _, __ = st.columns(4)
    k5.metric("Pays représentés", f"{nb_countries_db}")
    k6.metric("Années couvertes",
              f"{year_range[1] - year_range[0] + 1} ans")

    st.markdown("---")

    # ── LIGNE 1 : Pie + Line ─────────────────────────────────
    st.subheader("Composition et évolution du catalogue", anchor=False)
    col1, col2 = st.columns(2)

    with col1:
        tc = df_filtered["type"].value_counts().reset_index()
        tc.columns = ["Type", "Nombre"]
        if len(tc) > 0:
            fig = px.pie(tc, names="Type", values="Nombre",
                         title="Répartition Films / Séries",
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(title_x=0.5, title_xanchor="center", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_msg()

    with col2:
        if total_f > 0:
            cy = df_filtered.groupby(["release_year", "type"]).size().reset_index(name="Nombre")
            if len(cy) > 0:
                fig = px.line(cy, x="release_year", y="Nombre", color="type",
                              title="Évolution du catalogue dans le temps",
                              labels={"release_year": "Année", "type": "Type"},
                              color_discrete_sequence=px.colors.qualitative.Set1)
                fig.update_layout(title_x=0.5, title_xanchor="center", hovermode="x unified", showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                empty_msg()
        else:
            empty_msg()

    st.markdown("---")

    # ── LIGNE 2 : Top genres + Top pays ──────────────────────
    st.subheader("Genres et pays les plus représentés", anchor=False)
    col3, col4 = st.columns(2)

    with col3:
        if total_f > 0:
            gs = df_filtered["listed_in"].dropna().str.split(", ").explode().str.strip()
            if len(gs) > 0:
                tg = gs.value_counts().head(10).reset_index()
                tg.columns = ["Genre", "Nombre"]
                fig = px.bar(tg.sort_values("Nombre"), x="Nombre", y="Genre",
                             orientation="h", title="Top 10 des genres",
                             color="Nombre", color_continuous_scale="Reds")
                fig.update_layout(title_x=0.5, title_xanchor="center", coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                empty_msg()
        else:
            empty_msg()

    with col4:
        if total_f > 0:
            cs = df_filtered["country"].dropna().str.split(", ").explode().str.strip()
            if len(cs) > 0:
                tc2 = cs.value_counts().head(top_n).reset_index()
                tc2.columns = ["Pays", "Nombre"]
                fig = px.bar(tc2, x="Pays", y="Nombre",
                             title=f"Top {top_n} des pays producteurs",
                             color="Nombre", color_continuous_scale="Blues")
                fig.update_layout(title_x=0.5, title_xanchor="center", coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                empty_msg()
        else:
            empty_msg()

    st.markdown("---")

    # ── LIGNE 3 : Histogramme durée + Heatmap corrélation ────
    st.subheader("Analyse des films", anchor=False)
    col5, col6 = st.columns(2)

    with col5:
        if len(df_mov_db) > 0:
            avg_d = df_mov_db["duration_min"].mean()
            fig = px.histogram(df_mov_db, x="duration_min", nbins=35,
                               title="Distribution de la durée des films",
                               labels={"duration_min": "Durée (minutes)"},
                               color_discrete_sequence=["#E50914"])
            fig.add_vline(x=avg_d, line_dash="dash", line_color="black",
                          annotation_text=f"Moy. : {avg_d:.0f} min",
                          annotation_position="top right")
            fig.update_layout(title_x=0.5, title_xanchor="center", bargap=0.05)
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_msg("Aucun film dans la sélection.")

    with col6:
        if len(df_mov_db) >= 5:
            corr = df_mov_db[["release_year", "duration_min"]].corr().round(2)
            labels = {"release_year": "Année de sortie", "duration_min": "Durée (min)"}
            corr_d = corr.rename(index=labels, columns=labels)
            fig_hm = go.Figure(data=go.Heatmap(
                z=corr_d.values,
                x=corr_d.columns.tolist(),
                y=corr_d.index.tolist(),
                colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
                text=corr_d.values, texttemplate="%{text:.2f}",
                showscale=True,
            ))
            fig_hm.update_layout(
                title="Corrélation Année / Durée",
                title_x=0.5, title_xanchor="center", height=350,
            )
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            empty_msg("Pas assez de films pour la corrélation.")

    st.markdown("---")

    # ── TÉLÉCHARGEMENT CSV ────────────────────────────────────
    st.subheader("Télécharger les données filtrées", anchor=False)

    col_dl, col_info = st.columns([2, 3])

    with col_dl:
        if total_f > 0:
            csv = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Télécharger en CSV",
                data=csv,
                file_name=f"netflix_filtre_{selected_type}_{year_range[0]}_{year_range[1]}.csv",
                mime="text/csv",
            )
        else:
            empty_msg("Aucune donnée à télécharger.")

    with col_info:
        st.markdown(
            f"""
            Le fichier téléchargé contiendra **{total_f:,} lignes** correspondant
            à la sélection actuelle :
            type **{selected_type}**, années **{year_range[0]}–{year_range[1]}**,
            genre **{genre_label}**.
            """
        )

    st.markdown("---")
    st.caption("Netflix Explorer — Dashboard interactif | Parcours B — BONUS")
