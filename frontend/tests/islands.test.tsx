import { describe, it, expect, vi } from 'vitest';
import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SourceExplorer } from '../src/components/SourceExplorer';
import { Chronology } from '../src/components/Chronology';
import { ResearchArchive } from '../src/components/ResearchArchive';
import type { SourcesPayload, ChronologyPayload, ArchivePayload } from '../src/generated/contracts';
import sourcesJson from '../../contracts/fixtures/sources.json';
import chronologyJson from '../../contracts/fixtures/chronology.json';
import archiveJson from '../../contracts/fixtures/archive.json';
const sources=sourcesJson as SourcesPayload;
const chronology=chronologyJson as ChronologyPayload;
const archive=archiveJson as ArchivePayload;

describe('source explorer', () => {
  it('filters primary and secondary sources without changing the article', async () => {
    render(<SourceExplorer data={sources}/>);
    await userEvent.selectOptions(screen.getByLabelText('Source classification'), 'secondary');
    expect(screen.getByRole('status')).toHaveTextContent('1 of 2');
    expect(screen.getByRole('heading',{level:3})).toHaveTextContent('Fictional study');
  });
  it('links citations back to server-rendered passages', () => {
    render(<SourceExplorer data={sources}/>);
    expect(screen.getByRole('link',{name:'Read passage'})).toHaveAttribute('href','#passage-one');
    expect(screen.getByRole('link',{name:'View bibliography entry'})).toHaveAttribute('href','#source-letter');
  });
  it('has an explicit empty state', async () => {
    render(<SourceExplorer data={sources}/>);
    await userEvent.type(screen.getByLabelText('Search sources'),'no-such-document');
    expect(screen.getByText('No sources match these filters.')).toBeInTheDocument();
  });
});

describe('chronology', () => {
  it('filters by person and preserves the selection in the URL', async () => {
    render(<Chronology data={chronology}/>);
    await userEvent.selectOptions(screen.getByLabelText('Person'),'Example B');
    expect(screen.getByRole('heading',{level:2})).toHaveTextContent('Fictional later event');
    expect(window.location.search).toContain('person=Example+B');
    expect(window.location.hash).toBe('#event-late');
  });
  it('rejects year zero rather than silently changing the range', async () => {
    render(<Chronology data={chronology}/>);
    await userEvent.type(screen.getByLabelText('From year'),'0');
    expect(screen.getByRole('alert')).toHaveTextContent('there is no year zero');
  });
});

describe('archive', () => {
  it('uses a bounded same-origin endpoint and updates the URL', async () => {
    const user=userEvent.setup();
    const next={...archive, filters:{...archive.filters,q:'evidence'},results:[],total:0};
    const fetchMock=vi.fn().mockResolvedValue({ok:true,status:200,json:async()=>next});
    vi.stubGlobal('fetch',fetchMock);
    render(<ResearchArchive data={archive}/>);
    await user.type(screen.getByLabelText('Search title or abstract'),'evidence');
    await user.click(screen.getByRole('button',{name:'Search archive'}));
    await waitFor(()=>expect(window.location.search).toContain('q=evidence'));
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/archive/');
    expect(await screen.findByText('No public records match these filters. Try a broader search.')).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
  it('retains results when the backend fails', async () => {
    vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:503}));
    render(<ResearchArchive data={archive}/>);
    await userEvent.click(screen.getByRole('button',{name:'Search archive'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('previous results are retained');
    expect(screen.getByRole('link',{name:'Demonstration article'})).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});
