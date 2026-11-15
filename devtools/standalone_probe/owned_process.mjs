// Task-owned receiving children. This is not an application process manager.
import fs from 'node:fs';
import {spawn} from 'node:child_process';

export function launchOwned(command, args, {name, logPath, env, cwd, logLimitBytes=262144}) {
  if(!Number.isInteger(logLimitBytes)||logLimitBytes<0)throw new Error('Use a finite nonnegative log byte limit');
  const fd=fs.openSync(logPath,'wx',0o600);
  let written=0,suppressed=0,closed=false,startupError=null;
  const child=spawn(command,args,{env,cwd,stdio:['ignore','pipe','pipe','pipe']});
  function record(chunk){
    if(closed)return;
    const available=Math.max(0,logLimitBytes-written),retained=chunk.subarray(0,available);
    const count=retained.length?fs.writeSync(fd,retained):0;
    written+=count;suppressed+=chunk.length-count;
  }
  child.stdout.on('data',record);child.stderr.on('data',record);
  child.on('error',error=>{startupError=String(error);});
  function assertRunning(label){
    if(startupError)throw new Error(`Owned ${name} could not start before ${label}: ${startupError}`);
    if(child.exitCode!==null||child.signalCode!==null)throw new Error(`Owned ${name} exited before ${label}: ${child.signalCode??child.exitCode}`);
  }
  function closeLog(){
    if(!closed){
      closed=true;
      try{if(suppressed)fs.writeSync(fd,`\n[Receiving log truncated; ${suppressed} bytes suppressed]\n`);}
      finally{fs.closeSync(fd);}
    }
    return {name,byte_limit:logLimitBytes,retained_bytes:written,suppressed_bytes:suppressed,startup_error:startupError};
  }
  return {child,assertRunning,closeLog};
}
