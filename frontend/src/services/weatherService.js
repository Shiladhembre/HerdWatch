import {api} from './api.js';
export const weatherService = {get: async params => {
  // A district name is not a coordinate. Do not invent a weather location.
  if (params.latitude == null || params.longitude == null || !params.start_date || !params.end_date) return null;
  return (await api.get('/weather', {params})).data;
}};
