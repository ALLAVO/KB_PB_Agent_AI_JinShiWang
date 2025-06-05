# 보고서 생성/조회 API
from fastapi import APIRouter, HTTPException

from app.db.fake_report_db import get_fake_reports_db, increment_report_id_seq
from app.schemas.report import Report, ReportCreate
from app.services.report_gen import generate_report

router = APIRouter()

@router.post("/reports/", response_model=Report)
def create_report(report: ReportCreate):
    report_id = increment_report_id_seq()
    new_report = generate_report(report_id, report)
    get_fake_reports_db().append(new_report)
    return new_report

@router.get("/reports/{report_id}", response_model=Report)
def get_report(report_id: int):
    for report in get_fake_reports_db():
        if report.id == report_id:
            return report
    raise HTTPException(status_code=404, detail="Report not found")