import { Page, Locator } from '@playwright/test';

/**
 * Page object for Controller Horse Race screen
 */
export class ControllerHorseRacePage {
  readonly page: Page;

  // Header
  readonly playerScore: Locator;
  readonly connectionIndicator: Locator;
  readonly phaseText: Locator;
  readonly phaseTimer: Locator;

  // Betting Phase
  readonly bettingPhase: Locator;
  readonly bettingInstructions: Locator;
  readonly currentBet: Locator;
  readonly betHorseName: Locator;
  readonly changeBetButton: Locator;
  readonly horseSelection: Locator;

  // Racing Phase
  readonly racingPhase: Locator;
  readonly betReminderHorse: Locator;
  readonly racePositions: Locator;

  // Results Phase
  readonly resultsPhase: Locator;
  readonly winStatusIcon: Locator;
  readonly winStatusText: Locator;
  readonly pointsEarned: Locator;
  readonly resultsList: Locator;
  readonly finalScore: Locator;

  // Waiting Phase
  readonly waitingPhase: Locator;

  // Footer
  readonly roomCode: Locator;
  readonly roundDisplay: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.playerScore = page.locator('#player-score');
    this.connectionIndicator = page.locator('#connection-indicator');
    this.phaseText = page.locator('#phase-text');
    this.phaseTimer = page.locator('#phase-timer');

    // Betting Phase
    this.bettingPhase = page.locator('#betting-phase');
    this.bettingInstructions = page.locator('.betting-instructions');
    this.currentBet = page.locator('#current-bet');
    this.betHorseName = page.locator('#bet-horse-name');
    this.changeBetButton = page.locator('#change-bet-btn');
    this.horseSelection = page.locator('#horse-selection');

    // Racing Phase
    this.racingPhase = page.locator('#racing-phase');
    this.betReminderHorse = page.locator('#bet-reminder-horse');
    this.racePositions = page.locator('#race-positions');

    // Results Phase
    this.resultsPhase = page.locator('#results-phase');
    this.winStatusIcon = page.locator('#win-status-icon');
    this.winStatusText = page.locator('#win-status-text');
    this.pointsEarned = page.locator('#points-earned');
    this.resultsList = page.locator('#results-list');
    this.finalScore = page.locator('#final-score');

    // Waiting Phase
    this.waitingPhase = page.locator('#waiting-phase');

    // Footer
    this.roomCode = page.locator('#room-code');
    this.roundDisplay = page.locator('#round-display');
  }

  async goto() {
    await this.page.goto('http://localhost:7070/controller/horse-race.html');
    await this.page.waitForLoadState('networkidle');
  }

  async getPlayerScore(): Promise<number> {
    const scoreText = await this.playerScore.textContent() || '0';
    return parseInt(scoreText, 10);
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

  async isRacingPhaseVisible(): Promise<boolean> {
    return await this.racingPhase.isVisible();
  }

  async isResultsPhaseVisible(): Promise<boolean> {
    return await this.resultsPhase.isVisible();
  }

  async getAvailableHorses(): Promise<string[]> {
    // Wait for at least one horse card to be rendered
    await this.page.waitForSelector('.horse-bet-card', { state: 'visible', timeout: 10000 });

    const horseCards = await this.horseSelection.locator('.horse-bet-card').all();
    const horses: string[] = [];

    for (const card of horseCards) {
      const name = await card.locator('.horse-name').textContent();
      if (name) horses.push(name);
    }

    return horses;
  }

  async placeBet(horseIndex: number) {
    // Wait for horse cards to be rendered
    await this.page.waitForSelector('.horse-bet-card', { state: 'visible', timeout: 10000 });

    const horseCards = await this.horseSelection.locator('.horse-bet-card').all();
    if (horseIndex < 0 || horseIndex >= horseCards.length) {
      throw new Error(`Invalid horse index: ${horseIndex}`);
    }

    await horseCards[horseIndex].click();
    // Wait for bet to be processed
    await this.page.waitForTimeout(500);
  }

  async placeBetByName(horseName: string) {
    const horseCard = this.horseSelection
      .locator('.horse-bet-card')
      .filter({ hasText: horseName });

    await horseCard.click();
    // Wait for bet to be processed
    await this.page.waitForTimeout(500);
  }

  async getCurrentBet(): Promise<string | null> {
    if (await this.currentBet.isVisible()) {
      return await this.betHorseName.textContent();
    }
    return null;
  }

  async changeBet() {
    await this.changeBetButton.click();
  }

  async getBetReminder(): Promise<string> {
    return await this.betReminderHorse.textContent() || '';
  }

  async getRacePositions(): Promise<Array<{ lane: string; name: string; progress: number }>> {
    const positionBars = await this.racePositions.locator('.position-bar').all();
    const positions = [];

    for (const bar of positionBars) {
      const lane = await bar.locator('.position-lane').textContent() || '';
      const name = await bar.locator('.position-horse-name').textContent() || '';
      const progressBar = bar.locator('.position-progress');
      const progressStyle = await progressBar.getAttribute('style') || '';
      const widthMatch = progressStyle.match(/width:\s*(\d+(\.\d+)?)%/);
      const progress = widthMatch ? parseFloat(widthMatch[1]) : 0;

      positions.push({ lane, name, progress });
    }

    return positions;
  }

  async getWinStatus(): Promise<{ icon: string; text: string; points: string }> {
    return {
      icon: await this.winStatusIcon.textContent() || '',
      text: await this.winStatusText.textContent() || '',
      points: await this.pointsEarned.textContent() || '',
    };
  }

  async getRaceResults(): Promise<Array<{ position: string; name: string }>> {
    const resultItems = await this.resultsList.locator('.result-item').all();
    const results = [];

    for (const item of resultItems) {
      const position = await item.locator('.result-position').textContent() || '';
      const name = await item.locator('.result-horse-name').textContent() || '';
      results.push({ position, name });
    }

    return results;
  }

  async getFinalScore(): Promise<number> {
    const scoreText = await this.finalScore.textContent() || '0';
    return parseInt(scoreText, 10);
  }

  async waitForBettingPhase(timeout: number = 10000) {
    await this.bettingPhase.waitFor({ state: 'visible', timeout });
  }

  async waitForRacingPhase(timeout: number = 20000) {
    await this.racingPhase.waitFor({ state: 'visible', timeout });
  }

  async waitForResultsPhase(timeout: number = 30000) {
    await this.resultsPhase.waitFor({ state: 'visible', timeout });
  }

  async waitForRaceCompletion(timeout: number = 30000) {
    // Wait for all position bars to reach 100%
    await this.page.waitForFunction(
      () => {
        const bars = document.querySelectorAll('.position-progress');
        return Array.from(bars).every((bar) => {
          const style = (bar as HTMLElement).style.width;
          return style === '100%' || parseInt(style) >= 100;
        });
      },
      {},
      { timeout }
    );
  }
}
