# Vaniards

**Vaniards** is a 2D action-platformer made with GDevelop. The current game is based on the free GDevelop **Not a vania** example and has been renamed and adapted for its own Android release identity.

## Current release target

- **App name:** Vaniards
- **Android package:** `com.baltas80.vaniards`
- **Version:** 1.0.1
- **Orientation:** landscape
- **Languages:** English (default), Spanish
- **Controls:** keyboard, gamepad and mobile touch controls
- **Target API for Google Play:** Android 16 / API 36 or higher

## Mobile work prepared in the editable project

The updated project adds:

- Touch left/right movement buttons.
- Touch jump, attack and dash buttons.
- Mobile menu touch input.
- English/Spanish language selector.
- Spanish translations for menu, HUD, credits and victory screens.
- GDevelop anonymous metrics event removed.
- Mobile resolution adaptation enabled.
- Android package ID changed from the template ID to `com.baltas80.vaniards`.

The complete editable GDevelop project and its asset tree must be kept together when opened in GDevelop.

## Android / Google Play workflow

1. Open the updated `Vaniards.json` in GDevelop together with its existing `assets/` folder.
2. Run a desktop preview and verify the complete game.
3. Export an Android test build and verify touch controls on a physical device.
4. Generate a signed Android App Bundle (`.aab`) targeting API 36 or higher.
5. Test the release build.
6. Upload the AAB to a Google Play testing track.
7. Complete the store listing and required declarations.
8. Promote the tested release to production.

Google Play requires new apps and app updates submitted from 31 August 2026 to target Android 16 / API 36 or higher. citeturn992316search0turn992316search2

## License and third-party assets

Project code is distributed under the MIT license in `LICENSE`. Third-party art, music, fonts and sounds retain their own licenses and attribution requirements; they are **not automatically relicensed as MIT** by this repository.

Known credits and asset licensing notes are documented in `docs/ASSET_LICENSES.md`.

## APK

Current test artifact:

[`Vaniards - Copy-1_0_1.apk`](https://github.com/Baltas80/Vaniards/blob/master/Vaniards%20-%20Copy-1_0_1.apk)

This APK remains a test/reference build. It is not the final Play Store artifact until the updated Android build has been generated and tested.
