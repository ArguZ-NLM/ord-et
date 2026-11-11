# Reports to a Google Sheet

Students press **Forkert deling?** on a word; the word goes into "Mine rapporterede ord" on the start page.
**Send** posts the list (word, the app's split, the student's own split, an optional comment, app version) to a
Google Apps Script web app that writes one row per word in a Google Sheet. No login for the student.

## Setup (once, in your Google account)
1. Make a new sheet: https://sheets.new — call it e.g. *ord-et rapporter*.
2. **Udvidelser → Apps Script**. Delete what is there, paste all of `Code.gs`, press 💾 (Gem).
3. Choose the function **setup** in the bar at the top and press **▶ Kør**. Google asks for permission:
   *Gennemgå tilladelser* → your account → *Avanceret* → *Gå til … (usikker)* → *Tillad*.
   (It is "unverified" only because you wrote it yourself.) The sheet now has the tabs *Rapporter* and *Antal*.
4. **Implementer → Ny implementering** → ⚙ → **Webapp**.
   *Udfør som:* **Mig** · *Hvem har adgang:* **Alle** → **Implementer**.
5. Copy the **Webapp-URL** (`https://script.google.com/macros/s/…/exec`) and put it in `REPORT_URL` in `index.html`.

Opening the URL in a browser shows "ord-et rapporter: virker ✓".
If you change `Code.gs` later: **Implementer → Administrer implementeringer → ✏ → Version: Ny version** (the URL stays the same).
