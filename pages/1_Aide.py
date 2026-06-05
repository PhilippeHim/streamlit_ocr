"""Installation and usage help."""

import streamlit as st

st.set_page_config(page_title="Aide - Streamlit OCR", page_icon="?", layout="wide")
st.title("Aide")
st.markdown(
    """
## Capture vidéo et OCR

1. Saisissez une URL HTTP ou HTTPS complète.
2. Réglez le défilement et la durée maximale.
3. Démarrez la capture. Le navigateur fonctionne en arrière-plan.
4. Arrêtez manuellement ou attendez la fin de page.
5. Consultez la vidéo et téléchargez le texte reconstruit.

## Macros et captures

La page **Macros et captures** permet d'afficher un aperçu iframe, de définir
des actions Playwright en JSON, de prendre plusieurs captures PNG sans vidéo
et de générer une planification macOS quotidienne.

Les sites protégés par une authentification, un CAPTCHA, des DRM ou une
politique anti-automatisation peuvent refuser la capture. Respectez les droits
d'auteur et les conditions d'utilisation des pages consultées.
"""
)
