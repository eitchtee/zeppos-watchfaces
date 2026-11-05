"""Turn a Zeus build into a flat single-zip watchface (dist/<appName>.zip),
the layout used on amazfitwatchfaces.com. It opens in ZeppOS Player 2 and the
AmazFaces app:

    app.json            (flat v2 config, from the Zeus device build)
    app.js              (runtime wrapper)
    watchface/index.js  (the face source, wrapped for DeviceRuntimeCore)
    assets/...          (images already converted by Zeus for the device)
"""
import glob
import io
import json
import os
import zipfile

APP_JS = """try {
    (() => {
        const __$$app$$__ = __$$hmAppManager$$__.currentApp;
        __$$app$$__.__globals__ = {
            lang: new DeviceRuntimeCore.HmUtils.Lang(DeviceRuntimeCore.HmUtils.getLanguage()),
            px: DeviceRuntimeCore.HmUtils.getPx(390)
        };
        __$$app$$__.app = DeviceRuntimeCore.App({
            globalData: {},
            onCreate() {},
            onDestroy() {}
        });
    })();
} catch (e) {
    console.log('Mini Program Error', e);
    e && e.stack && e.stack.split(/\\n/).forEach(i => console.log('error stack', i));
}
"""

INDEX_HEAD = """try {
    (() => {
        const __$$app$$__ = __$$hmAppManager$$__.currentApp;
        const __$$module$$__ = __$$app$$__.current;
        const h = new DeviceRuntimeCore.WidgetFactory(new DeviceRuntimeCore.HmDomApi(__$$app$$__, __$$module$$__));
        const {px} = __$$app$$__.__globals__;
"""
INDEX_TAIL = """
    })();
} catch (e) {
    console.log('Mini Program Error', e);
    e && e.stack && e.stack.split(/\\n/).forEach(i => console.log('error stack', i));
}
"""


def latest_zab(dist):
    zabs = sorted(glob.glob(os.path.join(dist, "*.zab")), key=os.path.getmtime)
    if not zabs:
        raise SystemExit(f"no .zab in {dist} - run `zeus build` first")
    return zabs[-1]


def device_zip(zab_path):
    with zipfile.ZipFile(zab_path) as zab:
        zpk = next(n for n in zab.namelist() if n.endswith(".zpk"))
        with zipfile.ZipFile(io.BytesIO(zab.read(zpk))) as z:
            return zipfile.ZipFile(io.BytesIO(z.read("device.zip")))


def package(face_dir):
    dist = os.path.join(face_dir, "dist")
    with open(os.path.join(face_dir, "watchface", "index.js"), encoding="utf-8") as f:
        src = f.read()
    if "WatchFace({" not in src:
        raise SystemExit("watchface/index.js: WatchFace({ not found")
    src = src.replace("WatchFace({",
                      "__$$module$$__.module = DeviceRuntimeCore.WatchFace({", 1)
    index_js = INDEX_HEAD + src + INDEX_TAIL

    dev = device_zip(latest_zab(dist))
    name = json.loads(dev.read("app.json"))["app"]["appName"]
    out = os.path.join(dist, f"{name}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("app.json", dev.read("app.json"))
        z.writestr("app.js", APP_JS)
        z.writestr("watchface/index.js", index_js)
        for n in dev.namelist():
            if n.startswith("assets/") and not n.endswith("/"):
                z.writestr(n, dev.read(n))
    return out
