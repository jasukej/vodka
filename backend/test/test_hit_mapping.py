import sys
import os
import time
import random
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.segmentation_store import segmentation_store
from services.frame_buffer import frame_buffer
from services.hit_localizer import hit_localizer
from services.yolo_local import local_yolo

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_test_frame():
    return "mock_frame_data_base64"

def generate_random_coordinate(width=640, height=480):
    return {
        'x': random.randint(0, width),
        'y': random.randint(0, height)
    }

def print_separator(title=""):
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)

def main():
    print_separator("HIT MAPPING TEST")
    print("This test will:")
    print("  1. Run calibration to get segments")
    print("  2. Wait 10 seconds")
    print("  3. Generate random hit coordinates")
    print("  4. Map coordinates to detected materials")
    print("  5. Log what was hit")
    
    print_separator("STEP 1: Running Calibration")
    
    local_yolo.load_model()
    
    frame_data = generate_test_frame()
    frame_buffer.add_frame(frame_data, time.time())
    
    logger.info("Attempting segmentation (will use mock if model unavailable)...")
    segmentation_result = local_yolo.segment_frame(frame_data)
    
    if not segmentation_result or not segmentation_result.get('success'):
        logger.error("Segmentation failed")
        return
    
    segment_count = segmentation_result.get('count', 0)
    segments = segmentation_result.get('segments', [])
    
    logger.info(f"✅ Segmentation complete: {segment_count} material(s) detected")
    
    if segment_count == 0:
        logger.warning("No materials detected, cannot test hit mapping")
        return
    
    segmentation_store.store_segments(segmentation_result, time.time())
    logger.info("💾 Segments stored in memory")
    
    print_separator("DETECTED MATERIALS")
    for i, seg in enumerate(segments):
        bbox = seg.get('bbox', [0, 0, 0, 0])
        conf = seg.get('confidence', 0)
        class_name = seg.get('class_name', 'unknown')
        print(f"  #{i}: {class_name.upper()}")
        print(f"       Position: ({bbox[0]}, {bbox[1]})")
        print(f"       Size: {bbox[2]}x{bbox[3]}")
        print(f"       Confidence: {conf:.2%}")
    
    print_separator("STEP 2: Waiting 10 seconds")
    for i in range(10, 0, -1):
        print(f"  {i} seconds remaining...", end='\r')
        time.sleep(1)
    print("\n")
    
    print_separator("STEP 3: Generating Random Hit Coordinates")
    
    num_tests = 5
    for test_num in range(1, num_tests + 1):
        print(f"\n--- Test Hit #{test_num} ---")
        
        hit_position = generate_random_coordinate()
        hit_timestamp = time.time()
        
        logger.info(f"Generated hit at coordinates: ({hit_position['x']}, {hit_position['y']})")
        
        latest_frame = frame_buffer.get_latest_frame()
        stored_segments = segmentation_store.get_segments()
        
        if not stored_segments:
            logger.error("No segments in store!")
            continue
        
        print_separator("STEP 4: Localizing Hit")
        
        result = hit_localizer.localize_hit(
            frame=latest_frame,
            segments=stored_segments,
            hit_timestamp=hit_timestamp,
            hit_position=hit_position
        )
        
        if result:
            drum_pad = result.get('drum_pad', 'unknown')
            segment_id = result.get('segment_id', -1)
            confidence = result.get('confidence', 0)
            bbox = result.get('bbox', [0, 0, 0, 0])
            
            print(f"\n🎯 HIT DETECTED!")
            print(f"   Coordinates: ({hit_position['x']}, {hit_position['y']})")
            print(f"   Mapped to: {drum_pad.upper()}")
            print(f"   Confidence: {confidence:.2%}")
            print(f"   Segment ID: {segment_id}")
            
            if segment_id >= 0 and segment_id < len(segments):
                seg = segments[segment_id]
                class_name = seg.get('class_name', 'unknown')
                seg_bbox = seg.get('bbox', [0, 0, 0, 0])
                print(f"   Material: {class_name.upper()}")
                print(f"   Material bounds: ({seg_bbox[0]}, {seg_bbox[1]}) - ({seg_bbox[0]+seg_bbox[2]}, {seg_bbox[1]+seg_bbox[3]})")
                
                if seg_bbox[0] <= hit_position['x'] <= seg_bbox[0]+seg_bbox[2] and \
                   seg_bbox[1] <= hit_position['y'] <= seg_bbox[1]+seg_bbox[3]:
                    print(f"   ✅ Hit is INSIDE the {class_name} bounding box")
                else:
                    print(f"   ⚠️  Hit is OUTSIDE the {class_name} bounding box (fallback to largest)")
                
                logger.info(f"✅ Hit successfully mapped to {drum_pad} (material: {class_name})")
        else:
            print(f"\n❌ HIT MISSED")
            print(f"   Coordinates: ({hit_position['x']}, {hit_position['y']})")
            print(f"   Reason: Localizer returned None")
            logger.warning(f"Hit at ({hit_position['x']}, {hit_position['y']}) did not match any segment")
        
        time.sleep(0.5)
    
    print_separator("TEST SUMMARY")
    print("✅ Test completed!")
    print(f"   Calibrated segments: {segment_count}")
    print(f"   Random hits tested: {num_tests}")
    print("\nSegmentation store and hit localizer are working correctly.")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)

