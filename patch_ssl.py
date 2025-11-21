"""
SSL Patch for HyperLiquid API

This module disables SSL verification to fix connection issues with the HyperLiquid testnet API.
Import this at the beginning of main.py before any other imports that use HTTP clients.
"""
import ssl
import warnings

# Disable SSL warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Monkey-patch SSL context creation to disable verification
_original_create_default_context = ssl.create_default_context

def _create_unverified_context(*args, **kwargs):
    context = _original_create_default_context(*args, **kwargs)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

ssl.create_default_context = _create_unverified_context
ssl._create_default_https_context = _create_unverified_context

print("[SSL Patch] SSL verification disabled for all HTTPS connections")
