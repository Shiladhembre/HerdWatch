from datetime import date,timedelta,datetime,timezone
from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.schemas.case import CaseCreate
from app.schemas.prediction import DiseaseInput,RiskInput
from app.schemas.vaccination import VaccinationCreate
from app.ml.feature_validation import symptom_vector,risk_vector
from app.ml.metadata import ModelContract
from app.core.exceptions import FeatureMismatch
from app.core.symptom_config import FEATURE_CODES

def case_payload():
    return dict(animal_id=uuid4(),species='Cattle',state='Maharashtra',district='Pune',village='Test village',symptom_started_on=date.today(),affected_count=1,death_count=0)

@pytest.mark.parametrize('changes',[{'death_count':2},{'affected_count':-1},{'herd_id':uuid4()},{'animal_id':None},{'latitude':91,'longitude':70},{'latitude':18},{'affected_count':True},{'symptom_started_on':date.today()+timedelta(days=1)},{'symptoms':{'G01':True}},{'symptoms':{'G19':1}}])
def test_invalid_case(changes):
    with pytest.raises(ValidationError): CaseCreate(**{**case_payload(),**changes})

def test_features_exact_binary_and_ordered():
    features={key:i%2 for i,key in enumerate(FEATURE_CODES)}
    DiseaseInput(symptoms=features)
    assert symptom_vector(features,list(reversed(FEATURE_CODES)))==[features[k] for k in reversed(FEATURE_CODES)]
    with pytest.raises(ValidationError): DiseaseInput(symptoms={**features,'G19':0})
    with pytest.raises(ValidationError): DiseaseInput(symptoms={**features,'G01':True})
    with pytest.raises(ValidationError): DiseaseInput(symptoms={**features,'G01':'1'})

def test_risk_cutoff_and_leakage_contract():
    now=datetime.now(timezone.utc)
    metadata=ModelContract(name='test',version='1',features=['temperature'],pre_outbreak_features=['temperature'],feature_types={'temperature':'number'})
    payload=RiskInput(prediction_cutoff=now,features={'temperature':24},observed_at={'temperature':now-timedelta(days=1)})
    assert risk_vector(payload,metadata)==[24]
    with pytest.raises(FeatureMismatch): risk_vector(payload.model_copy(update={'observed_at':{'temperature':now+timedelta(seconds=1)}}),metadata)
    leak=ModelContract(name='test',version='1',features=['deaths'],pre_outbreak_features=['deaths'],feature_types={'deaths':'number'})
    with pytest.raises(FeatureMismatch): risk_vector(payload.model_copy(update={'features':{'deaths':2},'observed_at':{'deaths':now}}),leak)

def test_vaccine_dates():
    with pytest.raises(ValidationError): VaccinationCreate(animal_id=uuid4(),vaccine_name='Recorded vaccine',disease_target='Recorded target',dose_number=1,administered_on=date.today(),next_due_on=date.today()-timedelta(days=1))
