import { useEffect, useState } from 'react';

const BLEControlPanel = ({ socketService, connected }) => {
  const [bleStatus, setBleStatus] = useState({
    available: false,
    connected: false,
    scanning: false,
    device_address: null,
    total_hits: 0,
    battery_level: 0,
    uptime: 0
  });
  const [threshold, setThreshold] = useState(15.0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (!socketService.socket || !connected) return;

    // Listen for BLE events
    socketService.on('ble_status', (data) => {
      setBleStatus(prev => ({ ...prev, ...data }));
    });

    socketService.on('ble_scan_started', () => {
      setBleStatus(prev => ({ ...prev, scanning: true }));
    });

    socketService.on('ble_scan_stopped', () => {
      setBleStatus(prev => ({ ...prev, scanning: false }));
    });

    socketService.on('ble_error', (data) => {
      console.error('BLE Error:', data.message);
      alert(`BLE Error: ${data.message}`);
    });

    socketService.on('ble_command_sent', (data) => {
      console.log('BLE Command sent:', data);
    });

    socketService.on('drumstick_status', (data) => {
      console.log('Drumstick Status:', data);
      setBleStatus(prev => ({
        ...prev,
        total_hits: data.total_hits || prev.total_hits,
        battery_level: data.battery || prev.battery_level,
        uptime: data.uptime || prev.uptime
      }));
    });

    socketService.on('sensor_connected', (data) => {
      if (data.type === 'BLE') {
        setBleStatus(prev => ({ ...prev, connected: true }));
      }
    });

    socketService.on('sensor_disconnected', (data) => {
      if (data.type === 'BLE') {
        setBleStatus(prev => ({ ...prev, connected: false }));
      }
    });

    // Get initial status
    socketService.emit('ble_get_status');

    return () => {
      socketService.off('ble_status');
      socketService.off('ble_scan_started');
      socketService.off('ble_scan_stopped');
      socketService.off('ble_error');
      socketService.off('ble_command_sent');
      socketService.off('drumstick_status');
      socketService.off('sensor_connected');
      socketService.off('sensor_disconnected');
    };
  }, [socketService, connected]);

  const handleStartScan = () => {
    socketService.emit('ble_start_scan');
  };

  const handleStopScan = () => {
    socketService.emit('ble_stop_scan');
  };

  const handleCalibrate = () => {
    socketService.emit('ble_calibrate');
  };

  const handleSetThreshold = () => {
    socketService.emit('ble_set_threshold', { threshold });
  };

  const handleResetStats = () => {
    if (confirm('Reset hit counter and statistics?')) {
      socketService.emit('ble_reset_stats');
    }
  };

  const getConnectionStatusColor = () => {
    if (bleStatus.connected) return 'bg-green-600';
    if (bleStatus.scanning) return 'bg-yellow-600';
    return 'bg-red-600';
  };

  const getConnectionStatusText = () => {
    if (bleStatus.connected) return 'Connected';
    if (bleStatus.scanning) return 'Scanning...';
    return 'Disconnected';
  };

  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (!connected) return null;

  return (
    <div className="fixed top-20 right-4 z-50">
      <button
        onClick={() => setIsVisible(!isVisible)}
        className={`mb-2 px-3 py-1 ${getConnectionStatusColor()} hover:opacity-80 text-white text-xs rounded-lg backdrop-blur-sm border border-white/20 flex items-center gap-2`}
      >
        <div className="w-2 h-2 rounded-full bg-white"></div>
        🔵 BLE {getConnectionStatusText()} {isVisible ? '▼' : '▶'}
      </button>

      {isVisible && (
        <div className="bg-black/90 backdrop-blur-md border border-white/20 rounded-xl p-4 w-80">
          <div className="mb-3">
            <h3 className="text-white font-bold text-sm mb-2">BLE Drumstick Control</h3>

            {!bleStatus.available && (
              <div className="text-red-400 text-xs mb-2">
                ⚠️ BLE not available on backend
              </div>
            )}
          </div>

          {/* Connection Status */}
          <div className="mb-4 p-2 rounded-lg bg-white/5 border border-white/10">
            <div className="text-xs text-white/70 mb-1">Connection Status</div>
            <div className={`text-sm font-medium ${
              bleStatus.connected ? 'text-green-400' :
              bleStatus.scanning ? 'text-yellow-400' : 'text-red-400'
            }`}>
              {getConnectionStatusText()}
            </div>
            {bleStatus.device_address && (
              <div className="text-xs text-white/50">
                {bleStatus.device_address}
              </div>
            )}
          </div>

          {/* Connection Controls */}
          <div className="mb-4 space-y-2">
            {!bleStatus.connected && !bleStatus.scanning && (
              <button
                onClick={handleStartScan}
                disabled={!bleStatus.available}
                className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:opacity-50 text-white text-sm rounded-lg"
              >
                🔍 Start BLE Scan
              </button>
            )}

            {bleStatus.scanning && (
              <button
                onClick={handleStopScan}
                className="w-full px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg"
              >
                ⏹️ Stop Scan
              </button>
            )}
          </div>

          {/* Device Status */}
          {bleStatus.connected && (
            <div className="mb-4 space-y-2">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-white/5">
                  <div className="text-white/70">Hits</div>
                  <div className="text-white font-mono">{bleStatus.total_hits}</div>
                </div>
                <div className="p-2 rounded bg-white/5">
                  <div className="text-white/70">Battery</div>
                  <div className="text-white font-mono">{bleStatus.battery_level.toFixed(1)}V</div>
                </div>
                <div className="p-2 rounded bg-white/5 col-span-2">
                  <div className="text-white/70">Uptime</div>
                  <div className="text-white font-mono">{formatUptime(bleStatus.uptime)}</div>
                </div>
              </div>
            </div>
          )}

          {/* Controls */}
          {bleStatus.connected && (
            <div className="space-y-3">
              <div className="space-y-2">
                <label className="text-xs text-white/70">Impact Threshold</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    min="5"
                    max="50"
                    step="0.5"
                    value={threshold}
                    onChange={(e) => setThreshold(parseFloat(e.target.value))}
                    className="flex-1 px-2 py-1 bg-white/10 border border-white/20 rounded text-white text-sm"
                  />
                  <button
                    onClick={handleSetThreshold}
                    className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white text-xs rounded"
                  >
                    Set
                  </button>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleCalibrate}
                  className="flex-1 px-3 py-2 bg-orange-600 hover:bg-orange-700 text-white text-xs rounded"
                >
                  🔧 Calibrate
                </button>
                <button
                  onClick={handleResetStats}
                  className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-xs rounded"
                >
                  🔄 Reset Stats
                </button>
              </div>
            </div>
          )}

          <div className="mt-3 pt-2 border-t border-white/10">
            <div className="text-xs text-white/70">
              BLE provides lower latency and power consumption vs WebSocket
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BLEControlPanel;