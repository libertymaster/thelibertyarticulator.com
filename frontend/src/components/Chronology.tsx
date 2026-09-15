import { useEffect, useMemo, useState } from 'react';
import type { ChronologyPayload } from '../generated/contracts';
import { rangeError, safeHref, yearLabel } from '../lib';

const themeLabels: Record<string, string> = { life: 'Life', writing: 'Writings', politics: 'Political activity', context: 'Historical context' };
function initialFilters() {
  const query = new URLSearchParams(window.location.search);
  return { person: query.get('person') ?? '', theme: query.get('theme') ?? '', from: query.get('from') ?? '', to: query.get('to') ?? '', q: query.get('q') ?? '' };
}
export function Chronology({ data }: { data: ChronologyPayload }) {
  const [filters, setFilters] = useState(initialFilters);
  const [selection, setSelection] = useState(() => window.location.hash.replace(/^#event-/, ''));
  const error = rangeError(filters.from, filters.to);
  const people = useMemo(() => [...new Set(data.events.map(event => event.person))].sort(), [data.events]);
  const events = useMemo(() => error ? [] : data.events.filter(event =>
    (!filters.person || event.person === filters.person) && (!filters.theme || event.theme === filters.theme) &&
    (!filters.from || event.year >= Number(filters.from)) && (!filters.to || event.year <= Number(filters.to)) &&
    `${event.title} ${event.description} ${event.person}`.toLowerCase().includes(filters.q.trim().toLowerCase())
  ), [data.events, filters, error]);
  const selected = events.find(event => event.key === selection) ?? events[0];
  useEffect(() => {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) if (value) query.set(key, value);
    const hash = selected ? `#event-${selected.key}` : '';
    window.history.replaceState(null, '', `${window.location.pathname}${query.size ? `?${query}` : ''}${hash}`);
  }, [filters, selected?.key]);
  useEffect(() => {
    const back = () => { setFilters(initialFilters()); setSelection(window.location.hash.replace(/^#event-/, '')); };
    window.addEventListener('popstate', back);
    return () => window.removeEventListener('popstate', back);
  }, []);
  const change = (key: keyof typeof filters, value: string) => setFilters(current => ({ ...current, [key]: value }));
  return <section className="react-tool chronology-tool" aria-label="Interactive chronology">
    <div className="archive-form"><div className="form-grid">
      <label>Person<select value={filters.person} onChange={e => change('person', e.target.value)}><option value="">Compare all people</option>{people.map(person => <option key={person} value={person}>{person}</option>)}</select></label>
      <label>Theme<select value={filters.theme} onChange={e => change('theme', e.target.value)}><option value="">All themes</option>{Object.entries(themeLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
      <label>Search events<input type="search" value={filters.q} onChange={e => change('q', e.target.value)} /></label>
      <label>From year<input type="number" value={filters.from} onChange={e => change('from', e.target.value)} placeholder="Negative = BCE" /></label>
      <label>Through year<input type="number" value={filters.to} onChange={e => change('to', e.target.value)} placeholder="No year zero" /></label>
    </div><button type="button" className="secondary" onClick={() => setFilters({ person: '', theme: '', from: '', to: '', q: '' })}>Reset chronology</button></div>
    {error && <p className="notice" role="alert">{error}</p>}
    <p className="results-summary" role="status" aria-live="polite">{events.length} of {data.events.length} events. Filters and the selected event are included in this page's URL.</p>
    <div className="timeline-layout"><ol className="timeline-events" aria-label="Events">{events.map(event => <li key={event.key}><button type="button" className="timeline-event" aria-pressed={selected?.key === event.key} onClick={() => setSelection(event.key)}><time>{event.date_label}</time><strong>{event.title}</strong><small>{event.person} / {themeLabels[event.theme]}</small></button></li>)}</ol>
      {selected ? <article className="timeline-detail" aria-label="Selected event"><p className="eyebrow">{selected.date_label} / {yearLabel(selected.year)}</p><h2>{selected.title}</h2><p className="meta">{selected.person} / {themeLabels[selected.theme]}</p><p className="event-description">{selected.description}</p><div className="event-evidence"><h3>Evidence</h3><p>{selected.source_citation}</p>{safeHref(selected.source_url) && <a href={safeHref(selected.source_url)} rel="noopener noreferrer">Consult source</a>}</div>{safeHref(selected.article_url) && <p><a href={safeHref(selected.article_url)}>Related essay: {selected.article_title}</a></p>}<button type="button" className="secondary" onClick={() => { const fallback = document.getElementById('chronology-fallback'); if (fallback) { fallback.hidden = false; fallback.querySelector(`#event-${selected.key}`)?.scrollIntoView({ block: 'start' }); } }}>Read in the complete chronology</button></article> : <p>No events match these filters.</p>}
    </div>
  </section>;
}
