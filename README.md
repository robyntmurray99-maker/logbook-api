# Logbook PDF API

Flask API that generates styled PDF reports for the Surveyor's Logbook app.

## Deploy to Railway

1. Push this folder to a GitHub repository
2. Go to railway.app and click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose this repository
5. Railway will auto-detect Python and deploy
6. Copy the generated URL (e.g. https://logbook-api-production.up.railway.app)
7. Paste that URL into the logbook app's API_URL setting

## Endpoints

- GET  /health         → Check server is running
- POST /generate-pdf   → Generate PDF, returns binary PDF file

## POST /generate-pdf body
```json
{
  "student_name": "Your Name",
  "principal_name": "Timothy A. Thwaites, BA(Hons) MSc., CLS",
  "office": "Thwaites Surveying Ltd.",
  "period": "January 2025 – January 2026",
  "entries": [ ...array of entry objects from Supabase... ]
}
```
