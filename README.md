# redmine2confluence

Tool to convert the contents of all Redmine project wikis to a mix of plain HTML and [Confluence](https://www.atlassian.com/software/confluence) XML elements, and upload all converted pages and attachments to a single Confluence space. Each Redmine project will correspond to a page in a Confluence space, and all wiki pages from the Redmine project will be subpages to that page. The page structure in Redmine will be kept the same using subpages in Confluence.

## Get the redmine database dump
The database backups are postgresql binary dumps. Fetch a dump file from your server first, then convert it to a plain text sql file that can be parsed easily.

```bash
# download your dump file from the servers backup directory

# convert the dump file to plain sql
docker run -it -v $(pwd):/hostfs postgres:14.1-alpine pg_restore -f /hostfs/databasedump.sql /hostfs/database-20220505-0315.dump
```

## Download the Redmine attachment folder
To be able to upload attachments you must have all the attachment files. Look for the folder `files` in the root of your Redmine installation and download it.

## Get your Confluence settings

```yaml
url: "https://yoururl.atlassian.net"                        # the url to your confluence
user: "user@email.com"                                      # the email you login with
api_token: "f4k34p170k3n"                                   # create one at https://id.atlassian.com/manage-profile/security/api-tokens
space_id: "~2546254lhgj62435jlh6g234562fk54h6d24kth536f"    # copy from the url of the space you want to add pages to, https://yoururl.atlassian.net/wiki/spaces/~2546254lhgj62435jlh6g234562fk54h6d24kth536f/overview
```

Write down the confluence settings in config.yaml

## Run the script

Run the `redmine2confluence.py` script and give it the redmine database plain sql file, confluence config yaml file, and redmine attachments folder root as input arguments. A name of a redmine project can be given as a 4th argument to limit the conversion to a single project's wiki.

```bash
python3 redmine2confluence.py <redmine database dump file> <atlassian config yaml file> <redmine attachments folder root> [<redmine project name to limit conversion to>]
```

Sit back and enjoy.
