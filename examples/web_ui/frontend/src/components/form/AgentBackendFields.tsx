import { useQuery } from '@tanstack/react-query';
import {
	Blocks,
	Bot,
	Check,
	CircleAlert,
	Code2,
	Loader2,
	LogIn,
	RefreshCw,
	ShieldCheck,
	Terminal,
} from 'lucide-react';
import { useEffect, useId, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
	agentApi,
	type ExternalAccountStatus,
	type ExternalAgentConfig,
	type ExternalExecutableStatus,
	type AgentBackend,
} from '@/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface Props {
	backend: AgentBackend;
	config: ExternalAgentConfig;
	name: string;
	onBackendChange?: (backend: AgentBackend) => void;
	onConfigChange: (config: ExternalAgentConfig) => void;
	onNameChange: (name: string) => void;
}

const providers = [
	{ id: 'codex', name: 'Codex', icon: Terminal },
	{ id: 'qoder', name: 'Qoder', icon: Code2 },
] as const;

export function AgentBackendFields({
	backend,
	config,
	name,
	onBackendChange,
	onConfigChange,
	onNameChange,
}: Props) {
	const { t } = useTranslation();
	const id = useId();
	const external = backend !== 'agentscope';
	const {
		data: defaults,
		isPending: defaultsPending,
		isError: defaultsError,
	} = useQuery({
		queryKey: ['external-agent-defaults'],
		queryFn: () => agentApi.getExternalDefaults(),
		enabled: external,
	});
	const epoch = useRef(0);
	const loginTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
	const [loginError, setLoginError] = useState<string | null>(null);
	const [busy, setBusy] = useState<'detect' | 'account' | 'login' | null>(null);
	const [executable, setExecutable] = useState<{
		key: string;
		value: ExternalExecutableStatus;
	} | null>(null);
	const [account, setAccount] = useState<{ key: string; value: ExternalAccountStatus } | null>(
		null,
	);
	const key = JSON.stringify([backend, config.executable]);
	const detected = executable?.key === key ? executable.value : null;
	const identity = account?.key === key ? account.value : null;
	const accountName = identity?.account?.email ?? identity?.account?.username;

	useEffect(
		() => () => {
			epoch.current += 1;
			if (loginTimer.current !== null) clearTimeout(loginTimer.current);
		},
		[],
	);

	const resetDetection = () => {
		if (loginTimer.current !== null) clearTimeout(loginTimer.current);
		setLoginError(null);
		epoch.current += 1;
		setBusy(null);
		setExecutable(null);
		setAccount(null);
	};
	const selectBackend = (next: AgentBackend) => {
		if (next === backend || !onBackendChange) return;
		resetDetection();
		onBackendChange(next);
	};
	const detect = async () => {
		if (backend === 'agentscope') return;
		const request = ++epoch.current;
		setBusy('detect');
		setLoginError(null);
		setExecutable(null);
		setAccount(null);
		try {
			const value = await agentApi.detectExecutable(backend, config.executable);
			if (request === epoch.current) setExecutable({ key, value });
		} catch (error) {
			if (request === epoch.current)
				setExecutable({
					key,
					value: {
						installed: false,
						executable: null,
						error: error instanceof Error ? error.message : String(error),
					},
				});
		} finally {
			if (request === epoch.current) setBusy(null);
		}
	};
	const inspectAccount = async () => {
		if (backend === 'agentscope' || !detected?.executable) return;
		const request = ++epoch.current;
		setBusy('account');
		setLoginError(null);
		setAccount(null);
		try {
			const value = await agentApi.checkAccount(backend, detected.executable);
			if (request === epoch.current) setAccount({ key, value });
		} catch (error) {
			if (request === epoch.current)
				setAccount({
					key,
					value: {
						status: 'error',
						account: null,
						error: error instanceof Error ? error.message : String(error),
					},
				});
		} finally {
			if (request === epoch.current) setBusy(null);
		}
	};

	const login = async () => {
		if (backend !== 'qoder' || !detected?.executable || busy !== null) return;
		const request = ++epoch.current;
		const command = detected.executable;
		const deadline = Date.now() + 120_000;
		setBusy('login');
		setLoginError(null);
		const fail = (message: string) => {
			if (request !== epoch.current) return;
			setLoginError(message);
			setBusy(null);
		};
		const poll = async () => {
			if (request !== epoch.current) return;
			if (Date.now() >= deadline) {
				fail(t('external.loginTimeout'));
				return;
			}
			try {
				const value = await agentApi.checkAccount('qoder', command);
				if (request !== epoch.current) return;
				setAccount({ key, value });
				if (value.status !== 'not_authenticated') {
					setBusy(null);
					return;
				}
				loginTimer.current = setTimeout(() => void poll(), 2000);
			} catch (error) {
				fail(error instanceof Error ? error.message : String(error));
			}
		};
		try {
			await agentApi.loginQoder(command);
			if (request === epoch.current) void poll();
		} catch (error) {
			fail(error instanceof Error ? error.message : String(error));
		}
	};

	return (
		<section className="space-y-5">
			<div
				className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-2"
				role="group"
				aria-label={t('external.agentType')}
			>
				{[
					{
						value: 'agentscope' as const,
						title: 'nativeTitle',
						description: 'nativeDescription',
						icon: Bot,
						selected: !external,
					},
					{
						value: external ? backend : ('codex' as const),
						title: 'thirdPartyTitle',
						description: 'thirdPartyDescription',
						icon: Blocks,
						selected: external,
					},
				].map(({ value, title, description, icon: Icon, selected }) => (
					<Button
						key={title}
						type="button"
						variant="outline"
						aria-pressed={selected}
						disabled={!onBackendChange && !selected}
						onClick={() => selectBackend(value)}
						className={cn(
							'h-auto items-start justify-start gap-3 rounded-xl p-4 text-left whitespace-normal',
							selected && 'border-foreground/60 bg-muted/50',
						)}
					>
						<Icon className="mt-0.5 size-5 shrink-0" />
						<span className="min-w-0 flex-1 space-y-1">
							<span className="block text-sm font-medium">
								{t(`external.${title}`)}
							</span>
							<span className="block text-xs font-normal leading-relaxed text-muted-foreground">
								{t(`external.${description}`)}
							</span>
						</span>
						{selected && <Check className="mt-0.5 size-4 shrink-0" />}
					</Button>
				))}
			</div>
			{external && (
				<div className="space-y-5 rounded-xl border p-4 sm:p-5">
					<div className="space-y-3">
						<p className="text-sm font-medium">{t('external.providerTitle')}</p>
						<div
							className="grid grid-cols-2 gap-3"
							role="group"
							aria-label={t('external.providerTitle')}
						>
							{providers.map(({ id: provider, name: label, icon: Icon }) => (
								<Button
									key={provider}
									type="button"
									variant="outline"
									aria-pressed={backend === provider}
									disabled={!onBackendChange && backend !== provider}
									onClick={() => selectBackend(provider)}
									className={cn(
										'h-12 justify-start rounded-lg px-3',
										backend === provider && 'border-foreground/60 bg-muted/50',
									)}
								>
									<Icon className="size-4 shrink-0" />
									<span className="flex-1 text-left">{label}</span>
									{backend === provider && <Check className="size-4" />}
								</Button>
							))}
						</div>
					</div>
					<div className="space-y-2">
						<Label htmlFor={`${id}-binary`}>{t('external.executable')}</Label>
						<div className="flex flex-col gap-2 min-[420px]:flex-row">
							<Input
								id={`${id}-binary`}
								className="min-w-0 flex-1"
								value={config.executable}
								onChange={(event) => {
									resetDetection();
									onConfigChange({ ...config, executable: event.target.value });
								}}
								placeholder={t('external.binaryPlaceholder')}
								autoComplete="off"
							/>
							<Button
								type="button"
								variant="outline"
								disabled={busy !== null}
								onClick={() => void detect()}
							>
								{busy === 'detect' ? (
									<Loader2 className="size-4 animate-spin" />
								) : (
									<RefreshCw className="size-4" />
								)}
								{t(
									busy === 'detect'
										? 'external.checking'
										: 'external.detectExecutable',
								)}
							</Button>
						</div>
						<p className="text-xs leading-relaxed text-muted-foreground">
							{t(`external.${backend}Hint`)}
						</p>
						{detected && (
							<div
								role="status"
								className={cn(
									'space-y-1 rounded-lg bg-muted/50 p-3 text-xs',
									!detected.installed && 'text-destructive',
								)}
							>
								<div className="flex items-center gap-2">
									{detected.installed ? (
										<Check className="size-4 shrink-0" />
									) : (
										<CircleAlert className="size-4 shrink-0" />
									)}
									{t(
										detected.installed
											? 'external.binaryFound'
											: 'external.binaryMissing',
									)}
								</div>
								{detected.executable && (
									<code className="block break-all leading-relaxed">
										{detected.executable}
									</code>
								)}
								{detected.error && (
									<p className="break-words leading-relaxed">{detected.error}</p>
								)}
							</div>
						)}
					</div>
					<div className="space-y-3 border-t pt-4">
						<div className="flex flex-wrap items-center justify-between gap-3">
							<div className="flex items-center gap-2 text-sm font-medium">
								<ShieldCheck className="size-4" />
								{t('external.accountTitle')}
							</div>
							<Button
								type="button"
								variant="outline"
								size="sm"
								disabled={busy !== null || !detected?.installed}
								onClick={() => void inspectAccount()}
							>
								{busy === 'account' ? (
									<Loader2 className="size-4 animate-spin" />
								) : (
									<RefreshCw className="size-4" />
								)}
								{t(
									busy === 'account'
										? 'external.checking'
										: 'external.checkAccount',
								)}
							</Button>
						</div>
						<div
							role="status"
							className="space-y-1 text-xs leading-relaxed text-muted-foreground"
						>
							{!identity ? (
								<p>
									{t(
										busy === 'account'
											? 'external.checking'
											: detected?.installed
												? 'external.accountUnchecked'
												: 'external.detectFirst',
									)}
								</p>
							) : (
								<>
									<p
										className={cn(
											'flex items-center gap-2 text-sm',
											identity.status === 'error'
												? 'text-destructive'
												: 'text-foreground',
										)}
									>
										{identity.status === 'authenticated' ? (
											<Check className="size-4" />
										) : (
											<CircleAlert className="size-4" />
										)}
										{t(`external.accountStatus.${identity.status}`)}
									</p>
									{accountName && <p className="break-all">{accountName}</p>}
									{identity.account?.type && (
										<p>
											{t('external.accountMethod')}:{' '}
											{t(`external.accountTypes.${identity.account.type}`, {
												defaultValue: identity.account.type,
											})}
											{identity.account.planType
												? ` · ${identity.account.planType}`
												: ''}
										</p>
									)}
									{identity.status === 'configured' && (
										<p>{t('external.configuredHint')}</p>
									)}
									{identity.status === 'not_authenticated' && (
										<p>
											{t(
												backend === 'qoder'
													? 'external.qoderLoginHint'
													: 'external.loginHint',
												{
													provider:
														backend === 'codex' ? 'Codex' : 'Qoder',
												},
											)}
										</p>
									)}
									{identity.error && (
										<p className="break-words text-destructive">
											{identity.error}
										</p>
									)}
								</>
							)}
							{backend === 'qoder' &&
								detected?.installed &&
								identity?.status !== 'authenticated' &&
								identity?.status !== 'configured' && (
									<Button
										type="button"
										variant="outline"
										size="sm"
										disabled={busy !== null}
										onClick={() => void login()}
									>
										{busy === 'login' ? (
											<Loader2 className="size-4 animate-spin" />
										) : (
											<LogIn className="size-4" />
										)}
										{t(
											busy === 'login'
												? 'external.loginWaiting'
												: 'external.loginQoder',
										)}
									</Button>
								)}
							{busy === 'login' && identity?.status !== 'not_authenticated' && (
								<p>{t('external.qoderLoginHint')}</p>
							)}
							{loginError && (
								<p className="text-destructive" role="alert">
									{loginError}
								</p>
							)}
							<p>{t('external.accountHint')}</p>
						</div>
					</div>
					<div className="space-y-4 border-t pt-4">
						<div className="space-y-2">
							<Label htmlFor={`${id}-cwd`}>{t('external.workspacePath')}</Label>
							<Input
								id={`${id}-cwd`}
								value={config.cwd ?? ''}
								onChange={(event) =>
									onConfigChange({ ...config, cwd: event.target.value })
								}
								placeholder={t('external.workspaceDefault')}
								aria-describedby={`${id}-cwd-help`}
								autoComplete="off"
							/>
							<p
								id={`${id}-cwd-help`}
								className="break-words text-xs leading-relaxed text-muted-foreground"
							>
								{defaultsPending
									? t('external.workspaceLoading')
									: defaultsError
										? t('external.workspaceLoadError')
										: defaults?.workspace_path
											? t('external.workspaceHelp', {
													path: defaults.workspace_path,
												})
											: t('external.workspaceUnavailable')}
							</p>
						</div>
						<div className="space-y-2">
							<Label htmlFor={`${id}-name`}>{t('external.name')}</Label>
							<Input
								id={`${id}-name`}
								value={name}
								onChange={(event) => onNameChange(event.target.value)}
								autoComplete="off"
							/>
						</div>
					</div>
				</div>
			)}
		</section>
	);
}
