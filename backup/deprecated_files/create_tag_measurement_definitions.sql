-- 태그 측정 정의 테이블 생성
CREATE TABLE tag_measurement_definitions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tag_name VARCHAR(100) UNIQUE NOT NULL,
    measurement_type VARCHAR(20) NOT NULL,
    description TEXT,
    point1_mpidx INT,
    point2_mpidx INT,
    denominator_point1 INT,
    denominator_point2 INT,
    numerator_point1 INT,
    numerator_point2 INT,
    curvature_points JSON
);

-- 샘플 데이터 삽입
INSERT INTO tag_measurement_definitions (tag_name, measurement_type, description, point1_mpidx, point2_mpidx) VALUES
('mouth-너비', '길이', '입술의 좌우 끝점 간 거리', 61, 291),
('eye-크기', '길이', '눈의 좌우 끝점 간 거리', 33, 133);

INSERT INTO tag_measurement_definitions (tag_name, measurement_type, description, denominator_point1, denominator_point2, numerator_point1, numerator_point2) VALUES
('face-width-ratio', '비율', '얼굴 너비 대비 입 너비 비율', 234, 454, 61, 291);

INSERT INTO tag_measurement_definitions (tag_name, measurement_type, description, curvature_points) VALUES
('eyebrow-곡률', '곡률', '눈썹의 굽힘 정도', JSON_ARRAY(70, 107, 55, 8, 9));