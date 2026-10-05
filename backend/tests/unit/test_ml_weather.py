from datetime import date
from types import SimpleNamespace
import httpx
import pytest
from app.ml.model_loader import ModelSlot,ModelRegistry
from app.ml.symptom_predictor import predict
from app.ml.outbreak_predictor import predict as outbreak_predict
from app.ml.metadata import ModelContract
from app.core.exceptions import ModelUnavailable,DomainError
from app.core.symptom_config import FEATURE_CODES
from app.integrations.nasa_power import parse_weather,fetch

class FakeModel:
    """Test double only; never deployed as an ML artifact."""
    def predict(self,frame):
        assert list(frame.columns)==FEATURE_CODES
        return ['Test class']

def test_missing_models_never_fabricate():
    with pytest.raises(ModelUnavailable): predict(ModelSlot(),dict.fromkeys(FEATURE_CODES,0))
    with pytest.raises(ModelUnavailable): outbreak_predict(ModelSlot(),None)

def test_prediction_has_no_invented_confidence():
    slot=ModelSlot(model=FakeModel(),contract=ModelContract(name='unit-test-double',version='test',features=FEATURE_CODES,classes=['Test class']),status='loaded')
    label,confidence=predict(slot,dict.fromkeys(FEATURE_CODES,0))
    assert label=='Test class' and confidence is None

def test_corrupt_artifact_fails_safely(tmp_path,monkeypatch):
    artifact=tmp_path/'model.pkl';artifact.write_bytes(b'not a pickle')
    config=SimpleNamespace(model_metadata_path=tmp_path/'missing.json',symptom_model_path=artifact,outbreak_model_path=tmp_path/'absent.pkl',trust_model_artifacts=True)
    monkeypatch.setattr('app.ml.model_loader.get_settings',lambda:config)
    registry=ModelRegistry();registry.load()
    assert registry.symptom.status=='invalid_artifact' and registry.outbreak.status=='not_configured'

def test_weather_missing_values():
    result=parse_weather({'properties':{'parameter':{'T2M':{'20260101':25,'20260102':-999}}}},['T2M','RH2M'])
    assert result['T2M']['20260102'] is None and result['RH2M'] is None
    with pytest.raises(DomainError): parse_weather({'properties':{'parameter':{}}},['T2M'])

async def test_nasa_http_is_mocked():
    def response(request):
        assert request.url.params['community']=='AG'
        return httpx.Response(200,json={'properties':{'parameter':{'T2M':{'20260101':22}}}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(response)) as client:
        result=await fetch(18.5,73.8,date(2026,1,1),date(2026,1,1),['T2M'],client)
    assert result['parameters']['T2M']['20260101']==22
