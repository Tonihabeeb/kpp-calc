from flask import Blueprint, Response
import json
import time

stream_bp = Blueprint('stream', __name__)


def setup(controller):
    global _controller
    _controller = controller


@stream_bp.route('/stream')
def stream():
    def event_stream():
        queue = _controller.get_queue()
        while True:
            if not queue.empty():
                data = queue.get()
                yield f"data: {json.dumps(data)}\n\n"
            else:
                yield f"data: {json.dumps({'heartbeat': True})}\n\n"
            time.sleep(0.1)
    return Response(event_stream(), mimetype='text/event-stream')
