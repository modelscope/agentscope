import type { Msg } from '@agentscope-ai/agentscope/message';
import { CheckCircle2, CircleAlert, ListTodo, Loader2, Terminal } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface ToolSnapshot {
	tool_call_id: string;
	title?: string;
	status?: string;
	raw_input?: unknown;
	raw_output?: unknown;
	content?: Array<{
		type: string;
		content?: { type: string; text?: string };
		[key: string]: unknown;
	}>;
}

export function ExternalActivity({ message }: { message: Msg }) {
	const { t } = useTranslation();
	const tools = Object.values(
		(message.metadata?.external_tools ?? {}) as unknown as Record<string, ToolSnapshot>,
	);
	const plan = (message.metadata?.external_plan ?? []) as unknown as Array<{
		content: string;
		status: string;
	}>;
	if (!tools.length && !plan.length) return null;
	return (
		<div className="my-3 space-y-2">
			{tools.map((tool) => (
				<details
					key={tool.tool_call_id}
					className="rounded-xl border bg-muted/30 px-4 py-3 text-sm"
				>
					<summary className="flex cursor-pointer items-center gap-2">
						{tool.status === 'completed' ? (
							<CheckCircle2 className="size-4 shrink-0" />
						) : tool.status === 'failed' ? (
							<CircleAlert className="size-4 shrink-0 text-destructive" />
						) : !message.finished_at ? (
							<Loader2 className="size-4 shrink-0 animate-spin" />
						) : (
							<Terminal className="size-4 shrink-0" />
						)}
						<span className="min-w-0 flex-1 truncate">
							{tool.title ?? tool.tool_call_id}
						</span>
						<span className="text-xs text-muted-foreground">
							{t(`external.status.${tool.status ?? 'pending'}`)}
						</span>
					</summary>
					<div className="mt-3 space-y-2">
						{tool.raw_input != null && (
							<pre className="max-h-64 overflow-auto whitespace-pre-wrap break-all text-xs">
								{JSON.stringify(tool.raw_input, null, 2)}
							</pre>
						)}
						{tool.content?.map((item, index) => (
							<pre
								key={index}
								className="max-h-72 overflow-auto whitespace-pre-wrap break-words text-xs"
							>
								{item.content?.type === 'text'
									? item.content.text
									: JSON.stringify(item, null, 2)}
							</pre>
						))}
						{tool.raw_output != null && (
							<pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words text-xs">
								{JSON.stringify(tool.raw_output, null, 2)}
							</pre>
						)}
					</div>
				</details>
			))}
			{plan.length > 0 && (
				<div className="rounded-xl border p-4 text-sm">
					<div className="mb-2 flex items-center gap-2">
						<ListTodo className="size-4" />
						{t('external.plan')}
					</div>
					<ul className="space-y-1">
						{plan.map((entry, index) => (
							<li key={index} className="flex gap-2">
								<span className="min-w-0 flex-1 break-words">{entry.content}</span>
								<span className="text-xs text-muted-foreground">
									{t(`external.status.${entry.status}`)}
								</span>
							</li>
						))}
					</ul>
				</div>
			)}
		</div>
	);
}
