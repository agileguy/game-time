/**
 * Controller Trivia Screen
 * Handles question answering interface for players
 */

import CONFIG from '../../shared/js/config.js';
import { storage, logger } from '../../shared/js/utils.js';
import { appState } from '../../shared/js/state-manager.js';
import WebSocketClient, { ConnectionState } from '../../shared/js/websocket-client.js';
import notifications from '../../shared/js/components/notifications.js';

class TriviaController {
  constructor() {
    this.ws = null;
    this.sessionId = null;
    this.roomCode = null;
    this.gameState = null;
    this.currentAnswer = null;
    this.playerScore = 0;
    this.currentPhase = null; // Track current phase to detect transitions
    this.questionTimer = null;
    this.questionStartTime = null;

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
      phaseText: document.getElementById('phase-text'),
      phaseTimer: document.getElementById('phase-timer'),

      // Question phase
      questionPhase: document.getElementById('question-phase'),
      questionCounter: document.getElementById('question-counter'),
      questionCategory: document.getElementById('question-category'),
      questionText: document.getElementById('question-text'),
      answerOptions: document.getElementById('answer-options'),
      answerStatus: document.getElementById('answer-status'),

      // Results phase
      resultsPhase: document.getElementById('results-phase'),
      resultIcon: document.getElementById('result-icon'),
      resultText: document.getElementById('result-text'),
      correctAnswer: document.getElementById('correct-answer'),
      basePoints: document.getElementById('base-points'),
      speedBonus: document.getElementById('speed-bonus'),
      roundScore: document.getElementById('round-score'),
      totalScore: document.getElementById('total-score'),
      scoreBreakdown: document.getElementById('score-breakdown'),

      // Final phase
      finalPhase: document.getElementById('final-phase'),
      finalIcon: document.getElementById('final-icon'),
      finalTitle: document.getElementById('final-title'),
      finalSubtitle: document.getElementById('final-subtitle'),
      finalScoreValue: document.getElementById('final-score-value'),
      correctCount: document.getElementById('correct-count'),
      accuracy: document.getElementById('accuracy'),
      finalMessageText: document.getElementById('final-message-text'),

      // Waiting phase
      waitingPhase: document.getElementById('waiting-phase'),

      // Footer
      roomCode: document.getElementById('room-code'),
      progressDots: document.getElementById('progress-dots'),
    };

