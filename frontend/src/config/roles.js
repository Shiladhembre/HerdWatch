export const roles = {farmer:'Farmer / Livestock Owner',field:'Field Worker / Para-Vet',vet:'Veterinarian',officer:'District / Government Officer'};
export const permissions = {
  farmer:['dashboard','report-case','symptom-checker','outbreak-map','risk-analysis','animals','cases','vaccination','alerts','settings'],
  field:['dashboard','report-case','symptom-checker','outbreak-map','risk-analysis','animals','cases','vaccination','laboratory','alerts','settings'],
  vet:['dashboard','report-case','symptom-checker','outbreak-map','risk-analysis','animals','cases','vaccination','laboratory','alerts','analytics','settings'],
  officer:['dashboard','outbreak-map','risk-analysis','animals','cases','vaccination','laboratory','alerts','analytics','settings']
};
export const canReview = role => ['vet','officer'].includes(role);
export const canRecord = role => ['vet','field'].includes(role);
