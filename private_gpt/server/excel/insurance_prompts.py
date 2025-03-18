"""
DEPRECATED: This file is kept for reference only.
   The functionality has been moved to private_gpt/server/excel/prompts/ directory.
   Please use the modular prompts package for all new development.
"""

import json
from typing import Dict, Any, Optional

# Insurance Schema Definitions
# ---------------------------
INSURANCE_SCHEMA = {
    "LIFE INSURANCE & AD&D": {
        "Schedule or Amount of Insurance": "",
        "Reduction": "",
        "Non-Evidence Maximum": "",
        "Termination Age": ""
    },
    "DEPENDENT LIFE": {
        "Spouse": "",
        "Child": "",
        "Termination Age": ""
    },
    "LONG TERM DISABILITY": {
        "Monthly Maximum": "",
        "Tax Status": "",
        "Elimination Period": "",
        "Benefit Period": "",
        "Definition": ""
    }
}

# Default System Prompts
# ---------------------
DEFAULT_SYSTEM_PROMPT = """
You are an AI assistant specialized in extracting insurance information from documents. 
Extract the requested insurance details accurately based on the document content. 
Always return your answer as a valid JSON object matching the provided schema. 
The document might be split across multiple pages, so consolidate information from all pages. 
Search thoroughly through all provided pages of the document to find the information. 
Pay special attention to sections labeled 'Benefit Summary', 'Schedule of Benefits', or similar. 
If information is not found in the document, use null or appropriate empty values.

Example Insurance Data JSON:
{
  "LIFE INSURANCE & AD&D": {
    "Schedule": "$25,000",
    "Reduction": "50% at age 65",
    "Non-Evidence Maximum": "$25,000",
    "Termination Age": 70
  },
  "DEPENDENT LIFE": {
    "Spouse": "$10,000",
    "Child": "$5,000",
    "Termination Age": 70
  },
  "LONG TERM DISABILITY": {
    "Monthly Maximum": "$4,000",
    "Tax Status": "Taxable",
    "Elimination Period": "120 days",
    "Benefit Period": "To age 65",
    "Definition": "Own occupation for 24 months, any occupation thereafter"
  }
}
"""

DEFAULT_FIELD_SYSTEM_PROMPT_TEMPLATE = """
You are an AI assistant specialized in extracting insurance details from documents. 
Your task is to find the information in the document. 
Extract ONLY this requested piece of information. Be precise and accurate. 
If the requested data is not found in the document, respond with 'null'. 
Respond only with the value for the field, no other text or explanations.
"""

# Extraction Prompts
# -----------------
EXTRACTION_PROMPT_PREFIX = """Extract the insurance information from the document, focusing on benefit summary sections, and format it according to this schema.
The document is split across multiple pages, so search all pages thoroughly. Pay particular attention to:

- Schedule of Benefits sections
- Benefit Summary sections
- Life Insurance sections
- AD&D sections
- Insurance Summary Tables
- Dependent Life Coverage sections
- Long Term Disability sections

Look for information that matches exactly the field names in the schema.

Here are examples of how information might appear in the document:

Life Insurance Schedule/Amount:
- "Amount of Basic Term Life Insurance: $25,000"
- "BASIC LIFE INSURANCE: Schedule: 2x annual earnings"
- "Group Basic Term Life Insurance - Amount of Insurance: The Principal Sum of $20,000"

Reduction:
- "Benefit reduces to 50% at age 65"
- "The amount of your insurance reduces to 65% when you reach age 65"

Spouse/Child Coverage:
- "Spouse Life Insurance: $10,000"
- "Dependent Life - Child: The amount of insurance is $7,500 for each child"

Long Term Disability:
- "Elimination Period: 120 days"
- "Benefits begin after you have been continuously disabled for 180 days"
- "Definition of Disability: Own occupation for 24 months, any occupation thereafter"
"""

