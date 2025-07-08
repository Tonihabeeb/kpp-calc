Implementation Plan for KPP Simulator Fixes
 (Four Phases)
 Below is a phase-by-phase plan to implement the audit recommendations. Each phase is presented as a
 detailed prompt that can be given to GitHub Copilot, focusing on the specific tasks, files, and fixes needed.
 Following these phases in order will incrementally bring the simulator to an operational state.
 Phase 1: Fill Out Missing Server Modules
 Goal: Implement core server functionality for the backend API, WebSocket server, and master clock so the
 simulation can be started/stopped and state data streamed in real-time. The audit noted that these
 modules (
 app.py , 
main.py , 
realtime_sync_master_fixed.py ) were basically empty stubs . We
 will create the Flask API, WebSocket service, and synchronization clock as intended by the design (see ports/
 endpoints in the README) .
 2
 Files to update:
 3
 app.py , 
main.py , 
realtime_sync_master_fixed.py
 1. 
2. 
1
 app.py (Flask Backend on port 9100): Initialize a Flask app and integrate the simulation engine. 
Create a Flask application (
 app = Flask(__name__) ) and enable CORS (
 CORS(app) ) for cross
origin requests . 
1
 3. 
4. 
Instantiate the simulation engine at startup. For now, use 
SimulationEngine directly (we will
 wrap it with a thread-safe manager in the next phase). For example:
 engine = SimulationEngine(config=get_default_parameters())
 ◦ 
This uses default parameters for initial configuration. 
Endpoints: Implement RESTful endpoints to control and monitor the simulation: 
POST /start : Start the simulation by calling 
engine.start()
 4
 . If the simulation is
 already running, you can log or return a message indicating that. On success, return a JSON
 response like 
{"status": "running"} . 
◦ 
◦ 
POST /stop : Stop the simulation by calling 
{"status": "stopped"} or similar. 
5
 engine.stop() . Then return 
GET /status : Return the current simulation state by calling 
engine.get_state() and
 serializing it to JSON
 6
 . At minimum, this state should include whether the simulation is
 running and a timestamp. (The engine’s 
get_state currently provides 
timestamp , and an empty 
◦ 
is_running , 
components dict – that’s fine for now.) 
Parameter endpoints: Provide read-only access to default parameters and constraints so the
 UI can populate controls. For example, implement 
GET /parameters/defaults that
 returns 
get_default_parameters() (the default config values), and 
constraints that returns 
GET /parameters/
 get_parameter_constraints() (range or allowed values for
 each parameter). These leverage the imported schema functions in 
1
. This will enable the frontend to know slider ranges and
 config.parameter_schema
 default settings. 
◦ 
(Optional) 
7
 POST /parameters to accept a JSON of new parameter values. If you implement
 this, use 
validate_parameters_batch(request.json) to validate the input against the
 schema. If validation passes, update the engine’s configuration (or queue the update to apply
 in the simulation). For now, you might simply return a 200 OK if valid, as fully applying new
 parameters may require integration with the running engine (to be handled in a later phase
 or with ConfigManager). 
5. 
6. 
7. 
8. 
Ensure the Flask app is run when executing 
app.py . For example:
 if __name__ == "__main__":
 app.run(host="0.0.0.0", port=9100, threaded=True)
 8
 This will start the backend API server on port 9100 as specified in the README . Use 
threaded=True or similar to allow handling multiple requests (Flask’s default is already to run
 with threads, which is fine for our simple case). 
Logging: It’s good practice to set up logging (e.g., use Python’s 
logging module) to record when
 the simulation starts/stops or when endpoints are hit, but this is optional. The observability logs in
 the docs show an example of logging a “Simulation started successfully” message on /start , so
 you can add info logs for start/stop actions.
 9
 main.py (WebSocket Server on port 9101): Implement a server that streams simulation state to
 clients in real-time. 
10
 Use FastAPI (or Starlette) to create a WebSocket endpoint, since FastAPI is listed as a dependency
 . For example, create a FastAPI app:
 import asyncio, requests
 from fastapi import FastAPI, WebSocket
 app = FastAPI()
 Then define a websocket route:
 @app.websocket("/state")
 async def state_stream(websocket: WebSocket):
 await websocket.accept()
 try:
 while True:
 # fetch the latest state from the backend
 resp = requests.get("http://localhost:9100/status")
 state = resp.json()
 await websocket.send_json(state)
 await asyncio.sleep(0.033) # ~30 FPS
 except Exception:
 2
# If the client disconnects or error occurs, break out of loop
 await websocket.close()
 This will accept connections at 
