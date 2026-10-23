import { CircleAlert, Loader2, PlusCircle } from 'lucide-react';
import { useEffect, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import type { ContextConfig, InviteConfig, ReActConfig } from '@/api';
import type { ExternalAgentConfig, AgentBackend } from '@/api';
import { AgentBackendFields } from '@/components/form/AgentBackendFields';
import {
	AgentFormFields,
	defaultAgentFormValues,
	type AgentFormValues,
	type AgentSection,
} from '@/components/form/AgentFormFields';
import type { SchemaFormValue } from '@/components/form/SchemaForm';
import { Alert, AlertDescription } from '@/components/ui/alert.tsx';
import { Button } from '@/components/ui/button';
import {
	Dialog,
	DialogContent,
	DialogFooter,
	DialogHeader,
	DialogTitle,
	DialogDescription,
	DialogTrigger,
} from '@/components/ui/dialog';
import { useAgents } from '@/hooks/useAgents';
import { useAgentSchema } from '@/hooks/useAgentSchema';
import { formatApiErrorForAlert } from '@/lib/api-error';

interface Props {
	onCreated?: () => void;
	children: ReactNode;
}

export function AgentDialog({ onCreated, children }: Props) {
	const { create } = useAgents();
	const { t } = useTranslation();
	const { schema } = useAgentSchema();
	const [open, setOpen] = useState(false);
	const [submitting, setSubmitting] = useState(false);
	const [values, setValues] = useState<AgentFormValues | null>(null);
	const [errorMsg, setErrorMsg] = useState('');
	const [backend, setBackend] = useState<AgentBackend>('agentscope');
	const [externalConfig, setExternalAgentConfig] = useState<ExternalAgentConfig>({
		executable: '',
	});

	useEffect(() => {
		if (open && schema && !values) {
			setValues(defaultAgentFormValues(schema));
		}
		if (!open) {
			setValues(null);
			setBackend('agentscope');
			setExternalAgentConfig({ executable: '' });
			setErrorMsg('');
		}
	}, [open, schema, values]);

	const handleChange = (section: AgentSection, key: string, value: SchemaFormValue) => {
		setErrorMsg('');
		setValues((prev) =>
			prev ? { ...prev, [section]: { ...prev[section], [key]: value } } : prev,
		);
	};

	const handleSubmit = async () => {
		if (!values) return;
		const name = (values.identity.name as string | undefined)?.trim();
		if (!name) return;
		setErrorMsg('');
		setSubmitting(true);
		try {
			await create(
				{
					name,
					backend,
					...(backend !== 'agentscope' ? { external_config: externalConfig } : {}),
					system_prompt:
						backend === 'agentscope'
							? (values.identity.system_prompt as string | undefined)
							: undefined,
					chat_config:
						backend === 'agentscope'
							? {
									context_config:
										values.context_config as unknown as ContextConfig,
									react_config: values.react_config as unknown as ReActConfig,
									invite_config: values.invite_config as unknown as InviteConfig,
								}
							: undefined,
				},
				{ silent: true },
			);
			setOpen(false);
			onCreated?.();
		} catch (e) {
			setErrorMsg(formatApiErrorForAlert(e));
		} finally {
			setSubmitting(false);
		}
	};

	const nameValid = !!(values?.identity.name as string | undefined)?.trim();

	return (
		<Dialog open={open} onOpenChange={setOpen}>
			<DialogTrigger asChild>{children}</DialogTrigger>
			<DialogContent className="flex max-h-[calc(100dvh-2rem)] flex-col !w-[calc(100vw-2rem)] !max-w-[640px]">
				<DialogHeader className="shrink-0">
					<DialogTitle>{t('dialog-agent-create.title')}</DialogTitle>
					<DialogDescription className="sr-only">
						{t('dialog-agent-create.description')}
					</DialogDescription>
				</DialogHeader>
				<div className="no-scrollbar -mx-4 min-h-0 flex-1 overflow-y-auto px-4">
					{schema && values ? (
						<div className="space-y-5">
							<AgentBackendFields
								backend={backend}
								config={externalConfig}
								name={(values.identity.name as string) ?? ''}
								onBackendChange={(next) => {
									setBackend(next);
									setExternalAgentConfig({ executable: '' });
								}}
								onConfigChange={setExternalAgentConfig}
								onNameChange={(name) => handleChange('identity', 'name', name)}
							/>
							{backend === 'agentscope' && (
								<AgentFormFields
									schema={schema}
									values={values}
									onChange={handleChange}
								/>
							)}
						</div>
					) : (
						<p className="text-muted-foreground text-sm">{t('common.loading')}</p>
					)}
				</div>
				{errorMsg && (
					<Alert variant="destructive">
						<CircleAlert />
						<AlertDescription className="whitespace-pre-wrap">
							{errorMsg}
						</AlertDescription>
					</Alert>
				)}
				<DialogFooter className="shrink-0">
					<Button variant="ghost" onClick={() => setOpen(false)} disabled={submitting}>
						<CircleAlert className="size-3.5" />
						{t('common.cancel')}
					</Button>
					<Button
						onClick={handleSubmit}
						disabled={!nameValid || submitting || !schema || !values}
					>
						{submitting ? (
							<Loader2 className="size-3.5 animate-spin" />
						) : (
							<PlusCircle className="size-3.5" />
						)}
						{submitting ? t('common.creating') : t('common.create')}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
