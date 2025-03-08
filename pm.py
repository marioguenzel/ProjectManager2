import yaml
import argparse
from pathlib import Path
import os
import time
import re

from prompt_toolkit import Application
from prompt_toolkit.completion import CompleteEvent,WordCompleter, NestedCompleter,Completion
from typing import Iterable
from prompt_toolkit.document import Document
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import TextArea

HELP_MESSAGE = """
    ### All modes (OPEN and GROUP) ###
    # TUI handling
        open <PROJECT>               -> open a project and show its resources
        group <CATEGORY>             -> open the group view with category (use 'group *' to show all projects without grouping)
        filter <CATEGORY> <CONTEXT>  -> only show projects with that context
        filter-remove                -> remove all filters

        note <PROJECT>                     -> open markdown note
        context-note <CATEGORY> <CONTEXT>  -> open markdown note 

        backup  -> push changes to git (git -A commit; push)
        code    -> Open vscode of the folder to make modifications manually
        reload  -> Make sure to reload when making manual modifications

        resource <PROJECT> <RESOURCE> <ACTION>  -> do action for resource
        show-resources  -> toggle whether to show resources in group view
        
    # Modifications
        dump    -> Dump changes to file 
        create <PROJECT>      -> create a new project
        delete <PROJECT>      -> delete a projects
        link <PROJECT> <CATEGORY> <CONTEXT>    -> Create a new link
        unlink <PROJECT> <CATEGORY> <CONTEXT>  -> Remove a link

        context-create <CATEGORY> <CONTEXT>   -> create a new context (automatically adds category)
        context-delete <CATEGORY> <CONTEXT>   -> delete a context
        category-create <CATEGORY>  -> create a new category
        category-delete <CATEGORY>  -> deleta a category

        resource-create <PROJ> <RESOURCE> <TYPE> <SOURCE>  -> create a resource with name RESOURCE of TYPE with SOURCE for PROJ
        resource-delete <PROJ> <RESOURCE>                  -> delete a resource

        qnote <PROJECT> <TEXT>                     -> modify quicknote
        qnote-delete <PROJECT>                     -> modify quicknote
        context-qnote <CATEGORY> <CONTEXT> <TEXT>  -> modify quicknote 
        context-qnote-delete <CATEGORY> <CONTEXT>  -> modify quicknote 

    ### In OPEN-mode only ###
    (<PROJECT> is left out for commands:)

        resource <RESOURCE> <ACTION>                -> do action for resource
        resource-create <RESOURCE> <TYPE> <SOURCE>  -> create a resource with name RESOURCE of TYPE with SOURCE
        resource-delete <RESOURCE>                  -> delete a resource

    ### ACTIONS ###
        - SVN: code, checkout
        - GIT: code, clone
        - LINK: open

    ### KEYBINDINGS ###
        + ctrl-q  -> Quit
        + f1      -> Show help
        + f2      -> Show categories
        + esc     -> scroll to top

    ### To be added someday ###
        archive <PROJECT>     -> archive a project
        unarchive <PROJECT>   -> unarchive a project
"""

NOTES_SUBPATH = 'notes'
RESOURCES_SUBPATH = 'resources'

COMMANDS = [
    'open',
    'group',
    'filter',
    'filter-remove',
    'note',
    'context-note',
    'create',
    'delete',
    'archvie',
    'unarchive',
    'link',
    'unlink',
    'context-create',
    'context-delete',
    'category-create',
    'category-delete',
    'qnote',
    'context-qnote',
    'qnote-delete',
    'context-qnote-delete',
    'code',
    'reload',
    'dump',
    'backup',
    'resource',
    'resource-create',
    'resource-delete',
    'show-resources',

    'SVN',
    'GIT',
    'LINK',

    'checkout',
    'clone',
    'open',
    ]

