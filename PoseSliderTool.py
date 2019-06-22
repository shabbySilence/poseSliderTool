# !/usr/bin/python
# -*- coding: utf-8 -*-
import PySide2.QtCore as QtCore
import PySide2.QtGui  as QtGui
import PySide2.QtWidgets as QtWidgets
import maya.cmds  as mc
import pymel.core as pm

import maya.OpenMaya as om
import os
from functools import partial
import maya.utils as utils
#
__author__ = "ran.li"

def undo_pm(func):
    def wrapper(*args, **kwargs):
        pm.undoInfo(openChunk=True)
        try:
            ret = func(*args, **kwargs)
        finally:
            pm.undoInfo(closeChunk=True)
        return ret
    return wrapper
START      = 'start'
END        = 'end'
CACHE      = 'cache'
NODE       = 'node'

class InterpolateIt(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Pose Slider Tool')
        self.setObjectName('InterpolateIt')
        self.setFixedWidth(314)

        style_sheet_file = QtCore.QFile(os.path.join(os.path.dirname(__file__), 'stylesheets', 'scheme.qss'))
        style_sheet_file.open(QtCore.QFile.ReadOnly)
        #self.setStyleSheet(QtCore.QLatin1String(style_sheet_file.readAll()))

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(0)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFocusPolicy(QtCore.Qt.NoFocus)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.layout().addWidget(scroll_area)

        main_widget = QtWidgets.QWidget()
        main_widget.setObjectName('InterpolateIt')
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(5,5,5,5)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_widget.setLayout(main_layout)
        scroll_area.setWidget(main_widget)

        self.interp_layout = QtWidgets.QVBoxLayout()
        self.interp_layout.setContentsMargins(0,0,0,0)
        self.interp_layout.setSpacing(0)
        self.interp_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.addLayout(self.interp_layout)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0,0,0,0)
        button_layout.setAlignment(QtCore.Qt.AlignRight)
        main_layout.addLayout(button_layout)

        add_button = DT_ButtonThin('New..')
        button_layout.addWidget(add_button)

        new_widget = InterpolateWidget()
        new_widget.hideCloseButton()
        self.interp_layout.addWidget(new_widget)

        self._interp_widgets = []
        self._interp_widgets.append(new_widget)

        self._dock_widget = self._dock_name = None

        add_button.clicked.connect(self.add)

        self._callback_id = om.MEventMessage.addEventCallback('SceneOpened', self.clearAll)
        del_callback = partial(om.MMessage.removeCallback, self._callback_id)
        self.destroyed.connect(del_callback)

    #------------------------------------------------------------------------------------------#

    def add(self):
        new_widget = InterpolateWidget()
        self.interp_layout.addWidget(new_widget)
        self._interp_widgets.append(new_widget)
        #self.connect(new_widget, QtCore.SIGNAL('CLOSE'), self.remove)
        #
        new_widget.closeSig[str].connect(lambda *args: self.remove(new_widget))
        #
        new_widget.setFixedHeight(0)
        new_widget._animateExpand(True)
        self.setFixedHeight(500)


    def remove(self, interp_widget):
        #self.connect(interp_widget, QtCore.SIGNAL('DELETE'), self._delete)
        #
        interp_widget.deleteSig[str].connect(lambda *args: self._delete(interp_widget))
        #
        self._interp_widgets.remove(interp_widget)
        interp_widget._animateExpand(False)


    def _delete(self, interp_widget):
        self.interp_layout.removeWidget(interp_widget)
        interp_widget._animation = None
        interp_widget.deleteLater()

    #-----------------------------------------------------------------------------------------#

    def clearAll(self, *args):
        for interp_widget in self._interp_widgets:
            interp_widget.clearItems()

    #------------------------------------------------------------------------------------------#

    def connectDockWidget(self, dock_name, dock_widget):
        self._dock_widget = dock_widget
        self._dock_name   = dock_name


    def close(self):
        if self._dock_widget:
            mc.deleteUI(self._dock_name)
        else:
            QtWidgets.QWidget.close(self)
        self._dock_widget = self._dock_name = None

#--------------------------------------------------------------------------------------------------#