def get_extraction_prompt(schema: Dict[str, Any]) -> str:
    """Generate a complete extraction prompt using the given schema.
    
    Args:
        schema: The schema to use for extraction
        
    Returns:
        The complete extraction prompt
    """
    return (
        EXTRACTION_PROMPT_PREFIX +
        f"{json.dumps(schema, indent=2)}\n\n"
        f"Return ONLY the JSON result, without any explanations or other text."
    )

# Field-Specific Prompts
# ---------------------
def create_field_specific_prompt(section_name: str, field_name: str, company_name: Optional[str] = None) -> str:
    """Create a targeted prompt for a specific field.
    
    Args:
        section_name: Name of the section (e.g., "LIFE INSURANCE & AD&D")
        field_name: Name of the field (e.g., "Schedule")
        company_name: Optional insurance company name to use company-specific prompts.
        
    Returns:
        A string containing the targeted prompt
    """
    # Use company-specific prompts if available
    if company_name:
        company_prompt = get_company_specific_prompt(company_name, section_name, field_name)
        if company_prompt:
            return company_prompt
    
    # Default generic prompt
    base_prompt = f"Find the value for '{field_name}' in the insurance document. Look first under BENEFIT SUMMARY section and then under the specific {section_name} section."
    
    # Add field-specific guidance
    if section_name == "LIFE INSURANCE & AD&D":
        if field_name == "Schedule or Amount of Insurance":
            return base_prompt + " This information is usually found under BENEFIT SUMMARY section, the specific dollar amount of coverage provided under a policy (e.g. 20,000$). Respond only the amount value."
        elif field_name == "Reduction":
            return base_prompt + " This typically describes how the benefit amount reduces at certain ages (e.g., 'reduces to 50% at age 65'). Look for age-based reduction clauses."
        elif field_name == "Non-Evidence Maximum":
            return base_prompt + " This is the maximum coverage amount available without providing medical evidence. May also be called 'Non-Medical Maximum' or similar. Respond only the amount value."
        elif field_name == "Termination Age":
            return base_prompt + " This is the age at which coverage terminates, often retirement age or a specific age like 65 or 70. Respond only the age value."
            
    elif section_name == "DEPENDENT LIFE":
        if field_name == "Spouse":
            return base_prompt + " Look first under BENEFIT SUMMARY - DEPENDENT LIFE section. This is the insurance coverage amount for a spouse or partner, typically a flat dollar amount."
        elif field_name == "Child":
            return base_prompt + " Look first under BENEFIT SUMMARY - DEPENDENT LIFE section. This is the insurance coverage amount for dependent children, typically a flat dollar amount."
        elif field_name == "Termination Age":
            return base_prompt + " Look first under BENEFIT SUMMARY - DEPENDENT LIFE section. This is the age at which dependent coverage terminates. Respond only the age value."
            
    elif section_name == "LONG TERM DISABILITY":
        if field_name == "Monthly Maximum":
            return base_prompt + " This is the maximum monthly benefit amount, often expressed as a percentage of salary or a flat dollar amount."
        elif field_name == "Tax Status":
            return base_prompt + " This indicates whether premiums are taxable or non-taxable, or whether benefits are taxable or non-taxable."
        elif field_name == "Elimination Period":
            return base_prompt + " This is the waiting period before benefits begin, typically expressed in days or months (e.g., '120 days')."
        elif field_name == "Benefit Period":
            return base_prompt + " This is how long benefits will be paid, often to age 65 or for a specified period."
        elif field_name == "Definition":
            return base_prompt + " This describes how disability is defined, such as 'own occupation' or 'any occupation' and for what period."
            
    # Default for any other fields
    return base_prompt + " Search the entire document carefully for this information."

