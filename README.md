# Streamlit OCR

Application Streamlit permettant d'enregistrer le défilement d'une page web,
d'en extraire des images clés et de reconstruire son contenu textuel avec OCR.

## Fonctionnalités

- navigation automatisée avec Playwright et Chromium ;
- défilement paramétrable en pixels, délai et durée maximale ;
- arrêt manuel de la capture depuis l'interface ;
- enregistrement Playwright en WebM puis conversion en MP4 avec FFmpeg ;
- extraction d'images clés avec OpenCV ;
- OCR français et anglais avec Tesseract ;
- suppression des doublons, chevauchements, en-têtes et pieds répétés ;
- export du résultat en TXT, Markdown et CSV ;
- aperçu intégré du site lorsque les iframes sont autorisées ;
- macros Playwright sans vidéo avec captures PNG multi-pages ;
- navigateur visible pour préparer un parcours, puis mode headless automatique ;
- conservation optionnelle de la session de connexion ;
- exécution CLI et planification quotidienne macOS avec `launchd` ;
- suivi de progression, journalisation et gestion des erreurs.

## Prérequis

- Conda ou Miniconda ;
- macOS Apple Silicon, Windows ou Linux ;
- accès à Internet lors de l'installation de Chromium ;
- respect des droits d'auteur et des conditions d'utilisation des sites capturés.

Python 3.12, FFmpeg et Tesseract sont installés par `environment.yml`.

## Installation

Depuis la racine du projet :

```bash
conda env create -f environment.yml
conda activate streamlit_ocr
python -m playwright install chromium
```

Si l'environnement existe déjà, le mettre à jour avec :

```bash
conda env update -n streamlit_ocr -f environment.yml --prune
python -m playwright install chromium
```

Sous Linux uniquement, Chromium peut nécessiter des bibliothèques système :

```bash
python -m playwright install --with-deps chromium
```

## Lancement

```bash
conda activate streamlit_ocr
python -m streamlit run app.py
```

Ouvrir ensuite <http://localhost:8501>.

L'utilisation de `python -m streamlit` est volontaire : elle garantit que
Streamlit utilise le même interpréteur Python que l'environnement Conda actif.

### Vérifier l'environnement

macOS ou Linux :

```bash
which python
python --version
python -c "import playwright, streamlit; print('Environnement valide')"
```

Windows PowerShell :

```powershell
where.exe python
python --version
python -c "import playwright, streamlit; print('Environnement valide')"
```

Le chemin Python doit contenir `envs/streamlit_ocr` et la version doit être
Python 3.12.

## Utilisation

1. Saisir une URL HTTP ou HTTPS complète.
2. Régler le pas et la vitesse de défilement.
3. Définir une durée maximale.
4. Cliquer sur **Démarrer**.
5. Attendre la fin de page ou cliquer sur **Arrêter**.
6. Consulter la vidéo et le texte reconstruit.
7. Télécharger le résultat en TXT, Markdown ou CSV.

Le bouton d'arrêt envoie une demande au processus de capture. Playwright
finalise ensuite la vidéo avant le traitement OpenCV et OCR.

## Macros et captures PNG

Ouvrir la page **Macros et captures** dans le menu Streamlit. Ce mode ne crée
pas de vidéo et n'exécute pas d'OCR : il pilote directement Chromium puis
enregistre les captures demandées.

L'onglet **Aperçu du site** affiche une iframe. Certains sites la bloquent avec
leur politique de sécurité ; cela n'empêche pas nécessairement Playwright de
les ouvrir dans une fenêtre Chromium séparée.

Exemple de macro :

```json
{
  "name": "classement_jeu",
  "start_url": "https://example.com",
  "headless": true,
  "timeout_seconds": 60,
  "viewport_width": 1440,
  "viewport_height": 900,
  "persist_session": true,
  "actions": [
    {
      "action": "click",
      "selector": "a[href='/classement']",
      "duration_ms": 1000
    },
    {
      "action": "screenshot",
      "name": "classement_1",
      "full_page": true
    },
    {
      "action": "click",
      "selector": "button.next",
      "duration_ms": 1000
    },
    {
      "action": "screenshot",
      "name": "classement_2",
      "full_page": true
    }
  ]
}
```

Actions disponibles :

| Action | Paramètres principaux | Effet |
| --- | --- | --- |
| `goto` | `value` | Ouvre une autre URL |
| `click` | `selector` | Clique sur un élément |
| `fill` | `selector`, `value` | Remplit un champ |
| `press` | `selector`, `value` | Envoie une touche, par exemple `Enter` |
| `wait` | `duration_ms` | Attend une durée |
| `scroll` | `value` | Défile verticalement en pixels |
| `screenshot` | `name`, `full_page` | Enregistre une image PNG |

Les sélecteurs utilisent la syntaxe Playwright/CSS. Pour tester une connexion
manuelle, cocher **Afficher la fenêtre Chromium pendant ce test**. Lorsque
`persist_session` vaut `true`, les cookies et données de session sont conservés
dans `data/browser_profiles/`.

Le sélecteur d'un exemple doit toujours être remplacé par un élément réellement
présent sur le site ciblé. Par exemple, `a[href='/page-2']` ne fonctionne que
si la page contient exactement ce lien. Le bouton **Charger exemple sûr**
génère une macro sans clic, compatible avec toute URL publique. Lors d'un test
avec Chromium visible, ne fermez pas sa fenêtre avant la fin de la macro.

Ne placez pas de mot de passe directement dans le JSON. Une valeur telle que
`${GAME_PASSWORD}` est lue depuis une variable d'environnement au moment de
l'exécution.

