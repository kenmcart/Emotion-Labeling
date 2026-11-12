# Deploying this project

## 1) Frontend on GitHub Pages

Push this folder to GitHub and enable GitHub Pages for the repository.

Use the static files:
- `index.html`
- `ai_assisted.html`
- `style.css`
- `app.js`
- `ai_app.js`
- `fallacy_dataset.json`

## 2) AI backend on Render

Create a Render web service from this repo.

Use the following settings:
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn ai_server:app`

Render will run the Flask app and expose a public URL such as:
`https://your-app-name.onrender.com`

## 3) Supabase

Create a table:

```sql
create table public.task_responses (
  id uuid primary key default gen_random_uuid(),
  mode text not null check (mode in ('manual', 'ai_assisted')),
  labeler text not null,
  statement text not null,
  fallacy text not null,
  created_at timestamptz default now()
);

alter table public.task_responses enable row level security;

create policy "Allow public inserts"
on public.task_responses
for insert
with check (true);
```

Then copy:
- project URL
- anon key

into your frontend JavaScript.

## 4) Update the AI frontend

In `ai_app.js`, replace:

```javascript
const API_BASE = "";
```

with:

```javascript
const API_BASE = "https://your-app-name.onrender.com";
```

Then replace the fetch call with:

```javascript
const response = await fetch(`${API_BASE}/api/predict`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text })
});
```

## 5) Supabase in the frontend

In the frontend JavaScript, add:

```javascript
const supabaseUrl = "https://YOUR-PROJECT-REF.supabase.co";
const supabaseAnonKey = "YOUR_ANON_KEY";
const supabase = supabase.createClient(supabaseUrl, supabaseAnonKey);
```

Then insert each response with:

```javascript
await supabase.from("task_responses").insert([
  {
    mode: "manual",
    labeler: labelerId,
    statement: statements[currentNum],
    fallacy: selectedFallacy
  }
]);
```

## 6) Final flow

- Manual page saves to Supabase and localStorage
- AI page calls Render backend and saves to Supabase and localStorage
- Both versions are stored in one shared table
