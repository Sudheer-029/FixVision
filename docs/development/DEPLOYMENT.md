# Deployment

FixVision runs locally for the hackathon (see the README quickstart). There is no public deployment: the API has no login, so it must not be put on a public URL. The browser reaches the API through a Next.js rewrite, and `API_ORIGIN` sets where the API is.

Before any hosted version: add login with a separate manager role, then move SQLite and media to managed storage.
