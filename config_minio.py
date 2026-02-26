import config
from pathlib import Path
from alive_progress import alive_bar
from botocore.exceptions import ClientError


# Connexion au serveur MinIO
def s3_connect():
    s3_client = config.s3
    return s3_client


# Création du bucket onyxia si il n'existe pas
def s3_create_bucket(s3_client, s3_bucket):
    try:
        s3_client.head_bucket(Bucket=s3_bucket)
        print(f"Bucket '{s3_bucket}' existe déjà")
        return s3_bucket

    except ClientError as err:
        error_code = int(err.response["Error"]["Code"])

        if error_code == 404:
            print(f"Création du bucket '{s3_bucket}'")
            s3_client.create_bucket(Bucket=s3_bucket)
            return s3_bucket
        else:
            raise
        


# Téléversement des fichiers .txt le bucket MinIO onyxia
def s3_upload_files(s3_client, s3_bucket):
    print("Téléversement des fichiers vers MinIO Onyxia...")
    base_path = Path(config.DOWNLOAD_PATH)
    txt_files = list(base_path.rglob("*.txt"))

    if not txt_files:
        print("Aucun fichier à téléverser.")
        return

    # Récupération des objets existants
    existing_objects = set()
    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=s3_bucket):
        for obj in page.get("Contents", []):
            existing_objects.add(obj["Key"])

    with alive_bar(len(txt_files), title="Téléversement...") as bar:
        for path in txt_files:
            # object = path.relative_to(base_path).as_posix()
            object_name = "Texts/"+path.relative_to(base_path).name

            if object_name in existing_objects:
                print(f"{object_name} existe déjà.")
            else:
                s3_client.upload_file(str(path), s3_bucket, object_name)
                print(f"{object_name} téléversé.")
                # path.unlink()

            bar()

    print("Téléversement terminé.")


# Suppression des fichiers .txt du Bucket MinIO onyxia
def s3_delete_files(s3_client, s3_bucket):
    print("Suppression des fichiers en cours...")
    paginator = s3_client.get_paginator("list_objects_v2")
    
    for page in  paginator.paginate(Bucket=s3_bucket):

        if "Contents" in page:
            object = [{"Key": obj["Key"]} for obj in page["Contents"]]
            with alive_bar(len(object), title="Suppression...") as bar:
                for obj in object:
                    s3_client.delete_objects(Bucket=s3_bucket,Delete={"Objects": [obj]})
                    print(f"{obj['Key']} supprimé.")
                    bar()
    
    print("Suppression terminée")



    





