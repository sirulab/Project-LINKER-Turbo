# Project-LINKER-Turbo

這是一個展現使用AI加速開發的專案。Project-LINKER專注在how, 本專案檢討的why&what。跑過一遍研究提案發想到實踐流程，使用專案與產品思考框架，形成工作流。

為按時間收費的小型顧問公司打造的輕量級專案營利追蹤工具。透過無縫整合「專案預算(時間)」與「實際工時」，讓專案經理掌控專案進度，同時顧問能快速簡易完成工時回報。價值在於消除專案中的「隱形工時」與「過度服務 (Over-servicing)」，讓時間真正與金錢掛鉤。

荷蘭的 Teamleader 完美實現了從 CRM 報價到專案管理，再到 Invoice 請款的「一條龍資料不斷鏈」。Teamleader 體積龐大且設定繁瑣。我們的 MVP 將捨棄複雜的 CRM 模組，專注打透「時間/預算整合」的輕量級體驗，特別針對 30 人以下的顧問團隊，提供最快能看出「專案賺不賺錢」的捷徑。

### 核心功能 (Core Features)

為了快速驗證市場價值，MVP (最小可行性產品) 將專注於以下核心功能：
1. **任務時數配置**：根據報價單下拆解任務，賦予預估時數。
2. **工時回報介面**：顧問針對特定任務輸入實際耗用工時。
3. **進度儀錶板**：即時動態比對「總預算時數」與「已用時數」，透過視覺化圖表讓專案經理掌握專案，顧問看見剩餘時數配額。

### 技術棧 (Tech Stack)

落實 Phase 01 的商業需求，定義 MVP 的底層技術基底與資料結構。配合「AI 加速開發」的策略，在架構設計上將優先考量「清晰度」與「功能解耦」，為快速迭代建立穩固的基礎。

* **後端框架**：FastAPI (具備高效能、非同步支援與自動化 OpenAPI 文件生成)。
* **資料庫 ORM**：SQLModel
* **資料庫引擎**：SQLite (初期 MVP 快速開發與單機部署)，保留未來無縫轉移至 PostgreSQL 的能力。
* **前端渲染**：Jinja2 Templates + Bootstrap 5 (適合快速打造後台管理與表單填寫介面) + HTMX (進行局部畫面替換)
* **資料驗證**：Pydantic (確保 API 輸入輸出的資料型態正確)。

**架構決策理念 (Architecture Decision Record)**
* **捨棄超級工廠 (Drop Unified Factory)**：過去為了符合 DRY 原則，常將 CRUD 抽象成共用的 Factory。但在 AI 輔助開發的工作流中，「清晰 (Clarity)」大於「不重複 (DRY)」。AI 能極快地生成樣板代碼，因此我們選擇讓代碼具備高度可讀性，而非將邏輯隱藏在複雜的繼承關係中。
* **依功能切片 (Feature-driven)**：系統不以技術分層（不分龐大的 `routers`, `services` 資料夾），而是以「業務功能 (Use Case)」作為資料夾劃分。每個功能切片擁有自己的路由、驗證邏輯與資料庫操作。

### 資料表模型

以下為 SQLModel 的核心結構與關聯定義：

1. `Company` `1` to `N` `Project`
2. `Project` `1` to `N` `Quote`
3. `Quote` `1` to `N` `Task`
4. `Task` `1` to `N` `Timesheet`
5. `Employee` `1` to `N` `Timesheet`

### 資料夾結構

```text
/Project-LINKER-Turbo
├── .gitignore            
├── requirements.txt      
├── Dockerfile            
├── docker-compose.yml    
├── .env.example          
│
└── src/                  
    ├── main.py           # [系統入口]啟動 FastAPI，註冊所有 Features 的 Routers
    ├── database.py       # 共用：資料庫連線與 Session 管理
    ├── models.py         # 共用：定義 6 個 SQLAlchemy Tables
    │
    ├── static/           # [前端]
    │   ├── css/          # bootstrap.min.css, style.css
    │   └── js/           # bootstrap.bundle.min.js
    │
    ├── templates/        # [前端]
    │   ├── base.html     # 全域共用版型
    │   ├── components/   
    │   └── features/     
    │       ├── manage_projects/  # list.html, edit.html
    │       ├── manage_quotes/
    │       └── submit_timesheet/ # timesheet_form.html
    │
    ├── shared/               # 重複模塊 (DRY)
    │   ├── dependencies.py   # 例如：get_current_user, get_db_session
    │   ├── utils.py          # 例如：日期轉換工具、計算公式
    │   └── schemas.py        # 例如：共用的 ErrorResponse
    |
    └── features/         # [垂直切片]
        ├── manage_employees/
        │   ├── router.py 
        │   └── schemas.py
        │
        ├── manage_companies/
        │   ├── router.py 
        │   └── schemas.py
        │
        ├── manage_projects/
        │   ├── router.py
        │   └── schemas.py
        │
        ├── manage_quotes/
        │   ├── router.py
        │   └── schemas.py
        │
        ├── manage_tasks/
        │   ├── router.py
        │   └── schemas.py
        │
        ├── submit_timesheet/
        │   ├── router.py 
        │   ├── schemas.py
        │   └── queries.py
        │
        └── analyze_burn_rate/
            ├── router.py
            └── services.py
```
*(結構引用自 `Phase02_技術棧&架構.md`)*

### Code Review 實踐 (團隊協作與架構防腐)

在本專案極度依賴 AI 輔助生成的背景下，人類工程師的 Code Review 職責將從「檢查語法錯誤」轉移至「捍衛商業邏輯與架構一致性」：

1. **嚴守驗收標準 (Acceptance Criteria)**：審查 API 邏輯是否精準落實 `Phase02_使用者故事.md` 中的 AC，例如確保 `analyze_burn_rate` 確實具有 `(已用時數/總預算時數)*100% > 80%` 的防超支紅燈判斷。
2. **防範垂直切片被破壞**：因為專案採用 Feature-driven 架構，Review 時需嚴格禁止不同 `features/` 資料夾之間的服務邏輯互相依賴（高耦合）。若有共用邏輯，必須重構至 `shared/` 模組中。
3. **資料庫正規化驗證**：審查資料庫寫入行為，例如提交工時 (`submit_timesheet`) 時，確保僅寫入 `task_id`，而不再冗餘儲存 `project_id` 以確保資料的單一真值來源 (Single Source of Truth)。
4. **統一語言 (Ubiquitous Language) 稽核**：確保 AI 產出的變數與欄位名稱（如 `Timesheet`, `Task`, `quantity`）始終與 `Phase02_模型.md` 中定義的語言字典一致，避免上下文錯亂。

### 本地端開發設定

請依照以下步驟在本地環境中運行本專案（本專案捨棄了舊版的 Unified Factory，改由 SQLModel 於啟動時自動映射資料表）：

**1. 複製專案與建立虛擬環境**

```bash
git clone https://github.com/sirulab/Project-LINKER-Turbo.git
cd Project-LINKER-Turbo
python -m venv venv

# 啟動虛擬環境 (Windows)
venv\Scripts\activate
# 啟動虛擬環境 (macOS/Linux)
source venv/bin/activate
```

**2. 安裝依賴套件**

```bash
pip install -r requirements.txt
```

**3. 啟動伺服器 (資料庫將由 SQLModel 自動初始化)**

```bash
uvicorn src.main:app --reload
# 或執行 python src/main.py (若 main.py 內已配置 uvicorn.run)
```
