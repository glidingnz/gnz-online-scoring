# Implementation Plan - Complete

## Completed Phases

### Phase 1: Project Setup
- [x] config.yaml removed (dates now passed via CLI args)
- [x] app/ folder with source code
- [x] Build system with PyInstaller

### Phase 2: Core Infrastructure
- [x] Config loading (in-memory, no config file needed)
- [x] API client with Chrome user-agent
- [x] Direct HTTP requests
- [x] Airport coordinate fetching from WeGlide API

### Phase 3: Data Extraction
- [x] Filter by country (NZ)
- [x] Filter by date range
- [x] Paginated fetching

### Phase 4: Island Detection
- [x] Polygon-based detection (convex polygons)
- [x] Uses actual airport coordinates (not bbox)
- [x] Unmapped flights logged

### Phase 5: Output
- [x] CSV: pilot_id, name, Flight 1-5, total
- [x] CSV (valid only, separate file)
- [x] JSON: grouped by pilot with flight details + season dates
- [x] log.txt with run summary

### Phase 6: Build System
- [x] PyInstaller build script
- [x] Single executable in release/
- [x] Version in filename (v0.2.0)

### Phase 7: GUI
- [x] Tkinter GUI viewer
- [x] Pilot list sorted by total points
- [x] Island dropdown (north/south)
- [x] Date selectors with validation
- [x] OSM maps with flight locations
- [x] Preloaded maps
- [x] Scrollable flight details
- [x] Real-time output during download
- [x] Flight validity (rank -> valid)
- [x] Filter invalid flights checkbox
- [x] Yellow row for invalid pilots
- [x] ->pts<- markers for invalid flights

## Build

```bash
python build.py
# Output: release/gnz-online-scoring-v0.2.0.exe
```