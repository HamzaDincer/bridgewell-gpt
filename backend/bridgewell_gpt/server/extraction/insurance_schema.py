from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict

class BoundingBox(BaseModel):
    l: float = Field(description="Left coordinate of the bounding box (0.0 to 1.0)")
    t: float = Field(description="Top coordinate of the bounding box (0.0 to 1.0)")
    r: float = Field(description="Right coordinate of the bounding box (0.0 to 1.0)")
    b: float = Field(description="Bottom coordinate of the bounding box (0.0 to 1.0)")

class ExtractionField(BaseModel):
    value: str = Field(description="The extracted value from the document")
    page: Optional[int] = Field(None, description="The page number where the value was found")
    bbox: Optional[BoundingBox] = Field(None, description="The bounding box coordinates of the extracted text")
    source_snippet: Optional[str] = Field(
        None,
        description="Only the sentence or minimal span of text that supports the extracted value."
    )
    
    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True
    )

class LifeInsuranceADD(BaseModel):
    schedule: Optional[ExtractionField] = Field(None, 
    description="""Extract the insurance amount for the Life Insurance Benefit. Return the response in this format: Flat $[amount] (e.g., Flat $20,000) or $[multiplier] of Annual Salary  $[maximum amount] Example Values: Flat $20,000, 2x Annual Salary to maximum $500,000""")
    reduction: Optional[ExtractionField] = Field(None, 
    description="""Extract the age-based reduction clause for the Life Insurance Benefit. Return it in this format: Reduces by [percentage]% at age [age], further reduces to [amount] or [percentage]% at [age] Example Values: Reduces by 65% at age 65, Reduces by 65% at age 65, further reduces to 10,000$ at age 71""")
    non_evidence_maximum: Optional[ExtractionField] = Field(None, 
    description="""Extract the insurance amount that does not require medical evidence (Non-Evidence Maximum) for the Life Insurance Benefit. If not found, return the insurance amount found in the schedule field. Return it as a dollar value in this format: $[amount] (e.g., $25,000, $50,000) Example Values: $25,000, $50,000""")
    termination_age: Optional[ExtractionField] = Field(None, 
    description="""Extract the age at which Life Insurance coverage terminates. Return it in this format: [age] Example Values: 65, 70, 75""")

class DependentLife(BaseModel):
    schedule: Optional[ExtractionField] = Field(None, 
    description="""Extract the insurance amount for spouse and children in the Dependent Life Benefit. Return the response in this format: $[amount] Spouse; $[amount] per Child Example Values: $100,000 Spouse; $50,000 per Child""")
    termination_age: Optional[ExtractionField] = Field(None, 
    description="""Extract the age at which Dependent Life coverage terminates. Return it in this format: "[age]" Example Values: 65, 70, 75""")
                             
class CriticalIllness(BaseModel):
    schedule: Optional[ExtractionField] = Field(None, description="""Extract the insurance amount for the Critical Illness Benefit. Return the response in this format: Flat $[amount] (e.g., Flat $20,000) or $[multiplier] of Annual Salary to $[maximum amount] Example Values: Flat $20,000, 2x Annual Salary to maximum $500,000""")
    impairments: Optional[ExtractionField] = Field(None, description="""Extract the covered impairments/conditions for the Critical Illness Benefit. Return it in this format: "[number] illnesses included: [illness]" Example Values: 25 illnesses included: Aortic Surgery, Aplastic Anemia, Bacterial Meningitis, Benign Brain Tumour, Blindness, Cancer...""")
    termination_age: Optional[ExtractionField] = Field(None, description="""Extract the age at which Critical Illness coverage terminates. Return it in this format: "[age]" Example Values: 65, 70, 75""")

