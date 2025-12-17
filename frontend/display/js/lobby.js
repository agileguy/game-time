/**
 * Display Lobby Screen
 * Handles real-time lobby updates for TV/projector display
 */

import CONFIG from '../../shared/js/config.js';
import { storage, logger } from '../../shared/js/utils.js';
import { appState } from '../../shared/js/state-manager.js';
import WebSocketClient, { ConnectionState } from '../../shared/js/websocket-client.js';
import { updatePlayerList } from '../../shared/js/components/player-list.js';

class DisplayLobbyController {
  constructor() {
    this.ws = null;
    this.sessionId = null;
    this.roomCode = null;
    this.countdownTimer = null;
    this.init();
  }

  /**
   * Initialize controller
   */
  async init() {
    // Check session
    this.sessionId = storage.getSessionId();
    this.roomCode = storage.getRoomCode();

    if (!this.sessionId || !this.roomCode) {
      logger.warn('No session or room code found');
      this.showStatusMessage('Please create or join a room from your mobile device');
      return;
    }

    this.cacheElements();
    this.setupStateSubscriptions();
    await this.connectWebSocket();
    this.updateJoinUrl();
  }

  /**
   * Cache DOM elements
   */
  cacheElements() {
    this.elements = {
      // Header
      connectionIndicator: document.getElementById('connection-indicator'),
      connectionText: document.getElementById('connection-text'),

      // Room code
      roomCode: document.getElementById('room-code'),
      joinUrl: document.getElementById('join-url'),

      // Players
      playerCount: document.getElementById('player-count'),
      playersGrid: document.getElementById('players-grid'),
      waitingMessage: document.getElementById('waiting-message'),

      // Status
      statusMessage: document.getElementById('status-message'),
      startCountdown: document.getElementById('start-countdown'),
      countdownNumber: document.getElementById('countdown-number'),

      // Footer
      gameMode: document.getElementById('game-mode'),
      hostName: document.getElementById('host-name'),
    };
  }

  /**
   * Setup state subscriptions
   */
  setupStateSubscriptions() {
    // Subscribe to connection state changes
    appState.subscribe('connectionState', (state) => {
      this.updateConnectionStatus(state);
    });

    // Subscribe to player list changes
    appState.subscribe('players', (players) => {
      this.updatePlayers(players);
    });

    // Subscribe to room status changes
    appState.subscribe('roomStatus', (status) => {
      if (status === 'playing') {
        this.handleGameStarting();
      }
    });
  }

  /**
   * Connect to WebSocket
   */
  async connectWebSocket() {
    try {
      // Create WebSocket client
      this.ws = new WebSocketClient(this.sessionId);

      // Setup state change handler
      this.ws.onStateChange((newState) => {
        appState.set('connectionState', newState);
      });

      // Setup message handlers
      this.setupMessageHandlers();

      // Connect
      await this.ws.connect();
      logger.info('WebSocket connected');
    } catch (error) {
      logger.error('WebSocket connection failed:', error);
      this.showStatusMessage('Connection failed. Please refresh the page.');
    }
  }

  /**
   * Setup WebSocket message handlers
   */
  setupMessageHandlers() {
    // Room state updates
    this.ws.on('room_state', (data) => {
      logger.debug('Room state update:', data);
      this.handleRoomState(data);
    });

    // Player joined
    this.ws.on('player_joined', (data) => {
      logger.info('Player joined:', data.player_name);
      this.showStatusMessage(`${data.player_name} joined!`, 2000);
      this.playJoinSound();
    });

    // Player left
    this.ws.on('player_left', (data) => {
      logger.info('Player left:', data.player_name);
      this.showStatusMessage(`${data.player_name} left`, 2000);
    });

    // Player kicked
    this.ws.on('player_kicked', (data) => {
      logger.info('Player kicked:', data.player_name);
      this.showStatusMessage(`${data.player_name} was kicked`, 2000);
    });

    // Host transferred
    this.ws.on('host_transferred', (data) => {
      logger.info('Host transferred:', data);
      this.showStatusMessage(`${data.new_host_name} is now the host`, 2000);
    });

    // Game starting
    this.ws.on('game_starting', (data) => {
      logger.info('Game starting:', data);
      this.startCountdown(data.countdown || 3);
    });

    // Game started
    this.ws.on('game_started', (data) => {
      logger.info('Game started:', data);
      this.handleGameStarted();
    });

    // Error messages
    this.ws.on('error', (data) => {
      logger.error('WebSocket error:', data);
      this.showStatusMessage(`Error: ${data.message}`, 3000);
    });

    // Pong response
    this.ws.on('pong', () => {
      logger.debug('Pong received');
    });
  }

  /**
   * Handle room state update
   * @param {Object} data - Room state data
   */
  handleRoomState(data) {
    logger.debug('Updating room state:', data);

    // Update state
    appState.update({
      roomCode: data.room_code,
      roomStatus: data.status,
      players: data.players || [],
      maxPlayers: data.max_players || 12,
    });

    // Find host
    const host = data.players?.find((p) => p.is_host);

    // Update UI
    this.elements.roomCode.textContent = data.room_code;
    this.elements.hostName.textContent = host ? host.name : '---';
    this.elements.gameMode.textContent = this.formatStatus(data.status);
  }

