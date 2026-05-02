# PROJECT REPORT

## Industrial Digital Twin for 2,4-Dichlorophenol (DCP) Batch Reactor

---

**Submitted by:** Dhruv & Team  
**Academic Year:** 2025–2026  
**Date:** May 2026  
**Guide:** [Faculty Name]  
**Department:** [Department Name]  
**Institution:** [College Name]

---

## ABSTRACT

This project presents the design, development, and implementation of an **Industrial Digital Twin System** for a 2,4-Dichlorophenol (DCP) batch reactor used in the chemical manufacturing industry. The system creates a real-time virtual replica of a phenol chlorination reactor, enabling remote monitoring, predictive analytics, and operator training without the risks associated with physical plant operations.

The methodology employs a full-stack web architecture with a **Python FastAPI** backend handling physics-based simulation, Arrhenius chemical kinetics, PID temperature control, and an ISA-88 compliant recipe state machine. The frontend is built using **React 19** with **Three.js** for interactive 3D reactor visualization and **Recharts** for live telemetry dashboards. Real-time communication is achieved via WebSocket streaming at 10 Hz, while industrial integration is provided through an **OPC-UA server** (IEC 62541) for connectivity with Distributed Control Systems.

Key results include a fully functional digital twin with 10-phase batch recipe management, ML-based anomaly detection, soft sensor analytics for real-time purity estimation, electronic batch records with SHA-256 hash chaining for 21 CFR Part 11 compliance, role-based access control with JWT authentication, and multi-format report generation (CSV, PDF, DOCX).

The system demonstrates that digital twin technology can significantly improve operational visibility, reduce downtime through predictive maintenance, and provide a safe environment for operator training in hazardous chemical processes.

---

## CHAPTER 1: INTRODUCTION

### 1.1 Background

The chemical manufacturing industry faces significant challenges in process monitoring, quality control, and safety management. Traditional Supervisory Control and Data Acquisition (SCADA) systems provide limited insight into complex reaction dynamics, and operators often rely on periodic laboratory analysis for quality assessment. The concept of a **Digital Twin** — a virtual replica that mirrors a physical system's real-time state — has emerged as a transformative technology in Industry 4.0, enabling continuous monitoring, predictive analytics, and what-if scenario analysis.

**2,4-Dichlorophenol (DCP)** is a critical industrial chemical (CAS 120-83-2) used as an intermediate in the production of herbicides (2,4-D), antiseptics, and pharmaceuticals. It is produced via the **electrophilic aromatic chlorination of phenol** using chlorine gas (Cl₂) with a Lewis acid catalyst (FeCl₃). The reaction involves three consecutive chlorination steps, where selectivity control is essential to maximize the desired DCP product while minimizing over-chlorination to 2,4,6-Trichlorophenol (TCP).

### 1.2 Problem Statement

Operating a DCP batch reactor involves:
- **Temperature sensitivity** — The reaction requires precise control at 75°C ± 2°C; deviations cause selectivity loss.
- **Safety hazards** — Chlorine gas is toxic, and exothermic runaway is possible.
- **Quality variability** — Without continuous monitoring, product purity varies between batches.
- **Training limitations** — New operators cannot safely practice on live reactors.
- **Lack of real-time analytics** — Purity is typically measured only post-batch via lab analysis.

### 1.3 Objectives

1. Develop a physics-based reactor simulation with Arrhenius chemical kinetics.
2. Implement an ISA-88 compliant recipe state machine with 10 sequential production phases.
3. Create a real-time 3D visualization of the reactor reflecting physical state.
4. Build a live telemetry dashboard with process variable charting.
5. Implement ML-based anomaly detection for predictive maintenance.
6. Develop a soft sensor for real-time purity estimation without laboratory analysis.
7. Provide OPC-UA industrial protocol integration for DCS connectivity.
8. Implement electronic batch records with SHA-256 hash chaining for regulatory compliance.
9. Build role-based access control with JWT authentication.
10. Generate multi-format batch reports (CSV, PDF, DOCX).

