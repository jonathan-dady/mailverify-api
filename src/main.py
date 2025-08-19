from flask import Flask, request, jsonify
import smtplib
import dns.resolver
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
BLOCKED_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com"]
MAX_THREADS = 10  # Nombre maximum de threads simultanés pour les vérifications

# Liste de serveurs DNS publics fiables
DNS_SERVERS = ['8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1']

def setup_dns_resolver():
    resolver = dns.resolver.Resolver()
    resolver.nameservers = DNS_SERVERS
    resolver.timeout = 5
    resolver.lifetime = 5
    return resolver

def check_email(email):
    email = email.strip()
    if not EMAIL_REGEX.fullmatch(email):
        return {"email": email, "statut": "Syntaxe invalide", "info": "Adresse mal formée"}

    user, domain = email.split("@")

    if domain.lower() in BLOCKED_DOMAINS:
        return {"email": email, "statut": "Potentiellement valide", "info": "Domaine grand public, SMTP non testé"}

    resolver = setup_dns_resolver()
    
    try:
        # Essayer d'abord les enregistrements MX avec plusieurs serveurs DNS
        mx_records = []
        for dns_server in DNS_SERVERS:
            try:
                resolver.nameservers = [dns_server]
                records = resolver.resolve(domain, 'MX')
                mx_records = [str(mx.exchange).rstrip('.') for mx in records]
                if mx_records:
                    break
            except Exception:
                continue

        # Si pas de MX, essayer les enregistrements A
        if not mx_records:
            try:
                records = resolver.resolve(domain, 'A')
                mx_records = [domain]
            except Exception as e:
                return {"email": email, "statut": "Invalide", "info": f"Domaine introuvable"}

        if not mx_records:
            return {"email": email, "statut": "Invalide", "info": "Pas de serveur de mail trouvé"}

        for mx in mx_records:
            try:
                server = smtplib.SMTP(timeout=10)
                server.connect(mx)
                server.helo(server.local_hostname)
                server.mail('test@example.com')
                code, _ = server.rcpt(email)
                server.quit()

                if code == 250:
                    return {"email": email, "statut": "Valide", "info": "SMTP OK"}
                else:
                    return {"email": email, "statut": "Potentiellement valide", "info": f"SMTP réponse {code}"}
            except Exception as e:
                continue

        return {"email": email, "statut": "Potentiellement valide", "info": "Domaine OK, SMTP bloqué ou timeout"}
    except Exception as e:
        return {"email": email, "statut": "Invalide", "info": f"Erreur de vérification ({str(e)})"}

@app.route("/verify_emails", methods=["POST"])
def verify_emails():
    data = request.get_json()
    if not data or "emails" not in data or not isinstance(data["emails"], list):
        return jsonify({"error": "Veuillez fournir un champ 'emails' avec une liste d'e-mails"}), 400

    emails = data["emails"]
    results = [None] * len(emails)  # Pré-allouer la liste avec la même taille

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Créer un dictionnaire pour stocker l'index original de chaque email
        future_to_index = {executor.submit(check_email, email): idx 
                          for idx, email in enumerate(emails)}
        
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            result = future.result()
            results[idx] = result  # Placer le résultat à l'index original

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
