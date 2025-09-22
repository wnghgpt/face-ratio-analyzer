"""
비율 데이터 파싱 엔진
다양한 형태의 비율 문자열을 파싱하고 분석하는 모듈
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import re
from collections import Counter


class RatioParser:
    def __init__(self):
        self.ratio_patterns = {
            "normalized_3d": {"pattern": r"^1:[\d.]+:[\d.]+$", "components": 3, "description": "1:x:y 형태"},
            "normalized_2d": {"pattern": r"^1:[\d.]+$", "components": 2, "description": "1:x 형태"},
            "direct_2d": {"pattern": r"^[\d.]+:[\d.]+$", "components": 2, "description": "x:y 형태"},
            "direct_3d": {"pattern": r"^[\d.]+:[\d.]+:[\d.]+$", "components": 3, "description": "x:y:z 형태"},
            "direct_4d": {"pattern": r"^[\d.]+:[\d.]+:[\d.]+:[\d.]+$", "components": 4, "description": "x:y:z:w 형태"},
            "direct_5d": {"pattern": r"^[\d.]+:[\d.]+:[\d.]+:[\d.]+:[\d.]+$", "components": 5, "description": "x:y:z:w:v 형태"}
        }

    def analyze_ratio_format(self, ratio_data: pd.Series) -> Dict:
        """데이터셋의 비율 형태를 자동 분석"""
        formats = {}
        pattern_counts = Counter()

        for ratio_string in ratio_data.dropna():
            ratio_str = str(ratio_string).strip()

            # 패턴 매칭
            matched_pattern = None
            for pattern_name, pattern_info in self.ratio_patterns.items():
                if re.match(pattern_info["pattern"], ratio_str):
                    matched_pattern = pattern_name
                    break

            if matched_pattern:
                pattern_counts[matched_pattern] += 1

                if matched_pattern not in formats:
                    formats[matched_pattern] = {
                        'count': 0,
                        'examples': [],
                        'description': self.ratio_patterns[matched_pattern]["description"],
                        'components': self.ratio_patterns[matched_pattern]["components"]
                    }

                formats[matched_pattern]['count'] += 1
                if len(formats[matched_pattern]['examples']) < 5:
                    formats[matched_pattern]['examples'].append(ratio_str)

        # 통계 추가
        total_valid = sum(pattern_counts.values())
        for pattern_name in formats:
            formats[pattern_name]['percentage'] = (formats[pattern_name]['count'] / total_valid * 100) if total_valid > 0 else 0

        return formats

    def parse_ratio_to_components(self, ratio_string: str) -> Dict[str, float]:
        """비율 문자열을 개별 컴포넌트로 분해"""
        if pd.isna(ratio_string) or not ratio_string:
            return {}

        ratio_str = str(ratio_string).strip()
        components = {}

        try:
            # 콜론으로 분리
            parts = ratio_str.split(':')

            # 각 컴포넌트 파싱
            for i, part in enumerate(parts):
                try:
                    value = float(part.strip())
                    components[f'ratio_{i+1}'] = value
                except ValueError:
                    components[f'ratio_{i+1}'] = None

            # 계산된 비율들 추가
            if len(parts) >= 2 and components.get('ratio_1') and components.get('ratio_1') != 0:
                if components.get('ratio_2') is not None:
                    components['ratio_2_1'] = components['ratio_2'] / components['ratio_1']

            if len(parts) >= 3:
                if components.get('ratio_3') is not None and components.get('ratio_1') and components.get('ratio_1') != 0:
                    components['ratio_3_1'] = components['ratio_3'] / components['ratio_1']

                if components.get('ratio_3') is not None and components.get('ratio_2') and components.get('ratio_2') != 0:
                    components['ratio_3_2'] = components['ratio_3'] / components['ratio_2']

            # 추가 통계적 지표들
            values = [v for v in [components.get(f'ratio_{i+1}') for i in range(len(parts))] if v is not None]
            if len(values) >= 2:
                components['ratio_sum'] = sum(values)
                components['ratio_mean'] = np.mean(values)
                components['ratio_std'] = np.std(values)
                components['ratio_range'] = max(values) - min(values)

        except Exception as e:
            print(f"Error parsing ratio '{ratio_string}': {e}")
            return {}

        return components

    def extract_all_components_from_dataset(self, data: pd.DataFrame, ratio_column: str = 'faceRatio') -> pd.DataFrame:
        """데이터셋에서 모든 비율 컴포넌트 추출"""
        if ratio_column not in data.columns:
            return data

        # 각 행에 대해 비율 파싱
        parsed_components = []
        for _, row in data.iterrows():
            components = self.parse_ratio_to_components(row[ratio_column])
            parsed_components.append(components)

        # 컴포넌트 DataFrame 생성
        components_df = pd.DataFrame(parsed_components)

        # 기존 데이터와 병합
        result_df = pd.concat([data.reset_index(drop=True), components_df], axis=1)

        return result_df

    def get_variable_suggestions(self, data: pd.DataFrame) -> Dict[str, List[str]]:
        """분석 타입별 변수 추천"""
        available_vars = [col for col in data.columns if col.startswith('ratio_') or col in ['roll_angle', 'tag_count']]

        suggestions = {
            "basic_ratio_analysis": {
                "x_axis": [var for var in available_vars if 'ratio_2' in var or 'ratio_3' in var][:3],
                "y_axis": [var for var in available_vars if 'ratio_3' in var or 'ratio_4' in var][:3],
                "description": "기본 얼굴 비율 분석"
            },
            "proportion_analysis": {
                "x_axis": [var for var in available_vars if '_1' in var][:3],
                "y_axis": [var for var in available_vars if '_2' in var][:3],
                "description": "비례 관계 분석"
            },
            "symmetry_analysis": {
                "x_axis": ['ratio_2_1', 'roll_angle'] + [var for var in available_vars if 'ratio_2' in var][:2],
                "y_axis": ['ratio_3_2', 'ratio_std'] + [var for var in available_vars if 'ratio_3' in var][:2],
                "description": "대칭성 및 균형 분석"
            },
            "clustering_prep": {
                "x_axis": [var for var in available_vars if var in ['ratio_2', 'ratio_3', 'ratio_2_1']][:3],
                "y_axis": [var for var in available_vars if var in ['ratio_3', 'ratio_4', 'ratio_3_1']][:3],
                "description": "클러스터링 분석 준비"
            }
        }

        # 실제 존재하는 변수들만 필터링
        for analysis_type in suggestions:
            suggestions[analysis_type]["x_axis"] = [var for var in suggestions[analysis_type]["x_axis"] if var in available_vars]
            suggestions[analysis_type]["y_axis"] = [var for var in suggestions[analysis_type]["y_axis"] if var in available_vars]

        return suggestions

    def validate_variable_combination(self, data: pd.DataFrame, x_var: str, y_var: str) -> Dict:
        """변수 조합의 유효성 검증"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "suggestions": [],
            "statistics": {}
        }

        if x_var not in data.columns:
            validation_result["valid"] = False
            validation_result["warnings"].append(f"X축 변수 '{x_var}'가 데이터에 존재하지 않습니다.")

        if y_var not in data.columns:
            validation_result["valid"] = False
            validation_result["warnings"].append(f"Y축 변수 '{y_var}'가 데이터에 존재하지 않습니다.")

        if not validation_result["valid"]:
            return validation_result

        # 데이터 유효성 검사
        x_data = data[x_var].dropna()
        y_data = data[y_var].dropna()

        if len(x_data) == 0:
            validation_result["warnings"].append(f"X축 변수 '{x_var}'에 유효한 데이터가 없습니다.")

        if len(y_data) == 0:
            validation_result["warnings"].append(f"Y축 변수 '{y_var}'에 유효한 데이터가 없습니다.")

        # 통계 정보
        if len(x_data) > 0 and len(y_data) > 0:
            # 공통 유효 데이터
            common_valid = data[[x_var, y_var]].dropna()

            validation_result["statistics"] = {
                "x_var_stats": {
                    "count": len(x_data),
                    "mean": float(x_data.mean()),
                    "std": float(x_data.std()),
                    "min": float(x_data.min()),
                    "max": float(x_data.max())
                },
                "y_var_stats": {
                    "count": len(y_data),
                    "mean": float(y_data.mean()),
                    "std": float(y_data.std()),
                    "min": float(y_data.min()),
                    "max": float(y_data.max())
                },
                "common_valid_count": len(common_valid),
                "correlation": float(common_valid[x_var].corr(common_valid[y_var])) if len(common_valid) > 1 else None
            }

            # 경고 및 제안
            if len(common_valid) < len(data) * 0.5:
                validation_result["warnings"].append("유효한 데이터가 전체의 50% 미만입니다.")

            if abs(validation_result["statistics"]["correlation"] or 0) > 0.9:
                validation_result["suggestions"].append("두 변수 간 상관관계가 매우 높습니다. 다른 변수 조합을 고려해보세요.")

            if validation_result["statistics"]["x_var_stats"]["std"] < 0.01:
                validation_result["suggestions"].append(f"X축 변수 '{x_var}'의 분산이 매우 작습니다. 시각화에 적합하지 않을 수 있습니다.")

        return validation_result

    def create_custom_variable(self, data: pd.DataFrame, var_name: str, formula: str) -> pd.Series:
        """커스텀 변수 생성"""
        try:
            # 안전한 수식 평가를 위한 허용된 변수들
            allowed_vars = {col: data[col] for col in data.columns if col.startswith('ratio_') or col in ['roll_angle']}
            allowed_vars.update({
                'np': np,
                'abs': abs,
                'sqrt': np.sqrt,
                'log': np.log,
                'exp': np.exp
            })

            # 수식 평가
            result = eval(formula, {"__builtins__": {}}, allowed_vars)
            return pd.Series(result, name=var_name)

        except Exception as e:
            raise ValueError(f"커스텀 변수 생성 실패: {e}")

    def get_variable_info(self, data: pd.DataFrame, var_name: str) -> Dict:
        """변수 정보 반환"""
        if var_name not in data.columns:
            return {"error": f"변수 '{var_name}'가 존재하지 않습니다."}

        var_data = data[var_name].dropna()

        if len(var_data) == 0:
            return {"error": f"변수 '{var_name}'에 유효한 데이터가 없습니다."}

        return {
            "name": var_name,
            "count": len(var_data),
            "valid_percentage": len(var_data) / len(data) * 100,
            "mean": float(var_data.mean()),
            "median": float(var_data.median()),
            "std": float(var_data.std()),
            "min": float(var_data.min()),
            "max": float(var_data.max()),
            "quartiles": {
                "q1": float(var_data.quantile(0.25)),
                "q3": float(var_data.quantile(0.75))
            },
            "outlier_count": self._count_outliers(var_data)
        }

    def _count_outliers(self, data: pd.Series) -> int:
        """이상치 개수 계산 (IQR 방법)"""
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = data[(data < lower_bound) | (data > upper_bound)]
        return len(outliers)