ws://<host>:9101/state
 3
 updates ~30 times per second. We use the Flask API’s 
 and start sending JSON state
 /status endpoint to retrieve the state.
 (Alternatively, if the SimulationEngine could be shared, we’d use it directly, but since the WebSocket
 server might be a separate process, an HTTP call is the simplest integration.) 
9. 
10. 
11. 
12. 
13. 
Make sure to handle client disconnects. The 
except Exception (or more specifically 
WebSocketDisconnect ) should break the loop so we don’t try to send to a closed socket. 
You might include a simple health check for this service as well. For example, a root route 
could return something like 
11
 GET /
 {"status": "running"} or a message indicating the WS server is
 up . This is optional, but can be useful for quick checks (the observability doc suggests checking
 the WS server status via HTTP). 
Run the FastAPI app with Uvicorn when the script is executed:
 if __name__ == "__main__":
 import uvicorn
 uvicorn.run(app, host="0.0.0.0", port=9101)
 This ensures that running 
python main.py starts the WebSocket server on port 9101 as expected.
 Logging/Tracing (optional): The observability design includes trace IDs in each WS frame . We
 can ignore that for now, but keep in mind that after basic functionality, adding such metadata might
 be a future enhancement. For now, focus on getting the state flowing.
 12
 realtime_sync_master_fixed.py (Master Clock on port 9201): Implement the master clock
 service that synchronizes the simulation tick rate across components. 
14. 
Use FastAPI here as well (or even a simple 
◦ 
asyncio loop with websockets). A straightforward
 implementation: create a FastAPI app with two endpoints: 
GET /health : Returns 
{"status": "ok"} (HTTP 200) to indicate the master clock is
 running . 
13
 ◦ 
WebSocket /sync : When a client (e.g., the backend or the WS server) connects to 
/sync ,
 start sending out a tick message ~30 times per second. The message can be something
 simple like 
{"tick": <count>, "timestamp": <time>} . For example:
 from fastapi import FastAPI, WebSocket, WebSocketDisconnect
 import asyncio, time
 app = FastAPI()
 @app.websocket("/sync")
 async def sync_clock(websocket: WebSocket):
 await websocket.accept()
 tick = 0
 try:
 while True:
 tick += 1
 3
message = {"tick": tick, "timestamp": time.time()}
 await websocket.send_json(message)
 await asyncio.sleep(0.033) # 30 Hz
 except WebSocketDisconnect:
 # Client disconnected, end loop
 pass
 Maintain a 
tick counter and send it along with a timestamp. In a more advanced setup,
 you’d broadcast to multiple clients (e.g., keep a list of connected websockets and loop
 through them for each tick), but since this master clock might only have one or two clients,
 you can keep it simple or implement a broadcast if needed. 
15. 
16. 
Run this FastAPI app with Uvicorn on port 9201 when executed:
 if __name__ == "__main__":
 import uvicorn
 uvicorn.run(app, host="0.0.0.0", port=9201)
 Now, 
python realtime_sync_master_fixed.py will start the master clock server. 
Integration considerations: In the current step, we aren’t yet wiring the master clock into the
 simulation engine or WS server. Ultimately, the idea is that the backend API and WS server might 
subscribe to the master clock (via the 
/sync websocket) to know when to update or broadcast
 data. For now, simply having the master clock broadcasting ticks is sufficient to fulfill the audit
 recommendation. We can later decide if the backend should adjust its loop to sync with these ticks.
 At least, this implementation provides the mechanism and the health check endpoint.
 After Phase 1, we will have a running Flask API (start/stop/status), a WebSocket server streaming state, and
 a master clock broadcasting ticks. You can test this manually: start the three services in separate processes
 (per README order ), then use a WebSocket client (or the planned dashboard) to connect to 
2
 ws://
 localhost:9101/state and observe state updates. Also, hitting 
http://localhost:9100/status
 should return JSON state, and 
http://localhost:9201/health should return ok. The system’s basic
 external interfaces are now in place, addressing the missing server code noted in the audit.
 Phase 2: Complete Thread-Safe Engine and State Management
 Goal: Implement thread-safe mechanisms for the simulation engine so that concurrent access (between the
 simulation loop and API/WS threads) is handled safely. This involves creating a 
ThreadSafeEngine
 wrapper and a 
StateManager to synchronize state access. The audit found that thread-safety modules
 were stubbed out (e.g., 
thread_safe_engine.py and 
state_manager.py exist but are empty or just
 docstrings, and 
14
 app.py had to comment out using them) . We will now fill in these modules and
 integrate them with the engine.
 Files 
to update:
 simulation/managers/thread_safe_engine.py , 
