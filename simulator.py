import random


class TrafficSimulator:
    """Simulates vehicle queues at a four-way intersection."""

    LANES = ("north", "south", "east", "west")

    def __init__(self, seed=42):
        self.random = random.Random(seed)

        # Initial vehicles waiting in each lane
        self.queues = {
            "north": 5,
            "south": 4,
            "east": 6,
            "west": 3,
        }

        self.time = 0
        self.total_departed = 0
        self.total_waiting_time = 0
        self.last_departures = []

    def step(self, green_phase):
        """
        Simulate one second and record the vehicles that leave
        the junction for the visual animation.
        """
        self.time += 1
        self.last_departures = []

        green_lanes = (
            ("north", "south")
            if green_phase == "NS_GREEN"
            else ("east", "west")
        )
        departed_this_step = 0
        for lane in green_lanes:
            vehicles_can_leave = self.random.randint(1, 3)
            vehicles_leaving = min(vehicles_can_leave, self.queues[lane])

            self.queues[lane] -= vehicles_leaving
            departed_this_step += vehicles_leaving
            # Each passed vehicle selects a realistic movement.
            for _ in range(vehicles_leaving):
                movement = self.random.choices(
                    ["straight", "left", "right"],
                    weights=[60, 25, 15],
                    k=1,
                )[0]

                self.last_departures.append(
                    {
                        "from": lane,
                        "movement": movement,
                    }
                )
        self.total_departed += departed_this_step

        for lane in self.LANES:
            new_vehicles = self.random.choice([0, 0, 1, 1, 2])
            self.queues[lane] = min(self.queues[lane] + new_vehicles, 25)

        self.total_waiting_time += sum(self.queues.values())

        return self.snapshot()        


    def snapshot(self):
        """Return current simulation details."""

        total_queue = sum(self.queues.values())

        return {
            "time": self.time,
            "queues": self.queues.copy(),
            "total_queue": total_queue,
            "total_departed": self.total_departed,
            "average_wait": round(
                self.total_waiting_time / max(self.time, 1),
                2,
            ),
            "departures": self.last_departures.copy(),
        }