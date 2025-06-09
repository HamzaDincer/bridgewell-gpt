from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    page: int

class ExtractionField(BaseModel):
    value: str
    page: int
    coordinates: Optional[BoundingBox] = None
    source_snippet: Optional[str] = None
    
    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True
    )

class LifeInsuranceADD(BaseModel):
    schedule: Optional[ExtractionField] = Field(None, description="""Extract the insurance amount for the Life Insurance Benefit. 
                                    Return the response in this format: Flat $[amount] (e.g., Flat $20,000) or $[multiplier] of Annual Salary  $[maximum amount] 
                                    Examples: Flat $20,000, 2x Annual Salary to maximum $500,000""")
    reduction: Optional[ExtractionField] = Field(None, description="""Extract the age-based reduction clause for the Life Insurance Benefit. Return it in this format: "Reduces by [percentage]% at age [age], further reduces to [amount] or [percentage]% at [age]" Examples: Reduces by 65% at age 65, Reduces by 65% at age 65, further reduces to 10,000$ at age 71""")
    non_evidence_maximum: Optional[ExtractionField] = Field(None, description="""Extract the maximum amount that does not require medical evidence (No-Evidence Maximum). Return it as a dollar value in this format: $[amount] (e.g., $25,000, $50,000) Examples: $25,000, $50,000""")
    termination_age: Optional[ExtractionField] = Field(None, description="""Extract the age at which Life Insurance coverage terminates. Return it in this format: "[age]" Examples: 65, 70, 75""")

class DependentLife(BaseModel):
    schedule: Optional[ExtractionField] = Field(None, description="""Extract the insurance amount for spouse and children in the Dependent Life Benefit. Return the response in this format: $[amount] Spouse; $[amount] per Child Examples: $100,000 Spouse; $50,000 per Child""")
    termination_age: Optional[ExtractionField] = Field(None, description="""Extract the age at which Dependent Life coverage terminates. Return it in this format: "[age]" Examples: 65, 70, 75""")
                         
class CriticalIllness(BaseModel):
    schedule: Optional[ExtractionField] = Field(None, description="""Extract the insurance amount for the Life Insurance Benefit. Return the response in this format: Flat $[amount] (e.g., Flat $20,000) or $[multiplier] of Annual Salary to $[maximum amount] Examples: Flat $20,000, 2x Annual Salary to maximum $500,000""")
    impairments: Optional[ExtractionField] = Field(None, description="""Extract the covered impairments/conditions for the Critical Illness Benefit. Return it in this format: "[number] illnesses included: [illness]" Examples: 25 illnesses included: Aortic Surgery, Aplastic Anemia, Bacterial Meningitis, Benign Brain Tumour, Blindness, Cancer...""")
    termination_age: Optional[ExtractionField] = Field(None, description="""Extract the age at which Critical Illness coverage terminates. Return it in this format: "[age]" Examples: 65, 70, 75""")

