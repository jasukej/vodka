"""
Integration guide for enhanced accuracy improvements
Replace or modify your existing calibration handler with these enhancements
"""

# Add these imports to your app.py
from services.yolo_enhanced import enhanced_yolo
from services.material_classifier_enhanced import enhanced_material_classifier
from services.accuracy_tools import data_collector, accuracy_monitor
from enhanced_config import EnhancedConfig

# Enhanced calibration handler
@socketio.on('calibrate_frame')
def handle_calibrate_frame_enhanced(data):
    frame_data = data.get('frame')
    timestamp = data.get('timestamp')

    if not frame_data:
        logger.error('Calibrate frame called without frame data')
        emit('calibration_result', {
            'status': 'error',
            'message': 'No frame data provided',
            'timestamp': timestamp
        })
        return

    frame_size = len(frame_data)
    logger.info('=' * 70)
    logger.info(f'ENHANCED CALIBRATION STARTED (frame size: {frame_size} bytes)')
    logger.info('=' * 70)

    # Use enhanced YOLO model
    enhanced_yolo.load_model(EnhancedConfig.YOLO_MODEL_SIZE)
    segmentation_result = enhanced_yolo.segment_frame_enhanced(
        frame_data,
        conf_threshold=EnhancedConfig.YOLO_CONFIDENCE_THRESHOLD,
        iou_threshold=EnhancedConfig.YOLO_IOU_THRESHOLD
    )

    if segmentation_result and segmentation_result.get('success'):
        segment_count = segmentation_result.get('count', 0)
        segments = segmentation_result.get('segments', [])

        logger.info(f'✨ Enhanced segmentation complete: {segment_count} material(s) detected')

        if segment_count > 0:
            logger.info('📊 Enhanced detected materials:')
            for i, seg in enumerate(segments[:5]):
                bbox = seg.get('bbox', [0, 0, 0, 0])
                conf = seg.get('confidence', 0)
                cls = seg.get('class', -1)
                class_name = seg.get('class_name', 'unknown')
                area = seg.get('area', 0)
                logger.info(f'   #{i}: {class_name.upper()} - bbox=({bbox[0]:3d}, {bbox[1]:3d}, {bbox[2]:3d}, {bbox[3]:3d}), conf={conf:.3f}, area={area}')
            if len(segments) > 5:
                logger.info(f'   ... and {len(segments) - 5} more')

        segmentation_store.store_segments(segmentation_result, timestamp / 1000.0 if timestamp else None)
        logger.info(f'Segments stored in memory')

        # Use enhanced material classification
        logger.info('Starting enhanced material classification...')
        try:
            if EnhancedConfig.USE_ENSEMBLE_CLASSIFICATION:
                materials = enhanced_material_classifier.classify_segments_enhanced(frame_data, segmentation_result)
            else:
                materials = material_classifier.classify_segments(frame_data, segmentation_result)

            segmentation_store.store_materials(materials)
            logger.info(f'Enhanced material classification complete: {len(materials)} segments classified')

            # Collect training data if enabled
            if EnhancedConfig.COLLECT_TRAINING_DATA:
                sample_id = data_collector.collect_calibration_sample(
                    frame_data, segmentation_result, materials
                )
                logger.info(f'Training sample collected: {sample_id}')

        except Exception as e:
            logger.error(f'Enhanced material classification failed: {e}')
            import traceback
            traceback.print_exc()
            materials = {}

        # Prepare enhanced response with additional metadata
        enhanced_segments = []
        for seg in segments:
            seg_id = seg.get('id')
            material = materials.get(seg_id, 'unknown')

            # Get enhanced drum mapping
            class_name = seg.get('class_name', 'unknown')
            drum_mapping = _get_enhanced_drum_mapping(class_name, material)

            enhanced_seg = {
                'id': seg.get('id'),
                'bbox': seg.get('bbox'),
                'confidence': seg.get('confidence'),
                'class': seg.get('class'),
                'class_name': class_name,
                'material': material,
                'area': seg.get('area'),
                'drum_mapping': drum_mapping
            }
            enhanced_segments.append(enhanced_seg)

        emit('calibration_result', {
            'status': 'success',
            'segment_count': segment_count,
            'timestamp': timestamp,
            'message': f"Enhanced calibration with {segment_count} segments",
            'segments': enhanced_segments,
            'model_info': {
                'yolo_model': EnhancedConfig.YOLO_MODEL_SIZE,
                'clip_model': EnhancedConfig.CLIP_MODEL_SIZE,
                'ensemble_enabled': EnhancedConfig.USE_ENSEMBLE_CLASSIFICATION
            }
        })
        logger.info(f'ENHANCED CALIBRATION SUCCESS - Ready for hit detection')
        logger.info('=' * 70)
    else:
        logger.error('Enhanced segmentation failed or returned no results')
        emit('calibration_result', {
            'status': 'error',
            'message': 'Failed to segment frame with enhanced model',
            'timestamp': timestamp
        })
        logger.error('=' * 70)

