from urllib.request import urlopen, urlretrieve
from bs4 import BeautifulSoup
import bs4
import nltk.util
import re
import nltk
from ebooklib import epub
from subprocess import check_output
import os
import codecs

images_dict = {}

def node_to_sentences(node):
  # converts html node (tag) to list of sentences

  if node is None:
    return []

  # remove uninteresting tags
  for t in node.find_all(["script", "noscript", "style"]):
    t.decompose() # t.extract() is similar method 

  for idx, img in enumerate(node.find_all("img")):
      img.replaceWith("tdg_img_" + str(idx))
      img_key = "tdg_img_{}".format(idx)
      images_dict[img_key] = img["src"]

  all_nav_strings = [x for x in node.find_all(text=True) if x.strip() != "" if not type(x) is bs4.Comment]
  
  buffer = ""
  tokenized_strings = []
  for idx, nav_s in enumerate(all_nav_strings): # before it was enumerating node.stripped_strings
    s = nav_s.strip()
    s = s.replace("\r", "")

    try:
      s_next = all_nav_strings[idx + 1] # next navigable string
    except:
      s_next = None

    # we add string s to the buffer
    if s.startswith(",") or s.startswith(".") or buffer == "":
      buffer += s
    else:
      buffer += " " + s

    # tokenize the content of the buffer and empty the buffer.
    if s.endswith(".") or s_next is None or separate_strings(nav_s, s_next):
      # nav_s and s_next will be splitted
      tokenizer = nltk.data.load('nltk:tokenizers/punkt/english.pickle')
      buffer = buffer.replace("\n", " ")
      buffer = re.sub(" +", " ", buffer) # one or more spaces replace with one space
      sentences = tokenizer.tokenize(buffer)
      for sen in sentences:
        tokenized_strings.append(sen)
      buffer = ""

  return tokenized_strings

def separate_strings(s1, s2):
  onlys1 = [x.name for x in s1.parents if not x in s2.parents] # nodes only over s1
  onlys2 = [x.name for x in s2.parents if not x in s1.parents] # nodes only over s2
  # list of tags, that will let s1 and s2 splitted
  separatingTags = [ "h1", "h2", "h3", "h4", "h5", "h6", "h7", "li", "ol", "ul", "table", "tr", "th", "td", "div", "p" ]
  for x in separatingTags:
    if x in onlys1 or x in onlys2:
      return True
  return False

def get_soup_from_url(url):
  if url.startswith('http'):
    html = urlopen(url).read().decode('utf-8', 'ignore')
    soup = BeautifulSoup(html, features = "html.parser")
  elif url.endswith(".html"): # html file
    html = open(url, 'r')
    soup = BeautifulSoup(html.read())
    html.close()
  elif url.endswith(".epub"): # epub file
    book = epub.read_epub(url)
    pages = [page for page in book.items if type(page) == epub.EpubHtml]
    soup = BeautifulSoup("<html><head></head><body></body></html>")
    for p in pages:
      s = BeautifulSoup(p.content)
      part = s.html.body
      part.name = "p"
      soup.html.body.append(part)
      print (len(soup.html.body))
  elif url.endswith(".pdf"):
    first_page = input("First page: ")
    last_page = input("Last page: ")
    output = check_output(["pdftotext", "-f", first_page, "-l", last_page, "-htmlmeta", "-nopgbrk", "-layout", url, "-"])
    soup = BeautifulSoup(output)
  elif url.endswith(".txt"):
    text = open(url, 'r').readlines()
    title = url.replace(".txt", "")
    soup = BeautifulSoup("<html><title>" + title + "</title><head></head><body><div></div></body></html>")
    soup.html.body.div.append("".join(text))
    print (len(soup.html.body))
  else:
    return
  return soup

def save_article(url, title, sentences):

  if not os.path.exists(title):
      os.makedirs(title)

  file_name = "0000000.txt"

  i = 0  # number of file

  pattern = re.compile("tdg_img_\d+")

  for sentence in sentences:
    if pattern.match(sentence):
      img_url = images_dict[sentence]
          
      try:
          img_file_name = "%07d" % i
          if url.startswith("https") and not img_url.startswith("https"):
              urlretrieve("https:" + img_url, os.path.join(title, img_file_name))
          elif url.startswith("http") and not img_url.startswith("http"):
              urlretrieve("http:" + img_url, os.path.join(title, img_file_name))
          else:
              urlretrieve(img_url, os.path.join(title, img_file_name))
          file_name = "%07d.txt" % i 
      except:
          continue
      i = i + 1
      continue

    with codecs.open(os.path.join(title, file_name), "a", encoding="utf-8") as f:
      f.write(sentence + "\n")