class LongTermDisability(BaseModel):
    schedule: Optional[ExtractionField] = Field(None, description="""Extract the insurance amount for the Long Term Disability Benefit. Return the response in this format: %[percentage] of monthly earnings Examples: 75% of monthly earnings 66% of monthly earnings""")
    monthly_maximum: Optional[ExtractionField] = Field(None, description="""Extract the maximum monthly benefit amount for the Long Term Disability Benefit. Return it in this format: "$[amount]" Examples: $10,000, $20,000""")
    tax_status: Optional[ExtractionField] = Field(None, description="""Extract the tax status of the Long Term Disability Benefit. Return it in this format: "[tax status]" Examples: Taxable, Non-Taxable""")
    elimination_period: Optional[ExtractionField] = Field(None, description="""Extract the elimination period before benefits begin for the Long Term Disability Benefit. Return it in this format: "[number] days" Examples: 180 days, 119 days""")
    benefit_period: Optional[ExtractionField] = Field(None, description="""Extract the maximum period for which benefits will be paid for the Long Term Disability Benefit. Return it in this format: "to age [age]" Examples: to age 65, to age 70""")
    definition: Optional[ExtractionField] = Field(None, description="Definition of disability used")
    offsets: Optional[ExtractionField] = Field(None, description="""Extract the income/benefit offsets that reduce LTD benefit. Return it in this format: "[offsets]" Examples: Primary, Primary Direct, Family Indirect""")
    cost_of_living_adjustment: Optional[ExtractionField] = Field(None, description="""Extract the cost of living adjustment for the Long Term Disability Benefit. Return it in this format: "[cost of living adjustment]" Examples: 2%, Consumer Price index or 2%, whichever is less""")
    pre_existing: Optional[ExtractionField] = Field(None, description="""Extract the pre-existing condition limitations for the Long Term Disability Benefit. Return it in this format: "[number] months / [number] months" or "[number] weeks if treatment free; otherwise [number] months" Examples: 3 months / 12 months, 90 days / 12 months, 13 weeks if treatment free; otherwise 12 months""")
    survivor_benefit: Optional[ExtractionField] = Field(None, description="""Extract the survivor benefit details for the Long Term Disability Benefit. Return it in this format: "[survivor benefit details]" Examples: 3 months, 6 months, 1 year""")
    non_evidence_maximum: Optional[ExtractionField] = Field(None, description="""Extract the maximum amount without evidence for the Long Term Disability Benefit. Return it in this format: "$[amount]" Examples: $10,000, $20,000""")     
    termination_age: Optional[ExtractionField] = Field(None, description="""Extract the age at which coverage terminates for the Long Term Disability Benefit. Return it in this format: "[age]" Examples: 65, 70, 75""")

class ShortTermDisability(BaseModel):
    schedule: Optional[ExtractionField] = Field(None, description="""Extract the schedule of benefits for the Short Term Disability Benefit. Return it in this format: "[percentage]% of weekly earnings" Examples: 100% of weekly earnings, 80% of weekly earnings""")
    weekly_maximum: Optional[ExtractionField] = Field(None, description="""Extract the maximum weekly benefit amount for the Short Term Disability Benefit. Return it in this format: "$[amount]" Examples: $1,000, $2,000""")
    tax_status: Optional[ExtractionField] = Field(None, description="""Extract the tax status of the Short Term Disability Benefit. Return it in this format: "[tax status]" Examples: Taxable, Non-Taxable""")
    elimination_period: Optional[ExtractionField] = Field(None, description="""Extract the elimination period before benefits begin for the Short Term Disability Benefit. Return it in this format: "[number]st day accident & hospital; [number]th day sickness" Examples: 1st day accident & hospital; 8th day sickness""")
    benefit_period: Optional[ExtractionField] = Field(None, description="""Extract the maximum period for which benefits will be paid for the Short Term Disability Benefit. Return it in this format: "[number] weeks" Examples: 17 weeks, 26 weeks""")
    non_evidence_maximum: Optional[ExtractionField] = Field(None, description="""Extract the maximum amount without evidence for the Short Term Disability Benefit. Return it in this format: "$[amount]" Examples: $1,000, $2,000""")
    termination_age: Optional[ExtractionField] = Field(None, description="""Extract the age at which coverage terminates for the Short Term Disability Benefit. Return it in this format: "[age]" Examples: 65, 70, 75""")