class LongTermDisability(BaseModel):
    schedule: Optional[ExtractionField] = Field(None, 
    description="""Extract the insurance amount for the Long Term Disability Benefit. Return the response in this format: %[percentage] of monthly earnings or $[amount] Example Values: 75% of monthly earnings, $10,000""")
    monthly_maximum: Optional[ExtractionField] = Field(None, 
    description="""Extract the maximum monthly benefit amount for the Long Term Disability Benefit. Return it in this format: "$[amount]" Example Values: $10,000, $20,000""")
    tax_status: Optional[ExtractionField] = Field(None, 
    description="""Extract the tax status of the Long Term Disability Benefit. Return it in this format: "[tax status]" Example Values: Taxable, Non-Taxable""")
    elimination_period: Optional[ExtractionField] = Field(None, 
    description="""Extract the elimination period before benefits begin for the Long Term Disability Benefit. Return it in this format: "[number] days" Example Values: 180 days, 119 days""")
    benefit_period: Optional[ExtractionField] = Field(None, 
    description="""Extract the maximum period for which benefits will be paid for the Long Term Disability Benefit. Return it in this format: "to age [age]" Example Values: to age 65, to age 70""")
    definition: Optional[ExtractionField] = Field(
        None,
        description="""Extract the definition of disability in terms of duration and occupation type for the Long Term Disability Benefit. Return it in this format: "[duration] ([duration in months]) [occupation type]" Example Values: 2 years (24 months) own occupation, 2 years (24 months) any occupation"""
    )
    offsets: Optional[ExtractionField] = Field(
        None, 
        description="""Extract the income/benefit offsets that reduce LTD benefit. Return it in this format: "[offsets]" Example Values: Primary, Primary Direct, Family Indirect""")
    cost_of_living_adjustment: Optional[ExtractionField] = Field(
        None, 
        description="""Extract the cost of living adjustment for the Long Term Disability Benefit. Return it in this format: "[cost of living adjustment]" Example Values: 2%, Consumer Price index or 2%, whichever is less""")
    pre_existing: Optional[ExtractionField] = Field(
        None, 
        description="""Extract the pre-existing condition limitations for the Long Term Disability Benefit. Return it in this format: "[number] months / [number] months" or "[number] weeks if treatment free; otherwise [number] months" Example Values: 3 months / 12 months, 90 days / 12 months, 13 weeks if treatment free; otherwise 12 months""")
    survivor_benefit: Optional[ExtractionField] = Field(
        None, 
        description="""Extract the survivor benefit details for the Long Term Disability Benefit. Return it in this format: "[number] months" or "[number] year" Example Values: 3 months, 6 months, 1 year""")
    non_evidence_maximum: Optional[ExtractionField] = Field(
        None, 
        description="""Extract the maximum amount that does not require evidence for the Long Term Disability Benefit. If not explicitly stated, return the schedule amount listed under the Long Term Disability Benefit. Return it in this format: "$[amount]" Example Values: $10,000, $20,000""")     
    termination_age: Optional[ExtractionField] = Field(
        None, 
        description="""Extract the age at which coverage terminates for the Long Term Disability Benefit. Return it in this format: "[age]" Example Values: 65, 70, 75""")

class ShortTermDisability(BaseModel):
    schedule: Optional[ExtractionField] = Field(None, description="""Extract the schedule of benefits for the Short Term Disability Benefit. Return it in this format: "[percentage]% of weekly earnings" Example Values: 100% of weekly earnings, 80% of weekly earnings""")
    weekly_maximum: Optional[ExtractionField] = Field(None, description="""Extract the maximum weekly benefit amount for the Short Term Disability Benefit. Return it in this format: "$[amount]" Example Values: $1,000, $2,000""")
    tax_status: Optional[ExtractionField] = Field(None, description="""Extract the tax status of the Short Term Disability Benefit. Return it in this format: "[tax status]" Example Values: Taxable, Non-Taxable""")
    elimination_period: Optional[ExtractionField] = Field(None, description="""Extract the elimination period before benefits begin for the Short Term Disability Benefit. Return it in this format: "[number]st day accident & hospital; [number]th day sickness" Example Values: 1st day accident & hospital; 8th day sickness""")
    benefit_period: Optional[ExtractionField] = Field(None, description="""Extract the maximum period for which benefits will be paid for the Short Term Disability Benefit. Return it in this format: "[number] weeks" Example Values: 17 weeks, 26 weeks""")
    non_evidence_maximum: Optional[ExtractionField] = Field(None, description="""Extract the maximum amount without evidence for the Short Term Disability Benefit. Return it in this format: "$[amount]" Example Values: $1,000, $2,000""")
    termination_age: Optional[ExtractionField] = Field(None, description="""Extract the age at which coverage terminates for the Short Term Disability Benefit. Return it in this format: "[age]" Example Values: 65, 70, 75""")

