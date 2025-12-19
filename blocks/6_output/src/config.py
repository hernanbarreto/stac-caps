# Block 6: Output Config
OUTPUT_PARAMS = {
    'can': {'interface': 'can0', 'bitrate': 500000, 'brake_message_id': 0x100},
    'mqtt': {'broker': 'localhost', 'port': 8883, 'tls_enabled': True, 'qos': 2},
    'scada': {'protocol': 'opcua', 'endpoint': 'opc.tcp://localhost:4840'}
}
