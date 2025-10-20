"""
Event bus for inter-module communication.

The event bus allows modules to communicate asynchronously without
direct dependencies. Modules can publish events and subscribe to
events from other modules.
"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine

from neura.core.exceptions import EventBusError
from neura.core.types import Event

logger = logging.getLogger(__name__)


# Type alias for event handlers
EventHandler = Callable[[Event], Coroutine[None, None, None]]


class EventBus:
    """
    Asynchronous event bus for pub/sub communication.

    Example:
        >>> bus = EventBus()
        >>>
        >>> async def handle_memory_stored(event: Event):
        ...     print(f"Memory stored: {event.data}")
        >>>
        >>> bus.subscribe("memory.stored", handle_memory_stored)
        >>> await bus.publish("memory.stored", {"id": "123"}, source="memory")
    """

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._event_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False
        self._worker_task: asyncio.Task | None = None

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """
        Subscribe to an event.

        Args:
            event_name: Name of the event to subscribe to (e.g., "memory.stored")
            handler: Async function to handle the event

        Raises:
            EventBusError: If handler is not a coroutine function
        """
        if not asyncio.iscoroutinefunction(handler):
            raise EventBusError(
                "Event handler must be an async function",
                details={"event": event_name, "handler": handler.__name__},
            )

        self._subscribers[event_name].append(handler)
        logger.debug(f"Subscribed to event: {event_name} (handler: {handler.__name__})")

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """
        Unsubscribe from an event.

        Args:
            event_name: Name of the event
            handler: Handler to remove
        """
        if event_name in self._subscribers:
            try:
                self._subscribers[event_name].remove(handler)
                logger.debug(f"Unsubscribed from event: {event_name} (handler: {handler.__name__})")
            except ValueError:
                pass

    async def publish(self, event_name: str, data: dict, source: str) -> None:
        """
        Publish an event to the bus.

        Args:
            event_name: Name of the event (e.g., "memory.stored")
            data: Event payload
            source: Module that is publishing the event

        Example:
            >>> await bus.publish("cortex.generated", {"text": "Hello"}, source="cortex")
        """
        event = Event.create(name=event_name, data=data, source=source)
        await self._event_queue.put(event)
        logger.debug(f"Published event: {event_name} from {source}")

    async def _process_events(self) -> None:
        """
        Process events from the queue.

        This runs continuously in the background, dispatching events
        to their handlers.
        """
        while self._running:
            try:
                # Wait for an event with timeout to allow clean shutdown
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)

                # Dispatch to all subscribers
                handlers = self._subscribers.get(event.name, [])
                if handlers:
                    tasks = [handler(event) for handler in handlers]
                    await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    logger.debug(f"No handlers for event: {event.name}")

            except asyncio.TimeoutError:
                # No events, continue
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def start(self) -> None:
        """Start the event bus worker."""
        if self._running:
            logger.warning("Event bus already running")
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop the event bus worker."""
        if not self._running:
            return

        self._running = False
        if self._worker_task:
            await self._worker_task
        logger.info("Event bus stopped")


# Singleton instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.

    Returns:
        EventBus: The singleton event bus
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
