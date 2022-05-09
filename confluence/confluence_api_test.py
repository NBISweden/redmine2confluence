#from atlassian import Jira
from atlassian import Confluence
#from atlassian import Bitbucket
#from atlassian import ServiceDesk
#from atlassian import Xray
import yaml
import sys
import pdb

usage = f"Usage: python3 {sys.argv[0]} <atlassian config yaml file>"

try:
    atlassian_config_filename = sys.argv[1]
except IndexError:
    print(f"{usage}\n\nERROR: atlassian config yaml file argument missing")
    sys.exit()


with open(atlassian_config_filename, 'r') as file:
    try:
        config = yaml.safe_load(file)
        print(config)
    except yaml.YAMLError as exc:
        print(exc)


confluence = Confluence(
    url=config['url'],
    username=config['user'],
    password=config['api_token'],
    cloud=True)




# get all pages from space
#res = confluence.get_all_pages_from_space(space, start=0, limit=100, status=None, expand=None, content_type='page')

# Create page from scratch
title = "api_created_page_005"
body = '        <p>&nbsp;</p>         <table class="wysiwyg-macro" data-macro-name="code" data-macro-schema-version="1" data-macro-body-type="PLAIN_TEXT"><tr><td class="wysiwyg-macro-body"><pre>aehraeh</pre></td></tr></table><h1>test body</h1><p /><p>&nbsp;</p>'
confluence.create_page(config['space_id'], title, body, parent_id=None, type='page', representation='storage', editor='v2')




