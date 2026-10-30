import assert from 'node:assert/strict';
import { requireChatEventStream } from './chat-stream-response';

async function run() {
  await requireChatEventStream(new Response('data: {}\n\n', {
    headers: { 'Content-Type': 'text/event-stream; charset=utf-8' },
  }));
  for (const status of [200, 400]) {
    await assert.rejects(requireChatEventStream(new Response(JSON.stringify({
      success: false, err_msg: 'The file_path input is invalid.',
    }), { status, headers: { 'Content-Type': 'application/json; charset=utf-8' } })), /文件路径格式无效/);
  }
  await assert.rejects(requireChatEventStream(new Response('bad gateway', { status: 502 })), /HTTP 502/);
  await assert.rejects(requireChatEventStream(new Response('not a stream')), /请求未能开始/);
  await assert.rejects(requireChatEventStream(new Response('{', {
    status: 500, headers: { 'Content-Type': 'application/json' },
  })), /HTTP 500/);
  console.log('chat stream response tests passed');
}
void run();
