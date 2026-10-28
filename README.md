# Smart Traffic Signal Controller

An adaptive traffic-signal simulation built with Python and SUMO (Simulation of Urban MObility). The project models a four-way Indian left-hand-traffic intersection and dynamically selects north-south or east-west green phases based on real-time traffic conditions.

## AI Assistance

This project was developed with AI-assisted programming support using ChatGPT/Codex. AI was used to help generate, explain, debug, and improve parts of the code and documentation.

The project design decisions, SUMO installation, simulation configuration, testing, debugging, and GitHub deployment were completed and verified by Tushar Pandey.

## Features

- Four-way SUMO intersection with Indian left-hand traffic
- Collision-safe microscopic vehicle simulation using SUMO
- Adaptive paired signal phases:
  - North-South green
  - Yellow clearance
  - All-red safety phase
  - East-West green
- Live traffic-density and stopped-vehicle queue analysis
- Fairness mechanism to prevent any direction from waiting too long
- Configurable lane count from 1 to 6 lanes per direction
- Q-learning component in the Python traffic-control simulator
- Flask dashboard prototype for visual queue and metric monitoring
- Randomized multicolour car sprites in SUMO GUI
- Custom route flows for north, south, east, and west approaches

## Technology Stack

- Python
- SUMO / SUMO-GUI
- TraCI
- Flask
- NumPy
- HTML, CSS, JavaScript
- Git and GitHub

## Project Structure

```text
smart-traffic-signal-controller/
├── app.py                     # Flask dashboard entry point
├── controller.py              # Python traffic-control logic
├── simulator.py               # Simplified traffic simulator
├── sumo_controller.py         # Adaptive SUMO signal controller
├── network_generator.py       # Generates 1-6 lane SUMO networks
├── inspect_tls.py             # Inspects SUMO traffic-light phases
├── requirements.txt
├── static/
│   ├── app.js
│   └── style.css
├── templates/
│   └── index.html
└── sumo/
    ├── assets/                # Custom car sprites
    ├── intersection.nod.xml   # Intersection nodes
    ├── intersection.edg.xml   # Road edges
    ├── intersection.net.xml   # Generated SUMO network
    ├── intersection.rou.xml   # Vehicle routes and flows
    └── intersection.sumocfg   # SUMO configuration
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Tushar95488/smart-traffic-signal-controller.git
cd smart-traffic-signal-controller
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Install SUMO

On Windows:

```powershell
winget install --name sumo
```

Restart VS Code after installation so that `sumo-gui` and `netconvert` are available in the terminal.

## Run the SUMO Simulation

Generate a road network with the required lane count:

```powershell
python network_generator.py --ns-lanes 2 --ew-lanes 2
```

`--ns-lanes` and `--ew-lanes` accept values from `1` to `6`.

Start the adaptive controller:

```powershell
python sumo_controller.py
```

In SUMO-GUI, select the vehicle shape scheme:

```text
View Settings → Vehicles → raster images
```

This enables the custom coloured car sprites.

## Run the Flask Dashboard

```powershell
python app.py
```

Open this address in your browser:

```text
http://127.0.0.1:5000
```

## Adaptive Signal Strategy

The controller continuously monitors the intersection and makes decisions using:

- Vehicle density in north-south and east-west directions
- Number of stopped vehicles
- Current red-light waiting time
- Minimum and maximum green durations
- Yellow and all-red safety clearance times
- Fairness rules that prevent traffic starvation

Instead of turning one individual lane green at a time, the controller uses standard paired traffic phases:

```text
North + South green → Yellow → All red → East + West green
```

This reduces excessive waiting time and clears queues more efficiently while maintaining safe conflicting movements.

## Future Improvements

- Compare adaptive control against a fixed-time signal baseline
- Add emergency-vehicle priority
- Add pedestrian crossings and pedestrian signals
- Add traffic analytics charts and CSV result export
- Train and evaluate the Q-learning policy across different traffic scenarios

## Note on Assets

The custom car sprites are used for simulation visualization. Replace them with assets you are licensed to redistribute before using this project commercially or publicly if required.