import { mount } from './mount';
import type { ArchivePayload } from './generated/contracts';
import validate from './generated/validate_archive.js';
import { ResearchArchive } from './components/ResearchArchive';
mount<ArchivePayload>('archive-island', validate, data => <ResearchArchive data={data} />);
