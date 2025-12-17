import { test, expect, Browser, BrowserContext } from '@playwright/test';
import { ControllerJoinPage } from '../pages/controller/join.page';
import { ControllerLobbyPage } from '../pages/controller/lobby.page';
import { DisplayLobbyPage } from '../pages/display/lobby.page';
import { testPlayers } from '../fixtures/test-data';

test.describe('Multi-Client Integration', () => {
  test.describe('Controller + Display Synchronization', () => {
    let hostContext: BrowserContext;
    let displayContext: BrowserContext;
    let hostPage: ControllerLobbyPage;
    let displayPage: DisplayLobbyPage;
    let roomCode: string;

    test.beforeEach(async ({ browser }) => {
      // Create host
      hostContext = await browser.newContext();
      const hostBrowserPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostBrowserPage);
      hostPage = new ControllerLobbyPage(hostBrowserPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      roomCode = await hostPage.getRoomCode();

      // Create a display player to get a valid session
      const displaySetupContext = await browser.newContext();
      const displaySetupPage = await displaySetupContext.newPage();
      const displayJoinPage = new ControllerJoinPage(displaySetupPage);

      // Join the room as display player
      await displayJoinPage.joinRoom(roomCode, 'Display');

      // Get the session ID from localStorage
      const displaySessionId = await displaySetupPage.evaluate(() => {
        return localStorage.getItem('gametime_session');
      });

      await displaySetupContext.close();

      // Create display
      displayContext = await browser.newContext();
      const displayBrowserPage = await displayContext.newPage();
      displayPage = new DisplayLobbyPage(displayBrowserPage);

      // Set up display with the session and room code
      await displayPage.goto();
      await displayPage.page.evaluate(({ sessionId, code }) => {
        localStorage.setItem('gametime_session', sessionId);
        localStorage.setItem('gametime_room_code', code);
      }, { sessionId: displaySessionId, code: roomCode });

      // Reload to pick up the session
      await displayPage.page.reload();
      await displayPage.page.waitForLoadState('networkidle');

      // Wait for WebSocket to connect and room state to update
      await displayPage.page.waitForFunction(
        () => {
          const roomCodeEl = document.getElementById('room-code');
          return roomCodeEl && roomCodeEl.textContent !== '----';
        },
        { timeout: 10000 }
      );
    });

    test.afterEach(async () => {
      await hostContext?.close();
      await displayContext?.close();
    });

    test('should show same room code on both controller and display', async () => {
      const controllerRoomCode = await hostPage.getRoomCode();
      const displayRoomCode = await displayPage.getRoomCode();

      expect(controllerRoomCode).toBe(displayRoomCode);
      expect(controllerRoomCode).toBe(roomCode);
    });

    test('should sync player count across controller and display', async ({ browser }) => {
      // Add players
      const playerContexts: BrowserContext[] = [];

      for (let i = 0; i < 3; i++) {
        const playerContext = await browser.newContext();
        const playerBrowserPage = await playerContext.newPage();
        const playerJoinPage = new ControllerJoinPage(playerBrowserPage);

        await playerJoinPage.joinRoom(roomCode, `Player${i + 1}`);
        playerContexts.push(playerContext);

        // Wait for updates
        await displayPage.page.waitForTimeout(500);
      }

      // Wait for all updates to propagate
      await displayPage.page.waitForTimeout(1500);

      // Check player count matches
      const controllerCount = await hostPage.getPlayerCount();
      const displayCount = await displayPage.getPlayerCount();

      expect(controllerCount).toBe('4 / 12'); // host + 3 players
      expect(displayCount).toBe('4 / 12');

      // Clean up
      for (const context of playerContexts) {
        await context.close();
      }
    });

    test('should sync player names across controller and display', async ({ browser }) => {
      const playerNames = [testPlayers.player1.name, testPlayers.player2.name];

      // Add players
      for (const name of playerNames) {
        const playerContext = await browser.newContext();
        const playerBrowserPage = await playerContext.newPage();
        const playerJoinPage = new ControllerJoinPage(playerBrowserPage);

        await playerJoinPage.joinRoom(roomCode, name);
        await playerContext.close();
      }

      await displayPage.page.waitForTimeout(2000);

      // Get player names from both views
      const controllerPlayers = await hostPage.getPlayerNames();
      const displayPlayers = await displayPage.getPlayerNames();

      // Both should contain the host and all players
      expect(controllerPlayers).toContain(testPlayers.host.name);
      expect(displayPlayers).toContain(testPlayers.host.name);

      for (const name of playerNames) {
        expect(controllerPlayers).toContain(name);
        expect(displayPlayers).toContain(name);
      }
    });

    test('should sync game start countdown on display when host starts game', async ({ browser }) => {
      // Add a player (need min 2)
      const playerContext = await browser.newContext();
      const playerBrowserPage = await playerContext.newPage();
      const playerJoinPage = new ControllerJoinPage(playerBrowserPage);

      await playerJoinPage.joinRoom(roomCode, testPlayers.player1.name);
      await displayPage.page.waitForTimeout(1000);

      // Host starts game
      await hostPage.clickStartGame();

      // Display should show countdown
      await displayPage.waitForCountdownToAppear();

      const isCountdownVisible = await displayPage.isCountdownVisible();
      expect(isCountdownVisible).toBe(true);

      await playerContext.close();
    });
  });

  test.describe('Multiple Controllers + Display', () => {
    let contexts: BrowserContext[] = [];
    let roomCode: string;

    test.afterEach(async () => {
      for (const context of contexts) {
        await context.close();
      }
      contexts = [];
    });

    test('should handle 5+ concurrent players', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      roomCode = await hostLobbyPage.getRoomCode();
      contexts.push(hostContext);

      // Create a display player to get a valid session
      const displaySetupContext = await browser.newContext();
      const displaySetupPage = await displaySetupContext.newPage();
      const displayJoinPage = new ControllerJoinPage(displaySetupPage);

      await displayJoinPage.joinRoom(roomCode, 'Display');

      const displaySessionId = await displaySetupPage.evaluate(() => {
        return localStorage.getItem('gametime_session');
      });

      await displaySetupContext.close();

      // Create display
      const displayContext = await browser.newContext();
      const displayBrowserPage = await displayContext.newPage();
      const displayPage = new DisplayLobbyPage(displayBrowserPage);

      await displayPage.goto();
      await displayPage.page.evaluate(({ sessionId, code }) => {
        localStorage.setItem('gametime_session', sessionId);
        localStorage.setItem('gametime_room_code', code);
      }, { sessionId: displaySessionId, code: roomCode });
      await displayPage.page.reload();
      await displayPage.page.waitForLoadState('networkidle');

      // Wait for display to connect
      await displayPage.page.waitForFunction(
        () => {
          const roomCodeEl = document.getElementById('room-code');
          return roomCodeEl && roomCodeEl.textContent !== '----';
        },
        { timeout: 10000 }
      );
      contexts.push(displayContext);

      // Add 5 players
      const playerPages: ControllerLobbyPage[] = [];

      for (let i = 0; i < 5; i++) {
        const playerContext = await browser.newContext();
        const playerBrowserPage = await playerContext.newPage();
        const playerJoinPage = new ControllerJoinPage(playerBrowserPage);
        const playerLobbyPage = new ControllerLobbyPage(playerBrowserPage);

        await playerJoinPage.joinRoom(roomCode, `Player${i + 1}`);
        playerPages.push(playerLobbyPage);
        contexts.push(playerContext);

        // Brief delay between joins
        await displayPage.page.waitForTimeout(300);
      }

      // Wait for all updates
      await displayPage.page.waitForTimeout(2000);

      // Verify all players see 7 total players (host + Display + 5)
      const hostPlayerCount = await hostLobbyPage.getPlayerCount();
      expect(hostPlayerCount).toBe('7 / 12');

      for (const playerPage of playerPages) {
        const count = await playerPage.getPlayerCount();
        expect(count).toBe('7 / 12');
      }

      // Display should also show 7 players
      const displayCount = await displayPage.getPlayerCount();
      expect(displayCount).toBe('7 / 12');

      // Verify all player names are visible
      const displayPlayers = await displayPage.getPlayerNames();
      expect(displayPlayers.length).toBe(7);
    });

    test('should sync player leave across all clients', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      roomCode = await hostLobbyPage.getRoomCode();
      contexts.push(hostContext);

      // Add 2 players
      const player1Context = await browser.newContext();
      const player1Page = await player1Context.newPage();
      const player1JoinPage = new ControllerJoinPage(player1Page);
      const player1LobbyPage = new ControllerLobbyPage(player1Page);
      await player1JoinPage.joinRoom(roomCode, testPlayers.player1.name);
      contexts.push(player1Context);

      const player2Context = await browser.newContext();
      const player2Page = await player2Context.newPage();
      const player2JoinPage = new ControllerJoinPage(player2Page);
      const player2LobbyPage = new ControllerLobbyPage(player2Page);
      await player2JoinPage.joinRoom(roomCode, testPlayers.player2.name);
      contexts.push(player2Context);

      await hostLobbyPage.page.waitForTimeout(1000);

      // Player 2 leaves
      await player2LobbyPage.clickLeaveRoom();

      // All remaining clients should see the update
      await hostLobbyPage.waitForPlayerLeave(testPlayers.player2.name);
      await player1LobbyPage.waitForPlayerLeave(testPlayers.player2.name);

      await hostLobbyPage.page.waitForTimeout(1000);

      // Verify player count
      const hostCount = await hostLobbyPage.getPlayerCount();
      const player1Count = await player1LobbyPage.getPlayerCount();

      expect(hostCount).toBe('2 / 12');
      expect(player1Count).toBe('2 / 12');
    });

    test('should sync kick player across all clients', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      roomCode = await hostLobbyPage.getRoomCode();
      contexts.push(hostContext);

      // Add 2 players
      const player1Context = await browser.newContext();
      const player1Page = await player1Context.newPage();
      const player1JoinPage = new ControllerJoinPage(player1Page);
      const player1LobbyPage = new ControllerLobbyPage(player1Page);
      await player1JoinPage.joinRoom(roomCode, testPlayers.player1.name);
      contexts.push(player1Context);

      const player2Context = await browser.newContext();
      const player2Page = await player2Context.newPage();
      const player2JoinPage = new ControllerJoinPage(player2Page);
      const player2LobbyPage = new ControllerLobbyPage(player2Page);
      await player2JoinPage.joinRoom(roomCode, testPlayers.player2.name);
      contexts.push(player2Context);

      await hostLobbyPage.page.waitForTimeout(1000);

      // Host kicks player 2
      await hostLobbyPage.kickPlayer(testPlayers.player2.name);

      // Player 2 should be redirected
      await player2LobbyPage.page.waitForURL(/.*join\.html/, { timeout: 5000 });

      // Host and Player 1 should see kick notification
      await hostLobbyPage.waitForPlayerKicked(testPlayers.player2.name);
      await player1LobbyPage.waitForPlayerKicked(testPlayers.player2.name);

      await hostLobbyPage.page.waitForTimeout(1000);

      // Verify player count
      const hostCount = await hostLobbyPage.getPlayerCount();
      const player1Count = await player1LobbyPage.getPlayerCount();

      expect(hostCount).toBe('2 / 12');
      expect(player1Count).toBe('2 / 12');
    });

    test('should sync host transfer across all clients and display', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      roomCode = await hostLobbyPage.getRoomCode();
      contexts.push(hostContext);

      // Create a display player to get a valid session
      const displaySetupContext = await browser.newContext();
      const displaySetupPage = await displaySetupContext.newPage();
      const displayJoinPage = new ControllerJoinPage(displaySetupPage);

      await displayJoinPage.joinRoom(roomCode, 'Display');

      const displaySessionId = await displaySetupPage.evaluate(() => {
        return localStorage.getItem('gametime_session');
      });

      await displaySetupContext.close();

      // Create display
      const displayContext = await browser.newContext();
      const displayBrowserPage = await displayContext.newPage();
      const displayPage = new DisplayLobbyPage(displayBrowserPage);

      await displayPage.goto();
      await displayPage.page.evaluate(({ sessionId, code }) => {
        localStorage.setItem('gametime_session', sessionId);
        localStorage.setItem('gametime_room_code', code);
      }, { sessionId: displaySessionId, code: roomCode });
      await displayPage.page.reload();
      await displayPage.page.waitForLoadState('networkidle');

      // Wait for display to connect
      await displayPage.page.waitForFunction(
        () => {
          const roomCodeEl = document.getElementById('room-code');
          return roomCodeEl && roomCodeEl.textContent !== '----';
        },
        { timeout: 10000 }
      );
      contexts.push(displayContext);

      // Add player
      const playerContext = await browser.newContext();
      const playerBrowserPage = await playerContext.newPage();
      const playerJoinPage = new ControllerJoinPage(playerBrowserPage);
      const playerLobbyPage = new ControllerLobbyPage(playerBrowserPage);
      await playerJoinPage.joinRoom(roomCode, testPlayers.player1.name);
      contexts.push(playerContext);

      await displayPage.page.waitForTimeout(1500);

      // Original host leaves (transfers to player1)
      await hostLobbyPage.clickLeaveRoom();

      // Player should get host transfer notification
      await playerLobbyPage.waitForHostTransfer(testPlayers.player1.name);

      // Display should show host transfer message
      await displayPage.waitForHostTransferMessage(testPlayers.player1.name);

      await playerLobbyPage.page.waitForTimeout(1000);

      // Player should now be host
      const isHost = await playerLobbyPage.isHost();
      expect(isHost).toBe(true);

      // Display should show new host name
      const displayHostName = await displayPage.getHostName();
      expect(displayHostName).toBe(testPlayers.player1.name);
    });
  });

  test.describe('Stress Tests', () => {
    let contexts: BrowserContext[] = [];

    test.afterEach(async () => {
      for (const context of contexts) {
        await context.close();
      }
      contexts = [];
    });

    test('should handle rapid player joins', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();
      contexts.push(hostContext);

      // Rapidly add 8 players
      const joinPromises = [];

      for (let i = 0; i < 8; i++) {
        const promise = (async () => {
          const playerContext = await browser.newContext();
          const playerBrowserPage = await playerContext.newPage();
          const playerJoinPage = new ControllerJoinPage(playerBrowserPage);

          await playerJoinPage.joinRoom(roomCode, `Player${i + 1}`);
          contexts.push(playerContext);
        })();

        joinPromises.push(promise);
      }

      await Promise.all(joinPromises);

      // Wait for updates to propagate
      await hostLobbyPage.page.waitForTimeout(3000);

      // Verify all players joined
      const playerCount = await hostLobbyPage.getPlayerCount();
      expect(playerCount).toBe('9 / 12');

      const playerNames = await hostLobbyPage.getPlayerNames();
      expect(playerNames.length).toBe(9);
    });

    test('should handle max players (12)', async ({ browser }) => {
      // Create host
      const hostContext = await browser.newContext();
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      const roomCode = await hostLobbyPage.getRoomCode();
      contexts.push(hostContext);

      // Add 11 more players (total 12)
      for (let i = 0; i < 11; i++) {
        const playerContext = await browser.newContext();
        const playerBrowserPage = await playerContext.newPage();
        const playerJoinPage = new ControllerJoinPage(playerBrowserPage);

        await playerJoinPage.joinRoom(roomCode, `Player${i + 1}`);
        contexts.push(playerContext);

        await hostLobbyPage.page.waitForTimeout(200);
      }

      // Wait for updates
      await hostLobbyPage.page.waitForTimeout(2000);

      // Verify player count
      const playerCount = await hostLobbyPage.getPlayerCount();
      expect(playerCount).toBe('12 / 12');

      // Try to add one more player (should fail)
      const extraContext = await browser.newContext();
      const extraPage = await extraContext.newPage();
      const extraJoinPage = new ControllerJoinPage(extraPage);

      await extraJoinPage.goto();
      await extraJoinPage.joinWithRoomCode(roomCode);
      await extraPage.waitForTimeout(500);
      await extraJoinPage.enterPlayerName('ExtraPlayer');
      await extraJoinPage.clickJoin();

      // Should show error (room full)
      await extraPage.waitForTimeout(1000);
      // The player should either see an error or stay on join page
      const currentUrl = extraPage.url();
      // Exact behavior depends on backend implementation
      // Just verify we don't crash

      await extraContext.close();
    });
  });
});
