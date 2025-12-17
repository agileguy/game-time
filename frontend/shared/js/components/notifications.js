/**
 * Notification System
 * Toast notifications for user feedback
 */

import CONFIG from '../config.js';
import { dom } from '../utils.js';

/**
 * Notification types
 */
export const NotificationType = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
};

/**
 * Notification Manager Class
 */
export class NotificationManager {
  constructor() {
    this.container = null;
    this.notifications = [];
    this.init();
  }

  /**
   * Initialize notification container
   */
  init() {
    this.container = dom.createElement('div', {
      className: 'notification-container',
      id: 'notifications',
    });

    document.body.appendChild(this.container);
  }

  /**
   * Show notification
   * @param {string} message - Notification message
   * @param {string} type - Notification type
   * @param {number} duration - Duration in ms (0 for persistent)
   * @returns {Object} Notification object with dismiss method
   */
  show(message, type = NotificationType.INFO, duration = CONFIG.ui.toastDuration) {
    const id = `notification-${Date.now()}-${Math.random()}`;

    const notification = dom.createElement('div', {
      className: `notification notification-${type} fade-in`,
      id,
      dataset: { type },
    });

    // Icon based on type
    const icon = this.getIcon(type);
    const iconEl = dom.createElement('span', {
      className: 'notification-icon',
    }, icon);

    // Message
    const messageEl = dom.createElement('div', {
      className: 'notification-message',
    }, message);

    // Close button
    const closeBtn = dom.createElement('button', {
      className: 'notification-close',
      onClick: () => this.dismiss(id),
    }, '×');

    notification.appendChild(iconEl);
    notification.appendChild(messageEl);
    notification.appendChild(closeBtn);

    this.container.appendChild(notification);

    const notificationObj = {
      id,
      element: notification,
      dismiss: () => this.dismiss(id),
    };

    this.notifications.push(notificationObj);

    // Auto dismiss after duration
    if (duration > 0) {
      setTimeout(() => {
        this.dismiss(id);
      }, duration);
    }

    return notificationObj;
  }

  /**
   * Get icon for notification type
   * @param {string} type - Notification type
   * @returns {string} Icon character
   */
  getIcon(type) {
    const icons = {
      [NotificationType.SUCCESS]: '✓',
      [NotificationType.ERROR]: '✕',
      [NotificationType.WARNING]: '⚠',
      [NotificationType.INFO]: 'ℹ',
    };

    return icons[type] || icons[NotificationType.INFO];
  }

  /**
   * Dismiss notification
   * @param {string} id - Notification ID
   */
  dismiss(id) {
    const index = this.notifications.findIndex((n) => n.id === id);
    if (index === -1) return;

    const notification = this.notifications[index];
    notification.element.classList.add('fade-out');

    setTimeout(() => {
      notification.element.remove();
      this.notifications.splice(index, 1);
    }, 300);
  }

  /**
   * Show success notification
   * @param {string} message - Success message
   * @param {number} duration - Duration in ms
   * @returns {Object} Notification object
   */
  success(message, duration) {
    return this.show(message, NotificationType.SUCCESS, duration);
  }

  /**
   * Show error notification
   * @param {string} message - Error message
   * @param {number} duration - Duration in ms
   * @returns {Object} Notification object
   */
  error(message, duration = CONFIG.ui.toastErrorDuration) {
    return this.show(message, NotificationType.ERROR, duration);
  }

  /**
   * Show warning notification
   * @param {string} message - Warning message
   * @param {number} duration - Duration in ms
   * @returns {Object} Notification object
   */
  warning(message, duration) {
    return this.show(message, NotificationType.WARNING, duration);
  }

  /**
   * Show info notification
   * @param {string} message - Info message
   * @param {number} duration - Duration in ms
   * @returns {Object} Notification object
   */
  info(message, duration) {
    return this.show(message, NotificationType.INFO, duration);
  }

  /**
   * Clear all notifications
   */
  clearAll() {
    this.notifications.forEach((notification) => {
      notification.element.remove();
    });
    this.notifications = [];
  }
}

// Add notification styles
const style = document.createElement('style');
style.textContent = `
  .notification-container {
    position: fixed;
    top: var(--space-6);
    right: var(--space-6);
    z-index: var(--z-notification);
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    max-width: 400px;
    pointer-events: none;
  }

  .notification {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-4);
    background: var(--color-bg-secondary);
    border: var(--border-width) solid var(--color-primary);
    box-shadow: var(--shadow-lg);
    pointer-events: auto;
    font-size: var(--font-size-sm);
  }

  .notification-icon {
    font-size: var(--font-size-xl);
    flex-shrink: 0;
  }

  .notification-message {
    flex: 1;
    word-wrap: break-word;
  }

  .notification-close {
    font-size: var(--font-size-2xl);
    color: var(--color-gray-500);
    padding: 0;
    width: 2rem;
    height: 2rem;
    flex-shrink: 0;
  }

  .notification-close:hover {
    color: var(--color-primary);
  }

  .notification-success {
    border-color: var(--color-success);
  }

  .notification-success .notification-icon {
    color: var(--color-success);
  }

  .notification-error {
    border-color: var(--color-error);
  }

  .notification-error .notification-icon {
    color: var(--color-error);
  }

  .notification-warning {
    border-color: var(--color-warning);
  }

  .notification-warning .notification-icon {
    color: var(--color-warning);
  }

  .notification-info {
    border-color: var(--color-info);
  }

  .notification-info .notification-icon {
    color: var(--color-info);
  }

  .fade-out {
    animation: fadeOut var(--transition-slow) forwards;
  }

  @keyframes fadeOut {
    to {
      opacity: 0;
      transform: translateX(100%);
    }
  }

  /* Mobile adjustments */
  @media (max-width: 640px) {
    .notification-container {
      top: auto;
      bottom: var(--space-4);
      right: var(--space-4);
      left: var(--space-4);
      max-width: none;
    }
  }
`;
document.head.appendChild(style);

// Global notification instance
export const notifications = new NotificationManager();

export default notifications;
