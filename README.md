# Auditor

1. Loops through all folders that match ```**/distribution/``` and creates a ```manifest.json``` at the root directory with the: hash, file size (bytes), and file path of each file.
2. For each file added, search if there is a ```measures_info.json``` in the same directory, and check for a string match of the measure and the file name. If there is a match, append the data match from the ```measures_info.json``` on to the element in ```manifest.json```.

Thought process:
---
| Design | Pros | Cons | Mitigation
| ---  | --- | --- | ---| 
| One public branch, default to main, with a development branch with data | Users can pull the data directly | Developers need to switch a branch before developing | Preventing a push to main would signal them to switch branches |
|One public branch, default to development, with a distribution branch | Developers can develop on the main branch directly | <ol> <li> Users need to switch to the distribution branch to pull the repo without the extra data</li> <li>Developers can accidentally push to the main branch</li></ol> | <ol><li>Can probably include a link in the README to the main branch</li><li>Can set a restriction on who pushes to the distribution branch to prevent accidental pushing and needing to merge backwards</li></ol> |
| Two repos both public | Developers can develop directly, and users can pull directly from the repo | <ol><li> Users can see both branches and accidentally pull the one with data </li><li> Two branches are created for each repository </li></ol> | <ol><li>Can add in the README link to the data-less repo, or have a website that just points to the repos separately, or the name of the repo can include the type of repo it is </li></ol> |
|Two repos, one public one private | Users can pull the data directly, and developers can develop on the main branch directly | Loses transparency | The public repo can have a development branch that is one-to-one with the main branch of the private repo |

Timeline:
---
- **2022-09-14**: Updating to track md5 on all files, but not check for measures unless it matches suffixes in the settings
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