  /**
   * Update connection status display
   * @param {string} state - Connection state
   */
  updateConnectionStatus(state) {
    const indicator = this.elements.connectionIndicator;
    const text = this.elements.connectionText;

    // Remove all state classes
    indicator.classList.remove('connected', 'disconnected', 'connecting');

    switch (state) {
      case ConnectionState.CONNECTED:
        indicator.classList.add('connected');
        text.textContent = 'Connected';
        break;

      case ConnectionState.CONNECTING:
      case ConnectionState.RECONNECTING:
        indicator.classList.add('connecting');
        text.textContent = 'Connecting...';
        break;

      case ConnectionState.DISCONNECTED:
      case ConnectionState.FAILED:
        indicator.classList.add('disconnected');
        text.textContent = 'Disconnected';
        this.showStatusMessage('Connection lost. Reconnecting...', 3000);
        break;
    }
  }

  /**
   * Update players display
   * @param {Array} players - Players array
   */
  updatePlayers(players) {
    const maxPlayers = appState.get('maxPlayers') || 12;

    // Update player count
    this.elements.playerCount.textContent = `${players.length} / ${maxPlayers}`;

    // Show/hide waiting message
    if (players.length === 0) {
      this.elements.waitingMessage.classList.remove('hidden');
      this.elements.playersGrid.innerHTML = '';
    } else {
      this.elements.waitingMessage.classList.add('hidden');

      // Update players grid
      updatePlayerList(this.elements.playersGrid, players, {
        showHost: true,
        showConnected: true,
        showActions: false,
      });
    }
  }

  /**
   * Update join URL display
   */
  updateJoinUrl() {
    const hostname = window.location.hostname;
    const port = window.location.port;
    const url = port ? `${hostname}:${port}` : hostname;
    this.elements.joinUrl.textContent = url;
  }

  /**
   * Format room status
   * @param {string} status - Room status
   * @returns {string} Formatted status
   */
  formatStatus(status) {
    const statusMap = {
      lobby: 'Lobby',
      playing: 'Playing',
      finished: 'Finished',
    };

    return statusMap[status] || status;
  }

  /**
   * Show status message
   * @param {string} message - Message to show
   * @param {number} duration - Duration in ms (0 for permanent)
   */
  showStatusMessage(message, duration = 0) {
    this.elements.statusMessage.textContent = message;
    this.elements.statusMessage.classList.remove('hidden');

    if (duration > 0) {
      setTimeout(() => {
        this.elements.statusMessage.textContent = '';
        this.elements.statusMessage.classList.add('hidden');
      }, duration);
    }
  }

  /**
   * Start countdown animation
   * @param {number} seconds - Countdown seconds
   */
  startCountdown(seconds) {
    let count = seconds;

    // Clear existing timer
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
    }

    // Show countdown
    this.elements.startCountdown.classList.remove('hidden');
    this.elements.countdownNumber.textContent = count;

    // Play countdown sound
    this.playCountdownSound();

    // Update countdown
    this.countdownTimer = setInterval(() => {
      count--;

      if (count > 0) {
        this.elements.countdownNumber.textContent = count;
        this.playCountdownSound();

        // Trigger animation by removing and re-adding class
        this.elements.countdownNumber.style.animation = 'none';
        setTimeout(() => {
          this.elements.countdownNumber.style.animation = '';
        }, 10);
      } else {
        clearInterval(this.countdownTimer);
        this.countdownTimer = null;
        this.elements.startCountdown.classList.add('hidden');
      }
    }, 1000);
  }

  /**
   * Handle game starting
   */
  handleGameStarting() {
    this.showStatusMessage('Game Starting!', 0);
  }

  /**
   * Handle game started
   */
  handleGameStarted() {
    // Hide countdown
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
      this.countdownTimer = null;
    }

    this.elements.startCountdown.classList.add('hidden');
    this.showStatusMessage('Game Started!', 2000);

    // TODO: Transition to game view
    setTimeout(() => {
      logger.info('Game views not yet implemented');
    }, 2000);
  }

  /**
   * Play join sound effect (visual feedback for now)
   */
  playJoinSound() {
    // Visual feedback: briefly highlight the room code
    this.elements.roomCode.style.color = 'var(--color-success)';
    setTimeout(() => {
      this.elements.roomCode.style.color = '';
    }, 500);
  }

  /**
   * Play countdown sound effect (visual feedback for now)
   */
  playCountdownSound() {
    // Visual feedback: pulse the countdown number
    this.elements.countdownNumber.style.transform = 'scale(1.1)';
    setTimeout(() => {
      this.elements.countdownNumber.style.transform = '';
    }, 100);
  }
}

// Initialize controller when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new DisplayLobbyController();
});
