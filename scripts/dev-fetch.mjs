import { spawn } from 'node:child_process';
import { setTimeout as wait } from 'node:timers/promises';

const windowsViteBin = String.raw`node_modules\.bin\vite.cmd`;
const isWindows = process.platform === 'win32';
const command = isWindows ? 'cmd.exe' : 'node';
const bin = isWindows ? windowsViteBin : 'node_modules/.bin/vite';
const args = isWindows
  ? ['/c', bin, 'dev', '--host', '0.0.0.0', '--port', '8080']
  : [bin, 'dev', '--host', '0.0.0.0', '--port', '8080'];
const devProcess = spawn(command, args, {
  cwd: process.cwd(),
  stdio: ['ignore', 'inherit', 'inherit'],
});

devProcess.on('error', (error) => {
  console.error('Dev server failed to start:', error instanceof Error ? error.message : error);
  cleanup();
  process.exit(1);
});

let homeHtml = '';

const cleanup = () => {
  if (!devProcess.killed) {
    devProcess.kill('SIGINT');
  }
};

process.on('exit', cleanup);
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

const deadline = Date.now() + 15000;
await wait(1000);
while (Date.now() < deadline) {
  try {
    const res = await fetch('http://localhost:8080');
    homeHtml = await res.text();
    console.log(homeHtml);
    break;
  } catch (error) {
    if (error instanceof Error) {
      console.error('Fetch attempt failed:', error.message);
    } else {
      console.error('Fetch attempt failed:', error);
    }
    await wait(1000);
  }
}
if (!homeHtml) {
  console.error('Failed to fetch home page after several retries');
}
cleanup();
