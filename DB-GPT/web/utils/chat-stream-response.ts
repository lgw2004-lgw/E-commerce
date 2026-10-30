/** Reject HTTP/business errors before attempting to read them as SSE. */
export async function requireChatEventStream(response: Response): Promise<void> {
  const contentType = response.headers.get('content-type')?.split(';')[0].trim().toLowerCase();
  if (response.ok && contentType === 'text/event-stream' && response.body) return;

  let detail = '';
  if (contentType === 'application/json') {
    const payload = await response.json().catch(() => null);
    const value = payload?.err_msg || payload?.detail?.message || payload?.detail || payload?.error?.message;
    if (typeof value === 'string') detail = value;
  }
  if (detail === 'The file_path input is invalid.') {
    detail = '文件路径格式无效，请重新选择文件后重试。';
  }
  throw new Error(detail || `请求未能开始，请重试（HTTP ${response.status}）。`);
}
