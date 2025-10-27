# Deploying ChatFiscal to Streamlit Community Cloud

This file documents the exact steps to publish the app to Streamlit Community Cloud (share.streamlit.io). Follow these steps to make the app available for asynchronous academic evaluation.

Prerequisites
- A GitHub account and a GitHub repository containing this project (push your `main` branch).
- A Streamlit account (use your GitHub account to sign in) at https://share.streamlit.io/

1) Push code to GitHub

```powershell
git add .
git commit -m "Prepare repo for Streamlit Cloud deployment"
git push origin main
```

2) Create the app on Streamlit Cloud

- Login to https://share.streamlit.io/ with your GitHub account.
- Click "New app" → select the repository and the `main` branch.
- App directory: leave blank (root) unless your `app.py` is in a subfolder.
- Command: leave default `streamlit run app.py` (this is recommended).

3) Configure Secrets (important)

- On the Streamlit app page go to Settings → Secrets.
- Add any API keys your app needs (example keys listed in `.streamlit/secrets.toml.example`). Do not store secrets in the repo.

4) Build & first run

- After creating the app the Cloud will build using `requirements.txt`. The first build may take several minutes.
- Monitor the build logs in the app's Log tab. If the build fails, copy the error and fix locally (missing dependency or version conflict) and push again.

5) Post-deploy checks for evaluators

- Open the provided URL.
- Upload a CSV/XML file in the "Dados & Perguntas" tab and run a few sample queries.
- Check the Audit and Visualizations tabs.

Troubleshooting & tips

- Long `requirements.txt`: Streamlit Cloud installs every dependency listed. If builds take too long or fail, consider trimming unused packages from `requirements.txt` (we kept the full list by your choice).
- FAISS and heavy natives: `faiss-cpu` sometimes causes build issues on Streamlit Cloud. If you encounter problems, either:
  - Use a fallback (the app can be configured to skip faiss and use a simple in-memory fallback), or
  - Build a Docker-based deploy (Cloud Run / other provider) instead.
- Persistence: the local folder `memoria_chatfiscal/` is not guaranteed to persist robustly across Cloud restarts. For evaluation where persistence is required, configure an external storage (S3, GCS or a small DB) and put keys in Secrets.
- Logs: use the app Logs panel in Streamlit Cloud to see stdout/stderr. For more verbose logging, temporarily increase logging level in `app.py`.

Security notes
- Keep API keys and other secrets in Streamlit Secrets only. Do NOT commit any secret values to the repository.
- If you restrict access to the app, Streamlit Cloud supports password-protecting the app with a custom auth layer inside your app (a simple login form using the secrets as credentials), or you can keep the repo private and grant the evaluator access to the repo and Streamlit app.

Next steps I can help with
- Walk through the Streamlit Cloud "New app" flow after you push.
- If you want, I can add a short run-check endpoint or a health-check button to `app.py` that quickly validates required secrets and model availability at startup (no secrets will be printed to logs).
- Help create a minimal auth wrapper for the evaluator (optional): a small password-protected gate using the secret `EVALUATOR_PASSWORD`.
