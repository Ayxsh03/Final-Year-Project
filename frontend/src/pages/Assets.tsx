import { useState } from "react";
import { useLocation } from "react-router-dom";
import { Package, MapPin, Building, Monitor } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Location from "./assets/Location";
import Property from "./assets/Property";
import Device from "./assets/Device";

const Assets = () => {
  const location = useLocation();
  const [activeTab, setActiveTab] = useState("location");

  // Parse the current path to determine active tab
  const path = location.pathname;
  const currentTab = path.includes("/location") ? "location" 
    : path.includes("/property") ? "property"
    : path.includes("/device") ? "device" 
    : "location";

  const tabs = [
    { id: "location", label: "Location", icon: MapPin },
    { id: "property", label: "Property", icon: Building },
    { id: "device", label: "Device", icon: Monitor },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case "location":
        return <Location />;
      case "property":
        return <Property />;
      case "device":
        return <Device />;
      default:
        return <Location />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">Assets</h1>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-muted p-1 rounded-lg w-fit">
        {tabs.map((tab) => {
          const IconComponent = tab.icon;
          return (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? "default" : "ghost"}
              size="sm"
              onClick={() => {
                setActiveTab(tab.id);
                // Update URL to reflect the current tab
                window.history.pushState({}, '', `/assets/${tab.id}`);
              }}
              className={`flex items-center gap-2 ${
                activeTab === tab.id 
                  ? "bg-primary text-primary-foreground" 
                  : "hover:bg-background"
              }`}
            >
              <IconComponent className="h-4 w-4" />
              {tab.label}
            </Button>
          );
        })}
      </div>

      {/* Content */}
      {renderContent()}
    </div>
  );
};

export default Assets;