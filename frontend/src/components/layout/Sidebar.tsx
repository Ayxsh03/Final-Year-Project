import { Link, useLocation } from "react-router-dom";
import { 
  LayoutDashboard, 
  Users, 
  Brain, 
  UserCheck, 
  Car, 
  Users2, 
  ParkingCircle, 
  Package, 
  Settings, 
  Activity,
  Menu,
  Shield,
  Video
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
}

const menuItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/" },
  { icon: Video, label: "Live Feed", href: "/live-feed" },
  { icon: Users, label: "Footfall", href: "/footfall" },
  { icon: Brain, label: "AI Intelligence", href: "/ai-intelligence" },
  { icon: Users2, label: "People Count", href: "/people-count" },
  { icon: Package, label: "Assets", href: "/assets", hasSubmenu: true },
  { icon: Settings, label: "Settings", href: "/settings" },
  { icon: Activity, label: "Activity Log", href: "/activity-log" },
];

export const Sidebar = ({ collapsed, onToggleCollapse }: SidebarProps) => {
  const location = useLocation();

  return (
    <div className={cn(
      "fixed left-0 top-0 h-screen bg-sidebar border-r border-sidebar-border transition-all duration-300 z-50",
      collapsed ? "w-16" : "w-64"
    )}>
      <div className={cn("flex items-center p-4 border-b border-sidebar-border", collapsed ? "justify-center" : "justify-between")}>
        {!collapsed && (
          <div className="flex items-center gap-2">
            <Shield className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold text-sidebar-foreground">SecureWatch</span>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="text-sidebar-foreground hover:bg-sidebar-accent"
        >
          <Menu className="h-4 w-4" />
        </Button>
      </div>

      <nav className="mt-6">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-3 text-sidebar-foreground hover:bg-sidebar-accent transition-colors",
                isActive && "bg-sidebar-accent border-r-2 border-primary",
                collapsed && "justify-center px-2"
              )}
            >
              <item.icon className="h-5 w-5" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>
    </div>
  );
};