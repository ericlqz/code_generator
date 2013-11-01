import json
from string import Template

class DataTableGeneraotr:

    def generator(self):
        json_data = file("json_dataobject.json")
        data = json.load(json_data)

        template = file("template_tables.tp").read()
        code = Template(template)

        objects = data["objects"]
        table_config = data["table_config"]
        path = table_config["table_path"]
        file_name = table_config["file_name"]

        mapping = {
            "classname":table_config["file_name"],
            "package": table_config["package"],
            "authority": table_config["authority"]
        }

        data_tables = ""
        for object in objects:
            object_manager = object["object_manager"]
            if object_manager:
                data_tables += self.renderDataTable(object)
        mapping["data_tables"] = data_tables

        self.saveFile(path + file_name + ".java", code.substitute(mapping))
        # print code.substitute(mapping)

    def renderDataTable(self, object):
        """
        Generate Database Table Object from Template
        """
        template = file("template_data_table.tp").read()
        code = Template(template)

        classname = object["classname"].capitalize()
        classname_lower = classname.lower()
        classname_upper = classname.upper()

        mapping = object["table_config"]

        fields = object["fields"]
        columns_define = ""
        for index, field in enumerate(fields):
            newline = "\n" if (index + 1 == len(fields)) else "\n\n\t\t"
            comment = Template('/**\n\t\t * Column name for the name of ${classname}\n\t\t * <P>Type: ${type}</P>\n\t\t */')
            columns_define += comment.substitute(classname=classname, type=field["sqlite_type"]) + "\n\t\t"
            columns_define += 'public static final String ' + 'COLUMN_NAME_' + field["field"].upper() + ' = "' + field["field"].lower() + '";' + newline

        columns_create_statement = ""
        for index, field in enumerate(fields):
            newline = '' if (index + 1 == len(fields)) else "\n\t\t\t"
            type = field["sqlite_type"] + '"' if (index + 1 == len(fields)) else field["sqlite_type"] + ',"'
            columns_create_statement += '+ Table.' + classname + 'DB.COLUMN_NAME_' + field["field"].upper() + ' + ' + '" ' + type + newline

        mapping['classname'] = classname
        mapping['classname_lower'] = classname_lower
        mapping['classname_upper'] = classname_upper
        mapping['columns_define'] = columns_define
        mapping['columns_create_statement'] = columns_create_statement

        return code.substitute(mapping)

    def saveFile(self, path, content):
        f = open(path, 'w')
        f.write(content)
        f.close()

if __name__ == "__main__":
    generator = DataTableGeneraotr()
    generator.generator()
