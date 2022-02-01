# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QColorDialog, QHBoxLayout, QPlainTextEdit,
                             QVBoxLayout, QMenu, QLabel, QSpinBox,
                             QRadioButton, QFormLayout, QGroupBox, QDialog,
                             QApplication, QLineEdit, QMessageBox, QStyle,
                             QPushButton, QFileDialog)
from PyQt6.QtGui import (QKeySequence, QShortcut, QImageReader, QImageWriter,
                         QColor, QFont, QPainter, QPixmap, QAction, QImage)
from PyQt6.QtCore import QFile, Qt, QThread, pyqtSignal, QPoint
from typing import Callable


class ProcessingThread(QThread):
    __slots__ = (
        "asciiCharacters",
        "image",
    )
    onResultReady = pyqtSignal(str)

    def __init__(self, onResultReady: Callable) -> None:
        super().__init__()

        self.asciiCharacters, self.image = [
            "@", "#", "$", "%", "?", "*", "+", ";", ":", ",", " "
        ], None
        self.onResultReady.connect(onResultReady)

    def start(self, image: QImage) -> None:
        self.image = image
        super().start()

    def run(self) -> None:
        self.onResultReady.emit("".join(
            (w + "\n") for w in ("".join(
                self.asciiCharacters[self.image.pixelColor(x, y).value() // 25]
                for x in range(self.image.width()))
                                 for y in range(self.image.height()))
            if w.strip()))


class MainWindow(QDialog):
    __slots__ = (
        "backgroundColor",
        "foregroundColor",
        "image",
    )

    def __init__(self) -> None:
        super().__init__()

        def changeColor(forBackground: bool = False) -> None:
            color = QColorDialog.getColor(
                (self.backgroundColor
                 if forBackground else self.foregroundColor),
                title=
                f"Select {'Background' if forBackground else 'Foreground'}",
                options=QColorDialog.ColorDialogOption.ShowAlphaChannel)
            if not color.isValid(): return

            (
                backgroundColorPicker
                if forBackground else foregroundColorPicker
            ).setStyleSheet(
                f"QLabel {{ color: transparent; background-color: rgba{color.getRgb()}; }}"
            )

            if forBackground: self.backgroundColor = color
            else: self.foregroundColor = color

            generatedArtWindow.setStyleSheet(
                f"QPlainTextEdit {{ background-color: rgba{self.backgroundColor.getRgb()}; color: rgba{self.foregroundColor.getRgb()}; border: none; }}"
            )

        def resultReady(result: str) -> None:
            (generatedArtWindow.show if generatedArtWindow.isHidden() else
             generatedArtWindow.activateWindow)()
            generatedArtWindow.setPlainText(result)
            self.setDisabled(False)

        def fromClipboard() -> None:
            self.image = app.clipboard().mimeData().imageData()

            if not self.image or self.image.isNull():
                self.image = None
            else:
                fileLine.setText("[Image from clipboard]")

        def fromFile() -> None:
            self.image = QFileDialog.getOpenFileName(
                filter=
                f"Image File ({'; '.join(f'*.{x.data().decode()}' for x in QImageReader.supportedImageFormats())})"
            )[0].strip()

            if self.image: fileLine.setText(self.image)

        def process() -> None:
            if not self.image: return

            self.setDisabled(True)

            image = QImage(self.image)

            return processingThread.start(
                image.scaled(
                    *((image.width() * 2 // divideBySpinBox.value(),
                       image.height() // divideBySpinBox.value())
                      if divideByRadioButton.isChecked() else
                      (image.width() * 2, image.height())
                      if keepOriginalDimensionsRadioButton.isChecked() else
                      (widthSpinBox.value() * 2, heightSpinBox.value())),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))

        self.image, layout, fileLine = None, QVBoxLayout(self), QLineEdit(
            readOnly=True,
            textChanged=lambda text: processButton.setDisabled(not text.strip(
            )))
        processButton, self.foregroundColor, dimensionsGroupBox = QPushButton(
            "Process", clicked=process,
            enabled=False), QColor(0, 0, 0), QGroupBox("Output dimensions")
        dimensionsGroupBoxLayout, divideByRadioButton, processingThread = QFormLayout(
            dimensionsGroupBox), QRadioButton(
                checked=True), ProcessingThread(resultReady)
        divideBySpinBox, divideByLayout, keepOriginalDimensionsRadioButton = QSpinBox(
            minimum=2), QHBoxLayout(), QRadioButton("Keep it all as-is")
        customDimensionsGroupBox, customDimensionsRadioButton, heightSpinBox = QGroupBox(
            "Custom dimensions"), QRadioButton(), QSpinBox(minimum=1,
                                                           maximum=999999999)
        widthSpinBox, customDimensionsGroupBoxLayout, backgroundColorPicker = QSpinBox(
            minimum=1,
            maximum=999999999), QFormLayout(customDimensionsGroupBox), QLabel(
                toolTip="Background color",
                frameShape=QLabel.Shape.StyledPanel,
                styleSheet=
                "QLabel { color: transparent; background-color: #FFFFFF; }")
        foregroundColorPicker, self.backgroundColor = QLabel(
            toolTip="Text color",
            frameShape=QLabel.Shape.StyledPanel,
            styleSheet=
            "QLabel { color: transparent; background-color: #000000; }"
        ), QColor(255, 255, 255)

        fileLine.addAction(
            QAction(app.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogOpenButton),
                    "",
                    fileLine,
                    triggered=fromFile,
                    toolTip="Browse"),
            QLineEdit.ActionPosition.TrailingPosition)
        backgroundColorPicker.mousePressEvent, foregroundColorPicker.mousePressEvent = lambda event: changeColor(
            True), lambda event: changeColor()
        QShortcut(QKeySequence("Ctrl+V"), self, fromClipboard)

        customDimensionsGroupBoxLayout.addRow("Width: ", widthSpinBox)
        customDimensionsGroupBoxLayout.addRow("Height: ", heightSpinBox)

        divideByLayout.addWidget(divideByRadioButton)
        divideByLayout.addWidget(QLabel("Divide by"))
        divideByLayout.addWidget(divideBySpinBox)
        divideByLayout.addStretch(-1)

        dimensionsGroupBoxLayout.addRow(divideByLayout)
        dimensionsGroupBoxLayout.addRow(keepOriginalDimensionsRadioButton)
        dimensionsGroupBoxLayout.addRow(customDimensionsRadioButton,
                                        customDimensionsGroupBox)

        layout.addWidget(fileLine)
        layout.addWidget(dimensionsGroupBox)
        layout.addWidget(backgroundColorPicker)
        layout.addWidget(foregroundColorPicker)
        layout.addWidget(processButton)

        self.setFixedSize(self.sizeHint())
        self.show()


def contextMenuRequested(pos: QPoint) -> None:
    menu = QMenu()

    saveAction, toggleVerticalScrollBarAction, toggleHorizontalScrollBarAction = QAction(
        "Save As",
        shortcut=QKeySequence(QKeySequence.StandardKey.Save)), QAction(
            "Hide or show vertical scroll bar"), QAction(
                "Hide or show horizontal scroll bar")

    menu.addAction(saveAction)
    menu.addSeparator()
    menu.addActions(
        [toggleVerticalScrollBarAction, toggleHorizontalScrollBarAction])

    action = menu.exec(generatedArtWindow.mapToGlobal(pos))
    if not action: return

    if action in {
            toggleVerticalScrollBarAction, toggleHorizontalScrollBarAction
    }:
        return (
            generatedArtWindow.setVerticalScrollBarPolicy
            if action == toggleVerticalScrollBarAction else
            generatedArtWindow.setHorizontalScrollBarPolicy
        )(Qt.ScrollBarPolicy.ScrollBarAsNeeded if (
            generatedArtWindow.verticalScrollBarPolicy if action ==
            toggleVerticalScrollBarAction else generatedArtWindow.
            horizontalScrollBarPolicy)() == Qt.ScrollBarPolicy.
          ScrollBarAlwaysOff else Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    saveGeneratedArt()


def saveGeneratedArt() -> None:
    file = QFileDialog.getSaveFileName(
        filter=
        f"Plain Text File (*.txt);; Image File ({'; '.join(f'*.{x.data().decode()}' for x in QImageWriter.supportedImageFormats())})"
    )
    if not file[0]: return

    if file[1].startswith("Plain "):
        file = QFile(file[0])

        if not file.open(QFile.OpenModeFlag.WriteOnly):
            return QMessageBox.critical(
                generatedArtWindow, "Error",
                f"Could not open the file: [{file.error()}] {file.errorString()}"
            )

        file.write(generatedArtWindow.toPlainText().encode("UTF-8"))

        if file.error() != QFile.FileError.NoError:
            QMessageBox.critical(
                generatedArtWindow, "Error",
                f"Could not write to file: [{file.error()}] {file.errorString()}"
            )
        else:
            file.close()
            QMessageBox.information(
                generatedArtWindow, "Success",
                f"Successfully saved to {file.fileName()}")

        return

    pixmap = QPixmap(generatedArtWindow.fontMetrics().size(
        0, generatedArtWindow.toPlainText()))
    painter = QPainter(pixmap)

    painter.fillRect(pixmap.rect(), mainWindow.backgroundColor)
    painter.setFont(generatedArtWindow.font())
    painter.setPen(mainWindow.foregroundColor)

    painter.drawText(pixmap.rect(), 0, generatedArtWindow.toPlainText())

    painter.end()

    if not pixmap.save(file[0], quality=100):
        return QMessageBox.critical(generatedArtWindow, "Error",
                                    f"Could not save to {file[0]}")

    QMessageBox.information(generatedArtWindow, "Success",
                            f"Successfully saved to {file[0]}")


app = QApplication([], applicationName="ASCII Art Generator")

mainWindow, generatedArtWindow = MainWindow(), QPlainTextEdit(
    windowTitle="Generated ASCII Art",
    readOnly=True,
    lineWrapMode=QPlainTextEdit.LineWrapMode.NoWrap,
    font=QFont("Consolas", 1),
    styleSheet="QPlainTextEdit { border: none; }",
    contextMenuPolicy=Qt.ContextMenuPolicy.CustomContextMenu,
    customContextMenuRequested=contextMenuRequested)
QShortcut(QKeySequence(QKeySequence.StandardKey.Save), generatedArtWindow,
          saveGeneratedArt)

app.exec()