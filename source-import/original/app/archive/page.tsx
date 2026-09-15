import type { Metadata } from 'next';
import { ArchiveBrowser } from '@/components/archive-browser';
import { publications } from '@/lib/journal-data';

export const metadata: Metadata = {
  title: 'Archive',
  description: 'Search the founding editorial and commissioning portfolio by discipline, source, and method.',
  alternates: { canonical: '/archive' },
};

export default function ArchivePage() {
  return (
    <main id="main-content">
      <header className="page-hero archive-hero">
        <p className="eyebrow">Search & archive</p>
        <h1>Find the question behind the claim.</h1>
        <p>
          The archive currently contains one public founding editorial and nine clearly marked commissioning briefs.
          Nothing planned is presented as published or peer reviewed.
        </p>
      </header>
      <ArchiveBrowser publications={publications} />
      <aside className="status-note">
        <p className="eyebrow">Record status</p>
        <h2>Transparent by design.</h2>
        <p>
          “Public draft,” “planned,” “under review,” and “version of record” are distinct states. A review badge will never appear before the relevant editorial record exists.
        </p>
      </aside>
    </main>
  );
}
