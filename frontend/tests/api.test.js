import test from 'node:test';
import assert from 'node:assert/strict';
import {api, unwrapResponse} from '../src/services/api.js';
import {predictImage, validateImage} from '../src/services/imageService.js';
import {weatherService} from '../src/services/weatherService.js';

test('unwraps existing envelopes while preserving top-level image responses', () => {
  assert.deepEqual(unwrapResponse({data:{success:true,data:{id:'animal'}}}).data, {id:'animal'});
  const image = {success:true,prediction:{class:'healthy'},probabilities:{healthy:1}};
  assert.equal(unwrapResponse({data:image}).data, image);
});

test('validates image selection, MIME and size', () => {
  for (const type of ['image/jpeg','image/png','image/webp']) validateImage({size:100,type});
  for (const file of [null, {size:0,type:'image/png'}, {size:1,type:'text/plain'}, {size:10485761,type:'image/png'}]) {
    assert.throws(() => validateImage(file));
  }
});

test('image request sends multipart file and preserves response', async () => {
  globalThis.sessionStorage = {getItem: () => 'test-token'};
  api.defaults.baseURL = 'http://localhost:8000/api/v1';
  api.defaults.adapter = async config => {
    assert.equal(config.url, '/predict/image');
    assert.equal(config.method, 'post');
    assert.equal(config.headers.Authorization, 'Bearer test-token');
    assert.ok(config.data instanceof FormData);
    assert.equal(config.data.get('file').name, 'cow.png');
    return {data:{success:true,prediction:{class:'healthy'}},status:200,headers:{},config};
  };
  const result = await predictImage(new File(['test'], 'cow.png', {type:'image/png'}));
  assert.equal(result.prediction.class, 'healthy');
});

test('safe backend error is shown to the caller', async () => {
  api.defaults.adapter = async () => { throw {response:{data:{error:{message:'Image classification service is temporarily unavailable.'}}}}; };
  await assert.rejects(predictImage(new File(['test'], 'cow.png', {type:'image/png'})), /temporarily unavailable/);
});

test('district-only weather configuration does not send an invalid API request', async () => {
  api.defaults.adapter = () => { throw new Error('Must not request weather without coordinates and dates'); };
  assert.equal(await weatherService.get({district:'Pune'}), null);
});
