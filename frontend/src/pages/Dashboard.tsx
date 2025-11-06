// import { Users, Car, Shield, Activity, Zap, UserCheck } from "lucide-react";
// import { StatsCard } from "@/components/dashboard/StatsCard";
// import { EventChart } from "@/components/dashboard/EventChart";
// import { DateRangePicker } from "@/components/dashboard/DateRangePicker";
// import { useDashboardStats, useCameras } from "@/hooks/useDetectionData";

// const Dashboard = () => {
//   const { data: stats, isLoading: statsLoading } = useDashboardStats();
//   const { data: cameras } = useCameras();

//   if (statsLoading) {
//     return (
//       <div className="space-y-6">
//         <div className="flex items-center justify-between">
//           <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
//           <DateRangePicker />
//         </div>
//         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
//           {[...Array(6)].map((_, i) => (
//             <div key={i} className="h-32 bg-card animate-pulse rounded-lg" />
//           ))}
//         </div>
//       </div>
//     );
//   }

//   return (
//     <div className="space-y-6">
//       <div className="flex items-center justify-between">
//         <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
//         <DateRangePicker />
//       </div>

//       {/* Stats Grid */}
//       <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
//         <StatsCard
//           title="Total Events"
//           value={stats?.total_events || 0}
//           icon={Activity}
//           trend={{ value: stats?.events_trend || 0, label: "from yesterday" }}
//         />
//         <StatsCard
//           title="Active Devices"
//           value={stats?.active_devices || 0}
//           icon={Shield}
//           status="active"
//           trend={{ value: stats?.devices_trend || 0, label: "this week" }}
//         />
//         <StatsCard
//           title="Inactive Devices"
//           value={stats?.inactive_devices || 0}
//           icon={Shield}
//           status="inactive"
//         />
//         <StatsCard
//           title="Online Devices"
//           value={stats?.online_devices || 0}
//           icon={Zap}
//           status="online"
//         />
//         <StatsCard
//           title="Offline Devices"
//           value={stats?.offline_devices || 0}
//           icon={Zap}
//           status="offline"
//         />
//         <StatsCard
//           title="People Detected"
//           value={stats?.people_detected || 0}
//           icon={Users}
//           trend={{ value: stats?.people_trend || 0, label: "from yesterday" }}
//         />
//       </div>

//       {/* Charts Section */}
//       <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
//         <div className="lg:col-span-2">
//           <EventChart />
//         </div>
//         <div className="space-y-6">
//           <StatsCard
//             title="Vehicle Count"
//             value="456"
//             icon={Car}
//             trend={{ value: 15.2, label: "from last hour" }}
//             className="h-fit"
//           />
//           <StatsCard
//             title="Attendance Rate"
//             value="94.2%"
//             icon={UserCheck}
//             trend={{ value: 1.8, label: "from yesterday" }}
//             className="h-fit"
//           />
//         </div>
//       </div>
//     </div>
//   );
// };

// export default Dashboard;

import { Users, Car, Shield, Activity, Zap, UserCheck } from "lucide-react";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { EventChart } from "@/components/dashboard/EventChart";
import { DateRangePicker } from "@/components/dashboard/DateRangePicker";
import { useDashboardStats, useCameras } from "@/hooks/useDetectionData";
import { useRealtimeDetections } from "@/hooks/useRealtimeDetections";

const Dashboard = () => {
  // Enable real-time updates
  useRealtimeDetections();
  
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: cameras } = useCameras();

  if (statsLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <DateRangePicker />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-32 bg-card animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
        <DateRangePicker />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
        <StatsCard
          title="Total Events"
          value={stats?.total_events || 0}
          icon={Activity}
          trend={{ value: stats?.events_trend || 0, label: "from yesterday" }}
        />
        <StatsCard
          title="Total Cameras"
          value={stats?.total_cameras || 0}
          icon={Shield}
          trend={{ value: stats?.devices_trend || 0, label: "this week" }}
        />
        <StatsCard
          title="Online Cameras"
          value={stats?.online_cameras || 0}
          icon={Zap}
          status="online"
        />
        <StatsCard
          title="Offline Cameras"
          value={stats?.offline_cameras || 0}
          icon={Zap}
          status="offline"
        />
        <StatsCard
          title="Active Cameras"
          value={stats?.active_cameras || 0}
          icon={Shield}
          status="active"
        />
        <StatsCard
          title="People Detected"
          value={stats?.people_detected || 0}
          icon={Users}
          trend={{ value: stats?.people_trend || 0, label: "from yesterday" }}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <EventChart />
        </div>
        <div className="space-y-6">
          <StatsCard
            title="Vehicle Count"
            value="456"
            icon={Car}
            trend={{ value: 15.2, label: "from last hour" }}
            className="h-fit"
          />
          <StatsCard
            title="Attendance Rate"
            value="94.2%"
            icon={UserCheck}
            trend={{ value: 1.8, label: "from yesterday" }}
            className="h-fit"
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;