# Roadmap Scenario Planner
*Interactive Gantt & capacity simulation for PMs and engineering leads.*

Plan and simulate delivery across two cross-functional squads (**Alpha** and **Bravo**) with an interactive Gantt. Rank tasks by priority (drag to reorder), set **Streams** to control parallel work, and tune a **Capacity Factor** (availability + estimation uncertainty) for each discipline. The Gantt updates instantly so you can compare scenarios, surface bottlenecks, and choose the plan that best fits your constraints.

---

## ✨ Features

* **Interactive Gantt** that recalculates timelines as you drag priorities.
* **Two squads (Alpha & Bravo)** with their own resources & backlog.
* **Capacity Factor (%)** per Back-End/Front-End to reflect availability + estimation error.
* **Parallel Streams** (concurrency) to cap how many engineers can progress a task in parallel.
* **Role-based UI**: **admin** can edit & **Save Plan**; **viewer** is read-only.
* **Stateless setup**: single XML file (`resource_config.xml`) persists plans.
* **Batteries-included**: FastAPI, Jinja templates, Dockerfile, Railway-ready.

---

## 🧠 How it works (high level)

* You provide Back-End/Front-End **FTEs** per squad, **Capacity Factor (%)**, and a prioritized **task list**.
* For each task, you set **Effort #Weeks** (end-to-end, including QA & release) and **Parallel Streams** per discipline.
* The planner computes the schedule left-to-right, respecting capacity and max parallelism, then renders a Gantt.

---

## 🚀 Quickstart (local)

```bash
# 1) clone
git clone https://github.com/HamedShams/gantt_resource_planner.git
cd gantt_resource_planner

# 2) env (optional, see variables below)
export DISABLE_AUTH=true           # quick demo, everyone is admin
export CONFIG_PATH=resource_config.xml

# 3) install & run (Python 3.10+)
pip install -r requirements.txt
uvicorn main:app --reload
# -> http://localhost:8000
```

> Tip: For a realistic setup (with login), set admin/viewer credentials and a non-default `SECRET_KEY`.

---

## 🔐 Authentication & Roles

* **viewer**: read-only (can’t see the **Save Plan** button).
* **admin**: can edit and **Save Plan** (persists to XML).
* **DISABLE\_AUTH=true**: auth off; everyone is treated as admin (good for forks and demos).

---

## ⚙️ Environment Variables

These are read at runtime (no secrets in the repo). Defaults are sane for local demos.

| Key            | Default                     | What it does                                                   |
| -------------- | --------------------------- | -------------------------------------------------------------- |
| `ADMIN_USER`   | `admin`                     | Admin username (write access).                                 |
| `ADMIN_PW`     | `admin123`                  | Admin password.                                                |
| `VIEWER_USER`  | `viewer`                    | Read-only username.                                            |
| `VIEWER_PW`    | `viewer123`                 | Read-only password.                                            |
| `SECRET_KEY`   | `CHANGE_ME`                 | Cookie/session signing key (set a long random string in prod). |
| `DISABLE_AUTH` | `false`                     | `true` disables auth; everyone is admin.                       |
| `CONFIG_PATH`  | `/data/resource_config.xml` | XML path; for local you can set `resource_config.xml`.         |

**.env example (local):**

```dotenv
ADMIN_USER=admin
ADMIN_PW=changeMe!
VIEWER_USER=viewer
VIEWER_PW=viewOnly!
SECRET_KEY=this-should-be-very-random-and-long
DISABLE_AUTH=false
CONFIG_PATH=resource_config.xml
```

---

## 🧱 Data & Persistence

* Plans are stored in a single XML file (`resource_config.xml` by default).
* In **production on Railway**, use a **persistent volume** and point `CONFIG_PATH` to the mounted file (see below).

---

## 🐳 Docker (local)

```bash
# build
docker build -t gantt_resource_planner .

# run with a local data file mounted for persistence
mkdir -p ./data
cp resource_config.example.xml ./data/resource_config.xml  # if you keep an example file
docker run --rm -p 8000:8000 \
  -e ADMIN_USER=admin -e ADMIN_PW=changeMe! \
  -e VIEWER_USER=viewer -e VIEWER_PW=viewOnly! \
  -e SECRET_KEY=this-should-be-random \
  -e DISABLE_AUTH=false \
  -e CONFIG_PATH=/data/resource_config.xml \
  -v $(pwd)/data/resource_config.xml:/data/resource_config.xml \
  gantt_resource_planner
# -> http://localhost:8000
```

---

## ☁️ Deploying on Railway

**One-time setup**

1. **Deploy from GitHub** (Railway will build from your Dockerfile).
2. **Add Variables** (Service ▸ Variables): set the envs from the table above.
3. **Add a Volume** (Service ▸ Volumes) and set the **mount path** to:
   `/data/resource_config.xml`
4. Ensure `CONFIG_PATH` is `/data/resource_config.xml`.
5. **Generate a domain** (Service ▸ Networking) and open your app.

**Common gotchas**

* **Changes don’t persist** → Volume not mounted at `/data/resource_config.xml`, or `CONFIG_PATH` mismatch.
* **“Save Plan” not visible** → You’re logged in as `viewer` or auth disabled logic hasn’t been configured; check envs.
* **403 on save** → You’re not `admin` (or `DISABLE_AUTH` is `false` and creds are wrong).

---

## 🧭 Roadmap (ideas)
* Considering other deciplines based on the structure of your cross functional teams (e.g., design, data).
* Multi-squad (N squads) with reusable components.
* CSV import/export for tasks.
* OAuth/SSO option (e.g., JWT via an auth provider) while keeping env-based Basic auth as default.

---

## 📄 License
MIT License — see [LICENSE](LICENSE).

---

## 🤝 Contributing & Credits
PRs and issues are welcome. Please keep changes minimal and fork-friendly—no secrets in code, no vendor lock-ins.

**Credits:** Built by Seyed **Hamed Shams** (Lead PM at SnappDoctor) for internal planning; open-sourced so other teams can fork, deploy, and adapt quickly.  
**Website:** <https://HamedShams.com>
