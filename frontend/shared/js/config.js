/**
 * Frontend Configuration
 * Centralized configuration for the application
 */

const CONFIG = {
  // API Configuration
  api: {
    baseUrl: window.location.protocol === 'https:'
      ? `https://${window.location.host}`
      : `http://${window.location.hostname}:8000`,

    wsUrl: window.location.protocol === 'https:'
      ? `wss://${window.location.host}`
      : `ws://${window.location.hostname}:8000`,
  },

  // WebSocket Configuration
  websocket: {
    reconnectInterval: 3000,      // 3 seconds
    maxReconnectAttempts: 10,
    heartbeatInterval: 30000,     // 30 seconds
    connectionTimeout: 10000,     // 10 seconds
  },

  // Session Configuration
  session: {
    storageKey: 'gametime_session',
    roomCodeKey: 'gametime_room_code',
    playerNameKey: 'gametime_player_name',
  },

  // UI Configuration
  ui: {
    animationDuration: 300,       // milliseconds
    toastDuration: 3000,          // 3 seconds
    toastErrorDuration: 5000,     // 5 seconds
    roomCodeLength: 4,
    maxPlayerNameLength: 50,
    minPlayerNameLength: 1,
  },

  // Room Configuration
  room: {
    minPlayers: 2,
    maxPlayers: 12,
    defaultMaxPlayers: 12,
  },

  // Environment
  env: {
    isDevelopment: window.location.hostname === 'localhost',
    isProduction: window.location.hostname !== 'localhost',
  },

  // Logging
  logging: {
    enabled: true,
    level: window.location.hostname === 'localhost' ? 'debug' : 'error',
  },
};

// Freeze configuration to prevent modifications
Object.freeze(CONFIG);
Object.freeze(CONFIG.api);
Object.freeze(CONFIG.websocket);
Object.freeze(CONFIG.session);
Object.freeze(CONFIG.ui);
Object.freeze(CONFIG.room);
Object.freeze(CONFIG.env);
Object.freeze(CONFIG.logging);

export default CONFIG;
