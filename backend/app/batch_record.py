"""
Electronic Batch Record (EBR) System
ISA-88 / 21 CFR Part 11 compliant batch records for DCP production.

Features:
- Per-phase audit with parameters, actual PV values, and deviations
- Material balance tracking (phenol in, Cl2 consumed, DCP out, TCP waste)
- Quality summary (purity, selectivity, TCP impurity, temp excursions)
- SHA-256 hash-chaining for tamper evidence
- JSON and Markdown report export
"""

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any


@dataclass
class PhaseRecord:
    """Record for a single recipe phase (ISA-88 phase)."""
    phase_name: str
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    actual_values: Dict[str, Any] = field(default_factory=dict)  # min/max/avg
    deviations: List[str] = field(default_factory=list)
    operator_id: str = ""
    completed: bool = False


@dataclass
class ElectronicBatchRecord:
    """
    Complete electronic batch record for one DCP production batch.
    Conforms to ISA-88 batch record structure with 21 CFR Part 11
    tamper evidence via SHA-256 hash chaining.
    """
    batch_id: str = ""
    product: str = "2,4-Dichlorophenol"
    cas_number: str = "120-83-2"
    vessel_id: str = "R-101"
    batch_start: str = ""
    batch_end: str = ""
    operator_id: str = ""
    phases: List[PhaseRecord] = field(default_factory=list)
    material_balance: Dict[str, float] = field(default_factory=lambda: {
        "phenol_charged_kg": 0.0,
        "cl2_consumed_kg": 0.0,
        "dcp_produced_kg": 0.0,
        "yield_pct": 0.0,
        "tcp_waste_kg": 0.0,
    })
    quality_summary: Dict[str, float] = field(default_factory=lambda: {
        "avg_purity": 0.0,
        "min_purity": 100.0,
        "max_tcp_impurity": 0.0,
        "final_selectivity": 0.0,
        "temp_excursions_count": 0,
    })
    alarm_summary: List[Dict[str, Any]] = field(default_factory=list)
    scram_events: List[Dict[str, Any]] = field(default_factory=list)
    record_hash: str = ""
    previous_hash: str = ""

    def finalize(self, previous_hash: str = "0" * 64) -> "ElectronicBatchRecord":
        """
        Hash-chain this record for tamper evidence.
        
        Args:
            previous_hash: SHA-256 hash of the previous batch record

        Returns:
            self (for chaining)
        """
        self.previous_hash = previous_hash
        # Temporarily clear record_hash for consistent hashing
        self.record_hash = ""
        content = json.dumps(asdict(self), sort_keys=True, default=str)
        self.record_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return self

    def verify_integrity(self) -> bool:
        """Verify this record's hash has not been tampered with."""
        stored_hash = self.record_hash
        self.record_hash = ""
        content = json.dumps(asdict(self), sort_keys=True, default=str)
        computed = hashlib.sha256(content.encode("utf-8")).hexdigest()
        self.record_hash = stored_hash
        return computed == stored_hash

    def to_json_export(self) -> str:
        """Export complete record as formatted JSON string."""
        return json.dumps(asdict(self), indent=2, default=str)

    def to_markdown_report(self) -> str:
        """Generate human-readable markdown batch report."""
        lines = []
        lines.append(f"# Electronic Batch Record — {self.batch_id}")
        lines.append("")
        lines.append(f"| Field | Value |")
        lines.append(f"|-------|-------|")
        lines.append(f"| **Product** | {self.product} |")
        lines.append(f"| **CAS Number** | {self.cas_number} |")
        lines.append(f"| **Vessel** | {self.vessel_id} |")
        lines.append(f"| **Batch Start** | {self.batch_start} |")
        lines.append(f"| **Batch End** | {self.batch_end} |")
        lines.append(f"| **Operator** | {self.operator_id} |")
        lines.append("")

        # Phases
        lines.append("## Phase Execution")
        lines.append("")
        lines.append("| # | Phase | Duration (s) | Completed | Deviations |")
        lines.append("|---|-------|-------------|-----------|------------|")
        for i, phase in enumerate(self.phases, 1):
            dev_count = len(phase.deviations) if isinstance(phase, PhaseRecord) else len(phase.get("deviations", []))
            name = phase.phase_name if isinstance(phase, PhaseRecord) else phase.get("phase_name", "?")
            dur = phase.duration_seconds if isinstance(phase, PhaseRecord) else phase.get("duration_seconds", 0)
            comp = phase.completed if isinstance(phase, PhaseRecord) else phase.get("completed", False)
            lines.append(f"| {i} | {name} | {dur:.1f} | {'✅' if comp else '❌'} | {dev_count} |")
        lines.append("")

        # Material Balance
        mb = self.material_balance
        lines.append("## Material Balance")
        lines.append("")
        lines.append("| Material | Amount |")
        lines.append("|----------|--------|")
        lines.append(f"| Phenol Charged | {mb.get('phenol_charged_kg', 0):.3f} kg |")
        lines.append(f"| Cl₂ Consumed | {mb.get('cl2_consumed_kg', 0):.3f} kg |")
        lines.append(f"| DCP Produced | {mb.get('dcp_produced_kg', 0):.3f} kg |")
        lines.append(f"| TCP Waste | {mb.get('tcp_waste_kg', 0):.3f} kg |")
        lines.append(f"| **Yield** | **{mb.get('yield_pct', 0):.1f}%** |")
        lines.append("")

        # Quality Summary
        qs = self.quality_summary
        lines.append("## Quality Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Average Purity | {qs.get('avg_purity', 0):.1f}% |")
        lines.append(f"| Minimum Purity | {qs.get('min_purity', 0):.1f}% |")
        lines.append(f"| Max TCP Impurity | {qs.get('max_tcp_impurity', 0):.2f}% |")
        lines.append(f"| Final Selectivity | {qs.get('final_selectivity', 0):.4f} |")
        lines.append(f"| Temp Excursions | {qs.get('temp_excursions_count', 0)} |")
        lines.append("")

        # Alarms
        lines.append(f"## Alarm Summary ({len(self.alarm_summary)} events)")
        lines.append("")
        if self.alarm_summary:
            lines.append("| Time | Level | Message |")
            lines.append("|------|-------|---------|")
            for alarm in self.alarm_summary[:20]:
                lines.append(
                    f"| {alarm.get('timestamp', '?')} | {alarm.get('level', '?')} | {alarm.get('message', '?')} |"
                )
        else:
            lines.append("No alarms recorded.")
        lines.append("")

        # SCRAM Events
        if self.scram_events:
            lines.append(f"## SCRAM Events ({len(self.scram_events)})")
            lines.append("")
            for ev in self.scram_events:
                lines.append(f"- **{ev.get('timestamp', '?')}** — Trigger: {ev.get('trigger', '?')}")
            lines.append("")

        # Hash Verification
        lines.append("---")
        lines.append("## Record Integrity")
        lines.append(f"- **Record Hash (SHA-256):** `{self.record_hash}`")
        lines.append(f"- **Previous Record Hash:** `{self.previous_hash}`")
        integrity = "✅ VERIFIED" if self.verify_integrity() else "❌ TAMPERED"
        lines.append(f"- **Integrity Status:** {integrity}")
        lines.append("")

        return "\n".join(lines)


