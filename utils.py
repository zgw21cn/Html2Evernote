import evernote.edam.type.ttypes as Types
import binascii
import Queue
import threading
from django.utils.encoding import smart_str
import hashlib
import requests
from urlparse import urlsplit

class ThreadPool:
    def __init__(self, num_threads):
        self.tasks = Queue.Queue()
        self.result = Queue.Queue()
        
        for _ in range(num_threads):
            AttachImage(self.tasks, self.result)
            
    def add_task(self, url):
        """Add a task to the queue"""
        self.tasks.put(url)

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()
        
    def get_reuslt(self):
        """get result from result queue"""
        ret = []
        try:
            while 1:
                ret.append(self.result.get_nowait())
        except Queue.Empty:
            pass
        return ret

class AttachImage(threading.Thread):
    '''a worker thread'''
    def __init__(self, task_queue, result_queue):
        threading.Thread.__init__(self)       
        
        self.task_queue = task_queue
        self.result_queue = result_queue        
        
        self.daemon=True
        self.start()       
        
    def run(self):
        while True:
            try:
                #grabs img
                img=self.task_queue.get()
                img_url=img.attrib.get('src','')
                if img_url:
                    img_url_decoded = smart_str(img_url)
                    result, contentType = download_image(img_url_decoded)
                    # fail to load image
                    if not result:
                        img.drop_tree()
                    else:
                        #get hash of result
                        md5 = hashlib.md5()
                        md5.update(result)
                        hash = md5.digest()
                        hash_hex = binascii.hexlify(hash)
                        #create resource
                        data=Types.Data()
                        data.size=len(result)
                        data.bodyHash=hash
                        data.body=result
                        
                        resource = Types.Resource()
                        resource.mime = contentType
                        resource.data=data
                        
                        img.tag='en-media'
                        img.attrib['type'] = contentType
                        img.attrib['hash'] = hash_hex
                        
                        if "src" in img.attrib.keys():
                            del img.attrib["src"]                        
                        if "class" in img.attrib.keys():
                            del img.attrib["class"]
                            
                        self.result_queue.put(resource)
                    
                #signals to queue job is done
                self.task_queue.task_done()
            except Queue.Empty:
                break

def download_image(img_url):
    '''return downloaded image data and content type. if failure, return none.'''
    data = None
    contentType = ""
    if img_url:
        try:
            r=requests.get(img_url)
            if r.status_code == 200:
                suffix_list = ['jpg', 'gif', 'png', 'tif', 'svg','bmp','ico']
                file_name =  urlsplit(img_url)[2].split('/')[-1]
                file_suffix = file_name.split('.')[1]                
                if file_suffix in suffix_list:
                    data = r.content
                    contentType = r.headers['content-type']
                else:
                    return (data,contentType)
            else:
                return (data,contentType)
        except Exception:
            pass
    
    return (data,contentType)
