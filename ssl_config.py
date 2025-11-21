"""
SSL Configuration Bypass for HyperLiquid API

This module disables SSL verification for HTTP requests to fix connection issues
with the HyperLiquid testnet API. Import this at the beginning of main.py.
"""
import ssl
import httpx
import warnings

# Disable SSL warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Disable SSL verification globally for httpx
httpx._config.DEFAULT_SSL_CONTEXT = ssl._create_unverified_context()

print("[SSL Config] SSL verification disabled for HyperLiquid API connections")
