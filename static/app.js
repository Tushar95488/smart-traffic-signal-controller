const canvas = document.getElementById("trafficCanvas");
const ctx = canvas.getContext("2d");

let simulationState = null;
let isRunning = true;
let activeVehicles = [];
let previousFrameTime = 0;


/* ---------------- API FUNCTIONS ---------------- */

async function loadState() {
    const response = await fetch("/api/state");
    simulationState = await response.json();
    updateDashboard();
}

async function runTick() {
    const response = await fetch("/api/tick", {
        method: "POST",
    });

    simulationState = await response.json();

    spawnVehicles(simulationState.departures);
    updateDashboard();
}

async function resetSimulation() {
    const response = await fetch("/api/reset", {
        method: "POST",
    });

    simulationState = await response.json();
    activeVehicles = [];

    updateDashboard();
}


/* ---------------- DASHBOARD ---------------- */

function updateDashboard() {
    if (!simulationState) {
        return;
    }

    document.getElementById("signalPhase").textContent =
        simulationState.signal_phase.replace("_", " ");

    document.getElementById("phaseDuration").textContent =
        `Phase duration: ${simulationState.phase_duration} sec`;

    document.getElementById("totalQueue").textContent =
        simulationState.total_queue;

    document.getElementById("departed").textContent =
        simulationState.total_departed;

    document.getElementById("averageWait").textContent =
        simulationState.average_wait;

    document.getElementById("learnedStates").textContent =
        simulationState.learned_states;
}


/* ---------------- TRAFFIC PATHS ---------------- */

/*
Indian left-hand traffic lanes:
North → South uses right side of vertical road.
South → North uses left side of vertical road.
West → East uses upper side of horizontal road.
East → West uses lower side of horizontal road.
*/

function getVehiclePath(from, movement) {
    const paths = {
        north: {
            straight: {
                start: { x: 435, y: 145 },
                control: { x: 435, y: 330 },
                end: { x: 435, y: 560 },
            },
            left: {
                start: { x: 435, y: 145 },
                control: { x: 435, y: 215 },
                end: { x: 840, y: 215 },
            },
            right: {
                start: { x: 435, y: 145 },
                control: { x: 435, y: 305 },
                end: { x: -40, y: 305 },
            },
        },

        south: {
            straight: {
                start: { x: 365, y: 375 },
                control: { x: 365, y: 180 },
                end: { x: 365, y: -40 },
            },
            left: {
                start: { x: 365, y: 375 },
                control: { x: 365, y: 305 },
                end: { x: -40, y: 305 },
            },
            right: {
                start: { x: 365, y: 375 },
                control: { x: 365, y: 215 },
                end: { x: 840, y: 215 },
            },
        },

        west: {
            straight: {
                start: { x: 285, y: 215 },
                control: { x: 510, y: 215 },
                end: { x: 840, y: 215 },
            },
            left: {
                start: { x: 285, y: 215 },
                control: { x: 365, y: 215 },
                end: { x: 365, y: -40 },
            },
            right: {
                start: { x: 285, y: 215 },
                control: { x: 435, y: 215 },
                end: { x: 435, y: 560 },
            },
        },

        east: {
            straight: {
                start: { x: 515, y: 305 },
                control: { x: 290, y: 305 },
                end: { x: -40, y: 305 },
            },
            left: {
                start: { x: 515, y: 305 },
                control: { x: 435, y: 305 },
                end: { x: 435, y: 560 },
            },
            right: {
                start: { x: 515, y: 305 },
                control: { x: 365, y: 305 },
                end: { x: 365, y: -40 },
            },
        },
    };

    return paths[from][movement];
}


function getPointOnPath(path, progress) {
    const remaining = 1 - progress;

    return {
        x:
            remaining * remaining * path.start.x +
            2 * remaining * progress * path.control.x +
            progress * progress * path.end.x,

        y:
            remaining * remaining * path.start.y +
            2 * remaining * progress * path.control.y +
            progress * progress * path.end.y,
    };
}


function getVehicleAngle(path, progress) {
    const remaining = 1 - progress;

    const dx =
        2 * remaining * (path.control.x - path.start.x) +
        2 * progress * (path.end.x - path.control.x);

    const dy =
        2 * remaining * (path.control.y - path.start.y) +
        2 * progress * (path.end.y - path.control.y);

    return Math.atan2(dy, dx);
}


function spawnVehicles(departures) {
    if (!departures) {
        return;
    }

    const colors = {
        north: "#74a7ff",
        south: "#b782ff",
        west: "#ffbd5a",
        east: "#ff7180",
    };

    departures.forEach((vehicle, index) => {
        activeVehicles.push({
            path: getVehiclePath(vehicle.from, vehicle.movement),
            color: colors[vehicle.from],
            progress: -index * 0.13,
        });
    });
}


/* ---------------- CANVAS DRAWING ---------------- */

