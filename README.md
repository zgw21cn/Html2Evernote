Html2Evernote
=============

Save html that includes images to Evernote

## Requirements
[evernote.api.client](https://github.com/evernote/evernote-sdk-python)

accessToken

## Usage
	import requests
    
    access_token="access_token"
    
    title="The Present And Future Of Adobe Fireworks"
    url="http://fireworks.smashingmagazine.com/2013/12/19/present-future-adobe-fireworks/"
    resp = requests.get(url)
    html = resp.content
    
    html2En=Html2En(access_token, False)
    
    ret = html2En.saveEn(notebook='Smashingmagazine', title=title, html=html)
