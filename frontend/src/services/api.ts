// Resolve API base robustly. Default to '/api/v1' when unset/invalid.
const RAW_API_BASE = (import.meta.env as any).VITE_API_BASE_URL as string | undefined;
const NORMALIZED_BASE = (() => {
  const base = (RAW_API_BASE && RAW_API_BASE.trim()) ? RAW_API_BASE.trim() : '/api/v1';
  // If base is just '/', treat as unset
  const cleaned = base === '/' ? '/api/v1' : base;
  return cleaned.endsWith('/') ? cleaned.slice(0, -1) : cleaned;
})();
const API_BASE_URL = NORMALIZED_BASE;
const API_KEY = import.meta.env.VITE_API_KEY || '';

export interface DetectionEvent {
  id: string;
  timestamp: string;
  person_id: number;
  confidence: number;
  camera_name: string;
  image_path?: string;
  alert_sent: boolean;
  metadata: {
    bbox: [number, number, number, number];
    location?: string;
  };
}

export interface CameraDevice {
  id: string;
  name: string;
  rtsp_url: string;
  status: 'online' | 'offline';
  location: string;
  last_heartbeat: string;
}

export interface DashboardStats {
  total_events: number;
  total_cameras: number;
  online_cameras: number;
  offline_cameras: number;
  active_cameras: number;
  people_detected: number;
  events_trend: number;
  devices_trend: number;
  people_trend: number;
}

export interface HourlyData {
  hour: string;
  events: number;
  footfall: number;
  vehicles: number;
}

export interface PeopleCountDevice {
  camera_id: string;
  camera_name: string;
  location: string | null;
  count: number;
  last_detection: string | null;
  image_path: string | null;
  metadata: Record<string, unknown>;
}

