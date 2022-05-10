
import json

import bizerror
from fastutils import jsonutils
from fastutils import strutils
from fastutils import cipherutils
from fastutils import rsautils



class AbstractResultPacker(object):
    """第1个位置参数加入了后缀，避免与kwargs中的参数冲突。
    """
    def pack_result(self, __result_Pu1dvy86uRLpdNu2Czyf, **kwargs):
        raise NotImplementedError()

    def pack_error(self, __error_Pu1dvy86uRLpdNu2Czyf, **kwargs):
        raise NotImplementedError()

    def unpack(self, __data_Pu1dvy86uRLpdNu2Czyf, **kwargs):
        raise NotImplementedError()



class SimpleJsonResultPacker(AbstractResultPacker):

    def pack_result(self, __result_Pu1dvy86uRLpdNu2Czyf, **kwargs):
        result = __result_Pu1dvy86uRLpdNu2Czyf
        return {
            "success": True,
            "result": result,
        }

    def pack_error(self, __error_Pu1dvy86uRLpdNu2Czyf, **kwargs):
        error = __error_Pu1dvy86uRLpdNu2Czyf
        return {
            "success": False,
            "error": error,
        }

    def unpack(self, __data_Pu1dvy86uRLpdNu2Czyf, **kwargs):
        data = __data_Pu1dvy86uRLpdNu2Czyf
        if not data:
            raise bizerror.BadResponseContent(content=data)
        if isinstance(data, (str, bytes)):
            try:
                data = json.loads(data)
            except Exception:
                raise bizerror.ParseJsonError(text=data)
        success = data.get("success", None)
        if success == True and "result" in data:
            return data["result"]
        elif success == None and "result" in data:
            return data["result"]
        if "error" in data:
            raise bizerror.BizError(data["error"]["message"], data["error"]["code"])
        else:
            raise bizerror.BadResponseContent(content=data)

class SafeJsonResultPacker(SimpleJsonResultPacker):
    
    def __init__(self, result_encoder=cipherutils.SafeBase64Encoder(), password_length=32, client_id_fieldname="clientId", encrypted_password_fieldname="encryptedPassword", encrypted_data_fieldname="encryptedData"):
        self.password_length = password_length
        self.encrypted_password_fieldname = encrypted_password_fieldname
        self.encrypted_data_fieldname = encrypted_data_fieldname
        self.result_encoder = result_encoder
        self.client_id_fieldname = client_id_fieldname

    def pack_result(self, __result_Pu1dvy86uRLpdNu2Czyf, **kwargs):
        result = __result_Pu1dvy86uRLpdNu2Czyf
        result = super().pack_result(result, **kwargs)
        return self.encrypt_data(result, **kwargs)

    def pack_error(self, __error_Pu1dvy86uRLpdNu2Czyf, **kwargs):
        error = __error_Pu1dvy86uRLpdNu2Czyf
        error =  super().pack_error(error, **kwargs)
        return self.encrypt_data(__error_Pu1dvy86uRLpdNu2Czyf, **kwargs)

    def encrypt_data(self, __data_Pu1dvy86uRLpdNu2Czyf, **kwargs):
        data = __data_Pu1dvy86uRLpdNu2Czyf
        # get client rsa publickey
        get_client_rsa_publickey = kwargs["get_client_rsa_publickey"]
        client_id = kwargs[self.client_id_fieldname]
        client_rsa_publickey = get_client_rsa_publickey(client_id)
        # do data encrypt
        result_text = jsonutils.simple_json_dumps(data)
        password = strutils.random_string(self.password_length)
        result_cipher = cipherutils.AesCipher(password=password, result_encoder=self.result_encoder)
        result_data = result_cipher.encrypt(result_text.encode("utf-8"))
        encrypted_password = rsautils.encrypt(password.encode(), client_rsa_publickey)
        return {
            self.encrypted_password_fieldname: encrypted_password,
            self.encrypted_data_fieldname: result_data,
        }
 
    def unpack(self, __data_Pu1dvy86uRLpdNu2Czyf, **kwargs):
        data = __data_Pu1dvy86uRLpdNu2Czyf
        if not data:
            raise bizerror.BadResponseContent(content=data)
        if isinstance(data, (str, bytes)):
            try:
                data = json.loads(data)
            except Exception:
                raise bizerror.ParseJsonError(text=data)
        client_rsa_privatekey = kwargs["client_rsa_privatekey"]
        encrypted_password = data[self.encrypted_password_fieldname]
        encrypted_data = data[self.encrypted_data_fieldname]
        password = rsautils.decrypt(encrypted_password, client_rsa_privatekey)
        result_cipher = cipherutils.AesCipher(password=password, result_encoder=self.result_encoder)
        data_json = result_cipher.decrypt(encrypted_data)
        return super().unpack(data_json, **kwargs)
