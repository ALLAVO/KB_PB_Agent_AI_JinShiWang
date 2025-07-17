import json
import os
import gzip
from datetime import datetime, timedelta
from app.db.connection import check_db_connection
from app.core.config import settings

# 캐시 설정
CACHE_DIR = settings.cache_dir if hasattr(settings, 'cache_dir') else "/Users/hyungjuncho/Documents/SNU_BFA/KB_capstone/KB_PB_Agent_AI_JinShiWang/app/cache"
MCDONALD_CACHE_FILE = os.path.join(CACHE_DIR, "mcdonald_dict.json.gz")
CACHE_METADATA_FILE = os.path.join(CACHE_DIR, "cache_metadata.json")
CACHE_EXPIRY_HOURS = settings.cache_expiry_hours if hasattr(settings, 'cache_expiry_hours') else 168  # 7일

# 전역 변수: McDonald 사전 메모리 캐시
_mcdonald_dict = None

def ensure_cache_dir():
    """캐시 디렉토리 생성"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"[INFO] 캐시 디렉토리 생성: {CACHE_DIR}")

def export_mcdonald_dict_to_json():
    """
    Cloud SQL에서 McDonald 사전을 JSON 파일로 내보내기 (일회성 작업)
    """
    print("[INFO] McDonald 사전을 Cloud SQL에서 JSON으로 내보내는 중...")
    
    conn = check_db_connection()
    if conn is None:
        print("[ERROR] DB 연결 실패")
        return False
    
    try:
        ensure_cache_dir()
        
        cur = conn.cursor()
        cur.execute("SELECT word, positive, negative, uncertainty, litigious, constraining FROM mcdonald_masterdictionary")
        rows = cur.fetchall()
        
        mcdonald_dict = {}
        for row in rows:
            word, positive, negative, uncertainty, litigious, constraining = row
            mcdonald_dict[word] = {
                'positive': positive,
                'negative': negative,
                'uncertainty': uncertainty,
                'litigious': litigious,
                'constraining': constraining
            }
        
        # 압축된 JSON 파일로 저장
        with gzip.open(MCDONALD_CACHE_FILE, 'wt', encoding='utf-8') as f:
            json.dump(mcdonald_dict, f, indent=2)
        
        # 메타데이터 저장
        metadata = {
            "created_at": datetime.now().isoformat(),
            "word_count": len(mcdonald_dict),
            "db_query_time": datetime.now().isoformat()
        }
        
        with open(CACHE_METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        cur.close()
        conn.close()
        
        print(f"[INFO] McDonald 사전 JSON 내보내기 완료: {len(mcdonald_dict)}개 단어")
        print(f"[INFO] 파일 저장 위치: {MCDONALD_CACHE_FILE}")
        return True
        
    except Exception as e:
        print(f"[ERROR] McDonald 사전 JSON 내보내기 실패: {e}")
        if conn:
            conn.close()
        return False

def is_cache_valid():
    """
    캐시가 유효한지 확인 (파일 존재 여부 및 만료 시간 체크)
    """
    if not os.path.exists(MCDONALD_CACHE_FILE) or not os.path.exists(CACHE_METADATA_FILE):
        return False
    
    try:
        with open(CACHE_METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        created_at = datetime.fromisoformat(metadata['created_at'])
        expiry_time = created_at + timedelta(hours=CACHE_EXPIRY_HOURS)
        
        return datetime.now() < expiry_time
    except Exception as e:
        print(f"[WARNING] 캐시 메타데이터 확인 실패: {e}")
        return False

def load_mcdonald_dictionary():
    """
    McDonald 사전을 메모리에 로드하는 함수 (앱 시작 시 1회 실행)
    """
    global _mcdonald_dict
    if _mcdonald_dict is not None:
        return _mcdonald_dict
    
    print("[INFO] McDonald 사전을 메모리에 로드 중...")
    
    # 캐시 유효성 검사
    if not is_cache_valid():
        print("[INFO] 캐시가 유효하지 않음. 새로 생성합니다...")
        if not export_mcdonald_dict_to_json():
            print("[ERROR] 캐시 생성 실패. 빈 딕셔너리 반환.")
            return {}
    
    try:
        # 압축된 JSON 파일에서 로드
        with gzip.open(MCDONALD_CACHE_FILE, 'rt', encoding='utf-8') as f:
            _mcdonald_dict = json.load(f)
        
        print(f"[INFO] McDonald 사전 로드 완료: {len(_mcdonald_dict)}개 단어")
        return _mcdonald_dict
        
    except Exception as e:
        print(f"[ERROR] McDonald 사전 로드 실패: {e}")
        # JSON 로드 실패 시 DB에서 직접 로드 시도
        print("[INFO] DB에서 직접 로드를 시도합니다...")
        if export_mcdonald_dict_to_json():
            return load_mcdonald_dictionary()
        return {}

def get_mcdonald_word_info(word: str):
    """
    메모리에서 McDonald 사전 정보를 조회하는 함수
    """
    global _mcdonald_dict
    if _mcdonald_dict is None:
        _mcdonald_dict = load_mcdonald_dictionary()
    
    return _mcdonald_dict.get(word, None)

def refresh_cache():
    """
    캐시를 강제로 갱신하는 함수
    """
    global _mcdonald_dict
    _mcdonald_dict = None
    return export_mcdonald_dict_to_json()

def get_cache_info():
    """
    캐시 정보를 반환하는 함수
    """
    try:
        if os.path.exists(CACHE_METADATA_FILE):
            with open(CACHE_METADATA_FILE, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            file_size = os.path.getsize(MCDONALD_CACHE_FILE) / (1024 * 1024)  # MB
            metadata['file_size_mb'] = round(file_size, 2)
            metadata['is_valid'] = is_cache_valid()
            
            return metadata
        else:
            return {"error": "캐시 메타데이터 파일이 존재하지 않습니다."}
    except Exception as e:
        return {"error": f"캐시 정보 조회 실패: {e}"}
