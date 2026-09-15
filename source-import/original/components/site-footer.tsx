import { ArrowUpRight } from 'lucide-react';

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-intro">
        <div>
          <p className="eyebrow">The Liberty Articulator</p>
          <h2>Inquiry without a foregone conclusion.</h2>
        </div>
        <p>
          A forthcoming independent journal examining liberty through historical evidence,
          philosophical argument, political institutions, and extended analysis.
        </p>
      </div>
      <div className="footer-grid">
        <div>
          <h3>Journal</h3>
          <a href="/archive">Archive</a>
          <a href="/issue/founding">Founding issue</a>
          <a href="/sources">Sources</a>
        </div>
        <div>
          <h3>Practice</h3>
          <a href="/standards">Research standards</a>
          <a href="/standards#peer-review">Peer review</a>
          <a href="/standards#corrections">Corrections</a>
        </div>
        <div>
          <h3>Participate</h3>
          <a href="/submit">Submissions</a>
          <a href="/about">About the journal</a>
          <a href="/about#governance">Governance</a>
        </div>
        <div className="footer-question">
          <h3>What does history mean to you?</h3>
          <a href="/about#question">Join the founding inquiry <ArrowUpRight size={16} /></a>
        </div>
      </div>
      <div className="footer-base">
        <p>© 2026 The Liberty Articulator. Founding policies and content rights are being established.</p>
        <p>Chicago, Illinois · Versioned 29 August 2026</p>
      </div>
    </footer>
  );
}
