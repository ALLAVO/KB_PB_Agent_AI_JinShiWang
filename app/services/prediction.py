import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import shap
import ta
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
from app.db.connection import get_sqlalchemy_engine

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

FEATURES = [
    'SMA_5', 'SMA_20', 'SMA_diff',
    'RSI_14', 'Momentum_10', 'ROC_10',
    'price_to_peak', 'price_to_trough',
    'consecutive_up_days', 'consecutive_down_days'
]

def load_data(stock_symbol):
    """
    주어진 stock_symbol에 따라 적절한 테이블에서 데이터를 읽어와 DataFrame으로 반환합니다.
    DB 연결은 SQLAlchemy engine을 사용합니다.
    """
    engine = get_sqlalchemy_engine()
    first_char = stock_symbol[0].upper()
    if 'A' <= first_char <= 'D':
        table = 'fnspid_stock_price_a'
    elif 'E' <= first_char <= 'M':
        table = 'fnspid_stock_price_b'
    elif 'N' <= first_char <= 'Z':
        table = 'fnspid_stock_price_c'
    else:
        raise Exception("유효하지 않은 stock_symbol입니다.")
    query = f"SELECT * FROM {table} WHERE stock_symbol = %s ORDER BY date"
    df = pd.read_sql(query, engine, params=(stock_symbol,))
    if df.empty:
        raise ValueError(f"DB에서 {stock_symbol}에 해당하는 데이터가 없습니다.")
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def add_features(df):
    df['SMA_5'] = ta.trend.sma_indicator(df['close'], window=5)
    df['SMA_20'] = ta.trend.sma_indicator(df['close'], window=20)
    df['SMA_diff'] = df['SMA_5'] - df['SMA_20']

    df['RSI_14'] = ta.momentum.rsi(df['close'], window=14)
    df['Momentum_10'] = df['close'] - df['close'].shift(10)
    df['ROC_10'] = ta.momentum.roc(df['close'], window=10)

    df['rolling_max_20'] = df['close'].rolling(window=20).max()
    df['rolling_min_20'] = df['close'].rolling(window=20).min()
    df['price_to_peak'] = df['close'] / df['rolling_max_20']
    df['price_to_trough'] = df['close'] / df['rolling_min_20']

    df['up'] = (df['close'] > df['close'].shift(1)).astype(int)
    df['down'] = (df['close'] < df['close'].shift(1)).astype(int)
    df['consecutive_up_days'] = df['up'] * (df['up'].groupby((df['up'] != df['up'].shift()).cumsum()).cumcount() + 1)
    df['consecutive_down_days'] = df['down'] * (df['down'].groupby((df['down'] != df['down'].shift()).cumsum()).cumcount() + 1)

    df['future_return'] = df['close'].shift(-5) / df['close'] - 1
    df['target'] = df['future_return'].apply(lambda r: 1 if r >= 0.00267 else (-1 if r <= -0.00267 else 0))

    df.dropna(inplace=True)
    return df

def select_weekly_rows(df):
    df = df.resample('W-FRI').last()
    df.dropna(inplace=True)
    return df

def prepare_data(df, start_date, end_date):
    """
    end_date: 예측 기준 주간의 마지막 날짜 (토요일)
    학습: ~ end_date 까지 전체
    예측: 다음 주 금요일
    """
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # 학습 데이터: end_date까지
    df_train = df[df.index <= end_date]

    # 예측 대상: 그 다음 주 금요일
    next_friday = pd.to_datetime(end_date) + pd.Timedelta(days=6)
    df_test = df[df.index == next_friday]

    X_train = df_train[FEATURES]
    y_train = df_train['target']
    X_week = df_test[FEATURES]
    y_week = df_test['target']

    next_start_date = start_date + pd.Timedelta(days=7)
    next_end_date = end_date + pd.Timedelta(days=7)

    return X_train, y_train, X_week, y_week, next_start_date, next_end_date

def train_model(X_train, y_train):
    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    clf.fit(X_train, y_train)
    return clf

