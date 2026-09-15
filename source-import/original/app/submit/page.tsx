import type { Metadata } from 'next';
import { ArrowRight, Check, Clock3 } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Submissions',
  description: 'Forthcoming article types, evidence requirements, and submission guidance for The Liberty Articulator.',
  alternates: { canonical: '/submit' },
};

const articleTypes = [
  ['Research article', 'An original argument grounded in a defined primary corpus and situated in relevant scholarship.', '8,000–12,000 words'],
  ['Primary-source study', 'A source-centered intervention that explains provenance, mediation, evidentiary value, and limits.', '5,000–8,000 words'],
  ['Philosophical argument', 'A sustained argument with explicit premises, objections, historical context where relevant, and conceptual stakes.', '6,000–10,000 words'],
  ['Comparative analysis', 'A structured comparison whose cases, dimensions, evidence, and inference rules are declared in advance.', '7,000–11,000 words'],
  ['Critical exchange', 'A paired argument and response reviewed as one scholarly record.', '4,000–6,000 words each'],
  ['Methods note', 'A focused, reproducible intervention in source criticism, translation, archival, computational, or comparative method.', '3,000–5,000 words'],
] as const;

export default function SubmitPage() {
  return (
    <main id="main-content">
      <header className="page-hero submit-hero">
        <div>
          <p className="eyebrow">Submissions</p>
          <h1>Show the route from evidence to inference.</h1>
        </div>
        <p>
          The journal is not yet accepting manuscripts. Guidance is published early so prospective authors can inspect the standard before the submission system opens.
        </p>
      </header>

      <div className="submissions-status">
        <Clock3 size={21} />
        <div><strong>Submissions are not yet open.</strong><p>Policies, governance, reviewer protections, preservation, and production checks must be ratified first.</p></div>
      </div>

      <section className="article-types section-shell" aria-labelledby="article-types-title">
        <div className="section-heading">
          <div><p className="eyebrow">Planned article types</p><h2 id="article-types-title">Form follows the scholarly task.</h2></div>
          <p>Word ranges are guidance, not proxies for quality. Each type has a distinct evidence and review checklist.</p>
        </div>
        <div className="article-type-list">
          {articleTypes.map(([title, description, length], index) => (
            <article key={title}><span>{String(index + 1).padStart(2, '0')}</span><div><h3>{title}</h3><p>{description}</p></div><small>{length}</small></article>
          ))}
        </div>
      </section>

      <section className="submission-checklist" aria-labelledby="checklist-title">
        <div>
          <p className="eyebrow">Before a manuscript enters review</p>
          <h2 id="checklist-title">The submission packet.</h2>
        </div>
        <ul>
          {[
            'An abstract that states the question, argument, evidence, method, and limits.',
            'A research protocol naming the primary corpus and relevant secondary scholarship.',
            'A source ledger with retraceable locators for every material factual claim.',
            'A completed Bloch Lens identifying silence, mediation, comparison, counterevidence, and revision conditions.',
            'Authorship contributions, funding, competing interests, permissions, and ethics disclosures.',
            'An anonymized manuscript plus a separate identity and affiliation record.',
            'Data, transcription, translation, image, and code availability statements where applicable.',
          ].map((item) => <li key={item}><Check size={18} /><span>{item}</span></li>)}
        </ul>
      </section>

      <section className="submission-close">
        <p className="eyebrow">Prepare, do not upload</p>
        <h2>Use the public standard as your checklist.</h2>
        <p>No manuscript files or personal data are being collected through this preview.</p>
        <a className="primary-link" href="/standards">Read the research standards <ArrowRight size={18} /></a>
      </section>
    </main>
  );
}
