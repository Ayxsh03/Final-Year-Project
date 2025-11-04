import React, { useState, useEffect } from 'react';
import { X, Bell, AlertTriangle, CheckCircle, Info, AlertCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useNotifications, Notification } from '@/contexts/NotificationContext';

const NotificationPopup: React.FC = () => {
  const { notifications, markAsRead, removeNotification } = useNotifications();
  const [visibleNotifications, setVisibleNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    // Show only the latest unread notification as a popup
    const latestUnread = notifications.find(n => !n.read);
    if (latestUnread) {
      setVisibleNotifications([latestUnread]);
      
      // Auto-hide after 5 seconds
      const timer = setTimeout(() => {
        markAsRead(latestUnread.id);
        setVisibleNotifications([]);
      }, 5000);

      return () => clearTimeout(timer);
    } else {
      setVisibleNotifications([]);
    }
  }, [notifications, markAsRead]);

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'detection':
        return <Bell className="h-5 w-5 text-blue-500" />;
      case 'alert':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'error':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      default:
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const getBorderColor = (type: Notification['type']) => {
    switch (type) {
      case 'detection':
        return 'border-l-blue-500';
      case 'alert':
        return 'border-l-red-500';
      case 'success':
        return 'border-l-green-500';
      case 'warning':
        return 'border-l-yellow-500';
      case 'error':
        return 'border-l-red-500';
      default:
        return 'border-l-blue-500';
    }
  };

  if (visibleNotifications.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {visibleNotifications.map((notification) => (
        <Card
          key={notification.id}
          className={`bg-card border-border shadow-lg border-l-4 ${getBorderColor(notification.type)} animate-in slide-in-from-right-full duration-300`}
        >
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              {getIcon(notification.type)}
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-semibold text-foreground">
                  {notification.title}
                </h4>
                <p className="text-sm text-muted-foreground mt-1">
                  {notification.message}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  {notification.timestamp.toLocaleTimeString()}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-muted"
                onClick={() => {
                  markAsRead(notification.id);
                  setVisibleNotifications([]);
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default NotificationPopup;
