/**
 * Controller Join Screen
 * Handles room code entry and player name entry
 */

import CONFIG from '../../shared/js/config.js';
import { storage, validators, api, logger } from '../../shared/js/utils.js';
import notifications from '../../shared/js/components/notifications.js';

class JoinController {
  constructor() {
    this.currentStep = 'room-code';
    this.roomCode = null;
    this.init();
  }

  /**
   * Initialize controller
   */
  init() {
    this.cacheElements();
    this.attachEventListeners();
    this.restoreState();
  }

  /**
   * Cache DOM elements
   */
  cacheElements() {
    this.elements = {
      // Steps
      stepRoomCode: document.getElementById('step-room-code'),
      stepPlayerName: document.getElementById('step-player-name'),
      loadingState: document.getElementById('loading-state'),

      // Forms
      roomCodeForm: document.getElementById('room-code-form'),
      playerNameForm: document.getElementById('player-name-form'),

      // Inputs
      roomCodeInput: document.getElementById('room-code-input'),
      playerNameInput: document.getElementById('player-name-input'),

      // Buttons
      createRoomBtn: document.getElementById('create-room-btn'),
      backBtn: document.getElementById('back-btn'),
    };
  }

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    // Room code form
    this.elements.roomCodeForm.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleRoomCodeSubmit();
    });

    // Auto-format room code input
    this.elements.roomCodeInput.addEventListener('input', (e) => {
      e.target.value = validators.sanitizeRoomCode(e.target.value);
    });

    // Player name form
    this.elements.playerNameForm.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handlePlayerNameSubmit();
    });

    // Create room button
    this.elements.createRoomBtn.addEventListener('click', () => {
      this.handleCreateRoom();
    });

    // Back button
    this.elements.backBtn.addEventListener('click', () => {
      this.showStep('room-code');
    });
  }

  /**
   * Restore state from localStorage
   */
  restoreState() {
    const savedRoomCode = storage.getRoomCode();
    const savedPlayerName = storage.getPlayerName();

    if (savedRoomCode) {
      this.elements.roomCodeInput.value = savedRoomCode;
    }

    if (savedPlayerName) {
      this.elements.playerNameInput.value = savedPlayerName;
    }
  }

  /**
   * Handle room code submission
   */
  async handleRoomCodeSubmit() {
    const roomCode = this.elements.roomCodeInput.value.trim().toUpperCase();

    // Validate room code
    if (!validators.isValidRoomCode(roomCode)) {
      notifications.error('Please enter a valid 4-character room code');
      this.elements.roomCodeInput.focus();
      return;
    }

    // Check if room exists
    this.showLoading();

    try {
      await api.getRoomDetails(roomCode);
      this.roomCode = roomCode;
      storage.setRoomCode(roomCode);
      this.showStep('player-name');
      this.elements.playerNameInput.focus();
    } catch (error) {
      logger.error('Room not found:', error);
      notifications.error('Room not found. Please check the code and try again.');
      this.showStep('room-code');
      this.elements.roomCodeInput.select();
    }
  }

  /**
   * Handle player name submission
   */
  async handlePlayerNameSubmit() {
    const playerName = this.elements.playerNameInput.value.trim();

    // Validate player name
    if (!validators.isValidPlayerName(playerName)) {
      notifications.error('Please enter a valid name (1-50 characters)');
      this.elements.playerNameInput.focus();
      return;
    }

    const sanitizedName = validators.sanitizePlayerName(playerName);

    // Join room
    this.showLoading();

    try {
      const response = await api.joinRoom(this.roomCode, sanitizedName);

      logger.info('Joined room:', response);

      // Save session data
      storage.setSessionId(response.session_id);
      storage.setPlayerName(sanitizedName);
      storage.setRoomCode(this.roomCode);

      // Redirect to lobby
      window.location.href = 'lobby.html';
    } catch (error) {
      logger.error('Join room error:', error);

      if (error.message.includes('full')) {
        notifications.error('Room is full. Please try a different room.');
      } else if (error.message.includes('not in lobby')) {
        notifications.error('Game has already started. Please try a different room.');
      } else {
        notifications.error('Failed to join room. Please try again.');
      }

      this.showStep('player-name');
      this.elements.playerNameInput.focus();
    }
  }

  /**
   * Handle create room
   */
  async handleCreateRoom() {
    // Check if player name is already saved
    let playerName = storage.getPlayerName();

    if (!playerName) {
      playerName = prompt('Enter your name:');

      if (!playerName || !validators.isValidPlayerName(playerName)) {
        notifications.error('Please enter a valid name');
        return;
      }
    }

    const sanitizedName = validators.sanitizePlayerName(playerName);

    this.showLoading();

    try {
      const response = await api.createRoom(sanitizedName);

      logger.info('Created room:', response);

      // Save session data
      storage.setSessionId(response.session_id);
      storage.setPlayerName(sanitizedName);
      storage.setRoomCode(response.room_code);

      // Redirect to lobby
      window.location.href = 'lobby.html';
    } catch (error) {
      logger.error('Create room error:', error);
      notifications.error('Failed to create room. Please try again.');
      this.showStep('room-code');
    }
  }

  /**
   * Show specific step
   * @param {string} step - Step to show ('room-code' or 'player-name')
   */
  showStep(step) {
    this.currentStep = step;

    // Hide all steps
    this.elements.stepRoomCode.classList.add('hidden');
    this.elements.stepPlayerName.classList.add('hidden');
    this.elements.loadingState.classList.add('hidden');

    // Show requested step
    if (step === 'room-code') {
      this.elements.stepRoomCode.classList.remove('hidden');
      this.elements.roomCodeInput.focus();
    } else if (step === 'player-name') {
      this.elements.stepPlayerName.classList.remove('hidden');
      this.elements.playerNameInput.focus();
    }
  }

  /**
   * Show loading state
   */
  showLoading() {
    this.elements.stepRoomCode.classList.add('hidden');
    this.elements.stepPlayerName.classList.add('hidden');
    this.elements.loadingState.classList.remove('hidden');
  }
}

// Initialize controller when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new JoinController();
});
