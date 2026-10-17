/** Completed attachments are sendable even when the composer has no text. */
export function hasInputContent(text: string, files: readonly { status: string }[]): boolean {
	return text.trim().length > 0 || files.some((file) => file.status === 'done');
}
