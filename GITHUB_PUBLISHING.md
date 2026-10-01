# GitHub publication

This project contains a prepared GitHub Pages workflow that publishes the finished static `dist/` folder after an authorized push to `main`. It does not research, generate lessons, or run on a timer. All narrated audio and PDFs are committed with their exact scripts and citation metadata.

Before the first push, verify the connected GitHub identity, the precise owner/repository, the user's authorization for public source and publication, and whether the repository already contains work. Do not infer a repository from an account-profile URL. Never overwrite another project or use a different connected identity as a fallback.

Enable GitHub Pages with GitHub Actions as its publishing source, then monitor the Pages deployment to terminal success. Return only the verified published URL. Default GitHub Pages URLs include the account/organization name; a fully neutral address requires a neutral namespace or an authorized custom domain.

The Site's existing source and identity are preserved separately in `.openai/hosting.json`. Until an authorized migration finishes, do not call a local prepared workflow a live GitHub publication, and do not claim a new hostname is in use.

Official reference checked 1 October 2026: https://docs.github.com/en/get-started/start-your-journey/deploying-your-website-automatically
