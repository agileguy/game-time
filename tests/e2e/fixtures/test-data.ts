/**
 * Test data fixtures for e2e tests
 */

export const testPlayers = {
  host: {
    name: 'TestHost',
    maxPlayers: 12,
    isPublic: true,
  },
  player1: {
    name: 'Player1',
  },
  player2: {
    name: 'Player2',
  },
  player3: {
    name: 'Player3',
  },
  player4: {
    name: 'Player4',
  },
};

export const invalidRoomCodes = [
  '',           // Empty
  '123',        // Too short
  '12345',      // Too long
  'ABC',        // Too short
  'ABCDE',      // Too long
  'abc1',       // Lowercase
  '!@#$',       // Special characters
];

export const validPlayerNames = [
  'Alice',
  'Bob',
  'Charlie',
  'Dave',
  'Eve123',
  'Test Player',
];

export const invalidPlayerNames = [
  '',           // Empty
  ' ',          // Whitespace only
  'a'.repeat(51), // Too long (> 50 chars)
];

export const roomConfigurations = {
  default: {
    maxPlayers: 12,
    isPublic: true,
  },
  small: {
    maxPlayers: 4,
    isPublic: true,
  },
  large: {
    maxPlayers: 20,
    isPublic: true,
  },
  private: {
    maxPlayers: 12,
    isPublic: false,
  },
};

/**
 * Generate a random valid room code (4 uppercase alphanumeric characters)
 */
export function generateRoomCode(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let code = '';
  for (let i = 0; i < 4; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

/**
 * Generate a random player name
 */
export function generatePlayerName(prefix: string = 'Player'): string {
  return `${prefix}${Math.floor(Math.random() * 10000)}`;
}

/**
 * Wait for a specific duration
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
