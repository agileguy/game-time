/**
 * Horse Race Display Controller
 * Handles real-time race updates for TV/projector display
 */

import CONFIG from '../../shared/js/config.js';
import { storage, logger } from '../../shared/js/utils.js';
import { appState } from '../../shared/js/state-manager.js';
import WebSocketClient, { ConnectionState } from '../../shared/js/websocket-client.js';

class HorseRaceDisplayController {
  constructor() {
    this.ws = null;
    this.sessionId = null;
    this.roomCode = null;
    this.gameState = null;
    this.bettingTimer = null;
    this.raceAnimationFrame = null;

    this.init();
  }

  /**
   * Initialize controller
   */
  async init() {
    this.cacheElements();

    // Check session
    this.sessionId = storage.getSessionId();
    this.roomCode = storage.getRoomCode();

    if (!this.sessionId || !this.roomCode) {
      logger.warn('No session or room code found');
      return;
    }

    this.elements.roomCode.textContent = this.roomCode;

    this.setupStateSubscriptions();
    await this.connectWebSocket();
  }

  /**
   * Cache DOM elements
   */
  cacheElements() {
    this.elements = {
      // Header
      connectionIndicator: document.getElementById('connection-indicator'),
      connectionText: document.getElementById('connection-text'),
      phaseText: document.getElementById('phase-text'),
      phaseTimer: document.getElementById('phase-timer'),

      // Betting phase
      bettingPhase: document.getElementById('betting-phase'),
      bettingCountdown: document.getElementById('betting-countdown'),
      horsePreview: document.getElementById('horse-preview'),

      // Race track
      raceTrack: document.getElementById('race-track'),

      // Results
      resultsPhase: document.getElementById('results-phase'),
      resultsPodium: document.getElementById('results-podium'),
      standingsList: document.getElementById('standings-list'),

      // Footer
      roomCode: document.getElementById('room-code'),
      roundDisplay: document.getElementById('round-display'),
    };
  }

  /**
   * Setup state subscriptions
   */
  setupStateSubscriptions() {
    appState.subscribe('connectionState', (state) => {
      this.updateConnectionStatus(state);
    });
  }

  /**
   * Connect to WebSocket
   */
  async connectWebSocket() {
    try {
      this.ws = new WebSocketClient(this.sessionId);

      this.ws.onStateChange((newState) => {
        appState.set('connectionState', newState);
      });

      this.setupMessageHandlers();

      await this.ws.connect();
      logger.info('WebSocket connected');
    } catch (error) {
      logger.error('WebSocket connection failed:', error);
    }
  }

  /**
   * Setup WebSocket message handlers
   */
  setupMessageHandlers() {
    // Game state updates
    this.ws.on('game_state_update', (data) => {
      logger.debug('Game state update:', data);
      this.handleGameStateUpdate(data);
    });

    // Game started
    this.ws.on('game_started', (data) => {
      logger.info('Game started:', data);
      this.handleGameStarted(data);
    });

    // Error messages
    this.ws.on('error', (data) => {
      logger.error('WebSocket error:', data);
    });
  }

