import assert from 'node:assert/strict';
import {once} from 'node:events';
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import {launchOwned} from './owned_process.mjs';

function fixture(t){const directory=fs.mkdtempSync(path.join(os.tmpdir(),'sabueso-owned-child-'));t.after(()=>fs.rmSync(directory,{recursive:true}));return path.join(directory,'child.log');}

test('an exited child is diagnosed before a startup timeout',async t=>{
  const logPath=fixture(t),owned=launchOwned(process.execPath,['-e','process.exit(7)'],{name:'synthetic',logPath});
  await once(owned.child,'close');
  assert.throws(()=>owned.assertRunning('display readiness'),/Owned synthetic exited before display readiness: 7/);
  assert.equal(owned.closeLog().startup_error,null);
});

test('stdout and stderr are drained within one finite log budget',async t=>{
  const logPath=fixture(t),owned=launchOwned(process.execPath,['-e',"process.stdout.write('x'.repeat(100000));process.stderr.write('y'.repeat(100000));"],{name:'synthetic',logPath,logLimitBytes:1024});
  await once(owned.child,'close');
  assert.equal(owned.child.exitCode,0);const report=owned.closeLog();assert.equal(report.retained_bytes,1024);assert.equal(report.suppressed_bytes,198976);
  assert.ok(fs.statSync(logPath).size<1152);assert.match(fs.readFileSync(logPath,'utf8'),/Receiving log truncated/);
  assert.deepEqual(owned.closeLog(),report);
});

test('spawn failure remains a structured receiving error',async t=>{
  const logPath=fixture(t),owned=launchOwned(path.join(path.dirname(logPath),'missing-executable'),[],{name:'synthetic',logPath});
  await new Promise(resolve=>owned.child.once('close',resolve));
  assert.throws(()=>owned.assertRunning('readiness'),/Owned synthetic could not start before readiness/);
  assert.match(owned.closeLog().startup_error,/ENOENT/);
});

test('the molecular receiver fails promptly and bounds an owned display failure',t=>{
  const logPath=fixture(t),directory=path.dirname(logPath),bin=path.join(directory,'bin');fs.mkdirSync(bin);
  fs.writeFileSync(path.join(bin,'Xvfb'),'#!/usr/bin/env python\nimport sys\nsys.stderr.write("synthetic display failure\\n"*100000)\nsys.exit(7)\n',{mode:0o700});
  const card=path.join(directory,'card.json'),model=path.join(directory,'model.pdb'),output=path.join(directory,'receiving');
  fs.writeFileSync(card,'{}');fs.writeFileSync(model,'HEADER synthetic startup control\nEND\n');
  const started=Date.now(),run=spawnSync(process.execPath,[new URL('../molecular_explorer_journey.mjs',import.meta.url).pathname,'--output',output,'--card',card,'--model',model],{env:{...process.env,PATH:bin+path.delimiter+process.env.PATH},timeout:20000,encoding:'utf8'});
  assert.equal(run.status,1,run.stderr);assert.ok(Date.now()-started<15000);
  const receipt=JSON.parse(fs.readFileSync(path.join(output,'receipt.json'),'utf8'));
  assert.equal(receipt.state,'failed');assert.match(receipt.errors[0],/Owned xvfb exited before Xvfb: 7/);
  assert.ok(receipt.owned_logs[0].suppressed_bytes>0);assert.ok(fs.statSync(path.join(output,'xvfb.log')).size<262272);
});