def explain_shap_week(clf, X_week, y_week, next_start_date, next_end_date, top_n=3):
    if X_week.empty:
        return pd.DataFrame()

    explainer = shap.TreeExplainer(clf)
    shap_values = explainer.shap_values(X_week)

    if isinstance(shap_values, list):
        class_to_index = {label: idx for idx, label in enumerate(clf.classes_)}
    else:
        shap_values = [shap_values]
        class_to_index = {clf.predict(X_week)[0]: 0}

    records = []

    for i in range(len(X_week)):
        pred = clf.predict(X_week.iloc[[i]])[0]
        true = y_week.iloc[i]
        class_idx = class_to_index.get(pred, 0)

        shap_row = shap_values[class_idx][i]  # shape: (n_features, n_classes)
        shap_row = shap_row[:, class_idx]     # ➤ 예측 클래스에 해당하는 SHAP 값만 추출

        sorted_idx = np.argsort(np.abs(shap_row))[::-1][:top_n]

        for rank, idx in enumerate(sorted_idx):
            records.append({
                'next_start_date': next_start_date.date(),
                'next_end_date' : next_end_date.date(),
                'prediction': pred,
                'actual': true,
                'feature': X_week.columns[idx],
                'shap_value': shap_row[idx],
                'rank': rank + 1
            })

    return pd.DataFrame(records)


def generate_prompt(df, ticker, end_date):
    """
    SHAP 결과 DataFrame을 바탕으로 3줄 요약 생성용 프롬프트 생성
    """

    # 예측 방향별 피처 해석 사전
    feature_interpretation = {
        "price_to_peak": {
            "상승": "주가가 고점 부근에 위치해 강세 흐름이 유지되고 있습니다.",
            "하락": "주가가 고점 부근에 머물며 조정 가능성이 나타났습니다.",
            "보합": "주가가 고점 근처에서 방향을 탐색 중입니다."
        },
        "SMA_5": {
            "상승": "단기 이동평균선 기준으로 상승 흐름이 강화되고 있습니다.",
            "하락": "단기 추세가 약세로 전환되었습니다.",
            "보합": "단기 주가는 뚜렷한 방향 없이 횡보 중입니다."
        },
        "SMA_20": {
            "상승": "중기 이동평균선이 상승 흐름을 따라가며 안정적인 상승세를 보여주고 있습니다.",
            "하락": "중기 이동평균선이 하락세로 돌아서며 추세 전환의 조짐이 나타났습니다.",
            "보합": "중기 이동평균선이 횡보세를 유지하며 뚜렷한 방향성이 나타나지 않고 있습니다."
        },
        "ROC_10": {
            "상승": "최근 10일간 수익률이 개선되며 상승 탄력이 붙고 있습니다.",
            "하락": "최근 수익률이 둔화되며 상승 피로가 나타났습니다.",
            "보합": "수익률 변화가 크지 않아 방향성이 뚜렷하지 않습니다."
        },
        "SMA_diff": {
            "상승": "단기 이동평균이 중기선을 상회하며 상승 흐름을 보입니다.",
            "하락": "단기 이동평균이 중기선보다 낮아 하락 전환을 시사합니다.",
            "보합": "단기와 중기 평균 간의 차이가 미미합니다."
        },
        "RSI_14": {
            "상승": "매수세가 강해지며 RSI가 우상향하고 있습니다.",
            "하락": "과매수 구간에서 이탈하며 매도 신호가 발생했습니다.",
            "보합": "RSI가 중립 영역에서 움직이고 있습니다."
        },
        "Momentum_10": {
            "상승": "과거 대비 상승 모멘텀이 이어지고 있습니다.",
            "하락": "상승 탄력이 둔화되며 반락 조짐이 나타났습니다.",
            "보합": "추세 전환 없이 모멘텀은 안정된 상태입니다."
        },
        "price_to_trough": {
            "상승": "저점 대비 회복세가 강하게 나타나고 있습니다.",
            "하락": "최근 저점 대비 과도한 반등으로 부담이 존재합니다.",
            "보합": "저점 대비 완만한 회복세를 보이고 있습니다."
        },
        "consecutive_up_days": {
            "상승": "지속적 상승세가 이어지며 강한 흐름을 보여줍니다.",
            "하락": "과열된 흐름 이후 조정이 나타날 수 있습니다.",
            "보합": "상승일수가 제한되어 뚜렷한 추세는 없습니다."
        },
        "consecutive_down_days": {
            "상승": "하락세에서 벗어나 반등 가능성이 보입니다.",
            "하락": "연속 하락 흐름이 지속되고 있습니다.",
            "보합": "하락세는 멈췄지만 뚜렷한 반등 신호는 없습니다."
        }
    }

    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    next_start = df["next_start_date"].iloc[0]
    next_end = df["next_end_date"].iloc[0]
    prediction = df["prediction"].iloc[0]
    direction = "하락" if prediction == -1 else "상승" if prediction == 1 else "보합"

    top_features = df["feature"].tolist()

    # 예측 방향에 따른 해석 요약
    shap_summary = "\n".join([
        f"- {feature_interpretation.get(f, {}).get(direction, '기술적 요인이 감지되었습니다.')}"
        for f in top_features
    ])

    prompt = f"""
    {end_date.strftime('%m월 %d일')}을 기준으로, AI 모델은 과거 주가 데이터를 바탕으로 향후 1주일({next_start.strftime('%m월 %d일')}~{next_end.strftime('%m월 %d일')}) 동안의 주가 흐름을 예측했습니다.
    이번 예측 결과, 해당 종목은 '{direction}' 가능성이 높은 것으로 판단되었습니다.
    
    모델이 중요하게 반영한 요인들은 다음과 같은 흐름을 보여주었습니다:
    {shap_summary}
    
    위 내용을 바탕으로, 다음 조건을 만족하는 3~4줄 요약문을 작성해 주세요:
    
    1. **첫 문장은 반드시** ‘{end_date.strftime('%m월 %d일')}을 기준으로, AI 모델이 ~ 예측했습니다.’ 로 시작해 주세요.  
    2. 이후에는 예측 방향(‘{direction}’)과 그에 영향을 준 흐름(고점 위치, 추세 약화, 수익률 둔화 등)을 자연스럽게 풀어 주세요.  
    3. 기술 용어나 수치는 사용하지 말고, 자연스러운 보고서 스타일로 작성해 주세요.
    """
    return prompt


