# SPDX-License-Identifier: MIT

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
import os
from typing import Callable
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Form, Depends, HTTPException, status
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

BASE   = Path(__file__).parent

# ─── ENV config ───────────────────────────────────────────────────────
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PW = os.getenv("ADMIN_PW", "admin123")
VIEWER_USER = os.getenv("VIEWER_USER", "viewer")
VIEWER_PW = os.getenv("VIEWER_PW", "viewer123")
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME")
DISABLE_AUTH = os.getenv("DISABLE_AUTH", "true").lower() == "true"
CONFIG_PATH = Path(os.getenv("CONFIG_PATH", str(BASE / "data" / "resource_config.xml")))

DAY_PX = 32
WEEKEND = {3, 4}                      # Thu, Fri

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
    root = ET.parse(CONFIG_PATH).getroot(); out={}
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
    return out

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
    html = env.get_template("index.html").render(day_px=DAY_PX, is_admin=(user == ADMIN_USER))
    return HTMLResponse(content=html)

@app.get("/data")
def data(user: str = Depends(login_required)):
    return load_cfg()

@app.post("/save")
async def save(req: Request, user: str = Depends(admin_required)):
    save_cfg(await req.json())
    return {"status": "ok"}
