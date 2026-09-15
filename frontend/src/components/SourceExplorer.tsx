import { useMemo, useState } from 'react';
import type { SourcesPayload } from '../generated/contracts';
import { safeHref, yearLabel } from '../lib';

export function SourceExplorer({ data }: { data: SourcesPayload }) {
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState('');
  const [selectedKey, setSelectedKey] = useState(data.sources[0]?.key ?? '');
  const sources = useMemo(() => data.sources.filter(source =>
    (!kind || source.kind === kind) &&
    [source.title, source.authors, source.bibliography, source.annotation].join(' ').toLowerCase().includes(query.trim().toLowerCase())
  ), [data.sources, kind, query]);
  const selected = sources.find(source => source.key === selectedKey) ?? sources[0];
  return <section className="react-tool source-tool" aria-labelledby="source-tool-title">
    <p className="eyebrow">Examine the evidence</p><h2 id="source-tool-title">Explore the sources</h2>
    <label>Search sources<input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Author, title, annotation" /></label>
    <label>Source classification<select value={kind} onChange={e => setKind(e.target.value)}><option value="">All sources</option><option value="primary">Primary sources</option><option value="secondary">Secondary sources</option><option value="unclassified">Not classified</option></select></label>
    <p className="tool-count" role="status" aria-live="polite">{sources.length} of {data.sources.length} sources</p>
    <ul className="source-results">{sources.map(source => <li key={source.key}><button type="button" className="source-select" aria-pressed={selected?.key === source.key} onClick={() => setSelectedKey(source.key)}><span className="badge">{source.kind === 'unclassified' ? 'Not classified' : source.kind}</span><strong>{source.title}</strong><small>{source.authors}{source.year !== null ? ` / ${yearLabel(source.year)}` : ''}</small></button></li>)}</ul>
    {!selected && <p>No sources match these filters.</p>}
    {selected && <div className="source-detail" aria-label="Selected source">
      <h3>{selected.title}</h3><p className="source-bibliography">{selected.bibliography}</p>
      {selected.annotation && <><h4>Why it is used</h4><p>{selected.annotation}</p></>}
      <h4>Where it is cited</h4>
      {selected.citations.length ? <ul>{selected.citations.map(citation => <li key={citation.anchor}><a href={safeHref(citation.anchor)}>Note {citation.number}{citation.locator ? `: ${citation.locator}` : ''}</a>{' '}<a href={safeHref(citation.passage_anchor)}>Read passage</a></li>)}</ul> : <p>Listed in the bibliography; no passage references have been added.</p>}
      {safeHref(selected.url) && <p><a href={safeHref(selected.url)} rel="noopener noreferrer">Consult the source</a></p>}
      <a href={`#source-${selected.key}`}>View bibliography entry</a>
    </div>}
  </section>;
}
