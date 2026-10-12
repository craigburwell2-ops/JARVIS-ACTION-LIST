# JARVIS Action List

A minimal checkable action list that your bots can update via API.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

## Bot integration

POST new tasks:

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Call the three warm leads from this morning", "category": "Insurance", "notes": "Priority"}'
```

Mark complete:

```bash
curl -X PATCH http://localhost:8000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

Categories in use: Insurance, Fibre, Pool Care, Admin, General.

The interface is dark, mobile-friendly, and filters by category. Tasks persist in `action_list.db`.
