from PyQt5.QtWidgets import QApplication, QWidget, QListWidget, QHBoxLayout, QVBoxLayout, QListWidgetItem, QPushButton, QLineEdit, QGroupBox, QAbstractItemView
from PyQt5.QtWidgets import QLabel, QComboBox
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal
import sys
import glob
import os
import os.path
import html2txt
import re
import copy

class ImageViewer(QGraphicsView):
    factor = 2.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )
        self.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.setBackgroundRole(QPalette.NoRole)

        scene = QGraphicsScene()
        self.setScene(scene)

        self._pixmap_item = QGraphicsPixmapItem()
        scene.addItem(self._pixmap_item)

    def load_image(self, fileName):
        pixmap = QPixmap(fileName)
        if pixmap.isNull():
            return False
        self._pixmap_item.setPixmap(pixmap)
        return True

    def zoomIn(self):
        self.zoom(self.factor)

    def zoomOut(self):
        self.zoom(1 / self.factor)

    def zoom(self, f):
        self.scale(f, f)

    def resetZoom(self):
        self.resetTransform()

    def fitToWindow(self):
        self.fitInView(self.sceneRect(), QtCore.Qt.KeepAspectRatio)

class Dialog(QDialog):

    accepted = pyqtSignal(dict)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.url = QLineEdit()
        self.title = QLineEdit()
        self.word1 = QLineEdit()
        self.word2 = QLineEdit()
        self.word3 = QLineEdit()
        self.word4 = QLineEdit()
        self.word5 = QLineEdit()
        self.word6 = QLineEdit()

        btn = QPushButton('OK')
        btn.clicked.connect(self.ok_pressed)

        form = QFormLayout(self)
        form.addRow('url', self.url)
        form.addRow('title', self.title)
        form.addRow('word1', self.word1)
        form.addRow('word2', self.word2)
        form.addRow('word3', self.word3)
        form.addRow('word4', self.word4)
        form.addRow('word5', self.word5)
        form.addRow('word6', self.word6)
        form.addRow(btn)

    def ok_pressed(self):
        values = {'Url': self.url.text(),
                  'Title': self.title.text(),
                  'Word1': self.word1.text(),
                  'Word2': self.word2.text(),
                  'Word3': self.word3.text(),
                  'Word4': self.word4.text(),
                  'Word5': self.word5.text(),
                  'Word6': self.word6.text()}
        self.accepted.emit(values)
        self.accept()

