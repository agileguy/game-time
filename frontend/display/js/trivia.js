/**
 * Display Trivia Screen
 * Handles trivia game display for shared screens/TVs
 */

import CONFIG from '../../shared/js/config.js';
import { storage, logger } from '../../shared/js/utils.js';
import { appState } from '../../shared/js/state-manager.js';
import WebSocketClient, { ConnectionState } from '../../shared/js/websocket-client.js';
import notifications from '../../shared/js/components/notifications.js';

class TriviaDisplay {
  constructor() {
    this.ws = null;
    this.sessionId = null;
    this.roomCode = null;
    this.gameState = null;
    this.currentPhase = null;
    this.questionTimer = null;
    this.playerNames = {}; // Map session_id to player name

    this.init();
  }

  /**
   * Initialize display
   */
  async init() {
    // Check session
    this.sessionId = storage.getSessionId();
    this.roomCode = storage.getRoomCode();

    if (!this.sessionId || !this.roomCode) {
      logger.warn('No session or room code found, redirecting to join');
      window.location.href = '../controller/join.html';
      return;
    }

    this.cacheElements();
    this.setupStateSubscriptions();
    await this.connectWebSocket();

    this.elements.roomCode.textContent = this.roomCode;
    this.elements.footerRoomCode.textContent = this.roomCode;
  }

  /**
   * Cache DOM elements
   */
  cacheElements() {
    this.elements = {
      // Header
      questionProgress: document.getElementById('question-progress'),
      timer: document.getElementById('timer'),
      roomCode: document.getElementById('room-code'),

      // Question phase
      questionPhase: document.getElementById('question-phase'),
      questionCategory: document.getElementById('question-category'),
      questionText: document.getElementById('question-text'),
      optionsGrid: document.getElementById('options-grid'),
      playersList: document.getElementById('players-list'),

      // Results phase
      resultsPhase: document.getElementById('results-phase'),
      correctAnswerCard: document.getElementById('correct-answer-card'),
      playerResultsList: document.getElementById('player-results-list'),
      standingsList: document.getElementById('standings-list'),

      // Final phase
      finalPhase: document.getElementById('final-phase'),
      winnerName: document.getElementById('winner-name'),
      winnerScore: document.getElementById('winner-score'),
      finalLeaderboardList: document.getElementById('final-leaderboard-list'),

      // Waiting phase
      waitingPhase: document.getElementById('waiting-phase'),

      // Footer
      footerRoomCode: document.getElementById('footer-room-code'),
      progressFill: document.getElementById('progress-fill'),
      connectionStatus: document.getElementById('connection-status'),
      playerCount: document.getElementById('player-count'),
    };

    // Cache option cards
    this.optionCards = Array.from(this.elements.optionsGrid.querySelectorAll('.option-card'));
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

    // Player joined/left
    this.ws.on('player_joined', (data) => {
      this.handlePlayerUpdate(data);
    });

    this.ws.on('player_left', (data) => {
      this.handlePlayerUpdate(data);
    });

    // Room update (for player names)
    this.ws.on('room_update', (data) => {
      if (data.players) {
        this.updatePlayerNames(data.players);
      }
    });

    // Error
    this.ws.on('error', (data) => {
      logger.error('WebSocket error:', data);
    });

    // Game finished
    this.ws.on('game_finished', (data) => {
      logger.info('Game finished:', data);
    });
  }

  /**
   * Update player names map
   */
  updatePlayerNames(players) {
    this.playerNames = {};
    players.forEach(player => {
      this.playerNames[player.session_id] = player.name;
    });
  }

  /**
   * Get player name by session ID
   */
  getPlayerName(sessionId) {
    return this.playerNames[sessionId] || 'Player';
  }

  /**
   * Handle game started
   */
  handleGameStarted(data) {
    logger.info('Trivia game started');
    // Initial state will come through game_state_update
  }

  /**
   * Handle player updates
   */
  handlePlayerUpdate(data) {
    if (data.players) {
      this.updatePlayerNames(data.players);
      this.updatePlayerCount(data.players.length);
    }
  }