class HealthCare(BaseModel):
    prescription_drugs: Optional[ExtractionField] = Field(
        None, 
        description="""Extract the prescription drug coverage details for the Health Care Benefit. Return it in this format: "[coverage percentage]% - [deductible details]" Example Values: 100% - Equal to dispensing fee deductible per prescription, 90% - Nil deductible - Drugs purchased at Costco, 100% - Nil deductible, 80% - Nil deductible""")
    pay_direct_drug_card: Optional[ExtractionField] = Field(
        None, 
        description="""Extract the pay direct drug card availability for the Health Care Benefit. Format the response as in the Example Values. Example Values: Included - Generic Mandatory, Included - Brand Name Mandatory, Not Included""")
    maximum: Optional[ExtractionField] = Field(None, description="""Extract the overall maximum coverage for the Health Care Benefit. Return it in this format: "$[amount] or Unlimited" Example Values: Unlimited, $10,000, $20,000""")
    fertility_drugs: Optional[ExtractionField] = Field(None, description="""Extract the fertility drug coverage for the Health Care Benefit. Return it in this format: "$[amount] lifetime maximum" or "[number] cycles to $[amount] lifetime maximum" Example Values: $2,400 lifetime maximum, 6 cycles to $2,500 lifetime maximum""")
    smoking_cessations: Optional[ExtractionField] = Field(None, description="""Extract the smoking cessation coverage for the Health Care Benefit. Return it in this format: "$[amount] lifetime maximum" or "Not included" Example Values: $300 lifetime maximum, Not included""")
    vaccines: Optional[ExtractionField] = Field(None, description="""Extract the vaccine coverage for the Health Care Benefit. Return it in this format: "[vaccine coverage]" Example Values: "Included - reasonable & customary maximum", "Included - nil deductible", "Not included" """)
    major_medical: Optional[ExtractionField] = Field(None, description="""Extract the major medical coverage for the Health Care Benefit. Return it in this format: "[percentage]%" Example Values: 100%""")
    annual_deductible: Optional[ExtractionField] = Field(None, description="""Extract the annual deductible amount for the Health Care Benefit. Return it in this format: "$[amount]" Example Values: $1,000, $2,000, None""")
    hospitalization: Optional[ExtractionField] = Field(None, description="""Extract the hospitalization coverage for the Health Care Benefit. Return it in this format: "[percentage]% - [deductible details] - [room type]" Example Values: 100% - Nil deductible - Semi-Private""")
    orthotic_shoes: Optional[ExtractionField] = Field(None, description="""Extract the orthotic shoes coverage for the Health Care Benefit. Return it in this format: "$[amount] per benefit year maximum" Example Values: $250 per benefit year maximum""")
    orthotic_inserts: Optional[ExtractionField] = Field(None, description="""Extract the orthotic inserts coverage for the Health Care Benefit. Return it in this format: "$[amount] per benefit year maximum" or "$[amount] every [number] years" Example Values: $175 per benefit year maximum, $400 every 3 years""")
    hearing_aids: Optional[ExtractionField] = Field(None, description="""Extract the hearing aids coverage for the Health Care Benefit. Return it in this format: "$[amount] every [number] years" Example Values: $500 every 5 years""")
    vision_care: Optional[ExtractionField] = Field(None, description="""Extract the vision care coverage for the Health Care Benefit. Return it in this format: "$[amount] per benefit year maximum" Example Values: $1,000 per benefit year maximum""")
    eye_exams: Optional[ExtractionField] = Field(None, description="""Extract the eye exams coverage for the Health Care Benefit. Return it in this format: "$[amount] per benefit year maximum" Example Values: $100 per benefit year maximum""")
    paramedical_practitioners: Optional[ExtractionField] = Field(None, description="""Extract the paramedical practitioners coverage for the Health Care Benefit. Return it in this format: "[percentage]% - $[amount] per practitioner per benefit year maximum" Example Values: 100% - $500 per practitioner per benefit year maximum""")
    included_specialists: Optional[ExtractionField] = Field(None, description="""Extract the list of covered specialists under the Health Care Benefit. Return it in this format: "[specialist1], [specialist2], [specialist3]" Example Values: Chiropractor, Physiotherapist, Massage Therapist""")
    out_of_country: Optional[ExtractionField] = Field(None, description="""Extract the out of country coverage for the Health Care Benefit. Return it in this format: "[percentage]% - [deductible details] - $[amount] lifetime maximum" Example Values: 100% - Nil deductible - $3,000,000 lifetime maximum""")
    maximum_duration: Optional[ExtractionField] = Field(None, description="""Extract the maximum duration of coverage for the Health Care Benefit. Return it in this format: "[number] days" or "[number] months" Example Values: 30 days, 6 months""")
    trip_cancellation: Optional[ExtractionField] = Field(None, description="""Extract the trip cancellation coverage for the Health Care Benefit. Return it in this format: "$[amount] per trip" Example Values: $5,000 per trip""")
    private_duty_nursing: Optional[ExtractionField] = Field(None, description="""Extract the private duty nursing coverage for the Health Care Benefit. Return it in this format: "$[amount] per benefit year maximum" Example Values: $10,000 per benefit year maximum""")
    survivor_benefit: Optional[ExtractionField] = Field(None, description="""Extract the survivor benefit duration for the Health Care Benefit. Return it in this format: "[number] months" Example Values: 3 months""")
    termination_age: Optional[ExtractionField] = Field(None, description="""Extract the age at which coverage terminates for the Health Care Benefit. Return it in this format: "[age]" Example Values: 65""")

