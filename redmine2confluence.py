import sys
import os
import re
import pdb
from atlassian import Confluence
import textile
import html
import random
import string
from bs4 import BeautifulSoup
from urllib.parse import urlparse

usage = f"Usage: python3 {sys.argv[0]} <redmine database dump file> <atlassian config yaml file> <redmine attachments folder root> [<redmine project name to limit conversion to>]"

try:
    sql_filename = sys.argv[1]
except IndexError:
    print(f"{usage}\n\nERROR: Redmine sqldump file argument missing")
    sys.exit()


try:
    atlassian_config_filename = sys.argv[2]
except IndexError:
    print(f"{usage}\n\nERROR: Atlassian config file argument missing")
    sys.exit()


try:
    redmine_files = sys.argv[3]
except IndexError:
    print(f"{usage}\n\nERROR: Redmine attachments folder argument missing")
    sys.exit()


# reduce scope of run to a single redmine project
try:
    scope = sys.argv[4]
except IndexError:
    scope = None




#               _           _                               _
#  _ __ ___  __| |_ __ ___ (_)_ __   ___   _ __   __ _ _ __| |_
# | '__/ _ \/ _` | '_ ` _ \| | '_ \ / _ \ | '_ \ / _` | '__| __|
# | | |  __/ (_| | | | | | | | | | |  __/ | |_) | (_| | |  | |_
# |_|  \___|\__,_|_| |_| |_|_|_| |_|\___| | .__/ \__,_|_|   \__|
#                                         |_|
# redmine part


#import timeit
#timeit.timeit(stmt="r.match(s)", setup="import re; s = 'COPY public.wiki_contents (id, page_id, author_id, text, comments, updated_on, version) FROM stdin;'; r = re.compile(r'.+\((.+)\)')", number = 30000000)
#timeit.timeit(stmt="r.search(s)", setup="import re; s = 'COPY public.wiki_contents (id, page_id, author_id, text, comments, updated_on, version) FROM stdin;'; r = re.compile(r'\((.+)\)')", number = 30000000)


def parse_schema_line(line):
    """
    Function to parse a sql schema line
    e.g.
    
    COPY public.wiki_contents (id, page_id, author_id, text, comments, updated_on, version) FROM stdin;

    where the column names are inside the parantheses.

    To return the column names as a list, it will pick out the text between the parantheses and split it on ", " to get it as a list.
    """

    # return the schema as a list
    return re.search(r"\((.+)\)", line).groups()[0].split(", ")


def parse_sql_line(schema, line):
    """
    Function to parse a single line of tab separated columns into a dict, using a schema list as key names.
    e.g.

    schema = ["col1", "col2", "col3"]
    line = "val1\tval2\val3"
    to
    {'col1':'val1', 'col2':'val2', 'col3':'val3'}
    """
    
    # loop over the columns in row
    res = {}
    for i,col in enumerate(line.split("\t")):

        # remove surrounding whitespace and underscores before saving data
        col = col.strip().strip('_')

        # replace postgres None with python None
        if col == '\\N':
            col = None

        # save the column data using the schemas column name as key
        res[schema[i]] = col

    # return parsed row as well as the row's id (assumed first column)
    return res, res[schema[0]]


# init
mode = "searching"
redmine = {}
i=0
# open the sql filie
with open(sql_filename, 'r') as sql_file_handle:

    for line in sql_file_handle:

        line = line.strip()
        
