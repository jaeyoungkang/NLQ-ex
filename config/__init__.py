# config/__init__.py
"""
설정 패키지 초기화
"""

from .schema_config import PROJECT_ID, TABLE_SCHEMA, get_schema_prompt, get_full_table_name
from .prompts import (
    get_sql_generation_system_prompt,
    get_analysis_report_prompt,
    get_html_generation_prompt
)

__all__ = [
    'PROJECT_ID',
    'TABLE_SCHEMA',
    'get_schema_prompt',
    'get_full_table_name',
    'get_sql_generation_system_prompt',
    'get_analysis_report_prompt',
    'get_html_generation_prompt'
]