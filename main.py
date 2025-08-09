# SPDX-License-Identifier: MIT

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, Response, PlainTextResponse
from jinja2 import Environment, FileSystemLoader
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
import traceback, os, json
from typing import Callable
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Form, Depends, HTTPException, status
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

BASE = Path(__file__).parent


# ─── ENV config ───────────────────────────────────────────────────────
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PW = os.getenv("ADMIN_PW", "admin123")
VIEWER_USER = os.getenv("VIEWER_USER", "viewer")
VIEWER_PW = os.getenv("VIEWER_PW", "viewer123")
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME")
DISABLE_AUTH = os.getenv("DISABLE_AUTH", "true").lower() == "true"
CONFIG_PATH = Path(os.getenv("CONFIG_PATH", str(BASE / "data" / "resource_config.xml")))
# WEEKEND_DAYS: comma-separated weekday numbers (Python: Monday=0). Defaults to "3,4" → Thu & Fri (Persian Calendar)
WEEKEND_DAYS = {int(x) for x in os.getenv("WEEKEND_DAYS", "3,4").split(",") if x.strip().isdigit()}


# ─── constants ───────────────────────────────────────────────────────
DAY_PX = 32
WEEKEND = WEEKEND_DAYS
# JavaScript Date.getDay(): Sunday=0. Convert Python weekday numbers to JS numbers.
WEEKEND_JS = [(d + 1) % 7 for d in sorted(WEEKEND)]
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKEND_LABEL = " & ".join(WEEKDAY_NAMES[d] for d in sorted(WEEKEND))


env = Environment(loader=FileSystemLoader(BASE / "templates"))
templates = Jinja2Templates(directory=str(BASE / "templates"))
app  = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)  # cookie-based sessions

# ─── helpers ────────────────────────────────────────────────────────
def is_work(d): return d.weekday() not in WEEKEND
def add_wd(s,n):
    d,a=s,0
    while a<n:
        d+=timedelta(days=1)
        if is_work(d): a+=1
    return d

# ─── XML I/O ────────────────────────────────────────────────────────
def load_cfg():
    """
    Reads CONFIG_PATH XML and returns the same dict structure as before.
    On failure, logs a traceback to stdout (shows in Railway logs) and raises 500.
    """
    try:
        cfg_path = Path(CONFIG_PATH)  # CONFIG_PATH is already a Path-like
        if not cfg_path.exists():
            raise FileNotFoundError(f"{cfg_path} not found")
        if cfg_path.is_dir():
            raise IsADirectoryError(f"{cfg_path} is a directory; expected a file")
    
        root = ET.parse(cfg_path).getroot(); out={}
        for s in root.iter("squad"):
            n=s.attrib["name"]
            out[n]=dict(
                engineers  ={ k: float(v) for k,v in s.find("engineers").attrib.items() },  # ← float
                efficiency ={ k: float(v) for k,v in s.find("efficiency").attrib.items() }, # ← float
                startDate  = s.findtext("startDate"),
                projects   = []
            )
            for p in s.find("projects").iter("project"):
                out[n]["projects"].append(dict(
                id=p.attrib["id"], name=p.attrib["name"], priority=int(p.attrib["priority"]),
                effort      ={k: float(v) for k,v in p.find("effort").attrib.items()},
                concurrency ={k: int(v)   for k,v in p.find("concurrency").attrib.items()}
                ))
        # lightweight debug line to confirm load in logs
        try:
            total = sum(len(s["projects"]) for s in out.values())
            print(f"[load_cfg] OK - path={cfg_path} squads={list(out.keys())} total_projects={total}")
        except Exception:
            pass
                
        return out

    except Exception as e:
        traceback.print_exc()  # full stack in Deploy/HTTP logs
        raise HTTPException(status_code=500, detail=f"load_cfg failed for {CONFIG_PATH}: {e}")


def save_cfg(data):
    root=ET.Element("resourceConfig")
    for sq,cfg in data.items():
        s=ET.SubElement(root,"squad",name=sq)
        ET.SubElement(s,"engineers",  **{k:str(v) for k,v in cfg["engineers"].items()})
        ET.SubElement(s,"efficiency", **{k:str(v) for k,v in cfg["efficiency"].items()})
        ET.SubElement(s,"startDate").text = cfg["startDate"]
        ps=ET.SubElement(s,"projects")
        for p in cfg["projects"]:
            pr=ET.SubElement(ps,"project",id=p["id"],name=p["name"],priority=str(p["priority"]))
            ET.SubElement(pr,"effort",      **{k:str(v) for k,v in p["effort"].items()})
            ET.SubElement(pr,"concurrency", **{k:str(v) for k,v in p["concurrency"].items()})
    ET.indent(root); ET.ElementTree(root).write(CONFIG_PATH,encoding="utf-8",xml_declaration=True)

# -- Session / role helpers ---------------------------------------------------

def current_user(request: Request) -> str:
    if DISABLE_AUTH:
        return "admin"
    user = request.session.get("user")
    if user:
        return user
    # not logged in – redirect to login page
    raise HTTPException(status_code=status.HTTP_303_SEE_OTHER,
                        headers={"Location": "/login"})

def login_required(user: str = Depends(current_user)):
    return user

def admin_required(user: str = Depends(current_user)):
    if user != ADMIN_USER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user

# ─── /login routes ───────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    valid = ((username == ADMIN_USER and password == ADMIN_PW) or
             (username == VIEWER_USER and password == VIEWER_PW))
    if valid or DISABLE_AUTH:
        request.session["user"] = username or ADMIN_USER
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

# ─── routes ─────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index(request: Request, user: str = Depends(login_required)):
    html = env.get_template("index.html").render(
        day_px=DAY_PX,
        is_admin=(user == ADMIN_USER),
        weekend_js=json.dumps(WEEKEND_JS),
        weekend_label=WEEKEND_LABEL
    )
    return HTMLResponse(content=html)

@app.get("/data")
def data(user: str = Depends(login_required)):
    return load_cfg()

@app.post("/save")
async def save(req: Request, user: str = Depends(admin_required)):
    save_cfg(await req.json())
    return {"status": "ok"}

# ─── Export XML ──────────────────────────────────────────────────────
@app.get("/export")
def export_xml(user: str = Depends(login_required)):
    """Return the current XML config for download/viewing."""
    return FileResponse(CONFIG_PATH, media_type="application/xml", filename=CONFIG_PATH.name)

@app.get("/healthz")
def healthz():
    p = Path(CONFIG_PATH)
    exists = p.exists()
    is_dir = p.is_dir()
    size = (p.stat().st_size if exists and not is_dir else None)
    print(f"[healthz] path={p} exists={exists} is_dir={is_dir} size={size}")
    return JSONResponse({
        "ok": True,
        "port": os.getenv("PORT"),
        "config_path": str(p),
        "exists": exists,
        "is_dir": is_dir,
        "size": size,
    })

@app.get("/data_raw")
def data_raw():
    # no auth, just serve the exact XML file for isolation
    p = Path(CONFIG_PATH)
    xml = p.read_text(encoding="utf-8")
    print(f"[data_raw] served {p} ({len(xml)} bytes)")
    return Response(xml, media_type="application/xml")