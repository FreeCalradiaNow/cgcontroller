# CropsGrowController MVP - Kanban Backlog

## CHUNK 1: Environment & System Initialization (Infra)

- [ ] **Task 1.1: Headless OS Setup & Memory Optimization**
  *Description:* Flash Raspberry Pi OS Lite (64-bit). Configure Wi-Fi, enable SSH, and set hostname to `cropsgrowcontroller.local` via Pi Imager. Modify `/etc/fstab` to mount a volatile RAM disk (`tmpfs`) at `/tmp/grow_ram/` with a maximum size of 50MB to shield the SD card from live writes.
- [x] **Task 1.2: Project Directory & Python VirtualEnv**
  *Description:* Create project root directory `/home/pi/cropsgrowcontroller/`. Initialize a Python 3 virtual environment (`python3 -m venv venv`). Create `requirements.txt` containing: `fastapi`, `uvicorn`, `pydantic`, `adafruit-circuitpython-sht4x`, `adafruit-circuitpython-pca9685`.
- [x] **Task 1.3: Shared Data Models Definition**
  *Description:* Created `cropsgrowcontroller/models/` package with Pydantic v2 models: `LiveState` (+ nested `SensorTelemetry`, `ActuatorState`, `ControlStatus`) for `live.json`, `SystemConfig` for `config.json`, and `KlimaLogRecord` + `KLIMA_LOG_DDL` for the SQLite `klima_log` table. Path constants live in `cropsgrowcontroller/paths.py`.

## CHUNK 2: The Core Daemon & Hardware Integration (`controller_core.py`)

- [ ] **Task 2.1: I2C Multiplexer & Dual SHT Probe Fetching**
  *Description:* Implement code to initialize the TCA9548A I2C multiplexer. Write routines to read temperature and humidity from Channel 0 (Probe 1 - Canopy) and Channel 1 (Probe 2 - Intake). Calculate averaged values and compute the live VPD using the Magnus formula with a default `leaf_temp_offset = 2.0`.
- [ ] **Task 2.2: Level-Shifter & AeroZesh G8 PWM Control**
  *Description:* Implement hardware PWM control on GPIO 18 using the native Linux/Raspberry Pi hardware clock. Map a 0-100% duty-cycle integer input to the specific pulse widths required by the AeroZesh EC motor (leveraging the 5V level shifter output).
- [ ] **Task 2.3: PCA9685 & XLED 720W 0-10V Dimming Loop**
  *Description:* Implement I2C communication with the PCA9685 PWM module. Write a translation layer that takes a 0-100% light intensity variable and scales it to the required duty cycle for the physical PWM-to-0-10V analog converter connected to the XLED 720W driver.

## CHUNK 3: Automation Logic & Fallbacks

- [ ] **Task 3.1: Sunrise & Sunset Software Timer Ramp**
  *Description:* Implement a background timer checking system time against `light_on_time` and `light_off_time`. Write a 30-minute stepping routine: linearly ramp up light intensity from 0% to 100% at morning trigger, and ramp down from 100% to 0% at night trigger.
- [ ] **Task 3.2: Cascaded Climate Control Logic (RH over VPD)**
  *Description:* Implement the main control loop evaluation: If `avg_rh` > `max_rh` (e.g., 65%), override VPD and force fan to 80% (dehumidification). If `avg_rh` < `min_rh` (e.g., 40%), override VPD and force fan to 15% (moisture retention). If RH is stable, adjust fan speed dynamically (+/- steps) to match `target_vpd`.
- [ ] **Task 3.3: Defensive Exception Handling & Defensive Defs**
  *Description:* Wrap hardware I/O reads in strict `try-except` blocks. If I2C polling fails 3 consecutive times, trigger Emergency Mode: update state to alert, write 0% to PCA9685 (turn off lights to mitigate heat), and break PWM to GPIO 18 (letting the AeroZesh internal pull-up hardware autarkically max out at 100% for odor control).

## CHUNK 4: Caching, Interprocess Communication & SQLite Batching

- [ ] **Task 4.1: Volatile JSON State Broadcasting**
  *Description:* At the end of every `controller_core.py` loop execution (5-second intervals), serialize the current telemetry to `/tmp/grow_ram/live.json`. Read incoming manual overrides or target setting adjustments from `/tmp/grow_ram/config.json`.
- [ ] **Task 4.2: SQLite RAM-Disk Logging**
  *Description:* Initialize an SQLite database schema inside the volatile directory: `/tmp/grow_ram/grow_live.db`. Write a single row entry containing the compiled telemetry payload into the `klima_log` table on every loop iteration.
- [ ] **Task 4.3: 12-Hour SD Card Batch Synchronization Job**
  *Description:* Implement an asynchronous thread or cron-like timer within the core loop running every 12 hours. Open a connection to the physical database `/home/pi/grow_archive.db`. Read all rows from `/tmp/grow_ram/grow_live.db`, execute a bulk bulk-insert transaction to the SD card database, and clear the volatile database rows.

## CHUNK 5: The Backend & Web-API REST Layer (`backend_api.py`)

- [ ] **Task 5.1: FastAPI Server Setup & Routing**
  *Description:* Initialize the FastAPI application instance. Configure endpoints: `GET /api/live` (reads `/tmp/grow_ram/live.json`), `POST /api/settings` (validates payloads via Pydantic and overwrites `/tmp/grow_ram/config.json`).
- [ ] **Task 5.2: Historical Analytics API Query**
  *Description:* Implement endpoint `GET /api/history?hours=X`. Query the active local SQLite database (merging data from the RAM database and the SD-card archive) to output historical arrays of data as JSON for charting.
- [ ] **Task 5.3: Linux Systemd Integration (Auto-Boot)**
  *Description:* Create `cropsgrowcontroller_core.service` and `cropsgrowcontroller_api.service` files in `/etc/systemd/system/`. Configure dependencies so both services boot headlessly, run under the `pi` user context using the virtual environment, and auto-restart immediately if an unhandled crash or power-cut recovery occurs.

## CHUNK 6: Frontend Client Web UI (`/frontend`)

- [ ] **Task 6.1: Responsive HTML5/CSS3 Dark-Mode Shell**
  *Description:* Create `index.html` and `style.css`. Design a modern, mobile-friendly Grid/Flexbox dashboard interface showcasing live gauges (Temp, RH, VPD, Fan %, Light %). Avoid all external CSS frameworks.
- [ ] **Task 6.2: Vanilla JS Polling Engine & AJAX Controls**
  *Description:* Create `script.js`. Implement an asynchronous `fetch()` loop running every 2000ms against `GET /api/live` to surgically replace element text contents without page flickering. Bind EventListeners to settings input elements (sliders/input fields) to push instantaneous JSON payloads using `POST /api/settings`.

