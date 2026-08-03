import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from engines.functional.engine import FunctionalEngine
from engines.security.engine import SecurityEngine
from engines.accessibility.engine import AccessibilityEngine
from engines.visual.engine import VisualEngine
from engines.usability.engine import UsabilityEngine

@pytest.mark.asyncio
async def test_functional_engine_methods():
    engine = FunctionalEngine()
    assert hasattr(engine, "analyze_and_test")
    assert hasattr(engine, "check_api_response")

@pytest.mark.asyncio
async def test_security_engine_methods():
    engine = SecurityEngine()
    assert hasattr(engine, "scan_security_headers")
    assert hasattr(engine, "_check_zap_status")

@pytest.mark.asyncio
async def test_accessibility_engine_methods():
    engine = AccessibilityEngine()
    assert hasattr(engine, "scan_page")

@pytest.mark.asyncio
async def test_visual_engine_methods():
    engine = VisualEngine()
    assert hasattr(engine, "audit_visual_rendering")

@pytest.mark.asyncio
async def test_usability_engine_methods():
    engine = UsabilityEngine()
    assert hasattr(engine, "analyze_page")
