# 임시 보고서 DB 및 시퀀스
from typing import List
from app.schemas.report import Report

fake_reports_db: List[Report] = []
report_id_seq = 1

def get_fake_reports_db():
    return fake_reports_db

def increment_report_id_seq():
    global report_id_seq
    report_id_seq += 1
    return report_id_seq - 1
