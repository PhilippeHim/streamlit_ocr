"""Streamlit presentation layer."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from application.job_manager import CaptureJobManager
from domain.models import CaptureSettings, JobStatus
from services.container import build_job_manager
from services.export_service import ExportService

PROJECT_ROOT = Path(__file__).resolve().parent
LOG_FILE = PROJECT_ROOT / "data" / "streamlit_ocr.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)

st.set_page_config(page_title="Streamlit OCR", page_icon="OCR", layout="wide")


def get_job_manager() -> CaptureJobManager:
    """Keep the worker object alive across Streamlit reruns."""
    if "job_manager" not in st.session_state:
        st.session_state.job_manager = build_job_manager(PROJECT_ROOT)
    return st.session_state.job_manager


def start_capture(manager: CaptureJobManager) -> None:
    """Validate widgets and start the background use case."""
    try:
        settings = CaptureSettings(
            url=st.session_state.url,
            scroll_step=st.session_state.scroll_step,
            scroll_delay=st.session_state.scroll_delay,
            max_duration=st.session_state.max_duration,
        )
        manager.start(settings)
    except (ValueError, RuntimeError) as exc:
        st.error(str(exc))


def render_result(manager: CaptureJobManager) -> None:
    """Render status, artifacts and exports."""
    snapshot = manager.snapshot()
    active = snapshot.status in {JobStatus.RUNNING, JobStatus.STOPPING}
    progress_value = (
        min(snapshot.elapsed_seconds / snapshot.total_seconds, 1.0)
        if snapshot.total_seconds > 0
        else 0.0
    )
    st.progress(progress_value, text=snapshot.message)
    st.caption(
        f"État : {snapshot.status.value} | "
        f"Durée/progression : {snapshot.elapsed_seconds:.1f} s"
    )

    if snapshot.error:
        st.error(snapshot.error)
    if snapshot.result is None:
        if active:
            st.info("La capture continue en arrière-plan. Le statut est actualisé automatiquement.")
        return

    result = snapshot.result
    st.subheader("Vidéo")
    st.video(str(result.capture.mp4_video))
    st.caption(
        f"{result.capture.duration_seconds:.1f} secondes | "
        f"{len(result.document.frames)} images clés"
    )

    st.subheader("Texte reconstruit")
    st.text_area("Résultat OCR", result.document.text, height=360)
    exporter = ExportService()
    columns = st.columns(3)
    columns[0].download_button(
        "Télécharger TXT",
        exporter.to_txt(result.document),
        file_name="capture_ocr.txt",
        mime="text/plain",
        use_container_width=True,
    )
    columns[1].download_button(
        "Télécharger Markdown",
        exporter.to_markdown(result.document),
        file_name="capture_ocr.md",
        mime="text/markdown",
        use_container_width=True,
    )
    columns[2].download_button(
        "Télécharger CSV",
        exporter.to_csv(result.document),
        file_name="capture_ocr.csv",
        mime="text/csv",
        use_container_width=True,
    )


st.title("Capture web et OCR")
st.write(
    "Enregistrez le défilement d'une page, extrayez ses images clés et "
    "reconstruisez automatiquement son texte."
)

manager = get_job_manager()
current = manager.snapshot()
is_active = current.status in {JobStatus.RUNNING, JobStatus.STOPPING}

with st.sidebar:
    st.header("Paramètres")
    st.text_input(
        "URL",
        value="https://example.com",
        key="url",
        disabled=is_active,
    )
    st.slider(
        "Pas de défilement (px)",
        min_value=100,
        max_value=2000,
        value=700,
        step=50,
        key="scroll_step",
        disabled=is_active,
    )
    st.slider(
        "Pause entre deux pas (s)",
        min_value=0.1,
        max_value=5.0,
        value=0.8,
        step=0.1,
        key="scroll_delay",
        disabled=is_active,
    )
    st.number_input(
        "Durée maximale (s)",
        min_value=5,
        max_value=3600,
        value=120,
        step=5,
        key="max_duration",
        disabled=is_active,
    )
    start_column, stop_column = st.columns(2)
    start_column.button(
        "Démarrer",
        type="primary",
        disabled=is_active,
        on_click=start_capture,
        args=(manager,),
        use_container_width=True,
    )
    stop_column.button(
        "Arrêter",
        disabled=not is_active,
        on_click=manager.stop,
        use_container_width=True,
    )


@st.fragment(run_every=1.0)
def live_panel() -> None:
    render_result(manager)


live_panel()
