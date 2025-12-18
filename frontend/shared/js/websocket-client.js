/**
 * WebSocket Client
 * Manages WebSocket connections with automatic reconnection
 */

import CONFIG from './config.js';
import { logger } from './utils.js';

/**
 * WebSocket connection states
 */
export const ConnectionState = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  RECONNECTING: 'reconnecting',
  FAILED: 'failed',
};

/**
 * WebSocket Client Class
 */
export class WebSocketClient {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.ws = null;
    this.state = ConnectionState.DISCONNECTED;
    this.reconnectAttempts = 0;
    this.reconnectTimer = null;
    this.heartbeatTimer = null;
    this.messageHandlers = new Map();
    this.stateChangeHandlers = [];
  }

  /**
   * Connect to WebSocket server
   * @returns {Promise} Promise that resolves when connected
   */
  connect() {
    return new Promise((resolve, reject) => {
      if (this.state === ConnectionState.CONNECTED) {
        resolve();
        return;
      }

      this.setState(ConnectionState.CONNECTING);
      logger.debug('Connecting to WebSocket...', this.sessionId);

      const wsUrl = `${CONFIG.api.wsUrl}/api/ws/${this.sessionId}`;
      this.ws = new WebSocket(wsUrl);

      // Connection timeout
      const timeout = setTimeout(() => {
        if (this.state !== ConnectionState.CONNECTED) {
          logger.error('WebSocket connection timeout');
          this.ws.close();
          reject(new Error('Connection timeout'));
        }
      }, CONFIG.websocket.connectionTimeout);

      this.ws.onopen = () => {
        clearTimeout(timeout);
        this.setState(ConnectionState.CONNECTED);
        this.reconnectAttempts = 0;
        logger.info('WebSocket connected');
        this.startHeartbeat();
        resolve();
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event);
      };

      this.ws.onerror = (error) => {
        clearTimeout(timeout);
        logger.error('WebSocket error:', error);
      };

      this.ws.onclose = (event) => {
        clearTimeout(timeout);
        this.stopHeartbeat();
        logger.info('WebSocket closed:', event.code, event.reason);

        if (event.code !== 1000 && this.reconnectAttempts < CONFIG.websocket.maxReconnectAttempts) {
          this.reconnect();
        } else {
          this.setState(ConnectionState.DISCONNECTED);
        }
      };
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    logger.info('Disconnecting WebSocket...');
    this.stopHeartbeat();
    this.clearReconnectTimer();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.setState(ConnectionState.DISCONNECTED);
  }

  /**
   * Reconnect to WebSocket server
   */
  reconnect() {
    this.clearReconnectTimer();
    this.setState(ConnectionState.RECONNECTING);

    this.reconnectAttempts++;
    logger.info(
      `Reconnecting... (attempt ${this.reconnectAttempts}/${CONFIG.websocket.maxReconnectAttempts})`
    );

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch((error) => {
        logger.error('Reconnection failed:', error);
        if (this.reconnectAttempts >= CONFIG.websocket.maxReconnectAttempts) {
          this.setState(ConnectionState.FAILED);
        }
      });
    }, CONFIG.websocket.reconnectInterval);
  }

  /**
   * Send message to server
   * @param {string} type - Message type
   * @param {Object} data - Message data
   */
  send(type, data = {}) {
    if (this.state !== ConnectionState.CONNECTED) {
      logger.warn('Cannot send message: not connected');
      return;
    }

    const message = {
      type,
      data,
      timestamp: Date.now(),
    };

    logger.debug('Sending message:', message);
    this.ws.send(JSON.stringify(message));
  }

  /**
   * Handle incoming message
   * @param {MessageEvent} event - WebSocket message event
   */
  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      logger.debug('Received message:', message);

      const handlers = this.messageHandlers.get(message.type) || [];
      handlers.forEach((handler) => {
        try {
          handler(message.data, message);
        } catch (error) {
          logger.error('Error in message handler:', error);
        }
      });

      // Call wildcard handlers
      const wildcardHandlers = this.messageHandlers.get('*') || [];
      wildcardHandlers.forEach((handler) => {
        try {
          handler(message.data, message);
        } catch (error) {
          logger.error('Error in wildcard handler:', error);
        }
      });
    } catch (error) {
      logger.error('Error parsing message:', error);
    }
  }

  /**
   * Register message handler
   * @param {string} type - Message type to handle ('*' for all messages)
   * @param {Function} handler - Handler function
   * @returns {Function} Unsubscribe function
   */
  on(type, handler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }

    const handlers = this.messageHandlers.get(type);
    handlers.push(handler);

    // Return unsubscribe function
    return () => {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    };
  }

  /**
   * Register state change handler
   * @param {Function} handler - Handler function
   * @returns {Function} Unsubscribe function
   */
  onStateChange(handler) {
    this.stateChangeHandlers.push(handler);

    // Return unsubscribe function
    return () => {
      const index = this.stateChangeHandlers.indexOf(handler);
      if (index > -1) {
        this.stateChangeHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Set connection state
   * @param {string} newState - New connection state
   */
  setState(newState) {
    const oldState = this.state;
    this.state = newState;

    logger.debug(`State change: ${oldState} -> ${newState}`);

    this.stateChangeHandlers.forEach((handler) => {
      try {
        handler(newState, oldState);
      } catch (error) {
        logger.error('Error in state change handler:', error);
      }
    });
  }

  /**
   * Start heartbeat timer
   */
  startHeartbeat() {
    this.stopHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.state === ConnectionState.CONNECTED) {
        this.send('ping');
      }
    }, CONFIG.websocket.heartbeatInterval);
  }

  /**
   * Stop heartbeat timer
   */
  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Clear reconnect timer
   */
  clearReconnectTimer() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Get current connection state
   * @returns {string} Current state
   */
  getState() {
    return this.state;
  }

  /**
   * Check if connected
   * @returns {boolean} True if connected
   */
  isConnected() {
    return this.state === ConnectionState.CONNECTED;
  }
}

export default WebSocketClient;
