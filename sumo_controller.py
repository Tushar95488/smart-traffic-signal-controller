from collections import defaultdict
from pathlib import Path
import random

import traci


PROJECT_DIR = Path(__file__).resolve().parent
SUMO_CONFIG = PROJECT_DIR / "sumo" / "intersection.sumocfg"

TLS_ID = "center"

SIMULATION_STEP = 0.1

MIN_GREEN_TIME = 10.0
MAX_GREEN_TIME = 30.0
YELLOW_TIME = 3.0
ALL_RED_TIME = 1.0
MAX_RED_WAIT = 45.0

GROUPS = ("NS", "EW")

GROUP_EDGES = {
    "NS": ("north_in", "south_in"),
    "EW": ("east_in", "west_in"),
}


class FairQLearningController:
    def __init__(
        self,
        epsilon=0.10,
        learning_rate=0.20,
        discount_factor=0.90,
    ):
        self.epsilon = epsilon
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

        self.q_table = defaultdict(
            lambda: {"NS": 0.0, "EW": 0.0}
        )

        self.previous_state = None
        self.previous_action = None

    def get_state(self, ns_density, ew_density, ns_wait, ew_wait):
        return (
            min(int(ns_density // 3), 4),
            min(int(ew_density // 3), 4),
            min(int(ns_wait // 15), 3),
            min(int(ew_wait // 15), 3),
        )

    def choose_group(
        self,
        ns_density,
        ew_density,
        ns_wait,
        ew_wait,
        allowed=None,
    ):
        candidates = allowed or list(GROUPS)

        if ns_density > 0 and ns_wait >= MAX_RED_WAIT:
            selected = "NS"

        elif ew_density > 0 and ew_wait >= MAX_RED_WAIT:
            selected = "EW"

        elif random.random() < self.epsilon:
            selected = random.choice(candidates)

        else:
            state = self.get_state(
                ns_density,
                ew_density,
                ns_wait,
                ew_wait,
            )

            pressure = {
                "NS": ns_density * 0.50 + ns_wait * 0.03,
                "EW": ew_density * 0.50 + ew_wait * 0.03,
            }

            selected = max(
                candidates,
                key=lambda group:
                self.q_table[state][group] + pressure[group],
            )

        self.previous_state = self.get_state(
            ns_density,
            ew_density,
            ns_wait,
            ew_wait,
        )

        self.previous_action = selected

        return selected

    def learn(self, reward, ns_density, ew_density, ns_wait, ew_wait):
        if self.previous_state is None:
            return

        next_state = self.get_state(
            ns_density,
            ew_density,
            ns_wait,
            ew_wait,
        )

        old_value = self.q_table[
            self.previous_state
        ][self.previous_action]

        best_future_value = max(
            self.q_table[next_state].values()
        )

        self.q_table[
            self.previous_state
        ][self.previous_action] = old_value + (
            self.learning_rate
            * (
                reward
                + self.discount_factor * best_future_value
                - old_value
            )
        )


class PairedSignalController:
    def __init__(self):
        self.agent = FairQLearningController()

        self.group_link_indexes = {
            "NS": [],
            "EW": [],
        }

        self.signal_count = 0

        self.green_phase = {}
        self.yellow_phase = {}

        self.mode = "ALL_RED"
        self.current_group = None
        self.next_group = "NS"

        self.phase_elapsed = 0.0
        self.decision_elapsed = 0.0

        self.red_wait = {
            "NS": 0.0,
            "EW": 0.0,
        }

        self.last_report_second = -1

    def read_signal_links(self):
        connections = traci.trafficlight.getControlledLinks(
            TLS_ID
        )

        self.signal_count = len(connections)

        for index, link_group in enumerate(connections):
            if not link_group:
                continue

            from_lane = link_group[0][0]

            if (
                from_lane.startswith("north_in_")
                or from_lane.startswith("south_in_")
            ):
                self.group_link_indexes["NS"].append(index)

            elif (
                from_lane.startswith("east_in_")
                or from_lane.startswith("west_in_")
            ):
                self.group_link_indexes["EW"].append(index)

    def find_signal_phases(self):
        programs = traci.trafficlight.getAllProgramLogics(
            TLS_ID
        )

        program = programs[0]

        for phase in program.phases:
            state = phase.state

            ns_green = any(
                state[link] in ("G", "g")
                for link in self.group_link_indexes["NS"]
            )

            ew_green = any(
                state[link] in ("G", "g")
                for link in self.group_link_indexes["EW"]
            )

            ns_yellow = any(
                state[link] in ("Y", "y")
                for link in self.group_link_indexes["NS"]
            )

            ew_yellow = any(
                state[link] in ("Y", "y")
                for link in self.group_link_indexes["EW"]
            )

            if ns_green and not ew_green:
                self.green_phase["NS"] = state

            elif ew_green and not ns_green:
                self.green_phase["EW"] = state

            elif ns_yellow and not ew_yellow:
                self.yellow_phase["NS"] = state

            elif ew_yellow and not ns_yellow:
                self.yellow_phase["EW"] = state

        if (
            set(self.green_phase) != set(GROUPS)
            or set(self.yellow_phase) != set(GROUPS)
        ):
            raise RuntimeError(
                "Could not identify NS/EW signal states."
            )

        print("\nDetected standard signal states.")

    def get_group_density(self, group):
        total_density = 0.0

        for edge_id in GROUP_EDGES[group]:
            vehicles = traci.edge.getLastStepVehicleNumber(
                edge_id
            )

            stopped = traci.edge.getLastStepHaltingNumber(
                edge_id
            )

            total_density += vehicles + (stopped * 1.5)

        return total_density

    def get_densities(self):
        return {
            "NS": self.get_group_density("NS"),
            "EW": self.get_group_density("EW"),
        }

    def all_red_state(self):
        return "r" * self.signal_count

    def begin_green(self, group):
        traci.trafficlight.setRedYellowGreenState(
            TLS_ID,
            self.green_phase[group],
        )

        self.mode = "GREEN"
        self.current_group = group
        self.phase_elapsed = 0.0
        self.decision_elapsed = 0.0

    def begin_yellow(self):
        traci.trafficlight.setRedYellowGreenState(
            TLS_ID,
            self.yellow_phase[self.current_group],
        )

        self.mode = "YELLOW"
        self.phase_elapsed = 0.0

    def begin_all_red(self):
        traci.trafficlight.setRedYellowGreenState(
            TLS_ID,
            self.all_red_state(),
        )

        self.mode = "ALL_RED"
        self.phase_elapsed = 0.0

    def update_wait_times(self, densities):
        for group in GROUPS:
            if (
                self.mode == "GREEN"
                and group == self.current_group
            ):
                self.red_wait[group] = 0.0

            elif densities[group] > 0:
                self.red_wait[group] += SIMULATION_STEP

    def select_next_group(self, densities, force_change=False):
        if force_change:
            allowed = [
                group
                for group in GROUPS
                if group != self.current_group
            ]
        else:
            allowed = list(GROUPS)

        return self.agent.choose_group(
            densities["NS"],
            densities["EW"],
            self.red_wait["NS"],
            self.red_wait["EW"],
            allowed,
        )

    def print_metrics(self, simulation_time, densities):
        current_second = int(simulation_time)

        if current_second == self.last_report_second:
            return

        self.last_report_second = current_second

        print(
            f"Time={simulation_time:5.1f}s | "
            f"Mode={self.mode:7} | "
            f"Active={str(self.current_group):2} | "
            f"NS density={densities['NS']:4.1f} | "
            f"EW density={densities['EW']:4.1f} | "
            f"NS wait={self.red_wait['NS']:4.1f}s | "
            f"EW wait={self.red_wait['EW']:4.1f}s"
        )

    def update(self):
        simulation_time = traci.simulation.getTime()
        densities = self.get_densities()

        self.update_wait_times(densities)

        reward = -(
            densities["NS"]
            + densities["EW"]
            + 0.03 * (
                self.red_wait["NS"]
                + self.red_wait["EW"]
            )
        )

        self.agent.learn(
            reward,
            densities["NS"],
            densities["EW"],
            self.red_wait["NS"],
            self.red_wait["EW"],
        )

        self.phase_elapsed += SIMULATION_STEP

        if self.mode == "YELLOW":
            if self.phase_elapsed >= YELLOW_TIME:
                self.begin_all_red()

        elif self.mode == "ALL_RED":
            if self.phase_elapsed >= ALL_RED_TIME:
                self.begin_green(self.next_group)

        elif self.mode == "GREEN":
            self.decision_elapsed += SIMULATION_STEP

            other_group = (
                "EW"
                if self.current_group == "NS"
                else "NS"
            )

            if (
                self.phase_elapsed >= MAX_GREEN_TIME
                and densities[other_group] > 0
            ):
                self.next_group = self.select_next_group(
                    densities,
                    force_change=True,
                )

                self.begin_yellow()

            elif self.decision_elapsed >= 1.0:
                self.decision_elapsed = 0.0

                if self.phase_elapsed >= MIN_GREEN_TIME:
                    selected = self.select_next_group(densities)

                    if selected != self.current_group:
                        self.next_group = selected
                        self.begin_yellow()

        self.print_metrics(simulation_time, densities)


def main():
    traci.start([
        "sumo-gui",
        "-c",
        str(SUMO_CONFIG),
        "--start",
        "--delay",
        "150",
        "--collision.check-junctions",
        "true",
        "--collision.action",
        "warn",
        "--time-to-teleport",
        "-1",
    ])

    controller = PairedSignalController()

    controller.read_signal_links()
    controller.find_signal_phases()

    traci.trafficlight.setRedYellowGreenState(
        TLS_ID,
        controller.all_red_state(),
    )

    print("\nStandard paired NS/EW controller started.")

    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            controller.update()

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")

    except traci.exceptions.FatalTraCIError:
        print("\nSUMO GUI was closed or simulation finished.")

    finally:
        try:
            traci.close()
        except traci.exceptions.FatalTraCIError:
            pass


if __name__ == "__main__":
    main()