class InterpolateWidget(QtWidgets.QFrame):
    closeSig  = QtCore.Signal(str)
    deleteSig = QtCore.Signal(str)
    def __init__(self):
        QtWidgets.QFrame.__init__(self)
        self.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Raised)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(3,1,3,3)
        self.layout().setSpacing(0)
        self.setFixedHeight(150)

        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(QtWidgets.QVBoxLayout())
        main_widget.layout().setContentsMargins(2,2,2,2)
        main_widget.layout().setSpacing(5)
        main_widget.setFixedHeight(140)
        main_widget.setFixedWidth(290)

        graphics_scene = QtWidgets.QGraphicsScene()
        graphics_view  = QtWidgets.QGraphicsView()
        graphics_view.setScene(graphics_scene)
        graphics_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        graphics_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        graphics_view.setFocusPolicy(QtCore.Qt.NoFocus)
        graphics_view.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        graphics_view.setStyleSheet("QGraphicsView {border-style: none;}")
        self.layout().addWidget(graphics_view)
        self.main_widget_proxy = graphics_scene.addWidget(main_widget)
        main_widget.setParent(graphics_view)

        title_layout  = QtWidgets.QHBoxLayout()
        select_layout = QtWidgets.QHBoxLayout()
        button_layout = QtWidgets.QHBoxLayout()
        slider_layout = QtWidgets.QHBoxLayout()
        check_layout  = QtWidgets.QHBoxLayout()
        main_widget.layout().addLayout(title_layout)
        main_widget.layout().addLayout(select_layout)
        main_widget.layout().addLayout(button_layout)
        main_widget.layout().addLayout(slider_layout)
        main_widget.layout().addLayout(check_layout)

        self.title_line = DT_LineEdit()
        self.title_line.setPlaceholderMessage('Untitled')
        title_layout.addWidget(self.title_line)

        self.close_bttn = DT_CloseButton('X')
        self.close_bttn.setObjectName('roundedButton')
        title_layout.addWidget(self.close_bttn)

        store_items = DT_Button('Store Items')
        clear_items = DT_Button('Clear Items')

        select_layout.addSpacerItem(QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Expanding))
        select_layout.addWidget(store_items)
        select_layout.addWidget(clear_items)
        select_layout.addSpacerItem(QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Expanding))

        self.store_start_bttn = DT_ButtonThin('Store Start')
        self.reset_item_bttn  = DT_ButtonThin('Reset')
        self.store_end_bttn   = DT_ButtonThin('Store End')

        button_layout.addWidget(self.store_start_bttn)
        button_layout.addWidget(self.reset_item_bttn)
        button_layout.addWidget(self.store_end_bttn)

        self.start_lb = DT_Label('Start')
        self.slider = DT_Slider()
        self.slider.setRange(0, 49)
        self.end_lb = DT_Label('End')

        slider_layout.addWidget(self.start_lb)
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.end_lb)

        self.transforms_chbx = DT_Checkbox('Transform')
        self.attributes_chbx = DT_Checkbox('UD Attributes')
        self.transforms_chbx.setCheckState(QtCore.Qt.Checked)
        check_layout.addWidget(self.transforms_chbx)
        check_layout.addWidget(self.attributes_chbx)

        self.items = {}
        self.slider_down = False
        self._animation = None

        self.close_bttn.clicked.connect(self.closeWidget)

        store_items.clicked.connect(self.storeItems)
        clear_items.clicked.connect(self.clearItems)

        self.store_start_bttn.clicked.connect(self.storeStart)
        self.store_end_bttn.clicked.connect(self.storeEnd)
        self.reset_item_bttn.clicked.connect(self.resetAttributes)

        self.slider.valueChanged.connect(self.setLinearInterpolation)
        self.slider.valueChanged.connect(self.changeLabelGlow)

        self.slider.sliderReleased.connect(self._endSliderUndo)

        self.enableButtons(False)

    #------------------------------------------------------------------------------------------#

    def _animateExpand(self, value):
        opacity_anim = QtCore.QPropertyAnimation(self.main_widget_proxy, "opacity")
        opacity_anim.setStartValue(not(value));
        opacity_anim.setEndValue(value)
        opacity_anim.setDuration(200)
        opacity_anim_curve = QtCore.QEasingCurve()
        if value is True:
            opacity_anim_curve.setType(QtCore.QEasingCurve.InQuad)
        else:
            opacity_anim_curve.setType(QtCore.QEasingCurve.OutQuad)
        opacity_anim.setEasingCurve(opacity_anim_curve)

        size_anim = QtCore.QPropertyAnimation(self, "geometry")

        geometry = self.geometry()
        width    = geometry.width()
        x, y, _, _ = geometry.getCoords()

        size_start = QtCore.QRect(x, y, width, int(not(value)) * 150)
        size_end   = QtCore.QRect(x, y, width, value * 150)

        size_anim.setStartValue(size_start)
        size_anim.setEndValue(size_end)
        size_anim.setDuration(300)

        size_anim_curve = QtCore.QEasingCurve()
        if value:
            size_anim_curve.setType(QtCore.QEasingCurve.InQuad)
        else:
            size_anim_curve.setType(QtCore.QEasingCurve.OutQuad)
        size_anim.setEasingCurve(size_anim_curve)

        self._animation = QtCore.QSequentialAnimationGroup()
        if value:
            self.main_widget_proxy.setOpacity(0)
            self._animation.addAnimation(size_anim)
            self._animation.addAnimation(opacity_anim)
        else:
            self.main_widget_proxy.setOpacity(1)
            self._animation.addAnimation(opacity_anim)
            self._animation.addAnimation(size_anim)

        size_anim.valueChanged.connect(self._forceResize)
        self._animation.finished.connect(self._animation.clear)

        if not value:
            self._animation.finished.connect(self.deleteWidget)
        self._animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)


    def _forceResize(self, new_height):
        self.setFixedHeight(new_height.height()) #.toRect()

    #------------------------------------------------------------------------------------------#

    def _startSliderUndo(self):
        pm.undoInfo(openChunk=True)


    def _endSliderUndo(self):
        pm.undoInfo(closeChunk=True)
        self.slider_down = False

    #------------------------------------------------------------------------------------------#

    def storeItems(self):
        selection = pm.ls(sl=True, fl=True)
        if not selection:
            return
        #
        fillText = u','.join([i.name() for i in selection])
        self.title_line.setPlaceholderMessage(fillText)
        #
        self.items = {}
        for node in selection:
            self.items[node.name()] = {NODE:node, START:{}, END:{}, CACHE:{}}

        self.enableButtons(True)
        #

        #unicodeText = fillText.decode('gbk')
        #self.title_line.setText(fillText)




    def clearItems(self):
        self.items = {}
        self.enableButtons(False)
        self.slider.setValue(0)
        self.title_line.setPlaceholderMessage('Untitled')

    #------------------------------------------------------------------------------------------#

    def enableButtons(self, value):
        self.store_start_bttn.setEnabled(value)
        self.reset_item_bttn.setEnabled(value)
        self.store_end_bttn.setEnabled(value)
        self.transforms_chbx.setEnabled(value)
        self.attributes_chbx.setEnabled(value)
        self.slider.setEnabled(value)
        self.start_lb.setEnabled(value)
        self.end_lb.setEnabled(value)


    def hideCloseButton(self, value=True):
        self.close_bttn.setVisible(not(value))

    #------------------------------------------------------------------------------------------#

    def storeStart(self):
        if not self.items: return
        self._store(START, 0)
        self._cache()
        self.changeLabelGlow(0)


    def storeEnd(self):
        if not self.items: return
        self._store(END, 50)
        self._cache()
        self.changeLabelGlow(49)


    def _store(self, key, value):
        for name, item_dict in self.items.items():
            node = item_dict[NODE]

            if not node.exists():
                del(self.items[name])
                continue

            attrs = self.getAttributes(node)
            data = item_dict[key]
            for attr in attrs:
                data[attr] = node.attr(attr).get()

        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)


    def _cache(self):
        for item_dict in self.items.values():
            node  = item_dict[NODE]

            start = item_dict[START]
            end   = item_dict[END]
            if not start or not end:
                item_dict[CACHE] = None
                continue

            attrs = list(set(start.keys()) and set(end.keys()))

            cache = item_dict[CACHE] = {}
            for attr in attrs:
                start_attr = start[attr]
                end_attr   = end[attr]

                if start_attr == end_attr:
                    cache[attr] = None
                else:
                    cache_values = cache[attr] = []
                    interval     = float(end_attr - start_attr) / 49.0
                    for index in range(50):
                        cache_values.append((interval * index) + start_attr)

    #------------------------------------------------------------------------------------------#

    def getAttributes(self, node):
        attrs = []
        if self.transforms_chbx.isChecked():
            for transform in 'trs':
                for axis in 'xyz':
                    channel = '%s%s' %(transform, axis)
                    if node.attr(channel).isLocked(): continue
                    attrs.append(channel)

        if self.attributes_chbx.isChecked():
            for attr in node.listAttr(ud=True):
                if attr.type() not in ('double', 'int'): continue
                if attr.isLocked(): continue

                attrs.append(attr.name().split('.')[-1])

        return attrs


    @undo_pm
    def resetAttributes(self, *args):
        if not self.items:
            return

        for name, item_dict in self.items.items():
            node = item_dict[NODE]

            if not node.exists():
                del(self.items[name])
                continue

            attrs = self.getAttributes(node)

            for attr in attrs:
                default_value = pm.attributeQuery(attr, node=node, ld=True)[0]
                node.attr(attr).set(default_value)

    #------------------------------------------------------------------------------------------#

    def setLinearInterpolation(self, value):
        if not self.items: return

        if not self.slider_down:
            self._startSliderUndo()
            self.slider_down = True

        for name, item_dict in self.items.items():
            node  = item_dict[NODE]
            start = item_dict[START]

            if not node.exists():
                del(self.items[name])
                continue

            if not start or not item_dict[END]: continue

            cache = item_dict[CACHE]

            for attr in cache.keys():
                if cache[attr] == None: continue
                pm.setAttr(node.attr(attr), cache[attr][value])


    def changeLabelGlow(self, value):
        glow_value = int(float(value) / self.slider.maximum() * 100)
        self.start_lb.setGlowValue(100 - glow_value)
        self.end_lb.setGlowValue(glow_value)


    def closeWidget(self):
        #self.emit(QtCore.SIGNAL('CLOSE'), self)
        self.closeSig.emit('CLOSE')

    def deleteWidget(self):
        #self.emit(QtCore.SIGNAL('DELETE'), self)
        self.deleteSig.emit('DELETE')

