"""
Web-based Real-time Monitoring Dashboard for APGI System

Provides a modern web interface for real-time monitoring of APGI system dynamics
using Flask, WebSockets, and interactive JavaScript visualizations.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np

# Optional imports for web functionality
try:
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO, emit

    WEB_DEPENDENCIES_AVAILABLE = True
except ImportError:
    WEB_DEPENDENCIES_AVAILABLE = False
    Flask = None
    SocketIO = None


class WebMonitor:
    """
    Web-based real-time monitoring dashboard for APGI system.

    Features:
    - Real-time data streaming via WebSockets
    - Interactive Plotly.js visualizations
    - Multiple synchronized time series plots
    - System state indicators and alerts
    - Data export capabilities
    - Responsive web interface
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5000,
        buffer_size: int = 1000,
        update_interval: float = 0.1,
    ):
        """
        Initialize web monitor.

        Args:
            host: Server host address
            port: Server port number
            buffer_size: Maximum number of data points to keep in memory
            update_interval: Update interval in seconds
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.update_interval = update_interval

        # Data buffers
        self.time_buffer: deque[float] = deque(maxlen=buffer_size)
        self.ignition_buffer: deque[int] = deque(maxlen=buffer_size)
        self.free_energy_buffer: deque[float] = deque(maxlen=buffer_size)
        self.precision_buffer: deque[float] = deque(maxlen=buffer_size)
        self.energy_reserves_buffer: deque[float] = deque(maxlen=buffer_size)
        self.coherence_buffer: deque[float] = deque(maxlen=buffer_size)

        # System state
        self.is_monitoring = False
        self.system_status = "Stopped"
        self.current_metrics: Dict[str, Any] = {}
        self.alerts: List[Dict[str, Any]] = []

        # Flask app setup
        self.app: Optional[Flask] = None
        self.socketio: Optional[SocketIO] = None

        if Flask:
            self.app = Flask(
                __name__,
                template_folder=str(Path(__file__).parent / "templates"),
                static_folder=str(Path(__file__).parent / "static"),
            )
            self.app.config["SECRET_KEY"] = "apgi_monitor_secret_key"
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Setup routes
        if self.app:
            self._setup_routes()
            self._setup_socketio_events()

        # Background thread for data updates
        self.update_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

    def _setup_routes(self) -> None:
        """Setup Flask routes."""

        @self.app.route("/")
        def index() -> str:
            """Main dashboard page."""
            return render_template("dashboard.html")

        @self.app.route("/api/status")
        def get_status() -> Any:
            """Get current system status."""
            return jsonify(
                {
                    "is_monitoring": self.is_monitoring,
                    "system_status": self.system_status,
                    "buffer_size": len(self.time_buffer),
                    "current_metrics": self.current_metrics,
                    "alerts": self.alerts[-10:],  # Last 10 alerts
                }
            )

        @self.app.route("/api/data")
        def get_data() -> Any:
            """Get current data for plotting."""
            return jsonify(
                {
                    "time": list(self.time_buffer),
                    "ignition_signal": list(self.ignition_buffer),
                    "free_energy": list(self.free_energy_buffer),
                    "precision": list(self.precision_buffer),
                    "energy_reserves": list(self.energy_reserves_buffer),
                    "coherence": list(self.coherence_buffer),
                }
            )

        @self.app.route("/api/export")
        def export_data() -> Any:
            """Export current data as JSON."""
            data = {
                "export_timestamp": datetime.now().isoformat(),
                "data": {
                    "time": list(self.time_buffer),
                    "ignition_signal": list(self.ignition_buffer),
                    "free_energy": list(self.free_energy_buffer),
                    "precision": list(self.precision_buffer),
                    "energy_reserves": list(self.energy_reserves_buffer),
                    "coherence": list(self.coherence_buffer),
                },
                "metadata": {
                    "buffer_size": self.buffer_size,
                    "total_points": len(self.time_buffer),
                    "system_status": self.system_status,
                },
            }
            return jsonify(data)

    def _setup_socketio_events(self) -> None:
        """Setup WebSocket event handlers."""

        @self.socketio.on("connect")
        def handle_connect() -> None:
            """Handle client connection."""
            print(f"Client connected: {request.sid}")
            emit(
                "status_update",
                {"is_monitoring": self.is_monitoring, "system_status": self.system_status},
            )

        @self.socketio.on("disconnect")
        def handle_disconnect() -> None:
            """Handle client disconnection."""
            print(f"Client disconnected: {request.sid}")

        @self.socketio.on("start_monitoring")
        def handle_start_monitoring() -> None:
            """Handle start monitoring request."""
            self.start_monitoring()
            emit(
                "status_update",
                {"is_monitoring": self.is_monitoring, "system_status": self.system_status},
                broadcast=True,
            )

        @self.socketio.on("stop_monitoring")
        def handle_stop_monitoring() -> None:
            """Handle stop monitoring request."""
            self.stop_monitoring()
            emit(
                "status_update",
                {"is_monitoring": self.is_monitoring, "system_status": self.system_status},
                broadcast=True,
            )

        @self.socketio.on("clear_data")
        def handle_clear_data() -> None:
            """Handle clear data request."""
            self.clear_buffers()
            emit("data_cleared", broadcast=True)

    def start_monitoring(self):
        """Start real-time monitoring."""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.system_status = "Running"
            self.stop_event.clear()

            # Start background update thread
            self.update_thread = threading.Thread(target=self._update_loop)
            self.update_thread.daemon = True
            self.update_thread.start()

            print("Real-time monitoring started")

    def stop_monitoring(self):
        """Stop real-time monitoring."""
        if self.is_monitoring:
            self.is_monitoring = False
            self.system_status = "Stopped"
            self.stop_event.set()

            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=1.0)

            print("Real-time monitoring stopped")

    def clear_buffers(self):
        """Clear all data buffers."""
        self.time_buffer.clear()
        self.ignition_buffer.clear()
        self.free_energy_buffer.clear()
        self.precision_buffer.clear()
        self.energy_reserves_buffer.clear()
        self.coherence_buffer.clear()
        self.alerts.clear()
        print("Data buffers cleared")

    def update_data(self, system_state: Dict[str, Any]):
        """
        Update monitoring data with new system state.

        Args:
            system_state: Current APGI system state dictionary
        """
        current_time = system_state.get("time", time.time() * 1000)

        # Extract key metrics
        ignition_signal = system_state.get("ignition", {}).get("total_signal", 0.0)
        free_energy = system_state.get("free_energy", {}).get("total_free_energy", 0.0)
        precision = system_state.get("precision", {}).get("mean_precision", 0.0)
        energy_reserves = system_state.get("metabolism", {}).get("current_reserves", 1.0)
        coherence = system_state.get("self_model", {}).get("coherence_score", 0.0)

        # Update buffers
        self.time_buffer.append(current_time)
        self.ignition_buffer.append(ignition_signal)
        self.free_energy_buffer.append(free_energy)
        self.precision_buffer.append(precision)
        self.energy_reserves_buffer.append(energy_reserves)
        self.coherence_buffer.append(coherence)

        # Update current metrics
        self.current_metrics = {
            "ignition_signal": ignition_signal,
            "free_energy": free_energy,
            "precision": precision,
            "energy_reserves": energy_reserves,
            "coherence": coherence,
            "ignition_occurred": system_state.get("ignition", {}).get("ignition_occurred", False),
        }

        # Check for alerts
        self._check_alerts(system_state)

        # Emit data update via WebSocket
        if self.is_monitoring:
            self.socketio.emit(
                "data_update",
                {
                    "time": current_time,
                    "metrics": self.current_metrics,
                    "alerts": self.alerts[-5:] if self.alerts else [],
                },
            )

    def _check_alerts(self, system_state: Dict[str, Any]):
        """Check for system alerts and warnings."""
        current_time = datetime.now().isoformat()

        # Low energy alert
        energy_reserves = system_state.get("metabolism", {}).get("current_reserves", 1.0)
        if energy_reserves < 0.2:
            alert = {
                "timestamp": current_time,
                "level": "warning" if energy_reserves > 0.1 else "critical",
                "message": f"Low energy reserves: {energy_reserves:.2%}",
                "metric": "energy_reserves",
                "value": energy_reserves,
            }
            self.alerts.append(alert)

        # High free energy alert
        free_energy = system_state.get("free_energy", {}).get("total_free_energy", 0.0)
        if free_energy > 5.0:
            alert = {
                "timestamp": current_time,
                "level": "warning",
                "message": f"High free energy: {free_energy:.2f}",
                "metric": "free_energy",
                "value": free_energy,
            }
            self.alerts.append(alert)

        # Low coherence alert
        coherence = system_state.get("self_model", {}).get("coherence_score", 0.0)
        if coherence < 0.3:
            alert = {
                "timestamp": current_time,
                "level": "info",
                "message": f"Low self-model coherence: {coherence:.2f}",
                "metric": "coherence",
                "value": coherence,
            }
            self.alerts.append(alert)

        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-50:]

    def _update_loop(self):
        """Background thread for periodic updates."""
        while not self.stop_event.is_set():
            try:
                # Emit periodic status updates
                self.socketio.emit(
                    "heartbeat",
                    {
                        "timestamp": datetime.now().isoformat(),
                        "buffer_size": len(self.time_buffer),
                        "system_status": self.system_status,
                    },
                )

                time.sleep(self.update_interval)

            except Exception as e:
                print(f"Error in update loop: {e}")
                break

    def create_dashboard_template(self):
        """Create the HTML dashboard template."""
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)

        dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APGI System Monitor</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .metric-card { margin-bottom: 20px; }
        .alert-panel { max-height: 300px; overflow-y: auto; }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .status-running { background-color: #28a745; }
        .status-stopped { background-color: #dc3545; }
        .plot-container { height: 300px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-12">
                <h1 class="mt-3 mb-4">
                    <span class="status-indicator" id="statusIndicator"></span>
                    APGI System Real-time Monitor
                </h1>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-8">
                <!-- Control Panel -->
                <div class="card mb-3">
                    <div class="card-body">
                        <h5 class="card-title">Control Panel</h5>
                        <button id="startBtn" class="btn btn-success me-2">Start Monitoring</button>
                        <button id="stopBtn" class="btn btn-danger me-2">Stop Monitoring</button>
                        <button id="clearBtn" class="btn btn-warning me-2">Clear Data</button>
                        <button id="exportBtn" class="btn btn-info">Export Data</button>
                        <span id="statusText" class="ms-3 fw-bold">Stopped</span>
                    </div>
                </div>
                
                <!-- Plots -->
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">Ignition Signal</div>
                            <div class="card-body">
                                <div id="ignitionPlot" class="plot-container"></div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">Free Energy</div>
                            <div class="card-body">
                                <div id="freeEnergyPlot" class="plot-container"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">Precision Dynamics</div>
                            <div class="card-body">
                                <div id="precisionPlot" class="plot-container"></div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">Energy Reserves</div>
                            <div class="card-body">
                                <div id="energyPlot" class="plot-container"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <!-- Current Metrics -->
                <div class="card metric-card">
                    <div class="card-header">Current Metrics</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6"><strong>Ignition:</strong></div>
                            <div class="col-6" id="currentIgnition">0.00</div>
                        </div>
                        <div class="row">
                            <div class="col-6"><strong>Free Energy:</strong></div>
                            <div class="col-6" id="currentFreeEnergy">0.00</div>
                        </div>
                        <div class="row">
                            <div class="col-6"><strong>Precision:</strong></div>
                            <div class="col-6" id="currentPrecision">0.00</div>
                        </div>
                        <div class="row">
                            <div class="col-6"><strong>Energy:</strong></div>
                            <div class="col-6" id="currentEnergy">100%</div>
                        </div>
                        <div class="row">
                            <div class="col-6"><strong>Coherence:</strong></div>
                            <div class="col-6" id="currentCoherence">0.00</div>
                        </div>
                    </div>
                </div>
                
                <!-- Alerts -->
                <div class="card">
                    <div class="card-header">System Alerts</div>
                    <div class="card-body alert-panel" id="alertsPanel">
                        <p class="text-muted">No alerts</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Initialize Socket.IO connection
        const socket = io();
        
        // Initialize plots
        const plotConfig = {responsive: true, displayModeBar: false};
        
        // Initialize empty plots
        Plotly.newPlot('ignitionPlot', [{x: [], y: [], type: 'scatter', mode: 'lines', name: 'Ignition Signal'}], {}, plotConfig);
        Plotly.newPlot('freeEnergyPlot', [{x: [], y: [], type: 'scatter', mode: 'lines', name: 'Free Energy'}], {}, plotConfig);
        Plotly.newPlot('precisionPlot', [{x: [], y: [], type: 'scatter', mode: 'lines', name: 'Precision'}], {}, plotConfig);
        Plotly.newPlot('energyPlot', [{x: [], y: [], type: 'scatter', mode: 'lines', name: 'Energy Reserves'}], {}, plotConfig);
        
        // Control buttons
        document.getElementById('startBtn').addEventListener('click', () => {
            socket.emit('start_monitoring');
        });
        
        document.getElementById('stopBtn').addEventListener('click', () => {
            socket.emit('stop_monitoring');
        });
        
        document.getElementById('clearBtn').addEventListener('click', () => {
            socket.emit('clear_data');
        });
        
        document.getElementById('exportBtn').addEventListener('click', () => {
            window.open('/api/export', '_blank');
        });
        
        // Socket event handlers
        socket.on('status_update', (data) => {
            updateStatus(data.is_monitoring, data.system_status);
        });
        
        socket.on('data_update', (data) => {
            updateMetrics(data.metrics);
            updatePlots(data.time, data.metrics);
            updateAlerts(data.alerts);
        });
        
        socket.on('data_cleared', () => {
            clearPlots();
        });
        
        // Update functions
        function updateStatus(isMonitoring, status) {
            const indicator = document.getElementById('statusIndicator');
            const statusText = document.getElementById('statusText');
            
            if (isMonitoring) {
                indicator.className = 'status-indicator status-running';
                statusText.textContent = 'Running';
            } else {
                indicator.className = 'status-indicator status-stopped';
                statusText.textContent = 'Stopped';
            }
        }
        
        function updateMetrics(metrics) {
            document.getElementById('currentIgnition').textContent = metrics.ignition_signal.toFixed(2);
            document.getElementById('currentFreeEnergy').textContent = metrics.free_energy.toFixed(2);
            document.getElementById('currentPrecision').textContent = metrics.precision.toFixed(2);
            document.getElementById('currentEnergy').textContent = (metrics.energy_reserves * 100).toFixed(1) + '%';
            document.getElementById('currentCoherence').textContent = metrics.coherence.toFixed(2);
        }
        
        function updatePlots(time, metrics) {
            const update = {
                x: [[time]],
                y: [[metrics.ignition_signal]]
            };
            Plotly.extendTraces('ignitionPlot', update, [0]);
            
            Plotly.extendTraces('freeEnergyPlot', {x: [[time]], y: [[metrics.free_energy]]}, [0]);
            Plotly.extendTraces('precisionPlot', {x: [[time]], y: [[metrics.precision]]}, [0]);
            Plotly.extendTraces('energyPlot', {x: [[time]], y: [[metrics.energy_reserves]]}, [0]);
        }
        
        function updateAlerts(alerts) {
            const alertsPanel = document.getElementById('alertsPanel');
            if (alerts.length === 0) {
                alertsPanel.innerHTML = '<p class="text-muted">No alerts</p>';
                return;
            }
            
            let html = '';
            alerts.forEach(alert => {
                const alertClass = alert.level === 'critical' ? 'alert-danger' : 
                                 alert.level === 'warning' ? 'alert-warning' : 'alert-info';
                html += `<div class="alert ${alertClass} alert-sm">${alert.message}</div>`;
            });
            alertsPanel.innerHTML = html;
        }
        
        function clearPlots() {
            Plotly.deleteTraces('ignitionPlot', 0);
            Plotly.deleteTraces('freeEnergyPlot', 0);
            Plotly.deleteTraces('precisionPlot', 0);
            Plotly.deleteTraces('energyPlot', 0);
            
            Plotly.addTraces('ignitionPlot', {x: [], y: [], type: 'scatter', mode: 'lines', name: 'Ignition Signal'});
            Plotly.addTraces('freeEnergyPlot', {x: [], y: [], type: 'scatter', mode: 'lines', name: 'Free Energy'});
            Plotly.addTraces('precisionPlot', {x: [], y: [], type: 'scatter', mode: 'lines', name: 'Precision'});
            Plotly.addTraces('energyPlot', {x: [], y: [], type: 'scatter', mode: 'lines', name: 'Energy Reserves'});
        }
    </script>
</body>
</html>
        """

        with open(template_dir / "dashboard.html", "w", encoding="utf-8") as f:
            f.write(dashboard_html)

    def run(self, debug: bool = False):
        """
        Start the web monitoring server.

        Args:
            debug: Enable Flask debug mode
        """
        # Create template if it doesn't exist
        self.create_dashboard_template()

        print(f"Starting APGI Web Monitor on http://{self.host}:{self.port}")
        print("Press Ctrl+C to stop the server")

        try:
            self.socketio.run(
                self.app, host=self.host, port=self.port, debug=debug, allow_unsafe_werkzeug=True
            )
        except KeyboardInterrupt:
            print("\nShutting down web monitor...")
            self.stop_monitoring()
        except Exception as e:
            print(f"Error running web monitor: {e}")

    def __del__(self):
        """Cleanup when monitor is destroyed."""
        self.stop_monitoring()


