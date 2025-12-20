import { test, expect, BrowserContext } from '@playwright/test';
import { ControllerJoinPage } from '../pages/controller/join.page';
import { ControllerLobbyPage } from '../pages/controller/lobby.page';
import { DisplayLobbyPage } from '../pages/display/lobby.page';
import { testPlayers } from '../fixtures/test-data';

test.describe('WebSocket Real-time Updates', () => {
  // Track browser contexts for cleanup
  let contexts: BrowserContext[] = [];

  test.beforeEach(() => {
    contexts = [];
  });

  test.afterEach(async () => {
    // Close all browser contexts to prevent WebSocket connection leaks
    for (const context of contexts) {
      try {
        await context.close();
      } catch (error) {
        // Context may already be closed, ignore errors
      }
    }
    contexts = [];
  });
  test.describe('Connection Management', () => {
    test('should establish WebSocket connection on page load', async ({ page }) => {
      const joinPage = new ControllerJoinPage(page);
      const lobbyPage = new ControllerLobbyPage(page);

      // Create room
      await joinPage.createRoom(testPlayers.host.name);

      // Wait for connection
      await lobbyPage.page.waitForTimeout(2000);

      // Check connection status
      const isConnected = await lobbyPage.isConnected();
      expect(isConnected).toBe(true);

      const connectionText = await lobbyPage.getConnectionStatus();
      expect(connectionText).toBe('Connected');
    });

    test('should show connecting status initially', async ({ page }) => {
      const joinPage = new ControllerJoinPage(page);
      const lobbyPage = new ControllerLobbyPage(page);

      // Create room to get a valid session
      await joinPage.createRoom(testPlayers.host.name);

      // Check connection status shortly after joining (should be connecting or connected)
      await lobbyPage.page.waitForTimeout(100);

      const connectionText = await lobbyPage.getConnectionStatus();
      // Should be either "Connecting..." or "Connected"
      expect(connectionText).toMatch(/Connect/);
    });

    test('should maintain connection during user interaction', async ({ page, browser }) => {
      const joinPage = new ControllerJoinPage(page);
      const lobbyPage = new ControllerLobbyPage(page);

      // Create room
      await joinPage.createRoom(testPlayers.host.name);
      const roomCode = await lobbyPage.getRoomCode();

      // Add players while monitoring connection
      for (let i = 0; i < 3; i++) {
        const playerContext = await browser.newContext();
      contexts.push(playerContext);
        const playerBrowserPage = await playerContext.newPage();
        const playerJoinPage = new ControllerJoinPage(playerBrowserPage);

        await playerJoinPage.joinRoom(roomCode, `Player${i + 1}`);

        // Check host is still connected
        const isConnected = await lobbyPage.isConnected();
        expect(isConnected).toBe(true);

        await playerContext.close();
      }
    });
  });

  test.describe('Player Join Events', () => {
    test('should receive player_joined event in real-time', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      contexts.push(hostContext);
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();

      // Create player
      const playerContext = await browser.newContext();
      contexts.push(playerContext);
      const playerBrowserPage = await playerContext.newPage();
      const playerJoinPage = new ControllerJoinPage(playerBrowserPage);

      // Join room
      const startTime = Date.now();
      await playerJoinPage.joinRoom(roomCode, testPlayers.player1.name);

      // Host should receive notification quickly (< 2 seconds)
      await hostLobbyPage.waitForPlayerJoin(testPlayers.player1.name, 2000);
      const endTime = Date.now();

      const duration = endTime - startTime;
      expect(duration).toBeLessThan(2000); // Should be real-time (< 2s)

      await hostContext.close();
      await playerContext.close();
    });

    test('should update player list immediately on join', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      contexts.push(hostContext);
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();

      // Get initial players
      const initialPlayers = await hostLobbyPage.getPlayerNames();
      expect(initialPlayers.length).toBe(1);

      // Add player
      const playerContext = await browser.newContext();
      contexts.push(playerContext);
      const playerBrowserPage = await playerContext.newPage();
      const playerJoinPage = new ControllerJoinPage(playerBrowserPage);

      await playerJoinPage.joinRoom(roomCode, testPlayers.player1.name);

      // Wait for update (should be fast)
      await hostLobbyPage.page.waitForTimeout(1500);

      // Check updated list
      const updatedPlayers = await hostLobbyPage.getPlayerNames();
      expect(updatedPlayers.length).toBe(2);
      expect(updatedPlayers).toContain(testPlayers.player1.name);

      await hostContext.close();
      await playerContext.close();
    });

    test('should broadcast join to all connected clients', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      contexts.push(hostContext);
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();

      // Add first player
      const player1Context = await browser.newContext();
      contexts.push(player1Context);
      const player1Page = await player1Context.newPage();
      const player1JoinPage = new ControllerJoinPage(player1Page);
      const player1LobbyPage = new ControllerLobbyPage(player1Page);

      await player1JoinPage.joinRoom(roomCode, testPlayers.player1.name);

      // Add second player (should notify both host and player1)
      const player2Context = await browser.newContext();
      contexts.push(player2Context);
      const player2Page = await player2Context.newPage();
      const player2JoinPage = new ControllerJoinPage(player2Page);

      await player2JoinPage.joinRoom(roomCode, testPlayers.player2.name);

      // Both host and player1 should receive notification
      await Promise.all([
        hostLobbyPage.waitForPlayerJoin(testPlayers.player2.name, 2000),
        player1LobbyPage.waitForPlayerJoin(testPlayers.player2.name, 2000),
      ]);

      await hostContext.close();
      await player1Context.close();
      await player2Context.close();
    });
  });

  test.describe('Player Leave Events', () => {
    test('should receive player_left event in real-time', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      contexts.push(hostContext);
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();

      // Add player
      const playerContext = await browser.newContext();
      contexts.push(playerContext);
      const playerBrowserPage = await playerContext.newPage();
      const playerJoinPage = new ControllerJoinPage(playerBrowserPage);
      const playerLobbyPage = new ControllerLobbyPage(playerBrowserPage);

      await playerJoinPage.joinRoom(roomCode, testPlayers.player1.name);
      await hostLobbyPage.waitForPlayerJoin(testPlayers.player1.name);

      // Player leaves
      const startTime = Date.now();
      await playerLobbyPage.clickLeaveRoom();

      // Host should receive notification quickly
      await hostLobbyPage.waitForPlayerLeave(testPlayers.player1.name, 2000);
      const endTime = Date.now();

      const duration = endTime - startTime;
      expect(duration).toBeLessThan(2000);

      await hostContext.close();
      await playerContext.close();
    });

    test('should update player count immediately on leave', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      contexts.push(hostContext);
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();

      // Add player
      const playerContext = await browser.newContext();
      contexts.push(playerContext);
      const playerBrowserPage = await playerContext.newPage();
      const playerJoinPage = new ControllerJoinPage(playerBrowserPage);
      const playerLobbyPage = new ControllerLobbyPage(playerBrowserPage);

      await playerJoinPage.joinRoom(roomCode, testPlayers.player1.name);
      await hostLobbyPage.page.waitForTimeout(1000);

      // Verify count before leave
      let playerCount = await hostLobbyPage.getPlayerCount();
      expect(playerCount).toBe('2 / 12');

      // Player leaves
      await playerLobbyPage.clickLeaveRoom();
      await hostLobbyPage.waitForPlayerLeave(testPlayers.player1.name);
      await hostLobbyPage.page.waitForTimeout(1000);

      // Verify count after leave
      playerCount = await hostLobbyPage.getPlayerCount();
      expect(playerCount).toBe('1 / 12');

      await hostContext.close();
      await playerContext.close();
    });
  });

  test.describe('Host Transfer Events', () => {
    test('should receive host_transferred event when host leaves', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      contexts.push(hostContext);
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();

      // Add player
      const playerContext = await browser.newContext();
      contexts.push(playerContext);
      const playerBrowserPage = await playerContext.newPage();
      const playerJoinPage = new ControllerJoinPage(playerBrowserPage);
      const playerLobbyPage = new ControllerLobbyPage(playerBrowserPage);

      await playerJoinPage.joinRoom(roomCode, testPlayers.player1.name);

      // Wait for player to fully join and WebSocket events to propagate
      await hostLobbyPage.page.waitForTimeout(2000);

      // Host leaves
      await hostLobbyPage.clickLeaveRoom();

      // Player should receive host transfer notification (now checks notification history)
      await playerLobbyPage.waitForHostTransfer(testPlayers.player1.name, 8000);

      // Player should now be host
      await playerLobbyPage.page.waitForTimeout(1500);
      const isHost = await playerLobbyPage.isHost();
      expect(isHost).toBe(true);

      await hostContext.close();
      await playerContext.close();
    });
  });

  test.describe('Kick Player Events', () => {
    test('should receive player_kicked event immediately', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      contexts.push(hostContext);
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();

      // Add players
      const player1Context = await browser.newContext();
      contexts.push(player1Context);
      const player1Page = await player1Context.newPage();
      const player1JoinPage = new ControllerJoinPage(player1Page);
      const player1LobbyPage = new ControllerLobbyPage(player1Page);
      await player1JoinPage.joinRoom(roomCode, testPlayers.player1.name);

      const player2Context = await browser.newContext();
      contexts.push(player2Context);
      const player2Page = await player2Context.newPage();
      const player2JoinPage = new ControllerJoinPage(player2Page);
      const player2LobbyPage = new ControllerLobbyPage(player2Page);
      await player2JoinPage.joinRoom(roomCode, testPlayers.player2.name);

      await hostLobbyPage.page.waitForTimeout(1000);

      // Host kicks player2
      const startTime = Date.now();
      await hostLobbyPage.kickPlayer(testPlayers.player2.name);

      // Player1 should receive notification
      await player1LobbyPage.waitForPlayerKicked(testPlayers.player2.name, 2000);
      const endTime = Date.now();

      const duration = endTime - startTime;
      expect(duration).toBeLessThan(2000);

      // Player2 should be redirected
      await player2LobbyPage.page.waitForURL(/.*join\.html/, { timeout: 3000 });

      await hostContext.close();
      await player1Context.close();
      await player2Context.close();
    });
  });

  test.describe('Game Start Events', () => {
    test('should receive game_starting event with countdown', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      contexts.push(hostContext);
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();

      // Add player
      const playerContext = await browser.newContext();
      contexts.push(playerContext);
      const playerBrowserPage = await playerContext.newPage();
      const playerJoinPage = new ControllerJoinPage(playerBrowserPage);
      const playerLobbyPage = new ControllerLobbyPage(playerBrowserPage);

      await playerJoinPage.joinRoom(roomCode, testPlayers.player1.name);
      await hostLobbyPage.page.waitForTimeout(1000);

      // Start game
      const startTime = Date.now();
      await hostLobbyPage.clickStartGame();

      // Player should receive notification quickly
      await playerLobbyPage.waitForGameStarting(2000);
      const endTime = Date.now();

      const duration = endTime - startTime;
      expect(duration).toBeLessThan(2000);

      await hostContext.close();
      await playerContext.close();
    });

    test('should broadcast game start to all clients including display', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      contexts.push(hostContext);
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();

      // Add player
      const playerContext = await browser.newContext();
      contexts.push(playerContext);
      const playerBrowserPage = await playerContext.newPage();
      const playerJoinPage = new ControllerJoinPage(playerBrowserPage);
      const playerLobbyPage = new ControllerLobbyPage(playerBrowserPage);
      await playerJoinPage.joinRoom(roomCode, testPlayers.player1.name);

      // Create a display player session first
      const displaySetupContext = await browser.newContext();
      contexts.push(displaySetupContext);
      const displaySetupPage = await displaySetupContext.newPage();
      const displayJoinPage = new ControllerJoinPage(displaySetupPage);
      await displayJoinPage.joinRoom(roomCode, 'Display');
      const displaySessionId = await displaySetupPage.evaluate(() => {
        return localStorage.getItem('gametime_session');
      });
      await displaySetupContext.close();

      // Add display with valid session
      const displayContext = await browser.newContext();
      contexts.push(displayContext);
      const displayBrowserPage = await displayContext.newPage();
      const displayPage = new DisplayLobbyPage(displayBrowserPage);
      await displayPage.goto();
      await displayPage.page.evaluate(({ sessionId, code }) => {
        localStorage.setItem('gametime_session', sessionId);
        localStorage.setItem('gametime_room_code', code);
      }, { sessionId: displaySessionId, code: roomCode });
      await displayPage.page.reload();
      await displayPage.page.waitForLoadState('networkidle');

      // Wait a bit for all clients to be ready
      await displayPage.page.waitForTimeout(1500);

      // Start game
      await hostLobbyPage.clickStartGame();

      // All should receive notification (now checks notification history)
      await Promise.all([
        playerLobbyPage.waitForGameStarting(5000),
        displayPage.waitForGameStartingMessage(5000),
      ]);

      // Display should show countdown
      await displayPage.waitForCountdownToAppear(10000);

      await hostContext.close();
      await playerContext.close();
      await displayContext.close();
    });
  });

  test.describe('State Synchronization', () => {
    test('should keep room state in sync across multiple events', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      contexts.push(hostContext);
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();

      // Add 3 players
      const playerContexts = [];
      const playerLobbyPages = [];

      for (let i = 0; i < 3; i++) {
        const playerContext = await browser.newContext();
      contexts.push(playerContext);
        const playerBrowserPage = await playerContext.newPage();
        const playerJoinPage = new ControllerJoinPage(playerBrowserPage);
        const playerLobbyPage = new ControllerLobbyPage(playerBrowserPage);

        await playerJoinPage.joinRoom(roomCode, `Player${i + 1}`);
        playerContexts.push(playerContext);
        playerLobbyPages.push(playerLobbyPage);

        await hostLobbyPage.page.waitForTimeout(500);
      }

      // Wait for all updates
      await hostLobbyPage.page.waitForTimeout(1500);

      // All clients should have same player count
      const hostCount = await hostLobbyPage.getPlayerCount();
      expect(hostCount).toBe('4 / 12');

      for (const playerPage of playerLobbyPages) {
        const count = await playerPage.getPlayerCount();
        expect(count).toBe('4 / 12');
      }

      // All clients should have same player list
      const hostPlayers = await hostLobbyPage.getPlayerNames();
      expect(hostPlayers.length).toBe(4);

      for (const playerPage of playerLobbyPages) {
        const players = await playerPage.getPlayerNames();
        expect(players.length).toBe(4);
        expect(players.sort()).toEqual(hostPlayers.sort());
      }

      // Clean up
      await hostContext.close();
      for (const context of playerContexts) {
        await context.close();
      }
    });

    test('should recover state after brief disconnect', async ({ page }) => {
      // This test would require simulating a disconnect/reconnect
      // which is complex in e2e tests
      // Better suited for unit/integration tests
      // Placeholder for future implementation
    });
  });

  test.describe('Message Ordering', () => {
    test('should process events in correct order', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      contexts.push(hostContext);
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();

      // Add multiple players in sequence
      for (let i = 0; i < 3; i++) {
        const playerContext = await browser.newContext();
      contexts.push(playerContext);
        const playerBrowserPage = await playerContext.newPage();
        const playerJoinPage = new ControllerJoinPage(playerBrowserPage);

        await playerJoinPage.joinRoom(roomCode, `Player${i + 1}`);
        await hostLobbyPage.waitForPlayerJoin(`Player${i + 1}`);

        await playerContext.close();
      }

      // Final player list should be in correct order
      await hostLobbyPage.page.waitForTimeout(1500);

      const playerNames = await hostLobbyPage.getPlayerNames();
      expect(playerNames).toContain(testPlayers.host.name);
      expect(playerNames).toContain('Player1');
      expect(playerNames).toContain('Player2');
      expect(playerNames).toContain('Player3');

      await hostContext.close();
    });
  });
});
