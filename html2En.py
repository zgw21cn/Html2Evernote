# -*- coding: utf-8 -*-

from evernote.api.client import EvernoteClient
import lxml.html
import evernote.edam.type.ttypes as Types
from feedly.utils import ThreadPool
import re


EN_CONSUMER_KEY = 'consumer_key'
EN_CONSUMER_SECRET = 'consumer_secret'

THREAD_NUM_WORKERS = 5

class Html2En(object):
    def __init__(self, access_token, sandbox):
        self.access_token = access_token
        self.sandbox = sandbox
        
        self.remove_tags = [
        "applet", "base", "basefont", "bgsound", "blink", "button", "dir", "embed", "fieldset", "form", "frame", "frameset", "head", "iframe", "ilayer", "input", "isindex",
        "label", "layer", "legend", "link", "marquee", "menu", "meta", "noframes", "noscript", "object", "optgroup", "option", "param", "plaintext", "script", "select", "style",
        "textarea", "xml", "aside"]
        self.replace_with_div_tags = ["html", "body", "header", "footer", "nav", "section","article"]
        self.allow_attributes = ["href", "src" ]
    
    def create_notebook(self,name):
        notebook = Types.Notebook()
        notebook.name = name    
        return notebook
    
    def create_note(self, title, content, notebook_guid='', image_resource=None):
        note = Types.Note()
        if notebook_guid:
            note.notebookGuid = notebook_guid
    
        if image_resource:
            note.resources = image_resource
    
        note.title = title
        note.content = '''<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
        <en-note><caption>%s</caption>''' % content
        note.content += '</en-note>'
    
        return note
    
    def get_evernote_client(self,token=None):
        if token:
            return EvernoteClient(token=token, sandbox=self.sandbox)
        else:
            return EvernoteClient(
                consumer_key=EN_CONSUMER_KEY,
                consumer_secret=EN_CONSUMER_SECRET,
                sandbox=self.sandbox
            )
    
    def get_note_store(self):
        client = self.get_evernote_client(token=self.access_token)
        return client.get_note_store()

    def get_or_create_notebook(self, note_store, notebook_name):
        # find notebook_name in Evernote
        nbGuid = ''
        notebooks = note_store.listNotebooks()
        for book in notebooks:
            if book.name == notebook_name:
                nbGuid = book.guid
                break
            
        # did not find notebook_name,then create
        if not nbGuid:
            notebook = self.create_notebook(notebook_name)
            try:
                notebook = note_store.createNotebook(self.access_token, notebook)
                nbGuid = notebook.guid
            except:
                pass
        return nbGuid
    
    def save_note(self,title, content, notebook_guid, note_store, image_resource):
        ret = True
        note = self.create_note(title, content, notebook_guid=notebook_guid, image_resource=image_resource)
        try:
            note_store.createNote(self.access_token, note)
        except Exception, e:
            print str(e)
            ret = False
    
        return ret

    def saveEn(self, notebook, title, html):
        #clear html
        root = lxml.html.fromstring(html)
        # delete unnecessary tag
        for tag in self.remove_tags:
            for node in root.xpath('//' + tag):
                node.drop_tree()
        #replace with div
        for tag in self.replace_with_div_tags:
            for node in root.xpath('//' + tag):
                node.tag = "div"
        #remove unnecessary attribute
        for node in root.iter():
            for att in node.attrib.keys():
                if att not in self.allow_attributes:
                    del node.attrib[att]
                #remove javascirpt in href
                if att == "href":
                    url = node.attrib[att]
                    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url)
                    if len(urls) == 0:
                        del node.attrib[att]
        
        img_node = root.xpath('//img')
        if len(img_node) > 0:
            pool = ThreadPool(THREAD_NUM_WORKERS)
                
            #add task
            for img in img_node:
                pool.add_task(img)
                    
            # Wait for completion
            pool.wait_completion()
            #get result
            resources = pool.get_reuslt()
        
        content = lxml.etree.tostring(root, encoding="UTF-8")
        
        #create notebook
        note_store = self.get_note_store()
        #get notebook guid
        nbGuid = self.get_or_create_notebook(note_store, notebook)
        result = self.save_note(title, content, nbGuid, note_store, resources)
                
        return result

if __name__ == '__main__':
    import requests
    
    access_token="access_token"
    
    title="The Present And Future Of Adobe Fireworks"
    url="http://fireworks.smashingmagazine.com/2013/12/19/present-future-adobe-fireworks/"
    resp = requests.get(url)
    html = resp.content
    
    html2En=Html2En(access_token, False)
    
    ret = html2En.saveEn(notebook='Smashingmagazine', title=title, html=html)
