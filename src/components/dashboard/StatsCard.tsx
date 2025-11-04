import { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    label: string;
  };
  status?: "online" | "offline" | "active" | "inactive";
  className?: string;
}

export const StatsCard = ({ 
  title, 
  value, 
  icon: Icon, 
  trend, 
  status,
  className 
}: StatsCardProps) => {
  const getStatusColor = (status?: string) => {
    switch (status) {
      case "online": return "text-online";
      case "offline": return "text-offline";
      case "active": return "text-active";
      case "inactive": return "text-inactive";
      default: return "text-primary";
    }
  };

  return (
    <Card className={cn("bg-gradient-card border-border/50", className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <div className="flex items-center gap-2 mt-2">
              <p className="text-2xl font-bold text-foreground">{value}</p>
              {status && (
                <div className={cn("w-2 h-2 rounded-full", 
                  status === "online" || status === "active" ? "bg-online" : "bg-offline"
                )} />
              )}
            </div>
            {trend && (
              <p className="text-xs text-muted-foreground mt-1">
                <span className={trend.value >= 0 ? "text-success" : "text-destructive"}>
                  {trend.value >= 0 ? "+" : ""}{trend.value}%
                </span>{" "}
                {trend.label}
              </p>
            )}
          </div>
          <div className={cn("p-3 rounded-lg bg-primary/10", getStatusColor(status))}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};