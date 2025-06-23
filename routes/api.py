from flask import Blueprint, request, render_template, send_file, Response, jsonify
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

api_bp = Blueprint('api', __name__)


def setup(controller):
    global _controller
    _controller = controller


@api_bp.route('/start', methods=['POST'])
def start_simulation():
    params = request.get_json() or {}
    _controller.update_params(params)
    if not _controller.thread or not _controller.thread.is_alive():
        _controller.start()
    return ('Simulation started', 200)


@api_bp.route('/stop', methods=['POST'])
def stop_simulation():
    _controller.stop()
    return ('Simulation stopped', 200)


@api_bp.route('/update_params', methods=['POST'])
def update_params():
    params = request.get_json() or {}
    _controller.update_params(params)
    return ('OK', 200)


@api_bp.route('/summary')
def summary_data():
    q = _controller.get_queue()
    try:
        latest = q.queue[-1] if not q.empty() else None
    except Exception:
        latest = None
    return latest or {}


@api_bp.route('/chart/<metric>.png')
def chart_image(metric):
    times, torques, powers = [], [], []
    q = _controller.get_queue()
    with q.mutex:
        data_list = list(q.queue)
    for entry in data_list:
        times.append(entry.get('time', 0))
        torques.append(entry.get('torque', 0))
        powers.append(entry.get('power', 0))
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    if metric == 'torque' and times:
        ax.plot(times, torques, color='blue')
    elif metric == 'power' and times:
        ax.plot(times, powers, color='green')
    else:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center')
    ax.set_xlabel('Time (s)')
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@api_bp.route('/data/history')
def data_history():
    q = _controller.get_queue()
    with q.mutex:
        data_list = list(q.queue)
    times = [d.get('time', 0) for d in data_list]
    torques = [d.get('torque', 0) for d in data_list]
    powers = [d.get('power', 0) for d in data_list]
    return {'time': times, 'torque': torques, 'power': powers}


@api_bp.route('/reset', methods=['POST'])
def reset_simulation():
    _controller.stop()
    q = _controller.get_queue()
    with q.mutex:
        q.queue.clear()
    _controller.engine.time = 0.0
    return ('Simulation reset', 200)


@api_bp.route('/download_csv')
def download_csv():
    def generate_csv():
        yield 'time,torque,power\n'
        q = _controller.get_queue()
        with q.mutex:
            data_list = list(q.queue)
        for entry in data_list:
            yield f"{entry.get('time',0)},{entry.get('torque',0)},{entry.get('power',0)}\n"
    response = Response(generate_csv(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename="sim_data.csv"'
    return response
