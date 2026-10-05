import React from 'react';import {createRoot} from 'react-dom/client';import App from './App';import './styles.css';import {readStore} from './utils/storage';
const prefs=readStore('hw-preferences',{});document.documentElement.classList.toggle('large-text',!!prefs.largeText);document.documentElement.classList.toggle('reduce-motion',!!prefs.reduceMotion);document.documentElement.lang=readStore('hw-language','en');
createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>);
