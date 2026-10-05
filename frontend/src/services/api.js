import axios from 'axios';
const env = import.meta.env ?? {};
export const DEMO_MODE = env.VITE_DEMO_MODE !== 'false';
export const api = axios.create({baseURL:env.VITE_API_BASE_URL,timeout:15000,headers:{'Content-Type':'application/json'}});
api.interceptors.request.use(config => {
  if (!config.baseURL) throw new Error('Set VITE_API_BASE_URL before using live mode.');
  const token = sessionStorage.getItem('hw-token') || (DEMO_MODE ? 'demo-token' : null);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
export function unwrapResponse(response) {
  if (response.data?.success === true && Object.hasOwn(response.data, 'data')) response.data = response.data.data;
  return response;
}
api.interceptors.response.use(unwrapResponse, e => {const detail=e.response?.data?.error;const fields=detail?.details?.map(d=>`${d.location?.slice(1).join('.')}: ${d.message}`).join('; ');return Promise.reject(new Error(fields||detail?.message||(typeof e.response?.data?.detail==='string'?e.response.data.detail:e.message)||'Unable to reach the service. Please retry.'));});
