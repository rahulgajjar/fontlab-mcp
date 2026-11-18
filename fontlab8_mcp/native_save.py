"""Native save handler with explicit paths, retained backups and restored preferences."""

import json
import shutil
import tempfile
from pathlib import Path
import fontlab


def save(p, args, summary):
    from .layout_buffer import persist

    source = Path(p.path).expanduser().resolve()
    path = Path(args.get("path") or source).expanduser().resolve()
    kind = args.get("format", path.suffix.lstrip(".")).lower()
    if kind not in ("vfc", "vfj") or path.suffix.lower() != "." + kind:
        raise ValueError("Native save requires matching .vfc or .vfj path/format")
    existing_native = source.suffix.lower() in (".vfc", ".vfj")
    if existing_native and path != source:
        raise ValueError(
            "Native Save As is not qualified. Save to the current native document path, or open a file copy before editing"
        )
    if not existing_native:
        expected = Path(p.fileName).stem
        if path.stem != expected or kind != "vfc":
            raise ValueError(
                "First native save requires .vfc and the existing document basename: "
                + expected
                + ".vfc; VFJ sidecar is also created"
            )
    targets = [path.with_suffix(".vfc"), path.with_suffix(".vfj")]
    if any(t.exists() for t in targets) and not args.get("overwrite", False):
        raise ValueError("Destination exists; explicitly pass overwrite=true")
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = Path(
        tempfile.mkdtemp(
            prefix="native-save-",
            dir=str(Path.home() / "Library/Application Support/FontLab8MCP/backups"),
        )
    )
    for t in targets:
        if t.exists():
            shutil.copy2(t, backup / t.name)
    before = {
        str(t): (t.stat().st_mtime_ns, t.stat().st_size) if t.exists() else None
        for t in targets
    }
    w = fontlab.flWorkspace.instance()
    active = w.currentPackage
    prefs = fontlab.flPreferences()
    keys = ["fontAskFileName", "exportSaveFolder", "exportSaveVFJ"]
    old = {key: getattr(prefs, key) for key in keys}
    try:
        persist(p)
        prefs.fontAskFileName = 2
        prefs.exportSaveFolder = str(path.parent)
        prefs.exportSaveVFJ = True
        fontlab.SetCurrentFont(p.fgPackage)
        w.mainWindow.on_actionSaveFont_triggered()
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(
                "Native handler did not produce the requested file; inspect document before retrying"
            )
        sidecar = path.with_suffix(".vfj")
        if not sidecar.is_file():
            raise RuntimeError("Native save did not produce validation VFJ sidecar")
        data = json.loads(sidecar.read_text())
        if not isinstance(data.get("font"), dict):
            raise RuntimeError("Native VFJ does not contain a font object")
        if before.get(str(path)) == (path.stat().st_mtime_ns, path.stat().st_size):
            raise RuntimeError(
                "Native save did not update requested file; execution outcome requires inspection"
            )
        return dict(
            status="ok",
            font=summary(p),
            path=str(path),
            save_mode="native",
            sidecar=str(sidecar),
            backup_directory=str(backup),
            note="Native save; backups retained. Document destination follows FontLab native save behavior.",
        )
    finally:
        for key, value in old.items():
            setattr(prefs, key, value)
        if active is not None:
            fontlab.SetCurrentFont(active.fgPackage)
