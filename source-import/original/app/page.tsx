import { ArrowRight, ArrowUpRight, BookOpenText, GitCompareArrows, Scale } from 'lucide-react';
import { PublicationCard } from '@/components/publication-card';
import { blochLens, publications, standardsSources, workflow } from '@/lib/journal-data';

export default function Home() {
  return (
    <main id="main-content">
      <section className="masthead home-masthead">
        <div>
          <p className="eyebrow">Investigating under the microscope of liberty.</p>
          <h1>Analyzing through the<br />telescope of history.</h1>
        </div>
        <div className="masthead-side">
          <p className="masthead-note">
            We examine liberty as a historical problem, a philosophical claim, and a political practice—always through evidence.
          </p>
          <a className="text-link" href="/about">Read the founding charter <ArrowRight size={17} /></a>
        </div>
      </section>

      <section className="allocation" aria-label="Editorial allocation">
        <div className="allocation-label">
          <span>Editorial balance</span>
          <strong>Analysis across all three</strong>
        </div>
        <div className="allocation-bars">
          <a className="history-bar" href="/archive"><span>History</span><strong>50%</strong></a>
          <a className="philosophy-bar" href="/archive"><span>Philosophy</span><strong>30%</strong></a>
          <a className="politics-bar" href="/archive"><span>Politics</span><strong>20%</strong></a>
        </div>
      </section>

      <section className="proof-strip" aria-label="Journal commitments">
        <div><BookOpenText size={20} /><p><strong>Primary-source grounded</strong><span>Every claim leaves a retraceable trail.</span></p></div>
        <div><Scale size={20} /><p><strong>Independent review</strong><span>Review model and status are named, never implied.</span></p></div>
        <div><GitCompareArrows size={20} /><p><strong>Versioned corrections</strong><span>The scholarly record is amended, not silently replaced.</span></p></div>
      </section>

      <section className="feature-grid" aria-labelledby="feature-title">
        <article className="feature-copy">
          <div className="article-meta">
            <span>History</span>
            <span>Founding editorial</span>
            <span>Public draft · not externally reviewed</span>
          </div>
          <h2 id="feature-title">The archive is not the village</h2>
          <p className="feature-deck">
            How do we reason from the records that survived without mistaking institutional memory for the lives it only partly contains?
          </p>
          <div className="byline-row">
            <p><strong>The Editors</strong><br /><span>29 August 2026 · 9 min read · Version 1.0</span></p>
            <a className="read-link" href="/article/the-archive-is-not-the-village">Read the editorial <ArrowRight size={18} /></a>
          </div>
        </article>

        <aside className="source-panel" aria-label="The Bloch Lens">
          <div className="lens-mark" aria-hidden="true"><span /><span /></div>
          <div>
            <p className="panel-kicker">The Bloch Lens</p>
            <h2>Evidence has a history.</h2>
            <p>Every long-form article identifies what survives, what is silent, which comparison clarifies the problem, and what would change its conclusion.</p>
          </div>
          <a className="panel-link" href="/standards#bloch-lens">Open the seven questions <ArrowRight size={17} /></a>
        </aside>
      </section>

      <section className="section-shell" aria-labelledby="portfolio-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Founding portfolio</p>
            <h2 id="portfolio-title">A journal measured by what it publishes.</h2>
          </div>
          <div>
            <p>Ten commissioning briefs make the 5–3–2 balance visible before the first issue is accepted.</p>
            <a className="text-link" href="/issue/founding">Inspect the full portfolio <ArrowRight size={17} /></a>
          </div>
        </div>
        <div className="publication-grid home-publications">
          {[publications[1], publications[5], publications[8]].map((publication, index) => (
            <PublicationCard key={publication.slug} publication={publication} index={index} />
          ))}
        </div>
      </section>

      <section className="analysis-section" aria-labelledby="analysis-title">
        <div className="analysis-intro">
          <p className="eyebrow">Analysis is not a fourth category</p>
          <h2 id="analysis-title">It is the discipline applied to every category.</h2>
          <p>
            Inspired by Marc Bloch’s insistence on criticism, comparison, and explanation, the Bloch Lens is a public rubric rather than a ceremonial name.
          </p>
          <a className="light-link" href="/standards#bloch-lens">How the rubric is reviewed <ArrowUpRight size={17} /></a>
        </div>
        <ol className="lens-questions">
          {blochLens.map((question, index) => (
            <li key={question}><span>{String(index + 1).padStart(2, '0')}</span><p>{question}</p></li>
          ))}
        </ol>
      </section>

      <section className="source-desk section-shell" aria-labelledby="source-desk-title">
        <div className="source-desk-heading">
          <p className="eyebrow">The source desk</p>
          <h2 id="source-desk-title">Access is not evidence.<br />Evidence is not permission.</h2>
          <p>Each source record separates what an object can support, where it came from, and whether it may be reproduced.</p>
          <a className="text-link" href="/sources">Browse the source protocol <ArrowRight size={17} /></a>
        </div>
        <div className="source-list">
          {standardsSources.slice(0, 3).map((source, index) => (
            <a key={source.href} href={source.href} target="_blank" rel="noreferrer">
              <span className="source-number">0{index + 1}</span>
              <div><p>{source.kind}</p><h3>{source.title}</h3><span>{source.organization}</span></div>
              <ArrowUpRight size={18} />
            </a>
          ))}
        </div>
      </section>

      <section className="workflow-preview" aria-labelledby="workflow-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Editorial workflow</p>
            <h2 id="workflow-title">Rigor is a sequence of accountable decisions.</h2>
          </div>
          <div>
            <p>Submission, review, verification, publication, and correction each leave a visible record.</p>
            <a className="text-link" href="/standards#peer-review">See all ten gates <ArrowRight size={17} /></a>
          </div>
        </div>
        <div className="workflow-row">
          {workflow.slice(0, 4).map(([number, title, description]) => (
            <article key={number}><span>{number}</span><h3>{title}</h3><p>{description}</p></article>
          ))}
        </div>
      </section>

      <section className="founding-question" id="question">
        <p className="eyebrow">A question before a claim</p>
        <h2>What does history mean to you?</h2>
        <p>The question will open our first reader forum. Its answers will be moderated, preserved, and clearly distinguished from peer-reviewed scholarship.</p>
        <div>
          <a className="primary-link" href="/about#question">Read the forum protocol <ArrowRight size={18} /></a>
          <a className="secondary-link" href="/submit">View submission guidance</a>
        </div>
      </section>
    </main>
  );
}
