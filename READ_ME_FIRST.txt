HEATBANK UPDATE (profile picker + "Why this level?")

Unzip this, then upload the contents into the ROOT of your GitHub repo.
The folders inside match your repo, so files land in the right place:

  index.html                    (repo root: landing page, links go to dashboard/)
  .gitignore                    (adds .venv/ and *.egg-info/)
  dashboard/  core.js worker.js supervisor.js worker.html style.css data.js
  heatbank/i18n/strings.py
  tests/      dom_smoke.js test_part6.py

HOW TO UPLOAD (GitHub website)
1. Open your repo > Add file > Upload files.
2. Drag the files and the dashboard, heatbank and tests folders from the
   unzipped folder into the page (folders keep their paths).
3. Commit changes. GitHub Pages rebuilds in about a minute.

If .gitignore will not upload (hidden file): open .gitignore in the repo,
click the pencil, add two lines:  .venv/  and  *.egg-info/  then commit.

AFTER UPLOADING
- Settings > Pages: Deploy from a branch, main, / (root).
- Hard-refresh the live site (Ctrl+Shift+R) to clear the old cached files.
- The .venv folder already on GitHub: delete it there (open .venv, "..." menu,
  Delete directory). .gitignore only stops NEW uploads.

Do NOT upload the old dashboard/index.html (it was deleted on purpose).
