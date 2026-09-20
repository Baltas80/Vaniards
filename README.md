# Vaniards

Mobile action-platformer project built with GDevelop.

## Current status

- Project name: **Vaniards**
- Target platform: **Android / Google Play**
- Current test build: `Vaniards - Copy-1_0_1.apk`
- Default branch: `master`
- Current release status: pre-publication

## Repository contents

The repository currently contains the Android test APK and project documentation. The APK is a test artifact, not the final Google Play release package.

## Android release target

New Google Play submissions from 31 August 2026 must target Android 16 / API 36 or higher. The final Android build must therefore be generated against a toolchain compatible with API 36 before submission.

## Release workflow

1. Verify the game on Android hardware.
2. Configure the final application identity and package ID.
3. Verify touch controls, display scaling, audio and lifecycle behavior.
4. Generate a signed Android App Bundle (`.aab`).
5. Test the release build.
6. Upload the AAB to Google Play Console's testing track.
7. Complete the store listing and required declarations.
8. Promote the tested release to production.

## Important

The existing APK is retained as a reference/test build. Do not treat it as the final Play Store artifact until the target API, signing configuration and release checks have been verified.