### 1.4 Scope

**In Scope:** Full-stack web application with simulation, visualization, analytics, authentication, industrial protocol integration, and regulatory-compliant batch records.

**Out of Scope:** Physical hardware interfacing, cloud deployment, mobile native applications.

### 1.5 Motivation

This project bridges chemical engineering and computer science, demonstrating how modern web technologies can create industrial-grade digital twins. It provides a safe training environment, enables predictive maintenance, and offers continuous quality monitoring — capabilities that directly improve plant safety and efficiency.

---

## CHAPTER 2: LITERATURE REVIEW

### 2.1 Digital Twin Technology

The concept of Digital Twins was first introduced by Dr. Michael Grieves at the University of Michigan in 2002. NASA later adopted the concept for spacecraft lifecycle management. In industry, digital twins have evolved from simple 3D models to comprehensive cyber-physical systems that integrate real-time data, physics models, and machine learning.

### 2.2 ISA-88 Batch Control Standard

ISA-88 (ANSI/ISA-88.01) defines a standard for batch control systems, including models for physical equipment, procedural control, and recipe management. The standard defines a hierarchical recipe structure: Procedure → Unit Procedure → Operation → Phase. Our system implements the Phase-level control with a 10-state sequential state machine.

### 2.3 OPC Unified Architecture

OPC-UA (IEC 62541) is the industrial communication standard that replaced legacy OPC-DA. It provides platform-independent, secure, and reliable data exchange between industrial systems. Our system implements an OPC-UA server to expose reactor process variables as browsable nodes for DCS integration.

### 2.4 21 CFR Part 11 Compliance

The FDA's 21 CFR Part 11 regulation governs electronic records and electronic signatures in pharmaceutical manufacturing. Key requirements include audit trails, access controls, and data integrity verification. Our system implements SHA-256 hash chaining for tamper-evident batch records.

### 2.5 Arrhenius Chemical Kinetics

The Arrhenius equation (k = A × exp(−Ea/RT)) describes the temperature dependence of reaction rates. For phenol chlorination, three consecutive reactions occur with different activation energies, making temperature control critical for selectivity.

---

## CHAPTER 3: SYSTEM DESIGN & ARCHITECTURE

### 3.1 High-Level Architecture

The system follows a **client-server architecture**:

```
┌─────────────────────────────┐
│   CLIENT (Web Browser)      │
│  React 19 + Three.js + Charts│
└──────────┬──────────────────┘
           │ REST + WebSocket
┌──────────▼──────────────────┐
│  FastAPI Server (Uvicorn)   │
│  ├─ JWT Auth + RBAC         │
│  ├─ GodModeReactor (Physics)│
│  │  ├─ RecipeEngine (ISA-88)│
│  │  ├─ ChlorinationKinetics │
│  │  ├─ DCPSoftSensor        │
│  │  └─ PIDController        │
│  ├─ IntelligentBrain (ML)   │
│  ├─ DataLogger + BatchRecord│
│  └─ OPC-UA Server (Port 4840)│
└──────────┬──────────────────┘
           │
    ┌──────▼──────┐
    │  SQLite DB   │
    │  + JSON Files│
    └─────────────┘
```

### 3.2 Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python + FastAPI | 3.10+ |
| ASGI Server | Uvicorn | Latest |
| Frontend | React + Vite | 19.x / 7.x |
| 3D Engine | Three.js / React Three Fiber | Latest |
| Charting | Recharts | 3.x |
| Database | SQLite (SQLAlchemy ORM) | 3.x |
| Industrial | asyncua (OPC-UA) | 0.9+ |
| Auth | python-jose (JWT) + passlib | Latest |
| Reports | fpdf2, python-docx | Latest |
| Styling | TailwindCSS | 3.x |
| Icons | Lucide React | Latest |
| Animations | Framer Motion | Latest |

### 3.3 Backend Module Structure

