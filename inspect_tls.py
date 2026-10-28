import traci


SUMO_BINARY = "sumo"
SUMO_CONFIG = "sumo/intersection.sumocfg"


traci.start([
    SUMO_BINARY,
    "-c",
    SUMO_CONFIG,
])

try:
    traffic_lights = traci.trafficlight.getIDList()

    print("Traffic lights found:", traffic_lights)

    for traffic_light_id in traffic_lights:
        print(f"\nTraffic light: {traffic_light_id}")

        programs = traci.trafficlight.getAllProgramLogics(
            traffic_light_id
        )

        for program in programs:
            print(f"Program ID: {program.programID}")

            for index, phase in enumerate(program.phases):
                print(
                    f"Phase {index}: "
                    f"duration={phase.duration}, "
                    f"state={phase.state}"
                )

        print("\nControlled lane connections:")

        connections = traci.trafficlight.getControlledLinks(
            traffic_light_id
        )

        for index, link_group in enumerate(connections):
            if not link_group:
                continue

            from_lane, to_lane, via_lane = link_group[0]

            print(
                f"Signal index {index}: "
                f"{from_lane} -> {to_lane}"
            )

finally:
    traci.close()