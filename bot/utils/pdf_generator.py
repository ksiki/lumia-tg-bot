import asyncio
import json
import logging
import uuid
from datetime import time, timedelta
from logging import Logger
from asyncio import Queue
from pathlib import Path
from typing import Any, Final
from docxtpl import DocxTemplate

from database.data_services import DataServices
from scenarios.message_sendler import create_delayed_message


BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
PDF_TENPLATES_DIR: Final[Path] = BASE_DIR / "assets" / "pdf_templates"
PREDICTIONS_DIR: Final[Path] = BASE_DIR / "assets" / "predictions"
PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

PDF_QUEUE: Final[Queue] = Queue()
LOG: Final[Logger] = logging.getLogger(__name__)


async def pdf_worker(data_services: DataServices) -> None:
    while True:
        prediction_id, output_name, scheduler, delayed_message_method, args, failed_generate_method, failed_args = await PDF_QUEUE.get()
        LOG.info(f"Start generate pfd file for prediction id: {prediction_id}")

        try:
            prediction = data_services.get_prediction_by_id(prediction_id)
            data = json.loads(prediction["prediction"])
            template = prediction["type"]
            start_time = time.time()

            path = await generate_pdf(data, template, output_name)
            

            elapsed_time = time.time() - start_time
            wait_limit = 180
            remaining_wait = max(0, wait_limit - elapsed_time)

            create_delayed_message(
                scheduler, 
                delayed_message_method, 
                timedelta(seconds=remaining_wait),
                args + [path]
            )
        except Exception as e:
            LOG.error(f"Failed generate pfd file: {template}; Error: {e}")
            await create_delayed_message(
                scheduler, 
                failed_generate_method, 
                0,
                failed_args
            )
        finally:
            PDF_QUEUE.task_done()


async def generate_pdf(data: dict[str, Any], template_name: str, output_filename: str) -> Path:
    unique_id = uuid.uuid4().hex
    temp_docx_path = PREDICTIONS_DIR / f"temp_{unique_id}.docx"
    
    try:
        doc = DocxTemplate(PDF_TENPLATES_DIR / f"{template_name}.docx")
        doc.render(data)
        doc.save(temp_docx_path)

        process = await asyncio.create_subprocess_exec(
            'soffice', 
            '--headless', 
            '--convert-to', 
            'pdf', 
            '--outdir', 
            str(PREDICTIONS_DIR), 
            str(temp_docx_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        generated_pdf_path = PREDICTIONS_DIR / f"temp_{unique_id}.pdf"
        final_pdf_path = PREDICTIONS_DIR / output_filename
        
        if generated_pdf_path.exists():
            if final_pdf_path.exists():
                final_pdf_path.unlink()  
            generated_pdf_path.rename(final_pdf_path)
            return final_pdf_path
        else:
            raise FileNotFoundError("LibreOffice не смог создать PDF файл")
    except Exception as e:
        LOG.error(f"Failed convert docx ro pdf file: {e}")
        raise
    finally:
        if temp_docx_path.exists():
            temp_docx_path.unlink()