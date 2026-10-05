import {createContext,useContext,useState} from 'react';
import {DEMO_MODE} from '../services/api'; import {authService} from '../services/authService'; import {readStore,writeStore} from '../utils/storage';
const Context=createContext();
export function AuthProvider({children}){
 const[user,setUser]=useState(()=>{try{if(!DEMO_MODE&&!sessionStorage.getItem('hw-token'))return null;return JSON.parse(sessionStorage.getItem('hw-session'))||(DEMO_MODE?readStore('hw-session',null):null);}catch{return null;}});
 const login=async(form)=>{let result;if(DEMO_MODE){result={user:{id:'demo-'+form.role,name:form.name||({farmer:'Anil Patil',field:'Riya Deshmukh',vet:'Dr. Meera Joshi',officer:'Dr. Aditi Deshmukh'}[form.role]),role:form.role,email:form.email||form.identifier,district:form.district||'Pune'}};}else{result=await authService.login(form);sessionStorage.setItem('hw-token',result.access_token);}
 setUser(result.user);sessionStorage.setItem('hw-session',JSON.stringify(result.user));if(form.remember&&DEMO_MODE)writeStore('hw-session',result.user);else localStorage.removeItem('hw-session');return result.user;};
 const logout=async()=>{if(!DEMO_MODE)await authService.logout();setUser(null);sessionStorage.removeItem('hw-session');sessionStorage.removeItem('hw-token');sessionStorage.removeItem('hw-refresh');localStorage.removeItem('hw-session');};
 const updateProfile=data=>{const next={...user,...data};setUser(next);sessionStorage.setItem('hw-session',JSON.stringify(next));if(localStorage.getItem('hw-session'))writeStore('hw-session',next);};
 return <Context.Provider value={{user,login,logout,updateProfile}}>{children}</Context.Provider>;
}
export const useAuth=()=>useContext(Context);
