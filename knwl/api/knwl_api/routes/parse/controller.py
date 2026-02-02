from typing import Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from tempfile import NamedTemporaryFile
import os, datetime, io, zipfile
from fastapi import FastAPI, UploadFile
import shutil
from pathlib import Path

from knwl.api.knwl_api.models.JobStatus import JobResponse
from knwl.api.knwl_api.tasks import add_job

router = APIRouter()

from .service import *
@router.post("/extract/markdown")
async def extract_markdown(file: UploadFile, page_number:int=None):
    try:
        file_path = save_upload_file_tmp(file)
        job_id = await add_job("parse", doc.model_dump())
        return JobResponse(job_id=job_id, message="Ingestion job started successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start ingestion job: {str(e)}",
        )
    return extract_pdf_to_markdown(,page_number)

@router.post("/extract/tables")
def extract_table(file: UploadFile, page_number:int=None):
    
    out_dir= create_output_dir()
    file_name, file_extension = os.path.splitext(file.filename)
    extract_pdf_tables(save_upload_file_tmp((file)),page_number,out_dir)
    zip_stream = create_zip_stream(out_dir)
    
    return StreamingResponse(zip_stream, media_type="application/octet-stream", headers={"Content-Disposition": "attachment;  filename="+file_name+"_csv"+".zip"})

@router.post("/extract/images")
def extract_images(file: UploadFile, page_number:int=None):
    
    out_dir= create_output_dir()
    file_name, file_extension = os.path.splitext(file.filename)
    extract_json_and_images(save_upload_file_tmp((file)),out_dir,page_number)
    zip_stream = create_zip_stream(out_dir)

    return StreamingResponse(zip_stream, media_type="application/octet-stream", headers={"Content-Disposition": "attachment; filename="+file_name+".zip"})

def save_upload_file_tmp(upload_file: UploadFile) -> Path:
    try:
        suffix = Path(upload_file.filename).suffix
        with NamedTemporaryFile(delete=False,prefix=upload_file.filename, suffix=suffix) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)
    finally:
        
        upload_file.file.close()
    return tmp_path

def create_output_dir():
    output_dir = os.path.join('output', datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(output_dir)
    return output_dir

def create_zip_stream(output_dir):

    zip_stream = io.BytesIO()  
    with zipfile.ZipFile(zip_stream, "w") as zf:  
        for root, _, files in os.walk(output_dir):  
            for file in files:  
                file_path = os.path.join(root, file)  
                zf.write(file_path, os.path.relpath(file_path, output_dir))  
    zip_stream.seek(0) 
    return zip_stream