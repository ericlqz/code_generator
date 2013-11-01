# -*- coding: utf-8 -*-

import json
from string import Template
import os

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class DataObjectGeneraotr:

    def generator(self):
        json_data = file("json_dataobject.json")
        data = json.load(json_data)
        template = file(data["templates"]["object_template"]).read()
        json_hashmap_template = file(data["templates"]["object_json_hashmap_template"]).read()
        # template = file("template_data_object.tp").read()
        code = Template(template)

        objects = data["objects"]
        for object in objects:
            path = object["path"]
            rewrite = object["rewrite"]
            if os.path.exists(path) and not rewrite:
                print path, " exists not rewrite."
                continue

            classname = object["classname"].capitalize()
            class_comment = object["class_comment"].encode("utf-8")
            package = object["package"]

            codeDict = {
                "classname": classname,
                "classname_lower": classname.lower(),
                "class_comment": class_comment,
                "package": package
            }

            fields = object["fields"]

            codeDict["response_keys"] = self.renderResponseKey(classname, fields)
            codeDict["field_statements"] = self.renderFieldStatements(fields)
            codeDict["field_assigements"] = self.renderFieldAssigments(classname, fields)
            codeDict["data_validation"] = self.renderDataValidation(classname, fields)
            codeDict["data_validation"] = self.renderDataValidation(classname, fields)
            codeDict["to_string"] = self.renderToString(classname, fields)
            codeDict["setting_getting"] = self.renderSettingAndGetting(fields)

            object_manager = object["object_manager"]
            if object_manager:
                objectManagerRender = self.ObjectManagerRender()
                codeDict["object_manager"] = objectManagerRender.generator(classname, fields)
                # codeDict["setting_getting"] = self.renderSettingAndGetting(fields)
            else:
                codeDict["object_manager"] = ""
                # codeDict["setting_getting"] = ""

            if object.get("JsonHashMap"):
                key = object.get("key")
                codeDict["from_json_hash_map"] = self.renderFromJsonHashMap(classname, key, json_hashmap_template)
            else:
                codeDict["from_json_hash_map"] = ""

            self.saveFile(path, code.substitute(codeDict))

    def renderResponseKey(self, classname, fields):
        response_keys = ""
        code = '/** Key For Retrieve ${field_upper} Data From JSONObject */\n\t' \
               + 'private static final String RESPONSE_KEY_${classname_upper}_${field_upper} = "${field_lower}";\n\t'
        for fieldObject in fields:
            template = Template(code)
            mapping = {"field_upper": fieldObject["field"].upper(), "field_lower": fieldObject["field"].lower(),
                        "classname_upper": classname.upper()}
            response_keys += template.substitute(mapping)

        return response_keys

    def renderFieldStatements(self, fields):
        field_statements = ""
        code = '/** ${field_comment} */\n\tprivate ${field_type} ${field_lower};\n\t'
        for fieldObject in fields:
            template = Template(code)
            mapping = {
                "field_comment": fieldObject["comment"].encode("utf-8"),
                "field_lower": fieldObject["field"].lower(),
                "field_type": fieldObject["type"]
            }
            field_statements += template.substitute(mapping)

        return field_statements

    def renderFieldAssigments(self, classname, fields):
        field_assigements = ""
        code = "${classname_lower}.${field_lower} = object.get${field_type_capital}(${field_response_key});\n\t\t\t"
        for fieldObject in fields:
            template = Template(code)
            mapping = {
                "field_lower": fieldObject["field"].lower(),
                "field_type_capital": fieldObject["type"].capitalize(),
                "field_response_key": "RESPONSE_KEY_" + classname.upper() + "_" + fieldObject["field"].upper(),
                "classname_lower": classname.lower()
            }
            field_assigements += template.substitute(mapping)

        return field_assigements

    def renderFromJsonHashMap(self, classname, key, code):
        from_json_hash_map = ""
        template = Template(code)
        mapping = {
            "classname": classname.capitalize(),
            "classname_lower": classname.lower(),
            "key": key
        }
        from_json_hash_map += template.substitute(mapping)

        return from_json_hash_map

    def renderDataValidation(self, classname, fields):
        data_validations = ""
        for index, fieldObject in enumerate(fields):
            newline = "" if (index + 1) == len(fields) else "\n\t\t\t"
            code = "&& object.has(${field_response_key})" + newline
            template = Template(code)
            mapping = {
                "field_response_key": "RESPONSE_KEY_" + classname.upper() + "_" + fieldObject["field"].upper()
            }
            data_validations += template.substitute(mapping)

        return data_validations

    def renderToString(self, classname, fields):
        code = '"[' + classname.capitalize() + ' - "' + '\n\t\t\t'
        for field in fields:
            code += '+ " ' + field["field"].lower() + ': " + ' + field["field"].lower() + '\n\t\t\t'
        code += '+ "]";'
        return code

    def renderSettingAndGetting(self, fields):
        code = file("template_set_get.tp").read()
        setting_and_getting = ""
        for fieldObject in fields:
            template = Template(code)
            mapping = {
                "field_capitalize": fieldObject["field"].capitalize(),
                "field_lower": fieldObject["field"].lower(),
                "field_type": fieldObject["type"]
            }
            setting_and_getting += template.substitute(mapping)

        return setting_and_getting

    class ObjectManagerRender:

        def generator(self, classname, fields):
            code = file("template_object_manager.tp").read()
            template = Template(code)
            mapping = {"classname": classname.capitalize(),
                       "classname_lower": classname.lower(),
                       "classname_upper": classname.upper(),
                       "create_content_values": self.renderCreateContentValue(classname, fields),
                       "cursor_to_field": self.renderCursorToField(classname, fields)
            }

            return template.substitute(mapping)

        def renderCreateContentValue(self, classname, fields):
            create_content_value = ""
            code = "values.put(Table.${classname}DB.COLUMN_NAME_${column_name_upper}, ${classname_lower}.${field_lower});\n\t\t\t\t"
            for fieldObject in fields:
                template = Template(code)
                mapping = {
                    "classname": classname.capitalize(),
                    "classname_lower": classname.lower(),
                    "column_name_upper": fieldObject["field"].upper(),
                    "field_lower": fieldObject["field"].lower()
                }
                create_content_value += template.substitute(mapping)

            return create_content_value

        def renderCursorToField(self, classname, fields):
            cursor_to_field = ""
            code = "${classname_lower}.set${field_capitalize}(cursor.get${field_type_capitalize}(cursor.getColumnIndex(Table.${classname}DB.COLUMN_NAME_${column_name_upper})));\n\t\t\t\t"
            for fieldObject in fields:
                template = Template(code)
                mapping = {
                    "classname": classname.capitalize(),
                    "classname_lower": classname.lower(),
                    "column_name_upper": fieldObject["field"].upper(),
                    "field_capitalize": fieldObject["field"].capitalize(),
                    "field_type_capitalize": fieldObject["type"].capitalize()
                }
                cursor_to_field += template.substitute(mapping)
            return cursor_to_field

    def saveFile(self, path, content):
        f = open(path, 'w')
        f.write(content)
        f.close()

if __name__ == "__main__":
    generator = DataObjectGeneraotr()
    generator.generator()
