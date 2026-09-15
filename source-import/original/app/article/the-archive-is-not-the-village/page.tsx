import type { Metadata } from 'next';
import { ArrowLeft, ArrowUpRight, CheckCircle2, CircleAlert, FileText, GitCommitHorizontal } from 'lucide-react';
import { CitationCopy } from '@/components/citation-copy';

const articleTitle = 'The Archive Is Not the Village';
const articleDescription = 'A founding editorial on surviving records, institutional memory, archival silence, and the journal’s standard for historical inference.';

export const metadata: Metadata = {
  title: articleTitle,
  description: articleDescription,
  alternates: { canonical: '/article/the-archive-is-not-the-village' },
  openGraph: {
    type: 'article',
    title: articleTitle,
    description: articleDescription,
    url: '/article/the-archive-is-not-the-village',
    images: [],
  },
  twitter: {
    card: 'summary',
    title: articleTitle,
    description: articleDescription,
    images: [],
  },
  other: {
    citation_title: articleTitle,
    citation_author: 'The Editors',
    citation_publication_date: '2026/08/29',
    citation_journal_title: 'The Liberty Articulator',
    citation_language: 'en',
    citation_abstract_html_url: 'https://thelibertyarticulator.com/article/the-archive-is-not-the-village',
  },
};

export default function ArticlePage() {
  const citation = 'The Editors. “The Archive Is Not the Village.” The Liberty Articulator, public founding draft, version 1.0, August 29, 2026.';
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'ScholarlyArticle',
    headline: articleTitle,
    description: articleDescription,
    author: { '@type': 'Organization', name: 'The Editors, The Liberty Articulator' },
    datePublished: '2026-08-29',
    dateModified: '2026-08-29',
    version: '1.0',
    inLanguage: 'en',
    isPartOf: { '@type': 'Periodical', name: 'The Liberty Articulator' },
    about: ['historical method', 'source criticism', 'archives', 'Marc Bloch'],
  };

  return (
    <main id="main-content" className="article-page">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <header className="article-header">
        <a className="back-link" href="/archive"><ArrowLeft size={16} /> Archive</a>
        <div className="article-meta">
          <span>History</span><span>Founding editorial</span><span>Public draft</span>
        </div>
        <h1>{articleTitle}</h1>
        <p className="article-subtitle">
          A prospectus for reasoning from surviving records without mistaking institutional memory for the lives it only partly contains.
        </p>
        <div className="article-byline">
          <p><strong>The Editors</strong><span>The Liberty Articulator</span></p>
          <dl>
            <div><dt>Published</dt><dd>29 August 2026</dd></div>
            <div><dt>Version</dt><dd>1.0</dd></div>
            <div><dt>Reading time</dt><dd>9 minutes</dd></div>
          </dl>
        </div>
      </header>

      <div className="article-status">
        <CircleAlert size={20} />
        <p><strong>Review status:</strong> Founding editorial; editorially reviewed, not externally peer reviewed. This status is part of the record.</p>
      </div>

      <div className="article-layout">
        <aside className="article-toc">
          <p>In this article</p>
          <nav aria-label="Article contents">
            <a href="#abstract">Abstract</a>
            <a href="#made-record">1. The made record</a>
            <a href="#testimony">2. Testimony and criticism</a>
            <a href="#silence">3. Arguing from silence</a>
            <a href="#response">4. The journal’s response</a>
            <a href="#source-ledger">Source ledger</a>
            <a href="#references">References</a>
          </nav>
          <div className="toc-metrics"><p>Discipline target<strong>History · 50%</strong></p><p>Method<strong>Source criticism</strong></p></div>
        </aside>

        <article className="article-body">
          <section className="abstract" id="abstract">
            <p className="eyebrow">Abstract</p>
            <p>
              Archives do not simply hold a past that waits to be retrieved. Records were made for particular purposes,
              selected by institutions, described through changing systems, and encountered through unequal conditions of access.
              This founding editorial sets out a method for distinguishing surviving evidence from the historical worlds an article seeks to explain.
              It proposes a public source ledger and a seven-question analytical rubric inspired by Marc Bloch.
            </p>
            <div className="keywords"><span>Historical method</span><span>Archives</span><span>Source criticism</span><span>Marc Bloch</span><span>Silence</span></div>
          </section>

          <section id="made-record">
            <p className="section-number">01 / The made record</p>
            <h2>What survives was first made.</h2>
            <p className="dropcap">
              A village does not enter an archive all at once. It arrives as tax assessments, court depositions,
              parish registers, maps, contracts, petitions, censuses, photographs, letters, and the later descriptions
              that make some of those objects findable. Each form answered a practical demand. Each admitted certain people,
              actions, and categories more readily than others.
            </p>
            <p>
              That observation does not make the record unusable. It makes provenance part of the evidence. A poor-relief ledger may
              establish that an officer recorded a payment under a named category on a given date. It does not, by itself, establish the
              whole economy of need, the recipient’s account of the encounter, or the experiences of people who never appeared in the ledger.
              The distinction between the statement of the record and the reach of the inference is where analysis begins.
            </p>
            <p>
              The journal therefore asks authors to identify the exact object used, its creator and administrative purpose,
              its path into custody, its present description, and the transformations—copying, transcription, translation,
              digitization, search, or excerpting—through which the author encountered it.
            </p>
            <blockquote>
              <p>The first question is not only “What does this source say?” but “What had to happen for this source to exist here, in this form, for this question?”</p>
              <cite>— Founding analytical rule</cite>
            </blockquote>
          </section>

          <figure className="article-figure">
            <img src="/og.png" alt="The Liberty Articulator title over faint engraved telescope and microscope motifs" width="1200" height="630" />
            <figcaption>
              Fig. 1 · The journal’s optical motifs represent scales of inquiry. This is original editorial artwork, not a historical source or reproduction.
            </figcaption>
          </figure>

          <section id="testimony">
            <p className="section-number">02 / Testimony and criticism</p>
            <h2>Evidence must be questioned without being theatrically distrusted.</h2>
            <p>
              Marc Bloch’s unfinished <em>Apologie pour l’histoire</em> organized the historian’s craft around observation,
              testimony, criticism, analysis, and causation.<sup><a href="#note-1" aria-label="See note 1">1</a></sup> An earlier address,
              “Critique historique et critique du témoignage,” likewise treated indirect knowledge and the discrimination of truth,
              error, and plausibility as central problems.<sup><a href="#note-2" aria-label="See note 2">2</a></sup>
            </p>
            <p>
              The useful lesson is not that testimony is always false or that suspicion is sophistication. Criticism is comparative.
              It tests a statement against the circumstances of its production, independent traces, internal consistency, material features,
              and alternative accounts. A source may be inaccurate about an event and unusually revealing about the categories through which
              its maker perceived that event. The historical question determines which feature matters.
            </p>
            <p>
              This is also why “primary source” is not a permanent honorific attached to an object. The American Historical Association’s
              professional standards emphasize that primary and secondary status depends in part on the question, and that primary evidence
              must be critically examined in relation to relevant secondary scholarship.<sup><a href="#note-3" aria-label="See note 3">3</a></sup>
              A later catalog, edition, or oral recollection can play different evidentiary roles in different inquiries.
            </p>
          </section>

          <aside className="article-callout">
            <p className="eyebrow">Evidence / inference check</p>
            <div><strong>The record supports</strong><p>A bounded statement tied to a retraceable object and locator.</p></div>
            <div><strong>The author infers</strong><p>An interpretation whose steps, comparisons, assumptions, and alternatives must be stated.</p></div>
          </aside>

          <section id="silence">
            <p className="section-number">03 / Arguing from silence</p>
            <h2>Absence becomes evidence only through a warranted expectation.</h2>
            <p>
              “The archive is silent” is not yet an explanation. A missing name may reflect non-participation, deliberate exclusion,
              lost volumes, inconsistent spelling, catalog structure, a search interface, an unconsulted related series, or the simple fact
              that the relevant action did not ordinarily produce a record. To argue from silence, an author must explain why a trace would
              normally be expected, how complete the surviving series is, and which alternative causes of absence have been tested.
            </p>
            <p>
              Finding aids help establish the architecture of survival. The Archives nationales guide to historians’ private papers,
              for example, identifies the Marc Bloch fonds and the files containing manuscript and working material for the <em>Apologie</em>.
              It does not provide the manuscript itself, guarantee access, or authorize reproduction.<sup><a href="#note-4" aria-label="See note 4">4</a></sup>
              A rigorous citation records that distinction instead of turning a catalog description into the object described.
            </p>
            <p>
              Silence also has a politics. Institutions were uneven in whom they observed, believed, classified, compensated, punished,
              preserved, and described. Yet an account of power cannot be inferred from institutional bias alone. The author still owes the reader
              a demonstrated mechanism, comparison, chronology, and engagement with evidence that might resist the proposed interpretation.
            </p>
          </section>

          <section id="response">
            <p className="section-number">04 / The journal’s response</p>
            <h2>Make the reasoning inspectable.</h2>
            <p>
              The Liberty Articulator’s response is procedural. Every long-form article will carry a source ledger beside its bibliography.
              The ledger records the exact edition or archival unit used, the locator, the role the source plays, the state of verification,
              known mediation, and rights or access limits. It binds evidence to a particular article version so that later corrections do not
              erase the route by which an earlier conclusion was reached.
            </p>
            <p>
              A second device, the Bloch Lens, asks seven public questions about the inquiry, surviving evidence, silence and mediation,
              comparison, inference, counterevidence, and revision conditions. Reviewers will not be asked merely whether an article “feels analytical.”
              They will assess whether each required decision is explicit and adequately supported.
            </p>
            <p>
              None of this makes error impossible. It makes error easier to locate, contest, and correct. The journal’s scholarly standard is not
              invulnerability. It is a record strong enough to be examined by someone who was not present when the editorial decision was made.
            </p>
          </section>

          <section className="source-ledger-article" id="source-ledger">
            <p className="section-number">Source ledger / Version 1.0</p>
            <h2>Material sources used in this editorial.</h2>
            <div className="article-ledger-table" role="table" aria-label="Article source ledger">
              <div className="ledger-head" role="row"><span role="columnheader">Source</span><span role="columnheader">Use</span><span role="columnheader">Status</span></div>
              <div role="row"><span role="cell"><strong>Bloch, <em>Apologie</em></strong><small>UQAC digital edition from the 1952 edition</small></span><span role="cell">Methodological structure; no direct quotation</span><span role="cell">Consulted · rights not assumed</span></div>
              <div role="row"><span role="cell"><strong>Bloch, “Critique historique”</strong><small>1914 address, published posthumously in 1950</small></span><span role="cell">Early formulation of testimony criticism</span><span role="cell">Context caveat recorded</span></div>
              <div role="row"><span role="cell"><strong>AHA professional standards</strong><small>Amended through January 2023</small></span><span role="cell">Primary/secondary relation and retraceability</span><span role="cell">Consulted 29 Aug 2026</span></div>
              <div role="row"><span role="cell"><strong>Archives nationales finding aid</strong><small>Marc Bloch fonds references</small></span><span role="cell">Example of description versus archival object</span><span role="cell">Finding aid only · access restricted</span></div>
            </div>
          </section>

          <section className="article-notes" id="references">
            <p className="section-number">Notes & references</p>
            <ol>
              <li id="note-1"><span>1</span><p>Marc Bloch, <a href="https://classiques.uqam.ca/classiques/bloch_marc/apologie_histoire/apologie_histoire.html" target="_blank" rel="noreferrer"><em>Apologie pour l’histoire ou Métier d’historien</em> <ArrowUpRight size={13} /></a>, digital edition based on the 1952 second edition. The work was unfinished and published posthumously.</p></li>
              <li id="note-2"><span>2</span><p>Marc Bloch, <a href="https://doi.org/10.3406/ahess.1950.1781" target="_blank" rel="noreferrer">“Critique historique et critique du témoignage” <ArrowUpRight size={13} /></a>, delivered in 1914 and published by Lucien Febvre in 1950; Febvre noted that Bloch might have revised some formulations.</p></li>
              <li id="note-3"><span>3</span><p>American Historical Association, <a href="https://www.historians.org/resource/statement-on-standards-of-professional-conduct/" target="_blank" rel="noreferrer">“Statement on Standards of Professional Conduct” <ArrowUpRight size={13} /></a>, amended through January 2023.</p></li>
              <li id="note-4"><span>4</span><p>Archives nationales, <a href="https://www.archivesnationales.culture.gouv.fr/chan/chan/AP-pdf/AP-thematique-historiens-et-erudits.pdf" target="_blank" rel="noreferrer">“Papiers d’historiens et d’érudits” <ArrowUpRight size={13} /></a>, identifying the Marc Bloch fonds at AB XIX 3796–3852 and 4270–4275.</p></li>
            </ol>
          </section>

          <section className="cite-article">
            <p className="section-number">Suggested citation</p>
            <CitationCopy citation={citation} />
          </section>
        </article>

        <aside className="article-record">
          <div><FileText size={20} /><p><span>Article type</span><strong>Founding editorial</strong></p></div>
          <div><CheckCircle2 size={20} /><p><span>Review status</span><strong>Not externally reviewed</strong></p></div>
          <div><GitCommitHorizontal size={20} /><p><span>Current record</span><strong>Version 1.0 · no corrections</strong></p></div>
          <a href="/standards#corrections">Correction policy <ArrowUpRight size={15} /></a>
        </aside>
      </div>

      <section className="version-history" aria-labelledby="version-title">
        <div><p className="eyebrow">Editorial history</p><h2 id="version-title">Version record</h2></div>
        <ol>
          <li><span>29 Aug 2026</span><div><strong>Version 1.0 published</strong><p>Founding editorial issued as a public draft. Editorial review only; no external peer review.</p></div></li>
        </ol>
      </section>
    </main>
  );
}
