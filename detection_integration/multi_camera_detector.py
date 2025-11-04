#!/usr/bin/env python3
import cv2
import asyncio
import logging
import threading
import queue
import time
import requests
from ultralytics import YOLO
from ultralytics.nn.tasks import DetectionModel
from torch.serialization import safe_globals
from datetime import datetime
import json
import os
os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import signal
import sys

# ==================== CONFIGURATION ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
API_KEY = os.getenv("API_KEY", "111-1111-1-11-1-11-1-1")
IMAGES_DIR = os.getenv("IMAGES_DIR", "/absolute/path/to/shared/images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# Detection parameters
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
DETECTION_WIDTH = int(os.getenv("DETECTION_WIDTH", "640"))
DETECTION_HEIGHT = int(os.getenv("DETECTION_HEIGHT", "480"))

# Performance tuning
EVENT_COOLDOWN_SECONDS = float(os.getenv("EVENT_COOLDOWN_SECONDS", "5"))
TRACK_COOLDOWN_SECONDS = float(os.getenv("TRACK_COOLDOWN_SECONDS", "30"))  # Per-track cooldown
FRAME_STRIDE = int(os.getenv("FRAME_STRIDE", "5"))
MIN_BOX_AREA = float(os.getenv("MIN_BOX_AREA", "1000"))  # Minimum bounding box area

# Camera filtering
CAMERA_IDS = os.getenv("CAMERA_IDS", "").strip()
INCLUDE_OFFLINE = os.getenv("INCLUDE_OFFLINE", "false").lower() in ("1", "true", "yes")

# OpenCV/FFmpeg optimization options
OPENCV_OPTIONS = os.getenv("OPENCV_FFMPEG_CAPTURE_OPTIONS", 
    "rtsp_transport;tcp;"
    "fflags;genpts+nobuffer;"
    "flags;low_delay;"
    "flags2;showall;"
    "vsync;0;"
    "reset_timestamps;1"
)

# ==================== METRICS & LOGGING ====================
@dataclass
class CameraMetrics:
    """Per-camera metrics tracking"""
    camera_id: str
    camera_name: str
    frames_processed: int = 0
    detections_made: int = 0
    events_logged: int = 0
    last_frame_time: float = 0.0
    connection_attempts: int = 0
    successful_connections: int = 0
    errors: int = 0
    status: str = "offline"
    
    def fps(self, window_seconds: float = 60.0) -> float:
        """Calculate approximate FPS over time window"""
        if self.frames_processed == 0:
            return 0.0
        elapsed = time.time() - (self.last_frame_time - window_seconds)
        return max(0.0, self.frames_processed / max(elapsed, 1.0))
    
    def to_dict(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "frames_processed": self.frames_processed,
            "detections_made": self.detections_made,
            "events_logged": self.events_logged,
            "fps": round(self.fps(), 2),
            "connection_attempts": self.connection_attempts,
            "successful_connections": self.successful_connections,
            "errors": self.errors,
            "status": self.status
        }

def setup_logging() -> logging.Logger:
    """Setup structured logging with camera context"""
    # Create custom formatter that includes camera context
    class CameraContextFormatter(logging.Formatter):
        def format(self, record):
            # Add camera context if available
            camera_id = getattr(record, 'camera_id', 'system')
            camera_name = getattr(record, 'camera_name', 'system')
            event_key = getattr(record, 'event_key', 'general')
            
            # Create structured message
            prefix = f"[{camera_id[:8]}:{camera_name[:12]}:{event_key}]"
            record.msg = f"{prefix} {record.msg}"
            return super().format(record)
    
    # Setup logger
    logger = logging.getLogger("multi_camera_detector")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler with structured logging
    file_handler = logging.FileHandler('multi_camera_detection.log')
    file_handler.setFormatter(CameraContextFormatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CameraContextFormatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    
    return logger

logger = setup_logging()

def log_with_context(logger_instance: logging.Logger, level: str, message: str, 
                    camera_id: str = "system", camera_name: str = "system", 
                    event_key: str = "general"):
    """Log with camera context"""
    record = logging.LogRecord(
        name=logger_instance.name, level=getattr(logging, level.upper()),
        pathname="", lineno=0, msg=message, args=(), exc_info=None
    )
    record.camera_id = camera_id
    record.camera_name = camera_name
    record.event_key = event_key
    logger_instance.handle(record)

# ==================== SHARED MODEL MANAGER ====================
class ModelManager:
    """Singleton YOLO model manager to share model across cameras"""
    _instance = None
    _model = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_model(self) -> YOLO:
        """Get or create the shared YOLO model"""
        if self._model is None:
            with self._lock:
                if self._model is None:
                    log_with_context(logger, "info", "Loading YOLO model (yolov8n.pt)", event_key="model_init")
                    with safe_globals([DetectionModel]):
                        self._model = YOLO('yolov8n.pt')
                    log_with_context(logger, "info", "YOLO model loaded successfully", event_key="model_init")
        return self._model

# ==================== ASPECT RATIO PRESERVING DETECTION ====================
def calculate_letterbox_params(src_width: int, src_height: int, 
                              target_width: int, target_height: int) -> Tuple[int, int, int, int, float]:
    """
    Calculate letterboxing parameters to preserve aspect ratio
    Returns: (new_width, new_height, pad_x, pad_y, scale)
    """
    src_ratio = src_width / src_height
    target_ratio = target_width / target_height
    
    if src_ratio > target_ratio:
        # Source is wider - fit to width
        new_width = target_width
        new_height = int(target_width / src_ratio)
        pad_x = 0
        pad_y = (target_height - new_height) // 2
    else:
        # Source is taller - fit to height
        new_height = target_height
        new_width = int(target_height * src_ratio)
        pad_x = (target_width - new_width) // 2
        pad_y = 0
    
    scale = min(target_width / src_width, target_height / src_height)
    return new_width, new_height, pad_x, pad_y, scale

def letterbox_frame(frame, target_width: int, target_height: int):
    """Apply letterboxing to preserve aspect ratio"""
    src_height, src_width = frame.shape[:2]
    new_width, new_height, pad_x, pad_y, scale = calculate_letterbox_params(
        src_width, src_height, target_width, target_height
    )
    
    # Resize frame
    resized = cv2.resize(frame, (new_width, new_height))
    
    # Create letterboxed frame
    letterboxed = cv2.copyMakeBorder(
        resized, pad_y, target_height - new_height - pad_y,
        pad_x, target_width - new_width - pad_x,
        cv2.BORDER_CONSTANT, value=(114, 114, 114)  # Gray padding
    )
    
    return letterboxed, scale, pad_x, pad_y

def unletterbox_bbox(bbox: List[float], scale: float, pad_x: int, pad_y: int) -> List[float]:
    """Convert letterboxed bbox back to original coordinates"""
    x1, y1, x2, y2 = bbox
    # Remove padding and scale back
    x1 = (x1 - pad_x) / scale
    y1 = (y1 - pad_y) / scale
    x2 = (x2 - pad_x) / scale
    y2 = (y2 - pad_y) / scale
    return [x1, y1, x2, y2]

# ==================== CAMERA DETECTOR ====================
class CameraDetector:
    """Individual camera detection handler with improved performance and tracking"""

    def __init__(self, camera_id: str, camera_name: str, rtsp_url: str):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.rtsp_url = rtsp_url
        
        # Get shared model
        self.model_manager = ModelManager()
        
        # Threading and queues
        self.frame_queue: "queue.Queue" = queue.Queue(maxsize=10)
        self.stop_event = threading.Event()
        self.is_running = False
        
        # Metrics and tracking
        self.metrics = CameraMetrics(camera_id, camera_name)
        self._frame_counter = 0
        
        # Per-track cooldown mapping: (camera_id, class_id, track_id) -> last_snapshot_time
        self._track_snapshots: Dict[Tuple[str, int, int], float] = {}
        
        # General detection cooldown (legacy)
        self._last_event_at: Dict[str, float] = {}
        
        # Letterboxing parameters for current stream
        self._letterbox_params = None

    def _get_opencv_capture_options(self) -> dict:
        """Get OpenCV capture options for optimized RTSP streaming"""
        options = {}
        if OPENCV_OPTIONS:
            pairs = OPENCV_OPTIONS.split(';')
            for i in range(0, len(pairs), 2):
                if i + 1 < len(pairs):
                    key, value = pairs[i], pairs[i + 1]
                    if key and value:
                        options[key] = value
        return options

    async def update_camera_status(self, status: str):
        """Update camera status in backend"""
        try:
            response = requests.put(
                f"{API_BASE_URL}/cameras/{self.camera_id}/status",
                json={"status": status},
                headers={"X-API-Key": API_KEY},
                timeout=5
            )
            if response.status_code == 200:
                self.metrics.status = status
                log_with_context(logger, "info", f"Status updated to {status}", 
                               self.camera_id, self.camera_name, "status_update")
            else:
                log_with_context(logger, "error", f"Failed to update status: {response.status_code}", 
                               self.camera_id, self.camera_name, "status_error")
        except Exception as e:
            self.metrics.errors += 1
            log_with_context(logger, "error", f"Error updating status: {e}", 
                           self.camera_id, self.camera_name, "status_error")

    async def log_detection_event(self, person_id: int, confidence: float, 
                                bbox: List[float], image_path: Optional[str] = None):
        """Log detection event via API"""
        try:
            event_data = {
                "camera_id": str(self.camera_id),
                "timestamp": datetime.now().isoformat(),
                "person_id": person_id,
                "confidence": confidence,
                "camera_name": self.camera_name,
                "image_path": image_path,
                "alert_sent": False,
                "metadata": {
                    "bbox": bbox,
                    "location": self.camera_name
                }
            }

            response = requests.post(
                f"{API_BASE_URL}/events",
                json=event_data,
                headers={
                    "X-API-Key": API_KEY,
                    "Content-Type": "application/json"
                },
                timeout=10
            )

            if response.status_code == 200:
                self.metrics.events_logged += 1
                log_with_context(logger, "info", f"Event logged (confidence: {confidence:.2f})", 
                               self.camera_id, self.camera_name, "event_log")
            else:
                self.metrics.errors += 1
                log_with_context(logger, "error", f"Failed to log event: {response.status_code}", 
                               self.camera_id, self.camera_name, "event_error")

        except Exception as e:
            self.metrics.errors += 1
            log_with_context(logger, "error", f"Error logging event: {e}", 
                           self.camera_id, self.camera_name, "event_error")

    def frame_grabber(self):
        """Capture frames from RTSP stream with OpenCV optimizations"""
        cap = None
        reconnect_delay = 1
        max_reconnect_delay = 30

        while not self.stop_event.is_set():
            try:
                if cap is None:
                    self.metrics.connection_attempts += 1
                    log_with_context(logger, "info", f"Connecting to {self.rtsp_url}", 
                                   self.camera_id, self.camera_name, "connection")
                    
                    cap = cv2.VideoCapture(self.rtsp_url)
                    
                    # Apply OpenCV optimizations
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_FPS, 15)
                    
                    # Apply custom FFmpeg options if available
                    options = self._get_opencv_capture_options()
                    for key, value in options.items():
                        try:
                            # Map string keys to OpenCV constants if needed
                            if hasattr(cv2, f"CAP_PROP_{key.upper()}"):
                                prop = getattr(cv2, f"CAP_PROP_{key.upper()}")
                                cap.set(prop, float(value) if value.isdigit() else value)
                        except Exception as e:
                            log_with_context(logger, "warning", f"Failed to set {key}={value}: {e}", 
                                           self.camera_id, self.camera_name, "opencv_option")

                if not cap.isOpened():
                    log_with_context(logger, "warning", f"Failed to open stream", 
                                   self.camera_id, self.camera_name, "connection_fail")
                    cap = None
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                    continue

                ret, frame = cap.read()
                if ret:
                    # Connection successful
                    if self.metrics.successful_connections == self.metrics.connection_attempts - 1:
                        self.metrics.successful_connections += 1
                        log_with_context(logger, "info", "Stream connected successfully", 
                                       self.camera_id, self.camera_name, "connection_success")
                    
                    reconnect_delay = 1
                    self.metrics.frames_processed += 1
                    self.metrics.last_frame_time = time.time()

                    # Apply letterboxing if this is the first frame or size changed
                    if self._letterbox_params is None:
                        src_height, src_width = frame.shape[:2]
                        self._letterbox_params = calculate_letterbox_params(
                            src_width, src_height, DETECTION_WIDTH, DETECTION_HEIGHT
                        )
                        log_with_context(logger, "info", 
                                       f"Frame size: {src_width}x{src_height}, letterbox params: {self._letterbox_params}", 
                                       self.camera_id, self.camera_name, "letterbox_init")

                    # Apply letterboxing
                    letterboxed_frame, scale, pad_x, pad_y = letterbox_frame(frame, DETECTION_WIDTH, DETECTION_HEIGHT)

                    # Store original frame info for bbox conversion
                    frame_info = {
                        'original_frame': frame,
                        'letterboxed_frame': letterboxed_frame,
                        'scale': scale,
                        'pad_x': pad_x,
                        'pad_y': pad_y
                    }

                    # Add to queue (non-blocking)
                    try:
                        self.frame_queue.put(frame_info, block=False)
                    except queue.Full:
                        # Remove oldest frame and add new one
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put(frame_info, block=False)
                        except queue.Empty:
                            pass
                else:
                    log_with_context(logger, "warning", "Failed to read frame", 
                                   self.camera_id, self.camera_name, "frame_fail")
                    cap.release()
                    cap = None
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)

            except Exception as e:
                self.metrics.errors += 1
                log_with_context(logger, "error", f"Frame grabber error: {e}", 
                               self.camera_id, self.camera_name, "grabber_error")
                if cap:
                    cap.release()
                    cap = None
                time.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)

        if cap:
            cap.release()
        log_with_context(logger, "info", "Frame grabber stopped", 
                       self.camera_id, self.camera_name, "grabber_stop")

    @staticmethod
    def _box_area(bbox: List[float]) -> float:
        """Calculate bounding box area"""
        if not bbox or len(bbox) < 4:
            return 0.0
        return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])

    def _should_save_track_snapshot(self, class_id: int, track_id: int) -> bool:
        """Check if we should save a snapshot for this specific track"""
        if track_id is None:
            return True  # Fallback to old behavior if no track ID
            
        track_key = (self.camera_id, class_id, track_id)
        now = time.time()
        last_snapshot = self._track_snapshots.get(track_key, 0.0)
        
        if now - last_snapshot >= TRACK_COOLDOWN_SECONDS:
            self._track_snapshots[track_key] = now
            return True
        return False

    def _detection_key(self, box) -> str:
        """Build a stable key for a detection (legacy cooldown)"""
        try:
            if box.id is not None:
                return f"id:{int(box.id)}"
        except Exception:
            pass
        # Fallback: quantize bbox
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
        return f"bb:{round(x1/10)}-{round(y1/10)}-{round(x2/10)}-{round(y2/10)}"

    def _should_emit_event(self, key: str, bbox: List[float]) -> bool:
        """Rate-limit events per key and ignore tiny boxes (legacy)"""
        if MIN_BOX_AREA > 0 and bbox and self._box_area(bbox) < MIN_BOX_AREA:
            return False
        now = time.time()
        last = self._last_event_at.get(key, 0.0)
        if now - last < EVENT_COOLDOWN_SECONDS:
            return False
        self._last_event_at[key] = now
        return True

    async def start(self):
        """Start camera detection"""
        if self.is_running:
            return

        log_with_context(logger, "info", "Starting detection", 
                       self.camera_id, self.camera_name, "start")
        self.is_running = True
        self.stop_event.clear()
        self.metrics.status = "starting"

        # Start frame grabber thread
        self.frame_grabber_thread = threading.Thread(
            target=self.frame_grabber, 
            name=f"grabber-{self.camera_id}", 
            daemon=True
        )
        self.frame_grabber_thread.start()

        # Update camera status to online
        await self.update_camera_status("online")

    async def stop(self):
        """Stop camera detection"""
        if not self.is_running:
            return

        log_with_context(logger, "info", "Stopping detection", 
                       self.camera_id, self.camera_name, "stop")
        self.is_running = False
        self.stop_event.set()

        # Wait for frame grabber thread to finish
        if hasattr(self, 'frame_grabber_thread'):
            self.frame_grabber_thread.join(timeout=5)

        # Clear queues
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

        # Update camera status to offline
        await self.update_camera_status("offline")

    async def process_detections(self):
        """Main detection processing loop with improved tracking and cooldowns"""
        model = self.model_manager.get_model()
        
        while self.is_running:
            try:
                # Get frame from queue (non-blocking)
                try:
                    frame_info = self.frame_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue

                # Optional: process every Nth frame
                self._frame_counter += 1
                if FRAME_STRIDE > 1 and (self._frame_counter % FRAME_STRIDE != 0):
                    await asyncio.sleep(0)  # yield
                    continue

                original_frame = frame_info['original_frame']
                letterboxed_frame = frame_info['letterboxed_frame']
                scale = frame_info['scale']
                pad_x = frame_info['pad_x']
                pad_y = frame_info['pad_y']

                # Run detection + tracking on letterboxed frame
                results = model.track(letterboxed_frame, persist=True, verbose=False)

                if results and results[0].boxes is not None:
                    for box in results[0].boxes:
                        # Filter for person class (class 0 in COCO dataset)
                        class_id = int(box.cls)
                        if class_id == 0 and float(box.conf) > CONFIDENCE_THRESHOLD:
                            
                            # Extract detection info
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            letterboxed_bbox = [float(x1), float(y1), float(x2), float(y2)]
                            confidence = float(box.conf)
                            track_id = int(box.id) if box.id is not None else None
                            
                            # Convert bbox back to original coordinates
                            original_bbox = unletterbox_bbox(letterboxed_bbox, scale, pad_x, pad_y)
                            
                            self.metrics.detections_made += 1
                            
                            # Check per-track cooldown first (primary method)
                            if track_id is not None:
                                should_save = self._should_save_track_snapshot(class_id, track_id)
                            else:
                                # Fallback to legacy cooldown for detections without track IDs
                                key = self._detection_key(box)
                                should_save = self._should_emit_event(key, original_bbox)
                            
                            if not should_save:
                                continue
                            
                            # Check minimum box area after coordinate conversion
                            if MIN_BOX_AREA > 0 and self._box_area(original_bbox) < MIN_BOX_AREA:
                                continue

                            # Save image crop from original frame
                            x1i, y1i, x2i, y2i = map(lambda v: max(0, int(v)), original_bbox)
                            crop = original_frame[y1i:y2i, x1i:x2i]
                            image_to_save = crop if crop.size > 0 else original_frame

                            # Generate unique filename
                            track_suffix = f"_t{track_id}" if track_id is not None else ""
                            filename = f"{self.camera_id}{track_suffix}_{int(time.time()*1000)}.jpg"
                            filepath = os.path.join(IMAGES_DIR, filename)
                            
                            try:
                                cv2.imwrite(filepath, image_to_save)
                                log_with_context(logger, "debug", f"Saved snapshot: {filename}", 
                                               self.camera_id, self.camera_name, "snapshot")
                            except Exception as e:
                                log_with_context(logger, "error", f"Failed to save image: {e}", 
                                               self.camera_id, self.camera_name, "snapshot_error")
                                filename = None

                            # Log detection event
                            person_id = track_id if track_id is not None else 0
                            await self.log_detection_event(
                                person_id=person_id,
                                confidence=confidence,
                                bbox=original_bbox,
                                image_path=filename,
                            )

                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.05)

            except Exception as e:
                self.metrics.errors += 1
                log_with_context(logger, "error", f"Detection processing error: {e}", 
                               self.camera_id, self.camera_name, "detection_error")
                await asyncio.sleep(1)

