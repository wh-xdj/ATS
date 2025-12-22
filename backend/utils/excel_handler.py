"""Excel处理工具"""
import pandas as pd
from openpyxl import Workbook
from typing import List, Dict, Any
from pathlib import Path


def read_excel_file(file_path: str) -> pd.DataFrame:
    """读取Excel文件"""
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        raise ValueError(f"读取Excel文件失败: {str(e)}")


def export_to_excel(data: List[Dict[str, Any]], output_path: str, sheet_name: str = "Sheet1"):
    """导出数据到Excel"""
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        
        if not data:
            wb.save(output_path)
            return
        
        # 写入表头
        headers = list(data[0].keys())
        ws.append(headers)
        
        # 写入数据
        for row in data:
            values = [row.get(header, "") for header in headers]
            ws.append(values)
        
        wb.save(output_path)
    except Exception as e:
        raise ValueError(f"导出Excel文件失败: {str(e)}")


def validate_excel_format(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """验证Excel格式"""
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"缺少必需的列: {', '.join(missing_columns)}")
    return True

