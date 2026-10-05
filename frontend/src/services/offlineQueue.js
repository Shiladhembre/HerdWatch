import {readStore,writeStore} from '../utils/storage';
const key='hw-offline-queue';
export const queue={list:()=>readStore(key,[]),add:(payload,ownerId,mode)=>{const item={id:crypto.randomUUID(),ownerId,mode,payload,createdAt:new Date().toISOString()};writeStore(key,[...queue.list(),item]);return item;},remove:id=>writeStore(key,queue.list().filter(i=>i.id!==id))};
let running=false;
export async function syncQueue(ownerId,mode,submit){
 if(running)return {synced:0}; running=true; let synced=0;
 try{for(const item of queue.list().filter(i=>i.ownerId===ownerId&&i.mode===mode)){await submit(item.payload,item.id);queue.remove(item.id);synced++;}return {synced};}finally{running=false;}
}
