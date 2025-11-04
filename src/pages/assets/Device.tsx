import { useState } from "react";
import { Monitor, Search, Filter, Plus, Edit, Trash2, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";

const Device = () => {
  const [searchTerm, setSearchTerm] = useState("");

  const devices = [
    {
      id: "S348SK",
      spotName: "Purchasedept2",
      property: "sami sabinsagroup",
      location: "sami sabinsa group",
      currentStatus: "On",
      status: true,
      isOnline: true
    },
    {
      id: "CWAZPR",
      spotName: "Ground Floor Forward Store",
      property: "sami sabinsagroup", 
      location: "sami sabinsa group",
      currentStatus: "Off",
      status: false,
      isOnline: true
    },
    {
      id: "AEU5TW",
      spotName: "seti office main road",
      property: "seti",
      location: "italy",
      currentStatus: "Off",
      status: false,
      isOnline: true
    },
    {
      id: "OSHWG1",
      spotName: "abandonedobj",
      property: "seti",
      location: "italy", 
      currentStatus: "On",
      status: true,
      isOnline: true
    },
    {
      id: "2DDM17",
      spotName: "canteen",
      property: "sami sabinsagroup",
      location: "sami sabinsa group",
      currentStatus: "On",
      status: true,
      isOnline: true
    },
    {
      id: "PXQ708",
      spotName: "rage 02",
      property: "sami sabinsagroup",
      location: "sami sabinsa group", 
      currentStatus: "On",
      status: true,
      isOnline: true
    }
  ];

  const handleStatusToggle = (deviceId: string) => {
    // Handle device status toggle
    console.log(`Toggling status for device: ${deviceId}`);
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="bg-gradient-card border-border/50">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground font-medium mb-1">
              Total Devices
            </div>
            <div className="text-2xl font-bold text-blue-600">95</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-card border-border/50 bg-gradient-to-r from-green-500 to-green-600">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-white/90 font-medium mb-1">
              Active
            </div>
            <div className="text-2xl font-bold text-white">63</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-border/50 bg-gradient-to-r from-red-500 to-red-600">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-white/90 font-medium mb-1">
              Inactive
            </div>
            <div className="text-2xl font-bold text-white">32</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-border/50">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground font-medium mb-1">
              Online
            </div>
            <div className="text-2xl font-bold text-teal-600">43</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-border/50">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground font-medium mb-1">
              Offline
            </div>
            <div className="text-2xl font-bold text-purple-600">52</div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="Search device by ID, Property and Location"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-card border-border"
          />
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            className="border-primary text-primary hover:bg-primary hover:text-primary-foreground"
            onClick={() => console.log("Filter devices")}
          >
            <Filter className="h-4 w-4 mr-2" />
            FILTER
          </Button>
          <Button 
            size="sm" 
            className="bg-primary hover:bg-primary/90 text-primary-foreground"
            onClick={() => console.log("Add new device")}
          >
            <Plus className="h-4 w-4 mr-2" />
            ADD
          </Button>
        </div>
      </div>

      {/* Data Table */}
      <Card className="bg-card border-border">
        <Table>
          <TableHeader>
            <TableRow className="border-border">
              <TableHead className="text-foreground">Device ID</TableHead>
              <TableHead className="text-foreground">Spot Name</TableHead>
              <TableHead className="text-foreground">Property</TableHead>
              <TableHead className="text-foreground">Location</TableHead>
              <TableHead className="text-foreground">Current Status</TableHead>
              <TableHead className="text-foreground">Status</TableHead>
              <TableHead className="text-foreground">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {devices.map((device) => (
              <TableRow key={device.id} className="border-border">
                <TableCell className="font-medium">{device.id}</TableCell>
                <TableCell>{device.spotName}</TableCell>
                <TableCell className="text-muted-foreground">
                  {device.property}
                </TableCell>
                <TableCell>{device.location}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div 
                      className={`w-3 h-3 rounded-full ${
                        device.currentStatus === "On" ? "bg-green-500" : "bg-red-500"
                      }`}
                    />
                    <span className={
                      device.currentStatus === "On" ? "text-green-600" : "text-red-600"
                    }>
                      {device.currentStatus}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <Switch
                    checked={device.status}
                    onCheckedChange={() => handleStatusToggle(device.id)}
                    className="data-[state=checked]:bg-green-500"
                  />
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0 text-primary hover:bg-primary/10">
                        <span className="sr-only">Open menu</span>
                        <span className="text-primary font-medium">ACTION</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-popover border-border">
                      <DropdownMenuItem 
                        className="hover:bg-muted cursor-pointer"
                        onClick={() => console.log("View details for device:", device.id)}
                      >
                        <Eye className="mr-2 h-4 w-4" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="hover:bg-muted cursor-pointer"
                        onClick={() => console.log("Edit device:", device.id)}
                      >
                        <Edit className="mr-2 h-4 w-4" />
                        Edit Device
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="text-destructive hover:bg-destructive/10 cursor-pointer"
                        onClick={() => {
                          if (confirm("Are you sure you want to delete this device?")) {
                            console.log("Delete device:", device.id);
                          }
                        }}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
};

export default Device;