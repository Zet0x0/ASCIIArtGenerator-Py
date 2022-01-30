# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QSpinBox,
                             QRadioButton, QFormLayout, QGroupBox, QDialog,
                             QApplication, QLineEdit, QMessageBox, QStyle,
                             QPushButton, QFileDialog)
from PyQt6.QtGui import (QKeySequence, QShortcut, QImageReader, QAction,
                         QImage)
from PyQt6.QtCore import QFile, Qt, QThread, pyqtSignal


class ProcessingThread(QThread):
    __slots__ = (
        "asciiCharacters",
        "image",
    )
    onResultReady = pyqtSignal(bytes)

    def __init__(self) -> None:
        super().__init__()

        self.asciiCharacters, self.image = [
            "@", "#", "$", "%", "?", "*", "+", ";", ":", ",", "."
        ], None

    def start(self, image: QImage) -> None:
        self.image = image
        super().start()

    def run(self) -> None:
        self.onResultReady.emit("".join(
            ("".join(
                self.asciiCharacters[self.image.pixelColor(x, y).value() // 25]
                for x in range(self.image.width())) + "\n")
            for y in range(self.image.height())).encode("UTF-8"))


class Main(QDialog):
    __slots__ = (
        "image",
        "file",
    )

    def __init__(self) -> None:
        super().__init__()

        def fromClipboard() -> None:
            self.image = app.clipboard().mimeData().imageData()

            if self.image.isNull():
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

            image = image.scaled(
                *((image.width() * 2 // divideBySpinBox.value(),
                   image.height() // divideBySpinBox.value())
                  if divideByRadioButton.isChecked() else
                  (image.width() * 2, image.height())
                  if keepOriginalDimensionsRadioButton.isChecked() else
                  (widthSpinBox.value() * 2, heightSpinBox.value())),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation)

            file = QFileDialog.getSaveFileName(
                filter="Plain Text File (*.txt)")[0].strip()

            if file:
                self.file = QFile(file)

                if not self.file.open(QFile.OpenModeFlag.WriteOnly):
                    QMessageBox.critical(
                        self, "Error",
                        f"Could not open the file: [{self.file.error()}] {self.file.errorString()}"
                    )
                else:
                    processingThread.start(image)
            else:
                self.setDisabled(False)

        self.image, layout, fileLine = None, QVBoxLayout(self), QLineEdit(
            readOnly=True,
            textChanged=lambda text: processButton.setDisabled(not text.strip(
            )))
        processButton, self.file, dimensionsGroupBox = QPushButton(
            "Process", clicked=process,
            enabled=False), None, QGroupBox("Output dimensions")
        dimensionsGroupBoxLayout, divideByRadioButton, processingThread = QFormLayout(
            dimensionsGroupBox), QRadioButton(
                checked=True), ProcessingThread()
        divideBySpinBox, divideByLayout, keepOriginalDimensionsRadioButton = QSpinBox(
            minimum=2), QHBoxLayout(), QRadioButton("Keep it all as-is")
        customDimensionsGroupBox, customDimensionsRadioButton, heightSpinBox = QGroupBox(
            "Custom dimensions"), QRadioButton(), QSpinBox(minimum=1,
                                                           maximum=999999999)
        widthSpinBox, customDimensionsGroupBoxLayout = QSpinBox(
            minimum=1,
            maximum=999999999), QFormLayout(customDimensionsGroupBox)

        fileLine.addAction(
            QAction(app.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogOpenButton),
                    "",
                    fileLine,
                    triggered=fromFile,
                    toolTip="Browse"),
            QLineEdit.ActionPosition.TrailingPosition)
        QShortcut(QKeySequence("Ctrl+V"), self, activated=fromClipboard)
        processingThread.onResultReady.connect(self.resultReady)

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
        layout.addWidget(processButton)

        self.setFixedSize(self.sizeHint())

    def resultReady(self, result: bytes) -> None:
        self.file.write(result)

        if self.file.error() != QFile.FileError.NoError:
            QMessageBox.critical(
                self, "Error",
                f"Could not write to file: [{self.file.error()}] {self.file.errorString()}"
            )
        else:
            self.file.close()
            QMessageBox.information(
                self, "Success",
                f"Successfully saved to {self.file.fileName()}")

        self.setDisabled(False)


app = QApplication([], applicationName="ASCII Art Generator")
main = Main()
main.show()
app.exec()