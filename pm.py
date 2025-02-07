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

class Data:
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
    def __init__(self, DATA: Data):
        self.CONTENT = DATA
        self.mode = 'group'  # Can be show or group 
        self.mode_content = ['*']  # List of what is feeded into the mode
        self.filter = []
        self.line_start = 0  # show from beginning by default
        # self.line_length = 10  # show 10 lines by default
    
    def return_top_text(self):
        return '\n'.join(['- ' + str(proj) for proj in self.CONTENT.Projects])

def CommandParser(data: Data, tuimanager: TUIManager, *args):
    pass


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
    man = TUIManager(Data(LOCATION))
    

    ####
    # Prompt toolkit
    ###
            
    # Key bindings
    kb = KeyBindings()

    # Exit on Ctrl-Q
    @kb.add('c-q')
    def exit_app(event):
        event.app.exit()

    # Event when Enter is pressed
    @kb.add('enter')
    def handle_enter(event):
        command = command_input.text  # get text
        # CommandParser(command.split())  # Parse the command
        output_text.text = man.return_top_text()
        command_input.text = ''  # Clear the input area
        # raise ValueError('This is a test')  # TODO Just raise value error if options do not work


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