class Data:
    """Data loading, dumping and modification"""
    def __init__(self, LOCATION: Path):
        self.LOCATION = LOCATION
        self.Projects = dict()
        self.Contexts = dict()
        self.load()
    
    # Loading and Dumping
    def load(self):
        self.Projects = dict()
        with open(os.path.join(self.LOCATION,'Active_Projects.yaml'), 'r') as infile:
            self.Projects = yaml.safe_load(infile)
        with open(os.path.join(self.LOCATION,'Active_Contexts.yaml'), 'r') as infile:
            self.Contexts = yaml.safe_load(infile)

        if not self.Projects:
            self.Projects = dict()
        if not self.Contexts:
            self.Contexts = dict()
    
    def dump(self):
        with open(os.path.join(self.LOCATION,'Active_Projects.yaml'), 'w') as outfile:
            yaml.dump(self.Projects, outfile)
        with open(os.path.join(self.LOCATION,'Active_Contexts.yaml'), 'w') as outfile:
            yaml.dump(self.Contexts, outfile)

    # Get Information
    def get_categories(self):  # get all categories
        all_categories = []

        for proj in self.Projects.keys():
            if 'links' in self.Projects[proj]:
                for key in self.Projects[proj]['links'].keys():
                    if key not in all_categories:
                        all_categories.append(key)
        
        for key in self.Contexts:
            if key not in all_categories:
                all_categories.append(key)
        
        all_categories.sort()
        return all_categories

    def get_contexts(self, cat):  # get contexts of a specific category
        all_contexts = []
        for proj in self.Projects.keys():
            if 'links' in self.Projects[proj] and cat in self.Projects[proj]['links']:
                for context in self.Projects[proj]['links'][cat]:
                    if context not in all_contexts:
                        all_contexts.append(context)
        
        if cat in self.Contexts:
            for context in self.Contexts[cat]:
                if context not in all_contexts:
                    all_contexts.append(context)

        all_contexts.sort()
        return all_contexts

    def get_resources(self, project):  # list of resources for a project
        assert project in self.Projects

        return self.Projects[project]['resources'].keys() if 'resources' in self.Projects[project] else []

    def check_context(self, proj, cat, context):  # check if project links to specific context
        return proj in self.Projects and 'links' in self.Projects[proj] and cat in self.Projects[proj]['links'] and context in self.Projects[proj]['links'][cat]

    def check_no_context(self, proj, cat):  # check if project has no context from that category
        return 'links' not in self.Projects[proj] or cat not in self.Projects[proj]['links'] or not bool(self.Projects[proj]['links'][cat])
    
    def check_context_in_data(self, cat, context):  # Check if context exists already in data
        return bool(self.Contexts) and cat in self.Contexts and context in self.Contexts[cat]


    # Moodification
    def add_project(self, name: str):
        assert name not in self.Projects
        self.Projects[name] = dict()
    
    def remove_project(self, name: str):
        assert name in self.Projects

        del self.Projects[name]
    
    def add_category(self, name):
        if name not in self.Contexts:
            self.Contexts[name] = dict()
    
    def remove_category(self, name):
        if name in self.Contexts:
            del self.Contexts[name]
    
    def add_context(self, cat, context):
        if cat not in self.Contexts:
            self.add_category(cat)
        if context not in self.Contexts[cat]:
            self.Contexts[cat][context] = dict()
    
    def remove_context(self, cat, context):
        assert cat in self.Contexts and context in self.Contexts[cat]
        del self.Contexts[cat][context]

    def add_resource(self, proj, res_name, res_type, res_source):
        assert proj in self.Projects
        if 'resources' not in self.Projects[proj]:
            self.Projects[proj]['resources'] = dict()
        assert res_name not in self.Projects[proj]['resources']
        self.Projects[proj]['resources'][res_name] = {'type': res_type, 'source': res_source}
    
    def remove_resource(self, proj, res_name):
        assert proj in self.Projects and res_name in self.Projects[proj]['resources']
        del self.Projects[proj]['resources'][res_name]

    def link(self, project, category, context):
        assert project in self.Projects
        if 'links' not in self.Projects[project]:
            self.Projects[project]['links'] = dict()
        if category not in self.Projects[project]['links']:
            self.Projects[project]['links'][category] = []

        self.Projects[project]['links'][category].append(context)
    
    def unlink(self, project, category, context):
        assert project in self.Projects
        assert category in self.Projects[project]['links']
        assert context in self.Projects[project]['links'][category]
        
        self.Projects[project]['links'][category].remove(context)
        if len(self.Projects[project]['links'][category]) == 0:
            del self.Projects[project]['links'][category]
    
    def set_qnote_project(self, project, text):
        assert project in self.Projects
        self.Projects[project]['qnote'] = text
    
    def set_qnote_context(self, category, context, text):
        assert category in self.Contexts
        assert context in self.Contexts[category]
        self.Contexts[category][context]['qnote'] = text

    def open_note_project(self, project):
        assert project in self.Projects
        notes_path =  os.path.join(self.LOCATION, NOTES_SUBPATH)
        filename = str(project) + '.md'
        file_path = os.path.join(notes_path, filename)
        if not os.path.exists(notes_path):
            os.makedirs(notes_path)
        if not os.path.isfile(file_path):
            with open(file_path, 'w+') as f:
                pass
        os.system(f"code -g '{file_path}' -n '{notes_path}'")

    def open_note_context(self, category, context):
        assert category in self.Contexts
        assert context in self.Contexts[category]

        notes_path =  os.path.join(self.LOCATION, NOTES_SUBPATH)
        category_path = os.path.join(notes_path, category)
        file_path = os.path.join(category_path, str(context) + '.md')

        if not os.path.exists(notes_path):
            os.makedirs(notes_path)
        if not os.path.exists(category_path):
            os.makedirs(category_path)
        if not os.path.isfile(file_path):
            with open(file_path, 'w+') as f:
                pass
        os.system(f"code -g '{file_path}' -n '{notes_path}'")

    def resource_action(self, project, resource, action):
        assert project in self.Projects
        assert 'resources' in self.Projects[project]
        assert resource in self.Projects[project]['resources']

        resource_dict = self.Projects[project]['resources'][resource]

        gen_resource_path = os.path.join(self.LOCATION, RESOURCES_SUBPATH)
        this_resource_path = os.path.join(gen_resource_path, project, resource)

        if not os.path.exists(gen_resource_path):
            os.makedirs(gen_resource_path)

        if action == 'clone' and resource_dict['type'] == 'GIT':
            if not os.path.exists(this_resource_path):  # Make directory
                os.makedirs(this_resource_path)
            os.system(f"git clone {resource_dict['source']} '{this_resource_path}'")
        elif action == 'checkout' and resource_dict['type'] == 'SVN':
            if not os.path.exists(this_resource_path):  # Make directory
                os.makedirs(this_resource_path)
            os.system(f"svn checkout {resource_dict['source']} '{this_resource_path}'")
        elif action == 'code':
            os.system(f"code '{this_resource_path}'")
        elif action == 'open':
            os.system(f"open '{resource_dict['source']}'")
        else:
            raise ValueError(f"Action {action} is not available for resource of type {resource_dict['type']}")


