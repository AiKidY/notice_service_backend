#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class MyResponse(object):
    def __init__(self):
        self.__RESPONSE = {
            "code": 0,
            "message": "success",
            "data": {}
        }

    @property
    def get_resp(self):
        return self.__RESPONSE


class ErrorResponse:
    ExceptionError = {
        "code": 6450001,
        "message": "Exception Error."
    }
    ParamsCheckError = {
        "code": 6450002,
        "message": "Error request: Params check failed."
    }
    BizCodeError = {
        "code": 6450003,
        "message": "Error request :Unknown bizCode"
    }

# if __name__ == '__main__':
#     import pdb
#     pdb.set_trace()
#     ErrorResponse.LogicError.get("code")
