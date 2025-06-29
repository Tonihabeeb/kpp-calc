"""Simulation API blueprint (stub)."""

import os

from flask import Blueprint, send_from_directory

sim_api_bp = Blueprint("sim_api", __name__)


@sim_api_bp.route("/plots/<filename>", methods=["GET"])
def get_plot(filename):
    """
    Serve the generated plot images from the static/plots directory.
    """
    plots_dir = os.path.join(os.getcwd(), "static", "plots")
    return send_from_directory(plots_dir, filename)