  /**
   * Handle game state update
   */
  handleGameStateUpdate(data) {
    const isPhaseTransition = this.currentPhase !== data.phase;
    this.currentPhase = data.phase;

    this.gameState = data;

    // Update progress bar
    if (data.current_question_index !== undefined && data.total_questions) {
      const progress = ((data.current_question_index + 1) / data.total_questions) * 100;
      this.elements.progressFill.style.width = `${progress}%`;
    }

    // Update player count
    if (data.total_players !== undefined) {
      this.updatePlayerCount(data.total_players);
    }

    // Handle phase-specific rendering
    switch (data.phase) {
      case 'setup':
        this.showQuestionPhase(data, isPhaseTransition);
        break;
      case 'round_end':
        this.showResultsPhase(data);
        break;
      case 'finished':
        this.showFinalPhase(data);
        break;
      default:
        logger.warn('Unknown phase:', data.phase);
    }
  }

  /**
   * Show question phase
   */
  showQuestionPhase(data, isPhaseTransition) {
    // Hide other phases
    this.elements.resultsPhase.classList.add('hidden');
    this.elements.finalPhase.classList.add('hidden');
    this.elements.waitingPhase.classList.add('hidden');

    // Show question phase
    this.elements.questionPhase.classList.remove('hidden');

    // Reset timer on phase transition
    if (isPhaseTransition && this.questionTimer) {
      clearInterval(this.questionTimer);
    }

    const question = data.current_question;
    if (!question) {
      logger.warn('No current question in state');
      return;
    }

    // Update progress text
    const questionNum = (data.current_question_index || 0) + 1;
    const totalQuestions = data.total_questions || 5;
    this.elements.questionProgress.textContent = `Question ${questionNum} of ${totalQuestions}`;

    // Update category
    this.elements.questionCategory.textContent = question.category || 'General';

    // Update question text
    this.elements.questionText.textContent = question.question;

    // Update option cards
    if (question.options && question.options.length === 4) {
      const letters = ['A', 'B', 'C', 'D'];
      const answerCounts = data.answer_counts || [0, 0, 0, 0];

      this.optionCards.forEach((card, index) => {
        const letterSpan = card.querySelector('.option-letter');
        const textSpan = card.querySelector('.option-text');
        const countSpan = card.querySelector('.answer-count');

        letterSpan.textContent = letters[index];
        textSpan.textContent = question.options[index];
        countSpan.textContent = answerCounts[index];

        // Highlight if has answers
        if (answerCounts[index] > 0) {
          card.classList.add('has-answers');
        } else {
          card.classList.remove('has-answers');
        }
      });
    }

    // Update player indicators
    this.updatePlayerIndicators(data.players_answered || [], data.total_players || 0);

    // Start countdown timer (only on phase transition)
    if (isPhaseTransition && data.question_start_time && data.answer_time) {
      this.startQuestionTimer(data.question_start_time, data.answer_time);
    }
  }

  /**
   * Start question countdown timer
   */
  startQuestionTimer(startTime, duration) {
    const startTimestamp = new Date(startTime).getTime();

    const updateTimer = () => {
      const now = Date.now();
      const elapsed = (now - startTimestamp) / 1000; // seconds
      const remaining = Math.max(0, duration - elapsed);

      this.elements.timer.textContent = `${Math.ceil(remaining)}s`;

      if (remaining <= 0) {
        clearInterval(this.questionTimer);
      }
    };

    // Update immediately
    updateTimer();

    // Update every 100ms for smooth countdown
    this.questionTimer = setInterval(updateTimer, 100);
  }

  /**
   * Update player indicators
   */
  updatePlayerIndicators(playersAnswered, totalPlayers) {
    const playersArray = Object.keys(this.playerNames);

    this.elements.playersList.innerHTML = playersArray.map(sessionId => {
      const playerName = this.getPlayerName(sessionId);
      const hasAnswered = playersAnswered.includes(sessionId);

      return `
        <div class="player-indicator ${hasAnswered ? 'answered' : ''}">
          <span class="status-icon">${hasAnswered ? '✓' : '○'}</span>
          <span class="player-name">${playerName}</span>
        </div>
      `;
    }).join('');
  }

