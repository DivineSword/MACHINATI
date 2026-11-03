import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { LegalPage } from './pages/LegalPages';
import './style.css';

const path = window.location.pathname.replace(/\/+$/, '') || '/';
createRoot(document.getElementById('root')!).render(
  <React.StrictMode>{path === '/' ? <App /> : <LegalPage path={path} />}</React.StrictMode>,
);
