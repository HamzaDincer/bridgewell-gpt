"""
Base insurance prompt settings and schema definitions.

This module contains centralized definitions for:
- Insurance data extraction schemas
- Generic prompt templates
- Helper methods for prompt processing
"""

import json
import importlib
import os
from typing import Dict, Any, Optional

# Import helper functions from utils
from private_gpt.server.excel.prompts.utils import (
    load_insurance_schema,
    process_single_field_response,
    detect_insurance_company
)

# Insurance Schema Definitions
# ---------------------------
INSURANCE_SCHEMA = load_insurance_schema()

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
    "Schedule": "Flat $25,000",
    "Reduction": "Reduces by 50% at age 65",
    "Non-Evidence Maximum": "$25,000",
    "Termination Age": 70
  },
  "DEPENDENT LIFE": {
    "Schedule": "$10,000 Spouse; $5,000 per Child",
    "Termination Age": 70
  },
  "LONG TERM DISABILITY": {
    "Monthly Maximum": "$4,000",
    "Tax Status": "Taxable",
    "Elimination Period": "120 days",
    "Benefit Period": "To age 65",
    "Definition": "Own occupation for 24 months, any occupation thereafter",
    "Offsets": "Primary Direct, Family Indirect",
    "Pre-Existing": "3 months / 12 months",
    "Non-Evidence Maximum": "$5,000",
    "Termination Age": 65
  },
  "HEALTH CARE": {
    "Prescription Drugs": "100% - Nil deductible",
    "Pay Direct Drug Card": "Included - Generic Mandatory",
    "Maximum": "$10,000 per person per year",
    "Paramedical Practitioners": "100% - $300 per practitioner",
    "Included Specialists": ["Chiropractor", "Physiotherapist", "Massage Therapist"],
    "Vision Care": "Not included",
    "Eye Exams": "1 exam every 24 months"
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
- Extended Health Care sections
- Drug Coverage sections
- Paramedical Services sections

Look for information that matches exactly the field names in the schema.

Here are examples of how information might appear in the document:

Life Insurance:
- "Amount of Basic Term Life Insurance: $25,000"
- "BASIC LIFE INSURANCE: Schedule: 2x annual earnings"
- "Group Basic Term Life Insurance - Amount of Insurance: The Principal Sum of $20,000"

Reduction:
- "Benefit reduces to 50% at age 65"
- "The amount of your insurance reduces to 65% when you reach age 65"

Dependent Life:
- "Spouse Life Insurance: $10,000; Child Life Insurance: $5,000 per child"
- "Dependent Life - Child: The amount of insurance is $7,500 for each child"

Long Term Disability:
- "Elimination Period: 120 days"
- "Benefits begin after you have been continuously disabled for 180 days"
- "Definition of Disability: Own occupation for 24 months, any occupation thereafter"

Health Care:
- "Prescription Drugs: 100% coverage with no deductible"
- "Paramedical Practitioners: $500 per calendar year per practitioner"
- "Vision Care: $200 every 24 months"
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

# Generic Field-Specific Prompts
# -----------------------------
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
    
    # Life insurance section prompts
    if section_name == "LIFE INSURANCE & AD&D":
        if field_name == "Schedule or Amount of Insurance":
            return "Extract the life insurance schedule or amount. This refers to how much life insurance coverage is provided (e.g., 1x, 2x, or a specific dollar amount of annual earnings)."
        elif field_name == "Maximum":
            return "Extract the maximum life insurance coverage amount. This is typically a dollar amount (e.g., $500,000)."
        elif field_name == "Non-Evidence Maximum":
            return "Extract the non-evidence maximum for life insurance. This is the maximum amount provided without medical evidence of insurability."
        elif field_name == "Termination Age":
            return "Extract the termination age for life insurance coverage. This is typically when an employee reaches a specific age (e.g., age 65 or retirement)."
        elif field_name == "Reduction":
            return "Extract any age-based reductions to the life insurance coverage. This typically starts at a certain age (e.g., reduces to 50% at age 65)."
        else:
            return f"Extract the information about {field_name} from the {section_name} section."
    
    # Dependent life section prompts
    elif section_name == "DEPENDENT LIFE":
        if field_name == "Schedule or Amount of Insurance":
            return "Extract the schedule or amount for dependent life insurance. This typically specifies coverage amounts for spouse and children separately."
        elif field_name == "Termination Age":
            return "Extract the termination age for dependent life insurance coverage. This is typically when the employee reaches a specific age."
        else:
            return f"Extract the information about {field_name} from the {section_name} section."
    
    # Long term disability section prompts
    elif section_name == "LONG TERM DISABILITY":
        if field_name == "Schedule or Amount of Insurance":
            return "Extract the long term disability benefit schedule or amount. This is typically expressed as a percentage of monthly earnings (e.g., 66.67% of monthly earnings)."
        elif field_name == "Maximum":
            return "Extract the maximum monthly benefit for long term disability. This is typically a dollar amount cap on monthly benefits (e.g., $5,000 per month)."
        elif field_name == "Non-Evidence Maximum":
            return "Extract the non-evidence maximum for long term disability. This is the maximum amount provided without medical evidence of insurability."
        elif field_name == "Elimination Period":
            return "Extract the elimination or waiting period for long term disability benefits. This is how long the employee must be disabled before benefits begin (e.g., 120 days)."
        elif field_name == "Definition of Disability":
            return "Extract the definition of disability used for LTD benefits. This often includes an 'own occupation' period followed by 'any occupation' criteria."
        elif field_name == "Maximum Benefit Period":
            return "Extract the maximum benefit period for long term disability. This is how long benefits can be paid (e.g., to age 65)."
        elif field_name == "Taxability":
            return "Extract information about the taxability of LTD benefits. This indicates whether benefits are taxable or non-taxable to the employee."
        elif field_name == "Pre-Existing Condition Limitation":
            return "Extract information about pre-existing condition limitations for LTD. This refers to restrictions on coverage for conditions that existed before enrollment."
        elif field_name == "Termination Age":
            return "Extract the termination age for long term disability coverage. This is typically when an employee reaches a specific age (e.g., age 65)."
        else:
            return f"Extract the information about {field_name} from the {section_name} section."
    
    # Health care section prompts
    elif section_name == "HEALTH CARE":
        if field_name == "Prescription Drugs":
            return "Extract the prescription drug coverage details, including co-insurance (percentage covered) and any deductibles."
        elif field_name == "Pay Direct Drug Card":
            return "Extract information about the pay direct drug card, including whether it's provided and if generic substitution applies."
        elif field_name == "Maximum":
            return "Extract the overall maximum for health care benefits. This may be an annual or lifetime limit."
        elif field_name == "Paramedical Practitioners":
            return "Extract coverage details for paramedical practitioners, including co-insurance and maximum amounts."
        elif field_name == "Included Specialists":
            return "Extract the list of paramedical specialists included in the coverage (e.g., chiropractor, massage therapist, physiotherapist)."
        elif field_name == "Fertility Drugs":
            return "Extract the coverage details for fertility drugs, including any percentage covered and dollar maximums or cycle limits."
        elif field_name == "Smoking Cessations":
            return "Extract the coverage details for smoking cessation products or programs, including any limits or maximums."
        elif field_name == "Vaccines":
            return "Extract the coverage details for vaccines, including any co-insurance and maximums."
        elif field_name == "Major Medical":
            return "Extract the major medical coverage details, including co-insurance and any deductibles."
        elif field_name == "Annual Deductible":
            return "Extract the annual deductible amount for health care benefits, including whether it applies per person or per family."
        elif field_name == "Hospitalization":
            return "Extract the hospital room coverage details, including whether ward, semi-private, or private rooms are covered."
        elif field_name == "Orthotic Shoes":
            return "Extract the coverage details for orthopedic or orthotic shoes, including maximum amounts and frequency limits."
        elif field_name == "Orthotic Inserts":
            return "Extract the coverage details for custom foot orthotics, including maximum amounts and frequency limits."
        elif field_name == "Hearing Aids":
            return "Extract the coverage details for hearing aids, including maximum amounts and how often they can be claimed."
        elif field_name == "Out of Country":
            return "Extract the coverage details for emergency medical expenses when traveling outside Canada."
        elif field_name == "Maximum Duration":
            return "Extract the maximum duration for out-of-country emergency medical coverage (e.g., 60 days per trip)."
        elif field_name == "Trip Cancellation":
            return "Extract the coverage details for trip cancellation insurance, including maximum amounts."
        elif field_name == "Private Duty Nursing":
            return "Extract the coverage details for private duty nursing services, including maximum amounts."
        elif field_name == "Survivor Benefit":
            return "Extract details about the survivor benefit period for health care coverage for dependents after employee's death."
        elif field_name == "Dependent Child Definition":
            return "Extract the definition of dependent children for benefit eligibility, including age limits and student status provisions."
        elif field_name == "Benefit Year":
            return "Extract the benefit year definition used for calculating annual maximums (e.g., calendar year or from specific date)."
        elif field_name == "Second Medical Opinion":
            return "Extract information about whether second medical opinion services are included in the plan."
        elif field_name == "EAP":
            return "Extract information about the Employee Assistance Program (EAP), including whether it's included and any session limits."
        elif field_name == "Digital Wellness Program":
            return "Extract information about any digital wellness program included in the benefits."
        elif field_name == "Virtual Healthcare Services":
            return "Extract information about virtual healthcare or telemedicine services, including providers and any limits."
        else:
            return f"Extract the information about {field_name} from the {section_name} section."
    
    # Generic prompt for other sections or fields
    else:
        return f"Extract the information about {field_name} from the {section_name} section."

# Generic examples (used as fallback)
def get_generic_examples(section_name: str, field_name: str) -> str:
    """Get generic field-specific few-shot examples to guide extraction.
    
    Args:
        section_name: Name of the section (e.g., "LIFE INSURANCE & AD&D")
        field_name: Name of the field (e.g., "Schedule")
        
    Returns:
        A string containing few-shot examples for this field
    """
    examples = "Here are some examples of how this information might appear in insurance documents:\n"
    
    if section_name == "LIFE INSURANCE & AD&D":
        if field_name == "Schedule" or field_name == "Schedule or Amount of Insurance":
            return examples + (
                """Example 1:
Document text: "Amount of Basic Term Life Insurance: $25,000"
Correct extraction: $25,000

Example 2:
Document text: "Your Life Insurance Benefit is equal to 2 times your annual earnings."
Correct extraction: 2x annual earnings

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
        elif field_name == "Schedule":
            return examples + (
                """Example 1:
Document text: "Spouse Life Insurance: $10,000; Child Life Insurance: $5,000 per child"
Correct extraction: $10,000 Spouse; $5,000 per Child

Example 2:
Document text: "DEPENDENT LIFE INSURANCE:
- Spouse: The amount of insurance is $15,000
- Each Dependent Child: The amount of insurance is $7,500 for each child"
Correct extraction: $15,000 Spouse; $7,500 per Child

Example 3:
Document text: "DEPENDENT LIFE BENEFITS
Spouse: $5,000
Child: $2,500 (from birth)"
Correct extraction: $5,000 Spouse; $2,500 per Child (from birth)"""
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
        elif field_name == "Offsets":
            return examples + (
                """Example 1:
Document text: "Offsets: Direct Only - Benefits will be reduced by disability benefits from CPP/QPP, WCB/WSIB"
Correct extraction: Direct Only

Example 2:
Document text: "Benefit Integration: Primary and Family - Benefits are reduced by primary and family benefits from government plans"
Correct extraction: Primary Direct, Family Indirect

Example 3:
Document text: "Benefits are integrated with sources of income including CPP/QPP (Primary and Family benefits)"
Correct extraction: Primary Direct, Family Indirect"""
            )
        elif field_name == "Pre-Existing":
            return examples + (
                """Example 1:
Document text: "Pre-existing Condition Limitation: 3/12 - A pre-existing condition is any injury or illness for which you received medical care in the 3 months prior to your effective date. Benefits won't be paid for a disability arising from a pre-existing condition that begins during your first 12 months of coverage."
Correct extraction: 3 months / 12 months

Example 2:
Document text: "Pre-existing Conditions: No benefit is payable if the disability begins within the first 24 months of coverage and is due to a condition that existed in the 90 days before coverage began."
Correct extraction: 3 months / 24 months

Example 3:
Document text: "Pre-existing condition: 90-day look-back, 12-month limitation"
Correct extraction: 3 months / 12 months"""
            )
            
    elif section_name == "HEALTH CARE":
        if field_name == "Prescription Drugs":
            return examples + (
                """Example 1:
Document text: "Prescription Drug Coverage: 80% reimbursement after a $10 deductible per prescription"
Correct extraction: 80% - $10 deductible per prescription

Example 2:
Document text: "Drugs & Medicines: 100% coverage, no deductible applies"
Correct extraction: 100% - Nil deductible

Example 3:
Document text: "Prescription Drug Plan: 90% coverage with an annual deductible of $25 single/$50 family"
Correct extraction: 90% - $25/$50 annual deductible"""
            )
        elif field_name == "Pay Direct Drug Card":
            return examples + (
                """Example 1:
Document text: "Pay-Direct Drug Card: Yes, with mandatory generic substitution"
Correct extraction: Included - Generic Mandatory

Example 2:
Document text: "Drug payment via Pay-Direct Drug Card. Generic substitution applies unless physician indicates no substitution."
Correct extraction: Included - Generic Mandatory

Example 3:
Document text: "Drug Card is provided. Brand name drugs covered only when generic equivalent is not available."
Correct extraction: Included - Generic Mandatory"""
            )
        elif field_name == "Maximum":
            return examples + (
                """Example 1:
Document text: "Overall Health Care Maximum: $10,000 per person per benefit year"
Correct extraction: $10,000 per person per benefit year

Example 2:
Document text: "Extended Health Care has an unlimited lifetime maximum"
Correct extraction: Unlimited

Example 3:
Document text: "Maximum: $25,000 per calendar year"
Correct extraction: $25,000 per calendar year"""
            )
        elif field_name == "Hospitalization":
            return examples + (
                """Example 1:
Document text: "Hospital Coverage: 100% semi-private room accommodation"
Correct extraction: 100% - Nil deductible - Semi-Private

Example 2:
Document text: "Hospital Room: Private room covered at 80% of cost"
Correct extraction: 80% - Private

Example 3:
Document text: "Hospital Room: General ward accommodation (provincial plan level)"
Correct extraction: Ward room only"""
            )
        elif field_name == "Out of Country":
            return examples + (
                """Example 1:
Document text: "Emergency Out-of-Country Coverage: 100% coverage for emergency medical expenses, no deductible"
Correct extraction: 100% - Nil deductible - Unlimited

Example 2:
Document text: "Out of Country Medical: 100% to maximum $1,000,000 lifetime"
Correct extraction: 100% - Nil deductible - $1,000,000 lifetime

Example 3:
Document text: "Travel Health Coverage: Covered at 100% for emergency medical treatment"
Correct extraction: 100% - Nil deductible - Unlimited"""
            )
        elif field_name == "Maximum Duration":
            return examples + (
                """Example 1:
Document text: "Trip Coverage Duration: 60 consecutive days per trip"
Correct extraction: 60 consecutive days

Example 2:
Document text: "Travel coverage is limited to the first 90 days of each trip outside your province of residence"
Correct extraction: 90 consecutive days

Example 3:
Document text: "Coverage is limited to 120 days per trip outside of Canada"
Correct extraction: 120 consecutive days"""
            )
        elif field_name == "Paramedical Practitioners":
            return examples + (
                """Example 1:
Document text: "Paramedical Services: 80% to $500 per practitioner per calendar year"
Correct extraction: 80% - $500 per practitioner per calendar year

Example 2:
Document text: "Paramedical Practitioners: 100% coverage to a maximum of $300 per type of practitioner per benefit year"
Correct extraction: 100% - $300 per practitioner per benefit year

Example 3:
Document text: "Services of licensed practitioners covered at 90% to a combined maximum of $500 for all practitioners"
Correct extraction: 90% - $500 combined maximum"""
            )
        elif field_name == "Included Specialists":
            return examples + (
                """Example 1:
Document text: "Covered Practitioners: Chiropractor, Massage Therapist, Physiotherapist, Psychologist, Social Worker ($500 maximum combined), Naturopath, Osteopath"
Correct extraction: ["Chiropractor", "Massage Therapist", "Physiotherapist", "Psychologist", "Social Worker", "Naturopath", "Osteopath"]

Example 2:
Document text: "Paramedical Services include: Chiropodist, Podiatrist, Acupuncturist, Speech Therapist, Dietician"
Correct extraction: ["Chiropodist", "Podiatrist", "Acupuncturist", "Speech Therapist", "Dietician"]

Example 3:
Document text: "Eligible practitioners: 
- Chiropractor
- Massage Therapist
- Physiotherapist 
- Acupuncturist
- Naturopath"
Correct extraction: ["Chiropractor", "Massage Therapist", "Physiotherapist", "Acupuncturist", "Naturopath"]"""
            )
        elif field_name == "Dependent Child Definition":
            return examples + (
                """Example 1:
Document text: "Dependent Child Definition: Children under age 21, or under age 26 if a full-time student"
Correct extraction: Under age 21 - 26 if a full-time student

Example 2:
Document text: "Dependents are covered until age 19 or age 25 if in full-time attendance at an accredited educational institution"
Correct extraction: Under age 19 - 25 if a full-time student

Example 3:
Document text: "Coverage for dependent children ends at age 21, unless the child is a full-time student, in which case coverage continues to age 25"
Correct extraction: Under age 21 - 25 if a full-time student"""
            )
        elif field_name == "Fertility Drugs":
            return examples + (
                """Example 1:
Document text: "Fertility Drugs: Covered at 80% to a maximum of $2,400 lifetime"
Correct extraction: 80% - $2,400 lifetime

Example 2:
Document text: "Coverage for fertility medications is limited to $3,000 per lifetime"
Correct extraction: $3,000 lifetime

Example 3:
Document text: "Fertility drugs and treatments are not covered under this plan"
Correct extraction: Not covered"""
            )
        elif field_name == "Smoking Cessations":
            return examples + (
                """Example 1:
Document text: "Smoking Cessation Products: Covered at 80% to a maximum of $500 per lifetime"
Correct extraction: 80% - $500 lifetime

Example 2:
Document text: "Smoking Cessation aids are covered to a maximum of $300 in any 12-month period"
Correct extraction: $300 per 12 months

Example 3:
Document text: "No coverage is provided for smoking cessation products or medications"
Correct extraction: Not covered"""
            )
        elif field_name == "Vaccines":
            return examples + (
                """Example 1:
Document text: "Preventive Vaccines: Covered at 100% with no annual maximum"
Correct extraction: 100% - No maximum

Example 2:
Document text: "Vaccines are covered at 80% to a maximum of $300 per year"
Correct extraction: 80% - $300 per year

Example 3:
Document text: "Travel vaccines and immunizations are not covered under this plan"
Correct extraction: Not covered"""
            )
        elif field_name == "Major Medical":
            return examples + (
                """Example 1:
Document text: "Major Medical Coverage: 80% co-insurance with $25 single/$50 family deductible per year"
Correct extraction: 80% - $25/$50 deductible

Example 2:
Document text: "Major Medical Benefits: 90% coverage after annual deductible of $100"
Correct extraction: 90% - $100 deductible

Example 3:
Document text: "Comprehensive Major Medical: 100% coverage with no deductible"
Correct extraction: 100% - Nil deductible"""
            )
        elif field_name == "Annual Deductible":
            return examples + (
                """Example 1:
Document text: "Annual Health Care Deductible: $25 single/$50 family per calendar year"
Correct extraction: $25 single/$50 family per calendar year

Example 2:
Document text: "A deductible of $100 per person applies to all health benefits"
Correct extraction: $100 per person

Example 3:
Document text: "No deductible applies to health care benefits"
Correct extraction: Nil"""
            )
        elif field_name == "Orthotic Shoes":
            return examples + (
                """Example 1:
Document text: "Custom Orthopedic Shoes: 80% coverage to a maximum of $400 per calendar year"
Correct extraction: 80% - $400 per calendar year

Example 2:
Document text: "Orthopedic shoes are covered at 100% up to $200 per year"
Correct extraction: 100% - $200 per year

Example 3:
Document text: "Custom-made orthopedic shoes: $150 per person per 24 months"
Correct extraction: $150 per 24 months"""
            )
        elif field_name == "Orthotic Inserts":
            return examples + (
                """Example 1:
Document text: "Custom Foot Orthotics: 80% coverage to a maximum of $300 per calendar year"
Correct extraction: 80% - $300 per calendar year

Example 2:
Document text: "Custom-made foot orthotics are covered at 100% up to $200 per benefit year"
Correct extraction: 100% - $200 per benefit year

Example 3:
Document text: "Orthotics: $400 per person per 24 months"
Correct extraction: $400 per 24 months"""
            )
        elif field_name == "Hearing Aids":
            return examples + (
                """Example 1:
Document text: "Hearing Aids: 80% coverage to a maximum of $500 every 5 years"
Correct extraction: 80% - $500 per 5 years

Example 2:
Document text: "Coverage for hearing aids is limited to $1,000 per 36 months"
Correct extraction: $1,000 per 36 months

Example 3:
Document text: "Hearing aids are covered at 100% up to $750 per 48-month period"
Correct extraction: 100% - $750 per 48 months"""
            )
        elif field_name == "Trip Cancellation":
            return examples + (
                """Example 1:
Document text: "Trip Cancellation Insurance: $5,000 per person per trip"
Correct extraction: $5,000 per person per trip

Example 2:
Document text: "Coverage for trip cancellation up to $2,500 per calendar year"
Correct extraction: $2,500 per calendar year

Example 3:
Document text: "Trip cancellation or interruption benefits are not included in this plan"
Correct extraction: Not covered"""
            )
        elif field_name == "Private Duty Nursing":
            return examples + (
                """Example 1:
Document text: "Private Duty Nursing: 80% coverage to a maximum of $10,000 per calendar year"
Correct extraction: 80% - $10,000 per calendar year

Example 2:
Document text: "In-home nursing services are covered at 90% up to $5,000 per year"
Correct extraction: 90% - $5,000 per year

Example 3:
Document text: "Private duty nursing: $25,000 per person per 3 calendar years"
Correct extraction: $25,000 per 3 calendar years"""
            )
        elif field_name == "Survivor Benefit":
            return examples + (
                """Example 1:
Document text: "Survivor Benefit: Health coverage continued for 24 months after employee's death"
Correct extraction: 24 months

Example 2:
Document text: "In the event of your death, your dependents' health benefits will be extended for 12 months"
Correct extraction: 12 months

Example 3:
Document text: "Survivor benefits continue until the earlier of: 2 years following your death, the date your dependent is no longer eligible, or the date the policy terminates"
Correct extraction: 2 years"""
            )
        elif field_name == "Benefit Year":
            return examples + (
                """Example 1:
Document text: "Benefit Year: January 1 to December 31"
Correct extraction: Calendar Year (Jan 1 - Dec 31)

Example 2:
Document text: "The plan's benefit year runs from July 1 to June 30"
Correct extraction: July 1 - June 30

Example 3:
Document text: "All benefit maximums are applied on a calendar year basis"
Correct extraction: Calendar Year (Jan 1 - Dec 31)"""
            )
        elif field_name == "Second Medical Opinion":
            return examples + (
                """Example 1:
Document text: "Second Medical Opinion Service: Included at no additional cost"
Correct extraction: Included

Example 2:
Document text: "Access to second medical opinion services through Best Doctors is provided"
Correct extraction: Included

Example 3:
Document text: "Second medical opinion services are not included in this plan"
Correct extraction: Not included"""
            )
        elif field_name == "EAP":
            return examples + (
                """Example 1:
Document text: "Employee Assistance Program: Confidential counseling services available 24/7"
Correct extraction: Included

Example 2:
Document text: "EAP services are provided through LifeWorks, offering up to 6 sessions per issue"
Correct extraction: Included - 6 sessions per issue

Example 3:
Document text: "This plan does not include an employee assistance program"
Correct extraction: Not included"""
            )
        elif field_name == "Digital Wellness Program":
            return examples + (
                """Example 1:
Document text: "Digital Wellness Program: Access to online wellness resources and tools"
Correct extraction: Included

Example 2:
Document text: "Members have access to the Virgin Pulse digital wellness platform"
Correct extraction: Included - Virgin Pulse

Example 3:
Document text: "No digital wellness program is included with this benefit plan"
Correct extraction: Not included"""
            )
        elif field_name == "Virtual Healthcare Services":
            return examples + (
                """Example 1:
Document text: "Virtual Healthcare: 24/7 access to online medical consultations"
Correct extraction: Included - 24/7 access

Example 2:
Document text: "Telemedicine services are provided through Maple, with unlimited consultations"
Correct extraction: Included - Maple - Unlimited

Example 3:
Document text: "This plan includes virtual care services through Dialogue for all plan members"
Correct extraction: Included - Dialogue"""
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

# Company-specific prompt/example delegation
# -----------------------------------------
def get_company_specific_prompt(company_name: str, section_name: str, field_name: str) -> Optional[str]:
    """Get company-specific prompt for a field by dynamically importing the company module.
    
    Args:
        company_name: The insurance company name.
        section_name: Name of the section.
        field_name: Name of the field.
        
    Returns:
        A company-specific prompt string or None if no specific prompt is available.
    """
    try:
        # Try to import the company-specific module
        company_module = importlib.import_module(f"private_gpt.server.excel.prompts.companies.{company_name.lower()}")
        
        # If it has a get_prompt function, use it
        if hasattr(company_module, "get_prompt"):
            return company_module.get_prompt(section_name, field_name)
        
    except (ImportError, AttributeError):
        # Fall back to None if module not found or function not available
        pass
        
    return None
