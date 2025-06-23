from flask import Flask, render_template

from routes.stream import stream_bp, setup as stream_setup
from routes.api import api_bp, setup as api_setup
from simulation.controller import SimulationController
import config

app = Flask(__name__)

controller = SimulationController(config.DEFAULT_PARAMS.copy())
stream_setup(controller)
api_setup(controller)

app.register_blueprint(stream_bp)
app.register_blueprint(api_bp)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
