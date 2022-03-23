#!/usr/bin/env python3
# encoding: utf-8

from cortexutils.responder import Responder
import requests
import json

class ScorecardSubmit(Responder):
    def __init__(self):
        Responder.__init__(self)
        self.api_key = self.get_param('config.api_key', None, "API key is missing")
        self.base_uri = self.get_param('config.base_uri', None, "Base uri is missing")
        self.reason = self.get_param('config.reason', None, "Reason to close issue is missing")

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Token {}".format(self.api_key)
        }

    def submit(self, domain, issue_type, issue_id):
        payload  = {
                    "issue_ids": [issue_id],
                    "feedback_type": self.reason
        }

        response = requests.post("{}/companies/{}/issues/{}/feedback/".format(self.base_uri, domain, issue_type),
                            headers=self.headers, 
                            data=json.dumps(payload))

        if response.ok:
             response.close()
             return True
        else:
            self.error("Unable to send feedback. Error: {} - {}. ".format(response.status_code, response.reason))

    def parse_data(self, data, string_to_parse):
        matching = [s for s in data if string_to_parse in s]
        if matching:
            if string_to_parse == "type":
                parsed_data = matching[0].replace("type:", "").strip()
            else:
                parsed_data = matching[0].replace(string_to_parse, "").replace("*","").strip()
            return parsed_data
        else:
            self.error("{} was not found in data".format(string_to_parse))

                   
    def run(self):
        Responder.run(self)

        if self.data_type == "thehive:case":
            description = self.get_param("data.description", None, "Description is missing")
            tags = self.get_param("data.tags", None, "Tags are missing")
        elif self.data_type == "thehive:case_task" or self.data_type == "thehive:case_artifact":
            description = self.get_param("data.case.description", None, "Description is missing")
            tags = self.get_param("data.case.tags", None, "Tags are missing")
        else:
            self.error("Invalid dataType")

        description_array = description.splitlines()
        issue_id = self.parse_data(description_array, "issue_id:")
        domain = self.parse_data(description_array, "parent_domain:")
        issue_type = self.parse_data(tags, "issue_type:")

        if (self.submit(domain, issue_type, issue_id)):
            self.report({"message": "Submitted to Security ScoreCard"})
        else:
            self.error("Failed to submit")


    def operations(self, raw):
        return [self.build_operation("AddTagToArtifact", tag='scorecard:closed')]


if __name__ == '__main__':
       ScorecardSubmit().run()