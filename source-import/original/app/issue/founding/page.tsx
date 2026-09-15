import type { Metadata } from 'next';
import { PublicationCard } from '@/components/publication-card';
import { publications } from '@/lib/journal-data';

export const metadata: Metadata = {
  title: 'Founding Issue Portfolio',
  description: 'The proposed ten-piece founding portfolio: five history, three philosophy, and two politics articles.',
  alternates: { canonical: '/issue/founding' },
};

export default function FoundingIssuePage() {
  const counts = publications.reduce<Record<string, number>>((acc, publication) => {
    acc[publication.discipline] = (acc[publication.discipline] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <main id="main-content">
      <header className="page-hero issue-hero">
        <div>
          <p className="eyebrow">Issue 00 · commissioning portfolio</p>
          <h1>A balance declared before acceptance.</h1>
        </div>
        <p>
          These ten records are editorial briefs, not finished articles. They make scope, method, sources,
          and the 50/30/20 commitment inspectable while the founding issue is developed.
        </p>
      </header>

      <section className="issue-tally" aria-label="Founding issue discipline count">
        <div><strong>{counts.History}</strong><span>History</span><small>50 percent</small></div>
        <div><strong>{counts.Philosophy}</strong><span>Philosophy</span><small>30 percent</small></div>
        <div><strong>{counts.Politics}</strong><span>Politics</span><small>20 percent</small></div>
        <p>Analysis is evaluated across all ten records and is not counted as a fourth discipline.</p>
      </section>

      <section className="issue-list section-shell">
        <div className="publication-grid archive-grid">
          {publications.map((publication, index) => (
            <PublicationCard key={publication.slug} publication={publication} index={index} />
          ))}
        </div>
      </section>
    </main>
  );
}