#                          _                           _      
#  ___  ___  __ _ _ __ ___| |__    _ __ ___   ___   __| | ___ 
# / __|/ _ \/ _` | '__/ __| '_ \  | '_ ` _ \ / _ \ / _` |/ _ \
# \__ \  __/ (_| | | | (__| | | | | | | | | | (_) | (_| |  __/
# |___/\___|\__,_|_|  \___|_| |_| |_| |_| |_|\___/ \__,_|\___|
#                                                             
# search mode

        # if in searching mode
        if mode == "searching":

            # if wiki_contents is found
            if line.startswith("COPY public.wiki_contents "):
                mode = "wiki_contents"
                schema = parse_schema_line(line)
                print(f"Collecting {mode}")
                continue

            # if wiki_pages is found
            elif line.startswith("COPY public.wiki_pages "):
                mode = "wiki_pages"
                schema = parse_schema_line(line)
                print(f"Collecting {mode}")
                continue

            # if wikis is found
            elif line.startswith("COPY public.wikis "):
                mode = "wikis"
                schema = parse_schema_line(line)
                print(f"Collecting {mode}")
                continue

            # if projects is found
            elif line.startswith("COPY public.projects "):
                mode = "projects"
                schema = parse_schema_line(line)
                print(f"Collecting {mode}")
                continue

            # if users is found
            elif line.startswith("COPY public.users "):
                mode = "users"
                schema = parse_schema_line(line)
                print(f"Collecting {mode}")
                continue

            # if attachments is found
            elif line.startswith("COPY public.attachments "):
                mode = "attachments"
                schema = parse_schema_line(line)
                print(f"Collecting {mode}")
                continue




#                                                  _
#  _ __   __ _ _ __ ___  ___   _ __ ___   ___   __| | ___
# | '_ \ / _` | '__/ __|/ _ \ | '_ ` _ \ / _ \ / _` |/ _ \
# | |_) | (_| | |  \__ \  __/ | | | | | | (_) | (_| |  __/
# | .__/ \__,_|_|  |___/\___| |_| |_| |_|\___/ \__,_|\___|
# |_|
# parse mode

        else:

            # go back to search mode when the end of the sql block is reached
            if line == '\.':
                print(f"Finished {mode}")
                mode = "searching"
                continue

            # parse the line
            line_parsed, line_id = parse_sql_line(schema, line)

            # save the info
            try:
                redmine[mode][line_id] = line_parsed

            # if it is the first time this mode is run, the datastructure will not be initialized yet
            except KeyError:
                # initialize datastructure for the mode
                redmine[mode] = {}
                redmine[mode][line_id] = line_parsed




# make all objects have complete info about where they exist
for page in redmine['wiki_pages'].values():
    page['project_id'] = redmine['wikis'][page['wiki_id']]['project_id']

    # add pages list to wikis
    try:
        redmine['wikis'][page['wiki_id']]['pages'].append(page['id'])
    except KeyError:
        redmine['wikis'][page['wiki_id']]['pages'] = [page['id']]
        
    # add pages list to projects
    try:
        redmine['projects'][page['project_id']]['pages'].append(page['id'])
    except KeyError:
        redmine['projects'][page['project_id']]['pages'] = [page['id']]

    # add pages list to parent pages
    if page['parent_id']:
        try:
            redmine['wiki_pages'][page['parent_id']]['children'].append(page['id'])
        except KeyError:
            redmine['wiki_pages'][page['parent_id']]['children'] = [page['id']]


for contents in redmine['wiki_contents'].values():
    contents['wiki_id'] = redmine['wiki_pages'][contents['page_id']]['wiki_id']
    contents['project_id'] = redmine['wiki_pages'][contents['page_id']]['project_id']
    redmine['wiki_pages'][contents['page_id']]['contents_id'] = contents['id']

for wiki in redmine['wikis'].values():
    redmine['projects'][wiki['project_id']]['wiki_id'] = wiki['id']





# subset data for development
devel = False
if devel:
    n = 30
    page_list = []
    project_list = []
    for project in list(redmine['projects'].values())[:n]:
        project_list.append(project['id'])
        if 'pages' in project.keys():
            page_list += project['pages']

    for page in redmine['wiki_pages'].copy().values():
        if page['id'] not in page_list:
            del redmine['wiki_pages'][page['id']]

    for project in redmine['projects'].copy().values():
        if project['id'] not in project_list:
            del redmine['projects'][project['id']]

    print(f"Devel mode: will create up to {len(project_list)} project pages and {len(page_list)} wiki pages")