#--------------------------------------------------------------------------------------------------#

dialog = None

def create():
    global dialog
    if dialog is None:
        dialog = InterpolateIt()
        dialog.show()

def delete():
    global dialog
    if dialog:
        dialog.close()
        dialog = None



class Base(object):
    _glow_pens = {}
    for index in range(1, 11):
        _glow_pens[index] = [QtGui.QPen(QtGui.QColor(0, 255, 0, 12   * index), 1, QtCore.Qt.SolidLine),
                             QtGui.QPen(QtGui.QColor(0, 255, 0,  5   * index), 3, QtCore.Qt.SolidLine),
                             QtGui.QPen(QtGui.QColor(0, 255, 0,  2   * index), 5, QtCore.Qt.SolidLine),
                             QtGui.QPen(QtGui.QColor(0, 255, 0, 25.5 * index), 1, QtCore.Qt.SolidLine)]

    _pens_text   = QtGui.QPen(QtGui.QColor(202, 207, 210), 1, QtCore.Qt.SolidLine)
    _pens_shadow = QtGui.QPen(QtGui.QColor(  9,  10,  12), 1, QtCore.Qt.SolidLine)
    _pens_border = QtGui.QPen(QtGui.QColor(  9,  10,  12), 2, QtCore.Qt.SolidLine)
    _pens_clear  = QtGui.QPen(QtGui.QColor(  0,  0, 0, 0), 1, QtCore.Qt.SolidLine)

    _pens_text_disabled   = QtGui.QPen(QtGui.QColor(102, 107, 110), 1, QtCore.Qt.SolidLine)
    _pens_shadow_disabled = QtGui.QPen(QtGui.QColor(  0,   0,   0), 1, QtCore.Qt.SolidLine)

    _brush_clear  = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
    _brush_border = QtGui.QBrush(QtGui.QColor( 9, 10, 12))

    def __init__(self):
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setFamily("Calibri")
        self.setFont(font)

        self._hover = False
        self._glow_index = 0
        self._anim_timer = QtCore.QTimer()
        self._anim_timer.timeout.connect(self._animateGlow)

    #-----------------------------------------------------------------------------------------#

    def _animateGlow(self):
        if self._hover:
            if self._glow_index >= 10:
                self._glow_index = 10
                self._anim_timer.stop()
            else:
                self._glow_index += 1

        else:
            if self._glow_index <= 0:
                self._glow_index = 0
                self._anim_timer.stop()
            else:
                self._glow_index -= 1

        utils.executeDeferred(self.update)

    #-----------------------------------------------------------------------------------------#

    def enterEvent(self, event):
        super(self.__class__, self).enterEvent(event)

        if not self.isEnabled(): return

        self._hover = True
        self._startAnim()


    def leaveEvent(self, event):
        super(self.__class__, self).leaveEvent(event)

        if not self.isEnabled(): return

        self._hover = False
        self._startAnim()


    def _startAnim(self):
        if self._anim_timer.isActive():
            return

        self._anim_timer.start(20)

