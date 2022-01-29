# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QSpinBox,
                             QRadioButton, QFormLayout, QGroupBox, QDialog,
                             QApplication, QLineEdit, QMessageBox, QStyle,
                             QPushButton, QFileDialog)
from PyQt6.QtGui import (QKeySequence, QShortcut, QImageReader, QAction,
                         QImage)
from PyQt6.QtCore import QFile, Qt


class Main(QDialog):
    __slots__ = ("image", )

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

            if not keepOriginalDimensionsRadioButton.isChecked():
                image = image.scaled(
                    *((image.width() * multiplyBySpinBox.value(),
                       image.height() * multiplyBySpinBox.value())
                      if multiplyByRadioButton.isChecked() else
                      (image.width() // divideBySpinBox.value(),
                       image.height() // divideBySpinBox.value())
                      if divideByRadioButton.isChecked() else
                      (widthSpinBox.value(), heightSpinBox.value())),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)

            file = QFileDialog.getSaveFileName(
                filter="Plain Text File (*.txt)")[0].strip()

            if file:
                file = QFile(file)

                if not file.open(QFile.OpenModeFlag.WriteOnly):
                    QMessageBox.critical(
                        self, "Error",
                        f"Could not open the file: [{file.error()}] {file.errorString()}"
                    )
                else:
                    file.write("".join(
                        ("".join(
                            asciiCharacters[image.pixelColor(x, y).value() //
                                            25]
                            for x in range(image.width())) + "\n")
                        for y in range(image.height())).encode("UTF-8"))

                    if file.error() != QFile.FileError.NoError:
                        QMessageBox.critical(
                            self, "Error",
                            f"Could not write to file: [{file.error()}] {file.errorString()}"
                        )
                    else:
                        file.close()
                        QMessageBox.information(
                            self, "Success",
                            f"Successfully saved to {file.fileName()}")

            self.setDisabled(False)

        self.image, layout, fileLine = None, QVBoxLayout(self), QLineEdit(
            readOnly=True,
            textChanged=lambda text: processButton.setDisabled(not text.strip(
            )))
        processButton, asciiCharacters, dimensionsGroupBox = QPushButton(
            "Process", clicked=process, enabled=False), [
                "@", "#", "$", "%", "?", "*", "+", ";", ":", ",", "."
            ], QGroupBox("Output dimensions")
        dimensionsGroupBoxLayout, divideByRadioButton, multiplyByRadioButton = QFormLayout(
            dimensionsGroupBox), QRadioButton(checked=True), QRadioButton()
        divideBySpinBox, divideByLayout, keepOriginalDimensionsRadioButton = QSpinBox(
            minimum=2), QHBoxLayout(), QRadioButton()
        customDimensionsGroupBox, customDimensionsRadioButton, heightSpinBox = QGroupBox(
            "Custom dimensions"), QRadioButton(), QSpinBox(minimum=1,
                                                           maximum=999999999)
        widthSpinBox, customDimensionsGroupBoxLayout, multiplyByLayout = QSpinBox(
            minimum=1, maximum=999999999), QFormLayout(
                customDimensionsGroupBox), QHBoxLayout()
        multiplyBySpinBox = QSpinBox(minimum=2, maximum=999999999)

        fileLine.addAction(
            QAction(app.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogOpenButton),
                    "",
                    fileLine,
                    triggered=fromFile,
                    toolTip="Browse"),
            QLineEdit.ActionPosition.TrailingPosition)
        QShortcut(QKeySequence("Ctrl+V"), self, activated=fromClipboard)

        customDimensionsGroupBoxLayout.addRow("Width: ", widthSpinBox)
        customDimensionsGroupBoxLayout.addRow("Height: ", heightSpinBox)

        divideByLayout.addWidget(divideByRadioButton)
        divideByLayout.addWidget(QLabel("Divide by"))
        divideByLayout.addWidget(divideBySpinBox)
        divideByLayout.addStretch(-1)

        multiplyByLayout.addWidget(multiplyByRadioButton)
        multiplyByLayout.addWidget(QLabel("Multiply by"))
        multiplyByLayout.addWidget(multiplyBySpinBox)
        multiplyByLayout.addStretch(-1)

        dimensionsGroupBoxLayout.addRow(multiplyByLayout)
        dimensionsGroupBoxLayout.addRow(divideByLayout)
        dimensionsGroupBoxLayout.addRow(keepOriginalDimensionsRadioButton,
                                        QLabel("Keep original dimensions"))
        dimensionsGroupBoxLayout.addRow(customDimensionsRadioButton,
                                        customDimensionsGroupBox)

        layout.addWidget(fileLine)
        layout.addWidget(dimensionsGroupBox)
        layout.addWidget(processButton)

        self.setFixedSize(self.sizeHint())


app = QApplication([], applicationName="ASCII Art Generator")
main = Main()
main.show()
app.exec()