# gcp-tools

Variables d'environnement à préciser : 

- SQL_INSTANCE_NAME (Nom de l'instance SQL sur GCP)
- DB_USER (Login pour la base de données)
- DB_PASS (Mot de passe base de données)
- DB_NAME	(Nom de la base de données)
- PROJECT_NAME (Nom du projet GCP)
- STORAGE_NAME (Nom du bucket Google Storage)
- LOCATION (Location, exemple : europe-west1)

## Initialiser l'outil
```
from gcptools import GCP_Tools
gcptools = GCP_Tools()
```

## Jouer avec la base de données 

```

_SQL = "UPDATE table SET field='new_value' WHERE field='old_value'"
gcptools.execute(_SQL)
```