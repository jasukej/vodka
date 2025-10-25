import { useState, useEffect } from 'react';

const HitIndicator = ({ lastHit }) => {
  const [flash, setFlash] = useState(false);

  useEffect(() => {
    if (lastHit) {
      setFlash(true);
      const timer = setTimeout(() => setFlash(false), 300);
      return () => clearTimeout(timer);
    }
  }, [lastHit]);

  return (
    <div className={`p-5 rounded-xl transition-all duration-300 text-center backdrop-blur-md border ${
      flash 
        ? 'bg-yellow-400/90 border-yellow-300/50 shadow-[0_0_30px_rgba(250,204,21,0.5)]' 
        : 'bg-black/40 border-white/10'
    }`}>
      <h3 className={`mb-2.5 text-sm font-bold ${flash ? 'text-black' : 'text-white/90'}`}>
        Hit Detector
      </h3>
      <div className={`text-3xl font-bold ${flash ? 'text-black' : 'text-white/50'}`}>
        {flash ? '🥁 HIT!' : 'Waiting...'}
      </div>
    </div>
  );
};

export default HitIndicator;

