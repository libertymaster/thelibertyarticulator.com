import { Menu, Search } from 'lucide-react';

const navItems = [
  ['Journal', '/'],
  ['Archive', '/archive'],
  ['Sources', '/sources'],
  ['Standards', '/standards'],
  ['About', '/about'],
] as const;

export function SiteHeader() {
  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <div className="credibility-bar">
        <p>An independent journal of history, philosophy, and politics.</p>
        <p className="issue-note">Founding issue in development · 2026</p>
      </div>
      <header className="site-header">
        <a className="wordmark" href="/" aria-label="The Liberty Articulator home">
          <span className="optic-mark" aria-hidden="true"><i /><i /></span>
          <span>The Liberty Articulator</span>
        </a>
        <nav className="desktop-nav" aria-label="Primary navigation">
          {navItems.map(([label, href]) => <a key={href} href={href}>{label}</a>)}
        </nav>
        <a className="search-button" href="/archive" aria-label="Search and browse the journal">
          <Search size={17} strokeWidth={1.7} />
          <span>Search</span>
        </a>
        <details className="mobile-nav">
          <summary aria-label="Open navigation"><Menu size={20} /><span>Menu</span></summary>
          <nav aria-label="Mobile navigation">
            {navItems.map(([label, href]) => <a key={href} href={href}>{label}</a>)}
            <a href="/submit">Submissions</a>
          </nav>
        </details>
      </header>
    </>
  );
}
