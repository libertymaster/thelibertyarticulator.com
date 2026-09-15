import type { Metadata } from 'next';
import { ArrowRight, Eye, Landmark, Network, ShieldCheck } from 'lucide-react';

export const metadata: Metadata = {
  title: 'About',
  description: 'The founding mission, independence commitments, governance model, and central question of The Liberty Articulator.',
  alternates: { canonical: '/about' },
};

export default function AboutPage() {
  return (
    <main id="main-content">
      <header className="page-hero about-hero">
        <div>
          <p className="eyebrow">About the journal</p>
          <h1>Liberty is the inquiry, not the answer.</h1>
        </div>
        <p>
          The Liberty Articulator is being established as an independent journal for historically grounded,
          philosophically exacting, and politically serious work.
        </p>
      </header>

      <section className="mission-statement">
        <p className="eyebrow">Founding purpose</p>
        <blockquote>
          To publish scholarship that makes its evidence inspectable, its reasoning contestable,
          its uncertainties visible, and its corrections durable.
        </blockquote>
      </section>

      <section className="about-pillars section-shell" aria-label="Founding principles">
        <article><Landmark size={24} /><h2>Historical focus</h2><p>Half of the research portfolio is led by history, with primary-source studies, historiography, and comparative work at its center.</p></article>
        <article><Network size={24} /><h2>Interdisciplinary reach</h2><p>Philosophy receives thirty percent and politics twenty percent, while analysis crosses all three fields.</p></article>
        <article><Eye size={24} /><h2>Public method</h2><p>Review status, sources, disclosures, editorial dates, revisions, and limits remain visible at article level.</p></article>
        <article><ShieldCheck size={24} /><h2>Institutional independence</h2><p>Ownership, funding, editorial authority, and conflicts will be disclosed before submissions open.</p></article>
      </section>

      <section className="independence-section" id="governance">
        <div>
          <p className="eyebrow">Governance before publication</p>
          <h2>Independence needs structure.</h2>
          <p>
            The journal will not claim full operational independence until its governing body, funding model,
            editorial appointments, complaints route, and separation of editorial and commercial authority are public.
          </p>
        </div>
        <ol>
          <li><span>01</span><div><h3>Founding charter</h3><p>Defines purpose, scope, ownership, appointments, removal, voting, and amendment.</p></div></li>
          <li><span>02</span><div><h3>Editorial board</h3><p>Members, affiliations, terms, roles, relevant interests, and decision authority are published.</p></div></li>
          <li><span>03</span><div><h3>Financial disclosure</h3><p>Revenue sources, material donors, fees, sponsorships, and safeguards against influence are reported annually.</p></div></li>
          <li><span>04</span><div><h3>Independent appeal</h3><p>Complaints involving an editor are reassigned outside that editor’s authority and leave an auditable record.</p></div></li>
        </ol>
      </section>

      <section className="marc-bloch-section section-shell">
        <div className="optic-illustration" aria-hidden="true"><i /><i /><span>Analysis</span></div>
        <div>
          <p className="eyebrow">In honor of Marc Bloch</p>
          <h2>A living obligation to analyze.</h2>
          <p>
            The journal’s extended analytical focus draws inspiration from Bloch’s criticism of testimony,
            comparative imagination, attention to historical time, and insistence that the historian explain the craft.
          </p>
          <p>
            The Bloch Lens is therefore a working rubric, not a claim of institutional lineage, endorsement,
            or exclusive ownership of a broad historical method.
          </p>
          <a className="text-link" href="/standards#bloch-lens">Inspect the rubric <ArrowRight size={17} /></a>
        </div>
      </section>

      <section className="founding-question about-question" id="question">
        <p className="eyebrow">The founding inquiry</p>
        <h2>What does history mean to you?</h2>
        <p>
          The first reader forum will gather short, attributed answers from historians, philosophers,
          political scholars, archivists, teachers, students, and readers. Forum contributions will be moderated,
          consented, versioned, and labeled as invited reflection—not peer-reviewed research.
        </p>
        <a className="primary-link" href="/submit">See how participation will open <ArrowRight size={18} /></a>
      </section>
    </main>
  );
}
