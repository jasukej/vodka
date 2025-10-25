const Controls = ({ streaming, onToggleStream, connected }) => {
  return (
    <div className="flex gap-2.5 items-center p-5 bg-white rounded-lg shadow">
      <button
        onClick={onToggleStream}
        disabled={!connected}
        className={`px-5 py-2.5 text-base font-bold text-white border-0 rounded ${
          streaming ? 'bg-red-600' : 'bg-green-600'
        } ${connected ? 'cursor-pointer opacity-100' : 'cursor-not-allowed opacity-50'}`}
      >
        {streaming ? 'Stop Streaming' : 'Start Streaming'}
      </button>
      
      <div className="flex items-center gap-2 ml-auto">
        <div className={`w-2.5 h-2.5 rounded-full ${connected ? 'bg-green-600' : 'bg-red-600'}`} />
        <span className="text-sm text-gray-600">
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
    </div>
  );
};

export default Controls;

