import { useState, useEffect } from "react";
import { Monitor, Grid3X3, Grid2X2, Maximize2, Settings, AlertTriangle } from "lucide-react";
import { useCameras } from "@/hooks/useDetectionData";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";

type LayoutType = "1x1" | "2x2" | "3x3" | "4x4";

const layoutConfigs = {
  "1x1": { grid: "grid-cols-1", maxCameras: 1 },
  "2x2": { grid: "grid-cols-2", maxCameras: 4 },
  "3x3": { grid: "grid-cols-3", maxCameras: 9 },
  "4x4": { grid: "grid-cols-4", maxCameras: 16 },
};

const CameraFeed = ({ camera, index, demoMode }: { camera: any; index: number; demoMode: boolean }) => {
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);

  // Set up stream URL when camera is available or in demo mode
  useEffect(() => {
    if (demoMode) {
      setStreamUrl(`http://localhost:8000/api/v1/stream/demo`);
    } else {
      setStreamUrl(`http://localhost:8000/api/v1/stream/${camera.id}`);
    }
  }, [camera.id, camera.status, demoMode]);

  const handleImageLoad = () => {
    setLoading(false);
    setError(false);
  };

  const handleImageError = () => {
    setError(true);
    setLoading(false);
  };

  return (
    <Card className="relative group overflow-hidden">
      <CardHeader className="absolute top-0 left-0 right-0 z-10 bg-black/60 text-white p-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-sm font-medium truncate">{camera.name}</CardTitle>
          <div className="flex items-center gap-1">
            <Badge variant={camera.status === 'online' ? 'default' : 'destructive'} className="text-xs">
              {camera.status}
            </Badge>
          </div>
        </div>
        <p className="text-xs text-gray-300 truncate">{camera.location}</p>
      </CardHeader>
      
      <CardContent className="p-0 aspect-video bg-black relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-muted">
            <Skeleton className="w-full h-full" />
          </div>
        )}
        
        {streamUrl ? (
          <img
            src={streamUrl}
            alt={`Camera ${camera.name}`}
            className="w-full h-full object-contain bg-black"
            onLoad={handleImageLoad}
            onError={handleImageError}
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900 text-white">
            <AlertTriangle className="h-8 w-8 text-red-500 mb-2" />
            <p className="text-sm">No Stream URL</p>
            <p className="text-xs text-gray-400 truncate px-2">
              {camera.rtsp_url}
            </p>
          </div>
        )}
        
        {/* Error overlay - shows on top of image when there's an error */}
        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900 bg-opacity-90 text-white">
            <AlertTriangle className="h-8 w-8 text-red-500 mb-2" />
            <p className="text-sm">Stream Error</p>
            <p className="text-xs text-gray-400 truncate px-2">
              Failed to connect to camera
            </p>
            <p className="text-xs text-yellow-400 mt-1">Check camera network connectivity</p>
          </div>
        )}
        
        {/* Control overlay - shows on hover */}
        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" className="h-8 w-8 p-0">
              <Maximize2 className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="secondary" className="h-8 w-8 p-0">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const LiveFeed = () => {
  const [layout, setLayout] = useState<LayoutType>("2x2");
  const [demoMode, setDemoMode] = useState(false);
  const { data: cameras, isLoading, error } = useCameras();

  const currentConfig = layoutConfigs[layout];
  const displayCameras = cameras?.slice(0, currentConfig.maxCameras) || [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="aspect-video" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to load cameras. Please check your connection and try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Live Camera Feed</h1>
          <p className="text-muted-foreground">
            Monitor live feeds from {cameras?.length || 0} cameras
          </p>
        </div>

        {/* Layout Controls */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Layout:</span>
          {Object.entries(layoutConfigs).map(([key, config]) => (
            <Button
              key={key}
              variant={layout === key ? "default" : "outline"}
              size="sm"
              onClick={() => setLayout(key as LayoutType)}
              className="h-8 w-12"
            >
              {key === "1x1" && <Monitor className="h-4 w-4" />}
              {key === "2x2" && <Grid2X2 className="h-4 w-4" />}
              {key === "3x3" && <Grid3X3 className="h-4 w-4" />}
              {key === "4x4" && <Grid3X3 className="h-4 w-4" />}
            </Button>
          ))}
          <Button
            variant={demoMode ? "default" : "outline"}
            size="sm"
            onClick={() => setDemoMode((v) => !v)}
            className="h-8"
          >
            {demoMode ? 'Demo On' : 'Demo Off'}
          </Button>
        </div>
      </div>

      {/* Camera Grid */}
      {displayCameras.length > 0 ? (
        <div className={`grid ${currentConfig.grid} gap-4`}>
          {displayCameras.map((camera, index) => (
            <CameraFeed key={camera.id} camera={camera} index={index} demoMode={demoMode} />
          ))}
          
          {/* Empty slots */}
          {Array.from({ 
            length: Math.max(0, currentConfig.maxCameras - displayCameras.length) 
          }).map((_, index) => (
            <Card key={`empty-${index}`} className="aspect-video">
              <CardContent className="p-0 h-full flex items-center justify-center bg-muted">
                <div className="text-center text-muted-foreground">
                  <Monitor className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No Camera</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Alert>
          <Monitor className="h-4 w-4" />
          <AlertDescription>
            No cameras found. Please add cameras in the Assets section to view live feeds.
          </AlertDescription>
        </Alert>
      )}

      {/* Info Alert */}
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          <strong>Note:</strong> This live preview uses a simple MJPEG stream. For production-grade low-latency streaming, consider WebRTC/HLS via a media server (e.g., MediaMTX) and a player on the frontend.
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default LiveFeed;