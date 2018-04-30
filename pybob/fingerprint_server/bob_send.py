"""Simple interface for sending barcodes, etc. back to the server."""

import sys


from json_rpc_client import JsonRpcClient


class BobApi(object):
    def __init__(self, endpoint, client_type, client_id):
        """
        Arguments:
            endpoint:       url of api endpoint for sodad
            client_type:    0 or 1 for normal or soda machine, respectively
            client_id:      Usually 0, but to support multiple interfaces.
        """
        if client_id is None or client_type is None:
            raise Exception("client_id and client_type cannot be None")

        self.client = JsonRpcClient(endpoint)
        self.client_id = client_id
        self.client_type = client_type

    def send_enroll_progress(self, result):
        args = [self.client_type, self.client_id, result]
        return self.client.call("Soda.fp_enroll_progress", *args)

    def send_identify_result(self, result, userid):
        args = [self.client_type, self.client_id, result, userid]
        return self.client.call("Soda.fp_identify_result", *args)


def main():
    pass

if __name__ == "__main__":
    sys.exit(main())

