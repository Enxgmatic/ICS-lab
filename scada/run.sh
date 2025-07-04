#!/bin/bash
# persistent storage of application data (project), daq (tags history), logs and images (resource)
docker run -d -p 1881:1881 --restart=always -v fuxa_appdata:/usr/src/app/FUXA/server/_appdata -v fuxa_db:/usr/src/app/FUXA/server/_db -v fuxa_logs:/usr/src/app/FUXA/server/_logs -v fuxa_images:/usr/src/app/FUXA/server/_images frangoteam/fuxa:latest