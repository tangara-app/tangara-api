// Tangara API example for Node.js 22+. No packages required.
import { randomUUID } from 'node:crypto';
import { open, readFile } from 'node:fs/promises';
import { setTimeout as sleep } from 'node:timers/promises';

async function api(method, path, body) {
  const key = process.env.TANGARA_API_KEY;
  if (!key) throw new Error('Set TANGARA_API_KEY');
  const base = (process.env.TANGARA_API_URL || 'https://tangara.app/api/v1').replace(/\/$/, '');
  const response = await fetch(base + path, {
    method,
    headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(30_000),
    redirect: 'error',
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  return response.json();
}

const show = value => console.log(JSON.stringify(value, null, 2));

async function main() {
  const [command, argument] = process.argv.slice(2);
  if (command === 'models') return show(await api('GET', '/models'));
  if (!argument || !['prepare', 'submit', 'wait'].includes(command)) {
    throw new Error('Usage: video.mjs models | prepare FILE | submit FILE | wait TASK_UUID');
  }
  if (command === 'prepare') {
    const request = {
      client_request_id: randomUUID(),
      prompt: process.env.TANGARA_PROMPT || 'A hummingbird hovers beside a flower in soft morning light.',
      profile_id: process.env.TANGARA_PROFILE_ID || 'ltx-2.5-720p-v3',
      duration_seconds: Number(process.env.TANGARA_DURATION_SECONDS || 5),
      audio: true,
      seed: 42,
    };
    if (!Number.isInteger(request.duration_seconds)) throw new Error('Duration must be an integer');
    for (const field of ['first_image_id', 'last_image_id']) {
      const value = process.env[`TANGARA_${field.toUpperCase()}`];
      if (value) request[field] = value;
    }
    if (request.last_image_id && !request.first_image_id) throw new Error('An end frame requires a first frame');
    const quote = await api('POST', '/quote', {
      profile_id: request.profile_id, duration_seconds: request.duration_seconds,
    });
    request.expected_price = { version: quote.version, amount: quote.amount };
    const file = await open(argument, 'wx', 0o600);
    try {
      await file.writeFile(JSON.stringify(request, null, 2));
      await file.sync();
    } finally { await file.close(); }
    show(quote);
    console.log(`Saved ${argument}. Review the quote, then use submit to queue paid generation.`);
  } else if (command === 'submit') {
    show(await api('POST', '/tasks', JSON.parse(await readFile(argument, 'utf8'))));
  } else {
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(argument)) {
      throw new Error('Provide a task UUID');
    }
    const deadline = Date.now() + 3_600_000;
    while (Date.now() < deadline) {
      const task = await api('GET', `/tasks/${argument}`);
      console.error(task.result, task.stage || '');
      if (task.result === 'succeeded') return show(await api('GET', `/tasks/${argument}/result`));
      if (task.result === 'failed') throw new Error(task.error_message || 'Generation failed');
      await sleep(5000);
    }
    throw new Error('Polling stopped after one hour. The task remains saved; run wait again.');
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