class TUIManager:
    """Manages how to show the data."""
    def __init__(self, DATA: Data):
        self.CONTENT = DATA
        self.mode = 'group'  # Can be show or group 
        self.mode_content = '*'  # Category or Project
        self.filter = []
        self.line_start = 0  # show from beginning by default
        self.unsafed_changes = False
        
        self.help_message_visible = False # help message
        self.help_message_line = 0

        self.cat_list_visible = False # category and context list
        self.cat_list_line = 0

        self.show_resources = False  # show resources in group view
    
    def context_str(self, cat, context):
        exists_in_file = ' [?]'
        qnote = ''
        if self.CONTENT.check_context_in_data(cat, context):
            exists_in_file = ''
            if 'qnote' in self.CONTENT.Contexts[cat][context] and self.CONTENT.Contexts[cat][context]['qnote'] != '':
                qnote = '  (' + self.CONTENT.Contexts[cat][context]['qnote'] + ')'
        
        notepath = os.path.join(self.CONTENT.LOCATION, NOTES_SUBPATH, str(cat), str(context) + '.md')
        note = ' [N]' if os.path.isfile(notepath) else ''

        return f"{context}{note}{exists_in_file}{qnote}"
    
    def project_str(self, project):
        assert project in self.CONTENT.Projects
        qnote = ''
        note = ' [N]' if os.path.isfile(os.path.join(os.path.join(self.CONTENT.LOCATION, NOTES_SUBPATH), str(project) + '.md')) else ''
        if 'qnote' in self.CONTENT.Projects[project] and self.CONTENT.Projects[project]['qnote'] != '':
            qnote = '  (' + self.CONTENT.Projects[project]['qnote'] + ')'

        return f"{project}{note}{qnote}"
    
    def resources_str(self, project, resource):
        assert project in self.CONTENT.Projects
        assert 'resources' in self.CONTENT.Projects[project]
        assert resource in self.CONTENT.Projects[project]['resources']

        resource_dict = self.CONTENT.Projects[project]['resources'][resource]

        gen_resource_path = os.path.join(self.CONTENT.LOCATION, RESOURCES_SUBPATH)
        this_resource_path = os.path.join(gen_resource_path, project, resource)

        cloned = ''
        if os.path.exists(this_resource_path):
            cloned = " [C]"
        
        return f"{resource_dict['type']}: {resource}{cloned} ({resource_dict['source']})"



    def return_main_text(self):
        if self.help_message_visible:
            text_rows = HELP_MESSAGE.splitlines()
            return '\n'.join(text_rows[self.help_message_line:])
        
        elif self.cat_list_visible:
            text_rows = []
            for cat in self.CONTENT.get_categories():
                text_rows.append(f"# {cat}")
                for context in self.CONTENT.get_contexts(cat):
                    text_rows.append(f" - {self.context_str(cat, context)}")
                text_rows.append(' ')
            return '\n'.join(text_rows[self.cat_list_line:])
        
        elif self.mode == 'open':  # Open Mode
            open_proj = self.CONTENT.Projects[self.mode_content]  # dict of the project that is open
            text_rows = []
            text_rows.append(f"### {self.project_str(self.mode_content)} ###")
            if 'resources' not in open_proj or not bool(open_proj['resources']):
                text_rows.append('(No Resources)')
            else:
                for res in open_proj['resources']:
                    text_rows.append(f" - {self.resources_str(self.mode_content,res)}")
            return '\n'.join(text_rows)  # No Scrolling functionality for resources currently
        
        elif self.mode == 'group':  # Group Mode
            if self.mode_content == '*':
                text_rows = []
                for proj in self.CONTENT.Projects:
                    if all([self.CONTENT.check_context(proj,f1,f2) for f1,f2 in self.filter]):
                        text_rows.append('- ' + self.project_str(proj))
                        if self.show_resources:
                            for res in self.CONTENT.get_resources(proj):
                                text_rows.append('  - ' + self.resources_str(proj,res))
                return '\n'.join(text_rows[self.line_start:])
            
            elif self.mode_content in self.CONTENT.get_categories():
                text_rows = []
                contexts = self.CONTENT.get_contexts(self.mode_content)
                for con in contexts:
                    text_rows.append(f"# {self.context_str(self.mode_content,con)}")
                    for proj in self.CONTENT.Projects:
                        if all([self.CONTENT.check_context(proj,f1,f2) for f1,f2 in self.filter]):
                            if self.CONTENT.check_context(proj,self.mode_content,con):
                                text_rows.append(f" - {self.project_str(proj)}")
                                if self.show_resources:
                                    for res in self.CONTENT.get_resources(proj):
                                        text_rows.append('  - ' + self.resources_str(proj,res))
                    text_rows.append(f" ")
                text_rows.append(f"# (Ungrouped)")
                for proj in self.CONTENT.Projects:
                    if all([self.CONTENT.check_context(proj,f1,f2) for f1,f2 in self.filter]):
                        if self.CONTENT.check_no_context(proj, self.mode_content):
                            text_rows.append(f" - {self.project_str(proj)}")
                            if self.show_resources:
                                for res in self.CONTENT.get_resources(proj):
                                    text_rows.append('  - ' + self.resources_str(proj,res))

                return '\n'.join(text_rows[self.line_start:])

        else:
            return '(Data cannot be presented)'
    
    def return_head_text(self):
        return f"=== ProjectManager2 ===  Mode: '{self.mode} {self.mode_content}' | Showing Resources: {self.show_resources} | Filters: {self.filter} | {'All safed' if not self.unsafed_changes else '>Unsafed Changes<'}{' | HELP-VIEW' if self.help_message_visible else ''}{' | CONTEXT-OVERVIEW' if self.cat_list_visible else ''} ==="

    def autocomplete_suggestions(self):
        suggestions = []
        suggestions.extend(COMMANDS)
        for proj in self.CONTENT.Projects.keys():
            suggestions.append(proj)
            for res in self.CONTENT.get_resources(proj):
                suggestions.append(res)
        suggestions.extend(self.CONTENT.get_categories())
        for cat in self.CONTENT.get_categories():
            suggestions.extend(self.CONTENT.get_contexts(cat))
        suggestions.sort()
        return suggestions
    
    def autocomplete_dict_suggestions(self):
        projects_dict = {proj: None for proj in sorted(self.CONTENT.Projects.keys())}
        categories_dict = {cat: None for cat in sorted(self.CONTENT.get_categories())}
        categories_contexts_dict = {cat: {con: None for con in sorted(self.CONTENT.get_contexts(cat))} for cat in sorted(self.CONTENT.get_categories())}
        projects_resources_dict = {proj: {res: None for res in sorted(self.CONTENT.get_resources(proj))} for proj in sorted(self.CONTENT.Projects.keys())}
        def resources(proj):
            return {res: None for res in sorted(self.CONTENT.get_resources(proj))}
        def resources_actions(proj):
            return {res: {'code': None,'clone': None,'checkout': None,'open': None} for res in sorted(self.CONTENT.get_resources(proj))}
        projects_resources_actions_dict = {proj: resources_actions(proj) for proj in sorted(self.CONTENT.Projects.keys())}
        projects_categories_contexts_dict = {proj: categories_contexts_dict for proj in sorted(self.CONTENT.Projects.keys())}

        complete_dict = {
            'open': projects_dict,
            'group': categories_dict,
            'filter': categories_contexts_dict,
            'filter-remove': None,
            'note': projects_dict,
            'context-note': categories_contexts_dict,
            'backup': None,
            'code': None,
            'reload': None,
            'show-resources': None,
            'dump': None,
            'create': None,
            'delete': projects_dict,
            'link': projects_categories_contexts_dict,
            'unlink': projects_categories_contexts_dict,
            'context-create': categories_contexts_dict,
            'context-delete': categories_contexts_dict,
            'category-create': categories_dict,
            'category-delete': categories_dict,
            'qnote': projects_dict,
            'qnote-delete': projects_dict,
            'context-qnote': categories_contexts_dict,
            'context-qnote-delete': categories_contexts_dict,
        }
        if self.mode == 'open':
            open_proj = self.mode_content
            complete_dict['resource'] = resources_actions(open_proj)
            complete_dict['resource-create'] = None
            complete_dict['resource-delete'] = resources(open_proj)
        else:
            complete_dict['resource'] = projects_resources_actions_dict
            complete_dict['resource-create'] = projects_dict
            complete_dict['resource-delete'] = projects_resources_dict

        complete_dict = dict(sorted(complete_dict.items()))
        return complete_dict

