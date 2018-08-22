
= 'Accept Inventory'

This folder, and its corresponding folder in `../../web`, contain the code
necessary for using the order acceptance system.

`/scanner` offers a no-frills scanner experience. It provides feedback to users
scanning with the hand-held bluetooth scanners on phones.

`/watcher` offers an administrative overview page that shows what items are
remaining to be scanned, or otherwise have errors, as well as mechanisms to
manually adjust things.

No matter what, you'll need to finalize the order using the admin interface--
this system just handles, essentially, checking off a list of delivered items.
