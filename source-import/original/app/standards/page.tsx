import type { Metadata } from 'next';
import { ArrowUpRight, Check, CircleDashed, EyeOff, GitCompareArrows, Scale } from 'lucide-react';
import { blochLens, standardsSources, workflow } from '@/lib/journal-data';

export const metadata: Metadata = {
  title: 'Research & Editorial Standards',
  description: 'The Liberty Articulator’s founding standards for evidence, analysis, peer review, verification, and corrections.',
  alternates: { canonical: '/standards' },
};

export default function StandardsPage() {
  return (
    <main id="main-content">
      <header className="page-hero standards-hero">
        <div>
          <p className="eyebrow">Research & editorial standards</p>
          <h1>Rigor must be visible to be accountable.</h1>
        </div>
        <p>
          These founding standards define what the journal intends to verify, disclose, preserve, and correct.
          They are dated drafts until an editorial board formally ratifies them.
        </p>
      </header>

      <div className="policy-status">
        <p><CircleDashed size={18} /><strong>Status:</strong> Founding draft for public scrutiny</p>
        <p>Version 0.9 · issued 29 August 2026 · next review before submissions open</p>
      </div>

      <nav className="standards-index" aria-label="Standards on this page">
        <a href="#scope">01 <span>Scope & balance</span></a>
        <a href="#peer-review">02 <span>Peer review</span></a>
        <a href="#bloch-lens">03 <span>Analysis</span></a>
        <a href="#verification">04 <span>Verification</span></a>
        <a href="#corrections">05 <span>Corrections</span></a>
        <a href="#ethics">06 <span>Ethics</span></a>
      </nav>

      <section className="standards-section" id="scope">
        <div className="standards-kicker"><span>01</span><p>Scope & balance</p></div>
        <div className="standards-body">
          <h2>Three fields. One measurable commitment.</h2>
          <p className="standards-lead">
            The founding portfolio uses a ten-article unit: five articles led by history, three by philosophy,
            and two by politics. Each interdisciplinary article receives one primary discipline at acceptance;
            secondary tags do not alter the count.
          </p>
          <div className="ratio-table" role="table" aria-label="Editorial portfolio targets">
            <div role="row"><span role="cell">History</span><strong role="cell">5 of 10</strong><span role="cell">50%</span></div>
            <div role="row"><span role="cell">Philosophy</span><strong role="cell">3 of 10</strong><span role="cell">30%</span></div>
            <div role="row"><span role="cell">Politics</span><strong role="cell">2 of 10</strong><span role="cell">20%</span></div>
          </div>
          <p className="standards-note">
            Analysis is a cross-cutting method, not a fourth allocation. The journal will publish an annual count of accepted research articles and explain any temporary deviation from the target.
          </p>
        </div>
      </section>

      <section className="standards-section dark-standard" id="peer-review">
        <div className="standards-kicker"><span>02</span><p>Peer review</p></div>
        <div className="standards-body">
          <h2>Review is a process, not a guarantee.</h2>
          <p className="standards-lead">
            Research articles will normally receive two independent specialist reports. At launch, author and reviewer identities are concealed from one another; editors retain the information required to manage conflicts and accountability.
          </p>
          <div className="review-principles">
            <article><EyeOff size={22} /><h3>Identity transparency</h3><p>Each record names the review model in standardized language and states any exception.</p></article>
            <article><Scale size={22} /><h3>Conflict control</h3><p>Editors and reviewers declare relevant relationships, interests, funding, and recent collaboration before assignment.</p></article>
            <article><GitCompareArrows size={22} /><h3>Recorded revision</h3><p>Authors answer material objections point by point. Editors preserve reports, decisions, and manuscript versions.</p></article>
          </div>
          <p className="standards-note">
            Peer review can expose weaknesses and improve an argument; it does not certify truth. Editorials, news, reviews, and reader forums display their different review status plainly.
          </p>
        </div>
      </section>

      <section className="workflow-full" aria-labelledby="workflow-heading">
        <div className="section-heading">
          <div><p className="eyebrow">Ten accountable gates</p><h2 id="workflow-heading">From proposal to stewardship.</h2></div>
          <p>Every gate has an owner, an evidence requirement, and a dated decision. A publication cannot skip silently to the next state.</p>
        </div>
        <ol>
          {workflow.map(([number, title, description]) => (
            <li key={number}><span>{number}</span><div><h3>{title}</h3><p>{description}</p></div></li>
          ))}
        </ol>
      </section>

      <section className="standards-section" id="bloch-lens">
        <div className="standards-kicker"><span>03</span><p>The Bloch Lens</p></div>
        <div className="standards-body">
          <h2>Analysis in honor of Marc Bloch.</h2>
          <p className="standards-lead">
            The rubric is inspired by Bloch’s practice of critical testimony, comparison, historical analysis, and causal inquiry. It is not presented as a definitive reconstruction of his unfinished method.
          </p>
          <ol className="bloch-rubric">
            {blochLens.map((question, index) => (
              <li key={question}><span>{String(index + 1).padStart(2, '0')}</span><p>{question}</p><Check size={18} aria-hidden="true" /></li>
            ))}
          </ol>
        </div>
      </section>

      <section className="standards-section" id="verification">
        <div className="standards-kicker"><span>04</span><p>Verification</p></div>
        <div className="standards-body">
          <h2>A retraceable evidentiary trail.</h2>
          <div className="verification-grid">
            <article><span>A</span><h3>Source identity</h3><p>Repository, collection, series, box, folder, page or folio, stable identifier, consultation date, and rights status where relevant.</p></article>
            <article><span>B</span><h3>Textual accuracy</h3><p>Material quotations, names, dates, figures, translations, transcriptions, and image captions are checked against the cited object.</p></article>
            <article><span>C</span><h3>Claim support</h3><p>Editors distinguish what a source states, what an author infers, and which rival reading or counterevidence remains.</p></article>
            <article><span>D</span><h3>Access & limits</h3><p>Gaps, inaccessible holdings, selection effects, privileged access, permissions, and reproduction constraints are disclosed.</p></article>
          </div>
        </div>
      </section>

      <section className="standards-section dark-standard" id="corrections">
        <div className="standards-kicker"><span>05</span><p>Corrections</p></div>
        <div className="standards-body">
          <h2>The record is amended, never silently rewritten.</h2>
          <p className="standards-lead">
            Typographical fixes that do not alter meaning may be logged in place. Material corrections, expressions of concern, retractions, and responses receive their own dated notice, stable URL, reciprocal link, and explanation.
          </p>
          <ul className="check-list">
            <li><Check size={18} /> Prior public versions remain preserved.</li>
            <li><Check size={18} /> The current version identifies what changed and why.</li>
            <li><Check size={18} /> A correction never removes the original editorial history.</li>
            <li><Check size={18} /> Retraction marks the record; it does not make the record disappear.</li>
          </ul>
        </div>
      </section>

      <section className="standards-section" id="ethics">
        <div className="standards-kicker"><span>06</span><p>Ethics & independence</p></div>
        <div className="standards-body">
          <h2>Policies before prestige.</h2>
          <p className="standards-lead">
            Before submissions open, the journal will publish ratified policies for authorship, AI use, conflicts,
            funding, permissions, complaints, appeals, misconduct, privacy, licensing, preservation, and editorial independence.
          </p>
          <div className="policy-grid">
            {['Authorship & contribution', 'Funding & competing interests', 'Research ethics & permissions', 'Complaints & appeals', 'Misconduct response', 'Content, code & metadata rights'].map((policy) => (
              <div key={policy}><span>Founding draft</span><h3>{policy}</h3></div>
            ))}
          </div>
        </div>
      </section>

      <section className="standards-bibliography" aria-labelledby="standards-sources-heading">
        <div>
          <p className="eyebrow">Standards consulted</p>
          <h2 id="standards-sources-heading">The policy has sources, too.</h2>
          <p>Consulted sources guide the draft; listing them does not imply endorsement or certification by their publishers.</p>
        </div>
        <ol>
          {standardsSources.slice(3).map((source, index) => (
            <li key={source.href}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <div><h3>{source.title}</h3><p>{source.organization}</p><small>{source.note}</small></div>
              <a href={source.href} target="_blank" rel="noreferrer" aria-label={`Open ${source.title}`}><ArrowUpRight size={18} /></a>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