def CommandParser(data: Data, tuimanager: TUIManager, args):
    if args[0] == 'code':
        os.system(f"code '{data.LOCATION}'")
    elif args[0] == 'reload':
        data.load()
    elif args[0] == 'dump':
        data.dump()
        tuimanager.unsafed_changes = False
    elif args[0] == 'create':
        data.add_project(args[1])
        tuimanager.unsafed_changes = True
    elif args[0] == 'delete':
        data.remove_project(args[1])
        tuimanager.unsafed_changes = True
    elif args[0] == 'open':
        assert args[1] in data.Projects
        tuimanager.mode = 'open'
        tuimanager.mode_content = args[1]
        tuimanager.line_start = 0
    elif args[0] == 'group':
        assert args[1] == '*' or args[1] in data.get_categories() 
        tuimanager.mode = 'group'
        tuimanager.mode_content = args[1]
        tuimanager.line_start = 0
    elif args[0] == 'context-create':
        data.add_context(args[1], args[2])
        tuimanager.unsafed_changes = True
    elif args[0] == 'context-delete':
        data.remove_context(args[1], args[2])
        tuimanager.unsafed_changes = True
    elif args[0] == 'category-create':
        data.add_category(args[1])
        tuimanager.unsafed_changes = True
    elif args[0] == 'category-delete':
        data.remove_category(args[1])
        tuimanager.unsafed_changes = True
    elif args[0] == 'link':
        data.link(args[1], args[2], args[3])
        tuimanager.unsafed_changes = True
    elif args[0] == 'unlink':
        data.unlink(args[1], args[2], args[3])
        tuimanager.unsafed_changes = True
    elif args[0] == 'qnote':
        data.set_qnote_project(args[1], ' '.join(args[2:]))
        tuimanager.unsafed_changes = True
    elif args[0] == 'context-qnote':
        data.set_qnote_context(args[1], args[2], ' '.join(args[3:]))
        tuimanager.unsafed_changes = True
    elif args[0] == 'note':
        data.open_note_project(args[1])
    elif args[0] == 'context-note': 
        data.open_note_context(args[1], args[2])
    elif args[0] == 'backup':
        # check if git repo
        assert os.path.exists(os.path.join(data.LOCATION,'.git'))
        if os.path.exists(os.path.join(data.LOCATION,'notes')):
            os.system(f"git -C '{data.LOCATION}' add -A 'notes' > /dev/null")
        os.system(f"git -C '{data.LOCATION}' add -A 'Active_Contexts.yaml' > /dev/null")
        os.system(f"git -C '{data.LOCATION}' add -A 'Active_Projects.yaml' > /dev/null")
        os.system(f"git -C '{data.LOCATION}' commit -m 'Backup from ProjectManager2 on {time.ctime()}' > /dev/null")
        os.system(f"git -C '{data.LOCATION}' push --quiet")
    elif args[0] == 'resource-create':
        if tuimanager.mode == 'open':
            proj = tuimanager.mode_content
            data.add_resource(proj,args[1], args[2], args[3])
        else:
            data.add_resource(args[1], args[2], args[3], args[4])
        tuimanager.unsafed_changes = True
    elif args[0] == 'resource-delete':
        if tuimanager.mode == 'open':
            proj = tuimanager.mode_content
            data.remove_resource(proj, args[1])
        else:
            data.remove_resource(args[1], args[2])
        tuimanager.unsafed_changes = True
    elif args[0] == 'resource':
        if tuimanager.mode == 'open':
            proj = tuimanager.mode_content
            data.resource_action(proj, args[1], args[2])
        else:
            data.resource_action(args[1], args[2], args[3])
    elif args[0] == 'show-resources':
        tuimanager.show_resources = not tuimanager.show_resources
    elif args[0] == 'filter':
        if [args[1],args[2]] in tuimanager.filter:
            tuimanager.filter.remove([args[1],args[2]])
        else:
            tuimanager.filter.append([args[1],args[2]])
    elif args[0] == 'filter-remove':
        tuimanager.filter = []
    elif args[0] == 'qnote-delete':
        data.set_qnote_project(args[1], '')
        tuimanager.unsafed_changes = True
    elif args[0] == 'context-qnote-delete':
        data.set_qnote_context(args[1], args[2], '')
        tuimanager.unsafed_changes = True
    else:
        raise ValueError(f"Unknown Arguments {args}")


