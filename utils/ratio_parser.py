"""
Ratio Parser - 간단한 비율 파싱 모듈
"""

class RatioParser:
    """비율 문자열을 파싱하는 클래스"""

    def parse_ratio_to_components(self, ratio_string):
        """
        비율 문자열을 개별 컴포넌트로 파싱
        예: "1:1.2:0.8:1.5:0.9" -> {'ratio_1': 1.0, 'ratio_2': 1.2, ...}
        """
        components = {
            'ratio_1': None,
            'ratio_2': None,
            'ratio_3': None,
            'ratio_4': None,
            'ratio_5': None,
            'ratio_2_1': None,
            'ratio_3_1': None,
            'ratio_3_2': None
        }

        if not ratio_string:
            return components

        try:
            # ":"으로 분리
            parts = ratio_string.split(':')

            # 기본 비율들 파싱
            for i, part in enumerate(parts[:5]):  # 최대 5개
                ratio_key = f'ratio_{i+1}'
                try:
                    components[ratio_key] = float(part.strip())
                except (ValueError, AttributeError):
                    pass

            # 계산된 비율들 (ratio_1이 기준이라고 가정)
            if components['ratio_1'] and components['ratio_1'] != 0:
                if components['ratio_2']:
                    components['ratio_2_1'] = components['ratio_2'] / components['ratio_1']
                if components['ratio_3']:
                    components['ratio_3_1'] = components['ratio_3'] / components['ratio_1']

            # ratio_3 / ratio_2
            if components['ratio_2'] and components['ratio_3'] and components['ratio_2'] != 0:
                components['ratio_3_2'] = components['ratio_3'] / components['ratio_2']

        except Exception:
            # 파싱 실패 시 기본값 반환
            pass

        return components