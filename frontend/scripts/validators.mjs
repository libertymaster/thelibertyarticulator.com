import fs from 'node:fs';
import path from 'node:path';
import Ajv2020 from 'ajv/dist/2020.js';
import standaloneCode from 'ajv/dist/standalone/index.js';

// Compile at BUILD time: the browser does not need unsafe-eval or an AJV runtime.
for (const name of ['sources', 'archive', 'chronology']) {
  const schema = JSON.parse(fs.readFileSync(path.join('..', 'contracts', `${name}.schema.json`), 'utf8'));
  const ajv = new Ajv2020({ code: { source: true, esm: true }, allErrors: true, strict: true });
  const validate = ajv.compile(schema);
  fs.mkdirSync('src/generated', { recursive: true });
  fs.writeFileSync(`src/generated/validate_${name}.js`, standaloneCode(ajv, validate));
  fs.writeFileSync(`src/generated/validate_${name}.d.ts`, 'declare const validate: (value: unknown) => boolean;\nexport default validate;\n');
}
