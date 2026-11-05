"""Assistant conversationnel de TalentConnect (version à règles, sans service externe).

Il comprend des intentions par mots-clés et s'appuie sur le contexte réel de
l'utilisateur (profil, offres recommandées, candidatures). Évolution prévue :
brancher un modèle de langage derrière la même fonction `reply`.
"""
import unicodedata


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _has(text: str, *words: str) -> bool:
    return any(w in text for w in words)


def generate_cover_letter(name: str, education: str, offer_title: str, company: str,
                          matched: list[str], missing: list[str]) -> str:
    who = f"Actuellement {education}, je" if education else "Je"
    lines = [
        "Madame, Monsieur,",
        "",
        f"{who} me permets de vous adresser ma candidature pour le poste « {offer_title} » au sein de {company}.",
    ]
    if matched:
        lines += ["", f"Mon profil correspond à votre besoin : je maîtrise notamment {', '.join(matched)}."]
    if missing:
        lines += [f"Je suis par ailleurs motivé(e) pour renforcer rapidement mes compétences en {', '.join(missing[:3])}."]
    lines += [
        "",
        "Sérieux(se), curieux(se) et attaché(e) au travail bien fait, je serais heureux(se) "
        "de mettre mes compétences au service de votre équipe et de vous rencontrer lors d'un entretien.",
        "",
        "Dans l'attente de votre retour, je vous prie d'agréer, Madame, Monsieur, "
        "l'expression de mes salutations distinguées.",
        "",
        name or "Le candidat",
    ]
    return "\n".join(lines)


def reply(message: str, role: str, ctx: dict) -> dict:
    t = _norm(message)
    name = ctx.get("first_name") or ""
    hello = f"Bonjour {name} !" if name else "Bonjour !"

    if role == "company":
        return _reply_company(t, hello, ctx)
    return _reply_candidate(t, hello, ctx)


