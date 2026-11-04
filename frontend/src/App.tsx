import { useEffect, useState } from 'react';
import {
  Tractor,
  CalendarDays,
  Users,
} from 'lucide-react';
import { RequestsDashboard } from './pages/RequestsDashboard';
import { apiBaseUrl } from './shared/api';
import './operations.css';

type IntegratedView = 'catalogue' | 'cooperative' | 'operations';
type OperationsSection = 'requests' | 'overview';

const integratedPages: Record<Exclude<IntegratedView, 'operations'>, { title: string; source: string }> = {
  catalogue: { title: 'Catalogue Machinati', source: '/catalogue.html' },
  cooperative: { title: 'Espace coopérative', source: '/cooperative.html' },
};
const operationsPage = { title: 'Équipe opérations', source: '/equipe-machinati.html' };

function viewFromLocation(): IntegratedView {
  const requestedView = new URLSearchParams(window.location.search).get('view');
  if (requestedView === 'requests' || requestedView === 'operations') return 'operations';
  if (requestedView === 'cooperative') return 'cooperative';
  return 'catalogue';
}

function operationsSectionFromLocation(): OperationsSection {
  const params = new URLSearchParams(window.location.search);
  return params.get('view') === 'requests' || params.get('section') !== 'overview' ? 'requests' : 'overview';
}

export function App() {
  const [view, setView] = useState<IntegratedView>(viewFromLocation);
  const [operationsSection, setOperationsSection] = useState<OperationsSection>(operationsSectionFromLocation);

  useEffect(() => {
    const syncView = () => {
      setView(viewFromLocation());
      setOperationsSection(operationsSectionFromLocation());
    };
    window.addEventListener('popstate', syncView);
    return () => window.removeEventListener('popstate', syncView);
  }, []);

  function navigate(nextView: IntegratedView) {
    const url = new URL(window.location.href);
    if (nextView === 'catalogue') {
      url.searchParams.delete('view');
      url.searchParams.delete('section');
    } else {
      url.searchParams.set('view', nextView);
      if (nextView === 'operations') url.searchParams.set('section', 'requests');
      else url.searchParams.delete('section');
    }
    window.history.pushState(null, '', url);
    setView(nextView);
    if (nextView === 'operations') setOperationsSection('requests');
  }

  function navigateOperationsSection(nextSection: OperationsSection) {
    const url = new URL(window.location.href);
    url.searchParams.set('view', 'operations');
    if (nextSection === 'overview') url.searchParams.set('section', 'overview');
    else url.searchParams.set('section', 'requests');
    window.history.pushState(null, '', url);
    setView('operations');
    setOperationsSection(nextSection);
  }

  const page = view === 'operations' ? null : integratedPages[view];
  const frameSource = page
    ? `${page.source}?apiBaseUrl=${encodeURIComponent(apiBaseUrl)}`
    : '';
  const operationsFrameSource = `${operationsPage.source}?apiBaseUrl=${encodeURIComponent(apiBaseUrl)}&panel=overview`;

  return (
    <div className="integrated-app">
      <header className="integrated-nav">
        <a className="integrated-brand" href="/" onClick={event => { event.preventDefault(); navigate('catalogue'); }}>
          <span className="integrated-logo">M.</span> MACHINATI
        </a>
        <nav aria-label="Navigation principale">
          <button className={view === 'catalogue' ? 'active' : ''} onClick={() => navigate('catalogue')}><Tractor size={16} /> Catalogue</button>
          <button className={view === 'cooperative' ? 'active' : ''} onClick={() => navigate('cooperative')}><Users size={16} /> Coopérative</button>
          <button className={view === 'operations' ? 'active' : ''} onClick={() => navigate('operations')}><CalendarDays size={16} /> Opérations</button>
        </nav>
      </header>
      <div className="integrated-content">
        {page
          ? <iframe key={view} className="integrated-frame" title={page.title} src={frameSource} />
          : <div className="operations-workspace">
              <nav className="operations-tabs" role="tablist" aria-label="Vues des opérations">
                <button className={operationsSection === 'requests' ? 'active' : ''} role="tab" aria-selected={operationsSection === 'requests'} onClick={() => navigateOperationsSection('requests')}>Demandes</button>
                <button className={operationsSection === 'overview' ? 'active' : ''} role="tab" aria-selected={operationsSection === 'overview'} onClick={() => navigateOperationsSection('overview')}>Pilotage</button>
              </nav>
              <div className="operations-body">
                {operationsSection === 'requests'
                  ? <RequestsDashboard />
                  : <iframe className="operations-frame" title={operationsPage.title} src={operationsFrameSource} />}
              </div>
            </div>}
      </div>
    </div>
  );
}
