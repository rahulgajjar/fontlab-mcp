import copy
from types import SimpleNamespace
import pytest
from fontlab8_mcp import layout_buffer
from fontlab8_mcp.compiler import compile_snapshot


def package():
    return SimpleNamespace(
        packageLib={"user.keep": {"note": "untouched"}},
        fgPackage=SimpleNamespace(
            tables={"GSUB": bytearray(b"layout"), "maxp": bytearray(b"metrics")},
            glyphs=[SimpleNamespace(name=n) for n in [".notdef", "A", "V"]],
        ),
    )


def test_archive_tuple_roundtrip_restores_all_bytes_and_preserves_other_library():
    p = package()
    layout_buffer.persist(p, compiled_revision="r1", create=True)
    archive = p.packageLib[layout_buffer.ARCHIVE]
    archive["glyph_order"] = tuple(archive["glyph_order"])
    saved = copy.deepcopy(p.packageLib)
    p.fgPackage.tables.clear()
    assert layout_buffer.hydrate(p) == "rehydrated-from-native-package-library"
    assert (
        bytes(p.fgPackage.tables["GSUB"]) == b"layout"
        and bytes(p.fgPackage.tables["maxp"]) == b"metrics"
    )
    assert p.packageLib == saved and p.packageLib["user.keep"] == {"note": "untouched"}
    assert layout_buffer.hydrate(p) == "native-runtime-with-project-archive"


def test_archive_corruption_or_glyph_order_error_has_no_partial_hydration():
    p = package()
    layout_buffer.persist(p, create=True)
    p.fgPackage.tables.clear()
    good = copy.deepcopy(p.packageLib)
    p.packageLib[layout_buffer.ARCHIVE]["sha256"]["maxp"] = "bad"
    with pytest.raises(ValueError, match="Invalid"):
        layout_buffer.hydrate(p)
    assert p.fgPackage.tables == {}
    p.packageLib = good
    p.fgPackage.glyphs.reverse()
    with pytest.raises(ValueError, match="glyph order"):
        layout_buffer.hydrate(p)
    assert p.fgPackage.tables == {}


def test_managed_buffer_restore_leaves_unrelated_tables_and_detects_external_publish():
    p = package()
    layout_buffer.persist(p, compiled_revision="r1", create=True)
    old = layout_buffer.capture(p)
    p.fgPackage.tables["GSUB"][:] = b"changed"
    p.fgPackage.tables["GPOS"] = b"new"
    layout_buffer.restore(p, old)
    assert (
        bytes(p.fgPackage.tables["GSUB"]) == b"layout"
        and "GPOS" not in p.fgPackage.tables
    )
    assert bytes(p.fgPackage.tables["maxp"]) == b"metrics"
    p.fgPackage.tables["GSUB"] = b"external-compile"
    layout_buffer.persist(p)
    assert p.packageLib[layout_buffer.ARCHIVE]["compiled_revision"] is None


def snapshot(text):
    return dict(
        data={"text": text},
        glyph_order=[".notdef", "A", "V"],
        shared_classes={"Native": {"mode": "FeaClassGroupMode", "members": ["A"]}},
    )


def test_detached_compiler_supports_shared_class_and_three_managed_tables():
    text = "table GDEF {GlyphClassDef [A V], [], [], [];} GDEF; feature liga {sub @Native V by V;} liga; feature kern {pos A V -80;} kern;"
    data, warnings = compile_snapshot(snapshot(text))
    assert set(data) == {"GDEF", "GPOS", "GSUB"} and all(
        len(v) > 0 for v in data.values()
    )
    assert isinstance(warnings, list)


def test_compiler_refuses_include_missing_glyph_and_unpublished_name_table():
    with pytest.raises(ValueError, match="include"):
        compile_snapshot(snapshot("include(secret.fea);"))
    with pytest.raises(Exception):
        compile_snapshot(snapshot("feature liga {sub Missing by A;} liga;"))
    with pytest.raises(ValueError, match="additional tables"):
        compile_snapshot(
            snapshot(
                'feature ss01 {featureNames {name "Alternate";}; sub A by V;} ss01;'
            )
        )


def test_persist_refuses_to_relabel_old_compiled_glyph_order_without_new_compile():
    p = package()
    layout_buffer.persist(p, compiled_revision="r1", create=True)
    prior = copy.deepcopy(p.packageLib)
    p.fgPackage.glyphs.reverse()
    with pytest.raises(ValueError, match="glyph order"):
        layout_buffer.persist(p)
    assert p.packageLib == prior
    layout_buffer.persist(p, compiled_revision="explicit-new", create=True)
    assert p.packageLib[layout_buffer.ARCHIVE]["glyph_order"] == ["V", "A", ".notdef"]
