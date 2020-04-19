

def read_data(filename):
    """
    read a gedcom file and creates a structured data dict

    Args:
        filename (str): gedcom file

    Returns:
        dict: structured data
    """
    import re
    stack = [None, None, None, None, None, None, None, None]
    indi = re.compile(r'0 @I\d+@ INDI.*?(?=\n0)',
                      flags=re.DOTALL | re.MULTILINE)
    fam = re.compile(r'0 @F\d+@ FAM.*?(?=\n0)', flags=re.DOTALL | re.MULTILINE)
    content = open(filename, 'r', encoding='utf8').read()
    indi_database = {}
    for i in indi.finditer(content):
        ged_data = i.string[i.regs[0][0]:i.regs[0][1]]
        stack[0] = indi_database
        for line in ged_data.split('\n'):
            level = int(line[0])
            tag_name = line.split(' ')[1]
            tag_data = " ".join(line.split(' ')[2:])
            if tag_name not in stack[level]:
                stack[level][tag_name] = {'tag_data': tag_data}
            else:
                stack[level][tag_name]['tag_data'] += '\n'+tag_data
            stack[level+1] = stack[level][tag_name]
        if len(indi_database) > 999000:
            break
    fam_database = {}
    for i in fam.finditer(content):
        ged_data = i.string[i.regs[0][0]:i.regs[0][1]]
        stack[0] = fam_database
        for line in ged_data.split('\n'):
            level = int(line[0])
            tag_name = line.split(' ')[1]
            tag_data = " ".join(line.split(' ')[2:])
            if tag_name not in stack[level]:
                stack[level][tag_name] = {'tag_data': tag_data}
            else:
                stack[level][tag_name]['tag_data'] += '\n'+tag_data
            stack[level+1] = stack[level][tag_name]
        if len(fam_database) > 992000:
            break
    return indi_database, fam_database
