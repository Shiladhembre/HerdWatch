import {createContext,useContext,useState} from 'react';
import en from '../locales/en.json'; import mr from '../locales/mr.json'; import hi from '../locales/hi.json';
import {readStore,writeStore} from '../utils/storage';
const Context=createContext(); const dictionaries={en,mr,hi};
export function LanguageProvider({children}){const[language,setLang]=useState(()=>readStore('hw-language','en'));const setLanguage=l=>{setLang(l);writeStore('hw-language',l);document.documentElement.lang=l;};return <Context.Provider value={{language,setLanguage,t:key=>dictionaries[language]?.[key]??en[key]??key}}>{children}</Context.Provider>;}
export const useLanguage=()=>useContext(Context);
