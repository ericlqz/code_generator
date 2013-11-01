# -*- coding: utf-8 -*-

import json
import os
from string import Template

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class DataTaskGenerator:

    def generator(self):

        json_data = file("json_task.json")
        data = json.load(json_data)

        template_file = data["template"]
        template = file(template_file).read()
        code = Template(template)

        package = data["package"]
        tasks = data["tasks"]

        for taskObject in tasks:
            path = taskObject["path"]
            rewrite = taskObject["rewrite"]
            if os.path.exists(path) and not rewrite:
                print path, " exists not rewrite."
                continue

            classname = taskObject["classname"].capitalize()
            request_url = taskObject["request_url"]
            # path = taskObject["path"]

            request_params = taskObject["request_params"]
            response_params = taskObject["response_params"]
            error_codes = taskObject["error_codes"]
            mapping = {
                "package": package,
                "classname": classname,
                "classname_upper": classname.upper(),
                "classname_lower": classname.lower(),
                "request_url": request_url,
                "request_keys": self.renderRequestKeys(request_params),
                "response_keys": self.renderResponseKeys(response_params),
                "error_code_keys": self.renderErrorCodes(error_codes),
                "request_field_statements": self.renderRequestFieldStatements(request_params),
                "response_field_statements": self.renderResponseFieldStatements(response_params),
                "request_params_to_string": self.renderReqeustPramasToString(request_params),
                "set_request_params_value": self.rendereSetRequestParamsValue(request_params),
                "request_params_valid": self.renderRequestParamsValid(request_params),
                "is_response_data_valid": self.renderIsResponseDataValid(response_params),
                "response_data_from_json": self.renderResponseDataFromJson(response_params),
                "error_code_cases_statements": self.renderErrorCodeCase(error_codes)
            }
            self.saveFile(path, code.substitute(mapping))
            # print code.substitute(mapping)

    def renderRequestKeys(self, params):
        request_keys = ""

        code = '/** Key for add ${field_lower} data to JSONObject */\n\t' \
               + 'private static final String REQUEST_KEY_${field_upper} = "${field_lower}";\n\t'
        for paramObject in params:
            template = Template(code)
            mapping = {
                "field_upper": paramObject["field"].upper(),
                "field_lower": paramObject["field"].lower()}
            request_keys += template.substitute(mapping)

        return request_keys

    def renderResponseKeys(self, params):
        response_keys = ""

        code = '/** ${null_or_not}. Key for retrieve ${field_lower} data from JSONObject */\n\t' \
               + 'private static final String RESPONSE_KEY_${field_upper} = "${field_lower}";\n\t'
        for paramObject in params:
            template = Template(code)
            null_or_not = "Not Null" if paramObject["notnull"] else "Maybe Null"
            mapping = {
                "field_upper": paramObject["field"].upper(),
                "field_lower": paramObject["field"].lower(),
                "null_or_not": null_or_not
            }
            response_keys += template.substitute(mapping)

        return response_keys

    def renderErrorCodes(self, error_codes):
        error_code_keys = ""

        code = '/** Error Code ${error_desc} */\n\t' \
               + 'private static final int ERROR_CODE_${error_code} = 0x0${error_code};\n\t'
        for errorCode in error_codes:
            template = Template(code)
            mapping = {
                "error_desc": errorCode["comment"],
                "error_code": errorCode["code"]
            }
            error_code_keys += template.substitute(mapping)

        return error_code_keys

    def renderRequestFieldStatements(self, params):
        field_statements = ""

        code = '/** ${field_comment} */\n\t private ${field_type} m${field_capitalize};\n\t'
        template = Template(code)
        for paramObject in params:
            mapping = {
                "field_comment": paramObject["comment"],
                "field_type": paramObject["type"],
                "field_capitalize": paramObject["field"].capitalize()
            }
            field_statements += template.substitute(mapping)

        return field_statements

    def renderResponseFieldStatements(self, params):
        field_statements = ""

        code = '/** ${field_comment} */\n\t private ${field_type} m${field_capitalize}${list};\n\t'
        template = Template(code)
        for paramObject in params:
            if paramObject["type"] == "JSONHashMap" or paramObject["type"] == "JSONArray":
                type = "List<" + paramObject["field"].capitalize() + ">"
                list = "List"
            elif paramObject["type"] == "JSONObject":
                type = paramObject["field"].capitalize()
                list = ""
            else:
                type = paramObject["type"]
                list = ""
            mapping = {
                "field_comment": paramObject["comment"],
                "field_capitalize": paramObject["field"].capitalize(),
                "field_type": type,
                "list":list
            }
            field_statements += template.substitute(mapping)

        return field_statements

    def renderReqeustPramasToString(self, params):
        field_statements = ""

        code = ' + " ${field}: " + m${field_capitalize}'
        template = Template(code)
        for paramObject in params:
            mapping = {
                "field": paramObject["field"],
                "field_capitalize": paramObject["field"].capitalize()
            }
            field_statements += template.substitute(mapping)

        return field_statements

    def rendereSetRequestParamsValue(self, params):
        set_request_param_values = ""

        code = "params.put(REQUEST_KEY_${field_upper}, m${field_capitalize});\n\t\t\t"
        template = Template(code)
        for paramObject in params:
            mapping = {
                "field_upper": paramObject["field"].upper(),
                "field_capitalize": paramObject["field"].capitalize()
            }
            set_request_param_values += template.substitute(mapping)

        return set_request_param_values

    def renderRequestParamsValid(self, params):
        request_params_valid = ""

        for index, paramObject in enumerate(params):
            suffix = ";" if (index + 1 == len(params)) else " && "
            code = "!TextUtils.isEmpty(m${field_capitalize})" + suffix
            template = Template(code)
            mapping = {
                "field_capitalize": paramObject["field"].capitalize()
            }
            request_params_valid += template.substitute(mapping)

        return request_params_valid

    def renderIsResponseDataValid(self, params):
        response_data_valid = ""
        for index, paramObject in enumerate(params):
            if paramObject["notnull"]:
                code = "\n\t\t\t&& object.has(RESPONSE_KEY_${field_upper})"
                template = Template(code)
                mapping = {
                    "field_upper": paramObject["field"].upper()
                }
                response_data_valid += template.substitute(mapping)

        return response_data_valid

    def renderResponseDataFromJson(self, params):
        response_data_from_json = ""
        for paramObject in params:
            if paramObject["type"] == "JSONHashMap":
                response_data_from_json += self.renderResponseJsonHashMapDataFromJson(paramObject)
            elif paramObject["type"] == "JSONObject":
                response_data_from_json += self.renderResponseJsonObjectDataFromJson(paramObject)
            elif paramObject["type"] == "JSONArray":
                response_data_from_json += self.renderResponseJsonArrayDataFromJson(paramObject)
            else:
                response_data_from_json += self.renderResponseBasicTypeDataFromJson(paramObject)

        return response_data_from_json

    def renderResponseJsonHashMapDataFromJson(self, paramObject):
        code = 'if (object.has(RESPONSE_KEY_${field_upper})) {\n\t\t\t\t' \
                   + 'm${field_capitalize}List = ${field_capitalize}.fromJsonMap(object.getJSONObject(RESPONSE_KEY_${field_upper}));\n\t\t\t}\n\t\t\t'
        template = Template(code)
        mapping = {
            "field_upper": paramObject["field"].upper(),
            "field_capitalize": paramObject["field"].capitalize()
        }
        return template.substitute(mapping)

    def renderResponseJsonArrayDataFromJson(self, paramObject):
        code = 'if (object.has(RESPONSE_KEY_${field_upper})) {\n\t\t\t\t' \
                   + 'm${field_capitalize}List = ${field_capitalize}.fromJsonArray(object.getJSONArray(RESPONSE_KEY_${field_upper}));\n\t\t\t}\n\t\t\t'
        template = Template(code)
        mapping = {
            "field_upper": paramObject["field"].upper(),
            "field_capitalize": paramObject["field"].capitalize()
        }
        return template.substitute(mapping)

    def renderResponseJsonObjectDataFromJson(self, paramObject):
        # if paramObject["notnull"]:
        #     code = "m${field_capitalize}.fromJson(object.getJSONObject(RESPONSE_KEY_${field_upper}));\n\t\t\t"
        # else:
        code = 'if (object.has(RESPONSE_KEY_${field_upper})) {\n\t\t\t\t' \
                   + 'm${field_capitalize} = ${field_capitalize}.fromJson(object.getJSONObject(RESPONSE_KEY_${field_upper}));\n\t\t\t}\n\t\t\t'
                   # + 'm${field_capitalize}.fromJson(object.getJSONObject(RESPONSE_KEY_${field_upper}));\n\t\t\t}\n\t\t\t'
        template = Template(code)
        mapping = {
            "field_upper": paramObject["field"].upper(),
            "field_capitalize": paramObject["field"].capitalize()
        }
        return template.substitute(mapping)

    def renderResponseBasicTypeDataFromJson(self, paramObject):
        # if paramObject["notnull"]:
        #     code = "m${field_capitalize} = object.get${field_type_capitalize}(RESPONSE_KEY_${field_upper});\n\t\t\t"
        # else:
        code = 'if (object.has(RESPONSE_KEY_${field_upper})) {\n\t\t\t\t' \
                   + 'm${field_capitalize} = object.get${field_type_capitalize}(RESPONSE_KEY_${field_upper});\n\t\t\t}\n\t\t\t'
        template = Template(code)
        mapping = {
            "field_upper": paramObject["field"].upper(),
            "field_capitalize": paramObject["field"].capitalize(),
            "field_type_capitalize": paramObject["type"].capitalize()
        }
        return template.substitute(mapping)


    def renderErrorCodeCase(self, error_codes):
        error_code_case_statements = ""

        for index, errorCode in enumerate(error_codes):
            suffix = "" if (index + 1 == len(error_codes)) else "\n\t\t\t"
            code = "case ERROR_CODE_${error_code}:\n\t\t\t\t/** ${error_desc} */\n\t\t\t\tbreak;" + suffix
            template = Template(code)
            mapping = {
                "error_desc": errorCode["comment"],
                "error_code": errorCode["code"]
            }
            error_code_case_statements += template.substitute(mapping)

        return error_code_case_statements

    def saveFile(self, path, content):
        f = open(path, 'w')
        f.write(content)
        f.close()

if __name__ == "__main__":
    taskGenerator = DataTaskGenerator()
    taskGenerator.generator()
