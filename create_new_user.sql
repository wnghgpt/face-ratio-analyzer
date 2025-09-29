-- 새 사용자 및 데이터베이스 생성 스크립트

-- 1. 새 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS face_analysis
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 2. 새 사용자 생성 및 권한 부여
CREATE USER IF NOT EXISTS 'wnghgpt'@'localhost' IDENTIFIED BY 'dnlsehdn';
GRANT ALL PRIVILEGES ON face_analysis.* TO 'wnghgpt'@'localhost';

-- 3. 설정 적용
FLUSH PRIVILEGES;

-- 4. 데이터베이스 선택 및 테스트
USE face_analysis;

-- 5. 연결 테스트용 테이블
CREATE TABLE IF NOT EXISTS connection_test (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message VARCHAR(255) DEFAULT 'New user setup successful'
);

INSERT INTO connection_test (message) VALUES ('wnghgpt user created successfully');

-- 현재 상태 출력
SELECT 'New user and database setup completed!' as status;
SELECT * FROM connection_test;