function drawRoads() {
    ctx.fillStyle = "#2a4552";
    ctx.fillRect(0, 0, 800, 520);

    ctx.fillStyle = "#1d3440";
    ctx.fillRect(0, 165, 800, 190);
    ctx.fillRect(305, 0, 190, 520);

    ctx.strokeStyle = "#afc2c9";
    ctx.lineWidth = 2;
    ctx.setLineDash([14, 12]);

    ctx.beginPath();

    ctx.moveTo(0, 260);
    ctx.lineTo(305, 260);

    ctx.moveTo(495, 260);
    ctx.lineTo(800, 260);

    ctx.moveTo(400, 0);
    ctx.lineTo(400, 165);

    ctx.moveTo(400, 355);
    ctx.lineTo(400, 520);

    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = "#142731";
    ctx.fillRect(305, 165, 190, 190);
}


function drawSignal(x, y, isGreen) {
    ctx.fillStyle = "#0b1218";
    ctx.fillRect(x - 15, y - 15, 30, 30);

    ctx.beginPath();
    ctx.arc(x, y, 8, 0, Math.PI * 2);

    ctx.fillStyle = isGreen ? "#32dc9a" : "#ff5f6d";
    ctx.fill();
}


function drawCar(x, y, angle, color) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle);

    ctx.fillStyle = color;
    ctx.fillRect(-14, -8, 28, 16);

    ctx.fillStyle = "#c9eaff";
    ctx.fillRect(2, -5, 7, 10);

    ctx.fillStyle = "#101820";
    ctx.fillRect(-9, -10, 6, 3);
    ctx.fillRect(5, -10, 6, 3);
    ctx.fillRect(-9, 7, 6, 3);
    ctx.fillRect(5, 7, 6, 3);

    ctx.restore();
}


function drawLabel(text, x, y) {
    ctx.fillStyle = "#d7e6f8";
    ctx.font = "bold 14px Arial";
    ctx.fillText(text, x, y);
}


function drawQueuedVehicles() {
    if (!simulationState) {
        return;
    }

    const queues = simulationState.queues;

    // North → South: left-hand traffic uses x = 435.
    for (let i = 0; i < queues.north; i++) {
        drawCar(435, 135 - i * 30, Math.PI / 2, "#74a7ff");
    }

    // South → North: left-hand traffic uses x = 365.
    for (let i = 0; i < queues.south; i++) {
        drawCar(365, 385 + i * 30, -Math.PI / 2, "#b782ff");
    }

    // West → East: left-hand traffic uses y = 215.
    for (let i = 0; i < queues.west; i++) {
        drawCar(275 - i * 32, 215, 0, "#ffbd5a");
    }

    // East → West: left-hand traffic uses y = 305.
    for (let i = 0; i < queues.east; i++) {
        drawCar(525 + i * 32, 305, Math.PI, "#ff7180");
    }
}


function updateAndDrawMovingVehicles(deltaTime) {
    activeVehicles = activeVehicles.filter((vehicle) => {
        vehicle.progress += deltaTime / 1600;

        if (vehicle.progress < 0) {
            return true;
        }

        if (vehicle.progress >= 1) {
            return false;
        }

        const position = getPointOnPath(
            vehicle.path,
            vehicle.progress
        );

        const angle = getVehicleAngle(
            vehicle.path,
            vehicle.progress
        );

        drawCar(position.x, position.y, angle, vehicle.color);

        return true;
    });
}


function drawScene(deltaTime) {
    drawRoads();

    const northSouthGreen =
        simulationState &&
        simulationState.signal_phase === "NS_GREEN";

    drawSignal(470, 145, northSouthGreen);
    drawSignal(330, 375, northSouthGreen);

    drawSignal(285, 180, !northSouthGreen);
    drawSignal(515, 340, !northSouthGreen);

    drawQueuedVehicles();
    updateAndDrawMovingVehicles(deltaTime);

    if (simulationState) {
        drawLabel(`NORTH: ${simulationState.queues.north}`, 490, 30);
        drawLabel(`SOUTH: ${simulationState.queues.south}`, 490, 500);
        drawLabel(`WEST: ${simulationState.queues.west}`, 25, 145);
        drawLabel(`EAST: ${simulationState.queues.east}`, 650, 145);
    }
}


function animate(frameTime) {
    const deltaTime = Math.min(
        frameTime - previousFrameTime || 16,
        40
    );

    previousFrameTime = frameTime;

    drawScene(deltaTime);
    requestAnimationFrame(animate);
}


/* ---------------- BUTTON EVENTS ---------------- */

document.getElementById("pauseButton").addEventListener("click", () => {
    isRunning = !isRunning;

    document.getElementById("pauseButton").textContent =
        isRunning ? "Pause" : "Start";
});

document.getElementById("stepButton").addEventListener("click", () => {
    runTick();
});

document.getElementById("resetButton").addEventListener("click", () => {
    resetSimulation();
});


/* ---------------- START ---------------- */

loadState();

setInterval(() => {
    if (isRunning) {
        runTick();
    }
}, 1000);

requestAnimationFrame(animate);