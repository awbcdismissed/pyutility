import os

from PyQt6.QtCore import QEasingCurve, QObject, QEvent, QPropertyAnimation, QParallelAnimationGroup, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDialog,
    QGraphicsOpacityEffect,
    QScrollArea,
    QTabWidget,
    QWidget,
)


def reduced_motion_enabled(app=None):
    """Allow an explicit accessibility override without adding a dependency."""
    value = os.environ.get("PAP_REDUCED_MOTION", "").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return bool(app and app.property("reducedMotion"))


class AnimationController(QObject):
    """Centralized, lightweight motion for the application's standard widgets."""

    def __init__(self, app: QApplication):
        super().__init__(app)
        self.app = app
        self._animations = []
        app.installEventFilter(self)

    @property
    def reduced_motion(self):
        return reduced_motion_enabled(self.app)

    def duration(self, normal=220):
        return 0 if self.reduced_motion else normal

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Show and isinstance(watched, QWidget):
            popup_types = (Qt.WindowType.Popup, Qt.WindowType.ToolTip)
            if isinstance(watched, QDialog) or watched.windowType() in popup_types:
                self.fade(watched, 0.0, 1.0, 180)
        return super().eventFilter(watched, event)

    def fade(self, widget, start, end, duration=220):
        if not widget or (not widget.isVisible() and start != 0.0):
            return
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        effect.setOpacity(start)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(self.duration(duration))
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._keep_animation(animation)
        animation.finished.connect(lambda: self._finish_animation(animation, widget, end))
        animation.start()

    def animate_tab(self, tab_widget: QTabWidget, index):
        if index < 0:
            return
        page = tab_widget.widget(index)
        if page is None or self.reduced_motion or self._contains_dynamic_view(page):
            return
        effect = page.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(page)
            page.setGraphicsEffect(effect)
        effect.setOpacity(0.72)
        page_animation = QPropertyAnimation(effect, b"opacity", self)
        page_animation.setDuration(self.duration(220))
        page_animation.setStartValue(0.72)
        page_animation.setEndValue(1.0)
        page_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        bar_effect = tab_widget.tabBar().graphicsEffect()
        if not isinstance(bar_effect, QGraphicsOpacityEffect):
            bar_effect = QGraphicsOpacityEffect(tab_widget.tabBar())
            tab_widget.tabBar().setGraphicsEffect(bar_effect)
        bar_effect.setOpacity(0.94)
        bar_animation = QPropertyAnimation(bar_effect, b"opacity", self)
        bar_animation.setDuration(self.duration(160))
        bar_animation.setStartValue(0.94)
        bar_animation.setEndValue(1.0)
        group = QParallelAnimationGroup(self)
        group.addAnimation(page_animation)
        group.addAnimation(bar_animation)
        self._keep_animation(group)
        group.finished.connect(lambda: self._release_animation(group))
        group.start()

    def _keep_animation(self, animation):
        self._animations.append(animation)

    def _release_animation(self, animation):
        if animation in self._animations:
            self._animations.remove(animation)

    def _finish_animation(self, animation, widget, end):
        effect = widget.graphicsEffect()
        if isinstance(effect, QGraphicsOpacityEffect):
            effect.setOpacity(end)
        self._release_animation(animation)

    @staticmethod
    def _contains_dynamic_view(page):
        """Avoid compositing animations over widgets that frequently relayout."""
        return bool(page.findChildren(QAbstractItemView) or page.findChildren(QScrollArea))