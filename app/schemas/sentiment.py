from typing import Dict, List, Optional
from pydantic import BaseModel

class WeeklySentimentResponse(BaseModel):
    weekly_scores: Dict[str, int]
    weekly_top3_articles: Optional[Dict[str, List[str]]] = None

class WeeklySentimentWithSummaryResponse(BaseModel):
    sentiment: Dict[str, int]
    summaries: Optional[Dict[str, List[str]]] = None

class WeeklyTop3ArticlesResponse(BaseModel):
    weekly_top3_articles: Dict[str, list]
