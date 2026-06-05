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
- export du résultat en TXT, Markdown et PDF ;
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
7. Télécharger le résultat en TXT, Markdown ou PDF.

Le bouton d'arrêt envoie une demande au processus de capture. Playwright
finalise ensuite la vidéo avant le traitement OpenCV et OCR.

## Pipeline

```text
URL
  -> Playwright / Chromium
  -> capture WebM
  -> conversion FFmpeg en MP4
  -> sélection des images clés OpenCV
  -> OCR Tesseract
  -> reconstruction et déduplication
  -> exports TXT, Markdown et PDF
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
│   └── 1_Aide.py
├── services/
│   ├── browser_service.py
│   ├── container.py
│   ├── export_service.py
│   ├── ocr_service.py
│   └── video_service.py
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
- les exports TXT, Markdown et PDF.

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
- la qualité OCR dépend de la police, du contraste et des animations ;
- les contenus vidéo, canvas ou fortement dynamiques peuvent être incomplets ;
- les captures longues peuvent produire de nombreux fichiers et ralentir l'OCR.

