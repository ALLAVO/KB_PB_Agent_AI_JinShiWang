# 날짜 변환, 텍스트 처리 등 자주 쓰는 함수
import datetime

def format_date(date_obj: datetime.date, fmt: str = "%Y-%m-%d") -> str:
    return date_obj.strftime(fmt)

def simple_text_clean(text: str) -> str:
    return text.strip()

pass