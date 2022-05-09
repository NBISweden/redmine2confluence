import sys
import os
import re
import pdb

usage = f"Usage: python3 {sys.argv[0]} <redmine database dump file> <atlassian config yaml file>"

try:
    sql_filename = sys.argv[1]
except IndexError:
    print(f"{usage}\n\nERROR: sql file argument missing")
    sys.exit()



#TODO
# * handle wiki page attachments



#               _           _                               _
#  _ __ ___  __| |_ __ ___ (_)_ __   ___   _ __   __ _ _ __| |_
# | '__/ _ \/ _` | '_ ` _ \| | '_ \ / _ \ | '_ \ / _` | '__| __|
# | | |  __/ (_| | | | | | | | | | |  __/ | |_) | (_| | |  | |_
# |_|  \___|\__,_|_| |_| |_|_|_| |_|\___| | .__/ \__,_|_|   \__|
#                                         |_|
# redmine part



# init
wiki_contents   = {}
wiki_pages      = {}
wikis           = {} 
projects        = {}
users           = {}
mode = "searching"
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
                mode = "collect_contents"
                schema = line.strip()
                continue

            # if wiki_pages is found
            if line.startswith("COPY public.wiki_pages "):
                mode = "collect_pages"
                schema = line.strip()
                continue

            # if wikis is found
            if line.startswith("COPY public.wikis "):
                mode = "collect_wikis"
                schema = line.strip()
                continue

            # if wikis is found
            if line.startswith("COPY public.projects "):
                mode = "collect_projects"
                schema = line.strip()
                continue

            # if wikis is found
            if line.startswith("COPY public.users "):
                mode = "collect_users"
                schema = line.strip()
                continue
#           _ _    _                   _             _       
# __      _(_) | _(_)   ___ ___  _ __ | |_ ___ _ __ | |_ ___ 
# \ \ /\ / / | |/ / |  / __/ _ \| '_ \| __/ _ \ '_ \| __/ __|
#  \ V  V /| |   <| | | (_| (_) | | | | ||  __/ | | | |_\__ \
#   \_/\_/ |_|_|\_\_|  \___\___/|_| |_|\__\___|_| |_|\__|___/
#                                                            
# wiki contents

        # if in content collection mode
        elif mode == "collect_contents":

            if line == '\.':
                print(f"Leaving collect_contents, {line}")
                mode = "searching"
                continue
            
            # pick out digits
            content_id, page_id, author_id, text, comments, updated_on, version = line.split('\t')

            # save info
            wiki_contents[content_id] = {}
            wiki_contents[content_id]['page_id'] = page_id
            wiki_contents[content_id]['author_id'] = author_id
            wiki_contents[content_id]['text'] = text
            wiki_contents[content_id]['comments'] = comments
            wiki_contents[content_id]['updated_on'] = updated_on
            wiki_contents[content_id]['version'] = version




#           _ _    _
# __      _(_) | _(_)  _ __   __ _  __ _  ___  ___
# \ \ /\ / / | |/ / | | '_ \ / _` |/ _` |/ _ \/ __|
#  \ V  V /| |   <| | | |_) | (_| | (_| |  __/\__ \
#   \_/\_/ |_|_|\_\_| | .__/ \__,_|\__, |\___||___/
#                     |_|          |___/
# wiki pages

        # if page collection mode
        elif mode == "collect_pages":

            if line == '\.':
                print(f"Leaving collect_pages, {line}")
                mode = "searching"
                continue

            # pick out values
            page_id, wiki_id, title, created_on, protected, parent_id = line.split('\t')

            # save the page info
            wiki_pages[page_id] = {}
            wiki_pages[page_id]['wiki_id'] = wiki_id
            wiki_pages[page_id]['title'] = text
            wiki_pages[page_id]['created_on'] = created_on
            wiki_pages[page_id]['protected'] = protected
            wiki_pages[page_id]['parent_id'] = parent_id




#           _ _    _     
# __      _(_) | _(_)___ 
# \ \ /\ / / | |/ / / __|
#  \ V  V /| |   <| \__ \
#   \_/\_/ |_|_|\_\_|___/
#                        
# wikis

        # if wiki collection mode
        elif mode == "collect_wikis":

            if line == '\.':
                print(f"Leaving collect_wikis, {line}")
                mode = "searching"
                continue

            # split line and collect values
            wiki_id, project_id, start_page, status = line.split('\t')

            # save wiki
            wikis[wiki_id] = {}
            wikis[wiki_id]['project_id'] = project_id
            wikis[wiki_id]['start_page'] = start_page
            wikis[wiki_id]['status'] = status






#                  _           _       
#  _ __  _ __ ___ (_) ___  ___| |_ ___ 
# | '_ \| '__/ _ \| |/ _ \/ __| __/ __|
# | |_) | | | (_) | |  __/ (__| |_\__ \
# | .__/|_|  \___// |\___|\___|\__|___/
# |_|           |__/                   
# projects

        # if project collection mode
        elif mode == "collect_projects":

            if line == '\.':
                print(f"Leaving collect_projects, {line}")
                mode = "searching"
                continue
            
            # split line and collect values
            project_id, name, description, homepage, is_public, parent_id, created_on, updated_on, identifier, status, lft, rgt, inherit_members, default_version_id, default_assigned_to_id = line.split('\t')

            # save project
            projects[project_id] = {}
            projects[project_id]['name'] = name
            projects[project_id]['description'] = description
            projects[project_id]['homepage'] = homepage
            projects[project_id]['is_public'] = is_public
            projects[project_id]['parent_id'] = parent_id
            projects[project_id]['created_on'] = created_on
            projects[project_id]['updated_on'] = updated_on
            projects[project_id]['identifier'] = identifier
            projects[project_id]['status'] = status
            projects[project_id]['lft'] = lft
            projects[project_id]['rgt'] = rgt
            projects[project_id]['inherit_members'] = inherit_members
            projects[project_id]['default_version_id'] = default_version_id
            projects[project_id]['default_assigned_to_id'] = default_assigned_to_id









#
#  _   _ ___  ___ _ __ ___
# | | | / __|/ _ \ '__/ __|
# | |_| \__ \  __/ |  \__ \
#  \__,_|___/\___|_|  |___/
#
# users

        # if wiki collection mode
        elif mode == "collect_users":

            if line == '\.':
                print(f"Leaving collect_wikis, {line}")
                mode = "searching"
                continue
            
            # split line and collect values
            user_id, login, hashed_password, firstname, lastname, admin, status, last_login_on, language, auth_source_id, created_on, updated_on, type, identity_url, mail_notification, salt, must_change_passwd, passwd_changed_on, twofa_scheme, twofa_totp_key, twofa_totp_last_used_at = line.split('\t')

            # save 
            users[user_id] = {}
            users[user_id]['login'] = login
            users[user_id]['firstname'] = firstname
            users[user_id]['lastname'] = lastname

















#        _   _               _                                _   
#   __ _| |_| | __ _ ___ ___(_) __ _ _ __    _ __   __ _ _ __| |_ 
#  / _` | __| |/ _` / __/ __| |/ _` | '_ \  | '_ \ / _` | '__| __|
# | (_| | |_| | (_| \__ \__ \ | (_| | | | | | |_) | (_| | |  | |_ 
#  \__,_|\__|_|\__,_|___/___/_|\__,_|_| |_| | .__/ \__,_|_|   \__|
#                                           |_|                   
# atlassian part







