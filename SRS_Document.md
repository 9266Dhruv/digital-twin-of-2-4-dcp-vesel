# Software Requirements Specification (SRS)

## Industrial Digital Twin for 2,6-Dichlorophenol (DCP) Batch Reactor

**Version:** 3.0.0  
**Date:** March 5, 2026  
**Prepared by:** Project Team  
**Document Standard:** IEEE 830-1998 (IEEE Recommended Practice for SRS)

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [System Features / Functional Requirements](#3-system-features--functional-requirements)
4. [External Interface Requirements](#4-external-interface-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [System Models / Diagrams](#6-system-models--diagrams)
7. [Data Requirements](#7-data-requirements)
8. [Appendices](#8-appendices)

---

## 1. Introduction

### 1.1 Purpose

The purpose of this document is to provide a comprehensive Software Requirements Specification (SRS) for the **Industrial Digital Twin System** designed for a **2,6-Dichlorophenol (DCP) Batch Reactor**. This document defines the functional and non-functional requirements, system interfaces, constraints, and design considerations for the complete digital twin platform. It serves as a reference for developers, testers, project stakeholders, and evaluators throughout the software development lifecycle.

### 1.2 Scope

The **Industrial Digital Twin System** is a full-stack web application that creates a real-time virtual replica (digital twin) of a chemical batch reactor used for producing 2,6-Dichlorophenol (DCP) via phenol chlorination. The system encompasses:

- **Physics-based reactor simulation** with Arrhenius chemical kinetics, PID control, and thermodynamic modeling.
- **ISA-88 compliant batch recipe management** with a sequential state machine governing production phases.
- **Real-time 3D visualization** of the reactor reflecting physical state (temperature, vibration, rotation).
- **Live telemetry dashboard** with process variable charts and trend analysis.
- **ML-based anomaly detection** for predictive maintenance and fault alerting.
- **OPC-UA industrial protocol server** for integration with Distributed Control Systems (DCS).
- **Electronic Batch Records (EBR)** compliant with ISA-88 and 21 CFR Part 11 (tamper-evident via SHA-256 hash chaining).
- **Role-Based Access Control (RBAC)** with JWT authentication (Viewer, Worker, Owner roles).
- **Soft sensor analytics** for real-time purity estimation without laboratory analysis.
- **Multi-format batch report generation** (CSV, PDF, Word).

**Out of Scope:** Physical hardware interfacing with actual reactor equipment, deployment to cloud infrastructure, mobile native applications.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|-----------|
| **DCP** | 2,6-Dichlorophenol — the target chemical product |
| **TCP** | 2,4,6-Trichlorophenol — undesired over-chlorination byproduct |
| **2-CP** | 2-Chlorophenol — intermediate reaction product |
| **Digital Twin** | A virtual replica of a physical system that mirrors its real-time state |
| **ISA-88** | International standard for batch control (Batch Control Standard) |
| **21 CFR Part 11** | US FDA regulation on electronic records and signatures |
| **OPC-UA** | Open Platform Communications Unified Architecture — industrial communication protocol |
| **DCS** | Distributed Control System — industrial process control system |
| **PID** | Proportional–Integral–Derivative controller |
| **RBAC** | Role-Based Access Control |
| **JWT** | JSON Web Token — used for authentication |
| **EBR** | Electronic Batch Record |
| **CSTR** | Continuously Stirred Tank Reactor |
| **RUL** | Remaining Useful Life — predictive maintenance metric |
| **SCRAM** | Emergency shutdown procedure |
| **PV** | Process Variable (measured value) |
| **SP** | Setpoint (target value) |
| **API** | Application Programming Interface |
| **REST** | Representational State Transfer |
| **WebSocket** | Full-duplex communication protocol over TCP |
| **Arrhenius Equation** | k = A × exp(−Ea / RT) — relates reaction rate to temperature |

### 1.4 References

| # | Reference | Description |
|---|-----------|-------------|
| 1 | IEEE 830-1998 | IEEE Recommended Practice for Software Requirements Specifications |
| 2 | ISA-88.01 | Batch Control – Models and Terminology |
| 3 | 21 CFR Part 11 | FDA Electronic Records and Signatures |
| 4 | OPC-UA Specification | IEC 62541 — Unified Architecture |
| 5 | FastAPI Documentation | https://fastapi.tiangolo.com |
| 6 | React Three Fiber | https://docs.pmnd.rs/react-three-fiber |
| 7 | Recharts Library | https://recharts.org |
| 8 | Scikit-Learn Documentation | https://scikit-learn.org (Isolation Forest) |

---

## 2. Overall Description

### 2.1 Product Perspective

The Industrial Digital Twin System is a **standalone, new web-based application** that simulates an industrial DCP batch reactor digitally. It is **not** part of an existing system, but is designed to integrate with external industrial DCS platforms (Siemens PCS7, Honeywell Experion, ABB 800xA) via the OPC-UA protocol. The system follows a standard **client-server architecture** with a Python backend and a React frontend communicating over REST APIs and WebSockets.

### 2.2 Product Functions

The major functions of the system are:

1. **Reactor Physics Simulation** — Real-time simulation of a DCP batch reactor including temperature, pressure, vibration, flow rate, agitator RPM, and chemical concentrations.
2. **Recipe State Machine** — ISA-88 compliant sequential batch execution through 10 defined phases (IDLE → LOAD_PHENOL → ADD_SOLVENT → HEATING → HOLD_TEMP → ADD_CATALYST → CHLORINATING → COOLING → SEPARATING → COMPLETE).
3. **3D Reactor Visualization** — Interactive 3D model reflecting real-time reactor state (rotation speed, heat color mapping, vibration shake).
4. **Real-Time Dashboard** — Live telemetry charts for temperature, pressure, flow rate, purity, and conversion metrics.
5. **Anomaly Detection AI** — Physics-informed anomaly detection with alerts for flow blockage, contamination risk, and bearing failure prediction.
6. **Soft Sensor Analytics** — Virtual analyzer estimating DCP purity, TCP impurity, phenol conversion, and selectivity in real-time using ODE integration.
7. **Batch Record Management** — ISA-88 / 21 CFR Part 11 compliant electronic batch records with SHA-256 hash chaining for tamper evidence.
8. **Report Generation** — Batch reports exportable in CSV, PDF, and Word (DOCX) formats.
9. **OPC-UA Industrial Integration** — Server exposing reactor process variables as browsable OPC-UA nodes for DCS connectivity.
10. **User Authentication & Authorization** — JWT-based login with hierarchical RBAC (Viewer → Worker → Owner).
11. **Safety Interlocks** — Automated safety checks preventing unsafe operations (e.g., cannot chlorinate if temperature not at setpoint).
12. **Fault Injection** — Simulated equipment failures (heater failure, sensor drift, imbalance, overheat) for testing and training.

### 2.3 User Classes and Characteristics

| User Role | Access Level | Description | Permissions |
|-----------|-------------|-------------|-------------|
| **Viewer** | Level 0 (Lowest) | Remote monitoring personnel, trainees, auditors | View dashboard, telemetry, recipe status, events, interlocks, soft sensor data, OPC-UA status |
| **Worker** | Level 1 (Mid) | Plant operators, process engineers | All Viewer permissions + Start/Stop/Reset recipe, send control commands, generate/download batch reports |
| **Owner** | Level 2 (Highest) | Plant engineers, directors, system administrators | All Worker permissions + Toggle fault injections, manage Electronic Batch Records (list, view, verify integrity) |

### 2.4 Operating Environment

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend Runtime** | Python | 3.10+ |
| **Backend Framework** | FastAPI | Latest |
| **ASGI Server** | Uvicorn | Latest |
| **Frontend Runtime** | Node.js | 18+ |
| **Frontend Framework** | React | 19.x |
| **Build Tool** | Vite | 7.x |
| **3D Engine** | Three.js / React Three Fiber | 0.182 / 9.x |
| **Charting** | Recharts | 3.x |
| **Database** | SQLite (via SQLAlchemy) | 3.x |
| **Supported Browsers** | Chrome, Firefox, Edge | Latest |
| **Supported OS** | Windows 10/11, Linux, macOS | Any |

### 2.5 Design and Implementation Constraints

1. **Single-Process Backend**: The simulation and API run in a single Python asyncio event loop; no distributed worker architecture.
2. **SQLite Database**: Limited to single-writer concurrency; not suitable for multi-instance deployment.
3. **Hardcoded User Database**: Users are defined in source code (`auth.py`), not stored in a persistent database.
4. **WebSocket-Only Telemetry**: Real-time data requires WebSocket support in the client browser.
5. **OPC-UA Dependency**: The `asyncua` library is required for OPC-UA functionality; optional but enabled by default.
6. **No HTTPS/TLS**: The development configuration does not enforce encrypted communication.
7. **10Hz Simulation Rate**: The reactor simulation updates at 100ms intervals (10 ticks per second).

### 2.6 Assumptions and Dependencies

**Assumptions:**
- Users have a modern web browser with WebSocket and WebGL support.
- The backend and frontend are run on the same machine or local network.
- Python 3.10+ and Node.js 18+ are pre-installed on the host machine.

**Dependencies:**
| Dependency | Purpose |
|-----------|---------|
| `fastapi`, `uvicorn` | Web server and API framework |
| `numpy`, `pandas` | Numerical computation and data manipulation |
| `scikit-learn` | ML-based anomaly detection (Isolation Forest) |
| `sqlalchemy` | ORM for SQLite database |
| `asyncua` | OPC-UA server implementation |
| `python-jose` | JWT token encoding/decoding |
| `passlib` | Password hashing (SHA-256/bcrypt) |
| `fpdf2` | PDF report generation |
| `python-docx` | Word document report generation |
| `react`, `react-dom` | Frontend UI framework |
| `@react-three/fiber`, `three` | 3D reactor visualization |
| `recharts` | Real-time charting |
| `framer-motion` | UI animations |
| `lucide-react` | Icon library |

---

## 3. System Features / Functional Requirements

### 3.1 User Authentication System

**Priority:** High

| ID | Requirement |
|----|-------------|
| FR-AUTH-01 | The system shall provide a login page where users can enter a username and password. |
| FR-AUTH-02 | The system shall verify user credentials against the user database. |
| FR-AUTH-03 | The system shall issue a JWT access token upon successful authentication (HS256 algorithm). |
| FR-AUTH-04 | The system shall return the user's role, username, and token expiry time upon login. |
| FR-AUTH-05 | The system shall support JWT token expiration (configurable, default: 30 minutes). |
| FR-AUTH-06 | The system shall reject API requests with invalid or expired tokens with HTTP 401. |
| FR-AUTH-07 | The system shall enforce role-based access control on all API endpoints. |
| FR-AUTH-08 | The system shall support WebSocket authentication via `?token=<jwt>` query parameter. |
| FR-AUTH-09 | The system shall provide a `/api/auth/me` endpoint to retrieve current user info. |
| FR-AUTH-10 | The system shall support an `AUTH_ENABLED` environment variable to disable authentication for development. |

### 3.2 Reactor Physics Simulation

**Priority:** High

| ID | Requirement |
|----|-------------|
| FR-SIM-01 | The system shall simulate reactor temperature with heating and cooling power calculations. |
| FR-SIM-02 | The system shall simulate reactor pressure based on temperature and gas flow dynamics. |
| FR-SIM-03 | The system shall simulate reactor vibration with resonance and damping physics. |
| FR-SIM-04 | The system shall simulate agitator rotation with configurable RPM setpoints. |
| FR-SIM-05 | The system shall simulate Cl₂ (chlorine) gas flow rate and valve positions. |
| FR-SIM-06 | The system shall update all process variables at a rate of 10 Hz (every 100ms). |
| FR-SIM-07 | The system shall implement Arrhenius-based reaction kinetics for three consecutive chlorination reactions (Phenol → 2-CP → 2,4-DCP → TCP). |
| FR-SIM-08 | The system shall calculate heat generation from exothermic reactions and feed it back to the temperature model. |
| FR-SIM-09 | The system shall support fault injection for: heater failure, sensor drift, imbalance, and overheat conditions. |
| FR-SIM-10 | The system shall implement an emergency SCRAM shutdown procedure. |

### 3.3 Recipe State Machine (ISA-88)

**Priority:** High

| ID | Requirement |
|----|-------------|
| FR-REC-01 | The system shall implement a state machine with 10 sequential phases: IDLE, LOAD_PHENOL, ADD_SOLVENT, HEATING, HOLD_TEMP, ADD_CATALYST, CHLORINATING, COOLING, SEPARATING, COMPLETE. |
| FR-REC-02 | Additionally, the system shall support ABORTED and SAFETY_HOLD states. |
| FR-REC-03 | The system shall enforce sequential execution — phases must complete in order with dependency checking. |
| FR-REC-04 | Each recipe step shall have a defined name, description, target temperature, duration, tolerance, and prerequisite steps. |
| FR-REC-05 | The system shall allow starting a recipe only from the IDLE state. |
| FR-REC-06 | The system shall allow aborting a recipe at any time. |
| FR-REC-07 | The system shall allow resetting a completed or aborted recipe back to IDLE. |
| FR-REC-08 | The system shall provide auto-actions per step (e.g., automatic valve openings, heater activation). |
| FR-REC-09 | The system shall provide detailed status including current step index, step progress, elapsed time, and all step statuses via API. |

### 3.4 Safety Interlocks

**Priority:** High

| ID | Requirement |
|----|-------------|
| FR-INT-01 | The system shall prevent discharge valve opening if pressure > 1.2 bar or temperature > 60°C. |
| FR-INT-02 | The system shall prevent Cl₂ valve opening if agitator RPM < 50. |
| FR-INT-03 | The system shall prevent chlorination start if temperature is not at 75°C ± 2°C. |
| FR-INT-04 | The system shall prevent step transitions if pressure exceeds safety limits. |
| FR-INT-05 | The system shall report failed interlock conditions with reasons via API. |
| FR-INT-06 | The system shall hold the recipe in SAFETY_HOLD state when interlocks are violated during operation. |

### 3.5 Anomaly Detection (AI/ML)

**Priority:** Medium

| ID | Requirement |
|----|-------------|
| FR-AI-01 | The system shall detect flow blockage conditions when pressure > 1.5 bar and temperature < 40°C simultaneously. |
| FR-AI-02 | The system shall generate a contamination risk alert when temperature exceeds 75°C. |
| FR-AI-03 | The system shall predict bearing failure when vibration > 2.5 (RUL < 48 hours critical alert). |
| FR-AI-04 | The system shall recommend maintenance when vibration > 1.5 (bearing wear warning). |
| FR-AI-05 | The system shall classify overall system health as OPTIMAL, WARNING, or CRITICAL. |
| FR-AI-06 | The system shall log all AI alerts to the audit trail with telemetry snapshots. |

### 3.6 Soft Sensor (Virtual Analyzer)

**Priority:** Medium

| ID | Requirement |
|----|-------------|
| FR-SS-01 | The system shall estimate DCP purity (%) in real-time without laboratory analysis. |
| FR-SS-02 | The system shall estimate TCP impurity (%) as a quality metric. |
| FR-SS-03 | The system shall calculate phenol conversion percentage. |
| FR-SS-04 | The system shall calculate selectivity (moles DCP / moles phenol consumed). |
| FR-SS-05 | The system shall track five chemical species concentrations: Phenol, 2-CP, 2,4-DCP, TCP, dissolved Cl₂. |
| FR-SS-06 | The system shall use Euler integration of concentration ODEs for each simulation tick. |
| FR-SS-07 | The system shall account for mixing efficiency based on agitator RPM. |
| FR-SS-08 | The system shall calculate reaction heat generation for energy balance feedback. |
| FR-SS-09 | The system shall expose soft sensor readings via `/api/soft-sensor` endpoint. |

### 3.7 Real-Time Telemetry & Dashboard

**Priority:** High

| ID | Requirement |
|----|-------------|
| FR-TEL-01 | The system shall stream telemetry data to connected clients via WebSocket at 10 Hz. |
| FR-TEL-02 | The system shall broadcast telemetry to all connected WebSocket clients simultaneously. |
| FR-TEL-03 | The system shall accept control commands from WebSocket clients (bidirectional communication). |
| FR-TEL-04 | The system shall display real-time temperature, pressure, vibration, flow rate, agitator RPM, and purity on the dashboard. |
| FR-TEL-05 | The system shall display real-time temperature trend charts. |
| FR-TEL-06 | The system shall display material balance information (DCP purity, TCP impurity, selectivity). |
| FR-TEL-07 | The system shall store telemetry history in a ring buffer (max 3600 entries). |
| FR-TEL-08 | The system shall provide a REST endpoint for recent telemetry history (last 100 entries). |

### 3.8 3D Reactor Visualization

**Priority:** Medium

| ID | Requirement |
|----|-------------|
| FR-3D-01 | The system shall render a 3D model of the DCP batch reactor using WebGL (Three.js). |
| FR-3D-02 | The 3D model shall rotate at speed proportional to the simulated agitator RPM. |
| FR-3D-03 | The 3D model color shall change based on temperature (blue = cold, red = hot). |
| FR-3D-04 | The 3D model shall shake/vibrate proportional to simulated vibration levels. |
| FR-3D-05 | The system shall support camera orbit controls for user interaction with the 3D scene. |

### 3.9 Batch Record Management (EBR)

**Priority:** High

| ID | Requirement |
|----|-------------|
| FR-EBR-01 | The system shall create an Electronic Batch Record for each production batch. |
| FR-EBR-02 | Each batch record shall contain: batch ID, product name, operator ID, start/end times, phase records, quality summary, and alarm log. |
| FR-EBR-03 | Each phase record shall contain: phase name, duration, parameters, actual PV values, and deviations. |
| FR-EBR-04 | The system shall finalize batch records with SHA-256 hash chaining for tamper evidence (21 CFR Part 11). |
| FR-EBR-05 | The system shall support batch record integrity verification via hash comparison. |
| FR-EBR-06 | The system shall persist batch records as JSON files on disk. |
| FR-EBR-07 | The system shall generate human-readable Markdown reports from batch records. |
| FR-EBR-08 | The system shall provide REST endpoints for listing, viewing, and verifying batch records. |

### 3.10 Data Logging & Report Generation

**Priority:** Medium

| ID | Requirement |
|----|-------------|
| FR-LOG-01 | The system shall log telemetry data every 10 seconds during active batches. |
| FR-LOG-02 | The system shall log control actions with timestamps, action types, values, and sources. |
| FR-LOG-03 | The system shall log events with severity levels (INFO, WARNING, ERROR, CRITICAL). |
| FR-LOG-04 | The system shall generate CSV batch reports with columns: Timestamp, Step Number, Temperature, Flow Rate, Control Actions. |
| FR-LOG-05 | The system shall generate PDF batch reports with formatted tables and summary statistics. |
| FR-LOG-06 | The system shall generate Word (DOCX) batch reports with formatted tables and summary statistics. |
| FR-LOG-07 | The system shall list all available batch report files with metadata (filename, size, creation date). |
| FR-LOG-08 | The system shall allow downloading individual batch reports by filename. |

### 3.11 OPC-UA Industrial Integration

**Priority:** Low

| ID | Requirement |
|----|-------------|
| FR-OPC-01 | The system shall run an OPC-UA server on `opc.tcp://0.0.0.0:4840/dcp-twin/`. |
| FR-OPC-02 | The system shall expose reactor PV nodes (temperature, pressure, flow, pH, RPM, vibration, purity) as read-only OPC-UA variables. |
| FR-OPC-03 | The system shall expose setpoint (SP) nodes as writable OPC-UA variables for DCS integration. |
| FR-OPC-04 | The OPC-UA server shall update PV nodes every 1 second from the simulator. |
| FR-OPC-05 | The system shall read writable SP nodes and push setpoint changes back to the simulator. |
| FR-OPC-06 | The system shall expose OPC-UA server status via REST API endpoint. |
| FR-OPC-07 | The OPC-UA server shall be optionally enabled/disabled via `OPCUA_ENABLED` environment variable. |

### 3.12 Control Commands

**Priority:** High

| ID | Requirement |
|----|-------------|
| FR-CTL-01 | The system shall accept temperature setpoint commands. |
| FR-CTL-02 | The system shall accept agitator RPM commands with interlock validation. |
| FR-CTL-03 | The system shall accept Cl₂ valve open/close commands with interlock validation. |
| FR-CTL-04 | The system shall accept discharge valve commands with interlock validation. |
| FR-CTL-05 | The system shall accept recipe commands: START, STOP, RESET. |
| FR-CTL-06 | The system shall accept fault injection toggle commands (Owner only). |
| FR-CTL-07 | The system shall accept heater failure simulation commands. |
| FR-CTL-08 | All control actions shall be logged to the audit trail with operator identity. |

---

## 4. External Interface Requirements

### 4.1 User Interface (UI)

| ID | Requirement |
|----|-------------|
| UI-01 | The system shall provide a responsive web-based login page with username/password fields and role-specific styling. |
| UI-02 | The system shall display a main dashboard with navigation tabs (Dashboard, Reactor 3D, Controls, Recipe, AI Status). |
| UI-03 | The system shall display the 3D reactor model in a WebGL canvas with orbit controls. |
| UI-04 | The system shall display real-time telemetry values with color-coded criticality indicators (green = normal, yellow = warning, red = critical). |
| UI-05 | The system shall display interactive chart panels with Recharts line graphs for temperature trends. |
| UI-06 | The system shall provide a Control Panel with sliders (temperature, RPM), toggle switches (valves, faults), and action buttons (Start/Stop/Reset recipe). |
| UI-07 | The system shall provide a Recipe Panel showing all recipe steps, progress indicators, and detailed phase information. |
| UI-08 | The system shall display AI status panel with anomaly alerts, RUL predictions, and system health indicators. |
| UI-09 | The system shall display a user info bar showing logged-in username, role, and a logout button. |
| UI-10 | The system shall use role-based view rendering (Worker View vs Owner View with different control permissions). |

### 4.2 Hardware Interface

| ID | Requirement |
|----|-------------|
| HW-01 | The system shall operate on any standard desktop/laptop computer with a WebGL-capable GPU. |
| HW-02 | No direct hardware interfaces are required (simulation-only system). |
| HW-03 | The OPC-UA server can interface indirectly with industrial PLCs and DCS hardware via network. |

### 4.3 Software Interface

| ID | Requirement |
|----|-------------|
| SW-01 | **REST API** — FastAPI backend exposes RESTful endpoints at `/api/*` for CRUD operations on reactor status, recipes, batches, events, and control commands. |
| SW-02 | **WebSocket API** — Real-time bidirectional communication at `/ws` endpoint for telemetry streaming and command dispatch. |
| SW-03 | **SQLite Database** — SQLAlchemy ORM with two tables: `process_logs` (Log) and `telemetry` (TelemetryHistory). |
| SW-04 | **OPC-UA Server** — `asyncua` library implementing OPC-UA endpoint at TCP port 4840, namespace `http://dcp-digital-twin/`. |
| SW-05 | **File System** — Batch reports (CSV/PDF/DOCX) and Electronic Batch Records (JSON) stored in `logs/` and `data/batch_records/` directories respectively. |

### 4.4 Communication Interface

| ID | Requirement |
|----|-------------|
| COM-01 | **HTTP/HTTPS** — RESTful API communication over HTTP (port 8000 default). |
| COM-02 | **WebSocket (ws://)** — Full-duplex telemetry streaming over WebSocket protocol. |
| COM-03 | **OPC-UA (opc.tcp://)** — Industrial communication protocol over TCP port 4840. |
| COM-04 | **CORS** — Cross-Origin Resource Sharing enabled for all origins (development configuration). |
| COM-05 | **JSON** — All API request/response payloads use JSON format. |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement |
|----|-------------|
| NFR-PERF-01 | The simulation loop shall maintain a consistent 10 Hz update rate (100ms per tick). |
| NFR-PERF-02 | Telemetry WebSocket broadcast latency shall be < 50ms under normal conditions. |
| NFR-PERF-03 | REST API response time shall be < 500ms for all status/read endpoints. |
| NFR-PERF-04 | The 3D reactor visualization shall render at ≥ 30 FPS on modern hardware. |
| NFR-PERF-05 | The system shall support at least 10 concurrent WebSocket connections. |

### 5.2 Security

| ID | Requirement |
|----|-------------|
| NFR-SEC-01 | User passwords shall be hashed using SHA-256 (Passlib CryptContext). |
| NFR-SEC-02 | JWT tokens shall use HS256 algorithm with a configurable secret key. |
| NFR-SEC-03 | All authenticated API endpoints shall validate JWT tokens and enforce role hierarchy. |
| NFR-SEC-04 | WebSocket connections shall validate JWT tokens via query parameter when auth is enabled. |
| NFR-SEC-05 | Electronic Batch Records shall use SHA-256 hash chaining for tamper evidence. |
| NFR-SEC-06 | The `JWT_SECRET_KEY` shall be configurable via environment variable for production deployment. |

### 5.3 Reliability

| ID | Requirement |
|----|-------------|
| NFR-REL-01 | The system shall gracefully handle WebSocket disconnections without crashing the simulation loop. |
| NFR-REL-02 | The system shall implement graceful startup and shutdown events for OPC-UA server lifecycle. |
| NFR-REL-03 | The system shall maintain telemetry data in a ring buffer to prevent memory overflow (max 3600 entries). |
| NFR-REL-04 | The system shall clamp all chemical concentrations ≥ 0 for numerical stability. |
| NFR-REL-05 | The system shall support fallback authentication when optional dependencies (`jose`, `passlib`) are unavailable. |

### 5.4 Scalability

| ID | Requirement |
|----|-------------|
| NFR-SCA-01 | The frontend shall be built using component-based architecture (React) for feature extensibility. |
| NFR-SCA-02 | The backend shall use modular file structure with separate modules for simulation, recipes, auth, logging, and OPC-UA. |
| NFR-SCA-03 | The recipe engine shall support extensible recipe step definitions with configurable parameters. |

### 5.5 Usability

| ID | Requirement |
|----|-------------|
| NFR-USE-01 | The system shall provide role-specific UI views (Worker View, Owner View) showing only relevant controls. |
| NFR-USE-02 | The dashboard shall use color-coded indicators for easy visual identification of critical/warning states. |
| NFR-USE-03 | The 3D visualization shall provide intuitive orbit controls (zoom, pan, rotate) for exploring the reactor model. |
| NFR-USE-04 | The system shall provide one-click batch start/stop/reset via the Recipe Panel. |
| NFR-USE-05 | The login page shall display clear error messages for failed authentication attempts. |

### 5.6 Maintainability

| ID | Requirement |
|----|-------------|
| NFR-MAI-01 | The backend codebase shall follow modular architecture with separate files per concern (simulator, auth, recipe, logging, etc.). |
| NFR-MAI-02 | All API endpoints shall include docstrings describing their purpose and required role. |
| NFR-MAI-03 | Configuration parameters (JWT expiry, auth toggle, OPC-UA toggle) shall be externalized via environment variables. |

---

## 6. System Models / Diagrams

### 6.1 System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Web Browser)                         │
│  ┌───────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ Login Page │  │ 3D Model │  │ Dashboard  │  │  Control Panel   │  │
│  │  (React)   │  │ (R3F)    │  │ (Recharts) │  │  (React)         │  │
│  └─────┬─────┘  └────┬─────┘  └─────┬──────┘  └───────┬──────────┘  │
│        └──────────────┴──────────────┴─────────────────┘             │
│                        REST (HTTP) + WebSocket                       │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   FastAPI Application Server │
                    │   (Uvicorn ASGI)             │
                    │                              │
                    │  ┌────────────────────────┐  │
                    │  │   Authentication (JWT)  │  │
                    │  │   RBAC Middleware        │  │
                    │  └────────────────────────┘  │
                    │                              │
                    │  ┌────────────────────────┐  │
                    │  │   GodModeReactor        │  │
                    │  │   (Physics Engine)      │  │
                    │  │  ┌──────────────────┐   │  │
                    │  │  │ RecipeEngine     │   │  │
                    │  │  │ (ISA-88 State)   │   │  │
                    │  │  └──────────────────┘   │  │
                    │  │  ┌──────────────────┐   │  │
                    │  │  │ ChlorinationKin. │   │  │
                    │  │  │ (Arrhenius)      │   │  │
                    │  │  └──────────────────┘   │  │
                    │  │  ┌──────────────────┐   │  │
                    │  │  │ DCPSoftSensor    │   │  │
                    │  │  │ (Virtual Analyz.)│   │  │
                    │  │  └──────────────────┘   │  │
                    │  └────────────────────────┘  │
                    │                              │
                    │  ┌────────────────────────┐  │
                    │  │ IntelligentBrain (ML)  │  │
                    │  │ Anomaly Detection      │  │
                    │  └────────────────────────┘  │
                    │                              │
                    │  ┌────────────────────────┐  │
                    │  │ DataLogger / BatchRec. │  │
                    │  │ CSV/PDF/DOCX + EBR     │  │
                    │  └────────────────────────┘  │
                    │                              │
                    └─────┬──────────────┬─────────┘
                          │              │
               ┌──────────▼──┐   ┌───────▼───────┐
               │   SQLite DB  │   │  OPC-UA Server │
               │ (SQLAlchemy) │   │  (Port 4840)   │
               └──────────────┘   └───────┬───────┘
                                          │
                                  ┌───────▼───────┐
                                  │  External DCS  │
                                  │ (PCS7, etc.)   │
                                  └───────────────┘
```

### 6.2 Use Case Diagram

```
                         ┌─────────────────────────────────┐
                         │    Industrial Digital Twin       │
                         │           System                 │
                         │                                  │
   ┌────────┐            │  ┌──────────────────────┐       │
   │ Viewer │──────────▶ │  │ View Live Dashboard  │       │
   └────────┘            │  └──────────────────────┘       │
       │                 │  ┌──────────────────────┐       │
       ├───────────────▶ │  │ View 3D Reactor Model│       │
       │                 │  └──────────────────────┘       │
       │                 │  ┌──────────────────────┐       │
       └───────────────▶ │  │ View AI Alerts/Health│       │
                         │  └──────────────────────┘       │
   ┌────────┐            │  ┌──────────────────────┐       │
   │ Worker │──────────▶ │  │ Start/Stop/Reset     │       │
   └────────┘            │  │ Batch Recipe          │       │
       │                 │  └──────────────────────┘       │
       │                 │  ┌──────────────────────┐       │
       ├───────────────▶ │  │ Send Control Commands │       │
       │                 │  └──────────────────────┘       │
       │                 │  ┌──────────────────────┐       │
       └───────────────▶ │  │ Generate & Download   │       │
                         │  │ Batch Reports         │       │
                         │  └──────────────────────┘       │
   ┌────────┐            │  ┌──────────────────────┐       │
   │ Owner  │──────────▶ │  │ Inject/Toggle Faults │       │
   └────────┘            │  └──────────────────────┘       │
       │                 │  ┌──────────────────────┐       │
       ├───────────────▶ │  │ Manage Batch Records │       │
       │                 │  │ (View, Verify Hash)  │       │
       │                 │  └──────────────────────┘       │
       │                 │  ┌──────────────────────┐       │
       └───────────────▶ │  │ User/Role Management │       │
                         │  └──────────────────────┘       │
                         │                                  │
   ┌────────┐            │  ┌──────────────────────┐       │
   │  DCS   │◀─────────▶ │  │ OPC-UA PV/SP Exchange│       │
   │(Extern)│            │  └──────────────────────┘       │
   └────────┘            └─────────────────────────────────┘
```

### 6.3 Recipe State Machine Diagram

```
                    ┌───────┐
             ┌─────│ IDLE  │◀────────────────────────────────┐
             │     └───┬───┘                                  │
             │         │ START                            RESET│
             │         ▼                                      │
             │  ┌─────────────┐                               │
             │  │ LOAD_PHENOL │                               │
             │  └──────┬──────┘                               │
             │         │ duration complete                    │
             │         ▼                                      │
             │  ┌─────────────┐                               │
             │  │ ADD_SOLVENT  │                               │
             │  └──────┬──────┘                               │
             │         │ duration complete                    │
             │         ▼                                      │
             │  ┌─────────────┐                               │
             │  │   HEATING   │                               │
             │  └──────┬──────┘                               │
     ABORT   │         │ temp ≥ target ± tolerance            │
     at any  │         ▼                                      │
     time    │  ┌─────────────┐                               │
      │      │  │  HOLD_TEMP  │                         ┌──────────┐
      │      │  └──────┬──────┘                         │ COMPLETE │
      │      │         │ duration complete               └──────────┘
      │      │         ▼                                      ▲
      │      │  ┌──────────────┐                              │
      │      │  │ ADD_CATALYST │                              │
      │      │  └──────┬───────┘                              │
      │      │         │ duration complete                    │
      │      │         ▼                                      │
      │      │  ┌──────────────┐  interlock: T=75°C ± 2°C    │
      │      │  │ CHLORINATING │──────────────────────┐       │
      │      │  └──────┬───────┘                      │       │
      │      │         │ duration complete      ┌──────▼────┐ │
      │      │         ▼                        │SAFETY_HOLD│ │
      │      │  ┌──────────────┐                └───────────┘ │
      │      │  │   COOLING    │                              │
      │      │  └──────┬───────┘                              │
      │      │         │ temp ≤ target                        │
      │      │         ▼                                      │
      │      │  ┌──────────────┐                              │
      │      │  │  SEPARATING  │──────────────────────────────┘
      │      │  └──────────────┘
      │      │
      ▼      │
 ┌─────────┐ │
 │ ABORTED │◀┘
 └─────────┘
```

### 6.4 Data Flow Diagram (Level 0)

```
  ┌────────────┐                              ┌────────────────┐
  │   User     │── Login Credentials ────────▶│ Authentication │
  │  (Browser) │◀──── JWT Token ──────────────│    Module      │
  └─────┬──────┘                              └────────────────┘
        │
        │  Control Commands (WebSocket / REST)
        ▼
  ┌─────────────────┐    Telemetry     ┌──────────────────────┐
  │   API Gateway   │◀───────────────│   Reactor Simulator   │
  │  (FastAPI)      │                │   (GodModeReactor)     │
  │                 │── Commands ───▶│                        │
  └───────┬─────────┘                │  ┌──────────────────┐  │
          │                          │  │  Recipe Engine    │  │
          │  Telemetry               │  │  (State Machine)  │  │
          │  to all clients          │  └──────────────────┘  │
          ▼                          │  ┌──────────────────┐  │
  ┌───────────────┐                  │  │  Soft Sensor     │  │
  │  WebSocket    │                  │  │  (Purity Est.)   │  │
  │  Broadcaster  │                  │  └──────────────────┘  │
  └───────────────┘                  │  ┌──────────────────┐  │
                                     │  │  Kinetics Engine │  │
          ┌──────────────────┐       │  │  (Arrhenius)     │  │
          │   Data Logger    │◀──────│  └──────────────────┘  │
          │  (Telemetry Log) │       └──────────────────────┘
          └──────┬───────────┘                │
                 │                             │
        ┌────────▼────────┐          ┌─────────▼──────────┐
        │ Report Generator│          │   OPC-UA Server    │
        │ CSV / PDF / DOCX│          │   (Port 4840)      │
        └─────────────────┘          └────────────────────┘
                                              │
                                     ┌────────▼──────────┐
                                     │  External DCS     │
                                     └───────────────────┘
```

### 6.5 ER Diagram (Database)

```
┌───────────────────────────┐      ┌───────────────────────────┐
│       process_logs        │      │        telemetry           │
├───────────────────────────┤      ├───────────────────────────┤
│ id       INTEGER (PK)     │      │ id        INTEGER (PK)    │
│ timestamp DATETIME        │      │ timestamp  DATETIME       │
│ level    STRING           │      │ temperature FLOAT         │
│ message  STRING           │      │ pressure   FLOAT          │
│ meta_data JSON (nullable) │      │ ph         FLOAT          │
└───────────────────────────┘      │ purity     FLOAT          │
                                   └───────────────────────────┘

┌─────────────────────────────────────────────┐
│     Electronic Batch Records (JSON Files)    │
├─────────────────────────────────────────────┤
│ batch_id            STRING                   │
│ product_name        STRING                   │
│ operator_id         STRING                   │
│ batch_start_time    DATETIME                 │
│ batch_end_time      DATETIME                 │
│ phases[]            List<PhaseRecord>         │
│   ├─ phase_name     STRING                   │
│   ├─ start_time     DATETIME                 │
│   ├─ end_time       DATETIME                 │
│   ├─ duration_sec   FLOAT                    │
│   ├─ parameters     DICT                     │
│   ├─ actual_values  DICT                     │
│   ├─ deviations[]   List<STRING>             │
│   └─ operator_id    STRING                   │
│ quality_summary     DICT                     │
│ alarm_log[]         List<AlarmEntry>          │
│ hash                STRING (SHA-256)         │
│ previous_hash       STRING (SHA-256 chain)   │
└─────────────────────────────────────────────┘
```

---

## 7. Data Requirements

### 7.1 Database Tables

| Table | Columns | Purpose |
|-------|---------|---------|
| `process_logs` | id (PK), timestamp, level, message, meta_data (JSON) | Store persistent audit/event logs |
| `telemetry` | id (PK), timestamp, temperature, pressure, ph, purity | Store persistent telemetry snapshots |

### 7.2 In-Memory Data Stores

| Store | Type | Size | Purpose |
|-------|------|------|---------|
| `telemetry_buffer` | Ring buffer (deque) | 3600 entries max | Recent telemetry for API queries |
| `event_buffer` | Ring buffer (deque) | 500 entries max | Recent events for API queries |
| `control_action_buffer` | Ring buffer (deque) | 500 entries max | Recent control actions |
| `audit_trail` | List | 200 entries max | In-memory audit log for WebSocket broadcast |
| `reactor.state` | Dict | N/A | Current reactor process variables |
| `concentrations` | Dict | 5 species | Chemical concentration state vector |

### 7.3 File-Based Data Storage

| Path | Format | Purpose |
|------|--------|---------|
| `logs/*.csv` | CSV | Batch telemetry reports |
| `logs/*.pdf` | PDF | Formatted batch reports |
| `logs/*.docx` | DOCX | Word batch reports |
| `data/batch_records/*.json` | JSON | Electronic Batch Records (ISA-88) |
| `data/batch_records/chain_hash.txt` | Text | Last hash for chain continuity |
| `digital_twin_production.db` | SQLite | Persistent database for logs and telemetry |

### 7.4 Data Validation Rules

| Rule | Description |
|------|-------------|
| Temperature Range | 0°C ≤ T ≤ 200°C (clamped in simulation) |
| Pressure Range | 0.5 bar ≤ P ≤ 5.0 bar |
| Concentration Clamp | All chemical concentrations ≥ 0.0 mol/L |
| RPM Range | 0 ≤ RPM ≤ 500 |
| Valve Position | 0% ≤ position ≤ 100% |
| JWT Token | Must be valid HS256 JWT with `sub` and `role` claims |
| Batch ID Format | ISO timestamp-based unique identifier |
| Hash Chain | SHA-256, verified against stored hash for tamper detection |

---

## 8. Appendices

### 8.1 Glossary

| Term | Definition |
|------|-----------|
| **Digital Twin** | A digital counterpart of a physical process that receives real-time data and simulates behavior |
| **Batch Reactor** | A chemical reactor that processes material in discrete batches |
| **Phenol Chlorination** | Chemical process of adding chlorine atoms to phenol to produce chlorophenol derivatives |
| **Arrhenius Equation** | Mathematical formula relating reaction rate constant to temperature |
| **Euler Integration** | Numerical method for solving ordinary differential equations step-by-step |
| **Hash Chaining** | Cryptographic technique where each record's hash includes the previous record's hash |
| **Ghost Line** | Visual reference showing expected (ideal) process trajectory vs actual |
| **SCRAM** | Emergency reactor shutdown procedure |

### 8.2 API Endpoint Summary

| Method | Endpoint | Role Required | Description |
|--------|---------|---------------|-------------|
| POST | `/api/auth/login` | None | Authenticate user |
| POST | `/api/auth/logout` | None | Logout |
| GET | `/api/auth/me` | Viewer+ | Get current user info |
| GET | `/` | None | Health check |
| GET | `/api/status` | Viewer+ | Get reactor status |
| GET | `/api/recipe/status` | Viewer+ | Get recipe status |
| GET | `/api/recipe/steps` | Viewer+ | Get all recipe steps |
| POST | `/api/recipe/start` | Worker+ | Start batch recipe |
| POST | `/api/recipe/stop` | Worker+ | Abort batch recipe |
| POST | `/api/recipe/reset` | Worker+ | Reset recipe to IDLE |
| GET | `/api/batch/summary` | Viewer+ | Batch summary stats |
| GET | `/api/batch/report` | Worker+ | Download CSV report |
| GET | `/api/batch/report/pdf` | Worker+ | Download PDF report |
| GET | `/api/batch/report/docx` | Worker+ | Download DOCX report |
| GET | `/api/batch/reports` | Viewer+ | List all reports |
| GET | `/api/batch/report/{filename}` | Worker+ | Download specific report |
| GET | `/api/telemetry/history` | Viewer+ | Recent telemetry |
| GET | `/api/events` | Viewer+ | Recent events |
| GET | `/api/control-actions` | Viewer+ | Control action log |
| POST | `/api/control` | Worker+ | Send control command |
| GET | `/api/faults` | Viewer+ | Get fault status |
| POST | `/api/fault/{name}/toggle` | Owner | Toggle fault |
| GET | `/api/interlocks` | Viewer+ | Interlock status |
| GET | `/api/soft-sensor` | Viewer+ | Soft sensor readings |
| GET | `/api/opcua/status` | Viewer+ | OPC-UA status |
| GET | `/api/v1/batch-records` | Owner | List EBR records |
| GET | `/api/v1/batch-records/{id}` | Owner | Get EBR JSON |
| GET | `/api/v1/batch-records/{id}/report` | Owner | Get EBR markdown |
| POST | `/api/v1/batch-records/{id}/verify` | Owner | Verify EBR hash |
| WS | `/ws` | Viewer+ (optional) | Real-time telemetry |

### 8.3 Default User Credentials (Development)

| Username | Password | Role |
|----------|----------|------|
| worker | dcp2026 | WORKER |
| worker1 | worker123 | WORKER |
| owner | admin | OWNER |
| owner1 | owner456 | OWNER |
| viewer1 | view789 | VIEWER |

### 8.4 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | `dcp-twin-dev-secret-...` | Secret key for JWT signing |
| `JWT_EXPIRE_MINUTES` | `30` | Token expiration time (minutes) |
| `AUTH_ENABLED` | `true` | Enable/disable authentication |
| `OPCUA_ENABLED` | `true` | Enable/disable OPC-UA server |

### 8.5 Future Enhancements

1. **Persistent User Database** — Migrate from hardcoded users to database-backed user management with registration.
2. **HTTPS/TLS Support** — Add SSL certificates for encrypted production communication.
3. **Historical Trend Analysis** — Long-term telemetry storage with time-series database (InfluxDB/TimescaleDB).
4. **Advanced ML Models** — Integrate Isolation Forest and LSTM models for predictive maintenance.
5. **Mobile Responsive UI** — Optimize dashboard for tablet and mobile devices.
6. **Multi-Reactor Support** — Support monitoring and controlling multiple reactor instances.
7. **Email/SMS Alerting** — Push notifications for critical anomalies and safety events.
8. **Cloud Deployment** — Containerize with Docker and deploy on AWS/Azure/GCP.
9. **Audit Trail Export** — Export audit logs to CSV/PDF for regulatory compliance.
10. **PLC Direct Integration** — Connect to real hardware PLCs via Modbus TCP or OPC-UA client mode.

---

**End of Document**