class DentalCare(BaseModel):
    annual_deductible: Optional[ExtractionField] = Field(
        None,
        description="""Extract the annual deductible amount for the Dental Care Benefit. Return it in this format: "$[amount] Single; $[amount] Family" or "None"
Example Values: $25 Single; $50 Family, None"""
    )
    basic_and_preventative: Optional[ExtractionField] = Field(
        None,
        description="""Extract the basic & preventative services coverage for the Dental Care Benefit. Return it in this format: "[percentage]% up to $[amount] per year"
Example Values: 100% up to $1,500 per year, 80% up to $1,000 per year"""
    )
    periodontic_and_endodontic: Optional[ExtractionField] = Field(
        None,
        description="""Extract the periodontic & endodontic coverage for the Dental Care Benefit. Return it in this format: "[percentage]% up to $[amount] per year"
Example Values: 100% up to $1,500 per year, 80% up to $1,000 per year"""
    )
    annual_maximum: Optional[ExtractionField] = Field(
        None,
        description="""Extract the annual maximum coverage for the Dental Care Benefit. Return it in this format: "$[amount] per year"
Example Values: $1,500 per year, $2,000 per year"""
    )
    major_restorative_services: Optional[ExtractionField] = Field(
        None,
        description="""Extract the major restorative services coverage for the Dental Care Benefit. Return it in this format: "[percentage]% up to $[amount] per year"
Example Values: 50% up to $1,500 per year, 60% up to $2,000 per year"""
    )
    orthodontic_services: Optional[ExtractionField] = Field(
        None,
        description="""Extract the orthodontic services coverage for the Dental Care Benefit. Return it in this format: "[percentage]% up to $[amount] lifetime maximum"
Example Values: 50% up to $2,000 lifetime maximum, 60% up to $1,500 lifetime maximum"""
    )
    lifetime_maximum: Optional[ExtractionField] = Field(
        None,
        description="""Extract the lifetime maximum coverage for the Dental Care Benefit. Return it in this format: "$[amount] lifetime maximum"
Example Values: $2,000 lifetime maximum, $1,500 lifetime maximum"""
    )
    recall_frequency: Optional[ExtractionField] = Field(
        None,
        description="""Extract the recall examination frequency for the Dental Care Benefit. Return it in this format: "Every [number] months"
Example Values: Every 6 months, Every 9 months"""
    )
    scaling_and_rooting_units: Optional[ExtractionField] = Field(
        None,
        description="""Extract the scaling and root planing units coverage for the Dental Care Benefit. Return it in this format: "[number] units per year"
Example Values: 8 units per year, 10 units per year"""
    )
    white_filings: Optional[ExtractionField] = Field(
        None,
        description="""Extract the white fillings coverage for the Dental Care Benefit. Return it in this format: "[percentage]% to [tooth/teeth] or [surface]"
Example Values: 100% to all teeth, 100% to premolars and anterior teeth only"""
    )
    fee_guide: Optional[ExtractionField] = Field(
        None,
        description="""Extract the dental fee guide used for the Dental Care Benefit. Return it in this format: "[province] [year] fee guide"
Example Values: Ontario 2023 fee guide, Alberta 2022 fee guide"""
    )
    survivor_benefit: Optional[ExtractionField] = Field(
        None,
        description="""Extract the survivor benefit duration for the Dental Care Benefit. Return it in this format: "[number] months"
Example Values: 6 months, 12 months"""
    )
    termination_age: Optional[ExtractionField] = Field(
        None,
        description="""Extract the age at which coverage terminates for the Dental Care Benefit. Return it in this format: "[age]"
Example Values: 70, 75"""
    )

