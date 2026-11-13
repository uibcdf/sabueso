// One fresh process cohort. Both hosts run this exact journey and frontend build.
import { connectNative } from './cdp_driver.mjs';
import { connectTauri } from './tauri_driver.mjs';
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import {createHash} from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const value = name => args[args.indexOf(name) + 1];
const host = value('--host');
const labNoSandbox = args.includes('--lab-no-sandbox');
if (!['qt', 'electron', 'tauri'].includes(host)) throw new Error('Expected qt, electron or tauri');
const inputs = path.resolve(value('--inputs'));
const output = path.resolve(value('--output'));
const python = value('--python');
fs.mkdirSync(output, {recursive: false});
const privateBootstrap = path.join(output, 'bootstrap-private.json');
const children = [];
const report = {format: 'sabueso.standalone_host_observation@1', host,
  scope: 'Linux Xvfb; explicitly requested software rendering; development editable cohort',
  chromium_sandbox: labNoSandbox ? 'disabled explicitly for trusted local experiment only' : 'default configuration',
  checks: {}, timings: {}, phases: [], errors: [], external_requests: [], state: 'running'};
let browser;
let page;
let capability = '';
let fullUrl = '';
const clean = text => String(text).replaceAll(capability || '__no_capability__', '<redacted>')
  .replace(/(?:https?|wss?):\/\/127\.0\.0\.1:\d+/g, '<loopback>')
  .replace(/([#?&]token=)[^\s&#"]+/g, '$1<redacted>');
const wall = () => Date.now() / 1000;
const started = performance.now();
function sourceDigests(directory, prefix='') {
  const result={};
  for(const entry of fs.readdirSync(directory,{withFileTypes:true})) {
    if(['node_modules','target','gen','__pycache__'].includes(entry.name))continue;
    const name=prefix+entry.name, file=path.join(directory,entry.name);
    if(entry.isDirectory())Object.assign(result,sourceDigests(file,name+'/'));
    else if(entry.isFile() && !name.endsWith('.map'))result[name]=createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  }
  return result;
}
report.probe_source_digests=sourceDigests(here);
const inputManifest=JSON.parse(fs.readFileSync(path.join(inputs,'inputs.json'),'utf8'));
function protectedInputsMatch() {
  return Object.entries(inputManifest.files).every(([name,digest])=>
    createHash('sha256').update(fs.readFileSync(path.join(inputs,name))).digest('hex')===digest);
}
if(!protectedInputsMatch())throw new Error('Prepared public inputs changed');
function launch(command, argv, name, env = process.env, extraPipes = false) {
  const log = fs.openSync(path.join(output, `${name}.log`), 'wx');
  const child = spawn(command, argv, {env, stdio: extraPipes ? ['ignore', log, log, 'pipe'] : ['ignore', log, log]});
  child.once('error', error => report.errors.push(clean(error.stack)));
  children.push(child);
  fs.closeSync(log);
  return child;
}
async function until(predicate, description, timeout = 60000) {
  const end = performance.now() + timeout;
  while (performance.now() < end) {
    const found = await predicate();
    if (found) return found;
    await delay(100);
  }
  throw new Error(`Timed out: ${description}`);
}
async function freePort() {
  const server = net.createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}
async function state() {
  return page.evaluate(() => fetch('/api/state', {cache: 'no-store'}).then(r => r.json()));
}
async function click(name) {
  await clickElement(page.getByRole('button', {name, exact: true}),
    ['Back','Save reading','Reopen reading','Select annotated site','Open independent view','Close independent view'].includes(name));
}
async function clickElement(element, isAction = true) {
  const completed = await page.evaluate(() => window.__sabuesoProbe.metrics.actions_completed);
  await element.click();
  if (isAction) await page.waitForFunction(n => window.__sabuesoProbe.metrics.actions_completed > n, completed);
  await delay(80);
  await page.waitForFunction(() => !window.__sabuesoProbe.getState()?.busy);
  const current = await page.evaluate(() => window.__sabuesoProbe.getState());
  if (/^(422|500|403):/.test(current.message)) throw new Error(current.message);
}
async function screenshot(phase) {
  await page.screenshot({path: path.join(output, `${phase}.png`)});
  if (host === 'qt') {
    fs.writeFileSync(path.join(output,'native-capture-request.json'), JSON.stringify({phase}));
    await until(() => fs.existsSync(path.join(output,`${phase}-qt-native.png`)), 'Qt native widget capture', 5000);
  }
}
function cameraIdentity(camera) {
  if (!camera) return null;
  return Object.fromEntries(['position', 'target', 'up', 'mode', 'fov', 'radius', 'radiusMax'].map(k => [k, camera[k]]));
}
async function phase(name, ms) {
  const begin = wall();
  await delay(ms);
  report.phases.push({name, started_wall_s: begin, ended_wall_s: wall()});
}

try {
  const renderEnv = {...process.env, LIBGL_DRIVERS_PATH:'/usr/lib/x86_64-linux-gnu/dri', LIBGL_ALWAYS_SOFTWARE:'1'};
  const xvfb = launch('Xvfb', ['-displayfd', '3', '-screen', '0', '1600x1000x24', '-nolisten', 'tcp'], 'xvfb', renderEnv, true);
  let display = '';
  xvfb.stdio[3].on('data', data => {display += data.toString();});
  await until(() => /^\d+\n/.test(display), 'owned Xvfb display');
  const env = {...renderEnv, DISPLAY: `:${display.trim()}`, QT_QPA_PLATFORM: 'xcb'};
  if (args.includes('--system-sandbox-helper')) {
    if (labNoSandbox || args.includes('--namespace-sandbox')) throw new Error('Conflicting sandbox profiles');
    const helper = '/opt/google/chrome/chrome-sandbox';
    const info = fs.statSync(helper);
    if (info.uid !== 0 || !(info.mode & 0o4000) || (info.mode & 0o022)) throw new Error('Expected a protected root-owned system helper');
    env.CHROME_DEVEL_SANDBOX = helper;
    report.chromium_sandbox = 'existing system SUID helper; no global configuration change';
  }
  const backend = launch(python, [path.join(here, 'backend.py'), '--inputs', inputs,
    '--output', path.join(output, 'backend'), '--bootstrap', privateBootstrap], 'backend', env);
  await until(() => {
    if (backend.exitCode !== null) throw new Error(`Backend exited ${backend.exitCode}; inspect retained log`);
    if (!fs.existsSync(privateBootstrap)) return false;
    try {return JSON.parse(fs.readFileSync(privateBootstrap, 'utf8'));} catch {return false;}
  }, 'Python backend bootstrap');
  const bootstrap = JSON.parse(fs.readFileSync(privateBootstrap, 'utf8'));
  fullUrl = bootstrap.url;
  capability = new URL(fullUrl).hash.slice(1).split('token=')[1];
  report.timings.backend_process_to_ready_ms = performance.now() - started;
  const cdpPort = await freePort();
  const hostStarted = performance.now();
  let native;
  if (host === 'qt') {
    native = launch(python, [path.join(here, 'qt_host.py'), '--bootstrap', privateBootstrap,
      '--cdp-port', String(cdpPort), '--software', '--capture-dir',output,
      ...(labNoSandbox ? ['--lab-no-sandbox'] : [])], 'native-host', env);
  } else if (host === 'electron') {
    const electron = (await import('electron')).default;
    native = launch(electron, [...(args.includes('--namespace-sandbox') ? ['--disable-setuid-sandbox'] : []),
      ...(labNoSandbox ? ['--no-sandbox'] : []),
      path.join(here, 'electron_host.mjs'), '--bootstrap', privateBootstrap,
      '--cdp-port', String(cdpPort), '--profile', path.join(output, 'electron-profile'), '--software',
      ...(args.includes('--namespace-sandbox') ? ['--namespace-sandbox'] : [])], 'native-host', env);
  } else {
    const nativeEnv = {...env,SABUESO_PROBE_BOOTSTRAP:privateBootstrap,TAURI_WEBDRIVER_PORT:String(cdpPort),
      XDG_CACHE_HOME:path.join(output,'tauri-cache'),XDG_DATA_HOME:path.join(output,'tauri-data')};
    if (args.includes('--tauri-native-root')) {
      const root=path.resolve(value('--tauri-native-root'));
      nativeEnv.LD_LIBRARY_PATH=path.join(root,'usr/lib/x86_64-linux-gnu');
      nativeEnv.WEBKIT_EXEC_PATH=path.join(root,'usr/lib/x86_64-linux-gnu/webkit2gtk-4.1');
      nativeEnv.GIO_EXTRA_MODULES=path.join(root,'usr/lib/x86_64-linux-gnu/gio/modules');
    }
    if(labNoSandbox) {
      nativeEnv.WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS='1';
      report.chromium_sandbox='not applicable; WebKit sandbox explicitly disabled for the trusted local experiment';
    } else report.chromium_sandbox='not applicable; WebKit default requested';
    native=launch(path.resolve(value('--tauri-binary')),[],'native-host',nativeEnv);
  }
  await until(async () => {
    if (native.exitCode !== null || native.signalCode !== null) throw new Error(`Native host exited ${native.exitCode ?? native.signalCode}; inspect retained log`);
    try {return (await fetch(`http://127.0.0.1:${cdpPort}/${host==='tauri'?'status':'json/version'}`)).ok;} catch {return false;}
  }, 'native host CDP');
  browser = host==='tauri' ? await connectTauri(`http://127.0.0.1:${cdpPort}`,python,env)
    : await connectNative(`http://127.0.0.1:${cdpPort}`);
  page = await until(() => browser.contexts()[0]?.pages()[0], 'workspace page');
  page.on('pageerror', error => report.errors.push(clean(error.stack)));
  page.on('console', message => {if (message.type() === 'error') report.errors.push(clean(message.text()));});
  page.on('request', request => {
    const url = new URL(request.url());
    if (['http:', 'https:'].includes(url.protocol) && url.hostname !== '127.0.0.1') report.external_requests.push(clean(request.url()));
  });
  await page.waitForFunction(() => document.documentElement.dataset.probeReady === 'true', null, {timeout: 60000});
  report.timings.host_to_usable_card_ms = performance.now() - hostStarted;
  report.timings.full_cohort_to_usable_card_ms = performance.now() - started;
  await until(async () => (await state()).structure_complete, 'real molecular structure completion');
  const frame = await until(() => page.frames().find(f => f !== page.mainFrame() && f.url().includes('/session/client')), 'live Viewer frame');
  const canvas = frame.locator('canvas').first();
  await canvas.waitFor({state: 'visible'});
  if(host==='tauri') await page.waitForFunction(()=>!!window.__sabuesoObservedFrame?.graphics);
  const graphics = host==='tauri' ? await page.evaluate(()=>window.__sabuesoObservedFrame.graphics) : await canvas.evaluate(canvas => {
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    if (!gl) return {webgl: false};
    const debug = gl.getExtension('WEBGL_debug_renderer_info');
    const pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
    gl.readPixels(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    const colors = new Set();
    for (let i = 0; i < pixels.length; i += 4 * 17) colors.add(`${pixels[i]},${pixels[i+1]},${pixels[i+2]},${pixels[i+3]}`);
    return {webgl: true, width: gl.drawingBufferWidth, height: gl.drawingBufferHeight,
      renderer: debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
      version: gl.getParameter(gl.VERSION), sampled_colors: colors.size, error: gl.getError()};
  });
  report.graphics = graphics;
  report.webgpu = host==='tauri' ? await page.evaluate(()=>window.__sabuesoObservedFrame.webgpu) : await frame.evaluate(async () => {
    const result = {secure_context:isSecureContext, api_exposed:!!navigator.gpu, adapter_available:false};
    if (!navigator.gpu) return result;
    try {
      const adapter = await Promise.race([navigator.gpu.requestAdapter(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('adapter timeout')), 3000))]);
      result.adapter_available = !!adapter;
      if (adapter) {
        const info = adapter.info;
        result.adapter = info ? {vendor:info.vendor, architecture:info.architecture,
          device:info.device, description:info.description, fallback:info.isFallbackAdapter} : null;
      }
    } catch (error) { result.error = String(error); }
    return result;
  });
  if (!graphics.webgl || graphics.sampled_colors < 3) throw new Error('A real drawn molecular canvas was not established');
  report.timings.full_cohort_to_observed_model_ms = performance.now() - started;
  report.browser = await page.evaluate(() => ({user_agent: navigator.userAgent, width: innerWidth, height: innerHeight, dpr: devicePixelRatio}));
  report.checks.real_model_drawn = true;
  await screenshot('initial-workspace');

  await clickElement(page.locator('[data-topic="sequence"]'));
  const reading = await page.evaluate(() => window.__sabuesoProbe.getState().panel);
  await clickElement(page.getByRole('button', {name: 'Sources / questions', exact: true}).first());
  report.checks.original_source_route = (await page.evaluate(() => window.__sabuesoProbe.getState().panel.view_ref)) !== reading.view_ref;
  await clickElement(page.getByRole('button', {name:'Open',exact:true}).first());
  report.checks.original_source_record_open = await page.evaluate(() => window.__sabuesoProbe.getState().panel.is_source_assertion === true);
  await click('Back');
  await click('Back');
  report.checks.exact_return = (await page.evaluate(() => window.__sabuesoProbe.getState().panel.view_ref)) === reading.view_ref;
  if (!report.checks.original_source_route || !report.checks.exact_return) throw new Error('Original source/return navigation failed');
  await click('Save reading');
  await click('Reopen reading');
  const reopened = await page.evaluate(() => window.__sabuesoProbe.getState().panel);
  report.saved_reading_validation = reopened.reopen_validation;
  report.checks.original_saved_reading = reopened.mode === 'saved' && reopened.result_ref === reading.result_ref
    && !!reopened.reopen_validation && Object.values(reopened.reopen_validation).every(Boolean);
  if (!report.checks.original_saved_reading) throw new Error('Original saved reading failed');
  await click('Select annotated site');
  await until(async () => (await state()).active_selection.length > 0, 'source annotation -> molecular selection');
  await delay(700);
  const selected = await state();
  report.selection = {atom_indices: selected.active_selection};
  report.checks.source_to_molecular_selection = true;
  const box = await canvas.boundingBox();
  for (const [dx, dy] of [[0, 0], [30, 0], [-30, 0], [0, 30], [0, -30], [60, 30], [-60, -30], [90, 0], [-90, 0]]) {
    await canvas.click({position: {x: box.width / 2 + dx, y: box.height / 2 + dy}});
    await delay(200);
    const picked = (await state()).pick;
    if (picked?.atom_indices.length) {report.pick = picked; break;}
  }
  if (!report.pick) throw new Error('Real pointer picking did not reach the Python/source context');
  report.checks.molecular_pick_to_original_context = true;
  await screenshot('selected-workspace');
  await delay(700);
  const before = await state();
  const metricsBefore = await page.evaluate(() => ({...window.__sabuesoProbe.metrics}));
  await phase('visible_settled', 3000);
  await click('Hide molecule');
  await delay(400);
  await phase('hidden_retained', 3000);
  await click('Show molecule');
  const repetitions = args.includes('--quick-calibration') ? 0 : 20;
  for (let index = 0; index < repetitions; index++) {
    for (const name of ['Float molecule', 'Dock molecule', 'Hide molecule', 'Show molecule', 'Float reading', 'Dock reading']) {
      await click(name);
      await delay(70);
    }
  }
  await delay(700);
  const after = await state();
  const metricsAfter = await page.evaluate(() => ({...window.__sabuesoProbe.metrics}));
  report.lifecycle = {repetitions, before: metricsBefore, after: metricsAfter,
    registrations_before: before.client_registrations, registrations_after: after.client_registrations,
    camera_before: cameraIdentity(before.camera), camera_after: cameraIdentity(after.camera)};
  report.checks.retained_iframe_lifetime = metricsAfter.iframe_loads === metricsBefore.iframe_loads
    && metricsAfter.molecule_mounts === metricsBefore.molecule_mounts
    && metricsAfter.molecule_unmounts === metricsBefore.molecule_unmounts
    && after.client_registrations === before.client_registrations;
  report.checks.camera_continuity = !!before.camera && JSON.stringify(cameraIdentity(before.camera)) === JSON.stringify(cameraIdentity(after.camera));
  report.checks.selection_continuity = JSON.stringify(before.active_selection) === JSON.stringify(after.active_selection);
  if (!report.checks.retained_iframe_lifetime || !report.checks.camera_continuity || !report.checks.selection_continuity) throw new Error('A molecular lifecycle continuity check failed');
  await page.getByRole('button', {name: 'Float reading', exact: true}).focus();
  await page.keyboard.press('Enter');
  await delay(300);
  report.checks.keyboard_layout_action = await page.evaluate(() => window.__sabuesoProbe.api.getPanel('reading').api.location.type === 'floating');
  await click('Dock reading');
  report.layout_serialization_bytes = await page.evaluate(() => JSON.stringify(window.__sabuesoProbe.api.toJSON()).length);
  await screenshot('final-workspace');
  const survivorBefore = await state();
  await click('Open independent view');
  await until(async () => (await state()).independent_ready, 'independent real molecular view');
  await phase('two_independent_views', 3000);
  await click('Close independent view');
  await delay(700);
  const survivorAfter = await state();
  report.checks.independent_view_close = !survivorAfter.independent_exists && survivorAfter.structure_complete
    && survivorAfter.client_registrations === survivorBefore.client_registrations
    && JSON.stringify(cameraIdentity(survivorAfter.camera)) === JSON.stringify(cameraIdentity(survivorBefore.camera));
  const invalidation = await page.evaluate(async () => {
    const action = name => fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});
    const replacement = await action('replace_model_control');
    if (!replacement.ok) throw new Error(`Replacement control failed: ${replacement.status}`);
    const state = await (await fetch('/api/state')).json();
    const refusal = await action('select_active_site');
    return {binding_valid:state.binding_valid,pick:state.pick,selection_status:refusal.status};
  });
  report.model_invalidation = invalidation;
  report.checks.changed_model_mapping_refused = !invalidation.binding_valid && !invalidation.pick && invalidation.selection_status === 422;
  report.checks.no_external_scientific_requests = report.external_requests.length === 0;
  if(host==='tauri') {
    const observed=await page.evaluate(()=>window.__sabuesoObservedFrame);
    report.errors.push(...(observed?.errors??[]));
    report.external_requests.push(...(observed?.external_requests??[]));
    report.checks.no_external_scientific_requests = report.external_requests.length===0;
    report.automation='Embedded WebDriver observation + native XTest input on an owned Xvfb display; diagnostic script only';
  }
  if (!Object.values(report.checks).every(Boolean)) throw new Error('A selected journey check failed');
  report.state = 'passed_selected_journey';
  report.product_qualification = false;
  report.qualification_limit = 'Development-only selected checks; browser errors and native GPU/platform acceptance remain separate';
} catch (error) {
  report.state = 'failed';
  report.errors.push(clean(error.stack));
  if (page) {
    try {await page.screenshot({path: path.join(output, 'failure.png'), timeout: 5000});} catch {}
  }
} finally {
  if (page) {
    try {report.final_integration_state = await state();} catch {}
  }
  if (browser) {try {await browser.close();} catch {}}
  for (const child of [...children].reverse()) {
    if (child.exitCode === null && child.signalCode === null) {
      child.kill('SIGTERM');
      const done = await Promise.race([new Promise(resolve => child.once('exit', () => resolve(true))), delay(5000).then(() => false)]);
      if (!done) {child.kill('SIGKILL'); await new Promise(resolve => child.once('exit', resolve));}
    }
  }
  fs.rmSync(privateBootstrap, {force: true});
  report.checks.probe_files_unchanged=JSON.stringify(sourceDigests(here))===JSON.stringify(report.probe_source_digests);
  report.checks.protected_inputs_unchanged=protectedInputsMatch();
  if(!report.checks.probe_files_unchanged || !report.checks.protected_inputs_unchanged)report.state='failed';
  report.timings.total_experiment_ms = performance.now() - started;
  report.child_exit_states = children.map(c => ({exit_code: c.exitCode, signal: c.signalCode}));
  fs.writeFileSync(path.join(output, 'observation.json'), clean(JSON.stringify(report, null, 2)) + '\n');
  console.log(JSON.stringify({host, state: report.state, checks: report.checks, timings: report.timings, graphics: report.graphics}));
  if (report.state !== 'passed_selected_journey') process.exitCode = 1;
}
