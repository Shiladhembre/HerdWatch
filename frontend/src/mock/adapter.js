import * as seed from './demoData';
import {readStore,writeStore} from '../utils/storage';
const key='hw-demo-v1';
const initial=()=>({cases:seed.cases,animals:seed.animals,vaccinations:seed.vaccinations,labs:seed.labs,alerts:seed.alerts,trend:seed.trend,weather:seed.weather,facilities:seed.facilities});
export const demoAdapter={
 load:()=>readStore(key,initial()),
 save:data=>writeStore(key,data),
 reset:()=>{writeStore(key,initial());return initial();},
 assessment:()=>({disease:'Foot and Mouth Disease',risk:'High',priority:'Urgent',recommendation:'Contact the nearest veterinary officer for clinical assessment.',demo:true,selectedSymptoms:[],reasons:[]}),
 risk:()=>({risk:'Medium',demo:true,reasons:[],message:'Static demonstration output. No risk model has been run.'})
};