# Company-Specific Prompts
# ----------------------
def get_company_specific_prompt(company_name: str, section_name: str, field_name: str) -> Optional[str]:
    """Get company-specific prompt for a field.
    
    Args:
        company_name: The insurance company name.
        section_name: Name of the section.
        field_name: Name of the field.
        
    Returns:
        A company-specific prompt string or None if no specific prompt is available.
    """
    # Canada Life specific prompts
    if company_name == "CanadaLife":
        # Base prompt for Canada Life
        canada_life_base = f"Find the value for '{field_name}' in the Canada Life insurance booklet. "
        
        if section_name == "LIFE INSURANCE & AD&D":
            if field_name == "Schedule or Amount of Insurance":
                return canada_life_base + "Look for 'Basic Life Insurance' or 'Group Term Life Insurance' sections. Canada Life typically lists this as 'Amount of Insurance' or 'Benefit Amount' with a specific dollar value or formula (e.g., '1x annual earnings')."
            elif field_name == "Reduction":
                return canada_life_base + "Look for 'Age Based Reduction' or 'Benefit Reduction' clauses, typically found near the Life Insurance details. Canada Life usually specifies percentage reductions at specific ages (e.g., 'reduces by 50% at age 65')."
            elif field_name == "Non-Evidence Maximum":
                return canada_life_base + "Canada Life refers to this as 'Non-Evidence Limit' or 'Maximum Without Evidence'. Look in the Life Insurance section for this limit, which is the maximum coverage without medical evidence."
            elif field_name == "Termination Age":
                return canada_life_base + "Look for 'Termination of Benefits' or 'Coverage Termination'. Canada Life typically specifies an age (often 70 or 71) or refers to retirement."
                
        elif section_name == "DEPENDENT LIFE":
            if field_name == "Spouse":
                return canada_life_base + "Look for 'Dependent Life Insurance' or 'Spousal Life Insurance' sections. Canada Life typically shows a specific dollar amount for spouse coverage."
            elif field_name == "Child":
                return canada_life_base + "Look for 'Dependent Life Insurance' or 'Child Life Insurance' sections. Canada Life typically shows a specific dollar amount for each dependent child."
            elif field_name == "Termination Age":
                return canada_life_base + "Look for 'Termination of Coverage' in the Dependent Life section. Canada Life often ties this to the employee's termination age or when dependents no longer qualify."
                
        elif section_name == "LONG TERM DISABILITY":
            if field_name == "Monthly Maximum":
                return canada_life_base + "Look for 'Long Term Disability' or 'LTD Benefits' section. Canada Life typically expresses this as a percentage of monthly earnings with a dollar maximum."
            elif field_name == "Tax Status":
                return canada_life_base + "In the LTD section, look for information about whether benefits are taxable. This depends on who pays the premiums (employer-paid is usually taxable, employee-paid is usually non-taxable)."
            elif field_name == "Elimination Period":
                return canada_life_base + "Canada Life often calls this 'Waiting Period' in the LTD section. It's the period before benefits begin, typically 120 days or 4 months."
            elif field_name == "Benefit Period":
                return canada_life_base + "In the LTD section, look for how long benefits are payable. Canada Life typically specifies 'to age 65' or a specific duration."
            elif field_name == "Definition":
                return canada_life_base + "Look for 'Definition of Disability' in the LTD section. Canada Life typically uses a two-part definition: own occupation period followed by any occupation."
                
    # RBC specific prompts
    elif company_name == "RBC":
        # Base prompt for RBC
        rbc_base = f"Find the value for '{field_name}' in the RBC insurance booklet. "
        
        if section_name == "LIFE INSURANCE & AD&D":
                if field_name == "Amount of Insurance or Schedule":
                    return rbc_base + "RBC typically lists this under 'GROUP BASIC TERM LIFE INSURANCE – EMPLOYEE – BENEFIT SUMMARY' page. Look for 'Amount of Insurance' line item."
                elif field_name == "Reduction":
                    return rbc_base + "RBC generally includes age-based reductions in the Life Insurance section. Look for terms like 'Benefit Reduces' or 'Coverage Reduction' followed by percentages and ages."
                elif field_name == "Non-Evidence Maximum":
                    rbc_base = f"Find the value for Non-Evidence Maximum for GROUP BASIC TERM LIFE INSURANCE under Eligible Class(es): 1. All Eligible Employees Definition of Disability: Total Disability"
                    return rbc_base
                elif field_name == "Termination Age":
                    return rbc_base + "RBC typically specifies when coverage ends under 'Termination of Coverage' or 'When Coverage Ends', usually at age 65, 70, or retirement."
                    
        elif section_name == "DEPENDENT LIFE":
                if field_name == "Spouse":
                    rbc_base = f"Find the value for Maximum Amount of Insurance for spouse in the RBC insurance booklet. "
                    return rbc_base + "RBC lists spouse coverage amounts under 'GROUP BASIC TERM LIFE INSURANCE – DEPENDENTS – BENEFIT SUMMARY'. Look for a specific dollar amount for spousal coverage."
                elif field_name == "Child":
                    rbc_base = f"Find the value for Maximum Amount of Insurance for each child"
                    return rbc_base + ""
                
        elif section_name == "DEPENDENT LIFE":
            if field_name == "Spouse":
                return rbc_base + "RBC lists spouse coverage amounts under 'Dependent Life Insurance' or 'Family Coverage'. Look for a specific dollar amount for spousal coverage."
            elif field_name == "Child":
                return rbc_base + "RBC lists child coverage amounts under 'Dependent Life Insurance' or 'Family Coverage'. Look for a specific dollar amount for each dependent child."
            elif field_name == "Termination Age":
                return rbc_base + "For dependent coverage termination, RBC typically references the employee's termination age or when dependents no longer qualify as eligible dependents."
                
        elif section_name == "LONG TERM DISABILITY":
            if field_name == "Monthly Maximum":
                return rbc_base + "For LTD, RBC typically shows a percentage of monthly earnings (e.g., 66.67%) up to a specific maximum monthly benefit amount."
            elif field_name == "Tax Status":
                return rbc_base + "RBC specifies whether LTD benefits are taxable based on premium payment structure. Look for 'Tax Status of Benefits' or similar wording."
            elif field_name == "Elimination Period":
                return rbc_base + "RBC calls this the 'Elimination Period' or 'Qualifying Period' - the period you must be disabled before benefits begin (typically 120 days)."
            elif field_name == "Benefit Period":
                return rbc_base + "RBC indicates how long benefits will be paid, typically 'to age 65' or until recovery or death, whichever occurs first."
            elif field_name == "Definition":
                return rbc_base + "Look for 'Definition of Disability' or 'Total Disability Defined' - RBC typically uses a two-tiered definition with an initial own occupation period."  
    # Return None if no company-specific prompt is available
    return None

