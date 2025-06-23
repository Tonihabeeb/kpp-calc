# KPP Simulator

This project simulates a kinetic power plant and streams results via a small Flask
application.  The code is organized into modular packages so that physical
components and the web interface are easily extended.

## Structure

- `simulation/` — engine and physics components
- `simulation/controller.py` — manages the engine in a background thread
- `routes/` — Flask blueprints for the API and streaming endpoints
- `config/` — default parameters in JSON format
- `templates/` and `static/` — web UI assets

## Running

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` to view the interface.  API endpoints for starting
and stopping the simulation are provided under `/start` and `/stop`.
