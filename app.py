import streamlit as st
import config_minio
import config_duckdb
from st_aggrid import GridOptionsBuilder, AgGrid, ColumnsAutoSizeMode, GridUpdateMode
import config_fichiers
import config_minio
import config_duckdb
import config_csv


# Connexion à MinIO et DuckDB
s3_client=config_minio.s3_connect()
s3_bucket = "juliencnam"
conn = config_duckdb.connect()

# Configuration de la page Streamlit en mode large
st.set_page_config(layout="wide")

@st.dialog("Êtes-vous sûr de vouloir supprimer les fichiers du serveur MinIO Onyxia ?")
def confirmer():
    if st.button("Confirmer la suppression", type="primary"):
        config_minio.s3_delete_files(s3_client,s3_bucket)
        st.success("Suppression vers MinIO onyxia terminé.")
  


# Définitions des pages de l'application Streamlit
# Page d'accueil
def Accueil():
    st.title("Bridge : Gestion des Documents")
    st.write("Cette interface permet de gérer les documents ACCO , de les téléverser vers MinIO et d'insérer leurs métadonnées dans DuckDB.")
    st.write("Elle est basée sur un script Python qui automatise le téléchargement, l'extraction, le téléversement et l'insertion des métadonnées.")
    st.write("Elle permet aussi de consulter les documents stockés dans MinIO et leurs métadonnées dans DuckDB ainsi que d'en extraire un csv en damier.")

# Page de scripts
def Scripts():
    st.title("Scripts")

    # Gestion des fichiers : téléchargement et extraction
    if st.button("Télécharger, extraire et convertir les fichiers .docx"):
        config_fichiers.ensure_download_path()
        config_fichiers.ensure_extract_files()
        config_fichiers.ensure_conversion_txt()
        st.success("Téléchargement, extraction et conversion terminés.")

    # Connexion à MinIO et téléversement des fichiers .txt
    if st.button("Téléverser les fichiers vers le serveur MinIO Onyxia"):
        config_minio.s3_upload_files(s3_client,s3_bucket)
        st.success("Téléversement vers MinIO onyxia terminé.")
    
    # Connexion à MinIO et suppression des fichiers .txt
    if st.button("Supprimer les fichiers du serveur MinIO Onyxia",type="primary"):
        confirmer()
        

    # Connexion à DuckDB et insertion des métadonnées
    if st.button("Insérer les métadonnées dans DuckDB"):
        config_duckdb.create_table_metadata(conn)
        config_duckdb.insert_metadata(conn)
        st.success("Insertion des métadonnées dans DuckDB terminées.")

    # Création du csv avec les métadonnées qualitatives en booléan
    if st.button("Créer le csv métadonnées"):
        config_csv.get_csv(conn)
        st.success("Création du csv terminé.")
    


# Page des fichiers et de leurs métadonnées
def Fichiers():
    st.title("Fichiers")
    st.write("Liste des fichiers :")    

    # Pagination du DataFrame
    try:
        total_rows = conn.execute("SELECT COUNT(*) FROM metadonnee").fetchone()[0]
    except Exception as err:
        st.error(f"Erreur lors de la récupération des métadonnées depuis DuckDB. Veuillez vous assurer que la base existe et qu'elle n'est pas vide")
        return
    
        
    page_size = 20
    # Barre de recherche du DataFrame
    search = st.text_input("Recherche")
    # Pagination
    page = st.number_input("Page",min_value=1,max_value=(total_rows//page_size)+1,step=1)
    offset = (page-1)*page_size

    where = ""
    if search:
        where = f""" WHERE reference ILIKE '%{search}%' or titre ILIKE '%{search}%' or ape ILIKE '%{search}%' or nature ILIKE '%{search}%' 
        or raison_sociale ILIKE '%{search}%' or siret ILIKE '%{search}%' or  secteur ILIKE '%{search}%' or signataires ILIKE '%{search}%' or thematique ILIKE '%{search}%' """

    # Récupération des métadonnées depuis DuckDB
    try:
        df = conn.execute(f"SELECT * FROM metadonnee {where if where else ""}  order by date_signature DESC LIMIT {page_size} OFFSET {offset} ").df()

    except Exception as err:
        st.error(f"Erreur lors de la récupération des métadonnées depuis DuckDB : {err}")
        return
    

    # Affichage des métadonnées dans une grille interactive
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode="single", use_checkbox=True)
    gb.configure_pagination(enabled=False)
    gb.configure_side_bar()
    gb.configure_grid_options(domLayout='autoHeight',autoSizeStrategy={"type": "fitGridWidth" },rowHeight=40) #fitCellContents "defaultMinWidth": 150
    gridOptions = gb.build()

    # Affichage de la grille avec AgGrid
    data = AgGrid(df,
    gridOptions=gridOptions,
    enable_enterprise_modules=True,
    allow_unsafe_jscode=True,
    update_on=["selectionChanged"],
    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS)
    
    # Récupération de la ligne sélectionnée
    selected_rows = data["selected_rows"]

    # Affichage du document PDF sélectionné
    if selected_rows is not None and not selected_rows.empty:
        st.session_state.selected_ref = selected_rows["reference"].iloc[0]
        selected_ref = st.session_state.selected_ref
        response = s3_client.list_objects_v2(Bucket=s3_bucket,Prefix="Texts/"+selected_ref)
        obj = next(iter(response.get("Contents",[])), None)
        text = s3_client.get_object(Bucket=s3_bucket, Key=obj["Key"])["Body"].read().decode()
        st.text_area("Contenu du document", value=text, height=300, label_visibility="collapsed")
                    

def Documentation():
    st.title("Documentation")
    st.write("Documentation de l'application :")
    st.pdf("readme.pdf",height=800)

# Configuration de la navigation entre les pages
nav = st.navigation([Accueil, Scripts, Fichiers, Documentation],)
# Lancement de l'application Streamlit 
nav.run()