### Exécution en ligne de commande

Les macros enregistrées depuis l'interface sont placées dans `data/macros/`.

```bash
conda activate streamlit_ocr
python run_macro.py --config data/macros/classement_jeu.json --headless
```

### Planification quotidienne à 4 h sur macOS

Dans l'onglet **Planification**, choisir `4` heure et `0` minute, puis générer
le planning. L'interface affiche les commandes adaptées au fichier créé.

Installation manuelle équivalente :

```bash
mkdir -p "$HOME/Library/LaunchAgents"
cp "data/schedules/com.streamlit-ocr.classement-jeu.plist" \
  "$HOME/Library/LaunchAgents/"
launchctl bootstrap "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.streamlit-ocr.classement-jeu.plist"
```

Pour remplacer un planning déjà chargé :

```bash
launchctl bootout "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.streamlit-ocr.classement-jeu.plist"
launchctl bootstrap "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.streamlit-ocr.classement-jeu.plist"
```

`launchd` planifie la tâche, mais ne garantit pas le réveil matériel du Mac.
Pour un lancement exact à 4 h, le Mac doit être allumé et réveillé. Une
programmation de réveil peut être configurée séparément avec `pmset` et les
droits administrateur.

## Pipeline

```text
URL
  -> Playwright / Chromium
  -> capture WebM
  -> conversion FFmpeg en MP4
  -> sélection des images clés OpenCV
  -> OCR Tesseract
  -> reconstruction et déduplication
  -> exports TXT, Markdown et CSV
```

Playwright produit nativement une vidéo WebM. La conversion MP4 est donc une
étape distincte réalisée avec FFmpeg.

## Architecture DDD

```text
streamlit_ocr/
├── app.py
├── application/
│   ├── job_manager.py
│   ├── ports.py
│   └── use_cases.py
├── domain/
│   ├── exceptions.py
│   ├── models.py
│   └── text_reconstruction.py
├── pages/
│   ├── 1_Aide.py
│   └── 2_Macros_et_captures.py
├── services/
│   ├── browser_service.py
│   ├── container.py
│   ├── export_service.py
│   ├── macro_browser_service.py
│   ├── ocr_service.py
│   ├── schedule_service.py
│   └── video_service.py
├── run_macro.py
├── data/
├── recordings/
├── screenshots/
├── tests/
├── environment.yml
└── requirements.txt
```

- `domain/` contient les modèles et règles métier sans dépendance à Streamlit.
- `application/` orchestre les cas d'usage et les tâches en arrière-plan.
- `services/` implémente les adaptateurs Playwright, FFmpeg, OpenCV et OCR.
- `app.py` et `pages/` constituent la couche de présentation Streamlit.

Les contrats de `application/ports.py` permettent de remplacer un adaptateur
technique sans modifier le domaine.

## Fichiers générés

- `recordings/<session>/capture.webm` : vidéo Playwright originale ;
- `recordings/<session>/capture.mp4` : vidéo convertie pour lecture et export ;
- `screenshots/<session>/` : images clés sélectionnées ;
- `screenshots/macros/<macro>/<session>/` : captures PNG d'une macro ;
- `data/macros/` : configurations JSON enregistrées ;
- `data/browser_profiles/` : états de connexion Playwright ;
- `data/schedules/` : fichiers macOS `launchd` générés ;
- `data/streamlit_ocr.log` : journal applicatif.

Ces fichiers sont exclus de Git, à l'exception des fichiers `.gitkeep`.

## Tests

```bash
conda activate streamlit_ocr
python -m pytest -q
python -m compileall -q app.py application domain services pages tests
```

Les tests couvrent notamment :

- la validation des URL et paramètres ;
- la reconstruction et la déduplication OCR ;
- les exports TXT, Markdown et CSV.

## Dépannage

### `ModuleNotFoundError: No module named 'playwright'`

Si le traceback mentionne l'environnement `base`, la commande `streamlit`
utilise le mauvais interpréteur. Relancer avec :

```bash
conda activate streamlit_ocr
rehash
python -m streamlit run app.py
```

Sous Bash, utiliser `hash -r` à la place de `rehash`. Sous PowerShell, fermer
et rouvrir le terminal après l'activation de Conda si nécessaire.

### Chromium n'est pas installé

```bash
conda activate streamlit_ocr
python -m playwright install chromium
```

### FFmpeg ou Tesseract est introuvable

```bash
conda env update -n streamlit_ocr -f environment.yml --prune
ffmpeg -version
tesseract --version
tesseract --list-langs
```

Les langues `fra` et `eng` doivent apparaître dans la liste Tesseract.

### Avertissement Watchdog sur macOS

Watchdog améliore le rechargement pendant le développement, mais il n'est pas
nécessaire au fonctionnement de l'application. Pour l'ajouter :

```bash
xcode-select --install
python -m pip install watchdog
```

### La capture échoue sur un site

Certains sites bloquent l'automatisation, exigent une authentification ou un
CAPTCHA, utilisent des DRM, ou chargent leur contenu dans des composants non
accessibles. Tester d'abord avec une page publique simple.

## Limites actuelles

- le navigateur fonctionne en mode headless ;
- les pages protégées ou nécessitant une connexion ne sont pas prises en charge ;
- les macros peuvent réutiliser une connexion existante, mais ne contournent
  ni CAPTCHA, ni double authentification, ni protection anti-bot ;
- la qualité OCR dépend de la police, du contraste et des animations ;
- les contenus vidéo, canvas ou fortement dynamiques peuvent être incomplets ;
- les captures longues peuvent produire de nombreux fichiers et ralentir l'OCR.
