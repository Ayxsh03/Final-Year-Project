import { useState } from "react";
import { MapPin, Search, Filter, Plus, Edit, Trash2, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
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

const Location = () => {
  const [searchTerm, setSearchTerm] = useState("");

  const locations = [
    {
      id: "LOC001",
      name: "Main Office Building",
      address: "123 Business District, City Center",
      city: "Mumbai",
      state: "Maharashtra",
      country: "India",
      devices: 12,
      status: "active"
    },
    {
      id: "LOC002", 
      name: "Warehouse - North",
      address: "456 Industrial Area, Sector 5",
      city: "Delhi",
      state: "Delhi",
      country: "India",
      devices: 8,
      status: "active"
    },
    {
      id: "LOC003",
      name: "Retail Store - Downtown",
      address: "789 Shopping Complex, Mall Road",
      city: "Bangalore",
      state: "Karnataka", 
      country: "India",
      devices: 6,
      status: "inactive"
    }
  ];

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-card border-border/50">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground font-medium mb-1">
              Total Locations
            </div>
            <div className="text-2xl font-bold text-blue-600">15</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-card border-border/50">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground font-medium mb-1">
              Active
            </div>
            <div className="text-2xl font-bold text-green-600">12</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-border/50">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground font-medium mb-1">
              Inactive
            </div>
            <div className="text-2xl font-bold text-red-600">3</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-border/50">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground font-medium mb-1">
              Total Devices
            </div>
            <div className="text-2xl font-bold text-purple-600">126</div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="Search locations by name, city..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-card border-border"
          />
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="border-primary text-primary hover:bg-primary hover:text-primary-foreground">
            <Filter className="h-4 w-4 mr-2" />
            FILTER
          </Button>
          <Button size="sm" className="bg-primary hover:bg-primary/90 text-primary-foreground">
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
              <TableHead className="text-foreground">Location ID</TableHead>
              <TableHead className="text-foreground">Name</TableHead>
              <TableHead className="text-foreground">Address</TableHead>
              <TableHead className="text-foreground">City</TableHead>
              <TableHead className="text-foreground">State</TableHead>
              <TableHead className="text-foreground">Devices</TableHead>
              <TableHead className="text-foreground">Status</TableHead>
              <TableHead className="text-foreground">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {locations.map((location) => (
              <TableRow key={location.id} className="border-border">
                <TableCell className="font-medium">{location.id}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-primary" />
                    {location.name}
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {location.address}
                </TableCell>
                <TableCell>{location.city}</TableCell>
                <TableCell>{location.state}</TableCell>
                <TableCell>
                  <Badge variant="secondary" className="bg-primary/10 text-primary">
                    {location.devices}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge 
                    variant={location.status === "active" ? "default" : "secondary"}
                    className={location.status === "active" 
                      ? "bg-green-100 text-green-800 border-green-200" 
                      : "bg-red-100 text-red-800 border-red-200"
                    }
                  >
                    {location.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0 text-primary hover:bg-primary/10">
                        <span className="sr-only">Open menu</span>
                        <span className="text-primary font-medium">ACTION</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-card border-border">
                      <DropdownMenuItem className="hover:bg-muted cursor-pointer">
                        <Eye className="mr-2 h-4 w-4" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem className="hover:bg-muted cursor-pointer">
                        <Edit className="mr-2 h-4 w-4" />
                        Edit Location
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-destructive hover:bg-destructive/10 cursor-pointer">
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

export default Location;