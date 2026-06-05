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

La dernière URL validée au démarrage d'une capture est enregistrée localement
dans `data/preferences.json` et proposée automatiquement au prochain lancement.

## Macros et captures PNG

Ouvrir la page **Macros et captures** dans le menu Streamlit. Ce mode ne crée
pas de vidéo et n'exécute pas d'OCR : il pilote directement Chromium puis
enregistre les captures demandées.

La page utilise un seul champ **URL du site pour l'aperçu et Playwright**.
Cette valeur alimente à la fois l'iframe et le champ `start_url` de la macro,
puis elle est proposée à nouveau au prochain lancement.

L'onglet **Aperçu du site** affiche une iframe. Certains sites la bloquent avec
leur politique de sécurité ; cela n'empêche pas nécessairement Playwright de
les ouvrir dans une fenêtre Chromium séparée.

Les réglages sont présentés sous forme de champs :

- nom de la macro ;
- délai maximal par action ;
- largeur et hauteur du navigateur ;
- affichage facultatif de Chromium pendant le test ;
- conservation facultative de la session de connexion.
- OCR facultatif des captures PNG, sans passer par une vidéo.

Le parcours est construit dans un tableau dynamique. Une ligne correspond à
une action et les boutons du tableau permettent d'ajouter ou supprimer des
lignes.

| Action affichée | Paramètres à renseigner | Effet |
| --- | --- | --- |
| Capture PNG | nom, page entière | Enregistre une image |
| Clic | sélecteur CSS, délai | Clique sur un élément |
| Saisie de texte | sélecteur CSS, valeur | Remplit un champ |
| Touche clavier | sélecteur CSS, valeur | Envoie une touche comme `Enter` |
| Attente | délai en millisecondes | Attend avant l'étape suivante |
| Défilement | valeur en pixels, délai | Défile verticalement |
| Ouvrir une URL | valeur contenant l'URL | Navigue vers une autre page |

Les sélecteurs utilisent la syntaxe CSS de Playwright. Pour tester une
connexion manuelle, cocher **Afficher la fenêtre Chromium pendant le test**.
Lorsque **Conserver la session de connexion** est activé, les cookies et données
de session sont enregistrés dans `data/browser_profiles/`. Ne fermez pas la
fenêtre Chromium avant la fin de l'exécution.

Le format JSON reste utilisé uniquement en interne pour sauvegarder et
planifier les macros ; il n'est plus nécessaire de le modifier manuellement.

Lorsque **OCRiser les captures PNG** est activé, Tesseract traite chaque image
créée par les étapes de capture. Le texte est fusionné et peut être téléchargé
en TXT, Markdown ou CSV. En exécution planifiée, une copie `ocr.txt` est aussi
écrite dans le dossier de la session.

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