else:
    print(f"Normal mode: will create up to {len(redmine['projects'])} project pages and {len(redmine['wiki_pages'])} wiki pages")


#        _   _               _                                _   
#   __ _| |_| | __ _ ___ ___(_) __ _ _ __    _ __   __ _ _ __| |_ 
#  / _` | __| |/ _` / __/ __| |/ _` | '_ \  | '_ \ / _` | '__| __|
# | (_| | |_| | (_| \__ \__ \ | (_| | | | | | |_) | (_| | |  | |_ 
#  \__,_|\__|_|\__,_|___/___/_|\__,_|_| |_| | .__/ \__,_|_|   \__|
#                                           |_|                   
# atlassian part

import yaml
import pprint

def pp(s):
    """
    Pretty print data to make it more readable.
    """
    p = pprint.PrettyPrinter(indent=4)
    p.pprint(s)


def clean_space(space_id):
    """
    Delete all pages in a space until there are no pages left.
    """
    while True:

        pages = confluence.get_all_pages_from_space(space_id, start=0, limit=100, status=None, expand=None, content_type='page')

        # break when there are no more pages left
        if not pages:
            break

        for page in pages:
            print(f"Removing page: {page['title']}")
            confluence.remove_page(page['id'], status=None, recursive=False)


def get_project_wiki(project_id):
    """
    Get the wiki belonging to a project
    """
    for wiki in redmine['wikis'].values():
        if wiki['project_id'] == project_id:
            return wiki



#def get_all_wiki_pages(wiki_id):
#    """
#    Return a list of all pages from a wiki.
#    """
#    return [ x for x in redmine['wiki_pages'].values() if x['wiki_id'] == wiki_id ]


def get_page(wiki_id, title):
    """
    Get the page from wiki id and title.
    """

    # replace spaces with underscores
    title = title.replace(' ', '_').replace('/', '').replace(',','').replace('.','').replace('&quot;','"').replace('?','')

    # loop through all pages until the requested page is found
    for page in redmine['wiki_pages'].values():
        if wiki_id == page['wiki_id'] and page['title'].lower() == title.lower():
            return page
    
    # if no match is found
    return None




def create_confluence_page(title, page_html, parent=None):
    """
    Create a confluence page.
    """
    #return {'id':1, 'title':"devel", "space":{"key":"RED"}}
    return confluence.create_page(config['space_id'], title, page_html, parent_id=parent, type='page', representation='storage', editor='v2')




def update_confluence_page(confluence_response, title, page_html, parent=None):
    """
    Update a confluence page.
    """
    #return {'id':1, 'title':"devel", "space":{"key":"RED"}}
    return confluence.update_page(confluence_response['id'], title, page_html, parent_id=parent, type='page', representation='storage', minor_edit=False)



def add_attachments(scope=None):
    """
    Function that adds all redmine wiki page attachments to the corresponding confluence page.
    """
    
    # for a all wiki page attachments
    for attachment in redmine['attachments'].values():

        # skip attachments that are not attached to wiki pages
        if attachment['container_type'] != 'WikiPage':
            continue

        # find the corresponding wiki page object
        page = redmine['wiki_pages'][attachment['container_id']]

        # skip if attachment is not in the scope, if defined
        if scope:
            if scope != page['project_id']:
                continue

        # set empty values to None
        for key in attachment.keys():
            if attachment[key] == '':
                attachment[key] = None

        # unless it's

        # attach the file
        #pdb.set_trace()
        print(f'Adding attachment: {redmine["projects"][page["project_id"]]["name"]} - {page["title"]} : {attachment["filename"]}')
        response = add_attachment(f'{redmine_files}/{attachment["disk_directory"] or ""}/{attachment["disk_filename"]}', confluence_page_id=page['confluence']['id'], file_name=attachment['filename'], content_type=attachment['content_type'],  confluence_page_title=page['title'], confluence_space=page['confluence']['space']['key'], comment=attachment['description'])

        # save the attachment info in the page object
        try:
            page['attachments'].append(response)
        except:
            # first time attaching to this page, initiate a list first
            page['attachments'] = []
            page['attachments'].append(response)