  /**
   * Update connection status display
   */
  updateConnectionStatus(state) {
    const indicator = this.elements.connectionIndicator;
    const text = this.elements.connectionText;

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
        break;
    }
  }

  /**
   * Handle game started
   */
  handleGameStarted(data) {
    logger.info('Horse race game started:', data);

    // Store initial game state
    this.gameState = data;

    // Update round display
    const currentRound = data.current_round || 1;
    const totalRounds = data.total_rounds || 1;
    this.elements.roundDisplay.textContent = `Round ${currentRound} of ${totalRounds}`;

    // Show betting phase
    this.showBettingPhase(data);
  }

  /**
   * Handle game state update
   */
  handleGameStateUpdate(data) {
    logger.debug('Updating game state:', data);

    this.gameState = data;

    // Update phase indicator
    this.updatePhaseIndicator(data.phase);

    switch (data.phase) {
      case 'setup':
        this.showBettingPhase(data);
        break;

      case 'playing':
        this.showRaceTrack(data);
        this.updateRacePositions(data);
        break;

      case 'round_end':
      case 'finished':
        this.showResults(data);
        break;
    }
  }

  /**
   * Update phase indicator
   */
  updatePhaseIndicator(phase) {
    const phaseNames = {
      waiting: 'Waiting',
      setup: 'Betting Phase',
      playing: 'Racing!',
      round_end: 'Round Complete',
      finished: 'Game Over',
    };

    this.elements.phaseText.textContent = phaseNames[phase] || phase;
  }

  /**
   * Show betting phase
   */
  showBettingPhase(data) {
    // Hide other phases
    this.elements.raceTrack.classList.add('hidden');
    this.elements.resultsPhase.classList.add('hidden');

    // Show betting phase
    this.elements.bettingPhase.classList.remove('hidden');

    // Render horse preview
    this.renderHorsePreview(data.horses || []);

    // Start countdown
    const bettingDuration = data.betting_duration || 15;
    this.startBettingCountdown(bettingDuration);
  }

  /**
   * Render horse preview cards
   */
  renderHorsePreview(horses) {
    this.elements.horsePreview.innerHTML = '';

    horses.forEach((horse, index) => {
      const card = document.createElement('div');
      card.className = 'horse-preview-card';
      card.style.borderColor = horse.color;

      card.innerHTML = `
        <div class="horse-preview-icon">🐴</div>
        <div class="horse-preview-name" style="color: ${horse.color}">${horse.name}</div>
        <div class="horse-preview-odds">Lane ${index + 1}</div>
      `;

      this.elements.horsePreview.appendChild(card);
    });
  }

  /**
   * Start betting countdown
   */
  startBettingCountdown(duration) {
    let remaining = duration;

    // Clear existing timer
    if (this.bettingTimer) {
      clearInterval(this.bettingTimer);
    }

    // Update display
    this.elements.bettingCountdown.textContent = remaining;
    this.elements.phaseTimer.textContent = `${remaining}s`;

    // Start timer
    this.bettingTimer = setInterval(() => {
      remaining--;

      if (remaining >= 0) {
        this.elements.bettingCountdown.textContent = remaining;
        this.elements.phaseTimer.textContent = `${remaining}s`;
      } else {
        clearInterval(this.bettingTimer);
        this.bettingTimer = null;
      }
    }, 1000);
  }

  /**
   * Show race track
   */
  showRaceTrack(data) {
    // Hide other phases
    this.elements.bettingPhase.classList.add('hidden');
    this.elements.resultsPhase.classList.add('hidden');

    // Show race track
    this.elements.raceTrack.classList.remove('hidden');

    // Clear betting timer
    if (this.bettingTimer) {
      clearInterval(this.bettingTimer);
      this.bettingTimer = null;
    }

    // Render track lanes
    this.renderRaceTrack(data.horses || []);

    // Update phase timer
    this.elements.phaseTimer.textContent = '🏁';
  }

  /**
   * Render race track lanes
   */
  renderRaceTrack(horses) {
    const trackLanes = this.elements.raceTrack.querySelector('.track-lanes');
    trackLanes.innerHTML = '';

    horses.forEach((horse, index) => {
      const lane = document.createElement('div');
      lane.className = 'horse-lane';
      lane.dataset.horseId = index;

      lane.innerHTML = `
        <div class="lane-marker">
          <div class="lane-number">${index + 1}</div>
          <div class="lane-horse-name" style="color: ${horse.color}">${horse.name}</div>
        </div>
        <div class="horse-sprite" style="left: 0%; filter: drop-shadow(4px 4px 4px ${horse.color})">
          🐴
        </div>
      `;

      trackLanes.appendChild(lane);
    });
  }

  /**
   * Update race positions
   */
  updateRacePositions(data) {
    const horses = data.horses || [];
    const trackLength = 100; // Fixed track length

    horses.forEach((horse, index) => {
      const lane = this.elements.raceTrack.querySelector(
        `.horse-lane[data-horse-id="${index}"]`
      );
      if (!lane) return;

      const sprite = lane.querySelector('.horse-sprite');
      if (!sprite) return;

      // Calculate position as percentage (account for sprite width)
      const maxPosition = 90; // Leave room for horse sprite at finish line
      const positionPercent = Math.min(
        (horse.position / trackLength) * maxPosition,
        maxPosition
      );

      sprite.style.left = `${positionPercent}%`;

      // Add finish animation if horse crossed finish line
      if (horse.position >= trackLength && !sprite.classList.contains('finished')) {
        sprite.classList.add('finished');
        sprite.style.animation = 'none';
      }
    });
  }

  /**
   * Show results
   */
  showResults(data) {
    // Hide other phases
    this.elements.bettingPhase.classList.add('hidden');
    this.elements.raceTrack.classList.add('hidden');

    // Show results
    this.elements.resultsPhase.classList.remove('hidden');

    // Render podium
    this.renderPodium(data.horses || []);

    // Render player standings
    this.renderPlayerStandings(data.all_scores || {}, data.horses || []);

    // Update phase timer
    this.elements.phaseTimer.textContent = '🏆';
  }

  /**
   * Render podium
   */
  renderPodium(horses) {
    this.elements.resultsPodium.innerHTML = '';

    // Sort horses by position (descending to get finished order)
    const finishedHorses = [...horses]
      .filter((h) => h.position >= 100)
      .sort((a, b) => {
        // If both finished, compare by who finished first (higher position means finished earlier in tie)
        return b.position - a.position;
      });

    // Take top 3
    const topThree = finishedHorses.slice(0, 3);

    // Render in podium order: 2nd, 1st, 3rd
    const podiumOrder = [1, 0, 2];

    podiumOrder.forEach((index) => {
      if (!topThree[index]) return;

      const horse = topThree[index];
      const place = index + 1;

      const podiumPlace = document.createElement('div');
      podiumPlace.className = `podium-place podium-place-${place}`;

      const medals = ['🥇', '🥈', '🥉'];

      podiumPlace.innerHTML = `
        <div class="podium-horse">🐴</div>
        <div class="podium-rank">${medals[index]} ${this.getOrdinal(place)} Place</div>
        <div class="podium-horse-name" style="color: ${horse.color}">${horse.name}</div>
        <div class="podium-pedestal"></div>
      `;

      this.elements.resultsPodium.appendChild(podiumPlace);
    });
  }

  /**
   * Render player standings
   */
  renderPlayerStandings(scores, horses) {
    this.elements.standingsList.innerHTML = '';

    // Convert scores object to array and sort
    const standings = Object.entries(scores)
      .map(([playerId, score]) => ({ playerId, score }))
      .sort((a, b) => b.score - a.score);

    standings.forEach((standing, index) => {
      const item = document.createElement('div');
      item.className = 'standing-item';

      item.innerHTML = `
        <div class="standing-rank">#${index + 1}</div>
        <div class="standing-name">Player ${standing.playerId.substring(0, 8)}</div>
        <div class="standing-score">${standing.score} pts</div>
      `;

      this.elements.standingsList.appendChild(item);
    });
  }

  /**
   * Get ordinal suffix for number
   */
  getOrdinal(n) {
    const s = ['th', 'st', 'nd', 'rd'];
    const v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
  }

  /**
   * Cleanup
   */
  destroy() {
    if (this.bettingTimer) {
      clearInterval(this.bettingTimer);
    }
    if (this.raceAnimationFrame) {
      cancelAnimationFrame(this.raceAnimationFrame);
    }
    if (this.ws) {
      this.ws.disconnect();
    }
  }
}

// Initialize controller when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new HorseRaceDisplayController();
});