state_manager.py , and update references in 
simulation/managers/
 app.py (and possibly elsewhere) to use the new thread
safe engine.
 1. 
Implement 
ThreadSafeEngine class (
 simulation/managers/thread_safe_engine.py ):
 4
2. 
This class will wrap a 
SimulationEngine instance and provide synchronized access. Begin by
 importing the necessary modules: 
import threading and any types from simulation (and config
 if needed). 
3. 
4. 
5. 
In 
◦ 
◦ 
◦ 
ThreadSafeEngine.__init__ , accept a config (perhaps the same dict you would pass to 
SimulationEngine ). Initialize: 
self.engine = SimulationEngine(config) – the actual simulation engine doing the
 work. 
self.lock = threading.Lock() – a mutex to guard access to the engine’s methods and
 state. 
self.state_manager = StateManager() – an instance to track the latest state (we’ll
 implement StateManager next).
 You might also set up any other needed tracking (e.g., a flag or condition variable if needed
 for more complex sync). 
Implement 
start() method: Use the lock to ensure only one thread can start/stop at a time. For
 example:
 def start(self):
 with self.lock:
 self.engine.start()
 We rely on 
SimulationEngine.start() to spawn its own thread for the simulation loop . (If
 we wanted, we could also have ThreadSafeEngine spawn a thread, but it’s simpler to delegate to the
 engine’s internal thread.) 
Implement 
stop() method similarly:
 def stop(self):
 with self.lock:
 self.engine.stop()
 15
 This will request the simulation loop to halt
 6. 
Implement 
5
 and join the thread. 
get_state() : Acquire the lock and get a consistent snapshot of the simulation state.
 There are two ways to do this:
 a) Direct approach: Call 
state = self.engine.get_state() inside the lock and return it. This
 ensures no updates occur during the read.
 b) Via StateManager: If we update the StateManager periodically, 
get_state() could simply
 return 
7. 
8. 
self.state_manager.get_state() . This might be more efficient if the state is large, to
 avoid recomputing it on each call. For now, you can use the direct approach or the state manager
 approach – we will set up StateManager in step 2. 
(Optional) Implement other proxy methods if needed, such as 
update_parameters(new_params) or properties to access components. For instance, if the UI
 wants to toggle H1/H2 features, a method here could call into the appropriate component. These
 can be added as needed. The main ones required are start/stop/get_state for now. 
Ensure that any call that interacts with 
self.engine is wrapped in 
with self.lock: to
 prevent race conditions. This makes the engine’s operations thread-safe when accessed from
 multiple threads (e.g., Flask thread calling stop while simulation thread is running).
 5
9. 
Implement 
StateManager class (
 simulation/managers/state_manager.py ):
 10. 
11. 
12. 
13. 
14. 
15. 
◦ 
The StateManager will hold the latest state of the simulation in a thread-safe way. Define a class
 with: 
an internal lock (
 threading.Lock() ), 
◦ 
a variable for the current state (initialize as 
Implement 
None or an empty dict). 
update_state(new_state: dict) : acquire the lock and copy or store the 
new_state . You might deep-copy the dict to be safe if it’s mutable and could be modified
 elsewhere, or if performance isn’t a concern. For now, even a shallow copy might suffice since our
 state dict is simple. Example:
 def update_state(self, new_state: dict):
 with self.lock:
 self._state = new_state.copy()
 Implement 
get_state() : acquire the lock and return a copy of the stored state (to ensure the
 caller can’t mutate the internal state). For example:
 def get_state(self)-> dict:
 with self.lock:
 return None if self._state is None else self._state.copy()
 If 
