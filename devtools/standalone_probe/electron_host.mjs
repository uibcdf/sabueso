import { app, BrowserWindow, session } from 'electron';
import fs from 'node:fs';

const args = process.argv.slice(2);
const parameter = name => args[args.indexOf(name) + 1];
const bootstrap = JSON.parse(fs.readFileSync(parameter('--bootstrap'), 'utf8'));
if (new URL(bootstrap.url).hostname !== '127.0.0.1') throw new Error('Owned loopback backend required');
app.setPath('userData', parameter('--profile'));
app.commandLine.appendSwitch('remote-debugging-address', '127.0.0.1');
app.commandLine.appendSwitch('remote-debugging-port', parameter('--cdp-port'));
app.commandLine.appendSwitch('num-raster-threads', '1');
if (args.includes('--namespace-sandbox')) app.commandLine.appendSwitch('disable-setuid-sandbox');
if (args.includes('--software')) {
  app.commandLine.appendSwitch('use-gl', 'angle');
  app.commandLine.appendSwitch('use-angle', 'swiftshader');
  app.commandLine.appendSwitch('enable-unsafe-swiftshader');
  app.commandLine.appendSwitch('disable-gpu-compositing');
}
app.whenReady().then(async () => {
session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
  const url = new URL(details.url);
  callback({cancel: ['http:', 'https:', 'ws:', 'wss:'].includes(url.protocol) && url.hostname !== '127.0.0.1'});
});
const window = new BrowserWindow({
  width: 1280, height: 900, useContentSize: true, show: true,
  title: 'Sabueso — standalone integration probe',
  webPreferences: {contextIsolation: true, nodeIntegration: false, sandbox: true},
});
window.removeMenu();
window.webContents.setWindowOpenHandler(() => ({action: 'deny'}));
await window.loadURL(bootstrap.url);
});
app.on('window-all-closed', () => app.quit());
process.on('SIGTERM', () => app.quit());