def add_attachment(file_path, confluence_page_id, file_name=None, content_type=None, confluence_page_title=None, confluence_space=None, comment=None):
    """
    Function to add specific file to a specific confluence page
    """
    #pdb.set_trace()
    #return {'results':[{'title':file_name, "_links":{"download":f"https://www.se/{file_name}"}}]}
    return confluence.attach_file(file_path, name=file_name, content_type=content_type, page_id=confluence_page_id, title=confluence_page_title, space=confluence_space, comment=comment)






def create_project_pages(make_html=True, update=False, scope=None):
    """
    Create a page per project. If asked to, generate html and fill the confluence page with. Otherwise just create an empty page to initiate the page structure.
    """

    # if a single project is defined as scope for this run
    if scope:
        projects = [redmine['projects'][scope]]
    else:
        projects = redmine['projects'].values()
    
    # sort and iterate over all projects
#    pdb.set_trace()
    for project in sorted(projects, key=lambda d: d['name']):
        
        # skip projects with no wiki pages
        if 'pages' not in project.keys():
            #print(f"Skipping: no wiki pages, {project['name']}")
            continue

        wiki = get_project_wiki(project['id'])

        # get wiki start page id
        start_page = get_page(wiki['id'], wiki['start_page'])

        # get contents if the start page exist
        if start_page and make_html:
            start_page_html = get_page_html(start_page['id'])
        else:
            start_page_html = ''


        # if updating existing page
        if update:
            print(f"Updating page for project \"{project['name']}\"")
            update_confluence_page(project['confluence'], project['confluence']['title'], start_page_html)
            project['confluence']['updated_html'] = True

        
        # if creating the page
        else:
            print(f"Creating page for project \"{project['name']}\"")
            # save confluence response in the projects object
            try:
                project['confluence'] = create_confluence_page(project['name'], start_page_html)
            except:
                # probably because a page already exists with that name, try adding random suffix
                random_suffix = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=4))
                project['confluence'] = create_confluence_page(project['name'] + f" {random_suffix}", start_page_html)

        #pdb.set_trace()
        # if there is a corresponding start page object, save confluence response to that one as well
        if start_page:
            start_page['confluence'] = project['confluence']




def create_page_pages(make_html=True, update=False, scope=None):
    """
    Wrapper function to create a confluence page per wiki page. This is where prarallellization can be implemented if needed, or a good place to subset the pages to convert for debuggging. 
    """
    if scope:
        # get only pages belonging to the scope
        pages = [page for page in redmine['wiki_pages'].values() if page['project_id'] == scope]
    else:
        pages = redmine['wiki_pages'].values()

    for page in pages:

        # try to create it and all parents recursivly
        create_page_page(page, make_html, update)
        
#        if page['title'] == "Wiki":

            # try to create it and all parents recursivly
#            create_page_page(page, make_html, update)


def create_page_page(page, make_html=True, update=False):
    """
    Function to do the actual creation/updating of a page. If asked to, generate html and fill the confluence page with. Otherwise just create an empty page to initiate the page structure.
    """

