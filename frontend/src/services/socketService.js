import { io } from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
  }

  connect(url = 'http://localhost:5001') {
    if (this.socket?.connected) {
      return this.socket;
    }

    this.socket = io(url, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });

    this.socket.on('connect', () => {
      console.log('Connected to server');
      this.connected = true;
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from server');
      this.connected = false;
    });

    this.socket.on('connection_response', (data) => {
      console.log('Connection response:', data);
    });

    this.socket.on('error', (error) => {
      console.error('Socket error:', error);
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  emit(event, data) {
    if (this.socket && this.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('Socket not connected. Cannot emit event:', event);
    }
  }

  on(event, callback) {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event, callback) {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  sendFrame(frameData) {
    this.emit('video_frame', { frame: frameData, timestamp: Date.now() });
  }

  isConnected() {
    return this.connected;
  }
}

const socketService = new SocketService();

if (typeof window !== 'undefined') {
  window.socketService = socketService;
  
  window.simulateHit = (intensity = 500, x = null, y = null) => {
    const hitData = {
      intensity,
      timestamp: Date.now()
    };
    if (x !== null && y !== null) {
      hitData.position = { x, y };
    }
    
    if (!socketService.isConnected()) {
      console.warn('⚠️  Socket not connected yet. Hit may not be processed.');
    }
    
    socketService.emit('simulate_hit', hitData);
    console.log('🥁 Hit simulated:', hitData);
  };
  
  window.testPositions = () => {
    console.log('%c Testing hit positions...', 'font-size: 14px; font-weight: bold; color: purple');
    console.log('This will test 4 random positions and show backend logs');
    
    const positions = [
      { x: 150, y: 150 },
      { x: 400, y: 200 },
      { x: 200, y: 350 },
      { x: 320, y: 240 }
    ];
    
    positions.forEach((pos, i) => {
      setTimeout(() => {
        console.log(`\nTest ${i + 1}: Position (${pos.x}, ${pos.y})`);
        simulateHit(500, pos.x, pos.y);
      }, i * 1500);
    });
    
    console.log('\nCheck backend terminal for detailed mapping logs!');
  };
}

export default socketService;

