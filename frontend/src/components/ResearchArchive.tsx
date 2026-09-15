import { useEffect, useRef, useState, type FormEvent } from 'react';
import type { ArchiveFilters, ArchivePayload, Choice } from '../generated/contracts';
import validate from '../generated/validate_archive.js';
import { parsePayload, safeHref } from '../lib';

const fields = ['q', 'subject', 'author', 'series', 'source_kind', 'published_from', 'published_to', 'historical_from', 'historical_to', 'status', 'sort'] as const;
function toQuery(filters: ArchiveFilters, page = 1): URLSearchParams {
  const query = new URLSearchParams();
  for (const key of fields) if (filters[key]) query.set(key, filters[key]);
  if (page > 1) query.set('page', String(page));
  return query;
}
function Choices({ options }: { options: Choice[] }) {
  return <>{options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</>;
}
export function ResearchArchive({ data }: { data: ArchivePayload }) {
  const [result, setResult] = useState(data);
  const [filters, setFilters] = useState<ArchiveFilters>(data.filters);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(data.errors.join(' '));
  const controller = useRef<AbortController | null>(null);
  const sequence = useRef(0);
  const summary = useRef<HTMLParagraphElement>(null);

  async function load(query: URLSearchParams, push: boolean) {
    controller.current?.abort();
    const abort = new AbortController(); controller.current = abort;
    const requestId = ++sequence.current;
    setBusy(true); setError('');
    try {
      const endpoint = new URL(data.endpoint, window.location.origin);
      if (endpoint.origin !== window.location.origin) throw new Error('The archive endpoint must be on this site.');
      endpoint.search = query.toString();
      const response = await fetch(endpoint, { signal: abort.signal, credentials: 'same-origin', headers: { Accept: 'application/json' }, cache: 'no-store' });
      if (!response.ok && response.status !== 400) throw new Error('The archive could not be loaded. Try again.');
      const next = parsePayload<ArchivePayload>(await response.json(), validate);
      if (requestId !== sequence.current) return;
      if (!response.ok || next.errors.length) throw new Error(next.errors.join(' ') || 'Check the archive filters.');
      setResult(next); setFilters(next.filters);
      if (push) {
        const canonical = toQuery(next.filters, next.page).toString();
        window.history.pushState(null, '', `${window.location.pathname}${canonical ? `?${canonical}` : ''}`);
        requestAnimationFrame(() => summary.current?.focus());
      }
    } catch (reason) {
      if (requestId === sequence.current && !(reason instanceof DOMException && reason.name === 'AbortError')) {
        setError(reason instanceof Error ? reason.message : 'The archive could not be loaded.');
      }
    } finally { if (requestId === sequence.current) setBusy(false); }
  }
  useEffect(() => {
    const back = () => { void load(new URLSearchParams(window.location.search), false); };
    window.addEventListener('popstate', back);
    return () => { window.removeEventListener('popstate', back); controller.current?.abort(); };
  }, []);
  function change<K extends keyof ArchiveFilters>(key: K, value: ArchiveFilters[K]) {
    setFilters(current => ({ ...current, [key]: value }));
  }
  function submit(event: FormEvent) { event.preventDefault(); void load(toQuery(filters), true); }
  function clear() {
    const empty: ArchiveFilters = { q: '', subject: '', author: '', series: '', source_kind: '', published_from: '', published_to: '', historical_from: '', historical_to: '', status: '', sort: 'newest' };
    setFilters(empty); void load(toQuery(empty), true);
  }
  function remove(key: keyof ArchiveFilters) {
    const next = { ...result.filters, [key]: '' };
    setFilters(next); void load(toQuery(next), true);
  }
  return <section className="react-tool archive-tool" aria-label="Interactive research archive">
    <form onSubmit={submit} className="archive-form" aria-label="Archive filters">
      <div className="form-grid">
        <label className="wide-field">Search title or abstract<input type="search" value={filters.q} maxLength={120} onChange={e => change('q', e.target.value)} placeholder="What are you investigating?" /></label>
        <label>Subject<select value={filters.subject} onChange={e => change('subject', e.target.value)}><option value="">All subjects</option><Choices options={result.facets.subjects} /></select></label>
        <label>Author<select value={filters.author} onChange={e => change('author', e.target.value)}><option value="">All authors</option><Choices options={result.facets.authors} /></select></label>
        <label>Series<select value={filters.series} onChange={e => change('series', e.target.value)}><option value="">All series</option><Choices options={result.facets.series} /></select></label>
        <label>Source classification<select value={filters.source_kind} onChange={e => change('source_kind', e.target.value)}><option value="">Any classification</option><option value="primary">Includes primary sources</option><option value="secondary">Includes secondary sources</option><option value="unclassified">Includes unclassified sources</option></select></label>
        <label>Published from<input type="date" value={filters.published_from} onChange={e => change('published_from', e.target.value)} /></label>
        <label>Published through<input type="date" value={filters.published_to} onChange={e => change('published_to', e.target.value)} /></label>
        <label>Historical period from<input type="number" min={-10000} max={10000} value={filters.historical_from} onChange={e => change('historical_from', e.target.value)} placeholder="Negative years = BCE" /></label>
        <label>Historical period through<input type="number" min={-10000} max={10000} value={filters.historical_to} onChange={e => change('historical_to', e.target.value)} placeholder="No year zero" /></label>
        <label>Record status<select value={filters.status} onChange={e => change('status', e.target.value)}><option value="">All public records</option><option value="public_draft">Public drafts</option><option value="planned">Planned briefs</option><option value="under_review">Under review</option><option value="version_of_record">Versions of record</option></select></label>
        <label>Sort results<select value={filters.sort} onChange={e => change('sort', e.target.value as ArchiveFilters['sort'])}><option value="newest">Newest published</option><option value="oldest">Oldest published</option><option value="title">Title A-Z</option></select></label>
      </div>
      <div className="form-actions"><button type="submit" disabled={busy}>{busy ? 'Searching...' : 'Search archive'}</button><button type="button" className="secondary" onClick={clear} disabled={busy}>Clear filters</button></div>
    </form>
    {error && <p role="alert" className="notice">{error} The previous results are retained. Adjust the filters and search again.</p>}
    <div className="filter-chips">{fields.filter(key => key !== 'sort' && result.filters[key]).map(key => <button type="button" className="filter-chip" key={key} onClick={() => remove(key)} disabled={busy} aria-label={`Remove ${key} filter`}>{key.replaceAll('_', ' ')}: {result.filters[key]} <span aria-hidden="true">x</span></button>)}</div>
    <p className="results-summary" role="status" aria-live="polite" tabIndex={-1} ref={summary}>{busy ? 'Updating results...' : `${result.total} ${result.total === 1 ? 'public record' : 'public records'} found. Page ${result.page} of ${result.pages}.`}</p>
    <div className="publication-grid archive-grid" aria-busy={busy}>{result.results.map(article => <article className={`publication-card discipline-${article.discipline.toLowerCase()}`} key={article.id}>
      <p className="eyebrow">{article.discipline} / {article.article_type}</p><h2><a href={safeHref(article.url)}>{article.title}</a></h2>
      <p className="meta">{article.authors.join(', ')} / {article.publication_date ? <time dateTime={article.publication_date}>{article.display_date || article.publication_date}</time> : article.display_date}</p>
      <p className="card-subjects">{article.subjects.join(' / ')}</p>
      <details><summary>{article.record_status === 'planned' ? 'Read commissioning brief' : 'Read abstract'}</summary><p>{article.abstract}</p></details>
      <dl className="publication-signals"><div><dt>Status</dt><dd>{article.status_label}</dd></div><div><dt>Review</dt><dd>{article.review_status}</dd></div>{article.sources_summary && <div><dt>Sources</dt><dd>{article.sources_summary}</dd></div>}{article.method && <div><dt>Method</dt><dd>{article.method}</dd></div>}</dl>
      {article.record_status === 'planned' && <p className="planned-label">Planned commissioning brief, not a published research article.</p>}
      {article.historical_period && <p className="meta">Period covered: {article.historical_period}</p>}
      {article.is_demonstration && <span className="badge">Demonstration content</span>}
    </article>)}</div>
    {!result.results.length && !busy && <p>No public records match these filters. Try a broader search.</p>}
    <nav className="pagination" aria-label="Archive pages"><button type="button" className="secondary" disabled={busy || result.page <= 1} onClick={() => void load(toQuery(result.filters, result.page - 1), true)}>Previous</button><span>{result.page} / {result.pages}</span><button type="button" className="secondary" disabled={busy || result.page >= result.pages} onClick={() => void load(toQuery(result.filters, result.page + 1), true)}>Next</button></nav>
  </section>;
}
