from copy import deepcopy

try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree



def get_element_texts(showtree,tag):
    elems = showtree.findall(tag)
    text_blocks = set([elem.text for elem in elems])
    try: 
        text_blocks.remove(None)
    except (ValueError, KeyError):
        pass
    return text_blocks
    
def create_episode_title(episode_parts):
    return ' | '.join([seg['name'] for seg in episode_parts ])
    
def create_episode_overview(episode_parts):
    if len(episode_parts) == 1:
        data = episode_parts[0]['overview']
    else:       
        for seg in episode_parts:
            if seg['overview'] == None:
                seg['overview'] = ''
        data = '\n'.join(
            [seg['name'] + ':\n' + seg['overview']  for seg in episode_parts]
        )
    return data
    
def compile_piped_list(episode_parts, tag):  
    try:
        listy = [seg['EpNode'].find(tag).text for seg in episode_parts ]
        listylist = [item.split('|') for item in listy]
        flatlist = sorted(set([item for sublist in listylist for item in sublist]))
        for garbage in ['', 'None']:
            if garbage in flatlist:
                flatlist.remove(garbage)
        data = '|'+'|'.join(flatlist)+'|'
        if data == '||':
            data = ''
    except:
        data = ''
    return data

def retrieve_single_entry(episode_parts, tag):
    try:
        entries = set([seg['EpNode'].find(tag).text for seg in episode_parts])
        try:
            entries.remove(None)
        except (ValueError, KeyError):
            pass
        data = entries[0]
    except:
        data = ''
    return data
    
def get_boolean_flag(episode_parts, tag):
    bools = set([  seg['EpNode'].find(tag).text  for seg in episode_parts  ])
    if '1' in bools:
        data = '1'
    else:
        data = '0'
    return data
    
def get_average_value(episode_parts, tag):
    try:
        values = [float(seg['EpNode'].find(tag).text) for seg in episode_parts]
        data = sum(values, 0.0) / len(values)
    except:
        data = '0'
    return str(data)

def create_dvd_tree(showtree):
    '''
    This function takes an ElementTree object based on theTVDB.com data,
    and returns and ElementTree object containing data for the show in
    dvd order, including merging info when a dvd-ordered episode consists of 
    multiple aired-order episodes.  Episodes without a DVD Order are skipped.

    '''

    # Create Tree and add series data
    dvdroot = ElementTree.Element('Data')
    dvdroot.append(deepcopy(showtree.find('Series')))

    # Loop through seasons/episodes in showtree, and look for dvd order info.
    for seasonnum in get_element_texts(showtree,'Episode/DVD_season'):
        episode_nums = sorted(set(
            [int(float(epnum)) for epnum 
                    in get_element_texts(showtree,'Episode/DVD_episodenumber')]
        ))

        for episodenum in episode_nums:
            episode_parts = []
            for item in showtree.findall('Episode'):
                if item.find('DVD_season').text == str(seasonnum):
                    segmentnum = item.find('DVD_episodenumber').text
                    if segmentnum == None:
                        segmentnum = ''
                    if segmentnum[:-2] == str(episodenum):
                        Segment = {
                            'name'     : item.find('EpisodeName').text,
                            'overview' : item.find('Overview').text,
                            'EpNode'   : item
                        }
                        if Segment['name'] != None:
                            episode_parts.append(Segment)
            if episode_parts != []:
                # Set basic data
                episode = ElementTree.SubElement(dvdroot,'Episode')
                EpisodeName = ElementTree.SubElement(episode,'EpisodeName')
                EpisodeName.text = create_episode_title(episode_parts)
                SeasonNumber = ElementTree.SubElement(episode,'SeasonNumber')
                SeasonNumber.text = str(seasonnum)
                EpisodeNumber = ElementTree.SubElement(episode,'EpisodeNumber')
                EpisodeNumber.text = str(episodenum)
                Overview = ElementTree.SubElement(episode, 'Overview')
                Overview.text = create_episode_overview(episode_parts)

                # Flesh out the data
                tags = [child.tag for child 
                        in episode_parts[0]['EpNode'].getchildren()]
                for tag in [
                    'EpisodeName', 'Overview', 'SeasonNumber', 'EpisodeNumber']:
                    tags.remove(tag)

                # Things we want a piped list for
                for tag in ['Director', 'Writer', 'GuestStars']:
                    item = ElementTree.SubElement(episode, tag)
                    item.text = compile_piped_list(episode_parts, tag)
                    tags.remove(tag)

                # Things we want an average value for
                for tag in ['Rating']:
                    item = ElementTree.SubElement(episode, tag)
                    item.text = get_average_value(episode_parts, tag)
                    tags.remove(tag)

                # Boolean Flag, set to 1 if any is 1
                for tag in ['EpImgFlag']:
                    item = ElementTree.SubElement(episode, tag)
                    item.text = get_boolean_flag(episode_parts, tag)
                    tags.remove(tag)

                # Everything else we want a single entry for     
                for tag in tags:
                    item = ElementTree.SubElement(episode, tag)                 
                    item.text = retrieve_single_entry(episode_parts, tag)


    return dvdroot


def main():
    """For quick and dirty dev testing """

    import xml.dom.minidom as minidom

    # tvdbid = '78874'     # Firefly
    tvdbid = '75545'     # Invader Zim
    showtree = ElementTree.ElementTree()

    showtree.parse('/Users/Shared/tvdbfiles/'+tvdbid+'/en.xml')
    dvdroot = create_dvd_tree(showtree)
    dvdtree = ElementTree.ElementTree(dvdroot)
    my_xml = minidom.parseString(ElementTree.tostring(dvdroot))
    print(my_xml.toprettyxml())
            
    
if __name__ == "__main__":
    main()

