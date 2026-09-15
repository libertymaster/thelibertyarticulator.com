import { mount } from './mount';
import type { SourcesPayload } from './generated/contracts';
import validate from './generated/validate_sources.js';
import { SourceExplorer } from './components/SourceExplorer';
mount<SourcesPayload>('sources-island', validate, data => <SourceExplorer data={data} />);
