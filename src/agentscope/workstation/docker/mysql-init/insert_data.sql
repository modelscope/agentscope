INSERT INTO `account` (
    account_id,
    username,
    email,
    type,
    status,
    creator,
    modifier,
    password,
    gmt_create,
    gmt_modified
) VALUES
('10000', 'admin', 'admin@example.com', 'admin', 1, 'system', 'system', '{PASSWORD}',
 '{CURRENT_TIME}', '{CURRENT_TIME}'),
('10001', 'agentscope', 'agentscope@example.com', 'basic', 1, 'system',
'system',
'{PASSWORD}', '{CURRENT_TIME}', '{CURRENT_TIME}');
-- You can add more tables and insert statements here as needed
INSERT INTO `model` (
    workspace_id, icon, name, type, mode, model_id, provider, enable, tags, source, gmt_create, gmt_modified, creator, modifier
) VALUES
('1', NULL, 'qwen-max', 'llm', 'chat', 'qwen-max', 'Tongyi', 1, 'web_search,function_call', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen-max-latest', 'llm', 'chat', 'qwen-max-latest', 'Tongyi', 1, 'web_search,function_call,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen-plus', 'llm', 'chat', 'qwen-plus', 'Tongyi', 1, 'web_search,function_call', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen-plus-latest', 'llm', 'chat', 'qwen-plus-latest', 'Tongyi', 1, 'web_search,function_call,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen-turbo', 'llm', 'chat', 'qwen-turbo', 'Tongyi', 1, 'web_search,function_call', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen-turbo-latest', 'llm', 'chat', 'qwen-turbo-latest', 'Tongyi', 1, 'web_search,function_call,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen3-235b-a22b', 'llm', 'chat', 'qwen3-235b-a22b', 'Tongyi', 1, 'function_call,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen3-30b-a3b', 'llm', 'chat', 'qwen3-30b-a3b', 'Tongyi', 1, 'function_call,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen3-32b', 'llm', 'chat', 'qwen3-32b', 'Tongyi', 1, 'function_call,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen3-14b', 'llm', 'chat', 'qwen3-14b', 'Tongyi', 1, 'function_call,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen3-8b', 'llm', 'chat', 'qwen3-8b', 'Tongyi', 1, 'function_call,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen3-4b', 'llm', 'chat', 'qwen3-4b', 'Tongyi', 1, 'function_call,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen3-1.7b', 'llm', 'chat', 'qwen3-1.7b', 'Tongyi', 1, 'function_call,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen3-0.6b', 'llm', 'chat', 'qwen3-0.6b', 'Tongyi', 1, 'function_call,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen-vl-max', 'llm', 'chat', 'qwen-vl-max', 'Tongyi', 1, 'vision,function_call', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwen-vl-plus', 'llm', 'chat', 'qwen-vl-plus', 'Tongyi', 1, 'vision,function_call', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qvq-max', 'llm', 'chat', 'qvq-max', 'Tongyi', 1, 'vision,reasoning', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'qwq-plus', 'llm', 'chat', 'qwq-plus', 'Tongyi', 1, 'reasoning,function_call', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'text-embedding-v1', 'text_embedding', 'chat', 'text-embedding-v1', 'Tongyi', 1, 'embedding', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'text-embedding-v2', 'text_embedding', 'chat', 'text-embedding-v2', 'Tongyi', 1, 'embedding', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'text-embedding-v3', 'text_embedding', 'chat', 'text-embedding-v3', 'Tongyi', 1, 'embedding', 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'gte-rerank-v2', 'rerank', 'chat', 'gte-rerank-v2', 'Tongyi', 1, NULL, 'preset', NOW(), NOW(), NULL, NULL),
('1', NULL, 'deepseek-r1', 'llm', 'chat', 'deepseek-r1', 'Tongyi', 1, 'reasoning', 'preset', NOW(), NOW(), NULL, NULL);
INSERT INTO `provider` (
    workspace_id, icon, name, description, provider, enable, source,
    credential, supported_model_types, protocol, gmt_create, gmt_modified,
    creator, modifier
) VALUES (
    '1', NULL, 'Tongyi', 'Tongyi', 'Tongyi', 1, 'preset',
    JSON_OBJECT(
        'endpoint', 'https://dashscope.aliyuncs.com/compatible-mode',
        'api_key', '{API_KEY}'
    ),
    NULL, 'OpenAI', NOW(), NOW(),
    NULL, NULL
);