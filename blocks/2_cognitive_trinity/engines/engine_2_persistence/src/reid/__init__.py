# Engine 2: ReID Module - OSNet Re-Identification
from .osnet import OSNetReID
from .ema import update_embedding

__all__ = ['OSNetReID', 'update_embedding']
