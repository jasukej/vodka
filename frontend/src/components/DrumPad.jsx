const DrumPad = ({ name, position, active }) => {
  return (
    <div className={`inline-flex items-center justify-center w-20 h-20 rounded-xl text-white text-sm font-bold cursor-pointer transition-all duration-200 border ${
      active 
        ? 'bg-blue-500 border-blue-300/50 shadow-[0_0_25px_rgba(59,130,246,0.6)] scale-110' 
        : 'bg-white/10 border-white/20 hover:bg-white/15'
    }`}>
      {name}
    </div>
  );
};

export default DrumPad;

