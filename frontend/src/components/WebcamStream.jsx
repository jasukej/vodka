import { useEffect, useRef } from 'react';
import { useWebcam } from '../hooks/useWebcam';
import socketService from '../services/socketService';

const WebcamStream = ({ onFrameCapture, streaming, fps = 10 }) => {
  const { videoRef, isStreaming, error, startWebcam, stopWebcam, captureFrame } = useWebcam();
  const intervalRef = useRef(null);

  useEffect(() => {
    if (streaming && isStreaming && socketService.isConnected()) {
      intervalRef.current = setInterval(() => {
        const frameData = captureFrame();
        if (frameData) {
          socketService.sendFrame(frameData);
          if (onFrameCapture) {
            onFrameCapture(frameData);
          }
        }
      }, 1000 / fps);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [streaming, isStreaming, fps, captureFrame, onFrameCapture]);

  useEffect(() => {
    if (streaming) {
      startWebcam();
    } else {
      stopWebcam();
    }
  }, [streaming]);

  return (
    <div className="relative w-full h-full">
      {error && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 text-white px-4 py-3 bg-red-600/90 backdrop-blur-sm rounded-lg border border-red-400/20">
          Error: {error}
        </div>
      )}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover bg-black"
        style={{ transform: 'scaleX(-1)' }}
      />
      {isStreaming && (
        <div className="absolute top-6 left-6 bg-red-600/80 backdrop-blur-sm text-white px-3 py-1.5 rounded-full text-xs font-bold border border-red-400/20 flex items-center gap-1.5">
          <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
          LIVE
        </div>
      )}
    </div>
  );
};

export default WebcamStream;

