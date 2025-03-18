"""
Helper utilities for insurance prompt processing.

This module contains utility functions for:
- Schema loading
- Response processing
- Insurance company detection
"""

import json
import os
from typing import Dict, Any

def load_insurance_schema() -> Dict[str, Dict[str, str]]:
    """Load the insurance schema from structure.json file.
    
    Returns:
        The insurance schema as a dictionary
        
    Raises:
        FileNotFoundError: If the structure.json file does not exist
        json.JSONDecodeError: If the structure.json file is not valid JSON
    """
    # The structure.json file is in the excel directory
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "structure.json"
    )
        
    with open(schema_path, "r") as f:
        return json.load(f)

def process_single_field_response(response: str) -> Any:
    """Process the response for a single field extraction.
    
    Args:
        response: The response from the LLM
        
    Returns:
        The extracted value, properly formatted
    """
    # Clean the response
    cleaned = response.strip()
    
    # Check for null or empty responses
    if cleaned.lower() in ["null", "none", "not found", "not specified", "not mentioned", "n/a"]:
        return None
        
    if not cleaned:
        return None
        
    # Try to detect and convert numbers
    try:
        if cleaned.replace(".", "", 1).isdigit():
            # It's a number, determine if int or float
            if "." in cleaned:
                return float(cleaned)
            return int(cleaned)
    except:
        pass
        
    # Return as string if not null or number
    return cleaned

def detect_insurance_company(file_name: str) -> str:
    """Detect the insurance company from the file name.
    
    Args:
        file_name: The name of the file.
        
    Returns:
        The detected insurance company name or "generic" if not detected.
    """
    file_name_lower = file_name.lower()
    
    # Check for known insurance companies
    if "canada life" in file_name_lower:
        return "CanadaLife"
    elif "rbc" in file_name_lower:
        return "RBC"
    elif "manulife" in file_name_lower:
        return "Manulife"
    elif "sunlife" in file_name_lower or "sun life" in file_name_lower:
        return "SunLife"
    elif "great-west" in file_name_lower or "great west" in file_name_lower:
        return "GreatWest"
    elif "blue cross" in file_name_lower or "bluecross" in file_name_lower:
        return "BlueCross"
    elif "desjardins" in file_name_lower:
        return "Desjardins"
    elif "empire life" in file_name_lower or "empirelife" in file_name_lower:
        return "EmpireLife"
    elif "equitable" in file_name_lower:
        return "Equitable"
    elif "ssq" in file_name_lower:
        return "SSQ"
    
    # Default to generic if no match
    return "generic" 