class BatchRecordManager:
    """
    Manager for creating, tracking, and persisting Electronic Batch Records.
    """

    def __init__(self, storage_dir: str = "data/batch_records"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

        self.current_record: Optional[ElectronicBatchRecord] = None
        self.current_phase: Optional[PhaseRecord] = None
        self._phase_pv_buffer: Dict[str, List[float]] = {}  # for min/max/avg
        self._purity_samples: List[float] = []
        self._tcp_max: float = 0.0
        self._temp_excursions: int = 0
        self._last_hash: str = self._load_last_hash()

    def _load_last_hash(self) -> str:
        """Load the hash of the most recent batch record for chaining."""
        hash_file = os.path.join(self.storage_dir, ".last_hash")
        if os.path.exists(hash_file):
            with open(hash_file, "r") as f:
                return f.read().strip()
        return "0" * 64

    def _save_last_hash(self, hash_val: str):
        """Save hash for chain continuity."""
        hash_file = os.path.join(self.storage_dir, ".last_hash")
        with open(hash_file, "w") as f:
            f.write(hash_val)

    def start_batch(self, batch_id: str, operator_id: str = "system",
                    phenol_kg: float = 1.0):
        """Start a new Electronic Batch Record."""
        self.current_record = ElectronicBatchRecord(
            batch_id=batch_id,
            batch_start=datetime.now().isoformat(),
            operator_id=operator_id,
        )
        self.current_record.material_balance["phenol_charged_kg"] = phenol_kg
        self._purity_samples = []
        self._tcp_max = 0.0
        self._temp_excursions = 0
        self.current_phase = None
        self._phase_pv_buffer = {}

    def start_phase(self, phase_name: str, parameters: Dict = None,
                    operator_id: str = ""):
        """Record the start of a new recipe phase."""
        if not self.current_record:
            return

        # Close previous phase if any
        self._close_current_phase()

        self.current_phase = PhaseRecord(
            phase_name=phase_name,
            start_time=datetime.now().isoformat(),
            parameters=parameters or {},
            operator_id=operator_id or self.current_record.operator_id,
        )
        self._phase_pv_buffer = {"temperature": [], "pressure": []}

    def record_pv_sample(self, temperature: float, pressure: float,
                         dcp_purity: float = 0.0, tcp_impurity: float = 0.0,
                         target_temp: float = 75.0):
        """
        Record a process variable sample during the current phase.
        Called periodically by the simulator.
        """
        if not self.current_phase:
            return

        self._phase_pv_buffer.setdefault("temperature", []).append(temperature)
        self._phase_pv_buffer.setdefault("pressure", []).append(pressure)

        # Track quality metrics
        if dcp_purity > 0:
            self._purity_samples.append(dcp_purity)
        if tcp_impurity > self._tcp_max:
            self._tcp_max = tcp_impurity

        # Track temperature excursions (> 3°C from setpoint)
        if abs(temperature - target_temp) > 3.0:
            self._temp_excursions += 1

    def record_deviation(self, message: str):
        """Record an out-of-spec deviation in the current phase."""
        if self.current_phase:
            self.current_phase.deviations.append(
                f"{datetime.now().isoformat()}: {message}"
            )

    def record_alarm(self, level: str, message: str):
        """Record an alarm event in the batch record."""
        if self.current_record:
            self.current_record.alarm_summary.append({
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
                "acknowledged": False,
            })

    def record_scram(self, trigger: str):
        """Record a SCRAM event."""
        if self.current_record:
            self.current_record.scram_events.append({
                "timestamp": datetime.now().isoformat(),
                "trigger": trigger,
                "operator_response_time_s": 0.0,
            })

    def _close_current_phase(self):
        """Finalize and store the current phase record."""
        if not self.current_phase or not self.current_record:
            return

        now = datetime.now().isoformat()
        self.current_phase.end_time = now

        # Calculate duration
        try:
            start = datetime.fromisoformat(self.current_phase.start_time)
            end = datetime.fromisoformat(now)
            self.current_phase.duration_seconds = (end - start).total_seconds()
        except (ValueError, TypeError):
            self.current_phase.duration_seconds = 0.0

        # Compute min/max/avg for PVs
        for pv_name, values in self._phase_pv_buffer.items():
            if values:
                self.current_phase.actual_values[pv_name] = {
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "avg": round(sum(values) / len(values), 2),
                }

        self.current_phase.completed = True
        self.current_record.phases.append(self.current_phase)
        self.current_phase = None
        self._phase_pv_buffer = {}

    def finalize_batch(
        self,
        dcp_produced_kg: float = 0.0,
        cl2_consumed_kg: float = 0.0,
        tcp_waste_kg: float = 0.0,
        final_selectivity: float = 0.0,
    ) -> Optional[ElectronicBatchRecord]:
        """
        Finalize the current batch record, compute quality summary,
        hash-chain, and persist to disk.

        Returns the finalized ElectronicBatchRecord or None.
        """
        if not self.current_record:
            return None

        # Close any open phase
        self._close_current_phase()

        self.current_record.batch_end = datetime.now().isoformat()

        # Material balance
        mb = self.current_record.material_balance
        mb["dcp_produced_kg"] = round(dcp_produced_kg, 4)
        mb["cl2_consumed_kg"] = round(cl2_consumed_kg, 4)
        mb["tcp_waste_kg"] = round(tcp_waste_kg, 4)
        phenol_kg = mb.get("phenol_charged_kg", 1.0)
        if phenol_kg > 0:
            # Theoretical yield: 1 mol phenol → 1 mol DCP
            # MW phenol=94.11, MW DCP=163.0
            theoretical_dcp = phenol_kg * (163.0 / 94.11)
            mb["yield_pct"] = round(
                (dcp_produced_kg / theoretical_dcp) * 100.0
                if theoretical_dcp > 0 else 0.0, 1
            )

        # Quality summary
        qs = self.current_record.quality_summary
        if self._purity_samples:
            qs["avg_purity"] = round(
                sum(self._purity_samples) / len(self._purity_samples), 1
            )
            qs["min_purity"] = round(min(self._purity_samples), 1)
        qs["max_tcp_impurity"] = round(self._tcp_max, 2)
        qs["final_selectivity"] = round(final_selectivity, 4)
        qs["temp_excursions_count"] = self._temp_excursions

        # Hash-chain and finalize
        self.current_record.finalize(self._last_hash)
        self._last_hash = self.current_record.record_hash
        self._save_last_hash(self._last_hash)

        # Persist to disk
        filename = f"{self.current_record.batch_id}.json"
        filepath = os.path.join(self.storage_dir, filename)
        with open(filepath, "w") as f:
            f.write(self.current_record.to_json_export())

        record = self.current_record
        self.current_record = None
        return record

    def list_records(self) -> List[Dict[str, Any]]:
        """List all stored batch records with metadata."""
        records = []
        if not os.path.exists(self.storage_dir):
            return records

        for filename in sorted(os.listdir(self.storage_dir)):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(self.storage_dir, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                records.append({
                    "batch_id": data.get("batch_id", filename),
                    "product": data.get("product", ""),
                    "batch_start": data.get("batch_start", ""),
                    "batch_end": data.get("batch_end", ""),
                    "phases_count": len(data.get("phases", [])),
                    "yield_pct": data.get("material_balance", {}).get("yield_pct", 0),
                    "record_hash": data.get("record_hash", ""),
                    "filename": filename,
                })
            except (json.JSONDecodeError, IOError):
                continue
        return records

    def get_record(self, batch_id: str) -> Optional[ElectronicBatchRecord]:
        """Load a batch record from disk by batch_id."""
        filepath = os.path.join(self.storage_dir, f"{batch_id}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            record = ElectronicBatchRecord(**{
                k: v for k, v in data.items()
                if k in ElectronicBatchRecord.__dataclass_fields__
            })
            # Reconstruct PhaseRecord objects
            record.phases = [
                PhaseRecord(**p) if isinstance(p, dict) else p
                for p in record.phases
            ]
            return record
        except (json.JSONDecodeError, IOError, TypeError):
            return None

    def get_record_json(self, batch_id: str) -> Optional[str]:
        """Get raw JSON of a batch record."""
        filepath = os.path.join(self.storage_dir, f"{batch_id}.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r") as f:
            return f.read()

    def verify_record(self, batch_id: str) -> Dict[str, Any]:
        """Verify hash integrity of a stored batch record."""
        record = self.get_record(batch_id)
        if not record:
            return {"batch_id": batch_id, "found": False, "verified": False}
        return {
            "batch_id": batch_id,
            "found": True,
            "verified": record.verify_integrity(),
            "record_hash": record.record_hash,
            "previous_hash": record.previous_hash,
        }
