/**
 * State Manager
 * Simple reactive state management for the application
 */

import { logger } from './utils.js';

/**
 * State Manager Class
 * Manages application state with reactive updates
 */
export class StateManager {
  constructor(initialState = {}) {
    this.state = { ...initialState };
    this.listeners = new Map();
    this.computedValues = new Map();
  }

  /**
   * Get current state
   * @param {string} key - State key (optional)
   * @returns {any} State value or entire state
   */
  get(key) {
    if (key === undefined) {
      return { ...this.state };
    }

    // Check for computed values first
    if (this.computedValues.has(key)) {
      const compute = this.computedValues.get(key);
      return compute(this.state);
    }

    // Support nested keys with dot notation
    if (key.includes('.')) {
      return this.getNestedValue(key);
    }

    return this.state[key];
  }

  /**
   * Get nested value using dot notation
   * @param {string} path - Dot-separated path (e.g., 'user.name')
   * @returns {any} Nested value
   */
  getNestedValue(path) {
    return path.split('.').reduce((obj, key) => obj?.[key], this.state);
  }

  /**
   * Set state value
   * @param {string|Object} keyOrUpdates - State key or updates object
   * @param {any} value - New value (if key is string)
   */
  set(keyOrUpdates, value) {
    const updates = typeof keyOrUpdates === 'string'
      ? { [keyOrUpdates]: value }
      : keyOrUpdates;

    const changedKeys = new Set();

    Object.entries(updates).forEach(([key, newValue]) => {
      if (this.state[key] !== newValue) {
        this.state[key] = newValue;
        changedKeys.add(key);
        logger.debug(`State updated: ${key}`, newValue);
      }
    });

    // Notify listeners
    changedKeys.forEach((key) => {
      this.notifyListeners(key);
    });

    // Notify wildcard listeners
    if (changedKeys.size > 0) {
      this.notifyListeners('*');
    }
  }

  /**
   * Update state with partial object
   * @param {Object} updates - Partial state updates
   */
  update(updates) {
    this.set(updates);
  }

  /**
   * Delete state key
   * @param {string} key - State key to delete
   */
  delete(key) {
    if (key in this.state) {
      delete this.state[key];
      this.notifyListeners(key);
      this.notifyListeners('*');
    }
  }

  /**
   * Subscribe to state changes
   * @param {string} key - State key to watch ('*' for all changes)
   * @param {Function} callback - Callback function
   * @returns {Function} Unsubscribe function
   */
  subscribe(key, callback) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, []);
    }

    const listeners = this.listeners.get(key);
    listeners.push(callback);

    // Return unsubscribe function
    return () => {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  }

  /**
   * Watch a computed value
   * @param {string} key - Computed value key
   * @param {Function} compute - Compute function(state)
   * @param {Function} callback - Callback when value changes
   * @returns {Function} Unsubscribe function
   */
  watch(key, compute, callback) {
    this.computedValues.set(key, compute);

    let previousValue = compute(this.state);

    return this.subscribe('*', () => {
      const newValue = compute(this.state);
      if (newValue !== previousValue) {
        callback(newValue, previousValue);
        previousValue = newValue;
      }
    });
  }

  /**
   * Notify listeners of state change
   * @param {string} key - Changed state key
   */
  notifyListeners(key) {
    const listeners = this.listeners.get(key) || [];
    listeners.forEach((callback) => {
      try {
        callback(this.state[key], this.state);
      } catch (error) {
        logger.error('Error in state listener:', error);
      }
    });
  }

  /**
   * Reset state to initial or provided state
   * @param {Object} newState - New state (optional)
   */
  reset(newState = {}) {
    this.state = { ...newState };
    this.notifyListeners('*');
  }

  /**
   * Clear all state
   */
  clear() {
    this.reset({});
  }
}

/**
 * Global application state
 */
export const appState = new StateManager({
  // Connection state
  connectionState: 'disconnected',
  sessionId: null,

  // Room state
  roomCode: null,
  roomStatus: null,
  players: [],
  maxPlayers: 12,

  // Player state
  playerId: null,
  playerName: null,
  isHost: false,

  // UI state
  currentView: null,
  loading: false,
  error: null,

  // Game state
  gameType: null,
  gameState: null,
});

export default StateManager;