_state is not yet set, you might return 
None or 
could initialize state at start). 
{} . Choose what makes sense (the engine
 This manager could also track additional info (like last update timestamp, or a history of states if
 needed for debugging), but that’s optional. The primary purpose is to provide a safe snapshot of the
 latest simulation state.
 Integrate 
ThreadSafeEngine and 
StateManager with the SimulationEngine:
 ◦ 
We want the simulation’s loop to update the StateManager so that external threads (like the API or
 WS) can get the latest state without interfering. There are a couple of ways: 
Polling thread approach: After starting the simulation, spawn a separate thread that
 periodically (e.g., every 10 ms or 30 Hz) grabs 
engine.get_state() (protected by lock)
 and calls 
state_manager.update_state() with it. This decouples the state sampling
 from the simulation loop. You can start such a thread in 
ThreadSafeEngine.start() . For
 example, after 
self.engine.start() , start a daemon thread that runs: 
while self.engine.is_running:
 state = None
 with self.lock:
 state = self.engine.get_state()
 6
self.state_manager.update_state(state)
 time.sleep(0.033)
 This will continually refresh the stored state. Use a small sleep to avoid excessive CPU. 
◦ 
16. 
17. 
Callback approach: If modifying the 
SimulationEngine is feasible, you could alter its 
_update_simulation_state() to call a callback or update the StateManager directly
 each tick. For instance, pass the StateManager into the engine and inside 
_update_simulation_state , do 
state_manager.update_state(self.get_state()) . However, since 
SimulationEngine.get_state() may itself gather component states, calling it inside
 itself might be tricky if not properly implemented. The polling thread might be simpler given
 the current engine code. 
Either way, ensure that the state updates are done thread-safely (using the ThreadSafeEngine’s lock
 when reading from the engine). This guarantees we don’t read partial updates. 
Use ThreadSafeEngine in the Flask app: Now that ThreadSafeEngine is implemented, modify 
app.py to use it. For example:
 from simulation.managers.thread_safe_engine import ThreadSafeEngine
 engine = ThreadSafeEngine(config=get_default_parameters())
 Then update the routes: when a request comes in: 
◦ 
◦ 
◦ 
18. 
/start should call 
engine.start() (ThreadSafeEngine will handle locking internally). 
/stop calls 
engine.stop() . 
/status calls 
engine.get_state() – under the hood, this acquires the lock and either
 fetches from the real engine or from the StateManager’s latest copy. The response remains as
 before. 
Using the thread-safe wrapper means our Flask API won’t risk concurrent issues (like someone
 calling 
19. 
20. 
21. 
/stop exactly while the engine loop is updating). It also prepares us for future expansions
 where multiple threads (or even processes) might interact. 
StateManager usage: If you set up the polling thread or callback to populate StateManager, the 
engine.get_state() in ThreadSafeEngine could be replaced by 
self.state_manager.get_state() for efficiency. For now, you can keep it direct or use the
 manager – either approach will work. The key is that state access is locked and consistent. 
After this integration, test manually: Starting the simulation via the API should still work (and now be
 protected by locks). The WebSocket server (if still using HTTP polling to backend) will get the same
 data as before. We haven’t yet made the WS server subscribe to StateManager; it continues to call
 the 
/status endpoint, which in turn goes through ThreadSafeEngine. This means it’s indirectly
 thread-safe already, since 
/status now locks and gets state. So the WS updates remain consistent.
 (Optional) Improve simulation state detail: Currently, 
6
 SimulationEngine.get_state()
 returns a very basic structure . If there are accessible component states (environment,
 pneumatic, etc.), you could enhance 
get_state() to include them. For example, if
 self.environment 
exists, 
add 
something 
like 
"environment": 
self.environment.get_state() in the dict. Some components might have a method or at least
 properties we can expose. This isn’t strictly necessary for functionality, but it’s a possible
 7
improvement (ensuring the WebSocket clients get richer data). Make sure any such calls are also
 thread-safe via the ThreadSafeEngine. If it’s too early to do this (since many components might not
 have a 
get_state() ), you can skip it or just note it for future development. 
After Phase 2, the simulation engine is now safeguarded for concurrent access. The application uses
 ThreadSafeEngine , preventing race conditions between the simulation thread and external requests.
 The 
StateManager ensures we have the latest state readily available in a safe manner. We also resolve
 the import issues related to these managers (they are now implemented, so the previously commented
 import lines can be uncommented). The system architecture is closer to the intended design: a robust
 engine management layer that could support live parameter updates and complex interactions without
 threading issues.
 Phase 3: Add Functional Test Suite
 Goal: Introduce a comprehensive test suite to verify that the core components and new features work as
 expected. The audit noted a lack of real tests (only some fixtures and a trivial quick test were present). We
 will create unit and integration tests for configuration management, simulation components, and the API
 endpoints. This will help catch regressions and ensure the system meets its requirements. We’ll also use
 existing fixtures to avoid duplication, as maintaining the files without duplicating code is important.
 Files to update/add: Create new test modules under 
tests/ (e.g., 
test_engine.py , 
test_api.py , etc.), possibly update 
test_config.py , 
tests/conftest.py if needed to add
 f
 ixtures or utilities. We will not duplicate any existing test logic (e.g., if there’s a 
validation/tests/
 quick_test.py , we either build upon it or replace it with structured tests).
 1. 
Setup and Fixtures: Leverage 
tests/conftest.py for common fixtures. If 
defines fixtures like 
engine or 
conftest.py
 config objects, use them in our tests. For instance, if there’s a
 f
 ixture to provide a fresh 
SimulationEngine or load config files, that helps avoid repeating setup
 code. If no such fixtures exist yet for what we need, we can add some. For example, a fixture that
 starts the Flask app in testing mode and yields a test client, or a fixture that provides default
 parameters dict. Using fixtures will keep tests DRY (Don’t Repeat Yourself) and maintainable,
 addressing the “no duplications” requirement. 
2. 
3. 
Test Configuration Management: Verify that configs load and validate correctly. 
Default Parameters: Write a test to call 
get_default_parameters() (from 
config.parameter_schema ). The result should be a dict containing expected keys and values.
 Compare those values to known defaults from the README. For example:
 16
 defaults = get_default_parameters()
 assert defaults["num_floaters"] == 66 # per README recommended basic 
parameters
 assert defaults["air_pressure"] == 400000 # etc., check a few critical 
defaults
 8
This ensures our default config matches the documented expected values. 
4. 
5. 
6. 
7. 
8. 
9. 
10. 
11. 
Parameter Constraints: Call 
get_parameter_constraints() . This likely returns a dict of
 parameter names to their min/max or allowed ranges. Write assertions for a couple of parameters (if
 known). For instance, if we know from documentation or schema that 
"floater_volume" is
 between 0.1 and 1.0, check that. If such knowledge isn’t readily available, at least assert that the
 function returns non-empty and contains keys matching the default parameters. 
Batch Validation: If 
validate_parameters_batch is implemented, test it by providing a valid
 parameters dict vs an invalid one. E.g., a valid dict (like the defaults) should pass (function returns
 True or no exception), whereas a dict with an out-of-range value (e.g., 
"num_floaters": -5 )
 should either return False or raise an error. Assert the correct behavior. 
These tests confirm that the configuration subsystem (which is crucial for dynamic parameter
 updates) is working and that our default config is sane.
 Test Simulation Engine and Components: Ensure the simulation logic functions at a basic level. 
Engine Start/Stop: In 
test_engine.py , instantiate a 
ThreadSafeEngine or 
SimulationEngine (depending on what’s easier to import; 
ThreadSafeEngine is now our
 primary interface). Use a fixture if available to get an engine. Call 
engine.start() , then after a
 short delay (maybe sleep 50ms to allow the thread to run), verify 
engine.is_running becomes
 True
 17
 . Then call 
engine.stop() and verify 
is_running becomes False. Also ensure that
 calling 
stop when already stopped or 
start when running doesn’t cause errors (our
 implementation logs a warning, but should not throw). You can assert that multiple calls don’t
 change state beyond expected. 
Engine State: With the engine running for a short time, call 
returned dict has the keys 
engine.get_state() . Verify the
 "is_running" and 
"timestamp" (and possibly 
example:
 state = engine.get_state()
 assert state["is_running"] is True
 assert isinstance(state["timestamp"], float)
 "components" ). For
 If we extended state to include components, and if those components have predictable default
 values, we could test those too (e.g., if environment has a default pressure, check it). But since
 components might be mostly stubs or default, we can limit to basics. 
Environment Calculations: If 
simulation/components/environment.py has methods to
 compute properties (pressure, density, etc.), write targeted tests. For example, if there is a function
 or property for atmospheric pressure vs altitude, test a known scenario: at 0 m altitude, pressure ≈
 101325 Pa (sea-level standard). If altitude increases, pressure should decrease (we may not know the
 exact formula without looking at code, but perhaps test monotonic behavior or a rough expected
 range). Similarly, if environment tracks water density vs temperature, test that 4°C water is denser
 than 30°C water, etc., if those features exist. The idea is to validate the physics formula
 implementations against known physical facts. 
Pneumatic System: If 
PneumaticSystem (in 
simulation/components/pneumatics.py ) has
 functions like 
inject_air(volume) or similar, write tests for its behavior. Possibly, the code
 checks for exceeding pressure or tracks energy usage【?†L80-L158】. For instance, you might
 9
instantiate 
PneumaticSystem (with default config), call an inject method and assert that the
 internal state (pressure, tank level, etc.) changes as expected. If injecting beyond capacity is
 supposed to raise an exception or error, test that as well. Also test venting or compressor logic if
 accessible. 
12. 
13. 
14. 
15. 
16. 
17. 
18. 
Thread Safety (if feasible to test): Since ThreadSafeEngine primarily adds locking, a rigorous test
 would involve calling methods from multiple threads. This can be complex to automate, but you
 could simulate quick successive calls: e.g., start the engine in one thread and almost simultaneously
 call stop from the main thread, and assert that no race condition occurs (this is more about absence
 of errors than a specific state). Given the difficulty, this might be skipped, but it’s worth noting
 manually that our locks should prevent issues. 
Use fixtures for any heavy setup. For example, a fixture could yield a 
ThreadSafeEngine that’s
 already created (but not started), and ensure teardown stops it if it was started. This prevents
 duplicate code in start/stop tests and state tests.
 Test API Endpoints (Flask backend): Use Flask’s testing client to simulate HTTP requests to our new
 endpoints. 
In 
test_api.py , utilize Flask’s built-in test client. For example:
 import pytest
 from app import app # our Flask app
 @pytest.fixture
 def client():
 with app.test_client() as client:
 yield client
 This fixture provides a test client. (If our 
app.py constructs the engine at import time, it should be
 okay; the engine will be a ThreadSafeEngine which we can start/stop via endpoints.) 
/status endpoint: Initially, call 
GET /status on the client. Because the simulation hasn’t been
 started yet in this context, expect the response JSON 
"is_running": false (assuming default).
 Check that status code is 200 and JSON keys are present. For example:
 res = client.get("/status")
 data = res.get_json()
 assert res.status_code == 200
 assert data["is_running"] is False
 assert "timestamp" in data
 /start and /stop: Call 
POST /start via the client and ensure you get a 200 response. After 
start , call 
/status again and check 
that afterwards 
"is_running": true . Then call 
/status shows 
/
 POST /stop and verify
 "is_running": false again. Essentially, we’re testing the
 start/stop cycle through the API. Also, if the API returns a message in the JSON (like 
status: 
"running" ), we can assert those values. 
Parameter endpoints: If we implemented 
GET /parameters/defaults and 
constraints , test them as well. For example, hit 
/parameters/
 /parameters/defaults and compare the
 10
JSON to 
get_default_parameters() (which we can call in the test to get expected values).
 Similarly, 
19. 
20. 
21. 
22. 
23. 
24. 
/parameters/constraints should contain the keys and maybe min/max values 
ensure those keys match the defaults. 
Invalid input (if applicable): If we have 
POST /parameters for updating, try sending an out-of
range value. The expected behavior might be a 400 Bad Request or a JSON error message. Ensure
 the API responds correctly (e.g., does not crash; returns validation errors if we coded it to do so). 
These tests confirm that our Flask routes correctly interact with the engine. For example, the
 sequence of start → status → stop → status should show the engine was indeed started and
 stopped, indicating our ThreadSafeEngine and engine integration with Flask is working.
 Test WebSocket Server (optional/advanced): Testing WebSocket endpoints can be a bit more
 involved, but we can attempt a basic check: 
Use the 
websockets library or FastAPI’s 
TestClient with WebSocket support to connect to 
ws://localhost:9101/state . For example, FastAPI’s 
TestClient can open a WebSocket by 
client.websocket_connect("/state") . Since our WS server is running separately via Uvicorn,
 we might need to run it in a thread or subprocess for the test. This might be overkill for now, so an
 alternative is to refactor the WS server code to be testable (or just trust it if manual tests worked). 
If we do test it: start the 
main.app (FastAPI app) in the background, connect a WS client, receive a
 message or two, then close. Check that the received JSON has the keys 
state likely will show 
"is_running" , etc. The
 "is_running": false if the simulation wasn’t started, or true if it was (we
 could even start the simulation via the Flask client in the same test to see a live update). 
Due to complexity, you might skip automated WS testing. Instead, ensure via manual testing that it
 streams data. The presence of a comprehensive API and engine tests already gives confidence that if
 /status is correct, the WS just relays that. 
25. 
Test Master Clock (basic): If the master clock has a 
/health endpoint, you can test that with an
 HTTP client (e.g., Python 
requests.get("http://localhost:9201/health") ). In a test
 environment, you might launch the master clock server in a thread. Alternatively, since the master
 clock is simple, just test the FastAPI app directly by importing and using 
TestClient . If the
 FastAPI app is defined (e.g., 
app = FastAPI() in 
realtime_sync_master_fixed.py ), you can
 do:
 from realtime_sync_master_fixed import app as mc_app
 from fastapi.testclient import TestClient
 client = TestClient(mc_app)
 res = client.get("/health")
 assert res.status_code == 200
 assert res.json()["status"] == "ok"
 This ensures the health check responds as expected. Testing the 
/sync websocket of master clock
 would be similar to testing the WS server – we can skip detailed verification beyond perhaps
 ensuring the route exists (a 404 on connect would indicate we misnamed the route, for instance). 
11
Run the Test Suite: Execute 
26. 
pytest to run all tests. All tests should pass. If any fail, fix the
 corresponding code. For example, if the engine didn’t actually start on 
/start , figure out why
 (maybe we forgot to call thread-safe engine in the route). The tests effectively guide us to ensure
 each piece is properly integrated.
 By Phase 3, we will have a solid test suite covering: configuration defaults, engine start/stop behavior, key
 physics computations, and API contract (start/stop/status and parameter queries). We have made sure to
 use fixtures and not duplicate code between tests – common setup is shared, and each test focuses on one
 aspect. This dramatically improves the maintainability and reliability of the project: future changes can be
 validated against these tests to catch any breaks in functionality.
 Phase 4: Remove Stray Files and Final Cleanup
 Goal: Clean up the repository by removing unused or placeholder files and fixing minor issues (like package
 initialization and formatting) identified by the audit. This phase ensures the codebase is tidy and free of
 known structural problems (such as missing 
__init__.py causing import errors, or leftover zero-byte
 f
 iles). We will maintain all essential files and improve them, but eliminate duplicates or no-op files that only
 add confusion.
 Tasks:
 1. 
2. 
3. 
4. 
5. 
6. 
7. 
Delete or implement placeholder modules: The audit pointed out several modules that are
 essentially empty stubs. These include files under 
simulation/physics/ for advanced
 hypotheses and possibly others in 
simulation/logging/ . For example: 
simulation/physics/nanobubble_physics.py – meant for the H1 nanobubble feature ,
 but if it’s currently empty (0 bytes or just a placeholder), remove it. The H1 functionality is partly
 implemented in other areas (the audit mentioned a 
18
 Fluid subsystem handles effective density), so
 an empty module is not needed. 
simulation/physics/thermal_physics.py – meant for H2 thermal enhancement, but if it’s
 unused/empty, remove it. 
simulation/physics/pulse_controller.py – meant for H3 pulse-coast control, also remove if
 not implemented. 
simulation/logging/data_logger.py – if this file is a stub (the audit mentioned it as zero
length), remove it as well.
 Before deletion, do a quick search in the repository to ensure nothing imports these modules. Given
 they were empty, likely nothing critical relies on them. By removing them, we reduce “dead code”
 and avoid developers mistakenly thinking there’s functionality where there is none. (If in the future
 these features are to be added, they can be reintroduced properly.) 
Also remove any other obviously unused files. The audit mentioned “stray zero‑byte files and
 obsolete reports”. Check for any files named oddly (e.g., an empty file named 
utputFormat was
 hinted). If such files exist in the repo, delete them. They serve no purpose and might have been
 created by error. 
Check the 
docs/ or project root for large JSON or HTML analysis reports (like those
 PhaseX_summary.md or .json files). These may have been generated by analysis tools. If they are not
 needed in version control (likely not, as they reference specific runs and paths), consider removing
 them to declutter. At the very least, remove any that are empty or clearly not useful to maintain. (If
 12
the team wants to keep some audit reports for reference, that’s fine, but anything that’s basically
 noise should go.)
 8. 
9. 
10. 
11. 
12. 
13. 
14. 
15. 
16. 
17. 
18. 
Fix package initialization (
 __init__.py files): A critical issue found was that imports like
 kpp_simulator.config.core were failing, meaning the 
kpp_simulator package (and/or its
 subpackages) lacked 
__init__.py . To fix this: 
Add an empty 
__init__.py file in the 
kpp_simulator/ directory. Also add one in 
kpp_simulator/config/ and 
kpp_simulator/config/core/ if those directories exist. This
 will ensure Python recognizes these as packages and can import modules inside them. For instance,
 after this, an import of 
kpp_simulator.config.core.some_module will work (where previously
 it raised ModuleNotFoundError). 
Double-check the 
simulation/ package and subpackages as well. Most likely 
already had 
simulation/
 __init__.py since we could import from it. But ensure 
simulation/managers/
 has an 
__init__.py (so that our new ThreadSafeEngine class can be imported via 
simulation.managers.thread_safe_engine ). If missing, add it. 
No actual code needs to go in these 
__init__ files (unless we want to expose certain top-level
 symbols), but a module docstring or a brief comment indicating the package name is fine. The main
 point is their presence. 
After adding these, try running the tests or simply doing 
import kpp_simulator.config.core
 in a Python shell within the repo – it should succeed (even if core has nothing or just re-exports from
 config/ , at least it won’t error).
 Requirements and formatting fixes:
 Open 
requirements.txt and ensure the last line ends with a newline character. This is a minor
 formatting issue (some tools or shells may concatenate the last line with the prompt if newline is
 missing). Add a 
\n at the end of the file if it’s not already there. 
Verify that all necessary dependencies are listed in 
requirements.txt . We introduced FastAPI
 and Uvicorn in our implementation. If they weren’t already in the file, add 
(and possibly 
fastapi and 
uvicorn
 websockets if we explicitly used it, though we used 
requests which should
 already be there, and Python’s stdlib for threading/asyncio which don’t need listing). Also, ensure 
pytest is in 
requirements-dev.txt or similar (if there is a dev requirements file for testing
 tools). The summary mentioned PyYAML was added earlier – just ensure nothing is missing. This will
 prevent module import errors when others install the project. 
Check if any dependency is duplicated or conflicting between 
requirements.txt and
 requirements-dev.txt . The audit’s summary suggested they updated installation instructions to
 combine dev and runtime requirements. Ensure our documentation (README or CONTRIBUTING)
 reflects the correct way to install all dependencies (maybe one pip install command for both files).
 This is a documentation task, but since we are cleaning up, it’s good to have it consistent.
 Final verification:
 Run the full test suite (
 pytest ) after all changes. All tests added in Phase 3 should pass now. If any
 test fails due to path issues (for example, if we removed a placeholder module that a test was
 13
importing), update the test or remove that import. Ideally, tests should only target actual
 functionality; after removal of stubs, tests should target the remaining code. 
19. 
20. 
21. 
22. 
23. 
◦ 
Perform a manual integration test of the system: start the master clock, backend API, and WS server
 as before. Ensure that: 
The backend API (
 app.py ) launches without import errors (our 
__init__.py fixes should
 have solved the 
kpp_simulator.config import issue). 
◦ 
◦ 
The endpoints still function (try hitting 
/status , 
/start etc. via curl or browser). 
The WebSocket server (
 main.py ) launches and you can connect to 
ws://localhost:
 9101/state (using a tool or browser script) and see state JSON coming through. 
◦ 
The master clock (
 realtime_sync_master_fixed.py ) launches and its 
/health
 responds. (If you have a WS client, you could also test connecting to 
/sync to see tick
 messages, but at least ensure no immediate errors on start.) 
Check the console outputs for any exceptions or errors. For example, if the WS server tries to fetch
 from the Flask server before it’s up, you might see connection errors – in practice, one would start
 the master clock first, then backend, then WS, so following that order should avoid issues. 
Confirm that removing the files in step 1 did not break anything. If something was referencing them
 (say 
simulation/physics/__init__.py tried to import nanobubble_physics), remove those
 import lines as well. We want a clean run with no 
ImportError for missing modules. 
With everything running, it’s also wise to glance at resource usage (30 Hz updates should be fine, not
 consuming 100% CPU in one thread). Our sleep intervals should throttle loops. If any loop is too
 tight (e.g., missing a sleep), consider adding a small delay to avoid hogging CPU. This is more of a
 tuning note. 
Finally, update documentation if needed: For example, if we removed placeholder features (H1/H2/
 H3 stub modules), ensure the README doesn’t instruct users to toggle something that isn’t there yet.
 However, since the README described features conceptually, it’s okay – just know that not all are fully
 implemented (which is fine as long as the app doesn’t error out). Possibly note in a CHANGELOG or
 in commit messages which files were removed and why, for transparency.
 By Phase 4, the repository will be cleaner and more robust. We will have removed dead code and ensured
 all 
modules are properly initialized and referenced. The import issue reported in tests
 (kpp_simulator.config.core not found) will be resolved by the added 
__init__.py files, and the
 requirements formatting issue will be fixed. In summary, after this cleanup, the KPP simulator codebase
 should run the intended services without errors, all tests pass, and developers (or GitHub Copilot) can
 navigate the project without stumbling over incomplete or duplicate pieces. The project is now in a good
 position for further development or deployment, having addressed the immediate gaps identified by the
 audit. 
1
 7
 14
 app.py
 https://github.com/Tonihabeeb/kpp-calc/blob/8c02a82ab86efe686aca463058b50afa395446b8/app.py
 2
 3
 8
 10
 13
 16
 18
 README.md
 https://github.com/Tonihabeeb/kpp-calc/blob/8c02a82ab86efe686aca463058b50afa395446b8/README.md
 4
 5
 6
 15
 17
 engine.py
 https://github.com/Tonihabeeb/kpp-calc/blob/8c02a82ab86efe686aca463058b50afa395446b8/simulation/engine.py
 9
 11
 12
 OBSERVABILITY_README.md
 https://github.com/Tonihabeeb/kpp-calc/blob/8c02a82ab86efe686aca463058b50afa395446b8/OBSERVABILITY_README.md
 14