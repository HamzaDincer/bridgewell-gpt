"""
Prompts package for insurance data extraction.

This package provides a modular system for managing prompts used in insurance data extraction.
"""

from private_gpt.server.excel.prompts.base import (
    INSURANCE_SCHEMA,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_FIELD_SYSTEM_PROMPT_TEMPLATE,
    get_extraction_prompt,
    create_field_specific_prompt,
    get_generic_examples,
)

# Re-export utility functions
from private_gpt.server.excel.prompts.utils import (
    load_insurance_schema,
    process_single_field_response,
    detect_insurance_company
)

__all__ = [
    'INSURANCE_SCHEMA',
    'DEFAULT_SYSTEM_PROMPT',
    'DEFAULT_FIELD_SYSTEM_PROMPT_TEMPLATE',
    'get_extraction_prompt',
    'create_field_specific_prompt',
    'get_generic_examples',
    'load_insurance_schema',
    'process_single_field_response',
    'detect_insurance_company'
] 