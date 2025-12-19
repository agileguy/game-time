import { test, expect, BrowserContext } from '@playwright/test';
import { ControllerJoinPage } from '../pages/controller/join.page';
import { ControllerLobbyPage } from '../pages/controller/lobby.page';
import { ControllerHorseRacePage } from '../pages/controller/horse-race.page';
import { DisplayLobbyPage } from '../pages/display/lobby.page';
import { DisplayHorseRacePage } from '../pages/display/horse-race.page';
import { testPlayers } from '../fixtures/test-data';

test.describe('Horse Race Game', () => {
  test.describe('Complete Game Flow', () => {
    let hostContext: BrowserContext;
    let player1Context: BrowserContext;
    let player2Context: BrowserContext;
    let displayContext: BrowserContext;

    let hostLobby: ControllerLobbyPage;
    let player1Lobby: ControllerLobbyPage;
    let player2Lobby: ControllerLobbyPage;
    let displayLobby: DisplayLobbyPage;

    let hostGame: ControllerHorseRacePage;
    let player1Game: ControllerHorseRacePage;
    let player2Game: ControllerHorseRacePage;
    let displayGame: DisplayHorseRacePage;

    let roomCode: string;

    test.beforeEach(async ({ browser }) => {
      // Create host
      hostContext = await browser.newContext();
      const hostBrowserPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostBrowserPage);
      hostLobby = new ControllerLobbyPage(hostBrowserPage);
      hostGame = new ControllerHorseRacePage(hostBrowserPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      roomCode = await hostLobby.getRoomCode();

      // Create player 1
      player1Context = await browser.newContext();
      const player1BrowserPage = await player1Context.newPage();
      const player1JoinPage = new ControllerJoinPage(player1BrowserPage);
      player1Lobby = new ControllerLobbyPage(player1BrowserPage);
      player1Game = new ControllerHorseRacePage(player1BrowserPage);

      await player1JoinPage.joinRoom(roomCode, testPlayers.player1.name);

      // Create player 2
      player2Context = await browser.newContext();
      const player2BrowserPage = await player2Context.newPage();
      const player2JoinPage = new ControllerJoinPage(player2BrowserPage);
      player2Lobby = new ControllerLobbyPage(player2BrowserPage);
      player2Game = new ControllerHorseRacePage(player2BrowserPage);

      await player2JoinPage.joinRoom(roomCode, testPlayers.player2.name);

      // Create display player to get session
      const displaySetupContext = await browser.newContext();
      const displaySetupPage = await displaySetupContext.newPage();
      const displayJoinPage = new ControllerJoinPage(displaySetupPage);

      await displayJoinPage.joinRoom(roomCode, 'Display');

      const displaySessionId = await displaySetupPage.evaluate(() => {
        return localStorage.getItem('gametime_session');
      });

      await displaySetupContext.close();

      // Create display
      displayContext = await browser.newContext();
      const displayBrowserPage = await displayContext.newPage();
      displayLobby = new DisplayLobbyPage(displayBrowserPage);
      displayGame = new DisplayHorseRacePage(displayBrowserPage);

      await displayLobby.goto();
      await displayLobby.page.evaluate(
        ({ sessionId, code }) => {
          localStorage.setItem('gametime_session', sessionId);
          localStorage.setItem('gametime_room_code', code);
        },
        { sessionId: displaySessionId, code: roomCode }
      );

      await displayLobby.page.reload();
      await displayLobby.page.waitForLoadState('networkidle');

      // Wait for all connections
      await displayLobby.page.waitForTimeout(1000);
    });

    test.afterEach(async () => {
      await hostContext?.close();
      await player1Context?.close();
      await player2Context?.close();
      await displayContext?.close();
    });

    test('should complete full game with 3 players', async () => {
      // Verify we're in lobby
      expect(await hostLobby.isHost()).toBe(true);
      expect(await hostLobby.getPlayerCount()).toContain('4'); // 3 players + display

      // Host selects horse race game (wait for game selection to load)
      await hostLobby.page.waitForTimeout(1000);

      // Click on horse race game card
      const horseRaceCard = hostLobby.page.locator('.game-card[data-game-type="horse_race"]');
      await horseRaceCard.waitFor({ state: 'visible', timeout: 10000 });
      await horseRaceCard.click();

      // Wait for selection to register
      await hostLobby.page.waitForTimeout(500);

      // Verify start button is enabled
      const isStartEnabled = await hostLobby.isStartGameButtonEnabled();
      expect(isStartEnabled).toBe(true);

      // Host starts game
      await hostLobby.clickStartGame();

      // Wait for all clients to navigate to horse race page
      await Promise.all([
        hostLobby.page.waitForURL('**/controller/horse-race.html', { timeout: 10000 }),
        player1Lobby.page.waitForURL('**/controller/horse-race.html', { timeout: 10000 }),
        player2Lobby.page.waitForURL('**/controller/horse-race.html', { timeout: 10000 }),
        displayLobby.page.waitForURL('**/display/horse-race.html', { timeout: 10000 }),
      ]);

      // BETTING PHASE

      // Wait for betting phase
      await Promise.all([
        hostGame.waitForBettingPhase(),
        player1Game.waitForBettingPhase(),
        player2Game.waitForBettingPhase(),
        displayGame.waitForBettingPhase(),
      ]);

      // Verify betting phase is visible
      expect(await hostGame.isBettingPhaseVisible()).toBe(true);
      expect(await displayGame.isBettingPhaseVisible()).toBe(true);

      // Verify 4 horses are available
      const hostHorses = await hostGame.getAvailableHorses();
      expect(hostHorses).toHaveLength(4);

      const displayHorses = await displayGame.getHorsePreview();
      expect(displayHorses).toHaveLength(4);

      // Players place bets
      await hostGame.placeBet(0); // Host bets on horse 0
      await player1Game.placeBet(1); // Player 1 bets on horse 1
      await player2Game.placeBet(2); // Player 2 bets on horse 2

      // Verify bets were placed
      const hostBet = await hostGame.getCurrentBet();
      expect(hostBet).toBe(hostHorses[0]);

      const player1Bet = await player1Game.getCurrentBet();
      expect(player1Bet).toBe(hostHorses[1]);

      // Wait for betting phase to end (15 seconds + buffer)
      await hostGame.page.waitForTimeout(16000);

      // RACING PHASE

      // Wait for racing phase
      await Promise.all([
        hostGame.waitForRacingPhase(20000),
        player1Game.waitForRacingPhase(20000),
        player2Game.waitForRacingPhase(20000),
        displayGame.waitForRaceTrack(20000),
      ]);

      // Verify racing phase is visible
      expect(await hostGame.isRacingPhaseVisible()).toBe(true);
      expect(await displayGame.isRaceTrackVisible()).toBe(true);

      // Verify bet reminder shows correct horse
      const hostBetReminder = await hostGame.getBetReminder();
      expect(hostBetReminder).toBe(hostHorses[0]);

      // Wait for race to start
      await displayGame.waitForRaceStart();

      // Verify horses are moving
      const initialPositions = await displayGame.getHorsePositions();
      await displayGame.page.waitForTimeout(2000);
      const laterPositions = await displayGame.getHorsePositions();

      // At least one horse should have moved
      const someHorseMoved = initialPositions.some((initial, i) => {
        return laterPositions[i].position > initial.position;
      });
      expect(someHorseMoved).toBe(true);

      // Wait for race to complete
      await displayGame.waitForRaceCompletion(30000);

      // RESULTS PHASE

      // Wait for results
      await Promise.all([
        hostGame.waitForResultsPhase(35000),
        player1Game.waitForResultsPhase(35000),
        player2Game.waitForResultsPhase(35000),
        displayGame.waitForResults(35000),
      ]);

      // Verify results phase is visible
      expect(await hostGame.isResultsPhaseVisible()).toBe(true);
      expect(await displayGame.isResultsPhaseVisible()).toBe(true);

      // Get final positions
      const hostResults = await hostGame.getRaceResults();
      expect(hostResults).toHaveLength(4);

      const displayPodium = await displayGame.getPodiumResults();
      expect(displayPodium).toHaveLength(3); // Top 3 only

      // Verify podium order (1st, 2nd, 3rd)
      expect(displayPodium[0].place).toBe(1);
      expect(displayPodium[1].place).toBe(2);
      expect(displayPodium[2].place).toBe(3);

      // Get win status for each player
      const hostStatus = await hostGame.getWinStatus();
      const player1Status = await player1Game.getWinStatus();
      const player2Status = await player2Game.getWinStatus();

      // Verify at least one player won
      const someoneWon =
        hostStatus.icon === '🏆' ||
        player1Status.icon === '🏆' ||
        player2Status.icon === '🏆';
      expect(someoneWon).toBe(true);

      // Verify scores were updated
      const hostScore = await hostGame.getFinalScore();
      const player1Score = await player1Game.getFinalScore();
      const player2Score = await player2Game.getFinalScore();

      // Total points should be distributed (100 for 1st, 50 for 2nd)
      const totalPoints = hostScore + player1Score + player2Score;
      expect(totalPoints).toBe(150);

      // Verify display shows player standings
      const standings = await displayGame.getPlayerStandings();
      expect(standings.length).toBeGreaterThan(0);

      // Top scorer should have 100 points (winner)
      expect(standings[0].score).toBe(100);
    });

    test('should allow players to change bets during betting phase', async () => {
      // Start game
      await hostLobby.page.waitForTimeout(1000);
      const horseRaceCard = hostLobby.page.locator('.game-card[data-game-type="horse_race"]');
      await horseRaceCard.waitFor({ state: 'visible', timeout: 10000 });
      await horseRaceCard.click();
      await hostLobby.page.waitForTimeout(500);
      await hostLobby.clickStartGame();

      await hostLobby.page.waitForURL('**/controller/horse-race.html', { timeout: 10000 });

      // Wait for betting phase
      await hostGame.waitForBettingPhase();

      const horses = await hostGame.getAvailableHorses();

      // Place initial bet
      await hostGame.placeBet(0);
      let currentBet = await hostGame.getCurrentBet();
      expect(currentBet).toBe(horses[0]);

      // Change bet
      await hostGame.changeBet();
      await hostGame.placeBet(1);
      currentBet = await hostGame.getCurrentBet();
      expect(currentBet).toBe(horses[1]);

      // Change again
      await hostGame.changeBet();
      await hostGame.placeBet(3);
      currentBet = await hostGame.getCurrentBet();
      expect(currentBet).toBe(horses[3]);
    });

    test('should show real-time position updates during race', async () => {
      // Start game
      await hostLobby.page.waitForTimeout(1000);
      const horseRaceCard = hostLobby.page.locator('.game-card[data-game-type="horse_race"]');
      await horseRaceCard.waitFor({ state: 'visible', timeout: 10000 });
      await horseRaceCard.click();
      await hostLobby.page.waitForTimeout(500);
      await hostLobby.clickStartGame();

      await Promise.all([
        hostLobby.page.waitForURL('**/controller/horse-race.html', { timeout: 10000 }),
        displayLobby.page.waitForURL('**/display/horse-race.html', { timeout: 10000 }),
      ]);

      // Wait for betting phase and place bet
      await hostGame.waitForBettingPhase();
      await hostGame.placeBet(0);

      // Wait for betting to end
      await hostGame.page.waitForTimeout(16000);

      // Wait for racing phase
      await Promise.all([
        hostGame.waitForRacingPhase(20000),
        displayGame.waitForRaceTrack(20000),
      ]);

      // Wait for race to start
      await displayGame.waitForRaceStart();

      // Sample positions multiple times
      const position1 = await displayGame.getHorsePositions();
      await displayGame.page.waitForTimeout(1000);
      const position2 = await displayGame.getHorsePositions();
      await displayGame.page.waitForTimeout(1000);
      const position3 = await displayGame.getHorsePositions();

      // Verify positions are increasing over time
      const allHorsesProgressing = position1.every((p1, i) => {
        const p2 = position2[i];
        const p3 = position3[i];
        return p2.position >= p1.position && p3.position >= p2.position;
      });

      expect(allHorsesProgressing).toBe(true);

      // Controller should also show progressing positions
      const controllerPos1 = await hostGame.getRacePositions();
      await hostGame.page.waitForTimeout(1000);
      const controllerPos2 = await hostGame.getRacePositions();

      const controllerProgressing = controllerPos1.every((p1, i) => {
        const p2 = controllerPos2[i];
        return p2.progress >= p1.progress;
      });

      expect(controllerProgressing).toBe(true);
    });

    test('should sync game state across all clients', async () => {
      // Start game
      await hostLobby.page.waitForTimeout(1000);
      const horseRaceCard = hostLobby.page.locator('.game-card[data-game-type="horse_race"]');
      await horseRaceCard.waitFor({ state: 'visible', timeout: 10000 });
      await horseRaceCard.click();
      await hostLobby.page.waitForTimeout(500);
      await hostLobby.clickStartGame();

      await Promise.all([
        hostLobby.page.waitForURL('**/controller/horse-race.html', { timeout: 10000 }),
        player1Lobby.page.waitForURL('**/controller/horse-race.html', { timeout: 10000 }),
        player2Lobby.page.waitForURL('**/controller/horse-race.html', { timeout: 10000 }),
        displayLobby.page.waitForURL('**/display/horse-race.html', { timeout: 10000 }),
      ]);

      // All clients should be in same phase
      const hostPhase = await hostGame.getCurrentPhase();
      const player1Phase = await player1Game.getCurrentPhase();
      const player2Phase = await player2Game.getCurrentPhase();
      const displayPhase = await displayGame.getCurrentPhase();

      expect(player1Phase).toBe(hostPhase);
      expect(player2Phase).toBe(hostPhase);
      expect(displayPhase).toContain('Betting'); // Display shows "Betting Phase"

      // All controllers should have same horses
      const hostHorses = await hostGame.getAvailableHorses();
      const player1Horses = await player1Game.getAvailableHorses();
      const player2Horses = await player2Game.getAvailableHorses();

      expect(player1Horses).toEqual(hostHorses);
      expect(player2Horses).toEqual(hostHorses);

      // Display should show same horses
      const displayHorses = await displayGame.getHorsePreview();
      expect(displayHorses).toHaveLength(hostHorses.length);
    });
  });

  test.describe('Edge Cases', () => {
    let hostContext: BrowserContext;
    let hostLobby: ControllerLobbyPage;
    let hostGame: ControllerHorseRacePage;
    let roomCode: string;

    test.beforeEach(async ({ browser }) => {
      hostContext = await browser.newContext();
      const hostBrowserPage = await hostContext.newPage();
      const hostJoinPage = new ControllerJoinPage(hostBrowserPage);
      hostLobby = new ControllerLobbyPage(hostBrowserPage);
      hostGame = new ControllerHorseRacePage(hostBrowserPage);

      await hostJoinPage.createRoom(testPlayers.host.name);
      roomCode = await hostLobby.getRoomCode();
    });

    test.afterEach(async () => {
      await hostContext?.close();
    });

    test('should handle single player game', async () => {
      // Select and start game with just one player
      await hostLobby.page.waitForTimeout(1000);
      const horseRaceCard = hostLobby.page.locator('.game-card[data-game-type="horse_race"]');
      await horseRaceCard.waitFor({ state: 'visible', timeout: 10000 });
      await horseRaceCard.click();
      await hostLobby.page.waitForTimeout(500);

      // Should be able to start even with 1 player (min is 2 but host can override)
      const isEnabled = await hostLobby.isStartGameButtonEnabled();
      expect(isEnabled).toBe(true);

      await hostLobby.clickStartGame();
      await hostLobby.page.waitForURL('**/controller/horse-race.html', { timeout: 10000 });

      // Should still show betting phase
      await hostGame.waitForBettingPhase();
      expect(await hostGame.isBettingPhaseVisible()).toBe(true);

      // Should have 4 horses
      const horses = await hostGame.getAvailableHorses();
      expect(horses).toHaveLength(4);
    });

    test('should handle player not placing bet', async ({ browser }) => {
      // Add a second player
      const player1Context = await browser.newContext();
      const player1BrowserPage = await player1Context.newPage();
      const player1JoinPage = new ControllerJoinPage(player1BrowserPage);
      const player1Game = new ControllerHorseRacePage(player1BrowserPage);

      await player1JoinPage.joinRoom(roomCode, testPlayers.player1.name);

      // Start game
      await hostLobby.page.waitForTimeout(1000);
      const horseRaceCard = hostLobby.page.locator('.game-card[data-game-type="horse_race"]');
      await horseRaceCard.waitFor({ state: 'visible', timeout: 10000 });
      await horseRaceCard.click();
      await hostLobby.page.waitForTimeout(500);
      await hostLobby.clickStartGame();

      await Promise.all([
        hostLobby.page.waitForURL('**/controller/horse-race.html', { timeout: 10000 }),
        player1BrowserPage.waitForURL('**/controller/horse-race.html', { timeout: 10000 }),
      ]);

      // Host places bet, player1 does not
      await hostGame.waitForBettingPhase();
      await player1Game.waitForBettingPhase();
      await hostGame.placeBet(0);

      // Wait for betting phase to end
      await hostGame.page.waitForTimeout(16000);

      // Both should still progress to racing phase
      await Promise.all([
        hostGame.waitForRacingPhase(20000),
        player1Game.waitForRacingPhase(20000),
      ]);

      expect(await hostGame.isRacingPhaseVisible()).toBe(true);
      expect(await player1Game.isRacingPhaseVisible()).toBe(true);

      await player1Context.close();
    });
  });
});
