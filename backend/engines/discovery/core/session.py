import uuid
from typing import List, Type
from datetime import datetime, timezone
import logging
import asyncio
from core.event_bus import event_bus
from plugins.base import BaseDiscoveryPlugin

logger = logging.getLogger(__name__)

class DiscoverySession:
    """
    Orchestrates the entire discovery pipeline for a single reproducible session.
    """
    def __init__(self, application_id: str, seed_url: str):
        self.session_id = str(uuid.uuid4())
        self.application_id = application_id
        self.seed_url = seed_url
        self.started_at = datetime.now(timezone.utc)
        self.plugins: List[BaseDiscoveryPlugin] = []
        
    def load_plugins(self, plugin_classes: List[Type[BaseDiscoveryPlugin]]):
        """Loads plugins based on fingerprint/policy."""
        for p_class in plugin_classes:
            self.plugins.append(p_class(session_id=self.session_id, application_id=self.application_id))
            
    async def run(self, context: Any = None):
        """Executes the pipeline."""
        await event_bus.publish("SessionStarted", {
            "session_id": self.session_id,
            "application_id": self.application_id,
            "seed_url": self.seed_url
        })
        
        # We execute plugins concurrently. Task dependencies (DAG) would be resolved here in production.
        tasks = []
        for plugin in self.plugins:
            tasks.append(asyncio.create_task(plugin.execute(context)))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for plugin, result in zip(self.plugins, results):
            if isinstance(result, Exception):
                logger.error(f"Session {self.session_id} - Plugin {plugin.name} failed: {result}")
        
        await self._generate_quality_report()

    async def _generate_quality_report(self):
        """Generates the ARB-mandated Quality Metrics."""
        report = {
            "session_id": self.session_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "plugins_executed": len(self.plugins),
            "status": "completed"
            # Metrics like 'States found', 'Behavior coverage' would be aggregated here
        }
        await event_bus.publish("DiscoveryCompleted", report)
        logger.info(f"Session {self.session_id} completed.")
