-- 랜드마크 테이블 성능 최적화를 위한 인덱스 추가

-- 복합 인덱스 생성 (face_data_id, mp_idx)
CREATE INDEX idx_face_mp ON landmarks(face_data_id, mp_idx);

-- 인덱스 생성 확인
SHOW INDEX FROM landmarks;

-- 성능 테스트 쿼리
EXPLAIN SELECT x, y FROM landmarks WHERE face_data_id = 1 AND mp_idx = 33;