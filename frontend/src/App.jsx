import { useState, useEffect } from 'react';
import { useSocket } from './hooks/useSocket';
import WebcamStream from './components/WebcamStream';
import Visualizer from './components/Visualizer';
import HitIndicator from './components/HitIndicator';
import DrumPad from './components/DrumPad';
import './App.css';

function App() {
  const { connected, socketService } = useSocket();
  const [streaming, setStreaming] = useState(false);
  const [hits, setHits] = useState([]);
  const [lastHit, setLastHit] = useState(null);
  const [frameCount, setFrameCount] = useState(0);

  useEffect(() => {
    if (socketService.socket) {
      socketService.on('hit_detected', (data) => {
        console.log('Hit detected:', data);
        const newHit = { ...data, timestamp: Date.now() };
        setHits(prev => [...prev, newHit]);
        setLastHit(newHit);
      });

      socketService.on('drum_position', (data) => {
        console.log('Drum position:', data);
      });
    }

    return () => {
      if (socketService.socket) {
        socketService.off('hit_detected');
        socketService.off('drum_position');
      }
    };
  }, [socketService]);

  const handleToggleStream = () => {
    setStreaming(!streaming);
  };

  const handleFrameCapture = () => {
    setFrameCount(prev => prev + 1);
  };

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black">
      <header className="absolute top-0 left-0 right-0 z-50 flex items-center justify-between p-6 bg-gradient-to-b from-black/80 to-transparent">
        <h1 className="text-lg font-bold text-white">🥁 VODKA - Virtual Offline Drum Kit Application</h1>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-white/90">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          <button
            onClick={handleToggleStream}
            disabled={!connected}
            className={`px-6 py-2 text-sm font-bold text-white border-0 rounded-lg transition-all ${
              streaming ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'
            } ${connected ? 'cursor-pointer opacity-100' : 'cursor-not-allowed opacity-50'}`}
          >
            {streaming ? 'Stop Streaming' : 'Start Streaming'}
          </button>
        </div>
      </header>

      <div className="absolute inset-0">
        <WebcamStream 
          streaming={streaming}
          onFrameCapture={handleFrameCapture}
          fps={10}
        />
      </div>

      <div className="absolute top-24 right-6 z-40 flex flex-col gap-4 w-80">
        <HitIndicator lastHit={lastHit} />
        <Visualizer hits={hits} />
      </div>

      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-40">
        <div className="bg-black/60 backdrop-blur-md px-6 py-4 rounded-xl border border-white/10">
          <h3 className="mb-3 text-sm font-bold text-white/90 text-center">Drum Pads</h3>
          <div className="flex gap-3">
            <DrumPad name="Snare" position="center" active={lastHit?.drum === 'snare'} />
            <DrumPad name="Kick" position="bottom" active={lastHit?.drum === 'kick'} />
            <DrumPad name="Hi-Hat" position="top" active={lastHit?.drum === 'hihat'} />
          </div>
        </div>
      </div>

      {streaming && (
        <div className="absolute bottom-6 right-6 z-40 px-3 py-2 bg-black/60 backdrop-blur-md rounded-lg border border-white/10">
          <span className="text-xs text-white/80">
            Frames: {frameCount}
          </span>
        </div>
      )}
    </div>
  );
}

export default App;
