# ProjectManager2
The second version of my project manager.

## Installation
 1. The project manager is built on `Python 3.12.5`
 2. Make venv: `python -m venv venv`; `source venv/bin/activate`
 3. Check: `which python`
 4. Install requirements: `pip install -r requirements.txt`

## Set up a working directory
 1. Choose an empty directory `DIR`
 2. It is recommended to make a git repository and `git clone URL DIR` (this will enable the `backup`-command)
 3. Run the project manager init: `python pm -i DIR`
 4. You can create a backup with the command `backup <enter>`
 5. The backup should have been pushed to github automatically.
 6. Optional: Add the alias `alias pm="<PYTHON-PATH> <THIS-PATH>/pm.py DIR"` to your path to always have the project manager at hand.

## Run
 1. Just run the command `python pm DIR` (or `pm` if you created the alias)
 2. `group *` shows all current projects
 3. If there is no project, create one using `create <PROJECTNAME>`
 4. Remember to `dump` your changes (otherwise they will be lost when quitting), and `backup` regularly

## Different views
 There are two views `group`-view and `open`-view
 The `group`-view shows all projects, while the `open`-view shows the resources of a specific topic
 The `group`-view groups the projects by context (more on that below)

## Linking contexts
 In the project manager there are projects, contexts, and context categories. 
 Projects exist on their own. They can be linked to different contexts. Each context ALWAYS belongs to a category.

#### A simple example:
 Let's assume we have three projects ProjectA, ProjectB, ProjectC.
 ProjectA will be submitted to ConferenceA, ProjectB will be submitted to ConferenceB. 
 Furthermore, MrX is the leading Author of ProjectB and ProjectC.
 This translates into different contexts under two categories:
 - Conferences
    - ConferenceA
    - ConferenceB
 - LeadingAuthor
    - MrX

 All we have to do is to link the projects to the corresponding contexts. The rest will be organized by the manager.
 ```
 create ProjectA
 create ProjectB
 create ProjectC
 link ProjectA Conferences ConferenceA
 link ProjectB Conferences ConferenceB
 link ProjectB LeadingAuthor MrX
 link ProjectC LeadingAuthor MrX
 dump
 ```
 Now we get a nice overview of the different categories and contexts with `f2`, which looks just as intended.
 Furthermore, using `group Conferences` we obtain a list of all projects grouped by the contexts in Conferences, and using `group LeadingAuthor` we obtain the same for the leading authors.
 
 If we want to move ProjectA from ConferenceA to ConferenceB, we can do this by linking `link ProjectA Conference ConferenceB`, and then `unlink ProjectA Conference ConferenceB`.
 Please note before unlinking, ProjectA is assigned to both ConferenceA and ConferenceB.

 Assume there is also a ConferenceC starting soon, which we have no project yet, but we want to keep track of it anyways. 
 Then we can create the context manually using `context-create Conference ConferenceC`.
 If we look into the overview with `f2`, we notice that there is a marker `[?]` for the contexts which are automatically created and no marker for those that are manually added. 

## Resources

 Each Project can hold different resources (currently supported are: `GIT`, `SVN`, `LINK`). 
 To view and modify the resources, we need to be in open mode. 

 Going back to the example above, assume ProjectA has an implementation on Github under the link `<GITHUBLINK>` and a written paper in overleaf under the link `<OVERLEAFLINK>`.
 Lets add them first:
 ```
 open ProjectA
 resource-create Implementation GIT <GITHUBLINK>
 resource-create Paper LINK <OVERLEAFLINK>
 dump
 ```
 
 The resources should appear now in the open-mode view. 
 We can open the link using `resource Paper open`.
 Furthermore, we can clone the git repo with `resource Implementation clone` and let the project manager take care of where to store it.
 Please note that the cloned repo will be kept in a subfolder, and will not automatically be added to our project manager backup repo when we use the `backup` command.
 We can open the cloned resource in vscode using `resource Implementation code`.

## VSCODE-Integration
 This manager integrates vscode as the main application for coding.
 To that end, the resource action `code` as described above is integrated for cloned git repos and for checkouted svn repos.
 Furthermore, using simply the term `code` when the project manager is open, opens the project manager directory `DIR` in vscode and allows manual modifications of the actions and context files, using the yaml format. 
 Please make sure to use the command `reload` when making manual configurations. (Not dumped modifications from the textual user interface will get lost though.)

## Notes
 To keep track of important information for projects and for (manually created) contexts, there are two options:
 - **quicknotes**: a simple one-liner that is added after the project or context name in the overview
 - **notes**: a markdown note that will be added into a subfolder `notes`. The note will be added to the project manager backup repo open the `backup` command.

 To create/modify a quicknote, use the command `qnote <PROJECT> <NOTE>` or `context-qnote <CATEGORY> <CONTEXT>`.
 Note that spaces are allowed in `<NOTE>`, and that the previous quicknote will be overwritten by setting the new quicknote.

 To create/modify a note, use the command `note <PROJECT>` or `context-note <CATEGORY> <CONTEXT>`. 
 This will open the notes folder in vscode and show the corresponding note.
 If the command is run again, it will open the note file again to continue the modification.

## Help 
 - The help menu can be opened via `f1`
