import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';

// Compile the production helper in memory; no extra runner or generated files.
const source = readFileSync(
	new URL('../src/components/chat/input-content.ts', import.meta.url),
	'utf8',
);
const { outputText } = ts.transpileModule(source, {
	compilerOptions: { module: ts.ModuleKind.ESNext },
});
const { hasInputContent } = await import(
	`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
);

test('an empty or whitespace-only composer cannot send', () => {
	assert.equal(hasInputContent('', []), false);
	assert.equal(hasInputContent(' \n ', []), false);
});
test('a completed attachment can be sent without accompanying text', () => {
	assert.equal(hasInputContent('', [{ status: 'done' }]), true);
	assert.equal(hasInputContent('  ', [{ status: 'done' }]), true);
});
test('processing or removed attachments do not count as message content', () => {
	assert.equal(hasInputContent('', [{ status: 'processing' }]), false);
	assert.equal(hasInputContent('', []), false);
});
test('ordinary text and mixed messages retain their send behavior', () => {
	assert.equal(hasInputContent('hello', []), true);
	assert.equal(hasInputContent('hello', [{ status: 'done' }]), true);
});