#    if page['title'] == "Functional_annotation" or page['title'] == "WebApollo_users_and_invoicing": 
#        pdb.set_trace()

    # check if page is already created
    if not update and 'confluence' in page.keys():
        #print(f"Skipping: already created, \"{page['title']}\"")
        return True

    # check if page is already updated
    if update and 'updated_html' in page['confluence'].keys():
        #print(f"Skipping: already updated, \"{page['title']}\"")
        return True
    
    # try to create parent page
    if page['parent_id']:
        create_page_page(redmine['wiki_pages'][page['parent_id']], make_html, update)
        confluence_parent_id = redmine['wiki_pages'][page['parent_id']]['confluence']['id']

    # assign the projects start page as parent if there is no parent page
    else:
        confluence_parent_id = redmine['projects'][page['project_id']]['confluence']['id']

    # generate html if needed
    if make_html:
        page_html = get_page_html(page['id'])
    else:
        page_html = ''


    # if updating page
    if update:
        print(f"Updating page for page \"{page['title']}\", under project \"{redmine['projects'][page['project_id']]['name']}\"")
        try:
            update_confluence_page(page['confluence'], page['confluence']['title'], page_html)
            page['confluence']['updated_html'] = True
        except:

            # try a different html parser
            try:
                print(f"WARNING: something went wrong when updating page \"{page['title']}\" under project \"{redmine['projects'][page['project_id']]['name']}\". Trying again using alternative html parser (lxml).")
                update_confluence_page(page['confluence'], page['confluence']['title'], str(BeautifulSoup(page_html, features="lxml")))
                page['confluence']['updated_html'] = True
                print(f"SUCCESSFUL: alternative html parser (lxml) fixed the problem.")

            except:
                print(f"SKIPPING: something went wrong when updating page \"{page['title']}\" under project \"{redmine['projects'][page['project_id']]['name']}\"")
                pdb.set_trace()
                pass


    # if creating page
    else:
        # create the page
        print(f"Creating page for page \"{page['title']}\", under project \"{redmine['projects'][page['project_id']]['name']}\"")
        # save confluence response in the projects object
        try:
            page['confluence'] = create_confluence_page(page['title'], page_html, confluence_parent_id)
        except: 
            # probably because a page already exists with that name, try adding random suffix
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=4))
            page['confluence'] = create_confluence_page(page['title'] + f" {random_suffix}", page_html, confluence_parent_id)





def get_page_html(page_id):
    """
    Return the redmine contents converted to html, with fixed links
    """
    # get contents
    contents = get_page_contents(page_id)

    # skip empty pages
    if not contents:
        contents = {'text':''}

    text = contents['text']

    ### replace stuff
    #if page_id == '474':
#    if redmine['wiki_pages'][page_id]['title'].lower() == "Master_Images".lower():
#       pp(text)
#       pdb.set_trace()


    # fix newlines
    text = text.replace('\\r\\n', '\n')
    text = text.replace('\\r', '\n')
    text = text.replace('\\n', '\n')
    text = text.replace('\\t', '\t')

    # escape special html characters
#    text = html.escape(text)

    # escape invalid html tags
    text = fix_invalid_tags(text)

    # fix pre elements
#    text = text.replace('&lt;pre&gt;', '<pre>')
#    text = text.replace('&lt;/pre&gt;', '</pre>')
#    text = text.replace('&quot;', '"')

    # fix links
    text = fix_links(page_id, text)


    # convert to html
    text_html = textile.textile(text)

#    text_html = text_html.replace('<p><pre></p>', '<pre>')
#    text_html = text_html.replace('<p></pre></p>', '</pre>')

#    text = text.replace('<pre>', """<ac:structured-macro ac:name="code">
# <ac:plain-text-body>
#   <![CDATA[""")
#    text = text.replace('</pre>', """
#       ]]>
#  </ac:plain-text-body>
#</ac:structured-macro>""")

    # tidy the html up
    text_html = str(BeautifulSoup(text_html, features='html5lib'))
    #text_html = str(BeautifulSoup(text_html))

    return text_html





def fix_invalid_tags(text):
    """
    Removes all invalid html tags. Used to whitelist allowed tags to make Confluence API happy.
    There was an instance of an email being typed within tags, like <user@domain.com> which it did not like.
    """

    # handle <<EOF notations
    text = re.sub(f"<<", f"&lt;&lt;", text)

    # find all taglike substrings
    matches = re.findall(r'<([^>\n]+)>', text)
    for match in matches: 