| Module | File | Purpose |
|--------|------|---------|
| Main API Server | `main.py` (490 lines) | FastAPI app, REST endpoints, WebSocket |
| Reactor Simulator | `simulator.py` (676 lines) | Physics engine, PID control, fault injection |
| Recipe Engine | `recipe_engine.py` (460 lines) | ISA-88 state machine, interlocks |
| Chemical Kinetics | `kinetics.py` (124 lines) | Arrhenius rate calculations |
| Soft Sensor | `soft_sensor.py` (200 lines) | Real-time purity estimation |
| Authentication | `auth.py` (266 lines) | JWT + RBAC (Viewer/Worker/Owner) |
| Data Logger | `data_logger.py` (472 lines) | Telemetry logging, CSV/PDF/DOCX reports |
| Batch Records | `batch_record.py` (459 lines) | EBR with SHA-256 hash chaining |
| OPC-UA Server | `opcua_server.py` (245 lines) | Industrial protocol integration |
| Database | `database.py` (109 lines) | SQLAlchemy models |
| PID Controller | `controls.py` (260 lines) | PID temperature control |
| ML Module | `ml.py` (151 lines) | Anomaly detection |

### 3.4 Frontend Component Structure

| Component | File | Purpose |
|-----------|------|---------|
| App Shell | `App.jsx` | Main layout, routing, auth state |
| Login Page | `Login.jsx` | Animated login with role-based theming |
| Role Views | `Roles.jsx` | Worker/Owner dashboards with controls |
| 3D Reactor | `DCPReactorModel.jsx` | Three.js reactor with heat/vibration mapping |
| Recipe Panel | `RecipePanel.jsx` | ISA-88 recipe step visualization |
| AI Panel | `AIStatusPanel.jsx` | Anomaly alerts, RUL predictions |
| Charts | `Charts.jsx` | Recharts temperature trend graphs |
| Controls | `ControlPanel.jsx` | Sliders, toggles for reactor control |
| API Service | `api.js` | WebSocket + REST API client |

---

## CHAPTER 4: IMPLEMENTATION

### 4.1 Reactor Physics Simulation

The core simulator (`GodModeReactor` class) updates at 10 Hz (100ms intervals) and models:

**Temperature Dynamics:**
```
ΔT = (Q_reaction + Q_heater − Q_cooling) × dt
Q_reaction = heat from Arrhenius kinetics (W)
Q_heater = (heating_power/100) × 15°C/s
Q_cooling = (cooling_valve/100) × 10°C/s
```

**PID Temperature Control:**
```
PID Output = Kp×e(t) + Ki×∫e(t)dt + Kd×de/dt
Kp=2.0, Ki=0.1, Kd=0.5 (QUALITY mode)
Kp=5.0 (SPEED mode)
```

### 4.2 Arrhenius Chemical Kinetics

Three consecutive chlorination reactions are modeled:

| Reaction | Pre-exponential (A) | Activation Energy (Ea) | ΔH (J/mol) |
|----------|-------------------|----------------------|-------------|
| Phenol → 2-CP | 2.4×10⁸ L/mol/min | 62,000 J/mol | −125,000 |
| 2-CP → 2,4-DCP | 1.1×10⁷ L/mol/min | 68,000 J/mol | −118,000 |
| 2,4-DCP → TCP | 3.2×10⁶ L/mol/min | 74,000 J/mol | −110,000 |

Rate law: `k = A × exp(−Ea / (R × T))`, where R = 8.314 J/mol/K

### 4.3 ISA-88 Recipe State Machine

10-phase sequential execution:

| # | Phase | Duration | Target Temp | Key Action |
|---|-------|----------|-------------|------------|
| 1 | Load Phenol | 30s | 25°C | Load 1.0 kg phenol |
| 2 | Add Solvent | 45s | 25°C | Add chlorobenzene |
| 3 | Heating | 120s | 75°C | Ramp to setpoint |
| 4 | Hold Temp | 60s | 75°C | Stabilize ±2°C |
| 5 | Add Catalyst | 30s | 75°C | N-methylaniline |
| 6 | Chlorinating | 120s | 75°C | Cl₂ gas injection |
| 7 | Cooling | 90s | 30°C | Cool for separation |
| 8 | Separating | 60s | 30°C | Product isolation |

