import { Page, Locator } from '@playwright/test';

/**
 * Page object for Display Lobby screen (TV/Projector view)
 */
export class DisplayLobbyPage {
  readonly page: Page;

  // Header
  readonly gameTitle: Locator;
  readonly connectionIndicator: Locator;
  readonly connectionText: Locator;

  // Room Code Section
  readonly roomCodeLabel: Locator;
  readonly roomCode: Locator;
  readonly joinUrl: Locator;

  // Players Section
  readonly sectionTitle: Locator;
  readonly playerCount: Locator;
  readonly playersGrid: Locator;
  readonly waitingMessage: Locator;

  // Game Status Section
  readonly statusMessage: Locator;
  readonly startCountdown: Locator;
  readonly countdownNumber: Locator;

  // Footer
  readonly gameMode: Locator;
  readonly hostName: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.gameTitle = page.locator('.game-title');
    this.connectionIndicator = page.locator('#connection-indicator');
    this.connectionText = page.locator('#connection-text');

    // Room Code Section
    this.roomCodeLabel = page.locator('.room-code-label');
    this.roomCode = page.locator('#room-code');
    this.joinUrl = page.locator('#join-url');

    // Players Section
    this.sectionTitle = page.locator('.section-title');
    this.playerCount = page.locator('#player-count');
    this.playersGrid = page.locator('#players-grid');
    this.waitingMessage = page.locator('#waiting-message');

    // Game Status Section
    this.statusMessage = page.locator('#status-message');
    this.startCountdown = page.locator('#start-countdown');
    this.countdownNumber = page.locator('#countdown-number');

    // Footer
    this.gameMode = page.locator('#game-mode');
    this.hostName = page.locator('#host-name');
  }

  async goto() {
    await this.page.goto('http://localhost:7070/display/lobby.html');
    await this.page.waitForLoadState('networkidle');
  }

  async getRoomCode(): Promise<string> {
    return await this.roomCode.textContent() || '';
  }

  async getConnectionStatus(): Promise<string> {
    return await this.connectionText.textContent() || '';
  }

  async isConnected(): Promise<boolean> {
    return await this.connectionIndicator.evaluate((el) => el.classList.contains('connected'));
  }

  async getPlayerCount(): Promise<string> {
    return await this.playerCount.textContent() || '';
  }

  async isWaitingMessageVisible(): Promise<boolean> {
    return await this.waitingMessage.isVisible();
  }

  async getPlayerNames(): Promise<string[]> {
    const playerCards = await this.playersGrid.locator('.player-card').all();
    const names: string[] = [];

    for (const card of playerCards) {
      const name = await card.locator('.player-name').textContent();
      if (name) names.push(name);
    }

    return names;
  }

  async getHostName(): Promise<string> {
    return await this.hostName.textContent() || '';
  }

  async getGameMode(): Promise<string> {
    return await this.gameMode.textContent() || '';
  }

  async getStatusMessage(): Promise<string | null> {
    if (await this.statusMessage.isVisible()) {
      return await this.statusMessage.textContent();
    }
    return null;
  }

  async isCountdownVisible(): Promise<boolean> {
    return await this.startCountdown.isVisible();
  }

  async getCountdownNumber(): Promise<string> {
    return await this.countdownNumber.textContent() || '';
  }

  async waitForCountdownToAppear(timeout: number = 5000) {
    await this.startCountdown.waitFor({ state: 'visible', timeout });
  }

  async waitForCountdownToDisappear(timeout: number = 5000) {
    await this.startCountdown.waitFor({ state: 'hidden', timeout });
  }

  async waitForPlayerJoinMessage(playerName: string, timeout: number = 5000) {
    await this.statusMessage.filter({ hasText: `${playerName} joined!` }).waitFor({ timeout });
  }

  async waitForPlayerLeaveMessage(playerName: string, timeout: number = 5000) {
    await this.statusMessage.filter({ hasText: `${playerName} left` }).waitFor({ timeout });
  }

  async waitForHostTransferMessage(newHostName: string, timeout: number = 5000) {
    await this.statusMessage.filter({ hasText: `${newHostName} is now the host` }).waitFor({ timeout });
  }

  async waitForGameStartingMessage(timeout: number = 5000) {
    await this.statusMessage.filter({ hasText: 'Game Starting!' }).waitFor({ timeout });
  }
}
