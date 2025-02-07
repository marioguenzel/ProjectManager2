import yaml
import argparse
from pathlib import Path
import os


class Data:
    def __init__(self, LOCATION: Path):
        self.LOCATION = LOCATION
        self.Projects = {}
        self.Contexts = {}
    
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
        self.line_length = 10  # show 10 lines by default





def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('LOCATION', type=Path,
                        help='Specify folder.')

    args = parser.parse_args()

    LOCATION = args.LOCATION.resolve()

    print(LOCATION)
    data = Data(LOCATION)
    data.load()

    breakpoint()


if __name__ == "__main__":
    main()
