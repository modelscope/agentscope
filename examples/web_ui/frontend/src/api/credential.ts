import { client } from './client';
import type {
	CreateCredentialRequest,
	CreateCredentialResponse,
	CredentialListResponse,
	CredentialView,
	CredentialSchemasResponse,
	RemoteModelsResponse,
	UpdateCredentialRequest,
} from './types';

export const credentialApi = {
	list: () => client.get<CredentialListResponse>('/credential/'),

	schemas: () => client.get<CredentialSchemasResponse>('/credential/schemas'),

	create: (body: CreateCredentialRequest) =>
		client.post<CreateCredentialResponse>('/credential/', body),

	update: (credentialId: string, body: UpdateCredentialRequest) =>
		client.patch<CredentialView>(`/credential/${credentialId}`, body),

	delete: (credentialId: string) => client.delete(`/credential/${credentialId}`),

	/** Ask the configured endpoint which models it actually serves. */
	remoteModels: (credentialId: string, options?: { silent?: boolean }) =>
		client.get<RemoteModelsResponse>(
			`/credential/${credentialId}/remote-models`,
			undefined,
			options,
		),

	/** Probe one model with a 1-token request through the credential. */
	verifyModel: (
		credentialId: string,
		model: string,
		options?: { silent?: boolean },
	) =>
		client.post<{ ok: boolean }>(
			`/credential/${credentialId}/verify-model`,
			{ model },
			undefined,
			options,
		),
};
