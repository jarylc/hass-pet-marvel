import json
import logging
import time
import hashlib
from typing import Any

import aiohttp
from aiohttp import ClientError
from alibabacloud_iot_api_gateway.models import Config, CommonParams, IoTApiRequest
from alibabacloud_tea_util.models import RuntimeOptions

from .client import Client
from .const import VALID_COUNTRY_TO_CODE_MAPPING

_LOGGER = logging.getLogger(__name__)

ERROR_API_NOT_CONNECTED = "API not connected. Please call connect() first."


# for debug only
async def async_add_executor_job(target, *args):
    return target(*args)


class APIAuthError(Exception):
    """Exception class for auth error."""


class APIConnectionError(Exception):
    """Exception class for connection error."""


class PetMarvelAPI:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        async_executor=async_add_executor_job,
        base_url="https://app.api.ap.nyhx.vip",
        base_cn_url="https://app.api.nyhx.vip",
        app_id: str = "b0baae0630f444b0811ea3c2eb212171",
        app_key: str = "34280983",
        app_secret: str = "d342fca55b41d9b96490bda0c9c703b3",
        language="en-US",
    ) -> None:
        self._base_url = base_url
        self._base_cn_url = base_cn_url
        self._app_id = app_id
        self._app_key = app_key
        self._app_secret = app_secret
        self._language = language
        self._session = session
        self._identity_id = None
        self._oa_api_gateway_endpoint = None
        self._api_gateway_endpoint = None
        self._ali_authentication_token = None
        self._sid = None
        self._iot_token = None
        self.connected: bool = False
        self.async_executor = async_executor

    async def connect(
        self, country: str, email: str, password: str, first_run: bool = True
    ):
        if not self.connected:
            await self._load_auth_tokens(country, email, password)
            await self._load_region_data()
            vid = await self._get_vid()
            self._sid = await self._get_sid(vid)
        try:
            self._iot_token = await self._get_iot_token(self._sid)
            self.connected = True
        except APIAuthError as exc:
            if first_run:
                await self.connect(country, email, password, False)
            else:
                raise exc

    async def get_product_list(self):
        if not self.connected:
            raise APIConnectionError(ERROR_API_NOT_CONNECTED)
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self._api_gateway_endpoint,
        )
        client = Client(config)
        request = CommonParams(
            api_ver="1.1.7", language=self._language, iot_token=self._iot_token
        )
        body = IoTApiRequest(
            version="1.0", params={"productStatusEnv": "release"}, request=request
        )
        response = await self.async_executor(
            client.do_request,
            "/thing/productInfo/getByAppKey",
            "https",
            "POST",
            None,
            body,
            RuntimeOptions(),
        )
        response_data = json.loads(response.body)
        if response_data["code"] != 200:
            raise APIConnectionError(
                "Error getting product list: " + response_data["message"]
            )
        return response_data["data"]

    async def get_devices(self, page_no: int = 1, page_size: int = 20):
        if not self.connected:
            raise APIConnectionError(ERROR_API_NOT_CONNECTED)
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self._api_gateway_endpoint,
        )
        client = Client(config)
        request = CommonParams(
            api_ver="1.0.8", language=self._language, iot_token=self._iot_token
        )
        body = IoTApiRequest(
            version="1.0",
            params={
                "pageSize": page_size,
                "thingType": "DEVICE",
                "nodeType": "DEVICE",
                "pageNo": page_no,
            },
            request=request,
        )
        response = await self.async_executor(
            client.do_request,
            "/uc/listBindingByAccount",
            "https",
            "POST",
            None,
            body,
            RuntimeOptions(),
        )
        response_data = json.loads(response.body)
        if response_data["code"] != 200:
            raise APIConnectionError(
                "Error getting devices: " + response_data["message"]
            )
        return response_data["data"]["data"]

    async def get_device_properties(self, iot_id: str):
        if not self.connected:
            raise APIConnectionError(ERROR_API_NOT_CONNECTED)
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self._api_gateway_endpoint,
        )
        client = Client(config)
        request = CommonParams(
            api_ver="1.0.4", language=self._language, iot_token=self._iot_token
        )
        body = IoTApiRequest(version="1.0", params={"iotId": iot_id}, request=request)
        # send request
        response = await self.async_executor(
            client.do_request,
            "/thing/properties/get",
            "https",
            "POST",
            None,
            body,
            RuntimeOptions(),
        )
        response_data = json.loads(response.body)
        if response_data["code"] != 200:
            raise APIConnectionError(
                "Error getting device properties: " + response_data["message"]
            )
        return response_data["data"]

    async def set_device_properties(self, iot_id: str, items: dict[str, Any]):
        if not self.connected:
            raise APIConnectionError(ERROR_API_NOT_CONNECTED)
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self._api_gateway_endpoint,
        )
        client = Client(config)
        request = CommonParams(
            api_ver="1.0.4", language=self._language, iot_token=self._iot_token
        )
        body = IoTApiRequest(
            version="1.0", params={"items": items, "iotId": iot_id}, request=request
        )
        response = await self.async_executor(
            client.do_request,
            "/thing/properties/set",
            "https",
            "POST",
            None,
            body,
            RuntimeOptions(),
        )
        response_data = json.loads(response.body)
        if response_data["code"] != 200:
            raise APIConnectionError("Error setting device properties.")

    async def _load_auth_tokens(self, country: str, email: str, password: str):
        path = "/app/v1/auth/login"
        try:
            ts, sign = self._sign(path)
            area = VALID_COUNTRY_TO_CODE_MAPPING[country]
            async with self._session.post(
                url=self._base_cn_url if area == "86" else self._base_url,
                json={
                    "account": email,
                    "account_type": 0 if area == "86" else 1,
                    "area": area,
                    "clientid": "",
                    "password": password,
                    "brand": "",
                },
                headers={
                    "content-type": "application/json; charset=UTF-8",
                    "appid": self._app_id,
                    "ts": ts,
                    "sign": sign,
                    "version": "2.0.47",
                    "user-agent": "okhttp/3.12.8",
                },
            ) as response:
                response_data = await response.json()
                if response_data["code"] != 0:
                    raise APIAuthError(
                        "Error connecting to api. Invalid username or password."
                    )
                self._identity_id = response_data["data"]["identityid"]
                self._ali_authentication_token = response_data["data"]["token"]
        except ClientError as e:
            raise APIConnectionError("Error connecting to api: " + str(e))

    async def _load_region_data(self):
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain="cn-shanghai.api-iot.aliyuncs.com",
        )
        client = Client(config)
        request = CommonParams(api_ver="1.0.2", language=self._language)
        body = IoTApiRequest(
            version="1.0",
            params={
                "authCode": self._ali_authentication_token,
                "type": "THIRD_AUTHCODE",
            },
            request=request,
        )
        response = await self.async_executor(
            client.do_request,
            "/living/account/region/get",
            "https",
            "POST",
            None,
            body,
            RuntimeOptions(),
        )
        response_data = json.loads(response.body)
        if response_data["code"] != 200:
            raise APIConnectionError(
                "Error loading region data." + response_data["message"]
            )
        self._oa_api_gateway_endpoint = response_data["data"]["oaApiGatewayEndpoint"]
        self._api_gateway_endpoint = response_data["data"]["apiGatewayEndpoint"]

    async def _get_vid(self):
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self._oa_api_gateway_endpoint,
        )
        client = Client(config)
        body = {
            "request": {
                "context": {"appKey": self._app_key},
                "config": {"version": 0, "lastModify": 0},
                "device": {},
            }
        }
        response = await self.async_executor(
            client.do_request_raw,
            "/api/prd/connect.json",
            "https",
            "POST",
            None,
            body,
            RuntimeOptions(),
        )
        response_data = json.loads(response.body)
        if response_data["success"] != "true":
            raise APIConnectionError("Error getting vid.")
        if response_data["data"]["successful"] != "true":
            raise APIConnectionError(
                "Error getting vid: " + response_data["data"]["message"]
            )
        return response_data["data"]["vid"]

    async def _get_sid(self, vid: str):
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self._oa_api_gateway_endpoint,
        )
        client = Client(config)
        headers = {"Vid": vid}
        body = {
            "loginByOauthRequest": {
                "authCode": self._ali_authentication_token,
                "oauthPlateform": 23,
                "oauthAppKey": self._app_key,
                "riskControlInfo": {},
            }
        }
        response = await self.async_executor(
            client.do_request_raw,
            "/api/prd/loginbyoauth.json",
            "https",
            "POST",
            headers,
            body,
            RuntimeOptions(),
        )
        response_data = json.loads(response.body)
        if response_data["success"] != "true":
            raise APIAuthError("Error getting sid: " + response_data["errorMsg"])
        if response_data["data"]["successful"] != "true":
            raise APIAuthError("Error getting sid: " + response_data["data"]["message"])
        return response_data["data"]["data"]["loginSuccessResult"]["sid"]

    async def _get_iot_token(self, sid: str):
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self._api_gateway_endpoint,
        )
        client = Client(config)
        request = CommonParams(api_ver="1.0.4", language=self._language)
        body = IoTApiRequest(
            version="1.0",
            params={
                "request": {
                    "authCode": sid,
                    "accountType": "OA_SESSION",
                    "appKey": self._app_key,
                }
            },
            request=request,
        )
        response = await self.async_executor(
            client.do_request,
            "/account/createSessionByAuthCode",
            "https",
            "POST",
            None,
            body,
            RuntimeOptions(),
        )
        response_data = json.loads(response.body)
        if response_data["code"] != 200:
            self.connected = False
            raise APIAuthError("Error getting iot token: " + response_data["message"])
        return response_data["data"]["iotToken"]

    async def _invoke_service(self, iot_id: str, identifier: str, args: dict[str, Any]):
        if not self.connected:
            raise APIConnectionError(ERROR_API_NOT_CONNECTED)
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self._api_gateway_endpoint,
        )
        client = Client(config)
        request = CommonParams(
            api_ver="1.0.5", language=self._language, iot_token=self._iot_token
        )
        body = IoTApiRequest(
            version="1.0",
            params={"args": args, "identifier": identifier, "iotId": iot_id},
            request=request,
        )
        response = await self.async_executor(
            client.do_request,
            "/thing/service/invoke",
            "https",
            "POST",
            None,
            body,
            RuntimeOptions(),
        )
        response_data = json.loads(response.body)
        if response_data["code"] != 200:
            raise APIConnectionError("Error invoking service.")

    def _sign(self, path="/app/v1/auth/login") -> (str, str):
        ts = int(time.time())
        return f"{ts}", hashlib.md5(f"{self._app_id}{path}{ts}".encode()).hexdigest()