class HealthCare(BaseModel):
    prescription_drugs: Optional[ExtractionField] = Field(None, description="""Extract the prescription drug coverage details for the Health Care Benefit. Return it in this format: "[prescription drug coverage details]" Examples: 100% - Equal to dispensing fee deductible per prescription, 90% - Nil deductible - Drugs purchased at Costco, 100% - Nil deductible, 80% - Nil deductible""")
    pay_direct_drug_card: Optional[ExtractionField] = Field(None, description="""Extract the pay direct drug card availability for the Health Care Benefit. Return it in this format: "[pay direct drug card availability]" Examples: Included - Generic Mandatory, Included - Brand Name Mandatory""")
    maximum: Optional[ExtractionField] = Field(None, description="""Extract the overall maximum coverage for the Health Care Benefit. Return it in this format: "$[amount] or Unlimited" Examples: Unlimited, $10,000, $20,000""")
    fertility_drugs: Optional[ExtractionField] = Field(None, description="""Extract the fertility drug coverage for the Health Care Benefit. Return it in this format: "[fertility drug coverage]" Examples: $2,400 lifetime maximum, 6 cycles to $2,500 lifetime maximum""")
    smoking_cessations: Optional[ExtractionField] = Field(None, description="""Extract the smoking cessation coverage for the Health Care Benefit. Return it in this format: "[smoking cessation coverage] Examples: $300 lifetime maximum Not included""")
    vaccines: Optional[ExtractionField] = Field(None, description="""Extract the vaccine coverage for the Health Care Benefit. Return it in this format: "[vaccine coverage] Examples: Included - reasonable & customary maximum Included - nil deductible Not included""")
    major_medical: Optional[ExtractionField] = Field(None, description="""Extract the major medical coverage for the Health Care Benefit. Return it in this format: "[percentage]%" Examples: 100%""")
    annual_deductible: Optional[ExtractionField] = Field(None, description="""Extract the annual deductible amount for the Health Care Benefit. Return it in this format: "$[amount]" Examples: $1,000, $2,000, None""")
    hospitalization: Optional[ExtractionField] = Field(None, description="""Extract the hospitalization coverage for the Health Care Benefit. Return it in this format: "[hospitalization coverage] Examples: 100% - Nil deductible - Semi-Private""")
    orthotic_shoes: Optional[ExtractionField] = Field(None, description="""Extract the orthotic shoes coverage for the Health Care Benefit. Return it in this format: "[orthotic shoes coverage] Examples: $250 per benefit year maximum""")
    orthotic_inserts: Optional[ExtractionField] = Field(None, description="""Extract the orthotic inserts coverage for the Health Care Benefit. Return it in this format: "[orthotic inserts coverage] Examples: $175 per benefit year maximum $400 every 3 years""")
    hearing_aids: Optional[ExtractionField] = Field(None, description="""Extract the hearing aids coverage for the Health Care Benefit. Return it in this format: "[hearing aids coverage] Examples: $500 every 5 years""")
    vision_care: Optional[ExtractionField] = Field(None, description="""Extract the vision care coverage for the Health Care Benefit. Return it in this format: "[vision care coverage] Examples: $1,000 per benefit year maximum""")
    eye_exams: Optional[ExtractionField] = Field(None, description="""Extract the eye exams coverage for the Health Care Benefit. Return it in this format: "[eye exams coverage] Examples: $100 per benefit year maximum""")
    paramedical_practitioners: Optional[ExtractionField] = Field(None, description="""Extract the paramedical practitioners coverage for the Health Care Benefit. Return it in this format: "[paramedical practitioners coverage] Examples: 100% - $500 per practitioner per benefit year maximum""")
    included_specialists: Optional[List[ExtractionField]] = Field(None, description="""Extract the list of covered specialists for the Health Care Benefit. Return it in this format: "[list of covered specialists]""")
    out_of_country: Optional[ExtractionField] = Field(None, description="""Extract the out of country coverage for the Health Care Benefit. Return it in this format: "[out of country coverage] Examples: 100% - Nil deductible - $3,000,000 lifetime maximum""")
    maximum_duration: Optional[ExtractionField] = Field(None, description="Maximum duration of coverage")
    trip_cancellation: Optional[ExtractionField] = Field(None, description="""Extract the trip cancellation coverage for the Health Care Benefit. Return it in this format: "[trip cancellation coverage]""")
    private_duty_nursing: Optional[ExtractionField] = Field(None, description="""Extract the private duty nursing coverage for the Health Care Benefit. Return it in this format: "[private duty nursing coverage]""")
    survivor_benefit: Optional[ExtractionField] = Field(None, description="""Extract the survivor benefit duration for the Health Care Benefit. Return it in this format: "[survivor benefit duration]""")
    termination_age: Optional[ExtractionField] = Field(None, description="""Extract the age at which coverage terminates for the Health Care Benefit. Return it in this format: "[age]""")

