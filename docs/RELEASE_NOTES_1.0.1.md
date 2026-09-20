# Vaniards 1.0.1

## Existing APK

`Vaniards - Copy-1_0_1.apk`

The APK currently stored in this repository is the existing test/reference build.

## Updated source preparation

The editable GDevelop project has been prepared for the Android release with:
- Mobile touch controls for movement, jump, attack and dash.
- Touch navigation on the title menu.
- English as the default language.
- Spanish translation and language selector.
- Mobile runtime resolution adaptation.
- Android application ID set to `com.baltas80.vaniards`.
- Version set to `1.0.1`.
- The GDevelop anonymous metrics event removed.

## Final release gate

The final Google Play artifact must be generated from the updated GDevelop project as a **signed Android App Bundle (`.aab`)**, targeting Android 16 / API 36 or higher, then tested on real Android hardware.

The existing APK remains available as a reference and should not be treated as the final Play Store upload.
