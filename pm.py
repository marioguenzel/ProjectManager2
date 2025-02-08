import yaml
import argparse
from pathlib import Path
import os

from prompt_toolkit import Application
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import TextArea

HELP_MESSAGE = """
    ### All modes (OPEN and GROUP) ###
    # TUI handling
    open <PROJECT>  -> open a project and show its resources

    group <CATEGORY>  -> open the group view with category (use 'group *' to show all projects without grouping)
    filter <CATEGORY> <CONTEXT>  -> only show projects with that context

    note <PROJECT>   -> open markdown note
    qnote <PROJECT>  -> modify quicknote

    context-note <CATEGORY> <CONTEXT>  -> open markdown note 
    context-note <CATEGORY> <CONTEXT>  -> modify quicknote 

    # Modifications
    + create <PROJECT>      -> create a new project
    archive <PROJECT>     -> archive a project
    unarchive <PROJECT>   -> unarchive a project

    link <PROJECT> <CATEGORY> <CONTEXT>    -> Create a new link
    unlink <PROJECT> <CATEGORY> <CONTEXT>  -> Remove a link

    context-create <CATEGORY> <CONTEXT>   -> create a new context
    context-archive <CATEGORY> <CONTEXT>  -> archive a context
    context-unarchive <CATEGORY> <CONTEXT>  -> unarchive a context

    + code    -> Open vscode of the folder to make modifications manually
    + reload  -> Make sure to reload when making manual modifications
    + dump  -> Dump changes to file (Will be removed in later version)

    backup  -> push changes to git (git -A commit; push)

    ### In OPEN-mode only ###
    resource <RESOURCE> <ACTION>  -> do action for resource
    resource-create <RESOURCE> <TYPE> <source>  -> create a resource of TYPE with source
    resource-info <RESOURCE>      -> show infor of that resource 

    ### ACTIONS ###
    - SVN: code, clone
    - GIT: code, clone
    - LINK: open

    ### keys ###
    + ctrl-q  -> Quit
    + f1      -> Show help
    f2      -> Show categories
    esc     -> scroll to top
"""

class Data:
    """Data loading, dumping and modification"""
    def __init__(self, LOCATION: Path):
        self.LOCATION = LOCATION
        self.Projects = dict()
        self.Contexts = dict()
        self.load()
    
    def load(self):
        with open(os.path.join(self.LOCATION,'Active_Projects.yaml'), 'r') as infile:
            self.Projects = yaml.safe_load(infile)

    def dump(self):
        with open(os.path.join(self.LOCATION,'Active_Projects.yaml'), 'w') as outfile:
            yaml.dump(self.Projects, outfile)

    # TODO: Add self.dump() after some modifications

    def add_project(self, name: str):
        assert name not in self.Projects
        self.Projects[name] = dict()
    
    def remove_project(self, name: str):
        assert name in self.Projects

        del self.Projects[name]
    
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


class TUIManager:
    """Manages how to show the data."""
    def __init__(self, DATA: Data):
        self.CONTENT = DATA
        self.mode = 'group'  # Can be show or group 
        self.mode_content = '*'  # Category or Project
        self.filter = []
        self.line_start = 0  # show from beginning by default
        # self.line_length = 10  # show 10 lines by default
        self.help_message_visible = False
        self.help_message_line = 0
    
    def return_top_text(self):
        if self.help_message_visible:
            text_rows = HELP_MESSAGE.splitlines()
            return '\n'.join(text_rows[self.help_message_line:])
        else:
            text_rows = ['- ' + str(proj) for proj in self.CONTENT.Projects]
            return '\n'.join(text_rows[self.line_start:])

def CommandParser(data: Data, tuimanager: TUIManager, args):
    if args[0] == 'code':
        os.system(f"code '{data.LOCATION}'")
    elif args[0] == 'reload':
        data.load()
    elif args[0] == 'dump':
        data.dump()
    elif args[0] == 'create':
        data.add_project(args[1])
    else:
        raise ValueError(f"Unknown Arguments {args}")


def main():
    # Load Location
    parser = argparse.ArgumentParser()
    parser.add_argument('LOCATION', type=Path, help='Specify folder.')
    
    args = parser.parse_args()
    LOCATION = args.LOCATION.resolve()

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
    def exit_app(event):
        man.help_message_visible = not man.help_message_visible
        output_text.text = man.return_top_text()


    # Event when Enter is pressed
    @kb.add('enter')
    def handle_enter(event):
        command = command_input.text  # get text
        CommandParser(data, man, command.split())  # Parse the command
        output_text.text = man.return_top_text()
        command_input.text = ''  # Clear the input area
        # raise ValueError('This is a test')  # TODO Just raise value error if options do not work
    
    # Scrolling text functionality
    @kb.add('down')
    def handle_down(event):
        if man.help_message_visible:
            man.help_message_line += 1
        else:
            man.line_start +=1
        output_text.text = man.return_top_text()
    
    @kb.add('up')
    def handle_up(event):
        if man.help_message_visible:
            man.help_message_line = max(man.help_message_line- 1,0)
        else:
            man.line_start = max(man.line_start-1,0)
        output_text.text = man.return_top_text()
    
    @kb.add('escape')  # jumping to 0
    def handle_escape(event):
        if man.help_message_visible:
            man.help_message_line = 0
        else:
            man.line_start = 0
        output_text.text = man.return_top_text()


    # Top section - static text and output display
    output_text = FormattedTextControl("This is the static text at the top.")
    output_window = Window(content=output_text, wrap_lines=True)

    # Commands for completer
    commands = [
        'create',  # (PROJECT) create a new project
        'archive',  # (PROJECT) archive a project
        'unarchive',  # (PROJECT) unarchive a project
        'link',  # (PROJECT CAT CONTEXT) create a new link
        'unlink',  # (PROJECT CAT CONTEXT) remove a new link
        'open',  # (PROJECT) open a project and show its resources
        'group',  # (CAT) group projects according to context under category
        'filter',  # (CAT CONTEXT) only show projects with that context (setting filter again unsets the filter)
        'note',  # (PROJECT) open the markdown note of the context item
        'qnote',  # (PROJECT) modify quicknote

        'context-create',  # (CAT CONTEXT) create a new context
        'context-archive',  # (CAT CONTEXT) archive a context
        'context-unarchive',  # (CAT CONTEXT) unarchive a context
        'context-note',  # (CAT CONTEXT) open the markdown note of the context item
        'context-qnote',  # (CAT CONTEXT) modify quicknote

        'resource',  # (RESOURCE ACTION) make action for resource. Only available in Open Mode [Actions: code, clone, info, open (link), ]
    ]
    command_completer = WordCompleter(commands, ignore_case=True)

    # Bottom input area with autocomplete
    command_input = TextArea(
        prompt='> ',
        height=2,
        multiline=False,
        completer=command_completer
    )

    # Main layout
    root_container = HSplit([
        output_window,       # Static text at the top
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
    output_text.text = man.return_top_text()
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