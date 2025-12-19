# Block 6: Output Manager - Entry Point
from .config import OUTPUT_PARAMS

class OutputManager:
    """Multi-protocol output interface. CAN, SCADA, MQTT, REST."""
    def __init__(self):
        self.params = OUTPUT_PARAMS
    
    def send(self, safety_decision):
        """Send decision to all channels."""
        from .can.encoder import encode_can_message
        from .mqtt.publisher import publish_mqtt
        
        if safety_decision.action in ['EMERGENCY', 'SERVICE']:
            encode_can_message(safety_decision)
        publish_mqtt(safety_decision)
        return True
