/**
 * Controller Horse Race Screen
 * Handles betting interface and race view for players
 */

import CONFIG from '../../shared/js/config.js';
import { storage, logger } from '../../shared/js/utils.js';
import { appState } from '../../shared/js/state-manager.js';
import WebSocketClient, { ConnectionState } from '../../shared/js/websocket-client.js';
import notifications from '../../shared/js/components/notifications.js';

class HorseRaceController {
  constructor() {
    this.ws = null;
    this.sessionId = null;
    this.roomCode = null;
    this.playerId = null;
    this.gameState = null;
    this.currentBet = null;
    this.playerScore = 0;
    this.bettingTimer = null;

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

    this.elements.roomCode.textContent = this.roomCode;
  }

  /**
   * Cache DOM elements
   */
  cacheElements() {
    this.elements = {
      // Header
      playerScore: document.getElementById('player-score'),
      connectionIndicator: document.getElementById('connection-indicator'),
      connectionText: document.getElementById('connection-text'),
      phaseText: document.getElementById('phase-text'),
      phaseTimer: document.getElementById('phase-timer'),

      // Betting phase
      bettingPhase: document.getElementById('betting-phase'),
      currentBet: document.getElementById('current-bet'),
      betHorseName: document.getElementById('bet-horse-name'),
      changeBetBtn: document.getElementById('change-bet-btn'),
      horseSelection: document.getElementById('horse-selection'),

      // Racing phase
      racingPhase: document.getElementById('racing-phase'),
      betReminderHorse: document.getElementById('bet-reminder-horse'),
      racePositions: document.getElementById('race-positions'),

      // Results phase
      resultsPhase: document.getElementById('results-phase'),
      winStatusIcon: document.getElementById('win-status-icon'),
      winStatusText: document.getElementById('win-status-text'),
      pointsEarned: document.getElementById('points-earned'),
      resultsList: document.getElementById('results-list'),
      finalScore: document.getElementById('final-score'),

      // Waiting phase
      waitingPhase: document.getElementById('waiting-phase'),

      // Footer
      roomCode: document.getElementById('room-code'),
      roundDisplay: document.getElementById('round-display'),
    };
  }

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    // Change bet button
    this.elements.changeBetBtn?.addEventListener('click', () => {
      this.showBetSelection();
    });
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
      notifications.error('Failed to connect. Please refresh the page.');
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

    // Game action response
    this.ws.on('game_action_response', (data) => {
      logger.debug('Game action response:', data);
      this.handleGameActionResponse(data);
    });

