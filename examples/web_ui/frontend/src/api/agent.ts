import { client } from './client';
import type {
	ExternalExecutableStatus,
	ExternalAccountStatus,
	ExternalPermission,
	AgentListResponse,
	AgentView,
	AgentSchemaV2Response,
	CreateAgentRequest,
	CreateAgentResponse,
	UpdateAgentRequest,
} from './types';

export const agentApi = {
	loginQoder: (executable: string) =>
		client.post<{ started: boolean }>(
			'/agent/external/qoder/login',
			{ executable },
			undefined,
			{ timeoutMs: 10_000 },
		),
	getExternalDefaults: () =>
		client.get<{ workspace_path: string | null }>('/agent/external/defaults'),
	detectExecutable: (backend: 'codex' | 'qoder', executable: string) =>
		client.post<ExternalExecutableStatus>('/agent/external/detect', { backend, executable }),
	checkAccount: (backend: 'codex' | 'qoder', executable: string) =>
		client.post<ExternalAccountStatus>(
			'/agent/external/account',
			{ backend, executable },
			undefined,
			{ timeoutMs: 20_000 },
		),
	permissions: (agentId: string, sessionId: string) =>
		client.get<{ requests: ExternalPermission[] }>(
			`/agent/${agentId}/sessions/${sessionId}/external/permissions`,
		),
	answerPermission: (
		agentId: string,
		sessionId: string,
		requestId: string,
		option_id: string | null,
	) =>
		client.post(`/agent/${agentId}/sessions/${sessionId}/external/permissions/${requestId}`, {
			option_id,
		}),

	list: () => client.get<AgentListResponse>('/agent/'),

	getSchema: () => client.get<AgentSchemaV2Response>('/agent/schema/v2'),

	create: (body: CreateAgentRequest, options?: { silent?: boolean }) =>
		client.post<CreateAgentResponse>('/agent/', body, undefined, options),

	update: (agentId: string, body: UpdateAgentRequest, options?: { silent?: boolean }) =>
		client.patch<AgentView>(`/agent/${agentId}`, body, undefined, options),

	delete: (agentId: string) => client.delete(`/agent/${agentId}`),
};
