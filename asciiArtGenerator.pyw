# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QDialog, QApplication, QLineEdit, QMessageBox,
                             QStyle, QVBoxLayout, QPushButton, QFileDialog)
from PyQt6.QtGui import QHideEvent, QKeySequence, QShortcut, QAction
from PyQt6.QtCore import QDir, QFile, QThread, pyqtSignal
from random import randint
from PIL import Image


class ImageThread(QThread):
    __slots__ = ("file", )
    onReady = pyqtSignal(str)

    def __init__(self, onReady: "function",
                 setDisabledFunction: "function") -> None:
        super().__init__(started=lambda: setDisabledFunction(True),
                         finished=lambda: setDisabledFunction(False))
        self.onReady.connect(onReady)
        self.file = ""

    def start(self, file: str) -> None:
        self.file = file
        return super().start()

    def run(self) -> None:
        try:
            image = Image.open(self.file)
        except BaseException as error:
            QMessageBox.critical(self, "Error",
                                 f"Error opening the file: {error}")
            return self.finished.emit()

        image, ASCII_CHARS = image.convert("L").resize(
            (image.width * 2, image.height)), [
                "@", "#", "$", "%", "?", "*", "+", ";", ":", ",", "."
            ]

        asciiStr = "".join(ASCII_CHARS[x // 25] for x in image.getdata())
        self.onReady.emit("\n".join(
            asciiStr[x:x + image.width]
            for x in range(0, len(asciiStr), image.width)))


class Main(QDialog):
    __slots__ = (
        "clipboardTempDir",
        "imageThread",
    )

    def __init__(self) -> None:
        super().__init__()

        def saveResult(result: str) -> None:
            file = QFileDialog.getSaveFileName(
                self, filter="Plain Text (*.txt)")[0].strip()
            if not file: return

            file = QFile(file)
            file.open(file.OpenModeFlag.WriteOnly)
            file.write(result.encode("UTF-8", "ignore"))

            QMessageBox.information(
                self, "Success", f"Successfully saved to {file.fileName()}")
            file.close()

        def pasteFromClipboard() -> None:
            clipboard = app.clipboard().mimeData()
            if not clipboard.hasImage(): return

            self.clipboardTempDir.mkpath(
                ".") if not self.clipboardTempDir.exists() else ...
            file = f"{QDir.tempPath()}/clipboardTemp/tempImage-{randint(100000, 999999)}.png"
            clipboard.imageData().save(file)

            processButton.setDisabled(False)
            imageFile.setText(file)

        def selectAnImage() -> None:
            file = QFileDialog.getOpenFileName(
                self, filter="Images (*.png; *.jpg)")[0].strip()
            if not file: return

            processButton.setDisabled(False)
            imageFile.setText(file)

        layout, imageFile, processButton = QVBoxLayout(self), QLineEdit(
            readOnly=True), QPushButton("Process",
                                        clicked=lambda: self.imageThread.start(
                                            imageFile.text().strip()),
                                        enabled=False)
        self.clipboardTempDir, self.imageThread = QDir(
            f"{QDir.tempPath()}/clipboardTemp"), ImageThread(
                saveResult, self.setDisabled)

        QShortcut(QKeySequence("Ctrl+V"), self, activated=pasteFromClipboard)
        imageFile.addAction(
            QAction(app.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogOpenButton),
                    "",
                    imageFile,
                    triggered=selectAnImage,
                    toolTip="Select An Image"),
            imageFile.ActionPosition.TrailingPosition)

        layout.addWidget(imageFile)
        layout.addWidget(processButton)

        self.setFixedHeight(self.sizeHint().height())
        self.show()

    def hideEvent(self, event: QHideEvent) -> None:
        self.clipboardTempDir.removeRecursively()


app = QApplication([], applicationName="ASCII Art Generator")
main = Main()
main.show()
app.exec()