    // Cache answer buttons
    this.answerButtons = Array.from(this.elements.answerOptions.querySelectorAll('.answer-btn'));
  }

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    // Answer button clicks
    this.answerButtons.forEach((btn, index) => {
      btn.addEventListener('click', () => {
        this.submitAnswer(index);
      });
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

    // Error
    this.ws.on('error', (data) => {
      logger.error('WebSocket error:', data);
      notifications.error(data.message || 'An error occurred');
    });

    // Game finished
    this.ws.on('game_finished', (data) => {
      logger.info('Game finished:', data);
      this.handleGameFinished(data);
    });
  }

  /**
   * Handle game started
   */
  handleGameStarted(data) {
    logger.info('Trivia game started');
    // Initial state will come through game_state_update
  }

  /**
   * Handle game state update
   */
  handleGameStateUpdate(data) {
    const isPhaseTransition = this.currentPhase !== data.phase;
    this.currentPhase = data.phase;

    this.gameState = data;
    this.playerScore = data.your_score || 0;

    // Update score display
    this.elements.playerScore.textContent = this.playerScore;

    // Update progress dots
    if (data.current_question_index !== undefined && data.total_questions) {
      this.updateProgressDots(data.current_question_index, data.total_questions);
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

    // Only reset on phase transition (not every state update)
    if (isPhaseTransition) {
      this.currentAnswer = data.your_answer;
      this.elements.answerStatus.classList.add('hidden');

      // Reset question timer
      if (this.questionTimer) {
        clearInterval(this.questionTimer);
      }
    }

    const question = data.current_question;
    if (!question) {
      logger.warn('No current question in state');
      return;
    }

    // Update question header
    const questionNum = (data.current_question_index || 0) + 1;
    const totalQuestions = data.total_questions || 5;
    this.elements.questionCounter.textContent = `Question ${questionNum} of ${totalQuestions}`;
    this.elements.questionCategory.textContent = question.category || 'General';

    // Update question text
    this.elements.questionText.textContent = question.question;

    // Update answer options
    if (question.options && question.options.length === 4) {
      const letters = ['A', 'B', 'C', 'D'];
      this.answerButtons.forEach((btn, index) => {
        const letterSpan = btn.querySelector('.answer-letter');
        const textSpan = btn.querySelector('.answer-text');

        letterSpan.textContent = letters[index];
        textSpan.textContent = question.options[index];

        // Highlight selected answer
        if (data.your_answer === index) {
          btn.classList.add('selected');
          btn.classList.add('disabled');
        } else {
          btn.classList.remove('selected');
          // Only disable if already answered
          if (data.your_answer !== null && data.your_answer !== undefined) {
            btn.classList.add('disabled');
          } else {
            btn.classList.remove('disabled');
          }
        }
      });
    }

    // Show answer status if already answered
    if (data.your_answer !== null && data.your_answer !== undefined) {
      this.elements.answerStatus.classList.remove('hidden');
    }

    // Start countdown timer (only on phase transition)
    if (isPhaseTransition && data.question_start_time && data.answer_time) {
      this.startQuestionTimer(data.question_start_time, data.answer_time);
    }

    // Update phase indicator
    this.elements.phaseText.textContent = 'Question';
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

      this.elements.phaseTimer.textContent = `${Math.ceil(remaining)}s`;

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
   * Submit answer
   */
  async submitAnswer(answerIndex) {
    // Prevent duplicate submissions
    if (this.currentAnswer !== null && this.currentAnswer !== undefined) {
      logger.debug('Answer already submitted');
      return;
    }

    if (this.currentPhase !== 'setup') {
      logger.warn('Cannot submit answer in phase:', this.currentPhase);
      return;
    }

    // Mark as submitted immediately for UI feedback
    this.currentAnswer = answerIndex;

    // Update UI
    this.answerButtons.forEach((btn, index) => {
      if (index === answerIndex) {
        btn.classList.add('selected');
      }
      btn.classList.add('disabled');
    });

    this.elements.answerStatus.classList.remove('hidden');

    // Send to server
    try {
      await this.ws.sendGameAction('submit_answer', { answer: answerIndex });
      logger.info('Answer submitted:', answerIndex);
    } catch (error) {
      logger.error('Failed to submit answer:', error);
      notifications.error('Failed to submit answer');

      // Reset on error
      this.currentAnswer = null;
      this.answerButtons.forEach(btn => {
        btn.classList.remove('selected', 'disabled');
      });
      this.elements.answerStatus.classList.add('hidden');
    }
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

    const playerAnswer = data.your_answer;
    const correctAnswer = question.correct_answer;
    const isCorrect = playerAnswer === correctAnswer;
    const lastScore = data.last_score || 0;

    // Update result icon and text
    if (playerAnswer === null || playerAnswer === undefined) {
      // No answer
      this.elements.resultIcon.className = 'result-icon no-answer';
      this.elements.resultIcon.textContent = '⏱';
      this.elements.resultText.className = 'result-text no-answer';
      this.elements.resultText.textContent = 'Time\'s Up!';
    } else if (isCorrect) {
      // Correct
      this.elements.resultIcon.className = 'result-icon correct';
      this.elements.resultIcon.textContent = '✓';
      this.elements.resultText.className = 'result-text correct';
      this.elements.resultText.textContent = 'Correct!';
    } else {
      // Incorrect
      this.elements.resultIcon.className = 'result-icon incorrect';
      this.elements.resultIcon.textContent = '✗';
      this.elements.resultText.className = 'result-text incorrect';
      this.elements.resultText.textContent = 'Wrong Answer';
    }

    // Show correct answer
    const letters = ['A', 'B', 'C', 'D'];
    const correctLetter = letters[correctAnswer];
    const correctText = question.options[correctAnswer];

    this.elements.correctAnswer.innerHTML = `
      <span class="answer-letter">${correctLetter}</span>
      <span class="answer-text">${correctText}</span>
    `;

    // Show score breakdown only if answered
    if (isCorrect) {
      this.elements.scoreBreakdown.classList.remove('hidden');

      const basePoints = 100;
      const speedBonus = lastScore - basePoints;

      this.elements.basePoints.textContent = `+${basePoints}`;
      this.elements.speedBonus.textContent = `+${speedBonus}`;
      this.elements.roundScore.textContent = `+${lastScore}`;
    } else {
      this.elements.scoreBreakdown.classList.add('hidden');
    }

    // Update total score
    this.elements.totalScore.textContent = data.your_score || 0;

    // Update phase indicator
    this.elements.phaseText.textContent = 'Results';
    this.elements.phaseTimer.textContent = '5s';

    // Clear question timer
    if (this.questionTimer) {
      clearInterval(this.questionTimer);
    }

    // Reset for next question
    this.currentAnswer = null;
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

    // Determine placement
    const allScores = data.all_scores || {};
    const yourScore = data.your_score || 0;
    const sortedScores = Object.values(allScores).sort((a, b) => b - a);
    const placement = sortedScores.indexOf(yourScore) + 1;
    const totalPlayers = sortedScores.length;

    // Update icon based on placement
    if (placement === 1) {
      this.elements.finalIcon.textContent = '🏆';
      this.elements.finalSubtitle.textContent = '1st Place!';
      this.elements.finalMessageText.textContent = 'Champion! 🎉';
    } else if (placement === 2) {
      this.elements.finalIcon.textContent = '🥈';
      this.elements.finalSubtitle.textContent = '2nd Place!';
      this.elements.finalMessageText.textContent = 'Great job! 👏';
    } else if (placement === 3) {
      this.elements.finalIcon.textContent = '🥉';
      this.elements.finalSubtitle.textContent = '3rd Place!';
      this.elements.finalMessageText.textContent = 'Well done! 👍';
    } else {
      this.elements.finalIcon.textContent = '🎯';
      this.elements.finalSubtitle.textContent = `${placement}${this.getOrdinalSuffix(placement)} Place`;
      this.elements.finalMessageText.textContent = 'Good effort! 💪';
    }

    // Update stats
    const correctCount = data.correct_count || 0;
    const totalQuestions = data.total_questions || 5;
    const accuracy = totalQuestions > 0 ? Math.round((correctCount / totalQuestions) * 100) : 0;

    this.elements.finalScoreValue.textContent = yourScore;
    this.elements.correctCount.textContent = `${correctCount}/5`;
    this.elements.accuracy.textContent = `${accuracy}%`;

    // Update phase indicator
    this.elements.phaseText.textContent = 'Finished';
    this.elements.phaseTimer.textContent = '';

    // Clear question timer
    if (this.questionTimer) {
      clearInterval(this.questionTimer);
    }
  }

  /**
   * Get ordinal suffix for placement
   */
  getOrdinalSuffix(num) {
    const j = num % 10;
    const k = num % 100;
    if (j === 1 && k !== 11) return 'st';
    if (j === 2 && k !== 12) return 'nd';
    if (j === 3 && k !== 13) return 'rd';
    return 'th';
  }

  /**
   * Update progress dots
   */
  updateProgressDots(currentIndex, totalQuestions) {
    const dots = this.elements.progressDots.querySelectorAll('.dot');

    dots.forEach((dot, index) => {
      dot.classList.remove('active', 'completed');

      if (index < currentIndex) {
        dot.classList.add('completed');
      } else if (index === currentIndex) {
        dot.classList.add('active');
      }
    });
  }

  /**
   * Handle game action response
   */
  handleGameActionResponse(data) {
    if (data.success === false) {
      logger.error('Game action failed:', data.error);
      notifications.error(data.error || 'Action failed');
    }
  }

  /**
   * Handle game finished
   */
  handleGameFinished(data) {
    logger.info('Game finished');
    // State update will trigger final phase display
  }

  /**
   * Update connection status
   */
  updateConnectionStatus(state) {
    const indicator = this.elements.connectionIndicator;

    indicator.classList.remove('connected', 'disconnected', 'connecting');

    switch (state) {
      case ConnectionState.CONNECTED:
        indicator.classList.add('connected');
        break;
      case ConnectionState.DISCONNECTED:
        indicator.classList.add('disconnected');
        notifications.warning('Connection lost. Attempting to reconnect...');
        break;
      case ConnectionState.CONNECTING:
        indicator.classList.add('connecting');
        break;
    }
  }
}

// Initialize controller when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new TriviaController();
  });
} else {
  new TriviaController();
}

export default TriviaController;
