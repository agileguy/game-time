/**
 * Player List Component
 * Reusable component for displaying players in a room
 */

import { dom } from '../utils.js';

/**
 * Create player list element
 * @param {Array} players - Array of player objects
 * @param {Object} options - Display options
 * @returns {HTMLElement} Player list element
 */
export function createPlayerList(players = [], options = {}) {
  const {
    showHost = true,
    showConnected = true,
    showActions = false,
    onKick = null,
    currentPlayerId = null,
  } = options;

  const container = dom.createElement('div', {
    className: 'player-list',
  });

  if (players.length === 0) {
    const emptyState = dom.createElement('div', {
      className: 'player-list-empty text-secondary',
    }, 'Waiting for players...');
    container.appendChild(emptyState);
    return container;
  }

  // Sort players: host first, then by join order
  const sortedPlayers = [...players].sort((a, b) => {
    if (a.is_host && !b.is_host) return -1;
    if (!a.is_host && b.is_host) return 1;
    return (a.joined_at || 0) - (b.joined_at || 0);
  });

  sortedPlayers.forEach((player) => {
    const playerEl = createPlayerCard(player, {
      showHost,
      showConnected,
      showActions,
      onKick,
      isCurrentPlayer: player.id === currentPlayerId,
    });
    container.appendChild(playerEl);
  });

  return container;
}

/**
 * Create individual player card
 * @param {Object} player - Player object
 * @param {Object} options - Display options
 * @returns {HTMLElement} Player card element
 */
function createPlayerCard(player, options = {}) {
  const {
    showHost = true,
    showConnected = true,
    showActions = false,
    onKick = null,
    isCurrentPlayer = false,
  } = options;

  const classList = ['player-card'];
  if (!player.connected && showConnected) {
    classList.push('player-disconnected');
  }
  if (isCurrentPlayer) {
    classList.push('player-current');
  }
  if (player.is_host) {
    classList.push('player-host');
  }

  const card = dom.createElement('div', {
    className: classList.join(' '),
    dataset: { playerId: player.id },
  });

  // Player avatar (first letter of name)
  const avatar = dom.createElement('div', {
    className: 'player-avatar',
  }, player.name.charAt(0).toUpperCase());

  // Player info
  const info = dom.createElement('div', {
    className: 'player-info',
  });

  const nameContainer = dom.createElement('div', {
    className: 'player-name-container',
  });

  const name = dom.createElement('div', {
    className: 'player-name',
  }, player.name);

  nameContainer.appendChild(name);

  // Host badge
  if (player.is_host && showHost) {
    const hostBadge = dom.createElement('span', {
      className: 'badge badge-warning player-badge',
    }, 'HOST');
    nameContainer.appendChild(hostBadge);
  }

  // You badge
  if (isCurrentPlayer) {
    const youBadge = dom.createElement('span', {
      className: 'badge badge-primary player-badge',
    }, 'YOU');
    nameContainer.appendChild(youBadge);
  }

  info.appendChild(nameContainer);

  // Connection status
  if (showConnected) {
    const status = dom.createElement('div', {
      className: player.connected ? 'connected text-sm' : 'disconnected text-sm',
    }, player.connected ? '● Online' : '○ Offline');
    info.appendChild(status);
  }

  card.appendChild(avatar);
  card.appendChild(info);

  // Kick button (for host)
  if (showActions && onKick && !player.is_host && !isCurrentPlayer) {
    const kickBtn = dom.createElement('button', {
      className: 'btn btn-error btn-sm player-kick-btn',
      onClick: (e) => {
        e.stopPropagation();
        onKick(player.id);
      },
    }, 'Kick');
    card.appendChild(kickBtn);
  }

  return card;
}

/**
 * Update player list
 * @param {HTMLElement} container - Container element
 * @param {Array} players - Updated players array
 * @param {Object} options - Display options
 */
export function updatePlayerList(container, players, options = {}) {
  // Clear existing list
  container.innerHTML = '';

  // Create new list
  const newList = createPlayerList(players, options);

  // Move children from new list to container
  while (newList.firstChild) {
    container.appendChild(newList.firstChild);
  }
}

// Add player list styles
const style = document.createElement('style');
style.textContent = `
  .player-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .player-list-empty {
    padding: var(--space-8);
    text-align: center;
    font-size: var(--font-size-lg);
  }

  .player-card {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-4);
    background: var(--color-bg-secondary);
    border: var(--border-width) solid var(--color-primary);
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-base);
  }

  .player-card:hover {
    transform: translateX(4px);
    box-shadow: var(--shadow-md);
  }

  .player-host {
    border-color: var(--color-warning);
  }

  .player-current {
    border-color: var(--color-secondary);
  }

  .player-disconnected {
    opacity: 0.6;
    border-color: var(--color-gray-400);
  }

  .player-avatar {
    width: 3rem;
    height: 3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-primary);
    color: #000000;
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-bold);
    flex-shrink: 0;
  }

  .player-info {
    flex: 1;
    min-width: 0;
  }

  .player-name-container {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    flex-wrap: wrap;
    margin-bottom: var(--space-1);
  }

  .player-name {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .player-badge {
    font-size: var(--font-size-xs);
    padding: var(--space-1) var(--space-2);
  }

  .player-kick-btn {
    padding: var(--space-2) var(--space-4);
    font-size: var(--font-size-sm);
  }

  /* Display view (TV screen) - larger sizing */
  .display-view .player-list {
    gap: var(--space-6);
  }

  .display-view .player-card {
    padding: var(--space-6);
  }

  .display-view .player-avatar {
    width: 5rem;
    height: 5rem;
    font-size: var(--font-size-display-sm);
  }

  .display-view .player-name {
    font-size: var(--font-size-display-xs);
  }

  .display-view .player-badge {
    font-size: var(--font-size-base);
    padding: var(--space-2) var(--space-4);
  }
`;
document.head.appendChild(style);

export default {
  createPlayerList,
  updatePlayerList,
};