# Few-Shot Learning Examples
# ------------------------
def get_few_shot_examples(section_name: str, field_name: str, company_name: Optional[str] = None) -> str:
    """Get field-specific few-shot examples to guide extraction.
    
    Args:
        section_name: Name of the section (e.g., "LIFE INSURANCE & AD&D")
        field_name: Name of the field (e.g., "Schedule")
        company_name: Optional insurance company name to use company-specific examples.
        
    Returns:
        A string containing few-shot examples for this field
    """
    # Use company-specific examples if available
    if company_name:
        company_examples = get_company_specific_examples(company_name, section_name, field_name)
        if company_examples:
            return company_examples
    
    # Generic examples (used as fallback)
    examples = "Here are some examples of how this information might appear in insurance documents:\n"
    
    if section_name == "LIFE INSURANCE & AD&D":
        if field_name == "Schedule or Amount of Insurance":
            return examples + (
                """Example 1:
Document text: "Amount of Basic Term Life Insurance: $25,000"
Correct extraction: $25,000

Example 3:
Document text: "Group Basic Term Life Insurance - Benefit Summary
Amount of Insurance: The Principal Sum of $20,000"
Correct extraction: $20,000"""
            )
        elif field_name == "Reduction":
            return examples + (
                """Example 1:
Document text: "Benefit reduces to 50% at age 65"
Correct extraction: 50% at age 65

Example 2:
Document text: "The amount of your insurance reduces to 65% of the original amount when you reach age 65, and to 50% of the original amount when you reach age 70."
Correct extraction: 65% at age 65, 50% at age 70

Example 3:
Document text: "The benefit amount reduces by 50% at age 65."
Correct extraction: 50% at age 65"""
            )
        elif field_name == "Non-Evidence Maximum":
            return examples + (
                """Example 1:
Document text: "Non-Evidence Maximum: $50,000"
Correct extraction: $50,000

Example 2:
Document text: "Non-Medical Maximum: $45,000. Amounts over this are subject to evidence of insurability."
Correct extraction: $45,000

Example 3:
Document text: "Evidence of insurability is required for amounts exceeding $100,000"
Correct extraction: $100,000"""
            )
        elif field_name == "Termination Age":
            return examples + (
                """Example 1:
Document text: "Coverage terminates at age 70 or retirement, whichever occurs first."
Correct extraction: 70

Example 2:
Document text: "Termination Age: Your coverage terminates at the earlier of retirement or age 71."
Correct extraction: 71

Example 3:
Document text: "Your life insurance will terminate when you reach age 65."
Correct extraction: 65"""
            )
            
    elif section_name == "DEPENDENT LIFE":
        if field_name == "Spouse":
            return examples + (
                """Example 1:
Document text: "Spouse Life Insurance: $10,000"
Correct extraction: $10,000

Example 2:
Document text: "Dependent Life - Spouse: The amount of insurance is $15,000."
Correct extraction: $15,000

Example 3:
Document text: "DEPENDENT LIFE BENEFITS
Spouse: $5,000"
Correct extraction: $5,000"""
            )
        elif field_name == "Child":
            return examples + (
                """Example 1:
Document text: "Child Life Insurance: $5,000 per child"
Correct extraction: $5,000

Example 2:
Document text: "Dependent Life - Child: The amount of insurance is $7,500 for each child."
Correct extraction: $7,500

Example 3:
Document text: "DEPENDENT LIFE BENEFITS
Child: $2,500"
Correct extraction: $2,500"""
            )
        elif field_name == "Termination Age":
            return examples + (
                """Example 1:
Document text: "Coverage terminates when the employee reaches age 70 or retirement, whichever occurs first."
Correct extraction: 70

Example 2:
Document text: "Dependents' coverage will terminate when your coverage terminates or when they are no longer eligible as dependents, whichever occurs first."
Correct extraction: Same as employee

Example 3:
Document text: "Termination Age: your dependent coverage terminates at the earlier of retirement or age 71."
Correct extraction: 71"""
            )
            
    elif section_name == "LONG TERM DISABILITY":
        if field_name == "Monthly Maximum":
            return examples + (
                """Example 1:
Document text: "Maximum Monthly Benefit: $5,000"
Correct extraction: $5,000

Example 2:
Document text: "The monthly income benefit is 66.67% of your monthly earnings, up to a maximum of $6,000 per month."
Correct extraction: $6,000

Example 3:
Document text: "LONG TERM DISABILITY
Benefit Amount: 60% of your monthly earnings, to a maximum of $4,500"
Correct extraction: $4,500"""
            )
        elif field_name == "Tax Status":
            return examples + (
                """Example 1:
Document text: "Tax Status: Premiums are paid with after-tax dollars, therefore benefits are non-taxable."
Correct extraction: Non-taxable

Example 2:
Document text: "Since your employer pays the premium, your benefit payments are taxable income."
Correct extraction: Taxable

Example 3:
Document text: "LONG TERM DISABILITY
Benefit: 60% of monthly earnings
Tax Status: Taxable"
Correct extraction: Taxable"""
            )
        elif field_name == "Elimination Period":
            return examples + (
                """Example 1:
Document text: "Elimination Period: 120 days"
Correct extraction: 120 days

Example 2:
Document text: "Benefits begin after you have been continuously disabled for 180 days."
Correct extraction: 180 days

Example 3:
Document text: "LONG TERM DISABILITY
Waiting Period: 90 days of continuous disability"
Correct extraction: 90 days"""
            )
        elif field_name == "Benefit Period":
            return examples + (
                """Example 1:
Document text: "Benefit Period: to age 65"
Correct extraction: To age 65

Example 2:
Document text: "LTD benefits are payable to the earlier of your recovery, death, or the attainment of age 65."
Correct extraction: To age 65

Example 3:
Document text: "LONG TERM DISABILITY
Maximum Benefit Period: 2 years"
Correct extraction: 2 years"""
            )
        elif field_name == "Definition":
            return examples + (
                """Example 1:
Document text: "Definition of Disability: Own occupation for 24 months, any occupation thereafter"
Correct extraction: Own occupation for 24 months, any occupation thereafter

Example 2:
Document text: "You are considered disabled if you are unable to perform the duties of your regular occupation during the first 2 years of disability. After that, you are considered disabled if you are unable to perform the duties of any occupation for which you are reasonably qualified by education, training or experience."
Correct extraction: Own occupation for 2 years, any occupation thereafter

Example 3:
Document text: "LONG TERM DISABILITY
Definition of Total Disability: Unable to perform any occupation"
Correct extraction: Any occupation"""
            )
            
    # Default generic examples if no specific ones are available
    return examples + (
        """Example 1:
Document text: \"""" + field_name + """: [value]\"
Correct extraction: [value]

Example 2:
Document text: \"... """ + field_name.lower() + """ is [value] ...\"
Correct extraction: [value]"""
    )

