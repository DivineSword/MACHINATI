import { useEffect, useState } from 'react';
import {
  Tractor,
  LayoutDashboard,
  CalendarDays,
  Users,
  MessageCircle,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Search,
} from 'lucide-react';
import { LegalFooter } from './LegalPages';
import { apiRequest, errorMessage } from '../shared/api';
import type { MachineRow, RequestRow } from '../shared/types';

type DashboardView = 'requests' | 'machines';

const statusText: Record<string, string> = {
  draft: 'Brouillon',
  pending_review: 'À examiner',
  approved: 'Approuvée',
  rejected: 'Refusée',
  completed: 'Terminée',
};

export function RequestsDashboard() {
  const [items, setItems] = useState<RequestRow[]>([]);
  const [machines, setMachines] = useState<MachineRow[]>([]);
  const [errors, setErrors] = useState({ requests: '', machines: '' });
  const [view, setView] = useState<DashboardView>('requests');
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [busy, setBusy] = useState<number | null>(null);

  async function load() {
    const [requestResult, machineResult] = await Promise.allSettled([
      apiRequest<RequestRow[]>('/api/requests'),
      apiRequest<MachineRow[]>('/api/machines'),
    ]);

    if (requestResult.status === 'fulfilled') {
      setItems(requestResult.value);
      setErrors(current => ({ ...current, requests: '' }));
    } else {
      setErrors(current => ({ ...current, requests: errorMessage(requestResult.reason) }));
    }

    if (machineResult.status === 'fulfilled') {
      setMachines(machineResult.value);
      setErrors(current => ({ ...current, machines: '' }));
    } else {
      setErrors(current => ({ ...current, machines: errorMessage(machineResult.reason) }));
    }
  }

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 10000);
    return () => window.clearInterval(timer);
  }, []);

  async function update(id: number, status: string) {
    setBusy(id);
    try {
      await apiRequest(`/api/requests/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      await load();
    } catch (error) {
      setErrors(current => ({ ...current, requests: errorMessage(error) }));
    } finally {
      setBusy(null);
    }
  }

  const visibleRequests = items.filter(request =>
    (filter === 'all' || request.status === filter) &&
    `${request.farmer_phone} ${JSON.stringify(request.payload)}`.toLowerCase().includes(search.toLowerCase()),
  );
  const visibleMachines = machines.filter(machine =>
    `${machine.name} ${machine.machine_type} ${machine.location || ''}`.toLowerCase().includes(search.toLowerCase()),
  );
  const pending = items.filter(request => request.status === 'pending_review').length;
  const approved = items.filter(request => request.status === 'approved').length;
  const availableMachines = machines.filter(machine => Boolean(machine.available)).length;
  const machineLocations = new Set(machines.map(machine => machine.location).filter(Boolean)).size;

  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <span className="logo">✳</span>
          <span>MACHINATI<small>Gestion coopérative</small></span>
        </div>
        <div className="nav">
          <button className={view === 'requests' ? 'active' : ''} onClick={() => setView('requests')}>
            <LayoutDashboard size={19} /> Demandes
          </button>
          <div><CalendarDays size={19} /> Planning <small>Bientôt</small></div>
          <button className={view === 'machines' ? 'active' : ''} onClick={() => setView('machines')}>
            <Tractor size={19} /> Matériel
          </button>
          <div><Users size={19} /> Agriculteurs <small>Bientôt</small></div>
          <div><MessageCircle size={19} /> WhatsApp <small>Connecteur</small></div>
        </div>
        <div className="sidefoot">Prototype MVP · MACHINATI 2026</div>
      </aside>

      <main>
        <header>
          <div>
            <p className="eyebrow">ESPACE COOPÉRATIVE</p>
            <h1>{view === 'requests' ? 'Demandes de matériel' : 'Parc matériel'}</h1>
            <p className="muted">
              {view === 'requests' ? 'Suivez les demandes reçues depuis WhatsApp' : 'Consultez le matériel enregistré dans la coopérative'}
            </p>
          </div>
          <button className="refresh" onClick={() => void load()}>
            <RefreshCw size={16} /> Actualiser
          </button>
        </header>

        {view === 'requests' ? (
          <>
            <section className="metrics">
              <article><div className="metricicon mint"><MessageCircle size={20} /></div><div><span>Demandes reçues</span><strong>{items.length}</strong></div></article>
              <article><div className="metricicon amber"><Clock size={20} /></div><div><span>À examiner</span><strong>{pending}</strong></div></article>
              <article><div className="metricicon blue"><CheckCircle2 size={20} /></div><div><span>Approuvées</span><strong>{approved}</strong></div></article>
            </section>

            <section className="panel">
              <div className="paneltop">
                <div><h2>Toutes les demandes</h2><p className="muted">Les brouillons ne peuvent pas être approuvés.</p></div>
                <div className="controls">
                  <label className="search"><Search size={16} /><input placeholder="Rechercher..." value={search} onChange={event => setSearch(event.target.value)} /></label>
                  <select value={filter} onChange={event => setFilter(event.target.value)}>
                    <option value="all">Tous les statuts</option>
                    {Object.entries(statusText).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                </div>
              </div>
              {errors.requests && <div className="error">{errors.requests} — Vérifiez la connexion au backend FastAPI.</div>}
              <div className="tablewrap">
                <table>
                  <thead><tr><th>AGRICULTEUR</th><th>MACHINE / OPÉRATION</th><th>SURFACE</th><th>LOCALITÉ</th><th>DATE SOUHAITÉE</th><th>STATUT</th><th>ACTIONS</th></tr></thead>
                  <tbody>
                    {visibleRequests.map(request => (
                      <tr key={request.id}>
                        <td><div className="phone"><span className="avatar">{request.farmer_phone.slice(-2)}</span>{request.farmer_phone}</div></td>
                        <td><b>{request.payload.machine_type || 'Non précisé'}</b><small>{request.payload.operation || '—'}</small></td>
                        <td>{request.payload.area_hectares ?? '—'} ha</td>
                        <td>{request.payload.location || '—'}</td>
                        <td>{request.payload.preferred_date || request.payload.preferred_date_text || '—'}</td>
                        <td><span className={`status ${request.status}`}>{statusText[request.status] || request.status}</span></td>
                        <td>
                          {request.status === 'pending_review' ? (
                            <div className="actions">
                              <button disabled={busy === request.id} title="Approuver" onClick={() => void update(request.id, 'approved')}><CheckCircle2 size={17} /></button>
                              <button disabled={busy === request.id} title="Refuser" onClick={() => void update(request.id, 'rejected')}><XCircle size={17} /></button>
                            </div>
                          ) : <span className="muted">—</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!visibleRequests.length && <div className="empty"><Tractor size={36} /><h3>Aucune demande à afficher</h3><p>Les demandes WhatsApp apparaîtront ici après réception.</p></div>}
              </div>
            </section>
          </>
        ) : (
          <>
            <section className="metrics">
              <article><div className="metricicon mint"><Tractor size={20} /></div><div><span>Matériels enregistrés</span><strong>{machines.length}</strong></div></article>
              <article><div className="metricicon amber"><CheckCircle2 size={20} /></div><div><span>Disponibles</span><strong>{availableMachines}</strong></div></article>
              <article><div className="metricicon blue"><Users size={20} /></div><div><span>Localités</span><strong>{machineLocations}</strong></div></article>
            </section>

            <section className="panel">
              <div className="paneltop">
                <div><h2>Matériel de la coopérative</h2><p className="muted">Disponibilités et tarifs horaires</p></div>
                <label className="search"><Search size={16} /><input placeholder="Rechercher..." value={search} onChange={event => setSearch(event.target.value)} /></label>
              </div>
              {errors.machines && <div className="error">{errors.machines} — Vérifiez la connexion au backend FastAPI.</div>}
              <div className="tablewrap">
                <table>
                  <thead><tr><th>MATÉRIEL</th><th>TYPE</th><th>LOCALITÉ</th><th>TARIF HORAIRE</th><th>DISPONIBILITÉ</th></tr></thead>
                  <tbody>
                    {visibleMachines.map(machine => (
                      <tr key={machine.id}>
                        <td><b>{machine.name}</b></td>
                        <td>{machine.machine_type}</td>
                        <td>{machine.location || '—'}</td>
                        <td>{machine.hourly_rate == null ? '—' : `${machine.hourly_rate} / h`}</td>
                        <td><span className={`status ${machine.available ? 'approved' : 'rejected'}`}>{machine.available ? 'Disponible' : 'Indisponible'}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!visibleMachines.length && <div className="empty"><Tractor size={36} /><h3>Aucun matériel à afficher</h3><p>Le matériel enregistré apparaîtra ici.</p></div>}
              </div>
            </section>
          </>
        )}

        <LegalFooter />
      </main>
    </div>
  );
}