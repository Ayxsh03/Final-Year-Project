import { useState } from "react";
import { Building, Search, Filter, Plus, Edit, Trash2, Eye } from "lucide-react";
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

const Property = () => {
  const [searchTerm, setSearchTerm] = useState("");

  const properties = [
    {
      id: "PROP001",
      name: "Corporate Headquarters",
      type: "Office Building",
      location: "Main Office Building",
      area: "25,000 sq ft",
      floors: 15,
      devices: 45,
      status: "occupied"
    },
    {
      id: "PROP002", 
      name: "Storage Facility A",
      type: "Warehouse",
      location: "Warehouse - North",
      area: "50,000 sq ft",
      floors: 2,
      devices: 20,
      status: "occupied"
    },
    {
      id: "PROP003",
      name: "Retail Space - Ground Floor",
      type: "Retail Store",
      location: "Retail Store - Downtown",
      area: "5,000 sq ft",
      floors: 1,
      devices: 8,
      status: "vacant"
    }
  ];

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-card border-border/50">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground font-medium mb-1">
              Total Properties
            </div>
            <div className="text-2xl font-bold text-blue-600">28</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-card border-border/50">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground font-medium mb-1">
              Occupied
            </div>
            <div className="text-2xl font-bold text-green-600">22</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-border/50">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground font-medium mb-1">
              Vacant
            </div>
            <div className="text-2xl font-bold text-orange-600">6</div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-border/50">
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground font-medium mb-1">
              Total Area
            </div>
            <div className="text-2xl font-bold text-purple-600">850K</div>
            <div className="text-xs text-muted-foreground">sq ft</div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="Search properties by name, type..."
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
              <TableHead className="text-foreground">Property ID</TableHead>
              <TableHead className="text-foreground">Name</TableHead>
              <TableHead className="text-foreground">Type</TableHead>
              <TableHead className="text-foreground">Location</TableHead>
              <TableHead className="text-foreground">Area</TableHead>
              <TableHead className="text-foreground">Floors</TableHead>
              <TableHead className="text-foreground">Devices</TableHead>
              <TableHead className="text-foreground">Status</TableHead>
              <TableHead className="text-foreground">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {properties.map((property) => (
              <TableRow key={property.id} className="border-border">
                <TableCell className="font-medium">{property.id}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Building className="h-4 w-4 text-primary" />
                    {property.name}
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {property.type}
                </TableCell>
                <TableCell>{property.location}</TableCell>
                <TableCell>{property.area}</TableCell>
                <TableCell>
                  <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                    {property.floors}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" className="bg-primary/10 text-primary">
                    {property.devices}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge 
                    variant={property.status === "occupied" ? "default" : "secondary"}
                    className={property.status === "occupied" 
                      ? "bg-green-100 text-green-800 border-green-200" 
                      : "bg-orange-100 text-orange-800 border-orange-200"
                    }
                  >
                    {property.status}
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
                        Edit Property
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

export default Property;