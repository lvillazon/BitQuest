import uuid
import datetime

from constants import SAVE_FILES_FOLDER, SAVE_FILE_EXTENSION, NEW_LINE


class Session:
    """ Handles data logging and
    loading/saving progress between sessions"""

    def __init__(self, user_name, class_name):
        # arbitrary version id.
        # Logs with different version ids may not be compatible
        self.file_format_version = "0.1"
        self._user_name = user_name
        self._class_name = class_name
        self._current_level = "not set"
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
        self.open_tag = "<"  # arbitrary strings used to begin and close a tag
        self.close_tag = ">\n"
        self.section_delimiter = "</SECTION>\n\n"

    def get_user_name(self):
        return self._user_name

    def get_class_name(self):
        return self._class_name

    def get_user_id(self):
        """ return a composite string representing the user + class """
        return self._user_name + ', ' + self._class_name

    def set_current_level(self, level_name):
        self._current_level = level_name

    def write_time_stamp(self, file):
        timestamp = datetime.datetime.now()
        time_format = '%d-%m-%Y %H:%M:%S'  # dd/mm/yyyy hh:mm:ss
        file.write(self.open_tag +
                   "DATE/TIME=" + timestamp.strftime(time_format) +
                   self.close_tag)

    def save_header(self):
        """ the session header is written to the top of the file
        to identify the user and date/time"""
        with open(self.save_file, 'w') as file:  # create new file
            file.write(self.open_tag +
                       "SECTION=HEADER" +
                       self.close_tag)
            file.write(self.open_tag +
                       "FILE_VERSION=" + self.file_format_version +
                       self.close_tag)
            self.write_time_stamp(file)
            file.write(self.open_tag +
                       "USER_NAME=" + self.get_user_name() +
                       self.close_tag)
            file.write(self.open_tag +
                       "CLASS_NAME=" + self.get_class_name() +
                       self.close_tag)
            file.write(self.section_delimiter)


    def save_run(self, code_lines = None, errors = None):
        """ Save details of the current attempt to run a program """
        with open(self.save_file, 'a') as file:  # add to the file if it exists
            file.write(self.open_tag + "SECTION=ATTEMPT" + self.close_tag)
            self.write_time_stamp(file)
            file.write(self.open_tag
                       + "LEVEL=" + self._current_level
                       + self.close_tag)
            if code_lines:
                file.write(self.open_tag + "USER_PROGRAM" + self.close_tag)
                for line in code_lines:
                    file.write(line + NEW_LINE)
                file.write(self.open_tag + "/USER_PROGRAM" + self.close_tag)
            if errors:
                file.write(self.open_tag + "ERROR" + self.close_tag)
                for line in errors:
                    file.write(line + NEW_LINE)
                file.write(self.open_tag + "/ERROR" + self.close_tag)
            file.write(self.section_delimiter)

    def save_checkpoint_reached(self, checkpoint_name):
        """ Make a log entry whenever a checkpoint flag is reached"""
        with open(self.save_file, 'a') as file:  # append to existing file
            file.write(self.open_tag + "SECTION=CHECKPOINT" + self.close_tag)
            self.write_time_stamp(file)
            file.write(self.open_tag
                       + "LEVEL=" + checkpoint_name
                       + self.close_tag)
            # TODO add info about bonus goals achieved eg coins collected
            file.write(self.section_delimiter)
