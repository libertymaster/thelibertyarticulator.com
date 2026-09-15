import type { Metadata } from 'next';
import { ArrowUpRight, Archive, FileCheck2, Fingerprint, KeyRound } from 'lucide-react';
import { standardsSources } from '@/lib/journal-data';

export const metadata: Metadata = {
  title: 'Sources & Provenance',
  description: 'How The Liberty Articulator records, classifies, verifies, cites, and rights-checks primary and secondary sources.',
  alternates: { canonical: '/sources' },
};

export default function SourcesPage() {
  return (
    <main id="main-content">
      <header className="page-hero sources-hero">
        <div>
          <p className="eyebrow">Sources & provenance</p>
          <h1>A source is not primary in the abstract.</h1>
        </div>
        <p>
          Its evidentiary role depends on the question asked. The same pamphlet may be testimony for one inquiry,
          an edition for another, and an object of reception for a third.
        </p>
      </header>

      <section className="source-principles" aria-label="Source record principles">
        <article><Archive size={24} /><span>01</span><h2>Provenance</h2><p>Where the object came from, how it was transmitted, and which institution shaped its survival.</p></article>
        <article><Fingerprint size={24} /><span>02</span><h2>Identity</h2><p>The exact edition, translation, archival unit, catalog record, or digital artifact used.</p></article>
        <article><FileCheck2 size={24} /><span>03</span><h2>Verification</h2><p>The claim, locator, quotation or note, checking status, and article version that cited it.</p></article>
        <article><KeyRound size={24} /><span>04</span><h2>Rights</h2><p>Access, licence, permission, reproduction limits, and retrieval date are recorded separately.</p></article>
      </section>

      <section className="source-ledger section-shell" aria-labelledby="ledger-title">
        <div className="section-heading">
          <div><p className="eyebrow">Source ledger</p><h2 id="ledger-title">What every citation must let a reader recover.</h2></div>
          <p>A bibliography names an intellectual work. The source ledger records the exact object used and its role in the argument.</p>
        </div>
        <div className="ledger-table" role="table" aria-label="Required source ledger fields">
          <div role="row"><strong role="cell">Identity</strong><span role="cell">Creator · title · date · edition or version · language</span></div>
          <div role="row"><strong role="cell">Repository</strong><span role="cell">Institution · collection · series · box · folder · folio or page</span></div>
          <div role="row"><strong role="cell">Identifiers</strong><span role="cell">Archive ID · DOI · ISBN · catalog ID · stable URI</span></div>
          <div role="row"><strong role="cell">Use</strong><span role="cell">Claim supported · locator · quotation or note · primary/secondary role</span></div>
          <div role="row"><strong role="cell">Mediation</strong><span role="cell">Transcription · translation · digitization · alteration · known omission</span></div>
          <div role="row"><strong role="cell">Stewardship</strong><span role="cell">Rights · permission · access limits · retrieval date · checksum when retained</span></div>
        </div>
      </section>

      <section className="dossier-section" aria-labelledby="dossier-title">
        <div className="dossier-intro">
          <p className="eyebrow">Method dossier 001</p>
          <h2 id="dossier-title">Marc Bloch and the historian’s craft</h2>
          <p>
            This starter dossier identifies texts and archival guides that support the journal’s analytical method.
            It does not reproduce copyrighted editions or imply that free online access grants reuse permission.
          </p>
        </div>
        <div className="dossier-list">
          {standardsSources.slice(0, 4).map((source, index) => (
            <article key={source.href}>
              <div className="dossier-meta"><span>{String(index + 1).padStart(2, '0')}</span><p>{source.kind}</p></div>
              <h3>{source.title}</h3>
              <p className="dossier-org">{source.organization}</p>
              <p>{source.note}</p>
              <a href={source.href} target="_blank" rel="noreferrer">Open source record <ArrowUpRight size={16} /></a>
            </article>
          ))}
        </div>
      </section>

      <section className="source-cautions section-shell" aria-labelledby="cautions-title">
        <div>
          <p className="eyebrow">Non-negotiable distinctions</p>
          <h2 id="cautions-title">The source does not speak alone.</h2>
        </div>
        <ul>
          <li><span>01</span><p><strong>Primary does not mean sufficient.</strong> Evidence is scrutinized in relation to the question and the relevant secondary scholarship.</p></li>
          <li><span>02</span><p><strong>Digitized does not mean complete.</strong> Selection, description, scanning, search, and interface all mediate the record.</p></li>
          <li><span>03</span><p><strong>Accessible does not mean reusable.</strong> Copyright, contractual limits, privacy, cultural protocols, and repository rules remain distinct.</p></li>
          <li><span>04</span><p><strong>Silence is not absence.</strong> The missing record may reflect destruction, non-creation, catalog practice, power, or the limits of the search.</p></li>
        </ul>
      </section>
    </main>
  );
}
