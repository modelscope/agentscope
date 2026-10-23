import { useQuery } from '@tanstack/react-query';
import { Loader2, ShieldQuestion } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { agentApi } from '@/api';
import { Button } from '@/components/ui/button';

export function ExternalPermissionCard({
	agentId,
	sessionId,
	active,
}: {
	agentId: string;
	sessionId: string;
	active: boolean;
}) {
	const { t } = useTranslation();
	const [submitting, setSubmitting] = useState(false);
	const [error, setError] = useState('');
	const {
		data,
		refetch,
		error: queryError,
	} = useQuery({
		queryKey: ['external-permissions', agentId, sessionId],
		queryFn: () => agentApi.permissions(agentId, sessionId),
		enabled: active,
		refetchInterval: active ? 1000 : false,
		staleTime: 0,
	});
	const request = data?.requests[0];
	if (!active) return null;
	if (!request)
		return queryError ? (
			<p role="alert" className="rounded-xl border bg-card p-3 text-sm text-destructive">
				{queryError.message}
			</p>
		) : null;
	const answer = async (optionId: string | null) => {
		if (submitting) return;
		setSubmitting(true);
		setError('');
		try {
			await agentApi.answerPermission(agentId, sessionId, request.request_id, optionId);
			await refetch();
		} catch (caught) {
			setError(caught instanceof Error ? caught.message : String(caught));
			await refetch();
		} finally {
			setSubmitting(false);
		}
	};
	return (
		<div className="space-y-3 rounded-2xl border bg-card p-4 shadow-sm">
			<div className="flex items-center gap-2 text-sm font-medium">
				<ShieldQuestion className="size-4" />
				{t('external.approval')}
			</div>
			<p className="break-words text-sm">
				{request.tool_call.title ?? request.tool_call.tool_call_id}
			</p>
			{request.tool_call.raw_input != null && (
				<pre className="max-h-40 overflow-auto whitespace-pre-wrap break-all text-xs text-muted-foreground">
					{JSON.stringify(request.tool_call.raw_input, null, 2)}
				</pre>
			)}
			<div className="flex flex-wrap gap-2">
				{request.options.map((option) => (
					<Button
						key={option.option_id}
						size="sm"
						variant={option.kind.startsWith('reject') ? 'outline' : 'default'}
						disabled={submitting}
						onClick={() => void answer(option.option_id)}
					>
						{submitting && <Loader2 className="size-3 animate-spin" />}
						{option.name}
					</Button>
				))}
				<Button
					size="sm"
					variant="ghost"
					disabled={submitting}
					onClick={() => void answer(null)}
				>
					{t('common.cancel')}
				</Button>
			</div>
			{error && (
				<p role="alert" className="text-sm text-destructive">
					{error}
				</p>
			)}
		</div>
	);
}