  /**
   * Show results phase
   */
  showResultsPhase(data) {
    // Hide other phases
    this.elements.questionPhase.classList.add('hidden');
    this.elements.finalPhase.classList.add('hidden');
    this.elements.waitingPhase.classList.add('hidden');

    // Show results phase
    this.elements.resultsPhase.classList.remove('hidden');

    const question = data.current_question;
    if (!question || question.correct_answer === undefined) {
      logger.warn('No question or correct answer in results phase');
      return;
    }

    const correctAnswer = question.correct_answer;
    const letters = ['A', 'B', 'C', 'D'];

    // Show correct answer
    this.elements.correctAnswerCard.innerHTML = `
      <span class="answer-letter-large">${letters[correctAnswer]}</span>
      <span class="answer-text-large">${question.options[correctAnswer]}</span>
    `;

    // Show player results
    if (data.player_results && data.player_results.length > 0) {
      this.elements.playerResultsList.innerHTML = data.player_results.map(result => {
        const playerName = this.getPlayerName(result.player_id);
        const isCorrect = result.answer === correctAnswer;
        const scoreEarned = result.score || 0;
        const totalScore = result.total_score || 0;

        return `
          <div class="player-result ${isCorrect ? 'correct' : 'incorrect'}">
            <div class="result-icon-display">${isCorrect ? '✓' : '✗'}</div>
            <div class="result-player-name">${playerName}</div>
            <div class="result-score-earned">+${scoreEarned}</div>
            <div class="result-total-score">${totalScore} total</div>
          </div>
        `;
      }).join('');
    }

    // Show current standings
    this.updateStandings(data.player_results || []);

    // Update timer
    this.elements.timer.textContent = '5s';

    // Clear question timer
    if (this.questionTimer) {
      clearInterval(this.questionTimer);
    }
  }

  /**
   * Update standings list
   */
  updateStandings(playerResults) {
    const sorted = [...playerResults].sort((a, b) => b.total_score - a.total_score);

    this.elements.standingsList.innerHTML = sorted.map((result, index) => {
      const playerName = this.getPlayerName(result.player_id);
      const rank = index + 1;
      const rankClass = rank === 1 ? 'rank-1' : '';

      return `
        <div class="standing-item ${rankClass}">
          <div class="standing-rank">#${rank}</div>
          <div class="standing-player-name">${playerName}</div>
          <div class="standing-score">${result.total_score}</div>
        </div>
      `;
    }).join('');
  }

  /**
   * Show final results phase
   */
  showFinalPhase(data) {
    // Hide other phases
    this.elements.questionPhase.classList.add('hidden');
    this.elements.resultsPhase.classList.add('hidden');
    this.elements.waitingPhase.classList.add('hidden');

    // Show final phase
    this.elements.finalPhase.classList.remove('hidden');

    // Show winner
    if (data.leaderboard && data.leaderboard.length > 0) {
      const winner = data.leaderboard[0];
      const winnerName = this.getPlayerName(winner.player_id);

      this.elements.winnerName.textContent = winnerName;
      this.elements.winnerScore.textContent = `${winner.score} points`;

      // Show leaderboard
      this.elements.finalLeaderboardList.innerHTML = data.leaderboard.map((entry, index) => {
        const playerName = this.getPlayerName(entry.player_id);
        const position = index + 1;
        const correctCount = entry.correct_count || 0;
        const totalQuestions = data.total_questions || 5;
        const accuracy = totalQuestions > 0 ? Math.round((correctCount / totalQuestions) * 100) : 0;

        return `
          <div class="leaderboard-item">
            <div class="leaderboard-position">#${position}</div>
            <div class="leaderboard-player">${playerName}</div>
            <div class="leaderboard-stats">
              <div class="leaderboard-score">${entry.score}</div>
              <div class="leaderboard-correct">${correctCount}/${totalQuestions} correct (${accuracy}%)</div>
            </div>
          </div>
        `;
      }).join('');
    }

    // Update timer
    this.elements.timer.textContent = '';

    // Clear question timer
    if (this.questionTimer) {
      clearInterval(this.questionTimer);
    }
  }

  /**
   * Update player count
   */
  updatePlayerCount(count) {
    const plural = count === 1 ? 'player' : 'players';
    this.elements.playerCount.textContent = `${count} ${plural}`;
  }

  /**
   * Update connection status
   */
  updateConnectionStatus(state) {
    const indicator = this.elements.connectionStatus;

    switch (state) {
      case ConnectionState.CONNECTED:
        indicator.style.color = 'var(--color-success)';
        indicator.textContent = '●';
        break;
      case ConnectionState.DISCONNECTED:
        indicator.style.color = 'var(--color-error)';
        indicator.textContent = '○';
        break;
      case ConnectionState.CONNECTING:
        indicator.style.color = 'var(--color-warning)';
        indicator.textContent = '◐';
        break;
    }
  }
}

// Initialize display when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new TriviaDisplay();
  });
} else {
  new TriviaDisplay();
}

export default TriviaDisplay;
