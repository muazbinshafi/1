from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
from collector import LeadCollector
import os

app = FastAPI()

class Lead(BaseModel):
    id: int
    name: str
    type: str
    city: str
    phone: str
    website: Optional[str] = None
    contacted: bool = False

# In-memory storage
leads_db: List[Lead] = []
analytics_data = {"total_leads": 0, "contacted_leads": 0}

@app.on_event("startup")
async def startup_event():
    # Initialize mock data only if empty (to avoid duplicates on reload if applicable, though uvicorn reloads module)
    if not leads_db:
        collector = LeadCollector()
        raw_leads = collector.collect_leads()
        for raw in raw_leads:
            # Create Lead object, contacted defaults to False
            lead = Lead(**raw)
            leads_db.append(lead)
        analytics_data["total_leads"] = len(leads_db)

@app.get("/api/leads", response_model=List[Lead])
async def get_leads():
    # Return only uncontacted leads
    return [lead for lead in leads_db if not lead.contacted]

@app.post("/api/leads/{lead_id}/contact")
async def contact_lead(lead_id: int):
    for lead in leads_db:
        if lead.id == lead_id:
            if not lead.contacted:
                lead.contacted = True
                analytics_data["contacted_leads"] += 1
                return {"message": "Lead marked as contacted"}
            else:
                return {"message": "Lead already contacted"}
    raise HTTPException(status_code=404, detail="Lead not found")

@app.get("/api/analytics")
async def get_analytics():
    return analytics_data

# Ensure static directory exists
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return RedirectResponse(url="/static/dashboard.html")