#        pdb.set_trace()

        # define whitelite
        tag_whitelist = ['pre', '/pre', 'code', '/code']

        # if it is not in the whitelist, replace it with html escapes
        if match not in tag_whitelist:
            print(f"Tag not in whitelist: <{match}>")

            # escape regex control characters

            # replace the tags with html escapes
            text = re.sub(f"<{re.escape(match)}>", f"&lt;{match}&gt;", text)


    return text


def get_page_contents(page_id):
    """
    Return the contents object for a page
    """
    return redmine['wiki_contents'][redmine['wiki_pages'][page_id]['contents_id']]




def fix_links(source_page_id, html):
    """
    Modify all textile links [[link to something]] to proper html links with valid paths
    """

    # get source page
    source_page = redmine['wiki_pages'][source_page_id]

    # substitute attachment:"file name.pdf" links
    matches = re.findall(r'(attachment:\"[^\"]+\")', html)
    for link_org in matches:

        #pdb.set_trace()

        filename = re.search(r'attachment:\"([^\"]+)\"', link_org).groups()[0]

        # make confluence link
        html_link = f"<a href='{config['url']}/wiki/download/attachments/{source_page['confluence']['id']}/{filename}'>{filename}</a>"

        # replace link
        html = re.sub(f'{re.escape(link_org)}', html_link, html)




    # replace toc tag
    html = re.sub(r'{{>?toc}}', '<p><ac:structured-macro ac:name="toc"/></p>', html, flags=re.IGNORECASE)


    # substitute !image_links!
    matches = re.findall(r'!(\S+)!', html)
    for link_org in matches:

        # skip multiple !, i.e. not an image link but a really loud expression
        match =  re.search(r'^!+$', link_org)
        if match:
            # skip it
            continue
        
        # if a redmine link
        match = re.search(r'projects.nbis.se/attachments/download/(\d+)', link_org)
        if match:

            # pick out attachment from id
            attachment = redmine['attachments'][match[1]]

            # get source page
            attachment_page = redmine['wiki_pages'][attachment['container_id']]

            # make confluence link
            try:
                html_link = f"<img src='{config['url']}/wiki/download/attachments/{attachment_page['confluence']['id']}/{attachment['filename']}'>"
            except KeyError:
                print(f"ERROR: attachment page not found (running with reduced scope?). Source page: {source_page}, Link: {link_org}")
                html_link = link_org
                pass

            # replace link
            html = re.sub(f'!{re.escape(link_org)}!', html_link, html)

        # if http link
        elif link_org.startswith('http://') or link_org.startswith('https://'):

            # it will be replaced automatically by textile
            continue


        # it must be a file name
        else:
            # make confluence link
            html_link = f"<img src='{config['url']}/wiki/download/attachments/{source_page['confluence']['id']}/{link_org}'>"

            # replace link
            html = re.sub(f'!{re.escape(link_org)}!', html_link, html)

        # check if it is a http link to redmine
        print(f"{link_org} -> {html_link}")

    
    # substitute "linkText":http://www.se style links
    matches = re.findall(r'\"([^"]+)\":([\w\-\/\:@\.]+)', html)
    for link_org in matches:

        # check if it is a redmine attachment link
#        pdb.set_trace()
        match = re.search(r'projects\.(bils|nbis)\.se/documents/(\d+)', link_org[1])
        if match:
            attachment_id = match.groups()[1]
            
            try:
                attachment = redmine['attachments'][attachment_id]
            except KeyError:
                
                # the attachment does not exist
                html_link = f"<a href='{link_org[1]}'>INVALID LINK IN REDMINE: {link_org[0]}</a>"
                html = re.sub(f'\"{re.escape(link_org[0])}\":{link_org[1]}', html_link, html)
                continue

            #pdb.set_trace()
            # get source page
            attachment_page = redmine['wiki_pages'][attachment['container_id']]

            # make confluence link
            try:
                html_link = f"<img src='{config['url']}/wiki/download/attachments/{attachment_page['confluence']['id']}/{attachment['filename']}'>{link_org[0]}</a>"
            except KeyError:
                print(f"ERROR: attachment page not found (running with reduced scope?). Source page: {source_page}, Link: {link_org}")
                html_link = f"<a href='{link_org[1]}'>INVALID LINK IN REDMINE: {link_org[0]}</a>"
                pass