class DentalCare(BaseModel):
    annual_deductible: Optional[ExtractionField] = Field(None, description="""Extract the annual deductible amount for the Dental Care Benefit. Return it in this format: "$[amount]" or "None" Examples: $25 Single; $50 per Family, None""")
    basic_and_preventative: Optional[ExtractionField] = Field(None, description="""Extract the basic and preventative services coverage for the Dental Care Benefit. Return it in this format: "[basic and preventative services coverage]""")
    periodontic_and_endodontic: Optional[ExtractionField] = Field(None, description="""Extract the periodontic and endodontic coverage for the Dental Care Benefit. Return it in this format: "[periodontic and endodontic coverage]""")
    annual_maximum: Optional[ExtractionField] = Field(None, description="""Extract the annual maximum coverage for the Dental Care Benefit. Return it in this format: "$[amount]""")
    major_restorative_services: Optional[ExtractionField] = Field(None, description="""Extract the major restorative services coverage for the Dental Care Benefit. Return it in this format: "[major restorative services coverage]""")
    orthodontic_services: Optional[ExtractionField] = Field(None, description="""Extract the orthodontic services coverage for the Dental Care Benefit. Return it in this format: "[orthodontic services coverage]""")
    lifetime_maximum: Optional[ExtractionField] = Field(None, description="""Extract the lifetime maximum coverage for the Dental Care Benefit. Return it in this format: "$[amount]""")
    recall_frequency: Optional[ExtractionField] = Field(None, description="""Extract the recall examination frequency for the Dental Care Benefit. Return it in this format: "[recall examination frequency]""")
    scaling_and_rooting_units: Optional[ExtractionField] = Field(None, description="""Extract the scaling and root planing units coverage for the Dental Care Benefit. Return it in this format: "[scaling and root planing units coverage]""")
    white_filings: Optional[ExtractionField] = Field(None, description="""Extract the white fillings coverage for the Dental Care Benefit. Return it in this format: "[white fillings coverage]""")
    fee_guide: Optional[ExtractionField] = Field(None, description="""Extract the dental fee guide used for the Dental Care Benefit. Return it in this format: "[dental fee guide used]""")
    survivor_benefit: Optional[ExtractionField] = Field(None, description="""Extract the survivor benefit duration for the Dental Care Benefit. Return it in this format: "[survivor benefit duration]""")
    termination_age: Optional[ExtractionField] = Field(None, description="""Extract the age at which coverage terminates for the Dental Care Benefit. Return it in this format: "[age]""")

class NotesAndDefinitions(BaseModel):
    dependent_child_definition: Optional[ExtractionField] = Field(None, description="Definition of dependent child")
    benefit_year: Optional[ExtractionField] = Field(None, description="Benefit year definition")
    second_medical_opinion: Optional[ExtractionField] = Field(None, description="Second medical opinion services")
    eap: Optional[ExtractionField] = Field(None, description="Employee Assistance Program details")
    digital_wellness_program: Optional[ExtractionField] = Field(None, description="Digital wellness program details")
    virtual_healthcare_services: Optional[ExtractionField] = Field(None, description="Virtual healthcare services")

class InsuranceSummary(BaseModel):
    life_insurance_ad_d: Optional[LifeInsuranceADD] = Field(None, description="Life Insurance")
    dependent_life: Optional[DependentLife] = Field(None, description="Dependent Life Insurance coverage")
    critical_illness: Optional[CriticalIllness] = Field(None, description="Critical Illness coverage")
    long_term_disability: Optional[LongTermDisability] = Field(None, description="Long Term Disability coverage")
    short_term_disability: Optional[ShortTermDisability] = Field(None, description="Short Term Disability coverage")
    health_care: Optional[HealthCare] = Field(None, description="Health Care coverage")
    dental_care: Optional[DentalCare] = Field(None, description="Dental Care coverage")
    notes_and_definitions: Optional[NotesAndDefinitions] = Field(None, description="Additional notes and definitions") 