# API de Vérification d'Emails

## Aperçu
L'API de Vérification d'Emails est une application basée sur Flask qui fournit un endpoint pour vérifier la validité des adresses email. Elle vérifie la syntaxe de l'email, le domaine, et tente de se connecter au serveur de messagerie pour confirmer si l'adresse email est valide.

## Installation

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/jonathan-dady/mailverify-api.git
   cd mailverify-api
   ```

2. Créez un environnement virtuel (optionnel mais recommandé) :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows utilisez `venv\Scripts\activate`
   ```

3. Installez les dépendances requises :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

Pour lancer l'application, exécutez la commande suivante :

```bash
python src/main.py
```

L'API sera disponible à l'adresse `http://localhost:5000/verify_emails`.

### Exemple d'utilisation avec curl

```bash
curl --location 'http://127.0.0.1:5000/verify_emails' \
--header 'Content-Type: application/json' \
--data-raw '{
  "emails": [
    "john.doe@example.com",
    "contact@entreprise-fictive.com",
    "service.client@societe.test",
    "info@organisation.demo",
    "support@tech-demo.com",
    "contact@startup.test",
    "commercial@business.example",
    "info@company.demo",
    "service@enterprise.test",
    "contact@corporation.example"
  ]
}'
```

## Point d'accès API

### POST /verify_emails

#### Corps de la requête
```json
{
  "emails": ["exemple1@exemple.com", "exemple2@exemple.com"]
}
```

#### Réponse
La réponse sera un tableau JSON contenant les résultats de vérification pour chaque email.

## Exécution des Tests

Pour exécuter les tests unitaires, utilisez la commande suivante :

```bash
pytest tests/test_main.py
```

## Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou à soumettre une pull request pour toute amélioration ou correction de bug.

---
Développé