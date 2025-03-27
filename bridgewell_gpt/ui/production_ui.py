"""Production-ready UI implementation for the Benefit Extraction Tool."""

import base64
import logging
import os
from pathlib import Path
from typing import Any, Optional

import gradio as gr  # type: ignore
from fastapi import FastAPI, HTTPException
from gradio.themes.utils.colors import slate  # type: ignore
from injector import inject, singleton
from pydantic import BaseModel

from bridgewell_gpt.constants import PROJECT_ROOT_PATH
from bridgewell_gpt.di import global_injector
from bridgewell_gpt.server.ingest.ingest_service import IngestService
from bridgewell_gpt.server.extraction.extraction_service import ExtractionService
from bridgewell_gpt.settings.settings import settings
from bridgewell_gpt.ui.images import logo_svg

logger = logging.getLogger(__name__)

THIS_DIRECTORY_RELATIVE = Path(__file__).parent.relative_to(PROJECT_ROOT_PATH)
AVATAR_BOT = THIS_DIRECTORY_RELATIVE / "avatar-bot.ico"

UI_TAB_TITLE = "Benefit Extraction Tool"


class ExtractionStatus(BaseModel):
    """Model for tracking extraction status."""
    status: str
    progress: float
    message: str
    error: Optional[str] = None


def setup_ui_directories() -> None:
    """Create necessary directories for the UI if they don't exist."""
    ui_settings = settings().ui
    
    # Create output directory
    output_dir = Path(ui_settings.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created output directory: {output_dir}")
    
    # Create template directory
    template_dir = Path(ui_settings.template_directory)
    template_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created template directory: {template_dir}")
    
    # Check if template file exists
    template_file = template_dir / "benefit_comparison_template.xlsx"
    if not template_file.exists():
        logger.warning(f"Template file not found at: {template_file}")
        logger.warning("Please place the benefit comparison template Excel file in the template directory.")


@singleton
class ProductionUI:
    @inject
    def __init__(
        self,
        ingest_service: IngestService,
        extraction_service: ExtractionService,
    ) -> None:
        self._ingest_service = ingest_service
        self._extraction_service = extraction_service
        self._ui_block = None
        self._selected_filename = None
        self._extraction_status = ExtractionStatus(
            status="idle",
            progress=0.0,
            message="Ready to extract benefits"
        )
        
        # Set up UI directories
        setup_ui_directories()

    def _list_ingested_files(self) -> list[list[str]]:
        """List all ingested files with error handling."""
        try:
            files = set()
            for ingested_document in self._ingest_service.list_ingested():
                if ingested_document.doc_metadata is None:
                    continue
                file_name = ingested_document.doc_metadata.get(
                    "file_name", "[FILE NAME MISSING]"
                )
                files.add(file_name)
            return [[row] for row in files]
        except Exception as e:
            logger.error(f"Error listing ingested files: {e}")
            return []

    def _upload_file(self, files: list[str]) -> None:
        """Handle file upload with validation and error handling."""
        try:
            if not files:
                raise ValueError("No files provided")

            logger.debug("Processing %d files", len(files))
            paths = [Path(file) for file in files]

            # Validate file types
            for path in paths:
                if not path.suffix.lower() == '.pdf':
                    raise ValueError(f"Invalid file type: {path.suffix}. Only PDF files are supported.")

            # Remove existing documents with same names
            file_names = [path.name for path in paths]
            doc_ids_to_delete = []
            for ingested_document in self._ingest_service.list_ingested():
                if (
                    ingested_document.doc_metadata
                    and ingested_document.doc_metadata["file_name"] in file_names
                ):
                    doc_ids_to_delete.append(ingested_document.doc_id)

            if doc_ids_to_delete:
                logger.info(
                    "Replacing %d existing document(s)",
                    len(doc_ids_to_delete),
                )
                for doc_id in doc_ids_to_delete:
                    self._ingest_service.delete(doc_id)

            # Ingest new files
            self._ingest_service.bulk_ingest([(str(path.name), path) for path in paths])
            logger.info("Successfully uploaded %d files", len(files))

        except Exception as e:
            logger.error(f"Error uploading files: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    def _delete_selected_file(self) -> Any:
        """Delete selected file with error handling."""
        try:
            if not self._selected_filename:
                raise ValueError("No file selected")

            logger.debug("Deleting file: %s", self._selected_filename)
            for ingested_document in self._ingest_service.list_ingested():
                if (
                    ingested_document.doc_metadata
                    and ingested_document.doc_metadata["file_name"]
                    == self._selected_filename
                ):
                    self._ingest_service.delete(ingested_document.doc_id)

            self._selected_filename = None
            return [
                gr.List(self._list_ingested_files()),
                gr.components.Button(interactive=False),
                gr.components.Button(interactive=False),
                gr.components.Textbox("All files"),
            ]
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    def _delete_all_files(self) -> Any:
        """Delete all files with error handling."""
        try:
            ingested_files = self._ingest_service.list_ingested()
            logger.debug("Deleting %d files", len(ingested_files))
            
            for ingested_document in ingested_files:
                self._ingest_service.delete(ingested_document.doc_id)

            self._selected_filename = None
            return [
                gr.List(self._list_ingested_files()),
                gr.components.Button(interactive=False),
                gr.components.Button(interactive=False),
                gr.components.Textbox("All files"),
            ]
        except Exception as e:
            logger.error(f"Error deleting all files: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    def _deselect_selected_file(self) -> Any:
        """Deselect the currently selected file."""
        self._selected_filename = None
        return [
            gr.components.Button(interactive=False),
            gr.components.Button(interactive=False),
            gr.components.Textbox("All files"),
        ]

    def _selected_a_file(self, select_data: gr.SelectData) -> Any:
        """Handle file selection with validation."""
        try:
            if not select_data.value:
                raise ValueError("No file selected")

            self._selected_filename = select_data.value
            return [
                gr.components.Button(interactive=True),
                gr.components.Button(interactive=True),
                gr.components.Textbox(self._selected_filename),
            ]
        except Exception as e:
            logger.error(f"Error selecting file: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    def _start_extraction(self, company_name: str) -> Any:
        """Start the benefit extraction process."""
        try:
            if not self._selected_filename:
                raise ValueError("Please select a file first")

            if not company_name:
                raise ValueError("Please enter a company name")

            # Update status to processing
            self._extraction_status = ExtractionStatus(
                status="processing",
                progress=0.2,
                message="Starting extraction process..."
            )

            # Start the extraction process
            output_path, extraction_results = self._extraction_service.create_benefit_comparison(
                file_name=self._selected_filename,
                company_name=company_name
            )

            # Update status to completed
            self._extraction_status = ExtractionStatus(
                status="completed",
                progress=1.0,
                message="Extraction completed successfully",
                error=None
            )

            # Return updated UI state with file path
            return [
                gr.update(value="Extraction completed successfully"),
                gr.update(value=str(output_path), visible=True)
            ]

        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            self._extraction_status = ExtractionStatus(
                status="error",
                progress=0.0,
                message=f"Extraction failed: {str(e)}",
                error=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))

    def _build_ui_blocks(self) -> gr.Blocks:
        """Build the production UI with error handling and progress tracking."""
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
            "hr { margin-top: 1em; margin-bottom: 1em; border: 0; border-top: 1px solid #FFF; }",
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
                    # Extraction Interface
                    with gr.Column(elem_id="extraction-area"):
                        gr.Markdown("""
                        # Benefit Extraction
                        
                        Select a PDF file and enter company details to begin the extraction process.
                        """)

                        # Company Information
                        with gr.Group():
                            gr.Markdown("### Company Information")
                            company_name = gr.Textbox(
                                label="Company Name",
                                placeholder="Enter company name",
                                lines=1
                            )

                        # Extraction Controls
                        with gr.Group():
                            gr.Markdown("### Extraction Controls")
                            extract_button = gr.Button(
                                "Start Extraction",
                                variant="primary",
                                size="lg"
                            )

                        # Status and Progress
                        with gr.Group():
                            gr.Markdown("### Status")
                            status_text = gr.Textbox(
                                label="Status",
                                value="Ready to extract benefits",
                                interactive=False
                            )
                            # progress_bar = gr.Slider(
                            #     minimum=0,
                            #     maximum=1,
                            #     value=0,
                            #     step=0.1,
                            #     label="Progress",
                            #     interactive=False
                            # )

                        # Results
                        with gr.Group():
                            gr.Markdown("### Results")
                            download_button = gr.File(
                                label="Download Excel",
                                interactive=True,
                                visible=False,
                                type="filepath"
                            )

                        # Connect components
                        extract_button.click(
                            fn=self._start_extraction,
                            inputs=[company_name],
                            outputs=[
                                status_text,
                                download_button
                            ],
                            show_progress="minimal"  # Show minimal progress UI
                        )

        return blocks

    def get_ui_blocks(self) -> gr.Blocks:
        """Get or create the UI blocks."""
        if self._ui_block is None:
            self._ui_block = self._build_ui_blocks()
        return self._ui_block

    def mount_in_app(self, app: FastAPI, path: str) -> None:
        """Mount the UI in the FastAPI application."""
        blocks = self.get_ui_blocks()
        blocks.queue()
        logger.info("Mounting the production UI at path=%s", path)
        gr.mount_gradio_app(app, blocks, path=path, favicon_path=AVATAR_BOT)


if __name__ == "__main__":
    ui = global_injector.get(ProductionUI)
    _blocks = ui.get_ui_blocks()
    _blocks.queue()
    _blocks.launch(debug=False, show_api=False) 