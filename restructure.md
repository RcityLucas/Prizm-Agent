为了达成这个目标，我们可以深入分析当前的问题根源，并提出一个更统一、健壮、简洁的数据库交互方案。
当前方案存在的问题根源分析：
1.
数据库交互方式的多样性与不一致性:
◦
项目中使用了自定义的 SurrealDBHttpClient 来通过 HTTP API (/key/... 和 /sql 端点) 与 SurrealDB 交互-,-。
◦
SurrealStorage 类同时支持使用官方的 SurrealDB WebSocket 客户端和自定义的 HTTP 客户端。
◦
在 Manager 层 (BaseManager, EnhancedTurnManager, UserProfileManager, SemanticIndexManager), 记录的创建 (create_record, create_profile, create_index_entry) 有时直接构建原始 SQL INSERT 语句并通过 client.execute_sql 执行-,-,-,-，这与 SurrealDBHttpClient 中使用 /key/... 端点创建记录的方法 以及其异步版本 create_record_async 并存。
◦
查询操作 (get_records, get_turns) 也存在多种实现，包括使用 client.get_records (其内部可能构建 SQL 或使用 /key/...，并且包含了复杂的响应格式处理和备用查询逻辑-,-)，以及直接构建 SQL SELECT 语句通过 client.execute_sql 或 client.query 执行-,。
◦
这种多种交互方式并存，缺乏单一的、推荐的模式，增加了理解和维护的复杂性。
2.
自定义 HTTP 客户端的不稳定性与复杂的响应处理:
◦
SurrealDBHttpClient 中的 get_records 方法包含了对多种响应格式的复杂处理和过滤逻辑-,-，并明确在某些情况下会尝试备用 SQL 查询-,-,-。这表明通过 HTTP API 获取的数据结构可能不够稳定或解析不够完善。
◦
parse_surreal_response 函数的存在本身就是为了处理 SurrealDB 返回的不同格式-，其内部逻辑也相对复杂-。
◦
TurnManager.create_turn_async 在调用 client.create_record_async 后会执行额外的验证查询，如果验证失败或创建失败，会回退到直接执行 SQL INSERT 语句-。这种显式的验证和回退机制强烈暗示 client.create_record_async 方法（很可能对应于 /key/... 的 PUT 请求）在某些情况下并不可靠，而直接 SQL INSERT 被视为更稳定的备选方案。
3.
同步与异步操作的混用和手动事件循环管理:
◦
尽管项目支持异步操作，但在 SurrealStorage 的 _ensure_connected 方法中提到，在新版本 surrealdb 1.0.4 中大多数方法是同步的，但为了兼容性保留了异步签名。同时，_ensure_connected 每次都会创建一个新的连接实例来解决连接问题，这效率低下。
◦
在 SurrealMemory 类中，为了在同步方法 (add, get, clear) 中调用异步存储方法 (storage.create, storage.query)，使用了 asyncio.new_event_loop() 和 loop.run_until_complete() 来手动创建和管理事件循环-。
◦
在 async_utils.py 中也提供了 run_async 函数，其目的也是在同步上下文（如多线程 Web 应用）中运行异步函数，同样使用了 asyncio.new_event_loop() 和 loop.run_until_complete()-。
◦
在 init_storage_factory 中也使用了 asyncio.new_event_loop() 和 loop.run_until_complete() 来调用异步初始化方法。
◦
这种手动、多次创建和管理事件循环的方式是典型的反模式，会导致性能问题，并可能在复杂的多线程/多协程环境中引入难以调试的问题。正确的做法通常是在应用程序的入口点运行一个事件循环，并通过 await 或 asyncio.to_thread/run_in_executor 来协调同步和异步代码。
4.
代码冗余和职责不清:
◦
存在 TurnManager 和 EnhancedTurnManager，它们都管理轮次并提供类似的功能,。尽管 EnhancedTurnManager 描述中使用 HTTP API，但其 create_turn 却明确使用 SQL INSERT-。这种并存和职责模糊增加了混乱。
◦
BaseManager 提供了通用的数据库操作方法 (create_record, get_record 等)-，但这些方法在各个具体的 Manager 类中又被调用，并且具体的 Manager 类中又存在直接调用 client 的不同方法甚至构建 SQL 的情况,,,,-,-,-。
您提到的“不用官方的方式测试会失败”，很可能指的是使用自定义 HTTP 客户端的 /key/... 端点操作（比如 create_record）不如直接执行 SQL (execute_sql) 来得稳定可靠，导致基于前者的测试更容易失败。这里的“官方方式”可能更倾向于您认为稳定的 SQL 执行路径。
更健壮且代码更简洁的方案：统一基于参数化 SQL 的 HTTP 交互
基于以上分析，为了提高系统的健壮性和代码的简洁性，核心思想是统一数据库交互方式，并彻底解决同步/异步混用的问题。
最推荐的方案是：以您现有的自定义 SurrealDBHttpClient 为基础，但将所有数据操作（CRUD、查询、Schema 定义等）统一通过 /sql 端点执行参数化 SQL 查询。
以下是更详细的方案步骤：
步骤 1: 将 SurrealDBHttpClient 重构为统一的参数化 SQL 客户端
•
核心功能: SurrealDBHttpClient 只保留执行参数化 SQL 的核心方法，例如 execute_sql_async-（已存在）和其同步版本 execute_sql-（已存在，但需要确保内部逻辑只调用 /sql 端点）。
•
移除 /key/... 方法: 删除或重构 create_record, get_record, update_record, delete_record 及其异步版本-,-。如果需要保留这些方法的名称以减少上层代码修改，则在这些方法内部改写逻辑，使其通过构建相应的 SQL 语句并调用 execute_sql 或 execute_sql_async 实现。
•
规范响应解析: 将所有 /sql 端点返回结果的解析逻辑统一到 parse_surreal_response 函数中-，并彻底修复其健壮性，确保它能正确处理 /sql 端点的各种成功和失败响应格式。移除 get_records 中复杂的、针对不同格式的备用解析逻辑-。
•
移除复杂备用逻辑: 删除 get_records 中尝试多种查询方式（直接 SQL, 参数化 SQL, 备用 RETURN SELECT）-,- 的复杂逻辑。依赖于 /sql + 参数化查询的稳定性。
•
确保参数化查询的使用: 强制要求所有通过 /sql 执行的查询都使用参数化方式，而不是手动拼接 SQL 字符串,,-。这由 execute_sql / execute_sql_async 方法本身来保障。
•
保持同步和异步方法的对应: 确保客户端的每个同步方法都有对应的异步版本，并使用 requests 和 aiohttp 实现。
步骤 2: 重构 Manager 层
•
移除冗余 Manager: 评估 TurnManager 和 EnhancedTurnManager,，只保留一个。统一使用保留的 Manager 类（例如 TurnManager），并将其功能集成进来。
•
统一数据库操作调用: 所有 Manager 类（SessionManager, TurnManager, UserProfileManager, SemanticIndexManager, ContextManager）都只能通过其内部持有的 SurrealDBHttpClient 实例进行数据库交互。
•
使用参数化 SQL 构建器: 所有需要执行数据库操作的地方，不再手动拼接 SQL 字符串，而是使用 db_queries.py 中提供的参数化 SQL 构建函数- 或类似方法来生成 SQL 模板和参数字典，然后调用 client.execute_sql 或 client.execute_sql_async 执行。
◦
例如，UserProfileManager.create_profile 中手动构建 INSERT SQL- 的部分应改为：构建数据字典 -> 使用构建器生成 INSERT SQL 和参数 -> 调用 client.execute_sql (或 execute_sql_async).
•
移除 Manager 内部的验证和回退逻辑: 例如，TurnManager.create_turn_async 中的验证查询和 SQL 插入回退逻辑- 应该移除，因为它旨在解决底层 client.create_record_async 的不稳定性。通过修复和统一底层客户端，上层 Manager 应信任客户端方法的执行结果。
•
确保异步方法的正确使用: 在 Manager 的异步方法中，调用客户端的异步方法时必须使用 await 关键字。
步骤 3: 简化 SurrealStorage 或考虑移除
•
SurrealStorage 类同时支持 WebSocket 和 HTTP 客户端，并在 _ensure_connected 中包含复杂的连接管理逻辑-。既然我们已经有了自定义的 SurrealDBHttpClient 并计划统一使用它，那么 SurrealStorage 的 WebSocket 客户端选项变得不必要。
•
选项 A (简化): 将 SurrealStorage 修改为只使用 SurrealDBHttpClient (移除 use_http 参数和 WebSocket 客户端逻辑)。其 create, read, update, delete, query 等方法- 都委托给内部的 http_client 实现，并移除自身复杂的连接管理 (_ensure_connected)、SQL 构建 和回退逻辑。让它成为 SurrealDBHttpClient 的一个薄包装层，或者一个基于 SurrealDBHttpClient 实现 BaseStorage 接口的版本。
•
选项 B (移除): 如果 SurrealStorage 只是一个通用的存储接口实现，而实际业务逻辑都在 Manager 类中，并且 Manager 类直接使用了 SurrealDBHttpClient,,,,,，那么可以考虑移除 SurrealStorage 类，让 Manager 类直接作为业务逻辑与 SurrealDBHttpClient 之间的中介。StorageFactory 则直接创建并提供 Manager 实例。
步骤 4: 彻底解决同步/异步问题
•
应用程序入口点: 在应用程序的顶级入口（如 main.py 或 FastAPI 应用启动处），使用 asyncio.run() 来启动整个异步事件循环，并且只调用一次。
•
移除手动事件循环管理: 删除 SurrealMemory 中- 和 async_utils.run_async- 中手动创建和管理事件循环的代码 (asyncio.new_event_loop(), loop.run_until_complete(), asyncio.set_event_loop())。
•
异步化所有 DB 操作: 确保所有直接或间接与数据库交互的方法都是 async def 方法（除非它们确实不执行任何 awaitable 操作，例如纯同步计算）。
•
同步代码调用异步: 如果在应用程序的某个同步部分确实需要调用异步数据库方法，使用 asyncio.to_thread 或 loop.run_in_executor 将异步调用包装在线程池中执行，而不是手动创建事件循环。
•
异步代码调用同步: 如果在应用程序的某个异步部分需要调用少量、必须同步执行且耗时的代码，也应使用 asyncio.to_thread 或 loop.run_in_executor 避免阻塞事件循环。不过，理想情况下，数据库交互层应该是完全异步的。
步骤 5: 优化错误处理和日志记录
•
统一错误处理: 在 SurrealDBHttpClient 中捕获数据库交互相关的异常，并根据 HTTP 状态码和 SurrealDB 返回的错误信息抛出更具体的自定义异常。
•
详细日志: 在 SurrealDBHttpClient 的请求和响应流程中增加详细日志，记录发送的 SQL（参数化后）、接收到的响应、状态码以及解析结果或错误信息-,-。这对于调试 SurrealDB 交互问题至关重要。现有的日志记录已经比较详细,,,,,,,,,，但可以进一步标准化和完善。
•
Manager 层简化错误处理: Manager 层只需捕获客户端抛出的自定义异常，并根据业务需求进行处理或继续向上层抛出。不再需要在 Manager 层实现复杂的数据库交互错误回退逻辑（如 TurnManager.create_turn_async 中的备用 SQL 插入）-。
步骤 6: 解决特定已知问题
•
内存缓存策略: 重新评估 Manager 类中使用的内存缓存 (_session_cache, _turn_cache, _profile_cache, _embedding_cache),,,,。当前缓存可能导致数据与数据库不一致的问题，特别是更新和删除操作,,,,,,,,-。如果需要缓存，应实现更完善的缓存失效和同步机制，或者考虑使用专门的缓存层。为了简洁性，初期可以暂时移除这些缓存，后续根据性能需求再引入。
•
用户配置 time::now() 处理: UserProfileManager.create_profile 中手动构建 SQL 时，将 time::now() 字符串直接加入 VALUES-。而 SurrealDBHttpClient.create_record (非 SQL) 和 update_record 会尝试将 time::now() 字符串替换为 ISO 格式的当前时间,,,。这种不一致应该统一，推荐在应用程序代码中生成 ISO 格式时间，而不是依赖数据库或客户端特殊处理 time::now() 字符串。
此方案如何提升健壮性和简洁性:
•
健壮性:
◦
统一使用参数化 SQL + /sql 端点作为唯一的数据库交互方式，减少了因不同端点行为或响应格式不一致带来的问题。
◦
消除了手动拼接 SQL 字符串带来的潜在错误和安全风险（SQL 注入）。
◦
修复了 SurrealDBHttpClient 的响应解析逻辑，使其更可靠。
◦
移除了因底层不稳定而引入的复杂上层验证和回退逻辑。
◦
解决了手动事件循环管理的问题，避免了相关的性能和并发 Bug。
•
简洁性:
◦
数据库交互逻辑集中在 SurrealDBHttpClient 的核心方法中，上层 Manager 代码只需调用这些方法，无需关注具体 HTTP 请求细节或响应解析。
◦
移除了 SurrealStorage 中的重复功能和复杂连接管理。
◦
移除了 Manager 层中手动构建 SQL 和复杂的备用逻辑。
◦
统一异步模式，使异步代码更清晰、更符合惯例。
◦
减少了 parse_surreal_response 和 get_records 中针对多种响应格式的复杂分支判断。