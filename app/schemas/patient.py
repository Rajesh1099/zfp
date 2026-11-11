from pydantic import BaseModel

class PatientResponse(BaseModel):
    patient_id: str
    name: str
    sex: str
