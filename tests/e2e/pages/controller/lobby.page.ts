import { Page, Locator } from '@playwright/test';

/**
 * Page object for Controller Lobby screen
 */
export class ControllerLobbyPage {
  readonly page: Page;

  // Header
  readonly roomCode: Locator;
  readonly connectionIndicator: Locator;
  readonly connectionText: Locator;

  // Player Info
  readonly playerName: Locator;
  readonly hostBadge: Locator;

  // Players Section
  readonly playerCount: Locator;
  readonly playersList: Locator;

  // Host Controls
  readonly hostControls: Locator;
  readonly startGameButton: Locator;

  // Player Controls
  readonly leaveRoomButton: Locator;

  // Notifications
  readonly notification: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.roomCode = page.locator('#room-code');
    this.connectionIndicator = page.locator('#connection-indicator');
    this.connectionText = page.locator('#connection-text');

    // Player Info
    this.playerName = page.locator('#player-name');
    this.hostBadge = page.locator('#host-badge');

    // Players Section
    this.playerCount = page.locator('#player-count');
    this.playersList = page.locator('#players-list');

    // Host Controls
    this.hostControls = page.locator('#host-controls');
    this.startGameButton = page.locator('#start-game-btn');

    // Player Controls
    this.leaveRoomButton = page.locator('#leave-room-btn');

    // Notifications
    this.notification = page.locator('.notification');
  }

  async goto() {
    await this.page.goto('http://localhost:7070/controller/lobby.html');
    await this.page.waitForLoadState('networkidle');
  }

  async getRoomCode(): Promise<string> {
    return await this.roomCode.textContent() || '';
  }

  async getPlayerName(): Promise<string> {
    return await this.playerName.textContent() || '';
  }

  async isHost(): Promise<boolean> {
    return await this.hostBadge.isVisible();
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

  async getPlayerNames(): Promise<string[]> {
    const playerCards = await this.playersList.locator('.player-card').all();
    const names: string[] = [];

    for (const card of playerCards) {
      const name = await card.locator('.player-name').textContent();
      if (name) names.push(name);
    }

    return names;
  }

  async isHostControlsVisible(): Promise<boolean> {
    return await this.hostControls.isVisible();
  }

  async isStartGameButtonEnabled(): Promise<boolean> {
    return await this.startGameButton.isEnabled();
  }

  async clickStartGame() {
    await this.startGameButton.click();
  }

  async clickLeaveRoom() {
    // Handle the confirmation dialog
    this.page.on('dialog', dialog => dialog.accept());
    await this.leaveRoomButton.click();
  }

  async kickPlayer(playerName: string) {
    const playerCard = this.playersList.locator('.player-card').filter({ hasText: playerName });
    const kickButton = playerCard.locator('button').filter({ hasText: 'Kick' });

    // Handle the confirmation dialog
    this.page.on('dialog', dialog => dialog.accept());
    await kickButton.click();
  }

  async waitForPlayerJoin(playerName: string, timeout: number = 5000) {
    await this.notification.filter({ hasText: `${playerName} joined!` }).waitFor({ timeout });
  }

  async waitForPlayerLeave(playerName: string, timeout: number = 5000) {
    await this.notification.filter({ hasText: `${playerName} left` }).waitFor({ timeout });
  }

  async waitForPlayerKicked(playerName: string, timeout: number = 5000) {
    await this.page.waitForFunction(
      (name) => {
        const history = window.__notificationHistory || [];
        return history.some((n) => n.message.includes(`${name} was kicked`));
      },
      playerName,
      { timeout }
    );
  }

  async waitForHostTransfer(newHostName: string, timeout: number = 5000) {
    await this.page.waitForFunction(
      (name) => {
        const history = window.__notificationHistory || [];
        // Check for either "You are now the host!" (if this player became host)
        // or "{name} is now the host" (if another player became host)
        return history.some((n) =>
          n.message.includes('You are now the host') ||
          n.message.includes(`${name} is now the host`)
        );
      },
      newHostName,
      { timeout }
    );
  }

  async waitForGameStarting(timeout: number = 5000) {
    await this.page.waitForFunction(
      () => {
        const history = window.__notificationHistory || [];
        return history.some((n) => n.message.includes('Starting game'));
      },
      {},
      { timeout }
    );
  }

  async getNotificationText(): Promise<string | null> {
    if (await this.notification.isVisible()) {
      return await this.notification.textContent();
    }
    return null;
  }
}
