# Project-Scoped Rules

## Default Web Version Focus
- The user **ONLY** uses the Web version of the application located in the `web/` directory.
- The user **NO LONGER** uses the Python Desktop App. Do NOT modify the Python files outside of the `web/` directory unless explicitly requested.
- Whenever the user asks to write code, modify UI, add features, or "deploy", default to modifying the files in the `web/` directory (e.g., `web/app.js`, `web/index.html`, `web/styles.css`).
- For "deploy" requests, simply commit the changes in the `web/` folder and push to GitHub, as GitHub Actions handles the deployment.
