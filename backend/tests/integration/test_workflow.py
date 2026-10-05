from datetime import date,datetime,timezone
from uuid import uuid4
import pytest
from .conftest import login

pytestmark=pytest.mark.integration

async def test_registration_role_escalation_and_session(client):
    payload={'full_name':'Test Farmer','email':f'{uuid4().hex}@example.com','mobile':f'+91{str(uuid4().int)[:10]}','password':'Secure-test-password-1','state':'Maharashtra','district':'Pune','village':'Test Village'}
    denied=await client.post('/api/v1/auth/register',json={**payload,'role':'ADMIN'})
    assert denied.status_code==403
    created=await client.post('/api/v1/auth/register',json=payload);assert created.status_code==201,created.text
    logged=await client.post('/api/v1/auth/login',json={'identifier':payload['email'],'password':payload['password']});assert logged.status_code==200
    token=logged.json()['data'];headers={'Authorization':'Bearer '+token['access_token']}
    assert (await client.get('/api/v1/auth/me',headers=headers)).status_code==200
    refreshed=await client.post('/api/v1/auth/refresh',json={'refresh_token':token['refresh_token']});assert refreshed.status_code==200
    assert (await client.post('/api/v1/auth/refresh',json={'refresh_token':token['refresh_token']})).status_code==401
    new=refreshed.json()['data'];headers={'Authorization':'Bearer '+new['access_token']}
    assert (await client.post('/api/v1/auth/logout',headers=headers,json={'refresh_token':new['refresh_token']})).status_code==200
    assert (await client.get('/api/v1/auth/me',headers=headers)).status_code==401

async def test_full_scoped_lifecycle(client,users):
    farmer,_=await login(client,users['FARMER']);vet,_=await login(client,users['VETERINARIAN']);officer,_=await login(client,users['DISTRICT_OFFICER']);other,_=await login(client,users['OTHER'])
    animal_payload={'animal_tag':'TEST-'+uuid4().hex,'species':'Cattle','state':'Maharashtra','district':'Pune','village':'Test Village','latitude':18.5,'longitude':73.8}
    result=await client.post('/api/v1/animals',headers=farmer,json=animal_payload);assert result.status_code==201,result.text
    animal=result.json()['data']['id']
    assert (await client.get(f'/api/v1/animals/{animal}',headers=other)).status_code==404
    case_payload={'animal_id':animal,'species':'Cattle','state':'Maharashtra','district':'Pune','village':'Test Village','latitude':18.5,'longitude':73.8,'symptom_started_on':str(date.today()),'affected_count':1,'death_count':0,'observed_symptoms':'Observed sign for testing','severity':'URGENT','symptoms':{'G01':1}}
    key=str(uuid4());headers={**farmer,'Idempotency-Key':key}
    result=await client.post('/api/v1/cases',headers=headers,json=case_payload);assert result.status_code==201,result.text
    case=result.json()['data']['id']
    duplicate=await client.post('/api/v1/cases',headers=headers,json=case_payload)
    assert duplicate.json()['data']['duplicate'] is True and duplicate.json()['data']['id']==case
    conflict=await client.post('/api/v1/cases',headers=headers,json={**case_payload,'notes':'changed'})
    assert conflict.status_code==409
    assert (await client.patch(f'/api/v1/cases/{case}',headers=farmer,json={'status':'CONFIRMED','clinical_assessment':'Test evidence'})).status_code==403
    assert (await client.get(f'/api/v1/cases/{case}',headers=other)).status_code==404
    assert (await client.patch(f'/api/v1/cases/{case}',headers=vet,json={'status':'UNDER_REVIEW'})).status_code==200
    assert (await client.post(f'/api/v1/cases/{case}/escalate',headers=vet,json={'notes':'Test escalation for review'})).status_code==200
    missing=await client.post('/api/v1/predict/disease',headers=farmer,json={'case_id':case,'symptoms':{f'G{i:02}':0 for i in range(1,19)}})
    assert missing.status_code==503 and missing.json()['error']['code']=='MODEL_NOT_AVAILABLE'
    vaccine={'animal_id':animal,'vaccine_name':'Test record','disease_target':'Test target','dose_number':1,'administered_on':str(date.today())}
    assert (await client.post('/api/v1/vaccinations',headers=farmer,json=vaccine)).status_code==403
    assert (await client.post('/api/v1/vaccinations',headers=vet,json=vaccine)).status_code==201
    referral=await client.post('/api/v1/labs/referral',headers=vet,json={'case_id':case,'sample_type':'Test sample','laboratory_name':'Test laboratory'})
    assert referral.status_code==201,referral.text
    lab=referral.json()['data']['id']
    for status in ['COLLECTED','IN_TRANSIT','RECEIVED','TESTING']:
        response=await client.patch(f'/api/v1/labs/{lab}/status',headers=vet,json={'status':status,'collection_date':str(date.today())})
        assert response.status_code==200,response.text
    result_payload={'result':'Test-only laboratory entry, no clinical interpretation.','result_date':str(date.today())};result_headers={**vet,'Idempotency-Key':str(uuid4())}
    assert (await client.post(f'/api/v1/labs/{lab}/result',headers={**farmer,'Idempotency-Key':str(uuid4())},json=result_payload)).status_code==403
    assert (await client.post(f'/api/v1/labs/{lab}/result',headers=result_headers,json=result_payload)).status_code==200
    assert (await client.post(f'/api/v1/labs/{lab}/result',headers=result_headers,json=result_payload)).status_code==200
    updated=(await client.get(f'/api/v1/cases/{case}',headers=farmer)).json()['data'];assert updated['status']=='UNDER_REVIEW'
    assert (await client.get('/api/v1/alerts',headers=farmer)).json()['data']['total']>=1
    dashboard=await client.get('/api/v1/analytics/dashboard',headers=officer);assert dashboard.status_code==200,dashboard.text
    assert dashboard.json()['data']['summary']['active_cases']>=1
    geo=(await client.get('/api/v1/outbreaks/map',headers=officer)).json()['data']
    assert geo['type']=='FeatureCollection' and geo['features']
    assert 'owner_id' not in geo['features'][0]['properties'] and 'reporter_id' not in geo['features'][0]['properties']
    assert (await client.patch(f'/api/v1/cases/{case}',headers=vet,json={'status':'RESOLVED'})).status_code==200
    assert (await client.post(f'/api/v1/cases/{case}/close',headers=vet,json={'notes':'Test case closure'})).status_code==200

