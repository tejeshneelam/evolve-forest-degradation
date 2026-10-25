"""
EvOLve Test Suite — tests/test_pdf_and_reports.py
Validates PDF clearance certificates and tactical mission dispatch documents.
"""

def test_export_pdf_report(client):
    """Verifies baseline forest monitoring PDF report generation."""
    res = client.get("/api/export-pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    # PDF binary must start with '%PDF-'
    assert res.content.startswith(b"%PDF-")
    assert len(res.content) > 1000


def test_construction_permit_pdf(client):
    """Verifies official Hill Slope Construction Clearance Certificate PDF."""
    res = client.get("/api/construction-permit-pdf/1")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF-")
    assert len(res.content) > 2000
    # Check Content-Disposition attachment header
    cd = res.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "Civil_Safety_Permit_Patch_" in cd


def test_ranger_patrol_pdf(client):
    """Verifies Tactical Forest Ranger Mission Dispatch PDF."""
    res = client.get("/api/ranger-patrol-pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF-")
    assert len(res.content) > 2000
    cd = res.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "Ranger_Patrol_Dispatch_Order_" in cd

