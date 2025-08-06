from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

BASE   = Path(__file__).parent
DB     = BASE / "resource_config.xml"
DAY_PX = 32
WEEKEND = {3, 4}                      # Thu, Fri

env = Environment(loader=FileSystemLoader(BASE / "templates"))
app  = FastAPI()

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
    root = ET.parse(DB).getroot(); out={}
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
    ET.indent(root); ET.ElementTree(root).write(DB,encoding="utf-8",xml_declaration=True)

# ─── routes ─────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index(): return env.get_template("index.html").render(day_px=DAY_PX)

@app.get("/data")
def data(): return load_cfg()

@app.post("/save")
async def save(req:Request):
    save_cfg(await req.json()); return {"status":"ok"}
