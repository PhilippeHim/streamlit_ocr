"""Streamlit interface for visual Playwright macro configuration."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import streamlit as st

from application.macro_job_manager import MacroJobManager
from application.macro_use_cases import MacroRepository
from domain.macro_models import MacroDefinition
from domain.models import JobStatus
from services.container import build_macro_job_manager, build_macro_repository
from services.export_service import ExportService
from services.preferences_service import PreferencesService
from services.schedule_service import ScheduleService

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREFERENCES = PreferencesService(PROJECT_ROOT / "data" / "preferences.json")

ACTION_LABELS = {
    "Capture PNG": "screenshot",
    "Clic": "click",
    "Saisie de texte": "fill",
    "Touche clavier": "press",
    "Attente": "wait",
    "Défilement": "scroll",
    "Ouvrir une URL": "goto",
}
DEFAULT_ACTION_ROWS = [
    {
        "Action": "Attente",
        "Sélecteur CSS": "",
        "Valeur": "",
        "Nom de capture": "",
        "Délai (ms)": 1500,
        "Page entière": False,
    },
    {
        "Action": "Capture PNG",
        "Sélecteur CSS": "",
        "Valeur": "",
        "Nom de capture": "page_complete",
        "Délai (ms)": 0,
        "Page entière": True,
    },
]

st.set_page_config(page_title="Macros et captures", page_icon="M", layout="wide")


def get_manager() -> MacroJobManager:
    if "macro_job_manager" not in st.session_state:
        st.session_state.macro_job_manager = build_macro_job_manager(PROJECT_ROOT)
    return st.session_state.macro_job_manager


def get_repository() -> MacroRepository:
    if "macro_repository" not in st.session_state:
        st.session_state.macro_repository = build_macro_repository(PROJECT_ROOT)
    return st.session_state.macro_repository


def reset_visual_form() -> None:
    """Reset action rows without exposing the internal JSON representation."""
    st.session_state.action_rows = [dict(row) for row in DEFAULT_ACTION_ROWS]
    st.session_state.action_editor_version += 1


def records_from_editor(editor_value: Any) -> list[dict[str, Any]]:
    """Convert Streamlit's table result into plain records."""
    if hasattr(editor_value, "to_dict"):
        records = editor_value.to_dict(orient="records")
    else:
        records = list(editor_value)
    return [
        {key: _clean_cell(value) for key, value in record.items()}
        for record in records
    ]


def build_macro(editor_value: Any) -> MacroDefinition:
    """Build a validated domain macro from the visual form."""
    actions: list[dict[str, Any]] = []
    for row in records_from_editor(editor_value):
        label = str(row.get("Action") or "").strip()
        if not label:
            continue
        action_type = ACTION_LABELS.get(label)
        if action_type is None:
            raise ValueError(f"Action inconnue : {label}.")

        action: dict[str, Any] = {"action": action_type}
        selector = str(row.get("Sélecteur CSS") or "").strip()
        value = str(row.get("Valeur") or "").strip()
        name = str(row.get("Nom de capture") or "").strip()
        duration = int(row.get("Délai (ms)") or 0)

        if selector:
            action["selector"] = selector
        if value:
            action["value"] = value
        if name:
            action["name"] = name
        if duration:
            action["duration_ms"] = duration
        if action_type == "screenshot":
            action["full_page"] = bool(row.get("Page entière", True))
        actions.append(action)

    macro = MacroDefinition.from_dict(
        {
            "name": st.session_state.macro_name,
            "start_url": st.session_state.site_url,
            "headless": not st.session_state.visible_browser,
            "timeout_seconds": st.session_state.macro_timeout,
            "viewport_width": st.session_state.viewport_width,
            "viewport_height": st.session_state.viewport_height,
            "persist_session": st.session_state.persist_session,
            "perform_ocr": st.session_state.perform_ocr,
            "actions": actions,
        }
    )
    PREFERENCES.save_last_url(macro.start_url)
    return macro


def save_macro(macro: MacroDefinition, repository: MacroRepository) -> Path:
    """Persist a generated macro for CLI and scheduled execution."""
    path = repository.save(macro)
    st.session_state.saved_macro_path = str(path)
    return path


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
        st.warning("Aucune étape de capture PNG n'a été exécutée.")
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

    if result.document:
        st.subheader("Texte OCR reconstruit")
        st.text_area(
            "Résultat OCR",
            result.document.text,
            height=320,
            key=f"macro_ocr_{result.session_directory}",
        )
        exporter = ExportService()
        export_columns = st.columns(3)
        export_columns[0].download_button(
            "Télécharger TXT",
            exporter.to_txt(result.document),
            file_name=f"{result.macro_name}_ocr.txt",
            mime="text/plain",
            use_container_width=True,
        )
        export_columns[1].download_button(
            "Télécharger Markdown",
            exporter.to_markdown(result.document),
            file_name=f"{result.macro_name}_ocr.md",
            mime="text/markdown",
            use_container_width=True,
        )
        export_columns[2].download_button(
            "Télécharger CSV",
            exporter.to_csv(result.document),
            file_name=f"{result.macro_name}_ocr.csv",
            mime="text/csv",
            use_container_width=True,
        )


def _clean_cell(value: Any) -> Any:
    """Replace table NaN values with empty strings."""
    try:
        if value != value:
            return ""
    except (TypeError, ValueError):
        pass
    return value


manager = get_manager()
repository = get_repository()
snapshot = manager.snapshot()
is_active = snapshot.status in {JobStatus.RUNNING, JobStatus.STOPPING}

