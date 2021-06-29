# file parser module
# allows pseudo XML files to be read and parsed into sections and values

def is_section_start(line):
    # returns true if the line is enclosed by < >
    if line.lstrip().startswith('<') and line.rstrip().endswith('>'):
        return True
    else:
        return False

def is_section_end(line, section):
    # returns true if the line is enclosed by </section>
    if line.strip() == '</' + section + '>':
        return True
    else:
        return False

def get_section_name(line):
    # returns 'section' from '<section>'
    return line.strip().lstrip('<').rstrip('>')

def parse_section(lines):
    # parse a list of strings into a data structure
    parsed = {}
    i = 0
    while i < len(lines):
        # ignore any line beginning with #
        if not lines[i].lstrip().startswith('#'):
            # handle <section> </section>
            if is_section_start(lines[i]):
                # create a sub dictionary for this section
                section_name = get_section_name(lines[i])
                section = []
                i += 1
                # copy all the lines of this section into a sublist
                while i < len(lines) and not is_section_end(lines[i], section_name):
                    section.append(lines[i])
                    i += 1
                # recursively call the parser to build the dict
                parsed[section_name] = parse_section(section)

            # simple case: identifier = value
            elif '=' in lines[i]:
                expression = lines[i].split('=', 1)
                parsed[expression[0].strip()] = eval(expression[1].strip())

            # even simpler case: [ or ] on their own, start and end a list
            # called source, where each element is a line of robot source code
            elif lines[i].strip() == '[':
                i += 1
                new_list = []
                while i < len(lines) and lines[i].strip() != ']':
                    new_list.append(lines[i].rstrip())  # don't lstrip, since we need to preserve indents
                    i += 1
                parsed['source'] = new_list
        i += 1
    return parsed


def parse_file(file_name):
    """ given a file in this format:
            <SECTION>
            name = foo
            size = 16
            several_values = [1, 2, 3]
            list_name = [
            line1
            line2
            line3
            ]
            </SECTION>
            <SECTION>
            value = 19
            </SECTION>

        this function would return the following data structure:
            [
            {
            name: 'foo', size: 16, several_values: [1, 2, 3],
            list_name: ['line1', 'line2', 'line3']
            },
            {value: 19}
            ]
    """
    with open(file_name, 'r') as file:
        lines = file.readlines()  # read the whole file into a string array
        return parse_section(lines)

    #     while i < len(lines) and lines[i][:-1] != SENTRY_START:  # look for the start of a sentry definition
    #         i += 1
    #     if i < len(lines):
    #         all_sentries = []
    #         name = lines[i+1][:-1]  # strip trailing CRLF
    #         sentry_level = eval(lines[i+2])
    #         position = eval(lines[i+3])
    #         display_program = []
    #         if sentry_level == level:  # only create the sentries for this game level
    #             s = Sentry(world, position, name)
    #             all_sentries.append(s)
    #         i += 3  # skip on to next sentry
    # return all_sentries


