import { useEffect, useState } from 'react';
import {
  Tractor,
  LayoutDashboard,
  CalendarDays,
  Users,
} from 'lucide-react';
import { RequestsDashboard } from './pages/RequestsDashboard';
import { apiBaseUrl } from './shared/api';

type IntegratedView = 'catalogue' | 'cooperative' | 'operations' | 'requests';

const integratedPages: Record<Exclude<IntegratedView, 'requests'>, { title: string; source: string }> = {
  catalogue: { title: 'Catalogue Machinati', source: '/catalogue.html' },
  cooperative: { title: 'Espace coopérative', source: '/cooperative.html' },
  operations: { title: 'Équipe opérations', source: '/equipe-machinati.html' },
};

export function App() {
  const [view, setView] = useState<IntegratedView>(() => {
    const requestedView = new URLSearchParams(window.location.search).get('view');
    return requestedView && ['catalogue', 'cooperative', 'operations', 'requests'].includes(requestedView)
      ? requestedView as IntegratedView
      : 'catalogue';
  });

  useEffect(() => {
    const syncView = () => {
      const requestedView = new URLSearchParams(window.location.search).get('view');
      if (requestedView && ['catalogue', 'cooperative', 'operations', 'requests'].includes(requestedView)) {
        setView(requestedView as IntegratedView);
      } else {
        setView('catalogue');
      }
    };
    window.addEventListener('popstate', syncView);
    return () => window.removeEventListener('popstate', syncView);
  }, []);

  function navigate(nextView: IntegratedView) {
    const url = new URL(window.location.href);
    if (nextView === 'catalogue') url.searchParams.delete('view');
    else url.searchParams.set('view', nextView);
    window.history.pushState(null, '', url);
    setView(nextView);
  }

  const page = view === 'requests' ? null : integratedPages[view];
  const frameSource = page
    ? `${page.source}?apiBaseUrl=${encodeURIComponent(apiBaseUrl)}`
    : '';

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
          <button className={view === 'requests' ? 'active' : ''} onClick={() => navigate('requests')}><LayoutDashboard size={16} /> Demandes</button>
        </nav>
      </header>
      <div className="integrated-content">
        {page
          ? <iframe key={view} className="integrated-frame" title={page.title} src={frameSource} />
          : <RequestsDashboard />}
      </div>
    </div>
  );
}
