import { Page, Locator, expect } from '@playwright/test';

/**
 * Page object for Controller Join screen
 */
export class ControllerJoinPage {
  readonly page: Page;

  // Step 1: Room Code
  readonly roomCodeInput: Locator;
  readonly continueButton: Locator;
  readonly createRoomButton: Locator;

  // Step 2: Player Name
  readonly playerNameInput: Locator;
  readonly joinButton: Locator;
  readonly backButton: Locator;

  // Create Room Modal
  readonly hostNameInput: Locator;
  readonly maxPlayersInput: Locator;
  readonly publicRoomCheckbox: Locator;
  readonly createRoomSubmitButton: Locator;
  readonly cancelButton: Locator;

  // Notifications
  readonly notification: Locator;

  constructor(page: Page) {
    this.page = page;

    // Step 1: Room Code
    this.roomCodeInput = page.locator('#room-code-input');
    this.continueButton = page.locator('button[type="submit"]').filter({ hasText: 'Continue' });
    this.createRoomButton = page.locator('#create-room-btn');

    // Step 2: Player Name
    this.playerNameInput = page.locator('#player-name-input');
    this.joinButton = page.locator('button[type="submit"]').filter({ hasText: 'Join' });
    this.backButton = page.locator('button').filter({ hasText: 'Back' });

    // Create Room Modal
    this.hostNameInput = page.locator('#host-name-input');
    this.maxPlayersInput = page.locator('#max-players-input');
    this.publicRoomCheckbox = page.locator('#public-room-checkbox');
    this.createRoomSubmitButton = page.locator('#create-room-submit');
    this.cancelButton = page.locator('button').filter({ hasText: 'Cancel' });

    // Notifications
    this.notification = page.locator('.notification');
  }

  async goto() {
    await this.page.goto('http://localhost:7070/controller/join.html');
    await this.page.waitForLoadState('networkidle');
  }

  async enterRoomCode(code: string) {
    await this.roomCodeInput.fill(code);
  }

  async clickContinue() {
    // Dispatch submit event to ensure proper event handling
    await this.page.locator('#room-code-form').evaluate((form: HTMLFormElement) => {
      const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
      form.dispatchEvent(submitEvent);
    });
  }

  async joinWithRoomCode(code: string) {
    await this.enterRoomCode(code);
    await this.clickContinue();
  }

  async enterPlayerName(name: string) {
    await this.playerNameInput.fill(name);
  }

  async clickJoin() {
    // Dispatch submit event to ensure proper event handling
    await this.page.locator('#player-name-form').evaluate((form: HTMLFormElement) => {
      const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
      form.dispatchEvent(submitEvent);
    });
  }

  async joinRoom(roomCode: string, playerName: string) {
    await this.goto();
    await this.joinWithRoomCode(roomCode);

    // Wait for player name input to become visible (after API validation completes)
    await this.playerNameInput.waitFor({ state: 'visible', timeout: 10000 });

    await this.enterPlayerName(playerName);
    await this.clickJoin();
    await this.page.waitForURL('**/lobby.html');

    // Wait for WebSocket to connect and room state to load
    await this.page.waitForFunction(
      () => {
        const connectionText = document.getElementById('connection-text');
        const playerName = document.getElementById('player-name');
        // Wait for both connection AND player name to be populated (not "---")
        return connectionText &&
               connectionText.textContent === 'Connected' &&
               playerName &&
               playerName.textContent !== '---' &&
               playerName.textContent !== '';
      },
      { timeout: 10000 }
    );
  }

  async openCreateRoomModal() {
    await this.createRoomButton.click();
  }

  async createRoom(hostName: string, maxPlayers: number = 12, isPublic: boolean = true) {
    await this.goto();

    // Click create room button to open modal
    await this.createRoomButton.click();

    // Wait for modal to appear
    await this.page.waitForSelector('#create-room-modal:not(.hidden)', { timeout: 5000 });

    // Fill in the form
    await this.hostNameInput.fill(hostName);
    await this.maxPlayersInput.fill(maxPlayers.toString());

    if (!isPublic) {
      await this.publicRoomCheckbox.uncheck();
    }

    // Submit the form and wait for navigation
    await Promise.all([
      this.page.waitForURL('**/lobby.html', { timeout: 15000 }),
      this.createRoomSubmitButton.click(),
    ]);

    // Wait for WebSocket to connect and room state to load
    await this.page.waitForFunction(
      () => {
        const connectionText = document.getElementById('connection-text');
        const playerName = document.getElementById('player-name');
        // Wait for both connection AND player name to be populated (not "---")
        return connectionText &&
               connectionText.textContent === 'Connected' &&
               playerName &&
               playerName.textContent !== '---' &&
               playerName.textContent !== '';
      },
      { timeout: 10000 }
    );
  }

  async getNotificationText(): Promise<string | null> {
    if (await this.notification.isVisible()) {
      return await this.notification.textContent();
    }
    return null;
  }

  async waitForNotification(text: string, timeout: number = 5000) {
    await this.notification.filter({ hasText: text }).waitFor({ timeout });
  }
}
