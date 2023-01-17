"""
Yes, another duplicate file finder with Python...

There are various approaches to finding duplicate files using Python, but
when working with a large number of files, such as 2400 files, a simple
script may be inefficient and may consume a large amount of memory,
potentially causing the environment to crash. In this case, we tried using a
tool, but found that the analysis process was time-consuming and the user
interface was not very efficient.

In my opinion, a duplicate file is one that has the same content as another
file, which can be determined by comparing its size and hash value. As a
solution, we decided to use Python to filter the files by size and to
enhance the hash step using the xxhash library. This allowed us to
effectively identify and handle duplicate files in a more efficient manner.


Whats this script do:
- file duplicate analysis
- report through the ssh
- dump a JSON file

What this script dont do:
- delete files
- make the cofee
- bitcoin analysis

"""
