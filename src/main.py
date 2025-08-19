from flask import Flask, request, jsonify
import smtplib
import dns.resolver
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
BLOCKED_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com"]
MAX_THREADS = 10  # Nombre maximum de threads simultanés pour les vérifications

def check_email(email):
    email = email.strip()
    if not EMAIL_REGEX.fullmatch(email):
        return {"email": email, "statut": "Syntaxe invalide", "info": "Adresse mal formée"}

    user, domain = email.split("@")

    if domain.lower() in BLOCKED_DOMAINS:
        try:
            records = dns.resolver.resolve(domain, 'MX')
            if records:
                return {"email": email, "statut": "Potentiellement valide", "info": "Domaine OK, SMTP non testé"}
        except Exception as e:
            return {"email": email, "statut": "Invalide", "info": f"MX introuvable ({e})"}

    try:
        records = dns.resolver.resolve(domain, 'MX')
        if not records:
            return {"email": email, "statut": "Invalide", "info": "Pas de MX trouvé"}

        for mx in records:
            mx_record = str(mx.exchange)
            try:
                server = smtplib.SMTP(timeout=10)
                server.connect(mx_record)
                server.helo(server.local_hostname)
                server.mail('test@example.com')
                code, _ = server.rcpt(email)
                server.quit()

                if code == 250:
                    return {"email": email, "statut": "Valide", "info": "SMTP OK"}
                else:
                    return {"email": email, "statut": "Potentiellement valide", "info": f"SMTP réponse {code}"}
            except Exception:
                continue

        return {"email": email, "statut": "Potentiellement valide", "info": "Domaine OK, SMTP bloqué ou timeout"}
    except Exception as e:
        return {"email": email, "statut": "Invalide", "info": f"Erreur MX ({e})"}

@app.route("/verify_emails", methods=["POST"])
def verify_emails():
    data = request.get_json()
    if not data or "emails" not in data or not isinstance(data["emails"], list):
        return jsonify({"error": "Veuillez fournir un champ 'emails' avec une liste d'e-mails"}), 400

    emails = data["emails"]
    results = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_email = {executor.submit(check_email, email): email for email in emails}
        for future in as_completed(future_to_email):
            result = future.result()
            results.append(result)

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
