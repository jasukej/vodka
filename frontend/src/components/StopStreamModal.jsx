import { useState } from 'react';

const StopStreamModal = ({ isOpen, onClose, onSave, onDiscard, onFinalSave, videoUrl, frames, showLink, shareLink }) => {
  const [isLoading, setIsLoading] = useState(false);
  
  if (!isOpen) return null;

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await onSave();
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(shareLink).then(() => {
      console.log('Link copied to clipboard');
    });
  };

  return (
    <div 
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div 
        className="bg-black/90 backdrop-blur-xl rounded-2xl border border-white/10 p-8 max-w-2xl w-full mx-4 shadow-2xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-2xl font-bold text-white mb-4">
          {showLink ? 'Video Saved' : 'Stop Streaming?'}
        </h2>

        {frames.length > 0 && !showLink && (
          <div className="mb-6">
            <div className="bg-white/5 rounded-lg overflow-hidden border border-white/10">
              <img 
                src={frames[0]} 
                alt="Video preview" 
                className="w-full h-auto"
              />
            </div>
          </div>
        )}

        {videoUrl && showLink && (
          <div className="mb-6">
            <div className="bg-white/5 rounded-lg overflow-hidden border border-white/10">
              <img 
                src={videoUrl} 
                alt="Saved video" 
                className="w-full h-auto"
              />
            </div>
          </div>
        )}

        {showLink && shareLink && (
          <div className="bg-white/5 rounded-lg border border-white/10 p-4 mb-6">
            <p className="text-white/70 text-xs mb-2 text-left">Share Link:</p>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={shareLink}
                className="flex-1 px-3 py-2 bg-black/50 border border-white/20 rounded text-white text-sm"
              />
              <button
                onClick={copyToClipboard}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-all border border-green-400/20 flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span className="text-xs font-bold">Copy</span>
              </button>
            </div>
          </div>
        )}

        {!showLink && (
          <p className="text-white/70 mb-6 text-sm">
            Save your drum kit performance?
          </p>
        )}

        <div className="flex items-center gap-3">
          {!showLink ? (
            <>
              <button
                onClick={handleSave}
                disabled={isLoading}
                className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-lg transition-all border border-green-400/20 flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Saving...</span>
                  </>
                ) : (
                  'Save & Publish'
                )}
              </button>
              
              <button
                onClick={onDiscard}
                className="p-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all border border-red-400/20"
                title="Discard"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </>
          ) : (
            <button
              onClick={onFinalSave}
              className="w-full px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg transition-all border border-green-400/20"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default StopStreamModal;