def _reply_candidate(t: str, hello: str, ctx: dict) -> dict:
    skills = ctx.get("skills") or []
    top = ctx.get("top_offers") or []
    qr_default = ["Améliorer mon CV", "Préparer un entretien", "Quelles offres pour moi ?", "Lettre de motivation"]

    if _has(t, "bonjour", "salut", "hello", "bonsoir", "coucou"):
        return {"reply": f"{hello} Je suis l'assistant TalentConnect. Je peux vous aider sur votre CV, "
                         "vos candidatures, la préparation d'entretien et la recherche d'offres.",
                "quick_replies": qr_default}

    if _has(t, "merci"):
        return {"reply": "Avec plaisir ! Bonne chance pour vos candidatures.", "quick_replies": qr_default}

    if _has(t, "offre", "emploi", "recommand", "poste", "trouver", "cherche"):
        if top:
            lines = [f"• {o['title']} ({o['company']}) : compatibilité {o['score']} %" for o in top[:3]]
            return {"reply": "Voici les offres les plus adaptées à votre profil :\n" + "\n".join(lines) +
                             "\n\nRetrouvez-les dans « Mon espace > Recommandations ».",
                    "quick_replies": ["Quelles compétences développer ?", "Améliorer mon CV"]}
        return {"reply": "Je n'ai pas encore d'offre à vous recommander. Complétez vos compétences "
                         "dans votre profil ou déposez votre CV : je détecterai vos compétences automatiquement.",
                "quick_replies": ["Améliorer mon CV"]}

    if _has(t, "competence", "skill", "apprendre", "developper", "formation"):
        gaps = ctx.get("skill_gaps") or []
        if gaps:
            return {"reply": "Les compétences qui reviennent dans les offres et qui manquent à votre profil : "
                             f"{', '.join(gaps[:5])}. Les ajouter augmentera vos scores de compatibilité.",
                    "quick_replies": ["Quelles offres pour moi ?"]}
        if not skills:
            return {"reply": "Votre profil ne contient pas encore de compétences. Ajoutez-les (séparées par des "
                             "virgules) ou déposez votre CV PDF pour qu'elles soient détectées automatiquement."}
        return {"reply": f"Vos compétences actuelles : {', '.join(skills[:8])}. Elles couvrent bien les offres "
                         "actuelles. Continuez à enrichir votre profil avec des projets concrets."}

    if _has(t, "cv", "curriculum"):
        msg = ("Conseils pour un bon CV :\n• 1 page (2 maximum), claire et sans fautes\n"
               "• Un titre précis (ex. « Étudiant en génie logiciel »)\n• Vos compétences clés en haut\n"
               "• Des projets concrets avec des résultats\n• Format PDF, nom de fichier professionnel")
        if not ctx.get("has_cv"):
            msg += "\n\nVous n'avez pas encore déposé de CV : faites-le dans « Mon espace > Profil »."
        return {"reply": msg, "quick_replies": ["Lettre de motivation", "Préparer un entretien"]}

    if _has(t, "lettre", "motivation"):
        return {"reply": "Une bonne lettre de motivation : 1) pourquoi cette entreprise, 2) ce que vous apportez "
                         "(compétences précises), 3) votre disponibilité. Astuce : en cliquant sur « Postuler », "
                         "je génère automatiquement un brouillon adapté à l'offre, que vous pouvez modifier.",
                "quick_replies": ["Préparer un entretien", "Quelles offres pour moi ?"]}

    if _has(t, "entretien", "interview"):
        return {"reply": "Préparer un entretien :\n• Relisez l'offre et renseignez-vous sur l'entreprise\n"
                         "• Préparez une présentation de 1 minute\n• Ayez 2 exemples concrets de projets\n"
                         "• Préparez 2 questions à poser au recruteur\n• Soyez à l'heure (ou connecté 5 min avant)",
                "quick_replies": ["Améliorer mon CV", "Lettre de motivation"]}

    if _has(t, "stage", "convention"):
        return {"reply": "Pour un stage : vérifiez la durée exigée par votre établissement, demandez la convention "
                         "à votre école dès que l'entreprise vous accepte, et précisez vos dates de disponibilité "
                         "dans votre candidature.", "quick_replies": ["Quelles offres pour moi ?"]}

    if _has(t, "candidature", "statut", "postule"):
        n = ctx.get("applications_count", 0)
        if n:
            return {"reply": f"Vous avez {n} candidature(s). Consultez leur statut dans « Mon espace > Candidatures » : "
                             "vous êtes aussi notifié à chaque changement.", "quick_replies": ["Quelles offres pour moi ?"]}
        return {"reply": "Vous n'avez pas encore postulé. Parcourez les offres : le score de compatibilité vous "
                         "indique celles qui vous correspondent le mieux.", "quick_replies": ["Quelles offres pour moi ?"]}

    return {"reply": "Je n'ai pas bien compris, mais voici ce que je sais faire : conseils CV, lettre de motivation, "
                     "préparation d'entretien, compétences à développer et offres adaptées à votre profil.",
            "quick_replies": qr_default}


def _reply_company(t: str, hello: str, ctx: dict) -> dict:
    qr = ["Rédiger une bonne offre", "Trouver des candidats", "Gérer les candidatures"]
    if _has(t, "bonjour", "salut", "hello", "bonsoir"):
        return {"reply": f"{hello} Je peux vous aider à rédiger vos offres, trouver les bons profils "
                         "et suivre vos candidatures.", "quick_replies": qr}
    if _has(t, "merci"):
        return {"reply": "Avec plaisir !", "quick_replies": qr}
    if _has(t, "offre", "rediger", "publier", "annonce"):
        return {"reply": "Une offre efficace : un titre précis, 3 à 5 missions concrètes, les compétences requises "
                         "(listées, séparées par des virgules : c'est ce qui alimente le matching IA), le lieu et "
                         "la durée pour un stage.", "quick_replies": ["Trouver des candidats"]}
    if _has(t, "candidat", "profil", "talent", "trouver"):
        return {"reply": "Dans « Espace entreprise > Talents », choisissez une offre : l'IA classe les profils "
                         "inscrits par compatibilité et indique les compétences en commun et manquantes.",
                "quick_replies": ["Gérer les candidatures"]}
    if _has(t, "candidature", "statut", "gerer", "entretien"):
        n = ctx.get("pending", 0)
        extra = f" Vous avez {n} candidature(s) à traiter." if n else ""
        return {"reply": "Les candidatures sont classées par score de compatibilité. Changez leur statut "
                         "(présélectionnée, entretien, acceptée, refusée) : le candidat est notifié." + extra,
                "quick_replies": ["Trouver des candidats"]}
    return {"reply": "Je peux vous aider à rédiger une offre, trouver des profils compatibles ou gérer vos candidatures.",
            "quick_replies": qr}