class NotesAndDefinitions(BaseModel):
    dependent_child_definition: Optional[ExtractionField] = Field(
        None,
        description='Extract the definition of dependent child. Example: "Under age 21, or 25 if in full-time studies."'
    )
    benefit_year: Optional[ExtractionField] = Field(
        None,
        description='Extract the definition of the benefit year. Example: "Equals Calendar Year."'
    )
    second_medical_opinion: Optional[ExtractionField] = Field(
        None,
        description='Extract details about second medical opinion services. Example: "WorldCare Second Opinion included."'
    )
    eap: Optional[ExtractionField] = Field(
        None,
        description='Extract details about the Employee Assistance Program. Example: "Employee Assistance Program included."'
    )
    digital_wellness_program: Optional[ExtractionField] = Field(
        None,
        description='Extract details about the digital wellness program. Example: "Digital Wellness Program included."'
    )
    virtual_healthcare_services: Optional[ExtractionField] = Field(
        None,
        description='Extract details about virtual healthcare services. Example: "Maple Virtual Care included."'
    )

class InsuranceSummary(BaseModel):
    life_insurance_ad_d: Optional[LifeInsuranceADD] = Field(None, description="Life Insurance")
    dependent_life: Optional[DependentLife] = Field(None, description="Dependent Life Insurance coverage")
    critical_illness: Optional[CriticalIllness] = Field(None, description="Critical Illness coverage")
    long_term_disability: Optional[LongTermDisability] = Field(None, description="Long Term Disability coverage")
    short_term_disability: Optional[ShortTermDisability] = Field(None, description="Short Term Disability coverage")
    health_care: Optional[HealthCare] = Field(None, description="Health Care coverage")
    dental_care: Optional[DentalCare] = Field(None, description="Dental Care coverage")
    notes_and_definitions: Optional[NotesAndDefinitions] = Field(None, description="Additional notes and definitions") 