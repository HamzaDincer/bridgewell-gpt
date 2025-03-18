"""
CanadaLife-specific prompts and examples for insurance data extraction.
"""

from typing import Optional

def get_prompt(section_name: str, field_name: str) -> Optional[str]:
    """Get CanadaLife-specific prompt for a field.
    
    Args:
        section_name: Name of the section.
        field_name: Name of the field.
        
    Returns:
        A company-specific prompt string or None if no specific prompt is available.
    """
    # Base prompt for Canada Life
    canada_life_base = f"Find the value for '{field_name}' in the Canada Life insurance booklet. "
    
    if section_name == "LIFE INSURANCE & AD&D":
        if field_name == "Schedule":
            return  "Find the value for Amount of Insurance for Employee Life Insurance. Look under the Benefit Summary page. Canada Life typically lists this as 'Employee Life Insurance' with a specific dollar value or formula (e.g., 10,000$')."
        elif field_name == "Reduction":
            return canada_life_base + "Look for 'Age Based Reduction' or 'Benefit Reduction' clauses, typically found near the Life Insurance details. Canada Life usually specifies percentage reductions at specific ages (e.g., 'reduces by 50% at age 65')."
        elif field_name == "Non-Evidence Maximum":
            return canada_life_base + "Canada Life refers to this as 'Non-Evidence Limit' or 'Maximum Without Evidence'. Look in the Life Insurance section for this limit, which is the maximum coverage without medical evidence."
        elif field_name == "Termination Age":
            return canada_life_base + "Look for 'Termination of Benefits' or 'Coverage Termination'. Canada Life typically specifies an age (often 70 or 71) or refers to retirement."
            
    elif section_name == "DEPENDENT LIFE":
        if field_name == "Schedule or Amount of Insurance":
            return canada_life_base + "Look for 'Dependent Life Insurance' or 'Spousal Life Insurance' sections. Canada Life typically shows specific dollar amounts for spouse and child coverage separately."
        elif field_name == "Termination Age":
            return canada_life_base + "Look for 'Termination of Coverage' in the Dependent Life section. Canada Life often ties this to the employee's termination age or when dependents no longer qualify."
            
    elif section_name == "LONG TERM DISABILITY":
        if field_name == "Schedule or Amount of Insurance":
            return canada_life_base + "Look for 'Long Term Disability' or 'LTD Benefits' section. Canada Life typically expresses this as a percentage of monthly earnings (e.g., 66.67% of monthly earnings)."
        elif field_name == "Maximum":
            return canada_life_base + "Look for 'Maximum Monthly Benefit' in the LTD section. Canada Life typically expresses this as a dollar maximum amount."
        elif field_name == "Non-Evidence Maximum":
            return canada_life_base + "Canada Life refers to this as 'Non-Evidence Limit' for LTD. Look for the maximum coverage available without medical evidence."
        elif field_name == "Elimination Period":
            return canada_life_base + "Canada Life often calls this 'Waiting Period' in the LTD section. It's the period before benefits begin, typically 120 days or 4 months."
        elif field_name == "Definition of Disability":
            return canada_life_base + "Look for 'Definition of Disability' in the LTD section. Canada Life typically uses a two-part definition: own occupation period followed by any occupation."
        elif field_name == "Maximum Benefit Period":
            return canada_life_base + "In the LTD section, look for how long benefits are payable. Canada Life typically specifies 'to age 65' or a specific duration."
        elif field_name == "Taxability":
            return canada_life_base + "In the LTD section, look for information about whether benefits are taxable. This depends on who pays the premiums (employer-paid is usually taxable, employee-paid is usually non-taxable)."
        elif field_name == "Pre-Existing Condition Limitation":
            return canada_life_base + "Look for 'Pre-Existing Condition' limitations in the LTD section. Canada Life typically describes conditions that existed before enrollment and any waiting periods."
        elif field_name == "Termination Age":
            return canada_life_base + "Look for when LTD coverage ends, typically at age 65 or retirement."
            
    elif section_name == "HEALTH CARE":
        if field_name == "Prescription Drugs":
            return canada_life_base + "Canada Life typically lists drug coverage under 'Extended Health Care Plan' or 'Drug Coverage'. Look for percentage coverage and any deductibles."
        elif field_name == "Pay Direct Drug Card":
            return canada_life_base + "Look for references to a 'Pay Direct Drug Card' and whether generic substitution is mandatory or optional."
        elif field_name == "Maximum":
            return canada_life_base + "Look for 'Overall Maximum' or 'Lifetime Maximum' for Extended Health Care benefits. Canada Life often specifies this as a dollar amount per person."
        elif field_name == "Paramedical Practitioners":
            return canada_life_base + "Look for 'Paramedical Services' or 'Professional Services'. Canada Life typically lists coverage percentages and maximums for various practitioners."
        elif field_name == "Included Specialists":
            return canada_life_base + "Look for a list of specific practitioners covered under the plan, such as chiropractors, physiotherapists, etc."
        elif field_name == "Fertility Drugs":
            return canada_life_base + "Look for 'Fertility Drugs' or 'Infertility Treatments' under the prescription drug section. Canada Life typically specifies coverage limits for these medications."
        elif field_name == "Smoking Cessations":
            return canada_life_base + "Look for 'Smoking Cessation Products' in the drug coverage section. Canada Life often has specific limits for these products."
        elif field_name == "Vaccines":
            return canada_life_base + "Check for coverage of vaccines in the drug section. Canada Life may specify coverage for vaccines not covered by provincial plans."
        elif field_name == "Major Medical":
            return canada_life_base + "Look for 'Major Medical' or general coverage levels for medical expenses. Canada Life typically shows a percentage and may reference deductibles."
        elif field_name == "Annual Deductible":
            return canada_life_base + "Look for 'Deductible' information for health care benefits. Canada Life may specify different amounts for individuals and families."
        elif field_name == "Hospitalization":
            return canada_life_base + "Check for 'Hospital Benefits' or 'Hospital Room Coverage'. Canada Life typically specifies the type of room covered (ward, semi-private, private)."
        elif field_name == "Orthotic Shoes":
            return canada_life_base + "Look for 'Custom Orthopedic Shoes' under medical supplies. Canada Life typically lists coverage amounts and frequency limits."
        elif field_name == "Orthotic Inserts":
            return canada_life_base + "Look for 'Custom Foot Orthotics' under medical supplies. Canada Life typically lists coverage amounts and frequency limits."
        elif field_name == "Hearing Aids":
            return canada_life_base + "Check for 'Hearing Aids' coverage. Canada Life typically specifies a dollar maximum and how often they can be replaced."
        elif field_name == "Out of Country":
            return canada_life_base + "Look for 'Out-of-Country Emergency Medical' coverage. Canada Life typically provides comprehensive emergency coverage while traveling."
        elif field_name == "Maximum Duration":
            return canada_life_base + "Look for the maximum duration of out-of-country coverage, which is typically expressed as a number of days per trip."
        elif field_name == "Trip Cancellation":
            return canada_life_base + "Check if trip cancellation insurance is included. Canada Life sometimes includes this with out-of-country medical coverage."
        elif field_name == "Private Duty Nursing":
            return canada_life_base + "Look for 'Private Duty Nursing' coverage. Canada Life typically specifies a dollar maximum per year or period."
        elif field_name == "Survivor Benefit":
            return canada_life_base + "Check for 'Survivor Benefits' which extend health coverage to dependents after an employee's death. Canada Life typically specifies a time period."
        elif field_name == "Dependent Child Definition":
            return canada_life_base + "Look for 'Eligible Dependents' or 'Dependent Children Definition' which specifies age limits and conditions for coverage of dependent children."
        elif field_name == "Benefit Year":
            return canada_life_base + "Look for 'Benefit Year' definition which indicates the cycle for benefit maximums. Canada Life often uses calendar year but may specify other periods."
        elif field_name == "Second Medical Opinion":
            return canada_life_base + "Check if a second medical opinion service is included as an additional benefit. Canada Life sometimes includes this service."
        elif field_name == "EAP":
            return canada_life_base + "Look for 'Employee Assistance Program' or 'EAP' references. Canada Life may include this as part of the benefit package."
        elif field_name == "Digital Wellness Program":
            return canada_life_base + "Check for digital wellness programs or platforms. Canada Life has been introducing more digital health services."
        elif field_name == "Virtual Healthcare Services":
            return canada_life_base + "Look for 'Virtual Care' or 'Telemedicine' services. Canada Life typically specifies the provider and any limits."
            
    # Return None if no specific prompt is available for this field
    return None

# Examples are now standardized across all companies in base.py 