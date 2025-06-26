from fastapi import APIRouter, Query
from typing import Dict, Any
from app.services.summarize import get_weekly_top3_summaries

router = APIRouter()

@router.get(
    "/summarize/weekly",
    summary="주식 심볼별 주차별 상위 3개 기사 요약",
    description="주식 심볼, 시작일, 종료일을 입력받아 해당 기간 내 주차별 상위 3개 기사 요약 정보를 반환합니다.",
    tags=["article analyze"]
)
def get_weekly_summarize(
    stock_symbol: str = Query(..., description="종목 코드, 예: 'GS'"),
    start_date: str = Query(..., description="시작일, 예: '2023-12-11'"),
    end_date: str = Query(..., description="종료일, 예: '2023-12-14'")
) -> Dict[str, Any]:
    result = get_weekly_top3_summaries(stock_symbol, start_date, end_date)
    return result
'''
[response_body 예시: 일부만 표시]
    {
      "article": "By Lananh Nguyen NEW YORK, Dec 12 (Reuters) - Goldman Sachs' GS.N head of global commodities Ed Emerson will retire in March after more than 24 years at the Wall Street giant, according to a memo seen by Reuters. He will be succeeded by Xiao Qin and Nitin Jindal, who will jointly lead the firm's storied commodities business, according to a separate memo. Acompany spokesperson confirmed the contents of the memo. Revenue from Goldman's commodities business has been significantly lower in the first three quarters of 2023, according to the company's earnings filings. Still, the business has been a bright spot in results in recent years. Emerson, 47, will become an advisory director to Goldman after he steps down. The executive joined the firm in 1999 as an analyst and climbed the ranks to become managing director in 2008, then partner in 2012. \"He played a critical role in advancing the firm's oil business,\" wrote Ashok Varadhan, Dan Dees and Jim Esposito, the three leaders of Goldman's global banking and markets division, in a memo. Emerson helped \"cement Goldman Sachs' position as a leading franchise in commodities,\" they added. He previously ran global oil and refined products trading. Qin leads commodities trading in Europe, the Middle East, Africa and Asia Pacific. He also runs trading for oil and refined products worldwide. The executive was promoted to managing director in 2010 and partner in 2016. Jindal manages commodities trading in the Americas and natural gas and power trading in North America. He joined Goldman as a partner in 2018. (Reporting by Lananh Nguyen; Editing by Sinead Cruise) ((Lananh.Nguyen@thomsonreuters.com; +1 (646) 696 4829;)) The views and opinions expressed herein are the views and opinions of the author and do not necessarily reflect those of Nasdaq, Inc.",
      "date": "2023-12-12",
      "weekstart": "2023-12-10",
      "score": 0.575,
      "pos_cnt": 3,
      "neg_cnt": 0,
      "summary": "- 월스트리트 거물인 골드만사의 에드 엠러슨은 24년 이상 근무한 뒤 3월에 은퇴할 예정입니다.\n- 그의 후임은 샤오 친과 니틴 진달이 차지하게 되며, 이들은 회사의 유명한 상품 부문을 공동으로 이끌게 될 것입니다.\n- 2023년 상반기 동안 골드만의 상품 부문에서의 수익은 상당히 감소했습니다."
    }
  ]
}
'''
