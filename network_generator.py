from pathlib import Path
import argparse
import subprocess


PROJECT_DIR = Path(__file__).resolve().parent
SUMO_DIR = PROJECT_DIR / "sumo"

NODE_FILE = SUMO_DIR / "intersection.nod.xml"
EDGE_FILE = SUMO_DIR / "intersection.edg.xml"
NETWORK_FILE = SUMO_DIR / "intersection.net.xml"


def get_lane_count(name, default_value):
    while True:
        value = input(
            f"{name} lanes (1-6) [{default_value}]: "
        ).strip()

        if value == "":
            return default_value

        if value.isdigit() and 1 <= int(value) <= 6:
            return int(value)

        print("Enter a whole number from 1 to 6.")


def create_edge_file(ns_lanes, ew_lanes):
    edge_xml = f"""<?xml version="1.0" encoding="UTF-8"?>

<edges>
    <!-- North-South road -->
    <edge id="north_in" from="north" to="center"
          numLanes="{ns_lanes}" speed="13.89" priority="1"/>

    <edge id="south_in" from="south" to="center"
          numLanes="{ns_lanes}" speed="13.89" priority="1"/>

    <edge id="north_out" from="center" to="north"
          numLanes="{ns_lanes}" speed="13.89" priority="1"/>

    <edge id="south_out" from="center" to="south"
          numLanes="{ns_lanes}" speed="13.89" priority="1"/>

    <!-- East-West road -->
    <edge id="east_in" from="east" to="center"
          numLanes="{ew_lanes}" speed="13.89" priority="1"/>

    <edge id="west_in" from="west" to="center"
          numLanes="{ew_lanes}" speed="13.89" priority="1"/>

    <edge id="east_out" from="center" to="east"
          numLanes="{ew_lanes}" speed="13.89" priority="1"/>

    <edge id="west_out" from="center" to="west"
          numLanes="{ew_lanes}" speed="13.89" priority="1"/>
</edges>
"""

    EDGE_FILE.write_text(edge_xml, encoding="utf-8")


def build_network():
    command = [
        "netconvert",
        "--node-files",
        str(NODE_FILE),
        "--edge-files",
        str(EDGE_FILE),
        "--output-file",
        str(NETWORK_FILE),
        "--lefthand",
        "--tls.layout",
        "opposites",
    ]

    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ns-lanes",
        type=int,
        help="North-South lane count from 1 to 6",
    )

    parser.add_argument(
        "--ew-lanes",
        type=int,
        help="East-West lane count from 1 to 6",
    )

    args = parser.parse_args()

    ns_lanes = args.ns_lanes
    ew_lanes = args.ew_lanes

    if ns_lanes is None:
        ns_lanes = get_lane_count("North-South", 2)

    if ew_lanes is None:
        ew_lanes = get_lane_count("East-West", 2)

    if not 1 <= ns_lanes <= 6:
        raise ValueError("North-South lanes must be between 1 and 6.")

    if not 1 <= ew_lanes <= 6:
        raise ValueError("East-West lanes must be between 1 and 6.")

    create_edge_file(ns_lanes, ew_lanes)
    build_network()

    print("\nNetwork created successfully.")
    print(f"North-South lanes: {ns_lanes}")
    print(f"East-West lanes: {ew_lanes}")
    print("Now run: python sumo_controller.py")


if __name__ == "__main__":
    main()