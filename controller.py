import random


class AdaptiveSignalController:
    """
    Uses Q-learning to choose the better traffic-signal phase.

    NS_GREEN = North and South lanes get green.
    EW_GREEN = East and West lanes get green.
    """

    PHASES = ("NS_GREEN", "EW_GREEN")

    def __init__(self, epsilon=0.10, learning_rate=0.20, discount_factor=0.90):
        self.epsilon = epsilon
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

        self.q_table = {}
        self.current_phase = "NS_GREEN"
        self.phase_duration = 0

        self.previous_state = None
        self.previous_action = None

    def get_state(self, queues):
        """Convert queue sizes into small categories for Q-learning."""

        north_south_queue = queues["north"] + queues["south"]
        east_west_queue = queues["east"] + queues["west"]

        # Queue categories: 0=low, 1=medium, 2=high, 3=very high
        ns_level = min(north_south_queue // 4, 3)
        ew_level = min(east_west_queue // 4, 3)

        return (ns_level, ew_level)

    def choose_phase(self, queues):
        """Choose a signal phase while following safety timing rules."""

        state = self.get_state(queues)

        # A green signal must stay active for at least 4 seconds.
        if self.phase_duration < 4:
            self.phase_duration += 1
            self.previous_state = state
            self.previous_action = self.current_phase
            return self.current_phase

        # A green signal cannot stay active for more than 15 seconds.
        if self.phase_duration >= 15:
            chosen_phase = (
                "EW_GREEN"
                if self.current_phase == "NS_GREEN"
                else "NS_GREEN"
            )
        elif random.random() < self.epsilon:
            # Explore a random phase sometimes.
            chosen_phase = random.choice(self.PHASES)
        else:
            # Choose the phase with the highest learned Q-value.
            if state not in self.q_table:
                self.q_table[state] = {
                    "NS_GREEN": 0.0,
                    "EW_GREEN": 0.0,
                }

            chosen_phase = max(
                self.PHASES,
                key=lambda phase: self.q_table[state][phase],
            )

        if chosen_phase == self.current_phase:
            self.phase_duration += 1
        else:
            self.current_phase = chosen_phase
            self.phase_duration = 1

        self.previous_state = state
        self.previous_action = chosen_phase

        return chosen_phase

    def learn(self, reward, new_queues):
        """Update Q-values after seeing the result of the selected phase."""

        if self.previous_state is None:
            return

        next_state = self.get_state(new_queues)

        if next_state not in self.q_table:
            self.q_table[next_state] = {
                "NS_GREEN": 0.0,
                "EW_GREEN": 0.0,
            }

        if self.previous_state not in self.q_table:
            self.q_table[self.previous_state] = {
                "NS_GREEN": 0.0,
                "EW_GREEN": 0.0,
            }

        old_value = self.q_table[self.previous_state][self.previous_action]
        best_next_value = max(self.q_table[next_state].values())

        new_value = old_value + self.learning_rate * (
            reward
            + self.discount_factor * best_next_value
            - old_value
        )

        self.q_table[self.previous_state][self.previous_action] = new_value