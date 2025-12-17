/**
 * Utility Functions
 * Common helper functions used across the application
 */

import CONFIG from './config.js';

/**
 * Session Storage Utilities
 */
export const storage = {
  /**
   * Get session ID from localStorage
   * @returns {string|null} Session ID or null
   */
  getSessionId() {
    return localStorage.getItem(CONFIG.session.storageKey);
  },

  /**
   * Set session ID in localStorage
   * @param {string} sessionId - Session ID to store
   */
  setSessionId(sessionId) {
    localStorage.setItem(CONFIG.session.storageKey, sessionId);
  },

  /**
   * Clear session ID from localStorage
   */
  clearSessionId() {
    localStorage.removeItem(CONFIG.session.storageKey);
  },

  /**
   * Get room code from localStorage
   * @returns {string|null} Room code or null
   */
  getRoomCode() {
    return localStorage.getItem(CONFIG.session.roomCodeKey);
  },

  /**
   * Set room code in localStorage
   * @param {string} roomCode - Room code to store
   */
  setRoomCode(roomCode) {
    localStorage.setItem(CONFIG.session.roomCodeKey, roomCode);
  },

  /**
   * Clear room code from localStorage
   */
  clearRoomCode() {
    localStorage.removeItem(CONFIG.session.roomCodeKey);
  },

  /**
   * Get player name from localStorage
   * @returns {string|null} Player name or null
   */
  getPlayerName() {
    return localStorage.getItem(CONFIG.session.playerNameKey);
  },

  /**
   * Set player name in localStorage
   * @param {string} playerName - Player name to store
   */
  setPlayerName(playerName) {
    localStorage.setItem(CONFIG.session.playerNameKey, playerName);
  },

  /**
   * Clear player name from localStorage
   */
  clearPlayerName() {
    localStorage.removeItem(CONFIG.session.playerNameKey);
  },

  /**
   * Clear all session data
   */
  clearAll() {
    this.clearSessionId();
    this.clearRoomCode();
    this.clearPlayerName();
  },
};

/**
 * Validation Utilities
 */
export const validators = {
  /**
   * Validate room code format
   * @param {string} code - Room code to validate
   * @returns {boolean} True if valid
   */
  isValidRoomCode(code) {
    if (!code) return false;
    const trimmed = code.trim().toUpperCase();
    return /^[A-Z0-9]{4}$/.test(trimmed);
  },

  /**
   * Validate player name
   * @param {string} name - Player name to validate
   * @returns {boolean} True if valid
   */
  isValidPlayerName(name) {
    if (!name) return false;
    const trimmed = name.trim();
    return (
      trimmed.length >= CONFIG.ui.minPlayerNameLength &&
      trimmed.length <= CONFIG.ui.maxPlayerNameLength
    );
  },

  /**
   * Sanitize player name
   * @param {string} name - Player name to sanitize
   * @returns {string} Sanitized name
   */
  sanitizePlayerName(name) {
    return name
      .trim()
      .slice(0, CONFIG.ui.maxPlayerNameLength)
      .replace(/[^\x20-\x7E]/g, ''); // Remove non-printable characters
  },

  /**
   * Sanitize room code
   * @param {string} code - Room code to sanitize
   * @returns {string} Sanitized code
   */
  sanitizeRoomCode(code) {
    return code
      .trim()
      .toUpperCase()
      .replace(/[^A-Z0-9]/g, '')
      .slice(0, CONFIG.ui.roomCodeLength);
  },
};

/**
 * DOM Utilities
 */
