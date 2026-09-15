import { mount } from './mount';
import type { ChronologyPayload } from './generated/contracts';
import validate from './generated/validate_chronology.js';
import { Chronology } from './components/Chronology';
mount<ChronologyPayload>('chronology-island', validate, data => <Chronology data={data} />);
