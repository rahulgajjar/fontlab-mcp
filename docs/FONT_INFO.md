# Font Info reference

Read `get_font_info` for the selected font/master before editing. Patch with `set_font_info`; omitted fields are preserved. The native interface exposes the field names below. Readability does not establish that every setter, nested record, null value or localization combination has a verified roundtrip.

```json
{"name":"set_font_info","arguments":{"font_id":123,"font_info":{"openTypeNameDesigner":"Your Name","openTypeNameManufacturer":"Your Foundry","openTypeOS2VendorID":"TEST","versionMajor":1,"versionMinor":25,"ascender":850,"descender":-250}}}
```

Replace 123 with an ID from `list_fonts`. Representative naming/legal/version/metrics fields and per-master edits were qualified. Read back and save/reopen to verify a bulk edit. Family-name changes do not rebuild preferred/style-group/full/PostScript names automatically. Axes/instances use the separate structure tools; this is not the complete Font Info dialog.

## Native property names

- `ascender`
- `capHeight`
- `copyright`
- `descender`
- `familyName`
- `italicAngle`
- `macintoshFONDFamilyID`
- `macintoshFONDName`
- `note`
- `openTypeGaspRangeRecords`
- `openTypeHeadCreated`
- `openTypeHeadFlags`
- `openTypeHeadLowestRecPPEM`
- `openTypeHheaAscender`
- `openTypeHheaCaretOffset`
- `openTypeHheaCaretSlopeRise`
- `openTypeHheaCaretSlopeRun`
- `openTypeHheaDescender`
- `openTypeHheaLineGap`
- `openTypeNameCompatibleFullName`
- `openTypeNameDescription`
- `openTypeNameDesigner`
- `openTypeNameDesignerURL`
- `openTypeNameLicense`
- `openTypeNameLicenseURL`
- `openTypeNameManufacturer`
- `openTypeNameManufacturerURL`
- `openTypeNamePreferredFamilyName`
- `openTypeNamePreferredSubfamilyName`
- `openTypeNameRecords`
- `openTypeNameSampleText`
- `openTypeNameUniqueID`
- `openTypeNameVersion`
- `openTypeNameWWSFamilyName`
- `openTypeNameWWSSubfamilyName`
- `openTypeOS2CodePageRanges`
- `openTypeOS2FamilyClass`
- `openTypeOS2Panose`
- `openTypeOS2Selection`
- `openTypeOS2StrikeoutPosition`
- `openTypeOS2StrikeoutSize`
- `openTypeOS2SubscriptXOffset`
- `openTypeOS2SubscriptXSize`
- `openTypeOS2SubscriptYOffset`
- `openTypeOS2SubscriptYSize`
- `openTypeOS2SuperscriptXOffset`
- `openTypeOS2SuperscriptXSize`
- `openTypeOS2SuperscriptYOffset`
- `openTypeOS2SuperscriptYSize`
- `openTypeOS2Type`
- `openTypeOS2TypoAscender`
- `openTypeOS2TypoDescender`
- `openTypeOS2TypoLineGap`
- `openTypeOS2UnicodeRanges`
- `openTypeOS2VendorID`
- `openTypeOS2WeightClass`
- `openTypeOS2WidthClass`
- `openTypeOS2WinAscent`
- `openTypeOS2WinDescent`
- `openTypeVheaCaretOffset`
- `openTypeVheaCaretSlopeRise`
- `openTypeVheaCaretSlopeRun`
- `openTypeVheaVertTypoAscender`
- `openTypeVheaVertTypoDescender`
- `openTypeVheaVertTypoLineGap`
- `panose`
- `postscriptBlueFuzz`
- `postscriptBlueScale`
- `postscriptBlueShift`
- `postscriptBlueValues`
- `postscriptDefaultCharacter`
- `postscriptDefaultWidthX`
- `postscriptFamilyBlues`
- `postscriptFamilyOtherBlues`
- `postscriptFontName`
- `postscriptForceBold`
- `postscriptFullName`
- `postscriptIsFixedPitch`
- `postscriptNominalWidthX`
- `postscriptOtherBlues`
- `postscriptStemSnapH`
- `postscriptStemSnapV`
- `postscriptUnderlinePosition`
- `postscriptUnderlineThickness`
- `postscriptUniqueID`
- `postscriptWeightName`
- `postscriptWindowsCharacterSet`
- `styleMapFamilyName`
- `styleMapStyleName`
- `styleName`
- `trademark`
- `unitsPerEm`
- `versionMajor`
- `versionMinor`
- `xHeight`
- `year`
