# redmine2confluence

## Get the redmine database dump
The database backups are postgresql binary dumps. Fetch a dump file from your server first, then convert it to plain text.

```bash
# download your dump file from the servers backup directory

# convert the dump file to plain sql
docker run -it -v $(pwd):/hostfs postgres:14.1-alpine pg_restore -f /hostfs/databasedump.sql /hostfs/database-20220505-0315.dump
```

## Get your Confluence settings

```yaml
url: "https://yoururl.atlassian.net"                        # the url to your confluence
user: "user@email.com"                                      # the email you login with
api_token: "f4k34p170k3n"                                   # create one at https://id.atlassian.com/manage-profile/security/api-tokens
space_id: "~2546254lhgj62435jlh6g234562fk54h6d24kth536f"    # copy from the url of the space you want to add pages to, https://yoururl.atlassian.net/wiki/spaces/~2546254lhgj62435jlh6g234562fk54h6d24kth536f/overview
```

Write down the confluence settings in config.yaml

## Run the script

Run the `redmine2confluence.py` script and give it the redmine database plain sql file and confluence yaml file as input arguments.

```bash
python3 redmine2confluence.py <redmine sql file> <confluence config file>
```

Sit back and enjoy.

(soon, not finished yet!)


