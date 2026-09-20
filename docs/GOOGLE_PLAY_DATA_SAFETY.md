# Google Play — Data safety preparation

This document is a preparation aid for the Play Console Data safety form. It is based on the current Vaniards GDevelop source and must be rechecked against the final signed AAB before submission.

## Current project configuration

- No user account system.
- No Firebase authentication.
- No advertising SDK configured in the project.
- No in-app purchase system configured in the project.
- No leaderboard or online account feature configured.
- The original GDevelop anonymous metrics event has been removed from the adapted source.
- No intentional collection of name, email, contacts, precise location, camera or microphone data is present in the current source.

## Play Console review

Before submitting the final AAB:
1. Inspect the Play Console generated app bundle details and declared permissions.
2. Review every SDK/library included by the final Android export.
3. Confirm whether any third-party component collects or shares data.
4. Make the Data safety answers match the final binary, not only the GDevelop source.
5. Keep this document synchronized with future changes.

Official Google guidance:
https://support.google.com/googleplay/android-developer/answer/10787469
https://support.google.com/googleplay/android-developer/answer/10144311
