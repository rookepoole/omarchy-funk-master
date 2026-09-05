// Execute the actual adapter's QML JavaScript methods with timer/process doubles.
// No real idle deadline, lock, or display state is changed by these tests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const repo = path.resolve(__dirname, '..');
const source = fs.readFileSync(0, 'utf8');
assert(source.includes('FUNK MASTER ASCII ADAPTER'), 'Pipe adapted Idle QML source into this test.');

function method(source, name) {
  const start = source.indexOf('function ' + name + '(');
  assert(start >= 0, name);
  let brace = source.indexOf('{', start), depth = 1, i = brace + 1;
  for (; i < source.length && depth; i++) {
    if (source[i] === '{') depth++;
    if (source[i] === '}') depth--;
  }
  return source.slice(start, i);
}
const calls = [];
function timer(name) { return {running:false, restart(){this.running=true; calls.push(name+':start');}, stop(){this.running=false;}}; }
const saver = {active:false, start(){this.active=true;calls.push('saver:start');},dismiss(reason){this.active=false;calls.push('saver:dismiss:'+reason);}};
const root = {idledThisCycle:false, screensaverStartedThisCycle:false, screensaverWindowCount:0,
  screensaverDelaySeconds:0, lockDelaySeconds:150, idleEnabled:true};
const context = {root, shell:{serviceFor:()=>saver}, screensaverTimer:timer('saver-timer'),
  lockTimer:timer('lock-timer'), screensaverLaunchGraceTimer:timer('grace'),
  lockProcess:{},screensaverProcess:{},wakeProcess:{},Date,
  logEvent(){},runProcess(proc,label){calls.push('process:'+label);return true;}};
vm.createContext(context);
for (const name of ['funkSaver','funkSaverActive','launchScreensaver','resetScreensaverWindows',
  'startIdleCycle','handleActiveSignal','cancelIdleCycle','lockSystem']) {
  vm.runInContext(method(source,name),context);
  root[name] = (...args)=>context[name](...args);
}
context.startIdleCycle();
assert(saver.active && root.idledThisCycle && context.lockTimer.running);
context.handleActiveSignal();
assert(context.lockTimer.running && root.idledThisCycle, 'Overlay mapping must not disarm the native lock timer');
context.lockSystem('test');
assert(calls.includes('saver:dismiss:lock'));
assert(calls.includes('process:lock'));
assert(!saver.active && !root.idledThisCycle);
context.startIdleCycle();
context.cancelIdleCycle('user-activity');
assert(!context.lockTimer.running && !root.idledThisCycle);

const service = fs.readFileSync(path.join(repo,'desktop/screensavers/Service.qml'),'utf8');
const r = {lockService:{},sessionLocked:true,screensaverEnabled:true,active:false};
const gate = {root:r,lockService:r.lockService,sessionLocked:true,screensaverEnabled:true,Ascii:{scenes:[0,1,2,3]}};
vm.createContext(gate);
vm.runInContext(method(service,'start'),gate);
assert.equal(gate.start(0,true),'locked-or-not-ready');
gate.sessionLocked=false;gate.screensaverEnabled=false;
assert.equal(gate.start(0,false),'screensaver-disabled');
assert(!r.active);
console.log('Idle flow: launch, lock deadline, overlay activity, dismissal, lock gating and disabled saver checks passed.');
