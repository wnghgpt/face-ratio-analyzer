"""
얼굴 비율 계산 로직
ratioAnalysis.js의 계산 로직을 Python으로 포팅
"""
import math
import json
from pathlib import Path


class RatioCalculator:
    """랜드마크 기반 얼굴 비율 계산"""

    def __init__(self, ratio_definitions_path=None):
        """
        Args:
            ratio_definitions_path: ratio_definitions.json 파일 경로
        """
        if ratio_definitions_path is None:
            # 기본 경로: source_data/ratio_definitions.json
            base_dir = Path(__file__).parent.parent
            ratio_definitions_path = base_dir / "source_data" / "ratio_definitions.json"

        with open(ratio_definitions_path, 'r', encoding='utf-8') as f:
            self.definitions = json.load(f)

    @staticmethod
    def calculate_distance(p1, p2):
        """유클리드 거리 계산"""
        dx = p1['x'] - p2['x']
        dy = p1['y'] - p2['y']
        return math.sqrt(dx * dx + dy * dy)

    def calculate_all_ratios(self, landmarks, options=None):
        """
        모든 비율 계산

        Args:
            landmarks: list of dict [{mp_idx, x, y, z}, ...]
            options: dict {hairline_point, double_eyelid, image_width, image_height}

        Returns:
            list of dict [{part, ratio_type, side, calculated_value}, ...]
        """
        if options is None:
            options = {}

        # landmarks를 딕셔너리로 변환 (빠른 조회)
        landmark_dict = {lm['mp_idx']: lm for lm in landmarks}

        results = []

        # 각 부위별로 계산
        for part, part_definitions in self.definitions.items():
            for name, definition in part_definitions.items():
                # side 추출
                side = definition.get('side', 'center')
                if '(좌)' in name:
                    side = 'left'
                elif '(우)' in name:
                    side = 'right'

                # 계산
                value = self.calculate_ratio(landmark_dict, definition, options)

                if value is not None:
                    results.append({
                        'part': part,
                        'ratio_type': definition['type'],
                        'side': side,
                        'calculated_value': value
                    })

        return results

    def calculate_ratio(self, landmark_dict, definition, options):
        """
        단일 비율 계산

        Args:
            landmark_dict: dict {mp_idx: {x, y, z}}
            definition: 계산 정의 (JSON의 한 항목)
            options: {hairline_point, double_eyelid}
        """
        ratio_type = definition['type']

        # type별 계산 함수 호출
        if ratio_type == "pupil_white_ratio":
            return self._calc_pupil_white_ratio(landmark_dict, definition)

        elif ratio_type == "canthal_tilt":
            return self._calc_canthal_tilt(landmark_dict, definition)

        elif ratio_type == "ratio_axis":
            return self._calc_ratio_axis(landmark_dict, definition)

        elif ratio_type == "vertical_gap_normalized":
            return self._calc_vertical_gap_normalized(landmark_dict, definition)

        elif ratio_type == "double_eyelid_height":
            return self._calc_double_eyelid_height(landmark_dict, definition)

        elif ratio_type == "eye_width_segments":
            return self._calc_eye_width_segments(landmark_dict, definition)

        elif ratio_type == "nose_width_ratio":
            return self._calc_nose_width_ratio(landmark_dict, definition)

        elif ratio_type == "nose_length":
            return self._calc_nose_length(landmark_dict, definition)

        elif ratio_type == "nose_tip_width":
            return self._calc_nose_tip_width(landmark_dict, definition)

        elif ratio_type == "nose_height":
            return self._calc_nose_height(landmark_dict, definition)

        elif ratio_type == "lip_ratio":
            return self._calc_lip_ratio(landmark_dict, definition)

        elif ratio_type == "lower_face_ratio":
            return self._calc_lower_face_ratio(landmark_dict, definition)

        elif ratio_type == "eyebrow_detail":
            return self._calc_eyebrow_detail(landmark_dict, definition)

        elif ratio_type == "conditional_ratio_axis":
            return self._calc_conditional_ratio_axis(landmark_dict, definition, options)

        elif ratio_type == "face_length_ratio":
            return self._calc_face_length_ratio(landmark_dict, definition, options)

        elif ratio_type == "ratio":
            return self._calc_ratio(landmark_dict, definition, options)

        return None

    # ========== 개별 계산 함수들 ==========

    def _calc_pupil_white_ratio(self, landmark_dict, definition):
        """동공흰자비율 계산 (ratioAnalysis.js 218-242)"""
        points = definition['points']

        p1 = landmark_dict.get(points[0])
        p2 = landmark_dict.get(points[1])
        p3 = landmark_dict.get(points[2])
        p4 = landmark_dict.get(points[3])

        if not all([p1, p2, p3, p4]):
            return None

        # x좌표 거리 계산
        seg1 = abs(p2['x'] - p1['x'])  # 첫 번째 흰자
        seg2 = abs(p3['x'] - p2['x'])  # 동공
        seg3 = abs(p4['x'] - p3['x'])  # 두 번째 흰자

        if seg2 == 0:
            return None

        # 동공(seg2)을 1로 기준
        ratio1 = round(seg1 / seg2, 2)
        ratio3 = round(seg3 / seg2, 2)

        return f"{ratio1}:1:{ratio3}"

    def _calc_canthal_tilt(self, landmark_dict, definition):
        """Canthal tilt 각도 계산 (ratioAnalysis.js 244-257)"""
        points = definition['points']

        p1 = landmark_dict.get(points[0])
        p2 = landmark_dict.get(points[1])

        if not all([p1, p2]):
            return None

        dy = p2['y'] - p1['y']
        dx = p2['x'] - p1['x']

        if dx == 0:
            return None

        angle = math.degrees(math.atan(dy / dx))
        return f"{round(angle, 2)}°"

    def _calc_ratio_axis(self, landmark_dict, definition):
        """축 분리 비율 계산 (ratioAnalysis.js 317-329)"""
        num_points = definition['numerator']
        den_points = definition['denominator']
        num_axis = definition['numeratorAxis']
        den_axis = definition['denominatorAxis']

        p1 = landmark_dict.get(num_points[0])
        p2 = landmark_dict.get(num_points[1])
        p3 = landmark_dict.get(den_points[0])
        p4 = landmark_dict.get(den_points[1])

        if not all([p1, p2, p3, p4]):
            return None

        num = abs(p2['y'] - p1['y']) if num_axis == 'y' else abs(p2['x'] - p1['x'])
        den = abs(p4['y'] - p3['y']) if den_axis == 'y' else abs(p4['x'] - p3['x'])

        if den == 0:
            return None

        return str(round(num / den, 3))

    def _calc_vertical_gap_normalized(self, landmark_dict, definition):
        """정규화된 수직 간격 계산 (ratioAnalysis.js 259-277)"""
        points = definition['points']

        p1 = landmark_dict.get(points[0])
        p2 = landmark_dict.get(points[1])

        if not all([p1, p2]):
            return None

        # y 좌표 차이를 정규화 (0~1 범위에서)
        gap = abs(p2['y'] - p1['y'])

        return str(round(gap, 3))

    def _calc_double_eyelid_height(self, landmark_dict, definition):
        """쌍꺼풀 높이 3구간 비율 (ratioAnalysis.js 331-351)"""
        points = definition['points']

        p1 = landmark_dict.get(points[0])  # 눈썹
        p2 = landmark_dict.get(points[1])  # 쌍꺼풀선
        p3 = landmark_dict.get(points[2])  # 눈 위
        p4 = landmark_dict.get(points[3])  # 눈 아래

        if not all([p1, p2, p3, p4]):
            return None

        # y 좌표 차이
        seg1 = abs(p2['y'] - p1['y'])  # 눈썹-쌍꺼풀
        seg2 = abs(p3['y'] - p2['y'])  # 쌍꺼풀-눈위
        seg3 = abs(p4['y'] - p3['y'])  # 눈위-눈아래

        if seg2 == 0:
            return None

        ratio1 = round(seg1 / seg2, 2)
        ratio3 = round(seg3 / seg2, 2)

        return f"{ratio1}:1:{ratio3}"

    def _calc_eye_width_segments(self, landmark_dict, definition):
        """눈너비:미간 5구간 비율 (ratioAnalysis.js 353-384)"""
        points = definition['points']

        landmarks = [landmark_dict.get(p) for p in points]
        if not all(landmarks):
            return None

        # 5개 구간 계산
        segments = []
        for i in range(len(landmarks) - 1):
            seg = abs(landmarks[i+1]['x'] - landmarks[i]['x'])
            segments.append(seg)

        total = sum(segments)
        if total == 0:
            return None

        # 정규화 (합=1)
        normalized = [round(s / total, 2) for s in segments]

        return ':'.join(map(str, normalized))

    def _calc_nose_width_ratio(self, landmark_dict, definition):
        """코 너비 비율 (ratioAnalysis.js 386-402)"""
        midbrow = definition['midbrow_points']
        nose = definition['nose_points']

        p1 = landmark_dict.get(midbrow[0])
        p2 = landmark_dict.get(midbrow[1])
        p3 = landmark_dict.get(nose[0])
        p4 = landmark_dict.get(nose[1])

        if not all([p1, p2, p3, p4]):
            return None

        midbrow_width = abs(p2['x'] - p1['x'])
        nose_width = abs(p4['x'] - p3['x'])

        if midbrow_width == 0:
            return None

        ratio = round(nose_width / midbrow_width, 2)
        return f"1:{ratio}"

    def _calc_nose_length(self, landmark_dict, definition):
        """코 길이 3구간 비율 (ratioAnalysis.js 404-431)"""
        points = definition['points']

        p1 = landmark_dict.get(points[0])
        p2 = landmark_dict.get(points[1])
        p3 = landmark_dict.get(points[2])
        p4 = landmark_dict.get(points[3])
        p5 = landmark_dict.get(points[4])

        if not all([p1, p2, p3, p4, p5]):
            return None

        # 3개 구간 y 좌표 차이
        seg1 = abs(p2['y'] - p1['y'])
        seg2 = abs(p3['y'] - p2['y'])
        seg3 = abs(p5['y'] - p4['y'])

        if seg2 == 0:
            return None

        ratio1 = round(seg1 / seg2, 2)
        ratio3 = round(seg3 / seg2, 2)

        return f"{ratio1}:1:{ratio3}"

    def _calc_nose_tip_width(self, landmark_dict, definition):
        """코끝 폭 비율 (ratioAnalysis.js 433-449)"""
        upper = definition['upper_points']
        lower = definition['lower_points']

        p1 = landmark_dict.get(upper[0])
        p2 = landmark_dict.get(upper[1])
        p3 = landmark_dict.get(lower[0])
        p4 = landmark_dict.get(lower[1])

        if not all([p1, p2, p3, p4]):
            return None

        upper_width = abs(p2['x'] - p1['x'])
        lower_width = abs(p4['x'] - p3['x'])

        if upper_width == 0:
            return None

        ratio = round(lower_width / upper_width, 2)
        return f"1:{ratio}"

    def _calc_nose_height(self, landmark_dict, definition):
        """코 높이 비율 (ratioAnalysis.js 451-469)"""
        points = definition['points']

        p1 = landmark_dict.get(points[0])
        p2 = landmark_dict.get(points[1])
        p3 = landmark_dict.get(points[2])
        p4 = landmark_dict.get(points[3])

        if not all([p1, p2, p3, p4]):
            return None

        # p2, p3의 평균점
        mid_y = (p2['y'] + p3['y']) / 2

        seg1 = abs(mid_y - p1['y'])
        seg2 = abs(p4['y'] - mid_y)

        if seg1 == 0:
            return None

        ratio = round(seg2 / seg1, 2)
        return f"1:{ratio}"

    def _calc_lip_ratio(self, landmark_dict, definition):
        """입술 두께 비율 (ratioAnalysis.js 471-490)"""
        points = definition['points']

        p1 = landmark_dict.get(points[0])
        p2 = landmark_dict.get(points[1])
        p3 = landmark_dict.get(points[2])
        p4 = landmark_dict.get(points[3])
        p5 = landmark_dict.get(points[4])

        if not all([p1, p2, p3, p4, p5]):
            return None

        # p1, p2의 평균점
        avg_y = (p1['y'] + p2['y']) / 2

        seg1 = abs(p3['y'] - avg_y)
        seg2 = abs(p5['y'] - p4['y'])

        if seg1 == 0:
            return None

        ratio = round(seg2 / seg1, 2)
        return f"1:{ratio}"

    def _calc_lower_face_ratio(self, landmark_dict, definition):
        """하안면 비율 (ratioAnalysis.js 492-508)"""
        points = definition['points']

        p1 = landmark_dict.get(points[0])
        p2 = landmark_dict.get(points[1])
        p3 = landmark_dict.get(points[2])
        p4 = landmark_dict.get(points[3])

        if not all([p1, p2, p3, p4]):
            return None

        seg1 = abs(p2['y'] - p1['y'])
        seg2 = abs(p4['y'] - p3['y'])

        if seg1 == 0:
            return None

        ratio = round(seg2 / seg1, 2)
        return f"1:{ratio}"

    def _calc_eyebrow_detail(self, landmark_dict, definition):
        """눈썹 상세 (높이/Peak 위치) (ratioAnalysis.js 138-216)"""
        left_points = definition['left_points']
        right_points = definition['right_points']

        # 좌우 각각 계산
        left_result = self._calc_single_eyebrow(landmark_dict, left_points)
        right_result = self._calc_single_eyebrow(landmark_dict, right_points)

        # 좌우가 모두 있으면 반환
        if left_result and right_result:
            return {'left': left_result, 'right': right_result}

        return None

    def _calc_single_eyebrow(self, landmark_dict, points_def):
        """단일 눈썹 계산"""
        base = landmark_dict.get(points_def['base'])
        end = landmark_dict.get(points_def['end'])
        peak = landmark_dict.get(points_def['peak'])

        if not all([base, end, peak]):
            return None

        # 너비
        width = abs(end['x'] - base['x'])

        # 높이
        base_end_y = (base['y'] + end['y']) / 2
        height = abs(peak['y'] - base_end_y)

        # Peak x 위치
        peak_x_pos = abs(peak['x'] - base['x'])

        if width == 0:
            return None

        height_ratio = round(height / width, 3)
        peak_ratio = round(peak_x_pos / width, 3)

        return f"{height_ratio}|{peak_ratio}"  # 높이|Peak 위치

    def _calc_conditional_ratio_axis(self, landmark_dict, definition, options):
        """조건부 비율 계산 (ratioAnalysis.js 279-300)"""
        # 쌍꺼풀 유무에 따라 다른 포인트 사용
        has_double = options.get('double_eyelid', False)

        if has_double:
            points_to_use = definition['with_double']
        else:
            points_to_use = definition['without_double']

        up = points_to_use['up']
        down = points_to_use['down']
        axis = definition['axis']

        p1 = landmark_dict.get(up[0])
        p2 = landmark_dict.get(up[1])
        p3 = landmark_dict.get(down[0])
        p4 = landmark_dict.get(down[1])

        if not all([p1, p2, p3, p4]):
            return None

        seg_up = abs(p2['y'] - p1['y']) if axis == 'y' else abs(p2['x'] - p1['x'])
        seg_down = abs(p4['y'] - p3['y']) if axis == 'y' else abs(p4['x'] - p3['x'])

        if seg_up == 0:
            return None

        ratio = round(seg_down / seg_up, 2)
        return f"1:{ratio}"

    def _calc_face_length_ratio(self, landmark_dict, definition, options):
        """얼굴 길이 비율 (ratioAnalysis.js 90-135)"""
        hairline = options.get('hairline_point')
        if not hairline:
            return None

        p1 = landmark_dict.get(definition['points']['eyebrow_lower'])
        p2 = landmark_dict.get(definition['points']['nose_tip'])
        p3 = landmark_dict.get(definition['points']['chin'])

        if not all([p1, p2, p3]):
            return None

        seg1 = abs(p1['y'] - hairline['y'])
        seg2 = abs(p2['y'] - p1['y'])
        seg3 = abs(p3['y'] - p2['y'])

        if seg1 == 0:
            return None

        ratio2 = round(seg2 / seg1, 2)
        ratio3 = round(seg3 / seg1, 2)

        return f"1:{ratio2}:{ratio3}"

    def _calc_ratio(self, landmark_dict, definition, options):
        """일반 비율 계산 (ratioAnalysis.js 302-315)"""
        num = definition['numerator']
        den = definition['denominator']

        p1 = landmark_dict.get(num[0])
        p2 = landmark_dict.get(num[1])
        p3 = landmark_dict.get(den[0])
        p4 = landmark_dict.get(den[1])

        if not all([p1, p2, p3, p4]):
            return None

        num_dist = self.calculate_distance(p1, p2)
        den_dist = self.calculate_distance(p3, p4)

        if den_dist == 0:
            return None

        ratio = round(num_dist / den_dist, 3)
        return str(ratio)
