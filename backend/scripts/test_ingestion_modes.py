#!/usr/bin/env python3
"""Test script to compare Simple and Parallel ingestion modes."""

import argparse
import logging
import time
from pathlib import Path
import json
import sys

from bridgewell_gpt.di import global_injector
from bridgewell_gpt.server.ingest.ingest_service import IngestService
from bridgewell_gpt.settings.settings import Settings
from bridgewell_gpt.server.document_types.document_type_service import DocumentTypeService
from bridgewell_gpt.paths import local_data_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_ingestion_mode(file_path: Path, mode: str, wait_time: int = 30) -> dict:
    """Test ingestion with specified mode and return results."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {mode.upper()} mode ingestion")
    logger.info(f"{'='*60}")
    
    # Update settings to use specified mode
    settings = global_injector.get(Settings)
    original_mode = settings.embedding.ingest_mode
    settings.embedding.ingest_mode = mode
    
    # Re-create ingest service with new settings
    ingest_service = global_injector.get(IngestService)
    doc_type_service = global_injector.get(DocumentTypeService)
    
    start_time = time.time()
    
    try:
        # Ingest the file
        logger.info(f"Starting ingestion of {file_path.name}")
        docs = ingest_service.ingest_file(file_path.name, file_path)
        
        if not docs:
            logger.error("No documents returned from ingestion")
            return {"error": "No documents returned"}
        
        doc_id = docs[0].doc_id
        logger.info(f"Document ID: {doc_id}")
        
        # Wait for processing to complete
        logger.info(f"Waiting up to {wait_time} seconds for processing to complete...")
        for i in range(wait_time):
            phase = doc_type_service.get_document_phase(doc_id)
            logger.info(f"[{i+1}s] Current phase: {phase}")
            
            if phase in ["completed", "error"]:
                break
            
            time.sleep(1)
        
        # Get final results
        final_phase = doc_type_service.get_document_phase(doc_id)
        elapsed_time = time.time() - start_time
        
        # Check for extraction results
        extraction_result_path = local_data_path / "extraction_results" / doc_id / "result.json"
        extraction_data = None
        if extraction_result_path.exists():
            with open(extraction_result_path) as f:
                extraction_data = json.load(f)
        
        result = {
            "mode": mode,
            "doc_id": doc_id,
            "final_phase": final_phase,
            "elapsed_time": elapsed_time,
            "extraction_exists": extraction_result_path.exists(),
            "extraction_status": extraction_data.get("status") if extraction_data else None,
            "extraction_fields": len(extraction_data.get("result", {})) if extraction_data else 0
        }
        
        logger.info(f"\nResults for {mode} mode:")
        logger.info(f"  Doc ID: {result['doc_id']}")
        logger.info(f"  Final Phase: {result['final_phase']}")
        logger.info(f"  Elapsed Time: {result['elapsed_time']:.2f}s")
        logger.info(f"  Extraction Exists: {result['extraction_exists']}")
        logger.info(f"  Extraction Status: {result['extraction_status']}")
        logger.info(f"  Extraction Fields: {result['extraction_fields']}")
        
        return result
        
    finally:
        # Restore original mode
        settings.embedding.ingest_mode = original_mode


def compare_results(results: list[dict]) -> None:
    """Compare results from different ingestion modes."""
    logger.info(f"\n{'='*60}")
    logger.info("COMPARISON RESULTS")
    logger.info(f"{'='*60}\n")
    
    # Create comparison table
    logger.info(f"{'Mode':<10} {'Phase':<12} {'Time (s)':<10} {'Extraction':<12} {'Fields':<8}")
    logger.info("-" * 60)
    
    for result in results:
        if "error" in result:
            logger.info(f"{result.get('mode', 'Unknown'):<10} ERROR: {result['error']}")
        else:
            logger.info(
                f"{result['mode']:<10} "
                f"{result['final_phase']:<12} "
                f"{result['elapsed_time']:<10.2f} "
                f"{'Yes' if result['extraction_exists'] else 'No':<12} "
                f"{result['extraction_fields']:<8}"
            )
    
    # Check for feature parity
    logger.info(f"\n{'='*60}")
    logger.info("FEATURE PARITY CHECK")
    logger.info(f"{'='*60}")
    
    if len(results) >= 2:
        simple_result = next((r for r in results if r.get('mode') == 'simple'), None)
        parallel_result = next((r for r in results if r.get('mode') == 'parallel'), None)
        
        if simple_result and parallel_result and "error" not in simple_result and "error" not in parallel_result:
            parity_checks = [
                ("Final Phase", simple_result['final_phase'] == parallel_result['final_phase']),
                ("Extraction Exists", simple_result['extraction_exists'] == parallel_result['extraction_exists']),
                ("Extraction Status", simple_result['extraction_status'] == parallel_result['extraction_status']),
                ("Field Count", simple_result['extraction_fields'] == parallel_result['extraction_fields']),
            ]
            
            all_match = all(check[1] for check in parity_checks)
            
            for check_name, matches in parity_checks:
                logger.info(f"  {check_name}: {'✅ MATCH' if matches else '❌ MISMATCH'}")
            
            logger.info(f"\nOverall Feature Parity: {'✅ PASSED' if all_match else '❌ FAILED'}")
            
            # Performance comparison
            if simple_result['elapsed_time'] > 0:
                speedup = simple_result['elapsed_time'] / parallel_result['elapsed_time']
                logger.info(f"\nPerformance: Parallel mode is {speedup:.2f}x {'faster' if speedup > 1 else 'slower'}")


def main():
    parser = argparse.ArgumentParser(description="Test and compare ingestion modes")
    parser.add_argument("file", help="File to ingest for testing")
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=["simple", "parallel", "batch", "pipeline"],
        default=["simple", "parallel"],
        help="Modes to test (default: simple parallel)"
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=60,
        help="Maximum seconds to wait for processing (default: 60)"
    )
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    results = []
    
    for mode in args.modes:
        try:
            result = test_ingestion_mode(file_path, mode, args.wait)
            results.append(result)
        except Exception as e:
            logger.error(f"Error testing {mode} mode: {str(e)}")
            results.append({"mode": mode, "error": str(e)})
    
    # Compare results
    compare_results(results)


if __name__ == "__main__":
    main()