export const dom = {
  /**
   * Create element with attributes and children
   * @param {string} tag - HTML tag name
   * @param {Object} attrs - Attributes object
   * @param {Array|string} children - Child elements or text
   * @returns {HTMLElement} Created element
   */
  createElement(tag, attrs = {}, children = []) {
    const element = document.createElement(tag);

    // Set attributes
    Object.entries(attrs).forEach(([key, value]) => {
      if (key === 'className') {
        element.className = value;
      } else if (key === 'dataset') {
        Object.entries(value).forEach(([dataKey, dataValue]) => {
          element.dataset[dataKey] = dataValue;
        });
      } else if (key.startsWith('on') && typeof value === 'function') {
        const eventName = key.slice(2).toLowerCase();
        element.addEventListener(eventName, value);
      } else {
        element.setAttribute(key, value);
      }
    });

    // Add children
    const childArray = Array.isArray(children) ? children : [children];
    childArray.forEach((child) => {
      if (typeof child === 'string') {
        element.appendChild(document.createTextNode(child));
      } else if (child instanceof HTMLElement) {
        element.appendChild(child);
      }
    });

    return element;
  },

  /**
   * Show element
   * @param {HTMLElement} element - Element to show
   */
  show(element) {
    if (element) {
      element.classList.remove('hidden');
    }
  },

  /**
   * Hide element
   * @param {HTMLElement} element - Element to hide
   */
  hide(element) {
    if (element) {
      element.classList.add('hidden');
    }
  },

  /**
   * Toggle element visibility
   * @param {HTMLElement} element - Element to toggle
   */
  toggle(element) {
    if (element) {
      element.classList.toggle('hidden');
    }
  },
};

/**
 * Time Utilities
 */
export const time = {
  /**
   * Sleep for specified milliseconds
   * @param {number} ms - Milliseconds to sleep
   * @returns {Promise} Promise that resolves after sleep
   */
  sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  },

  /**
   * Format timestamp to time string
   * @param {number} timestamp - Unix timestamp
   * @returns {string} Formatted time string
   */
  formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  },
};

/**
 * Logging Utilities
 */
export const logger = {
  /**
   * Log debug message
   * @param {...any} args - Arguments to log
   */
  debug(...args) {
    if (CONFIG.logging.enabled && CONFIG.logging.level === 'debug') {
      console.log('[DEBUG]', ...args);
    }
  },

  /**
   * Log info message
   * @param {...any} args - Arguments to log
   */
  info(...args) {
    if (CONFIG.logging.enabled) {
      console.log('[INFO]', ...args);
    }
  },

  /**
   * Log warning message
   * @param {...any} args - Arguments to log
   */
  warn(...args) {
    if (CONFIG.logging.enabled) {
      console.warn('[WARN]', ...args);
    }
  },

  /**
   * Log error message
   * @param {...any} args - Arguments to log
   */
  error(...args) {
    if (CONFIG.logging.enabled) {
      console.error('[ERROR]', ...args);
    }
  },
};

/**
 * API Utilities
 */
export const api = {
  /**
   * Make HTTP request
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Fetch options
   * @returns {Promise} Response promise
   */
  async request(endpoint, options = {}) {
    const url = `${CONFIG.api.baseUrl}${endpoint}`;
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const response = await fetch(url, { ...defaultOptions, ...options });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  },

  /**
   * Create room
   * @param {string} hostName - Host player name
   * @param {number} maxPlayers - Maximum players
   * @param {boolean} isPublic - Is room public
   * @returns {Promise} Room data
   */
  async createRoom(hostName, maxPlayers = CONFIG.room.defaultMaxPlayers, isPublic = true) {
    return this.request('/api/rooms', {
      method: 'POST',
      body: JSON.stringify({
        host_name: hostName,
        max_players: maxPlayers,
        is_public: isPublic,
      }),
    });
  },

  /**
   * Join room
   * @param {string} roomCode - Room code
   * @param {string} playerName - Player name
   * @returns {Promise} Room data
   */
  async joinRoom(roomCode, playerName) {
    return this.request(`/api/rooms/${roomCode}/join`, {
      method: 'POST',
      body: JSON.stringify({
        player_name: playerName,
      }),
    });
  },

  /**
   * Get room details
   * @param {string} roomCode - Room code
   * @returns {Promise} Room details
   */
  async getRoomDetails(roomCode) {
    return this.request(`/api/rooms/${roomCode}`);
  },
};

export default {
  storage,
  validators,
  dom,
  time,
  logger,
  api,
};
