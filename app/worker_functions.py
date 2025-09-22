"""Worker functions for parallel processing."""

import time
import random
from typing import Dict, Any


def dummy_worker_process(file_path: str, worker_id: int) -> Dict[str, Any]:
    """Dummy worker process dat file processing simuleert."""
    
    # Simuleer processing werk
    # processing_time = random.uniform(0.1, 0.5)
    # time.sleep(processing_time)
    processing_time = 0.0
    
    # Simuleer success/failure
    success = random.random() > 0.1  # 90% success rate
   #DEBUG_OFF log message in dummy worker process
    # Stuur resultaat
    result = {
        'file_path': file_path,
        'worker_id': worker_id,
        'success': success,
        'processing_time': processing_time,
        'log_messages': [
            # {
            #     'level': 'DEBUG', 
            #     'message': f'Created in Workerfunctions.py: Worker {worker_id} processed {file_path} in {processing_time:.2f}s'
            # }
        ]
    }
    return result
