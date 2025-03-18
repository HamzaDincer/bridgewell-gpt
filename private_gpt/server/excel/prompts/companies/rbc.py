"""
RBC-specific prompts and examples for insurance data extraction.
"""

from typing import Optional

def get_prompt(section_name: str, field_name: str) -> Optional[str]:
    """Get RBC-specific prompt for a field.
    
    Args:
        section_name: Name of the section.
        field_name: Name of the field.
        
    Returns:
        A company-specific prompt string or None if no specific prompt is available.
    """
    # Base prompt for RBC
    rbc_base = f"Find the value for '{field_name}' in the RBC insurance booklet. "
    
    if section_name == "LIFE INSURANCE & AD&D":
        if field_name == "Schedule or Amount of Insurance":
            return rbc_base + "RBC typically lists this under 'EMPLOYEE – BENEFIT SUMMARY' as a flat amount. Look for 'Amount of Insurance'."
        elif field_name == "Reduction":
            return rbc_base + "RBC generally includes age-based reductions in the Life Insurance section. Look for terms like 'Benefit Reduces' or 'Coverage Reduction' followed by percentages and ages."
        elif field_name == "Non-Evidence Maximum":
            return rbc_base + "RBC refers to this as 'Non-Evidence Maximum' or 'Insurance Without Evidence'. It's the maximum amount available without medical underwriting."
        elif field_name == "Termination Age":
            return rbc_base + "RBC typically specifies when coverage ends under 'Termination of Coverage' or 'When Coverage Ends', usually at age 65, 70, or retirement."
            
    elif section_name == "DEPENDENT LIFE":
        if field_name == "Schedule or Amount of Insurance":
            return rbc_base + "RBC lists coverage amounts under 'Dependent Life Insurance' or 'Family Coverage'. Look for specific dollar amounts for spouse and each dependent child."
        elif field_name == "Termination Age":
            return rbc_base + "For dependent coverage termination, RBC typically references the employee's termination age or when dependents no longer qualify as eligible dependents."
            
    elif section_name == "LONG TERM DISABILITY":
        if field_name == "Schedule or Amount of Insurance":
            return rbc_base + "For LTD, RBC typically shows a percentage of monthly earnings (e.g., 66.67% of monthly earnings)."
        elif field_name == "Maximum":
            return rbc_base + "RBC shows the maximum monthly benefit amount for LTD, typically as a specific dollar value."
        elif field_name == "Non-Evidence Maximum":
            return rbc_base + "Look for the maximum LTD coverage available without medical evidence, which RBC often lists separately."
        elif field_name == "Elimination Period":
            return rbc_base + "RBC calls this the 'Elimination Period' or 'Qualifying Period' - the period you must be disabled before benefits begin (typically 120 days)."
        elif field_name == "Definition of Disability":
            return rbc_base + "Look for 'Definition of Disability' or 'Total Disability Defined' - RBC typically uses a two-tiered definition with an initial own occupation period."
        elif field_name == "Maximum Benefit Period":
            return rbc_base + "RBC indicates how long benefits will be paid, typically 'to age 65' or until recovery or death, whichever occurs first."
        elif field_name == "Taxability":
            return rbc_base + "RBC specifies whether LTD benefits are taxable based on premium payment structure. Look for 'Tax Status of Benefits' or similar wording."
        elif field_name == "Pre-Existing Condition Limitation":
            return rbc_base + "Look for limitations regarding pre-existing conditions, which RBC typically expresses as a lookback period and a limitation period."
        elif field_name == "Termination Age":
            return rbc_base + "Look for when LTD coverage ends, which is typically at age 65."
            
    elif section_name == "HEALTH CARE":
        if field_name == "Prescription Drugs":
            return rbc_base + "RBC typically includes this under 'Extended Health Care' or 'Prescription Drugs'. Look for percentage covered and any deductibles."
        elif field_name == "Pay Direct Drug Card":
            return rbc_base + "Check for references to a drug card and whether generic substitution is mandatory or optional under RBC's drug plan."
        elif field_name == "Maximum":
            return rbc_base + "Look for the overall health care maximum, which RBC typically expresses as an annual or lifetime limit."
        elif field_name == "Paramedical Practitioners":
            return rbc_base + "RBC lists coverage for various practitioners under 'Paramedical Services'. Look for coverage percentages and maximum amounts."
        elif field_name == "Included Specialists":
            return rbc_base + "Look for the specific list of covered practitioners under RBC's paramedical coverage section."
        elif field_name == "Fertility Drugs":
            return rbc_base + "Check for fertility drug coverage under the prescription drug section. RBC typically specifies any limits."
        elif field_name == "Smoking Cessations":
            return rbc_base + "Look for coverage of smoking cessation products, which RBC may list with specific limits."
        elif field_name == "Vaccines":
            return rbc_base + "Check if vaccines are covered under the drug plan or separately. RBC may specify coverage for vaccines not covered provincially."
        elif field_name == "Major Medical":
            return rbc_base + "Look for general medical coverage percentages and any applicable deductibles."
        elif field_name == "Annual Deductible":
            return rbc_base + "Check for any overall deductible that applies to health benefits. RBC may have different amounts for individuals vs. families."
        elif field_name == "Hospitalization":
            return rbc_base + "Look for hospital room coverage details. RBC typically specifies whether ward, semi-private, or private rooms are covered."
        elif field_name == "Orthotic Shoes":
            return rbc_base + "Check for coverage of custom orthopedic shoes under medical supplies. RBC typically lists maximum amounts and frequency."
        elif field_name == "Orthotic Inserts":
            return rbc_base + "Look for coverage of custom foot orthotics. RBC typically lists maximum amounts and how often they can be replaced."
        elif field_name == "Hearing Aids":
            return rbc_base + "Check for hearing aid coverage and limits. RBC typically specifies dollar maximums and replacement frequency."
        elif field_name == "Out of Country":
            return rbc_base + "Look for emergency medical coverage while traveling outside Canada. RBC typically provides comprehensive coverage."
        elif field_name == "Maximum Duration":
            return rbc_base + "Check how many consecutive days of out-of-country coverage are provided per trip. RBC typically specifies this clearly."
        elif field_name == "Trip Cancellation":
            return rbc_base + "Look for trip cancellation insurance, which may be included with RBC's travel medical coverage."
        elif field_name == "Private Duty Nursing":
            return rbc_base + "Check for private duty nursing coverage. RBC typically specifies maximum amounts per time period."
        elif field_name == "Survivor Benefit":
            return rbc_base + "Look for coverage continuation for dependents after employee's death. RBC typically expresses this as a time period."
        elif field_name == "Dependent Child Definition":
            return rbc_base + "Check for the definition of eligible dependent children, including age limits and student status provisions."
        elif field_name == "Benefit Year":
            return rbc_base + "Look for when the benefit year begins and ends for calculating maximums. RBC often uses calendar year."
        elif field_name == "Second Medical Opinion":
            return rbc_base + "Check if second medical opinion services are included as an additional benefit."
        elif field_name == "EAP":
            return rbc_base + "Look for Employee Assistance Program details, which RBC may include as a separate benefit."
        elif field_name == "Digital Wellness Program":
            return rbc_base + "Check for any digital wellness platform or resources included in the benefits package."
        elif field_name == "Virtual Healthcare Services":
            return rbc_base + "Look for virtual healthcare or telemedicine services, which RBC has been increasingly including in their plans."
            
    # Return None if no specific prompt is available for this field
    return None

