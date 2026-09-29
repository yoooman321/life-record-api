# life-record-api

後端 API,搭配前端主專案 `life-record` 使用。此檔案內容整理自與前端 session 的討論摘要(2026-09-17),供接續開發參考。

## 整體產品願景

使用者想做一個生活紀錄整合網站,取代原本分散在各 APP 的記帳/喝水/飲食/運動記錄。規劃的 tab:記帳、飲食、身體紀錄、運動、日記(可能再加「統計」tab 查看收支紀錄,尚未定案細節)。喝水目前併入身體紀錄或首頁小工具呈現。

## 技術棧(已定案)

- 前端:React 19 + Vite 8 + TypeScript,部署到 Vercel
- 後端:Python + FastAPI,容器化用 Docker,部署到 Google Cloud Run
- 資料庫:Neon(Serverless Postgres,已註冊帳號)
- 後端語言選 Python 是使用者想順便練習,非效能考量;若非 CPU-bound 工作 Node.js 也夠用,這點使用者知情但仍選擇 Python
- 後端走「模組化 monolith」(部署面):一個 FastAPI project,部署上是一份 Docker image、一個 Cloud Run 服務、一個 Neon DB,**不拆微服務**(個人專案流量小,拆分好處用不到)
- **後端內部資料夾組織(2026-09-23 改版)**:改採 FastAPI 官方教學(Bigger Applications + SQL (Relational) Databases 教學)的慣例,**依檔案類型分資料夾**,不是依功能分。也就是:
  - `src/life_record_api/db/`:資料庫基礎建設集中放這裡(`session.py` 放 engine + `get_session` 依賴注入函式、`create_tables.py` 放建表腳本)。這不算「依功能分」,是「依類型(資料庫基礎建設)分」,跟下面兩點是同一種精神,允許保留
  - `src/life_record_api/models.py`:**所有**功能的 table model 集中寫在這一個檔案(不再依功能拆檔案)。之後表一多、檔案變得難維護時,可以比照 `routers/` 的模式拆成 `models/accounting.py`、`models/diary.py` 這種依領域分檔案(但類型資料夾 `models/` 這一層還是保留),拆的時候要注意確保每個檔案都有被 import 到,不然 `create_all()` 不會建出那些表
  - `src/life_record_api/routers/`:每個功能一個檔案(例如 `routers/accounting.py`),裡面定義該功能的 API endpoint,最後在 `main.py` 用 `include_router` 掛上去
  - 這個決定只影響後端這個 repo 的內部組織,**不影響部署方式**,也**不需要跟前端同步**(前端維持自己的資料夾組織方式,見下一條)
- 前端是另一個獨立 project,依 feature 分資料夾,不照檔案類型分(這條只適用前端;後端已改成上面那條,兩邊不必一致)
- APP 化方向(尚未定案):傾向用 Capacitor 包現有 React 程式碼,而非重寫 React Native;主因是若要接 iPhone HealthKit,PWA/一般手機網頁完全無法存取(iOS 所有瀏覽器被迫用 WebKit,OS 層級限制),需要原生殼 + plugin

## 共用規劃文件的單一事實來源

前後端共用的規劃內容(產品設計、資料庫設計、跨專案里程碑規劃)已集中搬到獨立專案 `life-record-docs`(`/Users/fei/code/life-record-docs`),不再各自散落在 `life-record`(前端)或本專案裡:

- `life-record-docs/bookkeeping-slime/bookkeeping-slime.md`:記帳史萊姆產品設計文件
- `life-record-docs/bookkeeping-slime/datatable-design.md`:資料庫設計(單一事實來源,之後異動請直接改這邊,不要兩邊維護)
- `life-record-docs/schedule.md`:跨專案里程碑規劃 + 進度記錄(P1~P4)
- `life-record-docs/back-TODO.md`:後端(本專案)的 TODO(2026-09-29 定案)。使用者說「幫我寫進 TODO」時,寫的是這份檔案,**不是**本專案本地的 `TODO.md`(那份已經停用,只留一行指向這裡)。使用者另外會請 `life-record-docs` 那邊整理一份跨前後端的總 TODO,那是另一件事,不影響這條規則。

