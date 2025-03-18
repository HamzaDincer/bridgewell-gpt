# Insurance Prompts System

This directory contains a modular system for managing prompts used in insurance data extraction.

## Structure

```
prompts/
├── __init__.py              # Package exports
├── base.py                  # Core prompt functionality and generic prompts
├── utils.py                 # Helper functions for schema loading and processing
├── companies/               # Company-specific prompts
│   ├── __init__.py          # Companies package
│   ├── canadalife.py        # CanadaLife-specific prompts
│   ├── rbc.py               # RBC-specific prompts
│   └── ... (other companies)
```

## Features

- **Modular Design**: Each insurance company has its own dedicated module for company-specific prompts
- **Dynamic Loading**: Company-specific modules are loaded on-demand
- **Consistent Interface**: All company modules implement the same API (`get_prompt()` function)
- **Standardized Examples**: Examples are consistently defined once in the base module, not per company
- **External Schema**: Insurance schema is defined in `structure.json` for easy updates
- **Utility Functions**: Common helper functions are centralized in the `utils.py` module

## How to Add a New Company

To add support for a new insurance company:

1. Create a new file in `companies/` named after the company (lowercase, e.g., `sunlife.py`)
2. Implement the `get_prompt(section_name, field_name) -> Optional[str]` function
3. Return `None` for fields that don't have company-specific prompts

Example:

```python
"""
NewCompany-specific prompts for insurance data extraction.
"""

from typing import Optional

def get_prompt(section_name: str, field_name: str) -> Optional[str]:
    """Get NewCompany-specific prompt for a field."""
    # Base prompt for the company
    base_prompt = f"Find the value for '{field_name}' in the NewCompany insurance booklet. "

    if section_name == "LIFE INSURANCE & AD&D":
        if field_name == "Schedule or Amount of Insurance":
            return base_prompt + "Company-specific prompt here..."
    return None
```

## Schema Management

The insurance schema is defined in `structure.json` in the parent directory. This separation allows for easy updates to the schema without modifying code.

To change the extraction fields:

1. Edit `structure.json` to add, remove, or modify fields
2. Update company-specific prompts as needed

## Helper Functions

Helper functions for schema loading, response processing, and company detection are now located in the `utils.py` module for better organization.
