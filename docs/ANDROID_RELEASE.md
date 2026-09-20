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

From 31 August 2026, new apps and updates submitted to Google Play must target **Android 16 / API 36 or higher**.

Official requirement: https://developer.android.com/google/play/requirements/target-sdk

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
- [ ] Privacy policy URL

Google Play's current listing limits are 30 characters for the app title, 80 characters for the short description and 4,000 characters for the full description.

Official metadata guidance: https://support.google.com/googleplay/android-developer/

## Personal developer account testing

For personal developer accounts created after 13 November 2023, Google currently requires a closed test with at least 12 opted-in testers continuously for 14 days before production access can be requested.

Official guidance: https://support.google.com/googleplay/android-developer/answer/14151465?hl=es

## Privacy policy

Google Play requires a privacy policy for apps, including apps that do not access personal or sensitive user data. The policy must be available at an active public URL and must also be accessible from the app where applicable.

Official guidance: https://support.google.com/googleplay/android-developer/answer/10144311?hl=es

A web copy is stored at `docs/privacy-policy.html`. It can be served from a public web host for the Play Console URL.
