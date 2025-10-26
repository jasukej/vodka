# Tests

## Hit Mapping Test

Tests the segmentation store and hit localization integration.

### Run Test

```bash
cd backend
source venv/bin/activate
python test/test_hit_mapping.py
```

### What It Does

1. Runs calibration to detect objects (uses mock segments if YOLO unavailable)
2. Stores segments in memory
3. Waits 10 seconds
4. Generates 5 random hit coordinates
5. Maps each coordinate to detected objects
6. Logs what object was hit and the drum pad assignment

### Expected Output

```
======================================================================
  HIT MAPPING TEST
======================================================================

DETECTED OBJECTS
  #0: PERSON
       Position: (100, 100)
       Size: 200x150
       Confidence: 85.00%
  ...

Waiting 10 seconds...

🎯 HIT DETECTED!
   Coordinates: (150, 175)
   Mapped to: SNARE
   Object: PERSON
   Confidence: 95.00%
```

### Purpose

Verifies that:
- Segmentation store correctly saves and retrieves segments
- Hit localizer successfully maps coordinates to segmented objects
- Object class names are properly associated with hits
- The end-to-end flow from calibration → storage → hit detection works