def get_summary_from_openai(prompt):
    """
    OpenAI API를 통해 세 줄 요약 생성
    """
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 금융 데이터 분석 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].message.content.strip()



def run_prediction(request, prediction_id):
    # PredictionRequest: stock_symbol, start_date, end_date 등 포함
    stock_symbol = request.stock_symbol
    start_date = request.start_date
    end_date = request.end_date
    # 데이터 로드 및 피처 생성
    df = load_data(stock_symbol)
    df = add_features(df)
    df = select_weekly_rows(df)
    X_train, y_train, X_week, y_week, next_start_date, next_end_date = prepare_data(df, start_date, end_date)
    # 모델 학습 및 예측
    clf = train_model(X_train, y_train)
    shap_df = explain_shap_week(clf, X_week, y_week, next_start_date, next_end_date)
    prompt_text = generate_prompt(shap_df, ticker=stock_symbol, end_date=end_date)
    summary = get_summary_from_openai(prompt_text)
    # 예측 결과
    prediction = int(clf.predict(X_week)[0]) if not X_week.empty else 0
    return type('PredictionResult', (), {{
        'prediction_id': prediction_id,
        'stock_symbol': stock_symbol,
        'start_date': start_date,
        'end_date': end_date,
        'prediction': prediction,
        'summary': summary
    }})()


def get_prediction_summary(stock_symbol, start_date, end_date):
    """
    주어진 stock_symbol, start_date, end_date로 AI 요약 결과를 반환하는 함수
    """
    df = load_data(stock_symbol)
    df = add_features(df)
    df = select_weekly_rows(df)
    X_train, y_train, X_week, y_week, next_start_date, next_end_date = prepare_data(df, start_date, end_date)
    clf = train_model(X_train, y_train)
    shap_df = explain_shap_week(clf, X_week, y_week, next_start_date, next_end_date)
    if shap_df.empty:
        return "해당 기간에 대한 예측 요약을 생성할 수 있는 데이터가 부족합니다. 날짜 범위 또는 종목 코드를 확인해 주세요."
    prompt_text = generate_prompt(shap_df, ticker=stock_symbol, end_date=end_date)
    summary = get_summary_from_openai(prompt_text)
    return summary

# === 메인 실행 ===
if __name__ == "__main__":
    # ticker = 'AAPL'
    # start_date = '2023-03-05'
    # end_date = '2023-03-11'
    ticker = 'GS'
    start_date = '2023-12-10'
    end_date = '2023-12-16'

    df = load_data(ticker)  # ticker를 인자로 전달하여 DB에서 데이터 로드
    df = add_features(df)
    df = select_weekly_rows(df)
    X_train, y_train, X_week, y_week, next_start_date, next_end_date = prepare_data(df, start_date, end_date)

    clf = train_model(X_train, y_train)
    shap_df = explain_shap_week(clf, X_week, y_week, next_start_date, next_end_date)
    prompt_text = generate_prompt(shap_df, ticker=ticker, end_date=end_date)
    summary = get_summary_from_openai(prompt_text)
    print("\n=== AI 요약 결과 ===\n")
    print(summary)
