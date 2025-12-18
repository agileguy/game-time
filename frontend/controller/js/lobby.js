/**
 * Controller Lobby Screen
 * Handles real-time lobby updates via WebSocket
 */

import CONFIG from '../../shared/js/config.js';
import { storage, logger } from '../../shared/js/utils.js';
import { appState } from '../../shared/js/state-manager.js';
import WebSocketClient, { ConnectionState } from '../../shared/js/websocket-client.js';
import notifications from '../../shared/js/components/notifications.js';
import { updatePlayerList } from '../../shared/js/components/player-list.js';

class LobbyController {
  constructor() {
    this.ws = null;
    this.sessionId = null;
    this.roomCode = null;
    this.playerId = null;
    this.isHost = false;
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
      logger.warn('No session or room code found, redirecting to join');
      window.location.href = 'join.html';
      return;
    }

    this.cacheElements();
    this.attachEventListeners();
    this.setupStateSubscriptions();
    await this.connectWebSocket();
  }

  /**
   * Cache DOM elements
   */
  cacheElements() {
    this.elements = {
      // Header
      roomCode: document.getElementById('room-code'),
      connectionIndicator: document.getElementById('connection-indicator'),
      connectionText: document.getElementById('connection-text'),

      // Player info
      playerName: document.getElementById('player-name'),
      hostBadge: document.getElementById('host-badge'),

      // Players section
      playerCount: document.getElementById('player-count'),
      playersList: document.getElementById('players-list'),

      // Controls
      hostControls: document.getElementById('host-controls'),
      playerControls: document.getElementById('player-controls'),
      startGameBtn: document.getElementById('start-game-btn'),
      leaveRoomBtn: document.getElementById('leave-room-btn'),
    };
  }

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    // Start game button
    this.elements.startGameBtn?.addEventListener('click', () => {
      this.handleStartGame();
    });

    // Leave room button
    this.elements.leaveRoomBtn?.addEventListener('click', () => {
      this.handleLeaveRoom();
    });

    // Handle page unload
    window.addEventListener('beforeunload', () => {
      if (this.ws) {
        this.ws.disconnect();
      }
    });

    // Handle visibility change (reconnect on return)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && this.ws && !this.ws.isConnected()) {
        logger.info('Page visible, reconnecting...');
        this.ws.connect().catch((error) => {
          logger.error('Reconnect failed:', error);
        });
      }
    });
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

    // Subscribe to host status changes
    appState.subscribe('isHost', (isHost) => {
      this.isHost = isHost;
      this.updateHostControls();
    });

    // Subscribe to room status changes
    appState.subscribe('roomStatus', (status) => {
      if (status === 'playing') {
        this.handleGameStarted();
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
      notifications.error('Failed to connect. Please refresh the page.');
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
      notifications.success(`${data.player_name} joined!`);
    });

    // Player left
    this.ws.on('player_left', (data) => {
      logger.info('Player left:', data.player_name);
      notifications.warning(`${data.player_name} left`);
    });

    // Player kicked
    this.ws.on('player_kicked', (data) => {
      logger.info('Player kicked:', data.player_name);

      if (data.player_id === this.playerId) {
        notifications.error('You have been kicked from the room');
        setTimeout(() => {
          storage.clearAll();
          window.location.href = 'join.html';
        }, 2000);
      } else {
        notifications.warning(`${data.player_name} was kicked`);
      }
    });

    // Host transferred
    this.ws.on('host_transferred', (data) => {
      logger.info('Host transferred:', data);

      if (data.new_host_id === this.playerId) {
        notifications.success('You are now the host!');
      } else {
        notifications.info(`${data.new_host_name} is now the host`);
      }
    });

    // Game starting (with countdown)
    this.ws.on('game_starting', (data) => {
      logger.info('Game starting:', data);
      this.handleGameStarted();
    });

    // Error messages
    this.ws.on('error', (data) => {
      logger.error('WebSocket error:', data);
      notifications.error(data.message || 'An error occurred');
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

    // Find current player
    const currentPlayer = data.players?.find((p) => p.session_id === this.sessionId);

    if (currentPlayer) {
      this.playerId = currentPlayer.id;
      appState.update({
        playerId: currentPlayer.id,
        playerName: currentPlayer.name,
        isHost: currentPlayer.is_host,
      });

      // Update UI
      this.elements.roomCode.textContent = data.room_code;
      this.elements.playerName.textContent = currentPlayer.name;

      if (currentPlayer.is_host) {
        this.elements.hostBadge.classList.remove('hidden');
      } else {
        this.elements.hostBadge.classList.add('hidden');
      }
    }
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
        notifications.error('Connection lost. Attempting to reconnect...');
        break;
    }
  }

  /**
   * Update players list
   * @param {Array} players - Players array
   */
  updatePlayers(players) {
    // Update player count (only count connected players)
    const maxPlayers = appState.get('maxPlayers') || 12;
    const connectedPlayers = players.filter((p) => p.connected);
    this.elements.playerCount.textContent = `${connectedPlayers.length} / ${maxPlayers}`;

    // Update players list
    updatePlayerList(this.elements.playersList, players, {
      showHost: true,
      showConnected: true,
      showActions: this.isHost,
      onKick: (playerId) => this.handleKickPlayer(playerId),
      currentPlayerId: this.playerId,
    });

    // Update start game button state
    this.updateStartGameButton(players);
  }

  /**
   * Update host controls visibility
   */
  updateHostControls() {
    if (this.isHost) {
      this.elements.hostControls.classList.remove('hidden');
      this.updateStartGameButton(appState.get('players') || []);
    } else {
      this.elements.hostControls.classList.add('hidden');
    }
  }

  /**
   * Update start game button state
   * @param {Array} players - Players array
   */
  updateStartGameButton(players) {
    if (!this.isHost || !this.elements.startGameBtn) return;

    const connectedPlayers = players.filter((p) => p.connected);
    const minPlayers = CONFIG.room.minPlayers;

    if (connectedPlayers.length >= minPlayers) {
      this.elements.startGameBtn.disabled = false;
    } else {
      this.elements.startGameBtn.disabled = true;
    }
  }

  /**
   * Handle start game
   */
  handleStartGame() {
    if (!this.isHost) {
      notifications.error('Only the host can start the game');
      return;
    }

    const players = appState.get('players') || [];
    const connectedPlayers = players.filter((p) => p.connected);

    if (connectedPlayers.length < CONFIG.room.minPlayers) {
      notifications.error(`Need at least ${CONFIG.room.minPlayers} players to start`);
      return;
    }

    // Send start game message
    this.ws.send('start_game');
    // Note: Don't show notification here - game_starting event will handle it
  }

  /**
   * Handle kick player
   * @param {number} playerId - Player ID to kick
   */
  handleKickPlayer(playerId) {
    if (!this.isHost) {
      notifications.error('Only the host can kick players');
      return;
    }

    const players = appState.get('players') || [];
    const player = players.find((p) => p.id === playerId);

    if (!player) return;

    if (confirm(`Kick ${player.name}?`)) {
      this.ws.send('kick_player', { player_id: playerId });
      logger.info('Kicking player:', playerId);
    }
  }

  /**
   * Handle leave room
   */
  handleLeaveRoom() {
    if (confirm('Leave this room?')) {
      // Send leave room message to backend
      if (this.ws && this.ws.isConnected()) {
        this.ws.send('leave_room');

        // Give the message time to send before disconnecting
        setTimeout(() => {
          if (this.ws) {
            this.ws.disconnect();
          }

          // Clear session data
          storage.clearAll();

          // Redirect to join page
          window.location.href = 'join.html';
        }, 100);
      } else {
        // If not connected, just clear and redirect
        storage.clearAll();
        window.location.href = 'join.html';
      }
    }
  }

  /**
   * Handle game started
   */
  handleGameStarted() {
    notifications.success('Starting game...');

    // Redirect to game view
    setTimeout(() => {
      // TODO: Redirect to appropriate game view
      notifications.info('Game views not yet implemented');
    }, 1500);
  }
}

// Initialize controller when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new LobbyController();
});
