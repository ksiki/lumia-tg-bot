import asyncio
import json
import logging
import random
import uuid
import time
from datetime import timedelta
from logging import Logger
from asyncio import Queue
from pathlib import Path
from typing import Any, Final
from docxtpl import DocxTemplate

from config import DEBUG
from common.constants import DEBUG_WAIT
from database.data_services import DataServices
from scenarios.message_sendler import create_delayed_message


DOCX_EXT: Final[str] = ".docx"
PDF_EXT: Final[str] = ".pdf"
TEMP_FILE_PREFIX: Final[str] = "temp_"
FAILED_WAIT: Final[int] = 0

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
PDF_TEMPLATES_DIR: Final[Path] = BASE_DIR / "assets" / "pdf_templates"
PREDICTIONS_DIR: Final[Path] = BASE_DIR / "assets" / "predictions"
PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

PDF_QUEUE: Final[Queue] = Queue()
LOG: Final[Logger] = logging.getLogger(__name__)


async def pdf_worker(data_services: DataServices) -> None:
    while True:
        (
            prediction_id, 
            output_name, 
            scheduler, 
            delayed_method, 
            args, 
            failed_method, 
            failed_args
        ) = await PDF_QUEUE.get()
        
        LOG.info(f"Processing PDF generation for prediction ID: {prediction_id}")

        current_template = "unknown"
        try:
            prediction = await data_services.get_prediction_by_id(prediction_id)
            if not prediction:
                LOG.error(f"Prediction {prediction_id} not found in database")
                raise RuntimeError("Prediction exists check failed")

            current_template = prediction["type"]
            product = await data_services.get_product(current_template)
            
            prediction_data = json.loads(prediction["prediction"])
            
            start_mark = time.time()
            path = await generate_pdf(prediction_data, current_template, output_name)            
            elapsed = time.time() - start_mark

            if DEBUG:
                wait_limit = DEBUG_WAIT
            else:
                wait_limit = random.randint(product["min_generate_seconds"], product["max_generate_seconds"])

            remaining_wait = max(0.0, wait_limit - elapsed)

            create_delayed_message(
                scheduler, 
                delayed_method, 
                timedelta(seconds=remaining_wait),
                args + [prediction, path]
            )
            LOG.info(f"PDF successfully generated for ID: {prediction_id}")
        except Exception as e:
            LOG.error(f"Worker failed for template '{current_template}': {e}")
            create_delayed_message(
                scheduler, 
                failed_method, 
                timedelta(seconds=FAILED_WAIT),
                failed_args
            )
        finally:
            PDF_QUEUE.task_done()


async def generate_pdf(data: dict[str, Any], template_name: str, output_filename: str) -> Path:
    unique_suffix = uuid.uuid4().hex
    temp_docx_name = f"{TEMP_FILE_PREFIX}{unique_suffix}{DOCX_EXT}"
    temp_pdf_name = f"{TEMP_FILE_PREFIX}{unique_suffix}{PDF_EXT}"
    final_pdf_name = f"{output_filename}{PDF_EXT}"

    temp_docx_path = PREDICTIONS_DIR / temp_docx_name
    generated_pdf_path = PREDICTIONS_DIR / temp_pdf_name
    final_pdf_path = PREDICTIONS_DIR / final_pdf_name
    
    template_path = PDF_TEMPLATES_DIR / f"{template_name}{DOCX_EXT}"
    
    try:
        doc = DocxTemplate(template_path)
        doc.render(data)
        doc.save(temp_docx_path)

        process = await asyncio.create_subprocess_exec(
            'soffice',
            '--headless',
            '--invisible',
            '--nodefault',
            '--nofirststartwizard',
            '--nologo',
            '--convert-to', 'pdf',
            '--outdir', str(PREDICTIONS_DIR),
            str(temp_docx_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        if not generated_pdf_path.exists():
            LOG.error(f"LibreOffice failed to produce {generated_pdf_path}")
            raise FileNotFoundError("LibreOffice conversion failed to create PDF file")

        if final_pdf_path.exists():
            final_pdf_path.unlink()  
            
        generated_pdf_path.rename(final_pdf_path)
        return final_pdf_path

    except Exception as e:
        LOG.error(f"PDF generation error: {e}")
        raise
    finally:
        if temp_docx_path.exists():
            temp_docx_path.unlink()