class MonitoringIntegration:
    """
    Integration helper for connecting APGI system to web monitor.
    """

    def __init__(self, monitor: WebMonitor):
        """
        Initialize monitoring integration.

        Args:
            monitor: WebMonitor instance
        """
        self.monitor = monitor
        self.is_connected = False

    def connect_system(self, apgi_system):
        """
        Connect APGI system to web monitor.

        Args:
            apgi_system: APGI system instance to monitor
        """
        # Add monitoring callback to system
        if hasattr(apgi_system, "add_monitor_callback"):
            apgi_system.add_monitor_callback(self.monitor.update_data)
            self.is_connected = True
            print("APGI system connected to web monitor")
        else:
            print("Warning: APGI system does not support monitoring callbacks")

    def disconnect_system(self, apgi_system):
        """
        Disconnect APGI system from web monitor.

        Args:
            apgi_system: APGI system instance to disconnect
        """
        if hasattr(apgi_system, "remove_monitor_callback"):
            apgi_system.remove_monitor_callback(self.monitor.update_data)
            self.is_connected = False
            print("APGI system disconnected from web monitor")

    def simulate_data(self, duration: float = 60.0, interval: float = 0.1):
        """
        Simulate APGI system data for testing the monitor.

        Args:
            duration: Simulation duration in seconds
            interval: Update interval in seconds
        """
        print(f"Starting data simulation for {duration} seconds...")

        start_time = time.time()
        step = 0

        while time.time() - start_time < duration:
            # Generate synthetic APGI system state
            current_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Simulate realistic system dynamics
            ignition_base = 1.0 + 0.5 * np.sin(step * 0.1)
            ignition_noise = 0.2 * np.random.randn()
            ignition_signal = max(0, ignition_base + ignition_noise)

            free_energy = 1.5 + 0.3 * np.cos(step * 0.05) + 0.1 * np.random.randn()
            precision = 0.7 + 0.2 * np.sin(step * 0.08) + 0.05 * np.random.randn()
            energy_reserves = max(0.1, 1.0 - step * 0.0001 + 0.02 * np.random.randn())
            coherence = 0.6 + 0.3 * np.sin(step * 0.03) + 0.05 * np.random.randn()

            # Create mock system state
            system_state = {
                "time": current_time,
                "ignition": {
                    "total_signal": ignition_signal,
                    "ignition_occurred": ignition_signal > 2.0,
                },
                "free_energy": {"total_free_energy": free_energy},
                "precision": {"mean_precision": precision},
                "metabolism": {"current_reserves": energy_reserves},
                "self_model": {"coherence_score": coherence},
            }

            # Update monitor
            self.monitor.update_data(system_state)

            step += 1
            time.sleep(interval)

        print("Data simulation completed")


# Example usage and testing
if __name__ == "__main__":
    # Create and run web monitor
    monitor = WebMonitor(host="localhost", port=5000)
    integration = MonitoringIntegration(monitor)

    # Start simulation in a separate thread
    import threading

    sim_thread = threading.Thread(target=integration.simulate_data, args=(300.0, 0.1))
    sim_thread.daemon = True
    sim_thread.start()

    # Run web server
    monitor.run(debug=True)
