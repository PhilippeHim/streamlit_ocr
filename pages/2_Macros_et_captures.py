"""Streamlit interface for iframe preview and Playwright screenshot macros."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import streamlit as st

from application.macro_job_manager import MacroJobManager
from application.macro_use_cases import MacroRepository
from domain.macro_models import MacroDefinition
from domain.models import JobStatus
from services.container import build_macro_job_manager, build_macro_repository
from services.schedule_service import ScheduleService

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MACRO = {
    "name": "capture_page",
    "start_url": "https://example.com",
    "headless": True,
    "timeout_seconds": 60,
    "viewport_width": 1440,
    "viewport_height": 900,
    "persist_session": True,
    "actions": [
        {"action": "wait", "duration_ms": 1500},
        {"action": "screenshot", "name": "page_complete", "full_page": True},
    ],
}

st.set_page_config(page_title="Macros et captures", page_icon="M", layout="wide")


def get_manager() -> MacroJobManager:
    if "macro_job_manager" not in st.session_state:
        st.session_state.macro_job_manager = build_macro_job_manager(PROJECT_ROOT)
    return st.session_state.macro_job_manager


def get_repository() -> MacroRepository:
    if "macro_repository" not in st.session_state:
        st.session_state.macro_repository = build_macro_repository(PROJECT_ROOT)
    return st.session_state.macro_repository


def parse_editor() -> MacroDefinition:
    """Decode and validate the current JSON editor."""
    raw = json.loads(st.session_state.macro_json)
    if not isinstance(raw, dict):
        raise ValueError("La macro doit être un objet JSON.")
    macro = MacroDefinition.from_dict(raw)
    return replace(macro, headless=not st.session_state.visible_browser)


def load_safe_example() -> None:
    """Replace the editor with a macro that works on any public URL."""
    start_url = st.session_state.get("preview_url") or DEFAULT_MACRO["start_url"]
    example = {**DEFAULT_MACRO, "start_url": start_url}
    st.session_state.macro_json = json.dumps(example, ensure_ascii=False, indent=2)


def save_macro(repository: MacroRepository) -> Path | None:
    try:
        macro = parse_editor()
        path = repository.save(macro)
        st.session_state.saved_macro_path = str(path)
        st.success(f"Macro enregistrée dans {path.relative_to(PROJECT_ROOT)}.")
        return path
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        st.error(f"Configuration invalide : {exc}")
        return None


def start_macro(manager: MacroJobManager, repository: MacroRepository) -> None:
    path = save_macro(repository)
    if path is None:
        return
    try:
        manager.start(repository.load(path))
    except RuntimeError as exc:
        st.error(str(exc))


def generate_schedule(repository: MacroRepository) -> None:
    path = save_macro(repository)
    if path is None:
        return
    macro = replace(repository.load(path), headless=True)
    path = repository.save(macro)
    scheduler = ScheduleService(PROJECT_ROOT, Path(sys.executable))
    plist = scheduler.create_macos_daily_schedule(
        path,
        macro.name,
        hour=int(st.session_state.schedule_hour),
        minute=int(st.session_state.schedule_minute),
    )
    st.session_state.generated_plist = str(plist)


def render_gallery(manager: MacroJobManager) -> None:
    snapshot = manager.snapshot()
    active = snapshot.status in {JobStatus.RUNNING, JobStatus.STOPPING}
    progress = min(snapshot.current_step / snapshot.total_steps, 1.0)
    st.progress(progress, text=snapshot.message)
    st.caption(f"État : {snapshot.status.value}")
    if snapshot.error:
        st.error(snapshot.error)
    if active:
        st.info("La macro s'exécute en arrière-plan. L'arrêt intervient entre deux actions.")
    if not snapshot.result:
        return

    result = snapshot.result
    st.success(
        f"{len(result.screenshots)} capture(s) créée(s) en "
        f"{result.duration_seconds:.1f} secondes."
    )
    if not result.screenshots:
        st.warning("La macro ne contient aucune action `screenshot` exécutée.")
        return
    columns = st.columns(2)
    for index, screenshot in enumerate(result.screenshots):
        with columns[index % 2]:
            st.image(str(screenshot), caption=screenshot.name, use_container_width=True)
            st.download_button(
                f"Télécharger {screenshot.name}",
                screenshot.read_bytes(),
                file_name=screenshot.name,
                mime="image/png",
                key=f"download_{screenshot}",
                use_container_width=True,
            )


st.title("Macros de navigation et captures")
st.write(
    "Prévisualisez un site lorsqu'il accepte les iframes, testez un parcours "
    "dans Chromium, puis exécutez-le automatiquement sans enregistrer de vidéo."
)
st.warning(
    "Respectez les conditions d'utilisation du site. Les CAPTCHA et protections "
    "anti-automatisation ne sont pas contournés."
)

manager = get_manager()
repository = get_repository()
snapshot = manager.snapshot()
is_active = snapshot.status in {JobStatus.RUNNING, JobStatus.STOPPING}

if "macro_json" not in st.session_state:
    st.session_state.macro_json = json.dumps(DEFAULT_MACRO, ensure_ascii=False, indent=2)
if "preview_url" not in st.session_state:
    st.session_state.preview_url = DEFAULT_MACRO["start_url"]

preview_tab, macro_tab, schedule_tab = st.tabs(
    ["Aperçu du site", "Macro Playwright", "Planification"]
)

with preview_tab:
    preview_url = st.text_input("URL à prévisualiser", key="preview_url")
    st.caption(
        "L'aperçu dépend de la politique iframe du site. Une page vide ou une erreur "
        "signifie généralement que le site interdit son intégration."
    )
    st.iframe(preview_url, height=720)

with macro_tab:
    st.checkbox(
        "Afficher la fenêtre Chromium pendant ce test",
        value=False,
        key="visible_browser",
        disabled=is_active,
        help="Désactivé pour les exécutions automatiques et planifiées.",
    )
    st.text_area(
        "Configuration JSON",
        key="macro_json",
        height=440,
        disabled=is_active,
    )
    st.caption(
        "Actions : goto, click, fill, press, wait, scroll et screenshot. "
        "Utilisez ${NOM_VARIABLE} pour une valeur secrète."
    )
    example_column, save_column, run_column, stop_column = st.columns(4)
    example_column.button(
        "Charger exemple sûr",
        on_click=load_safe_example,
        disabled=is_active,
        use_container_width=True,
    )
    save_column.button(
        "Enregistrer",
        on_click=save_macro,
        args=(repository,),
        disabled=is_active,
        use_container_width=True,
    )
    run_column.button(
        "Exécuter la macro",
        type="primary",
        on_click=start_macro,
        args=(manager, repository),
        disabled=is_active,
        use_container_width=True,
    )
    stop_column.button(
        "Arrêter",
        on_click=manager.stop,
        disabled=not is_active,
        use_container_width=True,
    )

    @st.fragment(run_every=1.0)
    def live_macro_panel() -> None:
        render_gallery(manager)

    live_macro_panel()

with schedule_tab:
    st.subheader("Exécution quotidienne")
    st.write(
        "La planification génère un agent `launchd` macOS. Le Mac doit être allumé "
        "et réveillé à l'heure prévue."
    )
    hour_column, minute_column = st.columns(2)
    hour_column.number_input(
        "Heure",
        min_value=0,
        max_value=23,
        value=4,
        key="schedule_hour",
    )
    minute_column.number_input(
        "Minute",
        min_value=0,
        max_value=59,
        value=0,
        key="schedule_minute",
    )
    st.button(
        "Générer le planning macOS",
        on_click=generate_schedule,
        args=(repository,),
        disabled=is_active,
    )
    if st.session_state.get("generated_plist"):
        plist = Path(st.session_state.generated_plist)
        agent_path = f"$HOME/Library/LaunchAgents/{plist.name}"
        st.success(f"Planning généré : {plist.relative_to(PROJECT_ROOT)}")
        st.code(
            f'mkdir -p "$HOME/Library/LaunchAgents"\n'
            f'cp "{plist}" "{agent_path}"\n'
            f'launchctl bootstrap "gui/$(id -u)" "{agent_path}"',
            language="bash",
        )
        st.download_button(
            "Télécharger le fichier launchd",
            plist.read_bytes(),
            file_name=plist.name,
            mime="application/xml",
        )
