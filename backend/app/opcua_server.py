"""
OPC-UA Server for DCP Digital Twin
Exposes reactor process variables as OPC-UA nodes for DCS integration.

Endpoint: opc.tcp://0.0.0.0:4840/dcp-twin/
Namespace: http://dcp-digital-twin/

Connects to any industrial DCS (Siemens PCS7, Honeywell Experion, ABB 800xA)
via standard OPC Unified Architecture protocol.
"""

import asyncio
import logging
from typing import Callable, Optional

logger = logging.getLogger("opcua_server")


class DCPTwinOPCUAServer:
    """
    OPC-UA server exposing DCP reactor twin state as browsable tags.

    Read-only PV nodes update every 1 second from the simulator.
    Writable SP nodes allow a DCS to push setpoints to the twin.
    """

    def __init__(self):
        self.server = None
        self.running = False
        self.get_state: Optional[Callable] = None
        self.on_setpoint_change: Optional[Callable] = None

        # OPC-UA node references (populated in setup)
        self._nodes = {}

    async def setup(self, twin_state_getter: Callable, setpoint_callback: Callable = None):
        """
        Initialize OPC-UA server and create all nodes.

        Args:
            twin_state_getter: Callable returning dict of current reactor state
            setpoint_callback: Callable to push setpoint changes back to simulator
        """
        try:
            from asyncua import Server, ua
        except ImportError:
            logger.warning(
                "asyncua not installed — OPC-UA server disabled. "
                "Install with: pip install asyncua>=0.9.0"
            )
            return False

        self.get_state = twin_state_getter
        self.on_setpoint_change = setpoint_callback

        self.server = Server()
        await self.server.init()
        self.server.set_endpoint("opc.tcp://0.0.0.0:4840/dcp-twin/")
        self.server.set_server_name("DCP Digital Twin OPC-UA Server")

        # Register namespace
        uri = "http://dcp-digital-twin/"
        idx = await self.server.register_namespace(uri)

        # Create reactor object node
        objects = self.server.nodes.objects
        reactor = await objects.add_object(idx, "Reactor_R101")

        # ─── Read-Only Process Variables ───
        pv_folder = await reactor.add_folder(idx, "ProcessVariables")

        self._nodes["Temperature_PV"] = await pv_folder.add_variable(
            idx, "Temperature_PV", 25.0, ua.VariantType.Double
        )
        self._nodes["Pressure_PV"] = await pv_folder.add_variable(
            idx, "Pressure_PV", 1.0, ua.VariantType.Double
        )
        self._nodes["pH_PV"] = await pv_folder.add_variable(
            idx, "pH_PV", 7.0, ua.VariantType.Double
        )
        self._nodes["Cl2_Flow_PV"] = await pv_folder.add_variable(
            idx, "Cl2_Flow_PV", 0.0, ua.VariantType.Double
        )
        self._nodes["Agitator_RPM_PV"] = await pv_folder.add_variable(
            idx, "Agitator_RPM_PV", 0.0, ua.VariantType.Double
        )
        self._nodes["DCP_Purity_Est"] = await pv_folder.add_variable(
            idx, "DCP_Purity_Est", 0.0, ua.VariantType.Double
        )
        self._nodes["Selectivity_2_4_DCP"] = await pv_folder.add_variable(
            idx, "Selectivity_2_4_DCP", 0.0, ua.VariantType.Double
        )
        self._nodes["TCP_Impurity_Pct"] = await pv_folder.add_variable(
            idx, "TCP_Impurity_Pct", 0.0, ua.VariantType.Double
        )
        self._nodes["Phenol_Conversion_Pct"] = await pv_folder.add_variable(
            idx, "Phenol_Conversion_Pct", 0.0, ua.VariantType.Double
        )
        self._nodes["HCl_Offgas_Rate"] = await pv_folder.add_variable(
            idx, "HCl_Offgas_Rate", 0.0, ua.VariantType.Double
        )
        self._nodes["Recipe_State"] = await pv_folder.add_variable(
            idx, "Recipe_State", "IDLE", ua.VariantType.String
        )
        self._nodes["SCRAM_Active"] = await pv_folder.add_variable(
            idx, "SCRAM_Active", False, ua.VariantType.Boolean
        )
        self._nodes["Batch_ID"] = await pv_folder.add_variable(
            idx, "Batch_ID", "", ua.VariantType.String
        )
        self._nodes["Cooling_Valve_Pos"] = await pv_folder.add_variable(
            idx, "Cooling_Valve_Pos", 50.0, ua.VariantType.Double
        )
        self._nodes["Cl2_Valve_Pos"] = await pv_folder.add_variable(
            idx, "Cl2_Valve_Pos", 0.0, ua.VariantType.Double
        )

        # ─── Writable Setpoints (DCS → Twin) ───
        sp_folder = await reactor.add_folder(idx, "Setpoints")

        self._nodes["Temperature_SP"] = await sp_folder.add_variable(
            idx, "Temperature_SP", 75.0, ua.VariantType.Double
        )
        await self._nodes["Temperature_SP"].set_writable()

        self._nodes["Cl2_Flow_SP"] = await sp_folder.add_variable(
            idx, "Cl2_Flow_SP", 20.0, ua.VariantType.Double
        )
        await self._nodes["Cl2_Flow_SP"].set_writable()

        self._nodes["Agitator_SP"] = await sp_folder.add_variable(
            idx, "Agitator_SP", 100.0, ua.VariantType.Double
        )
        await self._nodes["Agitator_SP"].set_writable()

        logger.info("OPC-UA server initialized on opc.tcp://0.0.0.0:4840/dcp-twin/")
        return True

    async def update_loop(self):
        """
        Main OPC-UA update loop.
        Reads simulator state → writes to OPC-UA nodes (every 1 second).
        Reads writable SP nodes → pushes setpoints back to simulator.
        """
        if not self.server or not self.get_state:
            logger.warning("OPC-UA server not initialized, update loop skipped")
            return

        self.running = True
        async with self.server:
            logger.info("OPC-UA server started — update loop running")
            while self.running:
                try:
                    state = self.get_state()

                    # Update process variables from twin state
                    await self._nodes["Temperature_PV"].write_value(
                        float(state.get("temp", 25.0))
                    )
                    await self._nodes["Pressure_PV"].write_value(
                        float(state.get("pressure", 1.0))
                    )
                    await self._nodes["pH_PV"].write_value(
                        float(state.get("ph", 7.0))
                    )
                    await self._nodes["Cl2_Flow_PV"].write_value(
                        float(state.get("cl2_flow_lph", 0.0))
                    )
                    await self._nodes["Agitator_RPM_PV"].write_value(
                        float(state.get("inputs", {}).get("rpm", 0.0))
                    )

                    # Soft sensor values
                    soft = state.get("soft_sensor", {})
                    await self._nodes["DCP_Purity_Est"].write_value(
                        float(soft.get("dcp_purity", 0.0))
                    )
                    await self._nodes["Selectivity_2_4_DCP"].write_value(
                        float(soft.get("selectivity", 0.0))
                    )
                    await self._nodes["TCP_Impurity_Pct"].write_value(
                        float(soft.get("tcp_impurity", 0.0))
                    )
                    await self._nodes["Phenol_Conversion_Pct"].write_value(
                        float(soft.get("phenol_conversion", 0.0))
                    )

                    # HCl offgas rate (proportional to total reaction rate)
                    rates = soft.get("reaction_rates", {})
                    hcl_rate = (
                        rates.get("r1_phenol_to_2cp", 0.0)
                        + rates.get("r2_2cp_to_dcp", 0.0)
                        + rates.get("r3_dcp_to_tcp", 0.0)
                    )
                    await self._nodes["HCl_Offgas_Rate"].write_value(float(hcl_rate))

                    # Recipe & safety state
                    await self._nodes["Recipe_State"].write_value(
                        str(state.get("recipe_status", "IDLE"))
                    )
                    await self._nodes["SCRAM_Active"].write_value(
                        bool(state.get("safety_scram", False))
                    )
                    await self._nodes["Batch_ID"].write_value(
                        str(state.get("batch_id", ""))
                    )
                    await self._nodes["Cooling_Valve_Pos"].write_value(
                        float(state.get("inputs", {}).get("cooling", 50.0))
                    )
                    await self._nodes["Cl2_Valve_Pos"].write_value(
                        float(state.get("inputs", {}).get("cl2", 0.0))
                    )

                    # Read writable setpoints and push to simulator
                    if self.on_setpoint_change:
                        temp_sp = await self._nodes["Temperature_SP"].read_value()
                        cl2_sp = await self._nodes["Cl2_Flow_SP"].read_value()
                        agit_sp = await self._nodes["Agitator_SP"].read_value()
                        self.on_setpoint_change({
                            "reaction_temp_c": float(temp_sp),
                            "cl2_flow_lph": float(cl2_sp),
                            "agitator_rpm": float(agit_sp),
                        })

                except Exception as e:
                    logger.error(f"OPC-UA update error: {e}")

                await asyncio.sleep(1.0)  # 1-second update rate

    async def stop(self):
        """Gracefully stop the OPC-UA server."""
        self.running = False
        logger.info("OPC-UA server stopped")

    def get_status(self) -> dict:
        """Return current OPC-UA server status."""
        return {
            "enabled": self.server is not None,
            "running": self.running,
            "endpoint": "opc.tcp://0.0.0.0:4840/dcp-twin/" if self.server else None,
            "namespace": "http://dcp-digital-twin/",
            "node_count": len(self._nodes),
            "nodes": list(self._nodes.keys()),
        }
