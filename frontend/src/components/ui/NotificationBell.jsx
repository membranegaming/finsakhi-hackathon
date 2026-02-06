import { useState, useEffect } from 'react';
import { useApp } from '../../contexts/AppContext';
import './NotificationBell.css';

function NotificationBell() {
  const { t } = useApp();
  const [showPanel, setShowPanel] = useState(false);
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      title: 'New Learning Module Available',
      message: 'Check out the new advanced investment strategies module',
      time: '5 min ago',
      read: false,
      type: 'info'
    },
    {
      id: 2,
      title: 'Achievement Unlocked!',
      message: 'You completed 5 lessons this week',
      time: '1 hour ago',
      read: false,
      type: 'success'
    },
    {
      id: 3,
      title: 'Mentor Message',
      message: 'Your mentor has reviewed your progress',
      time: '2 hours ago',
      read: true,
      type: 'message'
    }
  ]);
  const [popupNotification, setPopupNotification] = useState(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  const handleNotificationClick = (notification) => {
    // Mark as read
    setNotifications(prev =>
      prev.map(n => n.id === notification.id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  // Simulate new notification popup
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!showPanel && notifications.some(n => !n.read)) {
        const unread = notifications.find(n => !n.read);
        if (unread) {
          setPopupNotification(unread);
          setTimeout(() => setPopupNotification(null), 5000);
        }
      }
    }, 3000);

    return () => clearTimeout(timer);
  }, [showPanel, notifications]);

  return (
    <>
      <div className="notification-bell-container">
        <button
          className="notification-bell"
          onClick={() => setShowPanel(!showPanel)}
          aria-label="Notifications"
        >
          {/* Bell Icon */}
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
          {unreadCount > 0 && (
            <span className="notification-badge">{unreadCount}</span>
          )}
        </button>

        {showPanel && (
          <div className="notification-panel">
            <div className="notification-header">
              <h3>Notifications</h3>
              <div className="notification-actions">
                <button onClick={markAllAsRead} className="action-btn">
                  Mark all read
                </button>
                <button onClick={clearAll} className="action-btn">
                  Clear all
                </button>
              </div>
            </div>

            <div className="notification-list">
              {notifications.length === 0 ? (
                <div className="no-notifications">
                  <p>No notifications</p>
                </div>
              ) : (
                notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`notification-item ${!notification.read ? 'unread' : ''}`}
                    onClick={() => handleNotificationClick(notification)}
                  >
                    <div className={`notification-icon ${notification.type}`}>
                      {notification.type === 'success' && '🎉'}
                      {notification.type === 'info' && 'ℹ️'}
                      {notification.type === 'message' && '💬'}
                    </div>
                    <div className="notification-content">
                      <h4>{notification.title}</h4>
                      <p>{notification.message}</p>
                      <span className="notification-time">{notification.time}</span>
                    </div>
                    {!notification.read && <div className="unread-dot"></div>}
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* Popup Notification */}
      {popupNotification && !showPanel && (
        <div className="notification-popup">
          <div className="popup-content">
            <div className={`popup-icon ${popupNotification.type}`}>
              {popupNotification.type === 'success' && '🎉'}
              {popupNotification.type === 'info' && 'ℹ️'}
              {popupNotification.type === 'message' && '💬'}
            </div>
            <div className="popup-text">
              <h4>{popupNotification.title}</h4>
              <p>{popupNotification.message}</p>
            </div>
            <button
              className="popup-close"
              onClick={() => setPopupNotification(null)}
            >
              ×
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default NotificationBell;

