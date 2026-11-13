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
const profileName=args.includes('--graphics-profile')?parameter('--graphics-profile'):(args.includes('--software')?'software':'default');
const profiles=JSON.parse(fs.readFileSync(new URL('./graphics_profiles.json',import.meta.url),'utf8'));
if(!profiles[profileName]?.hosts.includes('electron'))throw new Error('Unsupported graphics profile');
if(args.includes('--software') && profileName!=='software')throw new Error('Conflicting graphics requests');
for(const flag of profiles[profileName].chromium_switches) {
  const at=flag.indexOf('=');
  app.commandLine.appendSwitch(at<0?flag:flag.slice(0,at),at<0?undefined:flag.slice(at+1));
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
