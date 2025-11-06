import { useEffect, useMemo, useState } from "react";
import { Activity, Filter, Trash2, Search, Bell, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/useAuth";
import { useNotifications } from "@/contexts/NotificationContext";

const ActivityLog = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'activity' | 'notifications'>('activity');
  const [activityLogs, setActivityLogs] = useState<Array<{
    id: string;
    action: string;
    message: string | null;
    email: string | null;
    created_at: string;
  }>>([]);
  const { user } = useAuth();
  const { notifications, markAsRead, removeNotification } = useNotifications();

  useEffect(() => {
    const fetchLogs = async () => {
      const { data, error } = await supabase
        .from("activity_logs")
        .select("id, action, message, email, created_at")
        .order("created_at", { ascending: false })
        .limit(500);
      if (!error && data) {
        setActivityLogs(data as any);
      }
    };
    fetchLogs();

    const channel = supabase
      .channel("activity_logs_changes")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "activity_logs" },
        (payload) => {
          setActivityLogs((prev) => [payload.new as any, ...prev]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const filteredLogs = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (activeTab === 'activity') {
      if (!term) return activityLogs;
      return activityLogs.filter((log) =>
        (log.message || "").toLowerCase().includes(term) ||
        (log.email || "").toLowerCase().includes(term) ||
        (log.action || "").toLowerCase().includes(term)
      );
    } else {
      if (!term) return notifications;
      return notifications.filter((notification) =>
        notification.title.toLowerCase().includes(term) ||
        notification.message.toLowerCase().includes(term) ||
        notification.type.toLowerCase().includes(term)
      );
    }
  }, [searchTerm, activityLogs, notifications, activeTab]);

  const handleSelectItem = (itemId: string) => {
    setSelectedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleSelectAll = () => {
    if (selectedItems.length === filteredLogs.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(filteredLogs.map(log => log.id));
    }
  };

  const handleDelete = async () => {
    if (selectedItems.length === 0) return;
    
    if (activeTab === 'activity') {
      await supabase.from("activity_logs").delete().in("id", selectedItems);
      setActivityLogs((prev) => prev.filter((l) => !selectedItems.includes(l.id)));
    } else {
      // Remove notifications from context
      selectedItems.forEach(id => removeNotification(id));
    }
    setSelectedItems([]);
  };

  const handleDeleteAll = async () => {
    if (activeTab === 'activity') {
      await supabase.from("activity_logs").delete().neq("id", "");
      setActivityLogs([]);
    } else {
      // Clear all notifications
      notifications.forEach(notification => removeNotification(notification.id));
    }
    setSelectedItems([]);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">Activity</h1>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold text-foreground">Activity & Notifications</h2>
          <div className="flex gap-2">
            <Button
              variant={activeTab === 'activity' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('activity')}
              className="flex items-center gap-2"
            >
              <Activity className="h-4 w-4" />
              Activity Logs
            </Button>
            <Button
              variant={activeTab === 'notifications' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('notifications')}
              className="flex items-center gap-2"
            >
              <Bell className="h-4 w-4" />
              Notifications
              {notifications.filter(n => !n.read).length > 0 && (
                <Badge variant="destructive" className="ml-1 h-4 w-4 p-0 flex items-center justify-center text-xs">
                  {notifications.filter(n => !n.read).length}
                </Badge>
              )}
            </Button>
          </div>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            className="border-primary text-primary hover:bg-primary hover:text-primary-foreground"
            onClick={handleDelete}
            disabled={selectedItems.length === 0}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            DELETE
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            className="border-primary text-primary hover:bg-primary hover:text-primary-foreground"
            onClick={handleDeleteAll}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            DELETE ALL
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            className="border-primary text-primary hover:bg-primary hover:text-primary-foreground"
            onClick={() => console.log("Filter activity logs")}
          >
            <Filter className="h-4 w-4 mr-2" />
            FILTER
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
        <Input
          placeholder={activeTab === 'activity' ? "Search activity logs..." : "Search notifications..."}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 bg-card border-border"
        />
      </div>

      {/* Activity Log List */}
      <Card className="bg-card border-border p-6">
        <div className="space-y-4">
          {/* Select All Header */}
          <div className="flex items-center gap-3 pb-2 border-b border-border">
            <Checkbox
              checked={selectedItems.length === filteredLogs.length && filteredLogs.length > 0}
              onCheckedChange={handleSelectAll}
              className="border-border data-[state=checked]:bg-primary"
            />
            <span className="text-sm font-medium text-muted-foreground">
              Select All ({selectedItems.length}/{filteredLogs.length})
            </span>
          </div>

          {/* Activity Items */}
          {filteredLogs.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              {activeTab === 'activity' ? 'No activity logs found' : 'No notifications found'}
            </div>
          ) : (
            filteredLogs.map((item) => {
              if (activeTab === 'activity') {
                const log = item as any;
                return (
                  <div key={log.id} className="flex items-center gap-3 py-2 hover:bg-muted/50 rounded">
                    <Checkbox
                      checked={selectedItems.includes(log.id)}
                      onCheckedChange={() => handleSelectItem(log.id)}
                      className="border-border data-[state=checked]:bg-primary"
                    />
                    <Activity className="h-4 w-4 text-primary flex-shrink-0" />
                    <span className="text-foreground flex-1">
                      {log.message || `${log.email || "Unknown user"} ${log.action}`} • {new Date(log.created_at).toLocaleString()}
                    </span>
                  </div>
                );
              } else {
                const notification = item as any;
                return (
                  <div key={notification.id} className={`flex items-center gap-3 py-2 hover:bg-muted/50 rounded ${!notification.read ? 'bg-blue-50/50' : ''}`}>
                    <Checkbox
                      checked={selectedItems.includes(notification.id)}
                      onCheckedChange={() => handleSelectItem(notification.id)}
                      className="border-border data-[state=checked]:bg-primary"
                    />
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {notification.type === 'detection' && <Bell className="h-4 w-4 text-blue-500" />}
                      {notification.type === 'alert' && <Eye className="h-4 w-4 text-red-500" />}
                      {notification.type === 'info' && <Activity className="h-4 w-4 text-blue-500" />}
                      {!notification.read && <div className="w-2 h-2 bg-blue-500 rounded-full" />}
                    </div>
                    <div className="flex-1">
                      <div className="text-foreground font-medium">{notification.title}</div>
                      <div className="text-sm text-muted-foreground">{notification.message}</div>
                      <div className="text-xs text-muted-foreground">{notification.timestamp.toLocaleString()}</div>
                    </div>
                  </div>
                );
              }
            })
          )}
        </div>
      </Card>
    </div>
  );
};

export default ActivityLog;