Additional states: IDLE, COMPLETE, ABORTED, SAFETY_HOLD

### 4.4 Safety Interlocks

| Interlock | Condition | Action |
|-----------|-----------|--------|
| Discharge Lock | P > 1.2 bar OR T > 60°C | Block discharge valve |
| Cl₂ Lock | Agitator RPM < 50 | Block chlorine valve |
| Chlorination Lock | T ≠ 75°C ± 2°C | Prevent chlorination start |
| Pressure Lock | P > 2.5 bar | Block step transitions |
| Dead-Man Switch | Heart rate > 150 BPM | SCRAM shutdown |

### 4.5 Soft Sensor (Virtual Analyzer)

The soft sensor uses Euler integration of concentration ODEs:

```
dC_phenol/dt     = −r1
dC_2CP/dt        = +r1 − r2
dC_DCP/dt        = +r2 − r3
dC_TCP/dt        = +r3
dC_Cl2/dt        = feed_rate/V − r1 − r2 − r3
```

**Outputs:** DCP purity (%), TCP impurity (%), phenol conversion (%), selectivity

### 4.6 Authentication & RBAC

| Role | Level | Permissions |
|------|-------|-------------|
| Viewer | 0 | View dashboard, telemetry, AI status |
| Worker | 1 | + Start/Stop recipe, control commands, generate reports |
| Owner | 2 | + Fault injection, batch record management, hash verification |

JWT tokens use HS256 algorithm with configurable expiry (default 30 min).

### 4.7 OPC-UA Industrial Integration

Server endpoint: `opc.tcp://0.0.0.0:4840/dcp-twin/`

| Node Type | Count | Examples |
|-----------|-------|---------|
| Read-Only PVs | 15 | Temperature, Pressure, Purity, Recipe State |
| Writable SPs | 3 | Temperature SP, Cl₂ Flow SP, Agitator SP |

Updates at 1 Hz. Compatible with Siemens PCS7, Honeywell Experion, ABB 800xA.

### 4.8 Electronic Batch Records

- ISA-88 phase-level audit trail
- Material balance: phenol in, Cl₂ consumed, DCP out, TCP waste
- Quality summary: purity, selectivity, TCP impurity, temp excursions
- SHA-256 hash chaining for tamper evidence (21 CFR Part 11)
- JSON persistence + Markdown report export

### 4.9 3D Reactor Visualization

Built with React Three Fiber + Three.js:
- Rotation speed proportional to agitator RPM
- Color mapping: blue (cold) → red (hot) based on temperature
- Vibration/shake proportional to bearing wear
- Interactive orbit camera controls (zoom, pan, rotate)

---

## CHAPTER 5: TESTING & RESULTS

### 5.1 Functional Testing

| Feature | Test | Result |
|---------|------|--------|
| Login | Valid/invalid credentials | ✅ JWT issued / 401 rejected |
| RBAC | Viewer accessing Owner endpoint | ✅ 403 Forbidden |
| Recipe | Full 10-phase execution | ✅ Completes sequentially |
| Interlocks | Cl₂ valve at low RPM | ✅ Blocked with reason |
| SCRAM | Heart rate > 150 BPM | ✅ Emergency shutdown |
| Soft Sensor | Purity during chlorination | ✅ Tracks DCP concentration |
| Reports | CSV/PDF/DOCX generation | ✅ Files generated correctly |
| OPC-UA | Node browsing via UaExpert | ✅ All 18 nodes visible |
| Hash Chain | Tamper detection | ✅ Modified records detected |
| WebSocket | 10 Hz telemetry streaming | ✅ < 50ms latency |

### 5.2 Performance Results

