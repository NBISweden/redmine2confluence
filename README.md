# redmine2confluence

## Get the redmine database dump
The database backups are postgresql binary dumps. Fetch a dump file from your server first, then convert it to plain text.

```bash
# download your dump file

# convert the dump file to plain sql
docker run -it -v $(pwd):/hostfs postgres:14.1-alpine pg_restore -f /hostfs/databasedump.sql /hostfs/database-20220505-0315.dump
```











