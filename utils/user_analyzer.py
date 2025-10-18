"""
User 특징 태그 분석 서비스
- User의 2nd tag 측정값과 Pool 데이터 비교
- Percentile 기반 특징 태그 추출
- Tag relation 기반 상위 태그 역추적
"""
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from face_db_core.schema_def import (
    User2ndTagValue, Pool2ndTagValue, PoolTagRelation
)
import numpy as np


class UserAnalyzer:
    """User 특징 분석 및 태그 추출"""

    def __init__(self, db_session: Session):
        self.session = db_session
        self._tag_relations = None

    def analyze_user_features(
        self,
        user_id: int,
        top10_threshold: float = 0.90,  # 상위 10% = 90 percentile
        top25_threshold: float = 0.75   # 상위 25% = 75 percentile
    ) -> Dict:
        """
        User의 특징 태그 분석 및 추출

        Args:
            user_id: 사용자 ID
            top10_threshold: 상위 10% 기준 (0.90 = 90 percentile)
            top25_threshold: 상위 25% 기준 (0.75 = 75 percentile)

        Returns:
            {
                "extracted_2nd_tags": [...],
                "derived_1st_tags": [...],
                "derived_0th_tags": [...]
            }
        """
        # 1. User의 2nd tag 측정값 조회
        user_values = self._get_user_2nd_tag_values(user_id)
        if not user_values:
            return {
                "extracted_2nd_tags": [],
                "derived_1st_tags": [],
                "derived_0th_tags": []
            }

        # 2. 특징적인 2nd 태그 추출
        extracted_2nd_tags = self._extract_feature_2nd_tags(
            user_values,
            top10_threshold,
            top25_threshold
        )

        # 3. 2nd tag → 1st tag 역추적
        derived_1st_tags = self._derive_parent_tags(
            extracted_2nd_tags,
            parent_level=1
        )

        # 4. 1st tag → 0th tag 역추적
        derived_0th_tags = self._derive_parent_tags(
            derived_1st_tags,
            parent_level=0
        )

        return {
            "extracted_2nd_tags": extracted_2nd_tags,
            "derived_1st_tags": derived_1st_tags,
            "derived_0th_tags": derived_0th_tags
        }

    def _get_user_2nd_tag_values(self, user_id: int) -> List[Dict]:
        """
        User의 2nd tag 측정값 조회

        Returns:
            [{"tag_name": "eye-길이", "side": "left", "측정값": 0.123}, ...]
        """
        values = self.session.query(User2ndTagValue).filter(
            User2ndTagValue.user_id == user_id
        ).all()

        return [v.to_dict() for v in values]

    def _extract_feature_2nd_tags(
        self,
        user_values: List[Dict],
        top10_threshold: float,
        top25_threshold: float
    ) -> List[Dict]:
        """
        케이스1 + 케이스2 OR 조건으로 특징 2nd 태그 추출

        케이스1: 상위 10% 태그
        케이스2: 상위 25% 태그 중 tag_relation 조합을 만드는 태그들

        Returns:
            [{"tag_name": "eye-길이", "side": "left", "측정값": 0.123, "percentile": 0.95}, ...]
        """
        extracted = []

        for user_val in user_values:
            tag_name = user_val["tag_name"]
            side = user_val["side"]
            user_measurement = user_val["측정값"]

            if user_measurement is None:
                continue

            # Pool에서 동일한 tag_name + side의 측정값들 조회
            percentile = self._calculate_percentile(tag_name, side, user_measurement)

            if percentile is None:
                continue

            user_val["percentile"] = percentile

            # 케이스1: 상위 10%
            if percentile >= top10_threshold:
                extracted.append(user_val)

        # 케이스2: 상위 25% 중 tag_relation 조합
        top25_tags = [
            uv for uv in user_values
            if uv.get("percentile") and uv["percentile"] >= top25_threshold
        ]

        # tag_relation에서 이 top25 태그들이 조합을 만드는지 확인
        relation_based_tags = self._find_tags_forming_relations(top25_tags)

        # 중복 제거하며 합치기
        extracted_tag_keys = {(t["tag_name"], t["side"]) for t in extracted}
        for tag in relation_based_tags:
            key = (tag["tag_name"], tag["side"])
            if key not in extracted_tag_keys:
                extracted.append(tag)

        return extracted

    def _calculate_percentile(
        self,
        tag_name: str,
        side: str,
        user_value: float
    ) -> Optional[float]:
        """
        Pool 데이터와 비교하여 User 측정값의 percentile 계산

        Args:
            tag_name: 태그 이름
            side: 측정 위치
            user_value: User의 측정값

        Returns:
            percentile (0.0 ~ 1.0) 또는 None
        """
        # Pool에서 동일한 tag + side의 모든 측정값 조회
        pool_values = self.session.query(Pool2ndTagValue.측정값).filter(
            Pool2ndTagValue.tag_name == tag_name,
            Pool2ndTagValue.side == side,
            Pool2ndTagValue.측정값.isnot(None)
        ).all()

        if not pool_values:
            return None

        pool_measurements = [v[0] for v in pool_values]

        # Numpy percentile 계산
        percentile = np.sum(np.array(pool_measurements) <= user_value) / len(pool_measurements)

        return float(percentile)

    def _find_tags_forming_relations(self, top25_tags: List[Dict]) -> List[Dict]:
        """
        상위 25% 태그들 중 tag_relation에서 특정 1차 태그를 조합하는 태그들 찾기

        Args:
            top25_tags: 상위 25% 태그들

        Returns:
            relation을 만드는 태그들
        """
        if not top25_tags:
            return []

        relations = self._load_tag_relations()
        if not relations:
            return []

        forming_tags = []

        # tag_name만 추출 (side 제외)
        top25_tag_names = set(t["tag_name"] for t in top25_tags)

        # 각 relation을 체크
        for relation in relations:
            parent_level = relation.get("parent_level")
            child_tags = relation.get("child_tags", [])

            # parent_level이 1이고 (1차 태그를 만드는 경우)
            # child_tags가 모두 top25_tag_names에 포함되는 경우
            if parent_level == 1 and child_tags:
                if all(tag in top25_tag_names for tag in child_tags):
                    # 이 child_tags들을 forming_tags에 추가
                    for tag in child_tags:
                        matching_tags = [t for t in top25_tags if t["tag_name"] == tag]
                        forming_tags.extend(matching_tags)

        # 중복 제거
        unique_tags = []
        seen = set()
        for tag in forming_tags:
            key = (tag["tag_name"], tag["side"])
            if key not in seen:
                seen.add(key)
                unique_tags.append(tag)

        return unique_tags

    def _derive_parent_tags(
        self,
        child_tags: List[Dict],
        parent_level: int
    ) -> List[str]:
        """
        Child 태그들로부터 parent 태그 역추적

        Args:
            child_tags: child 태그들 (2nd or 1st tags)
            parent_level: 도출하려는 parent의 level (0 or 1)

        Returns:
            parent 태그 이름 리스트
        """
        if not child_tags:
            return []

        relations = self._load_tag_relations()
        if not relations:
            return []

        # child tag names만 추출
        child_tag_names = set(t["tag_name"] if isinstance(t, dict) else t for t in child_tags)

        parent_tags = set()

        # 각 relation을 체크
        for relation in relations:
            rel_parent_level = relation.get("parent_level")
            rel_parent_tags = relation.get("parent_tags", [])
            rel_child_tags = relation.get("child_tags", [])

            # parent_level이 일치하고
            # child_tags가 모두 우리가 가진 child_tag_names에 포함되는 경우
            if rel_parent_level == parent_level and rel_child_tags:
                if all(tag in child_tag_names for tag in rel_child_tags):
                    parent_tags.update(rel_parent_tags)

        return list(parent_tags)

    def _load_tag_relations(self) -> List[Dict]:
        """
        Tag relation 로드 (캐싱)

        Returns:
            [{"parent_tags": [...], "child_tags": [...], "parent_level": 1}, ...]
        """
        if self._tag_relations is not None:
            return self._tag_relations

        # DB에서 로드
        relations = self.session.query(PoolTagRelation).all()
        self._tag_relations = [r.to_dict() for r in relations]

        return self._tag_relations
