# event_bus.py
class EventBus:
    _listeners = {}

    @classmethod
    def subscribe(cls, event_type: str, listener_callable):
        if event_type not in cls._listeners:
            cls._listeners[event_type] = []
        cls._listeners[event_type].append(listener_callable)

    @classmethod
    def publish(cls, event_type: str, *args, **kwargs):
        results = []
        if event_type in cls._listeners:
            for listener in cls._listeners[event_type]:
                try:
                    results.append(listener(*args, **kwargs))
                except Exception as e:
                    print(f"[EventBus] '{event_type}' tetiklenirken hata oluştu: {e}")
        return results[0] if len(results) == 1 else results

    @classmethod
    def unsubscribe(cls, event_type: str, listener_callable):
        if event_type in cls._listeners and listener_callable in cls._listeners[event_type]:
            cls._listeners[event_type].remove(listener_callable)