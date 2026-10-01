# Listening Library

An independently hosted English listening library. Open the Site to play finished neural-narrated lessons, read their full scripts and plain-English vocabulary, and visit their original sources.

The user calls this project **Listening Library**, or **/listening** in conversation with Max. This is conversational shorthand, not an app slash-command integration. Maintain it **only when the user asks**. No recurring job, auto-import, external runtime feed, or automatic lesson production exists.

## Independent ownership

All content, audio and PDFs served by this Site live in this project's own `dist/` directory. Original production packages are kept in `content/lessons/`. The Site's registered identity is in `.openai/hosting.json`. Its source is persisted to its Sites source repository as part of each publication. Do not replace the Site or edit any other repository during routine maintenance.

The older GitHub listening-library project was a reference for requirements only. No old lessons were retained. This project does not depend on that repository or its GitHub Pages deployment. Do not delete or modify the older project without the user's explicit request.

## Maintenance

Read `MAINTENANCE.md` before adding lessons or changing the platform. The user does not run commands, make audio, copy scripts, or attend calls; Max completes research, narration, PDF creation, checks and publishing, then returns this same Site URL.

The static player is in `dist/index.html`, `dist/styles.css` and `dist/app.js`. The content builder is `tools/build_catalog.py`. There are no application credentials or paid API dependencies.
