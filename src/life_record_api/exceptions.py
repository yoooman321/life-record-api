from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [error["msg"] for error in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"status": "error", "error_code": "E00001", "errors": errors},
    )


class AppException(HTTPException):
    # __init__: new 一個物件時自動被呼叫的方法
    def __init__(self, status_code: int, error_code: str, detail: str):
        # 先呼叫父類別(HTTPException)原本的建構邏輯,把 status_code、detail 正常設定好,這部分不用自己重新實作
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_code": exc.error_code,
            "errors": [exc.detail],
        },
    )


# 萬一你或某個套件內部不小心直接 raise HTTPException(...)(沒有用你自訂的 AppException,沒有 error_code),也要有個備案,不然那種錯誤會漏網,沒被轉換成你要的格式。再寫一支處理普通 HTTPException 的 handler,給一個通用的 error_code
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "error_code": "E00003", "errors": [exc.detail]},
    )


# 之後你在 router 或 service 裡要拋錯誤時,就這樣寫:
# raise AppException(status_code=404, error_code="E01001", detail="找不到這個分類")
