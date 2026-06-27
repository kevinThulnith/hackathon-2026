# 🪐 Zeta-26 Relic Ring Protocol

**Launch26 Hackathon - IEEE CS University of Kelaniya**

## 📖 Executive Summary

The Relic Ring Protocol is a highly resilient, physics-based network routing simulation built to reconnect the fragmented Zeta-26 star system. Following the Hyper-Flare of 3704, this system dynamically calculates routing paths across legacy subsurface fiber rings and laser void transmissions, handling planetary data dialects (Codex translations) and hardware failures in real-time.

---

## 🚀 Key Features (Milestones Achieved)

- **M1: Universe Initialization:** Fully dynamic parsing of `universe-config.json`. No planetary values are hardcoded.
- **M2: Multi-Hop Proof:** Accurate numerical base conversion mapping internal ASCII representation to the required outbound Codex dialects.
- **M3: Latency Breakdown:** A rigorous mathematical physics engine calculating exact Subsurface Fiber Transit ($T_p$), Processing Delay, Atmospheric Refraction, and Void Transmission ($T_v$).
- **M4: Chaos Resilience:** Real-time state management integrated with Dijkstra's algorithm to instantly route around dead nodes/links without dropping packets.

---

## 🛠️ Tech Stack

- **Backend Core:** Python 3 (optimal for math, trigonometry, and graph algorithms)
- **API Framework:** Django (lightweight app structure via `manage.py`)
- **Package Manager:** `uv` (for lightning-fast virtual environment management)

---

## ⚙️ Setup & Running Instructions

### 1. Prerequisites

Ensure you have Python 3.10+ and `uv` installed on your system.

### 2. Environment Setup

Clone the repository and install the dependencies:

```bash
# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install required packages
uv add django django-cors-headers requests
```

### 3. Running the Server

Ensure `universe-config.json` is located in the root directory alongside `manage.py`.

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/api/`.

### 4. Running the Automated Tests

We have included a test suite that programmatically proves all Milestones (including the Chaos Test). In a separate terminal, run:

```bash
uv run test.py
```

## Docker execution

create `.env` on project root and this data.

```sh
# Postgres Settings
POSTGRES_DB=hackathonDatabase
POSTGRES_USER=hackathonDbUser
POSTGRES_PASSWORD=hackathonDB4080

# Redis Settings
REDIS_HOST=hackathon-redis
REDIS_CACHE_DB=1
REDIS_PORT=6379
REDIS_ADDR=redis://hackathon-redis:6379

# Database Settings
DATABASE_ENGINE=postgresql_psycopg2
DATABASE_NAME=hackathonDatabase
DATABASE_USERNAME=hackathonDbUser
DATABASE_PASSWORD=hackathonDB4080
DATABASE_HOST=hackathon-database
DATABASE_PORT=5432
DATABASE_URL=postgresql://hackathonDbUser:hackathonDB4080@hackathon-database:5432/hackathonDatabase
DATA_SOURCE_NAME=postgresql://hackathonDbUser:hackathonDB4080@hackathon-database:5432/hackathonDatabase?sslmode=disable

# Backend Settings
DEBUG=False
API_PORT=8000
JWT_SECRET=%rb#(d#^1g1vrivi08v%_bhkim6rn1i#sf%y$)%*e$$ynsjjat
SECRET_KEY=tl5$^=@msts_q4=^3et%$@kgmwctj=)5c%kkzima#tq-2o9lcl
CORS_ORIGINS=http://localhost,http://host.docker.internal,http://host.docker.internal:80
ALLOWED_HOSTS=localhost,host.docker.internal,127.0.0.1,localhost:5173,localhost:8000,127.0.0.1:8000,127.0.0.1:5173,
```

execute all services

```sh
docker-compose up -d --build
```

---

## 📐 Justification of Assumed Constants & Physics Math

As per the technical requirements, the system strictly adheres to the provided physics formulas and system assumptions:

**Void Distance ($L$) & Line of Sight:**
Distance $L$ is calculated using the center-to-center mathematical distance minus planetary radii and atmospheres. The Line-of-Sight tower pairing calculates the geometric angle between planets and snaps to the nearest available tower (Top = 0°, increasing clockwise). This determines the internal crust routing ($T_p$) but does not artificially alter the $L$ distance, satisfying the "Void Distance Simplification" rule.

**Atmospheric Transit:**
The atmospheric distance is handled as exactly $h$ for both the origin and destination planets regardless of transmission angle, satisfying the "Atmospheric Transit Distance Simplification" rule.

**Internal Crust Transit Time ($T_p$):**
The algorithm dynamically calculates the shortest path along the fiber ring (clockwise vs counter-clockwise). If the entry tower equals the exit tower, deduplication logic is applied ($s=0, m=1$). Processing delay ($7\text{ms}$) is calculated accurately based on the distinct towers hit.

**Graph Routing Constraints:**
Dijkstra's shortest-path algorithm is strictly constrained by $L_{max} = 50{,}000{,}000$ km. Any neighbor node exceeding this threshold is excluded from edge relaxation.

---

## 📡 API Reference

| Endpoint         | Method | Payload / Action                                                                                                        |
| ---------------- | ------ | ----------------------------------------------------------------------------------------------------------------------- |
| `/api/universe/` | `GET`  | Returns the loaded universe grid and planetary constants.                                                               |
| `/api/route/`    | `POST` | Takes `origin`, `destination`, and `payload`. Returns the optimal route and strict Packet Schema (including `hop_log`). |
| `/api/toggle/`   | `POST` | Takes `node_id` and `action` (`'kill'`/`'revive'`). Updates routing graph state.                                        |

---

## 💻 Frontend Development Steps (Next Phase)

To successfully demonstrate the visual requirements of the 10–15 minute demo video, a frontend visualization will be developed with the following steps:

### Step 1: Canvas / Web UI Setup

Build a lightweight `index.html` using Vanilla JS and the HTML5 `<canvas>` API (or React/D3.js for advanced rendering). Enable `django-cors-headers` on the backend to allow API requests from the frontend UI.

### Step 2: Render the Universe (Milestone 1)

Fetch `/api/universe/` on page load. Iterate through the `nodes` object and draw 2D circles representing planets. Coordinates $(x, y)$ will be scaled down appropriately to fit the screen viewport. Plot the active towers dynamically around the circumference of each planet.

### Step 3: Implement the Routing Dashboard (Milestones 2 & 3)

Create a UI form with dropdowns for Origin and Destination, and a text input for the Payload. On submission, POST to `/api/route/`.

- **Visualization:** Draw a colored, animated line passing through the `path_taken` array to visually prove the route.
- **Log Panel:** Render the `hop_log` JSON to the screen, showing the dialect conversions (Base 5, Base 14, etc.) and breaking down the latency per component ($T_p$, $T_v$).

### Step 4: The Chaos Interface (Milestone 4)

Add a click event listener (or a "Kill Switch" button) to the rendered planets. Clicking a planet sends a POST to `/api/toggle/` to kill it. Visually turn the planet red/gray on the UI. Resend the exact same packet payload and visually prove the routing path dynamically diverging around the dead node.
