import { Page, Locator } from '@playwright/test';

/**
 * Page object for Display Horse Race screen
 */
export class DisplayHorseRacePage {
  readonly page: Page;

  // Header
  readonly gameTitle: Locator;
  readonly phaseText: Locator;
  readonly phaseTimer: Locator;
  readonly connectionIndicator: Locator;
  readonly connectionText: Locator;

  // Betting Phase
  readonly bettingPhase: Locator;
  readonly bettingMessage: Locator;
  readonly bettingCountdown: Locator;
  readonly horsePreview: Locator;

  // Race Track
  readonly raceTrack: Locator;
  readonly trackLanes: Locator;
  readonly finishLine: Locator;

  // Results
  readonly resultsPhase: Locator;
  readonly resultsTitle: Locator;
  readonly resultsPodium: Locator;
  readonly standingsList: Locator;

  // Footer
  readonly roomCode: Locator;
  readonly roundDisplay: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.gameTitle = page.locator('.game-title');
    this.phaseText = page.locator('#phase-text');
    this.phaseTimer = page.locator('#phase-timer');
    this.connectionIndicator = page.locator('#connection-indicator');
    this.connectionText = page.locator('#connection-text');

    // Betting Phase
    this.bettingPhase = page.locator('#betting-phase');
    this.bettingMessage = page.locator('.betting-message');
    this.bettingCountdown = page.locator('#betting-countdown');
    this.horsePreview = page.locator('#horse-preview');

    // Race Track
    this.raceTrack = page.locator('#race-track');
    this.trackLanes = page.locator('.track-lanes');
    this.finishLine = page.locator('.finish-line');

    // Results
    this.resultsPhase = page.locator('#results-phase');
    this.resultsTitle = page.locator('.results-title');
    this.resultsPodium = page.locator('#results-podium');
    this.standingsList = page.locator('#standings-list');

    // Footer
    this.roomCode = page.locator('#room-code');
    this.roundDisplay = page.locator('#round-display');
  }

  async goto() {
    await this.page.goto('http://localhost:7070/display/horse-race.html');
    await this.page.waitForLoadState('networkidle');
  }

  async getRoomCode(): Promise<string> {
    return await this.roomCode.textContent() || '';
  }

  async getCurrentPhase(): Promise<string> {
    return await this.phaseText.textContent() || '';
  }

  async getPhaseTimer(): Promise<string> {
    return await this.phaseTimer.textContent() || '';
  }

  async isBettingPhaseVisible(): Promise<boolean> {
    return await this.bettingPhase.isVisible();
  }

  async isRaceTrackVisible(): Promise<boolean> {
    return await this.raceTrack.isVisible();
  }

  async isResultsPhaseVisible(): Promise<boolean> {
    return await this.resultsPhase.isVisible();
  }

  async getBettingCountdown(): Promise<number> {
    const countdownText = await this.bettingCountdown.textContent() || '0';
    return parseInt(countdownText, 10);
  }

  async getHorsePreview(): Promise<Array<{ name: string; lane: number }>> {
    const horseCards = await this.horsePreview.locator('.horse-preview-card').all();
    const horses = [];

    for (let i = 0; i < horseCards.length; i++) {
      const card = horseCards[i];
      const name = await card.locator('.horse-preview-name').textContent() || '';
      const laneText = await card.locator('.horse-preview-odds').textContent() || '';
      const laneMatch = laneText.match(/Lane (\d+)/);
      const lane = laneMatch ? parseInt(laneMatch[1], 10) : i + 1;

      horses.push({ name, lane });
    }

    return horses;
  }

  async getHorsePositions(): Promise<Array<{ lane: number; name: string; position: number }>> {
    const lanes = await this.trackLanes.locator('.horse-lane').all();
    const positions = [];

    for (const lane of lanes) {
      const laneNumber = parseInt(await lane.locator('.lane-number').textContent() || '0', 10);
      const horseName = await lane.locator('.lane-horse-name').textContent() || '';
      const horseSprite = lane.locator('.horse-sprite');
      const leftStyle = await horseSprite.getAttribute('style') || '';
      const leftMatch = leftStyle.match(/left:\s*(\d+(\.\d+)?)%/);
      const position = leftMatch ? parseFloat(leftMatch[1]) : 0;

      positions.push({ lane: laneNumber, name: horseName, position });
    }

    return positions;
  }

  async getPodiumResults(): Promise<Array<{ place: number; name: string }>> {
    const podiumPlaces = await this.resultsPodium.locator('.podium-place').all();
    const results = [];

    for (const place of podiumPlaces) {
      const className = await place.getAttribute('class') || '';
      const placeMatch = className.match(/podium-place-(\d+)/);
      const placeNumber = placeMatch ? parseInt(placeMatch[1], 10) : 0;
      const name = await place.locator('.podium-horse-name').textContent() || '';

      results.push({ place: placeNumber, name });
    }

    // Sort by place
    return results.sort((a, b) => a.place - b.place);
  }

  async getPlayerStandings(): Promise<Array<{ rank: number; score: number }>> {
    const standingItems = await this.standingsList.locator('.standing-item').all();
    const standings = [];

    for (const item of standingItems) {
      const rankText = await item.locator('.standing-rank').textContent() || '#1';
      const rank = parseInt(rankText.replace('#', ''), 10);
      const scoreText = await item.locator('.standing-score').textContent() || '0';
      const score = parseInt(scoreText.replace(' pts', ''), 10);

      standings.push({ rank, score });
    }

    return standings;
  }

  async waitForBettingPhase(timeout: number = 10000) {
    await this.bettingPhase.waitFor({ state: 'visible', timeout });
  }

  async waitForRaceTrack(timeout: number = 20000) {
    await this.raceTrack.waitFor({ state: 'visible', timeout });
  }

  async waitForResults(timeout: number = 30000) {
    await this.resultsPhase.waitFor({ state: 'visible', timeout });
  }

  async waitForRaceStart(timeout: number = 20000) {
    // Wait for horses to start moving (position > 0)
    await this.page.waitForFunction(
      () => {
        const sprites = document.querySelectorAll('.horse-sprite');
        return Array.from(sprites).some((sprite) => {
          const style = (sprite as HTMLElement).style.left;
          const position = parseFloat(style);
          return position > 0;
        });
      },
      {},
      { timeout }
    );
  }

  async waitForRaceCompletion(timeout: number = 30000) {
    // Wait for all horses to finish (position >= 90%)
    await this.page.waitForFunction(
      () => {
        const sprites = document.querySelectorAll('.horse-sprite');
        return Array.from(sprites).every((sprite) => {
          const style = (sprite as HTMLElement).style.left;
          const position = parseFloat(style);
          return position >= 90;
        });
      },
      {},
      { timeout }
    );
  }

  async isConnected(): Promise<boolean> {
    return await this.connectionIndicator.evaluate((el) =>
      el.classList.contains('connected')
    );
  }
}
