"""Context sharing for AI services."""
import logging
from app.services.ai_coordinator import AIRescueCoordinator

logger = logging.getLogger(__name__)

_ai_coordinator = None

def get_ai_coordinator():
    """Get or create AI coordinator instance (lazy initialization)."""
    global _ai_coordinator
    if _ai_coordinator is None:
        try:
            _ai_coordinator = AIRescueCoordinator()
            logger.info("✅ AI Rescue Coordinator initialized (Singleton)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI coordinator: {e}")
            raise
    return _ai_coordinator
