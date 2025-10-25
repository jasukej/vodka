const Visualizer = ({ hits = [] }) => {
  return (
    <div className="p-5 bg-black/40 backdrop-blur-md rounded-xl min-h-[140px] border border-white/10">
      <h3 className="mb-3 text-sm font-bold text-white/90">Hit Visualizer</h3>
      <div className="text-xs text-white/70">
        {hits.length === 0 ? (
          <p className="text-white/40">No hits detected yet...</p>
        ) : (
          <ul className="list-none p-0 space-y-1">
            {hits.slice(-5).reverse().map((hit, idx) => (
              <li key={idx} className="py-1 px-2 bg-white/5 rounded">
                Hit at {new Date(hit.timestamp).toLocaleTimeString()}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default Visualizer;

