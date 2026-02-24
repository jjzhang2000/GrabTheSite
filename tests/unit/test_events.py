"""事件总线模块单元测试"""

import pytest
import threading
import time
from unittest.mock import Mock

from utils.events import (
    Event,
    EventBus,
    EventPriority,
    get_event_bus,
    publish,
    subscribe,
    on,
)


class TestEvent:
    """测试 Event 数据类"""

    def test_event_creation(self):
        """测试事件创建"""
        event = Event(name="test_event", data={"key": "value"}, source="test")
        assert event.name == "test_event"
        assert event.data == {"key": "value"}
        assert event.source == "test"
        assert isinstance(event.timestamp, float)
        assert isinstance(event.id, str)

    def test_event_to_dict(self):
        """测试事件转换为字典"""
        event = Event(name="test_event", data={"key": "value"}, source="test")
        data = event.to_dict()
        assert data["name"] == "test_event"
        assert data["data"] == {"key": "value"}
        assert data["source"] == "test"
        assert "timestamp" in data
        assert "id" in data


class TestEventBus:
    """测试 EventBus 类"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.bus = EventBus()

    def teardown_method(self):
        """每个测试方法后执行"""
        self.bus.shutdown()

    def test_subscribe_and_publish(self):
        """测试订阅和发布"""
        received = []

        def handler(event):
            received.append(event.data)

        self.bus.subscribe("test_event", handler)
        self.bus.publish("test_event", data="test_data")

        assert len(received) == 1
        assert received[0] == "test_data"

    def test_unsubscribe(self):
        """测试取消订阅"""
        received = []

        def handler(event):
            received.append(event.data)

        self.bus.subscribe("test_event", handler)
        self.bus.publish("test_event", data="first")

        result = self.bus.unsubscribe("test_event", handler)
        assert result is True

        self.bus.publish("test_event", data="second")

        assert len(received) == 1
        assert received[0] == "first"

    def test_unsubscribe_not_exist(self):
        """测试取消不存在的订阅"""
        def handler(event):
            pass

        result = self.bus.unsubscribe("test_event", handler)
        assert result is False

    def test_priority_order(self):
        """测试优先级顺序"""
        order = []

        def high_handler(event):
            order.append("high")

        def low_handler(event):
            order.append("low")

        def normal_handler(event):
            order.append("normal")

        # 按不同顺序订阅
        self.bus.subscribe("test", low_handler, EventPriority.LOW)
        self.bus.subscribe("test", high_handler, EventPriority.HIGH)
        self.bus.subscribe("test", normal_handler, EventPriority.NORMAL)

        self.bus.publish("test")

        # 高优先级应该先执行
        assert order == ["high", "normal", "low"]

    def test_once_subscription(self):
        """测试一次性订阅"""
        received = []

        def handler(event):
            received.append(event.data)

        self.bus.once("test_event", handler)

        self.bus.publish("test_event", data="first")
        self.bus.publish("test_event", data="second")

        assert len(received) == 1
        assert received[0] == "first"

    def test_emit_alias(self):
        """测试 emit 是 publish 的别名"""
        received = []

        def handler(event):
            received.append(event.data)

        self.bus.subscribe("test_event", handler)
        self.bus.emit("test_event", data="test_data")

        assert len(received) == 1

    def test_on_decorator(self):
        """测试 on 装饰器"""
        received = []

        @self.bus.on("test_event")
        def handler(event):
            received.append(event.data)

        self.bus.publish("test_event", data="test_data")

        assert len(received) == 1
        assert received[0] == "test_data"

    def test_clear_specific_event(self):
        """测试清除特定事件"""
        received1 = []
        received2 = []

        def handler1(event):
            received1.append(event.data)

        def handler2(event):
            received2.append(event.data)

        self.bus.subscribe("event1", handler1)
        self.bus.subscribe("event2", handler2)

        self.bus.clear("event1")

        self.bus.publish("event1", data="test1")
        self.bus.publish("event2", data="test2")

        assert len(received1) == 0
        assert len(received2) == 1

    def test_clear_all(self):
        """测试清除所有事件"""
        received = []

        def handler(event):
            received.append(event.data)

        self.bus.subscribe("event1", handler)
        self.bus.subscribe("event2", handler)

        self.bus.clear()

        self.bus.publish("event1", data="test1")
        self.bus.publish("event2", data="test2")

        assert len(received) == 0

    def test_get_subscribers(self):
        """测试获取订阅者列表"""
        def handler1(event):
            pass

        def handler2(event):
            pass

        self.bus.subscribe("test_event", handler1)
        self.bus.subscribe("test_event", handler2)

        subscribers = self.bus.get_subscribers("test_event")

        assert len(subscribers) == 2
        assert handler1 in subscribers
        assert handler2 in subscribers

    def test_has_subscribers(self):
        """测试检查是否有订阅者"""
        def handler(event):
            pass

        assert self.bus.has_subscribers("test_event") is False

        self.bus.subscribe("test_event", handler)

        assert self.bus.has_subscribers("test_event") is True

    def test_handler_exception(self):
        """测试处理器异常处理"""
        received = []

        def error_handler(event):
            raise ValueError("Test error")

        def normal_handler(event):
            received.append(event.data)

        self.bus.subscribe("test_event", error_handler)
        self.bus.subscribe("test_event", normal_handler)

        # 不应该抛出异常
        self.bus.publish("test_event", data="test")

        # 正常处理器应该仍然执行
        assert len(received) == 1

    def test_thread_safety(self):
        """测试线程安全"""
        received = []
        lock = threading.Lock()

        def handler(event):
            with lock:
                received.append(event.data)

        self.bus.subscribe("test_event", handler)

        threads = []
        for i in range(10):
            t = threading.Thread(target=self.bus.publish, args=("test_event", i))
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(received) == 10

    def test_shutdown(self):
        """测试关闭事件总线"""
        received = []

        def handler(event):
            received.append(event.data)

        self.bus.subscribe("test_event", handler)

        self.bus.shutdown()

        # 关闭后发布事件不应该被处理
        self.bus.publish("test_event", data="test")

        assert len(received) == 0


class TestGlobalFunctions:
    """测试全局便捷函数"""

    def test_get_event_bus_singleton(self):
        """测试 get_event_bus 返回单例"""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_publish_subscribe(self):
        """测试全局 publish 和 subscribe"""
        received = []

        def handler(event):
            received.append(event.data)

        unsubscribe = subscribe("global_test", handler)
        publish("global_test", data="global_data")

        assert len(received) == 1
        assert received[0] == "global_data"

        unsubscribe()

    def test_on_decorator(self):
        """测试全局 on 装饰器"""
        received = []

        @on("decorator_test")
        def handler(event):
            received.append(event.data)

        publish("decorator_test", data="decorator_data")

        assert len(received) == 1
        assert received[0] == "decorator_data"
