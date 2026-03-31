"""
Soft Sensor for Real-Time Purity Estimation
Estimates 2,4-DCP concentration from process variables without lab analysis.

Uses Euler integration of concentration ODEs driven by ChlorinationKinetics.
Updates every simulation tick (~100ms) to provide continuous quality estimates.
"""

from .kinetics import ChlorinationKinetics


class DCPSoftSensor:
    """
    Real-time virtual analyser for 2,4-DCP production.

    Tracks five chemical species via ODE integration:
      - Phenol (starting material)
      - 2-Chlorophenol (2-CP, intermediate)
      - 2,4-Dichlorophenol (2,4-DCP, desired product)
      - 2,4,6-Trichlorophenol (TCP, undesired byproduct)
      - Dissolved Cl2 (reagent)

    Outputs purity, impurity, conversion, and selectivity metrics.
    """

    def __init__(self, kinetics: ChlorinationKinetics = None):
        self.kinetics = kinetics or ChlorinationKinetics()

        # State vector — concentrations in mol/L
        self.concentrations = {
            "phenol": 0.0,
            "monochlorophenol": 0.0,  # 2-CP
            "dcp_2_4": 0.0,           # 2,4-DCP (desired)
            "tcp_2_4_6": 0.0,         # 2,4,6-TCP (undesired)
            "cl2_dissolved": 0.0,
        }

        # Track initial phenol for conversion calculation
        self.initial_phenol = 0.0

        # Accumulated heat generation (Watts, for energy balance)
        self.last_heat_generation_W = 0.0

        # Reaction rates from last tick (for telemetry)
        self.last_rates = (0.0, 0.0, 0.0)

    def initialize(self, phenol_concentration: float):
        """
        Set initial phenol concentration at batch start.

        Args:
            phenol_concentration: Initial phenol concentration in mol/L
        """
        self.concentrations = {
            "phenol": max(0.0, phenol_concentration),
            "monochlorophenol": 0.0,
            "dcp_2_4": 0.0,
            "tcp_2_4_6": 0.0,
            "cl2_dissolved": 0.0,
        }
        self.initial_phenol = max(0.0, phenol_concentration)
        self.last_heat_generation_W = 0.0
        self.last_rates = (0.0, 0.0, 0.0)

    def update(
        self,
        dt_seconds: float,
        T_celsius: float,
        cl2_feed_rate_mol_per_min: float,
        volume_L: float,
        mixing_efficiency: float = 1.0,
    ) -> dict:
        """
        Euler integration of concentration ODEs for one time step.

        Args:
            dt_seconds: Time step in seconds
            T_celsius: Current reactor temperature (°C)
            cl2_feed_rate_mol_per_min: Cl2 feed rate (mol/min)
            volume_L: Reactor liquid volume (L)
            mixing_efficiency: 0.0–1.0 fraction based on agitator RPM

        Returns:
            Dictionary with purity estimate metrics
        """
        C = self.concentrations
        dt_min = dt_seconds / 60.0

        # Get reaction rates from Arrhenius kinetics
        r1, r2, r3 = self.kinetics.reaction_rates(
            C["phenol"],
            C["monochlorophenol"],
            C["dcp_2_4"],
            C["cl2_dissolved"],
            T_celsius,
        )

        # Apply mixing efficiency — poor mixing reduces effective rates
        r1 *= mixing_efficiency
        r2 *= mixing_efficiency
        r3 *= mixing_efficiency

        self.last_rates = (r1, r2, r3)

        # Euler integration — mass balances (mol/L/min * min = mol/L change)
        # dC_phenol/dt     = -r1
        # dC_2CP/dt        = +r1 - r2
        # dC_2_4_DCP/dt    = +r2 - r3
        # dC_TCP/dt        = +r3
        # dC_Cl2/dt        = feed_rate/V - r1 - r2 - r3
        C["phenol"]            -= r1 * dt_min
        C["monochlorophenol"]  += (r1 - r2) * dt_min
        C["dcp_2_4"]           += (r2 - r3) * dt_min
        C["tcp_2_4_6"]         += r3 * dt_min

        # Cl2 dissolved: fed in minus consumed by all reactions
        cl2_feed_concentration_rate = 0.0
        if volume_L > 0:
            cl2_feed_concentration_rate = cl2_feed_rate_mol_per_min / volume_L
        C["cl2_dissolved"] += (cl2_feed_concentration_rate - r1 - r2 - r3) * dt_min

        # Clamp all concentrations >= 0 (numerical safety)
        for key in C:
            C[key] = max(0.0, C[key])

        # Calculate heat generation for energy balance feedback
        self.last_heat_generation_W = self.kinetics.heat_generation_rate(
            r1, r2, r3, volume_L
        )

        return self.get_purity_estimate()

    def get_purity_estimate(self) -> dict:
        """
        Calculate quality metrics from current concentrations.

        Returns:
            dict with:
              - dcp_purity: % of chlorinated products that is 2,4-DCP
              - tcp_impurity: % of chlorinated products that is TCP
              - phenol_conversion: % of initial phenol consumed
              - selectivity: moles DCP / moles phenol consumed
              - concentrations: raw concentration dict
              - heat_generation_W: heat from reactions (Watts)
        """
        C = self.concentrations

        total_chlorinated = (
            C["monochlorophenol"] + C["dcp_2_4"] + C["tcp_2_4_6"]
        )

        if total_chlorinated < 1e-9:
            dcp_purity = 0.0
            tcp_impurity = 0.0
        else:
            dcp_purity = (C["dcp_2_4"] / total_chlorinated) * 100.0
            tcp_impurity = (C["tcp_2_4_6"] / total_chlorinated) * 100.0

        # Phenol conversion
        if self.initial_phenol < 1e-9:
            phenol_conversion = 0.0
        else:
            phenol_conversion = (
                (1.0 - C["phenol"] / self.initial_phenol) * 100.0
            )
            phenol_conversion = max(0.0, min(100.0, phenol_conversion))

        # Selectivity
        phenol_consumed = max(0.0, self.initial_phenol - C["phenol"])
        selectivity = self.kinetics.selectivity_2_4_DCP(
            C["dcp_2_4"], phenol_consumed
        )

        return {
            "dcp_purity": round(dcp_purity, 2),
            "tcp_impurity": round(tcp_impurity, 2),
            "phenol_conversion": round(phenol_conversion, 2),
            "selectivity": round(selectivity, 4),
            "concentrations": {k: round(v, 6) for k, v in C.items()},
            "heat_generation_W": round(self.last_heat_generation_W, 2),
            "reaction_rates": {
                "r1_phenol_to_2cp": round(self.last_rates[0], 8),
                "r2_2cp_to_dcp": round(self.last_rates[1], 8),
                "r3_dcp_to_tcp": round(self.last_rates[2], 8),
            },
        }

    def reset(self):
        """Reset soft sensor to zero state."""
        self.concentrations = {
            "phenol": 0.0,
            "monochlorophenol": 0.0,
            "dcp_2_4": 0.0,
            "tcp_2_4_6": 0.0,
            "cl2_dissolved": 0.0,
        }
        self.initial_phenol = 0.0
        self.last_heat_generation_W = 0.0
        self.last_rates = (0.0, 0.0, 0.0)
