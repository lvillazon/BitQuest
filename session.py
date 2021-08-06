import uuid
import datetime
import os

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
                if isinstance(errors, list):
                    file.write(NEW_LINE.join(errors))
                else:
                    file.write(errors)
                file.write(NEW_LINE)
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

def parse_log(file):
    # convert the XML text in the log file
    # into a list of log file sections, each one represented as a dict
    with open(file, "r") as f:
        lines = f.readlines()
    i = 0
    log = []
    while i < len(lines):
        if lines[i].startswith('<SECTION='):  # create a new section
            section = {}
            section['name'] = lines[i][9:-2]
        elif lines[i][0] == '<' and '=' in lines[i]:  # add a new value
            data = lines[i].split('=')
            section[data[0][1:]] = data[1][:-2]
        elif lines[i].startswith('</SECTION>'):
            log.append(section)
        i += 1
    return log

def view_logs():
    # print a summary of log info from all log files in the logs folder
    # this will hopefully be supplanted by the IA project developed by Abbie Hewitt
    # but it may still be handy to have a quick way to collate the data for a single user
    print("LOG SUMMARY")
    # get a list of all the log files
    log_files = []
    for root, dirs, files in os.walk(SAVE_FILES_FOLDER):
        for file in files:
            if file.endswith(SAVE_FILE_EXTENSION):
                log_files.append(os.path.join(root, file))
    print(len(log_files), "logs found.")
    # parse each log file into a dictionary and add to a list of logs
    all_logs = []
    for file in log_files:
        all_logs.append(parse_log(file))
    print(all_logs)

    # collate users
    # all logs with the same class are added to a list
    # and added to a dict keyed by class name
    collated_classes = {}
    for log in all_logs:
        if log:
            class_name = log[0]['CLASS_NAME']  # log[0] is always the header section
            print(class_name)
            if class_name not in collated_classes.keys():
                collated_classes[class_name] = []
            collated_classes[class_name].append(log)

    # summary of all classes found
    print(len(collated_classes), "classes found.")
    for class_name in collated_classes.keys():
        print(class_name)

    # per class summary
    for c in collated_classes.keys():
        print("Class", c, "has", len(collated_classes[c]), "records:")
        for r in collated_classes[c]:
            print("   ", r[0]['USER_NAME'], 'completed ', end='')
            for section in r:
                if section['name'] == 'CHECKPOINT' and 'LEVEL' in section.keys():
                    print(section['LEVEL'], end=', ')
            print()