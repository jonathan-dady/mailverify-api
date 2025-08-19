import smtplib
import dns.resolver
import socket
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# === LISTE DES EMAILS DANS LE CODE ===
emails_to_check = [
    "jonathanrabemananoro@gmail.com",
    "rivoarivelo@yahoo.fr",
    "autre@mail.com"
]

# Regex simple pour valider la syntaxe
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

# Domaines “gros fournisseurs” à ne pas vérifier via SMTP
BLOCKED_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com"]

# Nombre de threads pour exécution parallèle
MAX_THREADS = 10

def check_email(email):
    email = email.strip()
    if not EMAIL_REGEX.fullmatch(email):
        return email, {"statut": "Invalide", "info": "Syntaxe incorrecte"}

    user, domain = email.split("@")

    # Domaines bloqués → check MX uniquement
    if domain.lower() in BLOCKED_DOMAINS:
        try:
            records = dns.resolver.resolve(domain, 'MX')
            if records:
                return email, {"statut": "Potentiellement valide", "info": "Domaine OK, SMTP non testé"}
        except Exception as e:
            return email, {"statut": "Invalide", "info": f"MX record introuvable ({e})"}

    # Pour autres domaines → vérification SMTP
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)

        server = smtplib.SMTP(timeout=10)
        server.set_debuglevel(0)
        server.connect(mx_record)
        server.helo(server.local_hostname)
        server.mail('test@example.com')
        code, message = server.rcpt(email)
        server.quit()

        if code == 250:
            return email, {"statut": "Valide", "info": "SMTP OK"}
        else:
            return email, {"statut": "Invalide", "info": f"SMTP réponse {code}"}
    except Exception as e:
        return email, {"statut": "Invalide", "info": f"Erreur {e}"}

# === EXÉCUTION MULTI-THREAD ET AFFICHAGE JSON ===
results = {}

with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    futures = [executor.submit(check_email, email) for email in emails_to_check]
    for future in as_completed(futures):
        email, result = future.result()
        results[email] = result

print(json.dumps(results, indent=4, ensure_ascii=False))