export interface PeopleCountResponse {
  today: number;
  week: number;
  month: number;
  year: number;
  all: number;
  devices: PeopleCountDevice[];
}

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const isWrite = options?.method && options.method !== 'GET';
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    let url = `${API_BASE_URL}${path}`;
    // Add cache-busting for GET requests to avoid stale browser disk cache
    if (!isWrite) {
      url += (url.includes('?') ? '&' : '?') + `_=${Date.now()}`;
    }
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(isWrite && API_KEY ? { 'X-API-Key': API_KEY } : {}),
        ...options?.headers,
      },
      credentials: 'include',
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Dashboard Stats
  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/events/stats');
  }

  // People Count
  async getPeopleCount(search?: string): Promise<PeopleCountResponse> {
    const params = new URLSearchParams();
    if (search) {
      params.append('search', search);
    }
    const query = params.toString();
    return this.request<PeopleCountResponse>(`/people-count${query ? `?${query}` : ''}`);
  }

  // Detection Events
  async getDetectionEvents(
    page = 1, 
    limit = 10, 
    search?: string,
    dateFilter?: string,
    confidenceFilter?: string
  ): Promise<{
    events: DetectionEvent[];
    total: number;
    page: number;
    pages: number;
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    
    if (search) {
      params.append('search', search);
    }
    
    if (dateFilter && dateFilter !== 'all') {
      params.append('date_filter', dateFilter);
    }
    
    if (confidenceFilter && confidenceFilter !== 'all') {
      params.append('confidence_filter', confidenceFilter);
    }

    return this.request(`/events?${params}`);
  }

  async getDetectionEvent(id: string): Promise<DetectionEvent> {
    return this.request<DetectionEvent>(`/events/${id}`);
  }

  async createDetectionEvent(event: Omit<DetectionEvent, 'id'>): Promise<DetectionEvent> {
    return this.request<DetectionEvent>('/events', {
      method: 'POST',
      body: JSON.stringify(event),
    });
  }

  // Camera Management
  async getCameras(): Promise<CameraDevice[]> {
    return this.request<CameraDevice[]>('/cameras');
  }

  async getCameraStatus(id: string): Promise<{ status: string; last_heartbeat: string }> {
    return this.request(`/cameras/${id}/status`);
  }

  async updateCameraStatus(id: string, status: 'online' | 'offline'): Promise<void> {
    await this.request(`/cameras/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  }

  // Analytics
  async getHourlyData(): Promise<HourlyData[]> {
    return this.request<HourlyData[]>('/analytics/hourly');
  }

  async getDailyStats(days = 7): Promise<unknown[]> {
    return this.request(`/analytics/daily?days=${days}`);
  }

  async getTrends(): Promise<{
    events_trend: number;
    devices_trend: number;
    people_trend: number;
  }> {
    return this.request('/analytics/trends');
  }

  // Alert Logs
  async getAlertLogs(page = 1, limit = 10): Promise<{
    alerts: unknown[];
    total: number;
    page: number;
    pages: number;
  }> {
    return this.request(`/alerts?page=${page}&limit=${limit}`);
  }

  async triggerManualAlert(camera_id: string, message: string): Promise<void> {
    await this.request('/alerts', {
      method: 'POST',
      body: JSON.stringify({ camera_id, message }),
    });
  }

  // AI Intelligence
  async getAIIntelligenceMetrics(): Promise<{
    detection_accuracy: number;
    processing_speed: number;
    active_models: number;
    model_performance: {
      person_detection: number;
      object_classification: number;
      behavior_analysis: number;
    };
    confidence_distribution: {
      high: number;
      medium: number;
      low: number;
    };
    camera_performance: Array<{
      camera_name: string;
      detection_count: number;
      avg_confidence: number;
      last_detection: string | null;
    }>;
    recent_activities: Array<{
      type: string;
      message: string;
      timestamp: string;
    }>;
  }> {
    return this.request('/ai-intelligence');
  }
}

export const apiService = new ApiService();

// Minimal API client for the FastAPI backend

// export interface Camera {
//   id: string;
//   name: string;
//   rtsp_url: string;
//   status: "online" | "offline";
//   location?: string | null;
//   last_heartbeat?: string | null;
//   created_at: string;
//   updated_at: string;
// }

// export interface BBox { x1: number; y1: number; x2: number; y2: number; }

// export interface Event {
//   id: string;
//   timestamp: string;
//   person_id: number;
//   confidence: number;
//   camera_id: string;
//   camera_name?: string | null;
//   image_path?: string | null;
//   alert_sent: boolean;
//   metadata: Record<string, any>;
//   bbox_x1?: number | null;
//   bbox_y1?: number | null;
//   bbox_x2?: number | null;
//   bbox_y2?: number | null;
//   created_at: string;
// }

// export interface PaginatedEvents {
//   items: Event[];
//   page: number;
//   limit: number;
//   total: number;
// }

// export interface DashboardStats {
//   today_events: number;
//   week_events: number;
//   month_events: number;
//   total_cameras: number;
//   online_cameras: number;
// }

// export interface SeriesResponse {
//   labels: string[];
//   counts: number[];
// }

// const API_BASE_URL = "http://localhost:8000/api/v1";
// const API_KEY = "111-1111-1-11-1-11-1-1";

// async function request<T>(endpoint: string, init?: RequestInit): Promise<T> {
//   const isWrite = !!init?.method && init.method !== "GET";
//   const headers: Record<string, string> = {
//     "Content-Type": "application/json",
//     ...(init?.headers as Record<string, string>),
//   };
//   if (isWrite && API_KEY) headers["X-API-Key"] = API_KEY;

//   const res = await fetch(`${API_BASE_URL}${endpoint}`, { ...init, headers });
//   if (!res.ok) {
//     const text = await res.text();
//     throw new Error(`API ${res.status}: ${text}`);
//   }
//   return res.json() as Promise<T>;
// }

// // ---- Cameras ----
// export const listCameras = (q?: string) =>
//   request<Camera[]>(`/cameras${q ? `?q=${encodeURIComponent(q)}` : ""}`);

// export const createCamera = (body: { name: string; rtsp_url: string; location?: string }) =>
//   request<Camera>(`/cameras`, { method: "POST", body: JSON.stringify(body) });

// export const updateCameraStatus = (id: string, status: "online" | "offline") =>
//   request<Camera>(`/cameras/${id}/status`, {
//     method: "PUT",
//     body: JSON.stringify({ status }),
//   });

// export const heartbeatCamera = (id: string) =>
//   request<{ ok: boolean; camera_id: string; heartbeat_at: string }>(`/cameras/${id}/heartbeat`, {
//     method: "POST",
//   });

// // ---- Events ----
// export const listEvents = (params?: {
//   page?: number; limit?: number; search?: string; camera_id?: string; since?: string; until?: string;
// }) => {
//   const p = new URLSearchParams();
//   if (params?.page) p.set("page", String(params.page));
//   if (params?.limit) p.set("limit", String(params.limit));
//   if (params?.search) p.set("search", params.search);
//   if (params?.camera_id) p.set("camera_id", params.camera_id);
//   if (params?.since) p.set("since", params.since);
//   if (params?.until) p.set("until", params.until);
//   const qs = p.toString();
//   return request<PaginatedEvents>(`/events${qs ? `?${qs}` : ""}`);
// };

// export const getEvent = (id: string) => request<Event>(`/events/${id}`);

// export const createEvent = (body: {
//   person_id: number; confidence: number; camera_id: string; camera_name?: string;
//   image_path?: string; alert_sent?: boolean; metadata?: Record<string, any>; bbox?: BBox; timestamp?: string;
// }) => request<Event>(`/events`, { method: "POST", body: JSON.stringify(body) });

// // ---- Analytics ----
// export const getDashboardStats = () => request<DashboardStats>(`/dashboard/stats`);
// export const getHourlyTrends = () => request<SeriesResponse>(`/trends/hourly`);
// export const getDailyTrends = (days = 7) => request<SeriesResponse>(`/trends/daily?days=${days}`);