async def test_offline_sync_duplicate_and_invalid_input(client,users):
    farmer,_=await login(client,users['FARMER'])
    a=await client.post('/api/v1/animals',headers=farmer,json={'animal_tag':'SYNC-'+uuid4().hex,'species':'Cattle','state':'Maharashtra','district':'Pune','village':'Test Village'})
    animal=a.json()['data']['id']
    record={'client_record_id':str(uuid4()),'created_offline_at':datetime.now(timezone.utc).isoformat(),'payload':{'animal_id':animal,'species':'Cattle','state':'Maharashtra','district':'Pune','village':'Test Village','symptom_started_on':str(date.today()),'affected_count':1}}
    one=await client.post('/api/v1/sync',headers=farmer,json={'records':[record]});assert one.status_code==200,one.text
    two=await client.post('/api/v1/sync',headers=farmer,json={'records':[record]})
    assert one.json()['data'][0]['status']=='synced' and two.json()['data'][0]['status']=='duplicate'
    bad=await client.post('/api/v1/cases',headers=farmer,json={**record['payload'],'death_count':2})
    assert bad.status_code==422

async def test_unauthorized_cors_and_model_not_ready(client,users):
    assert (await client.get('/api/v1/cases')).status_code==401
    vet,_=await login(client,users['VETERINARIAN'])
    now=datetime.now(timezone.utc).isoformat()
    result=await client.post('/api/v1/predict/outbreak-risk',headers=vet,json={'prediction_cutoff':now,'features':{'temperature':20},'observed_at':{'temperature':now}})
    assert result.status_code==503 and result.json()['error']['code']=='MODEL_NOT_AVAILABLE'
    options=await client.options('/api/v1/cases',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'GET'})
    assert options.headers['access-control-allow-origin']=='http://localhost:5173'
    disallowed=await client.options('/api/v1/cases',headers={'Origin':'https://untrusted.example','Access-Control-Request-Method':'GET'})
    assert 'access-control-allow-origin' not in disallowed.headers