def get_company_specific_examples(company_name: str, section_name: str, field_name: str) -> Optional[str]:
    """Get company-specific few-shot examples for a field.
    
    Args:
        company_name: The insurance company name.
        section_name: Name of the section.
        field_name: Name of the field.
        
    Returns:
        A string containing company-specific examples or None if no specific examples available.
    """
    examples_intro = f"Here are examples of how this information appears in {company_name} insurance documents:\n"
    
    # Canada Life specific examples
    if company_name == "CanadaLife":
        if section_name == "LIFE INSURANCE & AD&D":
            if field_name == "Schedule or Amount of Insurance":
                return examples_intro + (
                    """
                    Example 1:
                    Document text: "Amount of Insurance: $25,000"
                    Correct extraction: $25,000
                    """
                )
            elif field_name == "Reduction":
                return examples_intro + (
                """
                Example 1:
                Document text: "Your Basic Life Insurance will reduce by 50% at age 65."
                Correct extraction: 50% at age 65

                Example 2:
                Document text: "Your Life Insurance amount reduces to 50% of the original amount when you reach age 65 and terminates at age 70."
                Correct extraction: 50% at age 65

                Example 3:
                Document text: "Benefit Reduction: Your benefit reduces by 50% at age 65."
                Correct extraction: 50% at age 65
                """
                )
            elif field_name == "Termination Age":
                return examples_intro + (
                """
                Example 1:
                Document text: "Termination Age: Your coverage will terminate when you reach age 71 or retirement, whichever is earlier."
                Correct extraction: 71

                Example 2:
                Document text: "Life Insurance terminates at the earlier of your retirement or age 71."
                Correct extraction: 71

                Example 3:
                Document text: "Coverage Termination: Coverage terminates at age 70."
                Correct extraction: 70
                """
                )
        
        elif section_name == "DEPENDENT LIFE":
            if field_name == "Spouse":
                return examples_intro + (
                    """Example 1:
Document text: "DEPENDENT LIFE INSURANCE
Spouse: $10,000"
Correct extraction: $10,000

Example 2:
Document text: "Your Spouse's insurance under this benefit is $15,000."
Correct extraction: $15,000

Example 3:
Document text: "Amount of Insurance - Dependent Life: Spouse: $10,000"
Correct extraction: $10,000"""
                )
            elif field_name == "Child":
                return examples_intro + (
                    """Example 1:
Document text: "DEPENDENT LIFE INSURANCE
Child: $5,000 per child"
Correct extraction: $5,000

Example 2:
Document text: "The amount of insurance for each of your Children is $10,000."
Correct extraction: $10,000

Example 3:
Document text: "Amount of Insurance - Dependent Life: Each Child: $5,000"
Correct extraction: $5,000"""
                )
        
        elif section_name == "LONG TERM DISABILITY":
            if field_name == "Monthly Maximum":
                return examples_intro + (
                    """Example 1:
Document text: "LONG TERM DISABILITY
Benefit: 66.7% of the first $3,500 of your monthly Earnings plus 50% of the remainder, subject to a maximum benefit of $10,000 per month."
Correct extraction: $10,000

Example 2:
Document text: "Maximum Monthly Benefit: $6,000"
Correct extraction: $6,000

Example 3:
Document text: "Your LTD benefit is 66.67% of your monthly Earnings, to a maximum of $7,500 per month."
Correct extraction: $7,500"""
                )
            elif field_name == "Elimination Period":
                return examples_intro + (
                    """Example 1:
Document text: "LONG TERM DISABILITY
Waiting Period: 119 days"
Correct extraction: 119 days

Example 2:
Document text: "Benefits begin after 4 months of continuous Total Disability."
Correct extraction: 4 months

Example 3:
Document text: "Elimination Period: 120 days"
Correct extraction: 120 days"""
                )
                
    # RBC specific examples
    elif company_name == "RBC":
        if section_name == "LIFE INSURANCE & AD&D":
            if field_name == "Schedule or Amount of Insurance":
                return examples_intro + (
                    """Example 1:
Document text: "Basic Employee Life Insurance: $50,000"
Correct extraction: $50,000

Example 2:
Document text: "Your Life Insurance Benefit is equal to 2 times your annual earnings."
Correct extraction: 2x annual earnings

Example 3:
Document text: "Basic Life Benefit: An amount equal to 1x your annual salary, rounded up to the next $1,000."
Correct extraction: 1x annual salary"""
                )
            elif field_name == "Reduction":
                return examples_intro + (
                    """Example 1:
Document text: "Your Basic Life Insurance will reduce to 50% of the original amount when you reach age 65."
Correct extraction: 50% at age 65

Example 2:
Document text: "Benefit Reduction: The amount reduces to 65% at age 65 and to 50% at age 70."
Correct extraction: 65% at age 65, 50% at age 70

Example 3:
Document text: "Your life insurance coverage reduces by 50% on your 65th birthday."
Correct extraction: 50% at age 65"""
                )
            elif field_name == "Non-Evidence Maximum":
                return examples_intro + (
                    """Example 1:
Document text: "Non-Evidence Maximum: $100,000"
Correct extraction: $100,000

Example 2:
Document text: "Non-Medical Maximum: The maximum amount of coverage available without evidence of insurability is $75,000."
Correct extraction: $75,000

Example 3:
Document text: "Evidence of Insurability: Not required for amounts of $50,000 or less."
Correct extraction: $50,000"""
                )
            elif field_name == "Termination Age":
                return examples_intro + (
                    """Example 1:
Document text: "Your Life Insurance coverage will terminate on the earliest of: the date you terminate employment, the date you retire, or the date you attain age 70."
Correct extraction: 70

Example 2:
Document text: "Termination: The earlier of age 65 or retirement."
Correct extraction: 65

Example 3:
Document text: "Coverage ends at age 70."
Correct extraction: 70"""
                )
        
        elif section_name == "DEPENDENT LIFE":
            if field_name == "Spouse":
                return examples_intro + (
                    """Example 1:
Document text: "Dependent Life Insurance - Spouse: $20,000"
Correct extraction: $20,000

Example 2:
Document text: "Your spouse's life insurance coverage amount is $10,000."
Correct extraction: $10,000

Example 3:
Document text: "DEPENDENT LIFE INSURANCE SUMMARY
Spouse: $15,000"
Correct extraction: $15,000"""
                )
            elif field_name == "Child":
                return examples_intro + (
                    """Example 1:
Document text: "Dependent Life Insurance - Child: $10,000 per child"
Correct extraction: $10,000

Example 2:
Document text: "Each dependent child is insured for $5,000."
Correct extraction: $5,000

Example 3:
Document text: "DEPENDENT LIFE INSURANCE SUMMARY
Child: $7,500 for each eligible child"
Correct extraction: $7,500"""
                )
            elif field_name == "Termination Age":
                return examples_intro + (
                    """Example 1:
Document text: "Dependent Life Insurance terminates when you reach age 70 or retire, whichever occurs first."
Correct extraction: 70

Example 2:
Document text: "Coverage for your dependents will end when your coverage ends or when they no longer qualify as eligible dependents."
Correct extraction: Same as employee

Example 3:
Document text: "Termination Age for all Dependent Life coverage: Employee's age 65"
Correct extraction: 65"""
                )
        
        elif section_name == "LONG TERM DISABILITY":
            if field_name == "Monthly Maximum":
                return examples_intro + (
                    """Example 1:
Document text: "Long Term Disability: 66.67% of monthly earnings to a maximum of $6,000 per month"
Correct extraction: $6,000

Example 2:
Document text: "Maximum Monthly Benefit: $7,500"
Correct extraction: $7,500

Example 3:
Document text: "LTD Benefit: 60% of your monthly earnings, subject to a maximum of $5,000 monthly"
Correct extraction: $5,000"""
                )
            elif field_name == "Tax Status":
                return examples_intro + (
                    """Example 1:
Document text: "Tax Status: Benefits are taxable"
Correct extraction: Taxable

Example 2:
Document text: "Because you pay the premium for this coverage with after-tax dollars, any benefits you receive are non-taxable."
Correct extraction: Non-taxable

Example 3:
Document text: "LTD benefits are non-taxable income."
Correct extraction: Non-taxable"""
                )
            elif field_name == "Elimination Period":
                return examples_intro + (
                    """Example 1:
Document text: "Elimination Period: 120 days"
Correct extraction: 120 days

Example 2:
Document text: "Benefits begin after you have been totally disabled for 180 consecutive days."
Correct extraction: 180 days

Example 3:
Document text: "Waiting Period: 17 weeks"
Correct extraction: 17 weeks"""
                )
            elif field_name == "Benefit Period":
                return examples_intro + (
                    """Example 1:
Document text: "Benefit Period: To age 65"
Correct extraction: To age 65

Example 2:
Document text: "Benefits are payable to the earlier of recovery, death, or your 65th birthday."
Correct extraction: To age 65

Example 3:
Document text: "Maximum Benefit Period: 5 years"
Correct extraction: 5 years"""
                )
            elif field_name == "Definition":
                return examples_intro + (
                    """Example 1:
Document text: "Definition of Disability: During the elimination period and the following 24 months, you are considered disabled if you are unable to perform the essential duties of your regular occupation. Thereafter, you are considered disabled if you are unable to perform any occupation for which you are reasonably qualified."
Correct extraction: Own occupation for 24 months, any occupation thereafter

Example 2:
Document text: "Total Disability Definition: You are unable to perform any occupation."
Correct extraction: Any occupation

Example 3:
Document text: "Definition: 2 year own occupation, followed by any occupation."
Correct extraction: Own occupation for 2 years, any occupation thereafter"""
                )
    
    # Add more companies as needed...
    
    # Return None if no company-specific examples are available
    return None

# Helper Methods
# ------------
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