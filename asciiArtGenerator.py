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
        "useOriginalImage",
        "asciiCharacters",
        "originalImage",
        "image",
    )
    onResultReady = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

        self.useOriginalImage, self.asciiCharacters, self.originalImage = False, [
            "@", "#", "$", "%", "?", "*", "+", ";", ":", ",", " "
        ], None
        self.image = None

    def start(self,
              onResultReady: Callable,
              image: QImage,
              useOriginalImage: bool = False) -> None:
        try:
            self.onResultReady.disconnect()
        except TypeError:
            pass

        self.onResultReady.connect(onResultReady)

        self.image, self.useOriginalImage, self.originalImage = image.scaled(
            *((image.width() * 2 // mainWindow.divideBySpinBox.value(),
               image.height() // mainWindow.divideBySpinBox.value())
              if mainWindow.divideByRadioButton.isChecked() else
              (image.width() * 2, image.height())
              if mainWindow.keepOriginalDimensionsRadioButton.isChecked() else
              (mainWindow.widthSpinBox.value() * 2,
               mainWindow.heightSpinBox.value())),
            Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.
            SmoothTransformation), useOriginalImage, image

        super().start()

    def run(self) -> None:
        image = self.originalImage if self.useOriginalImage else self.image

        self.onResultReady.emit("".join(
            (w + "\n") for w in ("".join(
                self.asciiCharacters[image.pixelColor(x, y).value() // 25]
                for x in range(image.width()))
                                 for y in range(image.height())) if w.strip()))


class MainWindow(QDialog):
    __slots__ = (
        "keepOriginalDimensionsRadioButton",
        "divideByRadioButton",
        "backgroundColor",
        "divideBySpinBox",
        "foregroundColor",
        "heightSpinBox",
        "widthSpinBox",
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

            processingThread.start(resultReady, QImage(self.image))

        self.image, layout, fileLine = None, QVBoxLayout(self), QLineEdit(
            readOnly=True,
            textChanged=lambda text: processButton.setDisabled(not text.strip(
            )))
        processButton, self.foregroundColor, dimensionsGroupBox = QPushButton(
            "Process", clicked=process,
            enabled=False), QColor(0, 0, 0), QGroupBox("Output dimensions")
        dimensionsGroupBoxLayout, self.divideByRadioButton, self.backgroundColor = QFormLayout(
            dimensionsGroupBox), QRadioButton(checked=True), QColor(
                255, 255, 255)
        self.divideBySpinBox, divideByLayout, self.keepOriginalDimensionsRadioButton = QSpinBox(
            minimum=2), QHBoxLayout(), QRadioButton("Keep it all as-is")
        customDimensionsGroupBox, customDimensionsRadioButton, self.heightSpinBox = QGroupBox(
            "Custom dimensions"), QRadioButton(), QSpinBox(minimum=1,
                                                           maximum=999999999)
        self.widthSpinBox, customDimensionsGroupBoxLayout, backgroundColorPicker = QSpinBox(
            minimum=1,
            maximum=999999999), QFormLayout(customDimensionsGroupBox), QLabel(
                toolTip="Background color",
                frameShape=QLabel.Shape.StyledPanel,
                styleSheet=
                "QLabel { color: transparent; background-color: #FFFFFF; }")
        foregroundColorPicker = QLabel(
            toolTip="Text color",
            frameShape=QLabel.Shape.StyledPanel,
            styleSheet=
            "QLabel { color: transparent; background-color: #000000; }")

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

        customDimensionsGroupBoxLayout.addRow("Width: ", self.widthSpinBox)
        customDimensionsGroupBoxLayout.addRow("Height: ", self.heightSpinBox)

        divideByLayout.addWidget(self.divideByRadioButton)
        divideByLayout.addWidget(QLabel("Divide by"))
        divideByLayout.addWidget(self.divideBySpinBox)
        divideByLayout.addStretch(-1)

        dimensionsGroupBoxLayout.addRow(divideByLayout)
        dimensionsGroupBoxLayout.addRow(self.keepOriginalDimensionsRadioButton)
        dimensionsGroupBoxLayout.addRow(customDimensionsRadioButton,
                                        customDimensionsGroupBox)

        layout.addWidget(fileLine)
        layout.addWidget(dimensionsGroupBox)
        layout.addWidget(backgroundColorPicker)
        layout.addWidget(foregroundColorPicker)
        layout.addWidget(processButton)

        self.setFixedSize(self.sizeHint())
        self.show()


def coloredResultReady(result: str, file: str) -> None:
    pixmap = QPixmap(processingThread.originalImage.size())
    painter = QPainter(pixmap)

    painter.setFont(generatedArtWindow.font())

    for line, y in zip(result.splitlines(), range(pixmap.height())):
        for char, x in zip(line, range(pixmap.width())):
            painter.setPen(processingThread.originalImage.pixelColor(x, y))
            painter.drawText(x, y, char)

    painter.end()

    if not pixmap.save(file, quality=100):
        return QMessageBox.critical(generatedArtWindow, "Error",
                                    f"Could not save to {file}")

    QMessageBox.information(generatedArtWindow, "Success",
                            f"Successfully saved to {file}")


def contextMenuRequested(pos: QPoint) -> None:
    menu = QMenu()

    saveAction, toggleVerticalScrollBarAction, toggleHorizontalScrollBarAction = QAction(
        "Save as...",
        shortcut=QKeySequence(QKeySequence.StandardKey.Save)), QAction(
            "Hide or show vertical scroll bar"), QAction(
                "Hide or show horizontal scroll bar")
    saveWithOriginalColorsAction = QAction(
        "Save as an image with original colors")

    menu.addAction(saveAction)
    menu.addSeparator()
    menu.addActions(
        [toggleVerticalScrollBarAction, toggleHorizontalScrollBarAction])
    menu.addSeparator()
    menu.addAction(saveWithOriginalColorsAction)

    action = menu.exec(generatedArtWindow.mapToGlobal(pos))
    if not action: return

    if action in {
            saveAction, toggleVerticalScrollBarAction,
            toggleHorizontalScrollBarAction
    }:
        return (
            (generatedArtWindow.setVerticalScrollBarPolicy
             if action == toggleVerticalScrollBarAction else
             generatedArtWindow.setHorizontalScrollBarPolicy
             )(Qt.ScrollBarPolicy.ScrollBarAsNeeded if (
                 generatedArtWindow.verticalScrollBarPolicy if action ==
                 toggleVerticalScrollBarAction else generatedArtWindow.
                 horizontalScrollBarPolicy)() == Qt.ScrollBarPolicy.
               ScrollBarAlwaysOff else Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ) if action != saveAction else saveGeneratedArt()

    if QMessageBox.question(
            generatedArtWindow, "Attention",
            "<h3>Note</h3>Image may not look that good nor that accurate." +
            "<h3>Warning</h3>This could possibly be performance/resource heavy and the program might crash, do you want to continue?<br>"
    ) == QMessageBox.StandardButton.Yes:
        file = QFileDialog.getSaveFileName(
            filter=
            f"Image File ({'; '.join(f'*.{x.data().decode()}' for x in QImageWriter.supportedImageFormats())})"
        )[0]
        if not file: return

        processingThread.start(lambda result: coloredResultReady(result, file),
                               processingThread.originalImage, True)


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


app, processingThread = QApplication(
    [], applicationName="ASCII Art Generator"), ProcessingThread()

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