import os
import json
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin"],
)

class QueryRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

base_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(base_dir, "..", "q-vercel-latency.json")
if not os.path.exists(path):
    path = os.path.join(base_dir, "q-vercel-latency.json")

with open(path, "r", encoding="utf-8") as f:
    DATA = json.load(f)

def calc_p95(vals):
    s = sorted(vals)
    r = 0.95 * (len(s) - 1)
    n = int(r)
    l = r - n
    return s[n] + l * (s[n + 1] - s[n]) if n + 1 < len(s) else s[n]

@app.post("/")
def get_analytics(payload: QueryRequest):
    res = {}
    for region in payload.regions:
        records = [x for x in DATA if x.get("region") == region]
        if not records:
            continue
        lat = [x["latency_ms"] for x in records]
        upt = [x["uptime_pct"] for x in records]
        res[region] = {
            "avg_latency": round(sum(lat) / len(lat), 2),
            "p95_latency": round(calc_p95(lat), 2),
            "avg_uptime": round(sum(upt) / len(upt), 3),
            "breaches": sum(1 for l in lat if l > payload.threshold_ms)
        }
    return {"regions": res}
