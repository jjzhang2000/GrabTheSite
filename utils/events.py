"""事件总线模块

提供发布-订阅模式的事件系统：
- EventBus: 事件总线
- Event: 事件数据类
- EventPriority: 事件优先级
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
import threading
import time
from functools import wraps

from logger import setup_logger, _ as _t

logger = setup_logger(__name__)


class EventPriority(Enum):
    """事件优先级"""
    HIGHEST = 0   # 最高优先级
    HIGH = 1      # 高优先级
    NORMAL = 2    # 普通优先级（默认）
    LOW = 3       # 低优先级
    LOWEST = 4    # 最低优先级


@dataclass
class Event:
    """事件数据类

    Attributes:
        name: 事件名称
        data: 事件数据
        timestamp: 事件发生时间
        source: 事件来源
        id: 事件唯一标识
    """
    name: str
    data: Any = None
    timestamp: float = field(default_factory=time.time)
    source: Optional[str] = None
    id: str = field(default_factory=lambda: str(time.time()))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'data': self.data,
            'timestamp': self.timestamp,
            'source': self.source,
            'id': self.id,
        }


class EventBus:
    """事件总线

    提供发布-订阅模式的事件系统，支持：
    - 多订阅者
    - 优先级
    - 异步/同步处理
    - 一次性订阅
    """

    def __init__(self):
        """初始化事件总线"""
        self._subscribers: Dict[str, List[tuple]] = {}  # event_name -> [(priority, callback, once)]
        self._lock: threading.RLock = threading.RLock()
        self._running: bool = True

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[Event], None],
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False
    ) -> Callable:
        """订阅事件

        Args:
            event_name: 事件名称
            callback: 回调函数
            priority: 优先级
            once: 是否只订阅一次

        Returns:
            取消订阅函数
        """
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []

            # 按优先级插入
            self._subscribers[event_name].append((priority.value, callback, once))
            self._subscribers[event_name].sort(key=lambda x: x[0])

        logger.debug(_t("订阅事件") + f": {event_name}, " + _t("优先级") + f": {priority.name}")

        # 返回取消订阅函数
        def unsubscribe():
            self.unsubscribe(event_name, callback)

        return unsubscribe

    def unsubscribe(self, event_name: str, callback: Callable[[Event], None]) -> bool:
        """取消订阅

        Args:
            event_name: 事件名称
            callback: 回调函数

        Returns:
            是否成功取消
        """
        with self._lock:
            if event_name in self._subscribers:
                original_len = len(self._subscribers[event_name])
                self._subscribers[event_name] = [
                    (p, cb, once) for p, cb, once in self._subscribers[event_name]
                    if cb != callback
                ]
                if len(self._subscribers[event_name]) < original_len:
                    logger.debug(_t("取消订阅") + f": {event_name}")
                    return True
        return False

    def publish(self, event_name: str, data: Any = None, source: Optional[str] = None) -> None:
        """发布事件（同步）

        Args:
            event_name: 事件名称
            data: 事件数据
            source: 事件来源
        """
        if not self._running:
            return

        event = Event(name=event_name, data=data, source=source)

        with self._lock:
            subscribers = list(self._subscribers.get(event_name, []))

        # 调用订阅者
        to_remove = []
        for priority, callback, once in subscribers:
            try:
                callback(event)
                if once:
                    to_remove.append((event_name, callback))
            except Exception as e:
                logger.error(_t("事件处理失败") + f": {event_name}, {e}")

        # 移除一次性订阅
        for event_name, callback in to_remove:
            self.unsubscribe(event_name, callback)

    def emit(self, event_name: str, data: Any = None, source: Optional[str] = None) -> None:
        """发布事件的别名"""
        self.publish(event_name, data, source)

    def on(self, event_name: str, priority: EventPriority = EventPriority.NORMAL):
        """事件装饰器

        用于将函数注册为事件处理器。

        Args:
            event_name: 事件名称
            priority: 优先级

        Returns:
            装饰器函数
        """
        def decorator(func: Callable[[Event], None]) -> Callable[[Event], None]:
            self.subscribe(event_name, func, priority)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper
        return decorator

    def once(self, event_name: str, callback: Callable[[Event], None]) -> Callable:
        """订阅一次性事件

        Args:
            event_name: 事件名称
            callback: 回调函数

        Returns:
            取消订阅函数
        """
        return self.subscribe(event_name, callback, once=True)

    def clear(self, event_name: Optional[str] = None) -> None:
        """清除订阅

        Args:
            event_name: 事件名称，如果为 None 则清除所有订阅
        """
        with self._lock:
            if event_name:
                if event_name in self._subscribers:
                    del self._subscribers[event_name]
                    logger.debug(_t("清除事件订阅") + f": {event_name}")
            else:
                self._subscribers.clear()
                logger.debug(_t("清除所有事件订阅"))

    def get_subscribers(self, event_name: str) -> List[Callable]:
        """获取事件的订阅者列表

        Args:
            event_name: 事件名称

        Returns:
            订阅者回调列表
        """
        with self._lock:
            return [cb for _, cb, _ in self._subscribers.get(event_name, [])]

    def has_subscribers(self, event_name: str) -> bool:
        """检查事件是否有订阅者

        Args:
            event_name: 事件名称

        Returns:
            是否有订阅者
        """
        with self._lock:
            return event_name in self._subscribers and len(self._subscribers[event_name]) > 0

    def shutdown(self) -> None:
        """关闭事件总线"""
        self._running = False
        self.clear()
        logger.info(_t("事件总线已关闭"))


# 全局事件总线实例
_event_bus: Optional[EventBus] = None
_event_bus_lock: threading.Lock = threading.Lock()


def get_event_bus() -> EventBus:
    """获取全局事件总线实例

    Returns:
        EventBus: 事件总线实例
    """
    global _event_bus
    if _event_bus is None:
        with _event_bus_lock:
            if _event_bus is None:
                _event_bus = EventBus()
    return _event_bus


def publish(event_name: str, data: Any = None, source: Optional[str] = None) -> None:
    """发布事件的便捷函数

    Args:
        event_name: 事件名称
        data: 事件数据
        source: 事件来源
    """
    get_event_bus().publish(event_name, data, source)


def subscribe(
    event_name: str,
    callback: Callable[[Event], None],
    priority: EventPriority = EventPriority.NORMAL
) -> Callable:
    """订阅事件的便捷函数

    Args:
        event_name: 事件名称
        callback: 回调函数
        priority: 优先级

    Returns:
        取消订阅函数
    """
    return get_event_bus().subscribe(event_name, callback, priority)


def on(event_name: str, priority: EventPriority = EventPriority.NORMAL):
    """事件装饰器的便捷函数

    Args:
        event_name: 事件名称
        priority: 优先级

    Returns:
        装饰器函数
    """
    return get_event_bus().on(event_name, priority)