# ==================== MULTI-CAMERA MANAGER ====================
class MultiCameraManager:
    """Manages multiple camera detectors with improved monitoring and metrics"""

    def __init__(self):
        self.cameras: Dict[str, CameraDetector] = {}
        self.is_running = False
        self._shutdown_event = threading.Event()

    async def load_cameras_from_db(self):
        """Load camera configurations from database"""
        try:
            response = requests.get(f"{API_BASE_URL}/cameras", timeout=10)
            if response.status_code == 200:
                cameras_data = response.json()
                log_with_context(logger, "info", f"Loaded {len(cameras_data)} cameras from database", 
                               event_key="db_load")

                # Optional allowlist via env: CAMERA_IDS="id1,id2"
                allow_ids = None
                if CAMERA_IDS:
                    allow_ids = set([s.strip() for s in CAMERA_IDS.split(",") if s.strip()])
                    log_with_context(logger, "info", f"Filtering cameras to: {allow_ids}", 
                                   event_key="camera_filter")

                # Prefer online cameras first
                def sort_key(cam):
                    return 0 if cam.get('status') == 'online' else 1

                cameras_data.sort(key=sort_key)

                added = 0
                for camera in cameras_data:
                    camera_id = camera.get('id')
                    camera_name = camera.get('name') or camera_id
                    rtsp_url = camera.get('rtsp_url') or ""
                    status = (camera.get('status') or '').lower()

                    if allow_ids and camera_id not in allow_ids:
                        continue
                    if not rtsp_url:
                        log_with_context(logger, "warning", f"Empty RTSP URL", 
                                       camera_id, camera_name, "config_error")
                        continue
                    if not INCLUDE_OFFLINE and status == 'offline':
                        log_with_context(logger, "info", "Skipping offline camera (set INCLUDE_OFFLINE=true to include)", 
                                       camera_id, camera_name, "skip_offline")
                        continue

                    detector = CameraDetector(camera_id, camera_name, rtsp_url)
                    self.cameras[camera_id] = detector
                    added += 1
                    log_with_context(logger, "info", f"Added camera [status={status}]", 
                                   camera_id, camera_name, "camera_add")

                log_with_context(logger, "info", f"Prepared {added} cameras for detection", 
                               event_key="cameras_ready")
            else:
                log_with_context(logger, "error", f"Failed to load cameras: {response.status_code}", 
                               event_key="db_error")

        except Exception as e:
            log_with_context(logger, "error", f"Error loading cameras: {e}", event_key="db_error")

    async def start_all_cameras(self):
        """Start detection for all cameras"""
        self.is_running = True
        log_with_context(logger, "info", "Starting all camera detectors", event_key="start_all")

        # Start all camera detectors
        for camera_id, detector in self.cameras.items():
            await detector.start()

        # Start detection processing for all cameras
        tasks = []
        for camera_id, detector in self.cameras.items():
            task = asyncio.create_task(detector.process_detections())
            tasks.append(task)

        # Wait for all tasks to complete or shutdown signal
        if tasks:
            try:
                await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                log_with_context(logger, "info", "Detection tasks cancelled", event_key="cancel")

    async def stop_all_cameras(self):
        """Stop detection for all cameras"""
        self.is_running = False
        log_with_context(logger, "info", "Stopping all cameras", event_key="stop_all")

        for camera_id, detector in self.cameras.items():
            await detector.stop()

        log_with_context(logger, "info", "All cameras stopped", event_key="stop_complete")

    async def monitor_health(self):
        """Enhanced health monitoring with metrics"""
        log_with_context(logger, "info", "Starting health monitor", event_key="health_start")
        
        while self.is_running and not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                
                # Check each camera's health
                for camera_id, detector in self.cameras.items():
                    metrics = detector.metrics
                    
                    # Check if camera is receiving frames
                    time_since_frame = current_time - metrics.last_frame_time
                    
                    if time_since_frame > 30 and metrics.frames_processed > 0:  # 30 seconds timeout
                        if metrics.status != "offline":
                            log_with_context(logger, "warning", f"Camera appears offline (no frames for {time_since_frame:.1f}s)", 
                                           camera_id, detector.camera_name, "health_check")
                            await detector.update_camera_status("offline")
                    else:
                        if metrics.status != "online" and detector.is_running:
                            await detector.update_camera_status("online")
                
                # Log aggregated metrics every 60 seconds
                await asyncio.sleep(15)  # Check every 15 seconds
                
            except Exception as e:
                log_with_context(logger, "error", f"Health monitoring error: {e}", event_key="health_error")
                await asyncio.sleep(15)

    def get_metrics_summary(self) -> dict:
        """Get comprehensive metrics for all cameras"""
        summary = {
            "total_cameras": len(self.cameras),
            "online_cameras": 0,
            "offline_cameras": 0,
            "total_frames_processed": 0,
            "total_detections": 0,
            "total_events": 0,
            "total_errors": 0,
            "cameras": {}
        }
        
        for camera_id, detector in self.cameras.items():
            metrics = detector.metrics.to_dict()
            summary["cameras"][camera_id] = metrics
            
            # Aggregate totals
            if metrics["status"] == "online":
                summary["online_cameras"] += 1
            else:
                summary["offline_cameras"] += 1
                
            summary["total_frames_processed"] += metrics["frames_processed"]
            summary["total_detections"] += metrics["detections_made"]
            summary["total_events"] += metrics["events_logged"]
            summary["total_errors"] += metrics["errors"]
        
        return summary

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        log_with_context(logger, "info", f"Received signal {signum}, initiating shutdown", event_key="shutdown")
        self._shutdown_event.set()

