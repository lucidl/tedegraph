from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QGroupBox
from PyQt5.QtWidgets import QLabel, QComboBox
from PyQt5.QtWidgets import QGraphicsScene, QFrame, QGraphicsView, QGraphicsPixmapItem, QDialog, QFormLayout, QMessageBox
from PyQt5.QtGui import QPainter, QPalette, QFont, QPixmap
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal
import sys
import glob
import os
import os.path
import html2txt
import re
import copy

class ImageViewer(QGraphicsView):
    factor = 1.5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
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

    def zoom_in(self):
        self.zoom(self.factor)

    def zoom_out(self):
        self.zoom(1 / self.factor)

    def zoom(self, f):
        self.scale(f, f)

    def reset_zoom(self):
        self.resetTransform()

    def fit_to_window(self):
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

        self.setGeometry(300, 300, 1200, 600)

         # image
        self.img_view = ImageViewer()
        self.img_view.setFrameShape(QFrame.NoFrame)

        # text
        self.text_label = QLabel("", self)
        self.text_label.setWordWrap(True)
        self.text_label.setFont(QFont('Arial', 12))
        self.text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # article choice
        self.combo_articles = QComboBox(self)
        self.init()
        self.combo_articles.currentTextChanged.connect(self.on_article_change)
        
        # buttons
        self.next_button = QPushButton('Next', self)
        self.next_button.setShortcut("Space")
        self.next_button.clicked.connect(self.on_next)

        self.prev_button = QPushButton('Prev', self)
        self.prev_button.setShortcut("Backspace")
        self.prev_button.clicked.connect(self.on_prev)

        self.end_button = QPushButton('End', self)
        self.end_button.clicked.connect(self.on_end)

        self.new_button = QPushButton('New', self)
        self.new_button.clicked.connect(self.on_new)

        self.zoom_in_button = QPushButton('Zoom In', self)
        self.zoom_in_button.clicked.connect(self.on_zoom_in)

        self.zoom_out_button = QPushButton('Zoom Out', self)
        self.zoom_out_button.clicked.connect(self.on_zoom_out)

        self.bookmark_button = QPushButton('Bookmark', self)
        self.bookmark_button.clicked.connect(self.on_create_bookmark)
        
        self.button_group = QGroupBox()
        vbox_buttons = QVBoxLayout()
        vbox_buttons.addWidget(self.new_button)
        vbox_buttons.addWidget(self.combo_articles)
        vbox_buttons.addWidget(self.next_button)
        vbox_buttons.addWidget(self.prev_button)
        vbox_buttons.addWidget(self.zoom_in_button)
        vbox_buttons.addWidget(self.zoom_out_button)
        vbox_buttons.addWidget(self.bookmark_button)
        vbox_buttons.addWidget(self.end_button)
        vbox_buttons.addStretch()
        self.button_group.setLayout(vbox_buttons)

        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.img_view)
        self.hbox.addWidget(self.text_label)
        self.hbox.addWidget(self.button_group)

        self.setWindowTitle('image <- text');
        self.setLayout(self.hbox)

        self.show()

    def on_article_change(self, value):
        self.current_article = value

        os.chdir(os.path.join(self.working_directory, self.current_article))
        self.article_parts = []
        for f in glob.glob("*.txt"):
            self.article_parts.append(f)
        self.article_parts.sort()
        self.article_part = 0
        self.lines = []
        self.line_number = 0
        breaker = False
        for idy, article_part in enumerate(self.article_parts):
          f = open(article_part, "r", encoding='utf-8', errors='ignore')
          lines = f.readlines()
          f.close()
          for idx, line in enumerate(lines):
              if line == "__BM__\n": # found bookmark
                  self.line_number = idx
                  self.article_part = idy
                  breaker = True
                  break
          if breaker:
              break

        if self.article_parts:
            f = open(self.article_parts[self.article_part], "r", encoding='utf-8', errors='ignore')
            self.lines = f.readlines()
            f.close()

            self.text_label.setText(self.lines[self.line_number])
            self.img_view.load_image(self.article_parts[self.article_part].replace(".txt", ""))
        else:
            self.text_label.setText("")
            self.lines = []
            self.line_number = 0
        os.chdir(self.working_directory)

    def init(self):
        if not os.path.exists("tdg_articles"):
            os.makedirs("tdg_articles")
        self.working_directory = os.path.abspath("tdg_articles")

        self.refresh_combo_articles()
        os.chdir(self.working_directory)
        self.text_label.setText("HELLO")

        self.img_view.load_image("logo.png")
        
        self.lines = []
        self.line_number = 0
        self.article_part = 0
        self.article_parts = []

    def refresh_combo_articles(self):
        article_names = [ '', ]
        article_names.extend(sorted([d for d in os.listdir("tdg_articles") \
                if os.path.isdir(os.path.join("tdg_articles", d))]))
        self.combo_articles.clear()
        self.combo_articles.addItems(article_names)
        self.current_article = str(self.combo_articles.currentText())


    def on_next(self):
        os.chdir(os.path.join(self.working_directory, self.current_article))
        if self.line_number < len(self.lines) - 1:
            self.line_number = self.line_number + 1
            self.text_label.setText(self.lines[self.line_number])
        elif self.article_part < len(self.article_parts) - 1:
            self.article_part = self.article_part + 1
            f = open(self.article_parts[self.article_part], encoding='utf-8', errors='ignore')
            self.lines = f.readlines()
            self.line_number = 0
            f.close()
            self.img_view.load_image(self.article_parts[self.article_part].replace(".txt", ""))
            self.text_label.setText(self.lines[self.line_number])

    def on_prev(self):
        os.chdir(os.path.join(self.working_directory, self.current_article))
        if self.line_number > 0:
            self.line_number = self.line_number - 1
            self.text_label.setText(self.lines[self.line_number])
        elif self.article_part > 0:
            self.article_part = self.article_part - 1
            f = open(self.article_parts[self.article_part], encoding='utf-8', errors='ignore')
            self.lines = f.readlines()
            self.line_number = len(self.lines) - 1
            f.close()
            self.img_view.load_image(self.article_parts[self.article_part].replace(".txt", ""))
            self.text_label.setText(self.lines[self.line_number])

    def on_new(self):
        # create a new article
        dg = Dialog()
        dg.accepted.connect(self.create_new_article)
        dg.exec_()

    def create_new_article(self, values):
        url = values['Url']
        title = values['Title']
        word1 = values['Word1']
        word2 = values['Word2']
        word3 = values['Word3']
        word4 = values['Word4']
        word5 = values['Word5']
        word6 = values['Word6']

        os.chdir(self.working_directory)

        soup = html2txt.get_soup_from_url(url)
        sentences = html2txt.node_to_sentences(soup.body)
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
        html2txt.save_article(url, title, sentences3)
        os.chdir("..")
        self.refresh_combo_articles()
        os.chdir(self.working_directory)

    def on_zoom_in(self):
        self.img_view.zoom_in()

    def on_zoom_out(self):
        self.img_view.zoom_out()

    def on_create_bookmark(self):

        if not self.current_article or self.lines[self.line_number] == "__BM__\n":
            return
        os.chdir(os.path.join(self.working_directory, self.current_article))

        # removing old bookmark
        for file in glob.glob("*.txt"):
            f = open(file, "r", encoding='utf-8', errors='ignore')
            lines = f.readlines()
            f.close()
            old_text = "".join(lines)
            if "__BM__\n" in old_text:
                with open(file, "w") as ff:
                    new_text = old_text.replace("__BM__\n", "")
                    ff.write(new_text)

        # making new bookmark
        f = open(self.article_parts[self.article_part], "r", encoding='utf-8', errors='ignore')
        self.lines = f.readlines()
        f.close()

        if self.line_number > 0:
            self.lines.insert(self.line_number - 1, "__BM__\n")
        else:
            self.lines.insert(0, "__BM__\n")

        f = open(self.article_parts[self.article_part], "w")
        new_text = "".join(self.lines)
        f.write(new_text)
        f.close()

        self.line_number = self.lines.index("__BM__\n")
        f = open(self.article_parts[self.article_part], "r", encoding='utf-8', errors='ignore')
        self.lines = f.readlines()
        f.close()

        os.chdir(self.working_directory)
        QMessageBox.about(self, "", "Bookmark added successfully")

    def on_end(self):
        sys.exit()

App = QApplication(sys.argv)
window = Window()
sys.exit(App.exec())