class MyNestedCompleter(NestedCompleter):  # Adding the WORD option to the nested completer
    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        # Split document.
        text = document.text_before_cursor.lstrip()
        stripped_len = len(document.text_before_cursor) - len(text)

        # If there is a space, check for the first term, and use a
        # subcompleter.
        if " " in text:
            first_term = text.split()[0]
            completer = self.options.get(first_term)

            # If we have a sub completer, use this for the completions.
            if completer is not None:
                remaining_text = text[len(first_term) :].lstrip()
                move_cursor = len(text) - len(remaining_text) + stripped_len

                new_document = Document(
                    remaining_text,
                    cursor_position=document.cursor_position - move_cursor,
                )

                yield from completer.get_completions(new_document, complete_event)

        # No space in the input: behave exactly like `WordCompleter`.
        else:
            completer = WordCompleter(
                list(self.options.keys()), ignore_case=self.ignore_case,WORD=True
            )
            yield from completer.get_completions(document, complete_event)


def main():
    # Load Location
    parser = argparse.ArgumentParser()
    parser.add_argument('LOCATION', type=Path, help='Specify folder.')
    parser.add_argument('-i', '--init', action='store_true', help='Initialize necessary files in the folder.')
    
    args = parser.parse_args()
    LOCATION = args.LOCATION.resolve()

    assert os.path.exists(LOCATION)  # Make sure location exists

    if args.init:
        print('Initializing files ...')
        files_to_create = ["Active_Contexts.yaml", "Active_Projects.yaml"]
        for file in files_to_create:
            filepath = os.path.join(LOCATION,file)
            if not os.path.isfile(filepath):
                with open(filepath, "w+") as f:
                    pass
                print(f"Created file: {file}")
            else:
                print(f"File {file} already exists.")


    # Load Data
    data = Data(LOCATION)
    data.load()

    # Start the Manager
    man = TUIManager(data)
    

    ####
    # Prompt toolkit
    ###
            
    # Key bindings
    kb = KeyBindings()

    # Exit on Ctrl-Q
    @kb.add('c-q')
    def exit_app(event):
        event.app.exit()

    # Show help
    @kb.add('f1')
    def show_help(event):
        man.help_message_visible = not man.help_message_visible
        output_text.text = man.return_main_text()
        head_text.text = man.return_head_text()
    
    # Show categories
    @kb.add('f2')
    def show_cat(event):
        man.cat_list_visible = not man.cat_list_visible
        output_text.text = man.return_main_text()
        head_text.text = man.return_head_text()


    # Event when Enter is pressed
    @kb.add('enter')
    def handle_enter(event):
        command = command_input.text  # get text
        CommandParser(data, man, command.split())  # Parse the command
        output_text.text = man.return_main_text()
        head_text.text = man.return_head_text()
        command_input.text = ''  # Clear the input area
        command_input.completer = MyNestedCompleter.from_nested_dict(man.autocomplete_dict_suggestions())
        # command_input.completer = WordCompleter(man.autocomplete_suggestions(), ignore_case=False,WORD=True) # Update the completer  # This is too heavy to do this every time ?
    
    # Scrolling text functionality
    @kb.add('down')
    def handle_down(event):
        if man.help_message_visible:
            man.help_message_line += 1
        elif man.cat_list_visible:
            man.cat_list_line += 1
        else:
            man.line_start +=1
        output_text.text = man.return_main_text()
    
    @kb.add('up')
    def handle_up(event):
        if man.help_message_visible:
            man.help_message_line = max(man.help_message_line-1,0)
        elif man.cat_list_visible:
            man.cat_list_line = max(man.cat_list_line-1,0)
        else:
            man.line_start = max(man.line_start-1,0)
        output_text.text = man.return_main_text()
    
    @kb.add('escape')  # jumping to 0
    def handle_escape(event):
        if man.help_message_visible:
            man.help_message_line = 0
        else:
            man.line_start = 0
        output_text.text = man.return_main_text()


    # Head section 
    head_text = FormattedTextControl("This is the head text.")
    head_window = Window(content=head_text, wrap_lines=False, height=1)

    # Top section
    output_text = FormattedTextControl("This is the main text.")
    output_window = Window(content=output_text, wrap_lines=True)

    # Commands for completer  # TODO update autocompletion

    command_completer = WordCompleter([], ignore_case=False,WORD=True)

    # Bottom input area with autocomplete
    command_input = TextArea(
        prompt='> ',
        height=2,
        multiline=False,
        completer=command_completer
    )

    # Main layout
    root_container = HSplit([
        head_window,  # Head text display 
        Window(height=1, char="-"),  # Divider
        output_window,       # Main text display
        Window(height=1, char="-"),  # Divider
        command_input        # Bottom input area
    ])

    layout = Layout(root_container)

    # Application
    application = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True
    )

    # Load once
    head_text.text = man.return_head_text()
    output_text.text = man.return_main_text()
    # command_input.completer = WordCompleter(man.autocomplete_suggestions(), ignore_case=False,WORD=True)
    command_input.completer = MyNestedCompleter.from_nested_dict(man.autocomplete_dict_suggestions())
    application.run()

    # breakpoint()


if __name__ == "__main__":
    main()



#####
# NOTES
#####

# MODE 1 Group-Mode 
# - groups projects according to context
# - if "group *" then groups according to nothing, i.e., just shows all projects
# - filter have impact here

# MODE 2 Open-Mode
# - shows resources of a specific projects

# NEXT TODO:
# - archive functionality
# - archive option: just switch the active and archive file while loading and dumping
# - filter functionality
# - Add images to the readme file