"""
계산된 비율을 DB에 저장하는 유틸리티
"""
from database.schema_def import PoolBasicRatio, PoolLandmark, PoolProfile
from database.ratio_calculator import RatioCalculator


def calculate_and_save_ratios(session, profile_id, options=None):
    """
    프로필의 모든 비율을 계산하고 PoolBasicRatio에 저장

    Args:
        session: SQLAlchemy session
        profile_id: 프로필 ID
        options: dict {hairline_point, double_eyelid, image_width, image_height}

    Returns:
        int: 저장된 비율 개수
    """
    if options is None:
        options = {}

    # 1. landmarks 가져오기
    landmarks = session.query(PoolLandmark).filter_by(profile_id=profile_id).all()

    if not landmarks:
        print(f"No landmarks found for profile_id={profile_id}")
        return 0

    # landmarks를 딕셔너리 리스트로 변환
    landmarks_list = [
        {
            'mp_idx': lm.mp_idx,
            'x': float(lm.x),
            'y': float(lm.y),
            'z': float(lm.z) if lm.z else 0.0
        }
        for lm in landmarks
    ]

    # 2. 비율 계산
    calculator = RatioCalculator()
    ratio_results = calculator.calculate_all_ratios(landmarks_list, options)

    # 3. 기존 비율 데이터 삭제 (재계산 시)
    session.query(PoolBasicRatio).filter_by(profile_id=profile_id).delete()

    # 4. 새로운 비율 데이터 저장 + JSONB 병행 저장
    saved_count = 0
    ratios_json = []
    for result in ratio_results:
        # eyebrow_detail처럼 좌우 값을 별도로 반환하는 경우 처리
        if isinstance(result['calculated_value'], dict):
            # {'left': value, 'right': value} 형태
            for side, value in result['calculated_value'].items():
                ratio_record = PoolBasicRatio(
                    profile_id=profile_id,
                    part=result['part'],
                    ratio_type=result['ratio_type'],
                    side=side,
                    calculated_value=value
                )
                session.add(ratio_record)
                saved_count += 1

                ratios_json.append({
                    'part': result['part'],
                    'ratio_type': result['ratio_type'],
                    'side': side,
                    'calculated_value': value
                })
        else:
            # 일반적인 경우
            ratio_record = PoolBasicRatio(
                profile_id=profile_id,
                part=result['part'],
                ratio_type=result['ratio_type'],
                side=result['side'],
                calculated_value=result['calculated_value']
            )
            session.add(ratio_record)
            saved_count += 1

            ratios_json.append({
                'part': result['part'],
                'ratio_type': result['ratio_type'],
                'side': result['side'],
                'calculated_value': result['calculated_value']
            })

    session.commit()

    # PoolProfile.ratios_json에 병행 저장
    profile = session.query(PoolProfile).filter_by(id=profile_id).first()
    if profile is not None:
        profile.ratios_json = ratios_json
        session.commit()

    print(f"Saved {saved_count} ratio records for profile_id={profile_id}")
    return saved_count


def get_ratios_by_profile(session, profile_id):
    """
    프로필의 모든 비율 조회

    Args:
        session: SQLAlchemy session
        profile_id: 프로필 ID

    Returns:
        list of dict: [{part, ratio_type, side, calculated_value}, ...]
    """
    ratios = session.query(PoolBasicRatio).filter_by(profile_id=profile_id).all()

    return [
        {
            'id': r.id,
            'part': r.part,
            'ratio_type': r.ratio_type,
            'side': r.side,
            'calculated_value': r.calculated_value
        }
        for r in ratios
    ]


def get_ratio_by_type(session, profile_id, ratio_type, side='center'):
    """
    특정 타입의 비율 조회

    Args:
        session: SQLAlchemy session
        profile_id: 프로필 ID
        ratio_type: 비율 타입 (예: 'pupil_white_ratio')
        side: 좌우 구분 (left, right, center)

    Returns:
        dict or None: {part, ratio_type, side, calculated_value}
    """
    ratio = session.query(PoolBasicRatio).filter_by(
        profile_id=profile_id,
        ratio_type=ratio_type,
        side=side
    ).first()

    if ratio:
        return {
            'id': ratio.id,
            'part': ratio.part,
            'ratio_type': ratio.ratio_type,
            'side': ratio.side,
            'calculated_value': ratio.calculated_value
        }

    return None
