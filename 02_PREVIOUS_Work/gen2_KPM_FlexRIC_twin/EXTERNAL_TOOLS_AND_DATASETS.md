# External Tools and Dataset Links

Use these when we move beyond the synthetic MVP.

## Highest-Value Next Tools

### OpenAirInterface

Use for realistic 5G RAN/Core emulation.

- Main site: https://openairinterface.org/
- GitLab: https://gitlab.eurecom.fr/oai
- 5G RAN docs: https://gitlab.eurecom.fr/oai/openairinterface5g
- 5G Core docs: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed

Where it fits:

```text
OAI gNB / UE / Core -> KPI collector -> Digital Twin -> AI/RCA/healing
```

Risk:

- Setup can be heavy.
- Works best with Linux/Ubuntu or WSL2/Docker.
- RF realism requires hardware or advanced emulation.

## O-RAN RIC / xApp Tools

### O-RAN Software Community

- Main site: https://o-ran-sc.org/
- Near-RT RIC docs: https://docs.o-ran-sc.org/projects/o-ran-sc-ric-plt-ric-dep/en/latest/
- xApp docs: https://docs.o-ran-sc.org/projects/o-ran-sc-ric-app-qp/en/latest/

Where it fits:

```text
Near-RT RIC -> xApp anomaly/healing logic -> E2 node/OAI/simulated node
```

Risk:

- Installation complexity is high.
- Best attempted after the synthetic MVP is stable.

## Mobility / Map Simulation

### SUMO

Use for vehicle/user movement and road-based service simulation.

- Official docs: https://eclipse.dev/sumo/docs/
- OpenStreetMap import tutorial: https://eclipse.dev/sumo/docs/Tutorials/Import_from_OpenStreetMap.html

Where it fits:

```text
OpenStreetMap roads -> SUMO mobility -> service-class user positions -> KPI simulator
```

### OpenStreetMap

- Main site: https://www.openstreetmap.org/
- Export data: https://www.openstreetmap.org/export

Use:

- roads
- intersections
- highways
- city zones
- vehicle route visualization

## 5G / Vehicular Network Simulators

### ns-3 / 5G-LENA

Use for deeper 5G NR simulation.

- 5G-LENA: https://5g-lena.cttc.es/
- ns-3 NR module: https://apps.nsnam.org/app/nr/

Risk:

- More difficult than SUMO/Python.
- Good for serious wireless simulation after MVP.

### Simu5G

Use for 5G/MEC simulations with OMNeT++.

- Main site: https://simu5g.org/
- User guide: https://simu5g.org/users-guide/overview
- MEC guide: https://simu5g.org/users-guide/mec

Risk:

- Requires OMNeT++ ecosystem.
- Useful if we want 5G + edge/MEC simulation.

### Veins

Use for vehicular network simulation with SUMO + OMNeT++.

- Docs: https://veins.car2x.org/documentation/

Risk:

- More suitable if V2X becomes a focused demo scenario.

## O-RAN Digital Twin / Testbed References

### Colosseum

- Paper: https://arxiv.org/abs/2404.17317
- Platform: https://www.northeastern.edu/colosseum/

Use:

- Research reference for high-fidelity Open RAN digital twin testbeds.

### OpenRAN Gym

- Paper copy: https://ece.northeastern.edu/fac-ece/basagni/papers/BonatiPDBM23.pdf
- Project: https://openrangym.com/

Use:

- xApp/data collection/testing reference.

## Possible Public Data Sources

These may help later, but the MVP does not require them yet.

| Source | Link | Use |
|---|---|---|
| CRAWDAD wireless datasets | https://crawdad.org/ | Mobility/network traces where available. |
| Telecom Italia Big Data Challenge | https://www.kaggle.com/datasets/marcodena/mobile-phone-activity | Mobile activity and demand modeling. |
| OpenCelliD | https://opencellid.org/ | Cell tower geography reference. |
| OpenStreetMap | https://www.openstreetmap.org/ | Road/city topology and map visualization. |

## Recommended Next Download by User

If you want to manually download anything now, prioritize:

1. OpenStreetMap extract of a small city/road area you care about.
2. SUMO installer / tools.
3. OpenAirInterface docs or Docker setup references.
4. Any mobile traffic dataset from Kaggle or CRAWDAD.

Do not start with full OAI + RIC install unless the MVP is stable and we have time for setup debugging.

