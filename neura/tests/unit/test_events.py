"""
Tests for event bus.
"""

import asyncio

import pytest

from neura.core.events import EventBus, get_event_bus
from neura.core.exceptions import EventBusError
from neura.core.types import Event


class TestEventBus:
    """Tests for EventBus."""

    @pytest.fixture
    def event_bus(self):
        """Create a fresh event bus for each test."""
        return EventBus()

    @pytest.mark.asyncio
    async def test_event_bus_init(self, event_bus):
        """Test event bus initialization."""
        assert event_bus is not None
        assert not event_bus._running
        assert event_bus._worker_task is None

    @pytest.mark.asyncio
    async def test_subscribe_valid_handler(self, event_bus):
        """Test subscribing with a valid async handler."""
        async def handler(event: Event):
            pass

        event_bus.subscribe("test.event", handler)
        assert "test.event" in event_bus._subscribers
        assert handler in event_bus._subscribers["test.event"]

    @pytest.mark.asyncio
    async def test_subscribe_invalid_handler(self, event_bus):
        """Test subscribing with a non-async handler raises error."""
        def sync_handler(event: Event):
            pass

        with pytest.raises(EventBusError):
            event_bus.subscribe("test.event", sync_handler)

    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus):
        """Test unsubscribing from an event."""
        async def handler(event: Event):
            pass

        event_bus.subscribe("test.event", handler)
        assert handler in event_bus._subscribers["test.event"]

        event_bus.unsubscribe("test.event", handler)
        assert handler not in event_bus._subscribers["test.event"]

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, event_bus):
        """Test unsubscribing from a non-existent event."""
        async def handler(event: Event):
            pass

        # Should not raise error
        event_bus.unsubscribe("nonexistent.event", handler)

    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus):
        """Test publishing an event."""
        await event_bus.publish("test.event", {"key": "value"}, source="test")
        
        # Event should be in queue
        assert not event_bus._event_queue.empty()
        
        # Get event from queue
        event = await event_bus._event_queue.get()
        assert event.name == "test.event"
        assert event.data == {"key": "value"}
        assert event.source == "test"

    @pytest.mark.asyncio
    async def test_start_stop(self, event_bus):
        """Test starting and stopping the event bus."""
        assert not event_bus._running
        
        await event_bus.start()
        assert event_bus._running
        assert event_bus._worker_task is not None
        
        await event_bus.stop()
        assert not event_bus._running

    @pytest.mark.asyncio
    async def test_start_already_running(self, event_bus):
        """Test starting an already running event bus."""
        await event_bus.start()
        
        # Starting again should log warning but not error
        await event_bus.start()
        
        await event_bus.stop()

    @pytest.mark.asyncio
    async def test_event_dispatch(self, event_bus):
        """Test that events are dispatched to handlers."""
        received_events = []

        async def handler(event: Event):
            received_events.append(event)

        event_bus.subscribe("test.event", handler)
        await event_bus.start()

        # Publish event
        await event_bus.publish("test.event", {"data": "test"}, source="test")

        # Wait for processing
        await asyncio.sleep(0.1)

        await event_bus.stop()

        # Handler should have received the event
        assert len(received_events) == 1
        assert received_events[0].name == "test.event"
        assert received_events[0].data == {"data": "test"}

    @pytest.mark.asyncio
    async def test_multiple_handlers(self, event_bus):
        """Test multiple handlers for the same event."""
        handler1_called = []
        handler2_called = []

        async def handler1(event: Event):
            handler1_called.append(event)

        async def handler2(event: Event):
            handler2_called.append(event)

        event_bus.subscribe("test.event", handler1)
        event_bus.subscribe("test.event", handler2)
        await event_bus.start()

        await event_bus.publish("test.event", {"data": "test"}, source="test")
        await asyncio.sleep(0.1)

        await event_bus.stop()

        # Both handlers should have been called
        assert len(handler1_called) == 1
        assert len(handler2_called) == 1

    @pytest.mark.asyncio
    async def test_no_handlers(self, event_bus):
        """Test publishing event with no handlers."""
        await event_bus.start()

        # Should not raise error
        await event_bus.publish("unhandled.event", {"data": "test"}, source="test")
        await asyncio.sleep(0.1)

        await event_bus.stop()

    @pytest.mark.asyncio
    async def test_handler_exception(self, event_bus):
        """Test that handler exceptions don't crash the bus."""
        async def failing_handler(event: Event):
            raise ValueError("Handler error")

        event_bus.subscribe("test.event", failing_handler)
        await event_bus.start()

        # Should not raise error
        await event_bus.publish("test.event", {"data": "test"}, source="test")
        await asyncio.sleep(0.1)

        await event_bus.stop()


class TestEventBusSingleton:
    """Tests for event bus singleton."""

    def test_get_event_bus(self):
        """Test getting the global event bus."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        
        # Should return the same instance
        assert bus1 is bus2

    @pytest.mark.asyncio
    async def test_singleton_persistence(self):
        """Test that singleton persists across calls."""
        bus = get_event_bus()
        
        async def handler(event: Event):
            pass
        
        bus.subscribe("test.event", handler)
        
        # Get bus again
        bus2 = get_event_bus()
        
        # Should have the same subscription
        assert "test.event" in bus2._subscribers
        assert handler in bus2._subscribers["test.event"]


class TestEventBusIntegration:
    """Integration tests for event bus."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete pub/sub workflow."""
        bus = EventBus()
        events_received = []

        async def memory_handler(event: Event):
            events_received.append(("memory", event))

        async def cortex_handler(event: Event):
            events_received.append(("cortex", event))

        # Subscribe handlers
        bus.subscribe("memory.stored", memory_handler)
        bus.subscribe("cortex.generated", cortex_handler)

        # Start bus
        await bus.start()

        # Publish events
        await bus.publish("memory.stored", {"id": "123"}, source="memory")
        await bus.publish("cortex.generated", {"text": "Hello"}, source="cortex")

        # Wait for processing
        await asyncio.sleep(0.2)

        # Stop bus
        await bus.stop()

        # Verify events received
        assert len(events_received) == 2
        
        memory_events = [e for name, e in events_received if name == "memory"]
        cortex_events = [e for name, e in events_received if name == "cortex"]
        
        assert len(memory_events) == 1
        assert len(cortex_events) == 1
        assert memory_events[0].data == {"id": "123"}
        assert cortex_events[0].data == {"text": "Hello"}

    @pytest.mark.asyncio
    async def test_event_ordering(self):
        """Test that events are processed in order."""
        bus = EventBus()
        order = []

        async def handler(event: Event):
            order.append(event.data["num"])

        bus.subscribe("test.event", handler)
        await bus.start()

        # Publish events in order
        for i in range(5):
            await bus.publish("test.event", {"num": i}, source="test")

        await asyncio.sleep(0.2)
        await bus.stop()

        # Events should be processed in order
        assert order == [0, 1, 2, 3, 4]
