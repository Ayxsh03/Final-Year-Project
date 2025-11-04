import { Brain, TrendingUp, Users, Shield, Activity, Camera, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAIIntelligenceMetrics } from "@/hooks/useDetectionData";

const AIIntelligence = () => {
  const { data: aiMetrics, isLoading } = useAIIntelligenceMetrics();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-foreground">AI Intelligence</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="bg-gradient-card border-border/50">
              <CardContent className="p-6">
                <div className="h-8 bg-muted animate-pulse rounded mb-2" />
                <div className="h-6 bg-muted animate-pulse rounded w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">AI Intelligence</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card className="bg-gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Detection Accuracy</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{aiMetrics?.detection_accuracy || 0}%</div>
            <p className="text-xs text-muted-foreground">
              Average confidence score
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing Speed</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{aiMetrics?.processing_speed || 0}ms</div>
            <p className="text-xs text-muted-foreground">
              Average detection time
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Models</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{aiMetrics?.active_models || 0}</div>
            <p className="text-xs text-muted-foreground">
              YOLOv8 Person Detection
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-gradient-card border-border/50">
          <CardHeader>
            <CardTitle>Model Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Person Detection</span>
                <span className="text-sm text-muted-foreground">{aiMetrics?.model_performance?.person_detection || 0}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div 
                  className="bg-primary h-2 rounded-full" 
                  style={{ width: `${aiMetrics?.model_performance?.person_detection || 0}%` }}
                ></div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Object Classification</span>
                <span className="text-sm text-muted-foreground">{aiMetrics?.model_performance?.object_classification || 0}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div 
                  className="bg-primary h-2 rounded-full" 
                  style={{ width: `${aiMetrics?.model_performance?.object_classification || 0}%` }}
                ></div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Behavior Analysis</span>
                <span className="text-sm text-muted-foreground">{aiMetrics?.model_performance?.behavior_analysis || 0}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div 
                  className="bg-primary h-2 rounded-full" 
                  style={{ width: `${aiMetrics?.model_performance?.behavior_analysis || 0}%` }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-border/50">
          <CardHeader>
            <CardTitle>Recent AI Activities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {aiMetrics?.recent_activities?.map((activity, index) => (
                <div key={index} className="flex items-center space-x-3">
                  {activity.type === 'detection' && <Activity className="h-4 w-4 text-primary" />}
                  {activity.type === 'model' && <Brain className="h-4 w-4 text-primary" />}
                  {activity.type === 'performance' && <TrendingUp className="h-4 w-4 text-primary" />}
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium capitalize">{activity.type}</p>
                    <p className="text-xs text-muted-foreground">{activity.message}</p>
                  </div>
                  <span className="text-xs text-muted-foreground">{activity.timestamp}</span>
                </div>
              )) || (
                <div className="text-center text-muted-foreground py-4">
                  No recent activities
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Camera Performance Section */}
      {aiMetrics?.camera_performance && aiMetrics.camera_performance.length > 0 && (
        <Card className="bg-gradient-card border-border/50">
          <CardHeader>
            <CardTitle>Camera Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {aiMetrics.camera_performance.map((camera, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Camera className="h-4 w-4 text-primary" />
                    <div>
                      <p className="text-sm font-medium">{camera.camera_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {camera.detection_count} detections
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{camera.avg_confidence}%</p>
                    <p className="text-xs text-muted-foreground">avg confidence</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Confidence Distribution */}
      {aiMetrics?.confidence_distribution && (
        <Card className="bg-gradient-card border-border/50">
          <CardHeader>
            <CardTitle>Confidence Distribution (Last 24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{aiMetrics.confidence_distribution.high}</div>
                <div className="text-xs text-muted-foreground">High (≥80%)</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{aiMetrics.confidence_distribution.medium}</div>
                <div className="text-xs text-muted-foreground">Medium (60-79%)</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{aiMetrics.confidence_distribution.low}</div>
                <div className="text-xs text-muted-foreground">Low (&lt;60%)</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AIIntelligence;