# ==================== MAIN FUNCTION ====================
async def main():
    """Enhanced main function with better error handling and metrics"""
    log_with_context(logger, "info", "Starting Multi-Camera Detection System", event_key="startup")
    log_with_context(logger, "info", f"Configuration: API={API_BASE_URL}, Images={IMAGES_DIR}, "
                    f"Confidence={CONFIDENCE_THRESHOLD}, Resolution={DETECTION_WIDTH}x{DETECTION_HEIGHT}",
                    event_key="config")

    # Create manager
    manager = MultiCameraManager()
    
    # Setup signal handlers
    # signal.signal(signal.SIGINT, manager.handle_shutdown)
    signal.signal(signal.SIGTERM, manager.handle_shutdown)

    try:
        # Load cameras from database
        await manager.load_cameras_from_db()

        if not manager.cameras:
            log_with_context(logger, "error", "No cameras loaded. Exiting.", event_key="no_cameras")
            return

        # Start health monitoring
        health_task = asyncio.create_task(manager.monitor_health())

        # Start all cameras
        detection_task = asyncio.create_task(manager.start_all_cameras())

        # Wait for tasks to complete or shutdown signal
        done, pending = await asyncio.wait(
            [health_task, detection_task],
            return_when=asyncio.FIRST_EXCEPTION
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except KeyboardInterrupt:
        log_with_context(logger, "info", "Received keyboard interrupt", event_key="interrupt")
    except Exception as e:
        log_with_context(logger, "error", f"Unexpected error: {e}", event_key="fatal_error")
    finally:
        # Cleanup
        await manager.stop_all_cameras()
        
        # Log final metrics
        metrics = manager.get_metrics_summary()
        log_with_context(logger, "info", f"Final metrics: {metrics}", event_key="final_metrics")
        
        log_with_context(logger, "info", "Multi-Camera Detection System stopped", event_key="shutdown_complete")

if __name__ == "__main__":
    asyncio.run(main())