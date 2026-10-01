# Maintaining Listening Library

## User workflow

The user asks Max in their existing chat. Examples:

- `/listening, make a 10-minute lesson about soil microbes.`
- `/listening, turn this paper into a lesson: [link]`
- `/listening, add more vocabulary explanations to the newest lesson.`

Treat `/listening` as a name for this existing project. Do not promise a chat command handler or embedded chatbot: neither exists. Make changes only on request, then publish and return the same Site URL. No automatic schedule is authorized.

## Open and preserve the existing Site

Read `.openai/hosting.json`, get the exact Site ID and current access through Sites, and restore its saved source before editing. It restores this same source even if the current cloud workspace has gone away. Preserve the existing audience unless the user asks to change it. The user made this Site public on 2026-10-01. Use the hosting workflow to push the exact source, package `dist/`, save and deploy. Confirm terminal deployment success before reporting readiness.

Do not operate on the old GitHub repository. This project must remain independent of it. Do not use its audio, transcripts, PDFs or catalog in future lessons.

## New lessons

1. Follow the user's supplied paper/topic, length, level and batch size. Do not treat ordinary project discussion as a lesson-production request. Research original, reputable sources and record their exact URLs, publication date and date checked. Prefer peer-reviewed papers, universities and official institutions. Distinguish original findings from summaries and preserve limits, uncertainty and study design.
2. Write original English narration for a former CET-4 / B1–B2 learner. Explain technical vocabulary frequently in fluent English. Use a coherent story, examples and recap. Default to passive listening: no quizzes, exercises, reflection questions or required responses unless the user asks for them. Do not read or closely paraphrase a copyrighted paper. For research: question, method, result, limits and implications.
3. For a 10-minute lesson, aim initially for at least 1,700–1,900 words, then measure the actual audio. For 30 minutes, plan at least 5,100 words. Word counts are planning guards, not duration guarantees. Use natural neural speech. Never substitute a robotic system voice, stretch audio or add silence/filler merely to reach length.
4. Create a self-contained `content/lessons/YYYY-MM-DD-short-topic/` package:
   - `lesson.json`: schema below
   - `transcript.txt`: exact narrated English text
   - `audio.mp3`: finished verified neural speech
   - `recap.pdf`: complete matching script with vocabulary highlighting, glossary and clickable original citation
   - `source-brief.json`: facts, source evidence/sections and limitations for production verification
5. For completed external production folders, `tools/import_finished_lesson.py <folder> --date YYYY-MM-DD` imports only packages whose script/audio hashes and audio/PDF QA records pass. It preserves exact scripts and full paper metadata.

6. Generate the matching PDF with `tools/build_recap.py <absolute-lesson-directory>` (read its header for dependencies/fonts), inspect rendered pages, then use `tools/build_catalog.py` to validate complete packages and rebuild `dist/catalog.json` and `dist/lessons/`. Keep incomplete work outside this content folder or set `published: false`. Never publish a mock player, a placeholder audio file, or an incomplete package.
7. Inspect audio beginning/middle/end, transcript fidelity, numerical/technical pronunciation, unnatural pauses, joins, clipping and actual duration. Render and inspect PDF pages. Test playback, pause, seeking, speed, lesson selection, transcript, vocabulary, PDF and original source links at desktop/mobile sizes. Source bot-blocking is not a broken link; do not silently replace a correct citation.
8. Publish through the currently authorized host. While this project remains on Sites, publish through Sites. Deployment contains only the built `dist/` assets and the required manifest, while production source is saved separately in the Site's source repository.

## Metadata schema

Every published paper lesson must visibly include the journal, complete author list, publication date, exact matching narration script, and original paper link. Prefer the user’s requested journals (Nature, Science and leading soil–plant–root domain journals), with verified source metadata.

Required lesson.json keys: `id`, `title`, `summary`, `category` (Research, Technology, Nature, Life, Culture), `difficulty` (1, 2, 3), `target_minutes` (10 or 30), `main_idea`, `source_name`, `source_url` (HTTPS), `source_checked`, `words` (array of `term: plain-English explanation`). Include `source_published`, `source_type`, `question`, `answer`, voice/model provenance, and additional citation data when known. Omit unknown dates rather than invent them. `published: false` hides a package without deleting it.

The builder measures audio and supplies local `audio`, `recap` and full `transcript` fields. No separate transcript download is exposed; the user can read it on the Site or in the PDF.

## Hosting migration

The user requested GitHub publication in the VinsonQi account on 2026-10-01. Do not use vinsonqi1998 or that account’s old project. Confirm the connected account and exact destination before any push, creation or settings change. A prepared Pages workflow is in `.github/workflows/pages.yml`; this file alone does not mean GitHub hosting is active. Read `GITHUB_PUBLISHING.md`. Preserve the current Site until the requested replacement URL is verified.

## Storage and dependencies

All runtime media uses relative same-Site paths. No external script, font, CDN, original-library feed or service is required. Original paper links are intentionally external citations. The cloud workspace is disposable, so persist source through the standard Sites workflow. Preserve `.openai/hosting.json` and this maintenance guide.

Keep each static asset under 25 MiB. If a future 30-minute audio file exceeds this, choose an appropriate high-quality speech bitrate or add supported storage with authorization; never silently truncate the lesson. Do not commit model caches, a Python virtual environment, credentials, token files, or transient QA artifacts.

The initial neural voice implementation and its reproducible setup are recorded in `tools/audio/README.md`. Run its setup in a scratch directory, then render an approved new script with `tools/audio/render.py`. Future generation must recheck model/tool availability and permissions; do not claim an API or unattended generator is running.
