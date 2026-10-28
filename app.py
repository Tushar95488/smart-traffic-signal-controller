from flask import Flask, jsonify, render_template

from simulator import TrafficSimulator
from controller import AdaptiveSignalController


app = Flask(__name__)

simulator = TrafficSimulator()
controller = AdaptiveSignalController()


def get_simulation_state():
    """Prepare all simulation information for the visual dashboard."""

    state = simulator.snapshot()

    state["signal_phase"] = controller.current_phase
    state["phase_duration"] = controller.phase_duration
    state["learned_states"] = len(controller.q_table)

    return state


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/state")
def state():
    return jsonify(get_simulation_state())


@app.route("/api/tick", methods=["POST"])
def tick():
    """Run the simulation for one second."""

    phase = controller.choose_phase(simulator.queues)

    departed_before = simulator.total_departed
    simulator.step(phase)

    vehicles_departed = simulator.total_departed - departed_before

    # Higher reward: more vehicles leave and fewer remain waiting.
    reward = (
        vehicles_departed * 2
        - simulator.snapshot()["total_queue"] * 0.25
    )

    controller.learn(reward, simulator.queues)

    return jsonify(get_simulation_state())


@app.route("/api/reset", methods=["POST"])
def reset():
    global simulator, controller

    simulator = TrafficSimulator()
    controller = AdaptiveSignalController()

    return jsonify(get_simulation_state())


if __name__ == "__main__":
    app.run(debug=True)