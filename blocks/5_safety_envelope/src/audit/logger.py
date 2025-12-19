# Block 5: Audit Logger
_audit = []

def log_decision(entry):
    """Log decision for audit trail (async)."""
    _audit.append(entry)
