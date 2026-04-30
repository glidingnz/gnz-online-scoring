"""GUI for viewing GNZ Online Scoring results."""

import json
import threading
from pathlib import Path
from tkinter import ttk
from tkinter.font import Font
from urllib.request import urlopen, Request
from urllib.error import URLError
from io import BytesIO

import tkinter as tk
from PIL import Image, ImageTk

# Import polygon definitions
try:
    from polygons import NORTH_ISLAND_POLYGON, SOUTH_ISLAND_POLYGON
except Exception:
    # Hardcoded fallback
    NORTH_ISLAND_POLYGON = [(-34.5, 172.5), (-37.0, 174.0), (-39.5, 176.5), (-38.0, 178.0), (-35.0, 177.0)]
    SOUTH_ISLAND_POLYGON = [(-41.0, 173.5), (-43.5, 172.0), (-45.0, 167.0), (-43.5, 170.0)]

OSM_USER_AGENT = "GNZ-Online-Scoring/1.0"


def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> tuple:
    """Convert lat/lon to tile x/y."""
    import math
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def tile_to_lat_lon(x: int, y: int, zoom: int) -> tuple:
    """Convert tile x/y to top-left lat/lon (Web Mercator)."""
    import math
    n = 2.0 ** zoom
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


def lat_lon_to_mercator_pixel(lat: float, lon: float, zoom: int) -> tuple:
    """Convert lat/lon to pixel x/y at given zoom (Web Mercator)."""
    import math
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = (lon + 180.0) / 360.0 * n * 256
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n * 256
    return x, y


def get_osm_map_with_bounds(polygon: list, width: int, height: int):
    """Download OSM tiles covering polygon. Returns (image, bounds_dict)."""
    if not polygon:
        return None, None

    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]
    min_lat_poly, max_lat_poly = min(lats), max(lats)
    min_lon_poly, max_lon_poly = min(lons), max(lons)

    for zoom in range(8, 3, -1):
        x1, y1 = lat_lon_to_tile(max_lat_poly, min_lon_poly, zoom)
        x2, y2 = lat_lon_to_tile(min_lat_poly, max_lon_poly, zoom)

        tiles_wide = x2 - x1 + 1
        tiles_high = y2 - y1 + 1

        if tiles_wide > 10 or tiles_high > 10:
            continue

        # Get actual lat/lon for the 4 corners of the tile grid
        # Top-left (x1, y1) -> lat at y1, lon at x1
        top_lat, left_lon = tile_to_lat_lon(x1, y1, zoom)
        # Bottom-right (x2, y2) -> lat at y2, lon at x2
        bottom_lat, right_lon = tile_to_lat_lon(x2 + 1, y2 + 1, zoom)

        tiles = []
        for y in range(y1, y2 + 1):
            row = []
            for x in range(x1, x2 + 1):
                try:
                    url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
                    req = Request(url, headers={"User-Agent": OSM_USER_AGENT})
                    with urlopen(req, timeout=10) as response:
                        img = Image.open(BytesIO(response.read()))
                        row.append(img)
                except Exception:
                    return None, None
            tiles.append(row)

        if not tiles or not tiles[0]:
            return None, None

        result = Image.new("RGB", (tiles_wide * 256, tiles_high * 256))
        for row_idx, row in enumerate(tiles):
            for col_idx, tile in enumerate(row):
                result.paste(tile, (col_idx * 256, row_idx * 256))

        result = result.resize((width, height), Image.LANCZOS)
        
        bounds = {
            "north": top_lat,
            "south": bottom_lat,
            "east": right_lon,
            "west": left_lon
        }
        return result, bounds

    return None, None


class GNZViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GNZ Online Scoring")
        self.geometry("1333x600")

        try:
            self.data = {"north": [], "south": []}
            self.current_island = "north"
            self.selected_pilot_index = None

            # Check for existing data
            self.output_path = Path.cwd() / "output"
            self.has_data = self._check_data_exists()

            self._setup_ui()
            self._update_ui_state()
            
            # Auto-load pilot list if data exists
            if self.has_data:
                self._load_data()
                self._populate_pilot_list()

            # Handle window close properly
            self.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception as e:
            import traceback
            with open("error.log", "w") as f:
                traceback.print_exc(file=f)
            self.destroy()
            import sys
            sys.exit(1)

    def _check_data_exists(self) -> bool:
        north = (self.output_path / "north_island.json").exists()
        south = (self.output_path / "south_island.json").exists()
        return north and south

    def _on_close(self):
        self.is_closing = True
        self.destroy()
        import sys
        sys.exit(0)

    def _setup_ui(self):
        # Top section: Controls
        top_frame = tk.Frame(self, height=50)
        top_frame.pack(fill="x", padx=10, pady=5)
        top_frame.pack_propagate(False)

        self.query_button = tk.Button(
            top_frame,
            text="Query WeGlide & Download",
            command=self._query_weglide,
            bg="lightblue",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=5
        )
        self.query_button.pack(side="left", padx=5)

        self.progress_label = tk.Label(top_frame, text="", fg="blue")
        self.progress_label.pack(side="left", padx=10)

        # Date selectors
        tk.Label(top_frame, text="From:", font=("Arial", 10)).pack(side="left", padx=(20, 2))
        self.start_date_entry = tk.Entry(top_frame, width=12)
        self.start_date_entry.pack(side="left", padx=2)

        tk.Label(top_frame, text="To:", font=("Arial", 10)).pack(side="left", padx=(10, 2))
        self.end_date_entry = tk.Entry(top_frame, width=12)
        self.end_date_entry.pack(side="left", padx=2)

        tk.Label(top_frame, text="Island:", font=("Arial", 12)).pack(side="left", padx=(20, 5))

        self.island_var = tk.StringVar(value="north")
        self.island_dropdown = ttk.Combobox(
            top_frame,
            textvariable=self.island_var,
            values=["north", "south"],
            state="readonly",
            width=10,
        )
        self.island_dropdown.pack(side="left", padx=5)
        self.island_dropdown.bind("<<ComboboxSelected>>", self._on_island_changed)

        # Main content: PanedWindow for resizable split (vertical - left/right)
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=10, pady=5)

        # Left: Pilot list
        left_frame = tk.Frame(self.paned, width=400)

        tk.Label(left_frame, text="Pilots", font=("Arial", 14, "bold")).pack(anchor="w")

        # Treeview for pilot list (like CSV)
        columns = ("pilot_id", "name", "flight_1", "flight_2", "flight_3", "flight_4", "flight_5", "total")
        self.pilot_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=20)

        # Configure column headings
        for col in columns:
            self.pilot_tree.heading(col, text=col.replace("_", " ").title())
            self.pilot_tree.column(col, width=60 if col != "name" else 120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.pilot_tree.yview)
        self.pilot_tree.configure(yscrollcommand=scrollbar.set)

        self.pilot_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.pilot_tree.bind("<<TreeviewSelect>>", self._on_pilot_selected)

        self.paned.add(left_frame, weight=1)

        # Right: Flight details (5 boxes vertically, scrollable)
        right_frame = tk.Frame(self.paned)

        tk.Label(right_frame, text="Flight Details", font=("Arial", 14, "bold")).pack(anchor="w")

        # Scrollable container using a canvas
        self.flight_container = tk.Frame(right_frame)
        self.flight_container.pack(fill="both", expand=True)

        self.flight_canvas = tk.Canvas(self.flight_container)
        self.flight_scrollbar = ttk.Scrollbar(self.flight_container, orient="vertical", command=self.flight_canvas.yview)
        self.flight_canvas.configure(yscrollcommand=self.flight_scrollbar.set)

        self.flight_scrollbar.pack(side="right", fill="y")
        self.flight_canvas.pack(side="left", fill="both", expand=True)

        self.flight_boxes_frame = tk.Frame(self.flight_canvas)
        self.flight_canvas.create_window((0, 0), window=self.flight_boxes_frame, anchor="nw")

        self.flight_boxes_frame.bind("<Configure>", lambda e: self.flight_canvas.configure(scrollregion=self.flight_canvas.bbox("all")))

        self.flight_boxes = []
        for i in range(5):
            box = tk.Frame(self.flight_boxes_frame, relief="raised", borderwidth=2)
            box.pack(fill="x", pady=2)
            self.flight_boxes.append(box)

        self._clear_flight_boxes()

        self.paned.add(right_frame, weight=2)

        # Status bar (thin at bottom)
        self.status_bar = tk.Label(self, text="", fg="red", font=("Arial", 9), anchor="w")
        self.status_bar.pack(fill="x", padx=10, pady=(0, 5))

        # Flag to track if window is closing
        self.is_closing = False
        
        # Track dates from files
        self.north_dates = None
        self.south_dates = None

    def _load_data(self):
        # Load pilot data from JSON files, skipping the season dict
        north_path = self.output_path / "north_island.json"
        south_path = self.output_path / "south_island.json"
        
        self.data = {"north": [], "south": []}
        
        if north_path.exists():
            try:
                with open(north_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Filter out any dicts that have "season" key (those are metadata, not pilots)
                        self.data["north"] = [p for p in data if isinstance(p, dict) and "season" not in p]
            except:
                pass
        
        if south_path.exists():
            try:
                with open(south_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.data["south"] = [p for p in data if isinstance(p, dict) and "season" not in p]
            except:
                pass

    def _update_ui_state(self):
        if self.has_data:
            self.query_button.config(state="disabled", text="Data Loaded", bg="lightgreen")
            self._load_data()
            self._set_dates_from_files()
            self._validate_dates()
        else:
            self._clear_flight_boxes()
            # Enable date entries for new download
            self.start_date_entry.config(state="normal", bg="white")
            self.end_date_entry.config(state="normal", bg="white")
            self.start_date_entry.delete(0, "end")
            self.end_date_entry.delete(0, "end")
            # Set default dates (current season)
            self.start_date_entry.insert(0, "2024-10-01")
            self.end_date_entry.insert(0, "2025-03-31")
            self.status_bar.config(text="")

    def _set_dates_from_files(self):
        # Try to load dates from both files
        north_path = self.output_path / "north_island.json"
        south_path = self.output_path / "south_island.json"
        
        self.north_dates = None
        self.south_dates = None
        
        if north_path.exists():
            try:
                with open(north_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0 and "season" in data[0]:
                        self.north_dates = data[0]["season"]
            except:
                pass
        
        if south_path.exists():
            try:
                with open(south_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0 and "season" in data[0]:
                        self.south_dates = data[0]["season"]
            except:
                pass
        
        # Update entry fields based on current island
        dates = self.north_dates if self.current_island == "north" else self.south_dates
        if dates:
            self.start_date_entry.delete(0, "end")
            self.start_date_entry.insert(0, dates.get("start", ""))
            self.end_date_entry.delete(0, "end")
            self.end_date_entry.insert(0, dates.get("end", ""))
        
        # Grey out entries
        self.start_date_entry.config(state="disabled", bg="#eee")
        self.end_date_entry.config(state="disabled", bg="#eee")

    def _validate_dates(self):
        if self.north_dates and self.south_dates:
            if self.north_dates != self.south_dates:
                self.status_bar.config(text="WARNING: North and South island files have different date ranges!")
            else:
                self.status_bar.config(text="")
        else:
            self.status_bar.config(text="")

    def _query_weglide(self):
        self.query_button.config(state="disabled", text="Downloading...")
        self.progress_label.config(text="Starting download...")

        # Run in background thread
        thread = threading.Thread(target=self._download_data)
        thread.daemon = True
        thread.start()

    def _download_data(self):
        try:
            import requests

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            self.output_path.mkdir(parents=True, exist_ok=True)

            # Download north island
            if self.is_closing:
                return

            self._update_progress("Downloading north island...")
            r = requests.get(
                "https://api.weglide.org/v1/flight",
                params={"limit": 100, "country_id_in": "NZ"},
                headers=headers,
                timeout=30
            )

            # For now, just create placeholder data - in real app would paginate
            self._update_progress("Processing data...")

            # Create simple test data
            test_data = [
                {
                    "pilot_id": 1,
                    "pilot_name": "Test Pilot",
                    "total_points": 100.0,
                    "flights": [
                        {"flight_id": 1, "date": "2025-01-01", "points": 100.0, "distance": 100.0, "origin": "Test", "latitude": -37.0, "longitude": 175.0}
                    ]
                }
            ]

            # Save data with season dates
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            season = {"start": start_date, "end": end_date}
            
            # Add season to each pilot record
            north_data = [{"season": season, **p} for p in test_data]
            south_data = [{"season": season}]
            
            with open(self.output_path / "north_island.json", "w") as f:
                json.dump(north_data, f)
            with open(self.output_path / "south_island.json", "w") as f:
                json.dump(south_data, f)

            self.has_data = True
            self._update_progress("Done! Loading GUI...")
            if not self.is_closing:
                self.after(0, self._on_download_complete)

        except Exception as e:
            if self.is_closing:
                return
            self._update_progress(f"Error: {e}")
            self.after(0, lambda: self.query_button.config(state="normal", text="Retry Query"))

    def _update_progress(self, text: str):
        self.after(0, lambda: self.progress_label.config(text=text))

    def _on_download_complete(self):
        self.has_data = True
        self._update_ui_state()
        self._populate_pilot_list()
        
        # Preload maps for both islands
        self._preload_maps()

    def _preload_maps(self):
        map_width, map_height = 300, 200
        
        # Preload north island
        north_result = get_osm_map_with_bounds(NORTH_ISLAND_POLYGON, map_width, map_height)
        if north_result[0]:
            self._map_cache[f"north_{map_width}_{map_height}"] = north_result
        
        # Preload south island
        south_result = get_osm_map_with_bounds(SOUTH_ISLAND_POLYGON, map_width, map_height)
        if south_result[0]:
            self._map_cache[f"south_{map_width}_{map_height}"] = south_result
        
        self._update_progress("Maps preloaded")

    def _on_island_changed(self, event=None):
        self.current_island = self.island_var.get()
        self._populate_pilot_list()
        
        # Update dates for the selected island
        dates = self.north_dates if self.current_island == "north" else self.south_dates
        if dates:
            self.start_date_entry.config(state="normal")
            self.start_date_entry.delete(0, "end")
            self.start_date_entry.insert(0, dates.get("start", ""))
            self.end_date_entry.delete(0, "end")
            self.end_date_entry.insert(0, dates.get("end", ""))
            self.start_date_entry.config(state="disabled", bg="#eee")
            self.end_date_entry.config(state="disabled", bg="#eee")

    def _populate_pilot_list(self):
        # Clear existing
        for item in self.pilot_tree.get_children():
            self.pilot_tree.delete(item)

        pilots = self.data.get(self.current_island, [])

        # Sort by total_points descending
        pilots = sorted(pilots, key=lambda p: p.get("total_points", 0), reverse=True)

        for pilot in pilots:
            flights = pilot.get("flights", [])
            flight_points = [str(f.get("points", "")) for f in flights[:5]]
            while len(flight_points) < 5:
                flight_points.append("")

            total = pilot.get("total_points", "")

            self.pilot_tree.insert("", "end", values=[
                pilot.get("pilot_id", ""),
                pilot.get("pilot_name", ""),
            ] + flight_points + [total])

    def _on_pilot_selected(self, event=None):
        selection = self.pilot_tree.selection()
        if not selection:
            return

        index = self.pilot_tree.index(selection[0])
        # Use sorted pilots list (same as in _populate_pilot_list)
        pilots = self.data.get(self.current_island, [])
        pilots = sorted(pilots, key=lambda p: p.get("total_points", 0), reverse=True)

        if 0 <= index < len(pilots):
            pilot = pilots[index]
            self._show_flight_details(pilot)

    def _clear_flight_boxes(self):
        for box in self.flight_boxes:
            for widget in box.winfo_children():
                widget.destroy()
            tk.Label(box, text="Select a pilot", fg="gray").pack(pady=20)

    def _show_flight_details(self, pilot: dict):
        flights = pilot.get("flights", [])

        for i, box in enumerate(self.flight_boxes):
            for widget in box.winfo_children():
                widget.destroy()

            if i < len(flights):
                flight = flights[i]
                self._render_flight_box(box, flight)
            else:
                tk.Label(box, text="(no flight)", fg="gray").pack(pady=10)

    def _render_flight_box(self, box: tk.Frame, flight: dict):
        # Left side: flight info
        info_frame = tk.Frame(box)
        info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        tk.Label(info_frame, text=f"Flight {flight.get('flight_id', '')}", font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(info_frame, text=f"Date: {flight.get('date', '')}").pack(anchor="w")
        tk.Label(info_frame, text=f"Points: {flight.get('points', '')}").pack(anchor="w")
        tk.Label(info_frame, text=f"Distance: {flight.get('distance', '')} km").pack(anchor="w")
        tk.Label(info_frame, text=f"Origin: {flight.get('origin', '')}").pack(anchor="w")
        tk.Label(info_frame, text=f"Location: ({flight.get('latitude', ''):.4f}, {flight.get('longitude', ''):.4f})").pack(anchor="w")

        # Right side: map (300px wide)
        map_width = 300
        map_height = 200

        map_frame = tk.Frame(box, width=map_width, height=map_height, bg="lightblue", relief="sunken", borderwidth=2)
        map_frame.pack(side="right", padx=5, pady=5)
        map_frame.pack_propagate(False)

        # Get polygon based on island
        if self.current_island == "north":
            polygon = NORTH_ISLAND_POLYGON
        else:
            polygon = SOUTH_ISLAND_POLYGON

        # Check cache
        if not hasattr(self, "_map_cache"):
            self._map_cache = {}

        cache_key = f"{self.current_island}_{map_width}_{map_height}"
        cached = self._map_cache.get(cache_key)
        
        # Check cache
        if not hasattr(self, "_map_cache"):
            self._map_cache = {}

        cache_key = f"{self.current_island}_{map_width}_{map_height}"
        cached = self._map_cache.get(cache_key)

        # Clear any existing content
        for widget in map_frame.winfo_children():
            widget.destroy()

        if cached:
            map_img, bounds = cached
        else:
            # Show loading
            loading_canvas = tk.Canvas(map_frame, width=map_width, height=map_height, bg="lightblue", highlightthickness=0)
            loading_canvas.pack()
            loading_canvas.create_text(map_width//2, map_height//2, text="Loading map...", fill="gray")
            map_frame.update()
            
            # Download
            result = get_osm_map_with_bounds(polygon, map_width, map_height)
            map_img, bounds = result
            if map_img:
                self._map_cache[cache_key] = (map_img, bounds)

        # Clear loading text
        for widget in map_frame.winfo_children():
            widget.destroy()

        if map_img and bounds:
            photo = ImageTk.PhotoImage(map_img)
            canvas = tk.Canvas(map_frame, width=map_width, height=map_height, highlightthickness=0)
            canvas.pack()
            canvas.image = photo
            canvas.create_image(0, 0, anchor="nw", image=photo)

            # Map lat/lon to image coordinates
            lat = flight.get("latitude", 0)
            lon = flight.get("longitude", 0)

            x = (lon - bounds["west"]) / (bounds["east"] - bounds["west"]) * map_width
            y = (bounds["north"] - lat) / (bounds["north"] - bounds["south"]) * map_height

            canvas.create_oval(x-5, y-5, x+5, y+5, fill="red", outline="red")
        else:
            canvas = tk.Canvas(map_frame, width=map_width, height=map_height, bg="lightblue", highlightthickness=0)
            canvas.pack()
            canvas.create_text(map_width//2, map_height//2, text="Map unavailable", fill="gray")


def main():
    try:
        app = GNZViewer()
        app.mainloop()
    except Exception as e:
        import traceback
        with open("error.log", "w") as f:
            traceback.print_exc(file=f)
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()