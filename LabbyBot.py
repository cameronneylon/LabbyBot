#!python## Copyright 2009 Jonathon Hunt, Dan Hagon, Cameron Neylon## Licensed under the Apache License, Version 2.0 (the "License");# you may not use this file except in compliance with the License.# You may obtain a copy of the License at## http://www.apache.org/licenses/LICENSE-2.0## Unless required by applicable law or agreed to in writing, software# distributed under the License is distributed on an "AS IS" BASIS,# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.# See the License for the specific language governing permissions and# limitations under the License.#from google.appengine.ext import webappfrom google.appengine.ext.webapp import utilimport feedparserfrom waveapi import eventsfrom waveapi import modelfrom waveapi import robotfrom waveapi import documentfrom waveapi import simplejson as jsonimport loggingdef parsefeed(feed):    """Take a URI and parse the feed to generate menu list    Uses feedparser.parse to get a feed and returns a list of items, currently    as a simple list. It might be better to do this as a dictionary. It attempts    to get a date from either entry.updated (which is usually filled from an    RSS feed) or entry.published (which is usually filled from an ATOM feed).    """    parsedfeed = feedparser.parse(feed) #parse the feed using feedparser library    logging.debug('Parsing feed:'+ feed + ' Return code:' + parsedfeed.status)    itemslist = [] #list for holding titles, links etc.    # Iterate over the list of entries and populate a list containing titles, links etc.    for entry in parsedfeed.entries: #populate the list with items         title = entry.get('title', 'No title')        link = entry.get('link', 'No link')        updated = entry.get('updated', 'No date available') # Try to get date from 'updated'            if updated == 'No date available':                updated = entry.get('published', 'No date available') # if not try to get from 'published'        if 'enclosures' in entry:            enclosure = entry.enclosures[0].get('href', 'No enclosure link available')            enclosuretype = entry.enclosures[0].get('type', 'No enclosure type available')        else:            enclosure = None # there are no enclosures        logging.debug('Title:' + title + ' Link:' + link + ' Enclosure:' + enclosure)        itemslist.append([title, link, updated, enclosure]) # returned list of attributes. Should this be a dictionary?    return itemslist def insertobject(title, url, blip, index, enclosure = 'none'):    """Take a list of characteristics and add back to wave"""    r = document.Range(index, (index + len(title)))    blip.GetDocument().AppendText('\n' + title) # insert the name    r.start = blip.GetDocument().GetText().find(title)    r.end = r.start + len(title)    blip.GetDocument().SetAnnotation(r, 'link/manual', url) #add link    if enclosure != None:        if enclosure.endswith('jpg'):            image = document.Image(enclosure)            blip.GetDocument().AppendElement(image)        def OnBlipSubmitted(properties, context):    logging.debug('OnBlipSubmitted()')    passdef insertItem(properties, context):    """User has chosen an object to insert."""    logging.debug('insertItem()')    blip = context.GetBlipById(properties['blipId'])    sourceGadget = blip.GetGadgetByUrl(             'http://labbybot.appspot.com/gadgets/feed-item-select-dropdown.xml')    sourceUrl = sourceGadget.get('selectedentry_url')    title = sourceGadget.get('selectedentry_title')    img = sourceGadget.get('selectedentry_img')    logging.debug('Inserting ' + sourceUrl)    logging.debug('Img source ' + img)    insertobject(title, sourceUrl, blip, len(blip.GetDocument().GetText()), img)def addForm(wavelet):    """Add form elements as the GUI (for choosing the RSS feed and inserting elements).    """    formblip = wavelet.CreateBlip()    formdoc = formblip.GetDocument()    # formdoc.SetText('This is your LaTeX blip. Write me and the click Compile to LaTeX to get a LaTeX version.\n\n\n\n')    formdoc.AppendElement(document.FormElement('INPUT', 'feedTextbox', 'Feed URL here'))    formdoc.AppendElement(document.FormElement('BUTTON', 'insertFeed', 'Insert feed'))def insertFeed(properties, context):    """The user wants a feed added."""    logging.debug('Add feed list elements')    blip = context.GetBlipById(properties['blipId'])    elements = blip.GetElements()    e = filter(lambda e: hasattr(e, 'name') and e.name == 'feedTextbox', blip.GetElements().values())    assert(len(e) == 1) # There should only be one matching element    feedurl= e[0].value    logging.debug('Feed url=' + feedurl)    # Now fetch the form elements and populate a dropdown box.    items = parsefeed(feedurl)    # We used radio buttons but that seemed to crash wave.    # Now use a gadget that wraps a drop-down.    doc = blip.GetDocument()    doc.AppendText('\n\n')    # Only pass the items needed to populate the list    # Current each entry is a tuple of title, url, enclosure_url    items = map(lambda i: (i[0], i[1], i[3]), items)    doc.AppendElement(document.Gadget(                'http://labbybot.appspot.com/gadgets/feed-item-select-dropdown.xml',                {'list' : json.dumps(items, sort_keys=False)}))    doc.AppendElement(document.FormElement('BUTTON', 'insertItem', 'Insert item'))    def OnFormClicked(properties, context):    """Handle all form events."""    logging.debug('OnFormClicked(): Button clicked was ' + properties['button'])    # Call the corresponding handler - will give an exception if no handler exists    {'insertFeed' : insertFeed,     'insertItem' : insertItem}[properties['button']](properties, context)def OnRobotAdded(properties, context):    """Invoked when the robot has been added.    In this case we need to add the gadget for creating dropdowns, grab the default rss    feed and initialize the state of the gadget"""    logging.info('OnRobotAdded()')    root_wavelet = context.GetRootWavelet()    root_wavelet.CreateBlip().GetDocument().SetText("Hello, I'm LabbyBot. I parse RSS/Atom feeds to populate a dropdown menu and help you connect your research objects up together. This is Version 0.1 of LabbyBot")    addForm(root_wavelet)def main():    LabbyBot = robot.Robot('LabNoteBot',                           image_url='http://www.chemspider.com/ImagesHandler.ashx?id=236',                           version = '2',                           profile_url='http://labnotebot.appspot.com')    LabbyBot.RegisterHandler(events.BLIP_SUBMITTED, OnBlipSubmitted)    LabbyBot.RegisterHandler(events.WAVELET_SELF_ADDED, OnRobotAdded)    LabbyBot.RegisterHandler(events.FORM_BUTTON_CLICKED, OnFormClicked)    LabbyBot.Run(debug=True)if __name__ == '__main__':    main()