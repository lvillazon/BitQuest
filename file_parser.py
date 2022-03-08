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

            # value assignment
            elif '=' in lines[i]:
                expression = lines[i].split('=', 1)
                # simple case - no opening brace at the end, just: identifier = value
                if not expression[1].rstrip().endswith('['):
                    parsed[expression[0].strip()] = eval(expression[1].strip())
                else:
                    # for more complex assignment, read in each line until a closing ]
                    # then eval the whole thing
                    i += 1
                    new_list = []
                    while i < len(lines) and lines[i].strip() != ']':
                        new_list.append(lines[i].rstrip())  # don't lstrip, since we need to preserve indents
                        i += 1
                    parsed[expression[0].strip()] = new_list
        i += 1
    return parsed


def parse_file(file_name, format = 'robots'):
    """ the default format (robots), expects a file in this format:
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

        and returns the following data structure:
            [
            {
            name: 'foo', size: 16, several_values: [1, 2, 3],
            list_name: ['line1', 'line2', 'line3']
            },
            {value: 19}
            ]

        alternatively, if type is 'users', data can be supplied in this format (designed to be pasted from the tracker)
        Bloggs, Fred, 7xy1
        Perkins, Sue, 8Cp/w2

        and returns the following data structure:
        [
        {surname: 'Bloggs', firstname: 'Fred', class: '7xy1', year: 7},
        {surname: 'Perkins', firstname: 'Sue', class: '8Cp/w2', year: 8}
        ]
    """
    parsed_data = []
    with open(file_name, 'r') as file:
        lines = file.readlines()  # read the whole file into a string array
        if format == 'robots':
                # look for the start of a section
                i = 0
                while i < len(lines):
                    # ignore any line beginning with #
                    if not lines[i].lstrip().startswith('#'):
                        if is_section_start(lines[i]):
                            # copy all the lines of this section into a sublist
                            section_name = get_section_name(lines[i])
                            section = []
                            i += 1
                            while i < len(lines) and not is_section_end(lines[i], section_name):
                                section.append(lines[i])
                                i += 1
                            # call the parser to build the dict
                            parsed_data.append(parse_section(section))
                    i += 1
        elif format == 'users':
            for data in lines:
                if ',' in data:  # standard format is Surname, Firstname<tab>classcode
                    user_data = {}
                    d2 = data.split(', ')
                    user_data['surname'] = d2[0]
                    d3 = d2[1].split('\t')
                    user_data['firstname'] = d3[0]
                    user_data['class'] = d3[1].strip()
                    user_data['year'] = int(d3[1][0])
                    if user_data['year'] == 1:
                        user_data['year'] = int(d3[1][1])+10  # allow for years 10 - 13 (unlikely, but possible)
                    parsed_data.append(user_data)
                elif ' ' in data and '\t' in data:  # alternative format is Firstname Surname<tab>classcode
                    user_data = {}
                    d2 = data.split('\t')
                    user_data['class'] = d2[1].strip()
                    user_data['year'] = int(d2[1][0])
                    d3 = d2[0].split(' ')
                    user_data['firstname'] = d3[0]
                    user_data['surname'] = ' '.join(d3[1:])  # allow for double-barrelled surnames
                    if user_data['year'] == 1:
                        user_data['year'] = int(d2[1][1])+10  # allow for years 10 - 13 (unlikely, but possible)
                    parsed_data.append(user_data)
    return parsed_data

