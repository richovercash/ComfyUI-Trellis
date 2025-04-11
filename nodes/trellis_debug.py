import logging
import json
from pathlib import Path
from datetime import datetime

class TrellisDebugger:
    def __init__(self):
        self.log_dir = Path(__file__).parent.parent / "debug_logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Create a new log file for each session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"trellis_debug_{timestamp}.log"
        
        # Set up file logger
        self.logger = logging.getLogger('TrellisDebug')
        self.logger.setLevel(logging.DEBUG)
        
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
    
    def log_data(self, source, event_type, data):
        try:
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, indent=2)
            else:
                data_str = str(data)
            
            message = f"\n=== {source} - {event_type} ===\n{data_str}\n"
            self.logger.debug(message)
        except Exception as e:
            self.logger.error(f"Error logging data: {e}")

debugger = TrellisDebugger() 