如果使用者開了 `life-record-docs` 的 session,可以用 `ListAgents` 找到,直接 `SendMessage` 過去溝通。

## 重點功能規劃:記帳史萊姆

詳細設計在 `life-record-docs/bookkeeping-slime/bookkeeping-slime.md`。把記帳做成養成遊戲:史萊姆有 6 個能力值(力量/敏捷/運氣/智力/體力/鈔能力),對應不同記帳分類;能力值累積到期後生成史萊姆,依最高能力值決定職業(戰士/弓箭手/盜賊/法師/富豪/聖騎士),可拿去打怪(自動戰鬥),賺金幣裝扮/升級。

**已定案的關鍵設計(這些會直接影響後端資料模型)**:

1. **能力值計算邏輯**:力量/敏捷/運氣/智力/體力用「筆數」累積(避免必需類別金額天生較大而壓過選擇性類別);鈔能力用「金額」累積(收入+投資,因為主題是「有多少錢」,且收入低頻高額用筆數沒意義)
2. **史萊姆三種狀態**:empty(虛線框架＋)→ growing(培育中)→ completed(凍結可戰鬥)
3. **Period(培育週期)**:欄位含 duration_type(1天/一週預設/一個月/自訂)、start_at/planned_end_at/actual_end_at、status(growing/completed)。**同一使用者同時間最多一個 growing 的 Period**
4. **結束時機**:自然到期(開 APP 時偵測)或提早結束(使用者主動按鈕),兩種都會跳出「要不要培育下一隻」的詢問
5. **Entry(記帳紀錄)**:需要 `period_id`(可為 null)。有 growing Period 就自動掛上;沒有的話 `period_id = null`,純紀錄,之後開新 Period 也不會回溯算入。沒有 growing Period 時記帳會跳提示詢問要不要先培育,可 toggle 不再提醒
6. **能力值不用累加計數器**,而是每次要顯示/結算時即時 SUM 該 growing Period 底下所有 Entry,新增/編輯/刪除記帳都會即時反映、不用寫回滾邏輯。只有 Period 變成 completed 那一刻才把算出來的數值**快照**進 Slime 表,之後不再重算
7. **統計 tab** 會撈全部 Entry(不分有無 period_id),跟史萊姆養成邏輯分開、共用同一份記帳資料

**開發優先序**:P1 記帳資料模型(跟 Phaser 無關,純資料)→ P2 生成史萊姆邏輯 → P3 Phaser 陽春 demo(一隻史萊姆打一隻怪,美術先用程式畫的 placeholder,跑通機制再換正式素材)→ P4 擴充(組隊/技能/boss/商店/金幣)

**未來構想(未排入優先序,暫定 P5)**:能力值結合其他生活紀錄功能(飲食/運動/身體紀錄/日記),因為各功能資料單位差很多、且會讓史萊姆模組耦合所有其他模組,先不做,等 P1~P4 純記帳版驗證好玩再評估。

## 記帳類別資料庫設計(P1 範圍)

完整 table/欄位設計以 `life-record-docs/bookkeeping-slime/datatable-design.md` 為準(單一事實來源)。摘要:`accounting_records`(記帳紀錄)、`periods`(培育週期)、`category_list`(類別總表)、`stat_list`(史萊姆能力值,細節待補)、`tag_list`(標籤總表)、`record_tags`、`record_images` 共 7 張表,命名統一 snake_case,索引尚未規劃。User Table 尚未設計,`user_id` 現階段固定寫死為 `0`。另有 `user_category_list`、`user_tag_list` 兩張表已棄用不實作(原因見該文件)。

## 注意事項

- 前端要自己練習實作,**不需要代寫前端程式碼**;後端目前也是使用者自己動手,協助時優先用引導/解釋的方式,而非直接寫完整程式碼(除非使用者明確要求)。
- **使用者是完全不懂後端、資料庫原理的初學者**。解釋任何後端/資料庫概念(例如 Docker、ORM、migration、連線、環境變數等)時,盡量用白話、生活化的比喻,避免預設他已經懂術語或前後文,寧可講細一點、多舉例,也不要跳過基礎環節。
- 更細節的部分(例如 Pydantic model 草稿)以本地 repo 實際檔案內容為準,這份文件僅供背景脈絡參考。