    // Error messages
    this.ws.on('error', (data) => {
      logger.error('WebSocket error:', data);
      notifications.error(data.message || 'An error occurred');
    });
  }

  /**
   * Update connection status display
   */
  updateConnectionStatus(state) {
    const indicator = this.elements.connectionIndicator;

    indicator.classList.remove('connected', 'disconnected', 'connecting');

    switch (state) {
      case ConnectionState.CONNECTED:
        indicator.classList.add('connected');
        break;

      case ConnectionState.CONNECTING:
      case ConnectionState.RECONNECTING:
        indicator.classList.add('connecting');
        break;

      case ConnectionState.DISCONNECTED:
      case ConnectionState.FAILED:
        indicator.classList.add('disconnected');
        notifications.error('Connection lost. Reconnecting...');
        break;
    }
  }

  /**
   * Handle game started
   */
  handleGameStarted(data) {
    logger.info('Horse race game started:', data);

    this.gameState = data;
    this.currentBet = null;

    // Update round display
    const currentRound = data.current_round || 1;
    const totalRounds = data.total_rounds || 1;
    this.elements.roundDisplay.textContent = `Round ${currentRound} of ${totalRounds}`;

    // Get initial player score
    if (data.all_scores && this.sessionId) {
      this.playerScore = data.all_scores[this.sessionId] || 0;
      this.elements.playerScore.textContent = this.playerScore;
    } else if (data.your_score !== undefined) {
      this.playerScore = data.your_score;
      this.elements.playerScore.textContent = this.playerScore;
    }

    // Show betting phase
    this.showBettingPhase(data);
  }

  /**
   * Handle game state update
   */
  handleGameStateUpdate(data) {
    logger.debug('Updating game state:', data);

    this.gameState = data;

    // Update scores
    if (data.all_scores && this.sessionId) {
      this.playerScore = data.all_scores[this.sessionId] || 0;
      this.elements.playerScore.textContent = this.playerScore;
    } else if (data.your_score !== undefined) {
      this.playerScore = data.your_score;
      this.elements.playerScore.textContent = this.playerScore;
    }

    // Update phase indicator
    this.updatePhaseIndicator(data.phase);

    switch (data.phase) {
      case 'setup':
        this.showBettingPhase(data);
        break;

      case 'playing':
        this.showRacingPhase(data);
        this.updateRacePositions(data);
        break;

      case 'round_end':
      case 'finished':
        this.showResults(data);
        break;

      case 'waiting':
        this.showWaitingPhase();
        break;
    }
  }

  /**
   * Handle game action response
   */
  handleGameActionResponse(data) {
    if (data.action === 'place_bet') {
      if (data.success) {
        this.currentBet = data.bet;
        this.showCurrentBet(data.bet);
        notifications.success('Bet placed!');
      } else {
        notifications.error(data.error || 'Failed to place bet');
      }
    }
  }

  /**
   * Update phase indicator
   */
  updatePhaseIndicator(phase) {
    const phaseNames = {
      waiting: 'Waiting',
      setup: 'Betting',
      playing: 'Racing!',
      round_end: 'Results',
      finished: 'Game Over',
    };

    this.elements.phaseText.textContent = phaseNames[phase] || phase;
  }

  /**
   * Show betting phase
   */
  showBettingPhase(data) {
    // Hide other phases
    this.elements.racingPhase.classList.add('hidden');
    this.elements.resultsPhase.classList.add('hidden');
    this.elements.waitingPhase.classList.add('hidden');

    // Show betting phase
    this.elements.bettingPhase.classList.remove('hidden');

    // Only render horses if we have valid horse data
    // Don't clear existing horses if update has no horse data
    if (data.horses && data.horses.length > 0) {
      this.renderHorseSelection(data.horses);
    }

    // Start countdown
    const bettingDuration = data.betting_duration || 15;
    this.startBettingCountdown(bettingDuration);

    // If player already has a bet, show it
    if (this.currentBet !== null) {
      this.showCurrentBet(this.currentBet);
    }
  }

  /**
   * Render horse selection cards
   */
  renderHorseSelection(horses) {
    this.elements.horseSelection.innerHTML = '';

    horses.forEach((horse, index) => {
      const card = document.createElement('div');
      card.className = 'horse-bet-card';
      card.dataset.horseId = index;

      if (this.currentBet === index) {
        card.classList.add('selected');
      }

      card.style.borderColor = horse.color;

      card.innerHTML = `
        <div class="horse-icon">🐴</div>
        <div class="horse-name" style="color: ${horse.color}">${horse.name}</div>
        <div class="horse-lane-number">Lane ${index + 1}</div>
      `;

      card.addEventListener('click', () => {
        this.handlePlaceBet(index);
      });

      this.elements.horseSelection.appendChild(card);
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
    this.elements.phaseTimer.textContent = `${remaining}s`;

    // Start timer
    this.bettingTimer = setInterval(() => {
      remaining--;

      if (remaining >= 0) {
        this.elements.phaseTimer.textContent = `${remaining}s`;
      } else {
        clearInterval(this.bettingTimer);
        this.bettingTimer = null;
      }
    }, 1000);
  }

  /**
   * Handle place bet
   */
  handlePlaceBet(horseId) {
    if (!this.ws || !this.ws.isConnected()) {
      notifications.error('Not connected');
      return;
    }

    // Send bet action
    this.ws.send('game_action', {
      action: 'place_bet',
      data: {
        horse_id: horseId,
      },
    });

    logger.info('Placing bet on horse:', horseId);
  }

  /**
   * Show current bet
   */
  showCurrentBet(horseId) {
    const horses = this.gameState?.horses || [];
    const horse = horses[horseId];

    if (!horse) return;

    this.elements.betHorseName.textContent = horse.name;
    this.elements.betHorseName.style.color = horse.color;
    this.elements.currentBet.classList.remove('hidden');

    // Update selected card
    const allCards = this.elements.horseSelection.querySelectorAll('.horse-bet-card');
    allCards.forEach((card) => {
      if (parseInt(card.dataset.horseId) === horseId) {
        card.classList.add('selected');
      } else {
        card.classList.remove('selected');
      }
    });
  }

  /**
   * Show bet selection
   */
  showBetSelection() {
    this.elements.currentBet.classList.add('hidden');
  }

  /**
   * Show racing phase
   */
  showRacingPhase(data) {
    // Hide other phases
    this.elements.bettingPhase.classList.add('hidden');
    this.elements.resultsPhase.classList.add('hidden');
    this.elements.waitingPhase.classList.add('hidden');

    // Show racing phase
    this.elements.racingPhase.classList.remove('hidden');

    // Clear betting timer
    if (this.bettingTimer) {
      clearInterval(this.bettingTimer);
      this.bettingTimer = null;
    }

    // Show bet reminder
    if (this.currentBet !== null) {
      const horses = data.horses || [];
      const horse = horses[this.currentBet];
      if (horse) {
        this.elements.betReminderHorse.textContent = horse.name;
        this.elements.betReminderHorse.style.color = horse.color;
      }
    }

    // Render race positions
    this.renderRacePositions(data.horses || []);

    // Update phase timer
    this.elements.phaseTimer.textContent = '🏁';
  }

  /**
   * Render race positions
   */
  renderRacePositions(horses) {
    this.elements.racePositions.innerHTML = '';

    horses.forEach((horse, index) => {
      const posBar = document.createElement('div');
      posBar.className = 'position-bar';
      posBar.dataset.horseId = index;

      if (index === this.currentBet) {
        posBar.classList.add('your-bet');
      }

      posBar.innerHTML = `
        <div class="position-header">
          <div class="position-horse-info">
            <div class="position-lane">${index + 1}</div>
            <div class="position-horse-name" style="color: ${horse.color}">${horse.name}</div>
          </div>
          <div class="position-indicator">🐴</div>
        </div>
        <div class="position-progress" style="width: 0%; background: linear-gradient(90deg, transparent, ${horse.color}20);"></div>
      `;

      this.elements.racePositions.appendChild(posBar);
    });
  }

  /**
   * Update race positions
   */
  updateRacePositions(data) {
    const horses = data.horses || [];
    const trackLength = 100; // Fixed track length

    horses.forEach((horse, index) => {
      const posBar = this.elements.racePositions.querySelector(
        `.position-bar[data-horse-id="${index}"]`
      );
      if (!posBar) return;

      const progress = posBar.querySelector('.position-progress');
      if (!progress) return;

      const positionPercent = Math.min((horse.position / trackLength) * 100, 100);
      progress.style.width = `${positionPercent}%`;
    });
  }

  /**
   * Show results
   */
  showResults(data) {
    // Hide other phases
    this.elements.bettingPhase.classList.add('hidden');
    this.elements.racingPhase.classList.add('hidden');
    this.elements.waitingPhase.classList.add('hidden');

    // Clear betting timer if still running
    if (this.bettingTimer) {
      clearInterval(this.bettingTimer);
      this.bettingTimer = null;
    }

    // Show results phase
    this.elements.resultsPhase.classList.remove('hidden');

    // Determine win/loss
    const horses = data.horses || [];
    const trackLength = 100;

    // Sort horses by position
    const sortedHorses = [...horses]
      .map((h, i) => ({ ...h, index: i }))
      .filter((h) => h.position >= trackLength)
      .sort((a, b) => b.position - a.position);

    const winner = sortedHorses[0];
    const didWin = winner && winner.index === this.currentBet;

    // Calculate points earned this round
    const previousScore = this.playerScore;
    const newScore = data.all_scores?.[this.sessionId] || data.your_score || 0;
    const pointsEarned = newScore - previousScore;

    // Update win status
    if (didWin) {
      this.elements.winStatusIcon.textContent = '🏆';
      this.elements.winStatusText.textContent = 'You Won!';
      this.elements.winStatusText.className = 'win-status-text won';
      this.elements.pointsEarned.textContent = `+${pointsEarned} points`;
      this.elements.pointsEarned.className = 'points-earned positive';
    } else {
      this.elements.winStatusIcon.textContent = '😔';
      this.elements.winStatusText.textContent = 'Better Luck Next Time';
      this.elements.winStatusText.className = 'win-status-text lost';
      this.elements.pointsEarned.textContent = '+0 points';
      this.elements.pointsEarned.className = 'points-earned';
    }

    // Render results list
    this.renderResultsList(sortedHorses);

    // Update final score
    this.elements.finalScore.textContent = newScore;

    // Update phase timer
    this.elements.phaseTimer.textContent = '🏆';
  }

  /**
   * Render results list
   */
  renderResultsList(sortedHorses) {
    this.elements.resultsList.innerHTML = '';

    const medals = ['🥇', '🥈', '🥉'];
    const positions = ['1st', '2nd', '3rd', '4th'];
    const positionClasses = ['first', 'second', 'third', ''];

    sortedHorses.forEach((horse, index) => {
      const item = document.createElement('div');
      item.className = 'result-item';

      if (horse.index === this.currentBet) {
        item.classList.add('your-bet');
      }

      item.innerHTML = `
        <div class="result-position ${positionClasses[index] || ''}">${positions[index] || `${index + 1}th`}</div>
        <div class="result-horse-name" style="color: ${horse.color}">${horse.name}</div>
        <div class="result-icon">${medals[index] || '🐴'}</div>
      `;

      this.elements.resultsList.appendChild(item);
    });
  }

  /**
   * Show waiting phase
   */
  showWaitingPhase() {
    // Hide other phases
    this.elements.bettingPhase.classList.add('hidden');
    this.elements.racingPhase.classList.add('hidden');
    this.elements.resultsPhase.classList.add('hidden');

    // Show waiting phase
    this.elements.waitingPhase.classList.remove('hidden');

    this.elements.phaseTimer.textContent = '⏳';
  }

  /**
   * Cleanup
   */
  destroy() {
    if (this.bettingTimer) {
      clearInterval(this.bettingTimer);
    }
    if (this.ws) {
      this.ws.disconnect();
    }
  }
}

// Initialize controller when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new HorseRaceController();
});
