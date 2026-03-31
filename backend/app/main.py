"""
Industrial Digital Twin API Server
FastAPI backend with WebSocket telemetry, REST endpoints, JWT auth,
OPC-UA integration, ISA-88 Batch Records, and soft sensor analytics.
"""

import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import init_db
from .simulator import GodModeReactor
from .data_logger import data_logger
from .auth import (
    authenticate_user, create_access_token, get_current_user, require_role,
    get_ws_user, Role, Token, UserInfo, TokenData, AUTH_ENABLED,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from .opcua_server import DCPTwinOPCUAServer

logger = logging.getLogger("dcp-twin")

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="2026 Industrial Digital Twin",
    description="2,6-Dichlorophenol Batch Reactor Digital Twin API — Industrial Grade",
    version="3.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize reactor simulator
reactor = GodModeReactor()

# OPC-UA server instance
opcua_server = DCPTwinOPCUAServer()
OPCUA_ENABLED = os.environ.get("OPCUA_ENABLED", "true").lower() == "true"


class ConnectionManager:
    """WebSocket connection manager for broadcasting telemetry"""
    
    def __init__(self):
        self.connections: list[WebSocket] = []
    
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
    
    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)
    
    async def broadcast(self, msg: str):
        disconnected = []
        for ws in self.connections:
            try:
                await ws.send_text(msg)
            except Exception:
                disconnected.append(ws)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)


manager = ConnectionManager()


async def run_simulation_loop():
    """Main simulation loop - updates reactor and broadcasts telemetry"""
    while True:
        reactor.update(dt=0.1)
        data = reactor.get_telemetry()
        payload = {
            "telemetry": data,
            "audit": reactor.get_audit_log()
        }
        await manager.broadcast(json.dumps(payload))
        await asyncio.sleep(0.1)


