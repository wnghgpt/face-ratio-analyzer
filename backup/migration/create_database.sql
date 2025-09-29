-- Face Analytics MariaDB 데이터베이스 설정
-- 실행 방법: sudo mysql < create_database.sql

-- 1. 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS face_analytics
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 2. 사용자 생성 및 권한 부여
CREATE USER IF NOT EXISTS 'face_user'@'localhost' IDENTIFIED BY 'face_password';
GRANT ALL PRIVILEGES ON face_analytics.* TO 'face_user'@'localhost';

-- 3. 설정 적용
FLUSH PRIVILEGES;

-- 4. 데이터베이스 선택
USE face_analytics;

-- 5. 연결 테스트용 테이블 (나중에 SQLAlchemy가 실제 테이블 생성)
CREATE TABLE IF NOT EXISTS connection_test (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message VARCHAR(255) DEFAULT 'MariaDB connection successful'
);

INSERT INTO connection_test (message) VALUES ('Database setup completed');

-- 현재 상태 출력
SELECT 'Database setup completed successfully!' as status;
SELECT * FROM connection_test;