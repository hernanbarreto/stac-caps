# Block 6: CAN Encoder
def encode_can_message(decision):
    """Encode brake command for CAN bus. (<1ms)"""
    return {'id': 0x100, 'data': [ord(decision.action[0])]}
