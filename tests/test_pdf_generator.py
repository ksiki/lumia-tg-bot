import pytest
import json
import asyncio
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch, AsyncMock
from bot.utils.pdf_generator import generate_pdf, pdf_worker, PDF_QUEUE

@pytest.mark.asyncio
class TestPdfGenerator:
    @patch("bot.utils.pdf_generator.DocxTemplate")
    @patch("asyncio.create_subprocess_exec")
    @patch("bot.utils.pdf_generator.Path.exists")
    @patch("bot.utils.pdf_generator.Path.rename")
    @patch("bot.utils.pdf_generator.Path.unlink")
    async def test_generate_pdf_success(self, mock_unlink, mock_rename, mock_exists, mock_subproc, mock_docx):
        mock_exists.return_value = True
        
        process_mock = AsyncMock()
        process_mock.communicate.return_value = (b"stdout", b"stderr")
        mock_subproc.return_value = process_mock

        data = {"name": "Test User"}
        template = "fate_matrix"
        output = "result_123"

        result_path = await generate_pdf(data, template, output)

        mock_docx.return_value.render.assert_called_with(data)
        mock_subproc.assert_called()  
        assert result_path.name == f"{output}.pdf"
        mock_unlink.assert_called()

    @patch("bot.utils.pdf_generator.DocxTemplate")
    @patch("asyncio.create_subprocess_exec")
    @patch("bot.utils.pdf_generator.Path.exists")
    async def test_generate_pdf_conversion_failure(self, mock_exists, mock_subproc, mock_docx):
        mock_exists.return_value = False
        
        process_mock = AsyncMock()
        process_mock.communicate.return_value = (b"", b"error")
        mock_subproc.return_value = process_mock

        with pytest.raises(FileNotFoundError):
            await generate_pdf({}, "template", "out")

    @patch("bot.utils.pdf_generator.generate_pdf")
    @patch("bot.utils.pdf_generator.create_delayed_message")
    async def test_pdf_worker_success(self, mock_delayed_msg, mock_gen_pdf):
        mock_data_services = AsyncMock()

        mock_prediction = {
            "id": 1,
            "type": "fate_matrix",
            "prediction": json.dumps({"key": "val"})
        }
        mock_product = {
            "min_generate_seconds": 1,
            "max_generate_seconds": 2
        }
        
        mock_data_services.get_prediction_by_id.return_value = mock_prediction
        mock_data_services.get_product.return_value = mock_product
        mock_gen_pdf.return_value = Path("fake.pdf")

        task_args = (
            1, "output", "scheduler_obj", "delayed_method", ["arg1"], 
            "failed_method", ["fail_arg"]
        )
        await PDF_QUEUE.put(task_args)

        worker_task = asyncio.create_task(pdf_worker(mock_data_services))
        await PDF_QUEUE.join()
        worker_task.cancel()

        mock_delayed_msg.assert_called_once()
        args, kwargs = mock_delayed_msg.call_args
        assert args[3][-1] == Path("fake.pdf")
        assert args[3][-2] == mock_prediction

    @patch("bot.utils.pdf_generator.create_delayed_message")
    async def test_pdf_worker_prediction_not_found(self, mock_delayed_msg):
        mock_data_services = AsyncMock()
        mock_data_services.get_prediction_by_id.return_value = None

        await PDF_QUEUE.put((999, "out", "sched", "meth", [], "failed_meth", ["fail"]))
        
        worker_task = asyncio.create_task(pdf_worker(mock_data_services))
        await PDF_QUEUE.join()
        worker_task.cancel()

        mock_delayed_msg.assert_called_with(
            "sched", "failed_meth", timedelta(seconds=0), ["fail"]
        )