#        pdb.set_trace()
        # if it is any other link, just use that one
        else:
            # replace link with html link
            html_link = f'<a href="{link_org[1]}">{link_org[0]}</a>'

        try:
            html = re.sub(f'\"{re.escape(link_org[0])}\":{link_org[1]}', html_link, html)
        except Exception as e:
            print(e)
            pdb.set_trace()




    # substitute [[Page Title]] style links
    matches = re.findall(r'\[\[([^\]]+)\]\]', html)
    for link_org in matches:

        link = link_org.strip() # don't strip the link, whitespace anywhere in the link is seen by redmine as _

#        pdb.set_trace()

        # is there an alternative text in the link?
        link_mod, alt_text = get_link_alt_text(link)

        # is there an anchor in the link? (no need? same syntax in html links)
        link_mod, anchor = get_link_anchor(link_mod)

        # is the link a url?
        if validate_url(link_mod):
            other_wiki = None

        # the link is not a url, is it to another wiki?
        else:
            link_mod, other_wiki = get_link_other_wiki(link_mod)


        # if the remaining link is empty, assume wiki main page
        if not link_mod:
            link_mod = 'Wiki'

        # if it is a valid url
        if validate_url(link_mod):

            # add it as is
            html_link = f"<a href='{link_mod}"

            # check for anchor
            if anchor:
                html_link += anchor

            # end it
            html_link += "'>"

        # if the link is not a valid url, it must be an internal redmine link
        else:

            # init
            target = {}
            html_link = ''
    
            try:
                # if same wiki
                if not other_wiki:
                    target['wiki'] = redmine['wikis'][source_page['wiki_id']]
                    target['project'] = redmine['projects'][source_page['project_id']]
                    target['page'] = get_page(source_page['wiki_id'], link_mod)
    
                else:
                    # get target wiki
                    target['wiki'] = get_wiki_from_project_name(other_wiki)
    
                    # if there is no corresponding wiki with that name
                    if not target['wiki']:
                        target['page'] = None
                        target['project'] = None
            
                    # if there is a wiki with that name
                    else:
                        target['project'] = redmine['projects'][target['wiki']['project_id']]
                        target['page'] = get_page(target['wiki']['id'], link_mod)
               
    
                # if the linked page exists
                if target['page']:
                    try:
                        html_link = f"<a href=\"/wiki/spaces/{config['space_id']}/pages/{target['page']['confluence']['id']}{anchor}\">"
                    except KeyError:
                        # get additional info
                        source_page['wiki'] = redmine['wikis'][source_page['wiki_id']]
                        source_page['project'] = redmine['projects'][source_page['project_id']]
                        source_page['page'] = get_page(source_page['wiki_id'], link_mod)
                        print(f"ERROR in page {source_page['project']['name']} - {source_page['title']}. Linked page ({target['project']['name']} - {target['page']['title']}) is not created in Confluence")
                        raise KeyError
    
                # if the link points to a non-existent wiki page
                else:
                    #print(link_org)
#                    pdb.set_trace()
                    html_link = f"<a href=''>INVALID LINK IN REDMINE: "
    
            except Exception as e:
                print(e)
                if not html_link:
                    #pdb.set_trace()
                    html_link = f"<a href=''>INVALID LINK IN REDMINE: "
                    pass

        if alt_text:
            html_link += alt_text
        else:
            html_link += link_mod
        html_link += "</a>"

        # substitute all occurrences of link
        try:
            # since the alt text pipe symbol will be interpreted by re.sub, it has to be escaped. url|linktext -> url\|linktext
            html = re.sub(re.escape(f'[[{link_org}]]'), html_link, html)
        except Exception as e:
            print(e)
            pdb.set_trace()


