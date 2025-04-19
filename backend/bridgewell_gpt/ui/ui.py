"""This file should be imported if and only if you want to run the UI locally."""

import base64
import logging
from pathlib import Path
from typing import Any

import gradio as gr  # type: ignore
from fastapi import FastAPI
from gradio.themes.utils.colors import slate  # type: ignore
from injector import inject, singleton

from bridgewell_gpt.constants import PROJECT_ROOT_PATH
from bridgewell_gpt.di import global_injector
from bridgewell_gpt.server.ingest.ingest_service import IngestService
from bridgewell_gpt.settings.settings import settings
from bridgewell_gpt.ui.images import logo_svg

logger = logging.getLogger(__name__)

THIS_DIRECTORY_RELATIVE = Path(__file__).parent.relative_to(PROJECT_ROOT_PATH)
# Should be "bridgewell_gpt/ui/avatar-bot.ico"
AVATAR_BOT = THIS_DIRECTORY_RELATIVE / "avatar-bot.ico"

UI_TAB_TITLE = "Benefit Extraction Tool"


@singleton
class PrivateGptUi:
    @inject
    def __init__(
        self,
        ingest_service: IngestService,
    ) -> None:
        self._ingest_service = ingest_service
        self._ui_block = None
        self._selected_filename = None

    def _list_ingested_files(self) -> list[list[str]]:
        files = set()
        for ingested_document in self._ingest_service.list_ingested():
            if ingested_document.doc_metadata is None:
                continue
            file_name = ingested_document.doc_metadata.get(
                "file_name", "[FILE NAME MISSING]"
            )
            files.add(file_name)
        return [[row] for row in files]

    def _upload_file(self, files: list[str]) -> None:
        logger.debug("Loading count=%s files", len(files))
        paths = [Path(file) for file in files]

        # remove all existing Documents with name identical to a new file upload:
        file_names = [path.name for path in paths]
        doc_ids_to_delete = []
        for ingested_document in self._ingest_service.list_ingested():
            if (
                ingested_document.doc_metadata
                and ingested_document.doc_metadata["file_name"] in file_names
            ):
                doc_ids_to_delete.append(ingested_document.doc_id)
        if len(doc_ids_to_delete) > 0:
            logger.info(
                "Uploading file(s) which were already ingested: %s document(s) will be replaced.",
                len(doc_ids_to_delete),
            )
            for doc_id in doc_ids_to_delete:
                self._ingest_service.delete(doc_id)

        self._ingest_service.bulk_ingest([(str(path.name), path) for path in paths])

    def _delete_selected_file(self) -> Any:
        logger.debug("Deleting selected %s", self._selected_filename)
        for ingested_document in self._ingest_service.list_ingested():
            if (
                ingested_document.doc_metadata
                and ingested_document.doc_metadata["file_name"]
                == self._selected_filename
            ):
                self._ingest_service.delete(ingested_document.doc_id)
        return [
            gr.List(self._list_ingested_files()),
            gr.components.Button(interactive=False),
            gr.components.Button(interactive=False),
            gr.components.Textbox("All files"),
        ]

    def _delete_all_files(self) -> Any:
        ingested_files = self._ingest_service.list_ingested()
        logger.debug("Deleting count=%s files", len(ingested_files))
        for ingested_document in ingested_files:
            self._ingest_service.delete(ingested_document.doc_id)
        return [
            gr.List(self._list_ingested_files()),
            gr.components.Button(interactive=False),
            gr.components.Button(interactive=False),
            gr.components.Textbox("All files"),
        ]

    def _deselect_selected_file(self) -> Any:
        self._selected_filename = None
        return [
            gr.components.Button(interactive=False),
            gr.components.Button(interactive=False),
            gr.components.Textbox("All files"),
        ]

    def _selected_a_file(self, select_data: gr.SelectData) -> Any:
        self._selected_filename = select_data.value
        return [
            gr.components.Button(interactive=True),
            gr.components.Button(interactive=True),
            gr.components.Textbox(self._selected_filename),
        ]

    def _build_ui_blocks(self) -> gr.Blocks:
        logger.debug("Creating the UI blocks")
        with gr.Blocks(
            title=UI_TAB_TITLE,
            theme=gr.themes.Soft(primary_hue=slate),
            css=".logo { "
            "display:flex;"
            "background-color: #C7BAFF;"
            "height: 80px;"
            "border-radius: 8px;"
            "align-content: center;"
            "justify-content: center;"
            "align-items: center;"
            "}"
            ".logo img { height: 50% }"
            ".contain { display: flex !important; flex-direction: column !important; }"
            "#component-0, #component-3, #component-10, #component-8  { height: 100% !important; }"
            "#extraction-area { flex-grow: 1 !important; overflow: auto !important;}"
            "#col { height: calc(100vh - 112px - 16px) !important; }"
            "hr { margin-top: 1em; margin-bottom: 1em; border: 0; border-top: 1px solid #FFF; }"
            ".footer { text-align: center; margin-top: 20px; font-size: 14px; display: flex; align-items: center; justify-content: center; }"
            ".footer-zylon-link { display:flex; margin-left: 5px; text-decoration: auto; color: var(--body-text-color); }"
            ".footer-zylon-link:hover { color: #C7BAFF; }"
            ".footer-zylon-ico { height: 20px; margin-left: 5px; background-color: antiquewhite; border-radius: 2px; }",
        ) as blocks:
            with gr.Row():
                gr.HTML(f"<div class='logo'><img src={logo_svg} alt='Benefit Extraction Tool'></div>")

            with gr.Row(equal_height=False):
                with gr.Column(scale=3):
                    upload_button = gr.components.UploadButton(
                        "Upload PDF File(s)",
                        type="filepath",
                        file_count="multiple",
                        size="sm",
                    )
                    ingested_dataset = gr.List(
                        self._list_ingested_files,
                        headers=["File name"],
                        label="Uploaded Files",
                        height=235,
                        interactive=False,
                        render=False,
                    )
                    upload_button.upload(
                        self._upload_file,
                        inputs=upload_button,
                        outputs=ingested_dataset,
                    )
                    ingested_dataset.change(
                        self._list_ingested_files,
                        outputs=ingested_dataset,
                    )
                    ingested_dataset.render()
                    
                    deselect_file_button = gr.components.Button(
                        "De-select selected file", size="sm", interactive=False
                    )
                    selected_text = gr.components.Textbox(
                        "All files", label="Selected File", max_lines=1
                    )
                    
                    # Row for file actions
                    with gr.Row():
                        # Delete buttons
                        delete_file_button = gr.components.Button(
                            "🗑️ Delete selected file",
                            size="sm",
                            visible=settings().ui.delete_file_button_enabled,
                            interactive=False
                        )
                        delete_files_button = gr.components.Button(
                            "⚠️ Delete ALL files",
                            size="sm",
                            visible=settings().ui.delete_all_files_button_enabled,
                        )
                    
                    deselect_file_button.click(
                        self._deselect_selected_file,
                        outputs=[
                            delete_file_button,
                            deselect_file_button,
                            selected_text,
                        ],
                    )
                    ingested_dataset.select(
                        fn=self._selected_a_file,
                        outputs=[
                            delete_file_button,
                            deselect_file_button,
                            selected_text,
                        ],
                    )
                    
                    delete_file_button.click(
                        self._delete_selected_file,
                        outputs=[
                            ingested_dataset,
                            delete_file_button,
                            deselect_file_button,
                            selected_text,
                        ],
                    )
                    delete_files_button.click(
                        self._delete_all_files,
                        outputs=[
                            ingested_dataset,
                            delete_file_button,
                            deselect_file_button,
                            selected_text,
                        ],
                    )

                with gr.Column(scale=7, elem_id="col"):
                    # Placeholder for extraction interface
                    with gr.Column(elem_id="extraction-area"):
                        gr.Markdown("""
                        # Benefit Extraction
                        
                        Select a PDF file to begin the extraction process.
                        
                        The extraction process will:
                        1. Identify benefit summary pages
                        2. Extract benefit information
                        3. Generate a comparison Excel file
                        """)

            with gr.Row():
                avatar_byte = AVATAR_BOT.read_bytes()
                f_base64 = f"data:image/png;base64,{base64.b64encode(avatar_byte).decode('utf-8')}"
                gr.HTML(
                    f"<div class='footer'><a class='footer-zylon-link' href='https://zylon.ai/'>Maintained by Zylon <img class='footer-zylon-ico' src='{f_base64}' alt=Zylon></a></div>"
                )

        return blocks

    def get_ui_blocks(self) -> gr.Blocks:
        if self._ui_block is None:
            self._ui_block = self._build_ui_blocks()
        return self._ui_block

    def mount_in_app(self, app: FastAPI, path: str) -> None:
        blocks = self.get_ui_blocks()
        blocks.queue()
        logger.info("Mounting the gradio UI, at path=%s", path)
        gr.mount_gradio_app(app, blocks, path=path, favicon_path=AVATAR_BOT)


if __name__ == "__main__":
    ui = global_injector.get(PrivateGptUi)
    _blocks = ui.get_ui_blocks()
    _blocks.queue()
    _blocks.launch(debug=False, show_api=False)
