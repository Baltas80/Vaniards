# Android / Google Play release checklist

## Project configuration prepared

- [x] App name: Vaniards
- [x] Package ID: `com.baltas80.vaniards`
- [x] Version name: 1.0.1
- [x] Orientation: landscape
- [x] English default
- [x] Spanish translation
- [x] Mobile touch controls added in updated source
- [x] Mobile menu touch input added
- [x] Anonymous GDevelop metrics event removed from updated source
- [x] Runtime resolution adaptation enabled

## Build gate

- [ ] Open updated `Vaniards.json` with the existing `assets/` folder
- [ ] Desktop preview passes
- [ ] Android test build installs
- [ ] Touch movement works
- [ ] Touch jump works
- [ ] Touch attack works
- [ ] Touch dash works
- [ ] Language selector works
- [ ] Spanish UI is readable on Android landscape screens
- [ ] Back/resume lifecycle checked
- [ ] Audio checked
- [ ] No blocking crashes

## Google Play target

As of 31 August 2026, new apps and updates submitted to Google Play must target **Android 16 / API 36 or higher**. citeturn992316search0turn992316search2

The final build therefore needs a GDevelop Android export toolchain that produces an APK/AAB with target API 36+.

## Release artifact

- [ ] Generate a signed `.aab`
- [ ] Keep the upload/signing key backed up securely
- [ ] Increment version code for every Play upload
- [ ] Verify application ID is `com.baltas80.vaniards`

## Store listing

- [ ] App title: Vaniards
- [ ] Short description
- [ ] Full description
- [ ] 512x512 Play Store icon
- [ ] Screenshots taken from the real Android build
- [ ] Content rating
- [ ] Data safety declaration
- [ ] Privacy policy URL where applicable

Google Play's current listing limits are 30 characters for the app title, 80 for the short description and 4,000 for the full description. citeturn207025search1turn207025search4

## Personal developer account testing

For personal developer accounts created after 13 November 2023, Google currently requires a closed test with at least 12 opted-in testers continuously for 14 days before production access can be requested. citeturn352291search3turn352291search6

## Current APK

The repository's existing APK is a reference/test build. It should not be treated as the final Play Store artifact until the updated source has been exported, signed and tested on Android hardware.
