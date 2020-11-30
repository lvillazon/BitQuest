import uuid
import datetime

from constants import SAVE_FILES_FOLDER, SAVE_FILE_EXTENSION


class Session:
    """ Handles data logging and
    loading/saving progress between sessions"""

    def __init__(self, user_name, class_name):
        self._user_name = user_name
        self._class_name = class_name
        self.current_level = ""
        # generate a unique file name for this session
        # the uuid module is used to generate unique hex file names
        # This is safer than using the username & class because
        # a) this will not necessarily be unique
        # b) it would need to be quite strictly sanitised to avoid
        #    file names with illegal characters or device names
        # the file name is created once and is used for the lifetime of the
        # program.
        self.save_file = SAVE_FILES_FOLDER \
                         + str(uuid.uuid4()) \
                         + SAVE_FILE_EXTENSION

    def begin_level(self, level_name):
        self.current_level = level_name

    def complete_level(self, level_name):
        self.save_progress(True)

    def get_user_name(self):
        return self._user_name

    def get_class_name(self):
        return self._class_name

    def get_user_id(self):
        """ return a composite string representing the user + class """
        return self._user_name + ', ' + self._class_name

    def save_progress(self, complete=False, code_lines = None):
        """ Write a text file for each unique user with the following info:
            * TODO Date and time
        	* TODO User name
            * TODO Level number
            * TODO Code from THIS attempt
            * TODO Level complete? If yes,
                * TODO Time taken
                * TODO Bonus items gathered
        """
        # write this map to the file
        delimiter = "###\n"
        with open(self.save_file, 'a') as file:  # add to the file if it exists
            timestamp = datetime.datetime.now()
            time_format = '%d-%m-%Y %H:%M:%S'  # dd/mm/yyyy hh:mm:ss
            file.write("<DATE/TIME=" + timestamp.strftime(time_format) +">\n")
            file.write("<USER_ID=" + self.get_user_id() + ">\n")
            file.write("<LEVEL=" + self.current_level + "\n")
            file.write("<LEVEL COMPLETE=" + str(complete) + ">\n")
            if complete:
                file.write("<TIME TAKEN=" + str(0) + ">\n")
                file.write("<BONUS_ITEMS=" + str(0) + ">\n")
            if code_lines:
                file.write("<USER PROGRAM>\n")
                for line in code_lines:
                    file.write(line + "\n")
                file.write("</USER PROGRAM>\n")
            file.write(delimiter)

