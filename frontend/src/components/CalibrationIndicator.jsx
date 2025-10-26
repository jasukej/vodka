import { useEffect, useState } from 'react';

const CalibrationIndicator = ({ status, segmentCount, autoHide = true }) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (status === 'success' && autoHide) {
      const timer = setTimeout(() => {
        setVisible(false);
      }, 2000);
      return () => clearTimeout(timer);
    } else {
      setVisible(true);
    }
  }, [status, autoHide]);

  if (!visible) {
    return null;
  }

  const getStatusContent = () => {
    switch (status) {
      case 'calibrating':
        return {
          bg: 'bg-blue-600/80',
          border: 'border-blue-400/20',
          icon: (
            <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ),
          text: 'Calibrating...',
          showCount: false
        };
      case 'success':
        return {
          bg: 'bg-green-600/80',
          border: 'border-green-400/20',
          icon: (
            <svg className="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
          ),
          text: 'Calibrated',
          showCount: true
        };
      case 'error':
        return {
          bg: 'bg-red-600/80',
          border: 'border-red-400/20',
          icon: (
            <svg className="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          ),
          text: 'Calibration Failed',
          showCount: false
        };
      default:
        return null;
    }
  };

  const content = getStatusContent();
  if (!content) return null;

  return (
    <div className={`${content.bg} backdrop-blur-sm ${content.border} border px-4 py-2 rounded-lg flex items-center gap-2 text-white text-sm font-medium transition-all`}>
      {content.icon}
      <span>{content.text}</span>
      {content.showCount && segmentCount !== null && (
        <span className="text-white/80 text-xs">({segmentCount} surfaces)</span>
      )}
    </div>
  );
};

export default CalibrationIndicator;

