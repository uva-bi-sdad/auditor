# Auditor

1. Loops through all folders that match ```**/distribution/``` and creates a ```manifest.json``` at the root directory with the: hash, file size (bytes), and file path of each file.
2. For each file added, search if there is a ```measures_info.json``` in the same directory, and check for a string match of the measure and the file name. If there is a match, append the data match from the ```measures_info.json``` on to the element in ```manifest.json```.

Timeline:
---
- **2022-09-07**: Auditor bug-fixes; split on ':' inside measure_info, and split on '.' for filename
- **2022-08-29**: Add auditor and test one repo versus two repo models
- **2022-08-23**: In the generation of the manifest, add in measure info data
- **2022-08-04**: Check the data repository is created in the right format and create a manifest.json file

Notes:
---
- Overleaf notes: https://www.overleaf.com/project/6306378e38071b727de6293e

Action references:
---
- Dataverse-uploader action: https://github.com/IQSS/dataverse-uploader
- Copy files to other repos action: https://github.com/derberg/copy-files-to-other-repositories
