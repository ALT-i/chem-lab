# Release bundle for NOUN (internal, ALT-I only)

NOUN receives ready-to-run packages, not the repositories. This folder builds them.

| File | Goes to NOUN? | Purpose |
| --- | --- | --- |
| `build-release.sh` | No | Builds the bundle from clean `git archive` copies of the release branches |
| `backend.Dockerfile` | No | Backend image, shipped as compiled bytecode only (no `.py`, no `.env`) |
| `admin.Dockerfile` | No | Admin dashboard image; reads its settings from `.env` at start-up |
| `docker-compose.yml` | Yes | Runs db, redis, web, worker and admin on NOUN's server |
| `env.template` | Yes | NOUN copies it to `/opt/chemlab/.env` and fills it in |
| `backup.sh` | Yes | Nightly backup of database, media and settings |

## Build a release

Needs Docker and Git Bash (or Linux). Run from the backend repo root:

```bash
git fetch && git -C ../chem_lab_admin_fe fetch
MEDIA_DIR=/path/to/media DATA_SQL=/path/to/chemlab-data.sql release/build-release.sh 1.0.0
```

- `MEDIA_DIR`: the media files the apps load from `/media/` (apparatus and bottle SVGs, demo videos, `intro/Introduction.mp4`). Copy them from the current Render server first.
- `DATA_SQL`: the first release only. Export the current content as plain SQL so it loads into Postgres 14:
  `pg_dump --no-owner --no-privileges "<render database url>" > chemlab-data.sql`
- Output: `release-dist/chemlab-release-<version>/` with `chemlab-images-<version>.tar.gz` (about 600 MB), the files above, optional `media.tar.gz` / `chemlab-data.sql`, and `SHA256SUMS`.
- The script stops if the backend image contains any `.py` file (other than `manage.py`) or a non-empty `.env`.

Hand the folder over by a private link or USB drive, and send `SHA256SUMS` separately (e.g. by email) so NOUN can check the download.

## Desktop installer

NOUN does not build the desktop app; ALT-I builds one per backend address. In the electron-app repo, on a Windows PC with Node 20 and Yarn:

| File | Change |
| --- | --- |
| `package.json` line 19 | `"build": "electron-builder"` (the current value points at one developer's laptop) |
| `package.json` line 5 | Raise `version` for every release |
| `src/renderer/utils/index.js` line 5 and `src/renderer/utils.js` line 4 | `absolute_url: 'https://<NOUN backend address>'`, no trailing slash, both files |
| `src/renderer/components/IndexPage.tsx` line 71 | `course_id:` NOUN's CHM 191 course ID |
| `src/renderer/utils/intro-video-config.ts` line 26 | `https://<NOUN backend address>/media/intro/Introduction.mp4` |

Then `yarn` and `yarn build --win`. Deliver `dist/v<version>/NOUNACETEL CHM vLab Setup <version>.exe`, renamed without spaces (e.g. `CHM-vLab-Setup-1.2.0.exe`). Making the backend address a runtime setting would let one installer serve every deployment; until then, each address change needs a new build.

## Fix before the first release ships

NOUN cannot patch the code, so these must be fixed in the release itself. Issues 1 to 3 were reproduced on a test install on 1 October 2026.

| # | Issue | Fix |
| --- | --- | --- |
| 1 | `POST /api/v1/register/` and `POST /api/v1/users/official/` need no login and accept `role: ADMIN`, which creates a Django superuser | Public sign-up always creates `STUDENT`; only a logged-in `ADMIN`/`SUPER` may create staff |
| 2 | `/api/v1/users/` lists and edits user records without login | Require login; users edit only themselves; staff see lists |
| 3 | Lessons, substances and apparatus can be created, changed or deleted without login | Reads stay open (the desktop app reads anonymously); writes need `INSTRUCTOR` or above |
| 4 | `POST /api/v1/moodle/grades/assignment/` lets any logged-in user post any grade, for any email, to any assignment | Only the caller's own email, only the lesson's assignment |
| 5 | Code falls back to a public `SECRET_KEY` when `DJANGO_SECRET_KEY` is unset | Refuse to start without it |
| 6 | Cloudinary key and signing secret in comments in `chem_lab_admin_fe/src/data/cloudinary-creds.js` | Delete the comments and rotate the keys |
| 7 | CORS and `ALLOWED_HOSTS` are open to everything | Limit to NOUN's two addresses |
| 8 | Email is sent without SMTP login (only host and port are read) | Add `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` |
| 9 | The backend ignores `MOODLE_COURSE_ID` / `MOODLE_DEFAULT_ASSIGNMENT_ID`; the desktop app hardcodes course 9 and falls back to assignment 1 | Use the settings server-side |
| 10 | Desktop installer is unsigned | Windows code-signing certificate |

## What "no source code" does and does not protect

The images keep the code out of plain sight, but they are not a lock. Python bytecode can be decompiled, the dashboard ships as minified JavaScript, and the Electron installer contains the app's bundled JavaScript. Anyone with the bundle and some effort can recover most of the logic. Real protection comes from the contract or licence with NOUN; the packaging just avoids handing over a working repository.
