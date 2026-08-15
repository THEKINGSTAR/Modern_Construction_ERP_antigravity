import pytest
from uuid import uuid4
import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.documents import Document

def test_document_upload_and_download(client: TestClient, db_session: Session, auth_headers, test_tenant):
    entity_id = uuid4()
    
    # Create a test file
    test_content = b"This is a test document."
    test_filename = "test_doc.txt"
    with open(test_filename, "wb") as f:
        f.write(test_content)
        
    try:
        # Upload
        with open(test_filename, "rb") as f:
            res = client.post(
                "/api/v1/documents/upload",
                data={
                    "entity_type": "PURCHASE_ORDER",
                    "entity_id": str(entity_id),
                    "title": "My PO Document"
                },
                files={"file": (test_filename, f, "text/plain")},
                headers=auth_headers
            )
            
        assert res.status_code == 201
        doc_data = res.json()
        assert doc_data["title"] == "My PO Document"
        assert doc_data["mime_type"] == "text/plain"
        assert doc_data["is_malware_scanned"] == True
        assert doc_data["malware_scan_result"] == "CLEAN"
        
        doc_id = doc_data["id"]
        
        # Download
        dl_res = client.get(f"/api/v1/documents/{doc_id}/download", headers=auth_headers)
        assert dl_res.status_code == 200
        assert dl_res.content == test_content
        
    finally:
        if os.path.exists(test_filename):
            os.remove(test_filename)