@app.on_event("startup")
async def startup_event():
    """Start simulation loop and OPC-UA server on app startup"""
    asyncio.create_task(run_simulation_loop())

    # Start OPC-UA server if enabled
    if OPCUA_ENABLED:
        try:
            def get_twin_state():
                return reactor.get_telemetry()

            def on_setpoint(sp: dict):
                reactor.set_command(sp)

            success = await opcua_server.setup(get_twin_state, on_setpoint)
            if success:
                asyncio.create_task(opcua_server.update_loop())
                logger.info("OPC-UA server started as background task")
        except Exception as e:
            logger.warning(f"OPC-UA server failed to start: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown"""
    await opcua_server.stop()


# =====================
# WebSocket Endpoint
# =====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    WebSocket endpoint for real-time telemetry streaming
    Optionally authenticated via ?token=<jwt> query param.
    """
    # Auth check (if enabled)
    if AUTH_ENABLED:
        user = await get_ws_user(token)
        if not user:
            # Accept then immediately close with auth error code
            # so the browser receives the proper close code (4001)
            await websocket.accept()
            await websocket.close(code=4001, reason="Authentication failed")
            return

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                cmd = json.loads(data)
                reactor.set_command(cmd)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON command received: {data[:100]}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# =====================
# Authentication Endpoints
# =====================

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login", response_model=Token)
async def login(form: LoginRequest):
    """Authenticate and receive JWT access token."""
    user = authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )
    token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(
        access_token=token,
        role=user.role.value,
        username=user.username,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.post("/api/auth/logout")
async def logout():
    """Logout (client should discard token)."""
    return {"status": "ok", "message": "Token discarded client-side"}


@app.get("/api/auth/me")
async def get_me(user: TokenData = Depends(get_current_user)):
    """Get current authenticated user info."""
    return UserInfo(username=user.username, role=user.role.value, full_name="")


# =====================
# REST API Endpoints
# =====================

@app.get("/")
async def root():
    """API root - health check"""
    return {
        "status": "online",
        "name": "2,6-Dichlorophenol Digital Twin",
        "version": "3.0.0",
        "auth_enabled": AUTH_ENABLED,
        "opcua_enabled": OPCUA_ENABLED,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/status")
async def get_status(user: TokenData = Depends(require_role(Role.VIEWER))):
    """Get current reactor status (VIEWER+)"""
    return reactor.get_telemetry()


@app.get("/api/recipe/status")
async def get_recipe_status(user: TokenData = Depends(require_role(Role.VIEWER))):
    """Get detailed recipe/batch status"""
    return reactor.recipe.get_detailed_status()


@app.get("/api/recipe/steps")
async def get_recipe_steps(user: TokenData = Depends(require_role(Role.VIEWER))):
    """Get all recipe steps with their status"""
    detail = reactor.recipe.get_detailed_status()
    return {
        "total_steps": detail["total_steps"],
        "current_step": detail["current_step_index"],
        "steps": detail["all_steps"]
    }


@app.post("/api/recipe/start")
async def start_recipe(user: TokenData = Depends(require_role(Role.WORKER))):
    """Start the batch recipe (WORKER+)"""
    success = reactor.recipe.start()
    if success:
        reactor.log_event("INFO", f"Recipe started via REST API by {user.username}")
        return {"status": "started", "message": "Batch recipe started"}
    return {"status": "error", "message": "Recipe could not be started (not in IDLE state)"}


@app.post("/api/recipe/stop")
async def stop_recipe(user: TokenData = Depends(require_role(Role.WORKER))):
    """Stop/abort the current batch (WORKER+)"""
    reactor.recipe.abort()
    reactor.log_event("WARNING", f"Recipe aborted via REST API by {user.username}")
    return {"status": "aborted", "message": "Batch recipe aborted"}


@app.post("/api/recipe/reset")
async def reset_recipe(user: TokenData = Depends(require_role(Role.WORKER))):
    """Reset recipe to IDLE state (WORKER+)"""
    reactor.set_command({"RECIPE_CMD": "RESET"})
    return {"status": "reset", "message": "Recipe reset to IDLE"}


@app.get("/api/batch/summary")
async def get_batch_summary(user: TokenData = Depends(require_role(Role.VIEWER))):
    """Get current/last batch summary statistics"""
    return data_logger.generate_batch_summary()


@app.get("/api/batch/report")
async def generate_batch_report(user: TokenData = Depends(require_role(Role.WORKER))):
    """Generate and return batch report CSV"""
    report_path = data_logger.generate_csv_report()
    
    if report_path and Path(report_path).exists():
        return FileResponse(
            path=report_path,
            filename=Path(report_path).name,
            media_type="text/csv"
        )
    
    raise HTTPException(status_code=404, detail="No batch data available for report")


@app.get("/api/batch/report/pdf")
async def generate_batch_report_pdf(user: TokenData = Depends(require_role(Role.WORKER))):
    """Generate and return batch report as PDF"""
    from datetime import datetime as dt
    report_path = data_logger.generate_pdf_report()

    if report_path and Path(report_path).exists():
        friendly_name = f"batch_report_{dt.now().strftime('%Y-%m-%d')}.pdf"
        return FileResponse(
            path=report_path,
            filename=friendly_name,
            media_type="application/pdf"
        )

    raise HTTPException(status_code=404, detail="No batch data available for PDF report")


@app.get("/api/batch/report/docx")
async def generate_batch_report_docx(user: TokenData = Depends(require_role(Role.WORKER))):
    """Generate and return batch report as Word document"""
    from datetime import datetime as dt
    report_path = data_logger.generate_docx_report()

    if report_path and Path(report_path).exists():
        friendly_name = f"batch_report_{dt.now().strftime('%Y-%m-%d')}.docx"
        return FileResponse(
            path=report_path,
            filename=friendly_name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    raise HTTPException(status_code=404, detail="No batch data available for Word report")


@app.get("/api/batch/reports")
async def list_batch_reports(user: TokenData = Depends(require_role(Role.VIEWER))):
    """List all available batch reports"""
    log_dir = Path(data_logger.log_dir)
    
    if not log_dir.exists():
        return {"reports": []}
    
    reports = []
    for f in log_dir.glob("*.csv"):
        reports.append({
            "filename": f.name,
            "size_bytes": f.stat().st_size,
            "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat()
        })
    
    return {"reports": sorted(reports, key=lambda x: x["created"], reverse=True)}


@app.get("/api/batch/report/{filename}")
async def download_batch_report(filename: str, user: TokenData = Depends(require_role(Role.WORKER))):
    """Download a specific batch report"""
    report_path = Path(data_logger.log_dir) / filename
    
    if report_path.exists() and report_path.suffix == ".csv":
        return FileResponse(
            path=str(report_path),
            filename=filename,
            media_type="text/csv"
        )
    
    raise HTTPException(status_code=404, detail="Report not found")


@app.get("/api/telemetry/history")
async def get_telemetry_history(user: TokenData = Depends(require_role(Role.VIEWER))):
    """Get recent telemetry history"""
    return {
        "count": len(data_logger.telemetry_buffer),
        "data": data_logger.get_recent_telemetry(100)
    }


@app.get("/api/events")
async def get_events(user: TokenData = Depends(require_role(Role.VIEWER))):
    """Get recent events/audit log"""
    return {
        "events": data_logger.get_recent_events(50)
    }


@app.get("/api/control-actions")
async def get_control_actions(user: TokenData = Depends(require_role(Role.VIEWER))):
    """Get recent control actions log"""
    return {
        "actions": data_logger.get_control_actions(50)
    }


@app.post("/api/control")
async def send_control(command: dict, user: TokenData = Depends(require_role(Role.WORKER))):
    """Send a control command to the reactor (WORKER+)"""
    try:
        reactor.set_command(command)
        return {"status": "ok", "command": command}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/faults")
async def get_faults(user: TokenData = Depends(require_role(Role.VIEWER))):
    """Get current fault injection status"""
    return reactor.faults


@app.post("/api/fault/{fault_name}/toggle")
async def toggle_fault(fault_name: str, user: TokenData = Depends(require_role(Role.OWNER))):
    """Toggle a fault injection (OWNER only)"""
    if fault_name in reactor.faults:
        reactor.set_command({"toggle_fault": fault_name})
        return {
            "fault": fault_name,
            "active": reactor.faults[fault_name]
        }
    
    raise HTTPException(
        status_code=404,
        detail=f"Unknown fault: {fault_name}. Available: {list(reactor.faults.keys())}"
    )


@app.get("/api/interlocks")
async def get_interlocks(user: TokenData = Depends(require_role(Role.VIEWER))):
    """Get current interlock status"""
    return {
        "active": reactor.recipe.interlock.active,
        "reason": reactor.recipe.interlock.reason,
        "conditions": reactor.recipe.interlock.failed_conditions
    }


# =====================
# Soft Sensor Endpoint
# =====================

@app.get("/api/soft-sensor")
async def get_soft_sensor(user: TokenData = Depends(require_role(Role.VIEWER))):
    """Get current soft sensor readings (purity, selectivity, TCP impurity, conversion)."""
    return reactor._soft_sensor_data or reactor.soft_sensor.get_purity_estimate()


# =====================
# OPC-UA Status Endpoint
# =====================

@app.get("/api/opcua/status")
async def get_opcua_status(user: TokenData = Depends(require_role(Role.VIEWER))):
    """Get OPC-UA server connection info and node list."""
    return opcua_server.get_status()


# =====================
# Electronic Batch Record (ISA-88) Endpoints
# =====================

@app.get("/api/v1/batch-records")
async def list_ebr(user: TokenData = Depends(require_role(Role.OWNER))):
    """List all Electronic Batch Records (OWNER+)."""
    return {"records": reactor.batch_record_mgr.list_records()}


@app.get("/api/v1/batch-records/{batch_id}")
async def get_ebr(batch_id: str, user: TokenData = Depends(require_role(Role.OWNER))):
    """Get a specific Electronic Batch Record as JSON (OWNER+)."""
    raw = reactor.batch_record_mgr.get_record_json(batch_id)
    if not raw:
        raise HTTPException(status_code=404, detail=f"Batch record '{batch_id}' not found")
    return JSONResponse(content=json.loads(raw))


@app.get("/api/v1/batch-records/{batch_id}/report")
async def get_ebr_report(batch_id: str, user: TokenData = Depends(require_role(Role.OWNER))):
    """Get markdown report of a batch record (OWNER+)."""
    record = reactor.batch_record_mgr.get_record(batch_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Batch record '{batch_id}' not found")
    return PlainTextResponse(content=record.to_markdown_report(), media_type="text/markdown")


@app.post("/api/v1/batch-records/{batch_id}/verify")
async def verify_ebr(batch_id: str, user: TokenData = Depends(require_role(Role.OWNER))):
    """Verify hash integrity of a batch record (OWNER+)."""
    result = reactor.batch_record_mgr.verify_record(batch_id)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail=f"Batch record '{batch_id}' not found")
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