defaults = {
    "site_url": PREFERENCES.load_last_url(),
    "macro_name": "capture_page",
    "visible_browser": False,
    "persist_session": True,
    "perform_ocr": False,
    "macro_timeout": 60,
    "viewport_width": 1440,
    "viewport_height": 900,
    "action_rows": [dict(row) for row in DEFAULT_ACTION_ROWS],
    "action_editor_version": 0,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.title("Macros de navigation et captures")
st.write(
    "Configurez visuellement un parcours Playwright et réalisez des captures PNG "
    "sans enregistrer de vidéo."
)
st.warning(
    "Respectez les conditions d'utilisation du site. Les CAPTCHA et protections "
    "anti-automatisation ne sont pas contournés."
)

st.text_input(
    "URL du site pour l'aperçu et Playwright",
    key="site_url",
    disabled=is_active,
)
st.caption("Cette URL unique est utilisée par l'aperçu et par la macro.")

preview_tab, macro_tab, schedule_tab = st.tabs(
    ["Aperçu du site", "Paramètres Playwright", "Planification"]
)

with preview_tab:
    st.caption(
        "Une page vide signifie généralement que le site interdit son intégration "
        "dans une iframe. Playwright peut néanmoins l'ouvrir dans Chromium."
    )
    st.iframe(st.session_state.site_url, height=720)

with macro_tab:
    st.subheader("Réglages généraux")
    name_column, timeout_column = st.columns(2)
    name_column.text_input(
        "Nom de la macro",
        key="macro_name",
        disabled=is_active,
    )
    timeout_column.number_input(
        "Délai maximal par action (secondes)",
        min_value=1,
        max_value=3600,
        key="macro_timeout",
        disabled=is_active,
    )

    width_column, height_column = st.columns(2)
    width_column.number_input(
        "Largeur du navigateur",
        min_value=320,
        max_value=3840,
        step=10,
        key="viewport_width",
        disabled=is_active,
    )
    height_column.number_input(
        "Hauteur du navigateur",
        min_value=240,
        max_value=2160,
        step=10,
        key="viewport_height",
        disabled=is_active,
    )

    option_column, session_column, ocr_column = st.columns(3)
    option_column.checkbox(
        "Afficher la fenêtre Chromium pendant le test",
        key="visible_browser",
        disabled=is_active,
    )
    session_column.checkbox(
        "Conserver la session de connexion",
        key="persist_session",
        disabled=is_active,
    )
    ocr_column.checkbox(
        "OCRiser les captures PNG",
        key="perform_ocr",
        disabled=is_active,
        help="Reconstruit le texte après l'exécution, sans enregistrer de vidéo.",
    )

    st.subheader("Étapes du parcours")
    st.caption(
        "Ajoutez ou supprimez des lignes. Le sélecteur CSS est requis pour un clic, "
        "une saisie ou une touche. La valeur sert au texte, à la touche, au nombre "
        "de pixels ou à l'URL selon l'action."
    )
    edited_actions = st.data_editor(
        st.session_state.action_rows,
        key=f"macro_actions_{st.session_state.action_editor_version}",
        num_rows="dynamic",
        disabled=is_active,
        hide_index=True,
        width="stretch",
        column_config={
            "Action": st.column_config.SelectboxColumn(
                "Action",
                options=list(ACTION_LABELS),
                required=True,
            ),
            "Sélecteur CSS": st.column_config.TextColumn("Sélecteur CSS"),
            "Valeur": st.column_config.TextColumn("Valeur"),
            "Nom de capture": st.column_config.TextColumn("Nom de capture"),
            "Délai (ms)": st.column_config.NumberColumn(
                "Délai (ms)",
                min_value=0,
                step=100,
                default=0,
            ),
            "Page entière": st.column_config.CheckboxColumn(
                "Page entière",
                default=True,
            ),
        },
    )

    reset_column, save_column, run_column, stop_column = st.columns(4)
    reset_column.button(
        "Réinitialiser",
        on_click=reset_visual_form,
        disabled=is_active,
        use_container_width=True,
    )

    save_clicked = save_column.button(
        "Enregistrer",
        disabled=is_active,
        use_container_width=True,
    )
    run_clicked = run_column.button(
        "Exécuter",
        type="primary",
        disabled=is_active,
        use_container_width=True,
    )
    stop_column.button(
        "Arrêter",
        on_click=manager.stop,
        disabled=not is_active,
        use_container_width=True,
    )

    if save_clicked or run_clicked:
        try:
            current_macro = build_macro(edited_actions)
            saved_path = save_macro(current_macro, repository)
            if save_clicked:
                st.success(f"Macro enregistrée dans {saved_path.relative_to(PROJECT_ROOT)}.")
            if run_clicked:
                manager.start(current_macro)
        except (TypeError, ValueError, RuntimeError) as exc:
            st.error(f"Configuration invalide : {exc}")

    @st.fragment(run_every=1.0)
    def live_macro_panel() -> None:
        render_gallery(manager)

    live_macro_panel()

with schedule_tab:
    st.subheader("Exécution quotidienne")
    st.write(
        "Le planning utilise les réglages et les étapes actuellement affichés. "
        "Le navigateur sera lancé en arrière-plan."
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

    if st.button("Générer le planning macOS", disabled=is_active):
        try:
            scheduled_macro = replace(build_macro(edited_actions), headless=True)
            macro_path = save_macro(scheduled_macro, repository)
            scheduler = ScheduleService(PROJECT_ROOT, Path(sys.executable))
            plist = scheduler.create_macos_daily_schedule(
                macro_path,
                scheduled_macro.name,
                hour=int(st.session_state.schedule_hour),
                minute=int(st.session_state.schedule_minute),
            )
            st.session_state.generated_plist = str(plist)
        except (TypeError, ValueError) as exc:
            st.error(f"Configuration invalide : {exc}")

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
