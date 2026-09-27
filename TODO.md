# TODO

## API 回應格式統一包裝(2026-09-24,前端 life-record-50 同步)— 已完成,待複習

完整格式規範跟 `error_code` 對照表見 `life-record-docs/api-error-codes.md`(單一事實來源)。

### 想複習的內容(標記給自己之後回來看)

1. **成功回應包裝**:`src/life_record_api/responses.py` 的 `EnvelopeJSONResponse` 繼承 `JSONResponse`,覆寫 `render()`,把 `content` 包成 `{"status": "success", "data": content}` 再交給 `super().render()` 處理。在 `main.py` 用 `FastAPI(default_response_class=EnvelopeJSONResponse)` 設成全域預設,不用改任何一支 route。
2. **驗證錯誤處理**:`exceptions.py` 的 `validation_exception_handler`,攔截 FastAPI 自動丟出的 `RequestValidationError`(使用者傳的資料格式不對時觸發),用 `exc.errors()` 取出訊息,組成 `error_code: E00001` 的錯誤格式。
3. **自訂例外 `AppException`**:繼承 `HTTPException`,多加一個 `error_code` 屬性(`HTTPException` 原生沒有地方放 `error_code`,只有 `status_code`/`detail`)。之後在 router/service 裡要主動拋錯誤,用 `raise AppException(status_code=404, error_code="E01001", detail="找不到這個分類")`。
4. **兩層 handler 的關係**:`app_exception_handler` 對應 `AppException`(有 `error_code`),`http_exception_handler` 對應普通 `HTTPException`(沒有 `error_code` 時的備案,統一給 `E00003`)。因為 `AppException` 是 `HTTPException` 的子類別,FastAPI 會依例外的實際型別,自動找**最精確符合**的 handler,兩者不衝突、不用自己判斷要走哪支。
5. **`main.py` 怎麼串起來**:用 `app.add_exception_handler(例外類型, handler函式)` 註冊,總共註冊三支:`RequestValidationError`、`AppException`、`HTTPException`。

複習時可以搭配 `src/life_record_api/responses.py`、`src/life_record_api/exceptions.py`、`main.py` 三個檔案的實際內容一起看。

### 已知限制(先不處理,之後有空再看)

**`/docs`(Swagger UI 自動文件)顯示的回應格式,沒有反映 `EnvelopeJSONResponse` 包的那層信封**。

原因:`/docs` 是照每支 route 的 `response_model` 型別標註產生文件的,這在寫程式碼時就決定好了;`EnvelopeJSONResponse` 的包裝發生在「轉成 bytes 送出去」的最後一步,兩者是 FastAPI 內部互相獨立的機制,不會自動同步。實測過 `/accounting/records` 這支,文件上寫的是裸的 `AccountingRecords`,但實際呼叫拿到的是包了 `{"status": "success", "data": {...}}` 的版本。

先不處理,因為前端(life-record-50)已經知道這個信封格式,不太需要靠自動文件去猜。如果之後要修:要幫每支 route 額外定義對應的「信封」Pydantic model(例如 `class SuccessEnvelope(BaseModel): status: Literal["success"]; data: AccountingRecords`),`response_model` 改指向信封 model 而不是原始資料 model;如果想通用所有型別,需要用到「泛型(Generic)」寫法,這是還沒學過的新概念。

之後(User 功能規劃時)要做,現在不急:

- **新使用者預設分類(category_list)**:使用者建立時,要順便幫他新增幾筆固定的預設分類(例如餐飲、交通)。不用另外開 table 存這份「預設清單」,直接寫死在程式碼(例如一個 `DEFAULT_CATEGORIES` 常數),在「建立使用者」的流程裡呼叫一個函式,迴圈把預設分類寫進 `category_list`,`user_id` 帶新使用者的 id。原因:這份清單是開發者自己決定的產品邏輯,不常變動,不需要透過資料庫動態調整,開新 table 反而多維護一組 schema 沒有實際好處。

## 記帳圖片上傳:GCS 孤兒檔案問題(2026-09-28)— 之後有空再處理

`src/life_record_api/services/accounting/records.py` 的 `insert_record`,`upload_image(data.image)` 是在 `session.commit()` 之前呼叫的。如果圖片已經成功上傳到 GCS,但接下來的 `session.commit()` 卻失敗(例如資料庫斷線、其他非預期錯誤),資料庫這邊會整個 rollback、不會留下這筆記帳,但 GCS 那邊的圖片檔案已經真的傳上去了,變成一個沒有任何 `record_images` 資料指向它的「孤兒檔案」。

現階段(個人專案、流量小)發生機率低,先不處理。之後有空可以考慮:
- 寫一支維護腳本,定期比對 GCS bucket 裡的檔案清單跟 `record_images.image_url`,找出沒被引用的檔案並刪除。
- 或改成「先 commit 資料庫,拿到 record 確定成功後,再上傳圖片,上傳失敗再回頭更新那筆記錄」,但這樣會讓「圖片上傳失敗」變成使用者要另外處理的情境,目前先接受「資料庫優先、圖片可能孤兒」這個較簡單的順序。
