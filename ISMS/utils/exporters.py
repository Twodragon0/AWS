"""
데이터 내보내기 유틸리티 모듈
CSV, Excel, JSON 형식으로 데이터 내보내기
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)


class DataExporter:
    """데이터 내보내기 클래스"""
    
    @staticmethod
    def export_to_csv(
        data: List[List[Any]],
        headers: List[str],
        output_path: str,
        encoding: str = 'utf-8-sig'  # Excel 호환성을 위해 BOM 포함
    ) -> None:
        """
        CSV 파일로 내보내기
        
        Args:
            data: 데이터 행 리스트
            headers: 헤더 리스트
            output_path: 출력 파일 경로
            encoding: 인코딩 (기본값: utf-8-sig)
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_file, 'w', newline='', encoding=encoding) as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(data)
            logger.info(f"CSV 파일 생성 완료: {output_path}")
        except Exception as e:
            logger.error(f"CSV 파일 생성 실패: {e}")
            raise
    
    @staticmethod
    def export_to_json(
        data: List[Dict[str, Any]],
        output_path: str,
        indent: int = 2
    ) -> None:
        """
        JSON 파일로 내보내기
        
        Args:
            data: 딕셔너리 리스트
            output_path: 출력 파일 경로
            indent: 들여쓰기 (기본값: 2)
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            logger.info(f"JSON 파일 생성 완료: {output_path}")
        except Exception as e:
            logger.error(f"JSON 파일 생성 실패: {e}")
            raise
    
    @staticmethod
    def export_to_excel(
        dataframes: Dict[str, 'pd.DataFrame'],
        output_path: str
    ) -> None:
        """
        Excel 파일로 내보내기 (여러 시트)
        
        Args:
            dataframes: 시트 이름을 키로 하는 DataFrame 딕셔너리
            output_path: 출력 파일 경로
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas와 openpyxl이 필요합니다. pip install pandas openpyxl")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                for sheet_name, df in dataframes.items():
                    # 시트 이름 길이 제한 (Excel 제한: 31자)
                    safe_sheet_name = sheet_name[:31]
                    df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            logger.info(f"Excel 파일 생성 완료: {output_path} ({len(dataframes)}개 시트)")
        except Exception as e:
            logger.error(f"Excel 파일 생성 실패: {e}")
            raise