NORMAL, DOWN, DISABLED = 1, 2, 3
INNER, OUTER = 1, 2


class DT_Button(QtWidgets.QPushButton, Base):
    _gradient = {NORMAL:{}, DOWN:{}, DISABLED:{}}

    inner_gradient = QtGui.QLinearGradient(0, 3, 0, 24)
    inner_gradient.setColorAt(0, QtGui.QColor(53, 57, 60))
    inner_gradient.setColorAt(1, QtGui.QColor(33, 34, 36))
    _gradient[NORMAL][INNER] = QtGui.QBrush(inner_gradient)

    outer_gradient = QtGui.QLinearGradient(0, 2, 0, 25)
    outer_gradient.setColorAt(0, QtGui.QColor(69, 73, 76))
    outer_gradient.setColorAt(1, QtGui.QColor(17, 18, 20))
    _gradient[NORMAL][OUTER] = QtGui.QBrush(outer_gradient)

    inner_gradient_down = QtGui.QLinearGradient(0, 3, 0, 24)
    inner_gradient_down.setColorAt(0, QtGui.QColor(20, 21, 23))
    inner_gradient_down.setColorAt(1, QtGui.QColor(48, 49, 51))
    _gradient[DOWN][INNER] = QtGui.QBrush(inner_gradient_down)

    outer_gradient_down = QtGui.QLinearGradient(0, 2, 0, 25)
    outer_gradient_down.setColorAt(0, QtGui.QColor(36, 37, 39))
    outer_gradient_down.setColorAt(1, QtGui.QColor(32, 33, 35))
    _gradient[DOWN][OUTER] = QtGui.QBrush(outer_gradient_down)

    inner_gradient_disabled = QtGui.QLinearGradient(0, 3, 0, 24)
    inner_gradient_disabled.setColorAt(0, QtGui.QColor(33, 37, 40))
    inner_gradient_disabled.setColorAt(1, QtGui.QColor(13, 14, 16))
    _gradient[DISABLED][INNER] = QtGui.QBrush(inner_gradient_disabled)

    outer_gradient_disabled = QtGui.QLinearGradient(0, 2, 0, 25)
    outer_gradient_disabled.setColorAt(0, QtGui.QColor(49, 53, 56))
    outer_gradient_disabled.setColorAt(1, QtGui.QColor( 9, 10, 12))
    _gradient[DISABLED][OUTER] = QtGui.QBrush(outer_gradient_disabled)


    def __init__(self, *args, **kwargs):
        QtWidgets.QPushButton.__init__(self, *args, **kwargs)
        Base.__init__(self)
        self.setFixedHeight(27)

        self._radius = 5

        self.font_metrics = QtGui.QFontMetrics(self.font())



    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        option  = QtWidgets.QStyleOption()
        option.initFrom(self)

        x = option.rect.x()
        y = option.rect.y()
        height = option.rect.height() - 1
        width  = option.rect.width()  - 1

        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        radius = self._radius

        gradient = self._gradient[NORMAL]
        offset = 0
        if self.isDown():
            gradient = self._gradient[DOWN]
            offset = 1
        elif not self.isEnabled():
            gradient = self._gradient[DISABLED]

        painter.setBrush(self._brush_border)
        painter.setPen(self._pens_border)
        painter.drawRoundedRect(QtCore.QRect(x+1, y+1, width-1, height-1), radius, radius)

        painter.setPen(self._pens_clear)

        painter.setBrush(gradient[OUTER])
        painter.drawRoundedRect(QtCore.QRect(x+2, y+2, width-3, height-3), radius, radius)

        painter.setBrush(gradient[INNER])
        painter.drawRoundedRect(QtCore.QRect(x+3, y+3, width-5, height-5), radius-1, radius-1)

        painter.setBrush(self._brush_clear)

        # draw text
        #
        text = self.text()
        font = self.font()

        text_width  = self.font_metrics.width(text)
        text_height = font.pointSize()

        text_path = QtGui.QPainterPath()
        text_path.addText((width-text_width)/2, height-((height-text_height)/2) - 1 + offset, font, text)

        glow_index = self._glow_index
        glow_pens  = self._glow_pens

        alignment = (QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        if self.isEnabled():
            painter.setPen(self._pens_shadow)
            painter.drawPath(text_path)

            painter.setPen(self._pens_text)
            painter.drawText(x, y+offset, width, height, alignment, text)

            if glow_index > 0:
                for index in range(3):
                    painter.setPen(glow_pens[glow_index][index])
                    painter.drawPath(text_path)

                painter.setPen(glow_pens[glow_index][3])
                painter.drawText(x, y+offset, width, height, alignment, text)

        else:
            painter.setPen(self._pens_shadow_disabled)
            painter.drawPath(text_path)

            painter.setPen(self._pens_text_disabled)
            painter.drawText(x, y+offset, width, height, alignment, text)

class DT_ButtonThin(DT_Button):
    def __init__(self, *args, **kwargs):
        DT_Button.__init__(self, *args, **kwargs)
        self.setFixedHeight(22)
        self._radius = 10

class DT_CloseButton(DT_Button):
    def __init__(self, *args, **kwargs):
        DT_Button.__init__(self, *args, **kwargs)
        self._radius = 10
        self.setFixedHeight(20)
        self.setFixedWidth(20)


    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        option  = QtWidgets.QStyleOption()
        option.initFrom(self)

        x = option.rect.x()
        y = option.rect.y()
        height = option.rect.height() - 1
        width  = option.rect.width()  - 1

        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        radius = self._radius

        gradient = self._gradient[NORMAL]
        offset = 0
        if self.isDown():
            gradient = self._gradient[DOWN]
            offset = 1
        elif not self.isEnabled():
            gradient = self._gradient[DISABLED]

        painter.setPen(self._pens_border)
        painter.drawEllipse(x+1, y+1, width-1, height-1)

        painter.setPen(self._pens_clear)
        painter.setBrush(gradient[OUTER])
        painter.drawEllipse(x+2, y+2, width-3, height-2)

        painter.setBrush(gradient[INNER])
        painter.drawEllipse(x+3, y+3, width-5, height-4)

        painter.setBrush(self._brush_clear)

        line_path = QtGui.QPainterPath()
        line_path.moveTo(x+8, y+8)
        line_path.lineTo(x+12, x+12)
        line_path.moveTo(x+12,  y+8)
        line_path.lineTo( x+8, y+12)

        painter.setPen(self._pens_border)
        painter.drawPath(line_path)

        glow_index = self._glow_index
        glow_pens  = self._glow_pens

        if glow_index > 0:
            for index in range(3):
                painter.setPen(glow_pens[glow_index][index])
                painter.drawPath(line_path)

            painter.setPen(glow_pens[glow_index][3])
            painter.drawPath(line_path)

class DT_Checkbox(QtWidgets.QCheckBox, Base):
    _glow_brushes = {}
    for index in range(1, 11):
        _glow_brushes[index] = [QtGui.QBrush(QtGui.QColor(0, 255, 0, 1    * index)),
                                QtGui.QBrush(QtGui.QColor(0, 255, 0, 3    * index)),
                                QtGui.QBrush(QtGui.QColor(0, 255, 0, 15   * index)),
                                QtGui.QBrush(QtGui.QColor(0, 255, 0, 25.5 * index))]

    _disabled_glow_brushes = {}
    for index in range(1, 11):
        _disabled_glow_brushes[index] = [QtGui.QBrush(QtGui.QColor(125,125,125, 1    * index)),
                                         QtGui.QBrush(QtGui.QColor(125,125,125, 3    * index)),
                                         QtGui.QBrush(QtGui.QColor(125,125,125, 15   * index)),
                                         QtGui.QBrush(QtGui.QColor(125,125,125, 25.5 * index))]


    def __init__(self, *args, **kwargs):
        QtWidgets.QCheckBox.__init__(self, *args, **kwargs)
        Base.__init__(self)



    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        option  = QtWidgets.QStyleOption()
        option.initFrom(self)

        x = option.rect.x()
        y = option.rect.y()
        height = option.rect.height() - 1
        width  = option.rect.width()  - 1

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)

        font = self.font()
        text = self.text()

        alignment = (QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        painter.setPen(self._pens_border)
        painter.setBrush(self._brush_border)
        painter.drawRoundedRect(QtCore.QRect(x+2, y+2, 13, 13), 3, 3)

        if self.isEnabled():
            painter.setPen(self._pens_shadow)
            painter.drawText(21, y+2, width, height, alignment, text)

            painter.setPen(self._pens_text)
            painter.drawText(20, y+1, width, height, alignment, text)

        else:
            painter.setPen(self._pens_shadow_disabled)
            painter.drawText(21, y+2, width, height, alignment, text)

            painter.setPen(self._pens_text_disabled)
            painter.drawText(20, y+1, width, height, alignment, text)

        painter.setPen(self._pens_clear)

        if self.isEnabled():
            glow_brushes =  self._glow_brushes
        else:
            glow_brushes =  self._disabled_glow_brushes

        if self.checkState():
            for index, pos, size, corner in zip(range(4), (2,3,4,5), (13,11,9,7), (4,3,3,2)):
                painter.setBrush(glow_brushes[10][index])
                painter.drawRoundedRect(QtCore.QRect(x+pos, y+pos, size, size), corner, corner)

        glow_index   = self._glow_index
        if glow_index > 0:
            for index, pos, size, corner in zip(range(4), (3,4,5,6), (11,9,7,5), (3,3,2,2)):
                painter.setBrush(glow_brushes[glow_index][index])
                painter.drawRoundedRect(QtCore.QRect(x+pos, y+pos, size, size), corner, corner)

class DT_Label(QtWidgets.QLabel):
    _glow_pens = Base._glow_pens

    _pens_text   = Base._pens_text
    _pens_shadow = Base._pens_shadow

    _pens_text_disabled   = Base._pens_text_disabled
    _pens_shadow_disabled = Base._pens_shadow_disabled


    def __init__(self, *args, **kwargs):
        QtWidgets.QLabel.__init__(self, *args, **kwargs)

        font = QtGui.QFont()
        font.setPointSize(8)
        font.setFamily("Calibri")
        self.setFont(font)

        self.setMargin(3)
        self._glow_index = 0



    def setGlowValue(self, value):
        self._glow_index = min(max(value/10, 0), 10)
        utils.executeDeferred(self.update)


    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        option  = QtWidgets.QStyleOption()
        option.initFrom(self)

        x = option.rect.x()
        y = option.rect.y()
        height = option.rect.height() - 1
        width  = option.rect.width()  - 1

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)

        text = self.text()
        if text == '': return

        font = self.font()
        font_metrics = QtGui.QFontMetrics(font)
        text_width  = font_metrics.width(text)
        text_height = font.pointSize()

        text_path = QtGui.QPainterPath()
        text_path.addText((width-text_width)/2, height-((height-text_height)/2) - 1, font, text)

        alignment = (QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        if self.isEnabled():
            pens_text   = self._pens_text
            pens_shadow = self._pens_shadow
        else:
            pens_text   = self._pens_text_disabled
            pens_shadow = self._pens_shadow_disabled

        painter.setPen(pens_shadow)
        painter.drawPath(text_path)
        painter.setPen(pens_text)
        painter.drawText(x, y, width, height, alignment, text)

        glow_index = self._glow_index
        glow_pens  = self._glow_pens

        if glow_index > 0 and self.isEnabled():
            for index in range(3):
                painter.setPen(glow_pens[glow_index][index])
                painter.drawPath(text_path)

            painter.setPen(glow_pens[glow_index][3])
            painter.drawText(x, y, width, height, alignment, text)

class DT_LineEdit(QtWidgets.QLineEdit):
    _glow_pens = Base._glow_pens

    _pens_text   = Base._pens_text
    _pens_shadow = Base._pens_shadow
    _pens_border = Base._pens_border
    _pens_clear  = Base._pens_clear

    _brush_clear = Base._brush_clear

    _pens_placeholder = QtGui.QPen(QtGui.QColor(202, 207, 210, 127), 1, QtCore.Qt.SolidLine)

    def __init__(self, *args, **kwargs):
        QtWidgets.QLineEdit.__init__(self, *args, **kwargs)

        font = QtGui.QFont()
        font.setPixelSize(16)
        self.setFont(font)
        self.font_metrics = QtGui.QFontMetrics(font)
        self.setFixedHeight(self.font_metrics.height() + 7)

        self._placeholder_message = ''

        self._text_glow = {}
        self._previous_text = ''

        text = self.text()
        if text: self.setText(text)

        self._anim_timer = QtCore.QTimer()
        self._anim_timer.timeout.connect(self._animateText)


    def setText(self, *args):
        QtWidgets.QLineEdit.setText(self, *args)
        self._text_glow = {}
        for index in range(len(text)):
            self._text_glow[index] = 0

    def setPlaceholderMessage(self, text):
        self._placeholder_message = str(text)



    def keyPressEvent(self, *args):
        QtWidgets.QLineEdit.keyPressEvent(self, *args)
        text = self.text()

        if text == self._previous_text: return

        len_text = len(text)
        if len_text > len(self._previous_text):
            self._anim_timer.start(30)
            self._text_glow[len_text-1] = 0
            self._text_glow[self.cursorPosition()-1] = 10

        elif len(self._text_glow.keys()) == 0:
            self._anim_timer.stop()

        self._previous_text = text



    def _animateText(self):
        stop_animating = True
        for key, value in self._text_glow.items():
            if value > 0:
                stop_animating = False
                self._text_glow[key] = value - 1

        if stop_animating:
            self._anim_timer.stop()

        utils.executeDeferred(self.update)

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        option  = QtWidgets.QStyleOptionFrame()
        self.initStyleOption(option)

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)

        contents = self.style().subElementRect(QtWidgets.QStyle.SE_LineEditContents, option, self)
        contents.setLeft(contents.left() + 2)
        contents.setRight(contents.right() - 2)
        alignment = (QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        text = self.text()
        font = self.font()
        font_metrics = self.font_metrics

        if not text:
            painter.setPen(self._pens_placeholder)
            painter.drawText(contents, alignment, self._placeholder_message)

        glow_pens  = self._glow_pens

        selected = self.hasSelectedText()
        if selected:
            selection = self.selectedText()
            selection_start = self.selectionStart()
            selection_end = selection_start + len(selection)

        left_edge = contents.left()
        for index, letter in enumerate(text):
            text_width = font_metrics.width(text[0:index])
            contents.setLeft(left_edge + text_width)

            x, y, width, height = contents.getRect()

            painter.setPen(self._pens_shadow)
            painter.drawText(x+1, y+1, width, height, alignment, letter)
            painter.setPen(self._pens_text)
            painter.drawText(contents, alignment, letter)

            glow_index = self._text_glow[index]
            if selected and (index >= selection_start and index < selection_end):
                glow_index = 10

            if glow_index > 0:
                text_path = QtGui.QPainterPath()
                text_path.addText(contents.left(), font.pixelSize() + 4, font, letter)

                for index in range(3):
                    painter.setPen(glow_pens[glow_index][index])
                    painter.drawPath(text_path)

                painter.setPen(glow_pens[glow_index][3])
                painter.drawText(contents, alignment, letter)


        if not self.hasFocus(): return

        contents.setLeft(left_edge)
        x, y, width, height = contents.getRect()

        painter.setPen(self._pens_text)

        cursor_pos = self.cursorPosition()
        text_width = font_metrics.width(text[0:cursor_pos])
        pos = x + text_width
        top = y + 1
        bttm = y + height - 1
        painter.drawLine(pos, top, pos, bttm)

        try:
            cursor_glow = self._text_glow[cursor_pos-1]
        except KeyError:
            return

        if cursor_glow > 0:
            for index in range(4):
                painter.setPen(glow_pens[cursor_glow][index])
                painter.drawLine(pos, top, pos, bttm)

class DT_Slider(QtWidgets.QSlider, Base):
    _glow_brushes = {}
    for index in range(1, 11):
        _glow_brushes[index] = [QtGui.QBrush(QtGui.QColor(0, 255, 0,    1 * index)),
                                QtGui.QBrush(QtGui.QColor(0, 255, 0,    3 * index)),
                                QtGui.QBrush(QtGui.QColor(0, 255, 0,    8 * index)),
                                QtGui.QBrush(QtGui.QColor(0, 255, 0, 25.5 * index)),
                                QtGui.QBrush(QtGui.QColor(0, 255, 0,   15 * index))]

    _pens_dark  = QtGui.QPen(QtGui.QColor( 0,  5,  9), 1, QtCore.Qt.SolidLine)
    _pens_light = QtGui.QPen(QtGui.QColor(16, 17, 19), 1, QtCore.Qt.SolidLine)

    _gradient_inner = QtGui.QLinearGradient(0, 9, 0, 15)
    _gradient_inner.setColorAt(0, QtGui.QColor(69, 73, 76))
    _gradient_inner.setColorAt(1, QtGui.QColor(17, 18, 20))

    _gradient_outer = QtGui.QLinearGradient(0, 9, 0, 15)
    _gradient_outer.setColorAt(0, QtGui.QColor(53, 57, 60))
    _gradient_outer.setColorAt(1, QtGui.QColor(33, 34, 36))


    def __init__(self, *args, **kwargs):
        QtWidgets.QSlider.__init__(self, *args, **kwargs)
        Base.__init__(self)

        self.setOrientation(QtCore.Qt.Horizontal)
        self.setFixedHeight(22)
        self.setMinimumWidth(50)

        self._track = False
        self._tracking_points = {}

        self._anim_follow_timer = QtCore.QTimer()
        self._anim_follow_timer.timeout.connect(self._removeTrackingPoints)

        self.valueChanged.connect(self._trackChanges)
        self._updateTracking()


    def setRange(self, *args, **kwargs):
        QtWidgets.QSlider.setRange(self, *args, **kwargs)
        self._updateTracking()

    def setMinimum(self, *args, **kwargs):
        QtWidgets.QSlider.setMinimum(self, *args, **kwargs)
        self._updateTracking()

    def setMaximum(self, *args, **kwargs):
        QtWidgets.QSlider.setMaximum(self, *args, **kwargs)
        self._updateTracking()

    def _updateTracking(self):
        self._tracking_points = [0] * (abs(self.maximum() - self.minimum()) + 1)


    def setValue(self, *args, **kwargs):
        QtWidgets.QSlider.setValue(self, *args, **kwargs)
        for index in range(len(self._tracking_points)):
            self._tracking_points[index] = 0


    def mouseMoveEvent(self, event):
        QtWidgets.QSlider.mouseMoveEvent(self, event)

        if self._anim_follow_timer.isActive():
            return

        self._anim_follow_timer.start(30)


    def _trackChanges(self, value):
        self._track = True
        #value = value - self.minimum()
        self._tracking_points[value] = 10


    def _removeTrackingPoints(self):
        self._track = False
        for index, value in enumerate(self._tracking_points):
            if value > 0:
                self._tracking_points[index] -= 1
                self._track = True

        if self._track is False:
            self._anim_follow_timer.stop()

        utils.executeDeferred(self.update)



    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        option  = QtWidgets.QStyleOption()
        option.initFrom(self)

        x = option.rect.x()
        y = option.rect.y()
        height = option.rect.height() - 1
        width  = option.rect.width()  - 1

        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        painter.setPen(self._pens_shadow)
        painter.setBrush(self._brush_border)
        painter.drawRoundedRect(QtCore.QRect(x+1, y+1, width-1, height-1), 10, 10)

        mid_height = (height / 2) + 1
        painter.setPen(self._pens_dark)
        painter.drawLine(10, mid_height, width - 8, mid_height)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        painter.setPen(self._pens_light)
        painter.drawLine(10, mid_height, width - 8, mid_height)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        minimum = self.minimum()
        maximum = self.maximum()
        value_range = maximum - minimum
        value = self.value() - minimum

        increment = ((width - 20) / float(value_range))
        center = 10 + (increment * value)
        center_point = QtCore.QPoint(x + center, y + mid_height)

        painter.setPen(self._pens_clear)

        glow_index   = self._glow_index
        glow_brushes = self._glow_brushes

        if self._track is True:
            for index, track_value in enumerate(self._tracking_points):
                if track_value == 0: continue
                track_center = 10 + (increment * index)
                painter.setBrush(glow_brushes[track_value][4])
                painter.drawEllipse(QtCore.QPoint(track_center, mid_height), 7, 7)

        if glow_index > 0:
            for index, size in zip(range(4), range(10, 6, -1)):
                painter.setBrush(glow_brushes[glow_index][index])
                painter.drawEllipse(center_point, size, size)

        painter.setBrush(QtGui.QBrush(self._gradient_outer))
        painter.drawEllipse(center_point, 6, 6)

        painter.setBrush(QtGui.QBrush(self._gradient_inner))
        painter.drawEllipse(center_point, 5, 5)
