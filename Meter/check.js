// Self-check for the drum logic: runs watchface/index.js against a stub of the
// watch runtime and drives its timer. `node Meter/check.js` after a build.
const assert = require('assert')
const fs = require('fs')
const path = require('path')
const vm = require('vm')

const src = fs.readFileSync(path.join(__dirname, 'watchface', 'index.js'), 'utf8')
const usedSrcs = new Set()

function run(screenType = 1) {
  const clock = { format_hour: 23, minute: 59, second: 58 }
  const widgets = []
  const timers = {}
  let nextId = 1
  const delegates = []
  const hmUI = {
    show_level: { ONLY_NORMAL: 1, ONLY_AOD: 2 },
    widget: new Proxy({}, { get: (_, k) => k }),
    data_type: new Proxy({}, { get: (_, k) => k }),
    system_status: new Proxy({}, { get: (_, k) => k }),
    align: { LEFT: 0, CENTER_H: 1 },
    prop: { VISIBLE: 'visible', MORE: 'more', TEXT: 'text' },
    createWidget(type, opts) {
      const w = { type, ...opts, visible: true,
        setProperty(p, v) {
          if (p === 'more') { Object.assign(w, v); usedSrcs.add(v.src) } else w[p] = v
        } }
      if (opts.src) usedSrcs.add(opts.src)
      for (const v of Object.values(opts)) if (Array.isArray(v)) v.forEach(s => typeof s === 'string' && usedSrcs.add(s))
      if (type === 'WIDGET_DELEGATE') delegates.push(opts)
      widgets.push(w)
      return w
    }
  }
  const hmSensor = {
    id: { TIME: 't', SLEEP: 's' },
    createSensor: id => (id === 't' ? clock : { getTotalTime: () => 435 })
  }
  const ctx = {
    hmUI, hmSensor,
    hmSetting: { getLanguage: () => 20, getScreenType: () => screenType, screen_type: { WATCHFACE: 1, AOD: 2 } },
    timer: {
      createTimer(delay, period, cb) { const id = nextId++; timers[id] = cb; return id },
      stopTimer(id) { delete timers[id] }
    },
    WatchFace: def => def.build()
  }
  vm.runInNewContext(src, ctx)
  const wheels = widgets.filter(w => w.type === 'IMG').slice(2, 8)
  const tick = () => Object.values(timers).forEach(cb => cb())
  return { clock, wheels, tick, timers, delegates }
}

const shown = f => f.wheels.map(w => w.src)
const settled = f => { for (let i = 0; i < 5; i++) f.tick(); return shown(f).map(s => path.basename(s, '.png')).join('') }

// wheels stay hidden until the timer runs, so IMG_TIME shows through
let f = run()
assert(f.wheels.every(w => w.visible === false))
f.tick()
assert(f.wheels.every(w => w.visible === true))
assert.strictEqual(settled(f), '235958')

// a one-second step rolls only the last wheel
f.clock.second = 59
f.tick()
assert(/\/89_0\.png$/.test(f.wheels[5].src), f.wheels[5].src)
assert(/\/5\.png$/.test(f.wheels[4].src))
assert.strictEqual(settled(f), '235959')

// midnight carries through every wheel, each on its own roll strip
Object.assign(f.clock, { format_hour: 0, minute: 0, second: 0 })
f.tick()
assert.deepStrictEqual(shown(f).map(s => path.basename(s, '.png')),
  ['20_0', '30_0', '50_0', '90_0', '50_0', '90_0'])
assert.strictEqual(settled(f), '000000')

// a jump with no roll strip snaps
f.clock.second = 42
f.tick()
assert.strictEqual(path.basename(f.wheels[4].src, '.png'), '4')

// pause stops the timer; resume after a long gap snaps instead of replaying
f.delegates.find(d => d.pause_call).pause_call()
assert.strictEqual(Object.keys(f.timers).length, 0)
Object.assign(f.clock, { format_hour: 7, minute: 30, second: 15 })
f.delegates.find(d => d.pause_call).resume_call()
assert.strictEqual(Object.keys(f.timers).length, 1)
f.tick()
assert.strictEqual(shown(f).map(s => path.basename(s, '.png')).join(''), '073015')

// no timer in always-on
f = run(2)
assert.strictEqual(Object.keys(f.timers).length, 0)

for (const s of usedSrcs) {
  assert(fs.existsSync(path.join(__dirname, 'assets', 'bip6', s)), `missing asset ${s}`)
}
console.log(`ok, ${usedSrcs.size} assets referenced`)
