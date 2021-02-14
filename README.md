# mygcc-utils
Tools for programmatically interfacing with https://my.gcc.edu/

> Note: this repository is still very much WIP and updates may include significant or breaking changes to this program's structure.

## Examples

Printing your name

```py
from gccutils.mygcc import MyGcc
import getpass

# obtain user credentials
username = input('Username: ')
password = getpass.getpass()

# fetch name from mygcc
gcc = MyGcc(username, password)
name = gcc.profile.name

# print the name
print(name)
```

Printing all available courses

```py
from gccutils.mygcc import MyGcc
import getpass

def callback(course):
    print(f'[{course.term}] {course.code} - {course.name} - {course.requisites}')

# obtain user credentials
username = input('Username: ')
password = getpass.getpass()

# fetch the course scraper
gcc = MyGcc(username, password)
scraper = gcc.academics.get_course_scraper(callback)

# start the scraper
scraper.start()
```

Printing your chapel requirements

```py
from gccutils.mygcc import MyGcc
import getpass

# obtain user credentials
username = input('Username: ')
password = getpass.getpass()

# fetch chapel info from mygcc
gcc = MyGcc(username, password)
chapel = gcc.student.chapel

# print the chapel info
print(chapel)
```