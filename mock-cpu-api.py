from flask import Flask, jsonify
import threading
import psutil

app = Flask(__name__)
cpu_usage = 0


def update_value():
    global cpu_usage
    while True:
        cpu_p = psutil.cpu_percent(interval=1)
        cpu_usage = cpu_p


@app.route("/cpu", methods=["GET"])
def get_value():
    return jsonify({"cpu_usage": cpu_usage})


if __name__ == "__main__":
    update_thread = threading.Thread(target=update_value)
    update_thread.daemon = True
    update_thread.start()

    app.run(debug=True, port=5001)