class Window(QWidget):
    def __init__(self):
        super().__init__()

         # image
        self.imgView = ImageViewer()
        self.imgView.setFrameShape(QFrame.NoFrame)

        # text
        self.textLabel = QLabel("", self)
        self.textLabel.setWordWrap(True)

        # article choice
        self.comboArticles = QComboBox(self)
        self.init()
        self.comboArticles.currentTextChanged.connect(self.onArticleChange)
        
        # buttons
        self.nextButton = QPushButton('Next', self)
        self.nextButton.setShortcut("Space")
        self.nextButton.clicked.connect(self.onNext)

        self.prevButton = QPushButton('Prev', self)
        self.prevButton.setShortcut("Backspace")
        self.prevButton.clicked.connect(self.onPrev)

        self.endButton = QPushButton('End', self)
        self.endButton.clicked.connect(self.onEnd)

        self.newButton = QPushButton('New', self)
        self.newButton.clicked.connect(self.onNew)

        self.zoomInButton = QPushButton('Zoom In', self)
        self.zoomInButton.clicked.connect(self.onZoomIn)

        self.zoomOutButton = QPushButton('Zoom Out', self)
        self.zoomOutButton.clicked.connect(self.onZoomOut)
        
        self.buttonGroup = QGroupBox()
        vboxButtons = QVBoxLayout()
        vboxButtons.addWidget(self.newButton)
        vboxButtons.addWidget(self.comboArticles)
        vboxButtons.addWidget(self.nextButton)
        vboxButtons.addWidget(self.prevButton)
        vboxButtons.addWidget(self.zoomInButton)
        vboxButtons.addWidget(self.zoomOutButton)
        vboxButtons.addWidget(self.endButton)
        vboxButtons.addStretch()
        self.buttonGroup.setLayout(vboxButtons)

        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.imgView)
        self.hbox.addWidget(self.textLabel)
        self.hbox.addWidget(self.buttonGroup)

        self.setWindowTitle('image <- text');
        self.setLayout(self.hbox)

        self.show()

    def onArticleChange(self, value):
        self.currentArticle = value

        os.chdir(os.path.join(self.working_directory, self.currentArticle))
        self.articleParts = []
        for f in glob.glob("*.txt"):
            self.articleParts.append(f)
        self.articleParts.sort()
        self.articlePart = 0
        self.lineNumber = 0
        breaker = False
        for idy, articlePart in enumerate(self.articleParts):
          f = open(articlePart, "r", encoding='utf-8', errors='ignore')
          lines = f.readlines()
          f.close()
          for idx, line in enumerate(lines):
              if line == "__BM__\n": # found bookmark
                  self.lineNumber = idx
                  self.articlePart = idy
                  breaker = True
                  break
          if breaker:
              break

        if self.articleParts:
            f = open(self.articleParts[self.articlePart], "r", encoding='utf-8', errors='ignore')
            self.lines = f.readlines()
            f.close()

            self.textLabel.setText(self.lines[self.lineNumber])
            self.imgView.load_image(self.articleParts[self.articlePart].replace(".txt", ""))
        else:
            self.textLabel.setText("")
            self.imgLabel.clear()
            self.lines = []
            self.lineNumber = 0
        os.chdir(self.working_directory)

    def init(self):
        if not os.path.exists("tdg_articles"):
            os.makedirs("tdg_articles")
        self.working_directory = os.path.abspath("tdg_articles")

        article_names = [ '', ]
        article_names.extend([d for d in os.listdir("tdg_articles") \
                if os.path.isdir(os.path.join("tdg_articles", d))])
        self.comboArticles.clear()
        self.comboArticles.addItems(article_names)
        self.currentArticle = str(self.comboArticles.currentText())
        os.chdir(self.working_directory)
        self.textLabel.setText("HELLO")

        pixmap = QPixmap("logo.png")
        self.imgView.load_image("logo.png")
        
        self.lines = []
        self.lineNumber = 0
        self.articlePart = 0
        self.articleParts = []

    def onNext(self):
        os.chdir(os.path.join(self.working_directory, self.currentArticle))
        if self.lineNumber < len(self.lines) - 1:
            self.lineNumber = self.lineNumber + 1
            self.textLabel.setText(self.lines[self.lineNumber])
        elif self.articlePart < len(self.articleParts) - 1:
            self.articlePart = self.articlePart + 1
            f = open(self.articleParts[self.articlePart], encoding='utf-8', errors='ignore')
            self.lines = f.readlines()
            self.lineNumber = 0
            f.close()
            self.imgView.load_image(self.articleParts[self.articlePart].replace(".txt", ""))
            self.textLabel.setText(self.lines[self.lineNumber])

    def onPrev(self):
        os.chdir(os.path.join(self.working_directory, self.currentArticle))
        if self.lineNumber > 0:
            self.lineNumber = self.lineNumber - 1
            self.textLabel.setText(self.lines[self.lineNumber])
        elif self.articlePart > 0:
            self.articlePart = self.articlePart - 1
            f = open(self.articleParts[self.articlePart], encoding='utf-8', errors='ignore')
            self.lines = f.readlines()
            self.lineNumber = len(self.lines) - 1
            f.close()
            self.imgView.load_image(self.articleParts[self.articlePart].replace(".txt", ""))
            self.textLabel.setText(self.lines[self.lineNumber])

    def onNew(self):
        # create a new article
        dg = Dialog()
        dg.accepted.connect(self.createNewArticle)
        dg.exec_()

    def createNewArticle(self, values):
        url = values['Url']
        title = values['Title']
        word1 = values['Word1']
        word2 = values['Word2']
        word3 = values['Word3']
        word4 = values['Word4']
        word5 = values['Word5']
        word6 = values['Word6']

        os.chdir(self.working_directory)

        soup = html2txt.getSoupFromUrl(url)
        sentences = html2txt.nodeToSentences(soup.body)
        start_pattern = re.compile('(.*?{}.*?{}.*?{}.*)'.format(word1, word2, word3))
        end_pattern = re.compile('(.*?{}.*?{}.*?{}.*)'.format(word4, word5, word6))
        sentences2 = copy.copy(sentences)
        for s in sentences:
            if not start_pattern.search(s):
                sentences2.pop(0)
            else:
                break
        sentences3 = []
        for s in sentences2:
            sentences3.append(s)
            if end_pattern.search(s):
                break
        html2txt.saveArticle(url, title, sentences3)

    def onZoomIn(self):
        self.imgView.zoomIn()

    def onZoomOut(self):
        self.imgView.zoomOut()

    def onEnd(self):
        sys.exit()

App = QApplication(sys.argv)
window = Window()
sys.exit(App.exec())
