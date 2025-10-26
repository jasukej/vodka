import { useState } from 'react';

const MaterialClassificationDebug = ({ calibrationData, lastHit }) => {
  const [isVisible, setIsVisible] = useState(false);

  if (!calibrationData || !calibrationData.segments) return null;

  const successfulClassifications = calibrationData.segments.filter(s => s.material !== 'unknown').length;
  const totalSegments = calibrationData.segments.length;
  const successRate = ((successfulClassifications / totalSegments) * 100).toFixed(1);

  const getSuccessColor = (rate) => {
    if (rate > 70) return 'text-green-400';
    if (rate > 40) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="fixed top-4 left-4 z-50">
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="mb-2 px-3 py-1 bg-purple-600/80 hover:bg-purple-600 text-white text-xs rounded-lg backdrop-blur-sm border border-purple-400/20"
      >
        🔬 Material Debug {isVisible ? '▼' : '▶'}
      </button>

      {isVisible && (
        <div className="bg-black/90 backdrop-blur-md border border-white/20 rounded-xl p-4 w-96 max-h-96 overflow-y-auto">
          <div className="mb-3">
            <h3 className="text-white font-bold text-sm mb-2">Classification Results</h3>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-white/70">Success Rate:</span>
              <span className={`font-bold ${getSuccessColor(successRate)}`}>
                {successRate}% ({successfulClassifications}/{totalSegments})
              </span>
            </div>
          </div>

          <div className="space-y-2">
            {calibrationData.segments.map((segment) => (
              <div
                key={segment.id}
                className={`p-2 rounded-lg border ${
                  segment.material === 'unknown'
                    ? 'bg-red-900/20 border-red-500/30'
                    : 'bg-green-900/20 border-green-500/30'
                } ${lastHit?.segment_id === segment.id ? 'ring-2 ring-yellow-400' : ''}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white text-xs font-medium">
                    #{segment.id} {segment.class_name}
                  </span>
                  <span className={`text-xs ${
                    segment.material === 'unknown' ? 'text-red-400' : 'text-green-400'
                  }`}>
                    {segment.material === 'unknown' ? '❌' : '✅'}
                  </span>
                </div>

                <div className="text-xs text-white/70 grid grid-cols-2 gap-1">
                  <span>Material: <span className="text-white">{segment.material}</span></span>
                  <span>Conf: <span className="text-white">{(segment.confidence * 100).toFixed(1)}%</span></span>
                  <span>Size: <span className="text-white">{segment.bbox[2]}×{segment.bbox[3]}</span></span>
                  <span>Area: <span className="text-white">{segment.area || 0}</span></span>
                </div>

                {lastHit?.segment_id === segment.id && (
                  <div className="mt-1 text-xs text-yellow-400">
                    🎯 Last Hit
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-3 pt-2 border-t border-white/10">
            <div className="text-xs text-white/70">
              <div>Object-aware classification enabled</div>
              <div>Fallback logic for low confidence</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MaterialClassificationDebug;