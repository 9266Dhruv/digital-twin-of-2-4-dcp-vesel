"""
Advanced Reactor Simulator for 2,6-Dichlorophenol Digital Twin
With integrated Recipe Management, State Machine, PID Control, and Data Logging
Upgraded with Arrhenius kinetics, soft sensor, and ISA-88 batch records.
"""

import math
import random
import uuid
from collections import deque
from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal, Log, TelemetryHistory
from .controls import PIDController
from .recipe_engine import RecipeEngine, RecipeState, ControlLogic
from .data_logger import data_logger
from .kinetics import ChlorinationKinetics
from .soft_sensor import DCPSoftSensor
from .batch_record import BatchRecordManager


class GodModeReactor:
    """
    Complete Digital Twin Reactor Simulator
    
    Features:
    - Physics-based simulation with chemical kinetics
    - Advanced recipe management with 7 sequential steps
    - Safety interlocks and state machine logic
    - PID temperature control with auto-tuning
    - Data logging every 10 seconds with CSV export
    - Fault injection for testing
    """
    
    def __init__(self):
        # Chemical State (Molar concentrations)
        self.conc_phenol = 10.0       # Starting phenol concentration
        self.conc_cl2 = 0.0           # Chlorine concentration
        self.conc_dcp = 0.0           # 2,6-Dichlorophenol product
        self.conc_hcl = 0.0           # HCl byproduct
        self.conc_2cp = 0.0           # 2-Chlorophenol intermediate
        self.conc_tcp = 0.0           # 2,4,6-Trichlorophenol byproduct
        self.initial_conc_phenol = self.conc_phenol
        self.initial_phenol_g = 1000  # 1.0 kg phenol (lab scale)
        
        # Reaction parameters
        self.reaction_temp_c = 75.0   # Target reaction temperature
        self.cl2_flow_lph = 20.0      # Chlorine flow rate L/h
        self.reactor_volume_L = 10.0  # Reactor liquid volume in liters
        
        # Physics State
        self.temp = 25.0              # Current temperature (°C)
        self.pressure = 1.0           # Current pressure (bar)
        self.purity = 100.0           # Purity estimate (%)
        
        # Hardware/Actuator State
        self.agitator_rpm = 100.0
        self.cl2_valve = 0.0          # Chlorine valve position (%)
        self.cooling_valve = 50.0     # Cooling valve position (%)
        self.heating_power = 0.0      # Heating power (%)
        self.discharge_valve = 0.0    # Product discharge valve (%)
        
        # Sensor/Diagnostic
        self.vibration = 0.5
        self.bearing_wear = 0.0
        
        # Safety/Interlock State
        self.interlock_active = False
        self.interlock_msg = ""
        self.safety_scram = False
        
        # Fault Injection
        self.faults = {
            "cooling_failure": False,
            "sensor_drift": False,
            "valve_stuck": False
        }
        
        # Financial tracking
        self.batch_value = 0.0
        
        # Worker Safety (Biometrics)
        self.worker_heart_rate = 75.0
        self.dead_man_triggered = False
        
        # Control Systems
        self.pid_temp = PIDController(kp=2.0, ki=0.1, kd=0.5)
        self.recipe = RecipeEngine()
        self.optimization_mode = "QUALITY"  # QUALITY or SPEED
        
        # ───── Advanced Chemistry Engine ─────
        self.kinetics = ChlorinationKinetics()
        self.soft_sensor = DCPSoftSensor(self.kinetics)
        self.soft_sensor.initialize(self.conc_phenol)  # mol/L initial phenol
        self._soft_sensor_data = {}  # cached latest soft sensor output
        
        # ───── Batch Record Manager ─────
        self.batch_record_mgr = BatchRecordManager()
        self.batch_id = ""
        
        # Manual override tracking — when user sends manual command,
        # protect that actuator from PID/auto overrides for OVERRIDE_COOLDOWN ticks
        self.OVERRIDE_COOLDOWN = 50   # 50 ticks × 0.1s = 5 seconds
        self.manual_override = {
            "heating_power": 0,
            "cooling_valve": 0,
            "cl2_valve": 0,
            "agitator_rpm": 0,
            "discharge_valve": 0,
        }
        
        # Timing
        self.tick_count = 0
        self.golden_batch_profile = [40 + 20 * math.sin(i / 10) for i in range(3600)]
        
        # Audit/Event Log
        self.audit_log = deque(maxlen=100)
        self.last_recipe_status = None
        self.last_deadman_state = False
        self._last_recipe_state = RecipeState.IDLE
        
        # Data logging (batch tracking)
        self.batch_active = False
    
    # =====================
    # INTERLOCK/SAFETY LOGIC
    # =====================
    
    def check_interlocks(self, cmd_type: str, value: float) -> tuple:
        """
        Safety Interlock Checks
        
        Rules:
        - Cannot open discharge valve if pressure > 1.2 bar or temp > 60°C
        - Cannot open Cl2 valve if agitator RPM < 50
        - Cannot start chlorination if temp not at 75°C ± 2°C
        
        Returns: (allowed: bool, reason: str)
        """
        # Discharge valve interlocks
        if cmd_type == "discharge_valve" and value > 0:
            if self.pressure > 1.2:
                return False, "SAFETY INTERLOCK: Pressure > 1.2 bar - Cannot discharge"
            if self.temp > 60:
                return False, "SAFETY INTERLOCK: Temp > 60°C - Wait for cooling"
        
        # Chlorine valve interlocks
        if cmd_type == "cl2_valve" and value > 0:
            if self.agitator_rpm < 50:
                return False, "PROCESS INTERLOCK: Agitator RPM too low for Cl2 injection"
            # Temperature requirement for chlorination
            if abs(self.temp - 75.0) > 5.0:
                return False, f"PROCESS INTERLOCK: Temp {self.temp:.1f}°C not near 75°C for chlorination"
        
        return True, "OK"
    
    def scram_shutdown(self):
        """Emergency shutdown procedure"""
        self.cl2_valve = 0
        self.heating_power = 0
        self.cooling_valve = 100
        self.recipe.abort()
        self.safety_scram = True
        self.log_event("CRITICAL", "SCRAM shutdown engaged - Emergency stop")
    
    # =====================
    # LOGGING
    # =====================
    
    def log_event(self, level: str, message: str, meta: dict = None):
        """Log event to audit trail and database"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "meta": meta or {}
        }
        self.audit_log.appendleft(entry)
        
        # Also log to data logger
        data_logger.log_event(level, message, meta)
        
        # Persist to database
        try:
            db: Session = SessionLocal()
            db_log = Log(
                timestamp=datetime.now(),
                level=level,
                message=message,
                meta_data=meta or {}
            )
            db.add(db_log)
            db.commit()
        except Exception as e:
            pass
        finally:
            try:
                db.close()
            except:
                pass
    
    def get_audit_log(self) -> list:
        """Get recent audit log entries"""
        return list(self.audit_log)
    
    # =====================
    # SIMULATION UPDATE LOOP
    # =====================
    
    def update(self, dt: float = 0.1):
        """
        Main simulation update loop
        Called every dt seconds (typically 0.1s = 100ms)
        """
        self.tick_count += 1
        
        # 1. UPDATE RECIPE STATE MACHINE
        recipe_target = self.recipe.update(
            current_temp=self.temp,
            pressure=self.pressure,
            agitator_rpm=self.agitator_rpm
        )
        
        # Track recipe status changes
        current_status = self.recipe.get_status()
        if current_status != self.last_recipe_status:
            self.log_event("INFO", f"Recipe status: {current_status}")
            self.last_recipe_status = current_status
            
            # Auto-start batch logging when recipe starts
            if self.recipe.state not in [RecipeState.IDLE, RecipeState.COMPLETE, RecipeState.ABORTED]:
                if not self.batch_active:
                    data_logger.start_batch()
                    self.batch_active = True
            
            # Auto-end batch logging when recipe completes
            if self.recipe.state in [RecipeState.COMPLETE, RecipeState.ABORTED]:
                if self.batch_active:
                    data_logger.end_batch()
                    self.batch_active = False
        
        # Decrement manual override cooldowns
        for key in self.manual_override:
            if self.manual_override[key] > 0:
                self.manual_override[key] -= 1
        
        # 2. DETERMINE TARGET TEMPERATURE
        if recipe_target:
            target_temp = recipe_target.get('target_temp', self.reaction_temp_c)
            
            # Apply auto-actions from recipe (only if NOT manually overridden)
            auto_actions = recipe_target.get('auto_actions', {})
            if 'heating_power' in auto_actions and self.manual_override['heating_power'] == 0:
                self.heating_power = auto_actions['heating_power']
            if 'cl2_valve' in auto_actions and not self.faults['valve_stuck'] and self.manual_override['cl2_valve'] == 0:
                # Only auto-set Cl2 valve if interlock allows
                ok, msg = self.check_interlocks('cl2_valve', auto_actions['cl2_valve'])
                if ok:
                    self.cl2_valve = auto_actions['cl2_valve']
                else:
                    self.interlock_msg = msg
        else:
            target_temp = self.reaction_temp_c
        
        # 3. DEAD-MAN SWITCH / WORKER SAFETY
        if self.worker_heart_rate > 150 and not self.dead_man_triggered:
            self.dead_man_triggered = True
            self.log_event("CRITICAL", "Dead-man switch triggered", 
                          {"worker_heart_rate": self.worker_heart_rate})
            self.scram_shutdown()
            return
        
        if self.dead_man_triggered:
            # Keep in safe state during scram
            self.cl2_valve = 0
            self.agitator_rpm = 0
            self.heating_power = 0
            self.temp -= 0.5 * dt
            return
        
        # 4. PID TEMPERATURE CONTROL
        if self.optimization_mode == "SPEED":
            self.pid_temp.kp = 5.0  # More aggressive
        else:
            self.pid_temp.kp = 2.0  # Normal
        
        control_output = self.pid_temp.update(self.temp, target_temp, dt)
        
        # Basic control logic: adjust heating/cooling based on PID output
        # ONLY if those actuators are NOT under manual override
        if control_output > 0:
            # Need heating
            if self.manual_override['heating_power'] == 0:
                self.heating_power = min(100, self.heating_power + control_output * 0.5)
            if self.manual_override['cooling_valve'] == 0:
                self.cooling_valve = max(20, self.cooling_valve - control_output * 0.3)
        else:
            # Need cooling
            if self.manual_override['heating_power'] == 0:
                self.heating_power = max(0, self.heating_power + control_output * 0.5)
            if self.manual_override['cooling_valve'] == 0:
                self.cooling_valve = min(100, self.cooling_valve - control_output * 0.3)
        
        # 5. CHEMICAL KINETICS — Arrhenius ODE via Soft Sensor
        mixing_efficiency = min(1.0, self.agitator_rpm / 300.0)
        
        # Convert Cl2 feed: valve position + flow rate → mol/min
        cl2_mol_per_min = 0.0
        if self.cl2_valve > 0:
            # cl2_flow_lph in L/h → L/min, then ideal gas ~ 0.0446 mol/L at STP
            cl2_L_per_min = (self.cl2_flow_lph / 60.0) * (self.cl2_valve / 100.0)
            cl2_mol_per_min = cl2_L_per_min * 0.0446
        
        # Run soft sensor ODE integration
        self._soft_sensor_data = self.soft_sensor.update(
            dt_seconds=dt,
            T_celsius=self.temp,
            cl2_feed_rate_mol_per_min=cl2_mol_per_min,
            volume_L=self.reactor_volume_L,
            mixing_efficiency=mixing_efficiency,
        )
        
        # Sync legacy concentration fields from soft sensor state
        sc = self.soft_sensor.concentrations
        self.conc_phenol = sc["phenol"]
        self.conc_cl2 = sc["cl2_dissolved"]
        self.conc_2cp = sc["monochlorophenol"]
        self.conc_dcp = sc["dcp_2_4"]
        self.conc_tcp = sc["tcp_2_4_6"]
        self.conc_hcl += (self.soft_sensor.last_rates[0]
                         + self.soft_sensor.last_rates[1]
                         + self.soft_sensor.last_rates[2]) * (dt / 60.0)
        
        # 6. THERMAL DYNAMICS — energy balance with Arrhenius heat generation
        heat_gen_W = self._soft_sensor_data.get("heat_generation_W", 0.0)
        # Convert Watts to °C/s: Q / (m * Cp), assume water-like ~4184 J/kg/°C, ~10 kg
        heat_gen_dT = heat_gen_W / (self.reactor_volume_L * 4184.0)
        
        # Heating contribution
        heating_power_effect = (self.heating_power / 100.0) * 15.0  # Max 15°C/s
        
        # Cooling contribution (affected by faults)
        effective_cooling = self.cooling_valve
        if self.faults['cooling_failure']:
            effective_cooling = 0  # Cooling system failed
        
        cooling_power_effect = (effective_cooling / 100.0) * 10.0  # Max 10°C/s
        
        # Temperature change
        self.temp += (heat_gen_dT + heating_power_effect - cooling_power_effect) * dt
        
        # Clamp temperature to reasonable bounds
        self.temp = max(15.0, min(120.0, self.temp))
        
        # 7. CHLORINE FEED (now handled inside soft sensor ODE)
        # Legacy field kept for backward compat
        
        # 8. DISCHARGE (product removal)
        if self.discharge_valve > 0:
            drain_frac = (self.discharge_valve / 100.0) * 0.5 * dt
            self.conc_dcp -= drain_frac
            self.conc_dcp = max(0, self.conc_dcp)
            # Also drain from soft sensor state
            self.soft_sensor.concentrations["dcp_2_4"] = max(0.0, self.soft_sensor.concentrations["dcp_2_4"] - drain_frac)
        
        # 9. PRESSURE CALCULATION
        # Pressure increases with HCl and temperature
        self.pressure = 1.0 + (self.conc_hcl * 0.05) + ((self.temp - 40) * 0.01)
        
        # Apply sensor drift fault
        if self.faults['sensor_drift']:
            self.pressure += math.sin(self.tick_count / 10.0) * 0.2
        
        # 10. EQUIPMENT WEAR / VIBRATION
        self.bearing_wear += 0.0001 * dt
        self.vibration = 0.5 + (self.bearing_wear * 5.0) + random.gauss(0, 0.1)
        
        # 11. PURITY — from soft sensor (replaces hardcoded)
        self.purity = self._soft_sensor_data.get("dcp_purity", 0.0)
        
        # 12. FINANCIAL VALUE — net batch profit
        # Revenue: DCP produced (mol/L × volume × MW × price/g)
        #   DCP MW = 163 g/mol, market ~$4.50/g for lab-grade 2,4-DCP
        dcp_mass_g = self.conc_dcp * self.reactor_volume_L * 163.0
        dcp_revenue = dcp_mass_g * 4.50
        # Cost: phenol consumed (initial - remaining) × MW × cost/g
        #   Phenol MW = 94.11 g/mol, cost ~$0.15/g industrial
        phenol_consumed_mol = max(0, self.initial_conc_phenol - self.conc_phenol)
        phenol_cost = phenol_consumed_mol * self.reactor_volume_L * 94.11 * 0.15
        # Cl2 cost: consumed Cl2 is roughly stoichiometric
        cl2_cost = phenol_consumed_mol * 2 * self.reactor_volume_L * 70.9 * 0.05
        # TCP waste penalty (disposal + lost selectivity)
        tcp_mass_g = self.conc_tcp * self.reactor_volume_L * 197.45
        tcp_penalty = tcp_mass_g * 2.0
        # Net batch value
        self.batch_value = dcp_revenue - phenol_cost - cl2_cost - tcp_penalty
        
        # 12b. BATCH RECORD — sample PVs periodically (every ~1 second)
        if self.tick_count % 10 == 0 and self.batch_record_mgr.current_record:
            self.batch_record_mgr.record_pv_sample(
                temperature=self.temp,
                pressure=self.pressure,
                dcp_purity=self.purity,
                tcp_impurity=self._soft_sensor_data.get("tcp_impurity", 0.0),
                target_temp=self.reaction_temp_c,
            )
        
        # 12c. BATCH RECORD — detect recipe phase transitions
        current_recipe_state = self.recipe.state
        if current_recipe_state != self._last_recipe_state:
            self._handle_phase_transition(self._last_recipe_state, current_recipe_state)
            self._last_recipe_state = current_recipe_state
        
        # 13. DATA LOGGING (every 10 seconds)
        telemetry = self.get_telemetry()
        data_logger.log_telemetry(telemetry)
    
    # =====================
    # COMMAND HANDLING
    # =====================
    
    def set_command(self, cmd: dict):
        """Process incoming control commands"""
        
        # Recipe commands
        if cmd.get('START_BATCH') or cmd.get('START_RECIPE') or cmd.get('RECIPE_CMD') == "START":
            self.recipe.start()
            self.log_event("INFO", "Recipe started (batch)")
        
        if cmd.get('RECIPE_CMD') == "STOP":
            self.recipe.abort()
            self.log_event("WARNING", "Recipe aborted by operator")
        
        if cmd.get('RECIPE_CMD') == "RESET":
            self.recipe.reset()
            # Reset reactor state for new batch
            self.conc_phenol = 10.0 * (self.initial_phenol_g / 1000.0)
            self.conc_cl2 = 0.0
            self.conc_dcp = 0.0
            self.conc_hcl = 0.0
            self.conc_2cp = 0.0
            self.conc_tcp = 0.0
            self.temp = 25.0
            self.pressure = 1.0
            # Reset soft sensor
            self.soft_sensor.initialize(self.conc_phenol)
            self._soft_sensor_data = {}
            self.log_event("INFO", "Recipe reset - Reactor ready for new batch")
        
        # Chlorine valve
        if 'cl2_valve' in cmd:
            value = float(cmd['cl2_valve'])
            ok, msg = self.check_interlocks("cl2_valve", value)
            if ok and not self.faults['valve_stuck']:
                self.cl2_valve = value
                self.manual_override['cl2_valve'] = self.OVERRIDE_COOLDOWN
                data_logger.log_control_action("cl2_valve", value)
            else:
                self.interlock_msg = msg
            self.log_event("INFO", f"Cl2 valve set to {self.cl2_valve}%")
        
        # Agitator RPM
        if 'agitator_rpm' in cmd:
            self.agitator_rpm = float(cmd['agitator_rpm'])
            self.manual_override['agitator_rpm'] = self.OVERRIDE_COOLDOWN
            data_logger.log_control_action("agitator_rpm", self.agitator_rpm)
            self.log_event("INFO", f"Agitator RPM set to {self.agitator_rpm}")
        
        # Cooling valve
        if 'cooling_valve' in cmd:
            self.cooling_valve = float(cmd['cooling_valve'])
            self.manual_override['cooling_valve'] = self.OVERRIDE_COOLDOWN
            data_logger.log_control_action("cooling_valve", self.cooling_valve)
            self.log_event("INFO", f"Cooling valve set to {self.cooling_valve}%")
        
        # Discharge valve (interlocked)
        if 'discharge_valve' in cmd:
            value = float(cmd['discharge_valve'])
            ok, msg = self.check_interlocks("discharge_valve", value)
            if ok:
                self.discharge_valve = value
                self.manual_override['discharge_valve'] = self.OVERRIDE_COOLDOWN
                data_logger.log_control_action("discharge_valve", value)
            else:
                self.interlock_msg = msg
            self.log_event("INFO", f"Discharge valve set to {self.discharge_valve}%")
        
        # Worker biometrics
        if 'worker_heart_rate' in cmd:
            self.worker_heart_rate = float(cmd['worker_heart_rate'])
        
        # Safety reset
        if 'reset_safety' in cmd:
            self.dead_man_triggered = False
            self.safety_scram = False
            self.interlock_msg = ""
            self.log_event("WARNING", "Safety reset by operator")
        
        # Optimization mode
        if 'optimize_mode' in cmd:
            self.optimization_mode = cmd['optimize_mode']
            self.log_event("INFO", f"Optimization mode: {self.optimization_mode}")
        
        # Heating power (manual override)
        if 'heating_power' in cmd:
            self.heating_power = float(cmd['heating_power'])
            self.manual_override['heating_power'] = self.OVERRIDE_COOLDOWN
            data_logger.log_control_action("heating_power", self.heating_power)
            self.log_event("INFO", f"Heating power set to {self.heating_power}%")
        
        # Batch size
        if 'initial_phenol_g' in cmd:
            self.initial_phenol_g = float(cmd['initial_phenol_g'])
            scale = max(0.1, self.initial_phenol_g / 1000.0)
            self.conc_phenol = 10.0 * scale
            self.initial_conc_phenol = self.conc_phenol
            self.conc_dcp = 0.0
            self.conc_cl2 = 0.0
            self.conc_hcl = 0.0
            self.log_event("INFO", f"Batch size set to {self.initial_phenol_g}g phenol")
        
        # Reaction temperature setpoint
        if 'reaction_temp_c' in cmd:
            self.reaction_temp_c = float(cmd['reaction_temp_c'])
            self.log_event("INFO", f"Reaction temp setpoint: {self.reaction_temp_c}°C")
        
        # Chlorine flow rate
        if 'cl2_flow_lph' in cmd:
            self.cl2_flow_lph = float(cmd['cl2_flow_lph'])
            self.log_event("INFO", f"Cl2 flow rate: {self.cl2_flow_lph} L/h")
        
        # Fault injection
        if 'toggle_fault' in cmd:
            fault_name = cmd['toggle_fault']
            if fault_name in self.faults:
                self.faults[fault_name] = not self.faults[fault_name]
                status = "ACTIVE" if self.faults[fault_name] else "CLEARED"
                self.log_event("WARNING", f"Fault {fault_name}: {status}")
        
        # PID tuning
        if 'pid_tune' in cmd:
            params = cmd['pid_tune']
            if 'kp' in params:
                self.pid_temp.kp = float(params['kp'])
            if 'ki' in params:
                self.pid_temp.ki = float(params['ki'])
            if 'kd' in params:
                self.pid_temp.kd = float(params['kd'])
            self.log_event("INFO", "PID parameters updated", 
                          {"kp": self.pid_temp.kp, "ki": self.pid_temp.ki, "kd": self.pid_temp.kd})
        
        # Generate batch report
        if 'generate_report' in cmd:
            report_path = data_logger.generate_csv_report()
            self.log_event("INFO", f"Batch report generated: {report_path}")
    
    # =====================
    # AI/ANALYSIS
    # =====================
    
    def get_ai_analysis(self) -> list:
        """Generate AI analysis alerts"""
        alerts = []
        
        # Blockage detection
        if self.pressure > 1.5 and self.temp < 42 and self.cl2_valve > 0:
            alerts.append({"type": "critical", "msg": "BLOCKAGE: P↑ T↓ Divergence detected"})
        
        # Temperature warning
        if self.temp > 78:
            alerts.append({"type": "warning", "msg": f"PURITY RISK: Temp {self.temp:.1f}°C > 78°C"})
        
        # Bearing wear prediction
        if self.vibration > 2.0:
            alerts.append({"type": "maintenance", "msg": "BEARING FAIL: < 48h RUL estimated"})
        
        # Cooling failure detection
        if self.faults['cooling_failure'] and self.temp > 50:
            alerts.append({"type": "critical", "msg": "COOLING FAILURE: Manual intervention required"})
        
        # Interlock active
        if self.recipe.interlock.active:
            alerts.append({"type": "warning", "msg": f"INTERLOCK: {self.recipe.interlock.reason}"})
        
        # TCP over-chlorination warning (from soft sensor)
        tcp_impurity = self._soft_sensor_data.get("tcp_impurity", 0.0)
        if tcp_impurity > 5.0:
            alerts.append({"type": "warning", "msg": f"High TCP formation ({tcp_impurity:.1f}%) - reduce Cl2 feed rate"})
        
        return alerts
    
    # =====================
    # TELEMETRY OUTPUT
    # =====================
    
    def get_telemetry(self) -> dict:
        """Get current telemetry data for dashboard"""
        idx = self.tick_count % 3600
        golden_temp = self.golden_batch_profile[idx]
        
        # Get detailed recipe status
        recipe_detail = self.recipe.get_detailed_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            
            # Core process values
            "temp": round(self.temp, 2),
            "pressure": round(self.pressure, 2),
            "purity": round(self.purity, 1),
            
            # Chemical state
            "moles_dcp": round(self.conc_dcp, 3),
            "moles_cl2": round(self.conc_cl2, 3),
            "moles_phenol": round(self.conc_phenol, 3),
            
            # Batch parameters
            "initial_phenol_g": self.initial_phenol_g,
            "reaction_temp_c": self.reaction_temp_c,
            "cl2_flow_lph": self.cl2_flow_lph,
            
            # Financial
            "financial_value": round(self.batch_value, 2),
            
            # Safety
            "worker_heart_rate": self.worker_heart_rate,
            "safety_scram": self.dead_man_triggered,
            
            # Control reference
            "golden_temp": round(golden_temp, 2),
            "optimization_mode": self.optimization_mode,
            
            # Interlocks
            "interlock_active": self.recipe.interlock.active,
            "interlock_msg": self.interlock_msg or self.recipe.interlock.reason,
            
            # Fault status
            "faults": self.faults,
            
            # PID state
            "pid_state": self.pid_temp.get_terms(),
            
            # Actuator positions
            "inputs": {
                "cl2": round(self.cl2_valve, 1),
                "rpm": round(self.agitator_rpm, 0),
                "cooling": round(self.cooling_valve, 1),
                "discharge": round(self.discharge_valve, 1),
                "heating": round(self.heating_power, 1)
            },
            
            # AI analysis
            "ai_analysis": self.get_ai_analysis(),
            
            # Recipe status
            "recipe_status": self.recipe.get_status(),
            "recipe_detail": recipe_detail,
            "recipe_step_index": recipe_detail.get("current_step_index", 0),
            "recipe_step_name": recipe_detail.get("current_step_name", "N/A"),
            
            # Data logging status
            "batch_logging_active": self.batch_active,
            "data_log_count": len(data_logger.telemetry_buffer),
            
            # ─── Soft Sensor & Advanced Chemistry ───
            "soft_sensor": self._soft_sensor_data,
            "batch_id": self.batch_id,
            "conc_2cp": round(self.conc_2cp, 6),
            "conc_tcp": round(self.conc_tcp, 6),
        }
    
    def _handle_phase_transition(self, old_state: RecipeState, new_state: RecipeState):
        """Handle recipe state transitions for batch record management."""
        # Batch START — create new EBR
        if old_state == RecipeState.IDLE and new_state != RecipeState.IDLE:
            self.batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
            self.batch_record_mgr.start_batch(
                batch_id=self.batch_id,
                operator_id="system",
                phenol_kg=self.initial_phenol_g / 1000.0,
            )
            # Re-initialize soft sensor for new batch
            self.soft_sensor.initialize(self.conc_phenol)
            self.log_event("INFO", f"Batch Record started: {self.batch_id}")

        # Phase transition — record phase change
        if new_state not in (RecipeState.IDLE, RecipeState.COMPLETE, RecipeState.ABORTED):
            step = self.recipe.get_current_step()
            if step:
                self.batch_record_mgr.start_phase(
                    phase_name=step.name,
                    parameters={
                        "target_temp": step.target_temp,
                        "duration_seconds": step.duration_seconds,
                        "cl2_required": step.cl2_flow_required,
                        "min_agitator_rpm": step.min_agitator_rpm,
                    },
                )

        # Batch COMPLETE or ABORTED — finalize EBR
        if new_state in (RecipeState.COMPLETE, RecipeState.ABORTED):
            ss = self._soft_sensor_data
            conc = self.soft_sensor.concentrations
            # MW: phenol=94.11, Cl2=70.9, DCP=163.0, TCP=197.45
            dcp_kg = conc.get("dcp_2_4", 0.0) * self.reactor_volume_L * 0.163
            tcp_kg = conc.get("tcp_2_4_6", 0.0) * self.reactor_volume_L * 0.19745
            cl2_consumed = max(0.0, self.initial_conc_phenol - conc.get("phenol", 0.0))
            cl2_kg = cl2_consumed * self.reactor_volume_L * 0.0709

            record = self.batch_record_mgr.finalize_batch(
                dcp_produced_kg=dcp_kg,
                cl2_consumed_kg=cl2_kg,
                tcp_waste_kg=tcp_kg,
                final_selectivity=ss.get("selectivity", 0.0),
            )
            if record:
                self.log_event("INFO", f"Batch Record finalized: {self.batch_id} (hash: {record.record_hash[:12]}...)")

    def run_projection(self, hours: int = 1) -> list:
        """Run forward projection (placeholder)"""
        return [{"time": f"+{i}m", "temp": 45} for i in range(60)]
