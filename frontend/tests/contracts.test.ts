import { describe, it, expect } from 'vitest';
import validateSources from '../src/generated/validate_sources.js';
import validateArchive from '../src/generated/validate_archive.js';
import validateChronology from '../src/generated/validate_chronology.js';
import sources from '../../contracts/fixtures/sources.json';
import archive from '../../contracts/fixtures/archive.json';
import chronology from '../../contracts/fixtures/chronology.json';
import { safeHref, rangeError, parsePayload } from '../src/lib';

describe('runtime contracts',()=>{
  it('accepts backend fixture payloads',()=>{
    expect(validateSources(sources)).toBe(true);
    expect(validateArchive(archive)).toBe(true);
    expect(validateChronology(chronology)).toBe(true);
  });
  it('rejects unexpected secret fields',()=>expect(validateSources({...sources,token:'not-public'})).toBe(false));
  it('fails closed on schema mismatch',()=>expect(()=>parsePayload({},validateArchive)).toThrow());
});
describe('safe reader helpers',()=>{
  it('rejects active and protocol-relative URLs',()=>{
    for(const url of ['javascript:alert(1)','data:text/html,test','//evil.example','/\\evil.example']) expect(safeHref(url)).toBeUndefined();
  });
  it('allows local anchors and HTTPS',()=>{
    expect(safeHref('#note-1')).toBe('#note-1');
    expect(safeHref('/archive/')).toBe('/archive/');
    expect(safeHref('https://example.org/')).toBe('https://example.org/');
  });
  it('validates BCE and CE ranges',()=>{
    expect(rangeError('-100','100')).toBe('');
    expect(rangeError('0','100')).not.toBe('');
    expect(rangeError('100','-100')).not.toBe('');
  });
});
