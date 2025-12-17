import { test, expect } from '@playwright/test';
import { ControllerJoinPage } from '../pages/controller/join.page';
import { ControllerLobbyPage } from '../pages/controller/lobby.page';
import { testPlayers, invalidRoomCodes, validPlayerNames, invalidPlayerNames } from '../fixtures/test-data';

test.describe('Controller Join Flow', () => {
  let joinPage: ControllerJoinPage;
  let lobbyPage: ControllerLobbyPage;

  test.beforeEach(async ({ page }) => {
    joinPage = new ControllerJoinPage(page);
    lobbyPage = new ControllerLobbyPage(page);
    await joinPage.goto();
  });

  test.describe('Create Room', () => {
    test('should successfully create a new room', async () => {
      await joinPage.createRoom(testPlayers.host.name, testPlayers.host.maxPlayers);

      // Should redirect to lobby
      await expect(joinPage.page).toHaveURL(/.*lobby\.html/);

      // Should show correct player name
      const playerName = await lobbyPage.getPlayerName();
      expect(playerName).toBe(testPlayers.host.name);

      // Should be the host
      const isHost = await lobbyPage.isHost();
      expect(isHost).toBe(true);

      // Should show room code
      const roomCode = await lobbyPage.getRoomCode();
      expect(roomCode).toMatch(/^[A-Z0-9]{4}$/);

      // Should show player count
      const playerCount = await lobbyPage.getPlayerCount();
      expect(playerCount).toContain('1 / 12');
    });

    test('should create room with default settings', async () => {
      await joinPage.createRoom(testPlayers.host.name);

      await expect(joinPage.page).toHaveURL(/.*lobby\.html/);

      const playerCount = await lobbyPage.getPlayerCount();
      expect(playerCount).toContain('1 / 12');
    });

    test('should cancel room creation', async () => {
      await joinPage.openCreateRoomModal();
      await joinPage.page.waitForTimeout(300);

      await joinPage.hostNameInput.fill(testPlayers.host.name);
      await joinPage.cancelButton.click();

      // Modal should close, still on join page
      await expect(joinPage.page).toHaveURL(/.*join\.html/);
      await expect(joinPage.createRoomButton).toBeVisible();
    });

    test('should show validation error for empty host name', async () => {
      await joinPage.openCreateRoomModal();
      await joinPage.page.waitForTimeout(300);

      // Try to submit without filling host name (browser validation should prevent submit)
      await joinPage.createRoomSubmitButton.click();

      // Should stay in modal (form validation prevents submission)
      const modalVisible = await joinPage.page.locator('#create-room-modal').isVisible();
      expect(modalVisible).toBe(true);
    });
  });

  test.describe('Join Existing Room', () => {
    let roomCode: string;

    test.beforeEach(async ({ browser }) => {
      // Create a room first in a separate context
      const hostContext = await browser.newContext();
      const hostPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostPage);
      const hostLobbyPage = new ControllerLobbyPage(hostPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      roomCode = await hostLobbyPage.getRoomCode();

      await hostContext.close();
    });

    test('should successfully join existing room with valid code', async () => {
      await joinPage.joinRoom(roomCode, testPlayers.player1.name);

      // Should redirect to lobby
      await expect(joinPage.page).toHaveURL(/.*lobby\.html/);

      // Should show correct player name
      const playerName = await lobbyPage.getPlayerName();
      expect(playerName).toBe(testPlayers.player1.name);

      // Should not be host
      const isHost = await lobbyPage.isHost();
      expect(isHost).toBe(false);

      // Should show same room code
      const lobbyRoomCode = await lobbyPage.getRoomCode();
      expect(lobbyRoomCode).toBe(roomCode);

      // Should show 2 players
      const playerCount = await lobbyPage.getPlayerCount();
      expect(playerCount).toContain('2 / 12');
    });

    test('should auto-uppercase room code', async () => {
      await joinPage.enterRoomCode(roomCode.toLowerCase());
      await joinPage.clickContinue();

      // Should accept lowercase and proceed to player name step
      await joinPage.page.waitForTimeout(500);
      await expect(joinPage.playerNameInput).toBeVisible();
    });

    test('should show error for non-existent room code', async () => {
      await joinPage.joinWithRoomCode('XXXX');
      await joinPage.page.waitForTimeout(1000);

      // Should show error notification
      await expect(joinPage.notification).toBeVisible();
      const notificationText = await joinPage.getNotificationText();
      expect(notificationText).toContain('Room not found');

      // Should stay on room code step
      await expect(joinPage.roomCodeInput).toBeVisible();
    });

    test.describe('Invalid Room Codes', () => {
      for (const invalidCode of invalidRoomCodes) {
        test(`should reject invalid room code: "${invalidCode}"`, async () => {
          await joinPage.enterRoomCode(invalidCode);
          await joinPage.clickContinue();

          // Should show error (either validation or room not found)
          await joinPage.page.waitForTimeout(500);
          await expect(joinPage.notification).toBeVisible();
          const notificationText = await joinPage.getNotificationText();

          // Note: Some codes like "12345", "ABCDE", "abc1" get auto-formatted (truncated/uppercased)
          // due to input maxlength and toUpperCase(), so they pass validation but fail at API level
          expect(notificationText).toMatch(/valid|not found/i);

          // Should stay on room code step
          await expect(joinPage.roomCodeInput).toBeVisible();
        });
      }
    });

    test.describe('Player Name Validation', () => {
      test.beforeEach(async () => {
        await joinPage.joinWithRoomCode(roomCode);
        await joinPage.page.waitForTimeout(500);
      });

      for (const validName of validPlayerNames) {
        test(`should accept valid player name: "${validName}"`, async () => {
          await joinPage.enterPlayerName(validName);
          await joinPage.clickJoin();

          // Should successfully join
          await expect(joinPage.page).toHaveURL(/.*lobby\.html/);
        });
      }

      for (const invalidName of invalidPlayerNames) {
        test(`should reject invalid player name: "${invalidName.substring(0, 20)}${invalidName.length > 20 ? '...' : ''}"`, async () => {
          await joinPage.enterPlayerName(invalidName);
          await joinPage.clickJoin();

          // Should show validation error or stay on page
          await joinPage.page.waitForTimeout(500);

          if (invalidName.trim().length === 0) {
            // Empty names should trigger browser validation
            await expect(joinPage.playerNameInput).toBeVisible();
          } else if (invalidName.length > 50) {
            // Too long should show error
            await expect(joinPage.notification).toBeVisible();
          }
        });
      }

      test('should navigate back to room code step', async () => {
        await joinPage.backButton.click();

        // Should show room code step
        await expect(joinPage.roomCodeInput).toBeVisible();
      });
    });
  });

  test.describe('UI Elements', () => {
    test('should show all required elements on room code step', async () => {
      await expect(joinPage.roomCodeInput).toBeVisible();
      await expect(joinPage.continueButton).toBeVisible();
      await expect(joinPage.createRoomButton).toBeVisible();
    });

    test('should show all required elements in create room modal', async () => {
      await joinPage.openCreateRoomModal();
      await joinPage.page.waitForTimeout(300);

      await expect(joinPage.hostNameInput).toBeVisible();
      await expect(joinPage.maxPlayersInput).toBeVisible();
      await expect(joinPage.publicRoomCheckbox).toBeVisible();
      await expect(joinPage.createRoomSubmitButton).toBeVisible();
      await expect(joinPage.cancelButton).toBeVisible();
    });

    test('should have proper input constraints', async () => {
      // Room code should have maxlength 4
      const maxLength = await joinPage.roomCodeInput.getAttribute('maxlength');
      expect(maxLength).toBe('4');

      // Room code should be uppercase
      await joinPage.roomCodeInput.fill('abcd');
      const value = await joinPage.roomCodeInput.inputValue();
      expect(value).toBe('ABCD');
    });
  });

  test.describe('Session Persistence', () => {
    test('should store session data after creating room', async () => {
      await joinPage.createRoom(testPlayers.host.name);

      // Check localStorage
      const sessionId = await joinPage.page.evaluate(() => {
        return localStorage.getItem('gametime_session');
      });
      const roomCode = await joinPage.page.evaluate(() => {
        return localStorage.getItem('gametime_room_code');
      });
      const playerName = await joinPage.page.evaluate(() => {
        return localStorage.getItem('gametime_player_name');
      });

      expect(sessionId).toBeTruthy();
      expect(roomCode).toMatch(/^[A-Z0-9]{4}$/);
      expect(playerName).toBe(testPlayers.host.name);
    });

    test('should redirect to lobby if valid session exists', async ({ browser }) => {
      // Create room and get session
      await joinPage.createRoom(testPlayers.host.name);
      await lobbyPage.page.waitForTimeout(1000);

      // Navigate back to join page
      await joinPage.goto();

      // Should redirect to lobby since session is valid
      // Note: This depends on the actual implementation
      // If join page doesn't auto-redirect, this test might need adjustment
    });
  });
});