#    if redmine['projects'][source_page['project_id']]['name'] == "Internal documents" and source_page['title'] == "Wiki":
#        pdb.set_trace()

    # substitute attachment:"file name.doc" style links
    matches = re.findall(r'attachment:&quot;(.+)&quot;', html)
    for link in matches:

        # init
        confluence_link = None

        # find the right attachment
#        pdb.set_trace()
        for attachment in source_page['attachments']:
            if attachment['results'][0]['title'] == link:

                # create download link
                confluence_link = f"<a href='{config['url']}/wiki{source_page['attachments'][0]['results'][0]['_links']['download']}'>{link}</a>"

#        pdb.set_trace()
        # replace link
        html = re.sub(f'attachment:&quot;{re.escape(link)}&quot;', confluence_link, html)






#href="/wiki/spaces/RED/pages/2091680460/ELIXIR_All-hands_meeting_2015_Travel_report"

    return html



def get_link_alt_text(link):
    """
    Return the link separated from the alternative text, if any
    """
    # is there an alternative text in the link?
    try:
        link, alt_text = link.split('|')
    except ValueError:
        alt_text = None

    return link, alt_text



def get_link_anchor(link):
    """
    Return the link separated from the anchor, if any
    """
    # is there an alternative text in the link?
    try:
        link, anchor = link.split('#')
    except ValueError:
        anchor = ''

    return link, anchor



def get_link_other_wiki(link):
    """
    Return the link separated from the other wiki, if any
    """
    # is there an alternative text in the link?
    try:
        other_wiki, link = link.split(':')
    except ValueError:
        other_wiki = None

    return link, other_wiki





def get_wiki_from_project_name(name):
    """
    Return the wiki for the project with matching title
    """
    for project in redmine['projects'].values():
        if project['name'].lower().replace(' ', '-') == name.lower() or project['identifier'] == name:
            return  redmine['wikis'][project['wiki_id']]

    return None





def get_projid_from_project_name(name):
    """
    Return the project id for the project with matching title
    """
    for project in redmine['projects'].values():
        if project['name'].lower().replace(' ', '-') == name.lower().replace(' ', '-') or project['identifier'] == name:
            return  project['id']

    return None







def fetch_page_info(page_id):
    """
    Print info about a page from page_id. Used for debugging in interactive shell.
    """

    page = redmine['wiki_pages'][page_id]
    project = redmine['projects'][page['project_id']]
    print(f"Name:\t\t{page['title']}\nProject:\t{project['name']}")



def validate_url(text):
    """
    Return True or False depending on if a text is a valid url.
    """
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except:
        return False











# read the atlassian config file
with open(atlassian_config_filename, 'r') as file:
    try:
        config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(exc)

# create a confluence object to communicate with the confluence API
confluence = Confluence(
    url=config['url'],
    username=config['user'],
    password=config['api_token'],
    cloud=True)

#pdb.set_trace()

# remove all existing pages from space
clean_space(config['space_id'])

# v2

### INITIATE STRUCTURE FIRST
# It is needed to 

# get scope id if specified
if scope:
    scope = get_projid_from_project_name(scope)

### initialize page structure before generation any html.
### This is needed because new pages in confluence gets a random id number assigned
### that is used in all links. Can't update any links without having the id's for
### all pages that might get linked to..

# initiate page structure in confluence for all projects with wikis with pages
create_project_pages(make_html=False, scope=scope)

# initiate page structure for all wiki_pages
create_page_pages(make_html=False, scope=scope)

# add attachments to pages
add_attachments(scope=scope)

# do it again, but generate html this time
create_project_pages(make_html=True, update=True, scope=scope)
create_page_pages(make_html=True, update=True, scope=scope)

# pause to have the redmine dict in memory after completeing the run. For debugging.
pdb.set_trace()
