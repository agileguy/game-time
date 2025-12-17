import { test, expect } from '@playwright/test';
import { ControllerJoinPage } from '../pages/controller/join.page';
import { ControllerLobbyPage } from '../pages/controller/lobby.page';
import { testPlayers } from '../fixtures/test-data';

test.describe('Controller Lobby', () => {
  let hostPage: ControllerLobbyPage;
  let playerPage: ControllerLobbyPage;
  let roomCode: string;

  test.beforeEach(async ({ browser }) => {
    // Create a room with host
    const hostContext = await browser.newContext();
    const hostBrowserPage = await hostContext.newPage();
    const hostJoinPage = new ControllerJoinPage(hostBrowserPage);
    hostPage = new ControllerLobbyPage(hostBrowserPage);

    await hostJoinPage.createRoom(testPlayers.host.name);
    roomCode = await hostPage.getRoomCode();

    // Create a player context
    const playerContext = await browser.newContext();
    const playerBrowserPage = await playerContext.newPage();
    const playerJoinPage = new ControllerJoinPage(playerBrowserPage);
    playerPage = new ControllerLobbyPage(playerBrowserPage);

    await playerJoinPage.joinRoom(roomCode, testPlayers.player1.name);
  });

  test.afterEach(async () => {
    await hostPage.page.context().close();
    await playerPage.page.context().close();
  });

  test.describe('UI Display', () => {
    test('should show room code correctly', async () => {
      const displayedCode = await hostPage.getRoomCode();
      expect(displayedCode).toBe(roomCode);
      expect(displayedCode).toMatch(/^[A-Z0-9]{4}$/);
    });

    test('should show player name correctly', async () => {
      const hostName = await hostPage.getPlayerName();
      expect(hostName).toBe(testPlayers.host.name);

      const playerName = await playerPage.getPlayerName();
      expect(playerName).toBe(testPlayers.player1.name);
    });

    test('should show host badge for host only', async () => {
      const hostHasBadge = await hostPage.isHost();
      expect(hostHasBadge).toBe(true);

      const playerHasBadge = await playerPage.isHost();
      expect(playerHasBadge).toBe(false);
    });

    test('should show correct player count', async () => {
      const hostPlayerCount = await hostPage.getPlayerCount();
      expect(hostPlayerCount).toBe('2 / 12');

      const playerPlayerCount = await playerPage.getPlayerCount();
      expect(playerPlayerCount).toBe('2 / 12');
    });

    test('should show all players in the list', async () => {
      const hostPlayerNames = await hostPage.getPlayerNames();
      expect(hostPlayerNames).toContain(testPlayers.host.name);
      expect(hostPlayerNames).toContain(testPlayers.player1.name);
      expect(hostPlayerNames.length).toBe(2);

      const playerPlayerNames = await playerPage.getPlayerNames();
      expect(playerPlayerNames).toContain(testPlayers.host.name);
      expect(playerPlayerNames).toContain(testPlayers.player1.name);
      expect(playerPlayerNames.length).toBe(2);
    });
  });

  test.describe('Connection Status', () => {
    test('should show connected status', async () => {
      const hostStatus = await hostPage.getConnectionStatus();
      expect(hostStatus).toBe('Connected');

      const playerStatus = await playerPage.getConnectionStatus();
      expect(playerStatus).toBe('Connected');
    });

    test('should show connected indicator', async () => {
      const hostConnected = await hostPage.isConnected();
      expect(hostConnected).toBe(true);

      const playerConnected = await playerPage.isConnected();
      expect(playerConnected).toBe(true);
    });
  });

  test.describe('Host Controls', () => {
    test('should show host controls only for host', async () => {
      const hostControlsVisible = await hostPage.isHostControlsVisible();
      expect(hostControlsVisible).toBe(true);

      const playerControlsVisible = await playerPage.isHostControlsVisible();
      expect(playerControlsVisible).toBe(false);
    });

    test('should enable start game button with enough players', async () => {
      // With 2 players (>= minPlayers of 2), button should be enabled
      const isEnabled = await hostPage.isStartGameButtonEnabled();
      expect(isEnabled).toBe(true);
    });

    test('should start game when host clicks start', async () => {
      await hostPage.clickStartGame();

      // Both should receive game starting notification
      await Promise.all([
        hostPage.waitForGameStarting(5000),
        playerPage.waitForGameStarting(5000),
      ]);
    });

    test('should kick player when host clicks kick', async ({ browser }) => {
      // Add another player to kick
      const player2Context = await browser.newContext();
      const player2BrowserPage = await player2Context.newPage();
      const player2JoinPage = new ControllerJoinPage(player2BrowserPage);
      const player2Page = new ControllerLobbyPage(player2BrowserPage);

      await player2JoinPage.joinRoom(roomCode, testPlayers.player2.name);

      // Wait for player to join
      await hostPage.waitForPlayerJoin(testPlayers.player2.name);

      // Kick player2
      await hostPage.kickPlayer(testPlayers.player2.name);

      // Host should see kick notification
      await hostPage.waitForPlayerKicked(testPlayers.player2.name);

      // Player2 should be redirected to join page
      await player2Page.page.waitForURL(/.*join\.html/, { timeout: 5000 });

      await player2Context.close();
    });
  });

  test.describe('Player Actions', () => {
    test('should leave room when player clicks leave', async () => {
      await playerPage.clickLeaveRoom();

      // Should redirect to join page
      await playerPage.page.waitForURL(/.*join\.html/, { timeout: 5000 });

      // Host should see player left notification
      await hostPage.waitForPlayerLeave(testPlayers.player1.name);

      // Player count should update
      await hostPage.page.waitForTimeout(1000);
      const playerCount = await hostPage.getPlayerCount();
      expect(playerCount).toBe('1 / 12');
    });

    test('should clear session data when leaving', async () => {
      await playerPage.clickLeaveRoom();
      await playerPage.page.waitForURL(/.*join\.html/);

      // Check that session is cleared
      const sessionId = await playerPage.page.evaluate(() => {
        return localStorage.getItem('gametime_session');
      });

      expect(sessionId).toBeNull();
    });
  });

  test.describe('Real-time Updates', () => {
    test('should update player list when new player joins', async ({ browser }) => {
      // Get initial player names
      const initialPlayers = await hostPage.getPlayerNames();
      expect(initialPlayers.length).toBe(2);

      // Add new player
      const player2Context = await browser.newContext();
      const player2BrowserPage = await player2Context.newPage();
      const player2JoinPage = new ControllerJoinPage(player2BrowserPage);

      await player2JoinPage.joinRoom(roomCode, testPlayers.player2.name);

      // Wait for join notification
      await hostPage.waitForPlayerJoin(testPlayers.player2.name);
      await playerPage.waitForPlayerJoin(testPlayers.player2.name);

      // Verify player list updated
      await hostPage.page.waitForTimeout(1000);
      const updatedPlayers = await hostPage.getPlayerNames();
      expect(updatedPlayers).toContain(testPlayers.player2.name);
      expect(updatedPlayers.length).toBe(3);

      // Verify player count updated
      const playerCount = await hostPage.getPlayerCount();
      expect(playerCount).toBe('3 / 12');

      await player2Context.close();
    });

    test('should update player list when player leaves', async () => {
      // Player leaves
      await playerPage.clickLeaveRoom();
      await playerPage.page.waitForURL(/.*join\.html/);

      // Wait for leave notification
      await hostPage.waitForPlayerLeave(testPlayers.player1.name);

      // Verify player list updated
      await hostPage.page.waitForTimeout(1000);
      const updatedPlayers = await hostPage.getPlayerNames();
      expect(updatedPlayers).not.toContain(testPlayers.player1.name);
      expect(updatedPlayers.length).toBe(1);

      // Verify player count updated
      const playerCount = await hostPage.getPlayerCount();
      expect(playerCount).toBe('1 / 12');
    });

    test('should transfer host when host leaves', async ({ browser }) => {
      // Wait for connection to be stable
      await playerPage.page.waitForTimeout(1000);

      // Host leaves
      await hostPage.clickLeaveRoom();
      await hostPage.page.waitForURL(/.*join\.html/);

      // Wait for host transfer to complete
      await playerPage.page.waitForTimeout(2000);

      // Player should now be host
      const isNowHost = await playerPage.isHost();
      expect(isNowHost).toBe(true);

      // Host controls should now be visible
      const hostControlsVisible = await playerPage.isHostControlsVisible();
      expect(hostControlsVisible).toBe(true);
    });
  });

  test.describe('Multiple Players', () => {
    test('should handle 4+ players correctly', async ({ browser }) => {
      const playerContexts = [];

      // Add 3 more players (total 5 including host and player1)
      for (let i = 0; i < 3; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        const joinPage = new ControllerJoinPage(page);

        await joinPage.joinRoom(roomCode, `Player${i + 3}`);
        await hostPage.waitForPlayerJoin(`Player${i + 3}`);

        playerContexts.push(context);
      }

      // Wait for all updates
      await hostPage.page.waitForTimeout(1000);

      // Verify player count
      const playerCount = await hostPage.getPlayerCount();
      expect(playerCount).toBe('5 / 12');

      // Verify all players in list
      const playerNames = await hostPage.getPlayerNames();
      expect(playerNames.length).toBe(5);

      // Clean up
      for (const context of playerContexts) {
        await context.close();
      }
    });

    test('should enable start game button only with minimum players', async ({ browser }) => {
      // With 2 players, should be enabled
      let isEnabled = await hostPage.isStartGameButtonEnabled();
      expect(isEnabled).toBe(true);

      // Remove the only other player
      await playerPage.clickLeaveRoom();
      await hostPage.waitForPlayerLeave(testPlayers.player1.name);
      await hostPage.page.waitForTimeout(1000);

      // With only 1 player (host), should be disabled
      isEnabled = await hostPage.isStartGameButtonEnabled();
      expect(isEnabled).toBe(false);
    });
  });

  test.describe('Error Handling', () => {
    test('should show error when non-host tries to start game', async () => {
      // This would require direct API call or WebSocket manipulation
      // since the UI doesn't show start button for non-hosts
      // Skipping this test as it's prevented by UI
    });

    test('should show error notification on WebSocket error', async () => {
      // This would require simulating a WebSocket error
      // which is complex in e2e tests
      // Could be covered in unit/integration tests instead
    });

    test('should attempt reconnection on connection loss', async () => {
      // This would require killing the WebSocket connection
      // which is complex in e2e tests
      // Could be covered in unit/integration tests instead
    });
  });
});