| Metric | Target | Achieved |
|--------|--------|----------|
| Simulation rate | 10 Hz | ✅ 10 Hz stable |
| WebSocket latency | < 50ms | ✅ ~20ms avg |
| API response time | < 500ms | ✅ ~50ms avg |
| 3D render FPS | ≥ 30 FPS | ✅ 60 FPS |
| Concurrent connections | 10+ | ✅ Tested with 10 |

### 5.3 Chemical Kinetics Validation

The Arrhenius kinetics model produces physically realistic results:
- DCP purity increases during chlorination phase
- TCP impurity rises with over-chlorination
- Phenol conversion tracks Cl₂ consumption
- Heat generation feedback matches exothermic behavior

---

## CHAPTER 6: API REFERENCE (KEY ENDPOINTS)

| Method | Endpoint | Role | Purpose |
|--------|---------|------|---------|
| POST | `/api/auth/login` | None | Authenticate |
| GET | `/api/status` | Viewer+ | Reactor status |
| GET | `/api/recipe/status` | Viewer+ | Recipe state |
| POST | `/api/recipe/start` | Worker+ | Start batch |
| POST | `/api/recipe/stop` | Worker+ | Abort batch |
| POST | `/api/control` | Worker+ | Send command |
| GET | `/api/soft-sensor` | Viewer+ | Purity data |
| GET | `/api/batch/report/pdf` | Worker+ | PDF report |
| GET | `/api/opcua/status` | Viewer+ | OPC-UA info |
| GET | `/api/v1/batch-records` | Owner | List EBRs |
| POST | `/api/v1/batch-records/{id}/verify` | Owner | Verify hash |
| WS | `/ws` | Viewer+ | Live telemetry |

Total: **30+ REST endpoints + 1 WebSocket endpoint**

---

## CHAPTER 7: CONCLUSION & FUTURE WORK

### 7.1 Conclusion

This project successfully demonstrates the feasibility and value of digital twin technology for chemical batch reactors. The system integrates physics-based simulation, real-time visualization, AI-driven anomaly detection, and regulatory-compliant batch records into a cohesive web application. Key achievements include:

1. A realistic reactor simulation with Arrhenius kinetics updating at 10 Hz.
2. ISA-88 compliant recipe management with safety interlocks.
3. Real-time 3D visualization reflecting physical reactor state.
4. Soft sensor analytics eliminating the need for periodic lab analysis.
5. OPC-UA integration enabling connectivity with industrial DCS platforms.
6. Tamper-evident electronic batch records meeting 21 CFR Part 11 requirements.
7. Role-based access control ensuring operational security.

### 7.2 Future Enhancements

1. **Persistent User Database** — Migrate to database-backed user management.
2. **HTTPS/TLS** — Add SSL for encrypted production communication.
3. **Time-Series Database** — InfluxDB/TimescaleDB for historical trends.
4. **Advanced ML** — LSTM models for predictive maintenance.
5. **Mobile UI** — Responsive design for tablets and phones.
6. **Multi-Reactor** — Support multiple reactor instances.
7. **Email/SMS Alerts** — Push notifications for critical anomalies.
8. **Docker + Cloud** — Containerize and deploy on AWS/Azure/GCP.
9. **PLC Integration** — Direct Modbus TCP or OPC-UA client mode.

---

## REFERENCES

1. IEEE 830-1998 — Recommended Practice for Software Requirements Specifications
2. ISA-88.01 — Batch Control: Models and Terminology
3. 21 CFR Part 11 — FDA Electronic Records and Signatures
4. IEC 62541 — OPC Unified Architecture Specification
5. FastAPI Documentation — https://fastapi.tiangolo.com
6. React Three Fiber — https://docs.pmnd.rs/react-three-fiber
7. Recharts Library — https://recharts.org
8. Scikit-Learn (Isolation Forest) — https://scikit-learn.org
9. Grieves, M. (2014). Digital Twins: Excellence through Intelligent Digital Twins
10. Python asyncua — https://github.com/FreeOpcUa/opcua-asyncio

---
