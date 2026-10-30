import assert from 'node:assert/strict';
import { reconcileChatModel } from './chat-model-selection';

// Adding/reordering a model must not override an explicit selection.
let selected = reconcileChatModel('', ['deepseek-flash']);
assert.equal(selected, 'deepseek-flash');
selected = reconcileChatModel(selected, ['deepseek-v4.1-flash', 'deepseek-flash']);
assert.equal(selected, 'deepseek-flash');
selected = 'deepseek-v4.1-flash';
assert.equal(reconcileChatModel(selected, ['deepseek-flash', selected]), selected);
assert.equal(reconcileChatModel(selected, ['deepseek-flash']), 'deepseek-flash');
assert.equal(reconcileChatModel(selected, []), '');
console.log('chat model selection tests passed');
