import {api} from './api';import {listAll,alertFromApi} from './contract';
export const alertService={list:params=>listAll('/alerts',alertFromApi,params),update:id=>api.patch(`/alerts/${encodeURIComponent(id)}/read`).then(r=>alertFromApi(r.data))};
