"""
랜드마크 좌표 기반 계산 유틸리티
"""
import numpy as np


def calculate_landmarks_metric(landmarks, points, calc_type):
    """랜드마크 기반 메트릭 계산"""
    try:
        # landmarks에서 선택된 점들 추출
        selected_landmarks = []
        for point_id in points:
            landmark = next((lm for lm in landmarks if lm['mpidx'] == point_id), None)
            if landmark:
                selected_landmarks.append(landmark)

        if len(selected_landmarks) != len(points):
            return None

        # 계산 실행 - 새로운 목적 기반 구조

        # 📍 단일 점 분석
        if calc_type == "X 좌표":
            return selected_landmarks[0]['x']
        elif calc_type == "Y 좌표":
            return selected_landmarks[0]['y']
        elif calc_type == "Z 좌표":
            return selected_landmarks[0]['z']
        elif calc_type == "원점에서의 거리":
            p = selected_landmarks[0]
            return np.sqrt(p['x']**2 + p['y']**2 + p['z']**2)

        # 📏 거리 측정
        elif calc_type == "유클리드 거리":
            p1, p2 = selected_landmarks[0], selected_landmarks[1]
            return np.sqrt((p1['x']-p2['x'])**2 + (p1['y']-p2['y'])**2 + (p1['z']-p2['z'])**2)
        elif calc_type == "맨하탄 거리":
            p1, p2 = selected_landmarks[0], selected_landmarks[1]
            return abs(p1['x']-p2['x']) + abs(p1['y']-p2['y']) + abs(p1['z']-p2['z'])
        elif calc_type == "X축 거리":
            p1, p2 = selected_landmarks[0], selected_landmarks[1]
            return abs(p1['x'] - p2['x'])
        elif calc_type == "Y축 거리":
            p1, p2 = selected_landmarks[0], selected_landmarks[1]
            return abs(p1['y'] - p2['y'])
        elif calc_type == "Z축 거리":
            p1, p2 = selected_landmarks[0], selected_landmarks[1]
            return abs(p1['z'] - p2['z'])

        # ⚖️ 비율 계산 (4개 점: A-B 거리 vs C-D 거리)
        elif calc_type == "거리 비율 (A-B : C-D)":
            if len(selected_landmarks) >= 4:
                p1, p2, p3, p4 = selected_landmarks[:4]
                dist1 = np.sqrt((p1['x']-p2['x'])**2 + (p1['y']-p2['y'])**2 + (p1['z']-p2['z'])**2)
                dist2 = np.sqrt((p3['x']-p4['x'])**2 + (p3['y']-p4['y'])**2 + (p3['z']-p4['z'])**2)
                return dist1 / dist2 if dist2 != 0 else 0
        elif calc_type == "X축 비율":
            if len(selected_landmarks) >= 4:
                p1, p2, p3, p4 = selected_landmarks[:4]
                dist1 = abs(p1['x'] - p2['x'])
                dist2 = abs(p3['x'] - p4['x'])
                return dist1 / dist2 if dist2 != 0 else 0
        elif calc_type == "Y축 비율":
            if len(selected_landmarks) >= 4:
                p1, p2, p3, p4 = selected_landmarks[:4]
                dist1 = abs(p1['y'] - p2['y'])
                dist2 = abs(p3['y'] - p4['y'])
                return dist1 / dist2 if dist2 != 0 else 0
        elif calc_type == "Z축 비율":
            if len(selected_landmarks) >= 4:
                p1, p2, p3, p4 = selected_landmarks[:4]
                dist1 = abs(p1['z'] - p2['z'])
                dist2 = abs(p3['z'] - p4['z'])
                return dist1 / dist2 if dist2 != 0 else 0

        # 📐 각도 측정
        elif calc_type == "벡터 각도":
            if len(selected_landmarks) >= 3:
                p1, p2, p3 = selected_landmarks[:3]
                # p2를 중심으로 p1과 p3 사이의 각도
                v1 = np.array([p1['x']-p2['x'], p1['y']-p2['y'], p1['z']-p2['z']])
                v2 = np.array([p3['x']-p2['x'], p3['y']-p2['y'], p3['z']-p2['z']])
                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                cos_angle = np.clip(cos_angle, -1, 1)  # 부동소수점 오차 방지
                return np.degrees(np.arccos(cos_angle))
        elif calc_type == "평면 각도":
            if len(selected_landmarks) >= 3:
                p1, p2, p3 = selected_landmarks[:3]
                # XY 평면에서의 각도만 계산
                v1 = np.array([p1['x']-p2['x'], p1['y']-p2['y']])
                v2 = np.array([p3['x']-p2['x'], p3['y']-p2['y']])
                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                cos_angle = np.clip(cos_angle, -1, 1)
                return np.degrees(np.arccos(cos_angle))
        elif calc_type == "기울기 각도":
            if len(selected_landmarks) >= 3:
                p1, p2, p3 = selected_landmarks[:3]
                # 첫 번째와 마지막 점을 연결한 직선의 기울기
                slope = (p3['y'] - p1['y']) / (p3['x'] - p1['x']) if p3['x'] != p1['x'] else float('inf')
                return np.degrees(np.arctan(slope)) if slope != float('inf') else 90

        # 📊 면적 계산
        elif calc_type == "삼각형 넓이":
            if len(selected_landmarks) >= 3:
                p1, p2, p3 = selected_landmarks[:3]
                # 3D 삼각형 넓이 계산 (외적 사용)
                v1 = np.array([p2['x']-p1['x'], p2['y']-p1['y'], p2['z']-p1['z']])
                v2 = np.array([p3['x']-p1['x'], p3['y']-p1['y'], p3['z']-p1['z']])
                cross = np.cross(v1, v2)
                return 0.5 * np.linalg.norm(cross)
        elif calc_type == "다각형 넓이":
            if len(selected_landmarks) >= 3:
                # 2D 다각형 넓이 (Shoelace formula)
                points = [(p['x'], p['y']) for p in selected_landmarks]
                n = len(points)
                area = 0
                for i in range(n):
                    j = (i + 1) % n
                    area += points[i][0] * points[j][1]
                    area -= points[j][0] * points[i][1]
                return abs(area) / 2

        # ⚖️ 대칭성 분석
        elif calc_type == "좌우 대칭 비율":
            if len(selected_landmarks) >= 4:
                # 첫 두 점 vs 나중 두 점의 거리 비교
                p1, p2, p3, p4 = selected_landmarks[:4]
                left_dist = np.sqrt((p1['x']-p2['x'])**2 + (p1['y']-p2['y'])**2)
                right_dist = np.sqrt((p3['x']-p4['x'])**2 + (p3['y']-p4['y'])**2)
                return left_dist / right_dist if right_dist != 0 else 0
        elif calc_type == "중심축 기준 거리차":
            if len(selected_landmarks) >= 4:
                p1, p2, p3, p4 = selected_landmarks[:4]
                # 중심축을 Y축으로 가정하고 좌우 점들의 중심축으로부터의 거리 차이
                center_x = (p1['x'] + p2['x'] + p3['x'] + p4['x']) / 4
                left_dist = abs(p1['x'] - center_x) + abs(p2['x'] - center_x)
                right_dist = abs(p3['x'] - center_x) + abs(p4['x'] - center_x)
                return abs(left_dist - right_dist)
        elif calc_type == "대칭도 점수":
            if len(selected_landmarks) >= 4:
                # 0에 가까울수록 대칭적
                p1, p2, p3, p4 = selected_landmarks[:4]
                center_x = (p1['x'] + p2['x'] + p3['x'] + p4['x']) / 4
                left_deviation = np.sqrt((p1['x'] - center_x)**2 + (p2['x'] - center_x)**2)
                right_deviation = np.sqrt((p3['x'] - center_x)**2 + (p4['x'] - center_x)**2)
                return abs(left_deviation - right_deviation)

        return None

    except Exception as e:
        return None


def calculate_length(landmarks, point1_id, point2_id, calc_type):
    """두 점 사이의 거리 계산"""
    try:
        # 점 찾기
        p1 = next((lm for lm in landmarks if lm['mpidx'] == point1_id), None)
        p2 = next((lm for lm in landmarks if lm['mpidx'] == point2_id), None)

        if not p1 or not p2:
            return None

        if calc_type == "직선거리":
            return np.sqrt((p1['x']-p2['x'])**2 + (p1['y']-p2['y'])**2 + (p1['z']-p2['z'])**2)
        elif calc_type == "X좌표거리":
            return abs(p1['x'] - p2['x'])
        elif calc_type == "Y좌표거리":
            return abs(p1['y'] - p2['y'])
        else:
            return None

    except Exception as e:
        return None