def _get_enhanced_drum_mapping(class_name: str, material: str) -> str:
    """Get enhanced drum mapping based on object class and material."""
    # Try object-material combination first
    combination_key = (class_name, material)
    if combination_key in EnhancedConfig.ENHANCED_SOUND_MAPPING:
        return EnhancedConfig.ENHANCED_SOUND_MAPPING[combination_key]

    # Try with unknown object
    fallback_key = ("unknown", material)
    if fallback_key in EnhancedConfig.ENHANCED_SOUND_MAPPING:
        return EnhancedConfig.ENHANCED_SOUND_MAPPING[fallback_key]

    # Final fallback to simple material mapping
    return EnhancedConfig.MATERIAL_TO_DRUM.get(material, "snare")

# Enhanced hit localization (modify your existing simulate_hit handler)
@socketio.on('simulate_hit_enhanced')
def handle_simulate_hit_enhanced(data):
    hit_timestamp = data.get('timestamp', 0) / 1000.0
    intensity = data.get('intensity', 1.0)
    position = data.get('position')

    logger.info('🥁 ' + '=' * 68)
    logger.info(f'ENHANCED HIT DETECTED (intensity: {intensity:.2f})')
    if position:
        logger.info(f'   Position: ({position.get("x", 0)}, {position.get("y", 0)})')

    if not segmentation_store.is_calibrated():
        logger.warning('System not calibrated - cannot localize hit')
        emit('hit_localized', {
            'status': 'error',
            'message': 'System not calibrated'
        })
        logger.info('=' * 70)
        return

    latest_frame = frame_buffer.get_latest_frame()
    if not latest_frame:
        logger.warning('No frame available in buffer')
        emit('hit_localized', {
            'status': 'error',
            'message': 'No frame available'
        })
        logger.info('=' * 70)
        return

    segments = segmentation_store.get_segments()
    segment_count = len(segments.get('segments', []))
    logger.info(f'Using enhanced calibration with {segment_count} segments')

    hit_result = hit_localizer.localize_hit(
        latest_frame,
        segments,
        hit_timestamp,
        None  # Use YOLOv8nano detection
    )

    if hit_result:
        drum = hit_result['drum_pad']
        conf = hit_result['confidence']
        pos = hit_result['position']
        segment_id = hit_result.get('segment_id', -1)
        bbox = hit_result.get('bbox', [])

        segment_list = segments.get('segments', [])
        class_name = 'unknown'
        material = 'unknown'
        if segment_id >= 0 and segment_id < len(segment_list):
            class_name = segment_list[segment_id].get('class_name', 'unknown')

        # Get enhanced material classification
        material = segmentation_store.get_segment_material(segment_id) or 'unknown'

        # Get enhanced drum mapping
        enhanced_drum = _get_enhanced_drum_mapping(class_name, material)

        logger.info(f'ENHANCED HIT LOCALIZED:')
        logger.info(f'   Object: {class_name.upper()}')
        logger.info(f'   Material: {material.upper()}')
        logger.info(f'   Original Drum Pad: {drum.upper()}')
        logger.info(f'   Enhanced Drum Pad: {enhanced_drum.upper()}')
        logger.info(f'   Confidence: {conf:.3f}')
        logger.info(f'   Position: ({pos.get("x", 0):.0f}, {pos.get("y", 0):.0f})')

        # Track accuracy if monitoring enabled
        if EnhancedConfig.ENABLE_ACCURACY_MONITORING:
            accuracy_monitor.add_prediction(segment_id, material)

        # Emit enhanced hit result
        emit('hit_localized', {
            'status': 'success',
            'drum_pad': enhanced_drum,  # Use enhanced mapping
            'original_drum_pad': drum,
            'confidence': conf,
            'position': pos,
            'segment_id': segment_id,
            'class_name': class_name,
            'material': material,
            'bbox': bbox,
            'timestamp': hit_timestamp,
            'intensity': intensity,
            'source': 'manual',
            'enhanced': True
        })

        logger.info('ENHANCED HIT LOCALIZATION COMPLETE')
        logger.info('=' * 70)
    else:
        logger.error('Enhanced hit localization failed')
        emit('hit_localized', {
            'status': 'error',
            'message': 'Enhanced hit localization failed'
        })
        logger.info('=' * 70)