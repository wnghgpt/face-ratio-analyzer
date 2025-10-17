"""
Face Ratio Analyzer - FastAPI Server
User 분석 및 Pool 데이터 조회 API
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import json

from database.connect_db import db_manager
from database.data_handler import DatabaseCRUD
from utils.user_analyzer import UserAnalyzer
from sqlalchemy.orm import Session


# FastAPI 앱 생성
app = FastAPI(
    title="Face Ratio Analyzer API",
    description="얼굴 비율 분석 및 Pool 데이터 조회 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 specific origins로 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database CRUD 서비스
crud_service = DatabaseCRUD()


# ==================== Dependency ====================

def get_db():
    """Database session dependency"""
    with db_manager.get_session() as session:
        yield session


# ==================== Request/Response Models ====================

class UserAnalysisResponse(BaseModel):
    """User 분석 결과 응답"""
    user_id: int
    extracted_2nd_tags: List[Dict]
    derived_1st_tags: List[str]
    derived_0th_tags: List[str]


class UserUploadRequest(BaseModel):
    """User JSON 업로드 요청"""
    name: str
    login_id: str
    password: str
    email: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Face Ratio Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/api/user/upload": "Upload user JSON with landmarks",
            "/api/user/{user_id}/analyze": "Analyze user features",
            "/api/pool/profiles": "Get all pool profiles",
            "/api/pool/profiles/{profile_id}": "Get pool profile by ID"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    stats = crud_service.get_database_stats()
    return {
        "status": "healthy",
        "database": stats
    }


@app.post("/api/user/upload", response_model=Dict)
async def upload_user_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    User JSON 파일 업로드 및 분석

    - JSON에서 landmarks 추출
    - User profile 및 landmarks 저장
    - 2nd tag 측정값 계산
    - 특징 태그 분석 및 반환
    """
    try:
        # JSON 파일 읽기
        content = await file.read()
        json_data = json.loads(content.decode('utf-8'))

        # TODO: 실제 구현 시 user 정보 받아야 함
        # 지금은 JSON에서 추출하거나 기본값 사용
        name = json_data.get("name", "unknown")
        login_id = json_data.get("login_id", f"user_{name}")
        password = "hashed_password"  # TODO: 해시 처리 필요

        # User 생성 및 landmarks 저장 (기존 data_handler 활용)
        from database.schema_def import UserProfile, UserLandmark
        user = UserProfile(
            name=name,
            login_id=login_id,
            password=password,
            json_file_path=file.filename
        )
        db.add(user)
        db.flush()

        # Landmarks 저장
        landmarks = json_data.get("landmarks", [])
        crud_service.save_landmarks_to_table(db, user.user_id, landmarks, is_user=True)

        # 2nd tag 측정값 계산 (기존 calculate_measurement_value 활용)
        from database.schema_def import Pool2ndTagDef, User2ndTagValue

        tag_defs = db.query(Pool2ndTagDef).all()
        for tag_def in tag_defs:
            try:
                # 3구간비율은 문자열이므로 제외
                if tag_def.measurement_type == "3구간비율":
                    continue

                value = crud_service.calculate_measurement_value(landmarks, tag_def)

                # 문자열 값은 저장 안함 (Float 컬럼이므로)
                if isinstance(value, str):
                    continue

                tag_value = User2ndTagValue(
                    user_id=user.user_id,
                    tag_name=tag_def.tag_name,
                    side=tag_def.side,
                    측정값=value
                )
                db.add(tag_value)
            except Exception as e:
                print(f"Error calculating {tag_def.tag_name}: {e}")
                continue

        db.commit()

        # User 특징 분석
        analyzer = UserAnalyzer(db)
        analysis_result = analyzer.analyze_user_features(user.user_id)

        return {
            "success": True,
            "user_id": user.user_id,
            "name": name,
            "analysis": analysis_result
        }

    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        import traceback
        print(f"Upload Error: {e}")
        print(traceback.format_exc())
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/user/{user_id}/analyze", response_model=UserAnalysisResponse)
async def analyze_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    User 특징 분석

    - User의 2nd tag 측정값 조회
    - Pool과 비교하여 percentile 계산
    - 특징 태그 추출 (상위 10% + 상위 25% relation 조합)
    - 1차, 0차 태그 역추적
    """
    try:
        analyzer = UserAnalyzer(db)
        result = analyzer.analyze_user_features(user_id)

        return {
            "user_id": user_id,
            **result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/pool/profiles")
async def get_pool_profiles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Pool 프로필 목록 조회"""
    try:
        from database.schema_def import PoolProfile
        profiles = db.query(PoolProfile).offset(skip).limit(limit).all()
        return {
            "success": True,
            "count": len(profiles),
            "profiles": [p.to_dict() for p in profiles]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/api/pool/profiles/{profile_id}")
async def get_pool_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    """Pool 프로필 상세 조회"""
    try:
        profile = crud_service.get_face_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return {
            "success": True,
            "profile": profile
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/api/pool/tags/{tag_name}")
async def get_profiles_by_tag(
    tag_name: str,
    db: Session = Depends(get_db)
):
    """특정 태그를 가진 Pool 프로필들 조회"""
    try:
        profiles = crud_service.get_faces_by_tag(tag_name)
        return {
            "success": True,
            "tag_name": tag_name,
            "count": len(profiles),
            "profiles": profiles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
