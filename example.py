import json
import sys

from eventdispatcher import EventDispatcher, Property


class SettingsFile(EventDispatcher):
    last_login = Property(None)
    color = Property("red")

    def __init__(self, filepath):
        super(SettingsFile, self).__init__()
        self.filepath = filepath
        self.number_of_file_updates = 0

        # Bind the properties to the function that updates the file
        self.bind(
            last_login=self.update_settings_file,
            color=self.update_settings_file,
        )

    def on_last_login(self, inst, last_login):
        # Default handler for the last_login property
        print("last login was %s" % last_login)

    def on_color(self, inst, color):
        # Default handler for the color property
        print("color has been set to %s" % color)

    def update_settings_file(self, *args):
        # Update the file with the latest settings.
        print("Updating settings file.")
        self.number_of_file_updates += 1
        with open(self.filepath, "w") as _f:
            settings = {"last_login": self.last_login, "color": self.color}
            json.dump(settings, _f)


if __name__ == "__main__":
    if sys.version_info[0] < 3 or (
        sys.version_info[0] == 3 and sys.version_info[1] <= 5
    ):
        raise Exception("This program requires Python 3.5 or higher")

    s = SettingsFile("./myfile.json")
    s.last_login = 'May 18 2015'                # Updates settings file
    s.last_login = 'May 18 2015'                # Does not update settings file
    s.color = 'blue'                     # Updates settings file
    s.color = 'blue'                     # Does not update settings file

    print("The file was updated %d times" % s.number_of_file_updates)

    file1 = SettingsFile("./myfile1.json")
    file2 = SettingsFile("./myfile2.json")

    # Binds the color property from file1 to the color property of file2
    # Changing file1.color will automatically update the value of file2.color
    file1.bind(color=file2.setter("color"))
    file1.color = "green"
